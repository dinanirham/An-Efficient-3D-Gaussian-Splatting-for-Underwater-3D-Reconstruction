#
# Copyright (C) 2023, Inria
# GRAPHDECO research group, https://team.inria.fr/graphdeco
# All rights reserved.
#
# This software is free for non-commercial, research and evaluation use
# under the terms of the LICENSE.md file.
#
# For inquiries contact  george.drettakis@inria.fr
#

import os
import time
from datetime import datetime
import glob
import json
from pathlib import Path
import torch
from typing import List
from random import randint
from utils.loss_utils import l1_loss, ssim, depth_weighted_l1_loss, depth_weighted_l2_loss
from gaussian_renderer import render, render_depth, network_gui
import sys
from scene import Scene, GaussianModel
from utils.general_utils import safe_state
import uuid
from tqdm import tqdm
from utils.general_utils import inverse_sigmoid
from utils.image_utils import psnr
from argparse import ArgumentParser, Namespace
from arguments import (
    ModelParams,
    PipelineParams,
    OptimizationParams,
    add_cell_argument,
    apply_cell_config,
)
from utils.preflight import preflight_args, preflight_scene, write_manifest
from utils.diagnostics import DiagnosticLogger
from source.simplify import accumulate_importance, cdf_keep_mask, sample_to_budget
from source.quantize import AttributeQuantizer
from source.storage import measure_model_size, write_compressed_model
try:
    from torch.utils.tensorboard import SummaryWriter
    TENSORBOARD_FOUND = True
except ImportError:
    TENSORBOARD_FOUND = False

# import kornia.morphology as morph
from deepseecolor.models import (
    AttenuateNet,
    AttenuateNetV2,
    AttenuateNetV3,
    BackscatterNet,
    BackscatterNetV2,
)
from deepseecolor.losses import (
    AlphaBackgroundLoss,
    AttenuateLoss,
    BackscatterLoss,
    DarkChannelPriorLoss,
    DarkChannelPriorLossV2,
    DarkChannelPriorLossV3,
    GrayWorldPriorLoss,
    RgbSpatialVariationLoss,
    RgbSaturationLoss,
    mixture_of_laplacians_loss
)
from deepseecolor.depth_losses import SmoothDepthLoss

from lpipsPyTorch import lpips
from metrics import readImages, read_image
from render_uw import estimate_atmospheric_light, render_set
from utils.sh_utils import SH2RGB

