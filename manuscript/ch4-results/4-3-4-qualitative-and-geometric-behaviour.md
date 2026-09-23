---
section: "4.3.4"
title: "Qualitative and Geometric Behaviour"
chapter: 4
action: Refine
evidence: ["FINDINGS §9", "renders", "per_view_metrics.csv"]
figures: ["figure-4-06-initialisation", "figure-q1-a1-initialisation"]
tables: []
citations: []
status: refined
word_count: 742
---

# 4.3.4 Qualitative and Geometric Behaviour

Sections 4.3.1 and 4.3.2 establish that deterministic initialisation is
radiometrically neutral or better, perceptually worse on two scenes, and
between nine and eighteen times smaller. This subsection asks what the smaller
representation looks like, and what kind of primitive population produces it.

> **[FIGURE Q1-A1]** `figures/chapter4/figure-q1-a1-initialisation.pdf`
> *Deterministic initialisation against the reference and the baseline.*
> Near-field crop of one held-out view per scene, seed 0, with ground truth,
> the reference, the unmodified configuration and the mechanism in that order.
> Each panel carries the peak signal-to-noise ratio and learned perceptual
> similarity of the view shown.
> **Status:** built · **Anchored on:** SS

At near field the mechanism's renderings are close to the reference's on all
four scenes, and the difference that does exist has one consistent character:
fine structure is slightly softer. Branching coral on Curaçao and the coral
heads on IUI3 Red Sea lose a degree of micro-texture, with the silhouettes and
the larger relief preserved. This is the signature of a representation that
cannot add primitives where the residual is largest, since the population is
fixed before optimisation and the optimiser can only move, scale and recolour
what it was given. The perceptual metric is sensitive to precisely this kind of
loss and the pixel metric is not, which is the mechanism of the disagreement
reported in Section 4.3.1 rather than merely its restatement.

The per-panel numbers support that reading and carry a caution. Learned
perceptual similarity is worse for the mechanism at the view shown on **all
four** scenes, including the two where the scene-mean effect is unresolved. Peak
signal-to-noise ratio at the same view is also *lower* on all four — by 0.3 to
0.9 dB — while the scene means reported in Section 4.3.1 are *higher* on all
four. A single view has therefore reversed the sign of the pixel-metric result
while preserving the sign of the perceptual one. This is the clearest instance
in the chapter of the limitation stated in Section 4.2.3: the held-out set
contains thirteen frames of very unequal difficulty, the figures use one fixed
index per scene, and a panel illustrates a phenomenon without measuring it. No
claim in this section rests on the panels.

> **[FIGURE 4.6]** `figures/chapter4/figure-4-06-initialisation.pdf`
> *Deterministic initialisation against the reference.* Ground truth, the
> reference and the mechanism at the same view and crop, one row per scene.
> **Status:** built · **Anchored on:** SS
>
> **[DATA-NEEDED]** The specification for this figure also calls for the two
> input point clouds — the sparse structure-from-motion cloud the reference
> begins from, and the dense correspondence cloud this mechanism begins from —
> shown side by side. No point-cloud visualisation was collected in this
> campaign, and the panel is absent rather than approximated. Producing it
> requires a rendering pass over the initial clouds, which the retained
> artefacts permit.

Geometrically the mechanism produces a population of a different character
rather than simply a smaller one. Between 78 and 94 per cent of its primitives
clear the visibility threshold, against 23 to 43 per cent for the reference
(Section 4.2.6). The representation is therefore composed almost entirely of
primitives that contribute to an image, which is the consequence of never
having run the cloning-and-splitting procedure that generates the reference's
large non-contributing population. It is also why the mechanism's headline
reduction of nine to eighteen times becomes four to five times when measured
against the visible population: most of what it removes was never rendered.

Two further geometric properties are recorded without interpretation. The final
population is remarkably uniform in absolute size across scenes — 197 000 to
243 000 primitives where the reference ranges over a factor of two — because
the correspondence stage, not the scene, sets it. And the detached-outlier
pathology described in Section 4.2.6 is a baseline property that this mechanism
does not introduce; because full point clouds were retained for one repeat per
configuration, no rate can be given for it here, and none is claimed.

The qualitative evidence in this subsection covers one repeat per scene, for
the reason given in Section 4.1.4. Where Section 4.3.1 reports a resolved
effect, the resolution comes from the three-repeat metrics and not from these
images.

---

## Review log

**Domain Researcher** — The draft described the softening as "blur", which
implies a filtering operation that is not what happens. The mechanism cannot
place new primitives where the residual is large, so fine structure is
represented by fewer, larger primitives. → *applied*, with the link to why the
two metrics disagree, making Section 4.3.1's finding mechanistic rather than
merely observed. Second finding: the visible-fraction figure belongs here as a
statement about population character, not only in Section 4.2.6 as an
accounting correction. → *applied*.

**Supervisor** — The per-panel numbers contradict the scene means on the pixel
metric, and the draft passed over it. That is the single most dangerous thing
on the page for a reader who scans figures. → *applied*: stated directly, with
both signs given and the conclusion that no claim rests on the panels. Devil's
advocate: if the figure contradicts the table, why print the figure? Because it
shows the *character* of the difference, which the table cannot, and because
concealing a fixed-view reversal would be worse than explaining it.

**Journal Reviewer** — Figure 4.6 was cited as though it contained the input
clouds its specification calls for; the built figure does not. → *applied*:
`[DATA-NEEDED]` block naming exactly what is missing and what would be needed,
rather than a caption describing a panel that does not exist. Second: the
single-repeat basis of the qualitative material needed restating at point of
use. → *applied*: closing paragraph.
