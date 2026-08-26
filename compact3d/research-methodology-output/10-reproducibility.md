# §10 — Reproducibility checklist

## 10.1 Seed handling — inherited, and probably insufficient for K-means

CompGS is a **file overlay** onto 3DGS `[repo: README.md]`, so `utils/general_utils.py` and its
`safe_state()` come from upstream — i.e. the 3DGS convention of hard-coded
`random.seed(0)`, `np.random.seed(0)`, `torch.manual_seed(0)`, and **no**
`torch.cuda.manual_seed_all`.

| Item | Status |
|---|---|
| Python / NumPy / Torch-CPU seeds | inherited from 3DGS, hard-coded **0** |
| `torch.cuda.manual_seed_all` | ❌ not called (3DGS convention) |
| Seed exposed on the CLI | ❌ |
| Seed reported in the paper | ❌ no mention of seeds, repeats or variance |

⚠️ **K-means initialisation is the specific concern.** I did not locate an explicit
initialisation in `kmeans_quantize.py` in this pass `[unverified]` — but any random or
k-means++ init would be driven by the torch/CUDA RNG, and **CUDA is not seeded**. Since the
codebook determines the entire compressed representation, this makes **model size and quality
run-dependent** in a way the paper does not characterise.

Compare across the set: `../CompGS/` (Liu) seeds CUDA explicitly (3407) and averages **five
runs**; `../EDGS/` seeds CUDA (228); `../mini-splatting/`, `../OMG/` and CompGS-VQ all inherit
3DGS's CPU-only seeding.

## 10.2 Train/test split — ✅ the cleanest statement in your set

> "For a fair comparison, we use the **same train-test split as Mip-NeRF360 [4] and 3DGS
> [33]** and directly report the metrics for other methods from 3DGS [33]. We also report our
> **reproduced metrics for 3DGS** since we observe slightly better results compared to the ones
> in [33]." `[paper §4]`

| Item | Value |
|---|---|
| Split | 3DGS standard (`llffhold = 8`), inherited via the overlay |
| `--eval` | passed in `run.sh` ✅ `[repo: run.sh]` |
| Baseline sourcing | other methods **from the 3DGS paper**; 3DGS itself **re-run locally** on the same GPU |
| Datasets | Mip-NeRF 360 (9), T&T (2), Deep Blending (2), **DL3DV-10K (140)**, **ARKit-200 (200)** |

✅ **Re-running the 3DGS baseline locally and reporting both numbers** (27.21 reported vs 27.42
reproduced) is good practice — and it means the compression ratios should be computed against
**778 MB**, not the 734 MB from the original paper.

⭐ **The DL3DV-10K and ARKit-200 evaluations are the largest in your entire comparison set** —
340 additional scenes versus the 13-scene standard benchmark. Protocol details are deferred to
the appendix `[unverified]`.

## 10.3 Exact metric computation

### (a) PSNR — inherited from 3DGS, and the paper flags the underlying issue itself

The metric harness comes from the upstream 3DGS repo via the overlay, so CompGS's numbers
follow whatever `metrics.py` does there — the same call-site ambiguity documented for
`../OMG/` and `../EDGS/` (a `psnr()` written for `(3,H,W)` but called with `(1,3,H,W)`, which
silently converts per-channel-mean into pooled-MSE). `[unverified]` here, since `metrics.py` is
not in this folder.

⭐ **But CompGS is the only paper in your nine that identifies the underlying statistical
problem** `[paper §4]`:

> "The common practice is to report the **average of PSNR** across a set of images and scenes.
> However, this metric **may be dominated by very accurate reconstructions (smaller errors)**
> since it is based on the **geometric average of the errors due to the log operation** in PSNR
> calculation. Hence, for the larger ARKit dataset, we also report **PSNR-AM** for which we
> **average the error across all images and scenes before calculating the PSNR**."

This is precisely the Jensen-inequality argument that separates the conventions used across
your set (see `../seasplat/…/10-reproducibility.md` §10.3c and
`../seathru_NeRF/…/10-reproducibility.md` §10.3a). **Cite this passage when you justify
whichever convention you standardise on** — it is the one in-set source that names the problem.

### (b) Masking: none. Full-frame. Standard 3DGS harness.

### (c) What `Mem` means — ✅ the cleanest accounting in the compression half