def training(model_params, opt_params, pipe_params, testing_iterations, saving_iterations, checkpoint_iterations, checkpoint, debug_from):
    if model_params.do_scene_bb:
        scene_bounds_xxyyzz = [
            model_params.bb_xlo,
            model_params.bb_xhi,
            model_params.bb_ylo,
            model_params.bb_yhi,
            model_params.bb_zlo,
            model_params.bb_zhi,
        ]
        print(f"boundaries for camera/pcd: {scene_bounds_xxyyzz}")
        model_params.scene_bounds_xxyyzz = scene_bounds_xxyyzz

    first_iter = 0
    tb_writer = prepare_output_and_logger(model_params)
    gaussians = GaussianModel(model_params.sh_degree, opt_params.do_isotropic)
    scene = Scene(model_params, gaussians, shuffle=opt_params.shuffle)

    # M2: the split can only be checked once the dataset is loaded.
    split_sizes = preflight_scene(scene)
    diag = DiagnosticLogger(model_params.model_path, opt_params.diag_interval)
    diag.log(
        iteration=0,
        event="init",
        n_primitives=gaussians.get_xyz.shape[0],
        note=f"train={split_sizes['train_cameras']} test={split_sizes['test_cameras']}",
    )

    # deep see color
    if opt_params.do_seathru:
        bs_model = BackscatterNetV2(use_residual=opt_params.use_bs_residual, scale=opt_params.bs_scale, do_sigmoid=opt_params.do_sigmoid_bs).cuda()
        if opt_params.use_at_v2:
            at_model = AttenuateNetV2(scale=opt_params.at_scale, do_sigmoid=opt_params.do_sigmoid_at).cuda()
        elif opt_params.use_at_v3:
            at_model = AttenuateNetV3(scale=opt_params.at_scale, do_sigmoid=opt_params.do_sigmoid_at, init_vals=not opt_params.do_sigmoid_at).cuda()
        else:
            at_model = AttenuateNet(scale=opt_params.at_scale, do_sigmoid=opt_params.do_sigmoid_at).cuda()
        bs_optimizer = torch.optim.Adam(bs_model.parameters(), lr=opt_params.bs_at_lr)
        at_optimizer = torch.optim.Adam(at_model.parameters(), lr=opt_params.bs_at_lr)

    depth_smooth_criterion = SmoothDepthLoss().cuda()
    gw_criterion = GrayWorldPriorLoss().cuda()
    rgb_sv_criterion = RgbSpatialVariationLoss().cuda()
    rgb_01_criterion = RgbSaturationLoss(saturation_val=1.0).cuda()
    rgb_sat_criterion = RgbSaturationLoss(saturation_val=0.7).cuda()
    alpha_bg_criterion = AlphaBackgroundLoss(use_kornia=opt_params.use_lab).cuda()

    dsc_at_criterion = AttenuateLoss().cuda()
    dcp_criterion = DarkChannelPriorLossV3().cuda()

    gaussians.training_setup(opt_params)
    if checkpoint:
        print(f"Loading checkpoint: {checkpoint}")
        (model_params, first_iter) = torch.load(checkpoint)
        gaussians.restore(model_params, opt_params)

    '''
    this bg color gets passed to the renderer
    '''
    bg_color = [1, 1, 1] if model_params.white_background else [0, 0, 0]
    background = torch.tensor(bg_color, dtype=torch.float32, device="cuda")
    if opt_params.random_background:
        bg = torch.rand((3), device="cuda")
    else:
        bg = background

    '''
    this lets us learn background
    '''
    learned_bg = torch.tensor([0, 0, 0], dtype=torch.float32, device="cuda")
    if opt_params.learn_background:
        assert not model_params.white_background
        bg_init = torch.rand((3), device="cuda")
        bg_init[2] = 0.8 # make the b channel high to start
        bg_init[1] = 0.25 # make the g channel high to start
        bg_init[0] = 0.05 # make the r channel low to start
        learned_bg = torch.nn.Parameter(inverse_sigmoid(bg_init.requires_grad_(True)))
        bg_optimizer = torch.optim.Adam([learned_bg], lr=opt_params.bg_lr)

    iter_start = torch.cuda.Event(enable_timing = True)
    iter_end = torch.cuda.Event(enable_timing = True)

    viewpoint_stack = None
    ema_loss_for_log = 0.0
    progress_bar = tqdm(range(first_iter, opt_params.iterations), desc="Training progress")
    first_iter += 1

    # allocate tensors outside the training loop
    depth_l1_loss = torch.Tensor([0.0]).squeeze().cuda()
    depth_smooth_loss = torch.Tensor([0.0]).squeeze().cuda()
    dcp_loss = torch.Tensor([0.0]).squeeze().cuda()
    gw_loss = torch.Tensor([0.0]).squeeze().cuda()
    rgb_01_loss = torch.Tensor([0.0]).squeeze().cuda()
    rgb_sv_loss = torch.Tensor([0.0]).squeeze().cuda()
    rgb_sat_loss = torch.Tensor([0.0]).squeeze().cuda()
    alpha_bg_loss = torch.Tensor([0.0]).squeeze().cuda()
    dsc_at_loss = torch.Tensor([0.0]).squeeze().cuda()
    binf_loss = torch.Tensor([0.0]).squeeze().cuda()
    alpha_smooth_loss = torch.Tensor([0.0]).squeeze().cuda()
    opacity_prior_loss = torch.Tensor([0.0]).squeeze().cuda()
    dl1 = torch.Tensor([0.0]).squeeze().cuda()

    '''
    training loop
    '''
    iteration = 1
    bs_update_counter = 0
    at_update_counter = 0
    bs_update_iter = 0
    at_update_iter = 0
    at_inited = False
    bs_inited = False

    # CD-6: medium-only steps still owed after a simplification event.
    rewarm_remaining = 0

    # M3: the three codebooks. Constructed unconditionally so that the storage
    # report exists even for cells that never enable it.
    attr_quantizer = AttributeQuantizer(
        num_clusters=opt_params.kmeans_k, num_iters=opt_params.kmeans_iters
    )

    update_gs_color_counter = 0
    adjust_gs_colors_for_cc = False

    done_binf_init_with_bg = False
    print_message_once = False
    effective_steps = 0
    training_started_at = time.time()
    while iteration < opt_params.iterations + 1:
        # Effective optimizer steps, which are NOT the iteration count.  The
        # medium warm-up, the colour-adjustment phase, the periodic medium
        # bursts and CD-6's re-identification all `continue` past
        # `iteration += 1`, so each performs a full forward, backward and
        # optimizer step without advancing the counter -- at default settings a
        # nominally 30k-iteration run does roughly 43k of them, each paying the
        # cost of both rasterization passes.  Every loop pass is one step, so
        # counting here is exactly the quantity a timing comparison needs.
        effective_steps += 1
        iter_start.record()

        # R-5 / CD-7: under dense initialization the position LR schedule is
        # clamped to its step-`m1_max_lr_floor` value.  EDGS applies this by
        # default and does not document it: a dense init starts ~50x closer to
        # the final geometry, so 3DGS's high early LR -- tuned to move a sparse
        # SfM seed across the scene -- would scatter a good initialization
        # rather than refine it.
        lr_iteration = iteration
        if opt_params.m1_dense_init and opt_params.m1_max_lr:
            lr_iteration = max(iteration, opt_params.m1_max_lr_floor)
        if (
            opt_params.m2_simplify
            and opt_params.m2_lr_rewind
            and iteration >= opt_params.simp_iteration1
        ):
            # Off by default.  Mini-Splatting's rewind exists so that freshly
            # REINITIALIZED primitives still have enough LR to move; under the
            # simplification-only scoping the survivors keep their parameters
            # and their Adam state, so the premise does not hold.  Kept as a
            # flag because it is the natural sensitivity check.
            lr_iteration = (
                iteration - opt_params.simp_iteration1 + opt_params.m2_lr_rewind_to
            )
        gaussians.update_learning_rate(lr_iteration)

        # Freeze the gaussian model as necessary
        if iteration == opt_params.freeze_gs_from_iter:
            gaussians.freeze_parameters(xyz=True, colors=False, opacity=True, scaling=True, rotation=True)
        if iteration == opt_params.unfreeze_gs_from_iter:
            print(f"[{iteration}] unfreezing gs parameters")
            gaussians.freeze_parameters(xyz=False, colors=False, opacity=False, scaling=False, rotation=False)
        if iteration == opt_params.seathru_from_iter + 1:
            if not print_message_once:
                print(f"[{iteration}] freezing gs parameters except color at seathru + 1")
                print_message_once = True
            gaussians.freeze_parameters(xyz=True, colors=False, opacity=True, scaling=True, rotation=True)
        if iteration == opt_params.seathru_from_iter + 2:
            print(f"[{iteration}] unfreezing gs parameters at seathru + 2")
            gaussians.freeze_parameters(xyz=False, colors=False, opacity=False, scaling=False, rotation=False)


        # Pick a random Camera
        if not viewpoint_stack:
            viewpoint_stack = scene.getTrainCameras().copy()
        viewpoint_cam = viewpoint_stack.pop(randint(0, len(viewpoint_stack)-1))

        # --- M3: install quantized overrides before anything renders --------
        # Cleared first, so an iteration before kmeans_st_iter renders exactly
        # the unquantized parameters. Kept in place for the whole iteration --
        # including evaluation -- because the quantized model is what gets
        # stored, so that is what should be scored.
        gaussians.clear_quant_override()
        if opt_params.m3_quantize and iteration > opt_params.kmeans_st_iter:
            attr_quantizer.apply(
                gaussians,
                assign=(iteration % opt_params.kmeans_freq == 1),
            )

        # Render
        render_pkg = render(viewpoint_cam, gaussians, pipe_params, bg)
        rendered_image, viewspace_point_tensor, visibility_filter, radii = \
            render_pkg["render"], render_pkg["viewspace_points"], render_pkg["visibility_filter"], render_pkg["radii"]

        # CD-13: the diff_gaussian_rasterization_ms fork returns no alpha from
        # the colour pass, so the depth pass doubles as an alpha probe (see
        # gaussian_renderer/__init__.py).  This pass ran unconditionally
        # upstream as well -- it has only moved earlier, it is not an extra one.
        #
        # CD-22: share the colour pass's gradient buffer.  Upstream reads alpha
        # from the colour pass, so alpha-loss gradients land in the tensor
        # add_densification_stats consumes; a probe pass with its own buffer
        # reproduces alpha's value and drops its gradient from density control.
        # Measured cost of getting this wrong: 743k primitives against
        # vanilla's 4.46M on Curasao.  Note this also admits the depth losses'
        # gradients, which upstream excludes -- a known, measured deviation.
        render_depth_pkg = render_depth(
            viewpoint_cam, gaussians, pipe_params, bg,
            screenspace_points=viewspace_point_tensor,
        )
        image_alpha = render_depth_pkg["alpha"]

        if opt_params.learn_background:
            if opt_params.bg_from_bs and opt_params.do_seathru and iteration > opt_params.seathru_from_iter:
                # do not use learned background; rely on backscatter to hopefully fill this in
                image = rendered_image
                if not done_binf_init_with_bg:
                    print(f"[{iteration} updated bs_model B_inf with learnred_bg parameters {torch.sigmoid(learned_bg)}")
                    bs_model.B_inf = torch.nn.Parameter(torch.clone(learned_bg.data).reshape(3, 1, 1)).cuda()
                    bs_optimizer = torch.optim.Adam(bs_model.parameters(), lr=opt_params.bs_at_lr)
                    done_binf_init_with_bg = True
            else:
                bg_image = torch.sigmoid(learned_bg).reshape(3, 1, 1) * (1 - image_alpha)
                bgdetached_image = torch.sigmoid(learned_bg.detach()).reshape(3, 1, 1) * (1 - image_alpha)
                image = rendered_image + bg_image
        else:
            image = rendered_image

        depth_image = render_depth_pkg["depth"]
        # CD-12: the per-frame depth normalisation constants. Recorded because
        # beta is only identifiable relative to them, so any change in the
        # primitive population rescales the medium model's only spatial input.
        depth_norm_min = None
        depth_norm_max = None
        if opt_params.filter_depth:
            depth_image = depth_image / image_alpha
            if torch.any(torch.logical_or(torch.isnan(depth_image), torch.isinf(depth_image))):
                valid_depth_vals = depth_image[torch.logical_not(torch.logical_or(torch.isnan(depth_image), torch.isinf(depth_image)))]
                if len(valid_depth_vals) == 0:
                    print(f"[training] everything is nan")
                    not_nan_max = 100.0
                else:
                    not_nan_max = torch.max(valid_depth_vals).item()
                depth_image = torch.nan_to_num(depth_image, not_nan_max, not_nan_max)
            depth_image = depth_image / opt_params.normalize_depth
            if opt_params.norm_depth_max:
                # Capture the constants BEFORE applying them: afterwards they
                # are 0 and 1 by construction and carry no information.
                depth_norm_min = depth_image.min().item()
                depth_norm_max = depth_image.max().item()
                if depth_image.min() != depth_image.max():
                    depth_image = (depth_image - depth_image.min()) / (depth_image.max() - depth_image.min())
                else:
                    depth_image = depth_image / depth_image.max()

        if opt_params.use_gt_depth:
            assert viewpoint_cam.original_depth_image is not None
            depth_image = viewpoint_cam.original_depth_image.cuda()

        '''
        deep see color
        '''
        if opt_params.do_seathru and iteration > opt_params.seathru_from_iter:
            image_batch = torch.unsqueeze(image, dim=0)
            depth_image_batch = torch.unsqueeze(depth_image, dim=0)

            # estimate attenuation
            if opt_params.disable_attenuation:
                direct = image_batch
            else:
                attenuation_map = at_model(depth_image_batch)
                attenuation_map_depth_detached = at_model(depth_image_batch.detach())
                direct = image_batch * attenuation_map

            # z score
            if opt_params.do_z_score:
                direct_mean = direct.mean(dim=[2, 3], keepdim=True)
                direct_std = direct.std(dim=[2, 3], keepdim=True)
                direct_z = (direct - direct_mean) / direct_std
                clamped_z = torch.clamp(direct_z, -3, 3)
                direct_filtered = torch.clamp(
                    (clamped_z * direct_std) + torch.maximum(direct_mean, torch.Tensor([1. / 255]).cuda()), 0, 1)
                direct = direct_filtered

            # estimate backscatter
            backscatter = bs_model(depth_image_batch)
            backscatter_depth_detached = bs_model(depth_image_batch.detach())

            # combined image
            underwater_image = torch.clamp(direct + backscatter, 0.0, 1.0)

        # gaussian splating loss
        gt_image = viewpoint_cam.original_image.cuda()
        if iteration > opt_params.seathru_from_iter and opt_params.do_seathru:
            if opt_params.use_depth_weighted_l1:
                Ll1 = depth_weighted_l1_loss(underwater_image, gt_image, depth_image.detach())
            elif opt_params.use_depth_weighted_l2:
                Ll1 = depth_weighted_l2_loss(underwater_image, gt_image, depth_image.detach())
            else:
                Ll1 = l1_loss(underwater_image, gt_image)
            l_ssim = ssim(underwater_image, gt_image)
        else:
            if opt_params.use_depth_weighted_l1:
                Ll1 = depth_weighted_l1_loss(image, gt_image, depth_image.detach())
            elif opt_params.use_depth_weighted_l2:
                Ll1 = depth_weighted_l2_loss(image, gt_image, depth_image.detach())
            else:
                Ll1 = l1_loss(image, gt_image)
            l_ssim = ssim(image, gt_image)
        loss = (1.0 - opt_params.lambda_dssim) * Ll1 + opt_params.lambda_dssim * (1.0 - l_ssim)

        # depth weighted l1
        if opt_params.add_recon_depth_l1:
            if iteration > opt_params.seathru_from_iter and opt_params.do_seathru:
                dl1 = depth_weighted_l1_loss(underwater_image, gt_image, depth_image.detach())
            else:
                dl1 = depth_weighted_l1_loss(image, gt_image, depth_image.detach())
            loss += opt_params.dwr_lambda * dl1

        # binary accumulation loss
        if opt_params.use_opacity_prior:
            opacity_prior_loss = mixture_of_laplacians_loss(scene.gaussians.get_opacity)
            loss += opt_params.opacity_prior_lambda * opacity_prior_loss

        # alpha loss
        if opt_params.learn_background:
            alpha_bg_loss = alpha_bg_criterion(rendered_image.detach(), torch.sigmoid(learned_bg.detach()), image_alpha)
            if opt_params.alpha_bg_opacities:
                rgb_colors = SH2RGB(gaussians.get_features).squeeze()
                # alpha_bg_loss = alpha_bg_criterion(rgb_colors.detach(), torch.sigmoid(learned_bg.detach()), gaussians.get_opacity.squeeze())
            if opt_params.do_seathru and iteration > opt_params.seathru_from_iter:
                if opt_params.alpha_binf_uw or opt_params.alpha_binf_render or opt_params.alpha_bg_opacities:
                    if not opt_params.add_bg_binf:
                        alpha_bg_loss = torch.Tensor([0.0]).squeeze().cuda()
                    if opt_params.alpha_binf_uw:
                        alpha_bg_loss += alpha_bg_criterion(underwater_image.squeeze().detach(), torch.sigmoid(bs_model.B_inf.detach()), image_alpha)
                    if opt_params.alpha_bg_uw:
                        alpha_bg_loss += alpha_bg_criterion(underwater_image.squeeze().detach(), torch.sigmoid(bs_model.B_inf.detach()), image_alpha)
                    if opt_params.alpha_binf_render:
                        alpha_bg_loss += alpha_bg_criterion(rendered_image.detach(), torch.sigmoid(bs_model.B_inf.detach()), image_alpha)
                    if opt_params.alpha_bg_opacities:
                        alpha_bg_loss += alpha_bg_criterion(rgb_colors.detach(), torch.sigmoid(bs_model.B_inf.detach()).squeeze(), gaussians.get_opacity.squeeze())
                elif opt_params.bg_from_bs:
                    if opt_params.turn_off_bg_loss:
                        alpha_bg_loss = torch.Tensor([0.0]).squeeze().cuda()
                    else:
                        alpha_bg_loss = alpha_bg_criterion(underwater_image.squeeze().detach(), torch.sigmoid(learned_bg.detach()), image_alpha)
            loss += opt_params.bg_lambda * alpha_bg_loss

        # depth l1 loss
        if opt_params.use_depth_l1_loss:
            gt_depth_image = viewpoint_cam.original_depth_image.cuda()
            depth_l1_loss = l1_loss(depth_image, gt_depth_image)
            loss += 0.1 * depth_l1_loss

        # depth smooth loss
        if opt_params.use_depth_smooth_loss:
            gt_rgb_batch = torch.unsqueeze(gt_image, dim=0)
            depth_image_batch = torch.unsqueeze(depth_image, dim=0)
            depth_smooth_loss = depth_smooth_criterion(gt_rgb_batch, depth_image_batch)
            loss += opt_params.depth_smooth_lambda * depth_smooth_loss # used to be 0.01

        # alpha smooth loss
        if opt_params.use_alpha_smooth_loss:
            gt_rgb_batch = torch.unsqueeze(gt_image, dim=0)
            alpha_image_batch = torch.unsqueeze(image_alpha, dim=0)
            alpha_smooth_loss = depth_smooth_criterion(gt_rgb_batch, alpha_image_batch)
            loss += opt_params.alpha_smooth_lambda * alpha_smooth_loss

        # gray world loss
        if opt_params.use_gw_loss:
            if opt_params.use_render_for_gw:
                image_batch = torch.unsqueeze(rendered_image, dim=0)
            elif opt_params.gw_detach_alpha_bg:
                image_batch = torch.unsqueeze(rendered_image + bgdetached_image, dim=0)
            elif opt_params.gw_reverse_J:
                J = direct.detach() / attenuation_map
                image_batch = J
            else:
                image_batch = torch.unsqueeze(image, dim=0)

            if opt_params.gw_filter_by_alpha != 0.0:
                mask = image_alpha.detach() > opt_params.gw_filter_by_alpha
                image_batch = image_batch[:, :, mask.squeeze()]

            gw_loss = gw_criterion(image_batch)
            if iteration > opt_params.gw_from_iter:
                loss += opt_params.gw_loss_lambda * gw_loss

        # rgb spatial variation loss
        if iteration > opt_params.seathru_from_iter and opt_params.do_seathru:
            if opt_params.use_rgb_sv_loss:
                image_batch = torch.unsqueeze(image, dim=0)
                rgb_sv_loss = rgb_sv_criterion(image_batch.detach(), direct)
                loss += 0.01 * rgb_sv_loss

        # rgb satuation loss
        if iteration > opt_params.seathru_from_iter and opt_params.do_seathru:
            if opt_params.use_rgb_sat_loss:
                image_batch = torch.unsqueeze(image, dim=0)
                rgb_sat_loss = rgb_sat_criterion(image_batch)
                loss += opt_params.sat_loss_lambda * rgb_sat_loss

        # B_inf loss
        if iteration > opt_params.seathru_from_iter and opt_params.do_seathru:
            if opt_params.use_binf_loss:
                image_batch_detached = torch.unsqueeze(image, dim=0).detach()
                binf_loss = bs_model.forward_rgb(image_batch_detached)
                loss += opt_params.binf_loss_lambda * binf_loss

        # deep see color backscatter loss for bs network
        # dark channel prior loss
        if opt_params.use_dcp_loss:
            gt_rgb_batch = torch.unsqueeze(gt_image, dim=0)
            if opt_params.do_seathru and iteration > opt_params.seathru_from_iter:
                # direct_grad_only_through_bsmodel_batch = underwater_image.detach() - backscatter_depth_detached
                direct_reversefromgt_through_bsmodel_batch = gt_rgb_batch.detach() - backscatter_depth_detached
                depth_image_batch = torch.unsqueeze(depth_image, dim=0)
                dcp_loss, _ = dcp_criterion(direct_reversefromgt_through_bsmodel_batch, depth_image_batch.detach())
                loss += opt_params.dcp_loss_lambda * dcp_loss
            else:
                # image_batch = torch.unsqueeze(image, dim=0)
                depth_image_batch = torch.unsqueeze(depth_image, dim=0)
                dcp_loss, _ = dcp_criterion(gt_rgb_batch, depth_image_batch.detach())

        # deep see color attenuation loss for at network
        if opt_params.do_seathru and iteration > opt_params.seathru_from_iter:
            if opt_params.use_dsc_at_loss:
                gt_rgb_batch = torch.unsqueeze(gt_image, dim=0)
                direct_reversefromgt_detached = (gt_rgb_batch - backscatter).detach()
                if opt_params.disable_attenuation:
                    J_through_atmodel = torch.zeros_like(direct_reversefromgt_detached)
                else:
                    J_through_atmodel = direct_reversefromgt_detached / attenuation_map_depth_detached
                dsc_at_loss = dsc_at_criterion(direct_reversefromgt_detached, J_through_atmodel)
                loss += opt_params.dsc_at_lambda * dsc_at_loss

        gaussians.optimizer.zero_grad(set_to_none = True)
        if opt_params.do_seathru and iteration > opt_params.seathru_from_iter:
            bs_optimizer.zero_grad()
            at_optimizer.zero_grad()
        if opt_params.learn_background:
            bg_optimizer.zero_grad()

        loss.backward()

        # CD-12: one unconditional diagnostic row every diag_interval steps.
        # Unconditional matters: upstream printed a primitive count only when
        # something was actually pruned, which makes silence ambiguous between
        # "under budget" and "never ran" -- and that ambiguity is precisely what
        # loses the answer to whether the budget ever bound.
        if diag.due(iteration):
            diag.log(
                iteration=iteration,
                event="periodic",
                n_primitives=gaussians.get_xyz.shape[0],
                alpha_image=image_alpha,
                bs_model=bs_model if opt_params.do_seathru else None,
                at_model=at_model if opt_params.do_seathru else None,
                loss=loss.item(),
                z_min=depth_norm_min,
                z_max=depth_norm_max,
            )

        '''
        periodically update the backscatter and attenuation functions for a given splat
        '''
        if opt_params.do_seathru and iteration > opt_params.seathru_from_iter :
            # ---- CD-6: medium re-identification after a simplification event.
            #
            # This is the central integration decision of the method.  The
            # medium model's only spatial input is a depth map renormalised to
            # [0,1] by its own per-frame min and max, and beta enters the image
            # formation model only through the product beta*Z.  Removing a
            # large fraction of the primitives changes which surfaces are
            # nearest and farthest in each frame, so the normalisation moves and
            # the depth field is rescaled -- which is formally indistinguishable
            # from a change in beta itself.
            #
            # That is SeaSplat's own depth/medium degeneracy, but it does NOT
            # arrive as something the optimizer discovered and is exploiting: it
            # is injected from outside the objective by a scheduled event.  Every
            # mechanism the baseline provides (gradient detachment, alternating
            # optimization, the global-homogeneity assumption) defends against
            # the former case and is silent about the latter.
            #
            # The remedy reuses the baseline's own machinery rather than adding
            # a new device: medium-only steps with the geometry untouched, the
            # same block-coordinate discipline that makes the factorisation
            # tractable in the first place.  Like the existing warm-up, these
            # steps consume no iteration budget -- they are extra optimizer
            # steps, and are reported as such.
            if rewarm_remaining > 0:
                bs_optimizer.step()
                at_optimizer.step()
                rewarm_remaining -= 1
                if rewarm_remaining == 0:
                    print(f"[{iteration}] medium re-identification complete")
                    diag.log(
                        iteration=iteration,
                        event="rewarm_end",
                        n_primitives=gaussians.get_xyz.shape[0],
                        bs_model=bs_model,
                        at_model=at_model,
                        z_min=depth_norm_min,
                        z_max=depth_norm_max,
                        note=f"steps={opt_params.m2_rewarm_steps}",
                    )
                continue

            do_at_bs_update = (not bs_inited and not at_inited) or (iteration % opt_params.update_bs_at_interval == 0)
            if do_at_bs_update:
                update_count = opt_params.update_bs_at_count if bs_inited else 1000
                if bs_update_counter == update_count:
                    bs_update_counter = 0
                    at_update_counter = 0
                    if not bs_inited and not at_inited:
                        print(f"[{iteration}] Backscatter and attenuation init'd")
                        bs_inited = True
                        at_inited = True
                        adjust_gs_colors_for_cc = True
                else:
                    bs_optimizer.step()
                    at_optimizer.step()

                    bs_update_counter += 1
                    at_update_counter += 1
                    bs_update_iter += 1
                    at_update_iter += 1
                    continue

            # adjust gaussian splat colors the first time the color correction models are used
            if adjust_gs_colors_for_cc:
                if update_gs_color_counter == 2000:
                    print(f"[{iteration}] Adjusted gs colors for color correction")
                    adjust_gs_colors_for_cc = False
                else:
                    gaussians.optimizer.step()
                    update_gs_color_counter += 1
                    continue

        iter_end.record()

        with torch.no_grad():
            # Progress bar
            ema_loss_for_log = 0.4 * loss.item() + 0.6 * ema_loss_for_log
            if iteration % 10 == 0:
                progress_bar.set_postfix({"Loss": f"{ema_loss_for_log:.{7}f}"})
                progress_bar.update(10)
            if iteration == opt_params.iterations:
                progress_bar.close()

            # Log and save
            if opt_params.do_seathru and iteration > opt_params.seathru_from_iter:
                training_report(
                    tb_writer, iteration, Ll1, loss, l1_loss, iter_start.elapsed_time(iter_end), testing_iterations, scene, render, (pipe_params, background),
                    learned_bg, opt_params.learn_background,
                    rgb_01_loss, rgb_01_criterion,
                    opt_params.normalize_depth, opt_params.norm_depth_max, depth_l1_loss, opt_params.use_gt_depth,
                    opt_params.do_seathru, opt_params.seathru_from_iter, opt_params.bg_from_bs,
                    None, dsc_at_loss, bs_model, at_model, None, dsc_at_criterion,
                    opt_params.do_z_score, opt_params.filter_depth, opt_params.disable_attenuation,
                    dcp_loss=dcp_loss, dcp_criterion=dcp_criterion,
                    depth_smooth_loss=depth_smooth_loss, depth_smooth_criterion=depth_smooth_criterion, alpha_smooth_loss=alpha_smooth_loss,
                    gw_loss=gw_loss, gw_criterion=gw_criterion,
                    rgb_sv_loss=rgb_sv_loss, rgb_sv_criterion=rgb_sv_criterion,
                    rgb_sat_loss=rgb_sat_loss, rgb_sat_criterion=rgb_sat_criterion,
                    alpha_bg_loss=alpha_bg_loss, alpha_bg_criterion=alpha_bg_criterion,
                    depth_alpha_threshold=opt_params.depth_alpha_threshold,
                    use_render_for_gw=opt_params.use_render_for_gw,
                    binf_loss=binf_loss,
                    opacity_prior_loss=opacity_prior_loss,
                    recon_depth_loss=dl1,
                )
            else:
                training_report(
                    tb_writer, iteration, Ll1, loss, l1_loss, iter_start.elapsed_time(iter_end), testing_iterations, scene, render, (pipe_params, background),
                    learned_bg, opt_params.learn_background,
                    rgb_01_loss, rgb_01_criterion,
                    opt_params.normalize_depth, opt_params.norm_depth_max, depth_l1_loss, opt_params.use_gt_depth,
                    filter_depth=opt_params.filter_depth,
                    dcp_loss=dcp_loss, dcp_criterion=dcp_criterion,
                    depth_smooth_loss=depth_smooth_loss, depth_smooth_criterion=depth_smooth_criterion, alpha_smooth_loss=alpha_smooth_loss,
                    gw_loss=gw_loss, gw_criterion=gw_criterion,
                    rgb_sat_loss=rgb_sat_loss, rgb_sat_criterion=rgb_sat_criterion,
                    alpha_bg_loss=alpha_bg_loss, alpha_bg_criterion=alpha_bg_criterion,
                    depth_alpha_threshold=opt_params.depth_alpha_threshold,
                    use_render_for_gw=opt_params.use_render_for_gw,
                    opacity_prior_loss=opacity_prior_loss,
                    recon_depth_loss=dl1,
                )

            # --- density control --------------------------------------------
            # R-4.  Upstream bundles clone/split, the alpha-prune and the
            # opacity reset into this single gated block, so the obvious
            # one-line `--no_densify` gate silently disables all three.  Under
            # dense initialization only the clone/split must go; the
            # alpha-prune is what *executes* L_op (see prune_only's docstring)
            # and the opacity reset is retained per CD-3.
            #
            # The two upstream branches differed only in the gradient
            # threshold, so they are unified here and the threshold is chosen
            # explicitly.  Behaviour at default settings is unchanged:
            # freeze/unfreeze both default to 9_000_000 and
            # scale_grad_threshold to 1.0.
            if iteration < opt_params.densify_until_iter:
                gs_frozen = (
                    opt_params.freeze_gs_from_iter <= iteration < opt_params.unfreeze_gs_from_iter
                )
                if not gs_frozen:
                    # Keep track of max radii in image-space for pruning
                    gaussians.max_radii2D[visibility_filter] = torch.max(gaussians.max_radii2D[visibility_filter], radii[visibility_filter])
                    gaussians.add_densification_stats(viewspace_point_tensor, visibility_filter)

                    if (
                        iteration % opt_params.densification_interval == 0
                        and iteration > opt_params.densify_from_iter
                    ):
                        size_threshold = 20 if iteration > opt_params.opacity_reset_interval else None
                        if opt_params.m1_dense_init:
                            # Opacity hygiene only: no clone/split, but the
                            # alpha-prune still runs.
                            n_pruned = gaussians.prune_only(
                                0.005, scene.cameras_extent, size_threshold
                            )
                            if diag.due(iteration):
                                diag.log(
                                    iteration=iteration,
                                    event="prune_only",
                                    n_primitives=gaussians.get_xyz.shape[0],
                                    note=f"pruned={n_pruned}",
                                )
                        else:
                            grad_threshold = opt_params.densify_grad_threshold
                            if iteration >= opt_params.unfreeze_gs_from_iter:
                                grad_threshold *= opt_params.scale_grad_threshold
                            gaussians.densify_and_prune(
                                grad_threshold, 0.005, scene.cameras_extent, size_threshold
                            )

                    # CD-3: retained even under dense initialization.  It is a
                    # co-mechanism of L_op against water-column floaters, and
                    # Mini-Splatting's silent removal of it is defensible only
                    # because its depth reinit resets opacity anyway -- a
                    # compensation this configuration does not have.
                    if iteration % opt_params.opacity_reset_interval == 0 or (model_params.white_background and iteration == opt_params.densify_from_iter):
                        print(f"[{iteration}] opacity reset")
                        gaussians.reset_opacity()

                # R-5: EDGS's continuous opacity decay, which pairs with the
                # alpha-prune above into a decay-and-cull -- the smooth
                # analogue of the periodic reset.
                #
                # Gated to stop at seathru_from_iter by default: L_op already
                # pushes opacity down for backscatter-dominated primitives, and
                # neither source method faced that combination, so stacking the
                # two risks over-pruning.  The gate is a config value rather
                # than a constant precisely so the choice is recorded in the
                # manifest and can be ablated.
                if (
                    opt_params.m1_dense_init
                    and opt_params.m1_reduce_opacity
                    and iteration % opt_params.m1_reduce_opacity_interval == 0
                    and not (
                        opt_params.m1_decay_stops_at_seathru
                        and iteration >= opt_params.seathru_from_iter
                    )
                ):
                    gaussians.reduce_opacity_step(opt_params.m1_reduce_opacity_factor)

            # --- M2: simplification to the primitive budget -----------------
            if opt_params.m2_simplify and iteration in (
                opt_params.simp_iteration1,
                opt_params.simp_iteration2,
            ):
                n_before = gaussians.get_xyz.shape[0]
                # Captured before the event: this row and the post_simp row
                # together are the direct test of whether primitive reduction
                # rescales the medium model's input (CD-12).
                diag.log(
                    iteration=iteration,
                    event="pre_simp",
                    n_primitives=n_before,
                    bs_model=bs_model if opt_params.do_seathru else None,
                    at_model=at_model if opt_params.do_seathru else None,
                    z_min=depth_norm_min,
                    z_max=depth_norm_max,
                )

                importance, _ = accumulate_importance(
                    gaussians,
                    scene.getTrainCameras(),
                    render,
                    pipe_params,
                    bg,
                    metric=opt_params.imp_metric,
                )

                if iteration == opt_params.simp_iteration1:
                    keep = sample_to_budget(importance, opt_params.n_bud)
                    how = f"stochastic sampling to budget {opt_params.n_bud}"
                else:
                    keep = cdf_keep_mask(importance, opt_params.cdf_thres)
                    how = f"cdf prune at {opt_params.cdf_thres}"

                gaussians.prune_points(~keep)

                # The QAT x simplification conflict.  This does not exist for
                # post-hoc quantization and is created by choosing the
                # quantization-aware formulation: the assignment vector is
                # per-primitive, so pruning silently desynchronises it from the
                # model.  Index-select it alongside everything else, then force
                # a full reassignment -- a prune is not parameter drift, so
                # waiting up to `kmeans_freq` steps would leave the model
                # rendering from a partition fitted to primitives that no
                # longer exist.
                if opt_params.m3_quantize:
                    attr_quantizer.prune(keep)
                    attr_quantizer.invalidate()

                torch.cuda.empty_cache()
                n_after = gaussians.get_xyz.shape[0]

                if iteration == opt_params.simp_iteration1:
                    budget_bound = n_before > opt_params.n_bud
                    note = f"{how}; before={n_before}; budget_bound={budget_bound}"
                    if not budget_bound:
                        # G-2.  A non-binding budget makes this cell equivalent
                        # to running without M2, which silently collapses A4
                        # onto A1 and A7 onto A5.  A null interaction measured
                        # in that state is a configuration artifact, not a
                        # finding, so it is called out loudly rather than left
                        # for the analysis to discover.
                        print(
                            f"[{iteration}] *** WARNING: budget did NOT bind "
                            f"({n_before} <= n_bud={opt_params.n_bud}). This run is "
                            f"equivalent to one without M2; treat any interaction "
                            f"result from it as a configuration artifact. ***"
                        )
                else:
                    note = f"{how}; before={n_before}"

                print(f"[{iteration}] M2 {how}: {n_before} -> {n_after}")
                diag.log(
                    iteration=iteration,
                    event="post_simp",
                    n_primitives=n_after,
                    bs_model=bs_model if opt_params.do_seathru else None,
                    at_model=at_model if opt_params.do_seathru else None,
                    note=note,
                )

                # CD-6: owe the medium model its re-identification steps.
                if opt_params.do_seathru and iteration > opt_params.seathru_from_iter:
                    rewarm_remaining = opt_params.m2_rewarm_steps


            # Optimizer step
            if iteration < opt_params.iterations:
                gaussians.optimizer.step()
                if opt_params.learn_background:
                    bg_optimizer.step()

            if (iteration in saving_iterations):
                print(f"\n[ITER {iteration}] Saving Gaussians")
                scene.save(iteration)

                # Model size, measured rather than asserted.  Written for EVERY
                # cell, not only the quantized ones: a compression ratio is only
                # meaningful against an artifact produced the same way, so the
                # unquantized cells need one too.  The .ply saved above is for
                # rendering and inspection; this is the shippable artifact and
                # the thing the reported size refers to.
                quant_active = (
                    opt_params.m3_quantize
                    and iteration > opt_params.kmeans_st_iter
                )
                artifact = write_compressed_model(
                    Path(model_params.model_path) / f"compressed_{iteration}",
                    gaussians,
                    attr_quantizer if quant_active else None,
                    bs_model=bs_model if opt_params.do_seathru else None,
                    at_model=at_model if opt_params.do_seathru else None,
                    learned_bg=learned_bg if opt_params.learn_background else None,
                )
                size_report = measure_model_size(artifact)
                with open(artifact / "model_size.json", "w", encoding="utf-8") as fh:
                    json.dump(size_report, fh, indent=2)

                print(
                    f"[ITER {iteration}] model size: {size_report['total_mb']:.3f} MB "
                    f"({size_report['bytes_per_primitive']:.2f} B/primitive, "
                    f"{size_report['num_primitives']} primitives)"
                )
                if quant_active:
                    print(
                        f"[ITER {iteration}] ratio {size_report['ratio_vs_this_baseline']:.2f}x "
                        f"vs this baseline's 14 floats/primitive -- NOT comparable "
                        f"with published ratios against 59"
                    )
                    # A gap here means the encoder is spending bits the analysis
                    # does not know about.
                    over = size_report.get("measured_over_analytical")
                    if over and over > 1.10:
                        print(
                            f"[ITER {iteration}] NOTE: measured size is {over:.2f}x the "
                            f"analytical count; the difference is container overhead "
                            f"and should be reported, not silently dropped."
                        )
            if (iteration in checkpoint_iterations):
                print(f"\n[ITER {iteration}] Saving Checkpoint in {scene.model_path}")
                torch.save((gaussians.capture(), iteration), scene.model_path + "/chkpnt" + str(iteration) + ".pth")
                if opt_params.do_seathru:
                    torch.save(bs_model.state_dict(), f"{scene.model_path}/backscatter_{iteration}.pth")
                    torch.save(at_model.state_dict(), f"{scene.model_path}/attenuate_{iteration}.pth")
                if opt_params.learn_background:
                    torch.save(learned_bg, f"{scene.model_path}/bg_{iteration}.pth")

        iteration += 1

    '''
    post training save images
    '''
    print(f"Rendering images for eval")
    if opt_params.do_seathru:
        at_model.eval()
        bs_model.eval()
    else:
        bs_model = None
        at_model = None

    skip_eval_train = False
    if 'metashape' in str(model_params.model_path):
        skip_eval_train = True

    train_image_dir = Path(model_params.model_path) / "train" / f"{'with_water' if opt_params.do_seathru else 'render'}"
    gt_dir = Path(model_params.source_path) / model_params.images
    png_images = glob.glob(f"{gt_dir}/*.png")
    use_jpeg = len(png_images) == 0

    if opt_params.bg_from_bs:
        learned_bg = None

    if not skip_eval_train:
        metrics_dirs = [train_image_dir]
        with torch.no_grad():
            render_set(
                Path(model_params.model_path), "train", iteration, scene.getTrainCameras(), gaussians, pipe_params, background,
                opt_params.do_seathru,
                False,
                False,
                learned_bg,
                bs_model,
                at_model,
                save_as_jpeg=use_jpeg,
            )
    else:
        metrics_dirs = []

    if model_params.eval:
        test_image_dir = Path(model_params.model_path) / "test" / f"{'with_water' if opt_params.do_seathru else 'render'}"
        with torch.no_grad():
            render_set(
                Path(model_params.model_path), "test", iteration, scene.getTestCameras(), gaussians, pipe_params, background,
                opt_params.do_seathru,
                False,
                False,
                learned_bg,
                bs_model,
                at_model,
                save_as_jpeg=use_jpeg,
            )
        metrics_dirs.append(test_image_dir)

    '''
    eval images
    '''
    print("Running metrics")
    from utils.metrics_conventions import (
        aggregate_images,
        convention_note,
        evaluate_pair,
    )

    # The container choice is silent upstream: the harness writes JPEG whenever
    # the ground-truth directory holds no PNGs, which quietly changes every
    # reported number. The local corpus is PNG, so this should read "png" --
    # logged rather than assumed.
    container = "jpeg" if use_jpeg else "png"
    lpips_net = "vgg"
    print(f"[eval] container={container}  lpips_backbone={lpips_net}  "
          f"masking=none  psnr=both conventions")

    results = {
        "container": container,
        "lpips_backbone": lpips_net,
        "masking": "none",
        "conventions": convention_note(lpips_net, container),
        "cost": {
            # Both, always.  A figure reported only in iterations is not
            # comparable with one reported in steps, and the two differ by
            # roughly 40% here.
            "iterations": int(opt_params.iterations),
            "effective_optimizer_steps": int(effective_steps),
            "train_wall_seconds": round(time.time() - training_started_at, 1),
            # The realised count, never the target budget: the survival draw is
            # stochastic and driven by device-computed probabilities, so it
            # varies run to run even at a fixed seed.
            "n_primitives_final": int(gaussians.get_xyz.shape[0]),
        },
    }
    chunk_size = 128
    for eval_idx, image_dir in enumerate(metrics_dirs):
        records = []

        fname_list = os.listdir(image_dir)
        for i in tqdm(range(0, len(fname_list), chunk_size)):
            upper =  min(i + chunk_size, len(fname_list))
            fnames = fname_list[i : upper]

            renders, gts, image_name = readImages(image_dir, gt_dir, fnames)

            for idx in range(len(renders)):
                rec = evaluate_pair(
                    renders[idx], gts[idx], ssim, lpips, lpips_net=lpips_net
                )
                rec["image"] = image_name[idx]
                records.append(rec)

        agg = aggregate_images(records)
        key = 'Train' if eval_idx == 0 else 'Test'

        print(f"-----------{key}  (n={agg['n_images']})")
        print("  SSIM  ^: {:>12.7f}".format(agg["ssim"]))
        print("  PSNR  ^: {:>12.7f}  (pooled -- the standard definition)".format(
            agg["psnr_pooled"]))
        print("  PSNR  ^: {:>12.7f}  (per-channel -- SeaSplat's convention)".format(
            agg["psnr_per_channel"]))
        print("  LPIPS v: {:>12.7f}  ({})".format(agg["lpips"], lpips_net))
        print("")

        results[key] = {
            **agg,
            # Legacy key names. "PSNR" maps to the POOLED figure because that
            # is what the upstream code actually computed here: readImages
            # returns (1,3,H,W), so image_utils.psnr's view(shape[0], -1)
            # collapsed to a single row and pooled the channels. The alias
            # preserves the historical meaning rather than the historical name.
            "SSIM": agg["ssim"],
            "PSNR": agg["psnr_pooled"],
            "LPIPS": agg["lpips"],
            "per_image": records,
        }

    results_file = Path(model_params.model_path) / "eval_metrics.json"
    with open(str(results_file), 'w') as f:
        json.dump(results, f, indent=2)


