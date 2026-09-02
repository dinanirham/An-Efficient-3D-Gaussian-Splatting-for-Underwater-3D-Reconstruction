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

import argparse
import json
import os
import sys
from argparse import ArgumentParser, Namespace
from pathlib import Path

class GroupParams:
    pass

class ParamGroup:
    def __init__(self, parser: ArgumentParser, name : str, fill_none = False):
        group = parser.add_argument_group(name)
        for key, value in vars(self).items():
            shorthand = False
            if key.startswith("_"):
                shorthand = True
                key = key[1:]
            t = type(value)
            value = value if not fill_none else None
            if t == bool:
                # CD-1.  Upstream registered every bool with action="store_true",
                # which can only SET a flag.  Roughly a dozen options default to
                # True, so they could not be turned off from the command line at
                # all -- making a 2^3 ablation matrix impossible without editing
                # source between cells.  BooleanOptionalAction gives both
                # --flag and --no-flag, which is the whole fix.
                #
                # Bools lose their single-dash shorthand: argparse cannot give a
                # short option a --no- counterpart.  Only _white_background was
                # affected (-w); the shorthands SeaSplat's README actually uses
                # (-s, -m) are strings and are untouched.
                group.add_argument(
                    "--" + key,
                    default=value,
                    action=argparse.BooleanOptionalAction,
                )
            elif shorthand:
                group.add_argument("--" + key, ("-" + key[0:1]), default=value, type=t)
            else:
                group.add_argument("--" + key, default=value, type=t)

    def extract(self, args):
        group = GroupParams()
        for arg in vars(args).items():
            if arg[0] in vars(self) or ("_" + arg[0]) in vars(self):
                setattr(group, arg[0], arg[1])
        return group

class ModelParams(ParamGroup):
    def __init__(self, parser, sentinel=False):
        self.sh_degree = 0 #3 # dxy: default to SH 0
        self._source_path = ""
        self._model_path = ""
        self._images = "images"
        self._resolution = -1
        self._white_background = False
        self.data_device = "cuda"
        self.eval = False
        self.znear=0.01
        self.zfar=100.0
        self.subsample = 0
        self.skip_first_n_images = 0
        self.start_cam = -1
        self.end_cam = -1
        self.rescale_units = 1.0
        # M1: path to the dense correspondence-derived point cloud produced by
        # source/roma_init.py.  Empty means "use COLMAP's sparse points", i.e.
        # the baseline path.  This cloud IS the experimental condition for the
        # A1-derived cells, so its sidecar hash is recorded in the manifest.
        self.pcd_path = ""
        self.scene_bounds_xxyyzz = None
        self.do_scene_bb = False
        self.bb_xlo = 0.0
        self.bb_xhi = 0.0
        self.bb_ylo = 0.0
        self.bb_yhi = 0.0
        self.bb_zlo = 0.0
        self.bb_zhi = 0.0
        super().__init__(parser, "Loading Parameters", sentinel)

    def extract(self, args):
        g = super().extract(args)
        g.source_path = os.path.abspath(g.source_path)
        return g

class PipelineParams(ParamGroup):
    def __init__(self, parser):
        self.convert_SHs_python = False
        self.compute_cov3D_python = False
        self.debug = False
        super().__init__(parser, "Pipeline Parameters")

