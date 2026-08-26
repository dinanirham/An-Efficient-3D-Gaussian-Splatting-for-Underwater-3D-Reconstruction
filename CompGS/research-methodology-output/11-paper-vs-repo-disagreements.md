# Paper-vs-repo disagreements — CompGS (Liu et al.)

**Paper:** `../../CompGS.pdf` = arXiv:2404.09458**v1** (15 Apr 2024).
**Repo:** `LiuXiangrui/CompGS` @ **`d501617`** (7 Nov 2024).

🔶 = a delta that could plausibly be arXiv-v1-vs-ACM-MM-camera-ready drift (the camera-ready
was not obtainable). Undocumented *code machinery* is marked without 🔶, since a
camera-ready would normally add such detail, not remove it.

## Zeroth-order finding — the acronym collision (PDF now corrected)

| Item | Detail |
|---|---|
| What this folder is | `github.com/LiuXiangrui/CompGS` (confirmed via `git remote -v`) → *CompGS: Efficient 3D Scene Representation via Compressed Gaussian Splatting* (Liu et al., ACM MM 2024) |
| The other "CompGS" | arXiv:2311.18159, *CompGS: Smaller and Faster Gaussian Splatting with Vector Quantization* (Navaneet et al., UC Davis, ECCV 2024) = the `../../compact3d/` folder |
| Irony | that other work is **a baseline in this work's own tables** — `Navaneet et al. [33]` in Tables 1–3, 7 and Figs. 6–7 |
| ⚠️ Historical note | until 2026-08-25, `../../CompGS.pdf` was a **byte-identical copy of `../../compact3d.pdf`** (`md5 = d38c06cf…`), i.e. the wrong paper. It has since been **replaced** with arXiv:2404.09458v1, verified byte-identical (`md5 = 89f5638d…`) to `arxiv.org/pdf/2404.09458v1`. Findings below were originally derived against a fetched copy and re-verified against the current local file |
| Version caveat | the repo's BibTeX cites **ACM MM 2024**; only **arXiv v1** (Apr 2024) is available, 7 months older than the commit |

## Disagreement table

