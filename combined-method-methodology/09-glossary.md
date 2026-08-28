# §9 — Merged glossary and notation, with cross-source collisions flagged

Merged from the four composition members' `09-glossary.md` files and reconciled against
`../comparison-glossary.md`, which merges all nine. This file is narrower and stricter: it
covers **only** the symbols that appear in the combined method, and it fixes **one** meaning
per glyph for the write-up.

Origin column: **SS** = SeaSplat · **ED** = EDGS · **MS** = Mini-Splatting ·
**VQ** = CompGS-VQ · **PI** = new here.

---

## 9.1 The write-up notation — one glyph, one meaning

Adopted from `../comparison-glossary.md` §6 and extended. **These are the symbols the thesis
chapter uses.** Where a source paper writes something different, the mapping is in §9.2.

| Concept | **This work writes** | Sources write | Why the change |
|---|---|---|---|
| Gaussian position | `μ` | `μ` (SS, VQ) · `p` (MS) · `g^x` (ED) | four glyphs for the most common concept in the set |
| Gaussian covariance | `Σ_3D` | `Σ` everywhere | bare `Σ` collides with summation and with RoMa's 2×2 pixel-space precision |
| Scale / rotation parameters | `s`, `q` | `s`,`r` (MS,VQ,OMG) · `S`,`R` (SS,ED) | `R` also means *bitrate* in the CompGS-Liu lineage |
| Opacity | `o` ∈ [0,1] | `o` (SS,VQ) · `α` (MS, 3DGS family) | `α` also means the Charbonnier shape parameter in the RoMa lineage, and `o` means *ray origin* in MS App. D |
| Rendered primitive count | `N_rend` | `N` | `N` means anchors, samples-per-ray, pixels, and patch counts elsewhere |
| Codebook size | `K_cb` | `K` (VQ) | `K` has **six** meanings across the nine folders |
| Camera intrinsics | `K_cam` | `K` (SS) | same |
| Attenuation coefficient | `β_att` | `β^D` (SS) | see §9.3 — the most dangerous collision in the underwater literature |
| Backscatter coefficient | `β_bs` | `β^B` (SS) | same |
| Every loss weight | `λ_<name>` | bare `λ` (six distinct values in SS alone, spanning 200×) | always subscript |
| PSNR | `PSNR_perchan` or `PSNR_pooled` | bare `PSNR` | **three** conventions are in play; see §9.4 |
| Primitive budget | `n_bud` | `sampling_factor·N` (MS) | **PI** — a count, not a ratio (CD-5) |
| Depth normalisation constants | `Ẑ_min`, `Ẑ_max` | *(implicit)* | **PI** — promoted to explicit logged state (CD-12) |

---

## 9.2 Symbol table

### 9.2.1 Geometry and primitives

| Symbol | Meaning | Shape | First defined | Origin |
|---|---|---|---|---|
| `μ` | Gaussian mean / 3D position | `(N_rend,3)` | `[SS repo: scene/gaussian_model.py]`; under M1 `[ED paper Eq.7]` | SS/ED |
| `Σ_3D` | Gaussian covariance, `Σ_3D = R_rot s sᵀ R_rotᵀ` | `(3,3)` per primitive | `[SS paper §III.A]` | SS |
| `s` | per-Gaussian scale, stored **pre-`exp`** | `(N_rend,3)` | `[SS repo: arguments/__init__.py:95]` | SS |
| `q` | rotation quaternion, stored **pre-normalisation** | `(N_rend,4)` | `[SS repo: arguments/__init__.py:96]` | SS |
| `o` | opacity ∈ [0,1], stored as a **logit** | `(N_rend,1)` | `[SS repo: arguments/__init__.py:94]` | SS |
| `f_dc` | DC spherical-harmonic coefficient (the colour) | `(N_rend,1,3)` | `[SS repo]` | SS |
| `f_rest` | higher-order SH — **empty**, `(N_rend,0,3)`, because `sh_degree = 0` | ∅ | `[SS repo: arguments/__init__.py:49]` | SS |
| `N_rend` | number of **rendered** Gaussians at the current iteration | scalar | — | PI |
| `n_bud` | the primitive budget targeted at `simp_iteration1` | scalar | — | PI |

