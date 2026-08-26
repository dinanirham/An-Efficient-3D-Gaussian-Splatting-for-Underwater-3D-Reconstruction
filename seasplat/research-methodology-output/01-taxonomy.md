# §1 — Taxonomic placement and modification

## Base method extended

**3D Gaussian Splatting**, Kerbl, Kopanas, Leimkühler & Drettakis, *ACM TOG 42(4), July 2023*
— specifically the **INRIA `graphdeco-inria/gaussian-splatting` reference implementation**,
not a reimplementation. `[paper §IV.C: "We build upon the code from 3D Gaussian Splatting [11]"]`
`[repo: README.md — "The codebase is built upon the original INRIA Gaussian Splatting implementation"; every core file retains the INRIA copyright header, e.g. train.py:1-10]`

Two secondary lineages are grafted on:

| Lineage | What is inherited | Evidence |
|---|---|---|
| **Akkaynak & Treibitz, "A Revised Underwater Image Formation Model", CVPR 2018** (ref [23]) | The image formation equation itself, `I = J·e^{-β^D Z} + B^∞(1 - e^{-β^B Z})`, with *distinct* wavelength-dependent `β^D ≠ β^B` | `[paper §III.B / Eq. 3]` |
| **DeepSeeColor**, Jamieson, How & Girdhar, ICRA 2023 (ref [32]) | The backscatter/attenuation **network parameterization** and the dark-channel-style backscatter loss | `[paper §IV.B, Eq. 4]` `[repo: deepseecolor/ — the whole directory is a vendored DeepSeeColor; deepseecolor/models.py:104-149 comments cite "DSC eqn 12"/"DSC eqn 13"]` |
| **Depth + alpha rasterization** from latentSplat (ref [36]) / DN-Splatter (ref [37]) | Differentiable depth and alpha output from the rasterizer | `[paper §IV.C]` `[repo: gaussian_renderer/__init__.py:109 render_depth]` |

## The modification, in one sentence

SeaSplat constrains the 3DGS rasterizer output to be the **medium-free radiance `Ĵ`**
rather than the observed radiance, and composes it with a *scene-global*, six-parameter
physical medium model driven by the rasterized depth `Ẑ` before applying the photometric
loss — so the photometric residual is paid by the medium model rather than by spurious
Gaussians in the water column.

## Design family, in one sentence

SeaSplat is an **explicit radiance field** (rasterized anisotropic 3D Gaussians, not an
implicit MLP field), **per-scene optimized** (not feed-forward/generalizable), with a
**physically-grounded medium model whose parameters are global constants for the scene**
— placing it on the opposite side of the field's sharpest axis from SeaThru-NeRF /
WaterNeRF, which estimate medium parameters *conditioned on viewing direction through a
learned MLP* and must therefore query the medium densely along every ray.

### Why this axis matters for the comparison set

The paper states the distinction explicitly and uses it as its efficiency argument:

> "While SeaThru-NeRF estimates water parameters per viewing direction with a learned MLP,
> SeaSplat assumes the water parameters are consistent for the whole scene and does not
> require such dense sampling." `[paper §V.A.b]`

> "our method does not require densely querying or sampling medium parameters at every
> pixel, instead having a set of global medium parameters." `[paper §V.B]`

Three consequences that propagate through the rest of this breakdown:

1. **Homogeneity assumption.** A single `(β^D, β^B, B^∞)` triple for the whole scene is a
   *regularity assumption* — it is one of the mechanisms that makes the objective
   well-posed (see [`05-constraints.md`](05-constraints.md)), not merely an efficiency choice.
2. **Notation collision risk.** SeaSplat's `β^D`/`β^B` are **global learned scalars**
   (3 per map). SeaThru-NeRF's corresponding quantities are **per-sample MLP outputs**
   evaluated along a ray. The symbols look identical in both papers and are *not the same
   mathematical object*. See [`09-glossary.md`](09-glossary.md) and the cross-method
   comparison glossary.
3. **Failure mode inheritance.** Because the medium is global, SeaSplat cannot represent
   spatially-varying water (turbidity gradients, shadow, caustics). The paper concedes
   caustics and shadows are out of scope `[paper §VI, Limitations]`.

## Position relative to the sibling folders in this comparison set

| Folder | Axis: explicit vs implicit | Axis: medium model | Relationship to SeaSplat |
|---|---|---|---|
| `seathru_NeRF/` | implicit MLP (Zip-NeRF/mip-NeRF-360 based) | physical, per-ray MLP-predicted | the direct baseline SeaSplat compares against `[paper Tab. I]` |
| `gaussian-splatting/` | explicit | none | the base method being modified |
| `mini-splatting/`, `CompGS/`, `compact3d/`, `OMG/` | explicit | none | orthogonal — compression/efficiency of the same 3DGS substrate |
| `EDGS/` | explicit | none | orthogonal — initialization/densification of the same substrate |
| `RoMa/`, `RoMaV2/` | neither (dense feature matcher) | none | upstream correspondence, not a radiance field |
