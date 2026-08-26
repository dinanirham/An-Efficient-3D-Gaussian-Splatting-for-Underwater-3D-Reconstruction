# §1 — Taxonomic placement and modification

## Base method extended

**DKM: Dense Kernelized Feature Matching for Geometry Estimation**, Edstedt, Athanasiadis,
Wadenbäck & Felsberg, **CVPR 2023** (ref **[17]**) — same first author, and the paper is
explicit and consistent about it:

> "We use the recent SotA dense feature matching model **DKM [17] as our baseline**. For
> consistency, we adapt the terminology used there." `[paper §3.1]`

The inheritance is deep, not nominal:

| Inherited from DKM | Evidence |
|---|---|
| The coarse-to-fine dense-warp formulation `(Ŵ^{A→B}, p^A)` | `[paper §3.1, Eqs. 1-4]` |
| The **Gaussian Process match encoder `E`** — kept unchanged | `[paper §3.1]` "We use a Gaussian Process [38] as the match encoder E as in previous work [17]" |
| The refiner architecture: ConvNets at strides {1,2,4,8}, conditioned on the previous warp via stacked features + a local correlation volume | `[paper §3.1]` "We use the same architecture as in the baseline" |
| **Gradient detachment between refiners** | `[paper §3.1]` "Following DKM, we detach the gradients between the refiners" |
| The `λ` hyperparameter weighting the marginal vs. the conditional | `[paper Eq. 14]` "Following DKM [17] we add a hyperparameter λ" |
| Balanced correspondence sampling (10 000 matches) | `[paper §4.3]` |
| The entire training setup: split, LRs, schedule | `[paper §4.2]` "We use the training setup as in DKM [17]" |

Two further named lineages:

| Lineage | What is inherited | Evidence |
|---|---|---|
| **DINOv2** (ref [37]/[60]) | The **frozen** coarse feature encoder — the paper's contribution (a) | `[paper §3.2]` `[repo: romatch/models/encoders.py:33, 42, 50, 61-64]` |
| **Generalized Charbonnier** (ref [3]) | The robust regression loss for refinement | `[paper §3.4]` `[repo: romatch/losses/robust_loss.py:92]` |

Setup I of the ablation is literally "DKM, retrained by us" `[paper §4.1]`, and Setups II–VII
add one change each — so **Table 2 is a clean incremental audit of exactly this
inheritance**.

## The modification, in one sentence

RoMa replaces DKM's jointly-trained feature pyramid with a **frozen DINOv2 coarse encoder
paired with a *separate*, specialised VGG19 fine encoder**, swaps the ConvNet match decoder
for a **position-encoding-free Transformer predicting anchor probabilities over a 64×64
grid**, and splits the objective into **regression-by-classification at the coarse scale**
(where the match distribution is multimodal) and **robust regression at the fine scales**
(where it is unimodal).

## Design family, in one sentence

RoMa is a **detector-free, pixel-dense, two-view feature matcher** built on a **frozen
foundation-model backbone**, trained **offline and generically** — placing it, with
`../RoMaV2/`, in a completely different family from the eight per-scene-optimized
radiance-field folders in your set.

### The axis this paper actually establishes

The paper's most transferable finding is not any single component — it is a **tension it
identifies and then exploits**:

> "Our finding indicates that there is an **inherent tension between fine localizability and
> coarse robustness**." `[paper §3.2]`

The evidence is a genuine surprise, and it is measured twice:

| Encoder | as **coarse** features (Table 1: EPE / Robustness %) | as **fine** features (Table 2) |
|---|---|---|
| VGG19 | **worst** — 87.6 / 43.2 | **best** — Setup III improves over Setup II |
| ResNet50 | middle — 60.2 / 57.5 | worse than VGG19 |
| DINOv2 | **best** — 27.1 / 85.6 | n/a (stride 14 only, no fine features) |

So the paper does the only sensible thing: **use each encoder where it wins**, and stop
sharing weights between the two roles. Setup II (decoupling alone, same architecture) already
improves 100-PCK@1px from 17.0 → 16.0 `[paper Tab. 2]`, before any encoder is swapped.

