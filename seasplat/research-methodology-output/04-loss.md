# §4 — Full loss function

## 4.1 The paper's statement

> `L = L_GS + L_bs + L_gw + L_sat + L_op + L_Zsmooth + L_Z-recon`  `[paper Eq. 10]`

Written as an **unweighted sum of seven terms**. The repository does not implement it that
way; every term carries a λ. Both forms are given below.

## 4.2 Term-by-term

### 1. `L_GS` — base 3DGS photometric loss

- **Closed form** `L_GS = (1 - λ_dssim)·L₁(Î, I) + λ_dssim·(1 - SSIM(Î, I))`, `λ_dssim = 0.2`
- `[paper Eq. 2]` `[repo: train.py:277-293; arguments/__init__.py:98]`
- **Purpose:** drives everything. Note the argument is `Î` (the *reconstructed in-medium*
  image), not `Ĵ` — this is the whole point of the method: the Gaussians only see the
  photometric gradient *through* the medium model.
- **Before `seathru_from_iter`** the argument is plain `Ĵ` (+ learned background), i.e.
  vanilla 3DGS `[repo: train.py:285-292]`.
- **If removed:** no photometric signal; the scene is unconstrained. Not ablatable.

### 2. `L_bs` — backscatter loss (DeepSeeColor dark-channel variant)

- **Paper form** `[paper Eq. 4]`:
  `L_bs = Σ_(i,j) Σ_c [ max{D̂_c(i,j), 0} + k·min{D̂_c(i,j), 0} ]`, `k > 1`, `D̂ := I - B̂`
- **Repo form** `[repo: deepseecolor/losses.py:146-161 (DarkChannelPriorLossV3), train.py:396-403]`:
  ```
  D̃   = I.detach() − B̂'                       # B̂' uses Ẑ.detach()
  pos = mean|relu( D̃)|                         # L1Loss(relu(D̃), 0)
  neg = SmoothL1(relu(−D̃), 0; β = 0.2)         # Huber, not linear
  L_bs = 1000·neg + pos
  ```
- **Purpose:** the dark-channel prior says *some* pixel in a natural scene is near-black in
  every channel; therefore after removing backscatter the residual `I − B̂` should be
  non-negative and as small as possible. The asymmetric weight (`k = 1000`) makes
  **over**-estimating backscatter (which drives `D̃` negative) catastrophically expensive
  while merely **under**-estimating it is cheap.
- **What it prevents if removed:** `B̂ ≡ 0`. Without a term that actively pushes `B̂` up,
  the trivially optimal medium is "no medium": `Â = 1, B̂ = 0, Ĵ = I`, which satisfies
  `L_GS` exactly. The paper names this degeneracy directly: "a model that adds no
  backscatter and performs no attenuation could still satisfy the optimization objective"
  `[paper §IV.B]`.
- **Gradient routing:** `I` is ground truth (no grad); `B̂'` is computed on detached depth.
  So `L_bs` is a loss on `β^B, B^∞` **only** — it cannot move the Gaussians at all.

### 3. `L_gw` — grey-world prior

- **Paper form** `[paper Eq. 5]`: `L_gw = (1/3) Σ_c ( (1/N) Σ_{i,j} Ĵ_c(i,j) − 0.5 )²`
- **Repo form** `[repo: deepseecolor/losses.py:185-203; train.py:354-371]`: identical —
  `mean over c of (mean_{H,W}(Ĵ_c) − 0.5)²`.
- **λ = 0.1**, and **gated to `iteration > gw_from_iter = 10 000`**
  `[repo: arguments/__init__.py:153,157; train.py:370-371]`.
- **Purpose:** fixes the global colour gauge. Buchsbaum's grey-world hypothesis (ref [34]).
- **What it prevents if removed:** the scale ambiguity `Ĵ ← cĴ`, `β^D ← β^D − ln(c)/Ẑ`.
  `Â` and `Ĵ` enter `Î` only as a product, so any per-channel rescaling of `Ĵ` can be
  absorbed by `β^D`. Without `L_gw` the restored image `Ĵ` has an arbitrary per-channel
  gain — it would still render correct in-medium images while being useless as a colour
  restoration. **This is the term that makes the "restoration" output meaningful, and it
  costs almost nothing on the in-medium metrics the ablation measures** (see §4.4).

### 4. `L_sat` — oversaturation penalty

- **Paper form** `[paper Eq. 6]`: `L_sat = Σ_{i,j} Σ_c max( Ĵ_c(i,j) − T_sat , 0 )`, `T_sat = 0.7`
- **Repo form** `[repo: deepseecolor/losses.py:218-232; train.py:381-385]`:
  `L_sat = mean( relu(−Ĵ) + relu(Ĵ − 0.7) )²`
  — **squared**, **mean not sum**, and with an extra **lower-bound** branch `relu(−Ĵ)`
  penalising negative radiance that the paper's formula does not contain.
- **λ = 2.0** `[repo: arguments/__init__.py:150]` — the largest weight in the objective,
  tied with `L_Zsmooth`.
