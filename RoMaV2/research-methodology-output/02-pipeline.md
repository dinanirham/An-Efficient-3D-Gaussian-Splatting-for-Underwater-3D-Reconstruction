# §2 — Pipeline flowcharts

`[R:file:line]` = `[repo: file:line]`; `[P §x]` = `[paper §x]`.
⚠️ Training is **not released** `[R:src/romav2/romav2.py:172]`, so Stages D–E are
**paper-only**; Stages A–C and F are verified against code.

---

## Stage A — Input → frozen DINOv3 features

```mermaid
flowchart LR
    IMG["I_A, I_B ∈ ℝ^{H×W×3}, values in [0,1]<br/><i>[R:romav2.py:174]</i>"]
    PREC["<b>require float32_matmul_precision == 'highest'</b><br/>else RuntimeError<br/><i>[R:romav2.py:169-170]</i>"]
    RES["resize to setting resolution<br/>(precise: 800×800 coarse, 1280×1280 fine)<br/><i>[R:romav2.py:151-159]</i>"]
    DINO["<b>DINOv3 ViT-L/16, FROZEN</b><br/>layer_idx = [11, 17] → 2 feature layers<br/>dim 1024<br/><i>[P §3.2]</i> <i>[R:features.py:83-89]</i>"]
    OUT["f_A, f_B at stride 16"]

    IMG --> PREC --> RES --> DINO --> OUT
```

> **Frozen is the whole argument.** `frozen: bool = True` `[R:features.py:85]`. The paper's
> case against UFM is that finetuning the backbone costs robustness to extreme appearance
> change `[P §1]`. Table 1 justifies the DINOv2→DINOv3 swap with a linear-probe study:
> EPE **27.1 → 19.0**, robustness **77.0% → 86.4%** `[P Tab. 1]`.
>
> Patch size grows 14 → 16, which the paper notes and accepts: DINOv3 "is more robust than
> its predecessor **despite its slightly larger patch size**" `[P §3.2]`.

---

## Stage B — Coarse matcher (stride 4 output)

```mermaid
flowchart TD
    FA["f_A (DINOv3, frozen)"]
    FB["f_B (DINOv3, frozen)"]

    MVT["<b>Multi-view Transformer — ViT-B</b><br/>alternating frame-wise ↔ global attention<br/>(following VGGT [50])<br/>RoPE on frame-wise attention ONLY<br/><i>[P §3.2]</i> <i>[R:matcher.py:70-73]</i>"]

    SIM["similarity matrix S ∈ ℝ^{M×N}<br/>single-headed attention<br/><b>replaces RoMa's Gaussian Process</b><br/>temp = 0.1  (RoMa: 0.2)<br/><i>[P §3.2]</i> <i>[R:matcher.py:75-76]</i>"]

    EMB["Softmax(S)·x_B — position embeddings as in RoMa<br/>scale = <b>1</b>, FIXED  (RoMa: init 8, learned)<br/><i>[P §3.2, §3.5]</i> <i>[R:matcher.py:77-78]</i>"]

    DPT["<b>DPT head</b> [32]<br/>jointly processes token embeddings,<br/>Softmax(S)x_B, and DINOv3 features<br/><i>[P §3.2]</i> <i>[R:dpt.py]</i>"]

    W4["W at stride 4 (4× downsampled)"]
    P4["p (confidence) at stride 4"]

    FA --> MVT
    FB --> MVT
    MVT --> SIM --> EMB --> DPT
    MVT --> DPT
    FA --> DPT
    DPT --> W4
    DPT --> P4
```

> **Why the GP had to go** `[P §3.2]`: "we found that in practice the **gradients through the
> GP were not sufficiently informative** to yield improvements, and caused **stability
> issues** during training." The GP is replaced by plain single-headed attention, and the
> lost supervision is restored by the auxiliary `L_NLL` (Stage D).
>
> **Two resolution-robustness fixes**, both verified in code `[R:matcher.py:75-78]`:
> `temp` **0.2 → 0.1** (undocumented in the paper — see D-1) and `scale` **8 (learned) → 1
> (fixed)**, the latter explained in `[P §3.5]`: high-frequency absolute position embeddings
> interpolate badly across resolutions, and the paper speculates this is "the cause of the
> issue that requires UFM to be run at a fixed resolution".

---

## Stage C — Refiners (strides 4 → 2 → 1)

