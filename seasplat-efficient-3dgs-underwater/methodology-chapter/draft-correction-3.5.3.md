# Draft correction — §3.5.3 Component 2: Spatial Reorganization

**Target:** draft thesis, *An Efficient 3D Gaussian Splatting for Underwater 3D Reconstruction*,
§3.5.3 (p. 59–60).
**Reason:** the section contradicts both the implementation and the thesis's own Chapter 4.

---

## 1. What is actually wrong — narrower than first reported

On close reading, §3.5.3 is **already half-revised**. It contains two layers of text, and the
newer layer is largely correct. My earlier audit note (delta D-19/D-20) overstated the problem
by reading the superseded layer as live text. The corrected assessment:

### Layer A — superseded, still physically present (p. 59)

Three paragraphs, the last ending with the editorial marker **`(removed)`**:

> "…**Rather than removing primitives through pruning**, which can introduce discontinuities and
> destabilize optimization, this component focuses on **reorganizing** primitives to better
> reflect underlying surface structure."
> "The spatial reorganization strategy adopted in this study is inspired by **surface-aware
> Gaussian grouping approaches**…"
> "The number of Gaussian primitives may be reduced **implicitly through structural
> consolidation**… **(removed)**"

This is the flat contradiction — but it is **leftover text the author already marked for
deletion**. It was never the live claim. It simply was not cut.

### Layer B — the revision, and it is correct

> "…directly inspired by **Mini-Splatting (Fang and Wang, 2024), which proposes importance-based
> pruning**…"
> Eq. (3.1): importance = opacity × scale ✅
> "…the **lowest-importance primitives are pruned** until the budget is satisfied." ✅
> "…designed to occur **continuously after adaptive densification has completed**… Applying
> reorganisation during the densification phase would allow newly densified Gaussians to refill
> the pruned positions, defeating the budget enforcement." ✅

**This paragraph is right, and it correctly describes the shipped code** — the every-500
trigger after `densify_until_iter`, with the regrowth rationale stated. It also settles audit
question Q-6: the notebook markdown documenting a *single-shot prune at iteration 12 000* is the
stale artifact; **the draft thesis documents the version that actually ran.** My §6 delta D-20
should be read as a notebook-vs-code mismatch, not a thesis-vs-code one.

### What genuinely still needs fixing

| # | Location | Problem |
|---|---|---|
| **C-1** | Layer A, all three paragraphs | Superseded text still present, including the "rather than removing primitives through pruning" sentence. **Delete.** |
| **C-2** | Paragraph after the budget discussion | *"spatial reorganisation is treated as a geometric regularisation mechanism rather than a **compression or parameter reduction technique**"* — this **survived into the revision** and is the live contradiction. Pruning 4.46 M → 800 000 primitives *is* parameter reduction, and it is the mechanism's principal measured effect (2.26–5.58× smaller models). It also contradicts Chapter 4: *"reorganization, **which directly reduces the number of Gaussian primitives**"* (p. 108). |
| **C-3** | Opening paragraph; summary paragraph | "enforce surface coherence", "operating exclusively on the **spatial arrangement** of Gaussian primitives", "structural consolidation". No surface-fitting, grouping, or spatial rearrangement exists — primitives are scored and deleted. `Φ = α · max(s)` contains no neighbourhood, normal, occlusion, or visibility term. |
| **C-4** | Mini-Splatting attribution | Fair at the level of "importance-based pruning", but Eq. (3.1) is **not** Mini-Splatting's importance (accumulated blending weight over training views) and the selection is **deterministic** where the source is stochastic. Needs one qualifying sentence so a reviewer familiar with that work is not misled. |
| **C-5** | Absent | The medium-aware property of `Φ_i` — the strongest claim available for this component — appears nowhere in Chapter 3. |

---

## 2. Replacement text

Drop-in for the whole of §3.5.3. Section title left unchanged (see §4 below). British `-s-`
spelling used throughout, matching the revised layer.

---

### 3.5.3 Component 2: Spatial Reorganisation

The second component of the proposed method addresses over-parameterisation in the explicit
Gaussian representation through importance-based population control. This component is
motivated by limitations identified in Chapter 2, where Gaussian-based radiance-field methods
accumulate large numbers of primitives through unstructured adaptive densification, even when
initialisation is stabilised. In underwater reconstruction, such redundancy increases memory
consumption and rendering cost, and enlarges the primitive population over which medium-related
parameters must be jointly optimised.

The spatial reorganisation strategy adopted in this study is inspired by Mini-Splatting (Fang
and Wang, 2024), which establishes importance-based pruning as a principled mechanism for
reducing Gaussian population size while preserving reconstruction quality. In the proposed
framework, each Gaussian primitive is assigned an importance score defined as:

<div align="center">

Φ<sub>i</sub> = α<sub>i</sub> · max(s<sub>i</sub>)  (3.1)

</div>

where α<sub>i</sub> is the opacity of the *i*-th Gaussian and s<sub>i</sub> denotes its three
scaling coefficients. Primitives combining low opacity with small spatial extent are designated
as geometrically redundant and become candidates for removal. It should be noted that this
score is computed directly from stored primitive attributes, and therefore differs from the
accumulated blending-weight formulation used in the source method, which integrates
per-primitive contribution across training views. The present formulation is adopted for its
substantially lower computational cost, and the resulting mechanism is accordingly characterised
as magnitude-based importance pruning rather than as a reimplementation of Mini-Splatting.

