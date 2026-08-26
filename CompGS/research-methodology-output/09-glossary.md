# §9 — Notation glossary — CompGS (Liu et al.)

Method key for the merged comparison glossary: **`compgs-liu`**.
Paper: `../../CompGS.pdf` = **arXiv:2404.09458v1**.
Repo: `LiuXiangrui/CompGS` @ `d501617`.

> **Disambiguation:** the merged glossary must distinguish this method from
> **`compgs-vq`** (= `../../compact3d/`, Navaneet et al., ECCV 2024), which shares the name
> "CompGS" and is a *baseline* here (`Navaneet et al. [33]`).

| Symbol | Meaning | Type / shape | First defined |
|---|---|---|---|
| `ω` | An **anchor primitive** — the predictor tier | — | paper §3.1 |
| `Ω` | The set of all anchor primitives | — | paper Eq. 1 |
| `γ_k` | A **coupled primitive** — the predicted tier; carries only `g_k` | — | paper §3.1 |
| `Γ` | The set of all coupled primitives | — | paper Eq. 1 |
| `K` | Coupled primitives per anchor = **10** (`derive_factor`) | integer | paper §3.4; repo `Configs/*.yaml` |
| `μ_ω` | Anchor **location**. ⚠ **Frozen** (lr = 0) at voxelized SfM positions | `(N,3)` | paper §3.1; repo `Model.py`, `Configs/*.yaml` |
| `Σ_ω` | Anchor **covariance** in the paper; in code a **6-D scaling vector** (`scales_before_exp`) + a separate quaternion. The 6-vector splits into `[0:3]` = offset modulation, `[3:6]` = scale modulation | `(N,6)`+`(N,4)` | paper §3.1/Eq. 2; repo `Prediction.py:69` |
| `f_ω` | **Reference embedding** of an anchor, dim **32** | `(N,32)` | paper §3.1, §3.4; repo `ref_feats` |
| `g_k` | **Residual embedding** of a coupled primitive, dim **8** — the paper's core object | `(N,K,8)` | paper §3.1, §3.4; repo `res_feats` |
| `h_k` | **Prediction features** `= f_ω ⊕ g_k`, dim 40 | `(N·K,40)` | paper §3.2; repo `Prediction.py:47` |
| `⊕` | Channel-wise concatenation | — | paper §3.2 |
| `θ_k` | **Affine parameters** predicted from `h_k` | — | paper Eq. 2 |
| `𝒜` | The **affine transform** `μ_k, Σ_k = 𝒜(μ_ω, Σ_ω | θ_k)`. ⚠ Implemented as Scaffold-GS offset prediction, not a general affine warp | — | paper Eq. 2 |
| `t_k` | Predicted **translation vector**. Repo: `means_offset`, then scaled by `exp(Σ_ω[0:3])` | `(·,3)` | paper Eq. 3; repo `Prediction.py:49,76` |
| `S_k` | Predicted **scaling matrix**. Repo: `sigmoid(u_k[0:3]) ⊙ exp(Σ_ω[3:6])` | `(·,3)` | paper Eq. 3; repo `Prediction.py:77` |
| `R_k` | Predicted **rotation matrix**. Repo: a normalized quaternion. ⚠ Collides with the rate symbol `R` | `(·,4)` | paper Eq. 3; repo `Prediction.py:78` |
| `𝒯, 𝒮, ℛ` | The three prediction networks of Eq. 3. ⚠ The repo has **two** geometry MLPs | — | paper Eq. 3 |
| `μ_k` | Location of coupled primitive `k` | `(·,3)` | paper Eq. 4 |
| `Σ_k` | Covariance of coupled primitive `k`. ⚠ Eq. 4 writes `Σ_k = S_k R_k`, not a valid factorisation | — | paper Eq. 4 |
| `α_k` | **Opacity** of a coupled primitive. ⚠ Repo: `Tanh` ⇒ range `[−1,1]`, and `α_k ≤ 0` means **culled** | `(·,1)` | paper Eq. 5; repo `Prediction.py:28,65` |
| `c_k` | View-dependent **colour**, `Sigmoid` | `(·,3)` | paper Eq. 5; repo `Prediction.py:29` |
| `γ` (view) | ⚠ **Overloaded.** §3.1 uses `γ_k` for a *coupled primitive*; Eq. 5 uses `γ` for the *view embeddings*. Repo: 4-D `[direction(3), distance(1)]` computed at the **anchor** | `(N,4)` | paper §3.1 vs Eq. 5; repo `Prediction.py:27,53-56` |
| `𝒞, 𝒪` | Colour and opacity prediction networks | — | paper Eq. 5 |
| `Q(·)` | **Scalar quantization** (rounding) | — | paper Eq. 6 |
| `s_Σ, s_f, s_g` | **Quantization steps** for `Σ_ω`, `f_ω`, `g_k`. `s_f = s_g = 1` fixed; `s_Σ` learnable, init 0.01 — repo makes it a **6-vector** | scalars / `(6,)` | paper Eq. 6, §3.4; repo `EntropyModel.py:228` |
| `Δ_Σ, Δ_f, Δ_g` | **Quantization noises**, `~ U(−½, ½)`, the differentiable surrogate for rounding | — | paper Eq. 7 |
| `x̃` (tilde) | The noise-perturbed / quantized version of `x` | — | paper Eq. 7 |
| `z_f` (paper: `f̄`) | **Hyperprior** for `f_ω`, dim **4** (`ref_hyper_dim`) | `(N,4)` | paper Eq. 8; repo `Configs/*.yaml` |
| `z_g` (paper: `ḡ`) | **Hyperprior** for `g_k`, dim **1** (`res_hyper_dim`) | `(N,1)` | paper Eq. 11; repo `Configs/*.yaml` |
| `E_f, E_Σ, E_g` | **Parameter prediction networks** producing `(μ, σ)` for each conditional Gaussian | — | paper Eqs. 8, 10, 11 |
| `μ_f, σ_f` etc. | Mean/scale of the **conditional Gaussian entropy model**. ⚠ `σ` here is an entropy-model scale, **not** a Gaussian-primitive scale and **not** a density | — | paper Eqs. 8, 10, 11 |
| `p(·)` | Estimated probability under the entropy model | — | paper Eqs. 8-12 |
| `R_f, R_Σ, R_gk` | **Bitrate** of each component | scalars | paper Eqs. 9, 12 |
| `R_ω,Γ` | Total bitrate of an anchor + its `K` coupled primitives, `= R_f + R_Σ + Σ_k R_gk` | scalar | paper Eq. 13 |
| `R` | Total **rate** over the whole scene | scalar | paper Eq. 1 |
| `D` | **Distortion** = the 3DGS rendering loss `0.8·L₁ + 0.2·(1−SSIM)` | scalar | paper Eq. 1, §3.3 |
| `λ` | **Lagrange multiplier**, ∈ `{0.001, 0.005, 0.01}` | scalar | paper Eq. 1, §3.4; repo `lambda_weight` |
| `L` | **Rate-distortion cost** `= λR + D`. ⚠ Eq. 1 as printed reads `arg max`; §3.1 prose and the repo both **minimize** | scalar | paper Eq. 1 |
| — | `REG = 0.01·mean(∏ scale_k)` — **repo-only** volume regulariser | scalar | repo `TrainerCompGS.py:220` |
| — | `aux_loss` — **repo-only** entropy-bottleneck CDF objective, separate optimizer | scalar | repo `TrainerCompGS.py:235` |
| — | `rate_loss_start_iteration = 3000` — **repo-only** rate warm-up | integer | repo `Configs/*.yaml` |
| — | `voxel_size` = 0.001 (M360) / 0.01 (T&T, DB) — **repo-only** | scalar | repo `Configs/*.yaml` |
| — | `couple_threshold`(40), `grad_threshold`, `opacity_threshold`, `update_depth`(3), `update_hierarchy_factor`(4), `update_init_factor`(16) — Scaffold-GS adaptive control | — | repo `Configs/*.yaml`; `AdaptiveControl.py` |