### 9.2.2 Rendering and the medium

| Symbol | Meaning | Shape | First defined | Origin |
|---|---|---|---|---|
| `I` | the **captured in-medium image** (white-balanced) | `(3,H,W)` | `[SS paper §III.B]` | SS |
| `Ĵ` | the **medium-free** radiance — the rasterizer's output, reinterpreted | `(3,H,W)` | `[SS paper §IV.A]` | SS |
| `Î` | the **reconstructed in-medium** image, `clamp(D̂ + B̂, 0, 1)` — **what is scored** | `(3,H,W)` | `[SS repo: train.py:273]` | SS |
| `α` | accumulated opacity from the rasterizer (a *rendered map*, not per-Gaussian `o`) | `(1,H,W)` | `[SS repo: train.py:202]` | SS |
| `Z_raw` | raw rasterized depth, second pass with `override_color = z_cam` | `(1,H,W)` | `[SS repo: gaussian_renderer/__init__.py:116-137]` | SS |
| **`Ẑ`** | `Z_raw/α`, NaN-fixed, then **min–max renormalised to [0,1] per frame** | `(1,H,W)` | `[SS repo: train.py:222-237]` | SS |
| `Ẑ_min`, `Ẑ_max` | the per-frame normalisation constants — **logged** | scalars | — | PI |
| `β_att` | attenuation coefficient — **3 global learned scalars for the whole scene** | `(3,1,1,1)` conv kernel | `[SS paper Eq.3]`, `[SS repo: models.py:216]` | SS |
| `β_bs` | backscatter coefficient — likewise 3 global scalars | `(3,1,1,1)` | `[SS repo: models.py:54]` | SS |
| `B^∞` | water colour at infinity, stored as a **logit**, used as `σ(B^∞)` | `(3,1,1)` | `[SS repo: models.py:61,77]` | SS |
| `bg` | learned background colour — **absent from the paper**; transferred into `B^∞` at `seathru_from_iter` | `(3,)` | `[SS repo: train.py:126-131, 209-212]` | SS |
| `Â` | attenuation map `exp(−clamp(β_att ⊛ Ẑ, ≥0))` | `(1,3,H,W)` | `[SS repo: models.py:226-232]` | SS |
| `B̂` | backscatter map `σ(B^∞) ⊙ (1 − exp(−clamp(β_bs ⊛ Ẑ, ≥0)))` | `(1,3,H,W)` | `[SS repo: models.py:70-85]` | SS |
| `D̂` | the **modelled** direct image, `Ĵ ⊙ Â` | `(1,3,H,W)` | `[SS paper §III.B]` | SS |
| `D̃` | the **empirical** backscatter-removed image, `I − B̂'` — the argument of `L_bs` | `(1,3,H,W)` | `[SS paper Eq.4]` | SS |
| `Â'`, `B̂'` | depth-**detached** duplicates of `Â`, `B̂` | as above | `[SS repo: train.py:255,270]` | SS |

> ⚠️ **`D̂` vs `D̃` is a within-paper overload, not a cross-method one.** SeaSplat's paper
> writes `D̂` for *both* `Ĵ ⊙ Â` (§III.B, the model) and `I − B̂` (Eq. 4, the observation).
> They are equal only at the optimum. This work follows `../seasplat/03-variables.md` in
> writing the second one `D̃`. `[../seasplat/03-variables.md §3.2 naming trap]`

### 9.2.3 Initialization (M1)

