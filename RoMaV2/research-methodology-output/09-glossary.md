# §9 — Notation glossary — RoMa v2

Method key for the merged comparison glossary: **`romav2`**.
Paper: arXiv:2511.15706v3. Repo: `Parskatt/RoMaV2` @ `v2.0.1-2-g95c9968`.

> This folder shares almost no vocabulary with the eight radiance-field folders — it is a
> two-view matcher, not a scene representation. The collisions that *do* exist (`Σ`, `W`,
> `p`, `c`, `D`) are therefore the dangerous kind: same glyph, unrelated meaning, no context
> cue.

| Symbol | Meaning | Type / shape | First defined |
|---|---|---|---|
| `I_A`, `I_B` | The two input images, values in `[0,1]` | `ℝ^{H×W×3}` | paper §1; repo `romav2.py:174` |
| `W^{A↦B}` | **Dense warp** from A to B — for every pixel of A, its location in B. In **normalized `[−1,1]²`** coordinates | `ℝ^{H×W×2}` | paper §1; repo `README.md` |
| `W^{B↦A}` | The reverse warp (bidirectional settings only) | `ℝ^{H×W×2}` | paper §1; repo `romav2.py:190-196` |
| `W` | The pair `{W^{A↦B}, W^{B↦A}}` | — | paper Fig. 2 |
| `W_GT` | Ground-truth warp, from MVS depth or flow | `ℝ^{H×W×2}` | paper Eq. 3 |
| `p^{A↦B}` | **Confidence / overlap** — 1 where co-visible, 0 where occluded | `[0,1]^{H×W×1}` | paper §1; repo `romav2.py:62` |
| `p_GT` | Ground-truth overlap ∈ {0,1}, from consistent depth (MVS) or warp cycle consistency (flow) | `{0,1}^{H×W}` | paper §3.3 |
| `p̂^{A↦B}` | Thresholded sampling distribution, `max(𝟙_{p>0.05}, p)` — **benchmark settings only** | `ℝ^{H×W×1}` | paper Eq. 6; repo `romav2.py:63-64` |
| `Σ` | ⚠ **Error covariance of the 2D warp residual** — *not* a Gaussian primitive's shape | `ℝ^{H×W×2×2}` | paper §3.3 / Eq. 4 |
| `Σ⁻¹` | **Precision matrix** — what is actually predicted. Positive definite by construction. Additive across strides: `Σ⁻¹_i = Σ_{j≥i} Σ⁻¹_j` | `ℝ^{H×W×2×2}` | paper §3.3; repo `geometry.py:168-174` |
| `P` | ⚠ The paper writes `P ∈ ℝ^{H×W×2×2}` for the precision matrix in one place and `Σ⁻¹` elsewhere — **the same object** | — | paper §3.3 |
| `z11, z21, z22` | Raw network outputs mapped to Cholesky factors | `ℝ^{H×W×3}` | paper §3.3; repo `refiner.py:201-204` |
| `l11, l21, l22` | Cholesky factors: `l11 = Softplus(z11)+1e-6`, `l21 = z21`, `l22 = Softplus(z22)+1e-6` | scalars | paper §3.3; repo `refiner.py:201-204` |
| `L` | ⚠ **Overloaded.** (a) the lower-triangular **Cholesky factor**, `Σ⁻¹ = LLᵀ` (§3.3); (b) the prefix of every **loss** (`L_NLL`, `L_warp`, …) | `2×2` / scalar | paper §3.3 vs Eqs. 1-5 |
| `r_θ` | **Residual**, `W_θ^{A↦B} − W_GT^{A↦B}`. **Detached** before `L_prec` | `ℝ^{H×W×2}` | paper Eq. 3 |
| `S` | **Similarity matrix** between all patches of A and all of B | `ℝ^{M×N}` | paper Eq. 1 |
| `M`, `N` | ⚠ **Number of patches** in image A and image B respectively — *not* a count of primitives or views | integers | paper §3.2 |
| `n*` | Index of the patch in B closest to the GT warp of patch `m` — the target of `L_NLL` | integer | paper Eq. 1 |
| `x_B` | Position embeddings of image B, aggregated as `Softmax(S)·x_B` | — | paper §3.2 |
| `f_A`, `f_B` | Frozen **DINOv3 ViT-L/16** features, layers [11, 17], dim 1024 | stride-16 tokens | paper §3.2; repo `features.py:83-89` |
| `L_NLL` | Patch-level negative log-likelihood over `Softmax(S)` — supervises `S` directly, replacing the removed Gaussian Process | scalar | paper Eq. 1 |
| `L_warp` | **Generalized Charbonnier** robust regression, `α = 0.5`, `c = 1e-3` | scalar | paper §3.3, ref [2] |
| `L_overlap` / `L_ov` | Pixel-wise BCE on confidence | scalar | paper Eq. 2 / Eq. 5 |
| `L_prec` | Gaussian NLL of the (detached) residual under `Σ⁻¹`; gated to co-visible pixels with `‖r‖ < 8 px` | scalar | paper Eq. 4 |
| `L_matcher` | `L_NLL + L_warp + 0.1·L_overlap` | scalar | paper Eq. 2 |
| `L_refiners` | `Σ_{i∈S} [L_warp + 1e-2·L_ov + 1e-3·L_prec]` | scalar | paper Eq. 5 |
| `λ` | ⚠ **Two meanings.** (a) overlap weight **0.1** in Eq. 2; (b) the **position-embedding scale**, `λ = 8` in RoMa → **`λ = 1` fixed** in v2 (§3.5) | scalar | paper Eq. 2 vs §3.5 |
| `λ_ov`, `λ_prec` | `1e-2`, `1e-3` | scalars | paper Eq. 5 |
| `α`, `c` | Charbonnier shape and scale: `0.5`, `1e-3` | scalars | paper §3.3 |
| `S` (again) | ⚠ **Also** the set of refiner strides `{1, 2, 4}` in Eq. 5 — a second meaning for the same glyph | set | paper Eq. 5 |
| `i` | Refiner **stride** ∈ {4, 2, 1} | integer | paper §3.3, Eq. 5 |
| `θ` | Network parameters (`θ_matcher`, `θ_i`) | — | paper Eq. 2, Eq. 5 |
| `Q`, `F` | Residual **quantile function** (UFM) and **CDF** (RoMa v2), used for the sub-pixel perturbation experiment | — | paper Eq. 7 |
| `temp` | Similarity temperature, **0.1** (RoMa: 0.2) — **repo-only, unmentioned in the paper** | scalar | repo `matcher.py:75-76` |
| `chol_eps` | `1e-6`, the Cholesky diagonal floor | scalar | paper §3.3 = repo `refiner.py:201` |
| `Setting` | Eight-valued inference preset: `turbo`, `fast`, `base`, `precise`, `mega1500`, `scannet1500`, `wxbs`, `satast` | enum | repo `types.py`; `romav2.py:119-160` |
| `anchor_width/height` | **512** — canonical resolution for displacement rescaling | integers | repo `romav2.py:76-77` |
| `local_corr_radius` | Local-correlation window radius per refiner: **3 / 1 / None** | integer | repo `refiner.py:243, 252, 261` |
| `confidence_dim` | **1** at the matcher, **4** at the refiners (1 overlap + 3 precision) | integer | repo `matcher.py:81`; `refiner.py:77` |

