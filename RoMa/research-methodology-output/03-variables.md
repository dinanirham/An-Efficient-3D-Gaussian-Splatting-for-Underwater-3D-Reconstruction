# §3 — Formal variable table

`H, W` = working resolution (must be a multiple of 14). `K = 64² = 4096` anchors.
Strides: coarse **14** (keyed `16`), refiners **{8, 4, 2, 1}**.

---

## 3.1 Independent variables (directly optimized)

Two parameter groups, with **different learning rates**, plus one frozen module.

| Component | Repo | Shape / architecture | lr | Source |
|---|---|---|---|---|
| **`F_coarse,θ` = DINOv2 ViT-L/14** | `CNNandDinov2.dinov2_vitl14` | ViT-L, patch 14, `.eval()` | ❌ **FROZEN — never optimized** | `[paper §3.2]` `[repo: encoders.py:42, 50, 61-64]` |
| **`F_fine,θ` = VGG19** | `VGG19` | `tvm.vgg19_bn(...).features[:40]`, strides {1,2,4,8} | `STEP_SIZE · 5e-6 / 8` (the "encoder" group) | `[paper §3.2]` `[repo: encoders.py:6-13; train_roma_outdoor.py:223]` |
| **`E` — Gaussian Process match encoder** | `GP` | `gp_dim = 512`; unchanged from DKM | decoder group | `[paper §3.1]` `[repo: roma_models.py:84]` |
| **`D` — Transformer match decoder** | `TransformerDecoder` | 5 × `Block(1024, 8 heads, MemEffAttention)`, MLP 4096, **`pos_enc=False`**; output `64² + 1 = 4097` | `STEP_SIZE · 1e-4 / 8` | `[paper §3.3]` `[repo: roma_models.py:87-96]` |
| **Refiners `R_θ,i`** | `ConvRefiner` ×4 | strides {8,4,2,1}; `hidden_blocks=8`, `kernel_size=5`, `displacement_emb_dim=64`, depthwise | decoder group | `[paper §3.1]` `[repo: roma_models.py:99-129]` |
| Projection heads | `proj1`, `proj2` | `Conv2d(128→64)`+BN, `Conv2d(64→9)`+BN | decoder group | `[repo: roma_models.py:172-173]` |

> **Freezing is structural, not a flag.** DINOv2 is stored inside a *list* —
> `self.dinov2_vitl14 = [dinov2_vitl14]`, commented *"ugly hack to not show parameters to
> DDP"* `[repo: encoders.py:50]` — so PyTorch never registers it as a submodule and it cannot
> reach the optimizer. Its forward additionally runs under `torch.no_grad()`
> `[repo: encoders.py:61]`. Belt and braces.

> ⚠️ **`cnn_kwargs = dict(pretrained=False, amp=True)`** `[repo: roma_models.py:197]` — the
> VGG19 fine encoder is **not** ImageNet-pretrained despite `vgg19_bn` being a stock
> torchvision model. The paper never states this. Same choice as `../RoMaV2/`
> `[RoMaV2 repo: features.py:182]`.

### Optimizer

| Item | Value | Source |
|---|---|---|
| Optimizer | **AdamW**, `weight_decay = 0.01` | `[repo: train_roma_outdoor.py:225]` — ⚠️ paper says only "training setup as in DKM" |
| Encoder lr | `STEP_SIZE · 5e-6 / 8` | `[paper §4.2]` = `[repo: train_roma_outdoor.py:223]` ✅ |
| Decoder lr | `STEP_SIZE · 1e-4 / 8` | `[paper §4.2]` = `[repo: train_roma_outdoor.py:224]` ✅ |
| Schedule | `MultiStepLR`, one milestone at **90%** of training | ⚠️ `[repo: train_roma_outdoor.py:226-227]` — not in paper |
| Budget | `N = 32 × 250 000` ⇒ **250k steps at batch 32** | ⚠️ `[repo: train_roma_outdoor.py:193]` — not in paper |
| Precision | AMP, `amp_dtype = torch.float16` | `[repo: roma_models.py:50]` |
| Distribution | DDP + gradient clipping | `[repo: train_roma_outdoor.py:248]` |

---

## 3.2 Dependent variables

### Model outputs

| Symbol | Shape | Meaning | Source |
|---|---|---|---|
| `Ŵ^{A→B}_coarse` | `(H/14, W/14, 2)` | coarse warp, decoded from anchor probabilities | `[paper Eq. 2]` |
| `p^{A,coarse}` | `(H/14, W/14)` | coarse matchability | `[paper Eq. 2]` |
| `Ŵ^{A→B}` | `(H, W, 2)` | refined dense warp, normalized `[−1,1]²` | `[paper Eq. 3]` |
| `p^A` | `(H, W)` | **certainty / matchability** — `p^A(x^A)` | `[paper §3.3]` |

> **Notation note** `[paper footnote 1]`: "This is denoted as `p^{A→B}` by Edstedt et al. [17].
> We omit the `B` to avoid confusion with the conditional." So RoMa's `p^A` is RoMa v2's
> `p^{A↦B}` — **the same object under two names across the two folders**.

### Internals