| Symbol | Meaning | First defined | Origin |
|---|---|---|---|
| `W_ij` | dense forward warp field from reference `I_i` to neighbour `I_j`, from RoMa | `[ED paper Eq.3]` | ED |
| `c_ij` | RoMa correspondence confidence ("certainty") | `[ED paper Eq.3]` | ED |
| `τ_corr` | confidence threshold — **has no config key**; inherits RoMa's `sample_thresh` = 0.05 | `[ED repo: corr_init.py:541]` | ED |
| `τ_proj` | reprojection-error tolerance = `proj_err_tolerance` = 0.01 | `[ED repo: configs/train.yaml]` | ED |
| `ε_ij^k` | `max(ε_i^k, ε_j^k)`, the per-match reprojection error | `[ED paper Eq.8, §3.4]` | ED |
| `p^corr`, `p^proj` | the two filters. ⚠️ `p^proj` is an **opacity mask** in code, not a sampling distribution | `[ED paper Eqs.9-10]` vs `[ED repo: corr_init.py:660-666]` | ED |
| `K_ref` | number of reference views = `min(num_refs, V)` | — | **PI** (CD-2) |
| `J` | neighbours per reference = `nns_per_ref` = 3 | `[ED repo: configs/train.yaml]` | ED |
| `V` | number of training views | — | PI |

### 9.2.4 Simplification (M2)

| Symbol | Meaning | Shape | First defined | Origin |
|---|---|---|---|---|
| `w` | per-pixel blending weight `T·o·G^{2D}(x)` | per pixel | `[MS paper Eq.1]` | MS |
| `I_imp` | **importance score** — `Σ_v accum_weights` (indoor `I¹`) or `Σ_v accum_weights/area_proj · 1[i ∈ I_max]` (outdoor `I²`) | `(N_rend,)` | `[MS paper §3.2, Eq.12]` | MS |
| `A_max` | `area_max` — pixel count where primitive `i` is the **argmax** contributor | `(N_rend,)` | `[MS paper Eq.2]`, `[MS repo: gaussian_renderer/__init__.py:191]` | MS |
| `P` | sampling probability `I_imp/ΣI_imp`, with `I_imp[A_max == 0] ← 0` | `(N_rend,)` | `[MS paper §4.2, Eq.3]` | MS |
| `S_i` | maximum-contribution **area** (a pixel count) — the blur-split criterion | integer | `[MS paper Eq.2]` | MS |
| `θ_blur` | blur-split threshold = `2×10⁻⁴` (as `H·W/5000`) | scalar | `[MS paper Eq.2]` | MS |
| `d^mid` / `out_pts` | ray/ellipsoid **mid-point** depth of the argmax Gaussian, `t^mid = −b/2a` | `(3,H,W)` | `[MS paper §4.1, App.D Eq.7]` | MS |

### 9.2.5 Quantization (M3)

| Symbol | Meaning | Shape | First defined | Origin |
|---|---|---|---|---|
| `C_g` | codebook (centroids) for group `g ∈ {dc, scale, rot}` | `(K_cb, d_g)` | `[VQ paper §3]` | VQ |
| `K_cb` | codebook size | scalar | `[VQ paper §4]` | VQ |
| `d_g` | parameter-vector dimensionality per group: `dc`=3, `scale`=3, `rot`=4 | scalar | `[VQ paper §3]` | VQ |
| `idx_g` / `cls_ids` | per-Gaussian assignment index | `(N_rend,)` | `[VQ repo: kmeans_quantize.py:118]` | VQ |
| `ẑ_g` | the quantized attribute, `C_g[idx_g]` — what the forward pass renders | as `z_g` | `[VQ repo: kmeans_quantize.py:194,204]` | VQ |
| `t` | K-means **assignment interval** = `kmeans_freq` = 100 | scalar | `[VQ paper §3]` | VQ |
| `λ_reg` | ℓ1 opacity weight = 1e-7 — **DISABLED in this work** | scalar | `[VQ paper §4]` | VQ / PI |

