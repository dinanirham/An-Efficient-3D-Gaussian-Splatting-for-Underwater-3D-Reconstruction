# Paper-vs-repo disagreements — OMG

**Paper:** `../../OMG.pdf` = arXiv:2503.16924**v2** (6 Nov 2025), NeurIPS 2025.
**Repo:** `maincold2/OMG` @ **`6edeb72`** (2025-03-24) — **~7 months older** than the paper
revision. 🔶 marks deltas plausibly explained by that gap.

> **Overall assessment:** OMG's paper is *architecturally faithful* — every equation I could
> check maps onto real code, and the SVQ / space-feature / LD-scoring designs are implemented
> as described. Its weakness is **under-specification**: essentially every constant lives only
> in the repository. Two genuine behavioural surprises (D-1, D-2) sit on top of that.

| # | Topic | Paper says | Repo does | Tags | Severity |
|---|---|---|---|---|---|
| D-1 | ⭐ **`N_i^K` neighbourhood** | Eq. 8 sums over "the set of **K-nearest neighbors**", approximated by Morton-order adjacency `[§3.3]` | **exactly 2** neighbours — `clamp(order−1)` and `clamp(order+1)`. `K` is not a parameter, not exposed, never swept | `[paper Eq. 8, §3.3]` vs `[repo: gaussian_model.py:653-655, 663]` | **medium** |
| D-2 | ⭐ **Codebook "fine-tuning"** | "after initializing with K-means, we freeze the indices and **finetune only the codebook using the rendering loss**" `[§3.2]` | `Adam(code_params, lr=**1e-8**)` for 1000 steps ⇒ each codeword moves ~1e-5. **Effectively frozen at the K-means init** | `[paper §3.2]` vs `[repo: gaussian_model.py:818; train.py:191-192]` | **medium** 🔶 |
| D-3 | **SVQ applied to scale** | "We apply SVQ to geometric attributes `s_n`, `r_n`" `[§3.2]` | `slice_scale = **1**` ⇒ one codebook over the whole 3-vector = **plain VQ**, not SVQ. Only rotation (M=2) and appearance (M=2) are genuinely partitioned | `[paper §3.2]` vs `[repo: arguments/__init__.py:100-101]` | low–medium |
| D-4 | **Every constant** | `D`, `λ`, space-feature dim, `n_frequencies`, MLP width/depth/activations, MLP optimizer, `net_itr`, all six SVQ constants, K-means settings — **none stated** | `D=3`, `λ=2.0`, 13, 16, 64×1, Adam(0.01)+chained scheduler, 15 000, (1,2⁶)/(2,2⁹)/(2,2¹⁰), cuML `max_iter=1000, n_init=1` | — vs `[repo: arguments/__init__.py:96-105; gaussian_model.py:672-751, 842-855]` | **high** for reproduction |
| D-5 | **Mini-Splatting inheritance** | cited only for "the blur split technique" `[§4.2]` and as the base implementation `[§4.1]` | the **entire** parameter block and `intersection_preserving` verbatim — so OMG silently inherits MS's undocumented mechanisms: **no `reset_opacity()`**, **`(1−α_accum)`-weighted** depth-reinit sampling, **LR-schedule rewind** at 15 000 | `[paper §4.1-4.2]` vs `[repo: arguments/__init__.py:89-95; gaussian_model.py:627-650; train.py:73-77]` | **medium** |
| D-6 | **What `res_color` compares** | "the similarity of the **static appearance feature** `T`" `[§3.3]` ✅ consistent | `T` is a **learned 3-D latent** (initialised from DC colour, then trained). Since `net_itr (15 000) < simp_iteration2 (20 000)`, the `T` branch always runs. The variable name `res_color` invites reading it as colour | `[paper §3.3]` vs `[repo: gaussian_model.py:657-663]` | low (clarifying) |
| D-7 | **`λ`'s role in Eq. 8** | rendered ambiguously in the PDF text layer; described as "a **scaling factor** that adjusts the sensitivity to appearance variation" `[§3.3]` | `imp_score * res_color ** lambda_ld` — an **exponent**. (A pure multiplier would cancel out of a CDF threshold entirely, so the exponent reading is almost certainly what Eq. 8 means) | `[paper Eq. 8]` vs `[repo: gaussian_model.py:665]` — `[unverified]`, **check Eq. 8 visually** | low |
| D-8 | **Default variant** | XS–XL ladder documented `[§4.1]` | config ships **`importance_thresh = 0.96`** = XS only; a bare `python train.py` reproduces only the smallest variant. (The README does document the ladder) | `[paper §4.1]` vs `[repo: arguments/__init__.py:98; README.md]` | low, high trap value |
| D-9 | **External dependencies** | not mentioned | **tiny-cuda-nn**, **cuML/RAPIDS**, and **TMC13/G-PCC** with its path **hard-coded at `utils/gpcc_utils.py` lines 243/258**; the G-PCC wrapper is itself borrowed from **HAC++** | — vs `[repo: README.md]` | **medium** for reproduction |
| D-10 | **`Ī_i`'s scene-type branch** | Eq. 7 gives **one** formula, `Ī_i = Σ_ρ w_{i,ρ}` | `--imp_metric` is a **required** CLI arg; `outdoor` uses `accum_weights / area_proj`, `indoor` uses `accum_weights`. Inherited from Mini-Splatting, whose own paper calls this "case-dependent and hand-crafted … an experimental trick" | `[paper Eq. 7]` vs `[repo: gaussian_model.py:641-646; README.md]` | **medium** |
| D-11 | **PSNR convention** | "PSNR, SSIM, LPIPS" | `metrics.py` loads `(1,3,H,W)` `[metrics.py:31-32]`, so 3DGS's `psnr()` — written for `(3,H,W)` — pools all channels ⇒ **pooled-MSE PSNR**, not the per-channel-mean convention the function implements. **Same call-site subtlety as `../EDGS/`** | `[paper §4.1]` vs `[repo: metrics.py:29-32; utils/image_utils.py:17-19]` | **medium** |

