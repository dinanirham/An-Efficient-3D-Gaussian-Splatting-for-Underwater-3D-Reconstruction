# §9 — Notation glossary — RoMa

Method key for the merged comparison glossary: **`roma`**.
Paper: arXiv:2305.15404v2 / CVPR 2024. Repo: `Parskatt/RoMa` @ `v0.1.2-4-g77f8d68`.

> RoMa and `../RoMaV2/` share an author and most of their vocabulary, but **differ on one
> important symbol** (`p^A` vs `p^{A↦B}`) — flagged below and stated by the paper itself.

| Symbol | Meaning | Type / shape | First defined |
|---|---|---|---|
| `I_A`, `I_B` | The two input images | `ℝ^{H×W×3}` | paper §3.1 |
| `x^A`, `x^B` | Pixel coordinates in image A / B, normalized to `[−1,1]²` | `ℝ²` | paper §3.1 |
| `F` | The feature encoder. **Decoupled** into `{F_coarse,θ, F_fine,θ}` | — | paper Eq. 1, Eq. 7 |
| `φ^A_coarse`, `φ^B_coarse` | **Coarse features** — frozen DINOv2 ViT-L/14, stride 14 | tokens, dim 1024→512 | paper Eq. 1, Eq. 7; repo `encoders.py:42` |
| `φ^A_fine`, `φ^B_fine` | **Fine features** — separate VGG19-BN, strides {1,2,4,8} | pyramid | paper Eq. 1; repo `encoders.py:6-13` |
| `G` | **Global matcher**, `G = D ∘ E` | — | paper Eq. 2 |
| `E` | **Match encoder** — a Gaussian Process, unchanged from DKM. `gp_dim = 512` | — | paper Eq. 2, §3.1; repo `roma_models.py:84` |
| `D` | **Match decoder** — Transformer, 5 blocks × 8 heads, hidden 1024, MLP 4096, `pos_enc = False` | — | paper §3.3; repo `roma_models.py:87-96` |
| `Ŵ^{A→B}_coarse` | Coarse warp, at stride 14 (**keyed `16` in code** ⚠) | `(H/14, W/14, 2)` | paper Eq. 2 |
| `Ŵ^{A→B}` | **Dense warp** at full resolution, normalized `[−1,1]²` | `(H, W, 2)` | paper Eq. 3 |
| **`p^A`** | **Matchability / certainty** at pixel `x^A`. ⚠ The paper *deliberately* drops the `B`: "This is denoted as `p^{A→B}` by Edstedt et al. [17]. **We omit the B to avoid confusion with the conditional**" | `(H, W)` | paper §3.1 footnote 1 |
| `R_θ` | The **refiners**, a sequence of ConvNets at strides {8,4,2,1} | — | paper Eq. 3, Eq. 4 |
| `R_θ,i` | The refiner at stride `2^i` | — | paper Eq. 4 |
| `π_k(x^A)` | **Anchor probabilities** — the categorical over `K` anchors | `(K, H/14, W/14)` | paper Eq. 8 |
| `m_k` | **Anchor coordinates**, a uniform tight cover of the image grid | `(K, 2)` | paper §3.3; repo `robust_loss.py:48-49` |
| `K` | Number of classification anchors = **64 × 64 = 4096**. ⚠ "When used for regression, `K` is set to `K = 2`" | integer | paper §3.3, footnote 3; repo `cls_to_coord_res = 64` |
| `B` | ⚠ **Overloaded.** (a) image **B** (`I_B`, `x^B`); (b) the **base distribution** of Eq. 8, set to `U` (uniform) | — | paper §3.1 vs Eq. 8 |
| `B_{m_k}` | The base distribution centred at anchor `m_k` | — | paper Eq. 8 |
| `k̂(x)` | `argmax_k π_k(x)` — the winning anchor | integer | paper Eq. 9 |
| `N₄(k)` | The anchor `k` **plus its four neighbours** (left/right/top/bottom) — the local softargmax support | 5 indices | paper Eq. 9 |
| `ToWarp(·)` | Decoding: `argmax` then local softargmax over `N₄(k̂)` | — | paper Eq. 9 |
| `q(x^A, x^B; s)` | ⭐ **The theoretical matchability model**: `𝒩(0, s²I) ∗ p(x^A, x^B; 0)` — the exact infinite-resolution matching **diffused** at scale `s` | distribution | paper Eq. 10 |
| `p(x^A, x^B; 0)` | The exact mapping at infinite resolution | distribution | paper Eq. 10 |
| `p_coarse,θ`, `p_i,θ` | The distributions modelled by the global matcher and by refiner `i` | — | paper Eqs. 5, 6 |
| `s` | ⚠ **Overloaded.** (a) the **diffusion scale** of Eq. 10; (b) `s = 2^i c`, the Charbonnier scale at stride `i` | scalar | paper Eq. 10 vs §3.4 |
| `μ(x^A_i, Ŵ_{i+1})` | The refiner's estimated **mean** of the local distribution | `ℝ²` | paper Eq. 16 |
| `α` | **Generalized-Charbonnier shape parameter = 0.5** ⇒ exponent `α/2 = 1/4` | scalar | paper §3.4; repo `train_roma_outdoor.py:219` |
| `c` | **Charbonnier scale.** ⚠ **Paper: 0.03. Code: 1e-4.** (class default: 1e-3) | scalar | paper §3.4 vs repo `train_roma_outdoor.py:220` |
| `λ` | Weight of the **marginal** vs. the **conditional**. ⚠ Value never stated in the paper; code uses `ce_weight = 0.01` | scalar | paper Eq. 14; repo `train_roma_outdoor.py:215` |
| `L_coarse` | Regression-by-classification loss (cross-entropy over anchors + BCE on matchability) | scalar | paper §3.4, Eq. 14 |
| `L_fine` | Robust regression loss, summed over strides {8,4,2,1} | scalar | paper §3.4, Eq. 18 |
| `L` | `L_coarse + L_fine`, with **no relative weighting needed** | scalar | paper Eq. 19 |
| `D_KL(·‖·)` | Kullback–Leibler divergence — both losses are derived as KL against `q` | — | paper Eqs. 11, 17 |
| `EPE` | End-point error, in pixels at a standardized resolution | scalar | paper §3.2 |
| **Robustness %** | ⭐ % of matches with error **< 32 px** — deliberately loose: "while these matches are not necessarily accurate, it is typically **sufficient for the refinement stage** to produce a correct adjustment" | % | paper §3.2 |
| **PCK** | Percent correct keypoints; Table 2 reports **100−PCK, so lower is better** | % | paper §4.1 |
| — | `ce_weight = 0.01`, `local_dist = {1:4,2:4,4:8,8:8}`, `local_largest_scale = 8`, `prob > 0.99` mask — **all repo-only** | — | repo `robust_loss.py:51,138-141`; `train_roma_outdoor.py:215-217` |
| — | `sample_thresh = 0.05`, `sample_mode = "threshold_balanced"`, `symmetric`, `upsample_preds`, `attenuate_cert` — inference knobs | — | repo `roma_models.py:52-56` |

