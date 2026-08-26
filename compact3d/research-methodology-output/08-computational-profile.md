# §8 — Computational profile

## 8.1 As reported

`[paper §4]`: **"All experiments were run on a single RTX-6000 GPU."**
`[paper Tab. 1 caption]`: "Our timings for 3DGS and CompGS are reported using a **RTX6000**
GPU while those with ‡ used **A6000** GPU."

Good disclosure — the GPU is named, 3DGS is **re-run on the same card**, and rows measured on
different hardware are footnoted rather than silently mixed.

### Mip-NeRF 360 `[paper Tab. 1]`

| Method | SSIM | PSNR | LPIPS | FPS | Mem (MB) | Train (min) |
|---|---|---|---|---|---|---|
| INGP-Big | 0.699 | 25.59 | 0.331 | 9.43 | **48** | 7.30 |
| Mip-NeRF 360 | 0.792 | **27.69** | **0.237** | 0.06 | 8.6 | **48 h** |
| 3DGS (reported) | 0.815 | 27.21 | 0.214 | 134 | 734 | 41.3 |
| **3DGS (reproduced)** | 0.813 | **27.42** | 0.217 | 149 | 778 | **21.6** |
| LightGaussian | 0.805 | 27.28 | 0.243 | 209 | 42 | — |
| CGR | 0.797 | 27.03 | 0.247 | 128 | 29.1 | — |
| CGS | 0.801 | 26.98 | 0.238 | — | 28.8 | — |
| **CompGS 16K** | 0.804 | 27.03 | 0.243 | **346** | **18** | 22.8 |
| **CompGS 32K** | 0.806 | 27.12 | 0.240 | 344 | 19 | 29.4 |
| **CompGS 32K BitQ** | 0.797 | 26.97 | 0.245 | 344 | **12** | 29.4 |

### Tanks&Temples `[paper Tab. 1]`

| Method | SSIM | PSNR | LPIPS | FPS | Mem | Train |
|---|---|---|---|---|---|---|
| 3DGS (reproduced) | 0.844 | 23.68 | 0.178 | 206 | 433 | 12.2 |
| **CompGS 16K** | 0.836 | 23.39 | 0.200 | **479** | **12** | 15.6 |
| **CompGS 32K** | 0.838 | 23.44 | 0.198 | 475 | 13 | 20.6 |
| **CompGS 32K BitQ** | 0.832 | 23.35 | 0.202 | 475 | **8** | 20.6 |

### Derived (vs. the **reproduced** 3DGS, the fair baseline)

| Comparison | Mip-NeRF 360 | Tanks&Temples |
|---|---|---|
| Compression, 32K | **41×** (778 → 19) | **33×** (433 → 13) |
| Compression, 32K BitQ | **65×** (778 → 12) | **54×** (433 → 8) |
| Rendering | **2.3×** (149 → 344) | **2.3×** (206 → 475) |
| PSNR, 32K | **−0.30 dB** | **−0.24 dB** |
| PSNR, 32K BitQ | −0.45 dB | −0.33 dB |
| Training, 16K | **+5.6%** (21.6 → 22.8) | +28% (12.2 → 15.6) |
| Training, 32K | **+36%** (21.6 → 29.4) | **+69%** (12.2 → 20.6) |

## 8.2 Reading these fairly

✅ **The headline claims are accurate and honestly framed.** "40× to 50× smaller and 2× to 3×
faster" `[paper §1]` matches the 32K rows; the 65× figure is explicitly the BitQ variant.

⚠️ **Training is the acknowledged cost, and the paper says so plainly** `[paper §4]`:
> "A limitation of CompGS compared to 3DGS is the **overhead in compute and training time
> introduced by the K-means clustering algorithm**. This is compensated in part by the reduced
> compute and time due to the decrease in Gaussian count. **CompGS 16K variant requires
> marginally more time than 3DGS while CompGS 32K needs 1.4× to 1.7× more training time.**"

✅ Verified against the table: 32K is 1.36× (M360) and 1.69× (T&T). Correctly stated.

> **Corroborated externally:** `../CompGS/` (Liu) measures this method's **encode time at
> 68.29 s — vs 0.54–2.23 s for four other compression methods** `[CompGS-Liu Tab. 7]`. K-means
> is by far the most expensive quantizer in the lineage, which is precisely what `../OMG/`'s
> Sub-Vector Quantization was designed to fix (**13–18× faster codebook initialisation**
> `[OMG §4.3]`).

⚠️ **The FPS gain is from pruning, not quantization.** Quantization changes *where* parameters
are read from, not how many Gaussians are rasterized. The paper is clear that the count
reduction "comes with a bi-product that is increase in inference speed" `[paper §3]`. If you
cite "2–3× faster", attribute it to the opacity regulariser.

⚠️ **LPIPS degrades most**, as in every compression method here: 0.217 → 0.240–0.245 on
Mip-NeRF 360.

✅ **The `Mem` column is the honest one to use** — it is a real model size, and unlike
`../OMG/` and `../CompGS/` (Liu) there is **no decoder network to account for**. CompGS's stored
artifact is codebooks + indices + unquantized attributes, full stop.

