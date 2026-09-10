# CHAPTER III — RESEARCH METHODOLOGY

> **Draft status.** Written under the positioning approved at Gate 2
> (`04-repositioning.md`). Sections describing the implementation are complete and stable;
> figures are named but not yet produced. Claims carry an evidence tag where they rest on
> measurement: `[measured n=k]` gives the number of runs behind a figure, and
> `[NOT YET SUPPORTED BY EVIDENCE]` marks a statement the campaign has not yet tested.
> Citations follow APA 7th edition; `[NEEDS CITATION]` marks a claim whose source must be
> supplied before submission.

---

## 3.1 Conceptual Framework

### 3.1.1 Research design

This study is a **controlled factorial experiment**. It does not propose a new compression
algorithm, a new radiance-field representation, or a new underwater image formation model.
It takes three efficiency mechanisms whose behaviour is documented on terrestrial scenes,
transfers each to a physics-aware underwater reconstruction pipeline, and measures what
happens — individually, in every pairwise combination, and all together.

The design follows from the question. Asking whether three mechanisms *transfer* is a
question about main effects; asking whether they *compose* is a question about interactions;
and interactions cannot be estimated from a cumulative ablation ladder, which is the form the
source literature almost universally adopts. A ladder confounds the effect of adding a
mechanism with the state of everything already added. A full factorial does not.

### 3.1.2 The problem

Three-dimensional Gaussian splatting (Kerbl et al., 2023) represents a scene as an explicit
set of anisotropic Gaussian primitives and renders by differentiable rasterisation. It
achieves real-time rendering at reconstruction quality competitive with neural radiance
fields (Mildenhall et al., 2020), and it does so without a neural network — the scene *is*
the parameters.

That explicitness is also its cost. A converged model of a single scene in this study's
corpus carries between 1.6 and 4.3 million primitives `[measured n=12]`, and at fourteen
float32 values per primitive that is 90–230 MB for one scene. The terrestrial literature has
responded with a substantial body of work on initialization, population reduction and
attribute compression.

Underwater reconstruction adds a second problem. Light is attenuated and scattered by the
medium, so an image is not a direct observation of scene radiance. SeaThru-NeRF (Levy et al.,
2023) and subsequently SeaSplat (Yang et al., 2024) address this by fitting a physical image
formation model jointly with the geometry, using the revised formulation of Akkaynak and
Treibitz (2018) in which attenuation and backscatter are governed by *distinct* coefficients.

**The gap this study addresses is the intersection.** The efficiency literature assumes the
rendered image is compared directly against the capture. Under a physics-aware formulation it
is not: the render is reinterpreted as medium-free radiance and composed through a medium
model before any comparison is made. Whether mechanisms developed under the first assumption
behave as documented under the second is not established, and — as §3.5.6 sets out — there
are specific structural reasons to expect that they may not.

### 3.1.3 Research questions

| | Question |
|---|---|
| **RQ1** | Do dense-correspondence initialization, importance-based simplification and attribute quantization individually transfer to a physics-aware underwater baseline, and at what efficiency–fidelity cost? |
| **RQ2** | Do they compose additively, or do they interact? |
| **RQ3** | Does primitive-population reduction perturb the identifiability of the medium model, and does a re-identification procedure restore it? |
| **RQ4** | What integration properties, invisible to each component method's own validation, govern whether the composition behaves as intended? |

RQ4 is unusual for a thesis of this kind and is included deliberately. The composition has
properties that belong to neither the baseline nor the mechanism being added, and §3.5.6
documents four such properties that were discovered only by executing the pipeline.

### 3.1.4 Hypotheses

| | Hypothesis | Contrast |
|---|---|---|
| **H1** | Each mechanism moves its own target cost beyond seed dispersion | main effects, both directions |
| **H2** | Efficiency gains are attenuated relative to published terrestrial magnitudes | renormalised comparison |
| **H3** | Simplification and quantization are sub-additive in fidelity cost | `A6 − A2 − A3 + A0` |
| **H4** | Primitive reduction perturbs medium identifiability; a re-identification burst mitigates it | β trajectory across the simplification boundary |
| **H5** | Initialization and simplification are degenerate unless the primitive budget binds | `A4 − A1 − A2 + A0` |

H2 is structural rather than speculative for the quantization mechanism. The baseline sets
spherical-harmonic degree to zero, so each primitive carries fourteen floats rather than the
fifty-nine assumed by the compression literature, and the quantizable fraction falls from
55/59 to 10/14 (§3.7.2).

H4 is the study's central hypothesis and is developed in §3.5.6.

### 3.1.5 Unit of analysis and variables

The **unit of analysis is a training run**: one cell, one scene, one seed. Scenes are
treated as experimental blocks and seeds as repeated measures. Individual images and pixels
are **not** independent observations and are not treated as such.

