# §9 — Notation glossary

Merged across SeaSplat and the three source mechanisms, plus the symbols this thesis introduces
for the integration itself. Method keys: `seasplat` · `edgs` · `mini-splatting` ·
`compgs-vq` (Navaneet et al., = `compact3d/`) · `roma`.

> ⚠️ `compgs-vq` is **not** `compgs-liu` (Liu et al., ACM MM 2024, Scaffold-GS + entropy model).
> Two unrelated methods share the name *CompGS*. This thesis uses only `compgs-vq`.

---

## 9.1 Symbols used in this thesis

| Symbol | Meaning here | Type | Origin |
|---|---|---|---|
| `I` | **Observed underwater image** (the ground truth) | `(3,H,W)` | `seasplat` |
| `Î` | Re-rendered underwater image | `(3,H,W)` | `seasplat` |
| `Ĵ` | Restored / medium-free image | `(3,H,W)` | `seasplat` |
| `Ẑ` | Rendered depth (range from camera) | `(1,H,W)` | `seasplat` |
| **`β^D`** | **Attenuation** coefficient — **3 global scalars per scene** | `(3,)` | `seasplat` |
| **`β^B`** | **Backscatter** coefficient — **3 global scalars per scene** | `(3,)` | `seasplat` |
| `B^∞` | Veiling light at infinite range — 3 global scalars | `(3,)` | `seasplat` |
| `μ_i, s_i, q_i, α_i, c_i` | Primitive centre, scale (pre-`exp`), rotation (pre-normalize), opacity (logit), DC colour | per-primitive | `seasplat` |
| `N` | **Number of Gaussian primitives** | integer | `seasplat` |
| `T_seathru` | `seathru_from_iter` = 10 000 | integer | `seasplat` |
| `λ_bs, λ_gw, λ_sat, λ_op, λ_Zsmooth, λ_Zrec` | Loss weights: 1.0, 0.1, 2.0, 0.01, 2.0, 1.0 | scalars | `seasplat` |
| **`Φ_i`** | ⭐ **Importance score** `= α_i · ρ(s_i)` — this thesis's pruning criterion | scalar | **new** (§9.3) |
| **`ρ`** | ⭐ Scale reduction: `max` (`outdoor`) or `mean` (`indoor`) over the 3 axes | — | **new** |
| **`N_init`** | ⭐ Seed primitive count from `roma_init.py`; under A1 also the *final* count | integer | **new** |
| **`N_max`** | ⭐ `max_gaussians` = 800 000 — the A2 budget | integer | **new** |
| `k` | **Codebook size** = 256 | integer | `compgs-vq` |
| `g` | Sub-vector group size = 4 | integer | `compgs-vq` |
| `τ_cert` | RoMa certainty threshold (0.05 / 0.02) | scalar | `edgs`/`roma` |
| `v` | Voxel dedup grid (0.005 / 0.002) | scalar | `edgs` |
| `k_nn` | Neighbour views per reference = 3 | integer | `edgs` |

---

## 9.2 ⚠️ Cross-method collisions

### The template case: `β^D` is not what it looks like

The check that motivates this whole section. `seasplat`'s `β^D` and `β^B` **do not pair with
`seathru_nerf`'s identically-named symbols.** In SeaThru-NeRF, `β^D`/`β^B` appear only in §3.2
and as simulation constants; the quantities that actually play SeaSplat's role are the per-ray
MLP-predicted `σ^attn` and `σ^bs`. The correct correspondence is:

| | `seasplat` | `seathru_nerf` |
|---|---|---|
| Attenuation | `β^D` | **`σ^attn`** (not `β^D`) |
| Backscatter | `β^B` | **`σ^bs`** (not `β^B`) |
| Cardinality | **9 global scalars per scene** | a **per-ray field** predicted by an MLP |
| Units | not inverse metres in a directly comparable sense | not inverse metres either |

**Even correctly paired, they are different objects** — 9 constants versus a field. This matters
structurally, not just notationally: SeaSplat's medium model is immune to per-primitive edits
*because* it is 9 globals (constraint W-3, §5.1). **None of this thesis's isolation results
would transfer to a per-ray medium model.** Any table placing this thesis beside SeaThru-NeRF
must carry this note.

### Collisions introduced by the three borrowed mechanisms

