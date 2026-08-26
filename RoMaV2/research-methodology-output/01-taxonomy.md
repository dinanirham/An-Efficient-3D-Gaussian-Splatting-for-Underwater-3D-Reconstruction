# §1 — Taxonomic placement and modification

## Base method extended

**RoMa: Robust Dense Feature Matching**, Edstedt, Sun, Bökman, Wadenbäck & Felsberg,
**CVPR 2024** (ref **[12]**) — the direct predecessor, same first author, and the
`../RoMa/` folder in this comparison set.

The paper is explicit that this is an incremental-but-broad upgrade: "we introduce RoMa v2,
which **builds on RoMa** and features several improvements to increase robustness while
simultaneously reducing the computational cost" `[paper §1]`.

Three further named lineages, each load-bearing:

| Lineage | What is inherited | Evidence |
|---|---|---|
| **DINOv3**, Siméoni et al. (ref **[41]**) | The **frozen** coarse-matching feature extractor — replacing RoMa's DINOv2 | `[paper §3.2]` `[repo: src/romav2/features.py:83 — name: DescriptorName = "dinov3_vitl16"; :85 frozen: bool = True]` |
| **UFM**, (ref **[56]**), NeurIPS'25 | The **decoupled two-stage training paradigm** (matcher first, then frozen; refiners after) — "inspired by UFM [56]. This enables rapid experimentation" | `[paper §3.1, §3.3]` |
| **VGGT**, (ref **[50]**), CVPR'25 | The **alternating frame-wise / global attention** pattern in the multi-view Transformer | `[paper §3.2]` `[repo: src/romav2/matcher.py:73 — mv_vit_attention_mode: Literal["alternating"]]` |
| **DPT**, Ranftl et al. (ref **[32]**) | The dense prediction head emitting warp + confidence | `[paper §3.2]` `[repo: src/romav2/dpt.py]` |
| **DKM** (ref [11]) → RoMa → RoMa v2 | The coarse-to-fine dense-warp formulation itself, and the generalized Charbonnier warp loss | `[paper §2, §3.3]` |

## The modification, in one sentence

RoMa v2 replaces RoMa's Gaussian-Process coarse matcher with a **multi-view Transformer over
frozen DINOv3 features supervised by an auxiliary patch-level NLL objective**, decouples
matcher and refiner training into two stages, adds a **predicted per-pixel 2×2 error
precision matrix**, and cuts runtime and memory through a custom local-correlation CUDA
kernel and power-of-two channel widths.

## Design family, in one sentence

RoMa v2 is a **detector-free, pixel-dense, two-view feature matcher** built on a **frozen
foundation-model backbone**, trained **offline and generically** (not per-scene) — which
places it in a completely different family from every other folder in your set except
`../RoMa/`: it is a **feed-forward, generalizable, pre-trained** model, whereas the eight
radiance-field folders are all **per-scene optimized**.

### Where it sits on the field's axes

| | RoMa v2 | RoMa v1 | UFM | LoFTR | DKM | Sparse (SuperGlue/LightGlue) | Feed-forward 3D (VGGT/MASt3R) |
|---|---|---|---|---|---|---|---|
| Density | **pixel-dense** | pixel-dense | pixel-dense | semi-dense | pixel-dense | sparse | dense point maps |
| Backbone | **frozen DINOv3** | frozen DINOv2 | **finetuned** | learned | learned | learned | learned |
| Coarse mechanism | **MV-Transformer + attention** | **Gaussian Process** | transformer | attention | feature pyramid | attention | transformer |
| Multi-view context in matcher | ✅ | ❌ | ✅ | ✅ | ❌ | ✅ | ✅ |
| Uncertainty output | **overlap + 2×2 precision** | overlap only | overlap only | ❌ | overlap | matchability | ❌ |
| Training data | **10 datasets** | MegaDepth only | mixed | MegaDepth/ScanNet | MegaDepth | MegaDepth | large mixed |
| Sub-pixel precision | **highest** | high | **low** | medium | high | medium | low |

