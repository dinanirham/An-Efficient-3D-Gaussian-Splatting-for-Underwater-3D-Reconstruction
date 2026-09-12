# Executive summary — main effects, 48 runs

**Scope.** Four configurations complete at three seeds across four scenes: the baseline (A0)
and each of the three efficiency mechanisms in isolation (A1 initialization, A2 simplification,
A3 quantization). The interaction cells (A4–A7) are in progress and nothing here speaks to
them.

**Reading convention.** Effects are scene-averaged (unweighted mean of scene means) and
accompanied by the number of scenes on which the effect exceeds twice the pooled within-cell
standard deviation. **No p-values**: three seeds on four scenes does not support a formal test
with meaningful power. An effect that resolves on 0 of 4 scenes is *unresolved*, not zero.

---

## 1. The table

| | **A0** baseline | **A1** init | **A2** prune | **A3** quantize |
|---|---:|---:|---:|---:|
| PSNR | 27.202 | **27.704** | 27.410 | 27.344 |
| SSIM | 0.8850 | **0.8901** | 0.8805 | 0.8862 |
| LPIPS *(lower better)* | **0.1819** | 0.1984 | 0.2301 | 0.1892 |
| primitives | 2,709,310 | 222,498 | **141,856** | 2,653,827 |
| model size | 144.7 MiB | 11.9 | **7.6** | 52.0 |
| bytes/primitive | 56.00 | 56.01 | 56.01 | **20.57** |
| render fps | 117.6 | 214.7 | **311.7** | 130.1 |
| training wall clock | 3,600 s | 2,970 | **2,711** | 3,774 |
| peak render memory | 2,518 MiB | **936** | 959 | 2,639 |
| **medium model intact** | **12/12** | **12/12** | **6/12** | **12/12** |

Effects against the baseline, with the count of scenes on which they resolve:

| | A1 | A2 | A3 |
|---|---|---|---|
| ΔPSNR | +0.503 **1/4** | +0.209 0/4 | +0.143 0/4 |
| ΔSSIM | +0.0051 **2/4** | −0.0045 **2/4** | +0.0012 0/4 |
| ΔLPIPS | +0.0165 **2/4** | +0.0482 **4/4** | +0.0073 **1/4** |
| Δfps | +97.1 **4/4** | +194.2 **4/4** | +12.5 **0/4** |
| Δtrain | −630 s **3/4** | −889 s **4/4** | **+174 s 2/4** |
| reduction | **11.9×** | **18.7×** | 1.02× count, **2.77× storage** |

---

## 2. What the research questions now have

### RQ1 — do the mechanisms individually transfer, and at what cost?

**Answered for all three.** All three transfer in the sense of running to convergence and
producing their intended effect. They do not transfer equally.

**M1 (dense initialization)** is the best-behaved. 11.9× fewer primitives, PSNR *higher* on
every scene, SSIM higher, LPIPS at baseline on two scenes and better on one. It is the only
mechanism whose fidelity effect is positive and resolvable anywhere.

**M2 (simplification)** buys the largest reduction — 18.7× — and pays for it perceptually.
LPIPS degrades on **all four** scenes, at 4.1 to 19.4 standard deviations. PSNR does not
register the cost at all.

**M3 (quantization)** delivers **2.77× storage and nothing else**. No frame-rate gain (0 of 4
scenes), no memory reduction, no population change, and training is **5% slower**.

### RQ2 — do they compose additively, or interact?

**Not yet answerable.** A4–A7 are in progress. One early signal: A4 (M1+M2) has lost no
attenuation channel in its first runs, where M2 alone loses half. If that holds it is a real
interaction, and the design's most interesting possible result.

### RQ3 — does primitive reduction perturb medium identifiability?

**Answered, and more sharply than the hypothesis stated.**

| | runs | medium model broken | largest β drop | where |
|---|---:|---:|---|---|
| A0 | 12 | 0 | 4.8–33.6% | seathru warm-up |
| A1 | 12 | **0** | 3.6–44.0% | scattered |
| **A2** | 12 | **6** | **25–195%** | **simplification boundary, 12/12** |
| A3 | 12 | 0 | 6.4–38.8% | seathru warm-up |

