# Supervisory Review II — the methodology corpus and the results to date

*The instrument of `07-supervisor-persona.md` applied to all of
`combined-method-methodology/` (26 files) and to the measured results of A0–A3 complete, A4
complete, A5 partial, A6 at n=1. `08-supervisory-review.md` examined whether the central
argument holds. This asks a different question: whether the **design** can answer what it was
built to answer, and whether the reporting does what the corpus says it does.*

*Two findings here are arithmetic rather than judgement, and both are computable from data
already on disk. Neither required another run.*

---

## 1. Verdict

The corpus is unusually disciplined and one of its central research questions is, on present
evidence, **unanswerable as designed** — not because the experiments are wrong but because the
sample size was fixed before the outcome variance was known, and the variance turned out to be
large. §4 gives the numbers. The finding is constructive: RQ2 remains answerable on two of its
three metrics, and knowing which one before spending the remaining 48 runs is worth more than
the runs.

The second finding, §3, is that the study's foundational claim is **underpowered rather than
merely narrow**. `08-supervisory-review` §7 recorded R-5 as "partial, n=3, Curasao only". That
understated it: at n=3 per side on a quantity with the measured dispersion, the comparison
cannot distinguish equivalence from a 24% difference.

---

## 2. What the instrument passes cleanly

Recorded first and in earnest, because the persona over-values negative results (§8) and a
review that opens with defects misrepresents this corpus.

**O-4 — "you are reporting the metric that agrees with you" — is answered better than most
published work in the area.** All three fidelity metrics are reported, and E.11 states outright
that LPIPS resolves what PSNR cannot and that *reporting PSNR alone would invert the
conclusion*. Volunteering the metric that contradicts your headline is rare.

**O-5 — "a fix in search of a problem" — is answered for every CD that claims one.** CD-6's
failure mode fired 12 of 12. CD-26's rejected 24% of all triangulations, 95% of all rejections.
CD-22/23's cost 6× in primitive count. Each is a measured occurrence, not a hypothetical.

**Question 3 — "method or implementation?" — is asked by the corpus of itself.** E.16 is
explicitly labelled *"a defect, not a finding"*. That distinction is the one students most often
fail to draw, and here it is drawn unprompted.

**The engineering is better than the thesis gives itself credit for.** Twelve verify suites,
81 acceptance checks, a ledger that survives its own file vanishing, instrumentation designed so
that its failure modes surface as suspicious numbers rather than silent nulls. The persona
under-weights this (§8); an examiner should not.

---

## 3. O-3 — the equivalence claim is underpowered, not merely narrow

Every number this study reports is a difference against A0. A0's standing therefore rests
entirely on A.3/E.5: *A0 is indistinguishable from unmodified SeaSplat*, established at 3+3
runs with a mean count ratio of 1.036.

**"Indistinguishable" is true. "Equivalent" does not follow, and the gap is wide.** A0's
per-scene coefficient of variation on converged count is 6.0–29.3% `[measured n=12]`. A ratio of
two means of three runs each therefore carries a 95% interval of:

| scene | A0 count CV | 95% CI on the A0/SS ratio |
|---|---:|---:|
| JapaneseGardens | 6.0% | ±9.6% |
| IUI3-RedSea | 9.6% | ±15.3% |
| **Curasao** — where the control actually ran | **14.7%** | **±23.5%** |
| Panama | 29.3% | ±46.9% |

So the observed 1.036 is consistent with A0 differing from vanilla SeaSplat by **up to roughly a
quarter** on the one scene tested. The test was designed to detect a difference and found none;
that is not the same as having shown there is none, and on a high-variance outcome at n=3 the
distinction is the whole matter.

Two aggravating details, both from reading `tools/replicate_baseline.py` rather than the claim:

- It extracts **primitive count only** — `final_count` parses `after=` out of densification
  logs. PSNR, SSIM and LPIPS were never compared between A0 and SS.
