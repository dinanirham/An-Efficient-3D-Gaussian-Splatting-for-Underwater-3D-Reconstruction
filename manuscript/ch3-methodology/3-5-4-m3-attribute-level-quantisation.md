---
section: "3.5.4"
title: "M3 — Attribute-Level Quantisation"
chapter: 3
action: Refine
evidence: ["CD register", "results_runs.csv"]
figures: []
tables: []
citations: ["Navaneet et al., 2024"]
status: refined
word_count: 826
---

# 3.5.4 M3 — Attribute-Level Quantisation

**Source.** CompGS (Navaneet et al., 2024).

**Mechanism as executed.** Per-primitive attributes are replaced by indices
into learned codebooks, with quantisation applied *during* training and
gradients routed to the unquantised parameters by a straight-through estimator.
Codebook centroids are updated every step and assignments recomputed
periodically. Quantisation becomes active at a fixed iteration and remains
active to the end of training.

**Post-hoc clustering is not this mechanism.** The source identifies precisely
that condition as the problem it exists to solve: nothing in a standard
training objective makes parameters clusterable, so clustering a converged
model degrades quality in a way that quantisation-aware training avoids. An
implementation that clustered after training would be measuring a different
thing.

## Three attribute groups, not four

The source quantises colour, higher-order spherical harmonics, scale and
rotation. At spherical-harmonic degree zero there are no higher-order harmonics
(Section 3.1.1), so three groups remain.

**Position and opacity are never quantised.** Sharing positions would make
distinct primitives coincide, and opacity is a scalar with nothing to gain from
a codebook. That exclusion is structurally important for this study rather than
merely sensible: it means this mechanism cannot corrupt the position field that
produces the rendered depth, and the rendered depth is what the medium model
reads. When Section 4.5.3 reports that the mechanism disturbs no medium
parameter, that is the expected consequence of this exclusion and not a
surprise.

## Adaptations made by this study

**Codebook initialisation uses k-means++ seeding with empty-cluster reseeding**,
replacing the source's uniform random initialisation. This is a defect
correction rather than a stylistic preference. Uniform seeding can place two
centroids inside one dense region while another region receives none, and
Lloyd iterations cannot recover from that: the result is higher quantisation
error at identical storage, which is precisely the quantity this mechanism is
measured on. On the test fixture used to verify the change, worst-case
quantisation error fell from 5.14 to 0.20.

**One source mechanism is deliberately disabled.** The source method includes
an opacity regulariser that reduces the primitive count. It is disabled here,
because with it enabled this mechanism and spatial reorganisation would both
reduce the population and would no longer be independent factors — the
factorial design requires that each factor act on its own target cost.

The consequence is stated rather than hidden: **this study's results for this
mechanism are not a reproduction of the source method's published figures**,
and its frame-rate result in particular is expected to be smaller, because the
source's published speed-up is credited by its own authors to that regulariser.
Section 4.5.2 reports no resolved frame-rate change on any scene, which is
consistent with that expectation and was registered in advance rather than
explained afterwards.

## What follows arithmetically

With three of fourteen per-primitive floating-point values replaced by codebook
indices, the storage cost per primitive is determined by the layout rather than
by the data. The realised figure is 20.6 bytes per primitive against 56.0, a
factor of 2.72, identical to three significant figures across all twelve runs.
Section 4.5.2 reports it as a structural fact carrying no uncertainty, for this
reason.

The same arithmetic bounds what the mechanism can achieve here. At full
spherical-harmonic degree a primitive carries fifty-nine values rather than
fourteen, and the three quantised groups would be a far larger share of the
total. **This configuration gives the mechanism less to compress than the
setting its source method was validated in**, which is a property of the
baseline's configuration for this corpus rather than of the mechanism, and is
recorded in Section 4.5.6 as a limitation on the compression result.

---

## Review log

**Domain Researcher** — The draft did not connect the position-and-opacity
exclusion to the medium result. It is the reason Section 4.5.3 finds no medium
disturbance, and stating it here converts that finding from a surprise into a
prediction. → *applied*. Second finding: the consequence of spherical-harmonic
degree zero was stated as a count of groups but not as a bound on the
mechanism's achievable compression. → *applied*: closing subsection, with
Section 4.5.6 named.

**Supervisor** — The draft disabled a source component and reported the fact
without the expectation that follows. If the frame-rate result is expected to
be smaller, saying so *before* Chapter IV reports no resolved change is what
makes it a registered expectation rather than a post-hoc rationalisation.
→ *applied*, with that phrasing explicit. Devil's advocate: is disabling a
component of a published method defensible? It is required by the design — two
factors reducing the same cost are not independent — and the cost of the
decision is stated in the same paragraph.

**Journal Reviewer** — The k-means++ change was described as a correction
without evidence that it corrects anything. → *applied*: the fixture measurement
of 5.14 to 0.20. Second: the 2.72 factor appeared without saying it is
arithmetic rather than measured, which Section 4.5.2 relies on.
→ *applied*, with the layout arithmetic given.
