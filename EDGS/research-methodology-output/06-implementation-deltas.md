# §6 — Implementation deltas from the paper

**Repo state inspected:** `github.com/CompVis/EDGS`, HEAD
`f90b022445fc88368f75e66e8fb34aea88372cac`, branch `main`, 2026-07-04. No tags.

**⚠️ The code is ~10 months older than the paper.** `git log` shows exactly one
code-bearing commit, **`668e280` "Init public code" (2025-04-21)**; `git diff --stat
668e280 HEAD` touches only `LICENSE.txt`, `README.md` and a removed `submodules/vggt`
pointer. The README states: *"**2026-03-25: Updated training code will be released
soon.**"* — it has not been.

**Paper inspected:** `../../EDGS.pdf` = **arXiv:2504.13204v2**, 12 Feb 2026 (CVPR 2026).
The released code therefore corresponds to **arXiv v1** (Apr 2025).

🔶 marks deltas plausibly explained by this v1→v2 gap.

**Files read directly:** `train.py`, `source/trainer.py`, `source/corr_init.py`,
`source/losses.py`, `source/utils_aux.py`, `configs/train.yaml`, `configs/gs/base.yaml`,
`install.sh`, `README.md`, plus `git log`/`git diff`.

---

## D-1 — **§3.5 (spherical-harmonics initialization) is not implemented** 🔶

`[paper §3.5, Eqs. 12-13]` describes fitting the 15 higher-order SH coefficients per splat
by least squares over `n` multi-view RGB observations:
> `Ĥ_k = argmin_{H∈ℝ^{16×3}} ‖Y_k H − O_k‖_F²`, and `Ĥ_k = Y_k^+ O_k` via the
> Moore–Penrose pseudoinverse when `n < 16`, "ensuring stable estimation under limited
> observations."

`[repo: source/corr_init.py:659]` (and identically at `:871` in the `_fast` variant):
```python
all_new_features_rest.append(torch.stack([gaussians._features_rest[-1].clone().detach() * 0.] * N, dim=0))
```
**`f_rest` is set to zero.** Only the DC term is initialized, from the reference pixel colour
`[repo: corr_init.py:658]`.

Verification: `grep -rn "pinv\|lstsq\|pseudoinv" source/` returns **one** hit —
`corr_init.py:472`, which is `torch.linalg.lstsq` solving the **triangulation** system of
`[paper Eq. 7]`, not the SH system of Eq. 12. There is no SH basis evaluation anywhere;
the only SH import is `RGB2SH` `[repo: corr_init.py:18]`.

**Consequence: Table 6's `SH Init.` row cannot be reproduced from this checkout** — the
"w/o SH init." configuration *is* what the code does.

**Severity: high.** Almost certainly the v1/v2 gap (§3.5 and Table 6 look like v2
additions), which is exactly what the pending "updated training code" would fix.

---

## D-2 — `p^proj` is an **opacity mask**, not a sampling distribution

`[paper Eq. 10]`: `p_ij^proj ∝ U{k : ε_ij^k < τ_proj}` — a distribution over which
correspondences to *select*.

`[repo: source/corr_init.py:660-666]`:
```python
# new version that sets points with large error invisible
# TODO: remove those points instead. However it doesn't affect the performance.
mask_bad_points = torch.tensor(
    NNs_triangulated_points_selected_proj_errors > keypoint_fit_error_tolerance,
    dtype=torch.float32).unsqueeze(1).to(device)
all_new_opacities.append(torch.stack([gaussians._opacity[-1].clone().detach()] * N, dim=0) * 0.
                         - mask_bad_points * (1e1))
```

Failing points are **kept** with opacity logit `−10` (α ≈ 4.5e-5) and left for the
`α < 0.005` prune `[repo: trainer.py:261]`. Functionally similar; structurally different —
and it means the **initial** Gaussian count is inflated relative to what Eq. 10 implies.
The source comment shows the authors are aware of the discrepancy.

**Severity: medium.**

---

## D-3 — Undocumented **continuous opacity decay** replaces 3DGS's opacity reset

