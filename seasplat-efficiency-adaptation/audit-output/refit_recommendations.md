# §5 — Ranked refit recommendations

Ranked by **value per unit of cost**, not by severity alone. Diagnostics that unblock
interpretation come first because several severe findings are *conditional* — they may or may
not apply depending on numbers nobody has recorded, and it is wasteful to retrain before
knowing which.

**Cost legend**

| | Meaning |
|---|---|
| 🟩 **free** | documentation or reporting change only |
| 🟦 **cheap / no retrain** | code or config change; existing checkpoints remain valid, or only the offline stage re-runs |
| 🟧 **cheap fix, retrain required** | small code change, but it alters training dynamics — all affected arms must be re-run |
| 🟥 **expensive, retrain required** | new mechanism to implement, then re-run |

---

## Ranked list

| # | Action | Class | Cost | Affects |
|---|---|---|---|---|
| **R-1** | Log Gaussian count unconditionally; record the `seathru_from_iter` value used | correctness | 🟦 | all 8 |
| **R-2** | Remove `'opacity'` from `to_quantize` | correctness | 🟦 | A3, A5, A6, A7 |
| **R-3** | Fill the three empty `docs/*.md` | correctness | 🟩 | all 8 |
| **R-4** | Decouple `--no_densify` from α-pruning and opacity reset | correctness | 🟧 | A1, A4, A5, A7 |
| **R-5** | Port EDGS's `reduce_opacity` decay and `max_lr` clamp | correctness | 🟧 | A1, A4, A5, A7 |
| **R-6** | `uint8` indices; report raw quantized size beside the zlib figure | efficiency | 🟦 | A3, A5, A6, A7 |
| **R-7** | Version + hash the dense `.ply`; seed `roma_init.py`; pin `romatch` | correctness | 🟦 | A1, A4, A5, A7 |
| **R-8** | Re-scope the Mini-Splatting attribution; rename `imp_metric` | correctness | 🟩 | A2, A4, A6, A7 |
| **R-9** | Add a real disable flag for A2 (`--no_reorg`) | correctness | 🟦 | A2, A4, A6, A7 |
| **R-10** | Replace deterministic top-k with stochastic importance sampling | correctness | 🟧 | A2, A4, A6, A7 |
| **R-11** | State A3's ≈2.8× ceiling up front, or add a position-coding path | efficiency | 🟩 / 🟥 | A3, A5, A6, A7 |
| **R-12** | Make A3 quantization-aware (STE), with `nn_index` carried through `prune_points` | correctness | 🟥 | A3, A5, A6, A7 |
| **R-13** | Implement Mini-Splatting's accumulated-blending-weight importance | correctness | 🟥 | A2, A4, A6, A7 |

---

## Do these first — no retraining, and they decide what else is worth doing

### R-1 🟦 Log the Gaussian count unconditionally, and record `seathru_from_iter`

**Why it is first.** Three unrecorded numbers (`cross_branch_comparison.md` U-1/U-2/U-3)
currently determine whether **four of the eight factorial cells exist at all**:

- With densification disabled, `N` can never grow, so if `N_init ≤ 800 000` then
  **A4 ≡ A1 and A7 ≡ A5** and A2 contributes nothing to either.
- `seathru_from_iter` defaults to **`9_000_000`** `[repo: arguments/__init__.py:179]`. If the
  flag was omitted, **the medium model never activated** and the entire study compared
  variants of plain 3DGS, not SeaSplat.

A2 currently prints `[A2] Reorg @ iter …` **only when `n_pruned > 0`**, so silence is
ambiguous between "under budget" and "not running." Move the count log outside that branch
and emit `n_current` every 500 iterations regardless.

**Retraining A5 or A7 before answering U-2 is the single most wasteful thing available.**

### R-2 🟦 Remove `'opacity'` from `to_quantize`

The highest benefit-to-cost fix in the audit. compact3d excludes opacity deliberately
`[compact3d §3]`; A3 includes it without stated reason. On A1-derived branches this is the
sharp end of the worst compounding defect in the set — unpruned `L_op`-suppressed Gaussians
meeting opacity quantization with no recovery step (`combination_audit/a1_a3.md` C5-1).

**Cost:** delete one string from a list. Opacity is 1 of 14 floats, so ~2 bytes per 20
(`a3.md` A3-7). **No retraining** — `quantize.py` re-runs against the existing `.ply`.

### R-3 🟩 Fill `docs/ablation_design.md`, `experiment_plan.md`, `reproducibility_notes.md`

All three exist and are **0 bytes**. Because of that, this audit could establish deviation
from the *published* source methods but **not from the author's intent** — several findings
would resolve immediately given a recorded rationale. Minimum contents:

