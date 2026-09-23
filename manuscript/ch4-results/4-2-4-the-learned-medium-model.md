---
section: "4.2.4"
title: "The Learned Medium Model"
chapter: 4
action: Add
evidence: ["FINDINGS §2b"]
figures: ["figure-4-03-attenuation-spectra"]
tables: ["Table 4.5", "Table 4.6"]
citations: ["Akkaynak & Treibitz, 2018"]
status: refined
word_count: 878
---

# 4.2.4 The Learned Medium Model

Every preceding subsection asks whether the medium model survived; none reports
what it was. The estimator's distinguishing output is a decomposition of the
observed image into a medium-free radiance and a water column, and the
parameters of that water column are the part of the output that can be checked
against physical expectation. This subsection reports them. It is descriptive
and was not pre-registered: no prediction was made about these values before the
campaign, nothing here is a hypothesis test, and it is presented as
characterisation rather than as a result.

**One caveat bounds everything in this subsection.** The depth the medium model
reads is renormalised to the unit interval per frame before it reaches the
attenuation and backscatter networks. The fitted coefficients are therefore
dimensionless with respect to a normalised depth rather than attenuation in
inverse metres. Two consequences follow, and both are binding. Their magnitudes
cannot be compared with published measurements of natural water, and they
cannot be compared across scenes of differing depth range. What remains
comparable is the **ordering of the three colour channels within one scene**,
because all three are fitted against the same normalised depth. Every
interpretation below is an interpretation of ordering.

> **[TABLE 4.5]** *Fitted medium parameters, mean over three repeats.*
> Attenuation coefficient β_att, backscatter saturation rate β_bs, and veiling
> light B∞, per colour channel. Dimensionless with respect to a per-frame
> normalised depth. Source: FINDINGS §2b.

| | Scene | β_att (r, g, b) | β_bs (r, g, b) | B∞ (r, g, b) |
|---|---|---|---|---|
| SS | Curaçao | 2.155, 1.724, 1.222 | 16.17, 10.69, 8.97 | 0.085, 0.097, 0.113 |
| | IUI3 Red Sea | **0.845, 0.933, 1.026** | 18.41, 15.97, 7.11 | 0.143, 0.224, 0.339 |
| | Japanese Gardens | 2.294, 1.837, 1.447 | 22.12, 10.77, 8.91 | 0.158, 0.199, 0.234 |
| | Panama | 1.372, 1.285, 1.033 | 11.87, 8.51, 8.28 | 0.157, 0.185, 0.211 |
| A0 | Curaçao | 2.160, 1.766, 1.255 | 14.06, 9.23, 7.76 | 0.087, 0.101, 0.118 |
| | IUI3 Red Sea | **0.956, 1.028, 1.064** | 16.48, 12.38, 5.40 | 0.144, 0.226, 0.354 |
| | Japanese Gardens | 1.985, 1.526, 1.148 | 20.47, 9.48, 7.19 | 0.158, 0.202, 0.243 |
| | Panama | 1.554, 1.264, 1.035 | 15.85, 12.28, 10.79 | 0.146, 0.163, 0.186 |

The veiling light behaves as expected everywhere. B∞ is ordered blue above
green above red on every scene in both implementations, which is a blue-green
veiling colour and is what these waters look like. There is nothing anomalous
to report on that parameter.

The attenuation coefficient is the informative one. Water attenuates long
wavelengths fastest, so β_att should be ordered red above green above blue
(Akkaynak & Treibitz, 2018). Testing the red-minus-blue difference against
repeat dispersion gives the following.

> **[TABLE 4.6]** *Spectral ordering of the fitted attenuation, per scene.*
> Red minus blue, with the z-score against repeat dispersion at three repeats.
> Source: FINDINGS §2b.

| Scene | A0: β_att,r − β_att,b | z | SS | z | Verdict |
|---|---:|---:|---:|---:|---|
| Curaçao | +0.905 | +4.18 | +0.933 | +5.23 | physical, resolved in both |
| Japanese Gardens | +0.838 | +2.57 | +0.848 | +4.86 | physical, resolved in both |
| Panama | +0.519 | +1.66 | +0.339 | +1.68 | physical in direction, `UNRESOLVED` |
| IUI3 Red Sea | **−0.108** | −1.63 | **−0.181** | −0.81 | **inverted in direction, `UNRESOLVED`** |

