# §9 — Notation glossary — EDGS

Method key for the merged comparison glossary: **`edgs`**.
Paper: arXiv:2504.13204v2 / CVPR 2026. Repo: `CompVis/EDGS` @ `f90b022`
(code content = `668e280`, 2025-04-21).

> EDGS writes Gaussian parameters with a **superscripted `g`** rather than the usual
> `μ, Σ, o, c` — a notation unique to this paper within your comparison set.

| Symbol | Meaning | Type / shape | First defined |
|---|---|---|---|
| `G` | The set of all Gaussians, `G = ∪_{i=1}^N g_i` | — | paper §3.1 |
| `g_i` | The `i`-th Gaussian, `{g_i^x, Σ_i, g_i^c, g_i^α}` | — | paper §3.1 |
| `g_i^x` | Gaussian **center / position** in ℝ³. ⚠ Written `g^x`, not `μ` | `(N,3)` | paper §3.1; repo `_xyz` |
| `Σ_i` | Gaussian **shape**, stated as `∈ ℝ⁷` (3 scale + 4 quaternion), reparameterised `Σ_i = R_i S_i S_iᵀ R_iᵀ` | `(N,7)` | paper §3.1, Eq. 2; repo `_scaling`+`_rotation` |
| `R_i`, `S_i` | Rotation and scaling matrices factoring `Σ_i` | — | paper Eq. 2 |
| `g_i^c` | Gaussian **RGB colour** ∈ ℝ³ (the SH DC term). ⚠ Written `g^c`, not `c` | `(N,3)` | paper §3.1; repo `_features_dc` |
| `g_i^α` | Gaussian **opacity** ∈ ℝ¹. ⚠ Written `g^α`, not `o` | `(N,1)` | paper §3.1; repo `_opacity` |
| `α_i(p)` | The **influence** of Gaussian `i` at pixel `p`, `g_i^α · exp(−½ (p−g_i^x)ᵀ Σ_i^{-1} (p−g_i^x))`. ⚠ Distinct from `g_i^α` | scalar | paper Eq. 1 |
| `C(p)` | Rendered pixel colour | `(3,)` | paper Eq. 1 |
| `p` | ⚠ **Overloaded.** (a) a **pixel** in Eq. 1; (b) the **sampling distributions** `p^corr`, `p^proj`, `p_i(k)`, `p(k)` in §3.4 | — | paper Eq. 1 vs §3.4 |
| `I_i` | **Reference image**. Repo: chosen by k-means over flattened `world_view_transform` | — | paper §3.2; repo `corr_init.py:555` |
| `𝓘_i` | The set of `J` neighbouring images of `I_i`, by **Frobenius distance** between pose matrices | — | paper §3.2; repo `corr_init.py:41` |
| `J` | Neighbours per reference (`nns_per_ref`, default **3**) | integer | paper §3.2; repo `configs/train.yaml` |
| `M` | ⚠ **Overloaded.** (a) the pretrained **matching network** (RoMa) in Eq. 3; (b) `matches_per_ref` = **15 000** in the repo | — | paper Eq. 3; repo `corr_init.py:540` |
| `W_ij` | Dense **forward warp field** from `I_i` to `I_j` | `(2,H,W)` | paper Eq. 3; repo `corr_init.py:100-177` |
| `c_ij` | **Correspondence confidence** ("certainty") map from the matcher | `(H,W)` | paper Eq. 3 |
| `(u_i^k, v_i^k)` | Pixel coordinates of match `k` in image `I_i` | — | paper §3.2 |
| `P^i` | Camera **projection matrix** for view `i`, ℝ^{4×3} | `(4,3)` | paper Eq. 4 |
| `P^i_col,m` | The `m`-th **column** of `P^i` | — | paper Eq. 5 |
| `w_i^k` | Homogeneous-coordinate normalisation scalar | scalar | paper Eq. 4 |
| `A`, `b` | The DLT system, `A g^x = −b` | `(4,3)`, `(4,)` | paper Eq. 6 |
| `g_k^x` | Triangulated position, `argmin_x ‖Ax + b‖²` — solved by `torch.linalg.lstsq` | `(3,)` | paper Eq. 7; repo `corr_init.py:471-472` |
| `π(P, ·)` | Projection with camera matrix `P` | — | paper Eq. 8 |
| `ε_i^k` | **Reprojection error** in view `i`, `‖π(P^i, g_k^x) − (u_i^k,v_i^k)‖₂` | scalar | paper Eq. 8 |
| `ε_ij^k` | `max(ε_i^k, ε_j^k)` — the worse of the two | scalar | paper §3.4 |
| `τ_corr` | Confidence threshold. ⚠ **No config key**; repo uses `roma_model.sample_thresh` | scalar | paper Eq. 9; repo `corr_init.py:541` |
| `τ_proj` | Reprojection-error threshold (`proj_err_tolerance` = **0.01**) | scalar | paper Eq. 10; repo `configs/train.yaml` |
| `p_ij^corr` | `U{k : c_ij(u_i^k,v_i^k) > τ_corr}` — **matcher-confidence** filter | — | paper Eq. 9 |
| `p_ij^proj` | `U{k : ε_ij^k < τ_proj}` — **geometric-consistency** filter. ⚠ Implemented as an **opacity mask** (logit −10), not a sampling distribution | — | paper Eq. 10; repo `corr_init.py:660-666` |
| `p_i(k)` | `max_{j∈𝓘_i}( p_ij^corr · p_ij^proj )` — per-reference distribution | — | paper Eq. 11 |
| `p(k)` | `Π_i p_i^k` — global sampling distribution across references | — | paper §3.4 |
| `O_k` | `n` RGB **observations** of splat `k` from directions `v_1..v_n`. ✗ no code | `(n,3)` | paper §3.5 |
| `Y_k` | Matrix of **16 real SH basis functions** (degree ≤ 3) evaluated at `v_1..v_n`. ✗ no code | `(n,16)` | paper §3.5 |
| `Ĥ_k` | Estimated **SH coefficients**, `argmin_H ‖Y_k H − O_k‖_F²`, or `Y_k^+ O_k` when `n < 16`. ✗ **no code — `f_rest ← 0`** | `(16,3)` | paper Eqs. 12-13; repo `corr_init.py:659` |
| `Y_k^+` | Moore–Penrose pseudoinverse (ref [56]). ✗ no code | — | paper Eq. 13 |
| `g_i(t)` | State of Gaussian `i` at optimization step `t` | — | paper §4.5 |
| `T` | Total number of optimization steps | integer | paper Eqs. 14-15 |
| — | **displacement** `(‖g^c(0)−g^c(T)‖₂, ‖g^x(0)−g^x(T)‖₂)` | `(2,)` | paper Eq. 14 |
| — | **trajectory length** `(Σ_t‖g^c(t)−g^c(t+1)‖₂, Σ_t‖g^x(t)−g^x(t+1)‖₂)` | `(2,)` | paper Eq. 15 |
| `#G` | Final Gaussian count, in millions. ⚠ For ScaffoldGS rows this means **derived splats**, not anchors | — | paper Tab. 1 |
| — | `num_refs` = **180**, `scaling_factor` = **0.001**, `add_SfM_init` = **False** | — | repo `configs/train.yaml` |
| — | `reduce_opacity` (×0.99 every 10 steps), `max_lr` (`max(step, 8000)`) — **repo-only** | — | repo `trainer.py:81-85, 146-147` |

