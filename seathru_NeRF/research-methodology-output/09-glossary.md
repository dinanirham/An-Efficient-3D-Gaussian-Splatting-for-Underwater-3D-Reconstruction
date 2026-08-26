# §9 — Notation glossary — SeaThru-NeRF

Method key for the merged comparison glossary: **`seathru_nerf`**.
Paper: arXiv:2304.07743v1 / CVPR 2023. Repo: `deborahLevy130/seathru_NeRF` @ `3f4ebfe`.

| Symbol | Meaning | Type / shape | First defined |
|---|---|---|---|
| `C(r)` | True (observed) pixel colour along ray `r` | `(3,)` | paper Eq. 1 |
| `C*(r)` | Ground-truth supervised pixel colour (linear, white-balanced) | `(3,)` | paper §4.4 |
| `Ĉ(r)` | Rendered pixel colour = `Ĉ^obj + Ĉ^med` | `(3,)` | paper Eq. 3, Eq. 12 |
| `Ĉ^obj_i` | Object contribution of interval `i` | `(3,)` | paper Eq. 13, final form Eq. 20 |
| `Ĉ^med_i` | Medium contribution of interval `i` | `(3,)` | paper Eq. 14, final form Eq. 21 |
| `r(t)` | Ray, `o + d·t` | — | paper §3.1 |
| `t_n, t_f` | Near / far bounds; **`0` and `1`** here (NDC) | scalars | paper Eq. 1; repo `configs/llff_256_uw.gin` |
| `s_i` | Distance to the start of interval `I_i` | scalar | paper Eq. 5 |
| `δ_i` | Interval length `s_{i+1} − s_i`, times `‖d‖` | scalar | paper Eq. 4; repo `render.py:163-164` |
| `δ^bs_i` | **Repo-only.** `stop_gradient(s_{i+1} − s_i)·‖d‖` — the detached spacing used by *all* medium terms | scalar | repo `render.py:179`; not in paper |
| `σ` | Density (generic NeRF) | scalar/sample | paper Eq. 1 |
| `σ^obj` | **Object** density — function of position only | `(B,N)` | paper Eq. 8; repo `models.py:836` |
| `σ^med` | **Medium** density in the *basic* model (before the §4.3 split) | `(B,1,3)` | paper Eq. 8 |
| `σ^attn` | **Attenuation** coefficient of the *final* model — per colour channel, **constant per ray**, MLP-predicted from viewing direction | `(B,1,3)` | paper §4.3 / Eq. 20; repo `models.py:889` (`sigma_atten`) |
| `σ^bs` | **Backscatter** coefficient of the *final* model — per channel, per ray, MLP-predicted | `(B,1,3)` | paper §4.3 / Eq. 21; repo `models.py:878` (`sigma_bs`) |
| `c^obj` | Object colour. Paper §4.3 says it depends on viewing direction; **released config makes it view-independent** (`uw_rgb_dir = False`) | `(B,N,3)` | paper §4.3; repo `models.py:921`, gin |
| `c^med` | Medium colour — **constant per ray**, MLP-predicted from viewing direction. Plays the role of `B^∞` | `(B,1,3)` | paper §4.1, §4.3; repo `models.py:871` |
| `T(t)` | Accumulated transmittance (generic NeRF) | scalar | paper Eq. 2 |
| `T^obj_i` | Object-only transmittance `exp(−Σ_{j<i} σ^obj_j δ_j)` — **the argument of the Eq. 27 prior** | `(B,N)` | paper Eq. 22; repo `render.py:214-219` (`trans`) |
| `T^bs_i` | Backscatter transmittance `exp(−Σ_{j<i} σ^bs δ^bs_j)` | `(B,N,3)` | repo `render.py:187-192`; implicit in paper Eq. 21 |
| `A_i` | Attenuation transmittance `exp(−σ^attn s_i)` | `(B,N,3)` | paper Eq. 20; repo `render.py:205-210` (`trans_atten`) |
| `α_i` | Object alpha `1 − exp(−σ^obj_i δ_i)` | `(B,N)` | paper Eq. 4; repo `render.py:213` |
| `α^bs_i` | Medium alpha `1 − exp(−σ^bs δ^bs_i)` | `(B,N,3)` | repo `render.py:185`; implicit in paper Eq. 21 |
| `w^obj_i` | Object **weight** `T^obj_i·(1 − exp(−σ^obj_i δ_i))` | `(B,N)` | paper Eq. 23; repo `render.py:220` |
| `w` | The sequence `{w^obj_i}` — argument of `L_prop` and (in the disabled variant) `L_objnorm` | `(B,N)` | paper §4.4 |
| `s` | The sequence of sample positions `{s_i}` — argument of `L_prop` | `(B,N+1)` | paper §4.4 |
| `J` | The **clear / restored** scene — what would have been captured with no medium. In code, `stop_gradient(Σ w^obj_i c^obj_i)`: an output only | `(B,3)` | paper Eq. 7 (as the *target* quantity); repo `render.py:319` |
| `I` | The captured linear image, in the non-volumetric §3.2 model | `(3,)` | paper Eq. 7 |
| `z` | Scene **range** from the camera (not depth below surface) | scalar | paper Eq. 7 |
| `β^D` | Attenuation coefficient of the **Akkaynak–Treibitz** model — used in §3.2 and §5.1 only, **not** in the final SeaThru-NeRF model | `(3,)` | paper Eq. 7 |
| `β^B` | Backscatter coefficient of the **Akkaynak–Treibitz** model — §3.2 and §5.1 only | `(3,)` | paper Eq. 7 |
| `B^∞` (paper writes `B`) | Backscatter colour at infinity ("veiling light"). §4.2 shows `c^med` plays this role | `(3,)` | paper Eq. 7 |
| `v_D`, `v_B` | The dependency vectors of `β^D`, `β^B` (on range, reflectance, ambient spectrum, camera response, water IOPs) | — | paper Eq. 7 / §3.2 |
| `L_recon` | RawNeRF gradient-reweighted reconstruction loss | scalar | paper Eq. 25 |
| `L_prop` | Interlevel / proposal loss (mip-NeRF 360) | scalar | paper Eq. 24, §4.4 |
| `L_objnorm` | Binary-transmittance NLL prior | scalar | paper Eq. 27 |
| `P(x)` | Mixture of two Laplacians, modes at 0 and 1, scale 0.1. **Symmetric in the paper; `6×`-asymmetric in code** | — | paper Eq. 26; repo `train_utils.py:162`, `configs.py:173` |
| `λ` | Weight of `L_objnorm` = **1e-4** | scalar | paper Eq. 24; repo gin `uw_final_acc_trans_loss_mult` |
| `κ` | **Repo-only.** `uw_acc_loss_factor = 6`, the mixture asymmetry | scalar | repo `configs.py:173` |
| `ε` | RawNeRF denominator floor = `1e-3` | scalar | paper Eq. 25; repo `train_utils.py:99` |
| `sg(·)` | Stop-gradient | — | paper Eq. 25 |
| `N` | Number of sampling intervals along a ray (**32** at the final level here) | integer | paper §3.1; repo gin `num_nerf_samples` |
| `I_i` | The `i`-th interval `[s_i, s_{i+1}]` | — | paper §3.1 |
| `x`, `d` | 3D position and viewing direction | `(3,)`, `(3,)` | paper §3.1 |
| `θ, φ` | Spherical parameterisation of `d` | scalars | paper §3.1 |
| I / II / III | Ablation variant labels: **I** = 1 medium parameter (`uw_fog_model`), **II** = 3 (`uw_old_model`), **III** = basic Eqs. 13-14 (`gen_eq`) | — | paper §5.2 / Tab. 1; repo `configs.py:177,181`, `models.py:706` |
| "red square" | A **zoomed far-field crop**, not a full frame — the rows where the method's margin is largest | — | paper Tab. 2, Fig. 5 caption |

