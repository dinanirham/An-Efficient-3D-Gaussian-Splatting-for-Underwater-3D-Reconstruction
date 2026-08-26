# §7 — Pseudocode

Notation follows the paper (`I_A, I_B, W^{A↦B}, p^{A↦B}, Σ⁻¹, S, f_A, f_B, r_θ, z11/z21/z22,
L, λ, λ_ov, λ_prec, α, c`). Tags: `[paper]` / `[repo: file:line]` / `[inferred]`.
⧉ = non-differentiable / detached. **`[paper-only]`** = no released implementation.

Two blocks are given because the method has two: the **training** procedure (paper-only) and
the **inference** procedure (fully verifiable, and the one you will actually run).

---

## Part 1 — Training ⚠️ `[paper-only]` — no code exists `[repo: romav2.py:172]`

```text
════════════════════════════════════════════════════════════════════════════════════════
STAGE 1 — COARSE MATCHER          300k steps · batch 128 · lr 4e-4 · ≈38M pairs
                                                                    [paper §3.2]
════════════════════════════════════════════════════════════════════════════════════════
 1  FOR step = 1 … 300 000:
 2      (I_A, I_B, W_GT, p_GT) ← sample from the 10-dataset mixture   [paper Tab.3]
                        ▲ wide-baseline (w=1): MegaDepth, AerialMD, BlendedMVS, Hypersim,
                          TartanAirV2, MapFree, ScanNet++v2
                          small-baseline: FlyingThings3D (0.5), UnrealStereo4k (0.01),
                          VKITTI2 (0.01).  5069 scenes total.
 3      resize to a randomly chosen resolution / aspect ratio        [paper §3.5] ⚠ exact
                        ▲ list UNRECOVERABLE from the PDF text layer — see delta D-10
 4      f_A ← DINOv3_ViT-L/16(I_A)   ⧉ FROZEN                        [paper §3.2] [repo: features.py:85]
 5      f_B ← DINOv3_ViT-L/16(I_B)   ⧉ FROZEN
 6      t_A, t_B ← MultiViewTransformer_ViT-B(f_A, f_B)
                        alternating frame-wise ↔ global attention (VGGT-style);
                        RoPE on the FRAME-WISE attention only, on a NORMALIZED grid
                                                                    [paper §3.2, §3.5] [repo: matcher.py:70-73]
 7      S ← Attention(t_A, t_B) / temp        S ∈ ℝ^{M×N}, temp = 0.1
                                                                    [paper §3.2] [repo: matcher.py:76]
                        ▲ single-headed attention REPLACES RoMa's Gaussian Process, because
                          "gradients through the GP were not sufficiently informative … and
                          caused stability issues"                   [paper §3.2]
 8      e   ← Softmax(S) · x_B                x_B = position embeddings, scale = 1 FIXED
                                                                    [paper §3.2, §3.5] [repo: matcher.py:78]
 9      W_θ, p_θ ← DPT_head( t_A, e, f_A )    at stride 4            [paper §3.2] [repo: dpt.py]

        ── loss ────────────────────────────────────────────────────────────────────────
10      n*  ← argmin_n ‖ patch_n(B) − W_GT(patch_m(A)) ‖   per patch m
11      L_NLL ← Σ_{m=1..M} −log( Softmax(S_m)_{n*} )                 [paper Eq.1]
                        ▲ direct supervision of S — the capability the GP used to provide.
                          "a dense directional version of, e.g. LoFTR"  [paper §3.2]
12      r_θ ← W_θ − W_GT                                             [paper Eq.3]
13      L_warp ← GeneralizedCharbonnier(r_θ; α = 0.5, c = 1e-3)      [paper §3.3, ref 2]
                        ▲ REPLACES RoMa's classification-by-regression term  [paper §3.2]
14      L_ov  ← BCE(p_θ, p_GT)                                       [paper §3.2]
15      L_matcher ← L_NLL + L_warp + 0.1 · L_ov                      [paper Eq.2]
16      AdamW step                                                   [inferred: repo types.py]

17  ⧉ FREEZE the entire matcher; switch it to inference mode          [paper §3.3]

════════════════════════════════════════════════════════════════════════════════════════
STAGE 2 — REFINERS                300k steps · batch 64 · lr 4e-4 · ≈19M pairs
                                  ALL at resolution 640 × 640        [paper §3.3, §3.5]
════════════════════════════════════════════════════════════════════════════════════════
18  FOR step = 1 … 300 000:
19      (I_A, I_B, W_GT, p_GT) ← sample                              [paper Tab.3]
20      W_4, p_4 ← FROZEN_matcher(I_A, I_B)          ⧉ no gradient   [paper §3.3]
21      g_A, g_B ← VGG19-BN(I_A), VGG19-BN(I_B)      pretrained = False
                                                                    [repo: features.py:179-182]
22      FOR i IN [4, 2, 1]:                          coarse → fine   [repo: refiner.py:239-265]
23          corr ← LocalCorrelation(g_A, g_B, W_i; radius = {3, 1, None}[i])
                        ▲ custom CUDA kernel; −14% memory at equal throughput
                                                                    [paper §3.3] [paper Tab.8]
24          ΔW, Δp, (z11, z21, z22) ← ConvRefiner_i( g_A, corr, emb(W_i), p_i )
                        ▲ confidence_dim = 4 = 1 overlap + 3 precision params
                                                                    [repo: refiner.py:77]
25          W_{i/2} ← W_i + ΔW ;   p_{i/2} ← p_i + Δp

            ── precision head ──────────────────────────────────────────────────────────
26          l11 ← Softplus(z11) + 1e-6 ;  l21 ← z21 ;  l22 ← Softplus(z22) + 1e-6
27          L   ← [[l11, 0], [l21, l22]] ;   Σ⁻¹_i ← L Lᵀ
                        ▲ positive-definite BY CONSTRUCTION — no constraint needed
                                                                    [paper §3.3] [repo: refiner.py:201-204]
28          r_i ← W_i − W_GT
29          ⟨if co-visible AND ‖r_i‖ < 8 px⟩                         [paper §3.3]
30              L_prec_i ← ½ ⧉r_iᵀ Σ⁻¹_i ⧉r_i − ½ log det(Σ⁻¹_i) + log 2π
                                                                    [paper Eq.4]
                        ▲ ⧉ RESIDUALS ARE DETACHED. Without this the model could minimise
                          L_prec by INFLATING residuals where it predicted low precision —
                          a self-fulfilling degeneracy. Same mechanism as seasplat's
                          Ẑ.detach() and seathru_NeRF's detached δ^bs.        [paper §3.3]
                        ▲ the ‖r‖<8px gate exists because Gaussian NLL has NO robustness
                          to the gross outliers endemic to dense matching.

31      L_refiners ← Σ_{i∈{1,2,4}} [ L_warp,i + 1e-2·L_ov,i + 1e-3·L_prec_i ]
                                                                    [paper Eq.5]
32      AdamW step
33      θ_EMA ← 0.999·θ_EMA + 0.001·θ                                [paper §3.3]
                        ▲ removes a measured ±0.1px sub-pixel bias that "appears almost
                          random" over training (Fig.5a → 5b). Selective: +1.4 AUC@5 on
                          MegaDepth, +0.0 on ScanNet.                [paper Tab.9]
════════════════════════════════════════════════════════════════════════════════════════
```