- It defaults to **16 000 iterations**, roughly half the campaign's training length.

A.3 currently reads *"A0 reproduces SeaSplat as published — Supported — and now demonstrated,
which the manuscript never did."* What was demonstrated is that the two reach comparable
primitive counts, on one scene, at half the training length, to within ±24%. That is a real
result and it is not the claim as written.

**What closes it.** S0's SS cell at 4 scenes × 3 seeds × 30 000 iterations with the full metric
set, which is already in the ledger (CD-30). But the design point stands independently: an
equivalence claim needs a **pre-specified margin** — "A0 and SS agree to within X% on count and
Y dB on PSNR" — stated before the runs, not a p-value afterwards. Without a margin, more runs
narrow the interval without ever licensing the word *equivalent*.

---

## 4. Question 1 applied to RQ2 — the design cannot answer it on PSNR

> *"Compared to what, measured how many times?"*

RQ2 asks whether the mechanisms compose additively or interact. A two-way interaction is
`A6 − A2 − A3 + A0`: four cell means, so its variance is about four times that of a single mean
and its standard error about twice as large. At three seeds per cell, using A0's measured
per-scene dispersion as the noise floor:

| metric | interaction resolvable at 2 SE | for scale, M2's **main** effect |
|---|---:|---:|
| **PSNR (pooled)** | **0.51 – 1.61 dB** | 0.21 dB |
| **LPIPS** | **0.0064 – 0.0235** | 0.0482 |

**On PSNR the design is not underpowered, it is inert.** The smallest interaction it could
resolve is 0.51 dB on the best-behaved scene and 1.61 dB on the worst — two to eight times
larger than the *main* effect of the mechanism whose interaction is being sought. Interactions
are generally smaller than the main effects they modify. No plausible M2×M3 interaction on PSNR
is detectable at three seeds, on any scene in this corpus.

**On LPIPS it works.** The resolvable interaction is 13–49% of M2's main effect, so a
sub-additive effect of even moderate size would clear the floor. This is the same asymmetry
E.11 and E.21 already found for the main effects — M2 and M1 are separable only under a
perceptual metric — extended to the interaction terms, where it matters more.

§12.6.3 anticipated the direction of this: *"an interaction term may not clear the noise floor
even after all 108 runs. If it does not, the honest report is UNDETERMINED."* That was right and
it was left qualitative. **The quantity was computable from S1 alone, before S2 ran.** It is
computable now, before the remaining 48 runs.

What follows is not that S4 and S5 are wasted. It is that:

1. **RQ2 must be adjudicated on LPIPS and on count, and PSNR reported as `UNDETERMINED` by
   construction** — a statement about the design's resolution, not about the mechanisms. Stating
   that in advance converts an embarrassment into a methodological result.
2. **A PSNR interaction reported as "no interaction detected" would be false precision.** The
   design cannot distinguish a null from a 1 dB effect on Curasao or Panama.
3. If a PSNR interaction is genuinely wanted, the fix is seeds, not cells: resolution improves
   as √n, so halving the detectable effect costs four times the seeds. That is 4× the campaign,
   which is the honest price and almost certainly not worth paying for one contrast.

---

## 5. O-2 — A2's bimodality is recorded but not acted on

> *"That is an average over things you have shown to be different."*

Six of A2's twelve runs have a permanently dead attenuation channel. The corpus knows this,
carries it as a covariate, and surfaces it before every contrast. **Then it reports a single mean
and standard deviation per scene anyway.** A mean over a two-population mixture is not made
correct by a footnote naming the mixture.

The right treatment is to report the collapsed and intact subpopulations separately wherever the
cell is used, or to condition on collapse and report both strata. At 2/3 and 2/3 on Curasao and
Panama the strata are large enough to be worth showing.

**And the variance carries a finding the corpus has not claimed.** If collapse changed
reconstruction quality, A2's within-scene PSNR dispersion would be inflated relative to A0's.
It is not — A2's PSNR sd is *smaller* than A0's on three of four scenes (Curasao 0.22 against
0.70, Panama 0.10 against 0.62), with two of three runs collapsed on both.

