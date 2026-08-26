# §9 — Notation glossary — OMG

Method key for the merged comparison glossary: **`omg`**.
Paper: arXiv:2503.16924v2 / NeurIPS 2025. Repo: `maincold2/OMG` @ `6edeb72`.

> OMG uses **3DGS's standard symbol set** for Gaussian attributes (`p, o, s, r, h, Σ, α, c`) —
> unlike `../mini-splatting/` (`p` for position) and `../EDGS/` (`g^x, g^c, g^α`). Where it
> introduces new symbols (`T, V, F, Ī, I, λ, τ`), those are the collision risks.

| Symbol | Meaning | Type / shape | First defined |
|---|---|---|---|
| `N` | Number of Gaussians (shrinks at 15 000 and 20 000) | integer | paper §3 Background |
| `p` | Gaussian **centre position** | `ℝ^{N×3}` | paper §3 Background; repo `_xyz` |
| `o` | **Opacity** ∈ [0,1]. After iteration 15 000, MLP-decoded | `ℝ^N` | paper §3, Eq. 3; repo `_opacity` |
| `s` | 3D **scale**. ⚠ **Kept per-Gaussian on purpose** | `ℝ^{N×3}_+` | paper §3, §3.1; repo `_scaling` |
| `r` | 3D **rotation** quaternion. ⚠ Also kept per-Gaussian | `ℝ^{N×4}` | paper §3, §3.1; repo `_rotation` |
| `Σ_n` | Gaussian **covariance**, determined by `s_n`, `r_n` | `ℝ^{3×3}` | paper §3 Background |
| `h^(0)` | **Static (DC) colour** SH coefficient — degree 0 | `ℝ^{N×3}` | paper §3, Eq. 3 |
| `h^(1,2,3)` | **View-dependent** SH coefficients — degrees 1–3 | `ℝ^{N×45}` | paper §3, Eq. 4 |
| `c_n` | Colour of Gaussian `n` under a given view direction | `ℝ³` | paper Eq. 1 |
| `α_n(x)` | Final **2D opacity** at pixel `x` | scalar | paper Eq. 2 |
| `C(x)` | Rendered pixel colour | `ℝ³` | paper Eq. 1 |
| `N(x)` | Number of Gaussians around pixel `x` (depth-sorted) | integer | paper Eq. 1 |
| **`T`** | ⭐ **Static appearance feature**, per Gaussian. ⚠ `D = 3` in code; initialised from `_features_dc[:,0]` | `ℝ^{N×D}` | paper §3.1; repo `_features_static` |
| **`V`** | ⭐ **View-dependent appearance feature**, per Gaussian. ⚠ `D = 3`; initialised to **zeros** | `ℝ^{N×D}` | paper §3.1; repo `_features_view` |
| **`D`** | Feature dimensionality. ⚠ **Value never stated in the paper**; code: **3** | integer | paper §3.1; repo `gaussian_model.py:724-725` |
| **`F_n`** | ⭐ **Space feature** — `MLP_s(γ(p_n))`. ⚠ 13-dimensional in code | `ℝ^{N×13}` | paper Eq. 4; repo `mlp_cont` |
| `γ(·)` | **Positional encoding**. ⚠ Frequency encoding, **16 frequencies** | — | paper Eq. 4; repo `gaussian_model.py:675-678` |
| `MLP_t`, `MLP_o`, `MLP_v`, `MLP_s` | MLPs for static colour, opacity, view-dependent colour, space feature. ⚠ All `tcnn.FullyFusedMLP`, **64 neurons, 1 hidden layer** | — | paper Eqs. 3-4; repo `gaussian_model.py:672-720` |
| `cat(·,·)` | Concatenation | — | paper Eq. 3 |
| **`z`** | An attribute vector to be quantized, `z ∈ ℝ^{ML}` | — | paper §3.2 |
| **`M`** | ⚠ **Number of sub-vectors (partitions)** in SVQ — *not* a count of views or Gaussians. Code: 1 (scale), 2 (rotation), 2 (appearance) | integer | paper Eq. 5; repo `slice_*` |
| **`L`** | ⚠ **Sub-vector length** — *not* a loss. Code: 3, 2, 3 respectively | integer | paper §3.2 |
| **`B`** | ⚠ **Number of codewords per codebook** — *not* image B or backscatter. Code: 2⁶, 2⁹, 2¹⁰ | integer | paper §3.2; repo `cluster_*` |
| `C^(m)` | The **codebook** for partition `m` | `ℝ^{B×L}` | paper §3.2 |
| `C^(m)[j]` | The `j`-th codeword of that codebook | `ℝ^L` | paper §3.2 |
| `i_m` | Selected **code index** for sub-vector `m` | ∈ {1..B} | paper Eq. 6 |
| `ẑ`, `ŝ_n`, `r̂_n`, `T̂_n`, `V̂_n` | SVQ-reconstructed quantities | — | paper Eq. 5, §3.2 |
| `q(z; M)` | The SVQ operator | — | paper Eq. 5 |
| **`Ī_i`** | ⭐ **Base importance** — accumulated blending weight, gated by "was argmax for ≥1 ray" | `ℝ^N` | paper Eq. 7 |
| **`I_i`** | ⭐ **Final importance** `= Ī_i · res^λ` | `ℝ^N` | paper Eq. 8 |
| `w_{i,ρ}` | **Blending weight** of Gaussian `i` for ray `ρ` | scalar | paper Eq. 7 |
| `NR` | Total number of rays across training views | integer | paper Eq. 7 |
| **`N_i^K`** | K-nearest neighbours of Gaussian `i`. ⚠ **`K = 2` exactly** — the Morton predecessor and successor | index set | paper Eq. 8; repo `gaussian_model.py:654-655` |
| **`λ`** | ⚠ **Scaling factor / exponent** on the distinctiveness term. Value **never stated**; code: **`2.0`**, applied as an **exponent** | scalar | paper Eq. 8; repo `lambda_ld` |
| **`τ`** | ⭐ **CDF pruning threshold** — the *only* knob spanning XS→XL: 0.96 / 0.98 / 0.99 / 0.999 / 0.9999 | scalar | paper §3.3, §4.1; repo `importance_thresh` |
| — | `net_itr = 15 000`, `svq_itr = 29 000` — **repo-only** | integers | repo `arguments/__init__.py:96-97` |
| — | `imp_metric ∈ {indoor, outdoor}` — **required CLI arg**, inherited from Mini-Splatting; absent from Eq. 7 | — | repo `README.md`; `gaussian_model.py:641-646` |
| — | `simp_iteration1/2`, `num_depth`, `num_max`, `sampling_factor`, `depth_reinit_interval` — **inherited verbatim from Mini-Splatting** | — | repo `arguments/__init__.py:89-95` |

