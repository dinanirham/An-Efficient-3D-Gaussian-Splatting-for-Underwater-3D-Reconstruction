---
section: "3.7.5"
title: "Scope and Repeat Coverage of Each Metric"
chapter: 3
action: Add
evidence: ["FINDINGS §0", "FINDINGS §9", "FINDINGS §10"]
figures: []
tables: ["Table 3.15"]
citations: []
status: refined
word_count: 706
---

# 3.7.5 Scope and Repeat Coverage of Each Metric

Not every measure in this study is available at every repeat, and a reader
needs to know which carry dispersion and which do not before reading any result
that rests on them.

The cause is a storage policy. Full point clouds were retained for the **first
repeat only** of each configuration and scene; the remaining two repeats kept
metrics and per-iteration diagnostics but not the trained representation. The
policy was necessary — 120 full point clouds exceeded the available storage —
and its consequences are asymmetric across the instrument set.

> **[TABLE 3.15]** *Repeat coverage by instrument group.*

| Instrument group | Repeats | Carries dispersion | Section |
|---|:-:|:-:|---|
| Fidelity metrics | 3 | yes | 3.7.1 |
| Primitive count, training time, render rate, stored bytes | 3 | yes | 3.7.2 |
| Medium scalars, collapse incidence, boundary alignment | 3 | yes | 3.7.3 |
| Visible fraction, geometric ratios | 1 | **no** | 3.7.4 |
| Restoration consistency | 1 | **no** | 3.7.4 |
| Rendered comparisons | 1 | **no** | 3.7.4 |

**The three instrument groups on which this thesis's principal claims rest all
carry three repeats.** Every main effect, every interaction, the equivalence
test and the collapse incidence are computed from all three, and are resolved
against dispersion under the rule of Section 3.6.5.

**Three groups rest on a single repeat and are never resolved.** The geometric
diagnostics, the restoration-consistency measurement and every rendered
comparison are reported without dispersion, and no claim in Chapter IV that
depends on them is presented as a resolved effect. Where such a quantity is
quoted, the dependence is stated at the claim rather than left to this table.

This asymmetry is visible in how Chapter IV argues. The finding that the
fidelity metrics cannot detect a collapsed medium rests on twelve
within-configuration comparisons at three repeats, and is load-bearing. The
finding that two attribute states of one model produce restored images 17 to 27
decibels apart rests on one repeat per configuration and scene, and is reported
as corroborating a conclusion established elsewhere rather than as establishing
it. Section 4.8.2 states that ordering explicitly.

## A verification step the single-repeat instruments require

Because the retained artefacts are point clouds rather than evaluated models,
any measurement recomputed from them must be checked against what the run
originally recorded. The collection tool therefore recomputes each run's mean
fidelity from the retained representation and compares it with the metrics that
run wrote during the campaign; a disagreement beyond a stated tolerance is
reported as a failure and blocks use of that run's recomputed values.

The check is not ceremonial. An earlier version of the collector rendered
quantised configurations from their stored continuous parameters — the state
the campaign never evaluated (Section 3.7.4) — and reported a fidelity figure
several decibels below the recorded one. The self-check is what identified it.
Every recomputed quantity used in Chapter IV passed this check on all forty
runs it covers.

---

## Review log

**Domain Researcher** — The draft stated the storage policy without tabulating
which instruments it affects, so a reader could not tell whether a given
Chapter IV number carries dispersion. → *applied*: coverage table by instrument
group, with the dispersion column explicit. Second finding: the policy's cause
was not given, leaving it to look like an oversight rather than a constraint.
→ *applied*.

**Supervisor** — The draft reported the asymmetry neutrally. It shapes how
Chapter IV argues — which findings are load-bearing and which corroborate — and
saying so makes the table consequential rather than administrative.
→ *applied*, with the two findings of Section 4.8 as the worked example. Devil's
advocate: does a single-repeat instrument belong in a thesis that insists on
dispersion everywhere else? It does when it is the only route to a quantity,
provided it is never asked to resolve anything — which is the rule stated here.

**Journal Reviewer** — The self-check was not described anywhere in the
methodology, though every recomputed value in Chapter IV depends on it having
passed. → *applied*: own subsection, with the failure it caught and the
coverage of the check.