So the collapsed and intact runs have PSNR within roughly 0.2 dB of each other. **E.7 is
currently `[measured n=1, decisive]`** — one run with the campaign's best PSNR and two dead
channels. The variance argument makes the same point at **n=12**: a mixture of physically
different models, half with a broken medium, is statistically indistinguishable under PSNR.
That is a stronger form of the study's most quotable claim and it is sitting unclaimed in a
column of standard deviations.

---

## 6. O-6 — state the geometric metric's history

> *"You found this because you were looking for it. What were you not looking for?"*

The spatial-extent protocol was motivated by an observation in a viewer, then hypothesised to
correlate with medium perturbation, then measured at **ρ = −0.40 — the wrong sign** (E.17),
then justified on different grounds: that it detects failure modes directly.

Every step of that is legitimate and the negative result is reported, which is to the project's
credit. But the *final* justification was constructed after the *original* one failed, and
`chapter/06` now presents only the final one. An examiner who reads E.17 will reconstruct the
sequence and ask why the chapter does not.

The fix is a sentence, not a study: say that the measure was introduced as a candidate proxy,
that the proxy hypothesis was tested and failed, and that what survives is the direct
detection. A reader who is told the history trusts the surviving claim more, not less.

---

## 7. A confirmation the corpus has measured and not claimed

E.20 — *it is the population discontinuity, not the population size* — rests on A1 (~230k, 0 of
10 collapsed) against A2 (~145k, 6 of 12). That contrast **confounds count with mechanism**: A1
has fewer collapses *and* a different mechanism *and* a higher count, so size is not isolated.

A4 partially deconfounds it, and A4 is complete. On Curasao, A4 converges to **129 473**
primitives — *below* A2's 147 032 on the same scene — with **0 of 3 collapsed** against A2's
2 of 3. Lower count, same simplification events, opposite outcome.

That is a direct strike against the size explanation and it is stronger than the contrast E.20
currently cites. It should be in the claim, and it costs nothing to add.

---

## 8. Corrections to apply to this review

Per the persona's own failure modes, applied to what is written above.

- **Over-valuing negative results.** §§3–6 are all defects. §2 and §7 are not, and §4's
  conclusion is that 48 queued runs remain worth running on the right metric. Weight
  accordingly.
- **Under-weighting engineering contribution.** The instrumentation in this project repeatedly
  caught its own failure modes — the cache trap, the decoder equality, the silent no-op on
  mechanism D. That is a methodological contribution in its own right and the thesis
  under-claims it.
- **Inverse-problems framing crowding out simpler explanations.** §4 is ordinary statistical
  power, not identifiability. It would have been found by anyone who multiplied a standard
  error by two, and the fact that it was not found for 65 runs is the point.
- **Slow to let a student stop.** Nothing in §§3–7 requires new experiments. §3 needs S0, which
  is already queued; §§4–7 are analysis and writing.

---

## 9. Actions

1. **Declare RQ2's resolution before S4 resumes.** State that PSNR interactions are
   `UNDETERMINED` by design at n=3, with the 0.51–1.61 dB figure, and that RQ2 is adjudicated on
   LPIPS and count. No compute. Highest value item here.
2. **Restate A.3 to what was measured** — count only, 16 000 iterations, one scene, ±24% — and
   set a pre-specified equivalence margin for S0's SS cell before it runs.
3. **Report A2 by collapse stratum**, and claim E.7 at n=12 from the variance argument in §5.
4. **Add A4's Curasao contrast to E.20** — 129 473 primitives, 0 of 3, below A2's count.
5. **Add one sentence to `chapter/06` §3.7.4** giving the geometric metric's history.

Items 1, 3, 4 and 5 are writing. Item 2 is writing plus a decision that must precede S0.