---

## Part 2 — Inference ✅ fully verified against code

```text
════════════════════════════════════════════════════════════════════════════════════════
ALGORITHM  RoMaV2.forward(I_A, I_B) → warps, overlaps, precisions
════════════════════════════════════════════════════════════════════════════════════════
 1  REQUIRE torch.get_float32_matmul_precision() == "highest"  else RuntimeError
                                                                    [repo: romav2.py:169-170]
                        ▲ hard error, not a warning. Any process that enabled TF32 elsewhere
                          crashes on the first forward — delta D-5
 2  REQUIRE not self.training                                       [repo: romav2.py:172]
 3  ASSUME images in [0, 1]                                         [repo: romav2.py:174]

 4  (H_lr, W_lr, H_hr, W_hr, bidirectional, threshold) ← SETTING     [repo: romav2.py:119-160]
       turbo      320²  / —      / uni  / —
       fast       512²  / —      / uni  / —
       base       640²  / —      / uni  / —      ← Tables 6, 7
       precise    800²  / 1280²  / bi   / —      ← LIBRARY DEFAULT
       mega1500 … 800²  / 1024²  / bi   / 0.05   ← Table 4
                        ▲ THREE different settings back three different tables, and the
                          default matches NONE of them — delta D-3

 5  f_A ← DINOv3(I_A_lr) ;  f_B ← DINOv3(I_B_lr)   ⧉ frozen         [repo: romav2.py:179-180]
 6  out ← matcher(f_A, f_B, I_A_lr, I_B_lr, bidirectional)          [repo: romav2.py:181-183]
 7  W_AB, c_AB ← out["warp_AB"], out["confidence_AB"]               [repo: romav2.py:186-189]
 8  ⟨if bidirectional⟩ W_BA, c_BA ← out["warp_BA"], out["confidence_BA"]
    ⟨else⟩             W_BA, c_BA ← None, None                      [repo: romav2.py:190-196]

    ── refinement, once at low res and (optionally) again at high res ──────────────────
 9  FOR stage, (I_A, I_B) IN enumerate([(I_A_lr, I_B_lr), (I_A_hr, I_B_hr)]):
10      ⟨if I_A is None⟩ break                    (single-stage settings)
11      W, c ← interpolate(⧉W, ⧉c, H//4, W//4)                      [repo: romav2.py:32-58]
                        ▲ BOTH detached between stages — refinement passes do not
                          backprop into one another (moot at inference, but it is how the
                          graph is built)
12      ⟨if stage > 0⟩ c[..., 1:] ← 0            ⧉ zero the precision channels
                        ▲ source comment: "delta at 4 is absolute, and … for the second pass
                          we therefore can't use first pred. overlap is fine since it's
                          relative to matcher pred."                [repo: romav2.py:46-49]
13      FOR i IN [4, 2, 1]:
14          W, c ← refiner_i(W, c, VGG19BN(I_A), VGG19BN(I_B))      [repo: refiner.py]

    ── decode outputs ──────────────────────────────────────────────────────────────────
15  overlap   ← sigmoid(c[..., :1])                                 [repo: romav2.py:62]
16  ⟨if threshold is not None⟩  overlap[overlap > 0.05] ← 1.0       [repo: romav2.py:63-64]
                        ▲ realises p̂ = max(1_{p>0.05}, p)            [paper Eq.6]
                          BENCHMARK SETTINGS ONLY — delta D-4
17  precision ← prec_mat_from_prec_params(c[..., 1:4])              [repo: romav2.py:65; geometry.py:168-174]
                        ▲ symmetric 2×2 assembled from 3 params

18  RETURN warp_AB, warp_BA, overlap_AB, overlap_BA, precision_AB, precision_BA

════════════════════════════════════════════════════════════════════════════════════════
DOWNSTREAM  (as documented in the README)
════════════════════════════════════════════════════════════════════════════════════════
19  matches, overlaps, prec_AB, prec_BA ← model.sample(preds, 5000)
                        ▲ balanced sampling via kernel density estimate; when bidirectional,
                          precisions are grid_sampled through the OPPOSITE warp and stacked,
                          so each match carries both views' uncertainty
                                                                    [paper §4.1] [repo: romav2.py:372-412]
20  kptsA, kptsB ← model.to_pixel_coordinates(matches, H_A, W_A, H_B, W_B)
                        ▲ matches are in NORMALIZED [−1,1]² — a frequent integration bug
                                                                    [repo: README.md]
21  F, mask ← cv2.findFundamentalMat(kptsA, kptsB, USAC_MAGSAC, thresh 0.2)
                                                                    [repo: README.md]
════════════════════════════════════════════════════════════════════════════════════════
```

