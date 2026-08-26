# §5 — Constraints and well-posedness

---

## 5.1 SeaSplat's own well-posedness machinery

The underwater inverse problem `I = J · e^(−β^D·Z) + B^∞ · (1 − e^(−β^B·Z))` is
under-determined: `J` and the medium parameters trade off against each other, and both trade
off against `Z`. SeaSplat closes it with four mechanisms, all of which the composed method
inherits unchanged.

| # | Mechanism | What it prevents | Where |
|---|---|---|---|
| **W-1** | **Gradient detachment** — `L_bs` acts on a detached `I − B̂′`; `L_Z-recon` uses a detached `Ẑ` weight | The medium model explaining away geometry, and vice versa. Auxiliary supervision informs without back-propagating into the term it supervises. | `deepseecolor/losses.py` |
| **W-2** | **Staged activation** — `seathru_from_iter = 10 000`; `L_gw` additionally gated on the same boundary | Solving the joint geometry+medium problem from `t = 0`, when `Ẑ` is meaningless. Geometry converges under `L_GS` alone first. | `train.py`, `arguments/__init__.py:179` |
| **W-3** | **Homogeneity assumption** — the medium is **9 global scalars** (`β^D, β^B, B^∞ ∈ ℝ³`), constant over the scene | An unconstrained per-point medium field, which can absorb arbitrary radiometric error. Contrast SeaThru-NeRF's per-ray MLP field (§9). | `deepseecolor/models.py` |
| **W-4** | **Range anchoring on `Ĵ`** — `L_gw` (λ = 0.1) fixes the aggregate colour scale, `L_sat` (λ = 2.0) caps `Ĵ` at 0.7 | The scale ambiguity `J·e^(−βZ) = (cJ)·e^(−(β − ln c/Z)Z)`. Without these, `J` and `β^D` are jointly unidentifiable. | `deepseecolor/losses.py` |

**W-3 is the load-bearing one for this thesis.** Because the medium is 9 globals in separate
`nn.Module`s under their own optimizers, no edit to the *per-primitive* population can corrupt
it. Every isolation result below is a consequence of W-3, and **none of them would transfer to
a method with a per-primitive or per-ray medium model.**

---

## 5.2 Per-mechanism check

Each row is a branch-level finding, not a restatement of the general principle.

### A1 — Deterministic initialization

| Constraint | Status | Evidence |
|---|---|---|
| W-1 detachment | ✅ intact | No loss file touched `[audit branch_inventory.md]` |
| W-2 staged activation | ⚠️ **weakened** | Staging still occurs at 10 000, but the `--no_densify` gate spans `[0, 15 000)` and therefore removes the **5 000-iteration window in which baseline geometry adapts to newly-explained backscatter**. Geometry error that only becomes visible once `B^∞` is modelled has no recovery path. `[audit a1.md]` |
| W-3 homogeneity | ✅ intact | A1 adds no parameters; medium modules untouched |
| W-4 range anchoring | ⚠️ latent | Colour fallback seeds `f_dc` at uniform grey 0.5 when the PLY carries no colours — exactly `L_gw`'s fixed point. Not triggered in practice (`roma_init.py` samples colours from source images) but the path exists. `[audit a1.md A1-8]` |
| **New: `L_op` executor** | 🔴 **removed** | `densify_and_prune` (carrying `min_opacity = 0.005`) and `reset_opacity` both sit inside the gated block, so `--no_densify` disables all three at once `[implemented: train.py:517-547]`. EDGS keeps its `α < 0.005` prune outside the gate `[paper]`; neither it nor `reduce_opacity`/`max_lr` was ported. |

**Empirical consequence.** Panama: PSNR **14.29** vs baseline **29.22** (−14.93 dB) at A1
density; **21.97** (−7.26 dB) at A1v2 density `[measured]`. The draft thesis reports this as a
density sensitivity boundary `[recommended: draft §4.3.2]`. The audit supplies the mechanism:
a frozen population, no opacity hygiene, and a matcher starved by turbidity — so `Ẑ` feeding
both exponentials is unreliable exactly where W-2 and W-4 need it most.

### A2 — Spatial reorganization

| Constraint | Status | Evidence |
|---|---|---|
| W-1 detachment | ✅ intact | `get_importance` runs under `torch.no_grad()`; no graph built |
| W-2 staged activation | ✅ **satisfied, and load-bearing** | First reorganization at **15 500**, i.e. 5 500 iterations *after* medium activation. Importance is scored on a population already co-adapted with `β^D, β^B, B^∞`. Pruning before 10 000 would have used opacities `L_op` had not yet shaped. `[audit a2.md]` |
| W-3 homogeneity | ✅ **verified** | `prune_points` → `_prune_optimizer` reaches **`gaussians.optimizer` only**; medium modules are structurally unreachable. Adam `exp_avg`/`exp_avg_sq`, `max_radii2D`, `xyz_gradient_accum`, `denom` all correctly index-selected. `[audit a2.md]` |
| W-4 range anchoring | ✅ intact | Losses act on rendered images, not per-primitive tensors; a change in `N` needs no loss-side adjustment |
| **New: coverage** | 🟡 open | Deterministic bottom-`n` removal is the approach Mini-Splatting §4.2 argues against, on the grounds that it strips coverage from low-importance but still-necessary regions `[paper]`. **Not manifest in the measurements** (mean ΔPSNR −0.05 dB, two scenes improve) but untested at tighter budgets. |

