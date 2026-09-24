---
section: "4.7.1"
title: "Incidence and Boundary Alignment"
chapter: 4
action: Add
evidence: ["FINDINGS §5a", "FINDINGS §5c", "medium_collapse.json"]
figures: ["figure-4-20-collapse-onset", "figure-4-c5-medium-convergence"]
tables: ["Table 4.21"]
citations: []
status: refined
word_count: 843
---

# 4.7.1 Incidence and Boundary Alignment

This section answers the third research question: whether reducing the
primitive population compromises the identifiability of the medium model, and
whether any mechanism combination protects it. The answer to both parts is
yes, and this subsection establishes the incidence on which the rest of the
section rests.

> **[TABLE 4.21]** *Attenuation-channel collapse across all configurations.*
> A run is counted as collapsed when an attenuation coefficient is driven to or
> below zero and does not recover before training ends. Twelve runs per
> configuration: four scenes, three repeats. Source: `medium_collapse.json`.

| Configuration | Mechanisms | Collapsed / runs |
|---|---|---:|
| SS | reference | 0 / 12 |
| A0 | none | 0 / 12 |
| A0D | gradient detachment | 0 / 12 |
| A1 | initialisation | 0 / 12 |
| **A2** | **simplification** | **5 / 12** |
| A3 | quantisation | 0 / 12 |
| A4 | initialisation + simplification | 0 / 12 |
| A5 | initialisation + quantisation | 0 / 12 |
| **A6** | **simplification + quantisation** | **4 / 12** |
| A7 | all three | 0 / 12 |

**Collapse occurs in exactly two of the ten configurations, and both contain
spatial reorganisation without deterministic initialisation.** No configuration
lacking spatial reorganisation ever loses a channel. Two configurations
containing it never do, and both of those also contain deterministic
initialisation.

Pooling the two groups that contain spatial reorganisation gives the campaign's
principal result on the third axis. Without deterministic initialisation, 9 of
24 runs lose a channel; with it, 0 of 24. By Fisher's exact test, two-sided,
**p = 0.0016**. Tested per pair, the simplification-alone against
initialisation-plus-simplification contrast gives 5 of 12 against 0 of 12,
p = 0.037; the quantisation pairing gives 4 of 12 against 0 of 12, p = 0.093.
The pooled contrast is the one the design supports, since the two pairs differ
by a mechanism that Section 4.5.3 shows is inert on this axis.

**Deterministic initialisation prevents a failure that spatial reorganisation
makes possible.** That is the strongest statement the incidence supports, and
Section 4.7.3 reports that the explanation registered in advance for *why* it
prevents it was refuted by the data that tested it. The rate is established;
the reason is not.

Three further properties of the incidence constrain the analysis that follows.

**The failure is seed-conditioned, not deterministic.** Three of the four
scenes produce both collapsed and intact repeats under identical configuration:
simplification alone gives 1 of 3 on Curaçao, 2 of 3 on Japanese Gardens, 2 of
3 on Panama, and 0 of 6 across both affected configurations on IUI3 Red Sea.
Spatial reorganisation does not cause collapse; it creates the conditions under
which collapse happens to some repeats and not others. Section 4.7.4 reports
that nothing measured before the cut predicts which.

**The failure is boundary-aligned without exception.** All 24 runs combining
spatial reorganisation without deterministic initialisation place their largest
attenuation drop at iteration 15 000, the first pruning event. Not most — all
of them. The alignment is what licenses attributing the failure to the
mechanism rather than to some unrelated instability of the optimisation, and it
is the cleanest signal in this section.

> **[FIGURE 4.20]** `figures/chapter4/figure-4-20-collapse-onset.pdf`
> *Onset of medium collapse.* The iteration at which each collapsed run's first
> channel crosses zero. Six onsets at iteration 15 001, one at 20 001, two at
> 22 500.
> **Status:** built

Onset is more concentrated still. Six of the nine collapses have their first
negative channel at iteration 15 001 — one step after the first pruning event —
one at 20 001 immediately after the second, and two at 22 500. Section 4.7.5
shows what is happening in those iterations, and it is not what the schedule
was designed to do.

**The failure has a consistent spectral direction.** The blue channel is lost
in all nine collapsed runs, and the green channel additionally in two of them.
No run loses red. Blue is the channel with the smallest fitted attenuation
coefficient on every scene where the spectrum is physical (Section 4.2.4), so
it is the channel nearest zero before the cut and the first to cross it. The
invariant is therefore the direction rather than the identity of the channel,
and Section 4.7.4 shows why that distinction matters: what decides the outcome
is the absolute level a channel reaches, and blue starts lowest.

> **[FIGURE C5]** `figures/chapter4/figure-4-c5-medium-convergence.pdf`
> *Medium parameters over training, all configurations.* The collapsed traces
> leave the envelope established by the reference at a pruning boundary and do
> not return.
> **Status:** built

---

## Review log

**Domain Researcher** — The draft reported the two affected configurations and
the protection separately, so the reader had to assemble the central result
themselves. Pooling is the right analysis here because the mechanism separating
the pairs is inert on this axis, and that has to be argued. → *applied*: pooled
contrast with the Fisher result, per-pair results given, and the justification
for pooling stated. Second finding: the draft asserted "the same channel" from
the specification; `medium_collapse.json` shows blue in all nine with green
additionally in two. → *applied*, with the explanation that blue is the channel
nearest zero and the invariant is direction.

**Supervisor** — The draft opened with a table. The section answers a research
question and should say so in its first sentence. → *applied*. Second: the
protection result was stated and then immediately qualified into near-nothing
by the forward reference to Section 4.7.3. → *applied*: the rate is established
and the reason is not, said in that order, so the finding stands before the
limitation. Devil's advocate: with 0 of 24, could the protection be an artefact
of the M1 cells simply being different in some untested way? Yes, and Section
4.7.4 point six says exactly that — the protections are mutually confounded.

**Journal Reviewer** — A p-value appeared without its test. → *applied*:
Fisher's exact, two-sided, with the per-pair values and the 2×2 structure
implied by the counts. Second: "boundary-aligned" was claimed without the
denominator. → *applied*: all 24 runs, stated as all rather than most.
