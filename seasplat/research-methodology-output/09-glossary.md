# §9 — Notation glossary — SeaSplat

Method key for the merged comparison glossary: **`seasplat`**.
Paper: arXiv:2409.17345v2. Repo: `dxyang/seasplat` @ `ddc6259`.

| Symbol | Meaning | Type / shape | First defined |
|---|---|---|---|
| `I` | Captured (in-medium) image — the observation | `(3,H,W)`, `[0,1]` | paper §III.B, Eq. 3 |
| `J` | True colour of the scene **as if no medium were present** | `(3,H,W)` | paper §III.B, Eq. 3 |
| `Ĵ` | *Estimated* `J` — the raw 3DGS rasterizer output | `(3,H,W)` | paper §IV.A; repo `train.py:201` (`rendered_image`) |
| `Î` | Reconstructed in-medium image, `Ĵ⊙Â + B̂` | `(1,3,H,W)` | paper §IV.A; repo `train.py:273` (`underwater_image`) |
| `Z` | **Range from the camera**, *not* depth below the sea surface | `(1,H,W)` | paper §III.B (explicit disambiguation) |
| `Ẑ` | Estimated `Z` from a second rasterization pass; `Z_raw/α`, then per-frame min–max normalised to `[0,1]` | `(1,H,W)` | paper §IV.A; repo `train.py:220-237` |
| `β^D` | **Attenuation** coefficient — wavelength-dependent, **global scalar per colour channel** | `(3,1,1,1)` conv kernel | paper §III.B, Eq. 3; repo `models.py:216` (`attenuation_conv_params`) |
| `β^B` | **Backscatter** coefficient — wavelength-dependent, **global scalar per colour channel**; `β^B ≠ β^D` by design | `(3,1,1,1)` conv kernel | paper §III.B, Eq. 3; repo `models.py:54` (`backscatter_conv_params`) |
| `B^∞` (paper writes `B`) | Backscatter water colour **at infinite range** (veiling light) | `(3,1,1)`, stored as logit, used as `σ(B^∞)` | paper §III.B, Eq. 3; repo `models.py:61` (`B_inf`) |
| `Â` | Attenuation map `= e^{-β^D Ẑ}` | `(1,3,H,W)` | paper §IV.A; repo `models.py:232` |
| `B̂` | Backscatter image `= B^∞(1-e^{-β^B Ẑ})` | `(1,3,H,W)` | paper §IV.A; repo `models.py:77` |
| `D` | **Direct image** `= J·e^{-β^D Z}` — the attenuated true colour | `(1,3,H,W)` | paper §III.B (final sentence) |
| `D̂` | ⚠ **Overloaded in the paper.** (a) §III.B/§IV.A: `Ĵ⊙Â`, the modelled direct image. (b) Eq. 4: `I − B̂`, the *empirical* backscatter-removed observation. Equal only at the optimum. I write (b) as `D̃`. | `(1,3,H,W)` | paper §III.B **and** Eq. 4; repo `train.py:256` vs `train.py:400` |
| `μ` | Gaussian mean (3D position) | `(N,3)` | paper §III.A; repo `gaussian_model.py` `_xyz` |
| `Σ` | Gaussian covariance, factored as `Σ = R S Sᵀ Rᵀ` | derived from `(N,3)`+`(N,4)` | paper §III.A |
| `S` | Per-Gaussian scale (the factor of `Σ`) | `(N,3)`, log-space | paper §III.A; repo `_scaling` |
| `R` | Per-Gaussian rotation (the factor of `Σ`) | `(N,4)` quaternion | paper §III.A; repo `_rotation` |
| `o` | Gaussian opacity | `(N,1)`, logit-space | paper §III.A; repo `_opacity` |
| `c` | Gaussian colour from SH coefficients — **degree 0 only**, so view-independent | `(N,1,3)` | paper §III.A, §IV.C; repo `_features_dc`, `arguments/__init__.py:49` |
| `α(x)` | Per-Gaussian alpha at pixel `x` in Eq. 1; **also** used for the *accumulated* alpha map in Eq. 9 | scalar / `(1,H,W)` | paper Eq. 1 (per-Gaussian) and Eq. 9 (accumulated); repo `train.py:202` (`image_alpha`, accumulated) |
| `C(x)` | Alpha-composited pixel colour, `Σᵢ cᵢαᵢ Πⱼ<ᵢ(1-αⱼ)` | scalar per channel | paper Eq. 1 |
| `T^cam_world` | World-to-camera extrinsic | `SE(3)` | paper §IV.A |
| `K` | Camera intrinsics | `(3,3)` | paper §IV.A |
| `N` | ⚠ **Overloaded.** (a) Eq. 1: number of Gaussians along a ray. (b) Eq. 5: number of **pixels** in `Ĵ`. | integer | paper Eq. 1 vs §IV.B |
| `λ` | 3DGS D-SSIM mixing weight (`lambda_dssim = 0.2`) | scalar | paper Eq. 2; repo `arguments/__init__.py:98` |
| `k` | Asymmetry factor in `L_bs`; paper says only `k>1`, repo sets **1000** | scalar | paper Eq. 4; repo `losses.py:147` (`cost_ratio`) |
| `T_sat` | Oversaturation threshold, **0.7** | scalar | paper Eq. 6 / §IV.B; repo `train.py:98` |
| `T_sim` | Colour-similarity threshold in `L_op`; paper leaves it free, repo fixes **`0.2√3`** | scalar | paper Eq. 9; repo `losses.py:248` |
| `J'` | Residual term of the SeaThru backscatter model — **present in code, disabled by default** | `(3,1,1)` | repo `models.py:59` (`J_prime`); not in paper |
| `bg` | Learned background colour — **repo-only, absent from the paper**; transferred into `B^∞` at `seathru_from_iter` | `(3,)` logit | repo `train.py:130, 209-212` |
| `L_GS` | Base 3DGS loss, `(1-λ)L₁ + λ L_D-SSIM` | scalar | paper Eq. 2 |
| `L_bs` | Backscatter (asymmetric dark-channel) loss | scalar | paper Eq. 4 |
| `L_gw` | Grey-world prior loss | scalar | paper Eq. 5 |
| `L_sat` | Oversaturation loss | scalar | paper Eq. 6 |
| `L_Z-recon` | Depth-weighted reconstruction loss | scalar | paper Eq. 7 |
| `L_Zsmooth` | Edge-aware depth total-variation loss | scalar | paper Eq. 8 |
| `L_op` | Background/opacity loss (labelled **BG** in the ablation) | scalar | paper Eq. 9 |
| `DS` / `SD` | Ablation label for the smooth-depth loss `L_Zsmooth` — the caption says `SD`, the rows say `DS` | — | paper Tab. III |
| `C` | Ablation label for the **pair** `{L_gw, L_sat}` ("the color losses") | — | paper Tab. III caption |
| `BS` | Ablation label for `L_bs` | — | paper Tab. III caption |
| `BG` | Ablation label for `L_op` | — | paper Tab. III caption |

