---
section: "4.9.2"
title: "Quantitative Comparison Against the Baseline"
chapter: 4
action: Add
evidence: ["FINDINGS §6", "results_by_scene.csv"]
figures: ["figure-q1-a0d-gradient"]
tables: ["Table 4.25"]
citations: []
status: refined
word_count: 704
---

# 4.9.2 Quantitative Comparison Against the Baseline

This contrast is reported against the configuration with no mechanism active,
not against the reference, for the reason given in Section 4.9.1: it is a
supplementary contrast on the factorial's own corner rather than a candidate
measured against the published method.

> **[TABLE 4.25]** *Gradient detachment against the unmodified configuration,
> per scene.* Ratios for multiplicative quantities, differences for additive
> ones, each with z against repeat dispersion at three repeats. Source:
> `results_by_scene.csv`.

| Scene | Count | Training time | Render rate | ΔPSNR | ΔLPIPS |
|---|---:|---:|---:|---:|---:|
| Curaçao | **×0.19** (−16.3) | ×0.68 (−21.3) | ×2.31 (+13.1) | +0.28 `UNRES` | **+0.011** (+3.9) |
| IUI3 Red Sea | **×0.32** (−9.4) | ×0.78 (−14.8) | ×1.35 (+6.5) | −0.09 `UNRES` | **+0.024** (+32.6) |
| Japanese Gardens | **×0.25** (−3.8) | ×0.76 (−6.9) | ×1.70 (+6.5) | +0.30 `UNRES` | **+0.009** (+3.0) |
| Panama | **×0.33** (−3.1) | ×0.81 (−3.4) | ×1.56 (+4.8) | +0.25 `UNRES` | **+0.026** (+4.7) |

**Both halves of the registered prediction held.** The count effect resolves on
all four scenes: three to five times fewer primitives, at 3.1 to 16.3 standard
errors. With it come 19 to 32 per cent less training time, 1.35 to 2.31 times
the frame rate, and 40 to 60 per cent less peak render memory. The pixel-metric
effect does not resolve on any scene, with every value under 1.1 standard
errors.

**The pixel-metric result is reported as unresolved, not as a point estimate,
and this retires an earlier figure.** An earlier campaign reported a specific
loss of 0.107 dB for this mechanism, measured against a baseline subsequently
shown to be defective and at one repeat. At three repeats against a sound
baseline the effect is +0.25 to +0.30 dB on three scenes and −0.09 dB on one,
none of it separable from repeat dispersion. The honest statement is **within
±0.5 dB at this resolution**, and the earlier point estimate is withdrawn. It
was never a measurement of the precision it implied.

**Perceptual similarity resolves worse on all four scenes**, by 0.009 to 0.026
at 3.0 to 32.6 standard errors. This was the metric flagged in advance as the
one that might resolve, and it resolves against the mechanism. The cost is real
and it is smaller than spatial reorganisation's — 0.009 to 0.026 against 0.033
to 0.082 — for a smaller count reduction, three to five times against fourteen
to twenty-five. Structural similarity does not move on any scene.

> **[FIGURE Q1-A0D]** `figures/chapter4/figure-q1-a0d-gradient.pdf`
> *Gradient detachment against the reference and the baseline.* Near-field crop
> of one held-out view per scene, seed 0, with ground truth, the reference, the
> unmodified configuration and the mechanism.
> **Status:** built · **Anchored on:** SS

**No run lost an attenuation channel: 0 of 12.** The mechanism reduces the
population by three to five times and the medium model survives it in every
run. Section 4.9.3 takes up what that does and does not tell us, since the
comparison with spatial reorganisation is the reason this contrast is
interesting beyond its own numbers.

One representational property is worth recording. The mechanism's output is 65
to 76 per cent visible, against 23 to 43 per cent for the reference and 78 to
94 per cent for deterministic initialisation (Section 4.2.6). It sits between
the two, which is consistent with a mechanism that suppresses densification
continuously rather than either preventing it entirely or pruning its results.
Its count reduction of three to five times is therefore a reduction of roughly
one and a half to two and a half times against the visible population, the
smallest such ratio of any mechanism here.

---

## Review log

**Domain Researcher** — The draft gave the pixel-metric effect as a mean with
no resolution marker, reproducing exactly the error the earlier campaign made.
→ *applied*: reported as unresolved with the range, the earlier point estimate
explicitly retired, and the reason it was never as precise as it looked.
Second finding: the visible-population figure was absent, leaving this the only
mechanism section without it. → *applied*, with the placement between the other
two mechanisms and the ratio against the visible population.

**Supervisor** — The draft reported the prediction's outcome in a subordinate
clause. A two-part prediction registered in advance and held in both parts is
worth stating as the subsection's first finding. → *applied*. Devil's advocate:
is retiring a published figure from an earlier campaign too aggressive? It was
measured against a baseline later shown defective at n = 1; retiring it is the
minimum, and the paragraph says why rather than simply asserting it.

**Journal Reviewer** — Peak render memory was quoted without appearing in the
table. → *retained in prose*: it is a secondary quantity and the table is
already six columns wide, but the range is now given explicitly rather than
described. Second: the perceptual cost was compared with spatial
reorganisation's without both count reductions being stated, which makes the
comparison unreadable. → *applied*: both pairs given.
