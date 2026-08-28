# §1 — Taxonomy: baseline, mechanisms, adaptation, and the novelty claim

## 1. Confirmed baseline/mechanism mapping

Each row below was confirmed from the named folder's **own** `01-taxonomy.md`, not assumed
from the method's reputation.

| Slot | Method | Design family (from that folder's §1) | Axis of contribution |
|---|---|---|---|
| **Underwater baseline** | **SeaSplat** | explicit radiance field · per-scene optimized · **physically-grounded medium model whose parameters are global constants for the scene** `[../seasplat/01-taxonomy.md]` | reinterprets the rasterizer output as medium-free radiance `Ĵ` and composes it through Akkaynak–Treibitz before the loss |
| **M1 — dense/deterministic init** | **EDGS** | explicit radiance field · per-scene optimized · **no medium model** · "its axis of contribution is **initialization**, the only method in the comparison set that changes neither the objective nor the optimizer nor the representation" `[../EDGS/01-taxonomy.md]` | one-shot triangulation of dense RoMa correspondences; densification deleted |
| **M2 — reorganization / budget prune** | **Mini-Splatting** | explicit radiance field · per-scene optimized · no medium model · "**primitive-count efficiency via spatial redistribution**" `[../mini-splatting/01-taxonomy.md]` | rewritten adaptive density control: blur split + depth reinitialization; then intersection preserving + importance-weighted stochastic sampling |
| **M3 — attribute quantization** | **CompGS-VQ** (`../compact3d/`) | explicit radiance field · per-scene optimized · no medium model · "**bits per primitive via quantization-aware vector quantization**" `[../compact3d/01-taxonomy.md]` | K-means VQ during training with STE; four grouped codebooks; ℓ1 opacity regulariser for count |

### The design family of the combined method

The combined method is an **explicit radiance field**, **per-scene optimized**, with a
**physically-grounded, scene-global medium model**, whose *additional* axis of contribution
is **joint efficiency across three orthogonal budgets simultaneously — optimization path
length, primitive count, and bits per primitive — under a physical medium constraint.**

That last clause is the whole of the taxonomic novelty, and it is deliberately narrow.
Positioned against the field's sharpest axis (`../seathru_NeRF/01-taxonomy.md`): the method
sits firmly on the **explicit-primitive, scene-global-constant** side, inheriting SeaSplat's
trade of medium expressiveness for a ~1000× cheaper medium representation. Nothing here
moves that axis; the contribution is entirely on the efficiency axis, *conditioned* on that
choice.

### Why the three mechanisms are called orthogonal, and where that breaks

The orthogonality is a statement about **which stage of the pipeline each one edits**, and
in air it is well-evidenced:

| | M1 EDGS | M2 Mini-Splatting | M3 CompGS-VQ |
|---|---|---|---|
| Changes the loss? | ❌ `[../EDGS/07-pseudocode.md line 33: "THE ENTIRE OBJECTIVE"]` | ❌ `[../mini-splatting/07-pseudocode.md lines 7–8]` | ✅ one term, ℓ1 opacity `[../compact3d/04-loss.md]` |
| Changes the representation? | ❌ | ❌ | ✅ (attributes become codebook + index) |
| Changes the rasterizer? | ❌ | ✅ forked `diff_gaussian_rasterization_ms` `[../mini-splatting/08-computational-profile.md §8.4]` | ❌ |
| Changes initialization? | ✅ **this is the whole method** | ⚠️ repeatedly, mid-training | ❌ |
| Changes the schedule? | ⚠️ yes, undocumented (`max_lr`, `reduce_opacity`) | ✅ (LR rewind, reinit) | ✅ (VQ start, reg window) |

EDGS's own Table 3 is the strongest external evidence for composability: dropping EDGS in as
initializer for three *unmodified* competing densification methods improved all three
(+0.12 / +0.14 / +0.36 dB) "without fine-tuning hyperparameters"
`[../EDGS/01-taxonomy.md, paper Tab. 3]`.

**But every one of those composability results was obtained on terrestrial scenes with a
loss that contains no medium model and no depth-dependent term.** The combined method's
baseline reads a *rasterized depth map* into a physical model and applies five auxiliary
priors to keep that model identifiable. All three mechanisms perturb the inputs to that
model. Section 3 below enumerates exactly where.

---

## 2. What each ablation is, and its identifier

The configuration matrix is a 2³ factorial over the three mechanism flags. Naming follows
the convention used consistently throughout this folder:

| ID | M1 init | M2 prune | M3 quant | Description |
|---|---|---|---|---|
| **A0** | — | — | — | SeaSplat baseline, unmodified |
| **A1** | ✅ | — | — | + dense correspondence init, densification off |
| **A2** | — | ✅ | — | + budget pruning to a fixed primitive count |
| **A3** | — | — | ✅ | + post-hoc / quantization-aware attribute VQ |
| **A4** | ✅ | ✅ | — | init + prune |
| **A5** | ✅ | — | ✅ | init + quant |
| **A6** | — | ✅ | ✅ | prune + quant |
| **A7** | ✅ | ✅ | ✅ | fully stacked |

`[proposed integration]` — the matrix, its labelling, and the choice of a 2³ factorial rather
than a cumulative ladder are design decisions of this work; see `05-experimental-design` in
the narrative chapter for the rationale and `10-reproducibility.md` for why the additive-vs-
leave-one-out distinction matters here.

---

## 3. Per-ablation: what must be **adapted**, not merely applied

This is the section that decides whether the work is engineering or research. For each
mechanism, the question is not "does it run on SeaSplat's codebase" but "does applying it
unmodified leave the baseline's well-posedness argument intact." In every case the answer
is no, and the required adaptation is stated.

### A1 — dense/deterministic initialization (EDGS)

**A1-a. Densification-off removes the mechanism SeaSplat's depth warm-up assumes.**
SeaSplat's staging runs vanilla 3DGS for the first `seathru_from_iter` (README: 10 000)
iterations specifically so that `Ẑ` becomes meaningful before any `β` is fit to it — "without
it, `β` would be fit to noise, landing directly in D-2"
`[../seasplat/05-constraints.md M-5]`. During that window, 3DGS's adaptive density control
is the thing that *makes* `Ẑ` meaningful: densify-and-prune runs every 100 iterations up to
15 000 `[../seasplat/07-pseudocode.md lines 61–64]`. EDGS switches ADC off entirely
`[../EDGS/03-variables.md, "Deleted machinery"]`. Under A1, the depth map that `β` is fit to
at iteration 10 001 is essentially **the triangulated initialization plus 10 000 steps of
photometric refinement**, not a densification-refined surface.
→ **Adaptation required:** either re-derive `seathru_from_iter` for the dense-init regime, or
justify keeping it. `[proposed integration]` The natural argument for *lowering* it is EDGS's
own measurement that its Gaussians start ~50× closer to their final positions
`[../EDGS/05-constraints.md D-1, paper §4.5 Eqs. 14–15]`, so the depth map stabilises much
earlier — but that is an argument, not a measurement, in this evidence base.

**A1-b. The water column is EDGS's named failure region.** `../EDGS/05-constraints.md` §5.3
states it without prompting: "Dense matchers are weakest on textureless, non-Lambertian and
view-dependent surfaces — **sky, water, glass, specular highlights**. For your underwater
work this is the central risk: the water column is exactly a region where RoMa will produce
low-confidence or hallucinated matches." And: "**No mechanism to add primitives.** With
densification off, a region missed by the matcher stays empty forever."
This collides head-on with the baseline's headline claim, which is about the water column:
3DGS "places many floaters within the water column"
`[../seasplat/05-constraints.md D-4, paper Fig. 4]`.
→ **Adaptation required:** the interaction is two-sided and must be reasoned about, not
assumed benign. Hallucinated matches in the water column seed floaters that `L_op` must then
kill; missed matches leave holes that nothing can fill. `[proposed integration]` A defensible
integration either (i) runs correspondence extraction on the *backscatter-removed* image
rather than the raw capture, or (ii) accepts raw-image matching and relies on `L_op` plus
EDGS's opacity decay to cull the hallucinations. Option (i) is not implementable at
initialization time — `B̂` does not exist until the medium model is trained — which is itself
a finding, and pushes toward (ii). Neither is measured here.

**A1-c. Two undocumented EDGS schedule mechanisms act on opacity, which is also `L_op`'s
target.** EDGS applies a continuous `×0.99` opacity decay every 10 steps for 15 000 steps —
cumulative logit shift ≈ **−15** — and **halves `opacity_lr`** to 0.025
`[../EDGS/05-constraints.md M-5]` `[repo: trainer.py:81-85]`. SeaSplat's `L_op` is an
opacity loss with λ = 0.01 whose gradient reaches **only** `α`
`[../seasplat/07-pseudocode.md line 30]`. Two independent forces now push the same variable
down, one of them calibrated for a codebase where `L_op` does not exist.
→ **Adaptation required:** `bg_lambda` and/or `reduce_opacity` must be re-tuned jointly, or
one disabled with justification. `[proposed integration]`

### A2 — spatial reorganization / budget pruning (Mini-Splatting)

**A2-a. `--imp_metric` has no default and no underwater variant.** It is a *required*
argument `[../mini-splatting/03-variables.md]`, with only `indoor` (`I¹` = accumulated
blending weight) and `outdoor` (`I²` = weight ÷ projected area, gated on intersection)
implemented. The paper itself calls the metric "case-dependent and hand-crafted … an
experimental trick" `[../mini-splatting/05-constraints.md §5.3, paper App. E]`, and notes
that `I²` exists to "suppress sky / far-field Gaussians"
`[../mini-splatting/07-pseudocode.md line 41]`.
→ **Adaptation required:** underwater scenes have no sky but do have a far-field water column
that is *systematically* low-contrast. Choosing `outdoor` imports a suppression rule designed
for a different phenomenon. `[proposed integration]` The medium-aware option — weighting
importance by `Â` so that heavily-attenuated primitives are not penalised twice — is
available in principle because `Â` is a per-pixel quantity the baseline already computes, but
it is not implemented in any source and is **not** claimed here as done.

**A2-b. Depth reinitialization fails exactly where SeaSplat needs it most.**
`../mini-splatting/05-constraints.md` §5.3: "**No depth ⇒ no reinitialization** … 'This
strategy fails in areas without a certain depth value, such as the sky in *train*' … **Directly
relevant to your underwater work:** the water column is the same kind of depth-less region as
the sky, and it is exactly where `seasplat/` reports 3DGS placing floaters."
Worse, the reinit's pixel-sampling probability is `(1 − α_accum)`, **biased toward
low-opacity pixels** `[../mini-splatting/11-paper-vs-repo-disagreements.md D-2]` — i.e.
preferentially resampling the water column.
→ **Adaptation required:** if the densification half of Mini-Splatting is used at all, its
interaction with the medium model must be argued. `[proposed integration]` The narrower and
more defensible reading of M2 is **simplification only** — intersection preserving plus
importance-weighted stochastic sampling to a budget — leaving 3DGS's ADC in place for
densification. That is the reading assumed by the "budget pruning to a fixed primitive count"
framing of A2, and it should be stated as a scoping decision rather than left implicit.

**A2-c. Pruning rescales the medium model's input domain.** This is the sharpest
integration problem in the whole combination, and it does not exist in air.
SeaSplat sets `norm_depth_max = True`, which **min–max renormalises `Ẑ` to `[0,1]`
per frame** `[../seasplat/03-variables.md; repo: train.py:233-237]`. The consequence is
already recorded: "the learned `β` are in units of *normalised per-frame depth*, **not**
inverse metres" and "the same physical depth maps to different `Ẑ` in different frames, which
is in tension with the global-`β` assumption"
`[../seasplat/05-constraints.md §5.3]`. Now remove 60–90% of the primitives at iteration
15 000. The *farthest* and *nearest* Gaussians contributing to each frame change, so `max Ẑ`
and `min Ẑ` change, so the normalised depth field is **rescaled by a factor the medium
parameters were not trained for**. Because `Â = e^{-β^D Ẑ}` and `β` is global, a
rescaling of `Ẑ` is exactly degeneracy **D-2** — the `βẐ` product invariance
`[../seasplat/05-constraints.md D-2]` — arriving not as an optimization shortcut but as a
*discontinuity injected by the pruning event*.
→ **Adaptation required, and it is not optional.** `[proposed integration]` Three candidate
fixes, in decreasing order of how much they preserve the baseline: (i) re-run the medium
warm-up burst (`update_bs_at_count`-style, medium-only steps with geometry frozen)
immediately after each simplification event, letting `β` re-fit to the new depth range;
(ii) freeze `Ẑ`'s normalisation constants at their pre-prune values; (iii) set
`norm_depth_max = False` and accept unnormalised depth throughout, which removes the
frame-to-frame inconsistency but changes the baseline. Option (i) is the one most consistent
with SeaSplat's existing alternating schedule and is the one this methodology adopts; see
`07-pseudocode.md` line 55.

**A2-d. Two rasterizers must be reconciled.** SeaSplat obtains depth by a **second full
rasterization pass** with `override_color = z_cam` on the *stock* kernel
`[../seasplat/02-pipeline.md Stage C]`. Mini-Splatting requires a **forked** kernel,
`diff_gaussian_rasterization_ms`, returning `accum_weights`, `area_proj`, `area_max`,
`out_pts`, `accum_alpha` `[../mini-splatting/08-computational-profile.md §8.4]`.
→ **Adaptation required:** one CUDA extension must serve both. `[proposed integration]` The
lower-risk direction is to port SeaSplat's depth pass onto Mini-Splatting's fork (SeaSplat's
addition is a Python-level second call with an overridden colour, whereas Mini-Splatting's
additions are inside the kernel). Note also that Mini-Splatting's fork already emits
`out_pts` — a *mid-point* depth per pixel from the argmax Gaussian — which is a
**different and arguably better-posed** depth than SeaSplat's alpha-normalised `Z_raw/α`.
Substituting it would change the medium model's input and is therefore a separate
experimental question, not a free improvement.

### A3 — attribute quantization (CompGS-VQ)

**A3-a. One of the four codebooks is empty.** CompGS-VQ quantizes four groups — DC colour
(`d=3`), higher-order SH (`d=45`), scale (`d=3`), rotation (`d=4`)
`[../compact3d/05-constraints.md M-3]`. SeaSplat sets **`sh_degree = 0`**, so `_features_rest`
has shape `(N, 0, 3)` — it is *empty*
`[../seasplat/03-variables.md; repo: arguments/__init__.py:49]`, confirmed by the paper: "We
use zero order spherical harmonics" `[seasplat paper §IV.C]`.
→ **Adaptation required:** the `sh` codebook must be dropped, leaving **three** codebooks.
`[proposed integration]` More consequentially, this **caps the achievable compression ratio a
priori**. Per-Gaussian storage in SeaSplat is **14 floats**, not 59
`[../seasplat/08-computational-profile.md §8.4]`, and the 45 SH floats CompGS-VQ compresses
hardest are the ones that do not exist. `../comparison-glossary.md` §3.2 flags this exactly:
"Normalising compression ratios against a 59-float baseline for one and 14 for the other is a
category error waiting to happen." Any headline compression number for A3 that is compared
against CompGS-VQ's published 41–65× is invalid unless renormalised.

**A3-b. Quantization damage to the restoration output is unmeasurable by construction.**
CompGS-VQ's quality cost is measured as PSNR/SSIM/LPIPS on the rendered image. In SeaSplat,
the rendered in-medium image `Î` is what is scored, and the *restored* medium-free image
`Ĵ` is **never scored** — "no ground truth exists 'without draining the ocean'"
`[../seasplat/10-reproducibility.md §10.3b, paper §V.A.c]`. But `Ĵ` is precisely the
quantity built from the quantized DC colour: `Î = Ĵ ⊙ Â + B̂`. Quantization error in `f_dc`
enters `Ĵ` directly and is then *multiplied by the attenuation map* `Â ≤ 1` before it reaches
the metric. **The metric attenuates the evidence of the damage in exactly the regions
(far-field, red channel) where restoration matters most.**
→ **Adaptation required:** this is a limitation to declare, not a bug to fix.
`[proposed integration]` The honest mitigations are (i) report a `Ĵ`-space
self-consistency metric — PSNR between `Ĵ` before and after quantization, with the
unquantized model as reference — as a *secondary* measure, and (ii) state plainly that no
external ground truth validates it. Neither substitutes for ground truth.

**A3-c. CompGS-VQ's own count-reduction machinery duplicates M2 and conflicts with `L_op`.**
CompGS-VQ is not purely a quantizer: it adds an ℓ1 opacity regulariser (λ_reg = 1e-7,
iterations 15 000–20 000) plus periodic pruning, and "the 2–3× rendering speedup comes from
the opacity pruning, not the quantization"
`[../compact3d/08-computational-profile.md §8.2]`. Under A3 alone that is a confound (the
"quantization" ablation would also be pruning); under A6/A7 it double-counts M2. And it is a
*third* force acting on opacity alongside `L_op` and (under A1) EDGS's decay.
→ **Adaptation required:** `--opacity_reg` must be **disabled** for M3 so that M3 is purely
`bits per primitive` and M2 is solely responsible for count. `[proposed integration]` This is
a deviation from CompGS-VQ as published and must be stated when its numbers are cited. It is
also what makes the 2³ matrix interpretable at all — without it, the M2 and M3 factors are
not independent.

**A3-d. The medium parameters must be excluded from quantization, and stored.** The nine
medium scalars plus the learned background live in separate `.pth` files
(`backscatter_<it>.pth`, `attenuate_<it>.pth`) `[../seasplat/02-pipeline.md Stage F]`. They
are `O(1)` and quantizing them is pointless; but they must appear in the reported model size
or the storage accounting is incomplete.
→ **Adaptation required:** trivially, but say so. `[proposed integration]`

### Cross-cutting: the shared-variable map

Three mechanisms plus the baseline touch three shared quantities. This table is the
interaction hypothesis of the whole study, and it is repeated as an interaction-candidate
flag in `03-variables.md`.

| Shared quantity | SeaSplat (A0) | M1 EDGS | M2 Mini-Splatting | M3 CompGS-VQ |
|---|---|---|---|---|
| **Opacity `o` / `α`** | `L_op` drives `α → 0` on water-coloured pixels (λ = 0.01); 3DGS opacity reset every 3 000 | continuous `×0.99` decay every 10 steps (Σ logit ≈ −15); `opacity_lr` **halved**; reset unreachable | opacity reset **removed entirely**; `α` **reset to `inverse_sigmoid(0.1)`** at every reinit | ℓ1 `Σα` regulariser + prune at 0.005 *(disabled per A3-c)* |
| **Rasterized depth `Ẑ`** | the medium model's only spatial input; min–max normalised **per frame** | replaced wholesale at init; no ADC to refine it | its distribution is what reinit resamples; pruning **rescales its range** | unaffected directly; affected via quantized scale/rotation changing the rendered surface |
| **Per-Gaussian attributes** | 14 floats (`sh_degree = 0`) | seeded from triangulation + reference-image RGB | `s`, `q`, `o`, `f_rest` **reset** at every reinit | the object being compressed; one of four codebooks is empty |

**Reading this table is the argument that the three mechanisms are *not* orthogonal on this
baseline, even though they are orthogonal on vanilla 3DGS.** Every cell in the opacity row is
a force on the same scalar, and three of the four were tuned in codebases where `L_op` does
not exist.

---

## 4. The novelty claim

The brief gates a defensible novelty claim on at least one of three grounds. Assessed
against the evidence actually available in this pass:

### (a) Prior-art gap — **SUPPORTED, but narrow**

The Phase 0 literature scan found an active underwater-3DGS efficiency literature and no
member of it occupying this space:

| Work | Efficiency mechanism(s) | Overlaps this method? |
|---|---|---|
| **TUGS** (arXiv:2505.08811) | tensorized higher-order Gaussians + adaptive medium estimation + tensorized densification; ~20% of 3DGS parameters, 21 MB, 106 FPS | ❌ tensor decomposition of the *representation*, not init/prune/quantize of standard Gaussians. No VQ, no correspondence init. |
| **UW-3DGS** (arXiv:2508.06169) | physics-aware uncertainty pruning (PAUP); VM tensor-decomposed voxel grid for the attenuation field; **standard sparse COLMAP init** | ⚠️ **closest on the pruning axis.** But its pruning targets *floaters by uncertainty*, not a primitive budget; its "compression" compresses the *medium field*, not Gaussian attributes; and its initialization is sparse SfM. |
| **WaterSplat-SLAM** (arXiv:2604.04642) | voxel-based merging of Gaussian primitives to reduce redundancy | ❌ SLAM setting; merging, not budget sampling or VQ. |
| **WaterClear-GS**, **3D-UIR**, **DualPhys-GS**, **UW-GS**, **AquaGS**, **Swimm3R** | degree-0 SH for compactness; appearance–medium decoupling; distractor handling; SfM-free MVS init | ❌ none does attribute vector quantization; none does dense-correspondence init with densification disabled. |
| **GETA-3DGS** (arXiv:2605.02086), **LFGS** | joint structured pruning + quantization; prune → SH adjust → EC-VQ | ⚠️ **the composition idea itself is not novel in air.** These are terrestrial and medium-free. |

**The gap is real and checkable: no published method combines dense correspondence-based
initialization, budget-based primitive reduction, and attribute vector quantization on a
physically-grounded underwater 3DGS baseline; and no underwater 3DGS method found uses
K-means attribute quantization at all.**

**The gap is also narrow.** GETA-3DGS and LFGS establish that prune+quantize composition is
a known move in air; EDGS's own Table 3 establishes that its initialization composes with
other methods. A reviewer can reasonably say the *combination* is unsurprising. Claim (a)
alone would be a weak contribution — "nobody has run these three on underwater data" is a
gap, not an insight. It carries weight only in support of (c).

### (b) Measured non-additive interaction effect — **NOT SUPPORTED**

Phase 0 searched `my-research/` outside the two excluded paths for any combined-method
artifact: metrics tables, logs, checkpoints, renders, output directories. **Nothing was
found.** There is no `draft-thesis-output/`, no `master_metrics.csv`, no per-scene results.
The only measured numbers available anywhere in this evidence base are the *individual*
published figures of the four source papers, on *terrestrial* data (except SeaSplat's).

Therefore:

- No statement of the form "stacking M1 and M2 yields less than the sum of their individual
  savings" can be made.
- No statement of the form "quantization costs more PSNR after pruning than before" can be
  made, even though `../OMG/`'s premise — "a smaller set of Gaussians becomes increasingly
  sensitive to lossy attribute compression" `[../OMG/00-index.md, paper Abstract]` — predicts
  exactly that and is the single most citable external reason to expect non-additivity.
- The interaction table in §3 above is an **analytical prediction**, explicitly labelled as
  such, not a measurement.

`08-computational-profile.md` records "no results found" in the places where combined
numbers would go, rather than interpolating them.

### (c) Required well-posedness / integration fix — **SUPPORTED, and this is the claim**

Section 3 enumerates **eleven** adaptations, of which the following are not cosmetic —
each names a specific way the baseline's identifiability argument breaks and a specific
remedy:

| # | The break | Traceable to |
|---|---|---|
| **A2-c** | Budget pruning rescales the per-frame min–max normalised `Ẑ`, injecting SeaSplat's own D-2 `βẐ`-invariance degeneracy as a step discontinuity at the simplification event | `../seasplat/05-constraints.md` D-2 + §5.3, `../seasplat/03-variables.md` (`norm_depth_max`) |
| **A1-a** | Disabling densification removes the process the `seathru_from_iter` warm-up relies on to make `Ẑ` meaningful before `β` is fit to it | `../seasplat/05-constraints.md` M-5, `../EDGS/03-variables.md` "Deleted machinery" |
| **A1-b / A2-b** | Both M1 and M2 have a documented failure mode in depth-less, textureless regions — which in this domain is the water column, the exact region the baseline's `L_op` exists to police | `../EDGS/05-constraints.md` §5.3, `../mini-splatting/05-constraints.md` §5.3, `../seasplat/05-constraints.md` D-4 |
| **Opacity row of §3's table** | Four independent forces act on opacity, three of them calibrated without `L_op` in the objective | all four folders' §5 |
| **A3-a** | The quantizer's largest codebook targets a parameter block the baseline does not have; the compression ratio is capped a priori and cannot be compared to published figures | `../seasplat/08-computational-profile.md` §8.4, `../comparison-glossary.md` §3.2 |
| **A3-c** | The quantizer ships its own count reduction, which confounds the M2/M3 factorisation unless explicitly disabled | `../compact3d/08-computational-profile.md` §8.2 |
| **A2-d** | Two incompatible CUDA rasterizers, one of which offers a *different, better-posed* depth than the baseline uses | `../seasplat/02-pipeline.md`, `../mini-splatting/08-computational-profile.md` §8.4 |

**Claim (c) is the defensible one.** The contribution is not "we combined three known
mechanisms"; it is *"we identified that a scene-global medium model whose only spatial input
is a per-frame-normalised rasterized depth map is not invariant to primitive-count reduction,
and specified what has to change for the composition to remain well-posed."* A1-a and A2-c
in particular are non-obvious, domain-specific, and would bite any future attempt at the same
composition.

### Verdict

**Novelty claim type: (c), supported by (a). (b) is unresolved for lack of measurements.**

This is a *methodological* contribution with an *empirical* obligation that the current
evidence base does not discharge. `12-novelty-defensibility.md` states the strongest
counter-objection, whether the evidence answers it, and the narrower contribution that
survives if it does not.

**What would upgrade the claim:** running the eight-cell matrix and reporting the A4/A5/A6/A7
cells against the additive prediction from A1/A2/A3. If the stacked cells deviate — in either
direction — beyond seed variance, claim (b) becomes available and the contribution strengthens
from "we specified the integration" to "we specified the integration *and* showed the
mechanisms are not independent on this baseline." Until then, over-claiming (b) would be
exactly the failure mode the brief warns against.

---

## 5. The closest related works

Named for the related-work section, in order of how hard a reviewer would press on them:

1. **UW-3DGS** — *Underwater 3D Reconstruction with Physics-Aware Gaussian Splatting*
   (arXiv:2508.06169). **The closest.** Same domain, same SeaThru-NeRF evaluation scenes,
   and it explicitly couples a physical underwater image formation model with a *pruning*
   mechanism (PAUP) and a *compressed* medium representation (VM tensor decomposition,
   rank 16, grid 64). The distinction to draw: UW-3DGS compresses the **medium field** and
   prunes **by uncertainty to remove floaters**; this work compresses the **Gaussian
   attributes** and prunes **to a primitive budget**, and additionally replaces
   initialization. Its reported 27.604 PSNR / 0.868 SSIM / 0.134 LPIPS on SeaThru-NeRF is the
   number to beat or to explain. `[unverified — figures from a Phase 0 web fetch of the
   arXiv HTML, not from a local PDF]`

2. **TUGS** — *Physics-based Compact Representation of Underwater Scenes by Tensorized
   Gaussian* (arXiv:2505.08811). The strongest published underwater *efficiency* result:
   ~20% of 3DGS's parameters, 21 MB, 106 FPS versus SeaThru-NeRF's 383 MB and 0.09 FPS.
   The distinction: TUGS achieves compactness by changing the **primitive type** (tensorized
   higher-order Gaussians), which is a representation change; this work keeps standard 3D
   Gaussians and attacks initialization, count, and bit-width separately, which is what makes
   the 2³ factorisation meaningful at all. `[unverified — from the Phase 0 scan]`

3. **OMG** — *Optimized Minimal 3D Gaussian Splatting* (NeurIPS 2025), present locally as
   `../OMG/`. Not underwater, but it is the **theoretical warrant for expecting the M2×M3
   interaction**: its opening premise is that count-reduction methods and
   attribute-compression methods "do not compose, because a smaller set of Gaussians becomes
   increasingly sensitive to lossy attribute compression" `[../OMG/00-index.md, paper
   Abstract]`. OMG's answer is to co-design them (local-distinctiveness scoring +
   sub-vector quantization). This work's A6 cell tests the un-co-designed composition on an
   underwater baseline; OMG is the reason to expect it to be sub-additive, and the obvious
   "why didn't you just use OMG" objection. OMG is also built directly on Mini-Splatting
   `[../OMG/00-index.md]`, so it is the natural upgrade path for M2+M3 jointly.

Honourable mentions for the related-work paragraph, all from the Phase 0 scan and all
`[unverified]` against a local PDF: **GETA-3DGS** (arXiv:2605.02086, joint structured pruning
+ quantization — the terrestrial precedent for the composition idea, and the reason claim (a)
alone is weak); **WaterSplat-SLAM** (voxel merging for medium-aware Gaussian maps);
**3D-UIR** (appearance–medium decoupling with an explicit fidelity/efficiency trade-off on the
same scenes).
