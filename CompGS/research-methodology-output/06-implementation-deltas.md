# §6 — Implementation deltas from the paper

**Repo state inspected:** `github.com/LiuXiangrui/CompGS`, commit
`d501617323606b769246eafc1fb8472a61859e1d`, branch `main`, 2024-11-07. No tags.

**Paper inspected:** `../../CompGS.pdf` = **arXiv:2404.09458v1**, 15 Apr 2024.
(The file was replaced on 2026-08-25; it previously held the `../compact3d/` paper — see
[`00-index.md`](00-index.md).)

🔶 **Version caveat.** The repo's BibTeX cites the **ACM MM 2024** camera-ready
`[repo: README.md]`, which I could not obtain; the commit is ~7 months after arXiv v1.
Deltas that could plausibly be v1-vs-camera-ready drift are marked 🔶. Deltas involving
undocumented *code-level* machinery (extra loss terms, frozen parameters, warm-ups) are
unlikely to be explained by revision drift, since a camera-ready would normally add such
detail rather than remove it.

**Files read directly:** `Train.py`, `Modules/TrainerCompGS.py`, `Modules/TesterCompGS.py`,
`Modules/GaussianModels/Model.py`, `Modules/GaussianModels/Modules/Prediction.py`,
`Modules/GaussianModels/Modules/EntropyModel.py`,
`Modules/Optimization/AdaptiveControl.py`, `Modules/Common/Datasets.py`,
`Configs/*.yaml`, `Scripts/derive_train_eval_scripts.py`, `README.md`.

---

## D-1 — The "affine transform" is Scaffold-GS offset prediction, with **two** MLPs not three

`[paper Eqs. 2-4]` describes a general affine warp:
> `μ_k, Σ_k = A(μ_ω, Σ_ω | θ_k)`, decomposed into a translation vector `t_k`, a scaling
> matrix `S_k` and a rotation matrix `R_k`, each from its own network:
> `t_k = 𝒯(h_k)`, `S_k = 𝒮(h_k)`, `R_k = ℛ(h_k)`, giving `μ_k = μ_ω + t_k`, `Σ_k = S_k R_k`.

`[repo: Modules/GaussianModels/Modules/Prediction.py:24-25, 49-50, 69, 76-78]`:
```python
self.means_pred_mlp      = ResidualMLP(in_dim=40, internal_dim=32, out_dim=3, num_res_layer=1)
self.covariance_pred_mlp = ResidualMLP(in_dim=40, internal_dim=32, out_dim=7, num_res_layer=1)
...
means_scaling_factor, scales_scaling_factor = torch.chunk(scaling_factors, dim=-1, chunks=2)
means   = means + means_offset * means_scaling_factor          # ← modulated by the ANCHOR's scale
scales  = torch.sigmoid(pred_covariance[:, :3]) * scales_scaling_factor
rotations = F.normalize(pred_covariance[:, 3:])
```

Four differences:

1. **Two geometry MLPs, not three.** Scale and rotation share one 7-channel head.
2. **Both the offset and the scale are modulated by the anchor's own learned 6-D scaling
   vector `exp(s_ω)`** — the `means_scaling_factor`/`scales_scaling_factor` split. Eq. 4
   (`μ_k = μ_ω + t_k`) has no such factor. This is Scaffold-GS's offset mechanism verbatim.
3. **Scale is `sigmoid`-bounded** relative to the anchor scale — an upper bound Eq. 3 does
   not express.
4. `[paper Eq. 4]` writes `Σ_k = S_k R_k`, which is not a valid covariance factorisation
   (a covariance is `R S Sᵀ Rᵀ`). The repo never forms `Σ`; it hands scale + quaternion to
   the rasterizer.

**Severity: high** — a reimplementation from Eqs. 2–4 would build a different, and probably
worse-conditioned, geometry model. 🔶 possible but unlikely to be v1 drift.

---

## D-2 — A **third loss term** exists that the paper never mentions

`[paper Eq. 1]`: `L = λR + D`. Two terms.

`[repo: Modules/TrainerCompGS.py:220, 229]`:
```python
reg_loss = 0.01 * render_results.scales.prod(dim=1).mean()
loss = rendering_loss + reg_loss + (rate_loss if iteration > 3000 else 0.)
```

A **volume regulariser** on the product of the three scale components, weight hard-coded at
`0.01`, exposed in no config. Inherited from Scaffold-GS.

This is not cosmetic: because `R` is in the loss, larger Gaussians are *rewarded* (fewer
primitives ⇒ fewer bits), so `REG` is the only term making volume expensive. See
[`05-constraints.md`](05-constraints.md) D-4/M-6.

**Severity: high.** Never ablated, never mentioned.

---

## D-3 — A **second optimizer and a second backward pass** (`aux_loss`)