```mermaid
flowchart TD
    VGG["<b>VGG19-BN</b> fine features<br/>pretrained = <b>False</b><br/><i>[P Fig.4]</i> <i>[R:features.py:179-182]</i>"]

    R4["<b>Refiner @ stride 4</b><br/>feat 256, proj 192, disp_emb 79,<br/>local_corr_radius 3 → 7×7 window<br/>total 192·2 + 79 + 7² = 512<br/><i>[R:refiner.py:239-247]</i>"]
    R2["<b>Refiner @ stride 2</b><br/>feat 128, proj 48, disp_emb 23,<br/>local_corr_radius 1 → 3×3<br/>total 48·2 + 23 + 3² = 128<br/><i>[R:refiner.py:248-256]</i>"]
    R1["<b>Refiner @ stride 1</b><br/>feat 64, proj 12, disp_emb 8,<br/><b>no local correlation</b><br/>total 12·2 + 8 = 32<br/><i>[R:refiner.py:257-265]</i>"]

    LC["<b>local_corr CUDA kernel</b><br/>PyTorch extension `fused-local-corr`<br/>Linux only<br/><i>[P §3.3]</i> <i>[R:local_correlation.py:4-7; pyproject.toml]</i>"]

    OUT["ΔW, Δp, and 3 precision params per pixel<br/>confidence_dim = 4 = 1 overlap + 3 precision<br/><i>[R:refiner.py:77]</i>"]

    VGG --> R4 --> R2 --> R1 --> OUT
    LC -.-> R4
    LC -.-> R2
```

> **All channel dimensions are powers of two** — the comments in `refiner.py` show the
> arithmetic (512 / 128 / 32), matching `[P §3.3]`: "We further change all channel dimensions
> to be powers of two, which further boosts performance." The refiner type is literally named
> `"roma-4-pow2"` `[R:refiner.py:228]`.
>
> **Only 3 refiners are needed, vs RoMa's 5.** "As the matcher predicts at **stride 4**, in
> contrast to RoMa's **stride 14**, we only need to refine at strides ≤ 4" `[P §3.3]`. This is
> a direct consequence of the DPT head, and it is where much of the 1.7× speedup comes from.
>
> **The CUDA kernel is optional but Linux-only**: `local_corr` is imported in a `try/except`
> `[R:local_correlation.py:4-7]` and the dependency is gated `sys_platform == 'linux'`
> `[R:pyproject.toml]`. Table 8 measures its effect: **5.6 → 4.8 GB** at nearly identical
> throughput (30.3 → 30.9 pairs/s) `[P Tab. 8]`.

---

## Stage D — Training objectives ⚠️ **paper-only, no released code**

```mermaid
flowchart TD
    subgraph MATCH["Stage 1: coarse matcher — 300k steps, batch 128, lr 4e-4"]
        NLL["<b>L_NLL</b> = Σ_m −log Softmax(S_m)_{n*}<br/>n* = patch closest to the GT warp<br/>'a dense directional version of LoFTR'<br/><i>[P Eq.1]</i>"]
        W1["L_warp — robust regression (Charbonnier)"]
        OV1["λ·L_overlap, λ = 0.1 (as in RoMa)"]
        LM["<b>L_matcher = L_NLL + L_warp + 0.1·L_overlap</b><br/><i>[P Eq.2]</i>"]
        NLL --> LM
        W1 --> LM
        OV1 --> LM
    end

    FREEZE["<b>freeze the matcher, run in inference mode</b><br/><i>[P §3.3]</i>"]

    subgraph REF["Stage 2: refiners — 300k steps, batch 64, lr 4e-4"]
        WARP["L_warp = ((i·c)/…) generalized Charbonnier [2]<br/>α = 0.5, c = 1e-3, per stride i ∈ {1,2,4}"]
        OV2["λ_ov · L_ov — pixel-wise BCE, λ_ov = 1e-2"]
        PREC["λ_prec · L_prec — Gaussian NLL of residuals<br/>λ_prec = 1e-3, residuals DETACHED,<br/>only where ‖r‖ &lt; 8 px<br/><i>[P Eq.4]</i>"]
        LR["<b>L_refiners = Σ_{i∈{1,2,4}} L_warp + λ_ov L_ov + λ_prec L_prec</b><br/><i>[P Eq.5]</i>"]
        WARP --> LR
        OV2 --> LR
        PREC --> LR
    end

    EMA["<b>EMA on refiner weights, decay 0.999</b><br/>removes a measured ±0.1 px sub-pixel bias<br/><i>[P §3.3, Fig.5]</i>"]

    MATCH --> FREEZE --> REF --> EMA
```

