# §2 — Pipeline flowcharts

`[R:file:line]` = `[repo: file:line]`; `[P §x]` = `[paper §x]`.
Unlike `../RoMaV2/`, **training code is released here**, so every stage is verifiable.

---

## Stage A — Decoupled feature extraction

```mermaid
flowchart LR
    IA["I_A"]
    IB["I_B"]

    subgraph COARSE["F_coarse — FROZEN DINOv2 ViT-L/14"]
        D["dinov2_vitl14, .eval()<br/>weights from dl.fbaipublicfiles.com<br/>forward under torch.no_grad()<br/><i>[P §3.2]</i> <i>[R:encoders.py:33,42,61-64]</i>"]
        DH["stride 14 only — no fine features<br/>⇒ resolution must be a multiple of 14<br/><i>[R:roma_models.py:71-72]</i>"]
    end

    subgraph FINE["F_fine — SEPARATE VGG19"]
        V["tvm.vgg19_bn(...).features[:40]<br/>strides {1, 2, 4, 8}<br/><i>[P §3.2]</i> <i>[R:encoders.py:6-13]</i>"]
    end

    IA --> D --> DH
    IA --> V
    IB --> D
    IB --> V
```

> **The decoupling *is* the contribution.** DKM used one encoder for both roles; RoMa splits
> `F` into `{F_coarse,θ, F_fine,θ}` and sets `F_coarse,θ = DINOv2` `[P §3.2 / Eq. 7]`.
> Setup II of Table 2 shows that **decoupling alone** — same architecture, just unshared
> weights — improves 100-PCK@1px from 17.0 → 16.0, *before* any encoder is changed.
>
> **Frozen is enforced structurally, not by a flag.** The DINOv2 module is stored inside a
> *Python list* — `self.dinov2_vitl14 = [dinov2_vitl14]`, with the source comment
> *"ugly hack to not show parameters to DDP"* `[R:encoders.py:50]` — so it is never registered
> as a submodule, never sees the optimizer, and is additionally run under `torch.no_grad()`
> `[R:encoders.py:61]`. ✅ matches "We keep the DINOv2 encoder frozen throughout training"
> `[P §3.2]`.

---

## Stage B — Global matcher `G = D ∘ E` (coarse, stride 14, keyed `16`)

```mermaid
flowchart TD
    FC["φ^A_coarse, φ^B_coarse — DINOv2, dim projected to 512"]

    GP["<b>E — Gaussian Process match encoder</b><br/>UNCHANGED from DKM<br/>output dim gp_dim = 512<br/><i>[P §3.1]</i> <i>[R:roma_models.py:84]</i>"]

    CAT["concat → decoder_dim = 512 + 512 = 1024<br/><i>[R:roma_models.py:84-86]</i>"]

    TD["<b>D — Transformer match decoder</b><br/>5 × Block(1024, 8 heads, MemEffAttention)<br/><b>pos_enc = False</b><br/><i>[P §3.3]</i> <i>[R:roma_models.py:87-96]</i>"]

    OUT["output width = cls_to_coord_res² + 1 = 64² + 1 = <b>4097</b><br/>= K anchor logits + 1 matchability logit<br/><i>[P §3.3]</i> <i>[R:roma_models.py:87,91]</i>"]

    DEC["<b>ToWarp</b>: k̂ = argmax_k π_k, then local softargmax<br/>over N₄(k̂) — the anchor and its 4 neighbours<br/><i>[P Eq. 9]</i>"]

    FC --> GP --> CAT --> TD --> OUT --> DEC
```

> **Every architectural number in §3.3 checks out**: "5 ViT blocks, with 8 heads, hidden size
> D 1024, and MLP size 4096" `[P §3.3]` ⇒ `Block(decoder_dim=1024, 8)` × 5, and 4096 is the
> default 4× MLP ratio. `K = 64 × 64` ⇒ `cls_to_coord_res = 64`, output `64² + 1`.
> ✅ `[R:roma_models.py:87-96]`.
>
> **`pos_enc = False` is deliberate and argued** `[P §3.3]`: "In early experiments, we found
> that ConvNet coarse match decoders **overfit to the training resolution**. Additionally,
> they tend to be **over-reliant on locality** … it leads to oversmoothing for the coarse warp.
> … **By restricting the model to only propagate by feature similarity, we found that the
> model became significantly more robust.**"
>
> ⚠️ **Naming trap:** the coarse level is keyed **`16`** in the `corresps` dict
> `[R:matcher.py:856]` and in `scale_weights` `[R:robust_loss.py:106]`, even though the actual
> stride is **14** (DINOv2 patch size). See D-6.

