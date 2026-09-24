---
section: "4.6.4"
title: "Initialisation × Quantisation"
chapter: 4
action: Add
evidence: ["FINDINGS §3", "analysis_unweighted.json"]
figures: ["figure-4-16-interaction-plots"]
tables: ["Table 4.18"]
citations: []
status: refined
word_count: 719
---

# 4.6.4 Initialisation × Quantisation

This pair carried a registered prediction of approximate additivity, together
with an explicit condition under which that prediction would be considered
falsified. **The prediction failed, and this subsection reports the failure
rather than reinterpreting it.**

> **[TABLE 4.18]** *Two-way interaction between deterministic initialisation
> and attribute-level quantisation.* Contrast A5 − A1 − A3 + A0. Source:
> `analysis_unweighted.json`.

| Scene | ΔLPIPS | z | Count (log ratio) | z |
|---|---:|---:|---:|---:|
| Curaçao | **+0.021** | **+4.8** | ×1.21 | `UNRES` |
| IUI3 Red Sea | **−0.008** | **−4.4** | ×1.14 | `UNRES` |
| Japanese Gardens | +0.005 | +1.4 | ×1.11 | `UNRES` |
| Panama | **+0.027** | **+4.9** | ×0.81 | `UNRES` |

The registered falsification condition was that the perceptual interaction
resolve in either direction at two or more standard errors. It resolves on
three scenes, at 4.4 to 4.9 standard errors. The prediction of approximate
additivity on perceptual similarity is therefore rejected by the criterion set
before the campaign ran.

On primitive count the prediction held: the interaction is unresolved on every
scene, with ratios between ×0.81 and ×1.21. As in Section 4.6.3, this is the
expected outcome for a mechanism that does not alter the population.

**The failure comes with a caveat that must travel with it, because it bears on
what the failure means.** The perceptual interaction's sign is inconsistent —
positive on Curaçao and Panama, negative on IUI3 Red Sea. A systematic coupling
between two mechanisms would be expected to hold its direction across a corpus.
A term that resolves strongly in both directions on different scenes is not the
signature of a mechanism interacting with another mechanism; it is what
scene-specific sensitivity looks like when the denominator is small. Perceptual
similarity's per-scene repeat dispersion in this campaign is between 0.001 and
0.009, so an absolute difference of 0.02 clears two standard errors comfortably
on most scenes without being large in the metric's own terms.

Both facts are reported and neither is used to dismiss the other. The
pre-registered condition was met and the prediction is recorded as failed. The
pattern of the failure does not support a claim that these two mechanisms
interact perceptually in any consistent direction, and no such claim is made.
What can be said is narrower: the assumption of additivity between these two
mechanisms is not safe on perceptual similarity, and a practitioner combining
them should not expect the costs of Sections 4.3.1 and 4.5.1 simply to add.

> **[FIGURE 4.16]** `figures/chapter4/figure-4-16-interaction-plots.pdf`
> *Interaction plots on perceptual similarity.* The rightmost panel is this
> pair. The lines are non-parallel in opposite directions on different scenes,
> which is the inconsistency described here.
> **Status:** built

It is worth being explicit about why this is reported at all, given that no
interpretation survives it. A pre-registered prediction that fails is evidence
about the prediction, and the alternative — quietly reclassifying it as
exploratory once the data arrived, or attaching a post-hoc mechanism to the
scenes where it resolved positive — is the practice pre-registration exists to
prevent. Section 4.7.3 reports a second and more consequential failure of the
same kind, and the two are treated identically.

The peak signal-to-noise interaction for this pair resolves on IUI3 Red Sea at
+0.91 dB and on Panama at −1.30 dB. These are `UNDETERMINED` by construction
(Section 4.6.1), and their signs disagree, which is the same pattern the
perceptual terms show and the reason Section 4.6.1 treats sign inconsistency as
corroborating the resolution argument rather than as a separate finding.

---

## Review log

**Domain Researcher** — The draft reported the resolved terms and then argued
they were probably noise, which reads as explaining away a failed prediction.
The correct treatment is to report the failure against the registered criterion
*and* report that the pattern does not support a mechanism claim, without
letting either cancel the other. → *applied*: both stated, with the explicit
sentence that neither is used to dismiss the other. Second finding: the
small-denominator point needed the actual dispersion figures to be checkable.
→ *applied*: 0.001 to 0.009.

**Supervisor** — The draft did not say why a failed prediction with no
surviving interpretation earns a subsection. → *applied*: the penultimate
paragraph, naming the alternatives that pre-registration exists to prevent and
linking to the second failure in Section 4.7.3. Devil's advocate: is "not safe
to assume additivity" too weak a conclusion to draw from three resolved terms?
It is what the inconsistent sign permits; a stronger claim would require the
direction to hold.

**Journal Reviewer** — The falsification condition was referred to but not
quoted, so a reader could not verify the prediction failed on its own terms.
→ *applied*: stated in full, with the observed z range against it. Second: the
PSNR terms were omitted. → *applied*, with the connection to Section 4.6.1's
sign-flip argument.