**Every A2 run's largest attenuation drop lands on a simplification boundary. No other cell
loses a channel at all.**

And the refinement: **A1 ends at ~222k primitives and A2 at ~142k — comparable populations,
opposite outcomes.** So the population *size* is not the operative variable. A population that
is low from the start lets β be fitted to it; a population that drops discontinuously at
iteration 15,000, after β has been fitted to a different one, does not. **The discontinuity is
the mechanism, not the count.**

### RQ4 — what integration properties govern the composition?

**Five documented, all found by execution rather than analysis.** Each is a property of a seam
that appears in neither component's documentation:

1. **Gradient destination** (CD-22/23) — substituting the rasteriser preserved every forward
   value and silently removed alpha's gradient from density control, collapsing the baseline to
   a sixth of its primitive count.
2. **Coupled parameters** (M1 schedule) — one parameter gates both the opacity reset and the
   size-based prune; correcting them site by site re-armed each in turn across three attempts.
3. **Cull ordering** — EDGS's decay removes what "the loss does not defend", which is unsound
   before the medium model exists.
4. **A defect in a published method** (CD-26) — EDGS names its own D-2 degeneracy and assigns
   it to a filter that cannot detect it. **95% of all rejected triangulations on this corpus
   came from the filter EDGS does not have.**
5. **Medium identifiability under population change** — RQ3 above.

---

## 3. The five findings that matter

### 3.1 PSNR cannot rank these mechanisms; LPIPS can

On PSNR the three cells span **0.36 dB** and not one difference resolves on more than a single
scene. On LPIPS they separate cleanly: **M2 worse on 4 of 4 scenes, M1 on 2, M3 on 1.**

Reporting PSNR alone would show three roughly equivalent mechanisms. The perceptual measure
shows one that costs almost nothing (M3), one that costs little (M1), and one that costs a
great deal (M2). **The conclusion inverts with the choice of metric**, which is why all three
are reported and none is used alone.

### 3.2 A primitive-count ratio does not predict a speedup

| | count reduction | fps gain | implied exponent |
|---|---:|---:|---:|
| M1 | 11.9× | 1.83× | 0.24 |
| M2 | 18.7× | 2.65× | 0.33 |

Both sub-linear, and by different exponents. **Per-primitive rasterisation cost is not
constant across cells** — M1's primitives carry correspondence-derived scales, M2's are
importance-weighted survivors of an optimised population. Any efficiency claim quoting "18.7×
fewer Gaussians" without the 2.65× beside it implies a speedup that does not exist.

### 3.3 The baseline's representation is mostly invisible

**A0 renders 35.9% of its primitives** above the visibility threshold; A1 renders 86.1% and A2
93.1%. Roughly two thirds of the baseline's population contributes nothing individually.

So the honest reduction figure depends on the question: **18.7× for storage** (every primitive
is written), **6.7× for scene representation**. Both are correct; quoting only the first
overstates how much representation was removed.

### 3.4 The baseline carries geometric pathology no fidelity metric can see

A0's bounding box is **96–99.96% empty**, in two distinct modes: detached *rendered* clusters
beyond ten times the median radius (IUI3-RedSea 1.69%, Panama 6.61%) — SeaSplat's degeneracy
D-4, identified geometrically — and a diffuse *invisible* halo on Curasao where opacity gating
raises occupancy 77-fold.

**A2 removes both.** A1 substantially reduces both. A3, which does not touch geometry,
reproduces the baseline's pathology exactly — which is the control that confirms the measure
is reading geometry rather than an artefact.

**JapaneseGardens has neither pathology**, and is the one scene where A2's occupancy is *lower*
than A0's. Where the baseline's geometry is sound, simplification does not improve it.

### 3.5 M1 nearly eliminates run-to-run variance

| | mean CV on primitive count |
|---|---:|
| A0 | 14.89% |
| **A1** | **0.66%** |
| A2 | 4.04% |
| A3 | 23.33% |

Under M1 densification never runs, so the amplification that drives the baseline's dispersion
— a primitive landing either side of a gradient threshold, compounded over 144 densification
events — has nothing to act on. The count is set by a hashed cloud and reduced only by opacity
pruning.

