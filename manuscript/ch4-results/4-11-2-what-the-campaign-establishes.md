---
section: "4.11.2"
title: "What the Campaign Establishes"
chapter: 4
action: Add
evidence: ["all"]
figures: []
tables: []
citations: []
status: refined
word_count: 704
---

# 4.11.2 What the Campaign Establishes

Stated at the level the evidence supports, and no higher.

**The reimplementation is sound.** The configuration with no mechanism active
is equivalent to the published reference within a pre-registered margin on all
four scenes, on every metric that margin covers, with the largest discrepancy —
0.245 dB — smaller than that scene's own repeat dispersion. Neither
implementation loses an attenuation channel in twenty-four runs. This is what
licenses every attribution in the chapter.

**All three mechanisms reduce their target cost, resolved on every scene.**
Deterministic initialisation gives 8.9 to 17.6 times fewer primitives and 11 to
26 per cent less training time; spatial reorganisation 14.3 to 28.5 times fewer
primitives and 1.8 to 3.5 times the frame rate; attribute-level quantisation a
factor of 2.72 in bytes per primitive. Against the population that actually
renders, the first two reductions are 3.7 to 5.3 and 5.1 to 9.5 times.

**Fidelity cost falls almost entirely on perceptual similarity.** Against the
reference, pixel-metric effects are unresolved on ten of the twelve
scene–mechanism pairs; the two that resolve are initialisation on Japanese
Gardens, favourably, and quantisation on IUI3 Red Sea, adversely. Perceptual
effects are resolved and adverse on two scenes for initialisation, four for
simplification, and one for quantisation.
A study reporting only peak signal-to-noise ratio would have concluded that all
three mechanisms are free, and would have been wrong three times over.

**The mechanisms do not compose additively.** The count interaction between
initialisation and simplification is a factor of eight to fourteen, resolved
everywhere, and is structural — a consequence of pruning to an absolute budget.
The perceptual interaction between the same pair is favourable and was not
predicted. Simplification and quantisation are sub-additive on quality on three
scenes, as the source literature's premise predicts.

**Spatial reorganisation destabilises the medium model, and deterministic
initialisation prevents it.** Nine of twenty-four runs lose an attenuation
channel without initialisation, none of twenty-four with it, Fisher exact
two-sided p = 0.0016. Every affected run places its largest attenuation drop at
the first pruning event, without exception. The loss is expressed in the 200
medium-only steps that follow the cut, not in the cut itself. The final size of
the representation is not the cause: the configuration that never collapses
finishes 13 to 17 per cent smaller.

**Whether a channel is lost is decided by the level reached, not the fraction
lost.** Runs that eventually collapse reach a weakest-channel attenuation
between −0.056 and +0.314; runs that do not reach between +0.110 and +6.327.
Configurations entering the first event at three times the attenuation survive
comparable fractional losses.

**The conventional fidelity metrics cannot detect any of this.** Collapsed and
intact runs of the same configuration on the same scene differ by a median 0.8
of a baseline standard deviation on the composed image, across twelve
comparisons, with the sign inconsistent. Two attribute states of a single model
that agree to 1.4 dB on the composed image differ by 17 to 27 dB on the
restored image. Both follow from scoring a product while claiming a
decomposition, and neither is a defect of the metrics within their own scope.

**A method that claims a physical decomposition requires instruments that
examine the decomposition.** This campaign used three — collapse incidence,
internal consistency, physical plausibility — and each detects failure without
needing a ground truth. None measures accuracy. This is the chapter's
methodological result and it generalises beyond the underwater setting to any
estimator whose objective scores a composition of factors it claims to
separate.

Every item above is a statement about four scenes from one corpus, ten
configurations at one operating point each, and three repeats. Section 4.12
states what that bounds.

---

## Review log

**Domain Researcher** — The draft mixed established results with the
descriptive accounts offered for them, so a reader could not tell which were
measurements. → *applied*: every entry is now a measurement or a rate; the
accounts stay in their own sections. Second finding: the visible-population
figures were omitted from the efficiency entry, which is where the chapter's
most easily overstated numbers are. → *applied*, both ranges given alongside
the totals.

**Supervisor** — The draft was a list of the chapter's section headings with
numbers attached. A synthesis has to say things that only become visible when
the results are put together — such as that a PSNR-only study would have
concluded all three mechanisms were free. → *applied*, and that sentence is now
the point of the fidelity entry. Devil's advocate: is the closing paragraph
about scope too grudging to end a synthesis on? It is one sentence and it
points to the section that expands it; ending without it would invite exactly
the over-generalisation the chapter has resisted throughout.

**Journal Reviewer** — The Fisher result and the collapse counts appeared
without the test in a section a reader may consult alone. → *applied*. Second:
the draft claimed pixel-metric effects were unresolved on eleven of twelve
scene–mechanism pairs. Recomputing against the reference gives ten of twelve:
initialisation on Japanese Gardens resolves at z = +2.00 and quantisation on
IUI3 Red Sea at z = −3.06. → *applied*: corrected, with both resolved pairs
named so the count is checkable against Sections 4.3.1, 4.4.1 and 4.5.1.
