# Paper-vs-repo disagreements — SeaThru-NeRF

Paper: arXiv:2304.07743v1 (CVPR 2023). Repo: `deborahLevy130/seathru_NeRF` @ **`3f4ebfe`** (2024-03-14).
Config values are from `configs/llff_256_uw.gin` (what `scripts/train_llff_uw.sh` actually
passes), not the `internal/configs.py` dataclass defaults.

| # | Topic | Paper says | Repo does | Tags | Severity |
|---|---|---|---|---|---|
| D-1 | **mediumMLP capacity** | "6 linear layers with 256 features and a softplus activation, followed by 3 branches" | `self.net_depth_water = 1`, width `net_width_viewdirs = 128`. 3-branch head ✅, trunk ✗ — ≈95× fewer trunk weights. Not gin-bindable (set in `setup()`) | `[paper §4.5]` vs `[repo: models.py:716, 678, 865-869]` | **high** |
| D-2 | **Binary-transmittance prior** | `P(x) ∝ e^{−\|x\|/0.1} + e^{−\|1−x\|/0.1}` — symmetric mixture | `−log( **6**·e^{−\|1−T\|/0.1} + e^{−\|T\|/0.1} )` — asymmetric, biased 6× toward `T^obj = 1` | `[paper Eq. 26-27]` vs `[repo: train_utils.py:160-162; configs.py:173]` | **medium** |
| D-3 | **Object colour** | "color `c^obj` is determined by the viewing direction (θ, φ) as well" | `uw_rgb_dir = False` in the released gin ⇒ the direction encoding is never appended to the colour bottleneck ⇒ **`c^obj` is view-independent (Lambertian)** | `[paper §4.3]` vs `[repo: models.py:898-900; configs/llff_256_uw.gin]` | **high** |
| D-4 | **Detached sample spacing** | not mentioned | `δ^bs = stop_gradient(t_delta)·‖d‖` feeds `α^bs`, `T^bs` and `A`; the object's `δ` stays live. A genuine well-posedness mechanism | — vs `[repo: render.py:179 vs :164]` | **medium** |
| D-5 | **The restored image `J`** | headline capability #1: "render clear views … removing the medium" | `J = jax.lax.stop_gradient(Σ w^obj c^obj)` — carries no gradient, enters **no loss and no metric** | `[paper §1]` vs `[repo: render.py:319]` | low (clarifying), high relevance |
| D-6 | **`L_recon`** | `((Ĉ − C*)/(sg(Ĉ)+ε))²`, `ε = 1e-3` | prediction is **clipped at 1** first, in both the residual and the denominator ⇒ overexposed predictions get **zero** gradient | `[paper Eq. 25]` vs `[repo: train_utils.py:95-102]` | low–medium |
| D-7 | **Distortion loss** | Eq. 24 lists three terms; "we keep the … optimization parameters the same as in [5]" | `Config.distortion_loss_mult = 0.` — mip-NeRF 360's main anti-floater regulariser is **explicitly disabled**, unremarked | `[paper §4.5 / Eq. 24]` vs `[repo: configs/llff_256_uw.gin]` | **medium** |
| D-8 | **Learning rate** | "We keep the learning rate and optimization parameters the same as in [5]" | UW gin: `lr_init = 2e-3`, batch 16 384, 250 k steps. Base `llff_256.gin`: `lr_init = 2.5e-4`, batch 2 048, 2 M steps. **8× LR, 8× batch, ⅛ steps** — principled linear scaling, but not "the same" | `[paper §4.5]` vs `[repo: configs/llff_256.gin vs configs/llff_256_uw.gin]` | low–medium |
| D-9 | **`λ` schedule** | single `λ = 0.0001` | `uw_decay_acc = 5000` switches initial→final multipliers, but both are `1e-4` ⇒ **no-op**; ramp machinery unused in published runs | `[paper Eq. 24]` vs `[repo: train.py:127-134; gin]` | cosmetic |
| D-10 | **Undocumented optional loss** | — | `uw_sig_med_loss` penalises `std(σ^attn) + std(σ^bs)` across the batch. Disabled, and the source comments say so twice: *"not in the paper"*, *"not in the paper!!"* | — vs `[repo: configs.py:168,174; train_utils.py:171-187]` | low (informational) |
| D-11 | **Ablation III reproducibility** | Table 1 column III = "Eqs. 13, 14" | requires setting **both** `Config.gen_eq` and `UWMLP.gen_eq`; the gin file's own comment: *"need to update the values twice, I know it's annoying"*. Setting one silently yields a mismatched model | `[paper Tab. 1]` vs `[repo: configs/llff_256_uw.gin]` | **medium** for ablation reproduction |
| D-12 | **Bias defaults** | not stated | `models.py` declares `density_bias = water_bias = -1.`; the gin overrides all three to `0`. Reading `models.py` alone gives the wrong initialisation | — vs `[repo: models.py:693-694 vs configs/llff_256_uw.gin]` | low, high trap value |
| D-13 | **Ablation table semantics** | Table 1 columns I / II / III | These are **complete alternative model formulations** (replacements of the medium parameterisation / rendering equations), **not** cumulative additions and **not** leave-one-out removals. No *loss* term is ablated anywhere in the paper | `[paper §5.2 / Tab. 1]` — `[inferred: mapped to `uw_fog_model`, `uw_old_model`, `gen_eq` via repo configs.py:177,181 and models.py:706]` | **medium** |

