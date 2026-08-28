# §3 — Merged variable table, tagged by origin

`N` = number of Gaussians at the current iteration. `H, W` = image height/width after
`--resolution` handling. `V` = number of training views. `K_cb` = codebook size.
Origin column: **A0** = SeaSplat baseline · **M1** = EDGS · **M2** = Mini-Splatting ·
**M3** = CompGS-VQ · **PI** = `[proposed integration]`, new to the combined method.

Symbols follow the recommended write-up notation of `../comparison-glossary.md` §6 where a
collision exists; see `09-glossary.md` for the mapping back to each source paper's glyphs.

---

## 3.1 Independent variables (directly optimized)

### Group 1 — the 3D Gaussian representation

Six parameter groups, one Adam group each, **inherited unchanged in type** by every
configuration. What changes across A0–A7 is *how they are initialized*, *how many of them
there are*, and *whether the forward pass reads them or their codebook substitutes*.

| Symbol | Repo name | Shape | Init in **A0** | Init under **M1** | lr | Origin |
|---|---|---|---|---|---|---|
| `μ` | `_xyz` | `(N,3)` | COLMAP sparse points `[repo: scene/gaussian_model.py]` | **triangulated correspondence point**, `argmin_x‖Ax+b‖²` via `lstsq` `[EDGS paper Eq.7; R:corr_init.py:657]` | exp `1.6e-4 → 1.6e-6`, `delay_mult=0.01` `[A0 repo: arguments/__init__.py:89-92]` | A0 / M1 |
| `f_dc` | `_features_dc` | `(N,1,3)` | `RGB2SH(COLMAP point colour)` | `RGB2SH(reference-image pixel / 255)` `[EDGS R:corr_init.py:658]` | `feature_lr = 2.5e-3` | A0 / M1 |
| `f_rest` | `_features_rest` | **`(N,0,3)` — empty** | n/a — `sh_degree = 0` `[A0 repo: arguments/__init__.py:49]` | n/a (EDGS's `f_rest ← 0` is inert here) | `feature_lr/20` | A0 |
| `o` | `_opacity` | `(N,1)` | `inverse_sigmoid(0.1)` | logit `0` (⇒ α=0.5), or **`−10`** if reprojection error > `τ_proj` `[EDGS R:corr_init.py:660-666]` | `0.05` (A0) / **`0.025`** under M1 `[EDGS configs/gs/base.yaml]` | A0 / M1 |
| `s` | `_scaling` | `(N,3)` | `log√(mean dist to 3 NN)` via `simple_knn` | `inv_act(‖μ − campos_ref‖ · 0.001)`, **isotropic**, then **× 0.5** globally `[EDGS R:corr_init.py:668-670; trainer.py:252-254]` | `5e-3` | A0 / M1 |
| `q` | `_rotation` | `(N,4)` | identity `[1,0,0,0]` | copy of `_rotation[-1]` `[EDGS R:corr_init.py:671]` | `1e-3` | A0 / M1 |

> **`sh_degree = 0` is the single most consequential inherited value in this table.**
> Per-Gaussian storage is **14 floats**, not 3DGS's 59
> `[../seasplat/08-computational-profile.md §8.4]`. It removes the 45-float block that M3's
> largest codebook exists to compress (`01-taxonomy.md` A3-a) and it removes the parameter
> M1's unimplemented §3.5 would have initialized (`02-pipeline.md` §2.3). Both effects are
> consequences of one flag.

> **Reset semantics under M2.** Mini-Splatting's `reinitial_pts` keeps **only** `μ` and the DC
> colour; `s`, `q`, `o` and `f_rest` return to their initialization values and
> `training_setup(opt)` **discards all Adam moment state**
> `[../mini-splatting/03-variables.md §3.1]`. Under the simplification-only reading of M2
> adopted here (`01-taxonomy.md` A2-a), this fires **twice** — after the 15 000 sampling step
> and after the 20 000 CDF prune — not five times. `[PI]` That scoping decision must be
> stated, because Mini-Splatting's published numbers come from the five-restart schedule.

### Group 2 — the medium model (baseline only; two separate Adam optimizers, `lr = 1e-2`)

**Untouched by all three mechanisms**, and this is a fact worth foregrounding: no mechanism
adds, removes, or reparameterises a medium variable.

| Symbol | Repo name | Shape | Init | Origin |
|---|---|---|---|---|
| `β_att` (paper `β^D`) | `at_model.attenuation_conv_params` | `(3,1,1,1)` | **`[1.1, 0.95, 0.95]`** fixed `[repo: models.py:216-218]` | A0 |
| `β_bs` (paper `β^B`) | `bs_model.backscatter_conv_params` | `(3,1,1,1)` | `U(0,1)³` `[repo: models.py:54]` | A0 |
| `B^∞` | `bs_model.B_inf` | `(3,1,1)` | `U(0,1)³` as a **logit**, then **overwritten by `learned_bg`** at `seathru_from_iter` `[repo: train.py:61,77,209-212]` | A0 |
| `bg` | `learned_bg` | `(3,)` | logit of `[0.05, 0.25, 0.80]` `[repo: train.py:126-131]` — **absent from the paper** | A0 |

> **Total learned medium parameters: 9 scalars** (+3 for `bg`, folded into `B^∞`)
> `[../seasplat/03-variables.md §3.1]`. This is the `O(1)` claim, and it survives the
> composition intact.

### Group 3 — quantization state (M3 only)

Not "optimized" in the Adam sense, but they are learned state that persists and is stored.

| Symbol | Repo name | Shape | Init / update | Origin |
|---|---|---|---|---|
| `C_dc` | `kmeans_dc.centers` | `(K_cb, 3)` | K-means over `_features_dc`; centroids re-averaged **every** iteration, assignments **every `t = 100`** `[compact3d paper §3; R:kmeans_quantize.py:46-61 vs 138-172]` | M3 |
| `C_scale` | `kmeans_sc.centers` | `(K_cb, 3)` | same, on `_scaling` **before `exp`** `[compact3d paper §4]` | M3 |
| `C_rot` | `kmeans_rot.centers` | `(K_cb, 4)` | same, on `_rotation` **before normalization** | M3 |
| ~~`C_sh`~~ | ~~`kmeans_sh.centers`~~ | ~~`(K_cb,45)`~~ | **DROPPED** — `f_rest` is empty under `sh_degree = 0` | **PI** |
| `idx_g` | `kmeans_*.cls_ids` | `(N,)` per group | argmin assignment, cached between reassignments | M3 |

---

## 3.2 Dependent variables (derived each forward pass)

| Symbol | Shape | Definition | Origin |
|---|---|---|---|
| `Ĵ` | `(3,H,W)` | rasterized colour = **medium-free** radiance | A0 `[paper §IV.A]` |
| `α` | `(1,H,W)` | accumulated opacity from the rasterizer | A0 |
| `Z_raw` | `(1,H,W)` | second rasterization pass, `override_color = z_cam` | A0 `[repo: gaussian_renderer/__init__.py:116-137]` |
| **`Ẑ`** | `(1,H,W)` | `Z_raw/α`, NaN→max, `÷ normalize_depth`, then **min–max renormalised to [0,1]** | A0 `[repo: train.py:222-237]` — ⚠️ **interaction candidate, see §3.5** |
| `Â` | `(1,3,H,W)` | `exp(−clamp(β_att ⊛ Ẑ, ≥0))` | A0 |
| `B̂` | `(1,3,H,W)` | `σ(B^∞) ⊙ (1 − exp(−clamp(β_bs ⊛ Ẑ, ≥0)))` | A0 |
| `D̂` | `(1,3,H,W)` | `Ĵ ⊙ Â` — the modelled direct image | A0 |
| `Î` | `(1,3,H,W)` | `clamp(D̂ + B̂, 0, 1)` — what the photometric loss scores | A0 |
| `D̃` | `(1,3,H,W)` | `I − B̂'`, both detached — the argument of `L_bs`. **Not** the same object as `D̂` | A0 `[../seasplat/03-variables.md naming trap]` |
| `Â'`, `B̂'` | as above | depth-**detached** duplicates | A0 |
| `ẑ_g` | per group | `C_g[idx_g]` — the quantized attribute substituted into the render | M3 |
| `W_ij`, `c_ij` | `(2,H,W)`, `(H,W)` | RoMa dense warp + confidence — **derived once, at IP1** | M1 |
| `ε_ij^k` | scalar per match | `max(ε_i^k, ε_j^k)` reprojection error | M1 |
| `I_imp` | `(N,)` | importance score: `Σ_v accum_weights` (indoor) or `Σ_v accum_weights/area_proj · 1[i ∈ I_max]` (outdoor) | M2 `[mini-splatting paper §3.2, Eq.12]` |
| `A_max` | `(N,)` | `area_max` — pixel count where `i` is the argmax contributor | M2 (**needs the forked rasterizer**) |
| `P_i` | `(N,)` | `I_imp / Σ I_imp`, with `I_imp[A_max == 0] ← 0` | M2 |
| **`Ẑ_min`, `Ẑ_max`** | scalars per frame | the per-frame min–max normalisation constants | **PI** — promoted from implicit to explicit state; see §3.5 |

---

## 3.3 Fixed / given inputs

### Data and camera

| Quantity | Value | Origin |
|---|---|---|
| `I` | captured white-balanced frames, `(3,H,W)` ∈ [0,1] | A0 |
| `K_cam`, `T^cam_world` | COLMAP intrinsics / extrinsics | A0 |
| Dataset | SeaThru-NeRF: Curasao (21 imgs), IUI3-RedSea (29), JapaneseGradens-RedSea (20), Panama (18) — **88 total** `[dataset/SeathruNeRF_dataset/, counted on disk]` | A0 |
| `znear`, `zfar` | `0.01`, `100.0` | A0 |

### Hyperparameters — baseline (A0), from `arguments/__init__.py` @ `ddc6259`

| Name | Default | Note |
|---|---|---|
| `iterations` | `30 000` | but ≈43 000 *effective* optimizer steps `[../seasplat/08-computational-profile.md §8.3]` |
| `sh_degree` | **`0`** | SeaSplat-specific; upstream 3DGS uses 3 |
| `lambda_dssim` | `0.2` | shared by all four methods `[../comparison-glossary.md §1.5]` |
| `do_seathru` | **`False`** | must be passed explicitly |
| `seathru_from_iter` | **`9 000 000`** | README passes `10000` — ⚠️ **interaction candidate, §3.5** |
| `bs_at_lr` | `1e-2` | medium optimizers |
| `update_bs_at_interval` / `update_bs_at_count` | `100` / `50` | the alternating burst schedule |
| `norm_depth_max` | **`True`** | ⚠️ **the single most important interaction candidate, §3.5** |
| `filter_depth` | `True` | `Ẑ ← Z/α` |
| `densify_from/until_iter` | `500` / `15 000` | ⚠️ overridden by M1 |
| `opacity_reset_interval` | `3 000` | ⚠️ removed by M2, unreachable under M1 |
| `dwr_lambda`, `dcp_loss_lambda`, `gw_loss_lambda`, `sat_loss_lambda`, `bg_lambda`, `depth_smooth_lambda` | `1.0, 1.0, 0.1, 2.0, 0.01, 2.0` | the six loss weights, spanning 200× |

### Hyperparameters — M1 (EDGS `init_wC` block)

| Name | EDGS default | **Combined-method value** | Note |
|---|---|---|---|
| `num_refs` (K) | `180` | **`min(180, V)`** `[PI]` | V is 18–29 per scene — the default exceeds the view count entirely (`02-pipeline.md` §2.3) |
| `matches_per_ref` (M) | `15 000` (README: `20000`) | to be set; determines the density regime | upper bound on init count is `num_refs × matches_per_ref` |
| `nns_per_ref` (J) | `3` | `3` — note `1` switches to a *different, faster* code path `[EDGS R:trainer.py:230-233]` |
| `scaling_factor` | `0.001` | `0.001` | then × 0.5 globally |
| `proj_err_tolerance` (τ_proj) | `0.01` | `0.01` | failing points get opacity logit −10, not deletion |
| `τ_corr` | **no config key** — inherits RoMa's `sample_thresh` (=0.05) | must be **exposed and reported** `[PI]` | `[../EDGS/11-paper-vs-repo-disagreements.md D-8]` |
| `roma_model` | `"outdoors"` | ⚠️ **neither "outdoors" nor "indoors" describes an underwater scene** `[PI]` | choice must be justified or ablated |
| `add_SfM_init` | `False` | ⚠️ **candidate to flip to `True`** `[PI]` — SfM points are the only geometry not derived from a matcher that fails in water (`01-taxonomy.md` A1-b) |
| `reduce_opacity` | `True` | ⚠️ interacts with `L_op`; see §3.5 |
| `max_lr` | `True` | ⚠️ interacts with M2's LR rewind; see §3.5 |

### Hyperparameters — M2 (Mini-Splatting)

| Name | Default | Note |
|---|---|---|
| `simp_iteration1` / `simp_iteration2` | `15 000` / `20 000` | ⚠️ **`simp_iteration1` coincides with `densify_until_iter` and sits after `seathru_from_iter`** — see §3.5 |
| `sampling_factor` | `0.5` | **not in the paper** `[../mini-splatting/11-paper-vs-repo-disagreements.md D-4]`; replaced here by an explicit target count `[PI]` |
| CDF prune threshold | `0.99` | **not in the paper**, same delta |
| `imp_metric` | **required, no default** | ⚠️ `indoor`/`outdoor` only; neither is underwater (`01-taxonomy.md` A2-a) |
| `num_depth`, `num_max` | `3.5 M`, `4.5 M` | only relevant if the densification half of M2 is used |
| `θ_blur` | `2e-4` | blur-split threshold, densification half only |

### Hyperparameters — M3 (CompGS-VQ)

| Name | Paper | `run.sh` | **Combined-method value** |
|---|---|---|---|
| `kmeans_st_iter` | `20 000` | `15 000` | ⚠️ must be **after** `simp_iteration2` `[PI]` — see the ordering argument in `07-pseudocode.md` |
| `kmeans_freq` (t) | `100` | `100` | `100` |
| `kmeans_iters` | `1` | `10` | `1` (the paper's value) `[PI]` |
| `K_cb` | dc 4096 · sh 4096 · cov 16384/32768 | 4096 / 512 | dc, scale, rot only `[PI]` |
| `opacity_reg` | on, λ_reg = 1e-7, 15 K–20 K | on | **OFF** `[PI]` — confounds M2 (`01-taxonomy.md` A3-c) |
| `n_bits` per index | implied `ceil(log2(K_cb))` | `ceil(log2(N))` — a bug | **`ceil(log2(K_cb))`** `[PI]` `[../compact3d/11-paper-vs-repo-disagreements.md D-4]` |

> **Two CLI-default traps carried forward.** CompGS-VQ's `--kmeans_st_iter` defaults to
> `30000 = total_iterations`, so the quantizer **never fires** on a bare run
> `[../compact3d/11-paper-vs-repo-disagreements.md D-6]`; EDGS's `train.gs_epochs` defaults
> to `0`, so **training does nothing** on a bare run `[../EDGS/03-variables.md]`. Both are
> silent no-ops, not errors. A combined-method run script must assert that each enabled
> mechanism actually fired.

---

## 3.4 Off-by-default in A0 and left off

`use_depth_l1_loss`, `use_alpha_smooth_loss`, `use_opacity_prior`, `use_rgb_sv_loss`,
`use_binf_loss`, `use_dsc_at_loss`, `use_depth_weighted_l1/l2`, `do_z_score`,
`disable_attenuation`, `use_gt_depth`, `use_bs_residual`, `use_at_v2` — all `False`
`[../seasplat/03-variables.md §3.3]`. None is touched by any mechanism. Noting them matters
only because SeaSplat registers booleans with `action="store_true"`, so the ~12 flags
defaulting `True` **cannot be disabled from the CLI** without editing the source
`[../seasplat/11-paper-vs-repo-disagreements.md D-12]` — which is the mechanism by which a
2³ feature-flag scheme has to be built (see `chapter/04-implementation-details.md`).

---

## 3.5 Shared variables — the interaction candidates

Every variable below is written by **more than one** of {A0, M1, M2, M3}. These are the
hypotheses the experimental matrix exists to test, and none of them is measured in this
evidence base.

### IC-1 — `o` / `_opacity` — **four writers, highest risk**

| Writer | Action | Origin |
|---|---|---|
| A0 `L_op` | gradient drives `α → 0` where `‖Î − σ(B^∞)‖₂ < 0.2√3`; λ = 0.01; **only `α` receives gradient** | `[../seasplat/07-pseudocode.md line 30]` |
| A0 3DGS ADC | `reset_opacity()` every 3 000 iterations; prune `α < 0.005` | `[../seasplat/07-pseudocode.md line 64]` |
| M1 | `logit ← logit + log(0.99)` every 10 steps for 15 000 steps (Σ ≈ **−15**); `opacity_lr` **halved**; `reset_opacity()` becomes unreachable | `[../EDGS/05-constraints.md M-5]` |
| M2 | `reset_opacity()` **removed entirely**; `o ← inverse_sigmoid(0.1)` at every reinit | `[../mini-splatting/11-paper-vs-repo-disagreements.md D-1; ../mini-splatting/03-variables.md]` |
| M3 | ℓ1 `Σα` + prune 0.005 — **disabled here** `[PI]` | `[../compact3d/04-loss.md]` |

**Why this is the sharpest interaction candidate.** `L_op` is the term that carries
SeaSplat's headline qualitative result — it is the only ablation row that moves in-medium
PSNR materially (**+2.42 dB alone**) `[../seasplat/04-loss.md §4.4]` — and its entire job is
to suppress water-column floaters by zeroing opacity. M1 and M2 both rewrite the opacity
dynamics that `L_op` was tuned against, in opposite directions: M1 adds a strong global
downward pressure, M2 periodically resets every opacity back *up* to 0.1. Under A4 and A7
both are active. **The prediction is that `bg_lambda = 0.01` is not the right value in any
configuration except A0**, and that is checkable.

### IC-2 — `Ẑ` and its normalisation constants — **the well-posedness interaction**

| Writer | Action | Origin |
|---|---|---|
| A0 | `Ẑ = Z_raw/α`, then **min–max renormalised to [0,1] per frame** (`norm_depth_max = True`) | `[repo: train.py:233-237]` |
| A0 | consumed by `Â`, `B̂`, `L_Z-recon`, `L_Zsmooth` — the entire medium model | `[../seasplat/02-pipeline.md Stage C]` |
| M1 | replaces the geometry that produces `Z_raw`; removes the ADC that refines it | `[../EDGS/03-variables.md]` |
| M2 | removing 60–90% of primitives **changes `Ẑ_min`, `Ẑ_max`** for every frame | `[inferred]` |
| M3 | quantized `s`, `q` change the rendered surface, hence `Z_raw` | `[inferred]` |

**Why this is the claim-(c) interaction.** `β` and `Ẑ` enter the model **only as the product
`βẐ`** — SeaSplat's degeneracy D-2, whose stated invariance is
`Ẑ ← cẐ, β ← β/c` `[../seasplat/05-constraints.md D-2]`. A per-frame min–max renormalisation
means the learned `β` are "in units of *normalised per-frame depth*, **not** inverse metres"
and "the same physical depth maps to different `Ẑ` in different frames, which is in tension
with the global-`β` assumption" `[../seasplat/05-constraints.md §5.3]`. A budget prune
therefore does not merely remove primitives — **it applies an uncontrolled scale factor `c`
to the medium model's only input, in the middle of training.** The `[PI]` remedy (a
medium-only re-warm-up burst immediately after each simplification event) is specified in
`02-pipeline.md` §2.6 and `07-pseudocode.md` line 55, and `Ẑ_min`/`Ẑ_max` are promoted to
explicit logged state in §3.2 above so the effect can be measured rather than assumed.

### IC-3 — the learning-rate schedule for `μ`

| Writer | Action | Origin |
|---|---|---|
| A0 | 3DGS exponential decay `1.6e-4 → 1.6e-6` over 30 000 | `[repo: arguments/__init__.py:89-92]` |
| M1 | `update_lr(max(i, 8000))` — **clamped**, never uses the high early LR | `[../EDGS/05-constraints.md M-7]` |
| M2 | `update_lr(i − simp_iteration1 + 5000)` — **rewound** after simplification | `[../mini-splatting/05-constraints.md M-8]` |

Contradictory intents, both undocumented in their source papers, both on by default. The
`[PI]` resolution — M2's rewind takes precedence from `simp_iteration1` onward — is stated in
`02-pipeline.md` §2.6 and recorded as a combined-method-specific decision in
`06-implementation-deltas.md`.

### IC-4 — iteration-schedule collisions

Three schedules land on overlapping iteration ranges, and the collisions are not accidental
— all three methods use 3DGS's 30 000-iteration budget with the same `densify_until_iter`.

| Iteration | A0 | M1 | M2 | M3 |
|---|---|---|---|---|
| 0 | — | **dense init** | — | — |
| 500–15 000 | densify every 100 | *(ADC off)* opacity decay every 10 | blur split, depth reinit every 5 000 | — |
| **10 000** | **`seathru_from_iter`** — medium turns on, 1 000 + 2 000 warm-up steps | — | — | — |
| 10 000 | `gw_from_iter` — `L_gw` enters | — | — | — |
| **15 000** | `densify_until_iter` | opacity decay stops | **`simp_iteration1`** — sample to budget | *(`run.sh` would start VQ here)* |
| **20 000** | — | — | **`simp_iteration2`** — CDF prune 0.99 | *(paper starts VQ here)* |
| **> 20 000** | — | — | — | **`kmeans_st_iter`** `[PI]` |
| 30 000 | end | end | end | end |

> `[PI]` **`kmeans_st_iter` must be pushed past `simp_iteration2`.** Both CompGS-VQ's paper
> value (20 000) and its `run.sh` value (15 000) collide with M2's simplification events
> `[../compact3d/11-paper-vs-repo-disagreements.md D-2]`. A codebook fitted at 15 000 is
> fitted to a population that is about to be cut by 60–90% and then reset — the centroids
> would be stale by construction, and the quantization-aware training would spend its budget
> adapting parameters that are then discarded. The combined method sets
> `kmeans_st_iter > simp_iteration2`, which leaves fewer than 10 000 iterations of
> quantization-aware training. Whether that is enough is an open question; `../OMG/` reports
> that K-means in only the **final 1 000 iterations** costs ≤0.05 dB
> `[../compact3d/05-constraints.md M-1/M-2 note, citing OMG Tab. 4]`, which is the reason to
> expect it is.
