# §4 — Full loss function

## 4.1 The paper's statement

> `L = L_recon(Ĉ, C*) + L_prop(s, w) + λ·L_objnorm(w)`, with `λ = 0.0001`
> "chosen through cross-validation." `[paper Eq. 24]`

Three terms. This is a genuinely small objective compared with SeaSplat's seven, and the
repo agrees on the count — the disagreements are inside the terms, not in the list.

## 4.2 Term-by-term

### 1. `L_recon` — RawNeRF gradient-reweighted reconstruction loss

- **Paper form** `[paper Eq. 25]`:
  `L_recon(Ĉ, C*) = ( (Ĉ − C*) / (sg(Ĉ) + ε) )²`, with `ε = 10⁻³`, `sg` = stop-gradient.
- **Repo form** `[repo: internal/train_utils.py:95-102]`:
  ```python
  rgb_render_clip = jnp.minimum(1., rendering['rgb'])          # ← clipping, not in the paper
  resid_sq_clip   = (rgb_render_clip - batch.rgb[..., :3]) ** 2
  scaling_grad    = 1. / (1e-3 + jax.lax.stop_gradient(rgb_render_clip))
  data_loss       = resid_sq_clip * scaling_grad ** 2
  ```
- **Purpose.** The inputs are **linear** (un-tonemapped) images. A plain L2 on linear data
  is dominated by bright pixels; RawNeRF's reweighting is the first-order approximation of
  applying L2 *after* a log tonemap, which equalises relative error across the dynamic
  range. This is exactly the regime underwater imagery lives in — the red channel in the
  far field is orders of magnitude dimmer than the near-field blue.
- **What it prevents if removed** (i.e. using plain MSE): the far-field, red-starved
  regions contribute negligible gradient and the network simply does not reconstruct them —
  which is the failure the paper's headline result (recovering "far objects, which are
  severely occluded by the medium" `[paper §1]`) is about.
- **Delta:** the repo clips `Ĉ` at 1 before both the residual and the denominator
  (comment: *"Clip raw values against 1 to match sensor overexposure behavior"*). Once
  `Ĉ > 1` the gradient through the clip is zero, so **overexposed predictions receive no
  correction**. The paper's Eq. 25 has no clipping. This is inherited from upstream
  RawNeRF/multinerf but is a real change to the stated objective.

### 2. `L_prop` — proposal / interlevel loss

- **Paper:** "an inherent part of Mip-NeRF-360 [5]. It penalizes for the discrepancy
  between the distributions of object weights at 'original' and 'proposed' samplings,
  where only the latter is used for rendering." `[paper §4.4]`
- **Repo** `[repo: internal/train_utils.py:115-127]`: unchanged from multinerf —
  `Σ_levels mean(lossfun_outer(sg(sdist), sg(w), sdist_prop, w_prop))`. The **stop-gradients
  on the NeRF-level histogram** mean the loss trains only the proposal MLP.
- **Multiplier: `interlevel_loss_mult = 1`** `[repo: configs/llff_256_uw.gin]`.
- **What it prevents if removed:** the proposal MLP stops tracking the NeRF's density and
  the 32 fine samples land in empty space — catastrophic, since only 32 fine samples are
  used at this config `[repo: configs/llff_256_uw.gin Model.num_nerf_samples = 32]`.

### 3. `λ·L_objnorm` — binary-transmittance prior

- **Paper form** `[paper Eq. 26-27]`:
  `P(x) ∝ e^{−|x|/0.1} + e^{−|1−x|/0.1}`, `L_objnorm(w) = −log P(T^obj_i)`, `λ = 1e-4`.
  A **symmetric** mixture of two Laplacians with modes at 0 and 1.