- **Purpose:** `L_gw` fixes the *mean*; nothing stops the distribution from blowing past
  1.0 in the bright regions to hit that mean. `L_sat` caps the top.
- **What it prevents if removed:** `Ĵ` clipping/blowing out where attenuation is strongest
  (distant, red-starved regions) — the de-attenuation `Ĵ = D̂/Â` amplifies by `1/Â`, which
  is unbounded as `Ẑ → 1`.

### 5. `L_op` — background/opacity loss ("BG" in the ablation)

- **Paper form** `[paper Eq. 9]`: `L_op = Σ_{i,j} α(i,j) · 1[ ‖I(i,j) − B‖²₂ < T_sim ]`
- **Repo form** `[repo: deepseecolor/losses.py:234-295 (AlphaBackgroundLoss); train.py:309-331]`:
  ```
  mask = ‖ Î.detach() − σ(B^∞).detach() ‖₂  <  0.2·√3       # L2 norm, not squared
  L_op = mean| α[mask] |                                     # L1Loss to zero
  ```
  Three differences from the paper: (a) the reference image is `Î` (the model's own
  reconstruction), not `I` (the capture); (b) the norm is unsquared; (c) `T_sim` is fixed
  at `0.2√3` rather than left free.
- **λ = `bg_lambda` = 0.01** `[repo: arguments/__init__.py:115]` — the *smallest* weight.
- **Purpose:** any pixel whose colour is indistinguishable from the water colour carries no
  geometric information, so no Gaussian should claim it. Drives `α → 0` there.
- **What it prevents if removed:** the *floaters in the water column* failure mode — the
  paper's headline qualitative result (Fig. 4: "3DGS places many floaters within the water
  column"). This is the only ablation row that moves the metric substantially (§4.4).

### 6. `L_Zsmooth` — edge-aware depth total variation

- **Paper form** `[paper Eq. 8]`: `L_Zsmooth = Σ_{i,j} ( e^{−∂ₓI}|∂ₓẐ| + e^{−∂_yI}|∂_yẐ| )`
- **Repo form** `[repo: deepseecolor/depth_losses.py:6-24; train.py:340-344]`:
  ```
  ∂ₓẐ ← Ẑ.diff(dim=-1);  ∂ₓI ← mean_c( I.diff(dim=-1) )
  L_Zsmooth = mean|∂ₓẐ · e^{−∂ₓI}| + mean|∂_yẐ · e^{−∂_yI}|
  ```
- **λ = 2.0** `[repo: arguments/__init__.py:130]`.
- **Purpose:** the medium model reads `Ẑ` per-pixel; a noisy `Ẑ` produces noisy `Â, B̂`
  which the photometric loss can exploit as free capacity. Smoothing `Ẑ` denies that.
- **What it prevents if removed:** high-frequency depth noise being used to explain
  photometric residual — i.e. the medium model degenerating into a per-pixel colour LUT.
- **⚠ Signed-gradient bug (inherited, and it matters).** Both paper Eq. 8 and the repo use
  `e^{−∂I}` with the **signed** image gradient. The canonical formulation from Godard et al.
  (ref [35]) uses `e^{−|∂I|}`. With the signed form, a *negative* image gradient produces
  `e^{+|∂I|} > 1`, i.e. depth smoothness is **more** strongly enforced across
  dark-to-bright edges than in flat regions — the opposite of the intended behaviour on
  half the edges. The repo's own commented-out block at `depth_losses.py:26-40` contains
  the correct `torch.abs(...)` version, disabled `[repo: deepseecolor/depth_losses.py:26-40]`.
  Paper and repo *agree* here, so this is not a paper-vs-repo disagreement — it is a
  shared deviation from the cited source.

### 7. `L_Z-recon` — depth-weighted reconstruction loss

- **Paper form** `[paper Eq. 7]`: `L_Z-recon = ‖ Z_detach ⊙ (I − Î) ‖₁`
- **Repo form** `[repo: utils/loss_utils.py:17-20; train.py:296-301]`:
  `mean| Ẑ.detach() ⊙ (Î − I) |` — matches (sign is irrelevant under `|·|`; `mean` vs `‖·‖₁`
  is a constant factor absorbed into λ).
- **λ = `dwr_lambda` = 1.0**, gate `add_recon_depth_l1 = True` `[repo: arguments/__init__.py:143-144]`.
- **Purpose:** `L_GS` is uniform over pixels, but attenuation and backscatter are strongest
  at large `Ẑ`, where the signal is weakest. This term re-weights the residual by depth so
  far-field pixels are not drowned out. Paper: "to emphasize the recovery of details far
  away, where backscatter and attenuation may have the largest effect" `[paper §IV.B]`.
- **Detachment:** the weight `Ẑ` is detached, so this term does **not** let the optimizer
  reduce the loss by shrinking depth. Without the detach, `Ẑ → 0` is a free win.
- **What it prevents if removed:** far-field colour restoration collapses to whatever
  `L_GS` alone supports — visually the "muted distant regions" failure the paper attributes
  to SeaThru-NeRF `[paper Fig. 5 caption]`.

