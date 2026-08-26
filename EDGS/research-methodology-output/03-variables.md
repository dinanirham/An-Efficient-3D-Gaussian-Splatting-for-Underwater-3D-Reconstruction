# §3 — Formal variable table

`N` = number of Gaussians. `H, W` = image resolution. `J` = neighbours per reference.
`M` = matches per reference. Paper notation writes a Gaussian's parameters as
`{g_i^x, Σ_i, g_i^c, g_i^α}` `[paper §3.1]`.

---

## 3.1 Independent variables (directly optimized)

**Unchanged from 3DGS — EDGS introduces zero new optimized parameters.** What it changes is
the *initialization* of the existing ones, and (undocumented) two schedule terms.

| Paper symbol | Repo name | Shape | **EDGS initialization** | lr | Source |
|---|---|---|---|---|---|
| `g_i^x` | `_xyz` | `(N, 3)` | **triangulated 3D point** from the correspondence pair — not an SfM point | `1.6e-4 → 1.6e-6`, but see `max_lr` below | `[paper §3.3 / Eq. 7]` `[repo: corr_init.py:657]` |
| `g_i^c` (DC) | `_features_dc` | `(N, 1, 3)` | `RGB2SH(reference-image pixel colour / 255)` | `feature_lr = 2.5e-3` | `[paper §3.5]` `[repo: corr_init.py:658]` |
| — (SH rest) | `_features_rest` | `(N, 15, 3)` | **`0`** ⚠️ — §3.5's least-squares SH fit is **not implemented** | `2.5e-3 / 20` | `[repo: corr_init.py:659, 871]` |
| `g_i^α` | `_opacity` | `(N, 1)` | logit `= 0` ⇒ `α = 0.5`; **`−10`** if reproj-error > `proj_err_tolerance` ⇒ `α ≈ 4.5e-5` | `opacity_lr = **0.025**` (3DGS uses 0.05 — **halved**) | `[repo: corr_init.py:660-666; configs/gs/base.yaml]` |
| `Σ_i` (scale part) | `_scaling` | `(N, 3)` | `inv_act(‖μ − campos_ref‖ · 0.001)`, **isotropic**, then **× 0.5** globally | `scaling_lr = 5e-3` | `[repo: corr_init.py:668-670; trainer.py:254]` |
| `Σ_i` (rotation part) | `_rotation` | `(N, 4)` | copy of `_rotation[-1]` (the last pre-existing Gaussian → identity) | `rotation_lr = 1e-3` | `[repo: corr_init.py:671]` |
| — | exposure | per-camera | 3DGS's newer per-image exposure compensation | `1e-2 → 1e-4` | `[repo: configs/gs/base.yaml exposure_lr_*]` |

> **Two undocumented schedule modifications**, both in `train_step_gs`:
> - **`max_lr: True`** (default) ⇒ `update_learning_rate(max(gs_step, 8000))`
>   `[repo: trainer.py:146-147]`. The exponentially-decaying **position** LR is clamped to
>   its step-8000 value, so EDGS *never* uses 3DGS's high early LR. Sensible — the
>   positions are already near-correct — but absent from the paper.
> - **`reduce_opacity: True`** (default) ⇒ every 10 steps while `gs_step < 15000`,
>   `_opacity ← log(exp(_opacity) · 0.99)`, i.e. **logit − 0.01005**
>   `[repo: trainer.py:81-85]`. ≈1500 applications, cumulative logit shift ≈ **−15**.

### Deleted machinery