`[repo: Modules/TrainerCompGS.py:184, 235-236, 299-300]`:
```python
aux_optimizer = WarpedAdam(self.gaussian_model.network.get_lr_aux_param_pairs(), lr=0., eps=1e-15)
...
aux_loss = self.gaussian_model.aux_loss
aux_loss.backward()
...
self.aux_optimizer.step(); self.aux_optimizer.zero_grad(set_to_none=True)
```

Standard CompressAI practice — the factorized entropy bottleneck's CDF parameters are fitted
by their own objective. Mandatory for the rate estimate to match reality, and **entirely
absent from the paper**, which presents a single objective (Eq. 1) and a single Adam
(§3.4).

**Severity: high for reproduction.**

---

## D-4 — The rate term is **gated off for the first 3 000 iterations**

`[repo: Modules/TrainerCompGS.py:226-229; Configs/*.yaml rate_loss_start_iteration: 3000]`.

`[paper Eq. 1]` presents a single objective active throughout. A 10% warm-up with **zero
rate pressure** is a materially different optimization, and — given that `R → 0` is a
genuine collapse mode (see [`05-constraints.md`](05-constraints.md) D-1) — plausibly
necessary for stability.

**Severity: high.**

---

## D-5 — MLP depth: mostly **one** residual layer, not "two"

`[paper §3.4]`: "Neural networks used in both prediction and entropy estimation are
implemented by **two** residual multi-layer perceptrons."

`[repo: Prediction.py:24-29]`: `num_res_layer=1` for means, covariance and opacity;
`num_res_layer=2` only for colour.
`[repo: EntropyModel.py:230]`: `num_res_layer=2` for the scale entropy model's `h_s`.

So the claim holds for parts of the entropy stack and for the colour head, and not for the
three other prediction heads.

**Severity: low–medium** 🔶 — plausibly loose phrasing, or v1 drift.

---

## D-6 — Anchor means are **frozen** (`lr = 0`)

`[repo: Configs/MipNeRF360.yaml, TanksAndTemplates.yaml, DeepBlending.yaml]`:
```yaml
means_lr_init: 0.0
means_lr_final: 0.0
means_lr_delay_mult: 0.0
```

`[paper §3.4]` says anchors "are initialized from sparse point clouds produced by
voxel-downsampled SfM points [36]" — which does not say they never move. Everywhere else in
the 3DGS literature, means *are* optimized.

Load-bearing three ways (gauge fixing, lossless G-PCC validity, rate reduction) — see
[`05-constraints.md`](05-constraints.md) M-5. Note also that
`[repo: Model.py:315]` **asserts** no duplicate voxelized means, which a moving anchor could
violate.

**Severity: high.**

---

## D-7 — Adaptive-control intervals scale with the **number of training views**

`[repo: Modules/TrainerCompGS.py:284-304]`:
```python
num_training_views = len(self.dataset)
aux_update_enable       = cfg['update_aux_start_base_interval'] * num_training_views < iteration < stop_iteration
adaptive_control_enable = (cfg['control_start_base_interval'] * num_training_views < iteration < stop_iteration
                           and iteration % (cfg['control_base_interval'] * num_training_views) == 0)
```
with bases `3`, `5`, `2` `[repo: Configs/*.yaml]`.

So on a 50-view scene, control runs every 100 iterations; on a 300-view scene, every 600 —
a **6× difference in densification frequency** at the same iteration budget. The paper says
only "adaptive control [27] is applied" `[paper §3.4]`.

**Severity: medium**, and a real reproduction hazard on new datasets.

---

## D-8 — Per-dataset hyperparameters, none of them in the paper

| Parameter | Mip-NeRF 360 | Tanks&Templates | Ratio |
|---|---|---|---|
| `voxel_size` | **0.001** | **0.01** | **10×** |
| `grad_threshold` | 1e-4 | 8e-5 | 1.25× |
| `opacity_threshold` | 8e-4 | 5e-4 | 1.6× |

`[repo: Configs/MipNeRF360.yaml vs Configs/TanksAndTemplates.yaml]`. `voxel_size` directly
sets the initial anchor count and the G-PCC grid resolution — a 10× difference is a major
tuning decision.

**Severity: medium.**

---

## D-9 — Reported `num_gaussians` counts **anchors only**

`[repo: Modules/TrainerCompGS.py:367]`: `'num_gaussians': self.gaussian_model.num_anchor_primitive`
`[repo: README.md]`: "`num_gaussians`: number of **anchor primitives**."

The number actually rasterized is up to `10×` larger (`K = 10`, minus the `α ≤ 0` cull).
Every other method in your comparison set reports rendered primitives.

**Severity: high for cross-method comparison**, though the repo's README is explicit —
this is a naming trap rather than a misrepresentation.

---

## D-10 — Opacity is `Tanh`-activated with a `> 0` **view-dependent cull**

