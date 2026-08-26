# §3 — Formal variable table

`B` = batch of rays (16 384). `N` = samples per ray at the final level (32).
"gin" values are from `configs/llff_256_uw.gin`, the config the released training script
uses; "dataclass" values are the Python defaults in `internal/configs.py` and are **not**
what runs.

---

## 3.1 Independent variables (directly optimized)

Everything optimized is **MLP weights** — there are no free per-scene physical parameters
at all. This is the single sharpest structural contrast with SeaSplat, which optimizes 9
raw scalars.

### PropMLP — proposal network (mip-NeRF 360, unchanged)

| Component | Shape | Init | Source |
|---|---|---|---|
| trunk | 4 dense layers × 256, skip connection every 4 | `he_uniform` | `[repo: models.py:682 weight_init; configs/llff_256_uw.gin PropMLP.net_depth=4, net_width=256]` |
| density head | `Dense(1)` | `he_uniform` | `[repo: models.py:786]` |
| RGB head | **absent** (`disable_rgb = True`) | — | `[repo: configs/llff_256_uw.gin]` |
| `density_bias` | scalar, **0** in gin (dataclass default `-1.`) | — | `[repo: configs/llff_256_uw.gin PropMLP.density_bias = 0; models.py:693]` |

### UWMLP — object branch (the "NeRF MLP")

| Component | Shape | Init | Source |
|---|---|---|---|
| density trunk | 8 dense × 256, skip every 4 | `he_uniform` | `[repo: models.py:674-675, 781-786; configs UWMLP.net_depth=8, net_width=256]` |
| `σ^obj` head | `Dense(1)`, then `softplus(raw + density_bias)`, `density_bias = 0` | `he_uniform` | `[repo: models.py:786, 836; configs UWMLP.density_bias = 0]` |
| bottleneck | `Dense(256)` | `he_uniform` | `[repo: models.py:676, 846]` |
| viewdir sub-MLP | `net_depth_viewdirs = 1` × `net_width_viewdirs = 128` | `he_uniform` | `[repo: models.py:677-678, 913-917]` |
| `c^obj` head | `Dense(3)` → `sigmoid`, then padded to `[-0.001, 1.001]` | `he_uniform` | `[repo: models.py:697, 699, 921-925]` |

### UWMLP — **mediumMLP** branch (the new part) — one evaluation per ray

| Component | Shape | Init | Source |
|---|---|---|---|
| direction encoding | `pos_enc(viewdirs, min_deg=0, max_deg=deg_view=4, append_identity=True)` → 27-dim | — | `[repo: models.py:686, 722-724]` |
| **water trunk** | **`net_depth_water = 1`** dense layer of width **`net_width_viewdirs = 128`**, `softplus` activation | `he_uniform` | `[repo: models.py:716, 678, 865-869]` |
| `c^med` head | `Dense(3)` → `sigmoid` | `he_uniform` | `[repo: models.py:871-873]` |
| `σ^bs` head | `Dense(3)` → `softplus(· + water_bias)`, `water_bias = 0` in gin (dataclass `-1.`) | `he_uniform` | `[repo: models.py:878-879, 694; configs UWMLP.water_bias = 0]` |
| `σ^attn` head | `Dense(3)` → `softplus(· + water_bias)` | `he_uniform` | `[repo: models.py:889-890]` |

> **⚠ D-1.** `[paper §4.5]` states: "for the mediumMLP, we use **6 linear layers with 256
> features** and a softplus activation, followed by 3 branches of dense layers". The
> released code hard-codes `self.net_depth_water = 1` at `[repo: models.py:716]` and uses
> `net_width_viewdirs` (=128), not `net_width` (=256). The **3-branch** structure matches;
> the **trunk does not**: 1×128 vs 6×256, roughly a **12× parameter reduction** in the
> medium trunk. This value is not exposed in gin, so no config can restore it.
> `[inferred: 6·256² ≈ 393k vs 1·(27·128) ≈ 3.5k trunk weights]`

### Optimizer

| Item | Value | Source |
|---|---|---|
| Optimizer | Adam, `eps = 1e-8` | `[repo: configs/llff_256_uw.gin Config.adam_eps]` |
| `lr_init → lr_final` | `2e-3 → 2e-5` | `[repo: configs/llff_256_uw.gin]` |
| `max_steps` | `250 000` | `[repo: configs/llff_256_uw.gin]` — matches `[paper §4.5]` |
| Gradient clipping | per-MLP: clip by value (`grad_max_val`), then by norm (`grad_max_norm`) | `[repo: train_utils.py:190-208]` |
| NaN handling | `jax.tree_util.tree_map(jnp.nan_to_num, grad)` — NaNs silently zeroed | `[repo: train_utils.py:313]` |