A hard population budget of N = 800,000 Gaussians is enforced as the design target for all
reorganisation configurations. When the current Gaussian count exceeds this budget, the
lowest-importance primitives are pruned until the budget is satisfied. This enforcement is
designed to occur continuously after adaptive densification has completed, that is, after the
densification phase concludes, to ensure that the budget constraint is applied to the fully
grown Gaussian population rather than to an intermediate state during active densification.
Applying reorganisation during the densification phase would allow newly densified Gaussians to
refill the pruned positions, defeating the budget enforcement. This sequencing is therefore a
design requirement of the mechanism.

A property specific to the underwater setting arises from the definition of the importance
score. Because the opacity term is read after the SeaSplat opacity prior has acted upon it,
primitives whose rendered contribution consists predominantly of backscatter, and which the
physical image formation model has therefore already driven towards zero opacity, receive the
lowest importance scores and are removed first. The pruning criterion is in this sense coupled
to the underwater image formation model, a coupling that has no analogue in the terrestrial
formulation from which the mechanism is drawn. This coupling is also the reason the
reorganisation trigger must follow the activation of the SeaThru image formation model:
importance scores computed before that point would reflect opacities the physical model has not
yet shaped.

Importantly, spatial reorganisation operates exclusively on the population of Gaussian
primitives. It reduces the number of primitives and, consequently, the storage and rendering
cost of the representation, but it performs no attribute quantisation and does not modify the
parameters governing attenuation and scattering. The distinction maintained here is between
population-level reduction, which is the concern of this component, and attribute-level
reduction, which is introduced in Section 3.5.4.

The purpose of this component is to constrain representation complexity before attribute-level
parameter reduction is introduced. By bounding the primitive population prior to quantisation,
the method seeks to ensure that subsequent efficiency mechanisms operate on a stable and
bounded geometric structure. This sequencing reflects the dependency identified in Chapter 2
between geometric regularity and reliable radiometric gradient estimation.

In summary, the second component introduces importance-based spatial reorganisation as a means
of reducing population-level redundancy while preserving physical consistency. By operating
exclusively on which Gaussian primitives are retained, and avoiding any modification to the
rendering equation or to medium-related parameters, this component complements deterministic
initialisation and prepares the representation for controlled attribute-level quantisation in
the subsequent stage.

---

## 3. Change summary

| Action | Detail |
|---|---|
| **Deleted** | All three Layer-A paragraphs, including the `(removed)` marker and the "rather than removing primitives through pruning" sentence (**C-1**) |
| **Rewrote** | The scope paragraph: no longer denies being a parameter reduction technique; now draws the population-level vs. attribute-level distinction, which is the distinction the author was reaching for (**C-2**) |
| **Rewrote** | Opening and summary paragraphs: "surface coherence" and "spatial arrangement" replaced with population control and retention (**C-3**) |
| **Added** | One sentence qualifying the Mini-Splatting attribution — magnitude-based vs. accumulated blending weight (**C-4**) |
| **Added** | One paragraph on the medium-aware property of Φ and why it forces the trigger ordering (**C-5**) |
| **Kept verbatim** | The Mini-Splatting citation, Eq. (3.1), the 800,000 budget, and the entire post-densification sequencing rationale — these were already correct |

Net effect: **shorter** (three superseded paragraphs removed, two short ones added), and
consistent with both the code and Chapter 4.

---

## 4. Collateral items — your call, not applied here

| # | Item | Recommendation |
|---|---|---|
| **X-1** | 🔴 **Equation number (3.1) is used twice** — for the importance score in §3.5.3 *and* for PSNR in §3.7.1 (SSIM is (3.2)). | Importance stays (3.1); renumber §3.7 onward. Cascades through Chapter 3 — worth checking whether any other equations exist between them. |
| **X-2** | Section title "Spatial Reorganization" now names a mechanism that prunes. | **Recommend keeping it.** The label is established across the TOC, Chapter 4 (§4.4), Chapter 5 (§5.1.2), the A2 configuration name, tables and figures. Renaming cascades widely for modest gain, and the replacement text defines the term correctly on first use. If you do rename, "Importance-Based Population Control" is the accurate alternative. |
| **X-3** | Mixed spelling: "reorganization"/"reorganisation", "quantization"/"quantisation" vary within and across sections. | Pick one and sweep the document. The revised layers use `-s-`. |
| **X-4** | Other editorial markers survive in the live text: `(remove)` at the end of the first §3.6.4 paragraph, `(B-05)` in §3.5.1 and §3.6.4. | Housekeeping sweep before submission. |
| **X-5** | §3.5.2 closes by saying insufficient point density in turbid scenes "motivates the spatial reorganisation mechanism described in Section 3.5.3." | ⚠️ This causal link does not hold — A2 removes primitives, it cannot add coverage where the matcher failed. Given A1's Panama result, the honest bridge is that the density limitation motivates the *sensitivity analysis* (A1v2), not Component 2. Separate fix; flagging only. |
| **X-6** | Notebook markdown for A2 still documents `--reorganize_from_iter 12000` and a "single-shot" prune. | The draft is correct and the notebook is stale. Update the notebook so the two agree, or the discrepancy will resurface at viva. |
