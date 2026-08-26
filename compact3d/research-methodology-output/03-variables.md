# §3 — Formal variable table

`N` = number of Gaussians (a few million; reduced by opacity pruning).
`K` = codebook size. `d` = per-group parameter dimensionality.

---

## 3.1 Independent variables (directly optimized)

**The non-quantized parameters are the ones that are optimized** — this is the defining
property of quantization-aware training: "In learning 3DGS, we **store the non-quantized
parameters**. In the forward pass … we quantize the parameters and replace them with the
quantized version (centroids) to do the rendering and calculate the loss. Then, we do the
backward pass to get the gradients for the quantized parameters and **copy the gradients to the
non-quantized parameters** to update them." `[paper §3]`

| Symbol | Repo | Shape | Quantized? | Codebook `K` | lr |
|---|---|---|---|---|---|
| `μ` (position) | `_xyz` | `(N, 3)` | ❌ **never** — "sharing them results in overlapping Gaussians" `[paper §3]` | — | 3DGS default |
| `α` (opacity) | `_opacity` | `(N, 1)` | ❌ — "a single scalar" `[paper §3]`; **but ℓ1-regularized** | — | 3DGS default |
| DC colour | `_features_dc` | `(N, 1, 3)`, `d = 3` | ✅ | `--kmeans_ncls_dc`, **4096** | 3DGS default |
| SH rest | `_features_rest` | `(N, 15, 3)`, `d = 45` | ✅ | `--kmeans_ncls_sh`, **4096** (default) / **512** (`run.sh`) | 3DGS default |
| Scale | `_scaling` | `(N, 3)`, `d = 3` | ✅ ⚠️ **before `exp`** | `--kmeans_ncls`, **4096** | 3DGS default |
| Rotation | `_rotation` | `(N, 4)`, `d = 4` | ✅ ⚠️ **before normalization** | `--kmeans_ncls`, **4096** | 3DGS default |

> `[paper §4]`: "**There are no changes in the hyperparameters used for training compared to
> 3DGS.**" All learning rates, densification thresholds, `opacity_reset_interval` etc. are
> inherited from the upstream repo via the file overlay.
>
> ⚠️ **The quantization happens pre-activation** `[paper §4]`: "The scale parameters of
> covariance are quantized **before applying the exponential activation** on them. Similarly,
> quaternion based rotation parameters are quantized **before normalization**." Clustering in
> the post-activation space would distort the metric.

### Codebook centroids — a second, non-gradient parameter set

| Symbol | Repo | Shape | Updated how |
|---|---|---|---|
| `C_dc`, `C_sh`, `C_scale`, `C_rot` | `Quantize_kMeans.centers` | `(K, d)` each | **Not by gradient descent.** Re-averaged from the non-quantized parameters every iteration `[repo: kmeans_quantize.py:46-61]`; assignments recomputed every `kmeans_freq` iterations |

This is a real structural difference from `../CompGS/` (Liu), whose entropy model *is* trained
by gradient descent, and from `../OMG/`, whose codebook is nominally finetuned by Adam.

---

## 3.2 Dependent variables

| Symbol | Repo | Definition |
|---|---|---|
| `nn_index` | `Quantize_kMeans.nn_index` | `(N,)` — cluster assignment per Gaussian, `argmin_j ‖z_i − C_j‖` `[repo: kmeans_quantize.py:143, 168]` |
| `cls_ids` | `Quantize_kMeans.cls_ids` | **set equal to `nn_index`** `[repo: kmeans_quantize.py:118]` — length `N`, not `K` |
| `ẑ` | `sampled_centers` | `centers[nn_index]` — the quantized parameter used for rendering `[repo: kmeans_quantize.py:194, 204]` |
| `cluster_len` | — | number of Gaussians per cluster, used for the averaging update `[repo: kmeans_quantize.py:61]` |
| `excl_clusters` | — | oversized clusters handled separately in the chunked averaging `[repo: kmeans_quantize.py:55-59]` |
| `L_reg_op` | — | `gaussians.get_opacity.sum()` `[repo: train_kmeans.py:164]` |
| `n_bits` | — | `ceil(log2(len(cls_ids)))` ⚠️ **= `ceil(log2(N))`**, not `ceil(log2(K))` `[repo: train_kmeans.py:263]` |

