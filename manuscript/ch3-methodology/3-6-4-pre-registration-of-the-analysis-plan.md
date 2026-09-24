---
section: "3.6.4"
title: "Pre-Registration of the Analysis Plan"
chapter: 3
action: Add
evidence: ["PLAN", "FINDINGS §3", "FINDINGS §5b"]
figures: []
tables: ["Table 3.9"]
citations: []
status: refined
word_count: 894
---

# 3.6.4 Pre-Registration of the Analysis Plan

The analysis plan — the hypotheses, the equivalence margin, the resolution
rule, the contrast equations, and the conditions under which specific claims
would be considered falsified — was written and committed **before the
campaign's results were examined**. This subsection states what was registered.
Chapter IV reports the outcomes, including two that failed.

Pre-registration is not common in this literature and the reason for adopting
it here is specific rather than ceremonial. The central hypothesis of this
study concerns a failure mode that is seed-conditioned, invisible to the
fidelity metrics, and observable only through diagnostics this study itself
added. A study in that position can construct a persuasive account of almost
any outcome after the fact. Registering the account and its falsification
condition in advance is what makes the eventual report a test rather than a
narrative.

> **[TABLE 3.9]** *Registered hypotheses.* Outcomes are reported in the
> sections named; they are listed here to show which claims were made in
> advance, not to anticipate their results.

| | Hypothesis as registered | Test | Reported in |
|---|---|---|---|
| **H1** | Each mechanism moves its own target cost beyond seed dispersion | Main effects against pooled repeat dispersion | 4.3.2, 4.4.2, 4.5.2 |
| **H2** | Gains are attenuated relative to published terrestrial magnitudes | Renormalised comparison; **structural for M3** — fourteen values per primitive here, not fifty-nine | 4.5.2 |
| **H3** | Simplification × quantisation is sub-additive on quality: a smaller population is more sensitive to lossy attribute compression | Two-way interaction on perceptual similarity | 4.6.3 |
| **H4** | Primitive reduction perturbs medium identifiability, and the medium-only interval mitigates it | Medium diagnostics across the reduction boundary | 4.7 |
| **H5** | Initialisation × simplification is degenerate or sub-additive on count unless the budget binds | Two-way interaction on count; degeneracy excluded in advance by the budget rule | 4.6.2 |
| — | Initialisation × quantisation is approximately additive | Two-way interaction, both metrics | 4.6.4 |

## The central hypothesis and its falsification condition

H4 was the study's central claim and it was registered with a mechanism, not
only a direction. The registered reasoning was an identifiability argument:
the medium model's only spatial input is the rendered depth, which is
renormalised per frame by its own extremes (Section 3.4.3); removing primitives
changes the rendered depth map and therefore those normalisation constants; and
because the attenuation coefficient and the depth enter the composition only as
their product, the coefficient must rescale to compensate. On this reasoning,
**collapse at a reduction event would be governed by the change in cross-frame
dispersion of the depth range across that event — and specifically not by
primitive count or by the proportion removed.**

The falsification condition was stated with the hypothesis: within the
configurations that apply spatial reorganisation without deterministic
initialisation, the ratio of depth-range dispersion after the first event to
dispersion before it must separate the runs that collapse from those that do
not. If it does not separate them, the account is **withdrawn rather than
qualified**, and the medium-only interval's failure returns to unexplained.

Section 4.7.3 reports that it does not separate them, and the account is
withdrawn. Two things follow for how this chapter should be read. The
medium-only interval of Section 3.5.3 remains part of the executed design, but
it is described there as an addition whose motivating reasoning did not survive
its test, not as a remedy derived from an established mechanism. And the
protection that deterministic initialisation provides, which Section 4.7.1
establishes as a rate at p = 0.0016, has no mechanism attached to it in this
thesis.

## The second registered prediction that failed

The initialisation × quantisation prediction of approximate additivity carried
its own falsification condition: that the perceptual interaction resolve in
either direction at two or more standard errors. Section 4.6.4 reports that it
resolves on three scenes at 4.4 to 4.9 standard errors, so the prediction is
rejected by the criterion set before the campaign.

Both failures are reported in the body of Chapter IV rather than in a
limitations section, and neither is reclassified as exploratory after the fact.
That discipline is the point of registering them.

## What else was registered

Three further items were fixed in advance and are stated in their own
subsections because they govern how every result is expressed: the equivalence
margin (Section 3.6.2), the resolution rule and the vocabulary for unresolved
and undetermined effects (Section 3.6.5), and the declaration that peak
signal-to-noise interactions are undetermined by construction, with
interactions adjudicated on perceptual similarity and primitive count (Sections
3.6.5 and 3.8.3).

The last of these deserves emphasis because it constrains the study's own
headline metric. It was registered *before* the analysis, on the arithmetic of
the design rather than on the results, and it means the campaign declined in
advance to interpret a class of quantity that it would nonetheless compute and
report.

---

## Review log

**Domain Researcher** — The draft listed the hypotheses without H4's mechanism,
which is what made it falsifiable and what Section 4.7.3 actually tests.
Registering a direction alone would not have been a test. → *applied*: the
identifiability argument in full, followed by the falsification condition as
written. Second finding: the draft did not state that the registered response
to failure was withdrawal rather than qualification, which is what makes
Section 4.7.3's treatment principled rather than harsh. → *applied*.

**Supervisor** — The draft justified pre-registration in general terms. The
specific reason is stronger and is particular to this study: a seed-conditioned
failure invisible to the standard metrics is exactly the situation in which a
post-hoc account is most persuasive and least trustworthy. → *applied*, as the
second paragraph. Devil's advocate: does a methodology chapter that announces
two failed predictions undercut the study? It is the opposite — a chapter
listing only predictions that held would invite the question of what else was
predicted.

**Journal Reviewer** — The table anticipated results in a methodology chapter.
→ *applied*: the caption states the table shows which claims were made in
advance, and outcomes are located rather than summarised. Second: the
undetermined declaration was mentioned without saying it was registered before
the analysis, which is the only thing that distinguishes it from a convenient
exclusion. → *applied*: closing paragraph.