A3's higher figure is **not an M3 effect**: quantization begins 7,000 iterations after the
population freezes, so A0 and A3 are the same process. Their twelve matched-seed pairs are
therefore a measurement of same-seed reproducibility — **median 21.1%, maximum 58.8%** — which
revises the earlier estimate's tail upward by a factor of three.

---

## 4. Deeper reading

### Why M2 breaks the medium model and M1 does not

Both end with an order of magnitude fewer primitives. The difference is *when*.

The medium model's only spatial input is rendered depth, renormalised per frame by its own
minimum and maximum. Under M1 that depth map is produced by a stable population from the first
iteration, and β is fitted to it throughout. Under M2 the population is cut by 94% at iteration
15,000 — **after** β has converged against a different depth distribution — and the
re-identification burst this study added does not restore it.

The failure is **bistable and seed-conditioned**: six of twelve runs, spread across all four
scenes, with the same configuration on the same scene collapsing on one seed and surviving on
another. It is not that some scenes are harder. Simplification pushes a stochastic process
toward a boundary, and which side it lands on is not determined by the configuration.

### Why M3 is the cleanest result and the least useful one

M3's outcome was predicted in advance and held exactly: **2.77× storage, no frame-rate gain, no
memory gain.** The reasoning was structural — at `sh_degree = 0` a primitive is fourteen floats
of which position and opacity are never quantized, leaving sixteen of fifty-six bytes
untouchable; and the source method's published speedup is credited by its own authors to an
opacity regulariser this study disables to keep the factors independent.

The published figure for this method is **41–65×**. This study measures **2.77×**. Both are
correct and they are different quantities — the published ratio is against fifty-nine floats
per primitive and additionally includes population reduction. **Tabulating them together would
be wrong**, and the renormalisation required to compare them is itself a contribution.

### What the baseline turns out to be

Three independent measurements say the same thing. It carries **2.7 million primitives of which
64% are individually invisible**; its bounding box is **96–99.96% empty**, held open by detached
clusters or an invisible halo depending on the scene; and its converged size varies by a
**median of 21% and up to 59% between identical runs**.

That is the reference point every efficiency ratio in this literature divides by, and none of
those three properties is visible in a PSNR table.

---

## 5. What cannot be concluded

**Nothing about interactions.** A4–A7 are incomplete.

**Nothing about operating points.** Each mechanism was evaluated at one budget and one codebook
size. The design answers whether the mechanisms interact; it **cannot** establish that any
ranking among them persists across budgets, and no such claim is made.

**Nothing about deployment.** No embedded hardware, power, latency or memory constraint was
tested. Peak render memory is measured on a data-centre GPU.

**Nothing beyond four scenes and thirteen held-out frames.** Per-scene dispersion varies by a
factor of five and every result here is reported per scene for that reason.

**The A2 aggregates mix two populations.** All four A2 cell×scene groups contain both collapsed
and intact medium models, so every A2 figure above is a mean over two physically different
models. The LPIPS and efficiency effects are far too large to be artefacts of that; **the PSNR
non-result is more exposed**, since an effect already below the noise floor cannot be defended
against a covariate that splits the group.

---

## 6. Provisional ranking

On present evidence, **M1 is the mechanism that transfers best**: the only positive and
resolvable fidelity effect, perceptual quality near baseline, an intact medium model in all
twelve runs, near-deterministic behaviour, and 11.9× reduction. It costs a preprocessing stage
the others do not — 35–53 s per scene, excluded from the training clock and reported separately.

**M2 buys the most reduction and is the only mechanism that breaks the physics.** Whether that
matters depends on what the model is for: a reconstruction judged on composed-image fidelity
tolerates it, a reconstruction whose medium parameters are the scientific output does not.

**M3 is cheap, safe and small.** It is the only one whose result was predicted exactly in
advance, and the only one delivering a single-axis benefit with no side effects.

**This ordering is provisional**, and the interaction cells could change it — particularly if
M1 proves to protect M2's medium model, which would make the combination more than the sum of
its parts.