## Cross-method collision warnings

| Symbol | In OMG it is… | Collides with |
|---|---|---|
| **`M`** | ⚠ **Number of SVQ sub-vectors** (1, 2, 2) | **Number of training views** in `../mini-splatting/` Eq. 12 and `../CompGS/`'s control schedule; the **matching network** in `../EDGS/` Eq. 3; **patch count** in `../RoMaV2/` Eq. 1. **Four unrelated meanings.** |
| **`L`** | ⚠ **SVQ sub-vector length** | **Loss** in every other folder (`L_GS`, `L_bs`, `L_matcher`, `L_refiners`, …), and the **Cholesky factor** in `../RoMaV2/` §3.3 |
| **`B`** | ⚠ **Codewords per codebook** | **Backscatter** `B̂`, `B^∞` in `../seasplat/` and `../seathru_NeRF/`; **image B** in `../RoMa/`, `../RoMaV2/`, `../EDGS/`; the Eq. 8 **base distribution** in `../RoMa/` |
| **`T`** | ⭐ **Static appearance feature** (a learned 3-D latent) | **Transmittance** in `../seathru_NeRF/` and `../mini-splatting/` Eq. 1; **thresholds** `T_sat`, `T_sim` in `../seasplat/`; **optimization steps** in `../EDGS/`; camera transform `T^cam_world` in `../seasplat/` |
| **`V`** | ⭐ **View-dependent appearance feature** | **View direction** `v_i` in `../EDGS/` §3.5; the dependency vectors `v_D`, `v_B` in `../seathru_NeRF/` Eq. 7 |
| **`F`** | ⭐ **Space feature** (an MLP output) | The **feature encoder** in `../RoMa/` Eq. 1; `f_dc`/`f_rest` SH coefficients in the 3DGS family; **fundamental matrix** in matching demos |
| **`I`** | ⭐ **Importance score** | **The captured image** in `../seasplat/` Eq. 3 and `../seathru_NeRF/` Eq. 7; **importance** in `../mini-splatting/` ✅ (consistent — both descend from the same lineage) |
| **`λ`** | **LD exponent = 2.0** | `λ_dssim = 0.2` in every 3DGS paper (**including OMG's own `lambda_dssim`**); the RD multiplier in `../CompGS/`; `L_objnorm` weight in `../seathru_NeRF/`; the marginal weight in `../RoMa/`; the position-embedding scale in `../RoMaV2/`. **OMG uses `λ` for two different things in one codebase.** |
| **`τ`** | **CDF pruning threshold** ∈ (0,1) | `τ_corr`, `τ_proj` in `../EDGS/`; the densification gradient threshold in the 3DGS family |
| **`D`** | **Feature dimensionality = 3** | **Distortion** in `../CompGS/` Eq. 1; the **direct image** in `../seasplat/` §III.B; the **match decoder** in `../RoMa/` Eq. 2; descriptor dimension in matching generally |
| **`N`** | **Number of Gaussians** ✅ | Consistent with `../mini-splatting/`, `../compact3d/`; but **anchors** in `../CompGS/` (≈10× fewer), **samples per ray** in `../seathru_NeRF/`, **pixels** in `../seasplat/` Eq. 5 |
| **`p`** | **Gaussian position** ✅ (same as `../mini-splatting/`) | **Confidence** in `../RoMa/`, `../RoMaV2/`; a **pixel** in `../EDGS/` Eq. 1; **entropy-model probability** in `../CompGS/` |
| **`s`, `r`** | **Scale, rotation** ✅ standard 3DGS | `s` = **diffusion scale** in `../RoMa/` Eq. 10; `r` = **residual** in `../RoMaV2/` Eq. 3 |
| **`α`** | 2D **opacity** at a pixel ✅ | Charbonnier shape in `../RoMa/`/`../RoMaV2/`; `[−1,1]`-ranged opacity in `../CompGS/` |
| **`w`** | **Blending weight** ✅ | Same in `../mini-splatting/`; object quadrature weight in `../seathru_NeRF/` |
| **"CompGS"** | In Tables 1–2 this is **Navaneet et al. = `../compact3d/`** `[inferred]` | Liu et al. = `../CompGS/`. The same acronym collision documented in `../CompGS/research-methodology-output/00-index.md` |

## Shared design patterns worth recording

**(a) The same degeneracy, two different answers.** `../mini-splatting/` and OMG both identify
that importance is **spatially autocorrelated**, so thresholding removes whole regions:

| Folder | Diagnosis | Remedy |
|---|---|---|
| `mini-splatting` | "neighboring Gaussians often exhibit similar importance … causing them to be either removed or preserved simultaneously" `[MS §4.2]` | **stochastic sampling**, `P_i ∝ I_i` |
| `omg` | "their blending weights tend to be highly similar … (1) abrupt degradation … (2) redundancy" `[paper §3.3]` | **deterministic distinctiveness reweighting**, `I_i = Ī_i · res^λ` |

A base method and its direct descendant diverging on the same problem.

**(b) Quantization strategy across the compression folders:**

| Folder | Strategy | Codebook | Rate in loss? |
|---|---|---|---|
| `omg` | **Sub-Vector (Product) QAT** | 64 / 512 / 1024 per partition | ❌ |
| `compact3d` | **K-means VQ**, joint with training | 4k / 32k | ❌ |
| `CompGS` (Liu) | scalar + **learned entropy model** | — | ✅ `λR` |
| `mini-splatting` (`ms_c`) | **RAHT transform coding** + zip, post-hoc | — | ❌ |
