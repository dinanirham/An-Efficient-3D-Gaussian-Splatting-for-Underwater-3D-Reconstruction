# Discrepancy Ledger

Contradictions between the manuscript, the prior implementation, the current implementation,
the source methods, and the executed runs. Recorded rather than silently reconciled, per the
brief's source-of-truth hierarchy.

Severity uses the brief's Phase 3 scale: *Conformant* · *Minor documentation drift* ·
**Material methodological deviation** · **Experiment-invalidating inconsistency** · *Unable to
verify*.

---

## D-1 — The manuscript's A2 is not Mini-Splatting

**Severity: experiment-invalidating inconsistency** (for the manuscript's headline result).

The manuscript and the SIGGRAPH submission describe A2 as *"Mini-Splatting importance-based
budget pruning"* (Reviewer 1's summary) and report it as the best-performing mechanism —
Reviewer 3 records *"budget pruning gives the best overall balance, reducing model size and
Gaussian count by about 72% with a 0.05 dB average PSNR decrease."*

The code on `feature/a2-spatial-reorganization` implements something else.

```python
def get_importance(self, imp_metric='outdoor'):
    """A2: Importance score per Gaussian.
    Inspired by Mini-Splatting (Fang & Wang, ECCV 2024).
    I_i = opacity_i * scale_i"""
    opacity = self.get_opacity.squeeze(-1)
    scale   = torch.max(self.get_scaling, dim=1).values
    return opacity * scale

def reorganize_gaussians(self, max_gaussians, imp_metric='outdoor'):
    ...
    _, idx = torch.sort(importance)          # ascending — lowest first
    prune_mask[idx[:n_prune]] = True
```
`[previous-repo @ bcd6eee: scene/gaussian_model.py:470-512]`

Three deviations, each material:

| | Mini-Splatting (ECCV 2024) | Prior A2 |
|---|---|---|
| **Importance** | Σ blending weight ÷ projected area, from the rasterizer's per-Gaussian accumulators | `opacity × max(scale)` — a proxy computable without them |
| **Selection** | importance-weighted **stochastic sampling** (`multinomial`) | **deterministic top-k** |
| **Schedule** | two simplification points (15 000 and 20 000) | fires **once** |

The second is not a simplification — it is **the failure mode Mini-Splatting's paper exists
to fix.** Its degeneracy S-4 states that deterministic top-k pruning destroys local geometry
because importance is spatially autocorrelated, and the paper validates stochastic sampling
against top-k using Chamfer distance rather than PSNR
`[../mini-splatting/05-constraints.md S-4]`. The prior implementation adopted the mechanism's
*goal* and the specific procedure the source method rejects.

The proxy metric was not a free choice either: the prior branch uses SeaSplat's own rasterizer
(`diff_gaussian_rasterization`), which does not return the accumulators the real metric needs.
The proxy is what remains computable without switching forks — which is precisely why the
current implementation switched forks (CD-13).

**Consequence.** The manuscript's strongest empirical claim is a claim about a mechanism that
was not implemented. The number may still be a true observation about deterministic
opacity×scale pruning; it is not evidence about Mini-Splatting, and it cannot be carried into
the revised Chapter 4 under that name.

**Current implementation: conformant.** `source/simplify.py` uses the `_ms` fork's
`accum_weights` / `area_proj` / `area_max`, `torch.multinomial` sampling, and both
simplification iterations `[implementation @ 3c165ae]`.

---

## D-2 — The manuscript's A3 is post-hoc, not quantization-aware

**Severity: material methodological deviation.**

```python
"""...applied post-training to Gaussian attributes."""
from sklearn.cluster import MiniBatchKMeans
...
self.quant_k = 256          # codebook size per attribute group
```
`[previous-repo @ 980e915: source/quantize.py:5,24; arguments/__init__.py:187]`

CompGS-VQ's method is **quantization-aware training** with a straight-through estimator —
its degeneracy C-1 is exactly that *"post-hoc clustering degrades quality because nothing in
the objective makes parameters clusterable"* `[../compact3d/05-constraints.md C-1]`. The prior
A3 implements the condition the source method identifies as the problem.

Codebook size also differs: **256** against the current implementation's **4096**. At
`sh_degree = 0` the source method's group machinery is inert, so `k` is the only quality dial
`[06-implementation-deltas.md CD-11]`, and a 16× smaller codebook is not a neutral choice.

**Reviewer 3 independently flagged the control problem** — *"A3 is applied to a separately
trained model rather than the identical A0 checkpoint, which confounds its small quality
difference."* Note that the current implementation cannot answer this by sharing a checkpoint:
quantization-aware training necessarily produces its own run. The correct answer is the one
now available — report the difference against measured run-to-run dispersion (D-5).

**Current implementation: conformant.** Straight-through estimator, quantization-aware from
iteration 22 000, k-means++ seeding, k = 4096.

---

## D-3 — A defect in the *current* implementation, found and corrected

**Severity: was experiment-invalidating; now resolved.**

Substituting the rasterizer (CD-13) preserved every forward value and silently changed which
loss gradients reach density control. Alpha's value was exact; its gradient was absent from
the densification signal. The baseline configuration converged to a sixth of SeaSplat's
primitive count.

| densification buffer receives | primitives, Curasao |
|---|---:|
| image only (as first merged) | 743 457 |
| image + alpha + depth (CD-22) | 635 038 — *worse* |
| image + alpha (CD-23, and upstream) | ~4.4M |

Resolved by CD-22 + CD-23 and verified: three runs of each implementation give overlapping
ranges, mean ratio **1.036** `[13-campaign-addendum.md §13.3]`.

**Recorded here because it is a positive finding, not only a bug.** No value-level check could
have caught it, and the class — *an integration boundary can preserve every value and still
change which gradients flow where* — is now a documented contribution
`[05-constraints.md §5.6]`. It is also the strongest available answer to Reviewer 2 and the
meta-review, both of whom asked why mechanisms behave as they do.

---

## D-4 — "Model size" means different things in the two codebases

**Severity: material — comparisons across the two are invalid as stated.**

The manuscript reports A0 at **194.18 MB** for **2 855 580** Gaussians. That is 68.0 bytes per
primitive, which is the **PLY** layout (17 float32: xyz, normals, f_dc, opacity, scale,
rotation).

The current implementation reports `model_size.json` over `compressed_*/`: float32 `.npy` at
**14** floats per primitive = 56 bytes, with normals and the empty `f_rest` block absent
`[source/storage.py]`.

A PLY-versus-`.npy` comparison is a 1.21× artifact before any mechanism acts. Any table
placing the manuscript's sizes beside new ones must state the container, and the
`ratio_vs_this_baseline` field exists for exactly this reason.

---

## D-5 — Run-to-run variance was unmeasured, and is large

**Severity: invalidates single-run comparisons in the manuscript.**

The manuscript reports single runs. Measured now, across S1's twelve A0 runs:

| scene | mean primitives | sd | CV |
|---|---:|---:|---:|
| Curasao | 3 757 808 | 550 866 | 14.7% |
| IUI3-RedSea | 2 537 851 | 242 367 | 9.6% |
| JapaneseGradens-RedSea | 2 235 661 | 134 610 | **6.0%** |
| Panama | 2 305 920 | 676 400 | **29.3%** |

Panama's slowest and fastest seeds differ by **1.85×** at identical configuration. The
mechanism is amplification: a primitive lands either side of `densify_grad_threshold` from run
to run, changing the population that feeds the next densification event, 144 times over
`[08-computational-profile.md §8.2b]`.

**The manuscript's headline "0.05 dB average PSNR decrease" is not interpretable without
this.** At three seeds and the mean CV, a difference on primitive count must exceed roughly
17% to clear the noise; a 0.05 dB fidelity difference from single runs is far inside it.
Reviewer 3 asked for *"information about repeated runs"* — this is the answer, and it is not
favourable to the original claim.

---

## D-6 — A0's primitive count is consistent across the two codebases

**Severity: conformant — recorded because it is load-bearing.**

| | primitives |
|---|---:|
| Manuscript A0 (prior codebase, scene-averaged) | 2 855 580 |
| Current A0 (median of 12 runs) | 2 482 200 |
| Current A0, Curasao only (mean of 3) | 3 757 808 |

These agree within the dispersion of D-5. Two independent implementations, on different
rasterizers, converge to the same baseline population — which corroborates that both
reproduce SeaSplat and that the D-3 defect was confined to the current codebase and is fixed.

**A caution for the rewrite.** The replication that established *A0 ≡ vanilla SeaSplat* ran on
**Curasao only**, where A0 sits near 3.8–4.4M. Statements of the form "A0 converges to ~4.4M"
are Curasao statements. The four-scene median is 2.48M.

---

## D-7 — Frame rate: not comparable as reported

**Severity: unable to verify.**

The manuscript reports **44.84 FPS** average, with Curasao at 30.84 and the others at
48.93–50.35, attributing Curasao's deficit to higher image resolution.

The current implementation measures **69.17 FPS** on Curasao at 4 285 043 primitives
(14.46 ms/frame, colour pass only, CUDA-synchronised, warm-up discarded)
`[utils/render_profile.py]`.

These cannot be compared: the manuscript states no timing protocol — Reviewer 3 lists
*"the missing hardware and timing protocol"* among what reproduction would require — and it is
unknown whether its figure synchronises the device, includes the probe passes, or times a warm
renderer. **The current implementation pays three rasterization passes per training iteration
(CD-23) but renders with one**, so a naïve carry-over of the older number would also
misattribute the training cost.

---

## D-8 — Chapter 2 omits whole compression families

**Severity: material — and it is the reviewer's stated reason for rejection.**

Reviewer 3: *"the related-work coverage and experimental design omit several major compression
families, including rate-distortion optimization, entropy coding, adaptive attribute pruning,
and structured representations."*

The repository's evidence base has the same hole. There is no
`research-methodology-output` for **EAGLES**, **LightGaussian**, **ReSplat**,
**WaterSplatting**, **Aquatic-GS**, or **Gaussian Splashing** — all named in the brief's
Phase 1 list. `CompGS` (Liu et al., predictive coding + entropy model) and `OMG` are analysed
but appear only as related work.

This is a literature obligation, not an experimental one, and it is tractable. Detailed in
`06-experiment-and-literature-plan.md`.

---

## D-9 — One operating point per mechanism

**Severity: material — limits what Chapter 4 may conclude.**

Reviewer 3: *"Each selected mechanism is also represented by essentially one operating point,
so Fig. 2 does not establish a Pareto surface or show that the ranking persists across
budgets."*

**The current design has the same limitation.** `n_bud` is a single fixed value (200 000), and
`kmeans_k` a single value (4096). The factorial answers *"do these three mechanisms interact?"*
It does not answer *"which mechanism is preferable at a given budget?"* — and the manuscript's
conclusions are phrased as mechanism-selection guidance, which is the second question.

This is the most consequential unresolved gap for the repositioning in `04-repositioning.md`,
and the minimum additional experiment that would close it is costed in
`06-experiment-and-literature-plan.md`.

---

## D-10 — Scope claims exceed evidence

**Severity: minor now, but the brief prohibits it explicitly.**

The manuscript frames the work around *"the envisaged usage in autonomous underwater
vehicles"* (Reviewer 1's summary). No deployment hardware, power, latency or memory budget is
evaluated. The brief states directly: *"Avoid treating AUV deployment as demonstrated unless
deployment hardware, power, latency, and memory are evaluated directly."*

Peak render memory is now measured (3 587 MB), which is one of the four — and it is measured
on an A100, not on an embedded target.

---

## Summary

| # | Discrepancy | Severity | Fixed in current impl? |
|---|---|---|---|
| D-1 | Prior A2 is not Mini-Splatting | experiment-invalidating | ✅ yes |
| D-2 | Prior A3 is post-hoc, k=256 | material | ✅ yes |
| D-3 | Alpha-gradient defect | was invalidating | ✅ yes, and documented |
| D-4 | "Model size" means two things | material | ✅ container recorded |
| D-5 | Variance unmeasured, and large | invalidates single runs | ✅ measured |
| D-6 | A0 counts agree across codebases | conformant | — |
| D-7 | FPS protocol undefined | unable to verify | ✅ protocol now defined |
| D-8 | Compression families omitted | material | ❌ **literature work outstanding** |
| D-9 | One operating point per mechanism | material | ❌ **design limitation, unresolved** |
| D-10 | AUV framing unsupported | minor | ❌ **framing to narrow** |

**Seven of ten are already resolved by the current implementation.** The three that are not —
D-8, D-9, D-10 — are precisely the three the reviewers rejected the paper for, and none of
them is an implementation problem. Two are writing; one is an experiment.
