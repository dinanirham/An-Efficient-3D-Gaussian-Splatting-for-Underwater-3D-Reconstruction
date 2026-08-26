# CompGS / Compact3D — research methodology breakdown

Generated per `../../research-methodology.md`.

## Sources of evidence

| Source | Identifier |
|---|---|
| Paper | `../../compact3d.pdf` — *CompGS: Smaller and Faster Gaussian Splatting with Vector Quantization*, K L Navaneet\*, Kossar Pourahmadi Meibodi\*, Soroush Abbasi Koohpayegani, Hamed Pirsiavash (UC Davis). **ECCV 2024**; local PDF is **arXiv:2311.18159v3**, 26 Sep 2024. ✅ **correctly named for this folder** |
| Repo | `github.com/UCDvision/compact3d`, commit **`dccc07e3ab05f65246be25f0ee416aa9a127b54e`** (`dccc07e`), branch `main`, 2024-09-25. No tags. |

⚠️ **Naming.** The paper is titled **CompGS**; the repo and this folder are named
**compact3d**; and the method is referred to as **Compact3D** in the repo's own overview text.
All three refer to this work. **A different ECCV-2024-era work by Liu et al. is also called
"CompGS"** — that is `../CompGS/`. ⚠️ Until 2026-08-25 `../../CompGS.pdf` was a
**byte-identical duplicate of this folder's PDF**; it has since been replaced with the
correct Liu et al. paper. See `../CompGS/research-methodology-output/00-index.md`.

## ⚠️ This repo is a **file overlay**, not a standalone project

`[repo: README.md]`: clone 3DGS separately, then `bash move_files_to_gsplat.sh` to copy these
files into it. That is why `utils/`, `scene/`, `arguments/` and `gaussian_renderer/` are absent
here — they come from the upstream INRIA repository. Consequently:

- Everything not overridden is **stock 3DGS**, including `safe_state`'s hard-coded seed 0,
  the `llffhold = 8` split, and the standard metric harness.
- Only **four** files carry the method: `train_kmeans.py`, `kmeans_quantize.py`,
  `gaussian_model.py`, `decompress_to_ply.py`.

## Evidence tags

`[paper §X]` · `[repo: path:line]` · `[unverified]` · `[inferred]`

## Section files

| § | File |
|---|---|
| 1 | [`01-taxonomy.md`](01-taxonomy.md) |
| 2 | [`02-pipeline.md`](02-pipeline.md) |
| 3 | [`03-variables.md`](03-variables.md) |
| 4 | [`04-loss.md`](04-loss.md) |
| 5 | [`05-constraints.md`](05-constraints.md) |
| 6 | [`06-implementation-deltas.md`](06-implementation-deltas.md) |
| 7 | [`07-pseudocode.md`](07-pseudocode.md) |
| 8 | [`08-computational-profile.md`](08-computational-profile.md) |
| 9 | [`09-glossary.md`](09-glossary.md) |
| 10 | [`10-reproducibility.md`](10-reproducibility.md) |
| — | [`11-paper-vs-repo-disagreements.md`](11-paper-vs-repo-disagreements.md) |

## One-paragraph summary

CompGS compresses 3DGS with **quantization-aware vector quantization**. The intuition is that
"many Gaussians may have similar parameter values (e.g. covariance)" `[paper §3]`, so K-means
is run *during* training: the forward pass renders with **quantized** (centroid) parameters,
the backward pass updates the **non-quantized** parameters via a straight-through estimator,
and only the codebook plus one index per Gaussian is stored. Parameters are grouped by type —
**DC colour, higher-order SH, scale, rotation** get four independent codebooks — while
**position and opacity are left unquantized** ("sharing them results in overlapping
Gaussians"; opacity is a single scalar). Two cost-control tricks make this affordable:
centroids are updated every iteration but **assignments only every ~100 iterations**, and a
single K-means iteration is used rather than running to convergence. Separately, an **ℓ1
opacity regulariser** plus periodic pruning cuts the Gaussian *count*, which is what buys the
2–3× rendering speedup — and which the paper motivates by observing that after quantization the
**unquantized position and opacity dominate >80% of the remaining memory** `[paper §3]`.

> **Result:** ~**45×** compression at −0.3 dB with **2.5×** faster rendering (CompGS-32K), or
> ~**65×** with post-training bit quantization `[paper Fig. 1, Tab. 1]`.

> **Headline deltas found:** the paper's **run-length encoding of sorted indices is not
> implemented**; the shipped `run.sh` uses a **different configuration** from the paper
> (codebook sizes, K-means iterations, start iteration all differ); the described
> **assignment freeze at 25K does not exist**; and index bit-width is derived from the
> **number of Gaussians** rather than the codebook size. See
> [`06-implementation-deltas.md`](06-implementation-deltas.md).