## Cross-paper disagreements (this paper vs. SeaSplat, on the same object)

| # | Topic | SeaThru-NeRF says | SeaSplat says | Assessment |
|---|---|---|---|---|
| X-1 | **Training cost of SeaThru-NeRF** | ≈10 h on an **A100** `[paper §4.5]` | 21 h, 33.2 GB VRAM, 10.184 s/frame, hardware unnamed `[seasplat paper Tab. II]` | Both defensible: different hardware. SeaSplat's `Dockerfile` targets SM 8.6/8.9 (consumer Ampere/Ada), so ~2× slower than an A100 is plausible. **Do not mix the two.** |
| X-2 | **PSNR convention** | pooled MSE over pixels **and** channels `[repo: internal/image.py:136]` | mean of **per-channel** PSNRs `[seasplat repo: utils/image_utils.py:17-19]` | `mean_c(PSNR_c) ≥ PSNR(pooled)` by Jensen, gap grows with channel divergence — maximal underwater. **SeaSplat's Table I compares the two conventions side by side**, in the direction favouring SeaSplat. |
| X-3 | **Metric colour space** | **linear**, explicitly pre-photofinishing `[paper §4.5, §5.1]` | 8-bit files re-read from disk, JPEG when GT has no PNGs `[seasplat repo: train.py:584-644]` | Second independent axis of non-comparability. |
| X-4 | **Simulated-medium strength** | `β^D = [1.3, 1.2, 0.9]`, `β^B = [0.95, 0.85, 0.7]` on LLFF `Fern` `[paper §5.1]` | `β^D = [2.6, 2.4, 1.8]`, `β^B = [1.9, 1.7, 1.4]` on Mip-NeRF-360 `garden` `[seasplat paper §V.A.a]` | **Exactly 2× stronger** medium, and a different base scene. The two "simulated underwater" benchmarks are unrelated. |
| X-5 | **Medium constancy assumption** | constant **per ray**; explicitly criticises per-scene constancy as "far less restrictive [than] models that assume constancy per image or even per scene [2]" `[paper §4.1]` | constant **per scene** `[seasplat paper §V.A.b]` | Not a contradiction — a deliberate expressiveness/cost trade. But it means `σ^attn/σ^bs` and `β^D/β^B` are objects of different type and cardinality (field vs. constants). See `09-glossary.md`. |

## Unverifiable in this pass

| Claim | Why |
|---|---|
| VRAM / parameter count | never reported by this paper `[unverified]` |
| Render time / FPS | never reported by this paper `[unverified]` |
| A100 variant (40 GB vs 80 GB) | not stated; matters because the README warns about OOM at batch 16 384 `[unverified]` |
| LPIPS backbone used for Table 2 | not stated in the paper; `internal/image.py`'s metric harness not traced in full this pass `[unverified]` |
| SSIM window/parameters | not stated `[unverified]` |
| Whether the published numbers came from this commit | commit is 11 months after arXiv v1; no tags `[unverified]` |
| Physical units of the recovered `σ^attn`, `σ^bs` | learned in inverse-NDC units; no calibration to inverse metres is described, despite the §1 claim that they are "informative properties of the captured environment" `[unverified]` |
