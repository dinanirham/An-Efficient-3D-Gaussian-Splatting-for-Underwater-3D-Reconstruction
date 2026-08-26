# §1 — Taxonomic placement and modification

## Base method extended

**Mip-NeRF 360**, Barron, Mildenhall, Verbin, Srinivasan & Hedman, *CVPR 2022* (ref [5])
— specifically the **`google-research/multinerf` JAX reference implementation**, in its
**forward-facing + normalized-device-coordinates (NDC)** configuration.

> "Our implementation is based on the code released in Mip-NeRF-360 [5], choosing the best
> performing baseline on our scenes which was the forward-looking configuration with
> normalized device coordinates (NDC)." `[paper §4.5]`

`[repo: README.md — "Our implementation is based on … Mip-NeRF 360 … and their github
repository (google-research/multinerf)"]`
`[repo: configs/llff_256_uw.gin:5 — `Config.forward_facing = True`; :2-3 — `near = 0., far = 1.`]`

Everything inherited from mip-NeRF 360 and *kept*: integrated positional encoding (IPE) over
conical frustums `[repo: internal/models.py:774-777]`, the proposal-MLP / interlevel-loss
sampling hierarchy `[repo: internal/train_utils.py:115-127]`, the `octahedron` positional
basis, and the Adam/learning-rate schedule (`"We keep the learning rate and optimization
parameters the same as in [5]"` `[paper §4.5]`).

Secondary lineages:

| Lineage | What is inherited | Evidence |
|---|---|---|
| **Akkaynak & Treibitz, "A Revised Underwater Image Formation Model", CVPR 2018** (ref [1]) | The target image formation model `I = J e^{-β^D z} + B^∞(1-e^{-β^B z})` with **distinct** `β^D ≠ β^B`; the whole point of §4.2 is to show the new rendering equations reduce to it | `[paper §3.2 / Eq. 7; §4.2]` |
| **RawNeRF**, Mildenhall et al. CVPR 2022 (ref [23]) | The gradient-reweighted reconstruction loss for linear/HDR images (Eq. 25) | `[paper §4.4 / Eq. 25]` `[repo: internal/train_utils.py:95-102]` |
| **Rebain et al. / ref [34]** | The mixture-of-two-Laplacians binary prior on transmittance (Eq. 26) | `[paper §4.4 / Eq. 26]` `[repo: internal/train_utils.py:153-167]` |

## The modification, in one sentence

SeaThru-NeRF adds a **second, medium-specific radiance component with its own density and
colour** directly inside the volume-rendering integral — `C(r) = ∫ T(t)(σ^obj c^obj +
σ^med c^med) dt` `[paper Eq. 8]` — and constrains the medium's parameters
`(c^med, σ^bs, σ^attn)` to be **constant along each 3D ray**, produced by a separate MLP
that takes only the viewing direction as input.

## Design family, in one sentence

SeaThru-NeRF is an **implicit MLP radiance field** (no explicit primitives), **per-scene
optimized**, with a **physically-grounded medium model whose parameters are a learned
function of viewing direction** — i.e. a *field*, not a set of constants — which places it
on the opposite side of the field's sharpest axis from SeaSplat's explicit-primitive,
scene-global-constant formulation.

### The axis, made precise

This is the distinction the methodology (§1) singles out, and it is worth stating exactly
because the two papers use nearly identical glyphs for objects of different type:

| | SeaThru-NeRF | SeaSplat |
|---|---|---|
| Scene representation | implicit MLP field, sampled along rays | explicit 3D Gaussians, rasterized |
| Medium parameters | `σ^attn(v), σ^bs(v), c^med(v)` — **functions of viewing direction `v`**, evaluated per ray | `β^D, β^B, B^∞` — **9 global scalars**, constant over the whole scene |
| Cardinality | one 9-vector **per ray** (≈ 16 384 per training batch) | one 9-vector **per scene** |
| Where the medium enters | inside the rendering integral, per sample | as a post-hoc composition on the rendered image |
| Constancy assumption | constant **along a ray** ("far less restrictive compared to models that assume constancy per image or even per scene [2]" `[paper §4.1]`) | constant **over the scene** — exactly the case SeaThru-NeRF names as more restrictive |
| Depth handling | depth is implicit in the sample distribution `s_i`; never materialised as a supervision target | explicit `Ẑ` map, rasterized in a second pass, then min–max normalised per frame |

**SeaThru-NeRF explicitly positions itself against the per-scene assumption that SeaSplat
later adopts.** That is not a contradiction — SeaSplat trades medium expressiveness for a
1000× cheaper representation — but any comparison table must not present the two `β`/`σ`
sets as measurements of the same physical quantity. See
[`09-glossary.md`](09-glossary.md) and `../../comparison-glossary.md`.

### Three further consequences

1. **Restoration is free, and unsupervised.** Because the object and medium components are
   separate summands, the "clean" image is just the object term rendered without
   attenuation. In code it is literally `J = stop_gradient(Σ w_i c^obj_i)`
   `[repo: internal/render.py:319]` — **an output only, carrying no gradient and never
   supervised**. Same situation as SeaSplat's `Ĵ`: no ground truth exists.
2. **No hand-crafted image priors.** SeaThru-NeRF has *no* grey-world, saturation,
   dark-channel, or background loss. Its entire well-posedness argument rests on the
   structural constraint (medium constant per ray) plus one transmittance prior. Contrast
   SeaSplat's five auxiliary priors. See [`05-constraints.md`](05-constraints.md).
3. **The background must not be opaque.** mip-NeRF 360 initialises the farthest interval
   with infinite density so rays that hit nothing get a background colour. SeaThru-NeRF
   **disables** this — "it prevents our method from explaining the medium that contributes
   to the rendered color along the ray" `[paper §4.5]`, confirmed
   `[repo: configs/llff_256_uw.gin — Model.opaque_background = False]`. Rays that hit no
   object must be explained *by the medium*, which is the mechanism that makes `c^med`
   identifiable at all.

## Position relative to the sibling folders

| Folder | Relationship |
|---|---|
| `nerf/` | the original NeRF (Mildenhall et al., ref [25]) — the root of this lineage |
| `seasplat/` | the explicit-primitive counterpart; SeaSplat benchmarks against this method `[seasplat paper Tab. I-II]` |
| `gaussian-splatting/` | the substrate SeaSplat uses; SeaThru-NeRF predates it |
| `colmap/` | upstream pose estimation — used here for real scenes `[paper §5.1]` |
| `mini-splatting/`, `CompGS/`, `compact3d/`, `OMG/`, `EDGS/` | orthogonal (3DGS efficiency/compression) — no shared machinery |
| `RoMa/`, `RoMaV2/` | orthogonal (dense matching) |