## RoMa ↔ RoMa v2 correspondence

For the merged glossary, these two folders describe the **same task** with **partly different
symbols**:

| Concept | `roma` (v1) | `romav2` |
|---|---|---|
| Dense warp | `Ŵ^{A→B}` | `W^{A↦B}` |
| Confidence | **`p^A`** (the `B` deliberately dropped) | **`p^{A↦B}`** (the `B` restored) |
| Coarse features | `φ_coarse` — frozen **DINOv2 ViT-L/14** | frozen **DINOv3 ViT-L/16** |
| Fine features | `φ_fine` — VGG19-BN | VGG19-BN |
| Coarse matching mechanism | **Gaussian Process** `E` + Transformer `D` | **attention** (GP removed) + DPT head |
| Coarse supervision | anchor **classification** over `K = 64²` | robust regression + **`L_NLL`** on `S` |
| Fine loss | generalized Charbonnier, `α = 0.5` | generalized Charbonnier, `α = 0.5` ✅ same |
| Charbonnier `c` | paper 0.03 / code **1e-4** | paper **1e-3** |
| Coarse stride | **14** (keyed `16`) | **4** |
| Refiners | **4** (strides 8,4,2,1) | **3** (strides 4,2,1) |
| Uncertainty | overlap only | overlap **+ 2×2 precision `Σ⁻¹`** |
| Training data | MegaDepth (+ScanNet for indoor) | **10 datasets, 5069 scenes** |
| Training released? | ✅ **yes** | ❌ no |