> **The two-stage decoupling is inherited from UFM** `[P §3.1]`: "While some previous works
> [11,12] decouple gradients between matchers and refiners but still **train both jointly**,
> we instead opt for a **two-stage training paradigm** inspired by UFM. This enables rapid
> experimentation."
>
> **None of this is in the repo.** `assert not self.training, "Currently only inference mode
> released"` `[R:romav2.py:172]`. See [`04-loss.md`](04-loss.md).

---

## Stage E — Training data mixture ⚠️ **paper-only**

```mermaid
flowchart LR
    subgraph WIDE["Wide-baseline (weight 1 each)"]
        MD["MegaDepth — 169 scenes, MVS"]
        AMD["AerialMD — 124, MVS"]
        BMVS["BlendedMVS — 493, Mesh"]
        HS["Hypersim — 393, Graphics"]
        TA["TartanAir v2 — 46, Graphics"]
        MF["Map-Free — 397, MVS"]
        SN["ScanNet++ v2 — 856, Mesh"]
    end
    subgraph SMALL["Small-baseline (down-weighted)"]
        US["UnrealStereo4k — 8 scenes, w = 0.01"]
        VK["Virtual KITTI 2 — 5 scenes, w = 0.01"]
        FT["FlyingThings3D — 2239 scenes, w = 0.5"]
    end
    TOT["<b>5069 scenes total</b><br/><i>[P Tab. 3]</i>"]
    WIDE --> TOT
    SMALL --> TOT
```

> RoMa v1 trained on **MegaDepth alone**. The stated purpose of each half `[P §3.4]`: the
> **aerial** datasets give robustness to "large rotations and air-to-ground viewpoint
> changes"; the **small-baseline** ones make the model "significantly better at predicting
> fine-grained details" and — notably — enable **textureless-surface** matching in driving
> scenes "despite only training on the very small-scale dataset VKITTI2".

---

## Stage F — Inference & downstream sampling

```mermaid
flowchart LR
    M["model(img_A, img_B)"]
    BI{"bidirectional?<br/>(True for precise / benchmark settings)"}
    AB["W^{A↦B}, p^{A↦B}, Σ⁻¹^{A↦B}"]
    BA["W^{B↦A}, p^{B↦A}, Σ⁻¹^{B↦A}"]

    MAP["_map_confidence():<br/>overlap = sigmoid(conf[...,:1])<br/>precision = prec_mat_from_prec_params(conf[...,1:4])<br/><i>[R:romav2.py:61-66; geometry.py:168-174]</i>"]
    THR["p̂ = max(1_{p &gt; 0.05}, p)<br/>thresholded distribution<br/><i>[P Eq.6]</i> <i>[R:romav2.py:126]</i>"]
    SAMP["model.sample(preds, 5000)<br/>balanced sampling by kernel density estimate<br/><i>[P §4.1]</i> <i>[R:romav2.py:372-...]</i>"]
    PIX["to_pixel_coordinates(matches, H_A, W_A, H_B, W_B)<br/>([−1,1]² → pixels)<br/><i>[R:README.md; geometry.py:to_pixel]</i>"]
    EST["cv2.findFundamentalMat / RANSAC / HLoc<br/><i>[R:README.md]</i>"]

    M --> BI
    BI -- yes --> AB & BA
    BI -- no --> AB
    AB --> MAP --> THR --> SAMP --> PIX --> EST
```

> **Precision parameterisation, verified end-to-end.** `[P §3.3]` specifies Cholesky factors
> `l11 = Softplus(z11) + 1e-6`, `l21 = z21`, `l22 = Softplus(z22) + 1e-6`, then
> `Σ⁻¹ = LLᵀ`. Code: `chol_eps = 1e-6`; `l00 = F.softplus(delta_confidence[..., 1]) + chol_eps`;
> `l11 = F.softplus(delta_confidence[..., 3]) + chol_eps` `[R:refiner.py:201-204]`, assembled
> into a symmetric 2×2 by `prec_mat_from_prec_params` `[R:geometry.py:168-174]`. ✅ matches.
>
> **Precision is accumulated additively across strides**: `Σ⁻¹_i = Σ_{j≥i} Σ⁻¹_j`, "using the
> fact that information is additive in the precision parameterization" `[P §3.3]` — the
> correct way to fuse independent Gaussian estimates.
