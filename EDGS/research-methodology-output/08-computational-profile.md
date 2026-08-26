# §8 — Computational profile

## 8.1 As reported

`[paper §4.1]`: **"All experiments were run on NVIDIA A100 GPUs, with competing methods
re-evaluated on the same hardware for fairness."**

That single sentence makes EDGS's timings **the most defensible in your comparison set** —
named hardware *and* baselines re-run on it. `[paper Tab. 1]` also footnotes which rows are
exceptions: `‡ results reported for an NVIDIA A6000`, `♦ results for an NVIDIA RTX 3090`,
`† results taken directly from the paper`.

Crucially: **"Reported training times for our approach include both initialization and
optimization, whereas for other methods (except Rain-GS) only the optimization time is
counted."** `[paper Tab. 1 caption]` — EDGS handicaps itself. Good practice; state it when
citing.

### Table 1 — full convergence (30 000 steps)

| Dataset | Method | SSIM | PSNR | LPIPS | Train | #G (10⁶) |
|---|---|---|---|---|---|---|
| **Tanks&Temples** | 3DGS | 0.841 | 23.14 | 0.183 | 27 m | 2.0 |
| | 3DGS* (retrained) | 0.853 | 23.76 | 0.169 | 19 m | 1.6 |
| | **EDGS + 3DGS** | **0.868** | **24.28** | **0.132** | 23 m | **1.4** |
| **Mip-NeRF 360** | 3DGS | 0.815 | 27.21 | 0.214 | 42 m | 3.5 |
| | 3DGS* | 0.816 | 27.49 | 0.215 | 26 m | 2.8 |
| | 3DGS-MCMC [32] | **0.842** | **28.15** | 0.176 | 20 m | 3.2 |
| | **EDGS + 3DGS** | 0.839 | 28.02 | **0.141** | 27 m | **1.9** |
| **Deep Blending** | 3DGS | 0.903 | 29.41 | 0.243 | 36 m | 3.2 |
| | 3DGS* | 0.908 | 29.77 | 0.242 | 27 m | 2.6 |
| | ScaffoldGS [44] | 0.907 | **30.25** | 0.245 | 28 m | 4.0 |
| | **EDGS + 3DGS** | 0.904 | 29.81 | **0.223** | 30 m | **1.6** |

**The consistent story is LPIPS and Gaussian count, not PSNR.**

| Metric | vs 3DGS* (the strong baseline) |
|---|---|
| LPIPS | **−22%** (T&T 0.169→0.132), **−34%** (M360 0.215→0.141), **−8%** (DB 0.242→0.223) |
| Gaussian count | **−13%**, **−32%**, **−38%** |
| PSNR | +0.52, +0.53, +0.04 dB |
| Train time | **+21%**, **+4%**, **+11%** — *including* initialization |

⚠️ **EDGS does not win PSNR on two of three datasets** (3DGS-MCMC leads on Mip-NeRF 360 by
0.13 dB; ScaffoldGS on Deep Blending by 0.44 dB), and the paper says so plainly: "our model
achieves the **best or second-best** results across all three metrics" `[paper §4.3]`. The
LPIPS margin is the robust claim.

### Table 2 — early stopping (Mip-NeRF 360)

| Method | SSIM | PSNR | LPIPS | Train | #G |
|---|---|---|---|---|---|
| gsplat [84] | 0.818 | 27.51 | 0.215 | 18 m | 3.1 |
| 3DGS+3DGS-LM [25] | 0.813 | 27.39 | 0.221 | 16 m | 2.8 |
| EAGLES [19] | 0.809 | 27.20 | 0.232 | 16 m | 1.3 |
| Taming 3DGS [46] | 0.820 | **27.71** | 0.207 | 14 m | 3.2 |
| MiniSplatting [15] | 0.820 | 27.25 | 0.217 | 12 m | **0.5** |
| **EDGS + 3DGS 10K** | **0.834** | 27.54 | **0.154** | 12 m | 2.1 |
| **EDGS + 3DGS 5K** | 0.825 | 26.88 | 0.166 | **8 m** | 2.6 |

- At **12 min**, EDGS-10K matches MiniSplatting's wall clock with **29% lower LPIPS**
  (0.154 vs 0.217) — but **4× more Gaussians** (2.1 M vs 0.5 M). Different axes; both
  numbers belong in your table.
- At **8 min**, EDGS-5K beats every competitor on SSIM and LPIPS while **losing on PSNR**
  (26.88, the lowest in the table). The paper is accurate: "it outperforms all competing
  methods on **two of the three** standard metrics" `[paper Tab. 2 caption]`.
- Fig. 1's headline "**35% lower LPIPS**" and "reaches original 3DGS quality in **15% of
  training time**" are LPIPS-based claims.

## 8.2 Hardware — A100, and the best software story in the set