---

## Stage C — Refiners (strides 8 → 4 → 2 → 1)

```mermaid
flowchart TD
    W16["Ŵ^{A→B}_coarse, p^{A,coarse} from Stage B"]

    R8["ConvRefiner @ stride 8"]
    R4["ConvRefiner @ stride 4"]
    R2["ConvRefiner @ stride 2"]
    R1["ConvRefiner @ stride 1"]

    COND["each refiner is conditioned on the previous warp by<br/>(a) stacking feature maps via the warp, and<br/>(b) a <b>local correlation volume</b> around the previous target<br/><i>[P §3.1]</i>"]

    DET["<b>⧉ gradients DETACHED between refiners</b><br/>warp upsampled bilinearly to the finer stride<br/><i>[P §3.1 'Following DKM']</i>"]

    OUT["Ŵ^{A→B}, p^A at full resolution<br/><i>[P Eq. 3]</i>"]

    W16 --> R8 --> R4 --> R2 --> R1 --> OUT
    COND -.-> R8
    DET -.-> R8
    DET -.-> R4
```

> Refiners "predict a **residual offset** for the estimated warp, and a **logit offset** for
> the certainty" `[P §3.1]`. `hidden_blocks = 8`, `kernel_size = 5`,
> `displacement_emb_dim = 64`, depthwise convs (`dw = True`) `[R:roma_models.py:99-129]`.
>
> **The inter-refiner detach is what makes the two losses independent** — see
> [`04-loss.md`](04-loss.md) §4.3.

---

## Stage D — Loss composition ✅ **verified against code**

```mermaid
flowchart TD
    GT["get_gt_warp(depth_A, depth_B, T_1to2, K1, K2)<br/>→ gt_warp x², gt_prob<br/><i>[R:robust_loss.py:126-136]</i>"]

    MASK["<b>supervision mask: prob &gt; 0.99</b><br/>⚠ not in the paper<br/><i>[R:robust_loss.py:51,71,91]</i>"]

    LOCAL["<b>local gating (scales ≤ 8):</b><br/>prob ×= (prev_epe &lt; (2/512)·local_dist[s]·s)<br/>local_dist = {1:4, 2:4, 4:8, 8:8}<br/>⚠ NOT IN THE PAPER<br/><i>[R:robust_loss.py:138-141; train_roma_outdoor.py:216]</i>"]

    subgraph COARSE_L["coarse (scale 16) — regression-by-classification"]
        CLS["cls_loss = CrossEntropy(gm_cls, GT_anchor)[prob&gt;0.99]<br/>GT_anchor = nearest of the 64×64 anchors<br/><i>[P Eq. 13]</i> <i>[R:robust_loss.py:43-51]</i>"]
        CERT1["certainty_loss = BCEWithLogits(gm_certainty, prob)<br/><i>[P Eq. 14]</i> <i>[R:robust_loss.py:52]</i>"]
        GM["gm_loss = cls_loss + <b>0.01</b>·certainty_loss<br/><i>[R:robust_loss.py:145]</i>"]
    end

    subgraph FINE_L["fine (scales 8,4,2,1) — robust regression"]
        REG["reg_loss = (c·s)^α · ((epe/(c·s))² + 1)^{α/2}<br/>α = 0.5, <b>c = 1e-4 in code / 0.03 in the paper</b><br/><i>[P Eqs. 15-16]</i> <i>[R:robust_loss.py:92; train:219-220]</i>"]
        CERT2["certainty_loss = BCEWithLogits(certainty, prob)<br/><i>[P Eq. 18]</i> <i>[R:robust_loss.py:88]</i>"]
        RG["reg = reg_loss + <b>0.01</b>·certainty_loss<br/><i>[R:robust_loss.py:158]</i>"]
    end

    TOT["<b>L = Σ_scales scale_weights[s]·(...)</b><br/>scale_weights = {1:1, 2:1, 4:1, 8:1, 16:1} — all 1<br/><i>[P Eq. 19]</i> <i>[R:robust_loss.py:106,146,159]</i>"]

    GT --> MASK --> LOCAL
    LOCAL --> CLS & CERT1 & REG & CERT2
    CLS --> GM
    CERT1 --> GM
    REG --> RG
    CERT2 --> RG
    GM --> TOT
    RG --> TOT
```

