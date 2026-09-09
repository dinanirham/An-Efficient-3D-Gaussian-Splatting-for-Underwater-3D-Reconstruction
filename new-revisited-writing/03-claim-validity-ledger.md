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
| E.2 | A scene-global medium model whose only spatial input is per-frame min–max-normalised depth is not invariant to primitive-count reduction | **Not yet tested** | Derived analytically `[05-constraints.md §5.4]`; CD-6 remedy implemented; needs S2's β diagnostics |
| E.3 | Converged primitive count carries 6–29% run-to-run dispersion, seeding notwithstanding | **Supported** | 12 A0 runs + 3+3 replication `[measured n=3/scene]` |
| E.4 | Detaching alpha gradients from densification yields ~6× fewer primitives at ~−0.1 dB | **Not yet tested** | `[measured n=1]` against a *defective* baseline, different seeds. Not claimable until S6 `[12-novelty-defensibility.md §12.6.2]` |
| E.5 | A0 is indistinguishable from unmodified SeaSplat | **Supported**, Curasao only | 3+3 runs, ratio 1.036. Should not be stated for all scenes |

---

## Summary

| Verdict | Count |
|---|---:|
| Supported | 6 |
| Partially supported | 3 |
| **Contradicted** | **4** |
| Not yet tested | 5 |
| Methodologically untestable with the current design | 2 |

### The four contradicted claims

They are not peripheral — **B.1 and B.2 are the manuscript's headline result**, and the one
the meta-review singled out as the study's most useful finding. C.3 and D.2 are framing.

None of the four is contradicted by an error in the *current* implementation. Three are
contradicted by fidelity gaps in the *prior* implementation (D-1, D-2), and one by a
measurement the prior work did not make (D-5).

**This is a better position than it appears.** The current implementation is faithful where
the prior one was not, and the corrections are documented with code and measurement. What the
rewrite must not do is carry the old numbers forward under the old names.
