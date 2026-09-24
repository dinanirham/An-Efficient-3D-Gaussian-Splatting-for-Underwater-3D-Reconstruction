---
section: "3.1.3"
title: "Framework Diagram"
chapter: 3
action: Refine
evidence: ["implementation"]
figures: ["figure-0-optimisation-loop", "figure-1-pipeline", "figure-2-schedule"]
tables: []
citations: []
status: refined
word_count: 512
---

# 3.1.3 Framework Diagram

The conceptual framework of this study is a single claim about structure, and
the three figures of this section state it: **the efficiency mechanisms act on
the geometry, the medium model is fitted downstream of the geometry through the
rendered depth, and the loss sees only their composition.** Every result in
Chapter IV follows from some consequence of that arrangement.

The three figures are complementary rather than alternative views, and they are
placed here together so a reader meets the whole structure before Section 3.5
describes any mechanism in detail.

**Figure 3.1 shows the coupling.** It is the smallest of the three and carries
the argument: the rasteriser emits a medium-free radiance and a depth map, the
medium model consumes both, and the photometric loss is taken on the result.
The medium parameters and the primitives descend the same gradient. Nothing in
the diagram supervises the medium-free radiance directly, and that absence is
the structural fact underlying Sections 4.8.2 and 4.8.3.

**Figure 3.2 shows where the mechanisms enter.** It places the three
interventions on the pipeline — one before optimisation, one within it, one at
the storage stage — and makes their disjointness visible. A reader should be
able to see from it that enabling any subset is well defined, which is the
precondition for the factorial design of Section 3.6.1.

**Figure 3.3 shows when.** The pipeline diagram is not time-ordered within the
optimisation loop, and two of the three mechanisms have schedules that matter:
the two pruning events with their medium-only intervals, and the iteration from
which quantisation becomes active. The collapse result of Section 4.7 is
boundary-aligned to one of the marks on this figure, so the schedule is
evidence and not only configuration.

> **[FIGURE 3.1]** `figures/figure-0-optimisation-loop.svg`
> *The optimisation loop and the medium coupling.*
> **Status:** built
>
> **[FIGURE 3.2]** `figures/figure-1-pipeline.svg`
> *The pipeline and the three insertion points.*
> **Status:** built
>
> **[FIGURE 3.3]** `figures/figure-2-schedule.svg`
> *The intervention schedule.*
> **Status:** built

What the framework does not include is as important as what it does. There is
no arrow from the medium model back to the primitive population: the mechanisms
are not medium-aware, none of them reads a medium parameter, and none was
designed with a medium model in mind. The coupling this study measures is
therefore entirely indirect, running from geometry to depth to medium fit. That
is why the study is framed as a transfer question — whether mechanisms
developed under an assumption that does not hold here behave as documented —
rather than as an integration or co-design question.

---

## Review log

**Domain Researcher** — The draft presented three figures with a caption each
and no argument connecting them. The framework is a claim, and the figures are
its parts. → *applied*: the claim stated first, each figure given the part of
it that it carries. Second finding: the absence of any medium-to-geometry arrow
was not remarked, and it is what makes this a transfer study rather than a
co-design study. → *applied*: closing paragraph.

**Supervisor** — The draft's figures were introduced in an order that did not
match their dependence. Coupling first, then placement, then timing.
→ *applied*. Second: Figure 3.3 was described as configuration; the collapse
result is aligned to a mark on it, so it is evidence. → *applied*.

**Journal Reviewer** — Figures were referenced but not numbered consistently
with Section 3.1.2, which introduces two of the same three.
→ *applied*: one numbering across both subsections, with 3.1.2 introducing
3.2 and 3.3 where they are first used and this subsection collecting all three.
