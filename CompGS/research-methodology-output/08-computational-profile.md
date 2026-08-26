# §8 — Computational profile

> ⚠️ `[paper …]` = **arXiv:2404.09458v1** = `../../CompGS.pdf`.

## 8.1 As reported

`[paper Tab. 7]` — Tanks&Templates, all methods re-run by the authors:

| Method | Train (min) | Enc (s) | Dec (s) | Render (ms) |
|---|---|---|---|---|
| Navaneet et al. [33] (= `compact3d/`) | 14.38 | 68.29 | 12.32 | 9.88 |
| Niedermayr et al. [34] | 15.50 | 2.23 | 0.25 | 9.74 |
| Lee et al. [20] | 44.70 | 1.96 | 0.18 | 6.60 |
| Girish et al. [10] | 8.95 | 0.54 | 0.64 | 6.96 |
| **Proposed (CompGS)** | **37.83** | 6.27 | 4.46 | **5.32** |

### Quality / size, all three datasets

`[paper Tabs. 1-3]` — three rows per dataset = λ ∈ {0.001, 0.005, 0.01}:

| Dataset | 3DGS [17] | CompGS (best quality → smallest) | Compression ratio |
|---|---|---|---|
| **Tanks&Templates** | 23.72 / 0.85 / 0.18 / **434.38 MB** | 23.70 / 0.84 / 0.21 / **9.60 MB**<br/>23.39 / 0.83 / 0.22 / 7.27 MB<br/>23.11 / 0.81 / 0.24 / **5.89 MB** | **45.2× – 73.8×** |
| **Deep Blending** | 29.54 / 0.91 / 0.24 / **665.99 MB** | 29.69 / 0.90 / 0.28 / **8.77 MB**<br/>29.40 / 0.90 / 0.29 / 6.82 MB<br/>29.30 / 0.90 / 0.29 / **6.03 MB** | **75.9× – 110.5×** |
| **Mip-NeRF 360** | 27.46 / 0.82 / 0.22 / **788.98 MB** | 27.26 / 0.80 / 0.24 / **16.50 MB**<br/>26.78 / 0.79 / 0.26 / 11.02 MB<br/>26.37 / 0.78 / 0.28 / **8.83 MB** | **47.8× – 89.4×** |

Best single-scene result: *Stump* (Mip-NeRF 360), **1149.30 MB → 6.56 MB = 175.2×**
`[paper §4.2]`.

### Reading these fairly

| Observation | Note |
|---|---|
| **Deep Blending, λ=0.001: +0.15 dB *over* 3DGS at 75.9× smaller** | The paper's explanation is plausible — "potentially attributed to the integration of feature embeddings and neural networks" `[paper §4.2]` — i.e. the MLP decoder acts as a regulariser. This is the strongest headline number in the paper. |
| **Tanks&Templates, λ=0.001: 23.70 vs 23.72 dB** — essentially lossless at 45.2× | ✅ |
| **LPIPS degrades consistently** | T&T 0.18→0.21, DB 0.24→0.28, M360 0.22→0.24 at the *best* operating point. PSNR/SSIM hold up better than LPIPS across all three datasets. Report LPIPS. |
| **Mip-NeRF 360 is the hardest** | −0.20 dB at 47.8×, degrading to −1.09 dB at 89.4×. Unbounded outdoor scenes resist the anchor/coupled structure more than the other two datasets. |
| **CompGS beats every compression baseline on size**, at comparable or better PSNR | Verified across all three tables. The margin over the next-smallest (Niedermayr) is ~2–3×. |

## 8.2 Hardware — **not named anywhere**

`grep -inE "gpu|rtx|a100|v100|nvidia|3090|4090|tesla"` over the full extracted paper text
returns **nothing**. `[paper]` reports training time, encode/decode time and render time
`[paper Tab. 7]` **without stating a device**, and reports **no VRAM at all**.

| Aspect | Assessment |
|---|---|
| **Device** | `[unverified]` — the worst disclosure in the comparison set, alongside `seasplat/`. |
| **Circumstantial evidence** | The repo has Windows-first instructions (`SET DISTUTILS_USE_SDK=1`, `run.bat`, `C:\Users\XiangruiLIU\...` paths in the README example) `[repo: README.md]`, suggesting a Windows workstation rather than a cluster. Suggestive only. |
| **vs your H100 96 GB** | Unknown baseline ⇒ **none of the Table 7 timings transfer**. If you need a training-time comparison, re-measure. |
| **VRAM** | `[unverified]` — never reported. But note the model is *tiny* by construction (anchors, not millions of Gaussians), so memory is unlikely to be a constraint on 96 GB. |
| **Software stack** | Python ≥ 3.10 `[repo: README.md]` — the **most modern stack in your comparison set** and the least likely to fight a CUDA 12 / H100 environment. `torch_scatter` and `einops` are used `[repo: AdaptiveControl.py:4-5]`. |
| **External dependency ⚠️** | **G-PCC (MPEG TMC13) must be downloaded and compiled separately** `[repo: README.md step 4]`, and its absolute path passed via `gpcc_codec_path` in every config. This is a hard blocker: **without it, compression cannot run at all**, since anchor positions are coded by G-PCC `[repo: Model.py:326]`. Budget this. |