> `[paper §4.5]`: "We keep the learning rate and optimization parameters the same as in [5]"
> — but the gin sets `lr_init = 0.002`, whereas the non-underwater `configs/llff_256.gin`
> in the same repo uses `lr_init = 0.00025` `[repo: configs/llff_256.gin]`. The two configs
> differ by 8×, alongside a batch-size change from 2048 to 16384 (also 8×) — consistent
> with linear LR scaling, but **not** "the same as [5]" in the literal sense.
> `[inferred: comparing the two gin files in the repo]`

---

## 3.2 Dependent variables (derived each forward pass)

### Per 3D sample `i` along ray `r`

| Symbol | Shape | Definition | Source |
|---|---|---|---|
| `σ^obj_i` | `(B, N)` | object density | `[paper Eq. 8]` `[repo: models.py:836]` |
| `c^obj_i` | `(B, N, 3)` | object colour | `[paper Eq. 20]` `[repo: models.py:921]` |
| `δ_i` | `(B, N)` | `(t_{i+1} − t_i)·‖d‖` | `[repo: render.py:163-164]` |
| `δ^bs_i` | `(B, N)` | `stop_gradient(t_{i+1} − t_i)·‖d‖` — **detached spacing** for all medium terms | `[repo: render.py:179]` |
| `T^obj_i` | `(B, N)` | `exp(−Σ_{j<i} σ^obj_j δ_j)` | `[paper Eq. 22]` `[repo: render.py:214-219]` |
| `α_i` | `(B, N)` | `1 − exp(−σ^obj_i δ_i)` | `[repo: render.py:213]` |
| `w^obj_i` | `(B, N)` | `α_i · T^obj_i` — the object "weight" | `[paper Eq. 23]` `[repo: render.py:220]` |
| `A_i` (`trans_atten`) | `(B, N, 3)` | `exp(−Σ_{j<i} σ^attn δ^bs_j)` — attenuation transmittance | `[paper Eq. 20]` `[repo: render.py:205-210]` |
| `α^bs_i` | `(B, N, 3)` | `1 − exp(−σ^bs δ^bs_i)` | `[repo: render.py:185]` |
| `T^bs_i` | `(B, N, 3)` | `exp(−Σ_{j<i} σ^bs δ^bs_j)` | `[repo: render.py:187-192]` |

### Per ray `r` (constant along the ray — the core modelling constraint)

| Symbol | Shape | Definition | Source |
|---|---|---|---|
| `c^med` | `(B, 1, 3)` | medium colour, `= B^∞` in the reduced model | `[paper §4.3]` `[repo: models.py:871]` |
| `σ^bs` | `(B, 1, 3)` | backscatter coefficient | `[paper Eq. 21]` `[repo: models.py:878]` |
| `σ^attn` | `(B, 1, 3)` | attenuation coefficient | `[paper Eq. 20]` `[repo: models.py:889]` |

### Rendered outputs

