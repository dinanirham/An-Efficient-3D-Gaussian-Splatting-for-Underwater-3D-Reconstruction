---
section: "3.1.2"
title: "Insertion Points of the Efficiency Mechanisms"
chapter: 3
action: Add
evidence: ["CD register", "implementation"]
figures: ["figure-1-pipeline", "figure-2-schedule"]
tables: ["Table 3.1"]
citations: ["Kotovenko et al., 2026", "Fang & Wang, 2024", "Navaneet et al., 2024"]
status: refined
word_count: 748
---

# 3.1.2 Insertion Points of the Efficiency Mechanisms

The three mechanisms under test act at disjoint stages of the pipeline and
share no code. That is what makes a factorial design appropriate: each can be
enabled or disabled independently, and any departure from additive composition
is a property of the pipeline rather than of an implementation in which the
mechanisms are entangled.

> **[TABLE 3.1]** *Where each mechanism acts.* The intervention, the stage, and
> the cost it targets.

| | Mechanism | Acts at | Intervention | Target cost |
|---|---|---|---|---|
| **M1** | Deterministic initialisation | Before optimisation | Replaces the sparse structure-from-motion cloud with a dense correspondence-derived cloud, and disables cloning and splitting for the whole run | Primitive count, training time |
| **M2** | Spatial reorganisation | Twice during optimisation | Prunes the population to an absolute budget by an importance criterion and redistributes survivors, each event followed by a medium-only interval | Primitive count, render rate |
| **M3** | Attribute-level quantisation | From a fixed iteration to the end | Replaces three per-primitive attribute vectors with indices into learned codebooks, trained through a straight-through estimator | Stored bytes |

**M1 acts before the first gradient step and persists by absence.** It supplies
the initial cloud and then removes the procedure that would have grown it
(Kotovenko et al., 2026). The population is fixed for the run; the optimiser
can move, scale and recolour primitives but cannot create or destroy them.

**M2 acts at two scheduled iterations.** It is the only mechanism that
intervenes during optimisation, and the only one whose intervention is
discontinuous (Fang & Wang, 2024). Each pruning event is followed by a short
interval in which only the medium parameters are optimised, the geometry held
fixed — an interval added as a remedy, whose behaviour Section 4.7.5 reports.

**M3 acts on storage and is transparent to rendering.** The codebooks are
decoded before rasterisation, so the renderer receives the same number of
primitives with the same attributes it would otherwise have had (Navaneet et
al., 2024). It changes what a primitive costs to store, not what it costs to
draw.

> **[FIGURE 3.2]** `figures/figure-1-pipeline.svg`
> *The pipeline and the three insertion points.* Preprocessing, initialisation,
> the optimisation loop with its two scheduled interventions, and the storage
> stage.
> **Status:** built

> **[FIGURE 3.3]** `figures/figure-2-schedule.svg`
> *The intervention schedule.* Iterations at which each mechanism becomes
> active, the two pruning events, and the medium-only intervals that follow
> them.
> **Status:** built

The disjointness is a claim about the implementation and is worth stating
precisely, because the factorial design depends on it. No mechanism reads a
parameter another writes; no mechanism's code path is entered by another's; and
enabling any subset produces the same behaviour for each member as enabling it
alone, up to the state the others leave behind. What the mechanisms *do* share
is the primitive population, which is the medium through which they interact:
M1 determines how many primitives exist when M2 prunes, and M2 determines how
many remain for M3 to compress. Section 4.6 measures the consequences.

One mechanism in the campaign does not appear in this table. Gradient
detachment removes the alpha-loss gradient from density control, and it is
**provably inert wherever M1 is active**, because M1 disables density control
entirely. It is therefore not a fourth factor — half the cells of a 2⁴ design
would be null — and is measured as a supplementary contrast against the
configuration with no mechanism active. Section 3.5.5 describes it and Section
4.9.1 states the exclusion argument in full.

A property of M2's budget should be recorded at this point because it
determines a result rather than merely describing a setting. The budget is an
**absolute** primitive count, not a proportion of the entering population. A
configuration arriving at the first event with 224 000 primitives therefore
loses about a third, and one arriving with 2.4 million loses about nine tenths.
Section 4.6.2 finds the interaction between M1 and M2 on count to be strongly
sub-additive, and this is why: the two mechanisms drive the population toward a
similar absolute figure by different routes, so their reductions cannot
multiply.

---

## Review log

**Domain Researcher** — The draft listed the mechanisms without stating that
they share no code, which is the assumption the factorial rests on and which a
referee would want asserted explicitly rather than implied. → *applied*, with
the precise form of the claim — no shared parameters, no shared code paths —
and the explicit statement of what they *do* share. Second finding: M2's
absolute budget was described as a setting. It determines the largest
interaction in the study. → *applied*: closing paragraph with the forward
reference.

**Supervisor** — The draft deferred the fourth-mechanism question to Chapter
IV, so a reader of the methodology would not know why a 2⁴ design was not run.
→ *applied*: stated here with the inertness argument in one sentence. Devil's
advocate: is "provably inert" too strong for a claim about an implementation?
It is provable from the code path — M1 disables density control, and the
mechanism modifies a gradient that only density control consumes — and Section
3.5.5 gives that argument.

**Journal Reviewer** — Three source methods were described without citation in
the section that introduces them. → *applied*, all three from the register.
Second: two built figures existed for this material and neither was referenced.
→ *applied*: pipeline and schedule, with captions.
