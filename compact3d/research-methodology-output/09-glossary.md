# §9 — Notation glossary — CompGS / Compact3D

Method key for the merged comparison glossary: **`compgs-vq`** (to disambiguate from
`compgs-liu` = `../CompGS/`).
Paper: arXiv:2311.18159v3 / ECCV 2024. Repo: `UCDvision/compact3d` @ `dccc07e`.

> CompGS uses **3DGS's standard symbols** (`μ, Σ, S, R, α, c, G`) and adds only a handful of
> quantization terms. Its collision risks are `K`, `d`, `N`, `t` and — most of all — **the
> method name itself**.

| Symbol | Meaning | Type / shape | First defined |
|---|---|---|---|
| `G(x)` | The 3D Gaussian function, `exp(−½(x−μ)ᵀΣ⁻¹(x−μ))` | — | paper §3 |
| `μ` | Gaussian **position**. ⚠ **Never quantized** — "sharing them results in overlapping Gaussians" | `(N,3)` | paper §3; repo `_xyz` |
| `Σ` | Gaussian **covariance**, factored `Σ = R S Sᵀ Rᵀ` | `(3,3)` | paper §3 |
| `S`, `R` | **Scale** and **rotation** matrices factoring `Σ`. Both quantized — `S` **before `exp`**, `R` **before normalization** | `(N,3)`, `(N,4)` | paper §3, §4; repo `_scaling`, `_rotation` |
| `α` | **Opacity**. ⚠ Not quantized ("a single scalar"), but **ℓ1-regularized** | `(N,1)` | paper §3; repo `_opacity` |
| `α_i` (rendering) | ⚠ **Overloaded**: also "the product of the value of the Gaussian at that point and its learned opacity" in the blending equation | scalar | paper §3 |
| `c_i` | **Colour** of the `i`-th Gaussian, from SH order 3 + a DC component | `ℝ³` | paper §3 |
| `C` | Rendered pixel colour, `Σ_i c_i α_i Π_{j<i}(1−α_j)` | `ℝ³` | paper §3 |
| **`N`** | **Number of Gaussians** — "a few millions" | integer | paper §3 |
| **`K`** | ⭐ **Codebook size** (number of cluster centres) — "a few thousands". 4096 / 16384 / 32768 | integer | paper §3; repo `--kmeans_ncls*` |
| **`d`** | ⭐ **Parameter-vector dimensionality** per quantized group: dc 3, sh 45, scale 3, rot 4 | integer | paper §3 |
| **`t`** | ⭐ **Assignment-update interval** — "update the assignments once every `t` iterations". `t = 100`; "works well even for `t` as high as 500" | integer | paper §3; repo `--kmeans_freq` |
| **`λ_reg`** | ⭐ **Opacity-regularization weight** = **1e-7** | scalar | paper §3; repo `--lambda_reg` |
| `L_3DGS` | The original 3DGS loss, `0.8·L₁ + 0.2·(1−SSIM)` | scalar | paper §3 |
| `L` | `L_3DGS + λ_reg Σ_i α_i` | scalar | paper §3 |
| — | `nn_index` — per-Gaussian cluster assignment | `(N,)` | repo `kmeans_quantize.py:143` |
| — | `cls_ids` — **set equal to `nn_index`**, hence length `N`, not `K` ⚠ | `(N,)` | repo `kmeans_quantize.py:118` |
| — | `centers` — the codebook `C_g` | `(K,d)` | repo `kmeans_quantize.py:17` |
| — | `n_bits = ceil(log2(len(cls_ids)))` ⚠ **= ceil(log2(N))**, not `log2(K)` | integer | repo `train_kmeans.py:263` |
| — | `kmeans_st_iter` — when QAT begins. paper 20 000 · run.sh 15 000 ⚠ | integer | repo `--kmeans_st_iter` |
| — | `max_prune_iter` = 20 000 — end of the opacity-reg window (start hard-coded at 15 000) | integer | repo `--max_prune_iter` |
| — | `quant_params` = `['sh','dc','scale','rot']`; also supports `pos`, `scale_rot`, `sh_dc` | list | repo `--quant_params` |
| **16K / 32K** | Variant names — the **covariance** codebook size | — | paper §4 |
| **BitQ** | Post-training bit quantization: **position → 16 bits, opacity → 8 bits**, rest 32 | — | paper Tab. 1 |
| **PSNR-AM** | ⭐ **Arithmetic-Mean PSNR** — average the *error* across all images/scenes **before** the log, rather than averaging PSNRs | metric | paper §4 |
| **STE** | Straight-Through Estimator — quantized forward, gradients to the non-quantized parameters | — | paper §3, ref [7] |
| **RLE** | Run-length encoding of sorted indices. ⚠ **Described in the abstract and §3; not implemented** | — | paper §3 |

## ⚠️ The name collision, stated once for the record