## 4.3 The objective as actually implemented

```
L_total = 0.8·L₁(Î,I) + 0.2·(1−SSIM(Î,I))            # L_GS,      λ implicit
        + 1.00 · L_Z-recon                            # dwr_lambda
        + 1.00 · L_bs                                 # dcp_loss_lambda
        + 0.10 · L_gw            [iter > 10 000]      # gw_loss_lambda
        + 2.00 · L_sat           [iter > seathru]     # sat_loss_lambda
        + 0.01 · L_op                                 # bg_lambda
        + 2.00 · L_Zsmooth                            # depth_smooth_lambda
```
`[repo: train.py:293, 301, 306, 331, 337, 344, 351, 371, 385, 392, 403, 419; weights from arguments/__init__.py:115,130,144,147,150,153]`

Spread of weights: **200×** (0.01 → 2.0). Reading Eq. 10 as an unweighted sum would
misrepresent the objective by that factor.

Gating summary — a term is only in the objective when its flag *and* its iteration gate hold:

| Term | flag (default) | iteration gate |
|---|---|---|
| `L_GS` | always | — (argument switches at `seathru_from_iter`) |
| `L_Z-recon` | `add_recon_depth_l1=True` | — |
| `L_bs` | `use_dcp_loss=True` | **added to loss only when `iter > seathru_from_iter`**; before that it is computed but *not added* `[repo: train.py:404-407]` |
| `L_gw` | `use_gw_loss=True` | `iter > gw_from_iter = 10 000` |
| `L_sat` | `use_rgb_sat_loss=True` | `iter > seathru_from_iter` |
| `L_op` | `learn_background=True` | — (but its reference colour switches from `bg` to `B^∞` at `seathru_from_iter`) |
| `L_Zsmooth` | `use_depth_smooth_loss=True` | — |

## 4.4 Reading the ablation table — **Table III is CUMULATIVE-ADDITIVE, not leave-one-out**

`[paper Tab. III]`, averaged over the four SeaThru-NeRF scenes, in-medium NVS:

| Row | PSNR | SSIM | LPIPS |
|---|---|---|---|
| Vanilla 3DGS | 24.42 | 0.85 | 0.25 |
| + DS | 24.03 | 0.84 | 0.25 |
| + C | 24.18 | 0.84 | 0.26 |
| + BG | **26.84** | 0.88 | 0.20 |
| + BS | 23.91 | 0.83 | 0.26 |
| + DS + BG | 26.71 | 0.87 | 0.19 |
| + DS + BG + C | **27.13** | 0.88 | **0.18** |
| + DS + BG + C + BS | 26.64 | 0.88 | 0.19 |
| Ours (all losses) | 27.11 | **0.89** | **0.18** |

**Precisely what each row represents:** every row is *vanilla 3DGS plus the listed subset*.
Rows 2–5 are single additions to the baseline; rows 6–8 are nested cumulative additions.
**No row is a leave-one-out from the full model.** Consequently:

- ❌ You may **not** say "removing BS costs 0.47 dB" from the gap between rows 8 and 9.
- ✅ You **may** say "adding BS on top of DS+BG+C costs 0.49 dB in-medium (27.13 → 26.64)."
- ❌ You may **not** conclude "L_gw contributes +0.42 dB" in general; you may only say
  "adding C on top of DS+BG gives +0.42 dB (26.71 → 27.13)."

**Row 9 ≠ row 8.** "Ours (all losses)" (27.11) is *not* the same configuration as
"+ DS + BG + C + BS" (26.64), so the additive ladder does **not** enumerate the full
objective. The legend defines only four component names (DS, C, BG, BS) while §4.3 lists
**six** optional terms; `L_Z-recon` (Eq. 7) and, arguably, the `L_op`/background-learning
machinery are unaccounted for in the ladder. `[inferred: comparing paper Tab. III legend against paper Eq. 10]`

**Legend typo:** the caption defines "**SD** refers to smooth depth loss" while every table
row is labelled "**DS**". They are the same term. `[paper Tab. III caption vs. rows]`

**The honest summary of Table III**, which the paper itself states: "many of the other loss
components individually do not lead to significant gains" — only **BG** (`L_op`, the
background/opacity loss, λ = 0.01, the *smallest* weight) moves in-medium PSNR materially
(+2.42 dB alone). DS and BS *individually hurt* the in-medium metric.

**Why that is not damning.** The paper explicitly flags the measurement mismatch: "these
ablations quantify the performance on in-medium novel view synthesis while we are also
concerned with the task of color restoration" `[paper §V.C]`. `L_gw`, `L_sat` and `L_bs`
exist to make `Ĵ` — the *restored, medium-free* image — meaningful, and **there is no
ground truth for `Ĵ`** ("unobtainable without draining the ocean" `[paper §V.A.c]`), so
their benefit is unmeasurable by construction and is argued only qualitatively (Fig. 5).
Any citation of Table III should carry that caveat.
