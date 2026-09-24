---
section: "3.6.6"
title: "Training Procedure and Intervention Schedule"
chapter: 3
action: Refine
evidence: ["FINDINGS §0", "CD register", "run_ledger.json"]
figures: ["figure-2-schedule"]
tables: ["Table 3.11"]
citations: []
status: refined
word_count: 706
---

# 3.6.6 Training Procedure and Intervention Schedule

Every run in the campaign trains for 30 000 iterations under the same schedule,
differing only in which mechanisms are enabled and when they act.

> **[TABLE 3.11]** *Training and intervention schedule.* Iteration counts are
> identical across all configurations; the intervention rows apply only where
> the corresponding mechanism is enabled.

| | Iteration | Applies to |
|---|---|---|
| Training length | 30 000 | All configurations |
| Densification | Disabled for the run | Configurations with M1 |
| First reduction event | 15 000 | Configurations with M2 |
| Medium-only interval | 15 000 – 15 200 | Configurations with M2 |
| Second reduction event | 20 000 | Configurations with M2 |
| Medium-only interval | 20 000 – 20 200 | Configurations with M2 |
| Quantisation active | Fixed iteration to end | Configurations with M3 |

**Effective optimizer steps are constant within each group**: 43 000 for every
configuration without spatial reorganisation, and 43 400 for every
configuration with it, the difference being the two intervals of 200
medium-only steps. This is a designed property rather than an observation. The
mechanisms alter what an iteration costs, not how many iterations are
performed, so wall-clock differences between configurations are attributable to
per-iteration cost rather than to schedule length. Section 4.3.2 relies on this
when it reports that training time falls by 11 to 26 per cent against a
population reduction of nine to eighteen times.

**No hyperparameter was selected on held-out data.** Every configuration value
is either inherited from a source method at its published setting, inherited
from the baseline implementation, or fixed in advance by a stated rule. Two
values fall in the last category and both rules are given where the mechanism
is described: the pruning budget of 200 000, fixed by the degeneracy rule of
Section 3.6.1, and the reference-view count of Section 3.5.2, which is the
smaller of the source default and the training-view count.

This is a constraint with a cost, and Section 3.4.4 states it: with thirteen
evaluation frames, a validation-driven search would fit the evaluation set and
the resulting figures would not be comparable with published ones. The
consequence is that every mechanism is measured at one operating point, which
Chapter IV's boundary subsections record as the most significant limitation on
the mechanism results.

**The schedule is evidence, not only configuration.** Section 4.7.1 reports
that all 24 runs applying spatial reorganisation without deterministic
initialisation place their largest attenuation drop at iteration 15 000, and
that six of the nine collapses cross zero at iteration 15 001. Those are marks
on this table. The boundary alignment is what licenses attributing the medium
failure to the mechanism rather than to some unrelated instability, and it is
only interpretable because the schedule is identical across configurations and
fixed in advance.

> **[FIGURE 3.3]** `figures/figure-2-schedule.svg`
> *The intervention schedule.* Iterations at which each mechanism becomes
> active, the two reduction events, and the medium-only intervals that follow
> them.
> **Status:** built

One property of the schedule is a limitation rather than a feature and is
recorded here because it follows from the table. The two reduction events and
their medium-only intervals are inseparable: no configuration in the campaign
reduces the population without the interval that follows. Section 4.7.5 reports
what that prevents the study from establishing.

---

## Review log

**Domain Researcher** — The draft gave the schedule as configuration. Chapter
IV's boundary-alignment result is a statement about marks on this table, and
saying so here makes the schedule part of the evidence rather than background.
→ *applied*, with the specific iterations and what the alignment licenses.
Second finding: the constant optimizer-step count was stated as an observation
when it is a designed property that a later result depends on. → *applied*.

**Supervisor** — The draft listed the no-validation-search rule without its
cost, which is the one-operating-point limitation that every boundary
subsection in Chapter IV then repeats. → *applied*, with the trade named.
Devil's advocate: does inheriting every hyperparameter risk measuring the
source methods at settings unsuited to this corpus? Yes, and Section 3.5.2
records exactly that for one mechanism — the configuration sits off the
published saturation curve because the corpus has too few views.

**Journal Reviewer** — The two fixed-by-rule values were referred to without
being enumerated. → *applied*: both named with their rules located. Second: the
schedule's inseparability of reduction and interval was in Section 3.5.3 but
not visible from the schedule table where a reader would notice it.
→ *applied*: closing paragraph.
