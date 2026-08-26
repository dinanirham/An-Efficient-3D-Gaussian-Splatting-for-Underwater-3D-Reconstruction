# Paper-vs-repo disagreements — SeaSplat

Paper: arXiv:2409.17345**v2** (2 Jun 2025). Repo: `dxyang/seasplat` @ **`ddc6259`** (2024-11-27).
The paper revision post-dates the code by ~6 months; "revision drift" is noted where plausible.

| # | Topic | Paper says | Repo does | Tags | Severity |
|---|---|---|---|---|---|
| D-1 | Loss weighting | `L = L_GS + L_bs + L_gw + L_sat + L_op + L_Zsmooth + L_Z-recon`, unweighted | six distinct λ spanning 200× (0.01 → 2.0) | `[paper Eq.10]` vs `[repo: arguments/__init__.py:115,130,144,147,150,153]` | **high** |
| D-2 | Attenuation model | "(1,1,1,3) kernel", i.e. one coefficient per channel | `AttenuateNetV3` — matches, but V1/V2 implementing DeepSeeColor's two-exponential `a e^{-bz}+c e^{-dz}` also ship and are the first classes in the file | `[paper §IV.C]` vs `[repo: models.py:104-241; arguments/__init__.py:176]` | low (agree) |
| D-3 | Depth detachment | "Ẑ … is detached to prevent gradients from flowing through" | medium maps computed **twice** — live-`Ẑ` copies feed `Î` (grad flows to geometry), detached copies feed `L_bs` | `[paper §IV.A]` vs `[repo: train.py:254-256, 269-273]` | **medium** |
| D-4 | `L_bs` asymmetry | `max{D̂,0} + k·min{D̂,0}`, "`k > 1`" | `k = 1000`; negative branch is `SmoothL1(β=0.2)` (Huber), not linear | `[paper Eq.4]` vs `[repo: losses.py:146-161]` | **medium** |
| D-5 | `L_sat` form | `Σ max(Ĵ_c − 0.7, 0)` — linear, one-sided, summed | `mean((relu(−Ĵ) + relu(Ĵ−0.7))²)` — squared, two-sided, averaged | `[paper Eq.6]` vs `[repo: losses.py:228-232]` | low–medium |
| D-6 | `L_op` reference image | `1[‖**I** − B‖²₂ < T_sim]` — the **capture**, squared norm, free `T_sim` | `‖**Î** − σ(B^∞)‖₂ < 0.2√3` — the **model's own reconstruction**, unsquared norm, hard-coded threshold | `[paper Eq.9]` vs `[repo: train.py:319; losses.py:248,283]` | **medium** |
| D-7 | `learned_bg` | not mentioned anywhere | a 4th learned parameter with its own Adam optimizer (`lr=1e-2`), init `[0.05,0.25,0.80]`, composited pre-SeaThru, then **copied into `B^∞`** at the transition | — vs `[repo: train.py:123-131, 204-216; arguments/__init__.py:114-124]` | **high** |
| D-8 | Iteration accounting | "interleaving optimization of the medium parameters with … the 3D Gaussian representation" (no schedule) | `continue` at `train.py:453,463` sits above `iteration += 1` at `train.py:567`; 1000 warm-up + 2000 colour-only + 50-per-100 bursts consume **zero** iteration budget → ≈43 000 optimizer steps for a "30 000-iteration" run, each re-running both rasterization passes | `[paper §IV.B]` vs `[repo: train.py:433-463, 567]` | **high** |
| D-9 | Kernel shape | "(1, 1, 1, 3) kernel" | `(3, 1, 1, 1)` — correct PyTorch `(out,in,kH,kW)` layout for the same object | `[paper §IV.C]` vs `[repo: models.py:216]` | cosmetic |
| D-10 | Medium init | not stated | `β^D ← [1.1, 0.95, 0.95]` (hand-tuned, red-fastest); `β^B, B^∞ ← U(0,1)³` | — vs `[repo: models.py:54,61,216-218]` | **medium** |
| D-11 | SH degree | "zero order spherical harmonics" | `sh_degree = 0` (upstream 3DGS uses 3) | `[paper §IV.C]` vs `[repo: arguments/__init__.py:49]` | low (agree), high relevance to the compression comparison set |
| D-12 | Ablation controllability | Table III ablates DS / C / BG / BS | all booleans registered `action="store_true"`; the ~12 flags defaulting `True` **cannot be disabled from the CLI** | `[paper Tab.III]` vs `[repo: arguments/__init__.py:35-38]` | **high** for reproduction |
| D-13 | Metric data path | "computing peak signal-to-noise ratio…" | metrics recomputed from **8-bit files re-read from disk**, saved as **JPEG** whenever the GT dir has no PNGs (true for the SeaThru-NeRF DSLR data) | `[paper §V.A.c]` vs `[repo: train.py:584-644; metrics.py:59-62]` | **medium** |
| D-14 | PSNR definition | unspecified | mean of **per-channel** PSNRs, not PSNR of the pooled MSE — inflates results most exactly where channel errors diverge, i.e. underwater | `[paper §V.A.c]` vs `[repo: utils/image_utils.py:17-19]` | **medium** |
| D-15 | Ablation table semantics | rows read as component contributions | rows are **cumulative additions to vanilla 3DGS**, not leave-one-out; row 9 ("Ours, all losses", 27.11) ≠ row 8 ("+DS+BG+C+BS", 26.64), so the ladder does **not** enumerate the full objective (`L_Z-recon` is unaccounted for) | `[paper Tab.III]` — internal inconsistency, `[inferred]` | **medium** |
| D-16 | Ablation legend | caption defines "**SD** = smooth depth loss" | every row is labelled "**DS**" | `[paper Tab.III]` — internal typo | cosmetic |
| D-17 | `--eval` | "comparing rendering at held-out test frames" | `eval` defaults `False` → empty test set, trains on everything; README's command omits `--eval` | `[paper §V.A.c]` vs `[repo: arguments/__init__.py:58; README.md]` | **high** for reproduction |

## Shared deviations from a *cited third source* (paper and repo agree with each other, both differ from the reference)

| # | Topic | Cited source | Both paper and repo do | Tags |
|---|---|---|---|---|
| S-1 | Edge-aware depth smoothness | Godard et al. 2017 (ref [35]) uses `e^{−\|∂I\|}` | use `e^{−∂I}` with the **signed** gradient, so smoothness is *more* strongly enforced across dark→bright edges than in flat regions — inverted on half of all edges. The repo's own commented-out block has the correct `abs` version | `[paper Eq.8]` + `[repo: depth_losses.py:17-24 vs 26-40]` |

## Unverifiable in this pass

| Claim | Why |
|---|---|
| GPU used for Table II | paper says only "a consistent set of hardware"; `Dockerfile:13-15` targets SM 8.6/8.9 with SM 9.0 commented out — suggestive of consumer Ampere/Ada, not conclusive `[unverified]` |
| Gaussian count / model size | never reported; only logged to TensorBoard `[repo: train.py:1007]` `[unverified]` |
| Whether SeaThru-NeRF's Table I numbers used the same PSNR convention | requires reading that codebase — see `../../seathru_NeRF/research-methodology-output/10-reproducibility.md` `[unverified]` |
| Intended value of `k` | paper states only `k > 1` `[unverified]` |
