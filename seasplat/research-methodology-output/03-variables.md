# §3 — Formal variable table

`N` = number of Gaussians at the current iteration (varies — densification/pruning).
`H, W` = image height/width after `--resolution` handling.
Tags per §6 of the methodology.

---

## 3.1 Independent variables (directly optimized)

### Group 1 — 3D Gaussian representation (inherited from 3DGS, one Adam param-group each)

| Symbol | Repo name | Shape | Initialization | lr | Source |
|---|---|---|---|---|---|
| `μ` | `_xyz` | `(N, 3)` | COLMAP sparse points, in world units scaled by `rescale_units` (default 1.0) | exp-decay `1.6e-4 → 1.6e-6` over 30 000 steps, `delay_mult=0.01` | `[repo: scene/gaussian_model.py; arguments/__init__.py:89-92]` |
| `f_dc` | `_features_dc` | `(N, 1, 3)` | `RGB2SH(colour of COLMAP point)` | `feature_lr = 2.5e-3` | `[repo: arguments/__init__.py:93]` |
| `f_rest` | `_features_rest` | `(N, 0, 3)` — **empty** | n/a | `feature_lr / 20` | `[repo: arguments/__init__.py:49 sets sh_degree = 0]` |
| `o_raw` | `_opacity` | `(N, 1)` | `inverse_sigmoid(0.1)` (3DGS default) | `opacity_lr = 0.05` | `[repo: arguments/__init__.py:94]` |
| `s_raw` | `_scaling` | `(N, 3)` | `log(√(mean dist to 3 nearest neighbours))` via `simple_knn` | `scaling_lr = 5e-3` | `[repo: arguments/__init__.py:95]` |
| `q` | `_rotation` | `(N, 4)` | identity quaternion `[1,0,0,0]` | `rotation_lr = 1e-3` | `[repo: arguments/__init__.py:96]` |

> **`sh_degree = 0` is a SeaSplat-specific change, not a 3DGS default.** Upstream 3DGS uses
> `sh_degree = 3`. The repo comment makes the intent explicit: `# dxy: default to SH 0`
> `[repo: arguments/__init__.py:49]`. The paper confirms: "We use zero order spherical
> harmonics, such that the color of each Gaussian has no view dependencies."
> `[paper §IV.C]`. **Consequence:** each Gaussian carries 3 colour numbers instead of 48,
> so per-Gaussian storage drops from 59 to 14 floats — relevant when comparing against
> `compact3d/`, `CompGS/`, `OMG/` whose entire contribution is compressing those 48 numbers.

### Group 2 — Medium model (new; two separate Adam optimizers, both `lr = 1e-2`)

| Symbol | Repo name | Shape | Initialization | Source |
|---|---|---|---|---|
| `β^B` (backscatter coeff.) | `bs_model.backscatter_conv_params` | `(3, 1, 1, 1)` — a 1×1 conv kernel, `out_ch=3, in_ch=1` | `torch.rand(3,1,1,1)` → `U(0,1)` per channel (`init_vals=False` is the default path from `train.py:84`) | `[repo: deepseecolor/models.py:46-54; train.py:84]` |
| `B^∞` (water colour at ∞) | `bs_model.B_inf` | `(3, 1, 1)` | `torch.rand(3,1,1)` → `U(0,1)`, stored as a **logit**; used as `σ(B^∞)` | `[repo: models.py:61, 77]` |
| `β^D` (attenuation coeff.) | `at_model.attenuation_conv_params` | `(3, 1, 1, 1)` | **`[1.1, 0.95, 0.95]`** fixed (because `AttenuateNetV3(init_vals = not do_sigmoid_at)` and `do_sigmoid_at` defaults `False`) | `[repo: models.py:216-218; train.py:88; arguments/__init__.py:173,176]` |
| — | `at_model.attenuation_coef` | `None` in V3 | n/a — V3 drops the two-exponential `a·e^{-bz} + c·e^{-dz}` form of DeepSeeColor Eq. 12 | `[repo: models.py:219]` |

> **Total learned medium parameters at default settings: 9 scalars** (`β^D ∈ ℝ³`,
> `β^B ∈ ℝ³`, `B^∞ ∈ ℝ³`) — `[inferred: counting the three tensors above, given
> use_bs_residual=False and use_at_v3=True at arguments/__init__.py:174,176]`.
> The paper's `O(1)` claim (§V.B) refers exactly to this.