- **Independent variables:** three binary factors — dense initialization (M1), spatial
  simplification (M2), attribute quantization (M3).
- **Dependent variables:** reconstruction fidelity (PSNR under both conventions, SSIM,
  LPIPS), primitive count, model size, render throughput, per-frame render time, peak render
  memory, training wall clock, effective optimizer steps.
- **Blocking variable:** scene (4 levels). **Repeated measure:** seed (3 levels).
- **Controlled:** hardware, undistorted image data, iteration schedule, evaluation schedule,
  storage container, LPIPS backbone, primitive budget, codebook size.
- **Measured but not controlled:** run-to-run dispersion, which §3.6.3 shows to be large
  enough to bound what the design can resolve.

---

## 3.2 Research Stages

The study proceeds in six stages. The staging is not merely administrative: each stage yields
a usable result on its own, so a campaign that exhausts its compute budget still produces a
defensible finding rather than a partial matrix.

| Stage | Cells | Runs | What it establishes |
|---|---|---:|---|
| **S1** | A0 | 12 | The baseline, its dispersion, and the reference point every ratio divides by |
| **S2** | A2 | 12 | RQ1 for simplification; **RQ3/H4** via the medium diagnostics |
| **S3** | A1, A3 | 24 | RQ1 for initialization and quantization |
| **S4** | A4, A5, A6 | 36 | RQ2 — the three two-way interactions |
| **S5** | A7 | 12 | RQ2 — the three-way term and the effect-from-above contrasts |
| **S6** | A0D | 12 | A supplementary contrast described in §3.6.2 |

A reference control of four further runs — unmodified SeaSplat at its published
configuration, one per scene — is run alongside, bringing the campaign to 112 runs.

Campaign state is held in a durable ledger rather than in a process, because the compute
environment terminates sessions long before the campaign completes. Interrupted runs are
**restarted rather than resumed**, deliberately: the inherited checkpoint omits the medium
model, the learned background, the codebooks and the loop's schedule flags, so resuming would
silently reinitialise the medium parameters and produce a run that looks complete and is a
different experiment.

*Figure 3.1 — Research stages and their dependencies. [to be produced]*

---

## 3.3 Dataset

### 3.3.1 Provenance and composition

The corpus is the **SeaThru-NeRF dataset** (Levy et al., 2023): four underwater scenes
captured with a housed DSLR by a diver, with camera poses recovered by structure-from-motion
(Schönberger & Frahm, 2016).

| Scene | Images | Water body | Character |
|---|---:|---|---|
| Curasao | 21 | Caribbean | Reef structure, moderate visibility |
| IUI3-RedSea | 29 | Red Sea | Reef wall, higher visibility |
| JapaneseGradens-RedSea | 20 | Red Sea | Coral garden, mixed range |
| Panama | 18 | Pacific | Turbid, strong backscatter |

Eighty-eight images in total.

### 3.3.2 Why this corpus

Its principal strength is comparability. The convention throughout this lineage is to hold
out every eighth image by index order, so the held-out frames used here are *the same frames*
that SeaThru-NeRF, SeaSplat and the competing underwater methods hold out. A fidelity number
produced in this study is measured on the same pixels as a published one — a stronger form of
comparability than most cross-paper comparisons in this literature enjoy.

The scenes also span a useful range of water conditions, which matters because the medium
model's identifiability is a function of how much the medium actually does to the image.

### 3.3.3 Data partitioning

Every eighth image by index order is held out, yielding **thirteen** evaluation frames across
the four scenes: three each from Curasao, JapaneseGardens and Panama, and four from the
twenty-nine-image IUI3-RedSea.

The remaining seventy-five frames are training views. **No validation split is used**, and no
hyperparameter is selected on held-out data; every configuration value is either inherited
from a source method or fixed in advance by a stated rule (§3.6.1).

### 3.3.4 Limitations that bound external validity

Thirteen evaluation images across four scenes is a small sample, and differences of a few
tenths of a decibel cannot be distinguished from run-to-run variation on it without repeated
runs and reported dispersion (§3.6.3). This is not a hypothetical concern: the baseline's own
published ablation reports differences below half a decibel from single runs with a randomly
seeded default `[repo: seasplat]`.

Four scenes is also the entire public corpus for this task. Claims of generalisation beyond
these water types are not available to this study and are not made.

*Figure 3.2 — Representative frames from each scene. [to be produced]*

---

## 3.4 Preprocessing

Preprocessing is deterministic, executed once per scene, and frozen before any training run
begins. Its output is hashed so that a run's manifest records exactly which data it consumed.

### 3.4.1 Camera model rectification

The distributed poses use the OpenCV camera model with radial and tangential distortion
coefficients. **The rasteriser assumes a pinhole projection and ignores distortion
parameters entirely** `[repo: gaussian-splatting]`. Training on the distributed data
therefore introduces a systematic geometric error that no downstream mechanism can correct
and no fidelity metric would attribute to its cause.

