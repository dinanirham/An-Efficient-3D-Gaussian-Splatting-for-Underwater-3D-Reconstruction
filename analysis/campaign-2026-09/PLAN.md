# Analysis plan — campaign 2026-09

*Written before the bundle is opened. The only campaign-2026-09 results seen at the time of
writing are the `check_margin` verdict (§1 below, already known: all four scenes WITHIN
MARGIN) and the fact that the 48 M2 diagnostics files are complete. No number from
`results_runs.csv`, `analysis_*.json`, `medium_collapse.json`, `spatial_extent.csv` or
`j_consistency.json` has been read. Old-campaign figures are cited as priors only and are
labelled as such.*

*Every item below is marked **PRE** (the prediction and its falsification condition were
written down before this campaign ran, with a citation to where) or **EXP** (exploratory:
reported, but not claimed as a test of anything). A **PRE** item that fails is reported as a
failure. An **EXP** item that looks good does not get promoted.*

---

## 0. Rules that apply to every section

**Unit of analysis.** Scene. Four blocks, three repeats each. No headline is a mean over
scenes; a scene mean may appear as a *last* column for continuity with the sources' convention,
never as the number a claim rests on. `[10-reproducibility §10.6 item 14b]`

**Noise floor.** A0's per-scene standard deviation over its three repeats, for the metric in
question, from *this* campaign. The old campaign's values (PSNR sd 0.22–0.70 dB; LPIPS
0.003–0.010; count CV 6–29%) are the prior; the new ones supersede them the moment they are
read.

**Resolvable.** An effect is resolved when |effect| ≥ 2 × SE, SE pooled from the cells involved.
A main effect is a difference of two means (SE ≈ √2 × single-mean SE). A two-way interaction is
a difference of four means (SE ≈ 2 × single-mean SE). The three-way term is eight means
(SE ≈ 2√2 × single-mean SE). An effect below that is reported as `UNRESOLVED`, not as zero and
not as absent — the two are different findings and the distinction survives into the text.
`[08-computational-profile §8.4]`

**Covariate.** Every M2 cell (A2, A4, A6, A7) is reported by collapse stratum wherever it
appears in a contrast. A mean over a mixture of intact and collapsed models is not made correct
by a footnote naming the mixture. `[09-supervisory-review-ii §5]`

**Multiplicity.** The pre-registered contrasts are enumerated in §§1–7 and number fewer than
twenty. Everything in §§8–14 is exploratory. No correction is applied to the pre-registered
set; the exploratory set is labelled and its size stated.

**Two campaigns.** The archived 74-run campaign is comparable (CD-27 is trajectory-neutral;
CD-26 touched only M1 cells, which were re-run). It is used in exactly one place — §11, as an
independent replication check on the main effects — and nowhere else.

---

## 1. Baseline replication — **PRE, already read**

**Question.** Is A0 the method it claims to reimplement?
**Data.** `check_margin.txt`.
**Registered.** PSNR ±1.0 dB, LPIPS ±0.02, count ±30%; scene means over repeats; fixed in
`configs/cells.json` before S0 ran. `[10-reproducibility item 14g]`
**Falsifies if.** Any scene OUTSIDE MARGIN on any metric.
**Result, known.** WITHIN on all four. Largest PSNR gap 0.245 dB, largest LPIPS gap 0.0067 —
both inside A0's own noise floor. Count within, JapaneseGardens at 74% of margin.
**Wording permitted.** *Equivalent to within the stated margin.* Not *reproduces*.
**Chapter 4 §1.**

## 2. Main effects — **PRE**

**Question.** Does each mechanism move its own target cost beyond seed dispersion? (H1)
**Data.** `analysis_unweighted.json`, `results_by_scene.csv`.
**Contrasts, per scene.** A1−A0 (M1), A2−A0 (M2), A3−A0 (M3). Both inference directions:
also A7−A6 (M1 from above), A7−A5 (M2), A7−A4 (M3).
**Metrics.** Each mechanism's *target*: M1 → training cost and count; M2 → count and
fps; M3 → bytes per primitive. Plus all three fidelity metrics for each, because reporting only
the one that moved is O-4.
**Registered directional priors.** M2: ~19× count reduction, LPIPS worse on all four scenes
`[results-01]`. M1: fidelity at or above A0 on three scenes, Panama unsettled `[results-03]`.
M3: ~2.7× bytes/primitive, fps unchanged `[08 §8.3b]`. These are old-campaign numbers and
are what the new campaign either replicates or does not.
**Falsifies if.** A mechanism's target-cost effect is below 2 SE on the majority of scenes.
**Chapter 4 §§2–3.**

## 3. Two-way interactions — **PRE, on LPIPS and count only**