| Symbol | Shape | Definition | Source |
|---|---|---|---|
| `Ĉ^obj` (`direct`) | `(B, 3)` | `Σ_i w^obj_i · A_i · c^obj_i` | `[paper Eq. 20]` `[repo: render.py:320]` |
| `Ĉ^med` (`bs`) | `(B, 3)` | `Σ_i T^obj_i · α^bs_i · T^bs_i · c^med` | `[paper Eq. 21]` `[repo: render.py:324]` |
| `Ĉ` (`rgb`) | `(B, 3)` | `Ĉ^obj + Ĉ^med` | `[paper Eq. 12]` `[repo: render.py:326]` |
| `J` | `(B, 3)` | `stop_gradient(Σ_i w^obj_i c^obj_i)` — the **restored** image | `[repo: render.py:319]` (not given a symbol in the paper's equations; called "clean" in §1) |
| `acc` | `(B,)` | `Σ_i w^obj_i` | `[repo: render.py:316]` |
| `E_map` | `(B, 3)` | `stop_gradient(E[A])` — attenuation map | `[repo: render.py:346]` |
| `distance_mean/_median` | `(B,)` | weighted percentile of `t` — the depth output | `[repo: render.py:351-354, 362-374]` |

---

## 3.3 Fixed / given inputs

### Data

| Quantity | Value | Source |
|---|---|---|
| Real scenes | Red Sea (20 imgs), Curaçao (20), Panama (18); 3 held out each | `[paper §5.1]` |
| Camera | Nikon D850 SLR, Nauticam housing, **dome port** (to preserve the pinhole model, ref [45]) | `[paper §5.1]` |
| Image state | **linear**, white-balanced with 0.5% per-channel clipping, downsampled to ≈900×1400 | `[paper §5.1]` |
| Poses | COLMAP (ref [39]) | `[paper §5.1]` |
| Simulated scene | LLFF `Fern`; depth from mip-NeRF 360, then Eq. 7 applied with `β^D = [1.3, 1.2, 0.9]`, `β^B = [0.95, 0.85, 0.7]`, `B^∞ = [0.07, 0.20, 0.39]`; fog with `β = 1.2` | `[paper §5.1]` |
| Baseline SFM depth (for the SeaThru [2] comparison) | Agisoft Metashape | `[paper §5.1]` |

> Note the **simulation constants differ from SeaSplat's**: SeaThru-NeRF uses
> `β^D = [1.3, 1.2, 0.9]`, SeaSplat uses `β^D = [2.6, 2.4, 1.8]` — exactly **2×**. Both
> papers call the setup "simulated underwater from an LLFF/Mip-NeRF-360 scene", but the
> media are not the same strength and results are not directly comparable.
> `[inferred: paper §5.1 vs seasplat paper §V.A.a]`

### Hyperparameters — gin (`configs/llff_256_uw.gin`)

| Name | Value | Note |
|---|---|---|
| `batch_size` | `16 384` rays | matches `[paper §4.5]` |
| `max_steps` | `250 000` | matches `[paper §4.5]` |
| `near`, `far` | `0.`, `1.` | NDC |
| `forward_facing` | `True` | |
| `factor` | `1` (vs `4` in the non-UW llff config) | full resolution |
| `Model.num_levels` | `2` | one proposal round + one NeRF round |
| `Model.num_prop_samples` | `128` | |
| `Model.num_nerf_samples` | `32` | |
| `Model.ray_shape` | `'cylinder'` | forward-facing/NDC choice |
| `Model.opaque_background` | **`False`** | matches `[paper §4.5]` — the medium must explain empty rays |
| `data_loss_type` | `'rawnerf'` | matches `[paper Eq. 25]` |
| `data_loss_mult` | `1` | |
| `interlevel_loss_mult` | `1` | `L_prop` |
| `distortion_loss_mult` | **`0.`** | mip-NeRF 360's distortion loss **disabled**; not mentioned in the paper |
| `use_uw_mlp` | `True` | |
| `use_uw_acc_trans_loss` | `True` | Eq. 27 on `T^obj` |
| `use_uw_acc_weights_loss` | **`False`** | the alternative form (on `Σw`) is off |
| `uw_initial/final_acc_trans_loss_mult` | `1e-4`, `1e-4` | = `λ` of `[paper Eq. 24]`; the ramp is a **no-op** |
| `uw_initial/final_acc_weights_loss_mult` | `1e-3`, `1e-3` | unused (loss disabled) |
| `uw_decay_acc` | `5 000` (dataclass) | switch point; no-op here |
| `uw_acc_loss_factor` | **`6`** (dataclass) | **asymmetry factor absent from `[paper Eq. 26]`** |
| `use_uw_sig_med_loss` | `False` | comment: *"not in the paper!!"* `[repo: configs.py:174]` |
| `uw_old_model` | `False` | `True` ⇒ ablation variant **II** (3 medium params) |
| `uw_fog_model` | `False` | `True` ⇒ ablation variant **I** (1 medium param) |
| `gen_eq` | `False` | `True` ⇒ ablation variant **III** (Eqs. 13–14) |
| `uw_atten_xyz` | `False` | would condition `σ^attn` on position too |
| `uw_rgb_dir` | **`False`** | ⇒ `c^obj` is **view-independent**; contradicts `[paper §4.3]` |
| `extra_samples` | `False` (dataclass) | extra near-camera samples for the fog sim; separate gin exists |
| `lr_init`, `lr_final` | `2e-3`, `2e-5` | |
| `deg_view` | `4` | direction encoding degree |
| `max_deg_point` | `16` | IPE degree |