> **`λ = ce_weight = 0.01`** `[R:train_roma_outdoor.py:215]` — the paper introduces `λ` in
> Eq. 14 but **never states its value**.
>
> **`c = 1e-4`** in the training script `[R:train_roma_outdoor.py:220]` versus **"we choose
> c = 0.03"** `[P §3.4]` — a **300× discrepancy**, and the single most significant delta in
> this folder. See D-1.
>
> **Two undocumented masks** gate all supervision: `prob > 0.99`, and the local-EPE window.

---

## Stage E — Training ✅ **verified**

```mermaid
flowchart LR
    DATA["MegaDepth `train_loftr` split, <b>concatenated twice</b>:<br/>min_overlap = 0.01 AND min_overlap = 0.35<br/>weight_scenes(alpha = 0.75)<br/>horizontal-flip aug, shake_t = 32, rot_prob = 0<br/><i>[R:train_roma_outdoor.py:198-212]</i>"]

    RES["resolution: low 448², <b>medium 560²</b> (=14·8·5), high 672²<br/>default 'medium'<br/><i>[P §4.2]</i> <i>[R:train_roma_outdoor.py:23,301]</i>"]

    OPT["<b>AdamW</b>, weight_decay = 0.01<br/>encoder lr = STEP_SIZE·5e-6/8<br/>decoder lr = STEP_SIZE·1e-4/8<br/><i>[P §4.2]</i> <i>[R:train_roma_outdoor.py:222-225]</i>"]

    SCHED["N = 32 × 250 000 → <b>250k steps at batch 32</b><br/>MultiStepLR, single milestone at 90%<br/><i>[R:train_roma_outdoor.py:193,226-227]</i>"]

    DDP["DDP, grad clipping, AMP (float16)<br/>attenuate_cert = <b>False</b> during training<br/><i>[R:train_roma_outdoor.py:187,248]</i>"]

    DATA --> RES --> OPT --> SCHED --> DDP
```

> The LR expressions **are** the paper's linear scaling made explicit: "a canonical learning
> rate (for batchsize = 8) of 10⁻⁴ for the decoder, and 5 × 10⁻⁶ for the encoder(s)"
> `[P §4.2]` ⇒ `STEP_SIZE * 1e-4 / 8` and `STEP_SIZE * 5e-6 / 8` ✅.
>
> **Step count, optimizer, weight decay, LR schedule, augmentation and scene weighting are
> all absent from the paper.** So is the two-way `min_overlap` concatenation, which is a
> deliberate easy/hard mixture. See D-3, D-4.

---

## Stage F — Inference & downstream sampling

```mermaid
flowchart LR
    M["roma_outdoor() / roma_indoor()<br/><i>[R:roma_models.py]</i>"]
    SYM["symmetric = True — match both directions<br/>upsample_preds = True — second pass at upsample_res<br/><i>[R:roma_models.py:52,209-210]</i>"]
    ATT["attenuate_cert = True at inference (False in training)<br/>low-res certainty interpolated and used to attenuate<br/><i>[R:matcher.py:854-860]</i>"]
    SAMP["sample_mode = 'threshold_balanced'<br/><b>sample_thresh = 0.05</b><br/>KDE-balanced, 10 000 matches<br/><i>[P §4.3]</i> <i>[R:roma_models.py:54-55]</i>"]
    PIX["to_pixel_coordinates(...) — [−1,1]² → pixels"]
    EST["cv2 / poselib RANSAC, HLoc"]

    M --> SYM --> ATT --> SAMP --> PIX --> EST
```

> ⭐ **`sample_thresh = 0.05` is what `../EDGS/` reads as its confidence threshold**:
> `upper_thresh = roma_model.sample_thresh` `[EDGS repo: source/corr_init.py:541]`. EDGS's
> `τ_corr` of `[EDGS paper Eq. 9]` is therefore *this constant*, inherited silently.
>
> ⚠️ **EDGS disables two of these**: `upsample_preds = False` and `symmetric = False`
> `[EDGS repo: source/corr_init.py:538-539]` — so EDGS runs a single-pass, one-directional
> RoMa, not the configuration benchmarked in the paper.
