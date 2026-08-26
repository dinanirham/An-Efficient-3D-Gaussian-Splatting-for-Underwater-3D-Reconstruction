# §3 — Formal variable table

⚠️ **The released package is inference-only** `[repo: src/romav2/romav2.py:172]`, so §3.1 is
split into (a) what the *paper* says was optimized during training, and (b) what the
*checkpoint* actually contains. Shapes are per image pair; `H, W` are the working resolution.

---

## 3.1a Independent variables — what was trained `[paper-only]`

Two disjoint stages, trained sequentially `[paper §3.2, §3.3]`:

| Stage | Trained | Frozen | Steps | Batch | LR | Data seen |
|---|---|---|---|---|---|---|
| **1 — coarse matcher** | MV-Transformer (ViT-B), attention/position embeddings, DPT head | **DINOv3 ViT-L/16** | 300 k | 128 | 4e-4 | ≈ 38 M pairs |
| **2 — refiners** | 3 ConvRefiners (strides 4/2/1), VGG19-BN fine features, precision heads | **matcher (all of stage 1)** + DINOv3 | 300 k | 64 | 4e-4 | ≈ 19 M pairs |

- Optimizer: `OptimizerName = Literal["adamw"]` `[repo: src/romav2/types.py]` — the type
  survives in the released code even though the training loop does not. `[inferred]`
- **EMA on the refiners**, decay **0.999** `[paper §3.3]` — a second set of shadow weights.
- Coarse matcher trained on **mixed resolutions and aspect ratios**; refiners "trained
  exclusively with size 640 × 640" `[paper §3.5]`. ⚠️ The exact resolution list is
  **unrecoverable** from this PDF — the sentence is mangled in every text extraction I tried
  (`pdftotext -layout` and `-raw`). `[unverified]`

## 3.1b What the released checkpoint contains

Loaded from a **version-pinned release asset**
`.../releases/download/v2.0.1/romav2.0.1.pt` `[repo: romav2.py:95-98]` into four submodules
`[repo: romav2.py:100-105]`:

| Submodule | Repo class | Configuration |
|---|---|---|
| `self.f` | `Descriptor` | `dinov3_vitl16`, `frozen=True`, `layer_idx=[11, 17]`, `dim` 1024, `enable_amp=True`, `normalize_feats=False` `[repo: features.py:82-90]` |
| `self.matcher` | `Matcher` | `mv_vit="vit_base"`, `mv_vit_use_rope=True`, `attention_mode="alternating"`, `head="dpt-no-pos"`, `temp=0.1`, `scale=1`, `dim=1024`, `warp_dim=2`, `confidence_dim=1`, `num_feature_layers=2`, `feat_dim=1024`, `pos_emb_dim=1024` `[repo: matcher.py:69-88]` |
| `self.refiners` | `Refiners` | `refiner_type="roma-4-pow2"`, `confidence_dim=4`, `grid_sample_mode="bilinear"` `[repo: refiner.py:227-230]` |
| `self.refiner_features` | `FineFeatures` | `vgg19bn`, `patch_size=4`, **`pretrained=False`** `[repo: features.py:179-182]` |

### Per-refiner architecture `[repo: refiner.py:239-265]`

| Stride | `feat_dim` | `proj_dim` | `displacement_emb_dim` | `local_corr_radius` | input width |
|---|---|---|---|---|---|
| 4 | 256 | 192 | 79 | **3** (7×7 window) | `192·2 + 79 + 7² = 512` |
| 2 | 128 | 48 | 23 | **1** (3×3 window) | `48·2 + 23 + 3² = 128` |
| 1 | 64 | 12 | 8 | **None** | `12·2 + 8 = 32` |

Shared: `kernel_size=5`, `hidden_blocks=8`, `norm_type_name="batch"`, `bn_momentum=0.01`,
`refine_init=4.0`, `enable_amp=True` `[repo: refiner.py:70-85]`.

> Two things worth flagging. **`pretrained=False` for VGG19-BN** — the fine-feature CNN is
> trained from scratch, not an ImageNet initialization, despite VGG19 being a stock
> torchvision model. And **`confidence_dim = 4`** at the refiners vs **`1`** at the matcher:
> the extra 3 channels are the precision parameters `z11, z21, z22`, which therefore exist
> only in the refinement stage `[repo: matcher.py:81 vs refiner.py:77]`.

---

## 3.2 Dependent variables (produced each forward pass)

### The model's outputs — the paper's headline signature `[paper §1, Fig. 2]`

| Symbol | Shape | Meaning | Source |
|---|---|---|---|
| `W^{A↦B}` | `(H, W, 2)` | dense warp, image A → image B, in **normalized `[−1,1]²` coordinates** | `[paper §1]` `[repo: README.md]` |
| `W^{B↦A}` | `(H, W, 2)` | the reverse warp (only when `bidirectional`) | `[paper §1]` `[repo: romav2.py:190-196]` |
| `p^{A↦B}`, `p^{B↦A}` | `(H, W, 1)` | **overlap / confidence** ∈ [0,1] — 1 where co-visible, 0 where occluded | `[paper §1]` `[repo: romav2.py:62]` |
| `Σ⁻¹^{A↦B}`, `Σ⁻¹^{B↦A}` | `(H, W, 2, 2)` | **precision matrix** — new in v2, positive definite | `[paper §3.3]` `[repo: romav2.py:65; geometry.py:168-174]` |