The paper frames its own contribution as resolving a specific trade-off it identifies
between its two closest competitors:

> "RoMa still struggles in many challenging scenarios … Additionally, RoMa has a significant
> runtime and memory footprint … Recently, UFM showed that dense matching can be made
> significantly faster … However, UFM requires **finetuning of the pretrained feature
> extracting backbone**, which leads to worse performance on datasets with extreme appearance
> changes such as WxBS. Furthermore, UFM performs worse than RoMa on benchmarks that require
> **subpixel precision**." `[paper §1]`

**Freezing the backbone is the pivot of that argument**, and it is verifiable in code:
`frozen: bool = True` `[repo: src/romav2/features.py:85]`. Table 13 supplies the direct
evidence for the sub-pixel half — artificially degrading RoMa v2's residuals to UFM's error
distribution drops MegaDepth-1500 AUC@5 from **62.8 → 46.3**, close to UFM's 41.5
`[paper Tab. 13]`. That is an unusually clean isolation of *why* one model beats another.

### Four consequences

1. **The GP → attention swap has a stated failure mode behind it.** "A naive approach would
   be to add a Multi-view Transformer to RoMa before the GP, however, we found that in
   practice **the gradients through the GP were not sufficiently informative** to yield
   improvements, and caused **stability issues** during training" `[paper §3.2]`. The GP was
   removed because it blocked gradient flow, not because attention is fashionable.
2. **v2 is *less* robust than v1 in one specific regime, and says so.** On **WxBS**
   (multi-modal, IR↔RGB) RoMa v2 scores **55.4 mAA** vs RoMa's **60.8** `[paper Tab. 11]`,
   conceded in §5: "Compared to RoMa, our model is slightly less robust to extreme changes in
   modality." The backbone ablation shows the same sign — DINOv2 **35.6** vs DINOv3 **34.2**
   on WxBS, while DINOv3 wins on Hypersim (79.2 vs 78.1) `[paper Tab. 10]`. **This is the
   one place where v1 is the right choice**, and it matters for anyone matching across
   modalities.
3. **Predictive covariance is a genuinely new output**, and the downstream gain is large:
   using it to reweight residuals lifts Hypersim AUC@1 from **54.9 → 76.4** `[paper Tab. 12]`.
   Nothing else in your comparison set consumes such a signal yet — but a
   covariance-weighted triangulation is an obvious extension for `../EDGS/`.
4. **Not a radiance field.** It has no scene representation, no per-scene optimization, no
   rendering. Comparisons against the other eight folders are only meaningful *through* a
   downstream consumer.

## Position relative to the sibling folders

| Folder | Relationship |
|---|---|
| **`../RoMa/`** | **the direct predecessor** (ref [12]); every table in this paper compares against it |
| **`../EDGS/`** | **the concrete downstream consumer in this set.** EDGS calls `roma_outdoor()` for all its geometry `[EDGS repo: source/corr_init.py:17, 533-537]`, and its Table 5 ablates LoFTR / DKM / RAFT / RoMa. RoMa v2 is the untested upgrade — see [`08-computational-profile.md`](08-computational-profile.md) §8.5 |
| `../colmap/` | the classical SfM pipeline whose correspondence stage this replaces; the paper positions both under "Feed-forward Reconstruction" `[paper §2]` |
| `../gaussian-splatting/`, `../mini-splatting/`, `../CompGS/`, `../compact3d/`, `../OMG/` | orthogonal — but all of them consume COLMAP points that come from matching |
| `../seasplat/`, `../seathru_NeRF/`, `../nerf/` | orthogonal. Note both underwater papers rely on COLMAP poses, and `../seathru_NeRF/` §6 lists pose estimation "in bad visibility" as a limitation — a matcher-quality problem |
