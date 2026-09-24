---
section: "4.6.5"
title: "Three-Way Interaction"
chapter: 4
action: Add
evidence: ["FINDINGS §4", "analysis_unweighted.json"]
figures: []
tables: ["Table 4.19"]
citations: []
status: refined
word_count: 512
---

# 4.6.5 Three-Way Interaction

The three-way term asks whether the combination of all three mechanisms departs
from what the three main effects and the three two-way terms together predict.
No directional prediction was registered for it.

> **[TABLE 4.19]** *Three-way interaction.* Contrast
> A7 − A6 − A5 − A4 + A3 + A2 + A1 − A0, with the standard error taken from
> all eight cell means. Source: `analysis_unweighted.json`.

| Scene | ΔLPIPS | z | Count (log ratio) | z |
|---|---:|---:|---:|---:|
| Curaçao | −0.016 | −2.0 | ×0.84 | `UNRES` |
| IUI3 Red Sea | +0.003 | +0.7 | ×0.88 | `UNRES` |
| Japanese Gardens | −0.003 | −0.6 | ×0.89 | `UNRES` |
| Panama | **−0.023** | **−2.7** | ×1.25 | `UNRES` |

**The term is `UNRESOLVED` on primitive count on every scene and on perceptual
similarity on three of four.** Panama resolves negative at 2.7 standard errors
and Curaçao sits exactly on the two-standard-error line. Following the analysis
plan, no interpretation is offered for a term that resolves on one scene of
four.

The more useful statement is the one Section 4.6.1 anticipated: this is what
the design's resolution looks like at three repeats. The standard error of an
eight-mean contrast is approximately 2√2 times that of a single cell mean, so
the three-way term is the least resolvable quantity the campaign estimates. Its
appearance as unresolved is the expected consequence of that arithmetic and
carries no information about whether three-way composition is additive. An
unresolved three-way term and a zero three-way term are not distinguishable
here, and reporting the former as evidence for the latter would be precisely
the error Section 4.1.2 forbids.

What the design does establish about the full combination is reported
elsewhere and does not depend on this term. The combined configuration's
position against the reference is in Section 4.6.6 and in Figure 4.15b: 14 to
25 times fewer primitives, peak signal-to-noise ratio indistinguishable on
three scenes and resolved better on one, and a resolved perceptual cost of 0.04
to 0.11 everywhere. That it never loses an attenuation channel is in Section
4.7.1. None of those results requires the three-way interaction term, and none
is weakened by its being unresolved.

---

## Review log

**Domain Researcher** — The draft opened by reporting the terms, which invites
a reader to interpret the one resolved value before learning that the design
cannot resolve this contrast. → *applied*: the resolution argument is now the
second paragraph, before any reading of Panama. Second finding: the draft did
not state what *is* known about the full combination, leaving the subsection
looking like a dead end. → *applied*: closing paragraph, with the results
located and the note that none depends on this term.

**Supervisor** — The draft wrote "no significant interaction was found", which
is exactly the formulation Section 4.1.2 rules out. → *applied*: `UNRESOLVED`
throughout, with the explicit statement that unresolved and zero are not
distinguishable. Devil's advocate: with one scene resolving at 2.7 standard
errors, is declining to interpret too conservative? The plan's rule was set in
advance and applies to a term resolving on one scene of four regardless of
which direction it takes; applying it selectively would be worse than applying
it strictly.

**Journal Reviewer** — The contrast was described but not written out, and the
source of its standard error was unstated. → *applied*, in the table caption.
Second: Curaçao's z of exactly −2.0 needed to be described as on the line
rather than resolved or unresolved. → *applied*.