class OptimizationParams(ParamGroup):
    def __init__(self, parser):
        self.iterations = 30_000
        self.position_lr_init = 0.00016
        self.position_lr_final = 0.0000016
        self.position_lr_delay_mult = 0.01
        self.position_lr_max_steps = 30_000
        self.feature_lr = 0.0025
        self.opacity_lr = 0.05
        self.scaling_lr = 0.005
        self.rotation_lr = 0.001
        self.percent_dense = 0.01
        self.lambda_dssim = 0.2
        self.densification_interval = 100
        self.opacity_reset_interval = 3000
        self.densify_from_iter = 500
        self.densify_until_iter = 15_000
        self.densify_grad_threshold = 0.0002
        self.random_background = False

        self.do_isotropic = False
        self.freeze_gs_from_iter = 9_000_000    # freeze the gaussian splat (do not update parameters)
        self.unfreeze_gs_from_iter = 9_000_000  # unfreeze the gaussian splat (do not update parameters)
        self.shuffle = True                     # shuffle cameras
        self.use_depth_weighted_l1 = False
        self.use_depth_weighted_l2 = False

        # background
        self.learn_background = True          # learn background color that is composited with splat render
        self.bg_lambda = 0.01                # lambda for background alpha loss
        self.add_bg_binf = False              # lambda for background alpha loss
        self.use_lab = False                  # use color difference in L*a*b* space for calculating close colors to background
        self.bg_from_bs = True               # once seathru is enabled, do not use the learned background
        self.bg_lr = 1e-2                     # learning rate for background values
        self.alpha_bg_opacities = False
        self.alpha_binf_uw = True
        self.alpha_binf_render = False
        self.alpha_bg_uw = False
        self.turn_off_bg_loss = False

        # depth
        self.use_gt_depth = False             # swap out rendered depth with pseudo ground truth depth
        self.use_depth_l1_loss = False        # use l1 depth reconstruction loss
        self.use_depth_smooth_loss = True    # depth smoothness loss based on xy gradients
        self.depth_smooth_lambda = 2.0       # lambda for depth smooth loss
        self.filter_depth = True             # depth = depth / alpha with nans filled in as depth.max() or depth = depth + (1 - alpha) * depth.max() or both
        self.normalize_depth = 1.0            # normalize depth by this value (if not -1) for use in downstream network input
        self.norm_depth_max = True
        self.depth_alpha_threshold = 0.5

        self.use_alpha_smooth_loss = False    # alpha smoothness loss based on xy gradients
        self.alpha_smooth_lambda = 1.0       # lambda for depth smooth loss

        self.use_opacity_prior = False
        self.opacity_prior_lambda = 0.0001

        # general losses
        self.add_recon_depth_l1 = True
        self.dwr_lambda = 1.0

        self.use_dcp_loss = True             # use dark channel prior loss
        self.dcp_loss_lambda = 1.0             # use dark channel prior loss

        self.use_rgb_sat_loss = True         # use RGB saturation loss
        self.sat_loss_lambda = 2.0         #

        self.use_gw_loss = True              # use gray world prior loss
        self.gw_loss_lambda = 0.1            # used to be 0.01 /shrug
        self.gw_reverse_J = False
        self.use_render_for_gw = False
        self.gw_detach_alpha_bg = False
        self.gw_from_iter = 10_000
        self.gw_filter_by_alpha = 0.0

        self.use_rgb_sv_loss = False          # use RGB spatial variation loss from DeepSeeColor

        self.use_binf_loss = False            # B_inf should approach the atmospheric light in the image
        self.binf_loss_lambda = 1.0
        self.use_dsc_at_loss = False          # DeepSeeColor attenuation loss term
        self.dsc_at_lambda = 1.0

        # seathru
        self.do_seathru = False
        self.bs_at_lr = 1e-2
        self.bs_scale = 5.0                   # model parameters for conv scaled between 0 and scale (i.e. depth dependent effect has 1/e^scale most change in color value)
        self.at_scale = 5.0                   # model parameters for conv scaled between 0 and scale (i.e. depth dependent effect has 1/e^scale most change in color value)
        self.do_sigmoid_bs = False
        self.do_sigmoid_at = False
        self.use_bs_residual = False          # use the residual terms in equation 10 from SeaThru ("depending on the scene, the residual can be left out...")
        self.use_at_v2 = False                # use attenuate net v2 (drops some terms)
        self.use_at_v3 = True                # use attenuate net v3 implx (simplest)
        self.disable_attenuation = False      # simplified model that only accounts for backscatter

        self.seathru_from_iter = 9_000_000
        self.update_bs_at_interval = 100      # every num gs updates, update the bs and at models
        self.update_bs_at_count = 50          # update bs and at models this many times

        self.scale_grad_threshold = 1.0

        # CD-23.  Route alpha through its own probe so density control sees
        # image + alpha, which is what upstream sees, and not depth.  Costs a
        # third rasterization per iteration; that shows up in wall clock, and
        # wall clock is a reported result -- so it is a config value, recorded
        # in every manifest, rather than a constant.
        self.separate_alpha_probe = True

        # Mechanism D, the supplementary contrast.  Detaching alpha from the
        # densification signal is what our pipeline did by accident before
        # CD-22/CD-23; measured against a broken baseline it looked like 6x
        # fewer primitives for -0.1 dB.  As a deliberate mechanism it needs a
        # faithful baseline to be measured against, which is what A0 now is.
        #
        # Free, and then some: with the gradient detached the alpha probe needs
        # no shared buffer, so this removes the third rasterization CD-23 added
        # rather than costing one.
        self.detach_alpha_gradient = False
        self.do_z_score = False               # z threshold direct image to +/- 5 stdevs

        # ------------------------------------------------------------------
        # Ablation mechanism flags (CD-1).
        #
        # These three bits, and nothing else, select a cell of the 2^3
        # factorial matrix:
        #     A0 000  A1 100  A2 010  A3 001
        #     A4 110  A5 101  A6 011  A7 111
        # Prefer `--cell A4` (configs/cells.json) over setting them by hand;
        # the cell file also carries the per-cell overrides each mechanism
        # needs, and it is what gets recorded in the run manifest.
        # ------------------------------------------------------------------
        self.m1_dense_init = False   # dense correspondence init; densification off
        self.m2_simplify = False     # importance-weighted simplification to budget
        self.m3_quantize = False     # quantization-aware attribute VQ

        # --- M1 sub-parameters (active only when m1_dense_init) ------------
        # The two EDGS mechanisms below are on by default in EDGS and appear
        # nowhere in its paper.  They are what make a densification-free
        # regime survivable, so they are ported (R-5) rather than dropped --
        # but both are exposed, because both interact with SeaSplat's opacity
        # prior in ways neither source method had to consider.
        self.m1_max_lr = True                    # clamp the position-LR schedule
        self.m1_max_lr_floor = 8000              # ...to its value at this step
        self.m1_reduce_opacity = True            # continuous opacity decay
        self.m1_reduce_opacity_factor = 0.99     # logit += log(factor)
        self.m1_reduce_opacity_interval = 10     # ...every N iterations
        self.m1_decay_stops_at_seathru = True    # stop once L_op is also acting

        # --- M2 sub-parameters (active only when m2_simplify) --------------
        self.simp_iteration1 = 15_000   # stochastic sampling to the budget
        self.simp_iteration2 = 20_000   # light deterministic CDF prune
        self.n_bud = -1                 # primitive budget; REQUIRED when m2 is on.
                                        # An explicit count, not a ratio (CD-5):
                                        # a ratio of a varying population cannot
                                        # be made to bind in every cell, and a
                                        # non-binding budget silently collapses
                                        # A4 onto A1 and A7 onto A5.
        self.imp_metric = "outdoor"     # indoor -> I^1, outdoor -> I^2
        self.cdf_thres = 0.99           # mass retained at the second event

        # CD-6 -- the central integration decision of this work.  After a
        # simplification event the per-frame depth normalisation constants have
        # moved, so beta is now fitted to a rescaled input.  These medium-only
        # steps let it re-identify before geometry moves again.  Exposed rather
        # than fixed because the right length is genuinely unknown (OQ-10).
        self.m2_rewarm_steps = 200

        # Mini-Splatting rewinds the position-LR schedule after simplification
        # so that freshly REINITIALIZED primitives can still move.  Under the
        # simplification-only scoping (CD-4) nothing is reinitialized -- the
        # survivors keep their parameters and their Adam state -- so that
        # premise does not hold here and the rewind is off by default.
        self.m2_lr_rewind = False
        self.m2_lr_rewind_to = 5_000

        # --- M3 sub-parameters (active only when m3_quantize) --------------
        # CD-10: quantization must start AFTER the last simplification event.
        # A codebook fitted before a 60-90% prune is fitted to a population
        # about to be discarded, and quantization-aware training would spend
        # its gradient budget adapting parameters that are then deleted.
        self.kmeans_st_iter = 22_000
        self.kmeans_k = 4096      # NOT 256: at sh_degree=0 the group machinery
                                  # is inert, so k is the only quality dial.
        self.kmeans_freq = 100    # t: full reassignment interval
        self.kmeans_iters = 1     # K-means iterations per assignment pass
        # CD-8: the reference method's l1-opacity regulariser is deliberately
        # NOT implemented.  Its own authors attribute their 2-3x rendering
        # speedup to it rather than to the quantization, so including it would
        # make the M3 factor a quantization-plus-pruning factor and the M2/M3
        # columns of the matrix would stop being independent.  Expect A3 to
        # show approximately no frame-rate gain; that is the correct result.

        # Run-harness controls (not part of the method).
        self.allow_any_gpu = False   # bypass the A100 check; invalidates cross-cell contrasts
        self.diag_interval = 500     # iterations between unconditional diagnostic rows

        super().__init__(parser, "Optimization Parameters")

