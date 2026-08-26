# §7 — Pseudocode: the full OMG pipeline

Notation follows the paper (`p, o, s, r, h^(0), h^(1,2,3), T, V, F, γ, Ī, I, λ, τ, D, M, L, B,
C^(m)`). Tags: `[paper]` / `[repo: file:line]` / `[inferred]`.
⧉ = non-differentiable / frozen. **⚠ = undocumented in the paper.**
**[MS]** = inherited verbatim from `../mini-splatting/`.

```text
════════════════════════════════════════════════════════════════════════════════════════
ALGORITHM  OMG — full 30 000-iteration run
════════════════════════════════════════════════════════════════════════════════════════
INPUT   COLMAP SfM points; --imp_metric ∈ {indoor, outdoor}  ⚠ REQUIRED  [repo: README.md]
CONST   simp_iteration1 = 15 000, simp_iteration2 = 20 000        [MS] [repo: arguments:89-90]
        net_itr = 15 000 ⚠, svq_itr = 29 000                      [repo: arguments:96-97]
        τ = importance_thresh = 0.96 (XS) … 0.9999 (XL)           [paper §4.1] [repo: arguments:98]
        λ = lambda_ld = 2.0 ⚠                                     [repo: arguments:99]
        (M,B): scale (1, 2⁶) ⚠, rotation (2, 2⁹) ⚠, appearance (2, 2¹⁰) ⚠
                                                                  [repo: arguments:100-105]
────────────────────────────────────────────────────────────────────────────────────────

 1  FOR i = 1 … 30 000:

      ── LR schedule, inherited ────────────────────────────────────────────────────────
 2     ⟨if i < 15 000⟩ update_lr(i)  ⟨else⟩ update_lr(i − 15 000 + 5000)   ⚠ [MS] REWIND
                                                                  [repo: train.py:73-77]
 3     ⟨if i > 15 000 AND i mod 1000 == 0⟩ oneupSHdegree()         [MS] [repo: train.py:80-81]

      ── SVQ switch-on ─────────────────────────────────────────────────────────────────
 4     ⟨if i == svq_itr (29 000)⟩  apply_svq()      → line 40      [repo: train.py:88-89]

      ── forward + loss: STOCK 3DGS ────────────────────────────────────────────────────
 5     cam ← pop random training view                             [repo: train.py:84-86]
 6     Î ← RASTERIZE(G, cam)     using ŝ, r̂ (SVQ) and MLP-decoded appearance
                                                                  [repo: train.py:95]
 7     L ← 0.8·‖Î − I‖₁ + 0.2·(1 − SSIM(Î, I))                     [repo: train.py:100-102]
                        ▲ THE ENTIRE OBJECTIVE. No rate term, no regulariser.
                          Contrast ../CompGS/, which puts λR in the loss.
 8     BACKWARD(L)                                                [repo: train.py:103]

      ═══ PHASE 1: Mini-Splatting densification (i < 15 000) [MS] ═══════════════════════
 9     blur split · depth reinit every 5000 · num_max = 4.5 M cap
                        ▲ inherits MS's UNDOCUMENTED mechanics: no reset_opacity(),
                          (1 − α_accum)-weighted depth-reinit sampling.  ⚠ delta D-5

      ═══ i == 15 000 : simplification 1 [MS]  +  neural field ON ══════════════════════
10     intersection_preserving + importance sampling (factor 0.5) + reinit    [MS]
11     ⟨if i == net_itr (15 000)⟩  CONSTRUCT_NET():                ⚠ [repo: train.py:178-180]
12         T ← _features_dc[:, 0].clone().detach()      ∈ ℝ^{N×3}  ⚠ D = 3
                                                                  [repo: gaussian_model.py:724]
13         V ← zeros(N, 3)                              ∈ ℝ^{N×3}  ⚠
                                                                  [repo: gaussian_model.py:725]
14         MLP_s : 3 → Frequency(16 freq) → 64 → 13   (ReLU)       ⚠ [paper Eq.4] [gm:672-686]
15         MLP_t : 16 → 64 → 3    (LeakyReLU)                      ⚠ [paper Eq.3] [gm:698-708]
16         MLP_o : 16 → 64 → 1    (LeakyReLU)                      ⚠ [paper Eq.3] [gm:710-720]
17         MLP_v : 16 → 64 → 45   (LeakyReLU)                      ⚠ [paper Eq.4] [gm:687-697]
                        ▲ 16 = 3 (T or V) + 13 (F). "a tiny MLP" is all the paper says.
18         Adam(lr = 0.01) + LinearLR(100) ⊕ MultiStepLR([1k,3.5k,6k], γ=0.33)  ⚠
                                                                  [repo: gaussian_model.py:737-751]

      ── appearance decoding, every forward pass after 15 000 ──────────────────────────
19     F_n ← MLP_s(γ(p_n))                          ∈ ℝ¹³         [paper Eq.4]
20     h_n^(0)      ← MLP_t(cat(T_n, F_n))          static colour  [paper Eq.3]
21     o_n          ← MLP_o(cat(T_n, F_n))          opacity        [paper Eq.3]
22     h_n^(1,2,3)  ← MLP_v(cat(V_n, F_n))          view-dep. SH   [paper Eq.4]
23     s_n, r_n     ← PER-GAUSSIAN, NOT through any field          [paper §3.1]
                        ▲ THE key architectural asymmetry: "each Gaussian covers a larger
                          spatial region, requiring a more specific scale and rotation"

      ═══ i == 20 000 : LD SCORING — OMG's contribution (1) ════════════════════════════
24     ⟨if i == simp_iteration2 (20 000)⟩                          [repo: train.py:171-176]
25         Ī ← intersection_preserving(...)                        [MS] [paper Eq.7] [gm:627-650]
26             FOR each training view: accumulate accum_weights, area_proj, area_max
27             ⟨imp_metric == outdoor⟩ Ī += accum_weights / area_proj   (masked area_max ≠ 0)
               ⟨imp_metric == indoor ⟩ Ī += accum_weights
                        ▲ ⚠ scene-type branch; paper Eq.7 shows ONE formula — delta D-10
28             Ī[accum_area_max == 0] ← 0            ⧉ the ∃ρ gate of Eq.7  [gm:648]

29         order   ← SORT_MORTON(p)   ⧉ 21-bit quantize → Morton encode → argsort
                                                                  [paper §3.3] [gm:752-760]
30         order_l ← clamp(order − 1, 0) ;  order_r ← clamp(order + 1, max)
                        ▲ ⚠ N_i^K is EXACTLY TWO neighbours — the Morton predecessor and
                          successor. K is not a parameter.  — delta D-1   [gm:654-655]
31         res ← mean( |T[order_l] − T| + |T[order_r] − T| )       [paper Eq.8] [gm:663]
                        ▲ ⚠ compares the LEARNED 3-D latent T, not colour — delta D-6
32         I   ← Ī · res^λ,   λ = 2.0                              [paper Eq.8] [gm:665]
                        ▲ ⚠ λ is an EXPONENT and its value is unstated — deltas D-4, D-7
                        ▲ WHY: nearby Gaussians have near-identical blending weights, so
                          plain thresholding either deletes a whole cluster at once or
                          keeps redundant duplicates.               [paper §3.3]
                        ▲ NB: ../mini-splatting/ answers the SAME degeneracy with
                          STOCHASTIC sampling; OMG answers it deterministically. [inferred]
33         keep ← INIT_CDF_MASK(I, thres = τ)        ⧉ [paper §3.3] [gm:666]
34         prune_points(¬keep)                                     [gm:668]
                        ▲ τ ALONE spans the XS→XL family — the single rate knob [paper §4.1]

      ═══ i == 29 000 : SUB-VECTOR QUANTIZATION — contribution (3) ═════════════════════
40     APPLY_SVQ():                                                [paper §3.2] [gm:805-819]
41         kmeans(_scaling,            M=1, B=2⁶ )   ⚠ M=1 ⇒ plain VQ — delta D-3
42         kmeans(_rotation,           M=2, B=2⁹ )
43         kmeans(cat(T, V),           M=2, B=2¹⁰)                 [gm:814-816]
44         FOR each partition m:  i_m ← argmin_j ‖z_m − C^(m)[j]‖²₂
                                                                  [paper Eq.6] [gm:842-855]
45         ⧉ INDICES FROZEN from here on                           [paper §3.2]
46         optimizer_code ← Adam(codebooks, lr = 1e-8)             ⚠ ≈ FROZEN — delta D-2
                                                                  [gm:818]
47     ⟨if i ≥ svq_itr⟩ optimizer_code.step()   (last 1000 it)     [repo: train.py:191-192]
48     ẑ ← cat(C^(1)[i_1], …, C^(M)[i_M])  then activation         [paper Eq.5] [gm:822-833]

      ── parameter updates ─────────────────────────────────────────────────────────────
49     gaussians.optimizer.step()                                  [repo: train.py:184-185]
50     ⟨if i > net_itr⟩ optimizer_net.step(); scheduler_net.step() [repo: train.py:188-190]
51     ⟨if i ≥ svq_itr⟩ optimizer_code.step()                      [repo: train.py:191-192]
                        ▲ FOUR optimizer groups vs Mini-Splatting's one

      ═══ i == 30 000 : ENCODE ═════════════════════════════════════════════════════════
52     p → float16 → uint16 → Morton sort → G-PCC (TMC13)          [paper §4.1] [gm:859-863]
53     SVQ indices → Huffman                                       [paper §4.1]
54     everything (incl. MLP weights) → single file, LZMA → comp.xz
                                                                  [paper §4.1] [train.py:116-117]
55     report os.path.getsize("comp.xz")  + per-component breakdown {xyz, scale,
       rotation, app, MLPs}                                        [train.py:119-123]
                        ▲ ✅ ACTUAL file size, and the MLPs ARE counted — honest accounting,
                          matching ../CompGS/'s practice
════════════════════════════════════════════════════════════════════════════════════════
```

