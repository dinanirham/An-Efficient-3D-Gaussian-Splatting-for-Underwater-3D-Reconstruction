# §7 — Pseudocode: the full CompGS train step

Notation follows the paper (`ω, γ_k, μ_ω, Σ_ω, f_ω, g_k, h_k, θ_k, α_k, c_k, R, D, λ,
s_f, s_g, s_Σ`). Tags: `[paper]` (= **arXiv:2404.09458v1** = `../../CompGS.pdf`) / `[repo: file:line]` /
`[inferred]`. Schedule-gated lines **⟨gate⟩**; ⧉ marks non-differentiable / detached steps.

```text
────────────────────────────────────────────────────────────────────────────────────────
ALGORITHM  CompGS (Liu et al.) — one training iteration
────────────────────────────────────────────────────────────────────────────────────────
INPUT  Ω = {ω_n}_{n=1..N}, each ω = (μ_ω ∈ ℝ³, s_ω ∈ ℝ⁶, q_ω ∈ ℝ⁴, f_ω ∈ ℝ³²)
       Γ = {γ_{n,k}}, each γ carrying ONLY g_k ∈ ℝ⁸,  K = derive_factor = 10  [paper §3.4]
       Θ_pred = {means_mlp, cov_mlp, opacity_mlp, color_mlp}                 [repo: Prediction.py:24-29]
       Θ_ent  = {ref_EM, res_EM, scale_EM}  (CompressAI)                     [repo: EntropyModel.py]
CONST  λ = lambda_weight ∈ {0.001, 0.005, 0.01}                              [paper §3.4]
       it_rate = rate_loss_start_iteration = 3000        ⧉ repo-only          [repo: Configs/*.yaml]
       it_stop = 15 000, it_end = 30 000                                     [repo: Configs/*.yaml]
       M = number of training views
────────────────────────────────────────────────────────────────────────────────────────

 1  FOR i = 1 … 30 000:
 2      view ← sample uniformly WITHOUT replacement from the M training views
                                                                  [repo: Datasets.py:63-67]
 3      lr_schedule(i)      per-group cosine/exp decay             [paper §3.4] [repo: TrainerCompGS.py:76]
                        ▲ μ_ω's LR is 0.0 → 0.0 ⇒ ANCHOR MEANS NEVER MOVE — delta D-6
                                                                  [repo: Configs/*.yaml]

        ── ENTROPY ESTIMATION (produces both the quantized values AND the rate) ────────
 4      z_f  ← h_a(f_ω)                       hyperprior, dim 4    [paper Eq.8]  [repo: EntropyModel.py:13-104]
 5      ⟨train⟩ f̃_ω ← f_ω + Δ_f,  Δ_f ~ U(−½,½)   ⧉ noise ≈ rounding
        ⟨eval ⟩ f̃_ω ← quantize_ste(f_ω)                            [paper Eqs.6-7] [repo: EntropyModel.py:246]
 6      (μ_f, σ_f) ← E_f(z_f) ;  p(f̃_ω) = N(μ_f, σ_f)              [paper Eq.8]
 7      R_f ← E[−log p(f̃_ω) − log p(z_f)]                          [paper Eq.9]
                        ▲ p(z_f) from the FACTORIZED ENTROPY BOTTLENECK [ref 1]

 8      (μ_Σ, σ_Σ) ← E_Σ(f̃_ω)                                      [paper Eq.10] [repo: EntropyModel.py:234-244]
 9      Σ̃_ω ← quantize(s_ω / s_Σ) · s_Σ,   s_Σ LEARNABLE, init 0.01, dim 6
                                                                  [paper §3.4]  [repo: EntropyModel.py:228,245-249]
10      R_Σ ← E[−log p(Σ̃_ω)]                                       [paper Eq.12]

11      z_g ← h_a(g_k)                        hyperprior, dim 1    [repo: Configs/*.yaml]
12      (μ_g, σ_g) ← E_g(f̃_ω ⊕ z_g) ;  p(g̃_k) = N(μ_g, σ_g)        [paper Eq.11] [repo: EntropyModel.py:133-158]
                        ▲ CONDITIONING ON f̃_ω is the predictive-coding step: whatever
                          g_k shares with f_ω becomes FREE to encode. This is what forces
                          information into the right tier (degeneracy D-2)  [inferred]
13      R_gk ← E[−log p(g̃_k) − log p(z_g)]                         [paper Eq.12]
14      R ← Σ_ω ( R_f + R_Σ + Σ_{k=1..K} R_gk )                    [paper Eq.13]

        ── INTER-PRIMITIVE PREDICTION (per anchor → K coupled primitives) ─────────────
15      h_k ← f̃_ω ⊕ g̃_k                       ∈ ℝ⁴⁰               [paper §3.2] [repo: Prediction.py:46-47]
16      Δμ_k ← means_mlp(h_k)                 ∈ ℝ³                 [paper Eq.3 t_k] [repo: Prediction.py:49]
17      u_k  ← cov_mlp(h_k)                   ∈ ℝ⁷                 [repo: Prediction.py:50]
                        ▲ ONE 7-channel head, not the two networks 𝒮, ℛ of paper Eq.3
                          — delta D-1
18      v    ← [ (μ_ω − campos)/‖·‖ , ‖μ_ω − campos‖ ]  ∈ ℝ⁴       [repo: Prediction.py:53-56]
                        ▲ computed at the ANCHOR and broadcast to all K — delta D-12
19      α_k  ← Tanh( opacity_mlp(h_k ⊕ v) )   ∈ [−1, 1]            [paper Eq.5] [repo: Prediction.py:28,61]
20      c_k  ← Sigmoid( color_mlp(h_k ⊕ v) )  ∈ [0, 1]³            [paper Eq.5] [repo: Prediction.py:29,62]

21      mask ← (α_k > 0)                      ⧉ VIEW-DEPENDENT CULL [repo: Prediction.py:65]
                        ▲ the set of rasterized primitives CHANGES WITH VIEWPOINT
                          — no other method in the comparison set does this — delta D-10

22      μ_k     ← μ_ω + Δμ_k ⊙ exp(Σ̃_ω[0:3])                       [paper Eq.4] [repo: Prediction.py:76]
23      scale_k ← sigmoid(u_k[0:3]) ⊙ exp(Σ̃_ω[3:6])                [repo: Prediction.py:77]
24      q_k     ← normalize(u_k[3:7])                              [repo: Prediction.py:78]
                        ▲ lines 22-23: BOTH offset and scale are modulated by the anchor's
                          own learned 6-D scaling vector. Paper Eq.4 has no such factor.
                          This is Scaffold-GS offset prediction — delta D-1

        ── RENDER ──────────────────────────────────────────────────────────────────────
25      Î ← RASTERIZE( {μ_k, scale_k, q_k, α_k, c_k}[mask] , view )
                                                                  [paper §3.4] [repo: Model.py:168-217]

        ── LOSS ────────────────────────────────────────────────────────────────────────
26      D   ← 0.8·‖Î − I‖₁ + 0.2·(1 − SSIM_msssim(Î, I))           [paper §3.3] [repo: TrainerCompGS.py:214-217]
27      REG ← 0.01 · mean_k( scale_kx · scale_ky · scale_kz )      ⧉ NOT IN THE PAPER
                                                                  [repo: TrainerCompGS.py:220]
                        ▲ Because R is in the loss, BIG Gaussians are REWARDED (fewer
                          primitives ⇒ fewer bits). REG is the only counter-pressure.
                          Hard-coded 0.01, no config knob — delta D-2  [inferred]
28      ⟨if i > it_rate (3000)⟩  L ← D + REG + λ·R                 [paper Eq.1] [repo: TrainerCompGS.py:229]
        ⟨else⟩                   L ← D + REG                      ⧉ NOT IN THE PAPER
                        ▲ 10% warm-up with ZERO rate pressure. R→0 (a constant scene) is a
                          global optimum of the rate term, so this gate is plausibly
                          load-bearing for stability — delta D-4  [inferred]
29      BACKWARD(L)                                                [repo: TrainerCompGS.py:232]

30      L_aux ← entropy_bottleneck.aux_loss()   ⧉ SEPARATE GRAPH   [repo: TrainerCompGS.py:235; Model.py:159]
31      BACKWARD(L_aux)                                            [repo: TrainerCompGS.py:236]
                        ▲ fits the bottleneck's learned CDF so that R is an HONEST estimate
                          of the coded size. Absent from the paper — delta D-3

        ── UPDATE ──────────────────────────────────────────────────────────────────────
32      ⟨if 3·M < i < it_stop⟩  accumulate ∇μ, α, denominators     [repo: TrainerCompGS.py:287-289]
33      ⟨if i == it_stop⟩       release adaptive-control buffers   [repo: TrainerCompGS.py:292-293]
34      gaussian_optimizer.step(); zero_grad()                     [repo: TrainerCompGS.py:296-297]
35      aux_optimizer.step();      zero_grad()                     [repo: TrainerCompGS.py:299-300]
                        ▲ TWO Adams, stepped every iteration on disjoint parameter sets

        ── ADAPTIVE CONTROL — Scaffold-GS, on a VIEW-COUNT-RELATIVE schedule ───────────
36      ⟨if 5·M < i < it_stop AND i mod (2·M) == 0⟩                [repo: TrainerCompGS.py:303-304]
                        ▲ intervals are multiples of M = #training views, NOT fixed
                          iteration counts ⇒ densification frequency scales inversely
                          with dataset size — delta D-7
37          GROWING:                                               [repo: AdaptiveControl.py:38-113]
38            ḡ ← ‖accumulated_grads / coupled_denorm‖
39            cand ← (coupled_denorm > couple_threshold = 40)
40            FOR level = 0 … update_depth−1 (=3):
41                τ ← grad_threshold · 2^level
42                m ← (ḡ ≥ τ) ∧ cand ∧ ( rand() > 0.5^(level+1) )  ⧉ STOCHASTIC
                                                                  [repo: AdaptiveControl.py:57]
43                v ← voxel_size · (16 // 4^level)
44                new ← unique( round(μ_k[m] / v) ) minus voxels already occupied by anchors
                                                                  [repo: AdaptiveControl.py:69-84]
45                μ_ω^new ← new · v ;  s_ω^new ← log(v)·1₆ ;  q_ω^new ← identity
46                f_ω^new ← scatter_max over the parent coupled primitives' f_ω
                                                                  [repo: AdaptiveControl.py:97-98]
47                g_k^new ← 0                                      ⧉ zero residuals
                                                                  [repo: AdaptiveControl.py:100]
48          PRUNE: drop anchors with Σα_accum < opacity_threshold · anchor_denorm
                                                                  [repo: AdaptiveControl.py:119]
49          reset_aux_params()                                     [repo: AdaptiveControl.py:36]
────────────────────────────────────────────────────────────────────────────────────────
```