## ✅ Verified-correct

| Paper claim | Code |
|---|---|
| Built on Mini-Splatting `[§4.1]` | parameter block + `intersection_preserving` verbatim ✅ |
| `Ī_i` = blending weight gated by argmax-contribution `[Eq. 7]` | `imp_score[accum_area_max == 0] = 0` `[gm:648]` ✅ |
| Morton-order neighbour approximation `[§3.3]` | `sort_morton()`, 21-bit quantize → Morton → argsort `[gm:752-760]` ✅ |
| CDF thresholding with τ `[§3.3]` | `init_cdf_mask(importance, thres=τ)` `[gm:666]` ✅ |
| τ = 0.96/0.98/0.99/0.999/0.9999 for XS–XL `[§4.1]` | `[arguments:98; README.md]` ✅ |
| `h^(0) = MLP_t(cat(T,F))`, `o = MLP_o(cat(T,F))`, `h^(1,2,3) = MLP_v(cat(V,F))` `[Eqs. 3-4]` | `n_input_dims = 16 = 3 + 13` on all three `[gm:687-720]` ✅ |
| `F_n = MLP_s(γ(p_n))` `[Eq. 4]` | `tcnn.NetworkWithInputEncoding`, Frequency encoding `[gm:672-686]` ✅ |
| **Geometry stays per-Gaussian** `[§3.1]` | `_scaling`, `_rotation` are ordinary parameters ✅ |
| SVQ = partition + independent codebooks `[Eqs. 5-6]` | `kmeans(..., svq_len, n_clusters)` per partition `[gm:842-855]` ✅ |
| SVQ on `s`, `r`, `cat(T,V)` `[§3.2]` | `[gm:814-816]` ✅ |
| K-means init, indices frozen, **final 1K iterations** `[§3.2]` | `svq_itr = 29 000` of 30 000 `[arguments:96; train.py:88-89]` ✅ |
| "K-means initialization is completed within seconds" `[§3.2]` | corroborated by Tab. 3: **+50 s to +3 min** total over Mini-Splatting ✅ |
| Post-processing: 16-bit + G-PCC, Huffman, LZMA `[§4.1]` | `[train.py:116-124; gm:857-864]` ✅ |
| **MLPs counted in the reported size** | `byte = {..., 'MLPs': 0}`; size = `getsize("comp.xz")` `[train.py:119-123]` ✅ honest |
| Loss unchanged from 3DGS | `0.8·L₁ + 0.2·(1−SSIM)` `[train.py:100-102]` ✅ |

