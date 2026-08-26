# Paper-vs-repo disagreements — EDGS

**Paper:** `../../EDGS.pdf` = arXiv:2504.13204**v2** (12 Feb 2026), CVPR 2026.
**Repo:** `CompVis/EDGS` @ HEAD **`f90b022`** (2026-07-04), but **all code is from
`668e280` (2025-04-21)** — the arXiv-v1 era. `git diff --stat 668e280 HEAD` touches only
`LICENSE.txt`, `README.md`, and a removed `submodules/vggt` pointer.
README: *"2026-03-25: Updated training code will be released soon."* — not yet shipped.

🔶 = plausibly explained by this ~10-month v1→v2 gap.

| # | Topic | Paper says | Repo does | Tags | Severity |
|---|---|---|---|---|---|
| D-1 | **SH initialization (§3.5)** | Eqs. 12-13: fit 16 SH coefficients per splat by least squares over `n` multi-view RGB observations; Moore–Penrose pseudoinverse when `n < 16` | **`f_rest ← 0`.** No SH basis evaluation anywhere; `grep "pinv\|lstsq"` finds only the *triangulation* solve at `corr_init.py:472`. **Table 6's `SH Init.` row is not reproducible** | `[paper §3.5, Eqs.12-13]` vs `[repo: corr_init.py:659, 871]` | **high** 🔶 |
| D-2 | **`p^proj`** | Eq. 10: a **sampling distribution** `U{k : ε_ij^k < τ_proj}` | an **opacity mask** — failing points are kept with logit `−10` (α ≈ 4.5e-5) and left for the `α<0.005` prune. Source comment: *"TODO: remove those points instead. However it doesn't affect the performance."* Inflates the post-init Gaussian count | `[paper Eq.10]` vs `[repo: corr_init.py:660-666]` | **medium** |
| D-3 | **Opacity handling** | not mentioned; §1 claims improvement "**without modifying the optimization algorithm**" | `reduce_opacity=True` (default): every 10 steps for 15 000 steps, `logit ← logit + log(0.99)` ⇒ cumulative ≈ **−15**. Meanwhile `reset_opacity()` is **unreachable** (`opacity_reset_interval = 30000 = iterations`, gated by `i < 15000`). `opacity_lr` also **halved** (0.025 vs 0.05) | `[paper §1]` vs `[repo: trainer.py:81-85, 195-205; configs/gs/base.yaml]` | **high** |
| D-4 | **Learning-rate schedule** | same claim as above | `max_lr=True` (default) ⇒ `update_learning_rate(max(step, 8000))` — the position LR is **clamped**, never using 3DGS's high early LR | `[paper §1]` vs `[repo: trainer.py:146-147]` | **high** |
| D-5 | **Reference-view selection** | §3.2: neighbours by "maximal overlap … Frobenius norm" (describes the *neighbour* step ✅) | the **reference views themselves** are chosen by **k-means over flattened `world_view_transform` matrices**, keeping the member nearest each cluster centre — undescribed | `[paper §3.2]` vs `[repo: corr_init.py:65-97, 555]` | **medium** |
| D-6 | **Scale seeding** | §1 claims "well-informed color, **scale**, and position"; no formula given | `scale = inv_act(‖μ − campos_ref‖ · 0.001)`, isotropic; then **every scale × 0.5** globally in the trainer | — vs `[repo: corr_init.py:668-670; trainer.py:252-254]` | **medium** |
| D-7 | **Rotation seeding** | not mentioned | copies `gaussians._rotation[-1]` — whatever quaternion sits at index −1 | — vs `[repo: corr_init.py:671]` | low |
| D-8 | **`τ_corr`** | Eq. 9 introduces a confidence threshold | **no config key**; the code uses `roma_model.sample_thresh`, i.e. RoMa's own default ⇒ swapping matchers (Table 5) silently moves the operating point | `[paper Eq.9]` vs `[repo: corr_init.py:541]` | **medium** |
| D-9 | **Matcher configuration** | §3.2 treats `M` as a black box | `roma_model.upsample_preds = False`, `roma_model.symmetric = False` — two RoMa defaults **disabled** | `[paper §3.2]` vs `[repo: corr_init.py:538-539]` | **medium** |
| D-10 | **README vs config** | — | `no_densify`: config `False`, README *"True by default"*. `wandb.mode`: config `"online"`, README *"Default: disabled"*. `gs_epochs`: config `0` (training is a no-op). `matches_per_ref`: config `15_000`, README command `20000` | `[repo: configs/train.yaml vs README.md]` | **medium**, high trap value |
| D-11 | **`batch_size: 64`** | — | read into `self.batch_size` at `trainer.py:48` and **never used**; `train_step_gs` samples **one** camera. Likely a remnant of the unreleased trainer | — vs `[repo: trainer.py:48, 155-157; configs/gs/base.yaml]` | low, high trap value |
| D-12 | **`eval` flag** | §4.1 reports held-out test metrics | `dataset.eval: false` in the config **and** `"eval": False` hard-coded into the emitted `cfg_args` at `train.py:38` ⇒ a bare README run trains on every view and finds an empty test set | `[paper §4.1]` vs `[repo: train.py:38; configs/gs/base.yaml]` | **medium** |
| D-13 | **PSNR convention** | §4.1: "Evaluation metrics include PSNR, SSIM, LPIPS" | `losses.py:psnr` is written for `(3,H,W)` (per-channel-mean, the 3DGS convention) but is **called with `(1,3,H,W)`** at `trainer.py:123`, which pools all channels ⇒ **pooled-MSE PSNR**, the `seathru_NeRF`/`CompGS` convention. The docstring says "NOT BATCHED!" | `[paper §4.1]` vs `[repo: losses.py:63-76 + trainer.py:123]` | **medium** |
| D-14 | **Ablation semantics** | Tabs. 3-6 all called ablations | **four different kinds**: Tab. 6 ⚠️ **direction ambiguous** (labels say leave-one-out, monotone ladder + terminal "baseline" row suggest cumulative removal; checkmarks do **not** survive `pdftotext -layout` **or** `-raw`); Tab. 5 = mutually-exclusive variants; Tab. 4 = 2×2 factorial; Tab. 3 = paired A/B **at a different `init_wC` setting than Tab. 1** ("we intentionally initialize with fewer Gaussians", §4.3) | `[paper §4.3, §4.5]` — `[inferred]`/`[unverified]` | **medium** |

