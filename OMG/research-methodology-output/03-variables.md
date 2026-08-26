# §3 — Formal variable table

`N` = number of Gaussians (shrinks at 15 000 and 20 000). `D = 3` (feature dimensionality —
code only). Strides/iterations follow Mini-Splatting's schedule.

---

## 3.1 Independent variables (directly optimized)

OMG has **four** optimizer groups, versus Mini-Splatting's one. Note that appearance
(`_features_dc`, `_features_rest`) stops being optimized at iteration 15 000 and is replaced by
`T`, `V` and the MLPs.

### Group 1 — Geometry: per-Gaussian, **deliberately not neural-fielded**

| Symbol | Repo | Shape | Init | lr | Source |
|---|---|---|---|---|---|
| `p` | `_xyz` | `(N, 3)` | COLMAP → depth-reinit points (Mini-Splatting) | exp `1.6e-4 → 1.6e-6`, **schedule rewound at 15 000** | `[repo: arguments/__init__.py:74-77; train.py:73-77]` |
| `s` | `_scaling` | `(N, 3)` | `log√(kNN dist)` | `5e-3` | `[paper §3.1]` `[repo: arguments/__init__.py:80]` |
| `r` | `_rotation` | `(N, 4)` | identity quaternion | `1e-3` | `[paper §3.1]` `[repo: arguments/__init__.py:81]` |

> `[paper §3.1]`: "we **retain the per-Gaussian parameterization for scale `s ∈ ℝ^{N×3}_+` and
> rotation `r ∈ ℝ^{N×4}` as in 3DGS**" — because sparse Gaussians each cover more space and
> "requir[e] a more specific scale and rotation to accurately capture structural details."

### Group 2 — Appearance: per-Gaussian features (created at iteration 15 000)

| Symbol | Repo | Shape | Init | Source |
|---|---|---|---|---|
| **`T`** | `_features_static` | `(N, **3**)` | `_features_dc[:, 0].clone().detach()` — seeded from the DC colour learned so far | `[paper §3.1]` `[repo: gaussian_model.py:724]` |
| **`V`** | `_features_view` | `(N, **3**)` | **zeros** | `[paper §3.1]` `[repo: gaussian_model.py:725]` |

> ⚠️ **`D = 3`.** The paper writes `T ∈ ℝ^{N×D}`, `V ∈ ℝ^{N×D}` and says only that "`D` is the
> dimensionality of each feature" `[paper §3.1]` — **the value never appears**. Code: 3 and 3,
> confirmed by the downstream MLPs' `n_input_dims = 16 = 3 + 13`.
>
> **Before iteration 15 000** the model uses standard 3DGS `_features_dc` (N,1,3) and
> `_features_rest` (N,15,3); after `construct_net()` these are superseded.

### Group 3 — The neural field (4 tiny MLPs, all `tcnn.FullyFusedMLP`, 64 neurons, 1 hidden layer)

| Symbol | Repo | Architecture | Source |
|---|---|---|---|
| `MLP_s` (space feature) | `mlp_cont` | `3 → Frequency(n_frequencies = **16**) → 64 → **13**`, ReLU | `[paper Eq. 4]` `[repo: gaussian_model.py:672-686]` |
| `MLP_t` (static colour) | `mlp_dc` | `16 → 64 → 3`, LeakyReLU | `[paper Eq. 3]` `[repo: gaussian_model.py:698-708]` |
| `MLP_o` (opacity) | `mlp_opacity` | `16 → 64 → 1`, LeakyReLU | `[paper Eq. 3]` `[repo: gaussian_model.py:710-720]` |
| `MLP_v` (view-dependent SH) | `mlp_view` | `16 → 64 → 3·max_sh_rest = **45**`, LeakyReLU | `[paper Eq. 4]` `[repo: gaussian_model.py:687-697]` |

**Optimizer:** Adam `lr = 0.01`, `eps = 1e-15`, with a `ChainedScheduler`:
`LinearLR(start_factor=0.01, total_iters=100)` ⊕ `MultiStepLR(milestones=[1000, 3500, 6000],
gamma=0.33)` `[repo: gaussian_model.py:737-751]`.

