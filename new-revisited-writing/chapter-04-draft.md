# CHAPTER IV — RESULTS AND DISCUSSION

*Draft against the architecture in `chapter-04-architecture.md` (Revision 2).
Every quantity is cited to a section of `analysis/campaign-2026-09/FINDINGS.md`,
given here as §0–§14, and none is re-derived in this chapter. Scene names are
given in their corrected form; the corresponding directory names in the
released artifacts are `Curasao`, `IUI3-RedSea`, `JapaneseGradens-RedSea` and
`Panama`, the third of which contains a spelling error that has been retained
in the data for reproducibility.*

---

## 4.1 Experimental Overview

### 4.1.1 Scope of the Completed Campaign

The results reported in this chapter derive from a single experimental
campaign executed between 15 and 21 September 2026. The campaign comprises ten
configurations evaluated on four underwater scenes with three independent
repeats of each combination, giving 120 training runs in total. All 120
completed and are included; none was discarded after inspection.

The ten configurations consist of the eight cells of the $2^3$ factorial
design over the three efficiency mechanisms, together with two configurations
that stand outside the factorial. The first, denoted SS, is the unmodified
upstream implementation of the underwater baseline, trained and measured on
the same harness as every other configuration and serving as the reference
control described in Section 4.2.1. The second, denoted A0D, is a
supplementary contrast in which the alpha-loss gradient is detached from
density control; because dense initialisation replaces density control
entirely, this mechanism is inert in any configuration containing it, and it
is therefore measured against the baseline alone rather than being entered as
a fourth factor (Section 4.9).

| Property | Value |
|---|---|
| Configurations | 10 (SS, A0–A7, A0D) |
| Scenes | 4 (Curaçao, IUI3 Red Sea, Japanese Gardens, Panama) |
| Repeats per cell and scene | 3 |
| Training runs | 120, all complete |
| Training iterations per run | 30 000 |
| Effective optimizer steps | 43 000, or 43 400 where simplification is active |
| Accelerator | NVIDIA A100-SXM4-40 GB throughout |
| Total accelerator time | 107 GPU-hours (9–13 h per configuration) |
| Execution window | 15–21 September 2026 |

*Table 4.1 — Scope of the completed campaign. Source: §0 and the campaign run
ledger.*

Two details of the accounting deserve statement because they bear on the cost
comparisons in Section 4.3 onward. First, the number of effective optimizer
steps is constant within each group of configurations: 43 000 for every
configuration without simplification, and 43 400 for every configuration with
it, the difference being two bursts of 200 medium-only steps that follow the
two simplification events. The mechanisms therefore alter what an iteration
costs rather than how many iterations are performed, and wall-clock
differences are attributable to per-iteration cost rather than to schedule
length. Second, four runs required more than one attempt before completing.
Each carried an empty error field, the signature of a platform disconnection
rather than a fault in the run, and each completed on the subsequent attempt;
the completed attempt is the one reported (§0).

### 4.1.2 Evaluation Criteria and Reporting Conventions

Four reporting conventions are applied throughout this chapter. They are
consequences of the experimental design rather than presentational
preferences, and stating them here avoids repeating the justification at each
result.

**Results are reported per scene and are never averaged across scenes.**
Baseline fidelity spans approximately 7 dB between the easiest and hardest
scene in the corpus, and baseline dispersion differs by a factor of
approximately four across scenes (Section 4.1.3). A fidelity figure averaged
over the four scenes therefore describes none of them, and would conceal the
scene-specific behaviour that Sections 4.3 to 4.5 identify as material.

**An effect is reported as resolved only when its magnitude is at least twice
its standard error**, computed against the repeat dispersion of the scene on
which it was measured. Effects below this threshold are reported as
`UNRESOLVED`. This label is a statement about the resolving power of three
repeats and must not be read as a statement that the effect is absent; an
unresolved effect and a zero effect are not distinguishable in this design.

**Interactions are adjudicated on perceptual similarity and primitive count,
and PSNR interactions are reported as `UNDETERMINED` by construction.** The
standard error of a two-way contrast is approximately twice, and of a
three-way contrast approximately $2\sqrt{2}$ times, the standard error of a
single cell mean. Applying the resolution rule above to the observed
dispersion gives a smallest resolvable PSNR interaction of 0.51 to 1.61 dB
depending on scene, which exceeds the largest PSNR main effect the campaign
measured. No PSNR interaction can therefore be resolved by this design,
whatever its true magnitude. The terms are tabulated in Section 4.6 for
completeness and marked accordingly; no claim in this thesis rests on them.

