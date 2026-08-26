# §7 — Pseudocode: the full RoMa train step

Notation follows the paper (`I_A, I_B, φ_coarse, φ_fine, E, D, G, R_θ,i, Ŵ^{A→B}, p^A,
π_k, m_k, K, N₄, q, α, c, λ, s`). Tags: `[paper]` / `[repo: file:line]` / `[inferred]`.
⧉ = gradient-detached or non-differentiable. **⚠ = undocumented in the paper.**

Unlike `../RoMaV2/`, **the training code is released**, so this block is verified rather than
transcribed.

```text
════════════════════════════════════════════════════════════════════════════════════════
ALGORITHM  RoMa — one training step
════════════════════════════════════════════════════════════════════════════════════════
INPUT   F_coarse = DINOv2 ViT-L/14      ⧉ FROZEN (never registered as a submodule)
                                                          [paper §3.2] [repo: encoders.py:42,50,61]
        F_fine   = VGG19-BN, strides {1,2,4,8}, pretrained = False
                                                          [paper §3.2] [repo: encoders.py:6-13; roma_models.py:197]
        E        = Gaussian Process match encoder (gp_dim 512), unchanged from DKM
                                                          [paper §3.1] [repo: roma_models.py:84]
        D        = Transformer decoder: 5 × Block(1024, 8 heads), pos_enc = False,
                   output width K + 1 = 64² + 1 = 4097     [paper §3.3] [repo: roma_models.py:87-96]
        R_θ,i    = ConvRefiners at strides {8, 4, 2, 1}    [paper §3.1] [repo: roma_models.py:99-129]
CONST   K = 64², α = 0.5, c = 1e-4 ⚠ (paper: 0.03), λ = ce_weight = 0.01 ⚠
        local_dist = {1:4, 2:4, 4:8, 8:8} ⚠, local_largest_scale = 8 ⚠
        resolution = 560×560 (= 14·8·5); batch 32; 250k steps
                                                          [repo: train_roma_outdoor.py:23,193,214-220]
────────────────────────────────────────────────────────────────────────────────────────

 1  (I_A, I_B, depth_A, depth_B, T_1to2, K1, K2) ← sample from MegaDepth `train_loftr`
        ▲ built TWICE and concatenated: min_overlap = 0.01 AND 0.35 ⚠
          weight_scenes(alpha = 0.75) ⚠; horizontal-flip aug, shake_t = 32 ⚠
                                                          [repo: train_roma_outdoor.py:198-212]

    ── decoupled feature extraction ───────────────────────────────────────────────────
 2  ⧉ with torch.no_grad():
 3       φ^A_coarse ← DINOv2(I_A) ;  φ^B_coarse ← DINOv2(I_B)      stride 14
                                                          [paper Eq.7] [repo: encoders.py:61-64]
        ▲ FROZEN. Reduces overfitting ⇒ robustness. The +36% WxBS result is THIS.
                                                          [paper §3.2, Tab.4]
 4  φ^A_fine, φ^B_fine ← VGG19(I_A), VGG19(I_B)            strides {1,2,4,8}
                                                          [paper Eq.1] [repo: encoders.py:6-13]
        ▲ SEPARATE encoder. Decoupling alone gives 17.0 → 16.0; VGG19-over-RN50 gives
          16.0 → 14.5. Largest single contribution in Tab.2.   [paper §3.2, Tab.2]

    ── coarse global matching  G = D ∘ E  (scale keyed 16, actual stride 14 ⚠) ─────────
 5  z ← E(φ^A_coarse, φ^B_coarse)                          GP match encoder, dim 512
                                                          [paper Eq.2] [repo: roma_models.py:84]
 6  h ← concat(proj(φ^A_coarse), z)                        dim 512 + 512 = 1024
 7  [π_1..π_K, logit_p] ← D(h)                             K + 1 = 4097 channels
                                                          [paper §3.3] [repo: roma_models.py:87-91]
        ▲ pos_enc = False: "By restricting the model to only propagate by feature
          similarity, we found that the model became significantly more robust."
                                                          [paper §3.3] [repo: roma_models.py:96]

    ── ground truth ───────────────────────────────────────────────────────────────────
 8  x², prob ← get_gt_warp(depth_A, depth_B, T_1to2, K1, K2, H, W)
                                                          [paper §4.2] [repo: robust_loss.py:126-136]

    ── COARSE LOSS: regression-by-classification ──────────────────────────────────────
 9  G_anchors ← meshgrid(linspace(−1+1/64, 1−1/64, 64))    ⧉ the K anchor coords m_k
                                                          [paper §3.3] [repo: robust_loss.py:48-49]
        ▲ a TIGHT COVER: no overlap between anchors, no holes.  [paper footnote 2]
10  GT_k ← argmin_k ‖m_k − x²‖₂                            ⧉ nearest anchor per pixel
                                                          [paper Eq.13] [repo: robust_loss.py:50]
11  L_cls  ← CrossEntropy(π, GT_k)[ prob > 0.99 ]          ⚠ mask undocumented
                                                          [paper Eq.13] [repo: robust_loss.py:51]
12  L_cert ← BCEWithLogits(logit_p, prob)                  (unmasked — needs negatives)
                                                          [paper Eq.14] [repo: robust_loss.py:52]
13  L ← L ⊕ 1·( L_cls + λ·L_cert ),  λ = 0.01 ⚠           [paper Eq.14] [repo: robust_loss.py:145]
        ▲ classification, NOT regression, because at MOTION BOUNDARIES the coarse
          conditional is MULTIMODAL — an L2 target converges to the mean of two modes,
          correct for neither object.        [paper §3.4, Eq.10, Fig.3]

    ── decode the coarse warp ─────────────────────────────────────────────────────────
14  k̂(x) ← argmax_k π_k(x)                                 [paper Eq.9]
15  Ŵ_coarse ← Σ_{i ∈ N₄(k̂)} π_i m_i  /  Σ_{i ∈ N₄(k̂)} π_i     local softargmax
                                                          [paper Eq.9]
        ▲ classification for EXPRESSIVENESS, local regression for PRECISION.
          Without line 15 the coarse warp is quantised to the 64×64 anchor grid. [inferred]

    ── REFINEMENT: strides 8 → 4 → 2 → 1 ──────────────────────────────────────────────
16  Ŵ ← Ŵ_coarse ;  p ← logit_p
17  FOR i IN [8, 4, 2, 1]:
18      ⧉ Ŵ ← detach(Ŵ) ; p ← detach(p) ; bilinear-upsample to stride i
                                                          [paper §3.1 "Following DKM"]
        ▲ THIS is why no loss weighting is needed: the two objectives optimise
          DISJOINT parameter sets and cannot compete.       [paper §3.4]
19      corr ← LocalCorrelation(φ^A_fine,i, φ^B_fine,i, Ŵ)  (custom CUDA kernel; Linux only ⚠)
                                                          [paper §3.1] [repo: roma_models.py:60-62]
20      ΔŴ, Δp ← R_θ,i(φ^A_fine,i, φ^B_fine,i, Ŵ, p)        residual warp + logit offset
                                                          [paper Eq.4]
21      Ŵ ← Ŵ + ΔŴ ;  p ← p + Δp

        ── local supervision gate ⚠ (entirely absent from the paper) ──────────────────
22      ⟨if i ≤ local_largest_scale (8)⟩
23          prob ← prob · 𝟙[ ⧉prev_epe < (2/512)·local_dist[i]·i ]
                                                          [repo: robust_loss.py:138-141]
        ▲ a refiner is supervised ONLY where the COARSER scale was already within
          ≈local_dist[i]·i px. A HARD gate, not the soft down-weighting the robust
          loss provides — so the robust loss rarely sees the outliers it was
          designed for.                                    ⚠ delta D-2

        ── FINE LOSS: robust generalized-Charbonnier ──────────────────────────────────
24      epe ← ‖Ŵ − x²‖₂
25      cs  ← c · i                                        c = 1e-4 ⚠ (paper: 0.03)
26      L_reg  ← cs^α · ( (epe[prob>0.99]/cs)² + 1 )^{α/2},  α = 0.5
                                                          [paper Eqs.15-16] [repo: robust_loss.py:90-92]
        ▲ gradient "locally matches L2 … but globally decays with |x|^{-1/2} toward
          zero" — a far coarse init contributes almost nothing.   [paper Fig.4]
27      L_cert ← BCEWithLogits(p, prob)                    [paper Eq.18] [repo: robust_loss.py:88]
28      L ← L ⊕ 1·( L_reg + λ·L_cert )                     scale_weights all = 1
                                                          [paper Eq.19] [repo: robust_loss.py:106,158]
29      ⧉ prev_epe ← detach(‖Ŵ − x²‖₂)                     feeds line 23 at the next scale
                                                          [repo: robust_loss.py:160]

    ── update ─────────────────────────────────────────────────────────────────────────
30  BACKWARD(L)  under AMP float16                         [repo: train_roma_outdoor.py:187]
31  clip_grad_norm ; AdamW.step()                          ⚠ AdamW + wd 0.01 undocumented
        lr_encoder = STEP_SIZE·5e-6/8 ;  lr_decoder = STEP_SIZE·1e-4/8
                                                          [paper §4.2] [repo: train_roma_outdoor.py:222-225]
32  MultiStepLR: single milestone at 90% of N = 32×250 000 ⚠
                                                          [repo: train_roma_outdoor.py:193,226-227]
════════════════════════════════════════════════════════════════════════════════════════
                        Note: attenuate_cert = FALSE during training,
                              TRUE at inference ⚠         [repo: train_roma_outdoor.py:187 vs roma_models.py:56]
════════════════════════════════════════════════════════════════════════════════════════
```

