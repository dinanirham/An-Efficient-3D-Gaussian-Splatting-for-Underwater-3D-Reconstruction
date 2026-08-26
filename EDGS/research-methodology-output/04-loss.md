# §4 — Full loss function

## 4.1 The objective is 3DGS's, unmodified

The paper states it in one clause — "Gaussians `G` are optimized with photometric loss"
`[paper §3.1]` — and writes no loss equation at all.

`[repo: source/trainer.py:163-167]`:
```python
L1_loss   = l1_loss(image, gt_image)
ssim_loss = (1.0 - ssim(image, gt_image))
loss = (1.0 - self.training_config.lambda_dssim) * L1_loss + \
       self.training_config.lambda_dssim * ssim_loss
```
with `lambda_dssim = 0.2` `[repo: configs/gs/base.yaml]`.

```
L = 0.8 · L₁(Î, I) + 0.2 · (1 − SSIM(Î, I))
```

**No regulariser. No correspondence loss. No auxiliary term.** `grep`ing `source/` for
additional loss terms finds `tv_loss` in `losses.py:78` — **defined but never called**
anywhere in the training path. `[repo: source/losses.py:78-99]`

Loss-term count across your comparison set:

| Method | Terms | New terms added |
|---|---|---|
| 3DGS | 2 | — |
| **EDGS** | **2** | **0** |
| `mini-splatting/` | 2 | 0 |
| `compact3d/` | 3 | 1 |
| `CompGS/` (Liu) | 3 (+aux) | 2 |
| `seathru_NeRF/` | 3 | 1 |
| `seasplat/` | 7 | 5 |

### Why this matters methodologically

EDGS and `mini-splatting/` are the only two methods here whose contribution is **entirely
outside the objective**, so every reported gain is cleanly attributable. EDGS goes further:
its contribution happens **once, before step 1**, whereas `mini-splatting/` intervenes
repeatedly during optimization. That makes EDGS the most surgically isolable change in the
set — and it is exactly what licenses Table 3's drop-in composability result.

⚠️ **But the isolation is not perfect in the released code.** Two undocumented *optimization*
changes are on by default (see [`06-implementation-deltas.md`](06-implementation-deltas.md)
D-3, D-4):
- `reduce_opacity` — a continuous ×0.99 opacity decay every 10 steps;
- `max_lr` — the position LR schedule clamped to `max(step, 8000)`.

So "we improve reconstruction **without modifying the optimization algorithm**"
`[paper §1, contribution 3]` is true of the *loss* and of *densification*, but not
literally of the optimizer schedule.

## 4.2 What replaces "loss terms" as the object of study

EDGS's analytical quantities are **selection and seeding rules**. For symmetry with the
other folders, each is given with its purpose and the failure it prevents.

### `p_ij^corr` — matcher-confidence filter

- **Form** `[paper Eq. 9]`: `p_ij^corr ∝ U{k : c_ij(u_i^k, v_i^k) > τ_corr}` — uniform over
  correspondences whose RoMa confidence exceeds a threshold.
