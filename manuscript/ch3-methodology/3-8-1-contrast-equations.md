---
section: "3.8.1"
title: "Contrast Equations"
chapter: 3
action: Add
evidence: ["PLAN", "analyse.py"]
figures: []
tables: ["Table 3.16"]
citations: []
status: refined
word_count: 782
---

# 3.8.1 Contrast Equations

Every effect reported in Chapter IV is a linear combination of cell means,
fixed in advance. This subsection gives them, so that any number in that
chapter can be recomputed from the per-cell results.

> **[TABLE 3.16]** *Contrasts.* Each is a weighted sum of cell means, computed
> per scene. M1 is deterministic initialisation, M2 spatial reorganisation, M3
> attribute-level quantisation.

| Effect | Contrast |
|---|---|
| M1, from below | A1 − A0 |
| M2, from below | A2 − A0 |
| M3, from below | A3 − A0 |
| M1, from above | A7 − A6 |
| M2, from above | A7 − A5 |
| M3, from above | A7 − A4 |
| M1 × M2 | A4 − A1 − A2 + A0 |
| M1 × M3 | A5 − A1 − A3 + A0 |
| M2 × M3 | A6 − A2 − A3 + A0 |
| Three-way | A7 − A4 − A5 − A6 + A1 + A2 + A3 − A0 |

**Main effects are estimated in both directions.** From below is the mechanism
added to the configuration where nothing is active; from above is the mechanism
removed from the configuration where everything is. The two are equal only if
the mechanism does not interact with the others, so reporting both is a
diagnostic as well as a report: where they agree within pooled dispersion,
either figure may be quoted, and where they disagree, neither may be quoted
alone (Section 3.6.1).

**Two-way interactions hold the third factor off.** The form is the design's
own: the effect of the pair minus the effects of each alone, all measured from
the corner where nothing is active. Writing it out,
(A4 − A0) − [(A1 − A0) + (A2 − A0)] reduces to A4 − A1 − A2 + A0.

**The three-way contrast is the standard sign-product form** over all eight
cells, with each cell's sign the product of its factor signs.

## Two properties of these contrasts that matter for interpretation

**They are built from the corner where no mechanism is active, not from the
reference implementation.** The arithmetic requires a corner of the design
cube, and the reference is not one. This does not conflict with the anchoring
decision of Section 3.6.2, because the reference cancels out of any difference
of differences: (A1 − SS) − (A0 − SS) is identically A1 − A0. Every contrast in
this table therefore takes the same value whether the underlying quantities are
expressed against the reference or against the no-mechanism corner.

**Every contrast is computed per scene.** None is pooled across the corpus, for
the reasons Section 3.3.2 establishes. Where Chapter IV reports a mechanism as
resolved, it reports on how many scenes and gives the per-scene values.

## Metric-dependent combination

Perceptual similarity and peak signal-to-noise ratio are combined additively:
the contrast is a difference in the metric's own units. **Primitive count,
stored bytes, render rate and training time are combined
log-multiplicatively**, because these are quantities whose natural composition
is a ratio: a mechanism that halves a count and another that halves it again
compose to a quarter, not to zero. Their contrasts are therefore ratios, and an
interaction of unity means the reductions multiply as independent composition
would predict.

This distinction is not cosmetic. Section 4.6.2 reports a count interaction of
eight to fourteen, which under additive treatment would be an uninterpretable
difference of millions of primitives and under the log-multiplicative treatment
is a clean statement: the pair removes eight to fourteen times less than
independent composition predicts.

## What is excluded

**The supplementary contrast of Section 3.5.5 appears in none of these
equations.** It is not a factor, it is provably inert wherever deterministic
initialisation is active, and differencing it against any factorial cell would
produce a quantity with no interpretation. It is compared against the
no-mechanism configuration alone, and Chapter IV reports it in a section of its
own.

---

## Review log

**Domain Researcher** — The draft gave the contrasts without the derivation of
the two-way form, which is the one a reader is most likely to want to check.
→ *applied*: written out and reduced. Second finding: the additive versus
log-multiplicative distinction was absent, and without it the count
interactions of Section 4.6 are unreadable. → *applied*, with the reason a
ratio is the natural composition for these quantities and the consequence for
Section 4.6.2.

**Supervisor** — The draft did not address the obvious objection: the chapter
anchors on the reference, so why are the contrasts built from A0? → *applied*:
the cancellation identity, stated so a reader can verify no contrast moves.
Devil's advocate: is estimating main effects in both directions redundant when
the interaction terms already measure non-additivity? It is not redundant in
use — the from-below figure is the one that gets quoted, and knowing whether it
survives the from-above check is what tells you if quoting it alone is honest.

**Journal Reviewer** — The exclusion of the supplementary contrast was stated
in Section 3.5.5 but not enforced visibly here, where the equations are.
→ *applied*: own subsection. Second: the contrasts were described as
"pre-registered" without a pointer to where. → *applied*: Section 3.6.4.