- **Repo form** `[repo: internal/train_utils.py:153-167]`:
  ```python
  weights = last_ray_results['trans']                    # = T^obj
  data_loss = mean( -log( config.uw_acc_loss_factor * exp(-|1-T|/0.1)
                                                    + exp(-|T|/0.1) ) )
  loss = sig_mult * data_loss                            # sig_mult = 1e-4
  ```
  with **`uw_acc_loss_factor = 6`** `[repo: internal/configs.py:173]`, whose own comment
  reads: *"factor which encourages one of the terms in the accuracy loss to be more
  dominant — for the trans it encourages it to be 1 and for the weights zero."*
- **So the deployed prior is asymmetric**, weighting the `T^obj = 1` mode **6× more** than
  the `T^obj = 0` mode. The paper's Eq. 26 is symmetric and says nothing about a factor.
- **Purpose.** "To enforce binary separation between points in space that contain objects
  and those that contain solely a medium — we add a prior on the transmittance `T^obj_i` of
  each point on the ray to be either 0 or 1, not allowing semi-transparent objects."
  `[paper §4.4]`
- **What it prevents if removed:** the degenerate "semi-transparent object" solution in
  which `σ^obj` spreads a small density over the whole ray, mimicking the medium. This is
  the *single* prior standing between the model and the object/medium identifiability
  problem — see [`05-constraints.md`](05-constraints.md) D-1.
- **The `6×` bias makes physical sense** and arguably matters: on a forward-facing
  underwater scene most samples along most rays are *empty water*, where `T^obj` should
  stay at 1. Biasing toward the `T = 1` mode is a prior that "most of the ray is not
  object". But it is an undocumented modelling choice, not a symmetric regulariser.

### Off-by-default terms present in code

| Term | Flag | Note |
|---|---|---|
| `L_objnorm` on `Σ_i w^obj_i` instead of `T^obj` | `use_uw_acc_weights_loss = False` | the mirror-image asymmetry (`6×` on the `w = 0` mode) `[repo: train_utils.py:138-150]` |
| `L_sig_med` — std of `σ^bs`, `σ^attn` across the batch | `use_uw_sig_med_loss = False` | repo comment: *"use std loss on medium's densities to imply smoothness on the densities — **not in the paper**"* `[repo: configs.py:168, 174; train_utils.py:171-187]` |
| `L_distortion` (mip-NeRF 360) | `distortion_loss_mult = 0.` | **explicitly zeroed** in the UW gin, though it is a standard part of the base method. Not mentioned in the paper. |

## 4.3 The objective as actually implemented

```
L_total = 1.0    · L_recon      # data_loss_mult,      RawNeRF w/ clipping at 1
        + 1.0    · L_prop       # interlevel_loss_mult
        + 1e-4   · L_objnorm    # uw_{initial,final}_acc_trans_loss_mult, asymmetric (6×)
        + 0.0    · L_distortion # explicitly disabled
```
`[repo: configs/llff_256_uw.gin; internal/train_utils.py:276-291]`

Weight spread: **10 000×** between the reconstruction terms and the prior — but unlike
SeaSplat, the paper *states* `λ = 1e-4`, so the code and paper agree on magnitudes. The
only unreported multiplier is the `6×` inside the prior.

## 4.4 Reading the ablations — **Table 1 columns are MODEL VARIANTS, not loss ablations**

This is the precision the methodology (§4) demands, and the distinction is different in
kind from SeaSplat's. `[paper Tab. 1]`, average PSNR on the Red Sea validation set:

| Column | PSNR | What it is |
|---|---|---|
| **Ours** | **21.83** | full model: `σ^attn ∈ ℝ³` and `σ^bs ∈ ℝ³` — **6 medium coefficients** |
| **I** | 21.76 | "1 parameter" — one `σ`, shared by attenuation *and* backscatter, *and* shared across colour channels (the fog model) |
| **II** | 21.43 | "3 parameters" — one `σ` per colour channel, still shared between attenuation and backscatter |
| **III** | 21.72 | the **basic** rendering equations (Eqs. 13–14) instead of the final ones (Eq. 22) |
| MIP360 [5] | 21.05 | baseline |
| NeRF-W [21] | 16.52 | baseline |
| NeRFReN [14] | 21.05 | baseline |

