# §3 — Formal variable table

`N` = number of **anchor** primitives (grows/shrinks under adaptive control).
`K = 10` = coupled primitives per anchor (`derive_factor`).
`M` = number of training views. Rendered Gaussians ≤ `N·K` (opacity-culled).

> ⚠️ `[paper …]` = **arXiv:2404.09458v1** = `../../CompGS.pdf`.

---

## 3.1 Independent variables (directly optimized)

### Group 1 — Anchor primitives `ω` (per-anchor tensors)

| Symbol | Repo name | Shape | Initialization | lr (Mip-NeRF 360 config) | Source |
|---|---|---|---|---|---|
| `μ_ω` | `means` | `(N, 3)` | centres of voxelized SfM points, `voxel_size = 0.001` (M360) / `0.01` (T&T, DB) | **`0.0` → `0.0`** — **FROZEN** | `[paper §3.4]` `[repo: Model.py:294; Configs/*.yaml]` |
| `s_ω` | `scales_before_exp` | `(N, 6)` | `log(voxel_size)·1₆` for new anchors | `0.007` → `0.007` (**constant, no decay**) | `[repo: AdaptiveControl.py:93; Configs/*.yaml]` |
| `q_ω` | `rotations_before_norm` | `(N, 4)` | identity `[1,0,0,0]` | `0.002` → `0.002` (**constant**) | `[repo: AdaptiveControl.py:94-95]` |
| `f_ω` | `ref_feats` | `(N, 32)` | learned; for new anchors, `scatter_max` over the parent coupled primitives' `f_ω` | `0.0075` → `5e-5` | `[paper §3.4]` `[repo: AdaptiveControl.py:97-98]` |
| `g_k` | `res_feats` | `(N, K, 8)` = `(N, 10, 8)` | **zeros** for new anchors | `0.0075` → `5e-5` | `[paper §3.4]` `[repo: AdaptiveControl.py:100]` |

> **`μ_ω` is frozen.** All three configs set `means_lr_init = means_lr_final =
> means_lr_delay_mult = 0.0` `[repo: Configs/MipNeRF360.yaml, TanksAndTemplates.yaml,
> DeepBlending.yaml]`. Anchors sit permanently on the initial voxel grid. This is the
> precondition for the lossless integer-grid G-PCC coding and the
> `assert torch.unique(means).shape[0] == means.shape[0]` at `[repo: Model.py:315]`.
> **The paper never mentions it.**
>
> **`s_ω` and `q_ω` have no LR decay** (`init == final`), unlike every other group. Also
> undocumented.

### Group 2 — Prediction networks (`PredictionNetwork`)

| Repo name | Architecture | lr | Source |
|---|---|---|---|
| `means_pred_mlp` | `ResidualMLP(40 → 32 → 3)`, **1** residual layer, no tail activation | `2e-3` → `2e-5` | `[repo: Prediction.py:24]` |
| `covariance_pred_mlp` | `ResidualMLP(40 → 32 → 7)`, **1** residual layer | `4e-3` → `4e-5` | `[repo: Prediction.py:25]` |
| `opacity_pred_mlp` | `ResidualMLP(44 → 32 → 1)`, **1** residual layer, **`Tanh`** tail | `2e-3` → `2e-5` | `[repo: Prediction.py:28]` |
| `color_pred_mlp` | `ResidualMLP(44 → 32 → 3)`, **2** residual layers, `Sigmoid` tail | `8e-3` → `8e-5` | `[repo: Prediction.py:29]` |

> `[paper §3.4]` states "Neural networks used in both prediction and entropy estimation are
> implemented by **two** residual multi-layer perceptrons." The repo uses **1** residual
> layer for three of the four prediction heads and **2** only for colour. See D-5.

### Group 3 — Entropy models (`EntropyModel`)

