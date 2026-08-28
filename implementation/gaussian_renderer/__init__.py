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
# ---------------------------------------------------------------------------
# MERGED RASTERIZER BINDING  (CD-13)
#
# Upstream SeaSplat imports `diff_gaussian_rasterization` from the fork
# `github.com/dxyang/diff-gaussian-rasterization`, whose forward returns
# `(color, alpha, radii)`.  Mini-Splatting's importance metrics need
# `diff_gaussian_rasterization_ms`, whose forward returns
# `(color, radii, accum_weights, accum_weights_count, accum_max_count)`.
# Neither fork returns both, and the two cannot be imported side by side
# without building two CUDA extensions with clashing symbols.
#
# This module resolves that by using the `_ms` fork ALONE and recovering the
# alpha channel analytically, without touching CUDA:
#
#   Alpha compositing is applied independently per colour channel, and the
#   accumulated alpha does not depend on the colour values at all:
#       C_ch = sum_i T_i * a_i * c_i,ch  +  T_final * bg_ch
#   Setting c_i = 1 for every Gaussian on a channel with bg = 0 gives
#       C_ch = sum_i T_i * a_i  =  1 - prod_i (1 - a_i)  =  alpha
#   which is exactly the quantity the dxyang fork returns, and it is
#   differentiable through the standard autograd path (gradients reach
#   `opacities` via `grad_out_color`), which SeaSplat's `L_op` requires.
#
# SeaSplat already runs a second rasterization pass for depth, using
# `override_color = [z, z, z]` and reading channel 0 only.  Channels 1 and 2
# are redundant.  We repurpose that pass as a *probe*:
#
#       channel 0 -> z          (blended depth,  Z_raw)
#       channel 1 -> 1          (accumulated alpha)
#       channel 2 -> 0          (unused, kept zero)
#
# so depth and alpha both come out of the pass that was already being paid
# for.  Net cost of the merge: zero extra passes, zero CUDA changes.
# ---------------------------------------------------------------------------

import math
from typing import Any, Optional

import torch

from diff_gaussian_rasterization_ms import (
    GaussianRasterizationSettings,
    GaussianRasterizer,
)
from scene.gaussian_model import GaussianModel
from utils.sh_utils import eval_sh


def render(
    viewpoint_camera: Any,
    pc: GaussianModel,
    pipe: Any,
    bg_color: torch.Tensor,
    scaling_modifier: float = 1.0,
    override_color: Optional[torch.Tensor] = None,
) -> dict[str, torch.Tensor]:
    """Rasterize the scene.

    Returns the rendered image, the screen-space bookkeeping tensors 3DGS's
    density control needs, and Mini-Splatting's three per-Gaussian importance
    accumulators.

    `bg_color` must be on the GPU.

    Note: unlike upstream SeaSplat this does NOT return `alpha` -- the `_ms`
    fork does not produce it.  Use `render_depth_alpha` for alpha; see the
    module docstring.
    """
    # Zero tensor used to make PyTorch return gradients of the 2D
    # (screen-space) means.
    screenspace_points = torch.zeros_like(
        pc.get_xyz, dtype=pc.get_xyz.dtype, requires_grad=True, device="cuda"
    ) + 0
    try:
        screenspace_points.retain_grad()
    except Exception:
        pass

    tanfovx = math.tan(viewpoint_camera.FoVx * 0.5)
    tanfovy = math.tan(viewpoint_camera.FoVy * 0.5)

    raster_settings = GaussianRasterizationSettings(
        image_height=int(viewpoint_camera.image_height),
        image_width=int(viewpoint_camera.image_width),
        tanfovx=tanfovx,
        tanfovy=tanfovy,
        bg=bg_color,
        scale_modifier=scaling_modifier,
        viewmatrix=viewpoint_camera.world_view_transform,
        projmatrix=viewpoint_camera.full_proj_transform,
        sh_degree=pc.active_sh_degree,
        campos=viewpoint_camera.camera_center,
        prefiltered=False,
        debug=pipe.debug,
    )

    rasterizer = GaussianRasterizer(raster_settings=raster_settings)

    means3D = pc.get_xyz
    means2D = screenspace_points
    opacity = pc.get_opacity

    scales = None
    rotations = None
    cov3D_precomp = None
    if pipe.compute_cov3D_python:
        assert False  # this is by default False
        cov3D_precomp = pc.get_covariance(scaling_modifier)
    else:
        scales = pc.get_scaling
        rotations = pc.get_rotation

    shs = None
    colors_precomp = None
    if override_color is None:
        if pipe.convert_SHs_python:
            assert False  # this is by default False
            shs_view = pc.get_features.transpose(1, 2).view(
                -1, 3, (pc.max_sh_degree + 1) ** 2
            )
            dir_pp = pc.get_xyz - viewpoint_camera.camera_center.repeat(
                pc.get_features.shape[0], 1
            )
            dir_pp_normalized = dir_pp / dir_pp.norm(dim=1, keepdim=True)
            sh2rgb = eval_sh(pc.active_sh_degree, shs_view, dir_pp_normalized)
            colors_precomp = torch.clamp_min(sh2rgb + 0.5, 0.0)
        else:
            shs = pc.get_features
    else:
        colors_precomp = override_color

    # The `_ms` fork returns three extra per-Gaussian accumulators alongside
    # the image.  They are produced during the forward pass regardless, so
    # collecting them costs nothing even when A2 is disabled.
    #   accum_weights       -> sum of blending weights   (Mini-Splatting I^1)
    #   accum_weights_count -> pixels the Gaussian projects onto (area_proj)
    #   accum_max_count     -> pixels where it is the argmax contributor
    #                          (area_max; drives intersection preserving)
    rendered_image, radii, accum_weights, area_proj, area_max = rasterizer(
        means3D=means3D,
        means2D=means2D,
        shs=shs,
        colors_precomp=colors_precomp,
        opacities=opacity,
        scales=scales,
        rotations=rotations,
        cov3D_precomp=cov3D_precomp,
    )

    return {
        "render": rendered_image,
        "viewspace_points": screenspace_points,
        "visibility_filter": radii > 0,
        "radii": radii,
        "accum_weights": accum_weights,
        "area_proj": area_proj,
        "area_max": area_max,
    }


