# §3 — Formal variable table

`N` = current number of Gaussians (changes constantly — that is the subject of the paper).
`H, W` = image resolution. `M` = number of training views. Line numbers are `ms/` unless noted.

---

## 3.1 Independent variables (directly optimized)

**Unchanged from 3DGS.** Mini-Splatting introduces **zero new optimized parameters** — this
is worth stating plainly, because it is the sharpest structural contrast with `seasplat/`
(9 new scalars + 3 optimizers) and `compact3d/` (a learned codebook).

| Symbol | Repo name | Shape | Initialization | lr | Source |
|---|---|---|---|---|---|
| `p` (paper) / `μ` | `_xyz` | `(N, 3)` | COLMAP points, **or** depth-reinit points, **or** surviving centers after sampling | exp `1.6e-4 → 1.6e-6` | `[repo: arguments/__init__.py:74-77]` |
| `f_dc` | `_features_dc` | `(N, 1, 3)` | `RGB2SH(colour)`; at reinit, `RGB2SH(GT pixel colour)` | `2.5e-3` | `[repo: gaussian_model.py:463-465]` |
| `f_rest` | `_features_rest` | `(N, (D+1)²−1, 3)` — **`D = 0` until iter 15 000**, then ramps to 3 | **reset to 0** at every reinit | `2.5e-3 / 20` | `[repo: ms/train.py:56, 250; gaussian_model.py:466]` |
| `o` | `_opacity` | `(N, 1)` | `inverse_sigmoid(0.1)`, **re-applied at every reinit** | `0.05` | `[repo: gaussian_model.py:475]` |
| `s` | `_scaling` | `(N, 3)` | `log(√(kNN dist via distCUDA2))`, **re-applied at every reinit** | `5e-3` | `[repo: gaussian_model.py:470-471]` |
| `q` | `_rotation` | `(N, 4)` | identity `[1,0,0,0]`, **re-applied at every reinit** | `1e-3` | `[repo: gaussian_model.py:472-473]` |

> **The reinit resets are the whole method.** `reinitial_pts` `[repo: gaussian_model.py:460-483]`
> keeps only `μ` and the DC colour; `s`, `q`, `o`, `f_rest` all return to their
> initialisation values, and `training_setup(opt)` immediately afterwards **discards all
> Adam moment state** `[repo: ms/train.py:204, 254, 285]`. At default settings this happens
> **five times** per run: iterations 5 000, 10 000, 15 000 (twice — sampling then reinit),
> and 20 000. `[inferred: repo ms/train.py:164, 203-204, 251-254, 285]`

### Not optimized, but state that persists across iterations

| Name | Shape | Role | Source |
|---|---|---|---|
| `mask_blur` | `(N,)` bool | accumulates "this Gaussian was blurry in some view since the last densify"; OR-ed each iteration, cleared after each densify/reinit | `[repo: ms/train.py:75, 151, 161, 205]` |
| `max_radii2D` | `(N,)` | 3DGS screen-size pruning state | `[repo: ms/train.py:147]` |
| `xyz_gradient_accum`, `denom` | `(N,1)` | 3DGS densification statistics | `[repo: ms/train.py:148]` |

---

## 3.2 Dependent variables (derived each forward pass)

### From the forked rasterizer `diff_gaussian_rasterization_ms`

| Symbol (paper) | Repo key | Shape | Definition | Source |
|---|---|---|---|---|
| `w_i` | (internal) | per-pixel | blending weight `T_i·α_i·G_i^{2D}(x)` | `[paper Eq. 1]` |
| `I_i¹` | `accum_weights` | `(N,)` | `Σ_j w_ij` over all rays hitting `G_i` in this view | `[paper §3.2]` `[repo: gaussian_renderer/__init__.py:189]` |
| `S_i^{proj}` | `area_proj` | `(N,)` | number of pixels `G_i` projects onto (`accum_weights_count`) | `[paper Eq. 12]` `[repo: gaussian_renderer/__init__.py:190]` |
| `S_i` | `area_max` | `(N,)` | **maximum-contribution area** — number of pixels where `i = argmax_k w_k` (`accum_max_count`) | `[paper Eq. 2]` `[repo: gaussian_renderer/__init__.py:191]` |
| `i_max(x)` | (implicit) | `(H,W)` | index of the argmax-weight Gaussian at pixel `x` | `[paper §4.1]` |
| `d_i^{mid}` / `out_pts` | `out_pts` | `(3,H,W)` | the world-space **mid-point** of the ray/ellipsoid intersection for the argmax Gaussian | `[paper §4.1, App. D / Eq. 7]` `[repo: ms/train.py:173]` |
| `α_accum` | `accum_alpha` | `(1,H,W)` | accumulated opacity along the pixel's ray | `[repo: ms/train.py:174]` |

### Derived in Python

| Symbol | Definition | Source |
|---|---|---|
| `G^{blur}` | `{G_i : S_i > θ_blur·H·W}` — accumulated as `mask_blur` | `[paper Eq. 2]` `[repo: ms/train.py:151]` |
| `G^{int}` | `{G_i : i ∈ I_max}` — realised as `imp_score[accum_area_max == 0] = 0` | `[paper Eq. 3]` `[repo: ms/train.py:232]` |
| `I_i¹` (aggregated) | `Σ_m accum_weights^{(m)}` — the **indoor** metric | `[paper §3.2, App. E]` `[repo: ms/train.py:230]` |
| `I_i²` (aggregated) | `Σ_m (accum_weights^{(m)} / area_proj^{(m)})·𝟙[i ∈ I_max^{(m)}]` — the **outdoor** metric | `[paper Eq. 12]` `[repo: ms/train.py:225-228]` |
| `P_i` | `I_i / Σ_k I_k` — the sampling probability | `[paper §4.2]` `[repo: ms/train.py:233]` |
| depth-reinit pixel prob | `(1 − α_accum) / Σ(1 − α_accum)` — **not in the paper** | `[repo: ms/train.py:177-179]` |

