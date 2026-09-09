# Reviewer-Feedback Traceability Matrix

SIGGRAPH Asia 2026, submission `tcom_126` (Technical Communications), *Efficiency–Fidelity
Tradeoffs in Compact 3D Gaussian Splatting for Underwater Scene Reconstruction*, Dinan &
Kusuma. **Decision: Reject.** Ratings −1 / −1 / −1 / +1, average −0.5, meta-review −1.

Reviews were recovered from a page-image PDF with no text layer (§0.2). Quotations below are
transcribed from the rendered pages.

**A rewritten explanation does not resolve a request for evidence.** Each row states what the
new work actually supplies, and where it does not, says so.

---

## R1 — Borderline Reject (−1)

> *"This work reports a combination of 3 computational techniques (EDSG dense deterministic
> initialisation, mini-Splatting importance-based budget pruning, and CompGS-style
> post-training attribute quantisation) to make balance between storage/computation and
> fidelity, with the envisaged usage in autonomous underwater vehicles."*

| # | Concern (verbatim) | Class | Underlying issue | New-framework response | Evidence available | Evidence missing | Revise |
|---|---|---|---|---|---|---|---|
| R1.1 | *"It is very specialised and narrow topic, and the context and background seems largely missing making it difficult to understand."* | Writing / framing | The paper assumed a reader inside the subfield | **Does not resolve — writing work.** A thesis has room a 4-page TC does not, but the same failure would recur if Ch. 2 opens at SeaSplat | Ch. 2 material exists across 9 method breakdowns | A narrative path from multi-view geometry → NeRF → 3DGS → underwater formation → efficiency | **Ch. 2 §2.1–2.5, Ch. 1 background** |
| R1.2 | *"Overall the context and background is minimal — very difficult for those not in this specific field to understand what the state-of-the-art is and what the study is attempting."* | Framing | No stated state of the art | Partially — the taxonomy exists but was never written out | `01-taxonomy.md` §4 | An explicit SOTA positioning table | **Ch. 2 §2.6, Ch. 1 gap** |
| R1.3 | *"There are some awkward and strange expressions and phrases throughout the paper (e.g. 'all three mechanisms leave submodules untouched by construction')."* | Writing | Repository shorthand leaked into prose | Resolvable | — | — | **All chapters — style pass** |
| R1.4 | *"Fig 1: it is not sufficient to just show those 4 photos and what they are, but there should be explanations of what to notice and what to compare between those photos."* | Figures | Qualitative figures without a reading instruction | Resolvable, and stronger now: crops can be tied to measured Ẑ/β diagnostics | CD-12 diagnostics per run | Figures not yet produced | **Ch. 4 figures** |
| R1.5 | *"Fig 2: some were labelled in the chart and some were not."* | Figures | Inconsistent labelling | Resolvable | — | — | **Ch. 4 figures** |

**Note.** R1 states *"References are relevant, and results reproducible."* — the only
favourable reproducibility judgement in the set, and it should not be over-read: R3 reached the
opposite conclusion on the same submission.

---

## R2 — Borderline Reject (−1)

> *"This paper presents a controlled study of transferring three existing 3DGS efficiency
> mechanisms to physics-aware underwater reconstruction with SeaSplat. The experiments show
> different efficiency–fidelity tradeoffs, with importance-based pruning achieving the best
> overall balance."*