Every scene is undistorted to a `PINHOLE` model before use, and the conversion is asserted
rather than assumed: the pipeline refuses to proceed if any camera in a scene still reports a
distorted model.

### 3.4.2 Scene normalisation and the training split

Scene loading applies the inherited normalisation — cameras are centred and the scene scaled
so that the camera extent is unity — and applies the every-eighth-frame split described in
§3.3.3. The split is applied at load time and the resulting counts are written into the run's
manifest, so a silently empty test set cannot pass unnoticed.

### 3.4.3 Sparse initialization, baseline path

The baseline path initialises primitives from the structure-from-motion point cloud
distributed with the dataset: 25,837 points for Curasao, with comparable counts for the other
scenes. Each point becomes one primitive with opacity 0.1, isotropic scale derived from its
distance to nearest neighbours, and colour from the sparse reconstruction.

### 3.4.4 Dense initialization path

The dense path replaces that cloud with one derived from dense correspondences (§3.5.3). It
is produced **offline**, before training, and is treated as data rather than as part of the
model: each cloud is written once, hashed with SHA-256, and accompanied by a sidecar
recording the matcher configuration, the number of reference views, the correspondence count,
the filter thresholds and the number of held-out frames excluded.

**Correspondences are drawn from training views only.** Including held-out frames would leak
the test set into the model through its geometry — a leak no metric could reveal, because it
arrives as structure rather than as supervision. The count of excluded frames is recorded in
the sidecar so the exclusion is verifiable rather than asserted.

### 3.4.5 Output of the preprocessing stage

Per scene: an undistorted image set with pinhole intrinsics, a camera manifest, the sparse
cloud, and — for the dense-initialisation cells — one hashed dense cloud with its provenance
sidecar. Every training run records the hash of the cloud it consumed.

---

## 3.5 Proposed Method

### 3.5.1 Overview

The method is the SeaSplat baseline (Yang et al., 2024) extended by three efficiency
mechanisms acting at three disjoint points of the training pipeline, together with a set of
integration decisions that keep the medium model identifiable while the geometry beneath it
is replaced, thinned and quantized.

The distinction between those two halves is structural and is stated plainly. **The
mechanisms are not this study's contribution**: each is an established technique with a
published evaluation. What this study contributes is the account of what happens when they
are applied to a representation whose loss reads a rendered depth map into a physical model
of the medium — a condition none of the three was designed for.

*Figure 3.3 — Architecture of the proposed method, showing the three intervention points.
[to be produced]*

### 3.5.2 The baseline

**Representation.** An explicit set of anisotropic 3D Gaussians, each carrying a position, a
covariance factored into scale and rotation, an opacity and a colour. Colour uses
**zero-order spherical harmonics only** — one RGB triple per primitive — on the reasoning
that underwater object colour is treated as view-independent, the view-dependence in the
observed image being attributable to the medium. Per-primitive storage is therefore fourteen
floats rather than the fifty-nine of unmodified 3DGS. This single inherited choice reappears
at three separate points later in this chapter.

**Image formation.** The rendered image is reinterpreted as the medium-free radiance *Ĵ* and
composed through the revised underwater model before comparison:

> *Î* = *Ĵ* ⊙ exp(−*β*<sub>att</sub> *Ẑ*) + σ(*B*<sup>∞</sup>) ⊙ (1 − exp(−*β*<sub>bs</sub> *Ẑ*))

where *Ẑ* is rendered depth, *β*<sub>att</sub> and *β*<sub>bs</sub> are **distinct**
attenuation and backscatter coefficients (Akkaynak & Treibitz, 2018), and *B*<sup>∞</sup> is
the water colour at infinity. Nine scalars describe the medium for the entire scene.

The photometric loss is applied to *Î*, not to *Ĵ*. This is the whole mechanism: the
optimiser sees photometric residual only *through* the medium composition, so veiling haze is
paid for by the medium model rather than by inventing primitives in the water column.

**Depth.** The medium model requires a per-pixel range, obtained by a second rasterisation
pass with primitive colour overridden by camera-frame depth, divided by accumulated opacity,
and — critically — **renormalised to the unit interval by its own minimum and maximum,
independently for every frame**. That renormalisation is the hinge of §3.5.6.

### 3.5.3 Component 1 — Dense deterministic initialization (M1)

**Source.** EDGS (Kotovenko et al., 2026).

**Mechanism.** Rather than initialising from a sparse structure-from-motion cloud and growing
the population by adaptive density control, M1 initialises from **dense correspondences**
computed by a learned matcher (RoMa; Edstedt et al., 2024) and **disables densification
entirely**. Reference views are selected by k-means over camera poses; each is matched
against its nearest neighbours; correspondences are triangulated; and surviving points become
primitives.

**Adaptations required by this study.**