| | This folder | `../CompGS/` |
|---|---|---|
| Paper title | *CompGS: Smaller and Faster Gaussian Splatting with **Vector Quantization*** | *CompGS: Efficient 3D Scene Representation via **Compressed Gaussian Splatting*** |
| Authors | Navaneet, Pourahmadi Meibodi, Koohpayegani, Pirsiavash (UC Davis) | Liu, Wu, Zhang, Wang, Li, Kwong (CityU HK et al.) |
| Venue | **ECCV 2024** | **ACM MM 2024** |
| arXiv | **2311.18159** | **2404.09458** |
| Repo | `UCDvision/compact3d` | `LiuXiangrui/CompGS` |
| Base method | vanilla 3DGS | **Scaffold-GS** |
| Mechanism | **K-means VQ**, quantization-aware | **predictive coding + learned entropy model**, RD-optimized |
| Glossary key | **`compgs-vq`** | **`compgs-liu`** |

⚠️ **Until 2026-08-25, `../../CompGS.pdf` was a byte-identical duplicate of
`../../compact3d.pdf`** (MD5 `d38c06cf…`) — the wrong paper sat in the `CompGS/` folder. It now
holds arXiv:2404.09458v1 (MD5 `89f5638d…`). Also note this work is a
**baseline inside** the other paper (`Navaneet et al. [33]`) and inside `../OMG/`
(`CompGS [44]`, `[inferred]`).

## Cross-method collision warnings

| Symbol | In CompGS-VQ it is… | Collides with |
|---|---|---|
| **`K`** | ⭐ **Codebook size** (4096–32768) | Camera **intrinsics** in `../seasplat/` §IV.A and `../seathru_NeRF/` §4.1; **coupled primitives per anchor** (=10) in `../CompGS/`; **rays intersecting a Gaussian** in `../mini-splatting/` §3.2; **anchors** (=64²) in `../RoMa/` §3.3; **neighbours** in `../OMG/` Eq. 8. **Six meanings across the set.** |
| **`d`** | **Parameter-vector dimensionality** per group | **Ray direction** in `../mini-splatting/` App. D and `../seathru_NeRF/`; **depth** in `../mini-splatting/` §4.1; **descriptor dim** in the matchers |
| **`N`** | **Number of Gaussians** ✅ | Consistent with `../mini-splatting/`, `../OMG/`; but **anchors** in `../CompGS/`, **samples per ray** in `../seathru_NeRF/`, **pixels** in `../seasplat/` Eq. 5, **patch count** in `../RoMaV2/` |
| **`t`** | **Assignment-update interval** (an iteration count) | **Ray parameter** `t` in `../seathru_NeRF/` and `../mini-splatting/` App. D; **translation vector** `t_k` in `../CompGS/` Eq. 3; **optimization step** in `../EDGS/` Eq. 14 |
| **`λ_reg`** | **Opacity-regularization weight** = 1e-7 | `λ_dssim = 0.2` in every 3DGS paper; the **RD multiplier** in `../CompGS/`; `λ` = LD exponent in `../OMG/`; six λ in `../seasplat/`; the marginal weight in `../RoMa/` |
| **`α`** | ⚠ **Two meanings in one paper**: the stored **opacity** parameter, and the per-Gaussian **blending weight** in the rendering equation | Opacity in the 3DGS family ✅; **Charbonnier shape** in `../RoMa/`/`../RoMaV2/`; `[−1,1]`-ranged opacity in `../CompGS/` |
| **`Σ`** | Gaussian **covariance** ✅ | A **6-D scaling vector** in `../CompGS/`; the **2×2 error precision** in `../RoMaV2/`; summation everywhere |
| **`S`, `R`** | **Scale / rotation matrices** ✅ standard | `S` = **max-contribution area** in `../mini-splatting/` Eq. 2; `S` = **similarity matrix** in `../RoMaV2/` Eq. 1; `R` = **BITRATE** in `../CompGS/` Eq. 1 |
| **`C`** | **Rendered pixel colour** ✅ | `C^(m)` = **codebook** in `../OMG/`; `C(r)` = ray colour in `../seathru_NeRF/` ✅ |
| **`G`** | The **Gaussian function** `G(x)` | The **set** of Gaussians in `../EDGS/`, `../mini-splatting/`; the **global matcher** in `../RoMa/` Eq. 2 |
| **"CompGS"** | **The method name itself** | `../CompGS/` (Liu et al.). See the table above |

## Lineage note for the comparison glossary

CompGS-VQ is the **origin point** of the quantization branch in your set, and both successors
respond to specific weaknesses it identified or exhibited:

| Weakness | CompGS-VQ | `../OMG/` response | `../CompGS/` (Liu) response |
|---|---|---|---|
| Position dominates post-quantization memory (>80%) | left at float32 | **G-PCC** on 16-bit positions | **G-PCC** on frozen voxelized anchors |
| Large codebooks are slow (68 s encode) | 4096–32768 entries, K-means in-loop | **Sub-Vector Quantization** — 13–18× faster init | scalar quantization + entropy model |
| Multiple indices per Gaussian | 4 codebooks ⇒ 4 indices | fewer, smaller partitions | one index per sub-vector |
| Indices bit-packed, not entropy-coded | plain bit-packing | **Huffman + LZMA** | **learned entropy model** |
| No rate term in the objective | ℓ1 opacity only | ℓ1-free; τ threshold | **`λR` in the loss** |