| # | Concern | Class | Underlying issue | New-framework response | Evidence available | Evidence missing | Revise |
|---|---|---|---|---|---|---|---|
| R2.1 | *"My main concern is the limited technical and analytical contribution. The work mainly transfers and evaluates existing 3DGS efficiency mechanisms in an underwater setting."* | Novelty | The contribution was framed as a method, delivered as a comparison | **Partially resolves.** Two genuine technical contributions now exist that did not before: the Ẑ-rescale/medium-identifiability analysis with its CD-6 remedy, and the gradient-destination finding (D-3). Both are about *composition*, not about a new compression algorithm | `05-constraints.md` §5.4, §5.6; `12-novelty-defensibility.md` §12.6 | The CD-6 remedy is implemented but **its effect is unmeasured** — it needs A2's diagnostics | **Ch. 1 contributions, Ch. 3 §3.4, Ch. 5** |
| R2.2 | *"the paper provides limited investigation into why these behaviors occur"* | Mechanistic explanation | Results reported without mechanism | **Resolves, and this is the strongest response available.** The whole CD-22/CD-23 investigation is a worked example of establishing *why* — four hypotheses, three refuted by measurement | `13-campaign-addendum.md` §13.2; per-event densification instrumentation | Applied to M1/M2/M3, not yet to their interactions | **Ch. 4 — restructure around mechanism, not around cells** |
| R2.3 | *"A deeper analysis connecting underwater characteristics such as scattering, low contrast, or geometric uncertainty to the behavior of different compression mechanisms would make the empirical findings more insightful and generalizable."* | Mechanistic / methodology | No underwater-conditioned analysis | **Partially.** The instrument exists — CD-12 logs Ẑ_min/Ẑ_max and all nine medium scalars every 500 iterations — and the hypothesis is stated (D-2 injected by pruning). It has not been evaluated | `diagnostics.csv` per run, all cells | S2 must complete; needs A2-vs-A0 β-drift analysis | **Ch. 3 §3.7 diagnostics, Ch. 4 §4.x new section** |

---

## R3 — Borderline Reject (−1) · the most technically specific review

> *"The paper asks a practical question, and I like the attempt to separate initialization,
> population reduction, and attribute compression within a common underwater pipeline… I also
> appreciate that the authors are explicit that the contribution is a controlled comparison
> rather than a new method."*

| # | Concern | Class | Underlying issue | New-framework response | Evidence available | Evidence missing | Revise |
|---|---|---|---|---|---|---|---|
| R3.1 | *"related-work coverage and experimental design omit several major compression families, including rate-distortion optimization, entropy coding, adaptive attribute pruning, and structured representations"* | Related work | Narrow comparison set | **Does not resolve — D-8.** The repository has the same gap: no breakdown for EAGLES, LightGaussian, ReSplat, WaterSplatting, Aquatic-GS, Gaussian Splashing | `CompGS` (entropy/predictive) and `OMG` analysed | Six method breakdowns | **Ch. 2 §2.5 — expand substantially** |
| R3.2 | *"Reproduction would also require the missing hardware and timing protocol, implementation details, per-scene results, and information about repeated runs."* | Reproducibility | Four specific omissions | **Fully resolves — all four.** `run_config.json` records GPU, driver, torch/CUDA, git SHA, full argv; timing protocol is defined and documented; per-scene results are the reporting unit; three seeds with dispersion | `10-reproducibility.md`; `utils/preflight.py`; S1's per-scene table | — | **Ch. 3 §3.8, Ch. 4 per-scene tables** |
| R3.3 | *"the study is not comprehensive enough to support its mechanism-selection conclusions"* | Framing | Conclusions exceeded the design | **Resolves by repositioning, not by evidence.** The conclusion must become an interaction claim, not a selection guide — see `04-repositioning.md` | 2³ factorial with both directions of inference | S2–S5 | **Ch. 1 RQs, Ch. 5 conclusions** |
| R3.4 | *"Each selected mechanism is also represented by essentially one operating point, so Fig 2 does not establish a Pareto surface or show that the ranking persists across budgets."* | Experimental design | No rate–distortion sweep | **Does not resolve — D-9.** The current design also has one `n_bud` and one `k` | — | A budget sweep — **the single highest-value additional experiment** | **Ch. 3 §3.6, Ch. 4 rate–distortion section** |
| R3.5 | *"The study uses only one SeaSplat formulation and four scenes"* | External validity | Small benchmark | **Does not resolve.** Four scenes is the whole public corpus | — | Nothing tractable; must be a stated limitation | **Ch. 1 scope, Ch. 5 validity** |
| R3.6 | *"A3 is applied to a separately trained model rather than the identical A0 checkpoint, which confounds its small quality difference."* | Baseline / control | Confounded comparison | **Resolves, but by a different route than the reviewer suggests.** Sharing a checkpoint would test *post-hoc* quantization; CompGS-VQ is quantization-aware, so its run is necessarily separate (D-2). The confound is real and the correct answer is dispersion — now measured at 6–29% (D-5) | S1 dispersion; quantization-aware implementation | A3 runs (S3) | **Ch. 3 §3.5.4, Ch. 4 §4.5** |
| R3.7 | *"Since the paper does not contribute a new method, the comparison itself needs to be broader and more carefully controlled."* | Framing | Sets the bar for a comparison paper | **Partially.** Control is much stronger (preflight, factorial, seeds, verified baseline); breadth is not — see R3.1, R3.4 | — | Budget sweep + broader related work | **Ch. 3, Ch. 2** |