### Group 3 — Learned background colour (repo-only; third Adam optimizer, `lr = 1e-2`)

| Symbol | Repo name | Shape | Initialization | Source |
|---|---|---|---|---|
| `bg` | `learned_bg` | `(3,)` | logit of `[r=0.05, g=0.25, b=0.80]` — hard-coded blue-green prior | `[repo: train.py:126-131]` |

> `learn_background = True` by default `[repo: arguments/__init__.py:114]`. **This
> parameter does not appear anywhere in the paper.** With `bg_from_bs = True` (also
> default, line 118) it is *transferred into* `B^∞` at the moment SeaThru turns on
> `[repo: train.py:209-212]` and then stops being used. So its true role is as a
> **structured initializer for `B^∞`**, replacing the `U(0,1)` init in Group 2.
> This is an important, undocumented well-posedness aid — see [`05-constraints.md`](05-constraints.md).

### Deactivated-by-default independent variables (present in code, off in configs)

| Repo name | Shape | Gate | Source |
|---|---|---|---|
| `bs_model.J_prime`, `bs_model.residual_conv_params` | `(3,1,1)`, `(3,1,1,1)` | `use_bs_residual = False` | `[repo: arguments/__init__.py:174; models.py:57-59]` |
| `at_model.attenuation_coef` (6 params, V1) | `(6,1,1)`+`(6,1,1,1)` | `use_at_v2 = False`, `use_at_v3 = True` → V1 unused | `[repo: arguments/__init__.py:175-176]` |

---

## 3.2 Dependent variables (derived each forward pass)

| Symbol | Shape | Definition | Source |
|---|---|---|---|
| `Ĵ` | `(3, H, W)` | rasterized colour = **medium-free** radiance | `[paper §IV.A]` `[repo: train.py:201-203]` |
| `α` | `(1, H, W)` | accumulated opacity from the rasterizer | `[repo: train.py:202]` |
| `Z_raw` | `(1, H, W)` | second rasterization pass, per-Gaussian `z` in camera frame used as override colour | `[repo: gaussian_renderer/__init__.py:116-137]` |
| `Ẑ` | `(1, H, W)` | `Z_raw / α`, NaN/Inf → max, `÷ normalize_depth`, then **min–max normalised to [0,1]** because `norm_depth_max = True` | `[repo: train.py:222-237; arguments/__init__.py:131-133]` |
| `Â` | `(1, 3, H, W)` | `exp(-clamp(β^D ⊛ Ẑ, ≥0))` in V3 — a per-channel exponential of depth | `[repo: models.py:226-232]` |
| `B̂` | `(1, 3, H, W)` | `σ(B^∞) ⊙ (1 - exp(-clamp(β^B ⊛ Ẑ, ≥0)))` | `[repo: models.py:70-85]` |
| `D̂` | `(1, 3, H, W)` | direct image `= Ĵ ⊙ Â` | `[paper §III.B]` `[repo: train.py:256]` |
| `Î` | `(1, 3, H, W)` | `clamp(D̂ + B̂, 0, 1)` — the in-medium reconstruction compared against `I` | `[repo: train.py:273]` |
| `D̃` | `(1, 3, H, W)` | backscatter-removed **observed** image `= I - B̂'` (both operands detached) — the argument of `L_bs` | `[paper Eq. 4 calls this D̂]` `[repo: train.py:400]` |
| `Â'`, `B̂'` | as above | depth-detached duplicates of `Â`, `B̂` | `[repo: train.py:255, 270]` |

> **Naming trap:** the paper uses `D̂` for *both* `Ĵ ⊙ Â` (§III.B, the modelled direct
> image) and `I - B̂` (Eq. 4, the empirical backscatter-removed image). These are only
> equal at the optimum. I write the second one `D̃` here and in the pseudocode to keep
> them distinct.

---

## 3.3 Fixed / given inputs

### Data & camera

