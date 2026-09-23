---
section: "4.5.1"
title: "Reconstruction Fidelity per Scene"
chapter: 4
action: Rewrite
evidence: ["FINDINGS §2", "results_by_scene.csv"]
figures: ["figure-q1-a3-quantisation", "figure-4-15b-configurations-vs-reference"]
tables: ["Table 4.13"]
citations: ["Navaneet et al., 2024"]
status: refined
word_count: 762
---

# 4.5.1 Reconstruction Fidelity per Scene

Attribute-level quantisation replaces three per-primitive attribute vectors
with indices into learned codebooks, trained through a straight-through
estimator from a fixed iteration onward (Navaneet et al., 2024). Unlike the two
preceding mechanisms it does not change the number of primitives; it changes
what each one costs to store. This subsection reports its effect on fidelity.

> **[TABLE 4.13]** *Attribute-level quantisation against the reference, per
> scene.* Effect with z against repeat dispersion at three repeats; |z| below 2
> is reported `UNRESOLVED`. Source: `results_by_scene.csv`.

| Scene | ΔPSNR (dB) | z | ΔLPIPS | z | Verdict |
|---|---:|---:|---:|---:|---|
| Curaçao | +0.34 | +0.6 | +0.005 | +1.2 | both `UNRESOLVED` |
| IUI3 Red Sea | **−1.21** | **−3.1** | **+0.028** | **+14.2** | both resolved worse |
| Japanese Gardens | +0.34 | +1.1 | +0.004 | +1.4 | both `UNRESOLVED` |
| Panama | +0.12 | +0.4 | +0.004 | +1.1 | both `UNRESOLVED` |

**The mechanism is fidelity-neutral on three scenes and resolved worse on
both metrics on the fourth.** On Curaçao, Japanese Gardens and Panama neither
metric separates it from the published reference at three repeats, with pixel
effects between +0.12 and +0.34 dB and perceptual effects of 0.004 to 0.005 —
the latter a quarter of the pre-registered equivalence margin. On IUI3 Red Sea
it loses 1.21 dB and 0.028 in learned perceptual similarity, both resolved.

This is a different shape of result from either preceding mechanism.
Deterministic initialisation was radiometrically neutral everywhere and
perceptually costly on two scenes; spatial reorganisation was radiometrically
neutral everywhere and perceptually costly on all four. This mechanism is
neutral on both metrics on three scenes, and on the fourth the two metrics
agree with each other for the only time in the chapter. Where the other two
mechanisms produce a characteristic loss that one metric sees and the other
does not, quantisation on IUI3 Red Sea degrades the reconstruction in a way
both metrics register.

IUI3 Red Sea is the third mechanism section in which that scene carries the
cost, and it is the largest single-scene pixel-metric loss in the campaign.
Section 4.12.4 collects the five observations attaching to it; the one relevant
here is that it is the scene whose medium fit is least coherent (Section 4.2.4).
A mechanism that perturbs the per-primitive attributes will perturb whatever the
optimiser had balanced between geometry and medium, and a scene whose balance is
already poorly constrained has least margin to absorb it. That is a plausible
reading and not a tested one: the campaign varied neither the codebook size nor
the scene conditioning, so it cannot separate this account from the alternative
that the scene is simply the hardest.

> **[FIGURE Q1-A3]** `figures/chapter4/figure-q1-a3-quantisation.pdf`
> *Attribute-level quantisation against the reference and the baseline.*
> Far-field crop of one held-out view per scene, seed 0, in the order ground
> truth, reference, unmodified configuration, mechanism. Each panel carries the
> peak signal-to-noise ratio and learned perceptual similarity of the view
> shown.
> **Status:** built · **Anchored on:** SS

The factorial comparison agrees closely here, which is worth recording because
it has not elsewhere. Measured against the unmodified configuration the
mechanism resolves worse on IUI3 Red Sea at −1.36 dB and resolves *better* on
Japanese Gardens at +0.59 dB; measured against the reference the first survives
at −1.21 dB and the second does not. The anchoring difference costs one
resolved result rather than reversing any, and the mechanism's principal
fidelity finding — a resolved loss on one scene and neutrality elsewhere — is
the same under both. Where Sections 4.3.1 and 4.4.1 had to distinguish the two
comparisons carefully, here they largely coincide.

One property of this mechanism separates it from the other two and is developed
in Section 4.5.7. Its fidelity effect on the composed image is small, and its
effect on the *restored* image — the medium-free radiance that is the
estimator's distinguishing output — is not small at all. Nothing in this table
detects that, because every number in it describes the composed image. The
reader should not carry away from this subsection that quantisation is nearly
free; they should carry away that it is nearly free on the quantity these
metrics measure.

---

## Review log

**Domain Researcher** — The draft described the mechanism as "compressing the
model", which conflates what it does to the representation with what it does to
stored size, and obscures that primitive count is unchanged. → *applied*:
described as replacing attribute vectors with codebook indices, with the
straight-through estimator and citation, and the explicit statement that count
is untouched. Second finding: the draft offered no reading of why IUI3 Red Sea
should be the scene that fails, in a section where that is the only resolved
result. → *applied*, marked as plausible and untested with the alternative
named.

**Supervisor** — The draft's summary — "largely neutral" — is the conclusion a
reader will take away and it is wrong in a specific way that Section 4.5.7
overturns. Say so here rather than letting the correction arrive two
subsections later. → *applied*: closing paragraph distinguishes neutral from
neutral-on-what-is-measured. Second: the three mechanisms' result shapes had
never been compared, and doing so makes this one's distinctiveness visible.
→ *applied*.

**Journal Reviewer** — The perceptual effects on three scenes were given
without a scale. → *applied*: a quarter of the equivalence margin. Second: the
factorial figures were quoted alongside the anchored ones without saying which
was which. → *applied*: the paragraph now labels both and states that the
finding is unchanged under either. Third: the source method needed citation at
first mention. → *applied*, from the register.