### Internals

| Symbol | Shape | Definition | Source |
|---|---|---|---|
| `f_A`, `f_B` | stride-16 tokens, dim 1024 | frozen DINOv3 ViT-L/16 features, layers 11 and 17 | `[paper §3.2]` `[repo: features.py:87-89]` |
| `S` | `(M, N)` | patch-to-patch **similarity matrix**; `M`, `N` = patch counts in A, B | `[paper Eq. 1]` `[repo: matcher.py]` |
| `Softmax(S)·x_B` | — | soft-aggregated position embeddings of B, fed to the DPT head | `[paper §3.2]` |
| `r_θ` | `(H, W, 2)` | **residual** `W_θ^{A↦B} − W_GT^{A↦B}` — the quantity whose covariance is predicted | `[paper Eq. 3]` |
| `z11, z21, z22` | `(H, W, 3)` | raw precision parameters emitted by each refiner | `[paper §3.3]` `[repo: refiner.py:201-204]` |
| `L` | `(H, W, 2, 2)` | lower-triangular Cholesky factor, `l11 = Softplus(z11)+1e-6`, `l21 = z21`, `l22 = Softplus(z22)+1e-6` | `[paper §3.3]` `[repo: refiner.py:201-204]` |
| `Σ⁻¹` | `(H, W, 2, 2)` | `L Lᵀ`; accumulated across strides as `Σ⁻¹_i = Σ_{j≥i} Σ⁻¹_j` | `[paper §3.3]` `[repo: geometry.py:168-174]` |
| `p̂^{A↦B}` | `(H, W, 1)` | thresholded sampling distribution `max(𝟙_{p>0.05}, p)` | `[paper Eq. 6]` `[repo: romav2.py:126]` |

---

## 3.3 Fixed / given inputs

### Inference settings — **the single most important table for using this model**

`[repo: src/romav2/romav2.py:119-160]`. `Setting` is a `Literal` of eight values
`[repo: types.py]`:

| Setting | coarse `H_lr×W_lr` | fine `H_hr×W_hr` | bidirectional | threshold | balanced sampling |
|---|---|---|---|---|---|
| `turbo` | 320×320 | — | ❌ | None | ✅ |
| `fast` | 512×512 | — | ❌ | None | ✅ |
| `base` | **640×640** | — | ❌ | None | ✅ |
| **`precise`** (default) | **800×800** | **1280×1280** | ✅ | None | ✅ |
| `mega1500`, `scannet1500`, `wxbs`, `satast` | **800×800** | **1024×1024** | ✅ | **0.05** | ✅ |

> ⚠️ **The default (`precise`) is not the benchmark setting.** `[paper §4.1]` states "We use a
> coarse resolution of 800 × 800 and a fine resolution of **1024 × 1024**" — that is the
> `mega1500` branch, **not** `precise` (which uses 1280 and no threshold). Meanwhile Tables 6
> and 7 feed **640 × 640** directly, i.e. `base`. **Three different configurations produce
> three different tables in one paper.** Always name the setting.

### Other hard requirements

| Requirement | Value | Source |
|---|---|---|
| Input range | `[0, 1]` | `[repo: romav2.py:174 — "assumes images between [0, 1]"]` |
| `torch.get_float32_matmul_precision()` | **must be `"highest"`**, else `RuntimeError` | `[repo: romav2.py:169-170]` |
| Mode | inference only — `assert not self.training` | `[repo: romav2.py:172]` |
| Anchor resolution | `anchor_width = anchor_height = 512` | `[repo: romav2.py:76-77]` |
| Output coordinates | normalized `[−1,1]²`; convert via `to_pixel_coordinates` | `[repo: README.md; geometry.py]` |
| Python | ≥ 3.10 (tested on 3.12) | `[repo: pyproject.toml; README.md]` |
| CUDA kernel | `fused-local-corr`, **Linux only**, optional | `[repo: pyproject.toml; local_correlation.py:4-7]` |
| Checkpoint | auto-downloaded from the **`v2.0.1` release** | `[repo: romav2.py:95-98]` |

### Training-time constants `[paper-only]`

| Name | Value | Source |
|---|---|---|
| `λ` (overlap, matcher) | **0.1** — "the same … as in RoMa" | `[paper Eq. 2]` |
| `λ_ov` (refiners) | **1e-2** | `[paper Eq. 5]` |
| `λ_prec` | **1e-3** | `[paper Eq. 5]` |
| Charbonnier `α` | **0.5** | `[paper §3.3]` |
| Charbonnier `c` | **1e-3** | `[paper §3.3]` |
| Precision-loss gate | only for co-visible pixels with `‖r‖ < 8 px`; residuals **detached** | `[paper §3.3]` |
| EMA decay | **0.999** | `[paper §3.3]` |
| Strides `S` | `{1, 2, 4}` | `[paper Eq. 5]` |
| Refiner training resolution | 640 × 640 exclusively | `[paper §3.5]` |
| Cholesky epsilon | **1e-6** | `[paper §3.3]` = `[repo: refiner.py:201]` ✅ |