**Every quantitative statement is labelled as pre-registered or post-hoc.**
The analysis plan, including its hypotheses, its equivalence margin and the
condition under which its central explanation would be considered falsified,
was written and committed before the campaign's results were examined.
Statements arising from that plan are identified as pre-registered; statements
arising from inspection of the data afterwards are identified as post-hoc and
are not presented as explanations. The distinction is carried in the body text
and not relegated to notes, because the strength of a claim in this chapter
depends on which of the two it is.

### 4.1.3 Repeat Dispersion as the Measurement Baseline

Every comparison in this chapter is referred to the dispersion of the baseline
configuration under repetition. Three repeats of the baseline were run on each
scene, differing only in seed, and their standard deviation establishes the
scale against which an effect is judged.

| Scene | PSNR (dB) | LPIPS | Primitive count (CV) |
|---|---:|---:|---:|
| Curaçao | 0.395 | 0.0025 | 8.6 % |
| IUI3 Red Sea | 0.245 | 0.0013 | 12.5 % |
| Japanese Gardens | 0.126 | 0.0050 | 34.3 % |
| Panama | 0.481 | 0.0091 | 36.6 % |

*Table 4.2 — Standard deviation of the baseline configuration over three
repeats, per scene. Source: §0.*

Two features of this table govern the interpretation of later results. The
dispersion of both fidelity metrics is small and comparable across scenes,
which is what makes fidelity effects of a few tenths of a decibel resolvable
at all. The dispersion of primitive count, by contrast, differs by a factor of
four across scenes and is substantial on two of them. On Japanese Gardens and
Panama the baseline's final population varies by approximately one third from
one repeat to the next under identical configuration. Independent measurement
of same-seed non-determinism in the underlying implementation found a median
variation of 21 % with a tail reaching 59 %, so dispersion of this order is
within what the training process itself produces rather than evidence of a
defect. Its consequence is nonetheless direct: on those two scenes, a
difference in primitive count must be large before it can be resolved, and the
interaction terms on count in Section 4.6 are correspondingly unresolved there.

### 4.1.4 Provenance and Experimental Integrity

The campaign was executed from a single implementation state on a single
accelerator type, and the run ledger records one continuous execution window
with no configuration change during it. Two qualifications apply.

First, the results table does not carry a per-run commit identifier. Each run
directory contains a configuration manifest that records the implementation
state at the time the run started, but the collection tool read a field that
the manifest does not write, and the corresponding column is empty for all 120
rows. The defect has been corrected and the field is populated by subsequent
collections; for the campaign reported here, the claim that all runs share one
implementation state rests on the ledger's execution window and the worker log
rather than on the results table itself. This is a weaker form of evidence
than a recorded identifier and is reported as such.

Second, the same audit established that at least one run of the earlier,
archived campaign was executed from an uncommitted working tree. That
observation does not affect the campaign reported in this chapter, but it
bears on the cross-campaign comparison in Section 4.10, where a discrepancy
cannot be attributed to a specific implementation change because the necessary
provenance was never recorded.

---

## 4.2 Baseline Validation

The baseline configuration, denoted A0, is the reference point for every
contrast in this chapter. Before any mechanism is evaluated against it, two
questions must be settled: whether A0 is a faithful realisation of the
published method it is derived from, and what its own behaviour is on each
scene. An efficiency result measured against an unfaithful baseline is
uninterpretable, and the archived campaign had previously been compromised in
exactly this way.

### 4.2.1 Equivalence to the Unmodified Reference

The unmodified upstream implementation was obtained, built and trained on the
same four scenes, with the same data preparation, the same evaluation
protocol and the same measurement code as every other configuration, and was
executed by the same worker. Twelve runs were produced. The comparison against
A0 was made against an equivalence margin fixed in the experiment
configuration before the reference implementation had been run: ±1.0 dB on
PSNR, ±0.02 on LPIPS, and ±30 % on final primitive count.

| Scene | ΔPSNR (dB) | ΔLPIPS | Δ count | Count margin used | Verdict |
|---|---:|---:|---:|---:|:--|
| Curaçao | +0.04 | −0.0001 | +242 953 | 20 % | Within margin |
| IUI3 Red Sea | −0.15 | +0.0005 | +262 899 | 31 % | Within margin |
| Japanese Gardens | +0.25 | −0.0067 | −583 914 | 74 % | Within margin |
| Panama | +0.12 | −0.0036 | +114 163 | 19 % | Within margin |

*Table 4.3 — Reference implementation minus baseline, per scene, against the
pre-registered equivalence margin. Positive ΔPSNR indicates the reference
scored higher. Source: §1.*

The two implementations are equivalent within the stated margin on all four
scenes. The largest fidelity discrepancy, 0.25 dB on Japanese Gardens, lies
inside that scene's own repeat dispersion and is therefore not resolvable as a
difference at all. The largest consumption of the count allowance, 74 % on the
same scene, occurs on the scene whose count dispersion is 34 %, and is
consistent with repeat variation rather than with a systematic divergence.