---

## 3.3 Fixed / given inputs

### Data

| Quantity | Value | Source |
|---|---|---|
| Datasets | Mip-NeRF 360 (9 scenes), Tanks&Temples (2), Deep Blending (2), **DL3DV-10K** (140 scenes), **ARKit-200** (200 scenes) | `[paper §4]` |
| Split | "the **same train-test split** as Mip-NeRF360 [4] and 3DGS [33]" | `[paper §4]` ✅ |
| Baseline numbers | "directly report the metrics for other methods from 3DGS [33]"; 3DGS itself also **reproduced** locally | `[paper §4]` |

> The **DL3DV-10K (140 scenes)** and **ARKit-200 (200 scenes)** evaluations are notable — an
> order of magnitude more scenes than the 13-scene standard benchmark, and the largest
> evaluation in your entire comparison set.

### Method hyperparameters

| Name | CLI default `[repo: train_kmeans.py:363-388]` | `run.sh` `[repo: run.sh]` | Paper `[paper §4]` |
|---|---|---|---|
| `--kmeans_st_iter` | `30000` (⇒ quantization never runs) | **15000** | **20000** ⚠️ |
| `--kmeans_iters` | **1** ✅ | **10** ⚠️ | **1** |
| `--kmeans_freq` | **100** ✅ | 100 ✅ | 100 ("works well even for `t` as high as 500") |
| `--kmeans_ncls` (scale, rot) | 4096 | 4096 ⚠️ | **16384** (16K) / 32768 (32K) |
| `--kmeans_ncls_sh` | 4096 | **512** ⚠️ | **4096** |
| `--kmeans_ncls_dc` | 4096 ✅ | 4096 ✅ | **4096** |
| `--quant_params` | `['sh','dc','scale','rot']` ✅ | same ✅ | same |
| `--opacity_reg` | `False` | enabled | enabled |
| `--lambda_reg` | `0.` | **1e-7** ✅ | **1e-7** |
| `--max_prune_iter` | `20000` ✅ | 20000 ✅ | 20000 |
| opacity-reg **lower** bound | **hard-coded 15000** `[repo: train_kmeans.py:160-161, 221]` | — | 15000 ✅ |
| `--total_iterations` | `30000` ✅ | 30000 ✅ | 30000 |
| `--start_checkpoint` | `None` | **required** — a separate non-quantized run to `st_iter` | not mentioned ⚠️ |

> ⚠️ **`run.sh` is not the paper's configuration.** It is the post-paper "opacity
> regularization" recipe announced in the README (31 July 2024). Three of its settings
> (`st_iter`, `kmeans_iters`, `ncls_sh`) differ from `[paper §4]`, and it additionally requires
> a **two-stage workflow** (train unquantized to 15K, checkpoint, then resume with
> quantization) that the paper does not describe. See D-2.

### Inherited from 3DGS (via the file overlay)

`iterations = 30000`, `sh_degree = 3`, `lambda_dssim = 0.2`, `densify_from/until_iter =
500/15000`, `densify_grad_threshold = 2e-4`, **`opacity_reset_interval = 3000` and
`reset_opacity()` IS called** `[repo: train_kmeans.py:217-218]`, `llffhold = 8`,
`safe_state` seed 0.

### Variants reported

| Variant | Covariance codebook | Notes |
|---|---|---|
| CompGS 16K | 16384 | main configuration |
| CompGS 32K | 32768 | best quality |
| CompGS 32K **BitQ** | 32768 | post-training: **position → 16 bits, opacity → 8 bits**, rest 32 bits `[paper Tab. 1 caption]` |

### Dependencies

Only **`bitarray`** beyond 3DGS `[repo: README.md]` — the lightest dependency footprint of any
compression method in your set. Compare `../OMG/` (tiny-cuda-nn + cuML + G-PCC) and
`../CompGS/` (CompressAI + G-PCC).