**Question.** Do the mechanisms compose additively? (RQ2)
**Data.** `analysis_unweighted.json`.
**Contrasts.** A4−A1−A2+A0 (M1×M2), A5−A1−A3+A0 (M1×M3), A6−A2−A3+A0 (M2×M3). Additive on
fidelity, multiplicative (log) on count, size, fps. `[08 §8.4]`
**Registered predictions.** `[08 §8.4, written before S4]`
- M2×M3 **sub-additive on quality** — H3, OMG's premise.
- M1×M2 **degenerate or sub-additive on count** — H5; degenerate only if the budget failed to
  bind, which preflight prevents, so sub-additive is the live prediction.
- M1×M3 **approximately additive** — the least-coupled pair.
**Metric rule, registered.** Adjudicated on **LPIPS and count**. PSNR interactions are reported
as `UNDETERMINED` **by construction**: the smallest resolvable PSNR interaction at n=3 is
0.51–1.61 dB against a 0.21 dB main effect. `[09-supervisory-review-ii §4; 08 §8.4]` This is
stated in the design and is not an excuse arrived at after seeing the data.
**Falsifies if.** M2×M3 super-additive or null on LPIPS at ≥2 SE; M1×M3 resolved in either
direction at ≥2 SE.
**Chapter 4 §4.**

## 4. Three-way interaction — **PRE, no directional prediction**

**Contrast.** A7−A6−A5−A4+A3+A2+A1−A0, on LPIPS and count. `[08 §8.4: "unpredicted"]`
**Reported as.** Resolved with sign, or `UNRESOLVED`. No interpretation is offered beyond that
unless the term clears 2 SE, in which case the interpretation is written *after* the sign is
known and labelled as such.
**Chapter 4 §5.**

## 5. The central hypothesis — **PRE, the decisive test**

**Question.** Does primitive reduction perturb medium identifiability, and *why*? (H4, RQ3)

**5a. The collapse itself.**
**Data.** `medium_collapse.json`, all 120.
**Registered.** A0: 0 of 12 lose a channel (prior, old campaign). A2: every run's largest
attenuation drop lands on a simplification boundary; ~6 of 12 collapse outright, seed-conditioned
`[E.2, results-01]`.
**Falsifies if.** Any A0 or SS run collapses; or A2's drops are not boundary-aligned.

**5b. The mechanism — the dispersion prediction.**
**Data.** `medium_collapse.json` (`zr_cv_ratio` per boundary per run) and the 48 M2 diagnostics.
**Registered.** *Collapse at a simplification event is governed by the change in cross-frame
dispersion of the depth range across that event — not by primitive count, not by count ratio,
not by mean depth range. A distribution that merely translates leaves β's compromise
attainable; one that broadens does not.* `[06-implementation-deltas §6.9; 08-supervisory-review
§4; the tool prints this]`
**Test.** Within each M2 cell, per scene: does `cv_after / cv_before` at the first event
separate runs that collapsed from runs that did not? Reported as the two strata's ratio
distributions and a rank statistic (Mann–Whitney, n small, reported as U and the exact
one-sided p; no claim of significance below n=6 per stratum).
**Falsifies if.** The ratio does not separate the strata — in which case **the identifiability
account of `08-supervisory-review` §2 is withdrawn rather than qualified**, and CD-6's failure
returns to "unexplained". This is the one item in the plan whose failure changes the thesis's
central claim, and that is why its falsification is written here in full.
**Prior, one run only.** A6/Curasao/s0, old campaign: ratio 1.141 at the 19.8× cut, β moved
58–87%; ratio 1.001 at the 1.34× cut, β moved 6–15%. One run. Not evidence; direction only.

**5c. M1 protects — and the mechanism says why.**
**Registered.** A4 and A7 (M1 + M2): dispersion ratio ≈ 1 and collapse rate near zero, because
dense initialisation keeps per-frame ranges uniform so the distribution translates rather than
broadens. `[08-supervisory-review §3.1]` Prior: A4/Curasao 0 of 3, old campaign.
**Falsifies if.** A4 or A7 collapse at A2's rate, or their ratios spread like A2's.

**5d. Size versus discontinuity.**
**Registered.** A4 converges *below* A2's count with the same events and does not collapse
(E.20, deconfounded). `[09-supervisory-review-ii §7]`
**Test.** Per scene, A4 count vs A2 count, A4 collapse rate vs A2's.

**5e. CD-6.**
**Registered.** The burst does not restore β; `rewarm_end` carries identical `zr_*` to
`post_simp` because geometry is frozen. `[E.6; 06 §6.9]`
**Reported as.** Negative result about this work's own remedy, with the derivation of why.

**Chapter 4 §§9–10.**

