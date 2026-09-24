---
section: "4.6.2"
title: "Initialisation × Simplification"
chapter: 4
action: Add
evidence: ["FINDINGS §3", "analysis_unweighted.json"]
figures: ["figure-4-16-interaction-plots"]
tables: ["Table 4.16"]
citations: []
status: refined
word_count: 803
---

# 4.6.2 Initialisation × Simplification

This is the campaign's largest interaction, it was predicted, and its cause is
structural rather than physical.

> **[TABLE 4.16]** *Two-way interaction between deterministic initialisation
> and spatial reorganisation.* Contrast A4 − A1 − A2 + A0; perceptual
> similarity additive, primitive count as a log ratio. z from the four cell
> means. Source: `analysis_unweighted.json`.

| Scene | ΔLPIPS | z | Count (log ratio) | z |
|---|---:|---:|---:|---:|
| Curaçao | −0.004 | −0.9 | **×14.3** | **+49.8** |
| IUI3 Red Sea | **−0.048** | **−17.1** | **×10.9** | **+33.1** |
| Japanese Gardens | **−0.015** | **−2.6** | **×9.7** | **+10.1** |
| Panama | **−0.017** | **−2.0** | **×8.0** | **+9.3** |

**On primitive count the two mechanisms are strongly sub-additive, by a factor
of eight to fourteen, resolved on every scene at 9 to 50 standard errors.** The
pre-registered hypothesis predicted sub-additivity or degeneracy here, and it
held in its sub-additive form.

The cause is the budget and can be stated exactly. Deterministic initialisation
alone reduces count to roughly 0.08 of the reference; spatial reorganisation
alone to roughly 0.05. Independent composition would multiply these, predicting
a combined population of approximately 11 000 primitives. The combination
instead lands near 130 000. The reason is that spatial reorganisation prunes to
an absolute budget of 200 000 primitives rather than by a proportion: a
configuration arriving at the pruning event with 224 000 primitives has a third
removed, where one arriving with 2 400 000 has nine tenths removed. The second
mechanism cannot remove what the first has already prevented from existing.

**This interaction is therefore an artefact of the budget's construction, not a
physical property of the scenes or of the mechanisms' interaction in any deeper
sense.** It would change, and could be made to vanish, by expressing the budget
as a proportion of the entering population instead of as an absolute count. The
distinction matters for what Chapter V may conclude: the finding is that
absolute-budget pruning does not compose multiplicatively with a mechanism that
reduces the entering population, which is a design lesson, not a discovery
about underwater reconstruction. Section 4.4.2 recorded the absolute-budget
property in anticipation of this.

**On perceptual similarity the interaction is negative on three scenes, and
this was not registered.** The pair costs *less* perceptual quality than the
sum of its parts — by 0.048 on IUI3 Red Sea at 17 standard errors, and by 0.015
to 0.017 on Japanese Gardens and Panama at the margin of resolution. The
mechanisms' perceptual costs do not add; combining them recovers part of what
each loses alone.

An interpretation is available and is labelled post-hoc because no prediction
was made: deterministic initialisation leaves spatial reorganisation a
better-placed population to select from, so the importance criterion discards
less of what matters. The campaign did not test this and cannot separate it
from the alternative that the combination simply operates in a regime where
both mechanisms' losses saturate. It is offered as a reading, not as an
explanation, and nothing later in this chapter depends on it.

> **[FIGURE 4.16]** `figures/chapter4/figure-4-16-interaction-plots.pdf`
> *Interaction plots on perceptual similarity.* The leftmost panel is this
> pair. Non-parallel lines indicate non-additive composition; the convergence
> visible on IUI3 Red Sea is the −0.048 term.
> **Status:** built

The favourable perceptual interaction is the reason the combined configuration
appears on the operating-point front in Section 4.6.6 where spatial
reorganisation alone does not. On three scenes the pair has both fewer
primitives and lower perceptual error than that mechanism by itself, which is
not a result either main effect predicts.

The peak signal-to-noise interaction for this pair resolves on Panama alone, at
−0.95 dB. Per Section 4.6.1 it is `UNDETERMINED` by construction and is
tabulated without interpretation. It is recorded here so that a reader
comparing this chapter against the underlying analysis finds nothing withheld.

One connection to Section 4.7 is worth flagging and not developing here. The
configuration pairing these two mechanisms is one of the two that never loses
an attenuation channel despite containing spatial reorganisation. That is a
result on the third axis, it is the campaign's largest finding on that axis,
and it belongs to Section 4.7.1 where the incidence across all configurations
is reported together. It is mentioned here only because a reader arriving at a
favourable count-and-perceptual interaction might otherwise conclude the pair
is favourable on every axis, which happens in this case to be true and is
established elsewhere.

---

## Review log

**Domain Researcher** — The draft reported the ×8–14 sub-additivity as a
finding about the mechanisms. It is a consequence of an absolute budget meeting
a reduced entering population, and stating it otherwise would mislead anyone
attempting to generalise. → *applied*: the arithmetic in full, with the
explicit statement that a proportional budget would change or remove it, and
what Chapter V may therefore conclude. Second finding: the post-hoc reading of
the perceptual interaction was presented as an explanation. → *applied*:
labelled, with the untested alternative named.

**Supervisor** — The draft buried the unregistered favourable result beneath
the predicted one. A result nobody predicted, resolved at 17 standard errors,
is the more interesting half of the subsection. → *applied*: bolded and given
its own development, with the forward link to why it puts this pair on the
front in Section 4.6.6. Devil's advocate: does calling the count interaction
"an artefact" undersell a resolved result at 50 standard errors? No — it is
resolved and it is structural, and both are said.

**Journal Reviewer** — The PSNR term for this pair was omitted entirely, which
a reader checking against the analysis would notice. → *applied*: reported with
its `UNDETERMINED` status and the reason. Second: the third-axis result was
alluded to without being placed. → *applied*: named as belonging to Section
4.7.1, with the reason for mentioning it at all.
