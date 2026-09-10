# Claim-Validity Ledger

Every substantive claim in the current manuscript, classified per the brief:
*Supported* · *Partially supported* · *Contradicted* · *Obsolete* · *Not yet tested* ·
*Methodologically untestable with the current design*.

Claims are quoted or paraphrased from the manuscript (153 pp., 2026-05-22) and the SIGGRAPH
submission.

---

## A. Baseline claims

| # | Claim | Verdict | Basis |
|---|---|---|---|
| A.1 | Physics-aware underwater 3DGS is feasible and achieves real-time rendering | **Supported** | Independently reproduced. Current A0: 69.2 fps at 4.29M primitives, Curasao `[measured n=1]` |
| A.2 | The baseline is "representation-heavy" — ~2.86M primitives, ~194 MB | **Supported**, with D-4 caveat | Current median 2 482 200 across 12 runs; the two agree within dispersion (D-6). "194 MB" is a **PLY** figure and must be labelled as such |
| A.3 | A0 reproduces SeaSplat as published | **Supported** — and now *demonstrated*, which the manuscript never did | 3 runs each vs unmodified SeaSplat, overlapping ranges, mean ratio 1.036 `[measured n=3]` |
| A.4 | Curasao renders slower (30.84 fps) because of higher image resolution and screen-space density | **Not yet tested** | Plausible but unverified; the current implementation measures Curasao *fastest-loaded* at 69.2 fps under a defined protocol. D-7: the two figures are not comparable |

---

## B. Mechanism claims — the ones that must change

| # | Claim | Verdict | Basis |
|---|---|---|---|
| B.1 | **"Mini-Splatting importance-based budget pruning gives the best overall balance — ~72% reduction in model size and Gaussian count for a 0.05 dB average PSNR decrease"** | **Contradicted as attributed** | **D-1.** The implemented mechanism was `opacity × scale` with deterministic top-k, firing once. Mini-Splatting's method is accumulator-based importance with *stochastic* sampling at two iterations — and Mini-Splatting's own paper rejects top-k as destroying local geometry (S-4). The number may describe a real behaviour of *that* pruning rule; it is not evidence about Mini-Splatting |
| B.2 | The same, as a *magnitude* | **Contradicted** | **D-5.** 0.05 dB from single runs, against measured per-scene CV of 6–29% on primitive count. Not interpretable without dispersion |
| B.3 | "CompGS-style post-training attribute quantisation mainly reduces storage" | **Partially supported**, wrongly attributed | **D-2.** Post-hoc k-means at k=256 is the condition CompGS-VQ's C-1 identifies as the problem it solves. Direction is plausible; the mechanism is not CompGS-VQ |
| B.4 | "Deterministic initialization trades substantial quality for more aggressive compaction" | **Not yet tested** in the current codebase | Prior A1 used a different pipeline. Current M1 (RoMa + cheirality + hash-verified clouds) is implemented but unrun — S3 |
| B.5 | The three mechanisms are orthogonal / "leave submodules untouched by construction" | **Partially supported** | True of the medium *modules*; **false of the medium model's identifiability** — pruning rescales Ẑ and thereby β `[05-constraints.md §5.4]`. R1.3 also flags the phrasing |

---

## C. Efficiency and comparison claims

| # | Claim | Verdict | Basis |
|---|---|---|---|
| C.1 | Composite metrics PSNR/MB = 0.156 and FPS/MB = 0.269 establish the efficiency denominator | **Methodologically untestable as constructed** | Ratios of quantities with different units and different container conventions (D-4). A per-MB ratio inherits the PLY-vs-npy artifact. Replace with explicit rate–distortion reporting |
| C.2 | The comparison supports **mechanism-selection guidance** for underwater deployment | **Methodologically untestable with the current design** | **D-9 / R3.4.** One operating point per mechanism cannot establish a Pareto front or show ranking persistence across budgets. This holds for the *new* design too |
| C.3 | Compression is comparable to terrestrial published ratios | **Contradicted** | `sh_degree = 0` gives 14 floats/primitive, not 59. Ratios against CompGS-VQ's published 41–65× are a different quantity without renormalisation `[08-computational-profile.md §8.2]` |
| C.4 | Results generalise to underwater reconstruction broadly | **Not supported** | Four scenes, one formulation (R3.5, R4.3). Per-scene dispersion differs 5× (D-5), which argues against pooling, let alone extrapolating |

---

## D. Framing claims

| # | Claim | Verdict | Basis |
|---|---|---|---|
| D.1 | Intended use in **autonomous underwater vehicles** | **Not supported** | **D-10.** No deployment hardware, power, latency or embedded memory evaluated. Peak render memory is measured — on an A100 |
| D.2 | The work contributes an *efficient method* (thesis title) | **Contradicted by the work's own framing** | The SIGGRAPH title already says "tradeoffs". R2.1, R3.7 and the meta-review all read it as a comparison. See `04-repositioning.md` |
| D.3 | No underwater pruning/compression methods exist (implied by the gap statement) | **Not verified — and the brief flags it** | D-8: the literature was not surveyed for this. Must be checked before any such statement survives |