## Cross-method collision warnings

For merging into `../../comparison-glossary.md`:

| Symbol | In CompGS (Liu) it is… | Collides with |
|---|---|---|
| **`R`** | **BITRATE** — the rate term of the rate-distortion cost | **Rotation matrix** in 3DGS, `seasplat/`, `compact3d/`, `mini-splatting/` — *and in this same paper*, where `R_k` (Eq. 3) is a rotation matrix while `R` (Eq. 1) is the rate. **The single worst collision in the entire comparison set**, and it is internal to one paper. |
| **`D`** | **DISTORTION** — the rendering loss | **Direct image** (`J·e^{-β^D Z}`) in `seasplat/`; descriptor dimension in `RoMa/`, `RoMaV2/`; depth in `mini-splatting/`. |
| **`Σ`** | Anchor "covariance" — but in code a **6-D scaling vector**, not a 3×3 matrix | Gaussian covariance (a genuine 3×3) in `seasplat/`, `compact3d/`, `mini-splatting/`; summation operator everywhere. |
| **`σ`** | The **scale parameter of a conditional Gaussian entropy model** (`σ_f`, `σ_Σ`, `σ_g`) | **Volumetric density** in `seathru_NeRF/` and `nerf/`; **Gaussian scale** in the 3DGS family. Three unrelated meanings. |
| **`μ`** | Two meanings **within this paper**: (a) anchor/coupled **position** `μ_ω`, `μ_k`; (b) the **mean of the entropy model's Gaussian** `μ_f`, `μ_Σ`, `μ_g` | Gaussian mean in the 3DGS family (consistent with (a)); **codebook centroid** in `compact3d/`. |
| **`γ`** | Two meanings **within this paper**: (a) a **coupled primitive** `γ_k` (§3.1); (b) the **view embedding** (Eq. 5) | — |
| **`λ`** | **Rate-distortion Lagrange multiplier**, 1e-3…1e-2 | `λ_dssim = 0.2` in every 3DGS paper; weight of `L_objnorm` (1e-4) in `seathru_NeRF/`; six different λ in `seasplat/`. Always subscript. |
| **`α`** | Coupled-primitive **opacity**, but ranging over `[−1, 1]` with `≤ 0` meaning "does not exist" | Opacity ∈ `[0,1]` everywhere else; accumulated alpha map in `seasplat/` Eq. 9; per-interval object alpha in `seathru_NeRF/`. **The range differs**, not just the meaning. |
| **`K`** | **Coupled primitives per anchor** (= 10) | Camera **intrinsics** matrix in `seasplat/` §IV.A and `seathru_NeRF/` §4.1; number of rays intersecting a Gaussian in `mini-splatting/` §3.2; **codebook size** in `compact3d/`. Four meanings. |
| **`N`** | Number of **anchor** primitives — **not** the rendered count | Number of Gaussians in `mini-splatting/`, `compact3d/`, `OMG/`; samples per ray in `seathru_NeRF/`; pixels in `seasplat/` Eq. 5. **Even within the "number of primitives" reading, CompGS's `N` is ~10× smaller than the comparable quantity.** |
| **`f`** | **Reference embedding** `f_ω` (a learned 32-D latent) | `f_dc`/`f_rest` = SH coefficients in the 3DGS family. Related in role (colour-ish features), unrelated in definition. |
| **`t`** | Predicted **translation vector** `t_k` | Ray parameter in `seathru_NeRF/` and `mini-splatting/` App. D. |
| **`S`** | Predicted **scaling matrix** `S_k` | Per-Gaussian scale in 3DGS ✅ roughly consistent; **maximum-contribution area** (a pixel count) in `mini-splatting/`. |
| **`p`** | **Probability** under the entropy model | Gaussian **position** in `mini-splatting/` (that paper's choice of glyph for the mean); sampling probability `P_i` in `mini-splatting/` §4.2. |
| **"CompGS"** | **The method name itself collides.** Liu et al., ACM MM 2024, arXiv:2404.09458 | Navaneet et al., ECCV 2024, arXiv:2311.18159 = `../../compact3d/`, which is a **baseline in this paper's own tables** (`Navaneet et al. [33]`). |