*Correspondences from training views only* (§3.4.4). *A cheirality check alongside the
reprojection filter* — a correspondence is kept only if its triangulated point lies in front
of both cameras. The source specifies only a reprojection-error filter, which is insufficient
here: near-parallel view rays, common in forward-facing captures, produce confident matches
that triangulate behind a camera with small reprojection error, and with densification
disabled nothing downstream removes them.

**A constraint imposed by the corpus.** The number of reference views is `min(num_refs, V)`
where *V* is the training-view count. The source default of 180 exceeds the total view count
of every scene here (15–25 training views), so the realised value collapses to the view
count. The resulting clouds hold 299,368–471,531 points — **8–19% of the population the
baseline converges to** `[measured n=12]`, where the source method builds approximately 3.6
million. **The configuration therefore sits off the saturation curve the source method
published**, and this is recorded rather than glossed: it is a property of the corpus, not of
the implementation, and it bounds what M1 can be expected to do.

**Undocumented behaviours carried with the mechanism.** The source applies a continuous
opacity decay and a clamped position learning rate; neither appears in its paper. Both are
ported, both are exposed as configuration, and the scheduling of the decay is itself an
integration decision (§3.5.6).

### 3.5.4 Component 2 — Spatial reorganization and budget pruning (M2)

**Source.** Mini-Splatting (Fang & Wang, 2024).

**Mechanism.** A per-primitive importance score is accumulated over every training view from
the rasteriser's internal blending weights and projected areas, and the population is reduced
to a fixed budget by **importance-weighted stochastic sampling**. The scoring runs at two
scheduled iterations.

**Two details of the source method are load-bearing and are reproduced exactly.**

First, importance is accumulated blending weight normalised by projected area, counted only
in views where the primitive is the argmax contributor. This requires per-primitive
accumulators that the baseline's rasteriser does not emit, and obtaining them is the reason
for the rasteriser substitution discussed in §3.5.6.

Second, selection is **stochastic, not deterministic top-k**. The source paper establishes
that deterministic top-k pruning destroys local geometry because importance is spatially
autocorrelated, and validates the stochastic alternative by Chamfer distance rather than by
PSNR. **A deterministic implementation is not this mechanism**, and would reproduce the
failure the source method exists to avoid.

**Scoping.** Mini-Splatting also contains a densification half — depth reinitialisation and
blur-based splitting. That half is **not** used: it would collide with M1 in the combined
cells, and this study's factor is population *reduction*. The scoping is a deviation from the
source method as published and is reported as such.

**Budget.** A single primitive budget is used, fixed **before** the campaign by a stated
rule: the budget must lie below the smallest primitive count any other enabled mechanism
produces, or it is provably inert under M1 and two cells of the matrix become exact
duplicates of two others. Against the measured dense clouds, 200,000 satisfies this for every
scene. The realised post-simplification count is stochastic and is reported per run rather
than the target.

### 3.5.5 Component 3 — Attribute vector quantization (M3)

**Source.** CompGS (Navaneet et al., 2024), referred to here as CompGS-VQ.

**Mechanism.** Attributes are replaced by indices into learned codebooks, with **quantization
applied during training** and gradients routed to the unquantized parameters by a
straight-through estimator. Codebook centroids are updated every step and assignments
recomputed periodically.

**Post-hoc clustering is not this mechanism.** The source method identifies precisely that
condition as the problem it exists to solve: nothing in a standard objective makes parameters
clusterable, so clustering a converged model degrades quality in a way quantization-aware
training avoids.

**Three groups, not four.** The source quantizes colour DC, higher-order spherical
harmonics, scale and rotation. At `sh_degree = 0` there are no higher-order harmonics, so
three groups remain. **Position and opacity are never quantized** — sharing positions makes
distinct primitives coincide, and opacity is a scalar with nothing to gain. That exclusion is
structurally important here: it means M3 cannot corrupt the position field that produces
depth, nor the opacity field the baseline's priors police.

**Adaptation.** Codebook initialisation uses k-means++ seeding with empty-cluster reseeding,
replacing the source's uniform random initialisation. This is a defect correction rather than
a stylistic change: uniform seeding can place two centroids in one dense region while another
receives none, and Lloyd iterations cannot recover, giving higher quantization error at
identical storage — which is the quantity M3 is measured on `[measured: worst-case error on
the test fixture fell from 5.14 to 0.20]`.

**One source mechanism is deliberately disabled.** CompGS-VQ includes an ℓ1 opacity
regulariser that reduces the primitive count. It is disabled here, because with it enabled M3
and M2 would both reduce population and would not be independent factors. The consequence is
stated rather than hidden: **this study's M3 results are not a reproduction of CompGS-VQ's
published figures**, and its frame-rate gain in particular is expected to be smaller, because
the source method's published speedup is credited by its own authors to that regulariser.

### 3.5.6 Integration decisions