## What the control flow makes visible

1. **Line 7 is the whole objective, and lines 9–55 are all outside it.** Like
   `../mini-splatting/` and `../EDGS/`, OMG achieves its result without touching the loss —
   and unlike `../CompGS/`, it reaches ~200× compression with **no rate term at all**. The
   rate–distortion family comes from a single post-hoc threshold (line 33).

2. **Line 23 is the paper's sharpest design decision, and it is one line.** Geometry bypasses
   the neural field entirely. Every other attribute is MLP-decoded. This is what separates OMG
   from LocoGS — and it is never ablated.

3. **Lines 12–17 reveal how small "tiny" is.** `T` and `V` are **3-dimensional**; the space
   feature is **13**; every MLP is **64 wide with one hidden layer**. The paper gives none of
   these numbers. The 16-dim MLP inputs are the only clue that `D = 3`.

4. **Line 30 is where `N_i^K` collapses to `K = 2`.** The paper's central equation is written
   with a general neighbourhood; the implementation uses exactly the Morton predecessor and
   successor.

5. **Line 46 undermines line 45's stated purpose.** The paper describes freezing indices *so
   that* the codebook can be finetuned; `lr = 1e-8` means it barely moves. Fortunately Table 4
   shows K-means alone costs ≤0.05 dB, so the pipeline works — just not by the stated
   mechanism.

6. **Line 32 and `../mini-splatting/`'s stochastic sampling are two answers to one
   degeneracy.** Both papers identify that importance is spatially autocorrelated; Mini-Splatting
   decorrelates by sampling, OMG reweights by distinctiveness. A base method and its descendant
   diverging on the same problem is a useful pairing for your write-up.

7. **Four optimizer groups (lines 49–51) on three different schedules.** Gaussians throughout;
   MLPs from 15 000; codebooks from 29 000. Mini-Splatting had one.