## 6. Mechanism D — **PRE**

**Question.** Does detaching alpha-loss gradients from density control give a large count
reduction at a small fidelity cost? (E.4)
**Data.** A0D vs A0, per scene.
**Registered.** Prior figure ~6× fewer primitives at −0.107 dB, from n=1 against a *defective*
baseline; explicitly not claimable until S6. `[12-novelty-defensibility §12.6.2]`
**Prediction, written before A0D ran.** *The count effect will resolve; the PSNR effect will
not.* A −0.1 dB difference sits at a fifth of A0's noise floor. `[my note at S6 launch]`
**What may be claimed.** The count reduction, with its resolution. The PSNR difference as
`UNRESOLVED at n=3`, never as a point estimate. LPIPS is the metric that might resolve it and
is reported alongside.
**Falsifies if.** Count reduction below 2 SE on the majority of scenes — then E.4 is dead and
the thesis has no positive engineering result.
**Chapter 4 §2 (as a supplementary contrast, never differenced with the factorial).**

## 7. Rate–distortion and Pareto — **NOT SUPPORTED BY DESIGN**

One operating point per mechanism. A Pareto *front* over the nine cells (fidelity vs count,
fidelity vs bytes) is drawn, per scene, as a description. No curve within a mechanism is drawn,
no claim about ranking persistence across budgets is made, and R3.4 remains unanswered. `[D-9;
04-repositioning §4.3]`
**Chapter 4 §§6–7, stated as such.**

---

## 8. Fidelity metrics cannot see collapse — **EXP → confirmatory at scale**

**Registered in form, not in number.** E.7 at n=12 (old campaign): collapsed and intact A2
strata within 0.4 sd on 7 of 8 comparisons, sign inconsistent. `[09-supervisory-review-ii §5]`
**Now.** The same stratification on every M2 cell — up to 48 runs — on PSNR and LPIPS.
**Reported as.** The within-scene stratum differences in units of A0's sd. If they stay below
~1 sd with inconsistent sign, E.7 holds at the campaign's full size.

## 9. Geometric pathology — **EXP**

**Data.** `spatial_extent.csv`, seed-0 runs (the only ones with a PLY).
**Prior.** A0's box 96–99.96% empty; two mechanisms (detached clusters, invisible halo); A2
clean. `[results-02]`
**Rule.** Reported as a direct detector of failure modes. **Never as a proxy for medium
health** — E.17, ρ = −0.40, wrong sign. No correlation between geometry and β is computed or
reported.

## 10. Ĵ self-consistency — **EXP, n=1 per scene**

**Data.** `j_consistency.json`, 16 runs (seed 0 only; the PLY is not kept for seeds 1–2).
**Prior.** None. Predicted range high-30s to 40s dB; a value at 100 dB is a bug, not a result.
**Reported as.** Secondary. Consistency, not accuracy. Never in a headline.

## 11. Replication across campaigns — **EXP**

The old 74-run campaign is comparable. For A0, A1, A2, A3 (12 runs each in both), the per-scene
means are compared. Agreement within noise is a replication; disagreement beyond it is a finding
to be explained, not suppressed.

## 12. Computational cost — **EXP**

Wall-clock, effective steps, fps, peak render memory, per cell per scene. Sub-linear fps in
count reduction, with the exponent differing by cell `[E.9]`. Instrumented runs carry ~3 s of
sweep time; the archived campaign's A6/Curasao/s0 carries ~75 s, and is not in this bundle.

## 13. Related work — **BLOCKED**

The numbers exist; the six literature breakdowns do not. Chapter 2's blocker, unchanged.

## 14. Limitations and anomalies — **the section written last**

Every `UNRESOLVED`, every scene that disagrees with the others, every stratum that is too small
to say anything about. THESIS.md: *treat inconsistent scenes as evidence requiring explanation*.

---

## What would change the thesis

Ranked by consequence.

1. **§5b fails** — the dispersion ratio does not separate collapsed from intact. The
   identifiability account is withdrawn. The thesis reverts to Framing A as approved: a
   controlled factorial study with a measured coupling and an unexplained failed remedy.
2. **§6 fails** — A0D's count effect does not resolve. No positive engineering result. The
   thesis is a negative characterisation of a published estimator, and is written as one.
3. **§5c fails** — M1 cells collapse like A2. The "discontinuity not size" claim (E.20) is
   weakened and the M1-protection mechanism is wrong.
4. **§3's M2×M3 is null on LPIPS** — H3 fails; OMG's premise does not transfer. Reportable.
5. **§1 had failed** — it did not. Recorded here because it was the one that mattered most.

Nothing on this list is bad for the thesis if it is reported as it falls. What would be bad is
any of them being reported as something other than what it is.
