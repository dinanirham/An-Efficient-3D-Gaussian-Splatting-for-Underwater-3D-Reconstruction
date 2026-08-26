# §4 — Full loss function

## 4.1 The paper's statement

> `L = L_3DGS + λ_reg Σ_i^N α_i`, "where `L_3DGS` is the original loss of 3DGS with or without
> quantization and `λ_reg` controls the sparsity of opacity." `[paper §3]`

**Two terms**, and the repo agrees exactly.

## 4.2 The objective as implemented

`[repo: train_kmeans.py:157-167]`:
```python
if args.opacity_reg:
    if iteration > args.max_prune_iter or iteration < 15000:
        lambda_reg = 0.
    else:
        lambda_reg = args.lambda_reg
    L_reg_op = gaussians.get_opacity.sum()
    loss = (1.0 - opt.lambda_dssim) * Ll1 + opt.lambda_dssim * (1.0 - ssim(image, gt_image)) + (
            lambda_reg * L_reg_op)
else:
    loss = (1.0 - opt.lambda_dssim) * Ll1 + opt.lambda_dssim * (1.0 - ssim(image, gt_image))
```

```
L = 0.8·L₁(Î, I) + 0.2·(1 − SSIM(Î, I))  +  λ_reg · Σ_i α_i
                                             └── active only for 15 000 < iter ≤ 20 000,
                                                 λ_reg = 1e-7
```

✅ **`get_opacity` is `sigmoid(_opacity) ≥ 0`, so `.sum()` *is* the ℓ1 norm** — the paper's
"ℓ1 norm of the opacity" is implemented correctly, without an unnecessary `abs()`.

Loss-term count across your set:

| Method | Terms | New |
|---|---|---|
| 3DGS | 2 | — |
| **CompGS (this)** | **3** | **1** (ℓ1 opacity) |
| `../OMG/` | 2 | 0 |
| `../mini-splatting/`, `../EDGS/` | 2 | 0 |
| `../CompGS/` (Liu) | 3 (+aux) | 2 (`λR` + volume reg.) |
| `../seasplat/` | 7 | 5 |

## 4.3 Term-by-term

### 1. `L_3DGS` — the base photometric loss, **evaluated on quantized parameters**

`0.8·L₁ + 0.2·(1 − SSIM)`, unchanged. The subtlety is *what it is evaluated on*: after
`kmeans_st_iter`, the render uses **centroids**, not the optimized parameters
`[repo: train_kmeans.py:126-143]`. So the loss measures quantized-model quality while the
gradients update the unquantized parameters — the definition of quantization-aware training.

### 2. `λ_reg · Σ_i α_i` — the ℓ1 opacity regulariser ⭐ **the only loss modification**

- **Motivation, stated as a consequence rather than a prior** `[paper §3]`:
  > "Some parameters like position of the Gaussians cannot be quantized easily, so … after
  > quantization, they **dominate the memory (more than 80% of memory)**. This means
  > **quantization cannot improve the compression any further**. One way to compress 3DGS more
  > is to reduce the number of Gaussians. Interestingly, this reduction comes with a bi-product
  > that is **increase in inference speed**."
- **Mechanism** `[paper §3]`: "very small values of opacity correspond to transparent or nearly
  invisible Gaussians. Hence, **inspired by training sparse models**, we add ℓ1 norm of the
  opacity to the loss." Then "similar to the original 3DGS, we remove the Gaussians with
  opacity smaller than a threshold."
- **Schedule** `[paper §4]` = `[repo: train_kmeans.py:160-162, 220-226]`: `λ_reg = 1e-7` from
  **15 000 to 20 000**, with `prune(0.005)` every 1000 iterations inside that window, then the
  regulariser is switched off. ✅ Exact match.
- **What it prevents if removed:** nothing about *quality* — it is purely a **count** reduction,
  and it is where the **2–3× rendering speedup** comes from. Without it, CompGS compresses but
  does not accelerate.
- ⚠️ **`λ_reg = 1e-7` is tiny**, and it is applied to a **sum over millions of Gaussians**, so
  the effective per-Gaussian pressure is small but the aggregate gradient is meaningful. Note
  this is a `.sum()`, not a `.mean()` — the regulariser's strength therefore **scales with `N`**,
  which is self-limiting as Gaussians are pruned. `[inferred]`

## 4.4 Reading the results and ablations

### Table 1 — main results: **CUMULATIVE VARIANTS, not an ablation**

`[paper Tab. 1]`, Mip-NeRF 360 / Tanks&Temples:

| Method | SSIM | PSNR | LPIPS | FPS | Mem (MB) | Train (m) |
|---|---|---|---|---|---|---|
| 3DGS (reported) | 0.815 | 27.21 | 0.214 | 134 | 734 | 41.3 |
| 3DGS (reproduced) | 0.813 | 27.42 | 0.217 | 149 | 778 | 21.6 |
| LightGaussian | 0.805 | 27.28 | 0.243 | 209 | 42 | — |
| CGR | 0.797 | 27.03 | 0.247 | 128 | 29.1 | — |
| CGS | 0.801 | 26.98 | 0.238 | — | 28.8 | — |
| **CompGS 16K** | 0.804 | 27.03 | 0.243 | **346** | **18** | 22.8 |
| **CompGS 32K** | 0.806 | 27.12 | 0.240 | 344 | 19 | 29.4 |
| **CompGS 32K BitQ** | 0.797 | 26.97 | 0.245 | 344 | **12** | 29.4 |

