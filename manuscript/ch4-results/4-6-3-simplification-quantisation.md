---
section: "4.6.3"
title: "Simplification × Quantisation"
chapter: 4
action: Add
evidence: ["FINDINGS §3", "FINDINGS §7", "analysis_unweighted.json"]
figures: ["figure-4-16-interaction-plots"]
tables: ["Table 4.17"]
citations: ["Navaneet et al., 2024"]
status: refined
word_count: 706
---

# 4.6.3 Simplification × Quantisation

This pair carries a pre-registered hypothesis with a directional prediction,
and it is the one that transfers a premise from the source literature rather
than arising from this design.

> **[TABLE 4.17]** *Two-way interaction between spatial reorganisation and
> attribute-level quantisation.* Contrast A6 − A2 − A3 + A0. Source:
> `analysis_unweighted.json`.

| Scene | ΔLPIPS | z | Count (log ratio) | z |
|---|---:|---:|---:|---:|
| Curaçao | **+0.020** | **+6.5** | ×1.18 | `UNRES` |
| IUI3 Red Sea | −0.006 | −1.3 | ×1.15 | `UNRES` |
| Japanese Gardens | **+0.017** | **+3.0** | ×1.13 | `UNRES` |
| Panama | **+0.015** | **+2.0** | ×0.82 | `UNRES` |

**The perceptual interaction is positive on three scenes: the pair costs more
than the sum of its parts.** The hypothesis registered before the campaign
predicted exactly this, on the premise that a smaller primitive population is
more sensitive to lossy attribute compression, because each surviving primitive
carries a larger share of the image and an error in its attributes is spread
over more pixels. That premise comes from the source compression literature
(Navaneet et al., 2024) and was carried into this design as a prediction. It
held on Curaçao and Japanese Gardens cleanly, and on Panama at the threshold
of resolution.

IUI3 Red Sea is the exception, with a term of −0.006 that does not resolve. It
is the exception in almost every section of this chapter, and Section 4.12.4
collects the pattern. Here the reading is unusually constrained: that scene is
also the one on which each mechanism's individual perceptual cost is largest,
so there is less room for their combination to cost more than their sum. That
is a saturation account and it is untested.

**On primitive count the interaction is unresolved on every scene**, with
ratios between ×0.82 and ×1.18. This is the expected result, and it is the
cleanest confirmation in the chapter that the mechanisms act where they are
supposed to. Attribute-level quantisation does not change the number of
primitives (Section 4.5.2), so there is nothing for it to interact with on that
axis, and the design duly finds nothing. A resolved count interaction here
would have indicated a fault in the implementation rather than a property of
the mechanisms.

> **[FIGURE 4.16]** `figures/chapter4/figure-4-16-interaction-plots.pdf`
> *Interaction plots on perceptual similarity.* The middle panel is this pair.
> Diverging lines indicate a cost greater than the sum of the parts.
> **Status:** built

One consequence appears in Section 4.6.6 and is worth connecting. The
configuration combining these two mechanisms is dominated on the count against
perceptual-error front on three scenes — by the configurations that include
deterministic initialisation, which have both fewer primitives and lower
perceptual error. The positive interaction reported here is part of why: the
pair pays a perceptual penalty that neither mechanism pays alone, and the
alternative combinations do not.

A second consequence is recorded in Section 4.6.6 from the opposite direction
and is easy to miss. Once the population is small, attribute-level quantisation
begins to cost frame rate — the configuration combining these two renders 5 to
22 per cent slower than spatial reorganisation alone on three scenes. Decoding
a codebook is not free at 130 000 primitives in the way it is at three million,
because the decode cost is a fixed fraction of a much smaller total. That
comparison is between configurations rather than a contrast, is unresolved as a
main effect from below (Section 4.5.2), and is reported as a description.

The peak signal-to-noise interaction for this pair resolves on Curaçao at
−1.30 dB and on Panama at −0.66 dB. Per Section 4.6.1 both are `UNDETERMINED`
by construction, the signs do not agree with the perceptual terms, and neither
is interpreted.

---

## Review log

**Domain Researcher** — The draft stated the hypothesis's premise without
attributing it, so a reader could not tell whether it originated in this work
or was carried from the compression literature. → *applied*, with the citation
and the mechanistic reason each surviving primitive carries more of the image.
Second finding: the unresolved count interaction was reported as a null result
when it is a positive control — a resolved term there would indicate an
implementation fault. → *applied*.

**Supervisor** — The draft treated IUI3 Red Sea's exception as one more entry
in a list of that scene's oddities. Here there is a specific reading available —
the mechanisms' individual costs are largest there, leaving less room for
super-additivity — and offering it, marked untested, is better than another
shrug. → *applied*. Second: the frame-rate consequence was in Section 4.6.6
only, where a reader of this pair would not find it. → *applied*, with its
status as a description rather than a contrast made explicit.

**Journal Reviewer** — "At the threshold of resolution" was used for Panama's
z of exactly 2.0 without stating the value. → *applied*: the table carries it
and the text names the threshold. Second: the PSNR terms were omitted.
→ *applied*, with their status and the observation that their signs disagree
with the perceptual terms.