## Inference path (what `../EDGS/` actually calls)

```text
 1  model ← roma_outdoor(device, coarse_res, upsample_res)        [repo: roma_models.py]
        defaults: symmetric = True, upsample_preds = True,
                  attenuate_cert = True, sample_thresh = 0.05,
                  sample_mode = "threshold_balanced"              [repo: roma_models.py:52-56]
 2  ⚠ EDGS OVERRIDES: upsample_preds ← False ; symmetric ← False
                                                          [EDGS repo: source/corr_init.py:538-539]
        ▲ so EDGS runs a SINGLE-PASS, ONE-DIRECTIONAL RoMa — not the benchmarked config
 3  warp, certainty ← model.match(im_A, im_B)
 4  ⚠ EDGS reads: upper_thresh ← model.sample_thresh (= 0.05)
                                                          [EDGS repo: source/corr_init.py:541]
        ▲ EDGS's τ_corr of [EDGS paper Eq.9] IS this constant, inherited silently
 5  matches ← model.sample(warp, certainty, num = M)      KDE-balanced
 6  kptsA, kptsB ← model.to_pixel_coordinates(matches, H_A, W_A, H_B, W_B)
        ▲ matches are normalized [−1,1]² — a classic integration bug
```

## What the control flow makes visible

1. **Lines 3 and 4 are the largest contribution in the paper, and they are one line apart.**
   Two encoders, two roles, no shared weights. Table 2's I→III accounts for **−2.5** of the
   total **−3.9** improvement — more than the decoder and both loss changes combined.