def prepare_output_and_logger(args):
    if not args.model_path:
        if os.getenv('OAR_JOB_ID'):
            unique_str=os.getenv('OAR_JOB_ID')
        else:
            unique_str = str(uuid.uuid4())
        args.model_path = os.path.join("./output/", unique_str[0:10])

    # Set up output folder
    print("Output folder: {}".format(args.model_path))
    os.makedirs(args.model_path, exist_ok = True)
    with open(os.path.join(args.model_path, "cfg_args"), 'w') as cfg_log_f:
        cfg_log_f.write(str(Namespace(**vars(args))))

    # Create Tensorboard writer
    tb_writer = None
    if TENSORBOARD_FOUND:
        tb_writer = SummaryWriter(args.model_path)
    else:
        print("Tensorboard not available: not logging progress")
    return tb_writer

def training_report(tb_writer, iteration, Ll1, loss, l1_loss, elapsed, testing_iterations, scene : Scene, renderFunc, renderArgs,
                    learned_bg, do_learn_bg,
                    rgb_01_loss, rgb_01_criterion,
                    depth_norm_value=1.0, norm_depth_max=False, depth_l1_loss=None, use_gt_depth=False,
                    do_seathru=False, seathru_from_iter=9999999999, bg_from_bs=False,
                    bs_loss=None, at_loss=None, bs_model=None, at_model=None, bs_criterion=None, at_criterion=None,
                    do_z_score=False, filter_depth=False, disable_attenuation=False,
                    dcp_loss=None, dcp_criterion=None,
                    depth_smooth_loss=None, depth_smooth_criterion=None, alpha_smooth_loss=None,
                    gw_loss=None, gw_criterion=None,
                    rgb_sv_loss=None, rgb_sv_criterion=None,
                    rgb_sat_loss=None, rgb_sat_criterion=None,
                    alpha_bg_loss=None, alpha_bg_criterion=None,
                    depth_alpha_threshold=0.0,
                    use_render_for_gw=False,
                    binf_loss=None,
                    opacity_prior_loss=None,
                    recon_depth_loss=None

):
    if tb_writer:
        # if bs_loss is not None:
        #     tb_writer.add_scalar('train_losses/bs_loss', bs_loss.item(), iteration)
        if at_loss is not None:
            tb_writer.add_scalar('train_losses/at_loss', at_loss.item(), iteration)
        tb_writer.add_scalar('train_losses/l1_loss', Ll1.item(), iteration)
        tb_writer.add_scalar('train_losses/rgb_01_loss', rgb_01_loss.item(), iteration)
        tb_writer.add_scalar('train_losses/depth_l1_loss', depth_l1_loss.item(), iteration)
        tb_writer.add_scalar('train_losses/depth_smooth_loss', depth_smooth_loss.item(), iteration)
        tb_writer.add_scalar('train_losses/alpha_smooth_loss', alpha_smooth_loss.item(), iteration)
        tb_writer.add_scalar('train_losses/dcp_loss', dcp_loss.item(), iteration)
        tb_writer.add_scalar('train_losses/gw_loss', gw_loss.item(), iteration)
        tb_writer.add_scalar('train_losses/alpha_bg_loss', alpha_bg_loss.item(), iteration)
        tb_writer.add_scalar('train_losses/recon_depth_loss', recon_depth_loss.item(), iteration)
        if binf_loss is not None:
            tb_writer.add_scalar('train_losses/binf_loss', binf_loss.item(), iteration)
        if rgb_sv_loss is not None:
            tb_writer.add_scalar('train_losses/rgb_sv_loss', rgb_sv_loss.item(), iteration)
        if rgb_sat_loss is not None:
            tb_writer.add_scalar('train_losses/rgb_sat_loss', rgb_sat_loss.item(), iteration)
        if opacity_prior_loss is not None:
            tb_writer.add_scalar('train_losses/opacity_prior_loss', opacity_prior_loss.item(), iteration)
        tb_writer.add_scalar('train_losses/total_loss', loss.item(), iteration)
        tb_writer.add_scalar('iter_time', elapsed, iteration)
        if do_learn_bg:
            tb_writer.add_scalar(f"background/r", torch.sigmoid(learned_bg)[0].item(), global_step=iteration)
            tb_writer.add_scalar(f"background/g", torch.sigmoid(learned_bg)[1].item(), global_step=iteration)
            tb_writer.add_scalar(f"background/b", torch.sigmoid(learned_bg)[2].item(), global_step=iteration)
            if iteration % 100 == 0:
                tb_writer.add_images(f"background/image", torch.sigmoid(learned_bg).reshape(1, 3, 1, 1), global_step=iteration)
        if bs_model is not None:
            for idx, val in enumerate(bs_model.B_inf):
                tb_writer.add_scalar(f'bs_model/B_inf_{idx}', torch.sigmoid(val).item(), iteration)
            if iteration % 100 == 0:
                tb_writer.add_images(f"bs_model/B_inf", torch.sigmoid(bs_model.B_inf).reshape(1, 3, 1, 1), global_step=iteration)
            for idx, val in enumerate(bs_model.backscatter_conv_params):
                if bs_model.do_sigmoid:
                    tb_writer.add_scalar(f'bs_model/backscatter_conv_{idx}', torch.sigmoid(val).item(), iteration)
                else:
                    tb_writer.add_scalar(f'bs_model/backscatter_conv_{idx}', val.item(), iteration)
            if bs_model.use_residual:
                for idx, val in enumerate(bs_model.J_prime):
                    tb_writer.add_scalar(f'bs_model/J_prime_{idx}', torch.sigmoid(val).item(), iteration)
                for idx, val in enumerate(bs_model.residual_conv_params):
                    tb_writer.add_scalar(f'bs_model/residual_conv_{idx}', torch.sigmoid(val).item(), iteration)
                if iteration % 100 == 0:
                    tb_writer.add_images(f"bs_model/J_prime", torch.sigmoid(bs_model.J_prime).reshape(1, 3, 1, 1), global_step=iteration)
        if at_model is not None:
            if type(at_model) is not AttenuateNetV3:
                for idx, val in enumerate(at_model.attenuation_coef):
                    if at_model.do_sigmoid:
                        tb_writer.add_scalar(f'at_model/attenuation_coeff_{idx}', torch.sigmoid(val).item(), iteration)
                    else:
                        tb_writer.add_scalar(f'at_model/attenuation_coeff_{idx}', val.item(), iteration)
            for idx, val in enumerate(at_model.attenuation_conv_params):
                if at_model.do_sigmoid:
                    tb_writer.add_scalar(f'at_model/attenuation_conv_{idx}', torch.sigmoid(val).item(), iteration)
                else:
                    tb_writer.add_scalar(f'at_model/attenuation_conv_{idx}', val.item(), iteration)


    # Report test and samples of training set
    if iteration in testing_iterations:
        torch.cuda.empty_cache()
        assert not torch.is_grad_enabled()
        validation_configs = ({'name': 'eval_test', 'cameras' : scene.getTestCameras()},
                              {'name': 'eval_train', 'cameras' : [scene.getTrainCameras()[idx % len(scene.getTrainCameras())] for idx in range(5, 51, 5)]})

        for config in validation_configs:
            if config['cameras'] and len(config['cameras']) > 0:
                l1_test = 0.0
                psnr_test = 0.0
                dsc_at_test = 0.0
                rgb_01_test = 0.0
                depth_l1_test = 0.0
                depth_smooth_test = 0.0
                alpha_smooth_test = 0.0
                dcp_test = 0.0
                gw_test = 0.0
                rgb_sv_test = 0.0
                rgb_sat_test = 0.0
                alpha_bg_test = 0.0
                binf_test = 0.0
                for idx, viewpoint in enumerate(config['cameras']):
                    render_pkg = renderFunc(viewpoint, scene.gaussians, *renderArgs)
                    render_depth_pkg = render_depth(viewpoint, scene.gaussians, *renderArgs)

                    rendered_image = render_pkg["render"]
                    # CD-13: alpha comes from the depth/alpha probe pass.
                    image_alpha = render_depth_pkg["alpha"]
                    depth_image = render_depth_pkg["depth"]

                    if filter_depth:
                        depth_image = depth_image / image_alpha
                        if torch.any(torch.logical_or(torch.isnan(depth_image), torch.isinf(depth_image))):
                            valid_depth_vals = depth_image[torch.logical_not(torch.logical_or(torch.isnan(depth_image), torch.isinf(depth_image)))]
                            if len(valid_depth_vals) == 0:
                                print(f"[eval] everything is nan")
                                not_nan_max = 100.0
                            else:
                                not_nan_max = torch.max(valid_depth_vals).item()
                            depth_image = torch.nan_to_num(depth_image, not_nan_max, not_nan_max)
                        depth_image = depth_image / depth_norm_value
                        if norm_depth_max:
                            if depth_image.min() != depth_image.max():
                                depth_image = (depth_image - depth_image.min()) / (depth_image.max() - depth_image.min())
                            else:
                                depth_image = depth_image / depth_image.max()

                        depth_mask = image_alpha.detach() > depth_alpha_threshold
                        masked_depth_image = depth_image * depth_mask
                        normalized_masked_depth_image = torch.clamp(masked_depth_image / torch.max(masked_depth_image), 0.0, 1.0)

                    if do_learn_bg:
                        if bg_from_bs and do_seathru and iteration > seathru_from_iter:
                            bg_image = torch.zeros_like(rendered_image) * 1.0
                            image = rendered_image
                        else:
                            bg_image = torch.sigmoid(learned_bg).reshape(3, 1, 1) * (1 - image_alpha)
                            image = rendered_image + bg_image
                        clamped_bg_image = torch.clamp(bg_image, 0.0, 1.0)
                    else:
                        image = rendered_image

                    normalized_depth_image = torch.clamp(depth_image / torch.max(depth_image), 0.0, 1.0)
                    clamped_raw_render_image = torch.clamp(rendered_image, 0.0, 1.0)
                    clamped_rgb_image = torch.clamp(image, 0.0, 1.0)

                    # implement the forward process here
                    if bs_model is not None and at_model is not None:
                        if use_gt_depth:
                            assert viewpoint.original_depth_image is not None
                            depth_image = viewpoint.original_depth_image.cuda()
                        depth_batch = torch.unsqueeze(depth_image, dim=0)
                        rgb_batch = torch.unsqueeze(image, dim=0)
                        if disable_attenuation:
                            attenuation_map = torch.ones_like(rgb_batch)
                        else:
                            attenuation_map = at_model(depth_batch)
                        direct = rgb_batch * attenuation_map
                        attenuation_map_normalized = attenuation_map / torch.max(attenuation_map)

                        if do_z_score:
                            direct_mean = direct.mean(dim=[2, 3], keepdim=True)
                            direct_std = direct.std(dim=[2, 3], keepdim=True)
                            direct_z = (direct - direct_mean) / direct_std
                            clamped_z = torch.clamp(direct_z, -5, 5)
                            direct_filtered = torch.clamp(
                                (clamped_z * direct_std) + torch.maximum(direct_mean, torch.Tensor([1. / 255]).cuda()), 0, 1)
                            direct = direct_filtered

                        backscatter = bs_model(depth_batch)
                        normalized_bs = backscatter / torch.max(backscatter)
                        underwater_image = torch.clamp(direct + backscatter, 0.0, 1.0)

                    # get the groundtruth rgb image
                    gt_image = torch.clamp(viewpoint.original_image.to("cuda"), 0.0, 1.0)
                    if viewpoint.original_depth_image is not None:
                        gt_depth_image = viewpoint.original_depth_image.to("cuda")
                        gt_normalized_depth_image = torch.clamp(gt_depth_image / torch.max(gt_depth_image), 0.0, 1.0)

                    # deepseecolor at loss
                    if at_criterion is not None:
                        reverse_direct = underwater_image - backscatter
                        if not disable_attenuation:
                            J = reverse_direct / attenuation_map
                        else:
                            J = torch.zeros_like(reverse_direct)
                        dsc_at_loss = at_criterion(reverse_direct, J)

                    # rgb [0, 1] loss
                    rgb_01_loss = rgb_01_criterion(image)

                    # alpha bg loss
                    alpha_bg_loss = 0.0
                    # if do_learn_bg:
                    #     alpha_bg_loss = alpha_bg_criterion(rendered_image.detach(), torch.sigmoid(learned_bg.detach()), image_alpha)
                    #     if do_seathru and iteration > seathru_from_iter:
                    #         alpha_bg_loss += alpha_bg_criterion(rendered_image.detach(), torch.sigmoid(bs_model.B_inf.detach().clone()), image_alpha)

                    '''
                    losses
                    '''
                    depth_batch = torch.unsqueeze(depth_image, dim=0)
                    rgb_batch = torch.unsqueeze(image, dim=0)
                    gt_rgb_batch = torch.unsqueeze(gt_image, dim=0)
                    alpha_batch = torch.unsqueeze(image_alpha, dim=0)

                    # dcp
                    if do_seathru and iteration > seathru_from_iter:
                        reverse_direct = underwater_image - backscatter
                        dcp_loss, dcp_image = dcp_criterion(reverse_direct, depth_batch)
                    else:
                        dcp_loss, dcp_image = dcp_criterion(rgb_batch, depth_batch)

                    # smooth depth criterion
                    depth_smooth_loss = depth_smooth_criterion(gt_rgb_batch, depth_batch)

                    # smooth alpha
                    alpha_smooth_loss = depth_smooth_criterion(gt_rgb_batch, alpha_batch)

                    # gw criterion
                    if use_render_for_gw:
                        gw_loss = gw_criterion(rendered_image.unsqueeze(0))
                    else:
                        gw_loss = gw_criterion(rgb_batch)

                    # rgb sv and sat criterion
                    if bs_model is not None and at_model is not None:
                        rgb_sv_loss = rgb_sv_criterion(rgb_batch, direct)
                        rgb_sat_loss = rgb_sat_criterion(direct + backscatter)

                    # B_inf loss
                    binf_loss = 0.0

                    if tb_writer and (idx < 5):
                        tag_header = config['name'] + "_view_{}".format(viewpoint.image_name)
                        tb_writer.add_images(f"{tag_header}/render", clamped_raw_render_image[None], global_step=iteration)
                        tb_writer.add_images(f"{tag_header}/depth_render", normalized_depth_image[None], global_step=iteration)
                        # tb_writer.add_images(f"{tag_header}/dcp_image", dcp_image, global_step=iteration)
                        tb_writer.add_images(f"{tag_header}/alpha_image", image_alpha[None], global_step=iteration)
                        # if filter_depth:
                        #     tb_writer.add_images(f"{tag_header}/depth_mask", depth_mask[None], global_step=iteration)
                        if do_learn_bg:
                            tb_writer.add_images(f"{tag_header}/bg_image", clamped_bg_image[None], global_step=iteration)
                            tb_writer.add_images(f"{tag_header}/render (with bg)", clamped_rgb_image[None], global_step=iteration)
                            tb_writer.add_histogram(f"{tag_header}/depth_histogram", depth_image, global_step=iteration)
                            tb_writer.add_histogram(f"{tag_header}/alpha_histogram", image_alpha, global_step=iteration)
                        if bs_model is not None and at_model is not None:
                            tb_writer.add_images(f"{tag_header}/backscatter_image", torch.clamp(backscatter, 0.0, 1.0), global_step=iteration)
                            tb_writer.add_images(f"{tag_header}/backscatter_image_normalized", torch.clamp(normalized_bs, 0.0, 1.0), global_step=iteration)
                            tb_writer.add_images(f"{tag_header}/attenuation_map", torch.clamp(attenuation_map, 0.0, 1.0), global_step=iteration)
                            tb_writer.add_images(f"{tag_header}/attenuation_map_normalized", torch.clamp(attenuation_map_normalized, 0.0, 1.0), global_step=iteration)
                            tb_writer.add_images(f"{tag_header}/attenuated_image", direct, global_step=iteration)
                            tb_writer.add_images(f"{tag_header}/underwater_image", underwater_image, global_step=iteration)
                        if iteration == testing_iterations[0]:
                            tb_writer.add_images(f"{tag_header}/ground_truth", gt_image[None], global_step=iteration)
                            if viewpoint.original_depth_image is not None:
                                tb_writer.add_images(f"{tag_header}/gt_depth_image", gt_normalized_depth_image[None], global_step=iteration)
                                # tb_writer.add_histogram(f"{tag_header}/gt_depth_histogram", gt_depth_image, global_step=iteration)

                    if bs_model is not None and at_model is not None:
                        l1_test += l1_loss(underwater_image.squeeze(), gt_image).mean().double()
                        psnr_test += psnr(underwater_image.squeeze(), gt_image).mean().double()
                        rgb_sv_test += rgb_sv_loss
                        rgb_sat_test += rgb_sat_loss
                    else:
                        l1_test += l1_loss(image, gt_image).mean().double()
                        psnr_test += psnr(image, gt_image).mean().double()
                    if viewpoint.original_depth_image is not None:
                        depth_l1_test += l1_loss(depth_image, gt_depth_image)
                    rgb_01_test += rgb_01_loss
                    dcp_test += dcp_loss
                    depth_smooth_test += depth_smooth_loss
                    alpha_smooth_test += alpha_smooth_loss
                    gw_test += gw_loss
                    binf_test += binf_loss
                    if do_learn_bg:
                        alpha_bg_test += alpha_bg_loss
                    if at_criterion is not None:
                        dsc_at_test += dsc_at_loss

                l1_test /= len(config['cameras'])
                psnr_test /= len(config['cameras'])
                rgb_01_test /= len(config['cameras'])
                dcp_test /= len(config['cameras'])
                depth_smooth_test /= len(config['cameras'])
                alpha_smooth_test /= len(config['cameras'])
                gw_test /= len(config['cameras'])
                binf_test /= len(config['cameras'])
                if viewpoint.original_depth_image is not None:
                    depth_l1_test /= len(config['cameras'])
                if bs_model is not None and at_model is not None:
                    rgb_sv_test /= len(config['cameras'])
                    rgb_sat_test /= len(config['cameras'])
                if do_learn_bg:
                    alpha_bg_test /= len(config['cameras'])
                if at_criterion is not None:
                    dsc_at_test /= len(config['cameras'])

                # write loss stats to tensorboard
                if tb_writer:
                    tb_writer.add_scalar(config['name'] + '/loss_viewpoint - l1_loss', l1_test, iteration)
                    tb_writer.add_scalar(config['name'] + '/loss_viewpoint - psnr', psnr_test, iteration)
                    tb_writer.add_scalar(config['name'] + '/loss_viewpoint - rgb_01_loss', rgb_01_test, iteration)
                    tb_writer.add_scalar(config['name'] + '/loss_viewpoint - dcp_loss', dcp_test, iteration)
                    tb_writer.add_scalar(config['name'] + '/loss_viewpoint - depth_smooth_loss', depth_smooth_test, iteration)
                    tb_writer.add_scalar(config['name'] + '/loss_viewpoint - alpha_smooth_test', alpha_smooth_test, iteration)
                    tb_writer.add_scalar(config['name'] + '/loss_viewpoint - gw_loss', gw_test, iteration)
                    tb_writer.add_scalar(config['name'] + '/loss_viewpoint - binf_loss', binf_test, iteration)
                    if viewpoint.original_depth_image is not None:
                        tb_writer.add_scalar(config['name'] + '/loss_viewpoint - depth_l1_loss', depth_l1_test, iteration)
                    if bs_model is not None and at_model is not None:
                        tb_writer.add_scalar(config['name'] + '/loss_viewpoint - rgb_sv_loss', rgb_sv_test, iteration)
                        tb_writer.add_scalar(config['name'] + '/loss_viewpoint - rgb_sat_loss', rgb_sat_test, iteration)
                    if do_learn_bg:
                        tb_writer.add_scalar(config['name'] + '/loss_viewpoint - alpha_bg_loss', alpha_bg_test, iteration)
                    if at_criterion is not None:
                        tb_writer.add_scalar(config['name'] + '/loss_viewpoint - dsc_at_loss', dsc_at_test, iteration)

        if tb_writer:
            tb_writer.add_histogram("scene/opacity_histogram", scene.gaussians.get_opacity, iteration)
            tb_writer.add_scalar('total_points', scene.gaussians.get_xyz.shape[0], iteration)
        torch.cuda.empty_cache()

