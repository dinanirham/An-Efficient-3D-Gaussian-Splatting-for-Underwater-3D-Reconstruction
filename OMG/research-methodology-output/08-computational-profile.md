# §8 — Computational profile

## 8.1 As reported

`[paper Tab. 1 caption]`: **"Baseline results are sourced from the LocoGS [53] paper, where the
rendering results were obtained using an NVIDIA RTX 3090 GPU. Our rendering performance was
measured using the same GPU, with the values in parentheses obtained from an NVIDIA RTX
4090 GPU."**

Good disclosure: the GPU is named, OMG re-measured on the *same* card as the baselines, and
the second card is reported separately in parentheses rather than mixed in.

### Mip-NeRF 360 `[paper Tab. 1]`

| Method | PSNR | SSIM | LPIPS | Size (MB) | FPS (3090) |
|---|---|---|---|---|---|
| 3DGS | 27.44 | 0.813 | 0.218 | 822.6 | 127 |
| Scaffold-GS | 27.66 | 0.812 | 0.223 | 187.3 | 122 |
| **Mini-Splatting** (base method) | **27.39** | **0.822** | **0.216** | 119.5 | (601) |
| CompGS † | 27.04 | 0.804 | 0.243 | 22.93 | 236 |
| Compact-3DGS | 26.95 | 0.797 | 0.244 | 26.31 | 143 |
| LightGaussian | 26.90 | 0.800 | 0.240 | 53.96 | 244 |
| HAC | 27.49 | 0.807 | 0.236 | 16.95 | **110** |
| LocoGS-S | 27.04 | 0.806 | 0.232 | 7.90 | 310 |
| LocoGS-L | 27.33 | 0.814 | 0.219 | 13.89 | 270 |
| **OMG-XS** | 27.06 | 0.807 | 0.243 | **4.06** | **350 (612)** |
| **OMG-M** | 27.21 | 0.814 | 0.229 | 5.31 | 298 (511) |
| **OMG-XL** | 27.34 | 0.819 | 0.218 | 6.82 | 251 (416) |

† "CompGS [44]" here is **Navaneet et al. = `../compact3d/`**, not Liu et al. = `../CompGS/`
`[inferred]` — ref [44] is also cited for opacity regularization and VQ `[paper §2.2]`.

### Tanks&Temples / Deep Blending `[paper Tab. 2]`

| Method | T&T: PSNR / Size / FPS | DB: PSNR / Size / FPS |
|---|---|---|
| 3DGS | 23.67 / 452.4 / 175 | 29.48 / 692.5 / 134 |
| Mini-Splatting | 23.41 / 67.6 / (1095) | 30.04 / 124.9 / (902) |
| LocoGS-S | 23.63 / 6.59 / 333 | 30.06 / 7.64 / 334 |
| **OMG-M** | 23.52 / **3.22** / **555 (887)** | 29.77 / **4.34** / **524 (894)** |
| **OMG-L** | 23.60 / 3.93 / 478 (770) | 29.88 / 5.21 / 479 (810) |

### Efficiency across the variant family `[paper Tab. 3]`

| Method | Training | #Gauss | Size | PSNR |
|---|---|---|---|---|
| Mini-Splatting | 19m 25s | 531 K | 119.5 | 27.39 |
| LocoGS-S | **1h** | 1.09 M | 7.90 | 27.04 |
| LocoGS-L | **1h** | 1.32 M | 13.89 | 27.33 |
| OMG-XS | **20m 15s** | 427 K | 4.06 | 27.06 |
| OMG-M | 21m 10s | 563 K | 5.31 | 27.21 |
| OMG-XL | 22m 26s | 727 K | 6.82 | 27.34 |

### Derived

| Comparison | Result |
|---|---|
| OMG-XS vs 3DGS | **203× smaller**, **2.8× faster**, −0.38 dB |
| OMG-XS vs Mini-Splatting (its base) | **29× smaller**, 20% fewer Gaussians, −0.33 dB, **0.6× FPS** |
| OMG-XL vs LocoGS-L | **2.0× smaller**, **0.9× FPS**, **+0.01 dB, +0.005 SSIM, −0.001 LPIPS** |
| OMG-XS vs LocoGS-S | **1.9× smaller**, **1.13× FPS**, +0.02 dB (LPIPS worse: 0.243 vs 0.232) |
| Training vs LocoGS | **~3× faster** (20 min vs 1 h) |
| OMG adds over Mini-Splatting | **+50 s to +3 min** training (19m25s → 20m15s–22m26s) |

## 8.2 Reading these fairly

⚠️ **OMG never beats its own base method on quality.** Mini-Splatting: 27.39 / 0.822 / 0.216;
OMG-XL: 27.34 / 0.819 / 0.218. The honest framing is **−0.05 dB for 17.5× smaller storage** —
excellent, and *not* "better than Mini-Splatting". The paper is careful about this, comparing
"among compression methods" `[paper Tab. 1 caption]`.

⚠️ **Mini-Splatting is faster.** 601 FPS vs OMG-XS's 612 on a 4090 — but on the *3090* column
Mini-Splatting has no entry, and on T&T/DB Mini-Splatting reaches **1095 / 902 FPS** versus
OMG's **887 / 894**. Despite having ~20% *more* Gaussians, Mini-Splatting renders faster
because OMG pays a **per-frame MLP decode** for appearance. Fewer primitives does not
automatically mean faster here.

✅ **The real claim, and it holds:** among *compression* methods OMG is simultaneously the
smallest **and** among the fastest. HAC reaches 16.95 MB at 110 FPS; OMG-XS reaches 4.06 MB at
350 FPS — **4× smaller and 3.2× faster**. The paper's explanation is structural: anchor-based
methods "require **per-view processing, involving multiple MLP forward passes**"
`[paper §2.2]`, whereas OMG's MLPs are per-Gaussian and tiny.