> **None of this architecture appears in the paper** — not the 64-neuron width, not the single
> hidden layer, not 16 frequencies, not the 13-dim space feature, not the LR schedule. The
> paper says only "a **tiny MLP**" `[paper §4.2]` and "efficiently parameterized using
> positional encoding and an MLP" `[paper §3.1]`.

### Group 4 — SVQ codebooks (created at iteration 29 000)

| Attribute | Vector | `slice` (M) | sub-vector length (L) | `cluster` (B) | Total codewords | Source |
|---|---|---|---|---|---|---|
| **scale** | `_scaling ∈ ℝ³` | **1** | 3 | `2⁶ = 64` | 64 | `[repo: arguments/__init__.py:100-101]` |
| **rotation** | `_rotation ∈ ℝ⁴` | **2** | 2 | `2⁹ = 512` | 1024 | `[repo: arguments/__init__.py:102-103]` |
| **appearance** | `cat(T, V) ∈ ℝ⁶` | **2** | 3 | `2¹⁰ = 1024` | 2048 | `[repo: arguments/__init__.py:104-105; gaussian_model.py:816]` |

**Optimizer:** Adam `lr = **1e-8**`, `eps = 1e-15` `[repo: gaussian_model.py:818]`.

> ⚠️ **`slice_scale = 1` means scale is not actually sub-vector quantized** — one 64-entry
> codebook over the full 3-vector, i.e. plain VQ.
>
> ⚠️ **`lr = 1e-8`** over the 1000 finetuning steps moves each codeword by ~1e-5. The paper
> describes "finetun[ing] only the codebook using the rendering loss" `[paper §3.2]`; in
> practice the codebook is essentially frozen at its K-means initialisation. See D-2.

---

## 3.2 Dependent variables (derived each forward pass, after iteration 15 000)

| Symbol | Shape | Definition | Source |
|---|---|---|---|
| `F_n` | `(N, 13)` | **space feature** `= MLP_s(γ(p_n))` — positional encoding then tiny MLP | `[paper Eq. 4]` `[repo: gaussian_model.py:672-686]` |
| `γ(·)` | — | Frequency positional encoding, **16 frequencies** | `[paper Eq. 4]` `[repo: gaussian_model.py:675-678]` |
| `h_n^(0)` | `(N, 3)` | static (DC) colour `= MLP_t(cat(T_n, F_n))` | `[paper Eq. 3]` |
| `o_n` | `(N, 1)` | opacity `= MLP_o(cat(T_n, F_n))` | `[paper Eq. 3]` |
| `h_n^(1,2,3)` | `(N, 45)` | view-dependent SH `= MLP_v(cat(V_n, F_n))` | `[paper Eq. 4]` |
| `ŝ_n`, `r̂_n` | `(N,3)`, `(N,4)` | SVQ-reconstructed geometry, `cat(C^(m)[i_m])` then activation | `[paper Eq. 5]` `[repo: gaussian_model.py:822-833]` |
| `T̂_n`, `V̂_n` | `(N,3)` each | SVQ-reconstructed appearance features, split back after quantizing `cat(T,V)` | `[paper §3.2]` `[repo: gaussian_model.py:816]` |
| `Ī_i` | `(N,)` | **base importance** — blending weight, gated by argmax-contribution | `[paper Eq. 7]` `[repo: gaussian_model.py:627-650]` |
| `order` | `(N,)` | Morton-order permutation of Gaussian centres (21-bit quantized) | `[paper §3.3]` `[repo: gaussian_model.py:752-760]` |
| `res_color` | `(N,)` | `mean(\|T[order_l] − T\| + \|T[order_r] − T\|)` — the **local distinctiveness** term | `[paper Eq. 8]` `[repo: gaussian_model.py:663]` |
| `I_i` | `(N,)` | final importance `= Ī_i · res_color^λ` | `[paper Eq. 8]` `[repo: gaussian_model.py:665]` |
| `Σ_n` | `(3,3)` | covariance from `ŝ_n`, `r̂_n` (rasterizer-side) | `[paper §3 Background]` |