This section is where the study's own technical content lives. Each item is a decision the
source methods do not specify, forced by their composition.

**(a) The medium model is not invariant to primitive-count reduction.**

The medium model's only spatial input is *Ẑ*, and *Ẑ* is renormalised per frame by its own
minimum and maximum. Removing primitives changes the rendered depth map, hence changes those
normalisation constants, hence rescales the medium model's input — and because *β* and *Ẑ*
enter the composition only as their product, *β* must rescale to compensate. **Simplification
therefore injects a degeneracy the baseline's own analysis identifies and defends against,
from outside the objective, where none of the baseline's defences apply.**

*The remedy.* A medium re-identification burst is performed immediately after each
simplification event: the geometry is held fixed and the medium parameters alone are
optimised for a short interval, on the reasoning that the medium model must be re-fitted to a
depth map that has discontinuously changed.

*The diagnostic.* The depth normalisation constants and all nine medium scalars are logged at
a fixed interval and at every intervention boundary, which converts H4 from an argument into
a measurement.

*What the measurement shows.* Every simplification run's largest single-step attenuation
change lands on a simplification boundary, at magnitudes of 25–195%; no baseline run loses an
attenuation channel `[measured n=12, with a 12-run control]`. **The remedy as configured does
not restore the medium parameters** — the post-burst state is already collapsed in the
affected runs — and this is reported as a negative result about the study's own proposed
mechanism.

The collapse is **bistable and conditioned on seed rather than scene**: six of twelve runs,
spread across all four scenes, with the same configuration on the same scene collapsing on one
seed and surviving on another `[measured n=12]`. Its consequence for the analysis is treated
in §3.6.3.

**(b) An integration boundary can preserve every value and still change which gradients
flow.**

Adaptive density control decides what to clone or split from the accumulated norm of the loss
gradient with respect to screen-space positions. Each rasterisation call owns one such buffer,
so whichever losses backpropagate through a given pass, their gradients land in that pass's
buffer and nowhere else.

Substituting the rasteriser (§3.5.4) preserved every forward value — alpha in range,
compositing correct, depth recovered to seven decimal places — and silently removed
alpha-derived gradients from the densification signal. The baseline configuration then
converged to one sixth of the baseline's primitive count. **No check on a returned value
could observe this**, and every acceptance check in the study was, at that point, a check on
a returned value.

The invariant now asserted, in both directions, is: *density control must see the image and
alpha, and must not see depth.* Both halves are load-bearing — omitting alpha gives 743,457
primitives, admitting depth as well gives 635,038, and satisfying both reproduces the
baseline within its run-to-run spread `[measured n=3]`.

**(c) Coupled parameters must be controlled at the switch, not at each site.**

The source of M1 disables the periodic opacity reset by setting its interval past the end of
training. That single parameter gates **two** mechanisms: the reset itself, and the
size-based prune that removes primitives by screen radius or world-scale. Under dense
initialization, densification never runs and primitive scales derive from correspondence
distance rather than from optimisation, so arming that prune removes most of the cloud with
nothing to replace it.

Reimplementing the source's intent site by site re-armed each mechanism in turn, across three
successive corrections `[measured n=1 each]`. The decision recorded here is to control the
behaviour at the parameter the source method uses, and the generalisable observation is that
**a composed method inherits its components' coupling as well as their behaviour**.

**(d) Interrupted runs restart rather than resume** (§3.2), because the inherited checkpoint
is incomplete in ways that would produce a silently different experiment.

### 3.5.7 An opportunity identified and not taken

The importance metric used by M2 was designed to suppress sky in terrestrial scenes by
normalising for projected area. Underwater, the structural analogue of sky is not the far
field — it is near-camera haze geometry, which has large projected area and low per-pixel
contribution. A medium-aware importance metric, weighting by the transmission map, is
therefore identifiable as a plausible improvement.

**It is not implemented.** Doing so would add a fourth factor whose interactions this study
cannot afford to measure, and would make M2 no longer the published mechanism. It is recorded
as future work.

---

## 3.6 Experimental Design

### 3.6.1 The factorial design

Three binary factors give eight configurations:

| Cell | M1 init | M2 prune | M3 quant | Isolates |
|---|:--:|:--:|:--:|---|
| **A0** | — | — | — | The baseline, and the denominator of every ratio |
| **A1** | ✓ | — | — | Initialization alone |
| **A2** | — | ✓ | — | Simplification alone; the primary H4 test |
| **A3** | — | — | ✓ | Quantization alone |
| **A4** | ✓ | ✓ | — | Init × prune |
| **A5** | ✓ | — | ✓ | Init × quant |
| **A6** | — | ✓ | ✓ | Prune × quant; the H3 test |
| **A7** | ✓ | ✓ | ✓ | Three-way term, and effects-from-above |

Eight cells × four scenes × three seeds = **ninety-six runs**.