⚠️ **LPIPS is OMG's weakest metric.** OMG-XS 0.243 vs LocoGS-S 0.232 at half the size; only
OMG-XL matches Mini-Splatting's 0.218. Consistent with heavy pruning removing fine detail that
PSNR forgives.

## 8.3 Hardware transferability to your H100 96 GB

| Aspect | Assessment |
|---|---|
| **Reported GPUs** | **RTX 3090** (24 GB, SM 8.6, Ampere consumer) and **RTX 4090** (24 GB, SM 8.9, Ada consumer) — both named, with baselines re-measured on the 3090 |
| **vs your H100** | Consumer-class, one to two generations behind. Same situation as `../mini-splatting/` (3090). Expect a real but **sub-linear** speedup: 3DGS rasterization is bound by tile sorting, atomics and memory bandwidth, not tensor cores |
| **Useful scaling datapoint** | The 3090→4090 ratios in Table 1 (**350→612**, **298→511**, **251→416** FPS ≈ **1.7×**) give an empirical sense of how this workload scales with newer hardware `[inferred]` |
| **VRAM** | ❌ **not reported** `[unverified]`. But peak memory is at Mini-Splatting's densification stage (`num_max = 4.5 M` Gaussians `[repo: arguments/__init__.py:92]`), which fits comfortably on 24 GB — so 96 GB is far more than needed |
| **Software stack** | CUDA 12.1, Python 3.11, torch 2.5.1 `[repo: README.md]` — **modern and H100-compatible**, much better than `../mini-splatting/` (Py 3.7 / CUDA 11.6) |
| ⚠️ **Three hard dependencies** | **tiny-cuda-nn** (all four MLPs), **cuML/RAPIDS** (K-means for SVQ — the README links the install guide and acknowledges trouble), and **TMC13/G-PCC**, which must be compiled separately with its path **hard-coded at `utils/gpcc_utils.py` lines 243, 258** `[repo: README.md]`. Without G-PCC, positions cannot be encoded and no size figure is reproducible |

## 8.4 Complexity claims — asymptotic vs. empirical

| Claim | Type | Verdict |
|---|---|---|
| SVQ reduces codebook computation vs VQ | **Structural, and quantified.** VQ needs `2¹⁴` entries per attribute; SVQ uses 64/512/1024 per partition `[repo: arguments/__init__.py:100-105]` | ✅ `[paper Tab. 5]`: VQ incurs a **13–18× increase in codebook initialization time**. K-means over a 1024-entry codebook on a 3-vector is genuinely cheap |
| SVQ avoids R-VQ's index overhead | **Structural.** One index per sub-vector vs one per residual stage | ✅ Argued in `[paper §3.2]`; R-VQ measured worse on rate–distortion `[paper Tab. 5]` |
| "absence of a large neural field" gives efficiency `[paper §4.2]` | **Empirical**, and structurally grounded | ✅ Four MLPs at 64×1 `[repo: gaussian_model.py:672-720]` vs LocoGS's larger field. Training 20 min vs 1 h |
| Fewer Gaussians ⇒ faster rendering | **Asymptotic in `N`**, but **confounded here** | ⚠️ OMG has ~20% fewer Gaussians than Mini-Splatting yet renders **slower** (887 vs 1095 FPS on T&T). The per-frame MLP decode eats the gain. The paper does not discuss this |
| "600+ FPS rendering" `[paper Fig. 1]` | **Empirical**, and it is the **4090** number for OMG-XS (612) | ⚠️ On the 3090 it is **350**. The abstract's "600+ FPS" and "under 5 MB" are both best-case, from different columns of the same table. Quote the card |
| ~50% storage reduction vs previous SotA `[paper Abstract, §4.2]` | **Empirical.** OMG-XS 4.06 vs LocoGS-S 7.90 MB | ✅ Accurate (1.95×), at comparable PSNR/SSIM but **worse LPIPS** |
| Training-time overhead over Mini-Splatting | **Empirical** | ✅ **+50 s to +3 min** on a 19m25s baseline — genuinely minimal, which validates the "K-means in seconds" claim `[paper §3.2]` |

## 8.5 Cross-method context

⚠️ **`#Gauss` is comparable here** — OMG reports rendered Gaussians, as do
`../mini-splatting/` and `../compact3d/`. It is **not** comparable to `../CompGS/`, which
reports **anchors** (up to 10× fewer than rendered). See
`../CompGS/research-methodology-output/08-computational-profile.md` §8.4.

⚠️ **`Size` accounting is honest and includes the decoder.** `[repo: train.py:119-123]` reports
`os.path.getsize("comp.xz")` with a per-component breakdown that explicitly lists **`MLPs`**.
Same practice as `../CompGS/`. Verify that `../compact3d/`'s codebook and
`../mini-splatting/`'s `ms_c` figures are on the same footing before tabulating.

⚠️ **PSNR convention — subtler than it looks.** OMG inherits Mini-Splatting's
`utils/image_utils.py:17-19`, which is written for `(3,H,W)` input and would then give the 3DGS
**per-channel-mean** PSNR. But the reported numbers come from `metrics.py`, which loads images
as `(1,3,H,W)` `[repo: metrics.py:31-32]`, so `.view(img1.shape[0], -1)` pools **all** channels
⇒ **pooled-MSE PSNR**. Exactly the same call-site subtlety documented in
`../EDGS/research-methodology-output/10-reproducibility.md` §10.3a. Resolve this before
tabulating against `../seasplat/` or `../compact3d/`. See
[`10-reproducibility.md`](10-reproducibility.md).