| Symbol | Shape | Definition | Source |
|---|---|---|---|
| `φ^A_coarse`, `φ^B_coarse` | stride-14 tokens | frozen DINOv2 features | `[paper Eq. 7]` |
| `φ^A_fine`, `φ^B_fine` | strides {1,2,4,8} | VGG19 features | `[paper Eq. 1]` |
| `π_k(x^A)` | `(K, H/14, W/14)` | **anchor probabilities**, `K = 64²` | `[paper Eq. 8]` |
| `m_k` | `(K, 2)` | anchor coordinates on a uniform grid, `linspace(−1+1/64, 1−1/64, 64)` | `[paper §3.3]` `[repo: robust_loss.py:48-49]` |
| `k̂(x)` | integer | `argmax_k π_k(x)` | `[paper Eq. 9]` |
| `N₄(k̂)` | 5 indices | `k̂` plus its left/right/top/bottom neighbours — the local softargmax support | `[paper Eq. 9]` |
| `epe` | `(B, H, W)` | end-point error `‖flow − x²‖₂` | `[repo: robust_loss.py:83]` |
| `prev_epe` | `(B, H, W)` | **detached** EPE from the previous (coarser) scale — drives the local gate | `[repo: robust_loss.py:160]` |
| `gt_warp`, `gt_prob` | `(B,H,W,2)`, `(B,H,W)` | supervision from depth + poses via `get_gt_warp` | `[repo: robust_loss.py:126-136]` |
| `q(x^A, x^B; s)` | — | the **theoretical** matchability model, `𝒩(0, s²I) ∗ p(·; 0)` | `[paper Eq. 10]` |

---

## 3.3 Fixed / given inputs

### Data

| Quantity | Value | Source |
|---|---|---|
| Training set (outdoor) | **MegaDepth**, `train_loftr` split, `loftr_ignore=True`, `imc21_ignore=True` | `[paper §4.2]` `[repo: train_roma_outdoor.py:197]` |
| ⚠️ Dataset construction | **two builds concatenated**: `min_overlap = 0.01` **and** `min_overlap = 0.35` | ⚠️ `[repo: train_roma_outdoor.py:201-210]` — not in paper |
| Scene weighting | `weight_scenes(..., alpha = 0.75)` | ⚠️ `[repo: train_roma_outdoor.py:212]` — not in paper |
| Augmentation | `use_horizontal_flip_aug = True`, `shake_t = 32`, `rot_prob = 0` | ⚠️ `[repo: train_roma_outdoor.py:199-206]` — not in paper |
| Supervision | MVS depth (MegaDepth) / RGB-D (ScanNet) → `get_gt_warp` | `[paper §4.2]` `[repo: robust_loss.py:126]` |
| Indoor model | separate script, ScanNet-trained, used only for ScanNet-1500 | `[paper §4.2]` `[repo: experiments/roma_indoor.py]` |

### Resolutions

| Name | Value | Note |
|---|---|---|
| `low` | `448 × 448` | used for the **ablation** table `[paper §4.2]` ✅ |
| **`medium`** | `560 × 560` (= 14·8·5) | **default**; the final model `[paper §4.2]` ✅ |
| `high` | `672 × 672` (= 14·8·6) | |

`[repo: train_roma_outdoor.py:23, 301]`. All are multiples of 14, enforced by
`assert resolution % 14 == 0` `[repo: roma_models.py:71-72]`.

### Loss hyperparameters — **the table to read carefully**

| Name | Class default `[repo: robust_loss.py:11-26]` | Training script `[repo: train_roma_outdoor.py:214-220]` | Paper |
|---|---|---|---|
| `alpha` (Charbonnier α) | `1.0` | **`0.5`** | **0.5** ✅ |
| `c` (Charbonnier scale) | `1e-3` | **`1e-4`** | **0.03** ❌ **300× off** |
| `ce_weight` (= paper's `λ`) | `0.01` | `0.01` | ❌ value never stated |
| `local_dist` | `4.0` | **`{1:4, 2:4, 4:8, 8:8}`** | ❌ not in paper |
| `local_largest_scale` | `8` | `8` | ❌ not in paper |
| `local_loss` | `True` | (default) | ❌ not in paper |
| `smooth_mask` | `False` | (default) | — |
| `depth_interpolation_mode` | `"bilinear"` | `"bilinear"` | — |
| `relative_depth_error_threshold` | `0.05` | (default) | — |
| `scale_weights` | `{1:1, 2:1, 4:1, 8:1, 16:1}` — all 1 | — | ❌ mechanism exists, unused |

> **Three of these need flagging.** `c` differs from the paper by **300×** (D-1). `λ` is
> introduced in `[paper Eq. 14]` but its value appears only in code. And `local_dist` /
> `local_largest_scale` implement an entire supervision-gating mechanism the paper does not
> mention (D-2).

### Inference settings `[repo: roma_models.py:46-56, 209-214]`

| Name | Default | Note |
|---|---|---|
| `symmetric` | `True` | match both directions ⚠️ **EDGS sets this `False`** |
| `upsample_preds` | `True` | second pass at `upsample_res` ⚠️ **EDGS sets this `False`** |
| `attenuate_cert` | `True` at inference, **`False`** during training | `[repo: train_roma_outdoor.py:187]` — a train/test asymmetry |
| **`sample_thresh`** | **`0.05`** | ⭐ **read directly by EDGS as its `τ_corr`** `[EDGS repo: source/corr_init.py:541]` |
| `sample_mode` | `"threshold_balanced"` | KDE-balanced sampling `[paper §4.3]` |
| `amp_dtype` | `torch.float16` (`float32` on CPU) | |
| `use_custom_corr` | forced `False` on non-Linux, with a warning | `[repo: roma_models.py:60-62]` — same as `../RoMaV2/` |
| Sampled matches | 10 000 for two-view geometry | `[paper §4.3]` |