| Aspect | Assessment |
|---|---|
| **Device** | **NVIDIA A100**, explicitly named, with competitors re-run on it `[paper §4.1]`. Only `seathru_NeRF/` matches this level of disclosure; `seasplat/` and `CompGS/` name nothing. |
| **vs your H100 96 GB** | Closest match in the set alongside `seathru_NeRF/` — same datacentre class, one generation apart. Timings should transfer *directionally*. |
| **VRAM** | ❌ **not reported** `[unverified]`. Note the initialization holds up to `180 × 15 000 = 2.7 M` candidate Gaussians (3.6 M at the README's 20 000) plus RoMa's activations, so **peak memory is at initialization, not training**. On 96 GB this is comfortable; on a 24 GB card it may not be. `[inferred]` |
| **Software stack** | **CUDA 12.1, Python 3.10, current PyTorch** `[repo: install.sh]` — the most modern in your comparison set and the least likely to fight an H100. Compare `mini-splatting/` (Python 3.7 / CUDA 11.6) and `seathru_NeRF/` (JAX 0.4.1 / CUDA 11). |
| **Extra dependency** | **RoMa weights** are downloaded at first use `[repo: corr_init.py:533-537]`. Needs network access on the cluster, or pre-staged weights. |
| **Two CUDA extensions** | `diff-gaussian-rasterization` and `simple-knn`, built from the vendored 3DGS submodule `[repo: install.sh]`. Standard; needs `TORCH_CUDA_ARCH_LIST` to include `9.0` for H100. |

## 8.3 The cost EDGS pays, and where

The initialization is not free, and the paper handles this correctly by folding it into the
reported training time. Its cost structure:

| Component | Scaling | Note |
|---|---|---|
| RoMa forward passes | `num_refs × nns_per_ref` = **180 × 3 = 540** pairs | the dominant cost; each is a full dense-matching forward |
| Triangulation | `540 × M` least-squares solves, batched | `torch.linalg.lstsq` on GPU `[repo: corr_init.py:471-472]` |
| Memory | up to `num_refs × matches_per_ref` Gaussians before pruning | peak of the whole run `[inferred]` |

Two knobs the paper documents as saturating `[paper Fig. 6]` — reference count, neighbour
count, and matches per reference — are therefore also the cost/quality dial. And note
`nns_per_ref = 1` switches to a **different, faster code path**
(`init_gaussians_with_corr_fast`) `[repo: trainer.py:230-233]`.

> **A hidden budget item:** the training loop **evaluates on the full test set frequently** —
> every 500 steps up to 3000, then every 1000 `[repo: trainer.py:97-99]` — and each
> evaluation runs **VGG-LPIPS** on every test image `[repo: trainer.py:53, 125]`. That is
> real wall-clock inside the reported time. The `Timer` class does pause during logging
> `[repo: trainer.py:86, 101, 168, 177]`, so evaluation is likely excluded from the reported
> figure — but `evaluate()` itself is called *outside* a `timer.pause()` block at
> `[repo: trainer.py:93-99]`, within the paused region. `[inferred; worth confirming if you
> benchmark]`

## 8.4 Complexity claims — asymptotic vs. empirical

| Claim | Type | Verdict |
|---|---|---|
| "removes the need for densification" `[paper Abstract]` | **Structural, and demonstrated.** | ✅ Table 4 is the clean test: 3DGS loses **1.89 dB** without densification; EDGS gains **0.06 dB** with it. The asymmetry is large and unambiguous. |
| "reaches original 3DGS LPIPS in 25% of training time / 15% (Fig. 1)" | **Empirical**, A100, all methods re-run. | ✅ Defensible. ⚠️ The README says **25%**, Fig. 1 says **15%** — different reference points (3DGS vs 3DGS\*, presumably). Quote the source you used. |
| "uses only 60% of the splats" `[repo: README.md]` | **Empirical.** | ✅ Consistent with Tab. 1 (1.9/2.8 = 68% on M360, 1.6/2.6 = 62% on DB, 1.4/1.6 = 88% on T&T). "60%" is the best case, not the average. |
| "35% lower LPIPS" `[paper Fig. 1]` | **Empirical, LPIPS-specific.** | ✅ M360: 0.215→0.141 is −34%. Accurate. But it is **not** a PSNR claim — EDGS is second-best on PSNR on two datasets. |
| Shorter optimization paths | **Empirical and directly measured** — the mechanism itself, not a proxy. | ✅ ~50× less displacement, ~30× shorter coordinate trajectory `[paper §4.5, Eqs. 14-15]`. The strongest mechanistic evidence in the paper. |
| Compatible with other methods | **Empirical, 3 methods, no retuning.** | ✅ Table 3: +0.12 / +0.14 / +0.36 dB, "without increasing final Gaussian count or increasing training time". Strong. ⚠️ Uses a *different* `init_wC` than Table 1 `[paper §4.3]`. |
| Saturation in all three init parameters | **Empirical**, published only as a plot. | ⚠️ `[unverified]` for exact values. |
| No asymptotic complexity claim is made | — | ✅ Correctly so. The initialization is `O(num_refs × nns × H·W)` — independent of the iteration count, which is the actual point. |

## 8.5 Cross-method context

⚠️ **Table 1's `#G` column is not comparable across all rows**, and the paper flags it:
`⋄ for ScaffoldGS denotes the number of splats produced by anchors` `[paper Tab. 1]`. That
is precisely the trap identified in `../CompGS/research-methodology-output/08-computational-profile.md`
§8.4 — CompGS reports **anchors**, ScaffoldGS here reports **derived splats**. When you build
the master table, normalise on *rendered* primitives and say so.

`mini-splatting/` (as "MiniSplatting [15]") is the one method here that beats EDGS on
Gaussian count by a wide margin (0.5 M vs 2.1 M at equal wall clock), while EDGS wins
decisively on LPIPS. They optimise different objectives and are the natural pair to
contrast — and, per [`01-taxonomy.md`](01-taxonomy.md), they are also the natural pair to
*combine*.
