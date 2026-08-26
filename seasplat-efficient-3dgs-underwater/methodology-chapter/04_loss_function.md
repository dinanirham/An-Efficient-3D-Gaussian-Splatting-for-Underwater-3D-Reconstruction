# §4 — Loss function

---

## 4.1 The composed method introduces **no new or modified loss term**

The objective is exactly SeaSplat's, unchanged:

```
L = L_GS
  + λ_bs      · L_bs          (backscatter,   λ = 1.0)
  + λ_gw      · L_gw          (grey-world,    λ = 0.1,  active only when iter > seathru_from_iter)
  + λ_sat     · L_sat         (saturation,    λ = 2.0)
  + λ_op      · L_op          (opacity prior, λ = 0.01)
  + λ_Zsmooth · L_Zsmooth     (depth smooth,  λ = 2.0)
  + λ_Zrec    · L_Z-recon     (depth recon,   λ = 1.0)

where  L_GS = (1 − λ_dssim) · L1(Î, I) + λ_dssim · (1 − SSIM(Î, I))
```

All seven terms, all seven weights, and the `seathru_from_iter` gate on `L_gw` are identical
across every configuration A0–A7.

### Justification — three independent lines of evidence

**(a) Code.** No branch modifies any loss-bearing file. Per-branch file lists show A1 touching
only `scene/__init__.py`, `train.py` (1 line), `arguments/__init__.py`, `source/roma_init.py`;
A2 only `scene/gaussian_model.py`, `train.py`, `arguments/__init__.py`; A3 only
`source/quantize.py`, `arguments/__init__.py`. **`deepseecolor/losses.py`,
`deepseecolor/depth_losses.py` and `utils/loss_utils.py` are untouched on all seven feature
branches** `[implemented: audit branch_inventory.md]`.

**(b) Mechanism type.** Each intervention operates at a level where a loss term is structurally
unnecessary:

| Mechanism | Level | Why no loss is needed |
|---|---|---|
| **A1** | initialization + a schedule gate | Changes *which parameters exist at `t = 0`* and whether the population may change. Both are outside the objective. |
| **A2** | population edit under `torch.no_grad()` | `get_importance` builds no graph; `prune_points` index-selects parameters and Adam state. Gradients are unaffected in form — only in which primitives receive them. |
| **A3** | offline, post-training | Runs after iteration 30 000 on a saved `.ply`. There is no objective left to modify. |

**(c) Design intent.** The draft thesis states it directly: the efficiency mechanisms "are not
intended to modify the underlying physical rendering equation … Across all experimental
configurations, the underlying physics-aware rendering model, **loss formulation**, and
optimization settings are held constant" `[recommended: draft §3.5.1, §3.6.4]`.

**This is the property that makes the ablation interpretable.** Because the objective is
literally identical, any measured difference between configurations is attributable to
representation structure alone — not to a reweighted objective. It should be stated explicitly
in the thesis, because it is the strongest internal-validity claim the design supports.

---

## 4.2 What the mechanisms do to the *existing* loss terms

No term changes, but two terms have their **effect** altered because the machinery that
executes them changes.

| Term | Altered by | How |
|---|---|---|
| **`L_op`** (λ = 0.01) | `[A1]` 🔴 | `L_op` drives `α → 0` for backscatter-only primitives. In baseline, the `min_opacity = 0.005` argument to `densify_and_prune` then **removes** them. Under `--no_densify` that prune is disabled along with densification `[implemented: train.py:517-547]`, so `L_op` still suppresses but nothing removes. **The loss term is unchanged; its executor is gone.** |
| **`L_op`** | `[A2]` 🟢 | `Φ_i = α_i · ρ(s_i)` reads post-`L_op` opacity, so the lowest-scoring primitives are exactly those `L_op` suppressed. A2 **supplies a removal path** for `L_op` — the same one A1 removes. |
| **`L_gw`, `L_sat`** | `[A3]` 🟡 | Both shape aggregate colour statistics of `Ĵ` over 20 000 iterations. A3 snaps `f_dc` to 256 centroids **after** training, with no gradient step remaining to rebalance them. The terms are unchanged; their converged solution is perturbed afterwards. |