---

## E. Claims the *new* work can make that the manuscript does not

| # | Claim | Verdict | Basis |
|---|---|---|---|
| E.1 | An integration boundary can preserve every forward value and still change which gradients drive densification | **Supported** | **D-3.** Bracketed at three configurations; the fix verified to indistinguishability at n=3 `[05-constraints.md §5.6]` |
| E.2 | A scene-global medium model whose only spatial input is per-frame min–max-normalised depth is not invariant to primitive-count reduction | **Supported** `[measured n=12 + 12 control]` | **12 of 12** A2 runs have their largest attenuation drop on a simplification boundary (25–195%); **0 of 12** A0 runs lose a channel. The collapse is **bistable and seed-conditioned** — 6 of 12, across all four scenes `[§13.13]` |
| E.6 | CD-6's medium re-identification burst restores β after a population change | **Contradicted** `[measured n=12]` | The `rewarm_end` row *is* the post-burst state, and β is already collapsed in it. 200 steps did not restore it in any of the six collapsed runs. A negative result about this work's own remedy `[§13.10, §13.13]` |
| E.7 | Fidelity metrics cannot certify that the medium model is intact | **Supported** `[measured n=1, decisive]` | `A1/Curasao/s0` produced the campaign's **best test PSNR (30.97, above A0's 30.48)** with **two of three attenuation channels permanently dead**. PSNR, SSIM and LPIPS score the composed image, which a saturated backscatter term still fits `[§13.12, §13.13]` |
| E.8 | M1 does not cost fidelity at 14× fewer primitives | **Not yet tested** `[measured n=1]` | A1/Curasao/s0 is **+0.49 dB test, +1.34 dB train** against A0 at 299,196 vs 4,285,043 primitives. Better on both splits. Against A0's 14.7% CV on this scene, one run is not evidence — needs S3's remaining eleven |
| E.9 | Frame-rate gain is sub-linear in primitive reduction, and not a single exponent | **Supported** `[measured n=1/cell]` | A1: 14.3× fewer → **1.48×** fps. A2: 29.7× fewer → **4.27×**. Per-primitive rasterization cost differs by cell, so a count ratio does not predict a frame-rate ratio `[§13.12]` |
| E.3 | Converged primitive count carries 6–29% run-to-run dispersion, seeding notwithstanding | **Supported** | 12 A0 runs + 3+3 replication `[measured n=3/scene]` |
| E.4 | Detaching alpha gradients from densification yields ~6× fewer primitives at ~−0.1 dB | **Not yet tested** | `[measured n=1]` against a *defective* baseline, different seeds. Not claimable until S6 `[12-novelty-defensibility.md §12.6.2]` |
| E.5 | A0 is indistinguishable from unmodified SeaSplat | **Supported**, Curasao only | 3+3 runs, ratio 1.036. Should not be stated for all scenes |

---

## Summary

| Verdict | Count |
|---|---:|
| Supported | 9 |
| Partially supported | 3 |
| **Contradicted** | **5** |
| Not yet tested | 5 |
| Methodologically untestable with the current design | 2 |

### Two claims have moved since this ledger was first written

**E.2 is now supported at n=12 with a 12-run control** — the campaign's central hypothesis,
established. Every A2 run drops on a simplification boundary; no A0 run loses a channel. The
collapse turns out to be **bistable and seed-conditioned** rather than scene-conditioned, which
is a stranger claim than the hypothesis made and is what the data supports.

**E.7 is the finding that answers the reviewers.** `A1/Curasao/s0` produced the best test PSNR
in the campaign with two of three attenuation channels dead. The physics broke while the
fidelity improved — which is the direct answer to *"why do these mechanisms behave differently
under underwater conditions"*, and not one the fidelity metrics could have produced.

**E.6 is contradicted** — CD-6, this thesis's own proposed remedy, did not restore β. That is
the first evidence either way, because the burst has been unconditionally enabled since it was
written. It is a negative result about the work's own contribution and it should be reported
as one `[13-campaign-addendum.md §13.10]`.

Both are `n=1`. They are recorded because they bear on the recommended positioning: the
"integration boundary" contribution now has a third instance, and unlike the other two it has
a physical rather than an engineering interpretation.

### The contradicted claims

They are not peripheral — **B.1 and B.2 are the manuscript's headline result**, and the one
the meta-review singled out as the study's most useful finding. C.3 and D.2 are framing.

None of the four is contradicted by an error in the *current* implementation. Three are
contradicted by fidelity gaps in the *prior* implementation (D-1, D-2), and one by a
measurement the prior work did not make (D-5).

**This is a better position than it appears.** The current implementation is faithful where
the prior one was not, and the corrections are documented with code and measurement. What the
rewrite must not do is carry the old numbers forward under the old names.