### 9.2.6 Losses

| Symbol | λ | Purpose | Origin |
|---|---|---|---|
| `L_GS` | implicit (0.8 / 0.2) | photometric, on `Î` not `Ĵ` | SS |
| `L_Z-recon` | `λ_dwr = 1.0` | depth-weighted residual; the weight `Ẑ⊘` is detached | SS |
| `L_bs` | `λ_dcp = 1.0` | asymmetric dark-channel; `k = 1000`; kills degeneracy D-1 | SS |
| `L_gw` | `λ_gw = 0.1` | grey-world; fixes the colour gauge (D-3) | SS |
| `L_sat` | `λ_sat = 2.0` | oversaturation cap, `T_sat = 0.7` | SS |
| `L_op` | `λ_bg = 0.01` | opacity → 0 on water-coloured pixels (D-4). **+2.42 dB alone** | SS |
| `L_Zsmooth` | `λ_dsm = 2.0` | edge-aware depth TV; signed image gradient (inherited deviation) | SS |

---

## 9.3 Cross-source collisions that matter here

`../comparison-glossary.md` §2 ranks the ten worst collisions across all nine folders. Six of
them involve at least two of this work's four sources, and are therefore live:

| Rank | Glyph | The collision, restricted to this work's sources | Resolution here |
|---|---|---|---|
| **1** | **`β^D`, `β^B`** | SS's are **9 global learned scalars in normalised-depth units**. SeaThru-NeRF's identically-written symbols are the Akkaynak–Treibitz *constants*, used only to state the model and to synthesise benchmarks; its **actually-learned** counterparts are `σ^attn`, `σ^bs`, **per ray**. The correct correspondence is `β^D ↔ σ^attn`, not `β^D ↔ β^D` | write `β_att`, `β_bs`; state "global, per-scene, in normalised-depth units" every time; **never tabulate against SeaThru-NeRF's coefficients as the same measured quantity** |
| **2** | **`N`** | Gaussians (SS, ED, MS, VQ) · pixels-per-image and Gaussians-per-ray **within SeaSplat's own equations** (Eq. 1 vs Eq. 5) | `N_rend` for primitives; spell out the others |
| **3** | **`Σ` / `σ`** | 3D covariance (all four) · summation · `σ(·)` the sigmoid applied to `B^∞` and `o` | `Σ_3D` for covariance; `σ(·)` only for the sigmoid |
| **4** | **`o` vs `α`** | SS and VQ write `o` for opacity; MS writes `α`; MS App. D writes `o` for **ray origin**. And in this work `α` is *also* the rendered accumulated-opacity **map** | `o` = per-Gaussian opacity; `α` = the rendered `(1,H,W)` map only |
| **5** | **`K`** | VQ's **codebook size** · SS's **camera intrinsics** · MS's **rays intersecting a Gaussian** | `K_cb`, `K_cam`; spell out the third |
| **6** | **`S`** | SS/ED: the **scale matrix** factoring `Σ_3D` · MS: **maximum-contribution area**, a *pixel count* | `s` for scale; `S_i` kept for MS's area, always with the word "area" |
| — | **`I`** | the **captured image** (SS) · the **importance score** (MS) | `I` = image; `I_imp` = importance |
| — | **`M`** | ED's **matching network** *and* its `matches_per_ref` · MS's **number of training views** | `M_match`, `matches_per_ref`, `V` |
| — | **`t`** | VQ's K-means **assignment interval** · MS's ray parameter `t^mid` | `t` = interval only; `d^mid` for the depth |
| — | **`D`** | SS's **direct image** `D̂`/`D̃` · VQ's **parameter dimensionality** | `D̂`, `D̃`; `d_g` for dimensionality |
| — | **`λ`** | six distinct SeaSplat loss weights spanning **200×**, plus VQ's `λ_reg` | always subscripted |