- **Purpose:** "confidence alone captures **semantic reliability**" `[paper §4.5]`. RoMa's
  certainty map is low in occluded, textureless and non-co-visible regions (visualised in
  `[paper Fig. 5]`, whose caption notes "Correspondence confidence is **not uniform** across
  the scene").
- **What it prevents if removed:** Gaussians seeded from hallucinated matches in regions the
  matcher could not actually see. Table 6's largest single drop.
- ⚠️ **`τ_corr` has no config key.** The repo instead uses `roma_model.sample_thresh`
  `[repo: corr_init.py:541]` — RoMa's own internal sampling threshold — so the paper's
  `τ_corr` is inherited from the matcher rather than exposed. See D-4.

### `p_ij^proj` — geometric-consistency filter

- **Form** `[paper Eq. 10]`: `p_ij^proj ∝ U{k : ε_ij^k < τ_proj}`, with
  `ε_ij^k = max(ε_i^k, ε_j^k)` the worse of the two reprojection errors `[paper Eq. 8]`.
- **Purpose:** "the re-projection term removes **mismatched or unstable correspondences**"
  `[paper §4.5]`. A high-confidence match can still triangulate badly if the pair is
  near-degenerate (small baseline, grazing rays).
- **These two are complementary by construction**, and the paper says so explicitly:
  "confidence alone captures semantic reliability but cannot enforce geometric consistency,
  whereas the re-projection term removes mismatched or unstable correspondences"
  `[paper §4.5]`.
- ⚠️ **Implemented as an opacity mask, not a sampling distribution**
  `[repo: corr_init.py:660-666]`:
  ```python
  mask_bad_points = (proj_errors > keypoint_fit_error_tolerance).float()
  all_new_opacities.append(opacity_template * 0. - mask_bad_points * 1e1)
  ```
  Points failing the test are **kept** with opacity logit `−10` (α ≈ 4.5e-5) rather than
  excluded. The source comment is candid: *"new version that sets points with large error
  invisible // TODO: remove those points instead. However it doesn't affect the
  performance."* They are then swept up by the `α < 0.005` prune at
  `[repo: trainer.py:261]`. Functionally similar, structurally different — and it means the
  initial Gaussian count is inflated relative to what Eq. 10 implies. See D-2.

### `p_i(k)` and `p(k)` — aggregation across neighbours and references

- **Form** `[paper Eq. 11]`: `p_i(k) ∝ max_{j∈𝓘_i} ( p_ij^corr · p_ij^proj )` — for each
  correspondence, take the **best** of its `J` neighbours; then `p(k) ∝ Π_i p_i^k` across
  reference views, "effectively selecting correspondences that remain consistent across
  multiple reference views" `[paper §3.4]`.
- **Repo:** `select_best_keypoints` `[repo: corr_init.py:492-519, 647]` picks, per
  correspondence, the neighbour minimising the max-reprojection-error — the `max_j`
  of Eq. 11 ✅. The **product over reference views** `Π_i` has no direct counterpart; each
  reference contributes its own Gaussians independently and they are concatenated
  `[repo: corr_init.py:673-686]`. `[inferred]`
- **Purpose of the `max`:** a correspondence needs to be good in *one* view pair, not all —
  otherwise occlusion in any single neighbour would veto it.

### Scale seeding — `scale = ‖μ − campos‖ · 0.001`, then `× 0.5`

- **No formula in the paper**; §1 and §3.2 claim only "well-informed color, scale, and
  position".
- **Repo** `[repo: corr_init.py:668-670]`: isotropic, proportional to distance from the
  reference camera — i.e. **constant angular footprint**, roughly one pixel-cone wide.
  Then every scale is halved `[repo: trainer.py:254]`.
- **Why distance-proportional:** each Gaussian is seeded from *one pixel*, so its
  world-space extent should scale with depth to cover a constant solid angle. Uniform
  scales would make distant Gaussians enormous and near ones invisible. `[inferred]`

### The convergence argument (Figs. 2, 4) — the paper's mechanistic evidence

Not an ablation, but the strongest support for the central claim. Two measured
distributions `[paper Eqs. 14-15]`:
- **displacement** `‖g^x(0) − g^x(T)‖₂` and `‖g^c(0) − g^c(T)‖₂`;
- **trajectory length** `Σ_t ‖g^x(t) − g^x(t+1)‖₂`.

Result: EDGS reduces coordinate **displacement by ~50×** and coordinate **trajectory length
by ~30×**; colour trajectory length falls only ~2× "as small oscillations remain"
`[paper §4.5]`. This is a direct measurement of the stated mechanism ("shorter optimization
path"), not a proxy — the analogue of `mini-splatting/`'s use of Chamfer distance.

## 4.3 Reading the ablations

### Table 6 — component ablation: ⚠️ **direction is genuinely ambiguous**

`[paper Tab. 6]`, Mip-NeRF 360. Columns `p_ij^corr | p_ij^proj | SH Init.` are marked with
checkmarks that **do not survive PDF text extraction** (verified with both `pdftotext
-layout` and `-raw`), so the pattern cannot be read from the file:

| Row | PSNR | SSIM | LPIPS |
|---|---|---|---|
| EDGS (full) | **28.02** | 0.839 | **0.141** |
| w/o SH init. | 27.80 | **0.840** | 0.175 |
| w/o `p_ij^proj` | 27.72 | 0.830 | 0.179 |
| w/o `p_ij^corr` | 27.55 | 0.829 | 0.197 |
| baseline | 27.43 | 0.822 | 0.202 |

**Two readings are consistent with the row labels, and they license different claims:**

| Reading | What each row is | What you may say |
|---|---|---|
| **(A) Cumulative removal** (rows nest: full → −SH → −SH−proj → −SH−proj−corr → baseline) | supported by the strictly monotone PSNR decrease 28.02 → 27.80 → 27.72 → 27.55 → 27.43 and by "baseline" being the natural end of a ladder | "Removing SH init costs 0.22 dB; additionally removing `p^proj` costs a further 0.08 dB…" |
| **(B) Leave-one-out** (each row removes exactly one component from the full model) | supported by the literal row labels "w/o X" | "Removing `p^corr` alone costs 0.47 dB; removing `p^proj` alone costs 0.30 dB…" |

Per `../../research-methodology.md` §4 — *"Do not infer a leave-one-out claim from an
additive-ablation table"* — **I am not resolving this from the PDF text layer.** Inspect the
checkmark column visually in `../../EDGS.pdf` before citing Table 6, and state which reading
you used. Note that reading (A) is the more conservative one.

**Independent of the reading, two things hold:**
- ✅ The full model is best on PSNR and LPIPS, and every component helps.
- ✅ **LPIPS separates the rows far more than PSNR does**: 0.141 → 0.202 is a **43% relative
  degradation**, versus 0.59 dB of PSNR. If you cite one number, cite LPIPS.
- ⚠️ **SSIM is non-monotone** — "w/o SH init." (0.840) is *higher* than the full model
  (0.839). Within noise, but it means SH init cannot be claimed to help all three metrics.
- ⚠️ **And the SH-init row is not reproducible from this checkout at all** — §3.5 is
  unimplemented (D-1).

### Table 5 — matcher choice: **MUTUALLY-EXCLUSIVE VARIANTS**

`[paper Tab. 5]`, Mip-NeRF 360. Four complete retrainings, each swapping `M`:

| Matcher | PSNR | SSIM | LPIPS |
|---|---|---|---|
| 3DGS (reference) | 27.49 | 0.816 | 0.215 |
| LoFTR [62] | 27.79 | 0.818 | 0.179 |
| DKM [12] | 27.81 | 0.831 | 0.192 |
| RAFT [64] | **26.90** | 0.803 | 0.201 |
| **RoMa [13]** | **28.02** | **0.839** | **0.141** |

Neither additive nor leave-one-out — the third category.

- ✅ "All methods except RAFT achieve comparable performance" `[paper §4.5]` — accurate:
  LoFTR/DKM/RoMa span 0.23 dB.
- ✅ **RoMa's advantage is concentrated in LPIPS** (0.141 vs 0.179/0.192) far more than in
  PSNR (28.02 vs 27.79/27.81).
- ✅ RAFT underperforms *3DGS itself*, with a stated mechanism: it is an **optical-flow**
  model designed for small inter-frame baselines `[paper §4.5]`.
- **Actionable for you:** `../RoMaV2/` is a strictly newer matcher not evaluated here, and
  Table 5 is the template for evaluating it as a drop-in.

### Table 4 — densification necessity: **2×2 factorial, read as pairs**

| Method | Densification-free | PSNR | SSIM | LPIPS |
|---|---|---|---|---|
| 3DGS | ✓ | **25.60** | 0.709 | 0.367 |
| 3DGS | | 27.49 | 0.816 | 0.215 |
| EDGS | ✓ | 28.02 | 0.839 | 0.141 |
| EDGS | | 28.08 | 0.831 | 0.140 |

The cleanest ablation in the paper: **3DGS loses 1.89 dB without densification; EDGS gains
0.06 dB with it.** That asymmetry is the paper's central claim, stated as
"EDGS does not require densification and only marginally improves when densification is
applied" `[paper Tab. 4 caption]`. Note EDGS+densification has *worse* SSIM (0.831 vs
0.839) — the gain is not uniform.

### Table 3 — EDGS as an initializer: **paired A/B, drop-in**

Covered in [`01-taxonomy.md`](01-taxonomy.md). Improves AbsGS (+0.12 dB), 3DGS-MCMC
(+0.14 dB) and Taming 3DGS (+0.36 dB) with **no hyperparameter tuning** `[paper Tab. 3]`.
Note the paper explicitly says it "intentionally initialize[s] with fewer Gaussians in this
experiment to allow ADC methods to further refine the scene" `[paper §4.3]` — so Table 3
does **not** use the same `init_wC` settings as Table 1. Do not cross-reference their `#G`.

### Figure 6 — saturation curves

Three parameters swept independently: number of reference views, nearest neighbours, and
correspondences per reference. All three **saturate** `[paper Fig. 6]`. This is the honest
justification for the defaults (180 / 3 / 15 000) and a useful cost/quality knob — but the
values are published only as a plot. `[unverified]` for exact numbers.
