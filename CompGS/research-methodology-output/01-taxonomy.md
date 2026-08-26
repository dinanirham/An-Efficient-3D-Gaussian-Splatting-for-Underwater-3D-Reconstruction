# §1 — Taxonomic placement and modification

> ⚠️ All `[paper …]` citations refer to **arXiv:2404.09458v1** = `../../CompGS.pdf`.
> Not to be confused with `../compact3d/`, the other "CompGS". See [`00-index.md`](00-index.md).

## Base method extended

**Scaffold-GS: Structured 3D Gaussians for View-Adaptive Rendering**, Lu, Yu, Xu, Xiangli,
Wang, Lin & Dai (ref **[27]** in the paper) — *not* vanilla 3DGS, despite 3DGS being the
headline comparison.

The paper cites Scaffold-GS only in passing — "Lu et al. [27] developed a structured
Gaussian splatting method named Scaffold-GS, in which anchor points are utilized to
establish a hierarchical representation of 3D scenes" `[paper §2.1]` — but the dependency
is structural, and three separate places make it explicit:

| Evidence | What it shows |
|---|---|
| "view embeddings **[27]**" `[paper §3.2]` | the view-conditioning scheme is Scaffold-GS's |
| "adaptive control **[27]** is applied to manage the number of anchor primitives" `[paper §3.4]` | the growing/pruning rules are Scaffold-GS's |
| "Recent work **[27]** introduces a primitive derivation paradigm … we devise a variant, named *w.o. Res. Embed.*, which adheres to such primitive derivation paradigm [27] by removing the residual embeddings" `[paper §4.3]` | **the ablation baseline literally *is* Scaffold-GS** |
| `[repo: README.md — Acknowledgment lists Scaffold-GS second, after 3DGS]` | |
| `[repo: Modules/Optimization/AdaptiveControl.py:38-113]` | multi-level voxel growing with `update_depth`/`update_hierarchy_factor`/`update_init_factor` — verbatim Scaffold-GS |

Reading Table 5 correctly therefore matters a great deal: **"w.o. Res. Embed." ≈
Scaffold-GS + rate-constrained optimization**, so the 0.99 dB gap it reports is CompGS's
gain *over its true base method*, not over 3DGS. See [`04-loss.md`](04-loss.md) §4.4.

Secondary lineages, all acknowledged `[repo: README.md]`:

| Lineage | What is inherited | Evidence |
|---|---|---|
| **3DGS** (ref [17]) | the rasterizer (custom CUDA kernels), the `(1−λ)L₁ + λ D-SSIM` rendering loss, the evaluation protocol and scene selection | `[paper §3.4, §4.1]` `[repo: submodules/diff-gaussian-rasterization]` |
| **Ballé et al. 2017/2018** (refs [1], [2]) | the **factorized entropy bottleneck** and the **conditional Gaussian entropy model with hyperpriors** — the core of the rate model | `[paper §3.3, Eqs. 8-12]` `[repo: Modules/GaussianModels/Modules/EntropyModel.py — `CompressionModel`, `GaussianConditional` from CompressAI]` |
| **CompressAI** (ref [5]) | the actual entropy-coding library | `[paper §3.4]` `[repo: README.md installation notes]` |
| **G-PCC / MPEG TMC13** (ref [37]) | lossless coding of anchor positions | `[paper §3.4]` `[repo: README.md; Modules/Common/ compress_gpcc]` |
| **VVC / affine motion compensation** (refs [6], [25]) | the *conceptual* framing: predict, code residuals, optimize rate-distortion | `[paper §2.3, §3.2]` |

## The modification, in one sentence

CompGS replaces Scaffold-GS's independently-stored per-anchor feature banks with a
**two-tier predictive code** — a few 32-D anchor reference embeddings from which `K = 10`
coupled primitives are decoded, each carrying only an 8-D residual embedding — and trains
the whole thing against an **explicit rate-distortion objective** `L = λR + D` whose `R`
comes from a differentiable conditional-Gaussian entropy model with hyperpriors.

## Design family, in one sentence

CompGS is an **explicit radiance field** (rasterized Gaussians), **per-scene optimized**,
with **no medium/degradation model**, whose axis of contribution is **rate-distortion
compression via learned predictive coding + entropy modelling** — i.e. it reduces *bits per
primitive*, not *number of primitives*, and it is the only method in your comparison set
that optimizes a **bitrate term inside the training loss**.

