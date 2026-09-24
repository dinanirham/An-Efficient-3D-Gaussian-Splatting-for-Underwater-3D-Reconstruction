---
section: "4.6.6"
title: "Operating Points Across Configurations"
chapter: 4
action: Add
evidence: ["FINDINGS §7", "results_by_scene.csv"]
figures: ["figure-4-09-operating-points", "figure-4-15b-configurations-vs-reference"]
tables: ["Table 4.20"]
citations: []
status: refined
word_count: 862
---

# 4.6.6 Operating Points Across Configurations

The preceding subsections report how the mechanisms compose. This one asks
which of the resulting configurations a practitioner would actually choose, and
it is a description of nine points rather than an analysis of a curve.

**This is not a rate–distortion characterisation, and the distinction is not
pedantic.** Each mechanism was run at one operating point — one initial cloud
size, one pruning budget, one codebook configuration — so the campaign has no
curve within any mechanism and cannot say how a configuration would move if its
parameter were changed. What it has is nine configurations at fixed settings,
and the non-dominated subset of those nine. A front drawn through nine points
describes which of those nine are worth considering; it does not describe the
achievable frontier of the method.

> **[TABLE 4.20]** *Non-dominated configurations per scene.* Over the nine
> trained configurations of the factorial and the gradient-detachment contrast;
> the reference is excluded as the anchor rather than as a candidate. Source:
> FINDINGS §7.

| Scene | count × LPIPS | bytes × LPIPS |
|---|---|---|
| Curaçao | A0, **A1**, A4, A7 | A0, A1, A5, A6, A7 |
| IUI3 Red Sea | A0, A0D, **A1**, A2, A4, A5 | A0, A0D, A1, A5, A6, A7 |
| Japanese Gardens | **A1**, A3, A4, A5 | A1, A3, A5, A7 |
| Panama | A0, **A1**, A4, A5 | A0, A1, A3, A5, A7 |

**Deterministic initialisation is on the count against perceptual-error front
on all four scenes.** It is the only configuration for which that is true. A
reduction of nine to eighteen times at baseline perceptual error on three
scenes is the most favourable single operating point in the design, and it is
also the only mechanism among the three that works by not creating primitives
rather than by removing or compressing them.

**Spatial reorganisation alone is dominated on three scenes**, by the
configurations that pair it with deterministic initialisation. Those
configurations have both fewer primitives and lower perceptual error —
0.215 against 0.216 on Curaçao, 0.202 against 0.217 on Japanese Gardens, 0.193
against 0.203 on Panama. This is the favourable perceptual interaction of
Section 4.6.2 made visible as a choice: adding a second mechanism to spatial
reorganisation improves it on both axes simultaneously, which neither main
effect predicts. IUI3 Red Sea is the exception, as elsewhere.

**The full combination is on the stored-bytes front on every scene**, at 2.4 to
2.7 MB. Set against the reference this is a reduction of roughly 43 to 90
times, at a perceptual cost of 0.06 to 0.11 over the unmodified configuration.
That comparison requires a stated derivation, because the reference records no
stored size (Section 4.5.2): its size is computed as its primitive count at the
unmodified configuration's 56.0 bytes per primitive, which is exact for the
attribute layout both share but is a derived figure and not a measurement. The
derived reference sizes are 114 to 240 MB across the four scenes. A reader
should treat the 43-to-90-fold range as arithmetic on a measured count, not as
a measured ratio.

> **[FIGURE 4.9]** `figures/chapter4/figure-4-09-operating-points.pdf`
> *Operating points per scene.* Count against perceptual error and stored bytes
> against perceptual error, one panel per scene, with the non-dominated set
> connected.
> **Status:** built

**Fronts drawn on peak signal-to-noise ratio are shown for completeness only.**
On that metric the non-dominated sets are populated by the spatial-reorganisation
configurations, but Sections 4.3.1, 4.4.1 and 4.5.1 established that the
mechanisms' pixel-metric effects are unresolved against the reference on almost
every scene. A front drawn on a metric that does not separate the candidates is
a front drawn on repeat dispersion, and no selection should be made from it.
This chapter reports those fronts because omitting them would be selective, and
marks them as uninterpretable for the stated reason.

One observation runs against the direction of the rest of this section and is
recorded because of it. **Attribute-level quantisation begins to cost frame
rate once the population is small.** The full combination renders 8 to 18 per
cent slower than the configuration without quantisation on every scene, and the
simplification-plus-quantisation pair 5 to 22 per cent slower than
simplification alone on three. Section 4.5.2 reported no frame-rate effect for
that mechanism as a main effect, and both statements are correct: decoding a
codebook is a fixed cost per primitive that is negligible against three million
primitives and is not against 130 000. These are comparisons between
configurations rather than resolved contrasts, and they are reported as
descriptions.

The practical summary is conditional on which cost binds. Where the constraint
is the number of primitives — memory during rendering, or the cost of
downstream geometric processing — deterministic initialisation alone is on the
front everywhere and is the defensible default. Where the constraint is stored
size, the full combination reaches 2.4 to 2.7 MB and nothing else comes close.
Where the constraint is perceptual quality, the unmodified configuration is on
the front on three scenes and every mechanism costs something. And where the
output is the decomposition rather than the image, Section 4.7 shows that two of
these configurations lose an attenuation channel in a substantial minority of
runs, which no axis in this section registers.

---

## Review log

**Domain Researcher** — The draft quoted the reference's stored size as though
recorded. It is not: the reference logs only peak render memory, and the 114 to
240 MB figure is its primitive count at 56.0 bytes per primitive. → *applied*:
the derivation stated, with the instruction to read the ratio as arithmetic on
a measured count. Second finding: the draft called the section a
rate–distortion analysis. One operating point per mechanism cannot support
that. → *applied*, as the opening claim.

**Supervisor** — The draft listed fronts and left the reader to extract a
recommendation. The section's value is the recommendation, and it is
conditional on which cost binds. → *applied*: closing paragraph, four cases,
including the case where none of these axes is the right one. Devil's advocate:
does including the PSNR fronts while declaring them uninterpretable just add
noise? Omitting them would be selective reporting; marking them is the honest
alternative.

**Journal Reviewer** — The frame-rate observation appeared to contradict
Section 4.5.2 without reconciling the two. → *applied*: both statements shown
to be correct, with the fixed-cost-per-primitive reason and the status as
description rather than contrast. Second: the perceptual-error figures for the
dominance claim were given without saying which configurations they belong to.
→ *applied*.