**Precisely what each row represents:** columns I, II, III are **complete retrainings of
alternative model formulations**, each differing from "Ours" in one structural choice.
They are **neither cumulative additions to a baseline nor leave-one-out removals from the
full model** — the third possibility, and the one that applies here. Nothing is being
"added" or "removed"; the medium parameterisation is being *replaced*.

Mapping to config flags — each variant is one gin binding
`[inferred: repo internal/configs.py:177-184 comments matched against paper §5.2 ablation text]`:

| Variant | Flag | Comment in source |
|---|---|---|
| **I** (1 param) | `uw_fog_model = True` | *"If True same sigmas for attenuation and backscatter and for the same for all color channels."* `[repo: configs.py:181]` |
| **II** (3 params) | `uw_old_model = True` | *"If True same sigmas for attenuation and backscatter."* `[repo: configs.py:177]` |
| **III** (Eqs. 13,14) | `gen_eq = True` | *"If True use general eq. (11)-(14)"* `[repo: models.py:706]`, routed to `compute_alpha_weights_uw_gen` / `volumetric_rendering_uw_gen` `[repo: models.py:232-238; render.py:231, 383]` |
| Ours (6 params) | all three `False` | `[repo: configs/llff_256_uw.gin]` |

The 6-unknown count is anchored in the physics: `[paper §3.2]` — "solving for the full model
requires at least 6 unknowns".

### What Table 1 does and does not license

- ✅ "The 6-parameter medium model outperforms the 1- and 3-parameter simplifications by
  **0.07 dB and 0.40 dB** respectively on Red Sea in-medium PSNR."
- ✅ "The final rendering equations (Eq. 22) outperform the basic ones (Eqs. 13–14) by
  **0.11 dB**."
- ❌ You may **not** read Table 1 as ablating any *loss* term. `L_objnorm`, `L_prop` and
  `L_recon` are never ablated anywhere in the paper.
- ⚠️ **The margins are very small.** Ours vs I is **0.07 dB**; Ours vs III is **0.11 dB**;
  the whole spread I→Ours is **0.40 dB**. These are single-scene (Red Sea only), single-run
  numbers with no error bars and no repeated seeds. Table 1 is *consistent with* the
  6-parameter model being better, but at 0.07 dB it does not establish it. The larger claim
  the paper actually supports is the **1.5–4 dB** gap over MIP360 in Table 2 on the "red
  square" (far-field) crops — that margin is robust.

### Table 2 (main results, PSNR / SSIM / LPIPS vs MIP360)

| Scene | MIP360 | Ours | ΔPSNR |
|---|---|---|---|
| Red Sea | 21.05 / 0.75 / 0.29 | **21.83 / 0.77 / 0.25** | +0.78 |
| Red Sea *red square* | 29.66 / 0.84 / 0.43 | **33.80 / 0.90 / 0.23** | **+4.14** |
| Curaçao | 26.54 / 0.81 / 0.33 | **30.48 / 0.87 / 0.20** | **+3.94** |
| Curaçao *red square* | 27.04 / 0.84 / 0.45 | **33.20 / 0.88 / 0.08** | **+6.16** |
| Panama | 27.43 / 0.82 / 0.23 | **27.89 / 0.83 / 0.22** | +0.46 |
| Fern fog | 30.23 / **0.88** / **0.15** | **30.75** / 0.87 / 0.16 | +0.52 |
| Fern underwater | 29.62 / **0.87** / 0.26 | **29.76** / 0.86 / **0.15** | +0.14 |

> "red square" rows are **zoomed crops of far-field regions**, not full frames
> `[paper Fig. 5 caption]`. The method's advantage is concentrated there (+4 to +6 dB),
> exactly as the mechanism predicts. Quoting the full-frame average alone (**≈ +0.8 dB**,
> the number the paper itself headlines in §5.2) understates the effect; quoting the crops
> alone overstates it. Report both.