## Post-training: compress → decompress → evaluate

```text
 1  μ_int ← round(μ_ω / voxel_size)
 2  assert unique(μ_int) == |μ_int|          ⧉ holds ONLY because μ_ω is frozen (D-6)
                                                                  [repo: Model.py:313-315]
 3  sort all params by MORTON ORDER of μ_int                       [repo: Model.py:318-320]
 4  strings ← arithmetic_code(f_ω, Σ_ω, g_k, z_f, z_g)  via CompressAI
                                                                  [paper §3.4] [repo: Model.py:323]
 5  means_strings ← G-PCC / MPEG TMC13 (external binary) on μ_int  [paper §3.4] [repo: Model.py:326]
 6  savez_compressed(bitstreams.npz, **strings)                    [repo: Model.py:331]
 7  size_total ← filesize(npz) + filesize(weights.pth)  ⧉ MLPs ARE COUNTED
                                                                  [repo: TrainerCompGS.py:346-348]
 8  decompress → render_inference(skip_quant=True), timing predict_time and render_time
                                                                  [repo: TesterCompGS.py:63-66; Model.py:257]
 9  save PNG → reopen with PIL → /255                              [repo: TesterCompGS.py:71-75,153-157]
10  PSNR ← 10·log₁₀(1 / F.mse_loss(gt, rec))     ⧉ POOLED MSE      [repo: TesterCompGS.py:158-159]
11  SSIM ← pytorch_msssim.ssim(...) ;  LPIPS ← lpips(net='vgg', version='0.1')
                                                                  [repo: TesterCompGS.py:37,162,165]
```