---

## 3.3 Fixed / given inputs

### Data

| Quantity | Value | Source |
|---|---|---|
| Datasets | Mip-NeRF 360 [2], Tanks&Temples [18], Deep Blending [14] | `[paper §6]` |
| Split / resolution | "identical processing details … scene selection, train/test split, and image resolution, as specified in the official implementation of 3DGS" | `[paper §6]` |
| Resolution flags | `-i images_4` (Mip-NeRF 360 outdoor), `-i images_2` (indoor), default elsewhere | `[repo: README.md]` |
| Dense-init experiment | MVS [33] points, randomly subsampled to **2 M** | `[paper App. B]` |

### Hyperparameters — Mini-Splatting-specific (all CLI args in `ms/train.py`)

| Name | Default | Paper value | Match? |
|---|---|---|---|
| `--simp_iteration1` | `15 000` | 15 K | ✅ `[paper App. F]` |
| `--simp_iteration2` | `20 000` | 20 K | ✅ `[paper App. F]` |
| `--num_depth` | `3 500 000` | "around 3.5 million" | ✅ `[paper §4.1]` |
| `--num_max` | `4 500 000` | — | ❌ **not in the paper** (hard cap on `N` during densification) |
| `--sampling_factor` | `0.5` | — | ❌ **not in the paper** (this is the knob that generates Fig. 7's curve) |
| `--imp_metric` | **required, no default** | `indoor`→`I¹`, `outdoor`→`I²` | ✅ `[paper App. E]` |
| `θ_blur` (implicit) | `1/5000 = 2×10⁻⁴` | `2×10⁻⁴` | ✅ `[paper Eq. 2]` vs `[repo: ms/train.py:151]` |
| CDF prune threshold | `0.99` | — | ❌ **not in the paper** `[repo: ms/train.py:282]` |
| Depth-reinit interval | every `5 000` (`i % 5000 == 0`) | "every 5K iterations" | ✅ `[paper App. F]` `[repo: ms/train.py:164]` |
| SH ramp | `oneupSHdegree()` every 1 000 it **after** 15 K | "enable SH … after simplification (15K)" | ✅ `[paper §5]` `[repo: ms/train.py:102-103]` |

### Hyperparameters — inherited 3DGS (`arguments/__init__.py`)

| Name | Value | Note |
|---|---|---|
| `iterations` | `30 000` | `[repo: arguments/__init__.py:73]`; matches `[paper §5]` |
| `lambda_dssim` | `0.2` | unchanged |
| `percent_dense` | `0.01` | unchanged |
| `densification_interval` | `100` | unchanged, but skipped when `i % 5000 == 0` |
| `densify_from_iter` / `densify_until_iter` | `500` / `15 000` | unchanged |
| `densify_grad_threshold` | `2e-4` | unchanged |
| `opacity_reset_interval` | `3 000` | ⚠ **the reset itself is never called**; the value survives only as the `size_threshold` switch at `[repo: ms/train.py:155]` |
| `sh_degree` (`ModelParams`) | `3` | ⚠ **ignored at construction** — `GaussianModel(sh_degree=0)` `[repo: ms/train.py:56]`; only read back at `[repo: ms/train.py:250]` |
| `_eval` | `False` | `--eval` must be passed; the README's commands **do** include it ✅ |
| min opacity for prune | `0.005` | hard-coded `[repo: ms/train.py:159]` |

### Mini-Splatting-C

| Name | Value | Source |
|---|---|---|
| RAHT depth | `16` | `[paper App. F]` = `[repo: ms_c/run.py:135]` |
| Quantization step | `0.02` | `[paper App. F]` = `[repo: ms_c/run.py:136]` |
| Positions | stored as **float32** (`pos_remain`) | `[paper App. F]` = `[repo: ms_c/run.py:173]` |
| Entropy coder | `numpy.savez_compressed` (zlib) | `[paper App. F]` = `[repo: ms_c/run.py:173]` |
| Voxel dedup | `np.unique` on the 2¹⁶ grid | ❌ **not in the paper** `[repo: ms_c/run.py:144]` |

### Variant differences (`ms/` vs `ms_d/`)

| Behaviour | `ms/` | `ms_d/` | Source |
|---|---|---|---|
| Simplification at 15 K / 20 K | ✅ | ❌ removed | `[repo: diff ms/train.py ms_d/train.py]` |
| `num_max` cap | `4.5 M` | **none** | `[repo: ms/train.py:153 vs ms_d/train.py:133]` |
| Depth-reinit sampling | `np.random.choice(..., replace=False)` | `np.random.choice(..., p=prob)` **with replacement**, then `np.unique` ⇒ **fewer** unique points than requested | `[repo: ms/train.py:189-190 vs ms_d/train.py:169-170]` |
| LR-schedule rewind boundary | `simp_iteration1` (15 K) | `densify_until_iter` (15 K) | same value by default |
