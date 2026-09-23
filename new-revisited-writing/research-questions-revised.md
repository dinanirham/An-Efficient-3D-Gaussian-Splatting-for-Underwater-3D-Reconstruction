# Research questions, revised

**Status:** draft for approval. Supersedes the RQ table in `04-repositioning.md`
§"Research questions". Fixes the Chapter IV heading order and all of §5.1.

Two decisions drive this revision, both taken on 2026-09-24.

**1. Evaluation is anchored on SS, the published reference, not on A0.**
A0 is our own implementation with all three mechanisms off. It was serving as
both the internal control and the thing results were reported against, and the
second role belongs to the published method. Against SS, A0's PSNR intervals
straddle zero on all four scenes and its count ratio is ≈ 1 — that equivalence
is what *licenses* A0 as a control, and it is a validation result rather than a
headline.

This costs nothing in the factorial algebra. Re-expressing every configuration
as a difference from SS leaves the contrasts unchanged, because the reference
cancels:

> (A1 − SS) − (A0 − SS)  =  A1 − A0

So main effects and interactions keep their existing values and their existing
resolution thresholds. What changes is what a *configuration* is reported
against, and that is now SS everywhere.

**2. Evaluation runs on three axes, not two.**
Cost and image fidelity are the axes every 3DGS efficiency paper reports. On
those two axes alone this work is an application of known compression to an
underwater method, and a reviewer is entitled to ask what is underwater about
it. The third axis is the one the campaign actually measured and the one the
method exists to serve.

| | Axis | Measured by | Anchored on |
|---|---|---|---|
| **I** | Image fidelity of Î | PSNR, SSIM, LPIPS on held-out views | SS |
| **II** | Cost | primitive count, render rate; stored bytes | SS for count and rate; **A0 for bytes** |
| **III** | **Medium integrity** | collapse incidence, channel-ordering plausibility, Ĵ consistency across attribute states | SS where defined; otherwise absolute |

Axis II carries one unavoidable exception: the reference records no
`total_bytes` or `bytes_per_primitive`, so stored size cannot be expressed
against SS and is reported against A0 with that stated at the point of use.

---

## Central thesis statement

Unchanged in substance from `04-repositioning.md`; sharpened to name the axis
that carries it.

> Efficiency mechanisms developed for terrestrial 3D Gaussian Splatting do not
> transfer to physics-aware underwater reconstruction as independent,
> behaviour-preserving modules. Their integration with a scene-global medium
> model introduces couplings that are invisible to the component methods' own
> validation — and invisible to the image-fidelity metrics by which such
> methods are conventionally judged — yet these couplings determine whether the
> efficiency gains are realised as a physically meaningful reconstruction.

---

## The questions

| | Question | Axis | Adjudicated on | Status |
|---|---|---|---|---|
| **RQ1** | How far do the three mechanisms reduce the cost of a physics-aware underwater reconstruction relative to the published method, and at what cost in image fidelity? | I, II | per-configuration contrasts against SS, per scene, at 2 SE | **answered** |
| **RQ2** | Do the mechanisms compose additively, or do they interact? | I, II | two- and three-way factorial contrasts, both directions; **LPIPS and count only** — PSNR interactions are `UNDETERMINED` at n = 3 by construction | **answered, with one axis undetermined** |
| **RQ3** | Does reducing the primitive population compromise the identifiability of the medium model, and does any mechanism combination protect it? | III | collapse incidence per cell; Fisher exact across the M1 contrast | **answered** |
| **RQ4** | Are the image-fidelity metrics conventionally used to validate such methods sensitive to medium-model failure? | I vs III | collapsed-minus-intact within cell × scene, in baseline sd units | **answered: no** |