## What the control flow makes visible

1. **Lines 4–14 run *before* line 25.** The rate model is not a post-hoc analysis of a
   trained scene — the quantized values `f̃_ω, Σ̃_ω, g̃_k` produced by the entropy stack are
   *the very values fed into the renderer*. The representation is never optimized in an
   un-quantized form. This is the structural difference from `compact3d/`, where K-means
   quantization is applied to parameters that are otherwise trained normally.

2. **Line 12 is the paper's contribution in one line.** Conditioning `p(g̃_k)` on `f̃_ω`
   is what makes residual embeddings cheap (6.52–15.36 bits vs the anchor's 80.65–128.26
   `[paper Fig. 8]`) and is what Table 5's +0.99 dB measures.

3. **Lines 27–28 are both undocumented, and they pull against each other.** The rate term
   rewards large Gaussians; `REG` penalises them. Neither the balance (`0.01` vs `λ`) nor
   the existence of `REG` appears in the paper.

4. **Lines 29–31: two backward passes per iteration.** Anyone implementing Eq. 1 literally
   gets one, and their coded sizes will not match their reported `R`.

5. **Line 21 makes the rendered primitive set view-dependent.** Combined with line 18
   (view features taken at the anchor), the model is best understood as *a neural field
   over (anchor, view) that emits Gaussians*, not as a static Gaussian cloud.

6. **Line 3's zero LR for `μ_ω` is what makes line 2 of the compression stage safe.**
   The `assert` at `[repo: Model.py:315]` would be a live failure mode if anchors could
   drift into the same voxel.