| Repo class | Role | lr | Source |
|---|---|---|---|
| `ReferenceFeatureEntropyModel` | hyperprior (`ref_hyper_dim = 4`) + conditional Gaussian for `f_ω` | `2e-4` → `1e-5` | `[paper Eqs. 8-9]` `[repo: EntropyModel.py:13-104]` |
| `ResidualFeatureEntropyModel` | hyperprior (`res_hyper_dim = 1`) + conditional Gaussian for `g_k`, **conditioned on `f̃_ω`** | `2e-4` → `1e-5` | `[paper Eqs. 11-12]` `[repo: EntropyModel.py:106-217]` |
| `ScaleEntropyModel` | conditional Gaussian for `s_ω`, conditioned on `f̃_ω`; `h_s` is `ResidualMLP(32→32→12)`, **2** residual layers | `2e-4` → `1e-5` | `[paper Eq. 10]` `[repo: EntropyModel.py:219-250]` |
| `s_Σ` (`quant_step`) | **learnable**, `nn.Parameter(ones(6) * 0.01)` — a **6-vector**, one per scale dim | (in the above group) | `[paper §3.4]` `[repo: EntropyModel.py:228]` |

### Group 4 — Auxiliary parameters (a **second optimizer**)

| Repo name | Role | Source |
|---|---|---|
| entropy-bottleneck CDF parameters | fitted by `aux_loss`, optimized by `aux_optimizer` (`WarpedAdam`) | `[repo: TrainerCompGS.py:184, 235-236, 299-300]` |

Standard CompressAI practice; **absent from the paper**. See D-3.

---

## 3.2 Dependent variables (derived each forward pass)

| Symbol | Shape | Definition | Source |
|---|---|---|---|
| `h_k` | `(N·K, 40)` | `f_ω ⊕ g_k` — prediction features | `[paper §3.2]` `[repo: Prediction.py:46-47]` |
| view feats | `(N·K, 4)` | `[dir(3), dist(1)]` from `μ_ω − campos`; **computed per anchor, broadcast to all K** | `[paper §3.2]` `[repo: Prediction.py:53-57]` |
| `Δμ_k` | `(N·K, 3)` | `means_pred_mlp(h_k)` | `[paper Eq. 3 `t_k`]` `[repo: Prediction.py:49]` |
| `μ_k` | `(·, 3)` | `μ_ω + Δμ_k ⊙ exp(s_ω[0:3])` | `[paper Eq. 4]` `[repo: Prediction.py:76]` |
| `scales_k` | `(·, 3)` | `sigmoid(out[:, :3]) ⊙ exp(s_ω[3:6])` | `[repo: Prediction.py:77]` |
| `q_k` | `(·, 4)` | `F.normalize(out[:, 3:])` | `[repo: Prediction.py:78]` |
| `α_k` | `(N·K, 1)` | `Tanh(opacity_pred_mlp(h_k ⊕ view))` ∈ `[−1, 1]` | `[paper Eq. 5]` `[repo: Prediction.py:28, 61]` |
| `c_k` | `(·, 3)` | `Sigmoid(color_pred_mlp(h_k ⊕ view))` | `[paper Eq. 5]` `[repo: Prediction.py:29, 62]` |
| `coupled_primitive_mask` | `(N·K,)` bool | `α_k > 0` — everything else is **culled before rasterization** | `[repo: Prediction.py:65]` |
| `f̃_ω, Σ̃_ω, g̃_k` | — | noise-perturbed (train) or STE-quantized (eval) versions | `[paper Eqs. 6-7]` `[repo: EntropyModel.py]` |
| `bpp` | dict of scalars | per-component estimated bitrate | `[paper Eqs. 9-13]` `[repo: TrainerCompGS.py:223]` |
| `accumulated_grads`, `coupled_denorm`, `accumulated_opacities`, `anchor_denorm` | — | adaptive-control statistics, released at iteration 15 000 | `[repo: Model.py:112-140; TrainerCompGS.py:292-293]` |

> **`Tanh` opacity + `> 0` cull is Scaffold-GS's mechanism**, not stated in the paper.
> It means roughly half of the `N·K` candidate primitives can vanish on any given view, and
> the set that is rasterized is **view-dependent** — a property no other method in the
> comparison set has.

---

## 3.3 Fixed / given inputs

### Data