if __name__ == "__main__":
    # Set up command line argument parser
    parser = ArgumentParser(description="Training script parameters")
    lp = ModelParams(parser)
    op = OptimizationParams(parser)
    pp = PipelineParams(parser)
    parser.add_argument('--ip', type=str, default="127.0.0.1")
    parser.add_argument('--port', type=int, default=6009)
    parser.add_argument('--debug_from', type=int, default=-1)
    parser.add_argument('--detect_anomaly', action='store_true', default=False)
    parser.add_argument("--test_iterations", nargs="+", type=int, default=[i for i in range(0, 60_000, 1000)])
    parser.add_argument("--save_iterations", nargs="+", type=int, default=[1_000, 7_000, 15_000, 30_000, 40_000, 50_000, 60_000])
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument("--checkpoint_iterations", nargs="+", type=int, default=[1_000, 7_000, 15_000, 30_000, 40_000])
    parser.add_argument("--start_checkpoint", type=str, default = None)
    parser.add_argument("--exp", type=str, default = "test")
    parser.add_argument("--seed", type=int, default = -1)
    add_cell_argument(parser)

    # CD-1: fold the selected cell into the parser DEFAULTS before parsing, so
    # that explicit command-line arguments still override it.  Doing it this
    # way means argparse's own precedence gives us
    #     code defaults < cell file < command line
    # without a second parse or any "was this actually passed?" sentinel logic.
    cell_name, cell_values = apply_cell_config(parser)

    args = parser.parse_args(sys.argv[1:])
    args.test_iterations.insert(0, 1)
    args.save_iterations.append(args.iterations)
    args.test_iterations.append(args.iterations)
    args.checkpoint_iterations.append(args.iterations)

    now = datetime.now()
    today = now.strftime("%m%d%Y")
    if not args.model_path:
        # Upstream always derived the output path from the source path and
        # today's date.  The campaign needs it explicit and stable instead: the
        # date makes a path change at midnight (so a resumed or re-attempted run
        # would land somewhere new), and Drive-backed output cannot live under
        # the dataset directory.  An explicit --model_path now wins.
        args.model_path = str(Path(args.source_path) / "experiments" / today / args.exp)
    if not os.path.exists(args.model_path):
        os.makedirs(args.model_path)

    print("Optimizing " + args.model_path)

    # M2: refuse to start a run that cannot answer the question it was
    # configured to ask.  Every check here guards a failure that is otherwise
    # silent -- see utils/preflight.py.
    preflight_args(args, op.extract(args), lp.extract(args))
    # The dense cloud IS the experimental condition for the A1-derived cells,
    # so its provenance sidecar is folded into the manifest.
    manifest_extra = {}
    if args.pcd_path:
        from utils.dense_init_io import read_sidecar
        manifest_extra["dense_pcd"] = {
            "path": args.pcd_path,
            **read_sidecar(args.pcd_path),
        }

    write_manifest(
        model_path=args.model_path,
        args=args,
        cell_name=cell_name,
        cell_values=cell_values,
        repo_root=Path(__file__).resolve().parent,
        extra=manifest_extra,
    )

    # Initialize system state (RNG)
    safe_state(args.quiet, args.seed)

    # Start GUI server, configure and run training
    network_gui.init(args.ip, args.port)
    torch.autograd.set_detect_anomaly(args.detect_anomaly)

    # Print out all the parameters in the run
    for k,v in vars(args).items():
        print(f"{k}: {v}")

    training(
        lp.extract(args),
        op.extract(args),
        pp.extract(args),
        args.test_iterations,
        args.save_iterations,
        args.checkpoint_iterations,
        args.start_checkpoint,
        args.debug_from
    )

    # All done
    print("\nTraining complete.")