The `train.py` comment `SeaThru models: unchanged` is **accurate** — verified, not assumed.

### A3 — Attribute-level quantization

| Constraint | Status | Evidence |
|---|---|---|
| W-1, W-2 | n/a | Runs offline after iteration 30 000; no gradients, no schedule |
| W-3 homogeneity | ✅ **verified and explicit** | `quantize.py` prints `Protected models: backscatter .pth  attenuate .pth` and emits a dequantized `reconstructed.ply` so evaluation runs through the full underwater path with quantization damage present and the medium model intact. **The only mechanism that documents its own medium-model interaction.** `[audit a3.md A3-8]` |
| W-4 range anchoring | 🟡 **weakened** | `f_dc` is snapped to 256 centroids *after* convergence, with no gradient step left for `L_gw`/`L_sat` to rebalance. The terms are unchanged; their solution is perturbed afterwards. |
| **New: opacity quantization** | 🟡 open | `opacity` is in `to_quantize`; CompGS excludes it deliberately `[paper: compact3d §3]`. Quantization is in **logit** space, which bounds the damage — the long negative tail spans many logit units, so large logit error means negligible `α` error. Exposure is confined to primitives near the `α ≈ 0.005` boundary. |

**The post-hoc choice is a stated design decision, not an oversight** — "avoids introducing
quantization-induced gradient perturbations into the SeaThru parameter estimation"
`[recommended: draft §3.5.4]`. It is a rationale CompGS never had to weigh, and the measured
outcome supports it (−0.075 dB mean). Its cost is the forfeited error-recovery path, which is
what makes A5/A7 the risky combinations below.

---

## 5.3 Combination-specific well-posedness risk

| Config | Risk unique to this combination | Status |
|---|---|---|
| **A4** = A1+A2 | A2 is the removal path `L_op` needs and A1 destroys — so in principle A4 *repairs* A1. **But at A1's measured density (222 k–369 k) the 800 000 budget never binds, so A2 never fires and no repair occurs: A4 ≡ A1 exactly.** At A1v2 density (889 k–1.46 M) the budget binds and the repair is real. | 🔴 **Degenerate as configured.** Resolvable at zero cost by pairing with A1v2 density (§10.4). |
| **A5** = A1+A3 | **The only combination with no compensating mechanism.** A1 leaves an unusually large, concentrated mass of `L_op`-suppressed `α ≈ 0` primitives in the `.ply` (nothing removed them); A3 then quantizes opacity. Primitives near the visibility boundary can be snapped above it, **re-materializing exactly the floaters SeaSplat's opacity prior suppressed** — post-hoc, with no gradient step remaining, and largely invisible to full-frame PSNR on `Î`. | 🔴 **Open limitation.** Predicted, never measured (A5 not run). Cheap mitigation available: drop `'opacity'` from `to_quantize` (§6). |
| **A6** = A2+A3 | The anticipated "pruning invalidates the codebook" conflict **cannot occur**: A3 is offline, so the codebook is necessarily fit after every A2 prune. Safe *by construction*. A2 additionally truncates the opacity tail before the codebook is fit, reducing A5's exposure. ⚠️ Making A3 quantization-aware would **create** this conflict — `prune_points` would have to carry the assignment vector, and A2's 500-iteration prune cadence would need syncing with CompGS's 100-iteration assignment refresh. | ✅ **Resolved by construction.** Safest combination; also the one the draft names as most promising `[recommended: draft §4.7.3]`. |
| **A7** = A1+A2+A3 | Inherits A5's compounding when A2 does not fire, and A4's repair when it does. At A1 density, **A7 ≡ A5 exactly**. At A1v2 density the ordering is coherent: dense init → count reduction → quantization, which is the sequencing CompGS argues for and the draft states as intentional `[recommended: draft §3.5.4]`. | 🔴 **Degenerate as configured**, coherent at A1v2 density. |

### Two structural facts that bound all of the above

1. **The combinations are clean file-level unions.** `git diff a4..a7 -- train.py
   scene/gaussian_model.py` is empty; `quantize.py` is byte-identical across `a3/a5/a6/a7`
   `[implemented: audit]`. No mechanism was altered to accommodate another, so every risk above
   is semantic, and every fix is local to a single arm.
2. **W-3 holds in all eight configurations.** No combination reaches the medium model. The
   separation principle asserted in `[recommended: draft §3.5.1]` is verified, not assumed —
   and it is the one claim in this chapter that is safe to state without qualification.

---

## 5.4 Acknowledged limitations of this thesis

Stated plainly, matching `[recommended: draft §4.7]`:

- **A4–A7 are unvalidated.** Every combination-level claim in §5.3 is analytical. `[measured]`
  covers A0, A1, A1v2, A2, A3 only.
- **A4 and A7 are degenerate at A1 density** — a design consequence provable from the completed
  runs, not yet reflected in the experimental plan.
- **No mitigation is implemented** for the A1 opacity-hygiene loss or the A5 compounding risk
  (§4.3).
- **Physical correctness is not validated.** No ground-truth depth, attenuation, or backscatter
  maps exist for these scenes, so W-3's homogeneity assumption is never tested against truth —
  only its *isolation* from the efficiency mechanisms is verified `[recommended: draft §4.7.2]`.
- **Four scenes, 3–4 test views each.** Coverage-loss risks (A2) and boundary effects (A3) may
  simply not be exercised at this scale.