RQ5 of the earlier table ("does mechanism ranking persist across operating
points?") remains **not designed** — there is no budget sweep — and is carried
into Chapter V as further work rather than left standing as an open question.

### What each is answered by, and with what

**RQ1.** Against SS, A7 reaches 14–25× fewer primitives with PSNR
indistinguishable on three scenes and resolved *better* on Japanese Gardens,
against a resolved LPIPS cost of 0.04–0.11 on all four. M3 does not move the
count at all — it compresses attributes, not population — so its cost axis is
bytes, which is the one axis SS cannot anchor. The honest summary is not "free":
it is a large, resolved population reduction at indistinguishable PSNR and a
measurable perceptual cost.

**RQ2.** Unchanged by the re-anchoring, for the reason given above. The PSNR
limitation is structural and must be stated as such: the smallest resolvable
interaction is 0.51–1.61 dB against a largest main effect of 0.80 dB, so
`UNDETERMINED` here means the design cannot see it, not that it is zero.

**RQ3.** Collapse occurs in exactly two cells, and both are M2 without M1:

| Cell | M2 | collapsed / runs |
|---|---|---:|
| A2 | alone | 5 / 12 |
| A6 | with M3 | 4 / 12 |
| A4 | **with M1** | **0 / 12** |
| A7 | **with M1 and M3** | **0 / 12** |

Pooled, 9 of 24 without dense initialisation against 0 of 24 with it; Fisher
exact, two-sided, **p = 0.0016**. The *rate* is established. The registered
explanation for it was withdrawn (FINDINGS §5b) and the replacement is
descriptive: M1's cloud enters the first simplification event at ~224 k, so a
200 k budget removes a third of it rather than nine tenths. Chapter IV must
report the protection as established and the reason as open.

**RQ4.** Within each cell × scene of A2 and A6 holding both strata, collapsed
minus intact is a median 0.8 baseline sd across twelve comparisons, with PSNR
splitting 2+/4− and LPIPS 4+/2−. A model whose blue attenuation is −0.05 renders
held-out views as well as one whose blue attenuation is +1.2. The single
comparison past 2 sd has the *collapsed* run better. This is the answer that
makes the other three worth reporting: the axis on which the mechanisms differ
is the axis the conventional metrics do not measure.

---

## Hypotheses

Carried forward, with the two that the campaign settled promoted out of the
diagnostic role they were written in.

| | Hypothesis | Test | Outcome |
|---|---|---|---|
| **H1** | Each mechanism moves its own target cost beyond seed dispersion | main effects against pooled sd | held on every target cost |
| **H2** | Gains are attenuated relative to published terrestrial magnitudes | renormalised comparison | held; **structural for M3** — 14 floats per primitive, not 59 |
| **H3** | M2 × M3 is sub-additive | `A6 − A2 − A3 + A0` | see §3 |
| **H4** | Primitive reduction perturbs medium identifiability | β across the simplification boundary | **held; the registered mechanism withdrawn** — the level β reaches decides the outcome, not the fraction removed |
| **H5** | M1 × M2 is degenerate unless the budget binds | `A4 − A1 − A2 + A0` | controlled by preflight |
| **H6** | Dense initialisation protects the medium against simplification-induced collapse | collapse incidence, Fisher exact | **held, p = 0.0016; reason open** |
| **H7** | Image-fidelity metrics do not discriminate a collapsed medium from an intact one | collapsed − intact, in baseline sd | **held; median 0.8 sd, sign inconsistent** |

H6 and H7 are new as *hypotheses*. Neither is a new finding: both are recorded
in FINDINGS §5c and §8 respectively, where they sit as consequences of the
central test rather than as claims in their own right. Promoting them is the
substance of this revision.

---

## Consequences for Chapter IV

1. **§4.2 becomes validation, not results.** A0 ≡ SS is what licenses A0 as a
   control. It stops being the chapter's opening result.
2. **Every per-configuration table and figure re-anchors to SS**, with stored
   bytes the stated exception.
3. **A new section for axis III.** Medium integrity currently lives inside the
   hypothesis test of §4.7; it becomes an evaluation axis reported for every
   configuration, like fidelity and cost.
4. **RQ4 gets its own section and closes the chapter's argument**, immediately
   before the synthesis — it is the reason the other axes are insufficient.
5. **Figure 4.15b becomes a primary figure**, not a companion: it is the
   per-configuration answer to RQ1.

## What this does not claim

Ĵ has no ground truth. Nothing here asserts restoration *accuracy*. Axis III
rests on three things that need no ground truth: collapse, which is a clamp
event and objective; channel-ordering plausibility against known optical
behaviour, which FINDINGS §2b reports as descriptive and unresolved on the one
scene that disagrees; and Ĵ self-consistency between attribute states, which is
n = 1 per scene.

The β magnitudes are dimensionless with respect to a per-frame renormalised
depth. Channel *ordering within a scene* is comparable; magnitudes across
scenes are not physical quantities and are never reported as such.