Two qualifications are required. First, the comparison is made between scene
means over repeats, not between matched seeds. The upstream implementation's
seed argument does not propagate to the stochastic operations that determine
its final population, so its three runs are repeat indices rather than
controlled seeds, and a paired comparison would imply a precision the design
does not possess. Second, a verdict of equivalence within a margin supports
the statement that the baseline is equivalent to the published method to
within that margin. It does not support the stronger statement that the
baseline reproduces the published method, which no finite sample can establish.

The result licenses the remainder of the chapter: differences measured against
A0 may be attributed to the mechanism under test rather than to a defect in
the baseline.

### 4.2.2 Baseline Reconstruction and Efficiency per Scene

| Scene | PSNR (dB) | SSIM | LPIPS | Primitives | Render rate (fps) | Training time (s) |
|---|---:|---:|---:|---:|---:|---:|
| Curaçao | 29.87 | 0.907 | 0.183 | 4 033 783 | 83.4 | 4 562 |
| IUI3 Red Sea | 27.65 | 0.869 | 0.208 | 2 814 411 | 152.2 | 3 324 |
| Japanese Gardens | 22.70 | 0.867 | 0.185 | 2 620 807 | 145.8 | 3 023 |
| Panama | 28.57 | 0.902 | 0.149 | 1 986 104 | 161.6 | 3 568 |

*Table 4.4 — Baseline reconstruction fidelity and efficiency, mean over three
repeats, per scene. Source: §2.*

The scenes differ substantially in difficulty. Baseline PSNR spans 7.17 dB
between Curaçao and Japanese Gardens, and the ordering of scenes by PSNR does
not match their ordering by perceptual similarity: Panama achieves the best
LPIPS of the four while ranking third by PSNR, and Japanese Gardens achieves
mid-range LPIPS while ranking last by PSNR by a wide margin. This divergence
between the two fidelity metrics is present in the baseline, before any
mechanism is applied, and it recurs throughout the chapter. It is the first
indication that the two metrics are not interchangeable summaries of
reconstruction quality in this domain.

The baseline's representation is large in absolute terms — between two and
four million primitives — and the scene requiring the most primitives is not
the scene that is hardest to reconstruct. Curaçao carries the largest
population and achieves the highest fidelity; Japanese Gardens carries a
comparable population and achieves the lowest. Population size is therefore
not a proxy for reconstruction difficulty, and the efficiency results that
follow are not simply a restatement of scene difficulty.

### 4.2.3 Baseline Representation Characteristics

Rendering-time inspection of the stored point clouds shows that a majority of
the baseline's primitives never contribute to any rendered view.

| Configuration | Curaçao | IUI3 Red Sea | Japanese Gardens | Panama |
|---|---:|---:|---:|---:|
| Baseline (A0) | 27 % | 40 % | 41 % | 36 % |
| Reference (SS), three repeats | 23–26 % | 29–43 % | 36–37 % | 26–37 % |

*Table 4.5 — Fraction of primitives exceeding the visibility threshold, seed 0
for the baseline and all three repeats for the reference. Source: §9.*

Between 59 % and 73 % of the baseline's primitives fall below the visibility
threshold. The unmodified reference implementation exhibits the same property
in the same range, which establishes that this is a characteristic of the
underlying optimiser and its densification schedule, not an artefact
introduced by this study's implementation. The observation has a direct
bearing on how the reductions in Sections 4.3 to 4.5 should be read: a
reduction of the total population by a factor of twenty is a reduction of the
*visible* population by a factor of approximately six, and the two are not the
same claim.

A second geometric observation is recorded for completeness. The ratio between
the full bounding box of the representation and the box containing its central
98 % of primitives reaches 313 on one repeat of the reference implementation,
indicating a small population of primitives detached far from the
reconstructed scene. As this occurs in the unmodified reference, the
detached-cluster pathology likewise belongs to the baseline optimiser. These
measurements are available for one repeat per configuration only, and are
reported as exploratory.

### 4.2.4 Baseline Medium Stability

The baseline jointly optimises the scene representation and nine scalar
parameters of a physical model of the water column. An attenuation
coefficient driven negative during optimisation is clamped and does not
recover; the model then ceases to be physically meaningful while continuing to
fit the observed images. The frequency of this outcome in the baseline is
therefore a precondition for attributing it to any mechanism.

Across the twelve baseline runs and the twelve reference runs — 24 runs in
total, spanning four scenes and two implementations — no run lost an
attenuation channel (§5a). The baseline and its reference are stable in this
respect. Any subsequent loss of a channel is therefore attributable to the
configuration in which it occurs, and Section 4.7 examines the configurations
in which it occurs at a substantial rate.