`[repo: source/trainer.py:81-85]`:
```python
if train_cfg.reduce_opacity:
    if self.gs_step < self.training_config.densify_until_iter and self.gs_step % 10 == 0:
        opacities_new = torch.log(torch.exp(self.GS.gaussians._opacity.data) * 0.99)
        self.GS.gaussians._opacity.data = opacities_new
```
`reduce_opacity` defaults to **`True`** `[repo: configs/train.yaml]`. Since `_opacity` is a
logit, this is `logit − log(1/0.99) ≈ logit − 0.01005`, applied every 10 steps for the first
15 000 steps ⇒ ~1500 applications, cumulative ≈ **−15**.

Meanwhile `reset_opacity()` **never fires**: `opacity_reset_interval = 30000` equals
`iterations` `[repo: configs/gs/base.yaml]`, and the call is additionally gated by
`gs_step < densify_until_iter = 15000` `[repo: trainer.py:195-205]`.

So 3DGS's periodic reset has been swapped for a smooth decay-and-cull. `opacity_lr` is also
**halved** (0.025 vs 3DGS's 0.05) `[repo: configs/gs/base.yaml]`, presumably tuned against
it. **None of this is in the paper.**

**Severity: high** — this is a real optimization-algorithm change, and the paper's
contribution 3 claims "without modifying the optimization algorithm" `[paper §1]`.

---

## D-4 — Undocumented **learning-rate clamp**

`[repo: source/trainer.py:146-147]`:
```python
if max_lr:
    self.GS.gaussians.update_learning_rate(max(self.gs_step, 8_000))
```
`max_lr` defaults to **`True`** `[repo: configs/train.yaml]`. The exponentially-decaying
position LR is clamped to its step-8000 value, so EDGS never uses 3DGS's high early LR.

Well-motivated by the paper's own Fig. 4 argument (Gaussians start ~50× closer to their
final positions, so large early steps would scatter a good initialization) — but
undocumented, and a second departure from "we don't modify the optimization algorithm".

**Severity: high.**

---

## D-5 — Reference views are selected by **K-means over pose matrices**

`[paper §3.2]`: "we identify neighboring images … that have **maximal overlap** with `I_i`,
based on camera parameters and spatial proximity. We measure proximity between camera
matrices using the **Frobenius norm**."

`[repo: source/corr_init.py:553-561]`:
```python
viewpoint_cam_all = torch.stack([x.world_view_transform.flatten() for x in viewpoint_stack], axis=0)
selected_indices  = select_cameras_kmeans(cameras=..., K=NUM_REFERENCE_FRAMES)   # ← k-means
closest_indices   = k_closest_vectors(viewpoint_cam_all, NUM_NNS_PER_REFERENCE)  # ← Frobenius
```

The **neighbour** step matches the paper ✅. The **reference-selection** step —
`scipy.cluster.vq.kmeans` over flattened 4×4 pose matrices, keeping the member nearest each
cluster centre `[repo: corr_init.py:65-97]` — is not described at all. It is a sensible
coverage-maximising choice, and it is why `num_refs` behaves as a *coverage* budget rather
than a "first N views" budget.

**Severity: medium.**

---

## D-6 — Undocumented scale seeding and a global **×0.5**

`[repo: source/corr_init.py:668-670]`:
```python
dist_points_to_cam1 = torch.linalg.norm(viewpoint_cam1.camera_center - new_xyz, dim=1, ord=2)
all_new_scaling.append(gaussians.scaling_inverse_activation((dist_points_to_cam1 * scaling_factor).unsqueeze(1).repeat(1, 3)))
```
— isotropic, proportional to distance from the reference camera, `scaling_factor = 0.001`.

Then `[repo: source/trainer.py:252-254]`:
```python
gaussians._scaling = gaussians.scaling_inverse_activation(gaussians.scaling_activation(gaussians._scaling) * 0.5)
```
— **every** scale halved immediately after initialization.

The paper claims "well-informed color, **scale**, and position" `[paper §1]` but gives no
formula for scale anywhere.

**Severity: medium.**

---

## D-7 — Rotation is copied from an arbitrary existing Gaussian

`[repo: source/corr_init.py:671]`:
```python
all_new_rotation.append(torch.stack([gaussians._rotation[-1].clone().detach()] * N, dim=0))
```
Every new Gaussian inherits `_rotation[-1]` — the last SfM-initialized Gaussian's quaternion
(identity in practice). Harmless given isotropic initial scales, but it is a
"borrow whatever is at index −1" pattern, matched by the opacity template at `:666`.

**Severity: low.**

---

## D-8 — `τ_corr` is not exposed; RoMa's internal threshold is used

