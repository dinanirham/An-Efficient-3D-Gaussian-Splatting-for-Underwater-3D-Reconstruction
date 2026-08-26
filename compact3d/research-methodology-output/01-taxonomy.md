# §1 — Taxonomic placement and modification

## Base method extended

**3D Gaussian Splatting**, Kerbl, Kopanas, Leimkühler & Drettakis, *ACM TOG 42(4), 2023*
(ref **[33]**) — the **INRIA reference implementation, unmodified**, with this repo's files
copied over the top.

> "For all our experiments, we use the **publicly available official code repository [1] of
> 3DGS [33]** provided by its authors. **There are no changes in the hyperparameters used for
> training compared to 3DGS.**" `[paper §4]`

`[repo: README.md]` confirms the mechanism: clone 3DGS, then `bash move_files_to_gsplat.sh`.
Only four files carry the method — `train_kmeans.py`, `kmeans_quantize.py`,
`gaussian_model.py`, `decompress_to_ply.py`. Densification, opacity reset, the LR schedule and
the loss are all stock, and `reset_opacity()` **is** still called
`[repo: train_kmeans.py:217-218]` — unlike `../mini-splatting/` and `../OMG/`, which silently
remove it.

Secondary lineages:

| Lineage | What is inherited | Evidence |
|---|---|---|
| **Straight-Through Estimator** (ref [7]) | The quantization-aware training mechanism: quantized forward, non-quantized backward | `[paper §3]` "We use straight-through estimator proposed in STE [7]" |
| **VQAD** (ref [60]), **VQRF** (ref [39]) | Vector quantization applied to radiance fields — but on grids/features, not Gaussians | `[paper §2]` |
| Sparse-model training | The ℓ1 opacity regulariser: "inspired by training sparse models" | `[paper §3]` |
| Absmax bit quantization (ref [14]) | The post-training BitQ variant | `[paper §4]` |

## The modification, in one sentence

CompGS runs **K-means vector quantization during training** — quantized forward, STE backward,
centroids updated every step but assignments only every ~100 steps — on **four separate
parameter groups** (DC colour, SH, scale, rotation) while leaving position and opacity
unquantized, and adds an **ℓ1 opacity regulariser with periodic pruning** to cut the Gaussian
count.

## Design family, in one sentence

CompGS is an **explicit radiance field** (rasterized 3D Gaussians), **per-scene optimized**,
with **no medium/degradation model**, whose axis of contribution is **bits per primitive via
quantization-aware vector quantization** — plus a secondary count reduction that exists
specifically because quantization alone hits a floor.

### The argument structure, which is unusually explicit

The paper's two contributions are **causally linked**, and it says so:

> "Some parameters like position of the Gaussians cannot be quantized easily, so … after
> quantization, they **dominate the memory (more than 80% of memory)**. This means
> **quantization cannot improve the compression any further**. One way to compress 3DGS more
> is to **reduce the number of Gaussians**." `[paper §3]`

So: VQ compresses the compressible attributes → position/opacity become the bottleneck → the
only remaining lever is fewer Gaussians → opacity regularization. And the count reduction has
a "bi-product that is increase in inference speed" `[paper §3]`, which is where the 2–3×
FPS gain comes from — **not** from the quantization.

**This matters when citing.** CompGS's compression is VQ; its *speedup* is pruning. They are
separable, and Table 1's FPS column reflects the second, not the first.

### Where CompGS sits among the compression folders

| | **CompGS (this)** | `../OMG/` | `../CompGS/` (Liu) | `../mini-splatting/` (`ms_c`) |
|---|---|---|---|---|
| Quantization | **K-means VQ, quantization-aware** | Sub-Vector (Product) QAT | scalar + learned entropy model | RAHT transform coding, post-hoc |
| Codebooks | 4 (dc, sh, scale, rot) | 3 (scale, rot, appearance) | — | — |
| Codebook size | **4096 / 16384 / 32768** | 64 / 512 / 1024 per partition | — | — |
| Rate term in the loss? | ❌ | ❌ | ✅ `λR` | ❌ |
| Count reduction | ✅ ℓ1 opacity reg. + pruning | ✅ LD scoring | ✅ anchor pruning | ✅ (the whole method) |
| Neural decode at render? | ❌ **none** | ✅ tiny MLPs | ✅ per-view MLP | ❌ |
| Base method | **vanilla 3DGS** | Mini-Splatting | Scaffold-GS | vanilla 3DGS |
| Output renderable directly? | ⚠️ needs codebook lookup, but `decompress_to_ply.py` restores a standard `.ply` | needs MLPs | needs MLPs + entropy decoder | needs RAHT decode |

### Three consequences

1. **CompGS is the *simplest* method in the compression half of your set** — no neural field,
   no entropy model, no external codec (contrast `../OMG/` and `../CompGS/`, which both need
   G-PCC compiled separately). Its only extra dependency is `bitarray` `[repo: README.md]`.
2. **It keeps 3DGS's rendering path intact.** Indices act "as a pointer to the correct code
   freeing the memory needed to replicate those parameters for all Gaussians" `[paper §1]`, so
   there is no per-frame decode cost — which is why it reaches 346 FPS where `../OMG/` (per-frame
   MLP) reaches 350 with far fewer Gaussians, and `HAC` reaches only 110.
3. **It is the baseline everyone else compares against.** It appears as
   "CompGS [44]" in `../OMG/`'s Tables 1–2 `[inferred]` and as "Navaneet et al. [33]" in
   `../CompGS/`'s Tables 1–3 and Fig. 6 — where its encode time (68.29 s) is the slowest
   measured, a direct consequence of K-means.

## Position relative to the sibling folders

| Folder | Relationship |
|---|---|
| `../gaussian-splatting/` | the base method (ref [33]), used unmodified as a file overlay |
| **`../CompGS/`** (Liu et al.) | **name collision**, and this work is a **baseline in that paper** (`Navaneet et al. [33]`). `../../CompGS.pdf` formerly duplicated this folder's PDF; corrected 2026-08-25 |
| **`../OMG/`** | a **direct descendant of the same idea** — replaces K-means VQ with Sub-Vector Quantization, explicitly citing R-VQ/VQ trade-offs `[OMG §3.2]`; lists this work in its Tables 1–2 |
| `../mini-splatting/` | orthogonal mechanism (count via redistribution), concurrent; `ms_c` competes on rate |
| `../nerf/` | the NeRF baseline whose model size CompGS aims to match `[paper Fig. 1]` |
| `../colmap/` | upstream SfM |
| `../EDGS/`, `../seasplat/`, `../seathru_NeRF/`, `../RoMa/`, `../RoMaV2/` | orthogonal |