## Cross-method collision warnings

These are the entries that must be flagged when this table is merged into
`../../comparison-glossary.md`:

| Symbol | In SeaSplat it is… | Collides with |
|---|---|---|
| **`β^D`, `β^B`** | **Nine global learned scalars** for the entire scene, applied as a 1×1 convolution over the rasterized depth map. Constant in space and view direction. Expressed in *per-frame min–max-normalised* depth units, so **not in inverse metres**. | SeaThru-NeRF's `β^b`/backscatter and attenuation terms, which are **per-sample quantities produced by an MLP conditioned on position and viewing direction**, evaluated at every sample along every ray. Same glyph, different mathematical object (constant vs. field), different units, different cardinality. **They are not comparable numerically.** |
| **`B^∞` / `B`** | A single global RGB triple, `σ`-squashed, warm-started from a learned background colour. | SeaThru-NeRF's medium colour, which is likewise view-dependent/MLP-produced. |
| **`Σ`** | Gaussian **covariance** matrix `R S Sᵀ Rᵀ`. | Summation operator in the loss equations of every paper in the set; and in `compact3d/`/`CompGS/` `Σ` also denotes the covariance being *quantised*. |
| **`μ`** | Gaussian **mean/position** in ℝ³. | In `compact3d/` and `OMG/`, `μ` may denote a **codebook centroid**. In statistics-flavoured sections of other papers, a distribution mean. |
| **`α`** | Both per-Gaussian alpha (Eq. 1) and the accumulated alpha map (Eq. 9). | Learning-rate / blending symbols elsewhere. |
| **`N`** | Both Gaussians-per-ray (Eq. 1) and pixels-per-image (Eq. 5). | Number of Gaussians in the scene, in most other papers. |
| **`D`** | Direct (attenuated true-colour) image. | Descriptor dimension in `RoMa`/`RoMaV2`; "Deep Blending" dataset abbreviation elsewhere. |
| **`J`** | Medium-free true colour. | Nothing in-set, but note `J'` is a *different* quantity (SeaThru residual). |