def homogenize_points(points: torch.Tensor) -> torch.Tensor:
    """Convert batched points (xyz) to (xyz1)."""
    return torch.cat([points, torch.ones_like(points[..., :1])], dim=-1)


def render_depth_alpha(
    viewpoint_camera: Any,
    pc: GaussianModel,
    pipe: Any,
    scaling_modifier: float = 1.0,
) -> dict[str, torch.Tensor]:
    """Recover blended depth and accumulated alpha in a single pass.

    Uses the standard rasterizer with a three-channel probe colour:

        channel 0 = z   (camera-frame depth of each Gaussian centre)
        channel 1 = 1   (accumulates to alpha)
        channel 2 = 0

    The background is forced to zeros so that neither channel picks up a
    background contribution.  Upstream SeaSplat passed the scene `bg` here;
    with SeaSplat's defaults (`white_background=False`, `random_background
    =False`) that background is already zero, so this is behaviourally
    identical at the default configuration and strictly more correct if a
    non-zero background is ever enabled.

    Both outputs are differentiable: depth w.r.t. the Gaussian means through
    the probe colour, and alpha w.r.t. opacity through the rasterizer's
    `grad_opacities`.  `L_op` depends on the latter.
    """
    points_world = pc.get_xyz
    T_cam_world = viewpoint_camera.world_view_transform.T

    points_world_homogenized = homogenize_points(points_world)
    points_cam_homogenized = (T_cam_world @ points_world_homogenized.T).T
    points_cam = points_cam_homogenized[:, :3]

    zs = points_cam[:, 2].unsqueeze(-1)
    probe_color = torch.cat(
        [zs, torch.ones_like(zs), torch.zeros_like(zs)], dim=-1
    )

    zero_bg = torch.zeros(3, dtype=torch.float32, device=probe_color.device)

    pkg = render(
        viewpoint_camera=viewpoint_camera,
        pc=pc,
        pipe=pipe,
        bg_color=zero_bg,
        scaling_modifier=scaling_modifier,
        override_color=probe_color,
    )

    probe = pkg["render"]
    pkg["depth"] = probe[0].unsqueeze(0)
    pkg["alpha"] = probe[1].unsqueeze(0)
    return pkg


def render_depth(
    viewpoint_camera: Any,
    pc: GaussianModel,
    pipe: Any,
    bg_color: torch.Tensor,
    scaling_modifier: float = 1.0,
) -> dict[str, torch.Tensor]:
    """Backwards-compatible alias for `render_depth_alpha`.

    Upstream callers read `pkg["render"][0]` as depth; that still works,
    because channel 0 of the probe is unchanged.  `bg_color` is accepted and
    ignored -- see `render_depth_alpha` for why the probe pass forces a zero
    background.
    """
    del bg_color  # intentionally unused; probe pass forces a zero background
    return render_depth_alpha(
        viewpoint_camera=viewpoint_camera,
        pc=pc,
        pipe=pipe,
        scaling_modifier=scaling_modifier,
    )