## Cross-method collision warnings

| Symbol | In RoMa v2 it is… | Collides with |
|---|---|---|
| **`Σ` / `Σ⁻¹`** | **2×2 error covariance / precision of a warp residual, in pixel units** | **3×3 Gaussian covariance** in `../seasplat/`, `../mini-splatting/`, `../compact3d/`, `../EDGS/`; a **6-D scaling vector** in `../CompGS/`; the **summation operator** everywhere. **Four unrelated meanings across the set** — and RoMa v2's is the only one that is a *statistical* covariance rather than a shape. |
| **`σ`** | The `σ_f`, `σ_Σ`, `σ_g` of `../CompGS/` are entropy-model scales; RoMa v2 has no `σ` | **volumetric density** in `../seathru_NeRF/`, `../nerf/`; **Gaussian scale** in the 3DGS family |
| **`W`** | **The dense warp field** — the method's primary output | Image **width** in `../mini-splatting/` Eq. 2, `../seasplat/`, and in this same paper's `ℝ^{H×W×2}` shapes. **`W` is both the warp and the width in one equation.** |
| **`p`** | **Confidence / overlap** ∈ [0,1] | A **pixel** in `../EDGS/` Eq. 1; **Gaussian position** in `../mini-splatting/`; **probability under an entropy model** in `../CompGS/`; **sampling probability** in `../mini-splatting/` §4.2. **Five meanings.** |
| **`c`** | Charbonnier scale constant `c = 1e-3`, **and** confidence `c_ij` in the RoMa-v1 lineage | **Colour** in every radiance-field folder (`c_i`, `c^obj`, `c^med`, `g^c`); **codebook code** in `../compact3d/` |
| **`L`** | Cholesky factor **and** loss prefix | Loss prefix everywhere ✅; nothing uses `L` for a matrix elsewhere |
| **`M`, `N`** | **Patch counts** in images A and B | `N` = number of **Gaussians** in `../mini-splatting/`, `../compact3d/`, `../OMG/`; **anchors** in `../CompGS/`; samples per ray in `../seathru_NeRF/`; **pixels** in `../seasplat/` Eq. 5. `M` = **training views** in `../mini-splatting/` and `../CompGS/`; the **matching network** in `../EDGS/` Eq. 3 |
| **`λ`** | Overlap weight (0.1) **and** position-embedding scale (1) | `λ_dssim = 0.2` in every 3DGS paper; RD multiplier in `../CompGS/`; `L_objnorm` weight in `../seathru_NeRF/`; six λ in `../seasplat/` |
| **`α`** | **Charbonnier shape parameter = 0.5** | **Opacity** in every 3DGS folder (and `[−1,1]`-ranged in `../CompGS/`); per-interval object alpha in `../seathru_NeRF/` |
| **`T`** | not used | Transmittance in `../seathru_NeRF/`, `../mini-splatting/`; thresholds in `../seasplat/`; optimization steps in `../EDGS/` |
| **`r`** | **Residual** `W_θ − W_GT` | Ray `r(t)` in `../seathru_NeRF/`, `../mini-splatting/` App. D |
| **`D`** | not used as a symbol | **Distortion** in `../CompGS/`; the **direct image** in `../seasplat/`; descriptor dimension in the matching literature generally |
| **`S`** | **Similarity matrix** *and* the stride set `{1,2,4}` | Per-Gaussian **scale matrix** in `../seasplat/`, `../EDGS/`; **max-contribution area** (a pixel count) in `../mini-splatting/`; predicted scaling matrix `S_k` in `../CompGS/` |
| **`i`, `j`** | Image/view indices and refiner strides | Gaussian indices everywhere else |

## Shared design pattern worth recording in the merged glossary

**Detached auxiliary supervision** appears independently in four folders, always with the same
justification — *let the auxiliary head explain the primary prediction, never shape it*:

| Folder | Detached tensor | Consumer | Degeneracy prevented |
|---|---|---|---|
| `romav2` | `detach(r)` — the warp residual | `L_prec` | precision head inflating residuals to match its own prediction |
| `seasplat` | `Ẑ.detach()` — rasterized depth | `L_bs`, `L_Z-recon` | medium params dragging geometry; `Ẑ → 0` shortcut |
| `seathru_nerf` | `stop_gradient(t_delta)` — sample spacing | all medium transmittances | sampler gaming the `σ·s` product |
| `mini-splatting` | — (none) | — | uses non-differentiable selection instead |

This is a genuine cross-method commonality rather than a notational one, and belongs in
`../../comparison-glossary.md` as such.