| 3DGS component | EDGS status | Evidence |
|---|---|---|
| Gradient-triggered clone/split | **disabled** when `no_densify=True` (the README's command) | `[paper Tab. 1 'Densification free' ✓]` `[repo: trainer.py:75-80; README.md]` |
| `reset_opacity()` | **never fires** — `opacity_reset_interval = 30000 = iterations`, and the call is gated by `gs_step < densify_until_iter = 15000` | `[repo: configs/gs/base.yaml; trainer.py:195-205]` |
| SfM point cloud | **pruned after initialization** unless `add_SfM_init` (default `False`) | `[repo: trainer.py:243-251; configs/train.yaml]` |
| Screen-size pruning | inactive in the `no_densify` path — only `α < 0.005` pruning remains | `[repo: trainer.py:258-264]` |

---

## 3.2 Dependent variables (derived once, at initialization)

| Symbol | Shape | Definition | Source |
|---|---|---|---|
| `I_i` | `(3,H,W)` | reference image | `[paper §3.2]` |
| `𝓘_i = {I_1..I_J}` | — | its `J = nns_per_ref` nearest neighbours by **Frobenius distance between `world_view_transform` matrices** | `[paper §3.2]` `[repo: corr_init.py:41, 561]` |
| `W_ij` | `(2,H,W)` | dense **forward warp field** from `I_i` to `I_j`, from RoMa | `[paper Eq. 3]` `[repo: corr_init.py:100-177]` |
| `c_ij` | `(H,W)` | **correspondence confidence** ("certainty") from RoMa | `[paper Eq. 3]` `[repo: corr_init.py:143-155]` |
| `(u_i^k, v_i^k)`, `(u_j^k, v_j^k)` | — | matched pixel pair `k` | `[paper §3.3]` `[repo: corr_init.py:315]` |
| `P^i, P^j` | `(4,3)` | camera projection matrices | `[paper Eq. 4]` |
| `A, b` | `(4,3)`, `(4,)` | the DLT system `A g^x = −b` | `[paper Eq. 6]` `[repo: corr_init.py:412-470]` |
| `g_k^x` | `(3,)` | triangulated point, `argmin_x ‖Ax + b‖²`, via `torch.linalg.lstsq` | `[paper Eq. 7]` `[repo: corr_init.py:471-472]` |
| `ε_i^k`, `ε_j^k` | scalars | reprojection error `‖π(P^i, g_k^x) − (u_i^k, v_i^k)‖₂` | `[paper Eq. 8]` |
| `ε_ij^k` | scalar | `max(ε_i^k, ε_j^k)` | `[paper §3.4]` `[repo: corr_init.py:492-519]` |
| `p_ij^corr` | — | `U{k : c_ij(u_i^k,v_i^k) > τ_corr}` — uniform over high-confidence matches | `[paper Eq. 9]` |
| `p_ij^proj` | — | `U{k : ε_ij^k < τ_proj}` — uniform over low-reprojection-error matches. ⚠️ **implemented as an opacity mask, not a sampling distribution** | `[paper Eq. 10]` `[repo: corr_init.py:662-666]` |
| `p_i(k)` | — | `max_{j∈𝓘_i}( p_ij^corr · p_ij^proj )` | `[paper Eq. 11]` |
| `p(k)` | — | `Π_i p_i^k` — global sampling distribution | `[paper §3.4]` |
| `O_k` | `(n,3)` | `n` RGB observations of splat `k` from directions `v_1..v_n` | `[paper §3.5]` — **no code** |
| `Y_k` | `(n,16)` | real SH basis (degree ≤ 3) evaluated at those directions | `[paper §3.5]` — **no code** |
| `Ĥ_k` | `(16,3)` | `argmin_H ‖Y_k H − O_k‖_F²`, or `Y_k^+ O_k` when `n < 16` | `[paper Eqs. 12-13]` — **no code** |

> **`O_k`, `Y_k`, `Ĥ_k` have no counterpart in the repository.** `grep -rn "pinv\|lstsq"`
> over `source/` returns exactly one hit — `corr_init.py:472`, which is the **triangulation**
> solve of Eq. 7, not the SH solve of Eq. 12. `_features_rest` is set to zero in **both**
> initialization functions `[repo: corr_init.py:659, 871]`.

---

## 3.3 Fixed / given inputs

### Data

| Quantity | Value | Source |
|---|---|---|
| Datasets | Mip-NeRF 360 (**9** scenes), Tanks&Temples (**2**), Deep Blending (**2**) | `[paper §4.1]` |
| Poses | COLMAP | `[paper §1]` |
| Matcher `M` | **RoMa** (default); LoFTR / DKM / RAFT ablated | `[paper §3.2, §4.5]` `[repo: corr_init.py:17]` |
| Hardware | **NVIDIA A100**, competitors re-run on the same hardware | `[paper §4.1]` |

### `init_wC` — the EDGS-specific hyperparameters `[repo: configs/train.yaml]`

| Name | Default | README command | Meaning |
|---|---|---|---|
| `use` | `True` | — | enable EDGS init |
| `matches_per_ref` | `15_000` | **`20000`** | correspondences sampled per reference view (`M`) |
| `num_refs` | `180` | `180` | reference views selected by K-means (`K`) |
| `nns_per_ref` | `3` | `3` | neighbours per reference (`J`); **`1` switches to `init_gaussians_with_corr_fast`** `[repo: trainer.py:230-233]` |
| `scaling_factor` | `0.001` | — | initial scale = `dist_to_cam · 0.001` |
| `proj_err_tolerance` | `0.01` | — | `τ_proj`; above this, opacity logit `−10` |
| `roma_model` | `"outdoors"` | — | `"indoors"` also available |
| `add_SfM_init` | `False` | — | if `False`, **SfM points are deleted** |
| — | — | — | ⚠️ `τ_corr` of `[paper Eq. 9]` has **no config key** |

> Upper bound on initial Gaussians: `num_refs × matches_per_ref` = 180 × 15 000 =
> **2.7 M** (README's 20 000 → **3.6 M**), before the `α ≈ 0` masking and subsequent
> pruning. Final counts are 1.4–1.9 M `[paper Tab. 1]`. `[inferred]`

### 3DGS optimization `[repo: configs/gs/base.yaml]`

| Name | EDGS | 3DGS default | Note |
|---|---|---|---|
| `iterations` | 30 000 | 30 000 | but `train.gs_epochs` defaults to **`0`** — must be passed |
| `sh_degree` | 3 | 3 | |
| `lambda_dssim` | 0.2 | 0.2 | |
| `position_lr_init/final` | 1.6e-4 / 1.6e-6 | same | ⚠️ but clamped by `max_lr` |
| `feature_lr` | 2.5e-3 | same | |
| **`opacity_lr`** | **0.025** | **0.05** | **halved** |
| `scaling_lr` | 5e-3 | same | |
| `rotation_lr` | 1e-3 | same | |
| `densify_from/until_iter` | 500 / 15 000 | same | inactive when `no_densify` |
| `densify_grad_threshold` | 2e-4 | same | |
| **`opacity_reset_interval`** | **30 000** | **3 000** | ⇒ **reset never fires** |
| `batch_size` | 64 | — | ⚠️ **read but never used**; `train_step_gs` samples **one** camera `[repo: trainer.py:48, 157]` |
| `dataset.eval` | `false` | — | ⚠️ and `train.py:38` hard-codes `"eval": False` into the emitted `cfg_args` |
| `antialiasing` | `false` | — | indicates a recent 3DGS release |
| `exposure_lr_*` | present | — | per-image exposure compensation |

### `train` block `[repo: configs/train.yaml]`

| Name | Config default | README says | ⚠️ |
|---|---|---|---|
| `gs_epochs` | **`0`** | `30000` in the command | training does nothing unless overridden |
| `no_densify` | **`False`** | *"Disables densification. **True by default**."* | **README contradicts the config** |
| `reduce_opacity` | `True` | not documented | undocumented mechanism |
| `max_lr` | `True` | not documented | undocumented mechanism |
| `seed` | `228` | not documented | |
| `wandb.mode` | **`"online"`** | *"Default: `"disabled"`"* | **README contradicts the config** |
