---
section: "4.2.2"
title: "Reconstruction Fidelity and Efficiency per Scene"
chapter: 4
action: Rewrite
evidence: ["FINDINGS §2", "results_by_scene.csv"]
figures: []
tables: ["Table 4.4"]
citations: ["Wang et al., 2004", "Zhang et al., 2018"]
status: refined
word_count: 688
---

# 4.2.2 Reconstruction Fidelity and Efficiency per Scene

This subsection establishes the operating point every later comparison moves
away from. It is reported per scene, and the reason for that convention is
visible in the table itself: the corpus is not four samples of one difficulty
but four materially different reconstruction problems.

> **[TABLE 4.4]** *Reference implementation and unmodified configuration, per
> scene. Mean over three repeats.* Render rate is measured on the evaluation
> hardware described in Section 4.1.1. Source: `results_by_scene.csv`.

| Scene | | PSNR (dB) | SSIM | LPIPS | Primitives | Render rate (fps) | Training (s) |
|---|---|---:|---:|---:|---:|---:|---:|
| Curaçao | SS | 29.910 | 0.905 | 0.1828 | 4 276 736 | 82.7 | 4 662 |
| | A0 | 29.868 | 0.907 | 0.1830 | 4 033 783 | 83.4 | 4 562 |
| IUI3 Red Sea | SS | 27.500 | 0.869 | 0.2081 | 3 077 310 | 157.0 | 3 482 |
| | A0 | 27.648 | 0.869 | 0.2076 | 2 814 411 | 152.2 | 3 324 |
| Japanese Gardens | SS | 22.945 | 0.874 | 0.1786 | 2 036 893 | 160.4 | 3 123 |
| | A0 | 22.700 | 0.867 | 0.1854 | 2 620 807 | 145.8 | 3 023 |
| Panama | SS | 28.690 | 0.904 | 0.1458 | 2 100 267 | 160.9 | 3 952 |
| | A0 | 28.567 | 0.902 | 0.1494 | 1 986 104 | 161.6 | 3 568 |

Reference fidelity spans 6.97 dB between the easiest scene and the hardest,
and 7.17 dB for the unmodified configuration. A mechanism effect of a few
tenths of a decibel is therefore an order of magnitude smaller than the
difference between scenes, which is the arithmetical reason this chapter never
reports a fidelity figure averaged across the corpus: such a figure would be
dominated by which scenes were included rather than by what the mechanism did.

**The two fidelity metrics do not rank the scenes alike, and the disagreement
is not marginal.** By peak signal-to-noise ratio the corpus orders Curaçao,
Panama, IUI3 Red Sea, Japanese Gardens, in both configurations. By learned
perceptual similarity the reference orders Panama, Japanese Gardens, Curaçao,
IUI3 Red Sea — and the unmodified configuration swaps the middle pair, the two
being separated by 0.0024 there against a repeat dispersion of 0.0050 on one of
them, so the ordering between them is not resolved. Japanese Gardens is
the worst scene by a distance on the pixel metric, 4.6 dB behind IUI3 Red Sea
in the reference, yet it is the better of the two perceptually. The two metrics are not
measuring the same property: one is sensitive to overall radiometric agreement
and the other to the presence of plausible texture (Wang et al., 2004; Zhang
et al., 2018). Where they disagree in this chapter — and Sections 4.4 and 4.6
contain the largest such disagreements — the disagreement is reported rather
than resolved by choosing the more convenient metric.

Efficiency varies as widely as fidelity. The reference's final population
ranges from approximately 2.0 million primitives on Japanese Gardens to
approximately 4.3 million on Curaçao, a factor of 2.1, and render rate ranges
from 83 to 161 frames per second, a factor of 1.9 running in the opposite
direction. Curaçao is simultaneously the highest-fidelity scene, the largest
representation and the slowest to render, which is what makes it the scene on
which the efficiency mechanisms have the most to gain. Training time follows
population only loosely: Curaçao is the longest at 4 662 s, but Panama trains
for longer than Japanese Gardens despite a smaller final population, because
training cost depends on the population present throughout optimisation rather
than on the population that survives to the end. Section 4.3.2 returns to this
distinction, which is where dense initialisation's effect on training time is
measured.

One feature of the table bears on Section 4.2.6 and is easily misread here.
The unmodified configuration finishes with a *larger* population than the
reference on Japanese Gardens alone, and with a smaller one on the other three
scenes. This is within the equivalence margin established in Section 4.2.1 and
within that scene's repeat dispersion, and it should not be read as a property
of either implementation. It is reported because Japanese Gardens is the scene
whose count dispersion is widest, and a reader comparing the two count columns
would otherwise reach for an explanation the data does not support.

Nothing in this table is a result about the mechanisms. It is the reference
against which those results are stated, and its function in the chapter is to
make the per-scene convention of Section 4.1.2 evidently necessary rather than
merely asserted.

---

## Review log

**Domain Researcher** — The draft reported only the unmodified configuration,
which was appropriate when it was the anchor but leaves the reader unable to
check any later claim against the reference. → *applied*: both configurations
tabulated on every metric. Second finding: the training-time column invited the
inference that cost tracks final population, which is wrong and matters for
Section 4.3.2. → *applied*: Panama and Japanese Gardens named as the
counterexample, with the reason.

**Supervisor** — The PSNR–LPIPS disagreement was stated as a curiosity and left
there. It is a load-bearing fact for Sections 4.4 and 4.6, and the subsection
should commit to how such disagreements will be handled. → *applied*: bolded,
quantified at 4.6 dB, and closed with the commitment that disagreement is
reported rather than resolved by metric selection. Second: the subsection had
no closing statement of its own role. → *applied*.

**Journal Reviewer** — The perceptual ordering of the scenes was given
without saying which configuration it came from, and the two differ: the
reference and the unmodified configuration swap Japanese Gardens and Curaçao,
which are separated by less than one repeat standard deviation. → *applied*:
the reference's ordering given, the swap noted as unresolved, and Section 3.3.2
now agrees. Second: two metrics named without citation at first substantive use
in this subsection. → *applied*. Third: render rate given without saying where
it was measured. → *applied*: cross-reference to Section 4.1.1. Fourth: the
Japanese Gardens count inversion appeared in the table with no comment, which
invites a reader to draw a conclusion the data does not support. → *applied*:
penultimate paragraph.