| Quantity | Value / source | Tag |
|---|---|---|
| `I` | captured images, `(3, H, W)`, `[0,1]` after `PILtoTorch` ÷255 | `[repo: utils/general_utils.py PILtoTorch]` |
| `K` | `(3,3)` intrinsics from COLMAP | `[paper §IV.A]` |
| `T^cam_world` | `SE(3)` extrinsics from COLMAP | `[paper §IV.A]` |
| `znear, zfar` | `0.01`, `100.0` | `[repo: arguments/__init__.py:57-58]` |
| Datasets | SeaThru-NeRF (Curaçao, Japanese Gardens, Panama, IUI3); SaltPond (CUREE robot, US Virgin Is.); SimFog + SimWater (Mip-NeRF-360 `garden` + synthetic medium) | `[paper §V.A.a]` |
| Simulation medium constants | `β^D = [2.6, 2.4, 1.8]`, `β^B = [1.9, 1.7, 1.4]`, `B^∞ = [0.07, 0.20, 0.39]`; fog uses `β^D = β^B = 2.4` | `[paper §V.A.a]` |

### Hyperparameters — **repo defaults** (`arguments/__init__.py`, commit `ddc6259`)

| Name | Default | Role |
|---|---|---|
| `iterations` | `30 000` | outer iteration budget |
| `sh_degree` | `0` | SH order (see note above) |
| `lambda_dssim` | `0.2` | `L_GS` mix |
| `percent_dense` | `0.01` | densify size threshold |
| `densification_interval` | `100` | |
| `opacity_reset_interval` | `3 000` | |
| `densify_from_iter` / `densify_until_iter` | `500` / `15 000` | |
| `densify_grad_threshold` | `2e-4` | |
| `do_seathru` | **`False`** | must be passed explicitly: `--do_seathru` |
| `seathru_from_iter` | **`9 000 000`** | README passes `--seathru_from_iter 10000` |
| `bs_at_lr` | `1e-2` | medium optimizers |
| `update_bs_at_interval` | `100` | GS steps between medium bursts |
| `update_bs_at_count` | `50` | medium steps per burst |
| `use_at_v3` | `True` | selects the 3-parameter attenuation model |
| `use_bs_residual` | `False` | drops SeaThru's residual `J'e^{-β z}` term |
| `do_sigmoid_bs` / `do_sigmoid_at` | `False` / `False` | β's are raw + clamped, not squashed |
| `bs_scale` / `at_scale` | `5.0` / `5.0` | unused when `do_sigmoid_* = False` |
| `filter_depth` | `True` | `Ẑ ← Z/α` |
| `norm_depth_max` | `True` | min–max renormalise `Ẑ` to `[0,1]` |
| `normalize_depth` | `1.0` | |
| `depth_alpha_threshold` | `0.5` | eval-time depth masking only |
| **Loss weights** | | |
| `dwr_lambda` (`L_Z-recon`) | `1.0` | `add_recon_depth_l1 = True` |
| `dcp_loss_lambda` (`L_bs`) | `1.0` | `use_dcp_loss = True` |
| `gw_loss_lambda` (`L_gw`) | `0.1` | `use_gw_loss = True`, `gw_from_iter = 10 000` |
| `sat_loss_lambda` (`L_sat`) | `2.0` | `use_rgb_sat_loss = True` |
| `bg_lambda` (`L_op`) | `0.01` | `learn_background = True` |
| `depth_smooth_lambda` (`L_Zsmooth`) | `2.0` | `use_depth_smooth_loss = True` |
| `T_sat` | `0.7` | `RgbSaturationLoss(saturation_val=0.7)` `[repo: train.py:98]` — matches `[paper §IV.B: "T_sat as a threshold empirically set to 0.7"]` |
| `k` in `L_bs` | `1000.0` | `DarkChannelPriorLossV3(cost_ratio=1000.)` `[repo: deepseecolor/losses.py:147]`; paper only says `k > 1` `[paper Eq. 4]` |
| `T_sim` in `L_op` | `0.2·√3 ≈ 0.3464` (an **L2 norm**, not squared) | `[repo: deepseecolor/losses.py:248]`; paper leaves `T_sim` unspecified `[paper Eq. 9]` |

### Off-by-default loss terms (exist in code, contribute 0 at defaults)

`use_depth_l1_loss`, `use_alpha_smooth_loss`, `use_opacity_prior`, `use_rgb_sv_loss`,
`use_binf_loss`, `use_dsc_at_loss`, `use_depth_weighted_l1/l2`, `do_z_score`,
`disable_attenuation`, `use_gt_depth` — all `False`
`[repo: arguments/__init__.py:110-112, 127, 136, 139, 160-164, 177, 184]`.