## Claims that need a caveat when cited

| Claim | Caveat |
|---|---|
| "nearly a 50% reduction in storage compared to … LocoGS, **while retaining PSNR and SSIM**" `[§4.2]` | ✅ Accurate (4.06 vs 7.90 MB, 27.06 vs 27.04 dB) — but **LPIPS is worse** (0.243 vs 0.232). PSNR and SSIM are named deliberately. |
| "600+ FPS rendering" and "under 5 MB" `[Abstract, Fig. 1]` | Both best-case, and **600+ FPS is the RTX 4090** figure. On the 3090 OMG-XS is **350 FPS**. Quote the card. |
| OMG "outperforms" the state of the art | ✅ among **compression** methods. ⚠️ **It never beats its own base method**: Mini-Splatting 27.39 / 0.822 / 0.216 vs OMG-XL 27.34 / 0.819 / 0.218. The honest framing is **−0.05 dB for 17.5× smaller**. |
| Fewer Gaussians ⇒ faster rendering | ⚠️ **Not against Mini-Splatting.** OMG has ~20% fewer Gaussians yet renders **slower** on T&T (887 vs 1095 FPS) — the per-frame MLP decode costs more than the primitive reduction saves. Not discussed in the paper. |
| Table 4's ablation | ✅ **A genuine leave-one-out table** — the cleanest structure in your comparison set. Rows 2–3 remove one component each, row 4 removes both, row 5 removes SVQ. The orthogonality claim checks out arithmetically on XS (−0.23 + −0.21 ≈ −0.54). |
| "w/o SVQ" row | ⚠️ Shows quality **improving** (27.26 vs 27.21 on M) at ~5× the size. SVQ is a **rate** win costing ≤0.05 dB — not a quality contribution. |
| Keeping geometry per-Gaussian `[§3.1]` | ⚠️ **Never ablated.** The paper's sharpest architectural claim rests on the sparsity argument plus OMG's overall win over LocoGS — which confounds it with LD scoring, SVQ and the smaller Gaussian count. |
| Baseline numbers in Tables 1–2 | **"sourced from the LocoGS paper"** `[Tab. 1 caption]` — not re-run. Only OMG's **FPS** was re-measured on the same 3090. |
| VKITTI-style claims about SVQ vs VQ/R-VQ `[Tab. 5]` | Directional claims quoted verbatim; **numeric cells did not survive text extraction** `[unverified]`. |

## Unverifiable in this pass

| Claim | Why |
|---|---|
| Supplementary "further implementation details" `[§4.1]` | `[unverified]` — not in the local PDF; may document the D-4 constants |
| Table 5 numeric values (SVQ vs VQ vs R-VQ) | `[unverified]` — cells lost in text extraction |
| Figure 5 values (LD scoring without attribute compression) | `[unverified]` — published as a plot |
| Whether "CompGS [44]" in Tabs. 1–2 is `../compact3d/` | `[inferred]` from ref [44] also being cited for opacity regularization and VQ `[§2.2]`; not confirmed against the bibliography |
| Eq. 8's exact rendering of `λ` | `[unverified]` — check the PDF visually (D-7) |
| Mip-NeRF 360 scene subset | "Following the previous works" `[§4.1]` — not enumerated `[unverified]` |
| `init_cdf_mask`, `utils/compress_utils.py`, `utils/gpcc_utils.py` internals | `[unverified]` — not read in depth |
| LPIPS backbone | `[unverified]` — vendored `lpipsPyTorch`; `net_type` not traced |
| VRAM | `[unverified]` — never reported |
| Whether commit `6edeb72` reproduces the arXiv-v2 numbers | `[unverified]` — commit is ~7 months older 🔶 |
