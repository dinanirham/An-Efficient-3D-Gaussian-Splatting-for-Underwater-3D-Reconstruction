# Paper-vs-repo disagreements — RoMa

**Paper:** `../../RoMa.pdf` = arXiv:2305.15404**v2** (11 Dec 2023), CVPR 2024.
**Repo:** `Parskatt/RoMa` @ **`77f8d68`**, `git describe` → **`v0.1.2-4-g77f8d68`** (2026-01-23)
— roughly **2 years newer** than the paper. 🔶 marks deltas plausibly explained by
post-publication drift.

> ✅ **Training code is released here**, unlike `../RoMaV2/`. Everything below is a genuine
> code-vs-paper comparison rather than an absence.

| # | Topic | Paper says | Repo does | Tags | Severity |
|---|---|---|---|---|---|
| D-1 | ⭐ **Charbonnier scale `c`** | §3.4: "In practice, we choose **`c = 0.03`**" | **`c = 1e-4`** in the training script (class default: `1e-3`). `c` **is** the loss's quadratic→sub-linear transition point — the quantity Fig. 4 plots. A **300×** difference | `[paper §3.4]` vs `[repo: train_roma_outdoor.py:220; robust_loss.py:25, 90-92]` | **high** 🔶 |
| D-2 | **Local supervision gate** | not mentioned | at scales ≤ 8, `prob ×= 𝟙[prev_epe < (2/512)·local_dist[s]·s]` with `local_dist = {1:4, 2:4, 4:8, 8:8}` — a refiner is supervised **only where the coarser scale was already close**. A hard gate, not the soft down-weighting the robust loss provides | — vs `[repo: robust_loss.py:138-141, 160; train_roma_outdoor.py:216-217]` | **high** |
| D-3 | **Supervision mask** | Eqs. 13-18 approximate `q` "with a discrete set of known correspondences" | all **warp** losses indexed `[prob > 0.99]`; the certainty BCE deliberately left unmasked; plus an all-zero guard | `[paper §3.4]` vs `[repo: robust_loss.py:51, 53-54, 71, 91]` | **medium** |
| D-4 | **`λ` value** | Eq. 14 introduces `λ` "that controls the weighting of the marginal compared to that of the conditional" — **value never given** | `ce_weight = 0.01` | `[paper Eq. 14]` vs `[repo: train_roma_outdoor.py:215]` | **medium** |
| D-5 | **Training schedule / optimizer / data construction** | §4.2: "We use the training setup as in DKM [17]" + two LRs + resolutions | **AdamW**, `weight_decay=0.01`; **250k steps at batch 32**; `MultiStepLR` with one milestone at 90%; MegaDepth built **twice** and concatenated (`min_overlap` 0.01 **and** 0.35); `weight_scenes(alpha=0.75)`; horizontal-flip aug, `shake_t=32` | `[paper §4.2]` vs `[repo: train_roma_outdoor.py:193, 198-212, 225-227]` | **medium** |
| D-6 | **Coarse scale key** | §3.1: refiners at strides {1,2,4,8}; coarse at DINOv2's stride **14** | the coarse level is keyed **`16`** throughout (`scale_weights`, `corresps[16]`), while `assert resolution % 14 == 0` | `[paper §3.1]` vs `[repo: robust_loss.py:106; matcher.py:856; roma_models.py:71-72]` | cosmetic, high trap value |
| D-7 | **`scale_weights`** | §3.4: "we do **not need to tune any scaling** between these losses" | the mechanism exists with an explanatory comment and is **all ones** — inert. *Corroborates* the paper's claim | `[paper §3.4]` vs `[repo: robust_loss.py:105-106]` | low (confirmatory) |
| D-8 | **VGG19 fine encoder** | §3.2 / Tab. 2 Setup III: "`F_fine,θ = VGG19`" | `vgg19_**bn**`, and **`pretrained=False`** — trained from scratch, not ImageNet-initialised | `[paper §3.2]` vs `[repo: roma_models.py:197; encoders.py:13]` | low–medium |
| D-9 | **`attenuate_cert`** | not mentioned | `True` at inference (low-res certainty interpolated and used to attenuate), **`False` during training**. The certainty reported at test time is not the one the model was trained to produce | — vs `[repo: matcher.py:854-860; roma_models.py:56; train_roma_outdoor.py:187]` | **medium** — and `../EDGS/` thresholds on exactly this signal |
| D-10 | **`TinyRoMa`** | absent | a whole second model with its own architecture, loss, training script, eval script, demo and tests | — vs `[repo: models/tiny.py; losses/robust_loss_tiny_roma.py; experiments/train_tiny_roma_v1_outdoor.py]` | low 🔶, high trap value |
| D-11 | **CUDA kernel** | not mentioned | `use_custom_corr` forced `False` on non-Linux with a warning | — vs `[repo: roma_models.py:60-62]` | low |

## ✅ Verified-correct — an unusually high hit rate

Every architectural number in §3.3 and every loss form in §3.4 checks out:

| Paper claim | Code |
|---|---|
| DINOv2 frozen throughout training `[§3.2]` | hidden from DDP in a list `[encoders.py:50]`, `.eval()` `[:42]`, `no_grad()` `[:61]` ✅ |
| Decoupled coarse/fine encoders `[Eq. 7]` | `CNNandDinov2` = separate paths `[encoders.py:29-64]` ✅ |
| GP match encoder retained from DKM `[§3.1]` | `gp_dim = 512` `[roma_models.py:84]` ✅ |
| Decoder: 5 blocks, 8 heads, hidden 1024, MLP 4096 `[§3.3]` | `[Block(1024, 8) × 5]`, `decoder_dim = 512+512` `[roma_models.py:84-91]` ✅ **exact** |
| `pos_enc = False` `[§3.3]` | `pos_enc=False` `[roma_models.py:96]` ✅ |
| `K = 64²`, output `K + 1` `[§3.3]` | `cls_to_coord_res = 64`, `64**2 + 1` `[roma_models.py:87, 91]` ✅ |
| Anchors a tight cover, no overlap/holes `[footnote 2]` | `linspace(−1+1/64, 1−1/64, 64)` `[robust_loss.py:48]` ✅ |
| `α = 0.5` `[§3.4]` | `alpha = 0.5` `[train_roma_outdoor.py:219]` ✅ |
| Charbonnier form `[Eqs. 15-16]` | `cs**a * ((x/cs)**2 + 1)**(a/2)` `[robust_loss.py:92]` ✅ |
| Cross-entropy to nearest anchor `[Eq. 13]` | `F.cross_entropy(gm_cls, argmin_k‖m_k − x²‖)` `[robust_loss.py:50-51]` ✅ |
| BCE on matchability `[Eq. 14]` | `binary_cross_entropy_with_logits` `[robust_loss.py:52, 88]` ✅ |
| Gradients detached between refiners `[§3.1]` | ✅ (and `prev_epe` detached `[robust_loss.py:160]`) |
| Canonical LRs 1e-4 / 5e-6 at batch 8 `[§4.2]` | `STEP_SIZE*1e-4/8`, `STEP_SIZE*5e-6/8` `[train_roma_outdoor.py:223-224]` ✅ |
| Ablations at 448², final at 560² `[§4.2]` | `{"low":(448,448), "medium":(14*8*5,...)}`, default `medium` `[train_roma_outdoor.py:23, 301]` ✅ |
| Test scenes excluded from training `[§4.2]` | `loftr_ignore=True, imc21_ignore=True` `[train_roma_outdoor.py:197]` ✅ |
| 10 000 balanced matches, `sample_thresh` `[§4.3]` | `sample_mode="threshold_balanced"`, `sample_thresh=0.05` `[roma_models.py:54-55]` ✅ |

## Claims that need a caveat when cited

| Claim | Caveat |
|---|---|
| "+36% on WxBS" `[paper Abstract, §4.3]` | ✅ Robust and correctly stated (58.9 → 80.1 mAA over DKM). **This is the result to cite** — the gains elsewhere are 2–9%. ⚠️ But no WxBS harness ships in the repo. |
| Setup V: "DINOv2 gives a significant improvement" `[paper §4.1]` | At **1px** the gain is **0.1** (14.4 → 14.3) — noise. At 3px (5.4 → 4.6) and 5px (4.1 → 3.2) it is real. DINOv2 supplies **robustness**, not sub-pixel precision — consistent with the paper's own framing, but "significant" needs the qualifier. |
| The Transformer decoder's contribution | ⚠️ **Setups IV and VIII measure the same component and disagree by 9×** (0.1 vs 0.9 at 1px). That is the paper's point — the decoder "particularly improves performance when used to predict anchor probabilities" `[paper §1]` — but it means **Setup IV alone must not be quoted** as the decoder's value. **Setup VIII is the leave-one-out; use it.** |
| Table 2 generally | **CUMULATIVE-ADDITIVE** for rows I→VII (each row = previous + one change), and **Setup VIII is a leave-one-out from the full model**. Two different kinds in one table. Also: the metric is **100−PCK, lower is better** — inverted relative to every other table in the paper. |
| "we do not need to tune any scaling between these losses" `[paper §3.4]` | ✅ Verified — `scale_weights` are all 1. A genuine structural consequence of the detached gradients and unshared encoders. |
| Fig. 4's gradient analysis | Drawn for `c = 0.03`; the shipped model was trained with `c = 1e-4` (D-1). The deployed robustness profile is not the analysed one. |
| The robust loss handles far-outside-support initialisations `[paper §3.4]` | ⚠️ In practice the **local-EPE gate (D-2) masks most such pixels out before the loss sees them.** The two mechanisms overlap, and only one is documented. |

## Unverifiable in this pass

| Claim | Why |
|---|---|
| Table 1's linear-probe study (VGG19 / RN50 / DINOv2) | "Further details … in the supplementary material" `[paper §3.2]`; no probe script in the repo `[unverified]` |
| Whether the released weights are the paper's model | repo HEAD is ~2 years post-publication; weights come from a release URL `[unverified]` |
| Any computational figure | **the paper reports none at all** — no GPU, no time, no memory, no parameter count `[unverified]` |
| GP match encoder internals | inherited wholesale from DKM; not traced `[unverified]` |
| `get_gt_warp` correctness | `romatch/utils/utils.py` not read line-by-line `[unverified]` |
| Full inference path (symmetric matching, `upsample_preds` second pass) | `matcher.py` read only around `attenuate_cert` `[unverified]` |
| WxBS / IMC2022 evaluation | no harness ships `[unverified]` |
| Whether `experiments/roma_indoor.py` matches the paper's ScanNet recipe | `[unverified]` |
