# §4 — Full loss function

## 4.1 The objective is 3DGS's, unmodified

```
L = (1 − λ_dssim)·L₁(Î, I) + λ_dssim·(1 − SSIM(Î, I)),   λ_dssim = 0.2
```
`[repo: ms/train.py:120-122]`:
```python
Ll1  = l1_loss(image, gt_image)
loss = (1.0 - opt.lambda_dssim) * Ll1 + opt.lambda_dssim * (1.0 - ssim(image, gt_image))
```

**That is the entire objective.** No regulariser, no auxiliary term, no new loss of any
kind is added anywhere in `ms/train.py`, `ms_d/train.py`, or `ms_c/run.py`. The paper never
writes a loss equation at all — it presents only 3DGS's rendering equation
`[paper Eq. 1]` and then discusses density control.

This is a genuine and citable structural fact, and it separates Mini-Splatting sharply from
its neighbours in your comparison set:

| Method | Loss terms | New loss terms added |
|---|---|---|
| 3DGS | 2 | — |
| **Mini-Splatting** | **2** | **0** |
| `compact3d/` | 3 | 1 (opacity regulariser) |
| `seasplat/` | 7 | 5 |
| `seathru_NeRF/` | 3 | 1 (`L_objnorm`); base already had 2 |

### Why this matters methodologically

Because the loss is untouched, **every result in the paper is attributable to the density
control schedule alone** — no confound from a changed objective. That is a strong internal
validity property and the paper should be cited for it. The converse is that the usual
"which loss term matters" ablation is not available; what gets ablated instead is the
*schedule* (§4.3).

## 4.2 What replaces "loss terms" as the object of study

The paper's own analytical quantities are **selection criteria**, not losses. For symmetry
with the other folders, here is each one with its purpose and the failure mode it addresses:

### `S_i` — maximum-contribution area, and the blur-split criterion

- **Closed form** `[paper Eq. 2]`:
  `G^blur = { G_i : S_i > T_blur }`, `T_blur = θ_blur·H·W`, `θ_blur = 2×10⁻⁴`
  where `S_i = Σ_{x} 𝟙(i(x) = i_max(x))` — the pixel count over which `G_i` is the
  *argmax-weight* Gaussian.
- **Repo** `[repo: ms/train.py:151]`: `mask_blur |= (area_max > H*W/5000)` — and
  `1/5000 = 2×10⁻⁴` exactly ✅. `area_max` is `accum_max_count` from the forked rasterizer
  `[repo: gaussian_renderer/__init__.py:191]`.
- **Purpose.** 3DGS's ADC splits on *positional gradient magnitude*, which "may fail in
  areas with smooth color transitions" `[paper §4.1]` — a large Gaussian covering a smooth
  region has a small gradient and survives, producing visible blur.
- **Key empirical insight (Fig. 3):** blur correlates with the **rendered** index `i_max(x)`
  (where the Gaussian *dominates*), **not** the projected index `i(x)` (where it merely
  *appears*). That distinction is why `area_max` and `area_proj` are separate rasterizer
  outputs.
- **Failure mode addressed:** `under-reconstruction` — persistent Gaussian-blur artifacts
  in low-texture regions.

### `d^mid` — the ray/ellipsoid mid-point depth

- **Closed form** `[paper App. D / Eqs. 4-7]`: model `G_i` as the ellipsoid
  `x²/s_x² + y²/s_y² + z²/s_z² = 1`; substitute `r(t) = o + td`; solve the quadratic
  `at² + bt + c = 0`; take `t^mid = −b/2a`, with discriminant `Δ = b² − 4ac` used as an
  existence test.
- **Equivalence noted in the paper:** `t^mid = t^opt`, the argmax of the Gaussian density
  along the ray. The mid-point form is preferred *only* because it yields the discriminant
  `[paper App. D]`.
- **Aggregation:** `d^mid = d^mid_{i_max}` — the depth of the **single argmax Gaussian**,
  not an alpha-blended average `[paper §4.1]`.
- **Failure mode addressed:** the three artifacts of blended depth, enumerated with a
  cause each `[paper App. C]` — *depth collapse* (low accumulated opacity on dark
  background objects pulls blended depth toward the near plane), *object misalignment*
  (large/floater Gaussians corrupt the weighted mean), *blending boundary* (a weighted sum
  cannot produce a sharp depth edge).
