# §1 — Taxonomic placement and modification

## Base method extended

**3D Gaussian Splatting**, Kerbl, Kopanas, Leimkühler & Drettakis, *ACM TOG 42(4), 2023*
(the paper's ref [17]) — specifically the **INRIA `graphdeco-inria/gaussian-splatting`
reference implementation**.

> "We implement our densification and simplification algorithms using PyTorch and integrate
> them into the optimization pipeline of 3DGS [17]." `[paper §6]`
> "**Acknowledgement.** This project is built upon [3DGS]." `[repo: README.md]`

More precisely, the target of modification is a *specific component* of 3DGS: the
**Adaptive Density Control (ADC)** heuristic — the gradient-thresholded clone/split plus
opacity/size pruning described in `[paper §3.1]`. The loss, the rasterizer's blending
equation, the Gaussian parameterisation, and the optimizer are all untouched.

One genuine CUDA-level change is required and is shipped as a forked rasterizer:

> "We modify the Gaussian rasterization module of 3DGS to render Gaussian indexes and depth
> points." `[paper §6]`
`[repo: gaussian_renderer/__init__.py:210 — `from diff_gaussian_rasterization_ms import ...`;
submodules/ contains the fork]`. The forked kernel returns three new per-Gaussian
accumulators — `accum_weights`, `area_proj`, `area_max` `[repo: gaussian_renderer/__init__.py:173, 189-191]` —
and a per-pixel `out_pts` / `accum_alpha` pair for depth `[repo: ms/train.py:173-174]`.

Secondary lineages:

| Lineage | What is inherited | Evidence |
|---|---|---|
| **Fang et al. / "VQ" — Compact 3D Scene Representation via Self-Organizing Gaussian Grids** family, via ref [21] | The **importance score** `I_i = Σ_j w_ij` (accumulated blending weight), originally a voxel-pruning idea from grid-based NeRFs | `[paper §3.2, §4.2, Appendix E]` |
| **Region-adaptive Hierarchical Transform (RAHT)**, ref [6] | The transform coding used by Mini-Splatting-**C** | `[paper Appendix F]` `[repo: ms_c/Haar3D_torch.py; ms_c/run.py:167]` |
| **Depth-supervised NeRF works**, refs [8, 39] | The idea (not the mechanism) of using depth to improve neural rendering | `[paper §4.1]` |

## The modification, in one sentence

Mini-Splatting replaces 3DGS's gradient-based adaptive density control with a
**reorganisation** schedule — blur-triggered splitting and periodic wholesale
reinitialization from rasterized ray/ellipsoid mid-point depth, followed by
intersection-preserving, importance-weighted **stochastic** subsampling — so that a fixed
Gaussian budget is spent on a uniform surface-adherent distribution rather than on
redundant clusters.

## Design family, in one sentence

Mini-Splatting is an **explicit radiance field** (rasterized 3D Gaussians), **per-scene
optimized**, with **no medium/degradation model whatsoever** — its axis of contribution is
**primitive-count efficiency via spatial redistribution**, which is orthogonal to the
physically-grounded-vs-learned-degradation axis that separates `seasplat/` from
`seathru_NeRF/`.

### The axis that actually matters here

Within the compression/efficiency half of your comparison set, the sharp distinction is
**what gets reduced**:

| | Mini-Splatting | `compact3d/` (CompGS-VQ) | `CompGS/` (Liu et al.) | `OMG/` | `EDGS/` |
|---|---|---|---|---|---|
| Reduces | **the number of Gaussians** `N` | **bits per Gaussian** (K-means codebook over `Σ` and SH) | bits per Gaussian (learned entropy model) | both | neither — it changes *initialization* |
| Mechanism | redistribute, then stochastically subsample | vector-quantize parameters during training | anchor/predictive coding + entropy model | see that folder | dense correspondence for init |
| Touches the loss? | **no** | **yes** (opacity regulariser) | yes | yes | no |
| Touches the rasterizer? | **yes** (needs index/depth output) | no | no | — | no |
| Output is a valid `.ply`? | **yes** — a plain, smaller 3DGS model | only after decompression | only after decoding | — | yes |

**Mini-Splatting-C sits in the second column too** — it is the only variant here that does
rate-distortion compression, and the paper is explicit that it "solely integrates basic
post-processing techniques" `[paper §6.1]` yet beats dedicated compression methods, because
the underlying model is already small. That framing — *make the representation good first,
then compress trivially* — is the paper's strategic claim against `compact3d/`-style work.

### Three consequences for the comparison

1. **The Gaussian counts are not comparable across variants without saying which one.**
   Mini-Splatting-**D** *increases* `N` (4.69 M vs 3DGS's 3.35 M on Mip-NeRF 360);
   Mini-Splatting *decreases* it to 0.49 M `[paper Tab. 1]`. Same paper, opposite
   direction. Always name the variant.
2. **`sh_degree` is scheduled, not fixed.** Training starts at SH degree 0
   `[repo: ms/train.py:56 — GaussianModel(sh_degree=0)]` and only ramps to the full degree
   *after* simplification at 15 K `[repo: ms/train.py:102-103, 250]`. The paper states the
   reason: "incorporating view-dependent colors barely enhance densification"
   `[paper §5]`. This is why Mini-Splatting-D can hold 5.40 M Gaussians in the *same*
   7.45 GB as 3DGS's 4.86 M `[paper Tab. 2]` — the extra Gaussians are cheap during the
   densification phase. Any per-Gaussian storage comparison must account for it.
3. **Its failure mode is the sky.** The method is depth-driven, so regions with no valid
   depth are not reinitialized: "This strategy fails in areas without a certain depth
   value, such as the sky in *train*" `[paper Appendix G]`, which the paper offers as the
   explanation for its lower PSNR on Tanks&Temples `[paper §6.1]`. Relevant if you intend
   to combine this with underwater scenes, where the *water column* is the analogous
   depth-less region.

## Position relative to the sibling folders

| Folder | Relationship |
|---|---|
| `gaussian-splatting/` | the base method; `gs/` in this repo is a vendored copy used as the `3DGS*` baseline |
| `compact3d/` | the "VQ" curve in `[paper Fig. 7]`; Mini-Splatting applies ref [21]'s pruning to 3DGS as a comparison point |
| `CompGS/`, `OMG/` | same efficiency axis, different mechanism (entropy coding / joint) |
| `EDGS/` | complementary — improves *initialization*; Mini-Splatting improves *redistribution*. Appendix B's "3DGS (Dense)" experiment is essentially the question EDGS answers `[paper Appendix B, Tab. 5]` |
| `colmap/` | upstream SfM initialization |
| `seasplat/`, `seathru_NeRF/`, `nerf/` | orthogonal — no shared machinery |
| `RoMa/`, `RoMaV2/` | orthogonal, but note Appendix B uses MVS [33] for dense init, which is the same role RoMa plays for EDGS |