## Cross-method collision warnings

For merging into `../../comparison-glossary.md`:

| Symbol | In SeaThru-NeRF it is… | Collides with |
|---|---|---|
| **`σ`** | **Density** (`σ^obj`, `σ^med`, `σ^attn`, `σ^bs`) — the NeRF convention, units of inverse length | In 3DGS-family papers (`seasplat/`, `mini-splatting/`, `CompGS/`, `compact3d/`, `OMG/`, `EDGS/`), the *upper-case* `Σ` is a Gaussian **covariance matrix**, and lower-case `σ` often denotes a **scale** parameter. Three unrelated meanings across the set. |
| **`β^D`, `β^B`** | Appear **only in §3.2 and §5.1** as the Akkaynak–Treibitz model's coefficients and as *simulation ground truth*; the actual learned quantities are `σ^attn`, `σ^bs` | SeaSplat uses `β^D`, `β^B` as the names of its **learned global scalars**. So `β^D` means *"the physical constant we simulate with"* here and *"the thing we optimize"* in SeaSplat. **The correct correspondence is `SeaSplat β^D ↔ SeaThru-NeRF σ^attn` and `SeaSplat β^B ↔ SeaThru-NeRF σ^bs`** — and even then they are objects of different type: **3 scene constants vs. a 3-vector field over viewing directions**. Not numerically comparable. |
| **`B^∞` / `B` / `c^med`** | `c^med(v)` is a **per-ray, direction-dependent** RGB triple that *plays the role* of `B^∞` | SeaSplat's `B^∞` is a **single global** RGB triple. Same physical concept, different cardinality (one per ray vs one per scene). |
| **`T`** | **Transmittance** `exp(−∫σ)` ∈ [0,1] | In `seasplat/`, `T_sat` and `T_sim` are **thresholds**; in 3DGS papers `T` often denotes a **camera transform** (`T^cam_world`). Three meanings. |
| **`w`** | Object **weight** `T^obj(1−e^{−σδ})` — a quadrature weight ∈ [0,1] | Network **weights** in the compression papers (`compact3d/`, `CompGS/`, `OMG/`). |
| **`c`** | Colour (`c^obj`, `c^med`) | Colour in `seasplat/` too (consistent), but a **codebook code/centroid** in `compact3d/`. |
| **`J`** | The medium-free clear image | Same meaning in `seasplat/` ✅ — one of the few symbols that is genuinely shared. Note `J'` in SeaSplat is a *different* quantity (SeaThru residual term). |
| **`z`** | Range from camera | Same in `seasplat/` ✅; but SeaSplat's `Ẑ` is additionally **min–max normalised per frame**, so the numeric ranges differ. |
| **`N`** | Samples per ray | Number of **Gaussians** in every 3DGS-family paper; number of **pixels** in SeaSplat Eq. 5. |
| **`α`** | Object alpha per interval | Accumulated alpha map in `seasplat/` Eq. 9; per-Gaussian alpha in 3DGS Eq. 1. |
| **`λ`** | Weight of `L_objnorm` = 1e-4 | `λ_dssim` = 0.2 in every 3DGS paper; several other λ in `seasplat/`. Always disambiguate by subscript. |
| **`δ`** | Interval length along a ray | Not used elsewhere in-set. |