- **Quantitatively decisive.** Table 4 shows blending depth is not merely worse but
  **catastrophic**: PSNR **17.67** vs **27.54**. See §4.3.

### `I_i` — importance, and importance-weighted sampling

- **Closed forms:**
  `I_i¹ = Σ_{j=1..K} w_ij` `[paper §3.2]` — total blending weight (indoor).
  `I_i² = Σ_{m=1..M} I_i^{(m)}·𝟙(i ∈ I_max^{(m)})`, `I_i^{(m)} = Σ_j w_ij^{(m)}/S_i^{(m)}`
  `[paper Eq. 12]` — intersection-gated, projected-area-normalised (outdoor).
  `P_i = I_i / Σ_k I_k` `[paper §4.2]`.
- **Repo** `[repo: ms/train.py:225-233]` — matches both forms, with the intersection gate
  applied as `imp_score[accum_area_max == 0] = 0`.
- **Purpose.** The paper's argument against deterministic top-`k` pruning is specifically
  about **spatial correlation**: "neighboring Gaussians often exhibit similar importance in
  a given area, causing them to be either removed or preserved simultaneously, thus risking
  the destruction of local geometry" `[paper §4.2]`. Stochastic sampling decorrelates the
  decision.
- **Measured with Chamfer distance**, not PSNR — Fig. 6 plots preserving-ratio against
  chamfer distance between pruned and unpruned Gaussian centers. This is the paper's most
  distinctive methodological move: **evaluating a rendering method with a point-cloud
  metric.**
- **Why `I²` for outdoor:** unbounded scenes contain sky/far-field Gaussians that
  accumulate large total weight without being locally important; dividing by projected area
  and gating on intersection suppresses them `[paper App. E]`.
- **The paper is candid about the status of this design:** "we posit that the design of
  importance metrics is case-dependent and hand-crafted. Thus, this part is presented as an
  **experimental trick** in the appendix." `[paper App. E]` Cite it that way — `--imp_metric`
  is a required CLI argument with no default `[repo: ms/train.py:409]`, i.e. the user must
  pick the scene type by hand.

## 4.3 Reading the ablations — **two different kinds in the same paper**

### Table 3 — densification: **CUMULATIVE-ADDITIVE**

`[paper Tab. 3]`, Mip-NeRF 360:

| Row | SSIM | PSNR | LPIPS | Num (M) |
|---|---|---|---|---|
| Baseline (3DGS*) | 0.815 | 27.47 | 0.216 | 3.35 |
| + Blur Split | 0.819 | 27.47 | 0.195 | 3.74 |
| + Depth Reinit | 0.832 | 27.54 | 0.175 | 4.32 |

**Precisely:** each row is the previous row **plus** one component. Row 3 is
"blur split *and* depth reinit", **not** "depth reinit alone".
The paper says so: "Starting from the 3DGS baseline, we **incrementally** introduce blur
splitting and depth reinitialization steps." `[paper §6.2]`

- ✅ "Adding blur split to 3DGS improves LPIPS by 0.021 at unchanged PSNR."
- ✅ "Adding depth reinit on top of blur split improves LPIPS by a further 0.020."
- ❌ You may **not** say "depth reinit contributes +0.07 dB" — that is a *conditional*
  increment given blur split, and no leave-one-out row exists.
- ⚠️ **PSNR is essentially flat across all three rows (27.47 → 27.47 → 27.54).** The gains
  are entirely in SSIM and LPIPS. The paper states the interpretation honestly: "we observe
  a high correlation between the number of Gaussians and the LPIPS metric" `[paper §6.2]`
  — i.e. *more Gaussians ⇒ better LPIPS*, which is close to tautological and is not
  evidence that the *distribution* improved. The distribution argument rests on Fig. 1/2/12
  visualisations and on Table 5, not on Table 3.
- ⚠️ Row 3's `Num` is **4.32 M**, but Mini-Splatting-D in Table 1 has **4.69 M** and in
  Table 4 "Mid" has **4.69 M**. Table 3's final row is therefore *not* Mini-Splatting-D.
  `[inferred: comparing paper Tab. 1, 3, 4]` The paper does not explain the gap.

### Table 4 — depth formulation: **MUTUALLY EXCLUSIVE VARIANTS**

`[paper Tab. 4]`:

| Variant | SSIM | PSNR | LPIPS | Num (M) |
|---|---|---|---|---|
| Blending | 0.513 | **17.67** | 0.475 | 4.01 |
| Center | 0.832 | 27.57 | 0.176 | 4.70 |
| Mid | 0.832 | 27.54 | 0.175 | 4.69 |

**Precisely:** three *alternative choices* for the same slot — neither additive nor
leave-one-out. The third category, as in `seathru_NeRF/`'s Table 1.

- ✅ **The decisive result of the paper.** Alpha-blended depth is not marginally worse, it
  is a **9.87 dB** collapse. Any subsequent 3DGS work that reinitializes from blended depth
  should cite this.
- ⚠️ **Center vs Mid is a wash**: 27.57 vs 27.54 PSNR, 0.176 vs 0.175 LPIPS — well inside
  noise. The paper concedes this ("depth reinitialization using Gaussian center yields
  results comparable to those obtained from the mid-point") and justifies choosing `Mid`
  on **non-metric** grounds: better dense point-cloud reconstruction (Fig. 5) and
  "potential for extension to normal estimation tasks" `[paper §6.2]`. That is a defensible
  choice, but **Table 4 does not support a rendering-quality claim for the mid-point
  formulation** — and the whole of Appendix D (Eqs. 4–11) exists to derive it.

### Figure 10 — simplification: **CURVES, not rows**

`[paper §6.2, Fig. 10]`. Four curves over Gaussian count, all starting from
Mini-Splatting-D:
`Add Pruning` (baseline) → `Add Intersection` → `Add Sampling`.

- The comparison is against **Mini-Splatting-D + direct pruning**, *not* against 3DGS +
  pruning. The paper is explicit that this is a deliberately strong baseline: "this
  baseline encompasses the combination of Mini-Splatting-D and direct pruning, **surpassing
  3DGS with pruning (i.e., VQ)** as depicted in Fig. 7" `[paper §6.2]`. Good practice —
  note it when citing.
- Headline claim: "approximately a **halved** reduction in the number of Gaussians while
  maintaining comparable rendering quality" `[paper §6.2]` — i.e. at equal quality,
  intersection+sampling needs ~½ the Gaussians that direct pruning needs.
- ⚠️ Read from a figure, not a table — no numeric values are published for these curves.
  `[unverified]` if you need exact figures.

### Table 1 — main results: watch the sign

| Dataset | 3DGS* | Mini-Splatting-D | Mini-Splatting |
|---|---|---|---|
| Mip-NeRF 360 | 0.815 / 27.47 / 0.216 / **3.35 M** | **0.831** / **27.51** / **0.176** / **4.69 M** | 0.822 / 27.34 / 0.217 / **0.49 M** |
| Tanks&Temples | 0.848 / 23.66 / 0.176 / 1.84 M | 0.853 / 23.23 / 0.140 / 4.28 M | 0.835 / 23.18 / 0.202 / 0.20 M |
| Deep Blending | 0.904 / 29.54 / 0.244 / 2.82 M | 0.906 / 29.88 / 0.211 / 4.63 M | **0.908** / **29.98** / 0.253 / 0.35 M |

- **Mini-Splatting-D *increases* the Gaussian count** (1.4×–2.3×). Only Mini-Splatting
  reduces it (≈**6.8×** on Mip-NeRF 360, **9.2×** on T&T, **8.1×** on DB).
- **PSNR drops on Tanks&Temples** for both variants (−0.43 and −0.48 dB). The paper
  attributes this to sky regions defeating the depth strategy `[paper §6.1, App. G]` —
  an honest, mechanistically-grounded concession.
- **LPIPS is where Mini-Splatting-D wins** (0.216→0.176, 0.176→0.140, 0.244→0.211), and
  the paper notes it beats Zip-NeRF on SSIM/LPIPS for Mip-NeRF 360 while losing on PSNR
  (27.51 vs 28.54).
- ⚠️ Mini-Splatting's **LPIPS is slightly worse than 3DGS** on 2 of 3 datasets
  (0.217 vs 0.216; 0.202 vs 0.176; 0.253 vs 0.244) — the "comparable to 3DGS with 7× fewer
  Gaussians" claim `[paper §6.1]` is carried by PSNR/SSIM, not LPIPS. Report all three.