### Where RoMa sits among matchers

| | RoMa | DKM (baseline) | RoMa v2 | LoFTR | Sparse (SuperGlue) |
|---|---|---|---|---|---|
| Density | pixel-dense | pixel-dense | pixel-dense | semi-dense | sparse |
| Coarse encoder | **frozen DINOv2 ViT-L/14** | trained ResNet50 | **frozen DINOv3 ViT-L/16** | learned | learned |
| Fine encoder | **separate VGG19** | shared with coarse | separate VGG19-BN | — | — |
| Match encoder | **Gaussian Process** | Gaussian Process | **attention** (GP removed) | attention | attention |
| Match decoder | **Transformer, anchor probs** | ConvNet, regression | DPT head | attention | attention |
| Coarse loss | **regression-by-classification** | L2 regression | robust regression + `L_NLL` | classification | classification |
| Fine loss | **robust (Charbonnier)** | clipped L2 | robust (Charbonnier) | L2 | — |
| Multi-view context in matcher | ❌ | ❌ | ✅ | ✅ | ✅ |
| Uncertainty output | overlap | overlap | overlap + **2×2 precision** | ❌ | matchability |
| Training data | MegaDepth (+ScanNet for indoor) | MegaDepth+ScanNet | **10 datasets** | MegaDepth/ScanNet | MegaDepth |

### Three consequences

1. **Freezing the backbone is a *robustness* argument, not an efficiency one** — though the
   paper notes both: "keeping the representations fixed **reduces overfitting** to the
   training set, enabling RoMa to be more robust. It is also additionally significantly
   cheaper computationally and requires less memory" `[paper §3.2]`. The payoff shows up
   exactly where you would predict: **WxBS +36% mAA** (58.9 → 80.1 over DKM), a benchmark of
   extreme appearance and modality change.
2. **The theoretical model is unusually load-bearing.** `[paper Eq. 10]` posits
   `q(x^A, x^B; s) = 𝒩(0, s²I) ∗ p(x^A, x^B; 0)` — matchability at scale `s` is the exact
   infinite-resolution matching diffused by a Gaussian. Near **motion boundaries** that
   diffusion makes the conditional **multimodal**, which is *why* the coarse stage needs
   classification and the fine stage does not. The losses are derived from KL divergence
   against this model `[paper Eqs. 11-18]`, not chosen empirically.
3. **RoMa is still the right choice for cross-modal matching.** `../RoMaV2/` concedes it:
   RoMa **60.8** vs RoMa v2 **55.4** mAA on WxBS `[RoMaV2 paper Tab. 11, §5]`, traced to the
   IR↔RGB subset. If any of your imagery is multi-modal, v1 wins.

## Position relative to the sibling folders

| Folder | Relationship |
|---|---|
| **`../EDGS/`** | **the concrete downstream consumer.** EDGS calls `roma_outdoor()` for *all* of its geometry and disables two of its features for speed (`upsample_preds=False`, `symmetric=False`) `[EDGS repo: source/corr_init.py:17, 538-539]`. It also reads `roma_model.sample_thresh` as its confidence threshold `[EDGS repo: source/corr_init.py:541]` — so RoMa's `sample_thresh = 0.05` `[repo: romatch/models/model_zoo/roma_models.py:54]` silently *is* EDGS's `τ_corr`. RoMa wins EDGS's Table 5 |
| **`../RoMaV2/`** | the successor by the same author. Every RoMa v2 table benchmarks against this model |
| `../colmap/` | the classical pipeline whose correspondence stage this replaces; RoMa is evaluated through HLoc on InLoc `[paper §4.4]` |
| `../gaussian-splatting/`, `../mini-splatting/`, `../CompGS/`, `../compact3d/`, `../OMG/` | orthogonal, but all consume COLMAP points derived from matching |
| `../seasplat/`, `../seathru_NeRF/`, `../nerf/` | orthogonal. Note `../seathru_NeRF/` §6 lists pose estimation "in bad visibility" as a limitation — a matcher-robustness problem, and WxBS-style robustness is precisely this model's strength |