| Symbol | In this thesis | Collides with | Resolution |
|---|---|---|---|
| **`I`** | 🔴 **Observed underwater image** — the GT of the image formation model | 🔴 `mini-splatting`'s **importance** `I¹`/`I²` (accumulated blending weight). A2 is drawn from that method, so the collision is live. | **Use `Φ` for importance.** Never write `I` for a per-primitive score in this thesis. |
| **`K`** | Camera intrinsics | `compgs-vq` **codebook size**; `mini-splatting` **rays intersecting a Gaussian**; `roma` **anchors** (=64²) | **Use lowercase `k` for the codebook**, reserve uppercase `K` for intrinsics. Applied throughout §3. |
| **`N`** | Number of primitives | `seasplat` also uses `N` for **pixels** in Eq. 5; `seathru_nerf` for **samples per ray**; `compgs-liu` for **anchors** | Subscript when ambiguous (`N_init`, `N_max`). ⚠️ "Number of primitives" is **not comparable across papers** — `compgs-liu` reports anchors, not primitives. |
| **`α`** | Opacity (stored as logit) | `compgs-vq` **overloads it in one paper** — the stored opacity *and* the per-primitive blending weight; `roma` uses `α` for a Charbonnier shape parameter | State "opacity" explicitly on first use; never use `α` for a blending weight here. |
| **`Σ`** | Covariance `R S Sᵀ Rᵀ` | Summation; `compgs-liu` 6-D scaling vector; `romav2` 2×2 error precision | Standard 3DGS usage — safe, but note it if a matcher symbol appears nearby. |
| **`S`, `R`** | Scale / rotation matrices | `mini-splatting` `S` = **max-contribution area** (Eq. 2); `compgs-liu` `R` = **bitrate** | ⚠️ A2 borrows from `mini-splatting`; use `s_i` (lowercase, vector) for per-primitive scale to avoid its `S`. |
| **`λ`** | Seven SeaSplat loss weights | `compgs-vq` `λ_reg` = 1e-7 opacity weight; `λ_dssim` = 0.2 everywhere; `compgs-liu` RD multiplier | Always subscript. This thesis adds **no new `λ`** (§4). |
| **`t`** | Iteration index | `compgs-vq` **assignment-update interval**; `seathru_nerf` **ray parameter**; COLMAP **translation vector** | Use `it` for iterations (as in §7), `t_i` only for COLMAP translation. |
| **`d`** | — (unused here) | `compgs-vq` group dimensionality; `mini-splatting` ray direction and depth; matchers' descriptor dim | Avoid entirely; this thesis uses `g` for group size. |
| **`G`** | Gaussian function | `edgs`/`mini-splatting` the **set** of Gaussians; `roma` the **global matcher** (Eq. 2) | Avoid; use `N` for the count and name the matcher `RoMa`. |

### 🔴 The parameter-name collision that is already in the code

| Name | In this thesis | In `mini-splatting` |
|---|---|---|
| **`imp_metric`** | selects `ρ = max` (`'outdoor'`) vs `ρ = mean` (`'indoor'`) over the **three scale axes** | selects `I¹` vs `I²` — different **powers of the accumulated blending weight** |

Same parameter name, same two string values, **entirely unrelated semantics**. A reader who
knows Mini-Splatting will misread the configuration. Renaming to `scale_reduction` is
recommended (§6, delta D-23); at minimum the thesis must define it explicitly on first use.

---

## 9.3 Symbols this thesis introduces

Only four, and each exists to avoid a collision or to name something the source methods do not
have.

| Symbol | Definition | Why a new symbol is needed |
|---|---|---|
| **`Φ_i = α_i · ρ(s_i)`** | Per-primitive importance driving A2's budget prune | Mini-Splatting's `I` collides with SeaSplat's observed image `I`. `Φ` also signals that this is **not** Mini-Splatting's quantity — it has no visibility or occlusion term (§6, D-21). |
| **`ρ`** | Scale reduction over the 3 axes | Distinguishes the `outdoor`/`indoor` switch from Mini-Splatting's `I¹`/`I²` |
| **`N_init`** | Seed count from the offline matcher; **also the final count under A1** | Under A1 the population is frozen, so initial and final count coincide — a property SeaSplat and EDGS have no symbol for, and the quantity that determines whether A2 ever fires (§8.4) |
| **`N_max`** | The A2 budget (800 000) | Mini-Splatting derives a count from its sampling procedure and has **no fixed budget**, so no source symbol exists |

**`Φ_i` is the notation for the thesis's most defensible contribution** (§1.3a): because `α_i`
is read *after* `L_op` has acted, `Φ_i` is medium-aware in a way no terrestrial importance
metric can be. The symbol should carry that meaning explicitly wherever it appears.

---

## 9.4 Non-notational hazards to carry into any comparison table

Four things that are not symbol collisions but will silently corrupt a cross-method table:

1. **PSNR convention.** `metrics.py` computes **pooled-MSE** PSNR (tensors are `(1,3,H,W)`, so
   channels and pixels flatten together), matching the draft's Eq. 3.1. But the *same* `psnr()`
   function called from `train.py` on a `(3,H,W)` tensor yields **per-channel-mean** PSNR. By
   Jensen's inequality per-channel-mean ≥ pooled-MSE, and **the gap is systematically wider
   underwater** because wavelength-dependent attenuation makes the channel MSEs diverge by
   design. Never quote a training-log PSNR beside a reported one. `compgs-vq` §4 discusses this
   directly and introduces PSNR-AM — cite that passage when justifying the convention.
2. **"Number of primitives" is not comparable across papers** (see `N` above).
3. **Model size accounting differs.** This thesis defines it as the compressed archive
   `[recommended: draft §3.5.4]`; `compgs-vq` reports bit-packed indices + codebooks; `omg` and
   `compgs-liu` must additionally account for neural decoders. The 4.27× figure (§8.2) is
   correct as defined but **includes zlib**, so it is not the same quantity as CompGS's `Mem`.
4. **Ablation structures differ.** This study is a full 2³ matrix reported additively (§10.4);
   `compgs-vq`'s Table 1 lists *variants*, not an ablation ladder; `edgs` uses a 2×2 factorial;
   `mini-splatting` uses a cumulative ladder. Rows from different structures are not
   interchangeable.