> **The `β` collision is the one to guard hardest.** It is ranked #2 across all nine folders
> and #1 within this work's domain, because the two papers a reader will most naturally
> compare — SeaSplat and SeaThru-NeRF — use the same glyphs for objects of different
> **type** (constant vs field), **cardinality** (one per scene vs one per ray), and **units**
> (normalised per-frame depth vs NDC). Neither is in inverse metres.
> `[../comparison-glossary.md §0]`

---

## 9.4 The PSNR convention — a glossary entry because it is a *definition*, not a detail

Three conventions are in play across the four sources, and the differences are not small in
this domain.

> ⚠️ **CORRECTION — established by measurement, 2026-08-28.** The claim that SeaSplat
> *reports* per-channel PSNR is half right, and the wrong half is the one that matters.
> `utils/image_utils.py:psnr` reduces with `.view(img.shape[0], -1)`, so **the convention is
> decided by the shape of the tensor handed to it** — and the repository hands it both:
>
> - the **in-training / TensorBoard** report passes `(3,H,W)` → `shape[0]=3` → **per-channel**;
> - the **disk-based evaluation that writes `eval_metrics.json`** passes `(1,3,H,W)`, because
>   `metrics.py:readImages` does `.unsqueeze(0)` → `shape[0]=1` → **pooled MSE**.
>
> So the figure a paper would quote is **pooled** — the *stricter* convention, not the
> inflated one. Measured on a synthetic pair with underwater-like channel divergence, the same
> function returns **27.881 dB from `(3,H,W)` and 16.068 dB from `(1,3,H,W)`**: an 11.8 dB
> spread from input shape alone `[implementation/tools/verify_metrics.py T4, executed]`.
>
> **This weakens an argument made in `10-reproducibility.md` §10.3c** — that SeaSplat's
> Table I comparison against SeaThru-NeRF is biased in SeaSplat's favour by its PSNR
> convention. If both used pooled MSE, that bias does not exist. Which path produced the
> published numbers is not recorded anywhere, so the argument should not be made without
> establishing it first. This is the same accidental call-site flip already documented for
> EDGS and OMG, now confirmed in the baseline as well.

| Convention | Formula | Used by | Effect |
|---|---|---|---|
| **Per-channel mean** | `mse_c` per channel → PSNR per channel → mean of three PSNRs | **SeaSplat's in-training path only** `[repo: utils/image_utils.py:17-19, called with (3,H,W)]` | **Higher** by Jensen's inequality; the gap grows as channel errors diverge |
| **Pooled MSE** | one `.mean()` over all pixels **and** channels | SeaThru-NeRF; and, via a call-site subtlety, EDGS and OMG | the standard, stricter definition |
| **Inherited / ambiguous** | whichever harness produced the number | Mini-Splatting, CompGS-VQ (3DGS's `metrics.py` via the file overlay) | unknown without checking |

**Underwater is the regime of maximum channel divergence** — red is attenuated to
near-nothing, blue is not — so the per-channel convention inflates PSNR more here than
anywhere else `[../seathru_NeRF/10-reproducibility.md §10.3a]`.

⭐ **CompGS-VQ is the only paper in the nine that names this problem and introduces a
corrected metric**, PSNR-AM, averaging the error *before* the log: "this metric may be
dominated by very accurate reconstructions … since it is based on the geometric average of
the errors due to the log operation" `[../compact3d/04-loss.md §4.5, paper §4]`. **Cite that
passage when justifying whichever convention this work standardises on** — it is the rare
case where one of the composed methods supplies the methodological warrant for a decision
about another.

`[PI]` **This work reports `PSNR_perchan`** (SeaSplat's convention, so A0 remains comparable
to SeaSplat's published Table I) **and additionally reports `PSNR_pooled`**, so that
comparisons against SeaThru-NeRF, UW-3DGS and TUGS are possible without re-deriving anyone's
numbers. Reporting both costs nothing and removes the entire class of ambiguity.
