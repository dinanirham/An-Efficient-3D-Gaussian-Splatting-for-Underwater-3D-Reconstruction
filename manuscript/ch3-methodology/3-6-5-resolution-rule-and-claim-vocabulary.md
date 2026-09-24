---
section: "3.6.5"
title: "Resolution Rule and Claim Vocabulary"
chapter: 3
action: Add
evidence: ["PLAN", "FINDINGS §0"]
figures: ["figure-4-01-resolution"]
tables: ["Table 3.10"]
citations: []
status: refined
word_count: 738
---

# 3.6.5 Resolution Rule and Claim Vocabulary

Every quantitative claim in this thesis carries one of a small set of labels,
fixed in advance. This subsection defines them, because the labels do
substantive work: two of them mark the boundary of what the design can
establish, and a reader who reads them as ordinary hedging will misunderstand
the results.

## The rule

**An effect is reported as resolved when its magnitude is at least twice its
standard error**, computed against the repeat dispersion of the scene on which
it was measured. The standard error combines the dispersion of both
configurations entering the contrast, so a comparison against the reference
carries the reference's variability as well as the mechanism's.

Two standard errors is a threshold, not a significance test, and it is applied
identically to effects of both signs. No p-value is computed for a main effect
or an interaction. Where a hypothesis test is used — the collapse-incidence
comparison of Section 4.7.1 — the test is named with its result, and it is a
test on counts rather than on a continuous effect.

> **[TABLE 3.10]** *Claim vocabulary.*

| Label | Means | Does not mean |
|---|---|---|
| **resolved** | The 2 SE interval excludes the null, against per-scene repeat dispersion at three repeats | That the effect is large, or important |
| **`UNRESOLVED`** | Not separable from repeat dispersion at three repeats | That the effect is zero, or absent |
| **`UNDETERMINED`** | The design's resolution threshold for this contrast exceeds the largest effect the mechanisms produce, so no value of the quantity could be resolved | That the quantity was not computed, or was suppressed |
| **registered** | Stated in the analysis plan before results were examined | — |
| **post-hoc** | Formed after seeing the data it describes | That it is wrong, only that it was not tested |

## Why `UNRESOLVED` needs a rule of its own

The temptation with a threshold is to read everything below it as zero, and in
a study reporting efficiency mechanisms that reading would be systematically
favourable: a mechanism whose fidelity cost fails to resolve would be described
as free. **An unresolved effect and a zero effect are not distinguishable in
this design**, and no argument in this thesis treats them as though they were.
Chapter IV states this at the point of use rather than relying on this
definition, and Section 4.12.3 enumerates every quantity the design could not
resolve.

## Why `UNDETERMINED` is a separate label

`UNRESOLVED` is a property of an observation; `UNDETERMINED` is a property of
the design, known in advance of any observation. The standard error of a
two-way contrast is approximately twice that of a single cell mean, and of a
three-way contrast approximately 2√2 times. Applying the resolution rule to the
dispersion this corpus produces gives a smallest resolvable peak signal-to-noise
interaction of 0.51 to 1.61 dB depending on scene, against a largest
pixel-metric main effect of 0.80 dB.

**No interaction on that metric can be resolved by this design, whatever its
true magnitude.** This was registered before the analysis (Section 3.6.4), on
the arithmetic rather than on the results. The terms are nonetheless computed
and tabulated in Chapter IV, marked accordingly and not interpreted, because
omitting them would be selective reporting. Interactions are adjudicated on
perceptual similarity and primitive count instead.

> **[FIGURE 3.5]** `figures/chapter4/figure-4-01-resolution.pdf`
> *Resolvable effect size against observed effect size, per scene.* The 2 SE
> threshold for main, two-way and three-way contrasts, with the observed main
> effects overlaid. The separation between the pixel-metric interaction
> threshold and the largest observed main effect is what `UNDETERMINED` means.
> **Status:** built

## Registered and post-hoc

Every quantitative statement in Chapter IV is labelled as one or the other, in
the body text rather than in notes, because the strength of a claim depends on
which it is. A post-hoc statement is not thereby wrong — Section 4.7.4 contains
the study's most detailed characterisation of the collapse and is entirely
post-hoc — but it has not been tested, and a reader is entitled to weight it
differently from a prediction that survived a stated falsification condition.

---

## Review log

**Domain Researcher** — The draft gave the rule without saying what the
standard error combines, which matters because the anchoring decision means
most contrasts carry the reference's dispersion rather than only the
mechanism's. → *applied*. Second finding: the draft did not distinguish the
threshold from a significance test, inviting a referee to ask for p-values.
→ *applied*, including where a hypothesis test *is* used and on what.

**Supervisor** — The draft defined `UNRESOLVED` and left the misreading
implicit. The misreading is systematically favourable to the study's own
mechanisms, and naming that is what makes the rule a discipline rather than a
formality. → *applied*. Devil's advocate: is computing undetermined terms and
declining to interpret them just theatre? No — omitting them would let a reader
assume they were never computed, and the sign-flip pattern they show is itself
corroborating evidence for the resolution argument (Section 4.6.1).

**Journal Reviewer** — The vocabulary was described in prose and could not be
consulted. → *applied*: tabulated, with a "does not mean" column, since every
one of these labels has a common misreading. Second: `post-hoc` was defined
without saying that it is not a synonym for unreliable. → *applied*.