This is the precise sense in which the mechanisms are "purely structural": they change *who the
losses act on* and *what happens to the result*, never the losses themselves.

---

## 4.3 Mitigation losses — status, stated separately

The prompt asks that *proposed*, *implemented*, and *validated* be kept distinct. They are three
different claims and the honest answer differs for each candidate.

> ⚠️ **No compatibility matrix exists.** `./seasplat-efficiency-adaptation/` contains only
> `audit-output/`; the efficiency-adaptation study that would have produced per-mechanism
> compatibility matrices was never run. Every "recommended" claim below therefore comes from the
> A1 design spec, the draft thesis Chapter 3, or the implementation audit's refit
> recommendations — **not** from a compatibility matrix. See `open_questions.md` Q-1.

| Candidate mitigation | Targets | Proposed? | Implemented? | Validated? |
|---|---|---|---|---|
| **CompGS ℓ1 opacity regularizer** (`λ_reg Σ α_i`, λ = 1e-7) `[paper: compact3d §3]` | Count reduction to complement quantization; CompGS's 2–3× FPS gain comes from this, not from VQ | ❌ **not proposed** anywhere | ❌ | ❌ |
| **EDGS `reduce_opacity`** — continuous `logit ← logit + log(0.99)` every 10 steps `[paper: EDGS repo trainer.py]` | Restores decay-and-cull under `--no_densify`; addresses the A1 stability boundary | ⚠️ **proposed in the audit only** `[audit refit R-5]`; absent from the design spec and draft thesis | ❌ | ❌ |
| **EDGS `max_lr`** — position-LR clamp `update_learning_rate(max(step, 8000))` | Dense-init points receive an LR schedule tuned for a *sparse* seed | ⚠️ audit only `[audit refit R-5]` | ❌ | ❌ |
| **Quantization-induced colour-drift regularizer** | `L_gw`/`L_sat` perturbation by post-hoc `f_dc` snapping | ❌ **not proposed** — the draft instead argues post-hoc quantization *avoids* perturbing SeaThru gradients `[recommended: draft §3.5.4]` | ❌ | ❌ |
| **Restoring the `α < 0.005` prune outside the densify gate** | The `L_op` executor A1 removes | ⚠️ audit only `[audit refit R-4]` | ❌ | ❌ |

**Summary: no mitigation loss or regularizer is implemented, and none is validated.** Two are
proposed in the implementation audit and are not yet reflected in the thesis's methodology.

### On the colour-drift risk specifically

The measured evidence does **not** show a colour-drift problem: A3's mean ΔPSNR is
**−0.075 dB** across four scenes, with two scenes improving `[measured]`. Two caveats keep this
from settling the question:

1. The A3 comparison is confounded — A3's runs produced *different Gaussian counts* from A0's
   (§8.3), so the deltas mix quantization effect with run-to-run variance.
2. `L_gw` and `L_sat` act on the **restored image `Ĵ`**, while the reported PSNR compares the
   **rendered underwater image `Î`** against the raw underwater GT. A colour shift in `Ĵ` is
   partly re-absorbed by the medium model on the way to `Î`, so full-frame PSNR on `Î` is the
   wrong instrument to detect it (§10.5).

**Recommendation:** before proposing any mitigation loss, measure the effect directly — compare
`Ĵ` before and after quantization on a fixed checkpoint. That is a zero-retraining check and it
converts an assumed risk into a measured one.

---

## 4.4 Well-posedness of the objective under all eight configurations

Because the objective is invariant, well-posedness reduces to whether each loss term still has
a valid domain and a valid gradient path. Confirmed per term in §5. The one term whose
*enforcement* changes is `L_op`, and that is tracked as the central compounding site (§3.5).
