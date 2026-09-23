---
section: "4.4.4"
title: "Qualitative and Geometric Behaviour"
chapter: 4
action: Refine
evidence: ["FINDINGS §9", "renders", "per_view_metrics.csv"]
figures: ["figure-4-07-simplification", "figure-q1-a2-simplification"]
tables: []
citations: []
status: refined
word_count: 718
---

# 4.4.4 Qualitative and Geometric Behaviour

Section 4.4.1 reports a perceptual cost that is resolved on every scene and a
pixel-metric effect that is resolved on none. That combination has a visible
signature, and this subsection identifies it.

> **[FIGURE Q1-A2]** `figures/chapter4/figure-q1-a2-simplification.pdf`
> *Spatial reorganisation against the reference and the baseline.* Near-field
> crop of one held-out view per scene, seed 0, in the order ground truth,
> reference, unmodified configuration, mechanism. Each panel carries the peak
> signal-to-noise ratio and learned perceptual similarity of the view shown; an
> accent border marks a run that lost an attenuation channel.
> **Status:** built · **Anchored on:** SS

The loss is high-frequency texture, and it is uniform across the frame rather
than concentrated at any depth or on any structure. Surfaces that carry fine
granular detail in the reference — the coral rubble on Curaçao, the encrusting
growth on Panama — are rendered in the mechanism's output as the same shapes
with the same colour and a smoother surface. Silhouettes, relief, depth
ordering and colour are preserved. Nothing is missing that a pixel-wise
comparison would weigh heavily, and a great deal is missing that a
feature-based comparison would.

This is what pruning to a fixed budget by an importance criterion produces. The
criterion retains primitives that contribute most to the rendered image, which
are the large ones covering many pixels, and discards the small ones whose
individual contribution is low. Fine texture is represented by exactly the
latter. The surviving population reproduces the scene's radiometry closely
enough that peak signal-to-noise ratio does not move, while carrying materially
less of the high-frequency content that learned perceptual similarity is
sensitive to. The two metrics disagree because the mechanism removes
precisely the component that distinguishes them.

> **[FIGURE 4.7]** `figures/chapter4/figure-4-07-simplification.pdf`
> *Spatial reorganisation against the reference.* Ground truth, the reference
> and the mechanism at the same view and crop, one row per scene, on the
> near-field region where the texture loss is visible.
> **Status:** built · **Anchored on:** SS

Geometrically the mechanism produces the tightest representations in the
campaign. Between 88 and 96 per cent of its primitives clear the visibility
threshold, against 23 to 43 per cent for the reference, and bounding-box
inflation falls to between 1.8 and 6.8 times where the reference reaches 313
times on one repeat (Section 4.2.6). Occupancy of the footprint grid falls to
between 1.3 and 3.3 per cent, and the ratio between the largest and median
primitive radius is the smallest of any configuration. What survives the cut is
compact, live and spatially concentrated: the importance criterion removes the
detached outlying primitives that the baseline optimiser produces, as well as
the invisible population, as a side effect of removing everything that does not
contribute.

The collapsed run on Japanese Gardens is the panel worth dwelling on. Its
composed image is indistinguishable from the unmodified configuration's beside
it, and its per-view peak signal-to-noise ratio is 24.8 dB against 25.0 dB.
Nothing in that panel indicates that the run's attenuation model has been
driven to a physically meaningless state. The failure is visible only in the
decomposition, which Figure 4.13 shows and which no fidelity metric in this
chapter evaluates. A qualitative subsection is the natural place to say this,
because a reader inspecting renders is doing exactly what would fail to detect
it.

Two limits apply to the material here, both from Section 4.1.4. All rendered
comparisons and all geometric statistics rest on the first repeat, so the
texture loss is illustrated rather than measured — Section 4.4.1 measures it —
and the geometric figures carry no dispersion. The collapsed panel shown is one
of five collapsed runs in this cell; the rate is established in Section 4.4.3
from all twelve.

---

## Review log

**Domain Researcher** — The draft attributed the texture loss to "fewer
primitives", which does not explain why the loss is spectrally selective. The
importance criterion preferentially retains large primitives and fine texture
is carried by small ones, which is the mechanistic account. → *applied*, and it
now explains the metric disagreement rather than merely restating it. Second
finding: the tight-geometry result was absent, and it is this mechanism's most
distinctive representational property. → *applied*, with the inflation,
occupancy and radius-ratio figures.

**Supervisor** — The draft described the collapsed panel in passing. It is the
one place in the chapter where a reader can see for themselves that inspection
fails, and a qualitative subsection is exactly where that should be said.
→ *applied*: own paragraph, with the two per-view numbers and the observation
that a reader inspecting renders is doing what would miss it. Devil's advocate:
does this belong here or in Section 4.8? Both — Section 4.8 establishes it at
scale over twelve comparisons, this shows a reader the instance.

**Journal Reviewer** — "Uniform across the frame" was asserted from one crop
per scene. → *applied*: the claim is now scoped to what the near-field crops
show, with the single-repeat limit restated at the end. Second: geometric
statistics were quoted without saying they are seed-0 only. → *applied*.
