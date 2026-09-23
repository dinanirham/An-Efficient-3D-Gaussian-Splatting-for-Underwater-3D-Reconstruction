---
section: "4.4.2"
title: "Efficiency Outcome"
chapter: 4
action: Rewrite
evidence: ["FINDINGS §2", "FINDINGS §9", "FINDINGS §12"]
figures: ["figure-4-18-fps-vs-count", "figure-4-17-population-trajectory"]
tables: ["Table 4.11"]
citations: []
status: refined
word_count: 771
---

# 4.4.2 Efficiency Outcome

Spatial reorganisation targets the size of the representation and, through it,
the rate at which it renders. It is the campaign's largest reduction on both
counts.

> **[TABLE 4.11]** *Efficiency of spatial reorganisation against the reference,
> per scene.* Population reduction is given against the total population and
> against the population above the visibility threshold. Source:
> `results_by_scene.csv`, FINDINGS §9.

| Scene | Primitives | Reduction, total | Reduction, visible | Render rate |
|---|---:|---:|---:|---:|
| Curaçao | 149 906 | 28.5× | 7.3× | 3.54× |
| IUI3 Red Sea | 132 955 | 23.1× | 9.5× | 1.84× |
| Japanese Gardens | 142 719 | 14.3× | 5.6× | 2.43× |
| Panama | 139 203 | 15.1× | 5.1× | 1.89× |

The representation shrinks by between 14.3 and 28.5 times against the published
reference, resolved at 16 to 61 standard errors, and render rate improves by
between 1.84 and 3.54 times, resolved on every scene. Both are larger than the
corresponding figures for deterministic initialisation, which is expected: this
mechanism prunes to a fixed budget and therefore acts on whatever population
exists at the event, where the other mechanism simply never grows one.

Against the visible population the reduction is between 5.1 and 9.5 times. The
gap between the two columns is smaller than it was for deterministic
initialisation, because this mechanism's output is 88 to 96 per cent visible
and it acts on a baseline population that was not. As Section 4.2.6 records,
the 28.5-fold reduction on Curaçao is approximately a sevenfold reduction of
the population that renders. The larger figure is the one that determines
storage and the smaller the one that determines representational capacity
surrendered, and both are reported for that reason.

**The rate improvement is strongly sub-linear in the population reduction, and
the exponent is scene-dependent.** A 28.5-fold reduction on Curaçao yields
3.54 times the frame rate; a 23.1-fold reduction on IUI3 Red Sea yields only
1.84 times. If rendering cost were proportional to primitive count these
factors would be 28.5 and 23.1. They are not close, and the discrepancy is not
a constant.

> **[FIGURE 4.18]** `figures/chapter4/figure-4-18-fps-vs-count.pdf`
> *Frame rate against population, logarithmic axes.* One point per
> configuration and scene. Fitted slopes lie between −0.11 and −0.28, against
> −1 for inverse proportionality.
> **Status:** built

Figure 4.18 fits the relationship across all configurations and scenes. The
fitted slopes are between −0.11 and −0.28 where inverse proportionality would
give −1, so at these populations a tenfold reduction in primitive count buys
roughly a 1.3- to 1.9-fold rate improvement. Rendering cost is evidently
dominated by terms that do not scale with the count — rasterisation of the
primitives that remain, the per-pixel compositing work, and fixed per-frame
overheads — and the scene-dependence of the exponent is consistent with scenes
differing in how much of the frame is covered by how many overlapping
primitives. This is a description of the observed relationship, not a model of
it; the campaign varied no rendering parameter and cannot decompose the cost.

The practical consequence is worth stating plainly, because the headline
reduction invites the wrong inference. A practitioner adopting this mechanism
for interactive rendering should expect a rate improvement between roughly two
and three and a half times, not between fourteen and twenty-nine. The large
figure is the storage benefit; the modest one is the speed benefit. Both are
real and they are not the same number.

> **[FIGURE 4.17]** `figures/chapter4/figure-4-17-population-trajectory.pdf`
> *Primitive population through training.* The two pruning events are visible
> as discontinuities; the budget binds at the first event on every scene.
> **Status:** built

One accounting property is recorded here and used in Section 4.6.2. The budget
is absolute rather than proportional, so every configuration containing this
mechanism converges to approximately the same final population regardless of
what it had before — 133 000 to 150 000 primitives here, against reference
populations differing by a factor of two. Section 4.6.2 finds the interaction
between this mechanism and deterministic initialisation to be strongly
sub-additive on count, and this is why: two mechanisms that both drive the
population toward a similar absolute figure cannot compose multiplicatively.
The interaction is structural, a consequence of the budget, and not a physical
property of the scenes.

---

## Review log

**Domain Researcher** — The draft stated the sub-linear rate relationship as a
curiosity. It is the central efficiency caveat of the mechanism and it needs a
mechanistic gloss a reader in this area would expect. → *applied*: bolded, with
the terms that plausibly dominate named and an explicit statement that the
campaign cannot decompose the cost. Second finding: the absolute-budget
property was absent, and it is what makes Section 4.6.2's interaction
structural. → *applied*: closing paragraph, with the forward reference.

**Supervisor** — A reader who takes "28.5× smaller" into a rendering decision
will be disappointed, and the draft left them to discover that in Figure 4.18.
→ *applied*: the practical consequence stated in its own paragraph, in the
numbers a practitioner would use. Devil's advocate: does emphasising the modest
speed gain undersell a genuinely large storage result? No — both are stated as
real, and the sentence says they are different numbers rather than ranking them.

**Journal Reviewer** — Reductions given without resolution status.
→ *applied*: 16 to 61 standard errors. Second: fitted slopes were quoted
without saying what they are fitted over. → *applied*: all configurations and
scenes, in the caption. Third: the visible-population column repeated Section
4.2.6's example without attributing it. → *applied*.