## 8.3 Hardware transferability to your H100 96 GB

| Aspect | Assessment |
|---|---|
| **Reported GPU** | **RTX 6000** — ambiguous between *Quadro RTX 6000* (Turing, 24 GB, 2018) and *RTX 6000 Ada* (2022). Given the paper's late-2023 arXiv v1 and the A6000 footnote, **Quadro RTX 6000 (Turing)** is the more likely reading `[unverified]` |
| **vs your H100** | Two to three generations behind, workstation-class. Expect a substantial but **sub-linear** speedup — 3DGS rasterization is bound by tile sorting, atomics and bandwidth |
| **K-means cost specifically** | This *is* compute-bound (`cdist` over `N × K`), so it **should** scale well to H100 — meaning the 1.4–1.7× training overhead is likely to shrink on your hardware `[inferred]` |
| **VRAM** | ❌ not reported `[unverified]`. But peak memory is 3DGS's densification phase, and the paper notes CompGS "maintains the other advantages of 3DGS such as **low inference memory usage**" `[paper §4]`. Comfortable on 96 GB |
| **Software stack** | Whatever the 3DGS release of late 2023 required (CUDA 11.x era) plus `bitarray` `[repo: README.md]`. ⚠️ **You will need to add `9.0` to `TORCH_CUDA_ARCH_LIST`** and rebuild `diff-gaussian-rasterization` + `simple-knn` for H100 |
| **Dependencies** | ✅ **Only `bitarray`** beyond 3DGS — the lightest footprint of any compression method in your set. No tiny-cuda-nn, no cuML, no G-PCC binary. Compare `../OMG/` (three) and `../CompGS/` (two) |

## 8.4 Complexity claims — asymptotic vs. empirical

| Claim | Type | Verdict |
|---|---|---|
| Indices act "as a pointer to the correct code **freeing the memory needed to replicate those parameters** for all Gaussians" `[paper §1]` | **Structural.** Storage goes from `N·d` floats to `K·d` floats + `N` indices | ✅ True asymptotically (`N ≫ K`: millions vs thousands). Note it also implies an **inference-memory** benefit, not just storage |
| Asymmetric K-means limits training cost `[paper §3]` | **Structural + empirical.** Expensive assignment step runs `1/t` as often | ✅ Confirmed in code `[repo: kmeans_quantize.py:46-61 vs 138-172]`; empirically 1.4–1.7× overhead rather than orders of magnitude |
| "works well even for `t` as high as 500" `[paper §3]` | **Empirical assertion, no supporting table** | ⚠️ `[unverified]`. Both the paper's experiments and `run.sh` use `t = 100` |
| 40–50× compression, 2–3× speedup `[paper §1]` | **Empirical**, single named GPU, baseline re-run | ✅ Verified against Table 1 |
| 65× with BitQ | **Empirical**, post-training | ✅ Explicitly attributed to BitQ |
| RLE "reducing the storage from `n` integers to `k` integers" `[paper §3]` | **Structural claim** | ❌ **Not implemented** — see [`06-implementation-deltas.md`](06-implementation-deltas.md) D-1 |
| Compression is capped by unquantized position/opacity `[paper §3]` | **Empirical, and the paper's most useful negative result** | ✅ >80% of post-quantization memory. **This is what motivated G-PCC position coding in `../OMG/` and `../CompGS/`** |

## 8.5 Cross-method context

| Method | Mip-NeRF 360 size | FPS | Decoder to store? | Extra deps |
|---|---|---|---|---|
| 3DGS | 778 MB | 149 | — | — |
| `../mini-splatting/` | 119.5 MB | (601) | — | forked rasterizer |
| **CompGS 32K** | **19 MB** | **344** | ❌ none | `bitarray` |
| **CompGS 32K BitQ** | **12 MB** | 344 | ❌ none | `bitarray` |
| `../OMG/` XS | 4.06 MB | 350 (612) | ✅ 4 MLPs (counted) | tcnn, cuML, G-PCC |
| `../CompGS/` (Liu) | 8.83–16.50 MB | — | ✅ MLPs + entropy model (counted) | CompressAI, G-PCC |

⚠️ **These figures come from three different papers on three different GPUs** (RTX 6000 /
RTX 3090 / unnamed) and, for `../OMG/`, from baseline numbers sourced from the *LocoGS* paper.
Do not build a table from this without re-measuring.

✅ **`Mem`/`#Gauss` semantics are consistent** between CompGS, `../mini-splatting/` and
`../OMG/` (all report rendered Gaussians and real file sizes). `../CompGS/` (Liu) reports
**anchors**, which are ~10× fewer than rendered primitives.

⚠️ **PSNR convention.** CompGS inherits 3DGS's `metrics.py` unchanged via the file overlay, so
its numbers follow whatever that harness does — the same ambiguity documented for `../OMG/` and
`../EDGS/`. See [`10-reproducibility.md`](10-reproducibility.md) §10.3. Note also that **this
paper is the only one in your set that explicitly identifies the log/Jensen problem with
averaging PSNR** and introduces **PSNR-AM** to address it `[paper §4]`.
