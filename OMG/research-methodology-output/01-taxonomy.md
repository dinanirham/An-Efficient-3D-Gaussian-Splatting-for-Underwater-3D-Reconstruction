# §1 — Taxonomic placement and modification

## Base method extended

**Mini-Splatting**, Fang & Wang, **ECCV 2024** (ref **[14]**) — the `../mini-splatting/`
folder in this comparison set. Not vanilla 3DGS, despite 3DGS being the headline comparison.

> "Our model is implemented upon **Mini-Splatting [14]**, one of the methods achieving high
> performance with a small number of Gaussians." `[paper §4.1]`

The inheritance is verbatim. `[repo: arguments/__init__.py:89-95]` carries Mini-Splatting's
entire parameter block unchanged:

```python
self.simp_iteration1 = 15_000      # Mini-Splatting simplification step 1
self.simp_iteration2 = 20_000      # Mini-Splatting simplification step 2
self.num_depth       = 3_500_000   # depth-reinit point budget
self.num_max         = 4_500_000   # densification cap
self.depth_reinit_interval = 5_000
self.sampling_factor = 0.5
```

and `intersection_preserving()` `[repo: scene/gaussian_model.py:627-650]` is Mini-Splatting's
importance routine line-for-line, including the `imp_metric ∈ {indoor, outdoor}` branch and
the `imp_score[accum_area_max == 0] = 0` realisation of `G^int`.

**So everything in `../mini-splatting/research-methodology-output/` applies here too** —
including its undocumented mechanisms: the removed opacity reset, the `(1 − α_accum)`-weighted
depth-reinit sampling, the LR-schedule rewind at 15 000. OMG inherits all of them silently.

The paper also credits Mini-Splatting for a qualitative result: OMG-XS beats 3DGS on the
*bicycle* scene, "This superiority can be attributed to the **blur split technique of our
baseline model, Mini-Splatting**" `[paper §4.2]`.

Secondary lineages:

| Lineage | What is inherited | Evidence |
|---|---|---|
| **Product Quantization**, Jégou et al. (ref [26]) | The idea behind SVQ — partition the vector, quantize each part independently | `[paper §3.2]` "motivated by Product Quantization [26]" |
| **Compact-3DGS** (ref [32]) | R-VQ as the comparison point; the hybrid neural-field-for-appearance idea | `[paper §2.2, §3.1]` |
| **LocoGS** (ref [53]) | The direct SotA competitor: "represents all Gaussian attributes except for view-independent color" with a neural field | `[paper §2.2, Tab. 1]` |
| **tiny-cuda-nn** | The actual MLP implementation — `FullyFusedMLP` + `Frequency` encoding | `[repo: scene/gaussian_model.py:672-720]` |
| **G-PCC / MPEG TMC13** (ref [51]) | Lossless position coding after 16-bit quantization | `[paper §4.1]` `[repo: utils/gpcc_utils.py]` |
| **HAC++** | The G-PCC wrapper is borrowed: "this script is sourced from HAC++" | `[repo: README.md]` |
| Huffman (ref [25]), LZMA (ref [1]) | Entropy coding of SVQ indices; final container compression | `[paper §4.1]` |

## The modification, in one sentence

OMG replaces Mini-Splatting's second-stage CDF prune with a **local-distinctiveness-weighted**
importance score, re-parameterises appearance as a **tiny per-Gaussian feature plus a
position-decoded space feature from a small frequency-encoded MLP** while keeping geometry
per-Gaussian, and compresses everything with **sub-vector quantization** — attacking Gaussian
*count* and Gaussian *storage* in a single pipeline.

## Design family, in one sentence

OMG is an **explicit radiance field** (rasterized 3D Gaussians), **per-scene optimized**, with
**no medium/degradation model**, whose axis of contribution is **joint primitive-count and
rate reduction** — making it the only method in your comparison set that attacks *both* axes
simultaneously, and the reason it is positioned against `../mini-splatting/` (count) and
`../compact3d/` / `../CompGS/` (rate) at the same time.

### The axis, and the gap OMG identifies

The paper's framing is a genuine observation about why the two literatures had not composed:

> "the aforementioned compression methods typically rely on a large number of Gaussians (over
> one million). This is due to two major challenges when the number of Gaussians is
> drastically reduced: 1) **each Gaussian needs to represent a larger portion of the scene,
> making it more susceptible to compression loss**, and 2) **the increased spacing between
> Gaussians disrupts spatial locality**, leading to higher attribute irregularity and posing
> challenges for entropy minimization." `[paper §1]`

