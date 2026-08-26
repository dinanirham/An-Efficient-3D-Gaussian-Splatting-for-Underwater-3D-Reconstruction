# §9 — Notation glossary — Mini-Splatting

Method key for the merged comparison glossary: **`mini-splatting`**.
Paper: arXiv:2403.14166v3 / ECCV 2024. Repo: `fatPeter/mini-splatting` @ `c0d5581`.

| Symbol | Meaning | Type / shape | First defined |
|---|---|---|---|
| `G_i` | The `i`-th 3D Gaussian primitive | — | paper §3.1 |
| `N` | **Number of Gaussians in the scene** (the quantity the paper minimises) | integer | paper §3.1 |
| `p_i` | Gaussian **center** (position). ⚠ The paper uses `p`, not `μ` | `(3,)` | paper §3.1; repo `gaussian_model.py` `_xyz` |
| `Σ_i` | Gaussian **covariance** in world space, `Σ = R S Sᵀ Rᵀ` | `(3,3)` | paper §3.1 |
| `s = (s_x, s_y, s_z)` | Per-Gaussian **scale**; also the ellipsoid semi-axes in App. D | `(3,)` | paper §3.1, App. D; repo `_scaling` |
| `α_i` | Gaussian **opacity** ∈ [0,1] | scalar | paper §3.1; repo `_opacity` |
| `c_i` | View-dependent **colour** from SH coefficients | `(3,)` | paper §3.1; repo `_features_dc`/`_features_rest` |
| `G_i^{2D}` | The **projected 2D Gaussian** of `G_i` via local affine approximation (Zwicker et al. [43]) | — | paper Eq. 1 |
| `c(x)` | Rendered pixel colour `Σ_i w_i c_i` | `(3,)` | paper Eq. 1 |
| `w_i` | **Blending weight** `T_i·α_i·G_i^{2D}(x)`. The atom of every importance metric here | scalar | paper Eq. 1 |
| `T_i` | Transmittance `Π_{j<i}(1 − α_j G_j^{2D}(x))` | scalar | paper Eq. 1 |
| `i(x)` | **Projected index** — the set of pixels `G_i` projects onto | — | paper §4.1; repo `area_proj` (as a count) |
| `i_max(x)` | **Rendered index** — `argmax_i w_i` at pixel `x`, i.e. the *dominant* Gaussian | integer per pixel | paper §4.1 |
| `I_max` | The set of all indices appearing in `i_max(x)` over an image | index set | paper Eq. 3 |
| `S_i` | **Maximum-contribution area** — `Σ_x 𝟙(i(x) = i_max(x))`, the pixel count over which `G_i` dominates | integer | paper Eq. 2; repo `area_max` (`accum_max_count`) |
| `T_blur` | Blur threshold `θ_blur · H · W` | scalar | paper Eq. 2 |
| `θ_blur` | Blur ratio, **`2×10⁻⁴`** (repo: `1/5000`) | scalar | paper Eq. 2; repo `ms/train.py:151` |
| `G^{blur}` | `{G_i : S_i > T_blur}` — the set to split | Gaussian set | paper Eq. 2; repo `mask_blur` |
| `G^{int}` | `{G_i : i ∈ I_max}` — **intersected** Gaussians, those that dominate somewhere | Gaussian set | paper Eq. 3; repo realised as `imp_score[accum_area_max==0]=0` |
| `d_i` | Depth of the center of `G_i` | scalar | paper §4.1 |
| `d^{blend}` | **Alpha-blended** depth `Σ_i w_i d_i` — the one the paper argues *against* | scalar | paper §4.1 |
| `d^{center}` | Depth of the argmax Gaussian's **center**, `d_{i_max}` | scalar | paper §4.1 |
| `d^{mid}` | Depth of the ray/ellipsoid **mid-point** of the argmax Gaussian — **the one used** | scalar | paper §4.1, App. D |
| `t^{mid}` | `−b/2a` from the ray/ellipsoid quadratic; equals `t^{opt}` | scalar | paper App. D / Eq. 7 |
| `t^{opt}` | The `t` maximising Gaussian density along the ray, `−B/2C` | scalar | paper App. D / Eq. 11 |
| `Δ` | Discriminant `b² − 4ac` — the reason the mid-point form is preferred over `t^{opt}` | scalar | paper App. D / Eq. 7 |
| `a, b, c` | Coefficients of the ray/ellipsoid quadratic. ⚠ **`c` here is NOT colour** | scalars | paper App. D / Eq. 5 |
| `A, B, C` | Coefficients of the log-density form `N = A exp(Bt + Ct²)`. ⚠ Unrelated to `a,b,c` | scalars | paper App. D / Eq. 10 |
| `r(t) = o + td` | Ray, in the **ellipsoid's** coordinate frame | — | paper App. D |
| `o, d` | Ray origin and direction (ellipsoid frame). ⚠ `o` is **not** opacity here | `(3,)` | paper App. D |
| `I_i` | **Importance** of `G_i` — generic | scalar | paper §3.2 |
| `I_i¹` | `Σ_{j=1..K} w_ij` — accumulated blending weight. **Used for INDOOR** | scalar | paper §3.2, App. E; repo `--imp_metric indoor` |
| `I_i²` | `Σ_m I_i^{(m)}·𝟙(i ∈ I_max^{(m)})`, `I_i^{(m)} = Σ_j w_ij^{(m)}/S_i^{(m)}`. **Used for OUTDOOR** | scalar | paper Eq. 12, App. E; repo `--imp_metric outdoor` |
| `K` | Number of rays intersecting `G_i` | integer | paper §3.2 |
| `M` | Number of training images | integer | paper Eq. 12 |
| `P_i` | **Sampling probability** `I_i / Σ_k I_k` | scalar | paper §4.2 |
| `δ(·)` / `𝟙(·)` | Indicator function. ⚠ `δ` here is **not** a ray-interval length | — | paper Eq. 2, Eq. 12 |
| `(H, W)` | Image resolution | integers | paper Eq. 2 |
| Mini-Splatting | densification **+** simplification; ≈0.2–0.6 M Gaussians | variant | paper §5 |
| Mini-Splatting-**D** | densification **only**; ≈3.8–5.4 M Gaussians (**more** than 3DGS) | variant | paper §5 |
| Mini-Splatting-**C** | Mini-Splatting **+** RAHT transform coding + zip | variant | paper §5, App. F |
| `Qstep` | Quantization step for RAHT coefficients, **0.02** | scalar | paper App. F; repo `ms_c/run.py:136` |
| `depth` (App. F) | RAHT octree depth, **16**. ⚠ **Not** a distance | integer | paper App. F; repo `ms_c/run.py:135` |
| — | `--sampling_factor` = **0.5**; `--num_max` = **4.5 M**; CDF threshold **0.99** | scalars | **repo-only**, `ms/train.py:406-407, 282` |