CELLS_PATH = Path(__file__).resolve().parent.parent / "configs" / "cells.json"


def load_cells() -> dict:
    """Read the ablation-matrix definition."""
    with open(CELLS_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def add_cell_argument(parser: ArgumentParser) -> None:
    """Register `--cell`, the only supported way to select a matrix cell."""
    parser.add_argument(
        "--cell",
        type=str,
        default=None,
        help="Ablation cell (A0..A7). Values from configs/cells.json are folded "
             "into the parser defaults, so anything given explicitly on the "
             "command line still wins.",
    )


def apply_cell_config(parser: ArgumentParser) -> tuple[str | None, dict]:
    """Fold the selected cell's values into `parser`'s defaults (CD-1).

    Resolution order is therefore, weakest to strongest:

        code defaults  <  cell file  <  explicit command line

    which falls out of argparse's own precedence once the cell values are
    installed as defaults -- no second parse and no "was this passed?"
    sentinel logic, both of which are easy to get subtly wrong.

    Returns (cell_name, applied_values) for the manifest.
    """
    pre = ArgumentParser(add_help=False)
    pre.add_argument("--cell", type=str, default=None)
    known, _ = pre.parse_known_args()
    if known.cell is None:
        return None, {}

    cells = load_cells()
    name = known.cell.upper()
    if name not in cells["cells"]:
        raise SystemExit(
            f"unknown cell {known.cell!r}; expected one of "
            f"{', '.join(sorted(cells['cells']))}"
        )

    values = dict(cells["defaults"])
    values.update(cells["cells"][name]["set"])
    parser.set_defaults(**values)
    return name, values


def get_combined_args(parser : ArgumentParser):
    cmdlne_string = sys.argv[1:]
    cfgfile_string = "Namespace()"
    args_cmdline = parser.parse_args(cmdlne_string)

    try:
        cfgfilepath = os.path.join(args_cmdline.model_path, "cfg_args")
        print("Looking for config file in", cfgfilepath)
        with open(cfgfilepath) as cfg_file:
            print("Config file found: {}".format(cfgfilepath))
            cfgfile_string = cfg_file.read()
    except TypeError:
        print("Config file not found at")
        pass
    args_cfgfile = eval(cfgfile_string)

    merged_dict = vars(args_cfgfile).copy()
    for k,v in vars(args_cmdline).items():
        if v != None:
            merged_dict[k] = v
    return Namespace(**merged_dict)