Rows are **variants**, not ablation steps: 16K vs 32K differ in covariance codebook size, and
BitQ is a **post-training** bit-quantization applied on top of 32K.

- ✅ **65× smaller than 3DGS on Mip-NeRF 360** (778 → 12 MB) at **−0.45 dB** vs the reproduced
  baseline; **45×** (778 → 19) at **−0.30 dB** without BitQ.
- ✅ **2.3× faster rendering** (149 → 344 FPS) — from the opacity pruning, not the quantization.
- ⚠️ **Training is slower**: 21.6 → 29.4 min for 32K. The paper is upfront: "A limitation of
  CompGS compared to 3DGS is the **overhead in compute and training time introduced by the
  K-means clustering algorithm** … CompGS 32K needs **1.4× to 1.7× more training time**"
  `[paper §4]`. Consistent with `../CompGS/` (Liu) measuring this method's **encode time at
  68.29 s — the slowest of five compared methods** `[CompGS-Liu Tab. 7]`.
- ⚠️ **LPIPS degrades most** (0.217 → 0.240/0.245), as with every compression method in your set.

### Table 6 — the memory breakdown that motivates contribution 2

`[paper §3]` cites it: after quantization, position and opacity are "**more than 80% of
memory**", and `[paper §4]` restates that "**more than two-thirds** of its memory is due to the
non-quantized position and opacity parameters".

⚠️ The two figures (>80% and >2/3) are quoted from different places and are not identical;
neither table's cells survived text extraction cleanly. `[unverified]` for exact values.

**This is the single most useful number in the paper for your comparison**, because it explains
why every *later* method (`../OMG/`, `../CompGS/`) puts so much effort into **position** coding
— G-PCC in both cases. CompGS leaves position at float32; its successors do not.

### Table 9 — which parameters to quantize: **mutually-exclusive variants**

`[paper §4]`: "Additional results with different parameters being quantized are provided in
Table 9." The repo supports the corresponding options — `pos`, `dc`, `sh`, `scale`, `rot`, and
the joint `scale_rot`, `sh_dc` `[repo: train_kmeans.py:131-144]`.

⚠️ Table 9's cells did not survive extraction. `[unverified]` — but the *fact* that `pos`
quantization is implemented and was evaluated is confirmed by the code path, and the paper's
prose gives the conclusion: position is excluded because "sharing them results in overlapping
Gaussians" `[paper §3]`.

### Table 2 — parameter-compression baselines

Int-16/8/4 bit quantization, and "3DGS-No-SH" (dropping harmonics) are compared as alternative
compression strategies `[paper §4]`. ⚠️ Cells not extracted. `[unverified]`

### The `t = 500` claim

`[paper §3]`: "We observe that the modified approach **works well even for values of `t` as
high as 500**." Both the paper's experiments and `run.sh` use `t = 100`
`[repo: run.sh; train_kmeans.py:377]`, so **500 is an observation, not the operating point**.
No table isolates it. `[unverified]`

## 4.5 A methodological point the paper raises that is worth borrowing

`[paper §4]`, on evaluation:

> "The common practice is to report the **average of PSNR** across a set of images and scenes.
> However, this metric **may be dominated by very accurate reconstructions (smaller errors)**
> since it is based on the **geometric average of the errors due to the log operation** in PSNR
> calculation. Hence, for the larger ARKit dataset, we also report **PSNR-AM**, for which we
> **average the error across all images and scenes before calculating the PSNR**."

⭐ **This is exactly the Jensen-inequality issue that separates the PSNR conventions across your
comparison set** — see `../seasplat/research-methodology-output/10-reproducibility.md` §10.3c
and `../seathru_NeRF/research-methodology-output/10-reproducibility.md` §10.3a. CompGS is the
**only paper in the nine** that identifies the problem explicitly and introduces a corrected
metric for it. Worth citing when you justify whichever convention you standardise on.

## 4.6 What is *not* ablated

| Component | Ablated? |
|---|---|
| `λ_reg = 1e-7` | ❌ value given, no sweep |
| The 15 000–20 000 regularisation window | ❌ (and the lower bound is hard-coded) |
| `kmeans_freq = 100` vs 500 | ⚠️ asserted "works well" at 500, no table |
| `kmeans_iters = 1` | ❌ |
| The assignment-freeze schedule | ❌ — and it is absent from the code entirely (D-3) |
| RLE index compression | ❌ — and it is **absent from the code** (D-1) |
| Codebook size | ✅ **partially** — 16K vs 32K in Table 1 |
| Which parameters to quantize | ✅ Table 9 `[unverified]` |
| Bit quantization | ✅ BitQ row, Table 2 |