On two scenes the physical ordering is recovered and resolved in both
implementations. On Panama it is present in direction but does not resolve at
three repeats. On IUI3 Red Sea the ordering is inverted — blue attenuating
faster than red — and **this inversion does not resolve either, and is not
claimed as a finding**. What can be stated is weaker, and is stated in three
parts.

First, IUI3 Red Sea is the only scene of the four whose fitted spectrum fails
to show the physical ordering, and it fails in both the reference and the
unmodified configuration. Whatever produces it is not introduced by the
reimplementation. Second, the direction is consistent across configurations:
taking intact runs only, red is the largest coefficient on the other three
scenes in all ten configurations, and on IUI3 Red Sea in only one. Ten
independently configured cells agreeing is not a significance test, but it is
not nothing. Third, and most informative, **the two halves of the medium model
disagree with each other on this scene and on no other**. The backscatter
saturation rate β_bs is ordered red above green above blue on IUI3 Red Sea in
both implementations — the physical ordering — while β_att on the same runs is
ordered blue above red. Nothing in the optimisation constrains the two
coefficient sets to order alike; on the other three scenes they nonetheless
agree. Under a single water column they describe the same inherent optical
properties and should agree. That they do not, on one scene, indicates that the
fit on that scene is not recovering physical parameters. That is a statement
about identifiability, not about the water.

> **[FIGURE 4.3]** `figures/chapter4/figure-4-03-attenuation-spectra.pdf`
> *Learned attenuation spectra, per scene.* β_att by channel for each scene,
> reference and unmodified configuration side by side, with the physical
> ordering marked and the inverted scene highlighted.
> **Status:** built

This observation joins four others already attached to the same scene. Every
mechanism costs perceptual quality on IUI3 Red Sea at 20 to 48 standard errors
(Section 4.3.1 onward); no simplification run collapses there where the other
three scenes collapse at a seed-conditioned rate (Section 4.7.1); one two-way
interaction takes the opposite sign there (Section 4.6.4); and one mechanism's
PSNR effect there fails to replicate across campaigns (Section 4.10). This
subsection adds a fifth: it is the scene whose medium fit is least physically
coherent. The five are consistent with a scene whose geometry–medium
decomposition is poorly constrained, and its acquisition is consistent with
that reading — 25 training views taken consecutively along a reef wall, the
worst-conditioned camera pairing in the corpus. That is an association across
five observations on one scene, not a demonstration, and Section 4.12.4 carries
it as a threat to external validity rather than as a finding.

Three things are explicitly not claimed: that the coefficients are physically
accurate on any scene, since the magnitudes are not in physical units; that the
inversion on IUI3 Red Sea is resolved; and that camera conditioning causes any
of it.

---

## Review log

**Domain Researcher** — The draft interpreted β_att magnitudes as attenuation
coefficients comparable to published water measurements. The per-frame depth
renormalisation makes that unavailable. → *applied*: the caveat is now the
second paragraph, marked as binding, and every interpretation below it is an
interpretation of ordering. Second finding: the strongest evidence for the IUI3
anomaly is not the inversion itself, which is unresolved, but that β_att and
β_bs disagree on that scene alone when the physics requires them to agree.
→ *applied*: promoted to the third and most informative of the three
statements, with the reason a referee would want.

**Supervisor** — The draft asserted the inversion as a finding, then hedged in
a footnote. Either it is claimed or it is not. → *applied*: "does not resolve
and is not claimed", in the body, followed by the three weaker statements that
can be made. Devil's advocate: with five anomalies on one scene, why not
exclude it? Because exclusion after seeing the results is exactly the practice
this chapter's pre-registration discipline exists to prevent; the scene stays
and the association is reported as an association.

**Journal Reviewer** — The physical expectation for spectral ordering was
asserted without citation. → *applied*: Akkaynak and Treibitz (2018), from the
register. Second: z-scores reported without stating the dispersion they are
computed against or the n. → *applied*, in the table caption. Third: the
subsection's unregistered status needed to be declared at the top rather than
inferred. → *applied*: opening paragraph.