- **`experiment_plan.md`** — the exact training command per branch, including
  `seathru_from_iter`, `--pcd_path`, `--no_densify`, `--max_gaussians`; dataset and split;
  the `--eval` flag (it defaults to `False` — see `validation_alignment.md`).
- **`ablation_design.md`** — that A0–A7 is a full 2³ factorial; which contrasts are read as
  additive and which as leave-one-out; the expected A1×A2 interaction (`a1_a2.md` C4-3).
- **`reproducibility_notes.md`** — `roma_init.py` invocation, output point count, `.ply`
  hash, `romatch` version, GPU/driver.

### R-6 🟦 `uint8` indices, and separate the zlib from the quantization

`k = 256` needs 8 bits; `km.labels_.astype(np.uint16)` uses 16 — a flat 2× waste on the index
payload, raising A3's raw ratio from ≈2.8× to ≈3.5×. Separately, the reported ratio uses
`np.savez_compressed`, so **generic zlib entropy coding is being credited to the quantizer**
(`a3.md` A3-6) and the number is not comparable to compact3d's bit-packed `Mem` column.
Report both. Re-runs the offline stage only.

### R-7 🟦 Make A1's dense cloud reproducible

The `.ply` **is** the experimental condition for A1/A4/A5/A7, and it is unversioned,
unhashed, and produced by an unseeded GPU matcher. Two runs of `roma_init.py` give different
clouds, hence different `N`, hence different "efficiency" numbers with no way to attribute
the variance. Record point count + SHA-256, seed the matcher, pin `romatch` (the only
dependency missing from `requirements.txt`).

### R-8 🟩 Re-scope the Mini-Splatting attribution

A2 implements none of blur split, depth reinitialization, or intersection preserving; its
importance is `opacity × scale` — an instantaneous parameter magnitude with **no visibility
or occlusion term** — rather than Mini-Splatting's accumulated blending weight; and it uses
deterministic top-k, **the approach Mini-Splatting §4.2 argues against**. It also reuses the
name `imp_metric` for an unrelated distinction (`max` vs `mean` over scale axes, not
`I¹` vs `I²`).

If the thesis cites A2 as a Mini-Splatting adaptation, it claims something the code does not
do. **Cite it as "magnitude-based budget pruning."** Rename `imp_metric` to
`scale_reduction` to stop the collision propagating.

There is a genuinely defensible framing available and it is stronger than the borrowed one:
`opacity × scale` reads post-`L_op` opacity, so it **prunes exactly the backscatter-only
Gaussians SeaSplat's opacity prior suppresses** (`a2.md` A2-3). That is a SeaSplat-specific
result, and it is the most interesting thing in the branch set. Claim that instead.

### R-9 🟦 Give A2 a real off switch

`hasattr(opt_params, 'max_gaussians')` is always `True` — the same branch defines the
attribute. There is currently **no way to disable A2 on its own branch**, so it cannot
produce a control run. Add `--no_reorg`, defaulting to `False`.

---

## Then these — cheap code, but they change training dynamics

### R-4 🟧 Decouple `--no_densify` from pruning and opacity reset

The most consequential correctness fix. In SeaSplat's `train.py` the gated block contains
**three** mechanisms; A1's one-line change disables all of them
`[repo: train.py:517-547]`:

```python
if not opt_params.no_densify and iteration < opt_params.densify_until_iter:
    ...
        gaussians.densify_and_prune(τ, 0.005, ...)   # ← densify AND α-prune
    ...
        gaussians.reset_opacity()                     # ← opacity reset
```

The α-prune is what executes SeaSplat's `L_op`: the opacity prior drives backscatter-only
Gaussians to `α ≈ 0`, and the prune removes them. Disabled, they persist for all 30 000
iterations — costing memory and per-frame sort time (harming the efficiency claim) while
contributing nothing to PSNR (so **the metric cannot see the problem**).

EDGS, the source method, keeps its `α < 0.005` prune running outside the densify gate
`[EDGS repo: trainer.py:258-264]`. Restore that:

```python
# densification proper — gated by no_densify
if not opt_params.no_densify and iteration < opt_params.densify_until_iter:
    ... add_densification_stats / densify_and_prune ...

# opacity hygiene — NOT gated by no_densify
if iteration < opt_params.densify_until_iter and iteration % opt_params.densification_interval == 0:
    gaussians.prune_points(gaussians.get_opacity.squeeze(-1) < 0.005)
```

### R-5 🟧 Port EDGS's two undocumented counterweights

Both default to `True` in EDGS and neither is in the paper — they are what make a
densification-free regime survivable `[EDGS: 05-constraints.md M-5, M-6]`:

- **`reduce_opacity`** — `logit ← logit + log(0.99)` every 10 steps while
  `iter < densify_until_iter`. Paired with the α-prune restored in R-4 this is a
  **continuous decay-and-cull**: every Gaussian's opacity bleeds away and only those the
  photometric loss actively defends survive. It is the smooth analogue of the opacity reset
  A1 removed.