`[paper Eq. 9]` introduces `τ_corr`. There is no config key for it
`[repo: configs/train.yaml]`; the code uses `upper_thresh = roma_model.sample_thresh`
`[repo: corr_init.py:541]` — RoMa's own default. Swapping matchers (Table 5) therefore
silently changes the confidence operating point.

**Severity: medium** for the Table 5 comparison.

---

## D-9 — RoMa is reconfigured, disabling two of its features

`[repo: source/corr_init.py:538-539]`:
```python
roma_model.upsample_preds = False
roma_model.symmetric      = False
```
Both are RoMa defaults being turned **off** — no coarse-to-fine upsampling of predictions,
and one-directional rather than symmetric matching. Not mentioned in the paper, and directly
relevant if you swap in `../RoMaV2/`.

**Severity: medium.**

---

## D-10 — README contradicts the shipped config in two places

| Key | `configs/train.yaml` | README |
|---|---|---|
| `train.no_densify` | **`False`** | *"Disables densification. **True by default**."* |
| `wandb.mode` | **`"online"`** | *"Default: `"disabled"`"* |
| `train.gs_epochs` | **`0`** | `30000` in the command (training is a no-op without it) |
| `init_wC.matches_per_ref` | `15_000` | `20000` in the command, `15_000` in the override example |

`[repo: configs/train.yaml vs README.md]`. The `no_densify` one matters most: the paper's
headline configuration is densification-free, but a bare `python train.py` **densifies**.

**Severity: medium**, high trap value.

---

## D-11 — `batch_size: 64` is read but never used

`[repo: source/trainer.py:48]` stores `self.batch_size = training_config.batch_size`, and
nothing reads it. `train_step_gs` samples **one** camera per step
`[repo: trainer.py:155-157]`, exactly as stock 3DGS. Dead config key — possibly a remnant of
the unreleased updated trainer.

**Severity: low**, high trap value (it suggests batched training that does not happen).

---

## D-12 — `eval` is hard-coded `False` in the emitted `cfg_args`

`[repo: train.py:38]` writes `"eval": False` into the `cfg_args` file that downstream 3DGS
tooling reads, and `[repo: configs/gs/base.yaml]` also has `dataset.eval: false`. Since
`[paper §4.1]` reports held-out test metrics, the evaluation path must set this elsewhere
(`full_eval.py` `[repo: full_eval.py]`, not read in depth this pass). Same class of trap as
`seasplat/`'s `--eval` default. `[unverified]` how the paper's splits were obtained.

**Severity: medium** for reproduction.

---

## D-13 — Ablation-table semantics

Three distinct kinds, none of them leave-one-out with certainty:

| Table | Kind |
|---|---|
| **Tab. 6** | ⚠️ **ambiguous** — row labels say "w/o X" (leave-one-out) but the monotone PSNR ladder and the "baseline" terminal row suggest **cumulative removal**. The checkmark column **does not survive PDF text extraction** (verified with `pdftotext -layout` and `-raw`), so I did not resolve it. See [`04-loss.md`](04-loss.md) §4.3 |
| **Tab. 5** | mutually-exclusive **variants** (four matchers) |
| **Tab. 4** | a **2×2 factorial** (method × densification) |
| **Tab. 3** | paired **A/B** with a *different* `init_wC` setting than Tab. 1 — "we intentionally initialize with fewer Gaussians in this experiment" `[paper §4.3]`. Do not cross-reference `#G` between them |

**Severity: medium.**

---

## Items I could *not* verify in this pass

| Claim | Status |
|---|---|
| Table 6's checkmark pattern | `[unverified]` — inspect `../../EDGS.pdf` visually |
| Whether the paper's numbers came from this code | `[unverified]` — the code is arXiv-v1-era; §3.5 is absent, so **the v2 numbers cannot have come from this checkout** |
| Time breakdown of initialization vs optimization | `[unverified]` — "see Sec. A for time break-down" `[paper §4.1]`; the appendix was not read this pass |
| Exact values behind Fig. 6's saturation curves | `[unverified]` — published as a plot |
| `full_eval.py` / `metrics.py` split handling | `[unverified]` — not read in depth |
| The removed `submodules/vggt` | `[unverified]` — hints at an unreleased VGGT-based initialization variant `[repo: git diff --stat 668e280 HEAD]` |
| Per-scene results (Sec. G) | `[unverified]` — appendix not read |
