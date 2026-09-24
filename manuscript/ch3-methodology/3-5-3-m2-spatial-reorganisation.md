---
section: "3.5.3"
title: "M2 — Spatial Reorganisation"
chapter: 3
action: Refine
evidence: ["CD register", "FINDINGS §5"]
figures: ["figure-2-schedule"]
tables: []
citations: ["Fang & Wang, 2024"]
status: refined
word_count: 833
---

# 3.5.3 M2 — Spatial Reorganisation

**Source.** Mini-Splatting (Fang & Wang, 2024).

**Mechanism as executed.** A per-primitive importance score is accumulated over
every training view from the rasteriser's internal blending weights and
projected areas, and the population is then reduced to a fixed budget by
importance-weighted stochastic sampling. Scoring and reduction run at two
scheduled iterations, 15 000 and 20 000, and each event is followed by 200
optimisation steps in which only the medium parameters are updated and the
geometry is held fixed.

## Two details of the source method that are load-bearing

**Importance is blending weight normalised by projected area, counted only in
views where the primitive is the largest contributor.** This requires
per-primitive accumulators that the baseline's rasteriser does not emit, and
obtaining them is the reason for the rasteriser substitution registered in
Section 3.5.6. Approximating the score from quantities the original rasteriser
does provide would not be this mechanism.

**Selection is stochastic, not deterministic top-k.** The source establishes
that deterministic top-k pruning destroys local geometry, because importance is
spatially autocorrelated and the highest-scoring primitives cluster; it
validates the stochastic alternative on a geometric criterion rather than on a
fidelity metric. **A deterministic implementation would not be this mechanism**,
and would reproduce the failure the source method exists to avoid. The
consequence for this study is that the realised post-reduction count is
stochastic, so it is reported per run rather than as the target.

## Scoping

The source method also contains a densification half — depth reinitialisation
and blur-based splitting. **That half is not used.** It would collide with
deterministic initialisation in the combined configurations, where density
control is disabled, and this study's factor is population *reduction*
specifically. The scoping is a deviation from the source method as published,
and it means this study's results for this mechanism are not comparable with
that method's published figures.

## The budget, and why it is what it is

A single budget of 200 000 primitives was used, fixed **before** the campaign
by a stated rule: the budget must lie below the smallest primitive count any
other enabled mechanism produces. If it did not, this mechanism would be
provably inert wherever deterministic initialisation is active, and two cells
of the factorial would become exact duplicates of two others — the design would
report a degenerate interaction as a finding. Against the measured dense clouds
of Section 3.5.2, which hold 244 197 to 293 642 points, 200 000 satisfies the
rule on every scene.

**The budget is an absolute count, not a proportion of the entering
population.** This is the source method's formulation and it is reproduced
unchanged, but it has a consequence this study's design makes visible: a
configuration arriving at the first event with roughly 224 000 primitives loses
about a third, while one arriving with millions loses about nine tenths. The
same mechanism therefore performs a qualitatively different operation depending
on what precedes it. Section 4.6.2 reports the resulting interaction as
structural for exactly this reason, and Section 4.7 reports that the two cut
sizes differ in whether the medium model survives them.

## The medium-only interval

Each reduction event is followed by 200 steps in which the geometry is frozen
and only the medium parameters are optimised. The interval was added as a
remedy: after a large change to the population, the medium model is given an
opportunity to re-identify itself against the new geometry before ordinary
training resumes.

It is recorded here as an intervention rather than as a detail because Section
4.7.5 reports that it does not behave as intended. A methodological consequence
follows and is stated in advance: **every configuration containing this
mechanism also contains the interval**, and the campaign has no configuration
that reduces the population without it. Whether the interval causes or merely
hosts the effects attributed to reduction is therefore untestable in this
design. Recognising that before the results are read is preferable to
discovering it afterwards.

---

## Review log

**Domain Researcher** — The draft described stochastic selection as an
implementation choice. The source validates it against deterministic top-k on a
geometric criterion, and a deterministic version reproduces the failure the
method exists to avoid — so it is definitional, not stylistic. → *applied*,
with the consequence that realised counts are reported per run. Second finding:
the absolute-versus-proportional budget was stated in Section 3.1.2 but not
here, where the mechanism is specified. → *applied*, with both downstream
sections named.

**Supervisor** — The draft introduced the medium-only interval as configuration
and left its consequences entirely to Chapter IV. The confound it creates —
that no configuration prunes without it — is a property of the design and
belongs in the methodology, stated before the results rather than discovered
after. → *applied*: own subsection, ending on that point. Devil's advocate:
does flagging a known confound here weaken §4.7? It strengthens it — a
limitation the design anticipated reads differently from one the analysis
stumbled on.

**Journal Reviewer** — The scoping deviation was stated without its
consequence for comparability. → *applied*: results for this mechanism are not
comparable with the source's published figures. Second: the budget rule was
described as "stated" without being stated. → *applied*, in full, with the
degeneracy it prevents.