## 8.3 Complexity claims — asymptotic vs. empirical

| Claim | Type | Verdict |
|---|---|---|
| Coupled primitives cost far fewer bits than anchors | **Empirical, but structurally grounded and well-supported.** Fig. 8: coupled **6.52–15.36** bits vs anchor **80.65–128.26** — a **~8–12×** ratio at every λ. | ✅ The mechanism (conditional entropy coding on `f̃_ω`) predicts exactly this, and the measurement confirms it. The strongest internal evidence in the paper. |
| Compression ratios of 45×–175× | **Empirical**, against 3DGS `.ply` files. | ✅ Real, and consistent across three datasets. ⚠️ Note the baseline is an **uncompressed** `.ply`; 3DGS `.ply` files are famously wasteful (float32 throughout, 59 floats/Gaussian). A `zip` of the same file is a fairer floor, and no paper in this set reports one. |
| Fastest rendering of all compared methods (5.32 ms) | **Empirical**, unnamed hardware, but **all methods re-run by the authors** `[paper §4.1]` — internally consistent. | ✅ Notable because CompGS pays an **extra MLP decode per view** that the others do not. It still wins because far fewer Gaussians reach the rasterizer (`N` anchors × `K`, minus the `α ≤ 0` cull) `[repo: Prediction.py:65]`. |
| Training time 37.83 min | **Empirical.** 2.6× slower than Navaneet, 4.2× slower than Girish; only Lee (44.70) is slower. | ⚠️ The paper does not comment on this. The cost is the entropy model + second optimizer + per-primitive MLP decode, all running every iteration. |
| **Network weights are a fixed cost** | — | ⚠️ **The most important caveat.** At λ=0.01 the MLPs are **45.98%** of the bitstream `[paper Fig. 8]`. Compression ratio therefore *saturates*: pushing λ higher shrinks scene bits around a constant floor. The paper never discusses this limit, though it does honestly *include* the weights in the reported size `[repo: TrainerCompGS.py:346-348]`. |

### Encode/decode asymmetry worth noting

CompGS: enc **6.27 s**, dec **4.46 s** — both dominated by arithmetic coding plus the
G-PCC subprocess. Compare Navaneet's **68.29 s** encode (K-means fitting is expensive) and
Niedermayr/Lee/Girish at **0.18–0.64 s** decode. CompGS sits in the middle: **~7–25×
slower to decode than the quantization-based methods**, which matters for a streaming or
on-device use case. The paper reports the numbers without comment.

## 8.4 The `num_gaussians` trap, restated for the comparison table

`[repo: TrainerCompGS.py:367]` and `[repo: README.md]`: the reported `num_gaussians` is the
number of **anchor primitives**. The number rasterized is up to `K = 10` times larger.

When you build the cross-method table, either:
- report **anchors** for CompGS and label the column accordingly, **or**
- instrument `[repo: Prediction.py:65]` to log `coupled_primitive_mask.sum()` and report the
  rendered count — which is what every other folder's number means.

Mixing the two understates CompGS's primitive count by up to an order of magnitude.

## 8.5 Cross-method context (as-published, **different/unknown hardware each**)

| Method | Model size (T&T) | Note |
|---|---|---|
| 3DGS | 434.38 MB | uncompressed `.ply` |
| `compact3d/` (Navaneet [33]) | 47.01 MB | K-means VQ |
| Niedermayr [34] | 17.65 MB | sensitivity-aware quantization + entropy coding |
| Lee [20] | 39.47 MB | learnable masks + grid fields |
| Girish [10] | 33.57 MB | latent embeddings |
| **CompGS** | **5.89 – 9.60 MB** | predictive coding + RD optimization |
| `mini-splatting/` (ms_c) | *not compared* | RAHT + zip on an already-simplified model |

⚠️ `mini-splatting/`'s Mini-Splatting-C is a concurrent ECCV 2024 method targeting the same
axis and is **not** in this comparison; conversely CompGS is not in mini-splatting's Fig. 9.
Neither paper measured the other, so any head-to-head you present is your own construction
and must be re-run.
