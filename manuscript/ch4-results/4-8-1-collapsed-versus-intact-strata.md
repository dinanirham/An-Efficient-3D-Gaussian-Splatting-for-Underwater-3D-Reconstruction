---
section: "4.8.1"
title: "Collapsed Versus Intact Strata"
chapter: 4
action: Add
evidence: ["FINDINGS §8", "RQ4", "H7"]
figures: ["figure-4-13-collapsed-medium"]
tables: ["Table 4.18"]
citations: ["Wang et al., 2004", "Zhang et al., 2018"]
status: refined
word_count: 742
---

# 4.8.1 Collapsed Versus Intact Strata

Sections 4.3 to 4.7 established that spatial reorganisation drives the medium
model into a degenerate state in a substantial minority of runs, and that
deterministic initialisation prevents it. This section establishes something
about the instruments rather than the mechanisms: none of the fidelity metrics
reported in this thesis, and none in general use for novel view synthesis,
distinguishes a run whose medium model has collapsed from one whose has not.

The comparison is made within cell and scene. Each of A2 and A6 produced both
collapsed and intact repeats on some scenes, so a collapsed run can be compared
with an intact run of the *same configuration* on the *same scene*, holding
everything fixed except the outcome under test. Six of the eight cell–scene
combinations support such a comparison; IUI3 Red Sea produced no collapsed run
in either cell and is therefore absent. Differences are expressed in units of
the unmodified configuration's per-scene standard deviation over three repeats,
so that a difference of one is exactly the run-to-run variation the campaign
would expect from reseeding alone.

> **[TABLE 4.18]** *Fidelity by collapse stratum, within cell and scene.*
> Collapsed minus intact, in units of the per-scene repeat standard deviation.
> The final column gives the blue-channel attenuation coefficient of each
> stratum, which is what separates them.

| Cell × scene | n (collapsed / intact) | ΔPSNR | ΔLPIPS | β_att,b collapsed → intact |
|---|:-:|---:|---:|---|
| A2 Curaçao | 1 / 2 | +1.42 | −0.21 | −0.048 → 1.17, 1.36 |
| A2 Japanese Gardens | 2 / 1 | −0.89 | +1.19 | −0.02, −0.04 → 1.00 |
| A2 Panama | 2 / 1 | −0.38 | +1.63 | −0.06, −0.05 → 1.21 |
| A6 Curaçao | 2 / 1 | −0.27 | +1.93 | −0.03, −0.06 → 1.18 |
| A6 Japanese Gardens | 1 / 2 | **+4.54** | −0.70 | −0.056 → 1.21, 1.07 |
| A6 Panama | 1 / 2 | −0.05 | +0.24 | −0.038 → 0.93, 1.27 |

Across the twelve comparisons the table contains, the median absolute
difference is 0.8 standard deviations. The sign is not consistent: PSNR
favours the collapsed stratum in two comparisons and the intact stratum in
four, while LPIPS favours the collapsed stratum in four and the intact stratum
in two. A difference smaller than the dispersion produced by reseeding, with a
sign that does not settle, is not a detection.

The single comparison exceeding two standard deviations deserves explicit
treatment, because it runs against the argument rather than for it. On
Japanese Gardens, A6's collapsed run scores 4.54 standard deviations *better*
in PSNR than its intact counterparts. The apparent magnitude is an artefact of
the denominator: that scene's PSNR standard deviation is 0.126 dB, so the
difference in question is 0.57 dB, and it rests on one collapsed run against
two intact ones. The honest reading is that the largest effect the fidelity
metrics register across this comparison points the wrong way, at a sample size
that cannot support it. Training PSNR behaves no differently — every stratum
pair falls within 0.6 dB — so the insensitivity is not an artefact of
evaluating on held-out views.

What separates the strata is visible in the final column and is not subtle. A
collapsed run has driven its blue attenuation coefficient to approximately
−0.05, against roughly +1.2 in an intact run of the same configuration on the
same scene. Negative attenuation is not a small error in a fitted parameter; it
describes water that amplifies light with distance, and it is physically
meaningless. Figure 4.13 shows what this looks like when rendered: the
attenuation map of the collapsed run is unmistakable beside the reference and
the unmodified configuration, while the composed images that the metrics
actually score are not.

> **[FIGURE 4.13]** `figures/chapter4/figure-4-13-collapsed-medium.pdf`
> *A lost attenuation channel — Japanese Gardens.* One scene and one held-out
> view across three configurations — the reference, the unmodified
> configuration, and a collapsed simplification run — shown as attenuation map
> and restored image. The collapsed attenuation map is immediately
> distinguishable; the composed images the fidelity metrics score are not.
> **Status:** built · **Anchored on:** SS

The explanation lies in the structure of the image formation model rather than
in any deficiency of the metrics themselves. PSNR, SSIM (Wang et al., 2004) and
LPIPS (Zhang et al., 2018) are computed on the composed image, which is the
product of a restored image and a medium term. When the medium term is driven
to a physically meaningless value, the restored image absorbs the discrepancy,
and their product continues to match the observation. The metrics are measuring
a quantity that remains correct while the decomposition beneath it becomes
wrong.

The consequence for this thesis is direct, and it constrains every fidelity
number reported in Chapter IV: those numbers are statements about the composed
image alone. The decomposition into a scene and a medium — which is the reason
a physically grounded underwater method is preferred to a general one — is not
something they can check. Any evaluation protocol that selects an efficiency
configuration on fidelity alone will select collapsed models without registering
that it has done so.

---

## Review log

**Domain Researcher** — Draft asserted that "quantisation and simplification
are equally invisible to the metrics." Only simplification produces collapse in
this campaign; quantisation does not, so the claim overreached its evidence.
→ *applied*: restricted to the two cells that collapse. Second finding: the
draft described β_att,b in physical units. Depth is renormalised per frame, so
the coefficient is dimensionless and only within-scene comparison is
meaningful. → *applied*: comparison kept within cell and scene, the word
"physically meaningless" attached to the sign rather than the magnitude.

**Supervisor** — The +4.54 outlier was in the table but not in the prose,
which reads as burying the one number that argues against the section.
→ *applied*: promoted to its own paragraph and reported as pointing the wrong
way, with the 0.126 dB denominator that explains it. Second finding: the
closing paragraph originally ended on the mechanism. It should end on the
consequence for a reader choosing a configuration. → *applied*.

**Journal Reviewer** — "median 0.8 sd" appeared without n or the sign
distribution. → *applied*: twelve comparisons named, sign split given for both
metrics. Second: LPIPS and SSIM were used without citation at first use in the
chapter. → *applied*: Wang et al. (2004) and Zhang et al. (2018), both in the
controlled register. Third: table lacked a stand-alone caption. → *applied*.