## Cross-method collision warnings

For merging into `../../comparison-glossary.md`:

| Symbol | In Mini-Splatting it is… | Collides with |
|---|---|---|
| **`p`** | Gaussian **position** (this paper's choice of glyph for the mean) | Every other 3DGS paper in the set — `seasplat/`, `compact3d/`, `OMG/`, `EDGS/` — writes the mean as **`μ`**. Also `P_i` (capital) is a *probability* in this same paper. Three-way clash. |
| **`Σ`** | Gaussian **covariance** | Summation operator in every paper; in `compact3d/` also the covariance *being quantized*; in `seathru_NeRF/` the related lower-case `σ` is a **density**. |
| **`σ`** | *(not used)* — this paper writes scale as `s`, avoiding the clash | `seathru_NeRF/`: **density**. Note the absence is itself worth recording. |
| **`d`** | Two meanings **within this paper**: (a) **depth** (`d_i`, `d^{mid}`, `d^{blend}`) in §4.1; (b) **ray direction** in App. D | `RoMa/`/`RoMaV2/`: descriptor dimension. `seasplat/`: `D` is the direct image. |
| **`o`** | Ray **origin** in App. D | **Opacity** in `seasplat/`, `compact3d/`, `OMG/`, and in 3DGS itself. This paper uses `α` for opacity — the opposite convention. **High collision risk.** |
| **`c`** | Two meanings: (a) **colour** `c_i` in §3.1; (b) the **quadratic coefficient** in App. D Eq. 5 | Colour in all papers; codebook **code** in `compact3d/`. |
| **`α`** | Gaussian **opacity** | Per-Gaussian alpha in `seasplat/` Eq. 1 ✅ consistent; but *accumulated* alpha map in `seasplat/` Eq. 9, and the **object alpha per interval** in `seathru_NeRF/`. |
| **`T`** | **Transmittance** in the rasterizer | `T^obj` transmittance in `seathru_NeRF/` ✅ consistent; but `T_sat`/`T_sim` are **thresholds** in `seasplat/` and `T_blur` is a **threshold** here too. Same paper, both meanings. |
| **`I`** | **Importance score** `I_i`, `I_i¹`, `I_i²` | **The captured image** in `seasplat/` (Eq. 3) and `seathru_NeRF/` (Eq. 7). Directly opposed meanings for the same glyph across the underwater and efficiency halves of the set. |
| **`δ`** | **Indicator function** (Eq. 12) | **Ray-interval length** in `seathru_NeRF/` (Eq. 4). Completely unrelated. |
| **`w`** | **Blending weight** `T_i α_i G^{2D}_i` | Object quadrature weight `w^obj` in `seathru_NeRF/` — *structurally analogous* (both are `T·α`), which makes this one of the few genuinely comparable symbols. Network **weights** in `compact3d/`. |
| **`N`** | **Number of Gaussians** — the paper's central quantity | Samples per ray in `seathru_NeRF/`; number of **pixels** in `seasplat/` Eq. 5; Gaussians per ray in `seasplat/` Eq. 1. |
| **`depth`** | RAHT **octree level** (=16) in App. F | Actual **depth/range** everywhere else, including elsewhere in this same paper. |
| **`S`** | **Maximum-contribution area** `S_i` (a pixel count) | Per-Gaussian **scale matrix** in `seasplat/` §III.A and in 3DGS. Same glyph, one is an integer count, the other a 3×3 factor. |