`[repo: Prediction.py:28, 61, 65]`:
```python
self.opacity_pred_mlp = ResidualMLP(..., tail_activation=nn.Tanh())
pred_opacities = self.opacity_pred_mlp(feats)
coupled_primitive_mask = (pred_opacities > 0.).view(-1)
```

`[paper Eq. 5]` says only `α_k = 𝒪(γ ⊕ h_k)`. Opacity ranging over `[−1, 1]` with negative
values meaning "does not exist" is Scaffold-GS's mechanism. Consequence: **the rasterized
primitive set is a function of the viewing direction**, which no other method here has.

**Severity: medium** (behaviour-relevant; unstated).

---

## D-11 — `s_Σ` is a learnable **6-vector**, not a scalar

`[paper §3.4]`: "`s_Σ` is a learnable parameter with an initial value of 0.01."
`[repo: EntropyModel.py:220, 228]`: `nn.Parameter(torch.ones(6) * 0.01, requires_grad=True)`
— one step per scale dimension.

**Severity: low.**

---

## D-12 — View features are **4-D and anchor-level**

`[repo: Prediction.py:27, 53-57]`: `view_feats_dim = 4` = direction (3) + distance (1),
computed from the **anchor** mean and then `repeat`-broadcast to all `K` coupled primitives.

`[paper §3.2]` says only "view embeddings γ are generated from camera poses". So all 10
coupled primitives of an anchor share one view feature — they cannot differ in
view-dependence. Scaffold-GS's design, unstated here.

**Severity: low–medium.**

---

## D-13 — Only λ = 0.001 ships in the configs

`[repo: Configs/*.yaml lambda_weight: 0.001]` — the **lowest-rate-penalty / highest-quality**
point. The other two operating points of `[paper §3.4]` come from
`[repo: Scripts/derive_train_eval_scripts.py:47-52]`, which overrides `lambda_weight` to
`0.005` and `0.01`.

Anyone running `Train.py` with a bare config reproduces only the top row of each results
table.

**Severity: low**, high trap value.

---

## D-14 — SSIM implementation is `pytorch_msssim`, not 3DGS's

`[repo: TrainerCompGS.py:9, 216; TesterCompGS.py:9, 162]` — `from pytorch_msssim import ssim`,
called with `data_range=1., size_average=True`. 3DGS and every other 3DGS-derived folder in
your set (`seasplat/`, `mini-splatting/`, `compact3d/`) use their own 11×11 σ=1.5
implementation. The defaults coincide, so values should be close, but the code paths differ.

**Severity: low.**

---

## D-15 — Metrics go through an 8-bit PNG disk round-trip

`[repo: TesterCompGS.py:71-75, 153-159]` (and identically in
`[repo: TrainerCompGS.py:144-161]`): render → `PIL.Image.save(...png)` →
`PIL.Image.open(...)` → `/255.` → `F.mse_loss` → `10·log₁₀(1/MSE)`.

So (a) 8-bit quantisation before scoring, and (b) **pooled-MSE PSNR** — the
`seathru_NeRF/` convention, **not** the per-channel-mean convention of 3DGS,
`seasplat/`, `mini-splatting/` and `compact3d/`. Since Tables 1–3 compare directly against
`Navaneet et al. [33]` (= `compact3d/`), whose codebase computes per-channel-mean PSNR,
**the baselines' numbers were recomputed here** — the paper says each method "undergoes five
independent evaluations in a consistent environment" `[paper §4.1]`, which suggests they
were re-run, but does not say whether the metric code was unified. `[unverified]`

**Severity: medium.**

---

## Items I could *not* verify in this pass

| Claim | Status |
|---|---|
| **The ACM MM 2024 camera-ready text** | `[unverified]` — only arXiv v1 obtained. All 🔶 items hinge on this. |
| GPU used for Table 7 timings | `[unverified]` — **the paper names no hardware at all** (grep for `GPU|RTX|A100|V100|NVIDIA|3090` over the full text returns nothing). |
| VRAM usage | `[unverified]` — not reported. |
| Whether Eq. 1's `arg max` is a typo or an extraction artifact | `[unverified]` — §3.1 prose says "minimization"; the repo minimizes. |
| Actual coded size vs. estimated `R` | `[unverified]` — the repo measures the real `.npz` size `[repo: Model.py:337]` but the paper never compares it to the entropy estimate. |
| CUDA rasterizer modifications | `[unverified]` — `submodules/diff-gaussian-rasterization` not read; the paper says "volume splatting [44] is implemented by custom CUDA kernels [17]" `[paper §3.4]`, implying it is stock 3DGS. |
| Per-scene appendix numbers | `[unverified]` — "provided in the Appendix" `[paper §4.1, §4.2]`, which is not in the arXiv v1 PDF. |