## Cross-method collision warnings

| Symbol | In RoMa it is… | Collides with |
|---|---|---|
| **`W`** | **The dense warp** `Ŵ^{A→B}` — the primary output | Image **width** in `../mini-splatting/` Eq. 2 and `../seasplat/` — and in RoMa's own `(H, W, 2)` shapes |
| **`p`** | **Matchability / certainty** ∈ [0,1] | A **pixel** in `../EDGS/` Eq. 1; **Gaussian position** in `../mini-splatting/`; **entropy-model probability** in `../CompGS/`; **sampling probability** in `../mini-splatting/` §4.2. **Five meanings across the set.** |
| **`D`** | The **match decoder** (a network) | **Distortion** in `../CompGS/`; the **direct image** `J·e^{-β^D Z}` in `../seasplat/`; descriptor dimension generally |
| **`E`** | The **match encoder** (a Gaussian Process) | **Expectation** operator in `../seathru_NeRF/` Eqs. 9-12 and `../CompGS/` Eqs. 9-13 |
| **`F`** | The **feature encoder** | Nothing in-set, but note `F_coarse`/`F_fine` vs `f_dc`/`f_rest` (SH coefficients) in every 3DGS folder |
| **`G`** | The **global matcher** `G = D ∘ E` | The set of **Gaussians** `G = ∪ g_i` in `../EDGS/` §3.1 and `../mini-splatting/`; `G^blur`, `G^int` in `../mini-splatting/` Eqs. 2-3 |
| **`K`** | **Number of anchors** = 4096 | Camera **intrinsics** in `../seasplat/` §IV.A, `../seathru_NeRF/` §4.1 — *and in RoMa's own `get_gt_warp(..., K1, K2)`* `[repo: robust_loss.py:130-131]`; **coupled primitives per anchor** in `../CompGS/`; **codebook size** in `../compact3d/` |
| **`B`** | Image **B**, *and* the Eq. 8 **base distribution** | **Backscatter** `B̂`, `B^∞` in `../seasplat/` and `../seathru_NeRF/`; **batch size** generally |
| **`α`** | **Charbonnier shape** = 0.5 | **Opacity** in every 3DGS folder; `[−1,1]`-ranged opacity in `../CompGS/`; per-interval object alpha in `../seathru_NeRF/` |
| **`λ`** | **Marginal/conditional weight** = 0.01 | `λ_dssim = 0.2` in every 3DGS paper; RD multiplier in `../CompGS/`; `L_objnorm` weight in `../seathru_NeRF/`; **and the position-embedding scale in `../RoMaV2/` §3.5** |
| **`s`** | **Diffusion scale** *and* Charbonnier scale `2^i c` | Per-Gaussian **scale** `s` in `../mini-splatting/` App. D and 3DGS |
| **`q`** | The **theoretical matchability distribution** | Gaussian **rotation quaternion** `q` in the 3DGS family |
| **`μ`** | The refiner's **estimated mean** (a 2D image coordinate) | Gaussian **mean / 3D position** in `../seasplat/`, `../CompGS/`, `../compact3d/`; entropy-model mean in `../CompGS/` |
| **`c`** | **Charbonnier scale constant** | **Colour** in every radiance-field folder; **codebook code** in `../compact3d/`; confidence `c_ij` in `../EDGS/` Eq. 3 |
| **`N₄`** | The **4-neighbourhood** of an anchor | `N` = number of Gaussians / samples / pixels / anchors, folder-dependent |