The stored artifact is: unquantized attributes (`.ply`) + `kmeans_centers.pth` +
`kmeans_inds.bin` + `kmeans_args.npy` `[repo: train_kmeans.py:190-279]`.

**There is no decoder network to account for** — unlike `../OMG/` (four MLPs, counted) and
`../CompGS/` (Liu) (MLPs + entropy model, counted). CompGS-VQ's number is unambiguous.

⚠️ **But see D-4**: `n_bits` is derived from `log2(N)` rather than `log2(K)`
`[repo: train_kmeans.py:263]`, so `kmeans_inds.bin` on disk is ~1.7× larger than the indices
require. Whether the paper's `Mem` column was measured from these files or computed
analytically is `[unverified]` — **check before quoting the size figures**.

### (d) Compression ratios

> "In comparing model sizes, we normalize all methods by dividing them by **the size of our
> method** to obtain compression ratio." `[paper §4]`

⚠️ Note the direction: ratios are *relative to CompGS*, not to 3DGS. Read Table 1's `Mem`
column directly rather than any normalised ratio.

## 10.4 Stated non-determinism

**None stated.** No seeds, repeats or error bars.

Margins that would need them `[paper Tab. 1]`:
- CompGS 16K vs 32K on Mip-NeRF 360: **0.09 dB** (27.03 vs 27.12), **1 MB** (18 vs 19).
- CompGS 32K vs CGR: 0.09 dB.

The **robust** results are the compression ratios (**41–65×**) and the FPS gain (**2.3×**),
both of which are order-of-magnitude effects. Cite those.

## 10.5 Reproduction checklist for your cluster

| # | Action | Why |
|---|---|---|
| 1 | **Clone 3DGS first, then overlay.** `bash move_files_to_gsplat.sh`; `pip install bitarray` | this repo is not standalone `[repo: README.md]` |
| 2 | Rebuild `diff-gaussian-rasterization` + `simple-knn` with `TORCH_CUDA_ARCH_LIST` including **`9.0`** | the 3DGS release of this era targets pre-Hopper architectures |
| 3 | ⚠️ **Do not expect `run.sh` to reproduce the paper.** It uses `st_iter=15000`, `kmeans_iters=10`, `ncls_sh=512`, `ncls=4096` — versus the paper's 20000 / 1 / 4096 / 16384 | delta D-2. `run.sh` is the post-paper *opacity-regularization* recipe (README, 31 July 2024) |
| 4 | For **CompGS-16K**, set `--kmeans_st_iter 20000 --kmeans_iters 1 --kmeans_ncls 16384 --kmeans_ncls_sh 4096 --kmeans_ncls_dc 4096` | to match `[paper §4]` |
| 5 | `run.sh` needs a **two-stage workflow** — a prior unquantized run to `st_iter`, saved as `chkpnt<st_iter>.pth`, passed via `--start_checkpoint` | not described in the paper |
| 6 | Note the CLI **defaults disable the method**: `--kmeans_st_iter 30000` (⇒ never fires), `--lambda_reg 0.`, `--opacity_reg False` | a bare run trains plain 3DGS (delta D-6) |
| 7 | **Verify `kmeans_inds.bin` size** against `N·ceil(log2(K))/8` before quoting any storage figure | `n_bits` uses `log2(N)`, not `log2(K)` (delta D-4) |
| 8 | **Do not expect RLE.** The abstract's "sorting them and using a method similar to run-length encoding" has no implementation | delta D-1 |
| 9 | Expect **no assignment freeze** after 25K | delta D-3 |
| 10 | To sweep the opacity-reg window, **edit the source** — the lower bound `15000` is hard-coded | delta D-5 |
| 11 | Run ≥3 seeds and report dispersion on **`Mem` as well as PSNR** | the codebook is a random-init K-means outcome and CUDA is unseeded (§10.1) |
| 12 | Compute compression against the **reproduced** 3DGS (778 MB), not the reported 734 MB | `[paper §4]` provides both |
| 13 | ✅ **Lightest dependency footprint in your set** — only `bitarray` | no tiny-cuda-nn, no cuML, no G-PCC binary. Contrast `../OMG/` and `../CompGS/` |
| 14 | Use `decompress_to_ply.py` if you want a standard `.ply` for a SIBR viewer | `[repo: decompress_to_ply.py]` — CompGS is the only compression folder here whose output round-trips back to plain 3DGS with no network |