## Cross-method collision warnings

For merging into `../../comparison-glossary.md`:

| Symbol | In EDGS it is… | Collides with |
|---|---|---|
| **`g^x`, `g^c`, `g^α`** | Gaussian position / colour / opacity — **a superscript convention unique to this paper** | Every other 3DGS paper writes these `μ`/`p`, `c`, `o`/`α`. EDGS's `g` is not any of those glyphs, so the *risk here is failing to align rows*, not mis-aligning them. In particular: **EDGS `g^x` = `seasplat` `μ` = `mini-splatting` `p` = `CompGS` `μ_ω`/`μ_k`.** |
| **`α`** | Two meanings **within this paper**: (a) `g_i^α`, the stored **opacity**; (b) `α_i(p)`, the **per-pixel influence** `g^α · exp(−½ …)` of Eq. 1 | Per-Gaussian alpha in `seasplat/` Eq. 1; accumulated alpha map in `seasplat/` Eq. 9; per-interval object alpha in `seathru_NeRF/`; `Tanh`-ranged `[−1,1]` opacity in `CompGS/`. |
| **`M`** | Two meanings **within this paper**: (a) the **matching network** (RoMa) in Eq. 3; (b) `matches_per_ref` in the repo | Number of **training views** in `mini-splatting/` Eq. 12 and `CompGS/`'s control schedule. |
| **`p`** | Two meanings: (a) a **pixel** (Eq. 1); (b) **sampling distributions** (§3.4) | Gaussian **position** in `mini-splatting/`; **probability** under the entropy model in `CompGS/`; sampling probability `P_i` in `mini-splatting/` §4.2. **Four-way clash.** |
| **`Σ`** | Gaussian **shape**, stated as `∈ ℝ⁷` — i.e. the *parameter vector*, not the 3×3 matrix, though Eq. 2 gives the matrix form | 3×3 covariance in `seasplat/`, `mini-splatting/`, `compact3d/`; a **6-D scaling vector** in `CompGS/`; summation operator everywhere. |
| **`c`** | Confidence map `c_ij`, **and** colour `g^c` | Colour in all 3DGS papers; codebook **code** in `compact3d/`; a **quadratic coefficient** in `mini-splatting/` App. D. |
| **`P`** | Camera **projection matrix** | Sampling **probability** `P_i` in `mini-splatting/`; probability `p(·)` in `CompGS/`. |
| **`τ`** | **Thresholds** `τ_corr`, `τ_proj` | Densification gradient threshold in 3DGS-family pseudocode; `T_sat`/`T_sim` in `seasplat/` are the same *concept* under a different glyph. |
| **`ε`** | **Reprojection error** | The RawNeRF denominator floor `ε = 1e-3` in `seathru_NeRF/` Eq. 25. |
| **`T`** | Number of **optimization steps** | **Transmittance** in `seathru_NeRF/` and `mini-splatting/` Eq. 1; **thresholds** in `seasplat/`. |
| **`W`** | Dense **warp field** `W_ij` | Image **width** in `mini-splatting/` Eq. 2 and `seasplat/`. |
| **`H`** | ⚠ `Ĥ_k` is the **SH coefficient matrix**; `H` is also image **height** | Image height across the whole set. |
| **`J`** | Number of **neighbour views** | The **medium-free true colour** `J` in `seasplat/` and `seathru_NeRF/` — a completely unrelated, and central, quantity in the underwater half of the set. |
| **`v`** | **View direction** `v_i` (§3.5) | `v_D`, `v_B` — the *dependency vectors* of the attenuation/backscatter coefficients in `seathru_NeRF/` Eq. 7. |
| **`N`** | Number of **Gaussians** | Samples per ray in `seathru_NeRF/`; **pixels** in `seasplat/` Eq. 5; **anchors** in `CompGS/`. |
| **`n`** | Number of **RGB observations** per splat (§3.5) | — |