### The axis that separates it from its neighbours

| | **CompGS (Liu)** | `compact3d/` (CompGS-VQ, Navaneet) | `mini-splatting/` | `OMG/` |
|---|---|---|---|---|
| What is reduced | **bits per primitive** | **bits per primitive** | **number of primitives** | both |
| Mechanism | learned **prediction** + **entropy model**, RD-optimized end-to-end | **K-means vector quantization** of `Σ` and SH, + opacity regulariser | spatial redistribution + stochastic subsampling | see that folder |
| Rate in the loss? | ✅ **yes**, `λR` with `λ ∈ {0.001, 0.005, 0.01}` | ❌ no — quantization error is implicit | ❌ no | — |
| Multiple rate points? | ✅ **yes** — a true R-D curve from one knob | ❌ single point per codebook size | ❌ (a quality/count curve, not R-D) | — |
| Needs an external codec? | ✅ **G-PCC** binary must be compiled separately | ❌ | ❌ (`numpy.savez_compressed`) | — |
| Output is a plain 3DGS `.ply`? | ❌ — decoding requires the MLPs **and** the entropy model | ❌ (needs codebook) | ✅ | — |
| Renders anchors or derived? | **derived** (`K = 10` per anchor), decoded **per frame, per view** | the Gaussians themselves | the Gaussians themselves | — |

Two consequences that must not be lost in a comparison table:

1. **`num_gaussians` is not comparable across these methods.** CompGS reports the number of
   **anchor primitives** `[repo: README.md — "num_gaussians: number of anchor primitives";
   Modules/TrainerCompGS.py:367]`. The number of Gaussians actually rasterized is up to
   `10×` larger (minus opacity-culled ones). Every other method in the set reports the
   rendered count.
2. **CompGS's model size includes the neural networks.** `[repo:
   Modules/TrainerCompGS.py:346-348]` explicitly adds `weights.pth` to the reported total,
   and Fig. 8 breaks out "Network Weights" as a bitstream component consuming ~24–46% of
   the bitstream at the operating points shown `[paper Fig. 8]`. That is honest accounting
   — and it is *why* the network-weight share grows as `λ` grows (the scene bits shrink but
   the MLPs do not). Confirm competitors count their decoders the same way before
   tabulating.

### Two further consequences

3. **Rendering requires an MLP forward pass per view.** Opacity and colour are
   view-dependent MLP outputs `[paper Eq. 5]` `[repo:
   Modules/GaussianModels/Modules/Prediction.py:59-62]`, so decode cost is paid at *every*
   frame, not once. The paper measures this separately as `predict_time`
   `[repo: Modules/TesterCompGS.py:63-66]`. Despite that, its reported render time is the
   **fastest** of all compared methods (5.32 ms vs 6.60–9.88 ms `[paper Tab. 7]`) — because
   far fewer Gaussians reach the rasterizer.
4. **Anchor positions are frozen.** `means_lr_init: 0.0` and `means_lr_final: 0.0` in all
   three shipped configs `[repo: Configs/*.yaml]`. Anchors never move from their voxelized
   SfM positions — which is what makes lossless G-PCC coding of an integer voxel grid valid
   `[repo: Modules/GaussianModels/Model.py:313-315]`. The paper does not state this.

## Position relative to the sibling folders

| Folder | Relationship |
|---|---|
| `gaussian-splatting/` | the anchor baseline (`Kerbl et al. [17]`) and the rasterizer source |
| `compact3d/` | **a directly-compared baseline** — `Navaneet et al. [33]` in Tables 1–3, Fig. 6, Fig. 7, Tab. 7. Also the source of the acronym collision. |
| `mini-splatting/` | not compared against (concurrent, ECCV 2024); orthogonal mechanism |
| `OMG/` | same compression axis, later work |
| `EDGS/` | orthogonal (initialization) |
| `colmap/` | upstream SfM; anchors are initialized from voxel-downsampled COLMAP points `[paper §3.4]` |
| `seasplat/`, `seathru_NeRF/`, `nerf/`, `RoMa/`, `RoMaV2/` | orthogonal |