---

## 3.3 Fixed / given inputs

### Data

| Quantity | Value | Source |
|---|---|---|
| Datasets | Mip-NeRF 360 [2], Tanks&Temples [31], Deep Blending [23] | `[paper §4.1]` |
| Split / protocol | standard 3DGS (`--eval`, every 8th held out) | `[repo: README.md]` |
| `--imp_metric` | **required**: `outdoor` (Mip-NeRF 360 outdoor + T&T) or `indoor` (M360 indoor + DB) | `[repo: README.md; gaussian_model.py:641-646]` |

### OMG-specific hyperparameters `[repo: arguments/__init__.py:96-105]`

| Name | Default | Paper | Match? |
|---|---|---|---|
| `importance_thresh` (**τ**) | **0.96** (= XS) | `{0.96, 0.98, 0.99, 0.999, 0.9999}` for XS/S/M/L/XL | ✅ `[paper §4.1]` |
| **`lambda_ld`** (**λ**) | **2.0** | ❌ **value never stated** | ✗ |
| `svq_itr` | **29 000** | "final 1K iterations" | ✅ `[paper §3.2]` |
| `net_itr` | **15 000** | ❌ not stated | ✗ |
| `slice_scale` / `cluster_scale` | `1` / `2⁶` | ❌ not stated | ✗ |
| `slice_rot` / `cluster_rot` | `2` / `2⁹` | ❌ not stated | ✗ |
| `slice_app` / `cluster_app` | `2` / `2¹⁰` | ❌ not stated | ✗ |
| `D` (feature dim) | `3` (implicit) | ❌ not stated | ✗ |
| Space feature dim | `13` | ❌ not stated | ✗ |
| `n_frequencies` | `16` | ❌ not stated | ✗ |
| MLP width / depth | `64` / 1 hidden layer | "tiny MLP" only | ✗ |
| Codebook lr | `1e-8` | "finetune … using the rendering loss" | ⚠️ see D-2 |

### Inherited from Mini-Splatting `[repo: arguments/__init__.py:73-95]`

| Name | Value |
|---|---|
| `iterations` | `30 000` |
| `sh_degree` | `3` |
| `lambda_dssim` | `0.2` |
| `simp_iteration1` / `simp_iteration2` | `15 000` / `20 000` |
| `num_depth` / `num_max` | `3 500 000` / `4 500 000` |
| `depth_reinit_interval` | `5 000` |
| `sampling_factor` | `0.5` |
| `densify_from/until_iter` | `500` / `15 000` |
| `densify_grad_threshold` | `2e-4` |
| `opacity_reset_interval` | `3 000` — ⚠️ **and, as in Mini-Splatting, `reset_opacity()` is never called** |
| position/feature/opacity/scaling/rotation lr | 3DGS defaults |

### Post-processing `[paper §4.1]` `[repo: train.py:116-124; utils/gpcc_utils.py]`

| Step | Detail |
|---|---|
| 1. Positions | float16 → uint16 → Morton sort → **G-PCC (MPEG TMC13)** |
| 2. SVQ indices | **Huffman** coding |
| 3. Container | single file, **LZMA** (`comp.xz`) |
| Reported size | `os.path.getsize("comp.xz")` — the **actual file**, with a per-component breakdown including **`MLPs`** |

### External dependencies

| Dependency | Note |
|---|---|
| **tiny-cuda-nn** (`tcnn`) | all four MLPs |
| **cuML** (`KMeans`, `cupy`) | SVQ codebook initialisation; README links the RAPIDS install guide |
| **TMC13 / G-PCC** | must be compiled separately; path hard-coded at `utils/gpcc_utils.py` lines 243, 258 |
| CUDA 12.1 / Python 3.11 / torch 2.5.1 | `[repo: README.md]` |