- **`max_lr`** — `update_learning_rate(max(gs_step, 8000))`, clamping the position-LR
  schedule so dense-init points do not receive the large early LR intended for a *sparse*
  SfM seed.

⚠️ Under SeaSplat, `reduce_opacity` interacts with `L_op` (λ = 0.01), which already pushes
opacity down for backscatter-only Gaussians. **Applying both may over-prune.** Gate
`reduce_opacity` to `iter < seathru_from_iter`, or reduce `λ_op` while it is active — and
test the pair, since neither source method faced this combination.

### R-10 🟧 Stochastic importance sampling instead of top-k

Mini-Splatting §4.2 argues that deterministic top-k collapses primitives onto high-importance
regions and strips coverage elsewhere. On A4/A7 there is no densification left to recover
what gets stripped. Replace the ascending sort with sampling without replacement ∝ importance
(`torch.multinomial`). Small change; changes which Gaussians survive, so it needs a re-run.

---

## Finally — expensive, and only if the scope demands it

### R-12 🟥 Make A3 quantization-aware

compact3d's contribution *is* quantization-aware training: quantized forward, STE backward,
so the non-quantized parameters adapt to the centroids they will be snapped to
`[compact3d §3]`. A3 snaps a finished model with **no recovery step**, which is precisely the
failure mode compact3d exists to prevent. Under SeaSplat it is worse than under plain 3DGS,
because `L_gw` (λ = 0.1) and `L_sat` (λ = 2.0) shape `f_dc` and cannot rebalance afterwards.

⚠️ **This repair creates a conflict that does not currently exist** (`a2_a3.md` C6-1). Once
quantization runs in-loop, A2's `prune_points` invalidates the assignment vector. Required
alongside:

1. `prune_points` must index-select `nn_index` with every other per-Gaussian tensor;
2. force an assignment refresh immediately after each `reorganize_gaussians` call —
   compact3d's cadence is `t = 100`, A2 prunes every 500;
3. handle clusters emptied by pruning.

compact3d solves this upstream (its own ℓ1-opacity pruning coexists with QAT,
`[compact3d repo: train_kmeans.py:158-166]`), so the pattern is available to copy.

**Also raise `k`.** 256 vs compact3d's 4096–32768 is 16–128× coarser, and at `sh_degree = 0`
the `group_size = 4` machinery is inert (every attribute is a single group), so `k` is the
only quality dial A3 has.

### R-13 🟥 Implement Mini-Splatting's importance properly

Accumulate per-Gaussian blending weight over training views during rasterization, giving
`I¹`/`I²`. This is the mechanism, and without it A2 is a different method. Only worth doing
if the thesis needs the Mini-Splatting attribution; **R-8 (re-scope the claim) is the cheap
alternative and is the recommended path** unless a reviewer requires the comparison.

### R-11 🟩/🟥 A3's compression ceiling

At `sh_degree = 0`, protected `xyz` is 12 of the 20 post-quantization bytes — **60% of the
residual** — capping A3 near **≈2.8×** (≈3.5× with R-6), against compact3d's reported 40–50×
(`a3.md` A3-7). This is exactly the bottleneck compact3d identified: after quantization,
position dominates, so the only remaining lever is *fewer Gaussians* `[compact3d §3]`.

- 🟩 **Recommended:** state the ceiling in `docs/ablation_design.md` before the runs, and
  frame A6/A7 as `count × bits` with the two factors reported separately — otherwise A2's
  count reduction will be silently credited to the quantizer (`a2_a3.md` C6-3).
- 🟥 **Only if a larger ratio is required:** add position coding (G-PCC, as in
  `my-research/OMG/` and `my-research/CompGS/`), or a rate term in the loss
  (`my-research/CompGS/`'s `λR`). Both are substantial new work.

---

## Suggested execution order

```
R-1, R-3  →  resolve U-1/U-2/U-3 before spending any GPU time
   │
   ├─ if U-2 shows the medium model was off ──► re-run everything; nothing else applies yet
   │
   └─ otherwise:
        R-2, R-6, R-7, R-8, R-9   (no retrain — re-run offline stages, fix docs)
                 │
                 ▼
        R-4, R-5  (retrain A1, A4, A5, A7 — the biggest correctness win)
                 │
                 ▼
        R-10      (retrain A2, A4, A6, A7 — optional, if the coverage argument matters)
                 │
                 ▼
        R-11 🟩   (re-scope the compression claim)
                 │
                 ▼
        R-12, R-13  (only if scope demands full fidelity to compact3d / Mini-Splatting)
```

**R-1 through R-9 cost no GPU time beyond re-running two offline scripts, and between them
address 5 of the 8 high-severity findings.** That is where the return is.