**Every main effect is estimated in both directions** — the mechanism added to the bare
baseline, and the mechanism removed from the complete system. Where the two agree within
pooled dispersion, the mechanism is independent of the others and either figure may be
quoted. Where they disagree, **neither may be quoted alone**; the disagreement is the
interaction and is reported as such.

**A ninth cell** (A0D, twelve runs) measures a supplementary contrast arising from §3.5.6(b):
detaching alpha-derived gradients from density control proved to be a large,
cheap population reduction in its own right. It is *not* a fourth factor, because M1 disables
densification and the contrast is therefore provably inert in all four M1 cells; a
sixteen-cell design would be half duplicates.

*Figure 3.4 — The factorial design and its contrasts. [to be produced]*

### 3.6.2 Why not a cumulative ladder

The source literature reports cumulative ablations: baseline, baseline + A, baseline + A + B.
That design cannot separate the effect of B from the effect of B *given* A. Since the central
question of this study is whether three mechanisms interfere with one another and with the
medium model, the ladder is structurally unable to answer it.

### 3.6.3 Repeated runs, dispersion, and the collapse covariate

**Three seeds per configuration per scene.** Results are reported as mean and standard
deviation across seeds, at both per-scene and aggregate level, for every measure.

This is the study's dominant cost and it is not negotiable. **No source method reports error
bars.** The baseline's published ablation contains differences of a few hundredths of a
decibel between rows, from single runs with a randomly seeded default.

**Bit-exact reproduction is unattainable and is not pursued.** The rasteriser uses atomic
accumulation in its backward pass, which is non-deterministic in floating-point arithmetic
irrespective of seeding. The correct response is to measure dispersion, and the measurement
is larger than the design assumed:

| Scene | mean primitives | sd | CV |
|---|---:|---:|---:|
| Curasao | 3,757,808 | 550,866 | 14.7% |
| IUI3-RedSea | 2,537,851 | 242,367 | 9.6% |
| JapaneseGradens-RedSea | 2,235,661 | 134,610 | **6.0%** |
| Panama | 2,305,920 | 676,400 | **29.3%** |

`[measured n=12]`

**Dispersion is heterogeneous across scenes by a factor of five**, and Panama's slowest and
fastest seeds differ by 1.85× at identical configuration. A pooled variance estimate would
hide this, so dispersion is reported **per scene**. At the mean coefficient of variation with
three seeds, a difference on primitive count must exceed roughly **17%** to clear the noise
floor; main effects are far larger, and interaction terms — differences of differences,
carrying approximately twice the variance — may not be.

Where an effect is of the same order as its dispersion, it is reported as **undetermined**.
A null interaction and an unresolvable one are different findings and are not conflated.

**The collapse covariate.** Because the medium-model collapse of §3.5.6(a) is seed-conditioned,
a cell whose three seeds are {collapsed, collapsed, intact} contains two physically different
models, and a mean over them measures neither. Every run therefore carries its collapse state,
and any aggregate that mixes states is flagged before the contrast is reported rather than
silently averaged.

### 3.6.4 Training configuration

All cells share the inherited schedule: 30,000 iterations, densification active to 15,000
where enabled, medium model active from 10,000, simplification at 15,000 and 20,000 where
enabled, quantization-aware training from 22,000 where enabled.

**Iterations and effective optimizer steps are both recorded**, because they are not
proportional: the medium model's alternating optimisation performs additional
forward-backward passes outside the iteration counter, and 30,000 iterations corresponds to
approximately 43,000 optimizer steps `[measured n=12]`. A cost reported in one unit is not
comparable with a cost reported in the other.

---

## 3.7 Evaluation Metrics

### 3.7.1 Reconstruction fidelity

**PSNR is computed under both conventions in use in this literature and both are reported.**
The pooled convention computes PSNR from mean squared error pooled over pixels and channels;
the per-channel convention averages the PSNR of each channel, which is systematically higher
by Jensen's inequality. The source methods differ in which they use and none states it in
text. Reporting one alone would make a cross-paper comparison silently wrong.

**SSIM** (Wang et al., 2004) uses the standard 3DGS implementation: 11×11 Gaussian window,
σ = 1.5. **LPIPS** (Zhang et al., 2018) uses the **VGG** backbone, stated explicitly because
VGG and AlexNet give systematically different values and no source paper reports which it
used.

Metrics are computed on 8-bit images re-read from disk as PNG. This is recorded because it is
not comparable with methods scoring linear pre-photofinished data.

**All three fidelity measures are reported together**, and none is used alone to certify a
result. §3.7.3 gives the reason.

### 3.7.2 Computational efficiency

| Measure | Definition |
|---|---|
| **Primitive count** | Realised count at convergence, never the target budget |
| **Model size** | Bytes of the compressed artifact, **with the container stated** |
| **Render throughput** | Frames per second over the held-out views |
| **Per-frame time** | Milliseconds per frame, with dispersion |
| **Peak render memory** | Peak device allocation during rendering |
| **Training wall clock** | Training loop only, excluding scene load and evaluation |

