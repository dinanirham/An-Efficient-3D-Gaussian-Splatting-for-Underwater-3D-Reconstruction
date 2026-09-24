---
section: "4.7.2"
title: "Final Size Is Not the Cause"
chapter: 4
action: Add
evidence: ["FINDINGS §5d", "results_by_scene.csv"]
figures: []
tables: ["Table 4.22"]
citations: []
status: refined
word_count: 574
---

# 4.7.2 Final Size Is Not the Cause

The obvious explanation for the incidence of Section 4.7.1 is that a small
representation cannot support a medium model — that the collapse is a
consequence of how few primitives remain. This subsection rules that
explanation out, and does so with a comparison the design provides directly.

> **[TABLE 4.22]** *Final primitive count against collapse, for the two
> configurations that differ by deterministic initialisation.* Mean over three
> repeats with standard deviation. Both configurations run the same two pruning
> events at the same iterations to the same budget. Source:
> `results_by_scene.csv`, `medium_collapse.json`.

| Scene | A2 count | A4 count | A2 collapsed | A4 collapsed |
|---|---:|---:|:-:|:-:|
| Curaçao | 149 906 ± 2 858 | **129 677** ± 4 220 | 1 / 3 | 0 / 3 |
| IUI3 Red Sea | 132 955 ± 2 234 | **114 103** ± 1 066 | 0 / 3 | 0 / 3 |
| Japanese Gardens | 142 719 ± 2 086 | **127 632** ± 1 342 | 2 / 3 | 0 / 3 |
| Panama | 139 203 ± 9 728 | **115 174** ± 638 | 2 / 3 | 0 / 3 |

**The configuration that never collapses finishes smaller than the one that
does, on every scene, by 13 to 17 per cent.** Both run the same two pruning
events at the same iterations against the same absolute budget. If the size of
the surviving representation were what breaks the medium model, the smaller
configuration would fail at least as often; it never fails at all.

This deconfounds two quantities that the campaign's design would otherwise
leave entangled, and it is the reason the rest of this section looks at the cut
rather than at its result. What distinguishes the two configurations is not
where they finish but how they get there: one arrives at the first pruning
event with roughly 200 000 primitives and loses about a third, the other
arrives with millions and loses about nine tenths. Section 4.7.4 measures both
quantities and reports what covaries with the outcome.

The result also constrains what a practitioner may infer. A representation of
115 000 primitives is not inherently too small to carry a medium model — the
configuration that reaches that size by never growing larger carries one
without difficulty on all twelve runs. Any account of the failure has to be an
account of the transition, not of the destination.

One limitation bounds the comparison. The two configurations differ by
deterministic initialisation, which sets the entering count, the entering
attenuation level, and the fraction removed simultaneously (Section 4.7.4,
point six). This subsection establishes that final size is not the operative
variable; it does not establish which of the remaining three is, and the design
cannot separate them.

---

## Review log

**Domain Researcher** — The draft presented this as a supporting observation.
It is a deconfounding result and it eliminates the first hypothesis any reader
in this area will form, so it should be framed as such. → *applied*: the
subsection now opens with the explanation it rules out. Second finding: the
draft did not state that both configurations run identical pruning schedules,
without which the comparison proves nothing. → *applied*, in the table caption
and the body.

**Supervisor** — The draft stopped at the finding. The interesting consequence
is that any account must be about the transition rather than the destination,
and that is what directs the reader into Section 4.7.4. → *applied*, with the
practitioner-facing version alongside. Devil's advocate: could the smaller
configuration be protected by something other than its gentler cut? Yes — the
closing limitation says the three candidate variables move together and this
design cannot separate them.

**Journal Reviewer** — Counts were given without dispersion, in a subsection
whose whole argument is a comparison of counts. → *applied*: standard
deviations in the table. Second: "13 to 17 per cent" was asserted without the
scene-level figures being checkable against it. → *applied*: the table carries
both columns so the range can be verified.