| Quantity | Value | Source |
|---|---|---|
| Datasets | Tanks&Templates [19], Deep Blending [12], Mip-NeRF 360 [4] | `[paper §4.1]` |
| Scene selection & protocol | "we conform to the experimental protocols in 3DGS [17] … the scenes specified by 3DGS are involved" | `[paper §4.1]` |
| Initial points | **sparse point clouds provided by 3DGS**, voxel-downsampled | `[paper §3.4, §4.1]` |
| Split | "one view is selected from every eight views for testing" | `[paper §4.1]` = `[repo: Datasets.py:20, 45-46]` ✅ |
| `z_near`, `z_far` | `0.01`, `100` | `[repo: Datasets.py:20]` |

### Hyperparameters — from `Configs/*.yaml` (the shipped configs)

| Name | Mip-NeRF 360 | T&T | Deep Blending | Paper |
|---|---|---|---|---|
| `max_iterations` | 30 000 | 30 000 | 30 000 | not stated `[unverified]` |
| `ssim_weight` | 0.2 | 0.2 | 0.2 | "rendering loss [17]" ✅ |
| `lambda_weight` (**λ**) | **0.001** | **0.001** | **0.001** | `{0.001, 0.005, 0.01}` `[paper §3.4]` — configs ship only the *lowest*; the other two come from `Scripts/derive_train_eval_scripts.py:47-52` |
| `rate_loss_start_iteration` | **3 000** | 3 000 | 3 000 | ❌ **not in the paper** |
| `voxel_size` | **0.001** | **0.01** | — | ❌ per-dataset value not stated |
| `derive_factor` (**K**) | 10 | 10 | 10 | `K = 10` ✅ `[paper §3.4]` |
| `ref_feats_dim` | 32 | 32 | 32 | 32 ✅ |
| `res_feats_dim` | 8 | 8 | 8 | 8 ✅ |
| `ref_hyper_dim` | 4 | 4 | 4 | ❌ not stated |
| `res_hyper_dim` | 1 | 1 | 1 | ❌ not stated |
| `save_interval` | 10 000 | 10 000 | 10 000 | — |

### Adaptive control (Scaffold-GS rules; **per-dataset**, and not in the paper)

| Name | Mip-NeRF 360 | T&T | Meaning |
|---|---|---|---|
| `couple_threshold` | 40 | 40 | min. access count before a coupled primitive can seed a new anchor |
| `grad_threshold` | **1e-4** | **8e-5** | base gradient threshold; scaled `×2^level` |
| `opacity_threshold` | **8e-4** | **5e-4** | prune anchors below this mean accumulated opacity |
| `update_depth` | 3 | 3 | number of hierarchy levels |
| `update_hierarchy_factor` | 4 | 4 | voxel-size divisor per level |
| `update_init_factor` | 16 | 16 | level-0 voxel multiplier |
| `stop_iteration` | 15 000 | 15 000 | adaptive control ends |
| `update_aux_start_base_interval` | 3 | 3 | ×`M` views |
| `control_start_base_interval` | 5 | 5 | ×`M` views |
| `control_base_interval` | 2 | 2 | ×`M` views |

> **All control intervals are multiples of the number of training views `M`**, not fixed
> iteration counts `[repo: TrainerCompGS.py:287, 303-304]`. Densification frequency
> therefore scales inversely with dataset size — undocumented, and a real reproduction
> hazard.

### Quantization steps

| Step | Value | Paper | Repo |
|---|---|---|---|
| `s_f` (reference embeddings) | 1 (fixed) | ✅ `[paper §3.4]` | `[repo: EntropyModel.py:13-104]` — no explicit division |
| `s_g` (residual embeddings) | 1 (fixed) | ✅ | `[repo: EntropyModel.py:106-217]` |
| `s_Σ` (anchor scaling) | **learnable, init 0.01** | ✅ `[paper §3.4]` | `[repo: EntropyModel.py:220, 228]` — but a **6-vector**, not a scalar |

### Optimizer

Adam (`WarpedAdam`, `eps = 1e-15`) with per-group LRs and cosine annealing
`[paper §3.4]` `[repo: TrainerCompGS.py:182-184, 200-203]`. A **second** Adam
(`aux_optimizer`, also `eps = 1e-15`) trains the entropy-bottleneck CDF parameters
`[repo: TrainerCompGS.py:184]`.