**Model size requires care and is a recorded source of error.** Three defensible numbers
exist for the same model: the interchange PLY at 68 bytes per primitive — which includes
three normal floats that the representation never uses and always writes as zero — an
uncompressed baseline at 56 bytes, and the compressed artifact. Quoting the wrong pair
inflates a compression ratio by 1.21× before any mechanism acts. Every size figure in this
study is measured on the compressed artifact and reported with its container.

**The compression ceiling is structural.** At `sh_degree = 0` a primitive is fourteen floats,
of which position (three) and opacity (one) are never quantized. Sixteen of fifty-six bytes
are therefore untouchable, and with three 12-bit indices the achievable ratio is
approximately **2.7×** `[measured n=1]`. The compression literature's published ratios of
41–65× are measured against fifty-nine floats and additionally include population reduction
from a regulariser this study disables. **The two figures are different quantities and are
not tabulated together.**

**Frame rate is measured under a stated protocol**: the colour pass alone, over the held-out
views, with device synchronisation around the timing loop and warm-up frames discarded.
Synchronisation is load-bearing — CUDA kernel launches are asynchronous, and timing without
it measures how fast the host can enqueue work. The probe passes used by the medium model are
excluded, as they serve training rather than rendering.

**Frame-rate gains are expected to be sub-linear in primitive reduction**, and the first
measurements show this is not even a single exponent: a 14.3× reduction bought 1.48×, while a
29.7× reduction bought 4.27× `[measured n=1 per cell]`. **A primitive-count ratio does not
predict a frame-rate ratio**, and no such implication is drawn.

**Composite per-megabyte ratios are not used.** Ratios of quantities with different units
inherit the container ambiguity above and obscure rather than summarise the trade-off;
rate–distortion reporting is used instead.

### 3.7.3 Medium-model diagnostics

Fidelity and efficiency metrics are insufficient to certify this method, and the reason is
demonstrable rather than precautionary.

PSNR, SSIM and LPIPS all score the **composed** image *Î*. A model whose attenuation term has
collapsed to unity and whose backscatter term has saturated to a constant is no longer
physical — it is plain Gaussian splatting with a global colour offset — but it can still fit
*Î*, and the fidelity metrics cannot distinguish it from an intact model.

**This is observed, not hypothesised.** One run in this study produced the campaign's highest
test PSNR — above the baseline's — with two of its three attenuation channels permanently
clamped at zero `[measured n=1]`.

The following are therefore reported alongside the standard metrics:

- the depth normalisation constants, at a fixed interval and at every intervention boundary;
- all nine medium scalars on the same schedule;
- **the collapse state of every run**: which attenuation channels, if any, ended negative and
  are therefore permanently clamped out of the model.

**No efficiency or fidelity result in this study is reported without its collapse state.**

---

## 3.8 Reproducibility Protocol

**Seeding.** Every run receives an explicit seed; the baseline's state-initialisation routine
is patched to seed the device generator, which upstream never does; and every run records its
seed alongside its fully resolved configuration. Bit-exact reproduction remains unattainable
for the reason given in §3.6.3, and dispersion is reported instead of determinism being
claimed.

**Per-run manifest.** Each run writes the resolved configuration, the git commit of the
implementation, the full command line, the GPU model and driver version, the framework and
CUDA versions, the host compiler, the dataset split sizes, and the hash of any dense cloud
consumed. The host compiler is included because it supplies the standard library headers the
CUDA extensions compile against and is invisible in every other version string — a change to
it broke the build mid-campaign while every other version reported the expected value.

**Hardware.** All runs execute on a single NVIDIA A100-SXM4-40GB (sm_80). The harness refuses
to start on a different device, because every conclusion in this study is a between-cell
contrast and cells on different devices are not comparable.

**Acceptance tests.** Ten test suites, eighty-one checks, are run before any campaign session.
The decisive checks assert the rasteriser identity on which every cell depends, the gradient
destination invariant of §3.5.6(b), and the scheduling invariant of §3.5.6(c). Suites that
assert *behaviour* rather than *returned values* were added in response to the defects those
sections describe.

**Artifacts retained per run.** Diagnostics trajectory, evaluation metrics, resolved
configuration, medium-model parameters, compressed model artifact, and training log. Full
point clouds are retained for one seed per cell; checkpoints are not written, because
interrupted runs restart rather than resume.

---

## 3.9 Threats to Validity

**Undocumented behaviours travel with their mechanisms.** Three of the four source codebases
contain behaviours their publications omit — a continuous opacity decay and a clamped learning
rate in the initialization codebase, a removed opacity reset in the pruning codebase, an
undocumented parameter transfer in the baseline. Each is ported explicitly, exposed as
configuration and recorded in the manifest, but a mechanism's *published* description and its
*implemented* behaviour are not the same object and this study measures the latter.