## What the control flow makes visible

1. **Line 17 of Part 1 is the architectural hinge.** Freezing the matcher before Stage 2 is
   what makes refiner training a *stationary* problem — the refiners are not chasing a moving
   coarse prediction. This is the UFM-derived change that the paper credits for "rapid
   experimentation" `[paper §3.1]`, and it is why the two objectives can be listed separately
   at all.

2. **Line 30's `⧉r` is the same mechanism as three other folders in this set.** `../seasplat/`
   detaches `Ẑ` before the medium losses; `../seathru_NeRF/` detaches the sample spacing
   `δ^bs`; RoMa v2 detaches the residual before `L_prec`. In every case an auxiliary head is
   allowed to *explain* the primary prediction but never to *shape* it. Worth carrying into
   the comparison glossary as a shared design pattern rather than three coincidences.

3. **Lines 11–12 of Part 2 show the two-stage refinement is not simply "run it again".**
   The precision channels are explicitly zeroed before the high-resolution pass because
   "delta at 4 is **absolute**" `[repo: romav2.py:46-49]` — the stride-4 refiner predicts an
   absolute displacement, not a correction, so a second pass cannot inherit its precision.
   The overlap channel *can* be inherited because it is relative to the matcher prediction.
   This asymmetry appears nowhere in the paper.

4. **Line 4 of Part 2 is the single most consequential line for a user.** The eight-way
   `Setting` enum determines resolution, directionality and thresholding — and the default
   (`precise`) reproduces none of the paper's tables.

5. **There is nothing to detach at inference.** Unlike the radiance-field folders, the whole
   of Part 2 runs under `@torch.inference_mode()` `[repo: romav2.py:162]`. The `.detach()`
   calls at lines 11–12 are structural leftovers from the training graph.