## Claims that need a caveat when cited

| Claim | Caveat |
|---|---|
| "improves reconstruction **without modifying the optimization algorithm**" `[paper §1]` | True of the **loss** (2 terms, stock) and of **densification**. **Not** literally true of the schedule: `reduce_opacity` and `max_lr` are both on by default and undocumented (D-3, D-4). |
| "35% lower LPIPS" / "reaches 3DGS quality in 15% of training time" `[paper Fig. 1]` | **LPIPS-specific.** EDGS is **second-best on PSNR** on Mip-NeRF 360 (3DGS-MCMC 28.15 vs 28.02) and Deep Blending (ScaffoldGS 30.25 vs 29.81) `[paper Tab. 1]`. The paper says "best or **second-best**" — quote that. |
| "reaches 3DGS LPIPS in **25%** of training time" `[repo: README.md]` | Fig. 1 says **15%**. Different reference baselines (3DGS vs 3DGS\*). Say which. |
| "uses only **60%** of the splats" `[repo: README.md]` | Best case. Actual vs 3DGS\*: 88% (T&T), 68% (M360), 62% (DB) `[paper Tab. 1]`. |
| EDGS-5K "outperforms all competing methods" `[paper Tab. 2]` | On **two of three** metrics — its PSNR (26.88) is the **lowest in the table**. The caption is accurate; a one-line citation of it may not be. |
| Table 3 composability | ✅ Strong result (no hyperparameter tuning), but uses a **different `init_wC`** than Table 1 `[paper §4.3]` — do not cross-reference `#G` between the two tables. |
| Table 6 component contributions | ⚠️ **Direction unresolved** (D-14), **and** the `SH Init.` component does not exist in the released code (D-1). |
| Table 1 `#G` column | ⚠️ Not homogeneous — the paper's own footnote says ScaffoldGS's `#G` counts **derived splats from anchors**. Same trap as `../CompGS/`'s anchor-vs-rendered count. |

## Unverifiable in this pass

| Claim | Why |
|---|---|
| Table 6's checkmark pattern | `[unverified]` — glyphs survive neither `pdftotext -layout` nor `-raw`; inspect `../../EDGS.pdf` visually |
| Whether Table 1's numbers came from this checkout | `[unverified]` — **they cannot have**, since §3.5 is unimplemented (D-1). The v2 results presumably came from the unreleased updated code |
| Which code produced the reported PSNR | `[unverified]` — bears directly on D-13 |
| Initialization-vs-optimization time breakdown | `[unverified]` — "see Sec. A" `[paper §4.1]`; appendix not read |
| VRAM | `[unverified]` — never reported; peak is at initialization, not training `[inferred]` |
| Exact values behind Fig. 6's saturation curves | `[unverified]` — published as a plot |
| How `full_eval.py` / `metrics.py` set the split | `[unverified]` — not read in depth (bears on D-12) |
| The removed `submodules/vggt` | `[unverified]` — hints at an unreleased VGGT-based initialization variant `[repo: git diff --stat 668e280 HEAD]` |
| Per-scene results (Sec. G) | `[unverified]` — appendix not read |