---

## R4 — Borderline Accept (+1)

| # | Concern | Class | New-framework response | Revise |
|---|---|---|---|---|
| R4.1 | *"Fig 1 is labeled A,B,C,D and then corresponds to A0, A2, A3… which is confusing to map and read."* | Figures | Resolvable — label panels by cell ID directly | **Ch. 4 figures** |
| R4.2 | *"Similarly Fig 2 could put the legends nearer the datapoints instead of having them separate."* | Figures | Resolvable | **Ch. 4 figures** |
| R4.3 | *"Given the small size of the dataset (4 scenes), it is unclear how generalizable the results are, but… This limitation is clearly written and acknowledged."* | External validity | Retain the acknowledgement; strengthen with per-scene heterogeneity (D-5) — the scenes differ by 5× in dispersion, which is itself evidence against pooling | **Ch. 1 scope, Ch. 4, Ch. 5** |

---

## Meta-Review — Borderline Reject (−1)

> *"Both reviewers acknowledge that the paper presents a controlled evaluation of three
> existing 3DGS efficiency techniques for underwater reconstruction and provides reproducible
> experimental results. However, both lean toward rejection, primarily due to the limited
> contribution beyond transferring existing techniques. The reviewers also identify
> insufficient analysis and contextualization of the experimental findings."*

> *"The study is relevant and provides useful empirical results, with importance-based pruning
> showing a favorable efficiency–fidelity tradeoff. However, the contribution is primarily an
> evaluation of existing techniques in an underwater setting. The reviewers particularly note
> the limited analysis of why these methods behave differently under underwater conditions.
> Stronger contextualization, deeper analysis of the observed behaviors, and clearer
> presentation of the experimental results would strengthen the contribution."*

Three demands, in the meta-reviewer's own order of emphasis:

| | Demand | Status |
|---|---|---|
| M.1 | **Contribution beyond transfer** | Partially resolved. Two composition-level findings now exist (R2.1). Neither is a new compression algorithm, and the thesis should stop implying one. |
| M.2 | **Why the methods behave differently underwater** | Instrumented but unevaluated. This is the highest-value analysis the remaining runs can produce. |
| M.3 | **Clearer presentation** | Writing work throughout. |

**A caution.** The meta-review credits *"importance-based pruning showing a favorable
efficiency–fidelity tradeoff"* — the finding D-1 shows was produced by a mechanism that was
not Mini-Splatting, and D-5 shows was reported without the dispersion needed to interpret it.
**That specific result cannot be carried forward as-is**, even though it is the one the
reviewers found most persuasive.

---

## Aggregate

| Class | Concerns | Fully resolved | Partially | Not resolved |
|---|---:|---:|---:|---:|
| Writing / framing | 5 | 0 | 2 | 3 |
| Figures | 4 | 4 | 0 | 0 |
| Reproducibility | 1 | 1 | 0 | 0 |
| Mechanistic explanation | 2 | 1 | 1 | 0 |
| Experimental design | 3 | 0 | 1 | 2 |
| Novelty / contribution | 2 | 0 | 2 | 0 |
| External validity | 2 | 0 | 1 | 1 |
| **Total** | **19** | **6** | **7** | **6** |

**The six unresolved concerns are not distributed evenly.** Five of them (R1.1, R1.2, R3.1,
R3.3, R3.5, R3.7) are *writing and positioning*; exactly **one** — R3.4, the missing
rate–distortion sweep — requires additional computation.

That ratio is the central finding of this audit and it drives `04-repositioning.md`: the
rejection was mostly not about the experiments.