2. **Line 13 vs line 26: two structurally different losses, derived from one model.**
   Classification where the target is multimodal (motion boundaries), robust regression where
   it is unimodal but the initialisation may be far off. Both fall out of KL divergence
   against `q(x^A, x^B; s) = 𝒩(0, s²I) ∗ p(·; 0)` `[paper Eqs. 10-18]` — this is a *derived*
   objective, unusual in this comparison set.

3. **Line 18's detach is what buys line 28's uniform weights.** Because gradients are cut
   between stages *and* the encoders are unshared, the coarse and fine objectives touch
   disjoint parameters. The paper's "we do not need to tune any scaling" `[paper §3.4]` is
   confirmed by `scale_weights` being all ones `[repo: robust_loss.py:106]`.

4. **Lines 22–23 and 29 form a feedback loop the paper never mentions.** `prev_epe` from the
   coarser refiner gates supervision at the finer one. It is the *implementation* of "refinement
   is conditional on a previous estimate" — as a hard mask rather than a soft weight.

5. **Line 25's `c` is the single most consequential constant, and it disagrees with the paper
   by 300×.** It sets exactly where the Fig. 4 gradient curve bends.

6. **Line 15 is easy to miss and load-bearing.** Without the local softargmax,
   regression-by-classification would cap coarse precision at the 64×64 anchor grid — and the
   whole sub-pixel argument would collapse.