Both design choices follow directly from that diagnosis:

| Challenge | OMG's response |
|---|---|
| (1) sparse Gaussians are compression-sensitive | **keep geometry per-Gaussian** — "each Gaussian covers a larger spatial region, requiring a more specific scale and rotation to accurately capture structural details. Therefore, we **retain the per-Gaussian parameterization** for scale and rotation as in 3DGS" `[paper §3.1]` |
| (2) sparsity breaks spatial locality | **hybrid** appearance — a small per-Gaussian feature (irregularity) **plus** a position-decoded space feature (continuity), rather than committing to either |

### Where OMG sits among the compression folders

| | **OMG** | `../mini-splatting/` | `../compact3d/` | `../CompGS/` (Liu) |
|---|---|---|---|---|
| Reduces **count** | ✅ (LD scoring) | ✅ (the whole method) | ❌ (opacity reg. only) | ✅ (anchor pruning) |
| Reduces **bits/primitive** | ✅ (SVQ + neural field) | ⚠️ `ms_c` only, post-hoc | ✅ (K-means VQ) | ✅ (learned entropy model) |
| Rate term in the loss? | ❌ | ❌ | ❌ | ✅ |
| Quantization | **Sub-Vector (Product)** | RAHT + zip | **K-means VQ / R-VQ** | scalar + entropy model |
| Neural decode per frame? | ⚠️ **only for appearance**, and MLPs are tiny | ❌ | ❌ | ✅ (per-view MLP) |
| Needs an external codec? | ✅ **G-PCC** | ❌ | ❌ | ✅ G-PCC |
| Rendering FPS | **350 (612 on 4090)** | 601 (as measured by OMG) | 236 | — |
| Mip-NeRF 360 size | **4.06 MB** | 119.5 MB | 22.93 MB† | — |

† `[paper Tab. 1]` lists "CompGS [44]" at 22.93 MB. Given ref [44] is also cited for
"opacity regularization" and "vector quantization" `[paper §2.2]`, this is
**Navaneet et al. = `../compact3d/`**, not Liu et al. = `../CompGS/`. `[inferred]` —
the same acronym collision flagged in `../CompGS/research-methodology-output/00-index.md`.

### Four consequences

1. **OMG is the only method here that keeps rendering *fast* while compressing hard.** The
   anchor-based competitors pay a per-view MLP cost: "these approaches require **per-view
   processing, involving multiple MLP forward passes**, which results in significant rendering
   latency" `[paper §2.2]` — visible in Table 1, where HAC reaches 16.95 MB at only **110 FPS**
   while OMG-XS reaches 4.06 MB at **350 FPS**.
2. **Geometry is deliberately *not* compressed by a neural field.** This is the paper's
   sharpest departure from LocoGS, which neural-fields everything except DC colour. The
   justification (sparse Gaussians need specific scale/rotation) is stated but **never
   ablated** — see [`04-loss.md`](04-loss.md) §4.4.
3. **One knob spans the whole variant family.** "The only factor controlling the storage is
   the CDF-based threshold value τ of Gaussian importance, which is set to 0.96, 0.98, 0.99,
   0.999, and 0.9999" for XS/S/M/L/XL `[paper §4.1]` = `[repo: arguments/__init__.py:98]`.
   A genuinely clean rate-distortion knob, comparable to `../CompGS/`'s λ sweep.
4. **The loss is completely unmodified 3DGS.** Like `../mini-splatting/` and `../EDGS/`, every
   reported gain is attributable to the pipeline rather than to a changed objective. See
   [`04-loss.md`](04-loss.md).

## Position relative to the sibling folders

| Folder | Relationship |
|---|---|
| **`../mini-splatting/`** | **the base method** (ref [14]), inherited verbatim; also a headline baseline in Tables 1–3 |
| **`../compact3d/`** | listed as "CompGS [44]" in Tables 1–2 `[inferred]`; also the R-VQ comparison in Table 5 (via Compact-3DGS [32]) |
| `../CompGS/` (Liu) | **not** compared against, despite the name collision |
| `../gaussian-splatting/` | the ultimate baseline (ref [28]) |
| `../EDGS/` | orthogonal (initialization) and not compared; both build on the 3DGS substrate |
| `../colmap/` | upstream SfM |
| `../seasplat/`, `../seathru_NeRF/`, `../nerf/`, `../RoMa/`, `../RoMaV2/` | orthogonal |