| # | Topic | Paper says | Repo does | Tags | Severity |
|---|---|---|---|---|---|
| D-1 | **Geometry prediction** | Eqs. 2-4: an affine transform `𝒜` with **three** networks `𝒯, 𝒮, ℛ` giving `t_k`, `S_k`, `R_k`; `μ_k = μ_ω + t_k`, `Σ_k = S_k R_k` | **two** MLPs (`means`→3ch, `covariance`→7ch); **both** the offset and the scale are modulated by the anchor's own learned 6-D scaling vector `exp(Σ_ω)`; scale is `sigmoid`-bounded. This is Scaffold-GS offset prediction. Also `Σ_k = S_k R_k` is not a valid covariance factorisation | `[paper Eqs. 2-4]` vs `[repo: Prediction.py:24-25, 49-50, 69, 76-78]` | **high** 🔶 |
| D-2 | **Loss terms** | Eq. 1: `L = λR + D` — **two** terms | **three**: `L = D + 0.01·mean(∏scales) + λR`. The volume regulariser is hard-coded, has no config key, is never ablated, and is never mentioned | `[paper Eq. 1]` vs `[repo: TrainerCompGS.py:220, 229]` | **high** |
| D-3 | **Optimizers** | §3.4: "Adam optimizer [18] is used to optimize parameters" — one | **two** Adams and **two** backward passes: `loss.backward()` and `aux_loss.backward()`, the latter fitting the CompressAI entropy-bottleneck CDF | `[paper §3.4]` vs `[repo: TrainerCompGS.py:184, 235-236, 299-300]` | **high** |
| D-4 | **Rate warm-up** | Eq. 1 presents a single objective active throughout | `rate_loss` is added **only when `iteration > 3000`** — a 10% warm-up with zero rate pressure. Given that `R → 0` (a constant scene) is a global optimum of the rate term, this is plausibly load-bearing | `[paper Eq. 1]` vs `[repo: TrainerCompGS.py:229; Configs/*.yaml]` | **high** |
| D-5 | **MLP depth** | §3.4: "implemented by **two** residual multi-layer perceptrons" | `num_res_layer=1` for means, covariance and opacity; `=2` only for colour and for the scale entropy model's `h_s` | `[paper §3.4]` vs `[repo: Prediction.py:24-29; EntropyModel.py:230]` | low–medium 🔶 |
| D-6 | **Anchor positions** | §3.4: anchors "are initialized from sparse point clouds produced by voxel-downsampled SfM points" | `means_lr_init = means_lr_final = means_lr_delay_mult = **0.0**` in all three configs ⇒ **anchor means are frozen forever**. This is what makes the lossless integer-grid G-PCC coding and the `assert unique(means)` at `Model.py:315` valid | `[paper §3.4]` vs `[repo: Configs/*.yaml; Model.py:313-315]` | **high** |
| D-7 | **Adaptive-control schedule** | §3.4: "adaptive control [27] is applied to manage the number of anchor primitives" | intervals are `base × num_training_views`, not fixed iteration counts ⇒ a 300-view scene densifies **6× less often** than a 50-view scene at equal iterations | `[paper §3.4]` vs `[repo: TrainerCompGS.py:284-304; Configs/*.yaml]` | **medium** |
| D-8 | **Per-dataset hyperparameters** | none stated | `voxel_size` **0.001** (M360) vs **0.01** (T&T/DB) — 10×; `grad_threshold` 1e-4 vs 8e-5; `opacity_threshold` 8e-4 vs 5e-4 | — vs `[repo: Configs/MipNeRF360.yaml vs TanksAndTemplates.yaml]` | **medium** |
| D-9 | **Reported primitive count** | Tables report sizes; §3.4 says `K = 10` | `num_gaussians` in `results.json` = **anchor** count. Rendered count is up to 10× larger. (The README states this explicitly, so it is a naming trap, not a misrepresentation) | `[paper §3.4]` vs `[repo: TrainerCompGS.py:367; README.md]` | **high** for cross-method comparison |
| D-10 | **Opacity** | Eq. 5: `α_k = 𝒪(γ ⊕ h_k)` | `Tanh` tail ⇒ `α_k ∈ [−1,1]`, and `α_k ≤ 0` ⇒ the primitive is **culled**. So the rasterized set is **view-dependent** — unique among all nine folders | `[paper Eq. 5]` vs `[repo: Prediction.py:28, 61, 65]` | **medium** |
| D-11 | **`s_Σ` shape** | §3.4: "a learnable parameter with an initial value of 0.01" | `nn.Parameter(torch.ones(6) * 0.01)` — a **6-vector**, one step per scale dimension | `[paper §3.4]` vs `[repo: EntropyModel.py:220, 228]` | low |
| D-12 | **View embeddings** | §3.2: "view embeddings γ are generated from camera poses" | 4-D `[direction(3), distance(1)]`, computed at the **anchor** mean and broadcast to all `K` coupled primitives ⇒ the 10 siblings cannot differ in view-dependence | `[paper §3.2]` vs `[repo: Prediction.py:27, 53-57]` | low–medium |
| D-13 | **λ operating points** | §3.4: `λ ∈ {0.001, 0.005, 0.01}` | all three YAMLs ship **only `0.001`**; the other two come from `Scripts/derive_train_eval_scripts.py` | `[paper §3.4]` vs `[repo: Configs/*.yaml; Scripts/derive_train_eval_scripts.py:47-52]` | low, high trap value |
| D-14 | **SSIM implementation** | "rendering loss [17]" implies 3DGS's | `pytorch_msssim.ssim(..., data_range=1.)` — a different library from 3DGS's custom 11×11 σ=1.5 kernel (matching defaults, different code path) | `[paper §3.3]` vs `[repo: TrainerCompGS.py:9, 216; TesterCompGS.py:162]` | low |
| D-15 | **Metric computation** | §4.1: "We adopt PSNR, SSIM and LPIPS" | 8-bit **PNG disk round-trip**, then **pooled-MSE PSNR** (`F.mse_loss`) — the `seathru_NeRF/` convention, **not** the per-channel-mean convention of 3DGS / `compact3d/` / `seasplat/` / `mini-splatting/`, against which Tables 1–3 directly compare | `[paper §4.1]` vs `[repo: TesterCompGS.py:71-75, 153-159]` | **medium** |
| D-16 | **Eq. 1's operator** | prints `Ω, Γ = arg **max** L = arg **max** λR + D` | §3.1 prose says "rate-distortion cost **minimization**"; the repo **minimizes**. Internal inconsistency — sign typo or an extraction artifact | `[paper Eq. 1 vs §3.1]` — `[unverified]` | low, but note it |
| D-17 | **Ablation semantics** | Tabs. 4, 5, 6 all called "ablation studies" | **three different kinds**: Tab. 4 is **cumulative-additive** (3DGS → +hybrid → +RD-opt); Tab. 5 is **one alternative variant** (≈ Scaffold-GS) at a *different operating point* (5.51 MB vs Tab. 4's 8.60 MB — do not cross-reference); Tab. 6 is **three retrainings at different `K`**. None is leave-one-out | `[paper §4.3]` — `[inferred]` | **medium** |

## Claims that need a caveat when cited

| Claim | Caveat |
|---|---|
| "compression ratio up to 89.35× / 175.20×" `[paper §4.2]` | Baseline is an **uncompressed 3DGS `.ply`** (float32, 59 floats/Gaussian). No paper in this set reports a plain-`zip` floor. |
| Deep Blending: **+0.15 dB over 3DGS** at 75.9× smaller `[paper Tab. 2]` | Real and notable, but PSNR/SSIM hold up much better than **LPIPS**, which degrades on all three datasets (T&T 0.18→0.21, DB 0.24→0.28, M360 0.22→0.24) even at the best operating point. |
| "the highest rendering quality, i.e., 23.70 dB, and the smallest bitstream size" `[paper §4.2]` | True for T&T. On **Mip-NeRF 360** the best CompGS point is **−0.20 dB** vs 3DGS, degrading to −1.09 dB at the smallest size. Unbounded outdoor scenes are the weak case. |
| `K = 10` is optimal `[paper Tab. 6]` | `K=10` beats `K=5` by **0.08 dB** while being **9% larger**. On a rate-distortion basis `K=5` is arguably better; the paper computes no BD-rate. Single scene, single run. |
| Hybrid structure gives 5.3×/20.1× size reduction `[paper Tab. 4]` | Cumulative-additive ladder, only **2 of 9** T&T scenes shown, and SSIM/LPIPS get slightly **worse** at each step. |
| Fastest rendering, 5.32 ms `[paper Tab. 7]` | Hardware **unnamed anywhere in the paper**. All methods were re-run by the authors, so internally consistent; not transferable. |
| Compression ratios scale with λ | ⚠️ **Saturating.** Network weights are **29.6% → 37.8% → 46.0%** of the bitstream as λ grows `[paper Fig. 8]` — a fixed floor the paper does not discuss. |

## Unverifiable in this pass

| Claim | Why |
|---|---|
| The **ACM MM 2024 camera-ready** text | only arXiv v1 obtained; all 🔶 items hinge on it `[unverified]` |
| GPU / hardware for Table 7 | **the paper names no device at all** — grep for `GPU|RTX|A100|V100|NVIDIA|3090|Tesla` over the full text returns nothing `[unverified]` |
| VRAM | never reported `[unverified]` |
| Whether baseline rows used unified metric code | §4.1 says "a consistent environment", not "a consistent metric implementation" `[unverified]` — bears directly on D-15 |
| Estimated `R` vs. actual coded bytes | the repo measures real file sizes `[repo: Model.py:337]`, but the paper never compares them to the entropy estimate `[unverified]` |
| Per-scene results | "provided in the Appendix" `[paper §4.1, §4.2]`, absent from the arXiv v1 PDF `[unverified]` |
| Rasterizer modifications | `submodules/diff-gaussian-rasterization` not read; §3.4 implies stock 3DGS kernels `[unverified]` |
| Whether "five independent evaluations" means five trainings or five re-evaluations | ambiguous `[unverified]`; with a hard-coded seed, only the former would be informative |
