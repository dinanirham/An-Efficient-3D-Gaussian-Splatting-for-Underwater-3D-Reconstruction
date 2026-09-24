---
section: "3.6.1"
title: "Factorial Structure and Cell Definition"
chapter: 3
action: Add
evidence: ["PLAN", "run_ledger.json"]
figures: []
tables: ["Table 3.8"]
citations: []
status: refined
word_count: 741
---

# 3.6.1 Factorial Structure and Cell Definition

The design is a full 2³ factorial over the three mechanisms of Section 3.5,
blocked by scene and repeated three times.

> **[TABLE 3.8]** *The eight factorial cells.* M1 is deterministic
> initialisation, M2 spatial reorganisation, M3 attribute-level quantisation.

| Cell | M1 | M2 | M3 | Isolates |
|---|:-:|:-:|:-:|---|
| **A0** | — | — | — | No mechanism active; the corner every contrast is built from |
| **A1** | ✓ | — | — | Initialisation alone |
| **A2** | — | ✓ | — | Simplification alone |
| **A3** | — | — | ✓ | Quantisation alone |
| **A4** | ✓ | ✓ | — | Initialisation × simplification |
| **A5** | ✓ | — | ✓ | Initialisation × quantisation |
| **A6** | — | ✓ | ✓ | Simplification × quantisation |
| **A7** | ✓ | ✓ | ✓ | The three-way term, and effects estimated from above |

Eight cells across four scenes at three repeats gives ninety-six runs. A ninth
configuration, the supplementary contrast of Section 3.5.5, adds twelve, and
the reference control of Section 3.6.2 adds twelve more: **120 runs in total**.

**Why a factorial rather than a cumulative ablation.** The source literature
almost universally reports cumulative ablations — baseline, baseline plus A,
baseline plus A plus B. That design cannot separate the effect of B from the
effect of B *given* A, because the two are never observed apart. Since the
central question here is whether three mechanisms interfere with one another
and with the medium model, a ladder is structurally unable to answer it. A full
factorial observes every mechanism in the presence and the absence of every
other, which is what makes an interaction estimable at all.

**Every main effect is estimated in both directions.** A mechanism's effect can
be read as the difference from the corner where nothing is active, or as the
difference from the complete system with that mechanism removed — from below
and from above. Where the two agree within pooled dispersion, the mechanism
behaves independently of the others and either figure may be quoted. Where they
disagree, **neither may be quoted alone**: the disagreement *is* the
interaction, and Section 3.8.1 gives the contrasts for both directions.

This is a stronger discipline than reporting a single direction and testing
interactions separately, and it was adopted because a mechanism's headline
number is the thing most likely to be quoted out of context. A figure that
holds only when the other two mechanisms are disabled should not be reported as
though it were the mechanism's effect.

**Two combinations were checked in advance for degeneracy.** A factorial cell
is worthless if its two mechanisms cannot both act — the cell would duplicate
another and the interaction term would measure nothing. The pruning budget of
Section 3.5.3 was therefore fixed before the campaign by a rule that guarantees
it binds even when deterministic initialisation has already reduced the
entering population. Had it not, cells A4 and A7 would have been exact
duplicates of A1 and A5.

The supplementary contrast is deliberately outside the factorial, for the
structural reason set out in Section 3.5.5: it is provably inert wherever
deterministic initialisation is active, so half the cells of a 2⁴ design would
be null and every contrast involving it would be uninterpretable. It is never
differenced with any factorial cell, and Section 3.8.1 enforces that in the
contrast definitions.

---

## Review log

**Domain Researcher** — The draft asserted the factorial's superiority over a
ladder without stating what specifically cannot be estimated from a ladder.
→ *applied*: the effect of B given A is never observed apart from the effect of
B, which is the precise defect. Second finding: the degeneracy check on the
budget was described in Section 3.5.3 as a setting but its design purpose — that
two cells would otherwise duplicate two others — belongs here where cells are
defined. → *applied*, with the specific cells named.

**Supervisor** — The both-directions rule was stated as a procedure. Its
justification is about how results get misquoted, and saying that makes it a
discipline rather than a convention. → *applied*. Devil's advocate: is
forbidding a single-direction figure too strict when the two agree? The rule
only bites when they disagree; where they agree either may be quoted, and the
text says so.

**Journal Reviewer** — The run arithmetic was given as "ninety-six runs" with
the other twenty-four appearing in different sections, so the campaign total
never appeared beside its components. → *applied*: 96 + 12 + 12 = 120, in one
place. Second: the table's "Isolates" column described A0 as "the baseline",
which the chapter elsewhere reserves for a different sense. → *applied*: "no
mechanism active; the corner every contrast is built from".