**The mechanisms are not reproductions.** M2 omits the source's densification half; M3
disables the source's opacity regulariser. Both deviations are required to keep the factors
independent, and both mean the corresponding published figures are not reproduced here.

**Single operating points.** Each mechanism is evaluated at one budget and one codebook size.
The design can therefore answer whether the mechanisms interact; it **cannot** establish that
any ranking among them persists across operating points, and no such claim is made. A
rate–distortion sweep is identified as the highest-value extension.

**Sample size.** Four scenes, thirteen held-out frames, three seeds. Effect sizes are reported
against measured dispersion with the sample size stated; **no claim of statistical
significance in the hypothesis-testing sense is made**, because three seeds on four scenes
does not support a formal test with meaningful power and reporting a p-value from that sample
would give a false impression of rigour.

**Deployment is not evaluated.** No embedded hardware, power budget, latency requirement or
memory constraint is tested. Peak render memory is measured on a data-centre GPU. Claims
about deployment on autonomous underwater vehicles are outside this study's evidence and are
not made.

---

## 3.10 Summary

The chapter has specified a controlled factorial experiment over three efficiency mechanisms
applied to a physics-aware underwater reconstruction baseline: eight configurations, four
scenes, three seeds, with a ninth supplementary cell and a four-run reference control.

Its methodological content is concentrated in §3.5.6 and §3.7.3 — the integration decisions
forced by composing methods whose assumptions do not overlap, and the diagnostics required
because the standard metrics are structurally unable to detect one of the failure modes this
composition produces.

---

## Sources cited in this chapter

Listed for verification during drafting; they belong in the thesis bibliography rather than
here. Preprint identifiers are given where the peer-reviewed version was not the copy
consulted, per the brief's requirement to explain preprint use.

- Akkaynak, D., & Treibitz, T. (2018). A revised underwater image formation model.
  *Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition*.
- Edstedt, J., Sun, Q., Bökman, G., Wadenbäck, M., & Felsberg, M. (2024). RoMa: Robust dense
  feature matching. *Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern
  Recognition*.
- Fang, G., & Wang, B. (2024). Mini-Splatting: Representing scenes with a constrained number
  of Gaussians. *European Conference on Computer Vision*. arXiv:2403.14166
- Kerbl, B., Kopanas, G., Leimkühler, T., & Drettakis, G. (2023). 3D Gaussian splatting for
  real-time radiance field rendering. *ACM Transactions on Graphics, 42*(4).
- Kotovenko, D., Grebenkova, O., & Ommer, B. (2026). EDGS: Eliminating densification for
  efficient convergence of 3DGS. *Proceedings of the IEEE/CVF Conference on Computer Vision
  and Pattern Recognition*. **Note:** the released implementation predates the paper by
  approximately ten months and contains mechanisms the paper does not describe; this study
  measures the implementation and says so (§3.9).
- Levy, D., Peleg, A., Pearl, N., Rosenbaum, D., Akkaynak, D., Korman, S., & Treibitz, T.
  (2023). SeaThru-NeRF: Neural radiance fields in scattering media. *Proceedings of the
  IEEE/CVF Conference on Computer Vision and Pattern Recognition*.
- Mildenhall, B., Srinivasan, P. P., Tancik, M., Barron, J. T., Ramamoorthi, R., & Ng, R.
  (2020). NeRF: Representing scenes as neural radiance fields for view synthesis. *European
  Conference on Computer Vision*.
- Navaneet, K. L., Pourahmadi Meibodi, K., Abbasi Koohpayegani, S., & Pirsiavash, H. (2024).
  CompGS: Smaller and faster Gaussian splatting with vector quantization. *European
  Conference on Computer Vision*.
- Schönberger, J. L., & Frahm, J.-M. (2016). Structure-from-motion revisited. *Proceedings of
  the IEEE Conference on Computer Vision and Pattern Recognition*.
- Wang, Z., Bovik, A. C., Sheikh, H. R., & Simoncelli, E. P. (2004). Image quality
  assessment: From error visibility to structural similarity. *IEEE Transactions on Image
  Processing, 13*(4), 600–612.
- Yang, D., Leonard, J. J., & Girdhar, Y. (2024). SeaSplat: Representing underwater scenes
  with 3D Gaussian splatting and a physically grounded image formation model.
  arXiv:2409.17345
- Zhang, R., Isola, P., Efros, A. A., Shechtman, E., & Wang, O. (2018). The unreasonable
  effectiveness of deep features as a perceptual metric. *Proceedings of the IEEE Conference
  on Computer Vision and Pattern Recognition*.

**Author names and venues require verification against the PDFs before submission.** They
were transcribed from the repository's method breakdowns rather than from the papers
directly.
