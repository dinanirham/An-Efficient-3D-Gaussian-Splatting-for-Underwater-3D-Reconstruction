---
section: "4.3.2"
title: "Efficiency Outcome"
chapter: 4
action: Rewrite
evidence: ["FINDINGS §2", "FINDINGS §9", "FINDINGS §12"]
figures: ["figure-4-17-population-trajectory", "figure-4-18-fps-vs-count"]
tables: ["Table 4.9"]
citations: []
status: refined
word_count: 786
---

# 4.3.2 Efficiency Outcome

Deterministic initialisation targets two costs: the size of the representation
and the time taken to train it. It reduces both, on every scene, resolved in
every case. This subsection reports the magnitudes and then qualifies the
headline figure in the way Section 4.2.6 requires.

> **[TABLE 4.9]** *Efficiency of deterministic initialisation against the
> reference, per scene.* Population reduction is given against the total
> population and against the population above the visibility threshold. Render
> rate is reported as a ratio. Source: `results_by_scene.csv`, FINDINGS §9.

| Scene | Primitives | Reduction, total | Reduction, visible | Render rate | Training saved |
|---|---:|---:|---:|---:|---:|
| Curaçao | 243 298 | 17.6× | 5.0× | 2.25× | 1 196 s |
| IUI3 Red Sea | 220 895 | 13.9× | 5.3× | 1.25× | 385 s |
| Japanese Gardens | 230 156 | 8.9× | 3.7× | 1.57× | 728 s |
| Panama | 196 567 | 10.7× | 4.3× | 1.34× | 939 s |

The representation shrinks by between 8.9 and 17.6 times against the published
reference, resolved on every scene at 15 to 51 standard errors. The mechanism
also converges on a strikingly consistent absolute size: between 197 000 and
243 000 primitives across four scenes whose reference populations differ by a
factor of two. This is a property of the mechanism rather than of the scenes —
the population is fixed by the correspondence stage before optimisation begins
and cannot subsequently grow — and it is the reason Section 4.6.2 finds the
interaction with simplification to be structural rather than physical.

**The reduction against the visible population is between 3.7 and 5.3 times,
not between 8.9 and 17.6.** Section 4.2.6 established that only 23 to 43 per
cent of the reference's primitives clear the visibility threshold, against 78
to 94 per cent of this mechanism's. A large part of the headline ratio is
therefore the removal of primitives that were never rendered. Both columns
belong in the table: the total is what determines file size and memory
footprint, and the visible figure is what determines how much representational
capacity was given up. Reporting only the first would overstate the
mechanism's effect on the reconstruction by a factor of roughly three.

Training time falls on every scene, by 385 to 1 196 seconds, or 11 to 26 per
cent. The saving is largest on Curaçao, which is the scene with the largest
reference population, and smallest on IUI3 Red Sea, which has the smallest
saving in both absolute and relative terms. This ordering is the expected one:
disabling cloning and splitting saves the optimiser the work of carrying a
population that grows throughout training, so the saving scales with how much
growth was being carried. It is worth noting that the saving is proportionally
smaller than the population reduction — 26 per cent against 17.6 times on
Curaçao — because training cost is dominated by the number of optimizer steps,
which Section 4.1.1 established is identical across configurations, rather than
by the final population.

> **[FIGURE 4.17]** `figures/chapter4/figure-4-17-population-trajectory.pdf`
> *Primitive population through training.* Anchors at the schedule's inflection
> points, per scene, per configuration. Deterministic initialisation is flat by
> construction; the reference and the unmodified configuration grow throughout.
> **Status:** built

Render rate improves by between 1.25 and 2.25 times. The gain is markedly
sub-linear in the population reduction — a 17.6-fold reduction on Curaçao buys
a 2.25-fold rate improvement, and a 13.9-fold reduction on IUI3 Red Sea buys
only 1.25-fold. Rendering cost is therefore not proportional to primitive
count, and the exponent relating the two differs by scene. Section 4.4.2
returns to this with the same finding for spatial reorganisation, and
Figure 4.18 fits the relationship across all configurations.

> **[FIGURE 4.18]** `figures/chapter4/figure-4-18-fps-vs-count.pdf`
> *Frame rate against population, logarithmic axes.* Fitted slopes between
> −0.11 and −0.28 against −1 for inverse proportionality, confirming that
> rendering cost is dominated by terms other than primitive count at these
> populations.
> **Status:** built

Render rate is not this mechanism's target cost and is reported here for
completeness rather than as a claim. The mechanism does not act on the
rendering path, and its rate improvement follows from the smaller population
alone; Section 4.5.2 reports the mechanism that does act on storage and finds,
consistently with Figure 4.18, that it changes no frame rate at all.

---

## Review log

**Domain Researcher** — The draft led with the 8.9–17.6× headline and mentioned
the visible-population qualification in a closing sentence, which inverts their
importance for anyone reading the number as a claim about the reconstruction.
→ *applied*: both columns in the table, the qualification bolded in the body,
and an explicit statement of what each column determines. Second finding: the
consistency of the absolute final size across scenes went unremarked, and it is
the fact that makes Section 4.6.2's interaction structural. → *applied*.

**Supervisor** — The draft reported the training saving without explaining why
it is proportionally so much smaller than the population reduction, which reads
as an inconsistency to anyone who has just seen 17.6×. → *applied*: the
optimizer-step accounting from §4.1.1, which makes the two figures compatible.
Devil's advocate: is the render-rate gain being quietly claimed as a benefit of
this mechanism? It was. → *applied*: closing paragraph states it is not the
target cost, follows from population alone, and is reported for completeness.

**Journal Reviewer** — Reductions given without their resolution status.
→ *applied*: 15 to 51 standard errors, stated in the body. Second: the two
reduction columns were unlabelled as to which population each used, leaving the
table ambiguous in isolation. → *applied*, in the caption. Third: Figure 4.18
was cited for a claim made in Section 4.4.2 but not introduced here where it is
first relevant. → *applied*, with the fitted slopes quoted.
