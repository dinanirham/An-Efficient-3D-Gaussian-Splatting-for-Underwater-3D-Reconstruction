# §7 — Pseudocode: the full Mini-Splatting train step

Notation follows the paper (`G_i, p_i, Σ_i, α_i, c_i, w_i, T_i, S_i, I_i, P_i, d^mid,
G^blur, G^int, I_max, θ_blur`). Tags: `[paper]` / `[repo: file:line]` / `[inferred]`.
Schedule-gated lines are **⟨gate⟩**. Line numbers are `ms/train.py` unless noted.

There is **no gradient detachment anywhere** in this method — the well-posedness mechanisms
are all non-differentiable selection steps, marked ⧉.

```text
────────────────────────────────────────────────────────────────────────────────────────
ALGORITHM  Mini-Splatting — full training run (cf. paper Algorithm 1)
────────────────────────────────────────────────────────────────────────────────────────
INPUT   {G_i = (p_i, Σ_i(s_i,q_i), α_i, c_i)}  ← SfM points               [paper Alg.1:1]
        {I_m, K_m, T_m}_{m=1..M}   posed training images
CONST   it_simp1 = 15 000, it_simp2 = 20 000, it_end = 30 000             [repo: :403-404]
        num_depth = 3.5e6, num_max = 4.5e6, f_samp = 0.5                  [repo: :405-407]
        θ_blur = 2e-4  (as H·W/5000)                                      [paper Eq.2] [repo: :151]
        imp_metric ∈ {indoor, outdoor}      REQUIRED, no default          [repo: :409]
INIT    sh_degree ← 0    ⧉ hard-coded, ignores --sh_degree                [repo: :56]
        mask_blur ← 0 ∈ {0,1}^N                                          [repo: :75]
────────────────────────────────────────────────────────────────────────────────────────

 1  FOR i = 1 … it_end:

      ── learning-rate schedule, with a REWIND at simplification ─────────────────────
 2     ⟨if i < it_simp1⟩  update_lr(i)                                    [repo: :96-97]
 3     ⟨else⟩             update_lr(i − it_simp1 + 5000)   ⧉ REWOUND to step 5000
                                                                          [repo: :98-99]
                        ▲ undocumented; without it the reinitialized Gaussians are born
                          into an almost-decayed LR — delta D-5

 4     ⟨if i > it_simp1 AND i mod 1000 == 0⟩  oneupSHdegree()             [paper §5] [repo: :102-103]

      ── forward + loss: IDENTICAL to 3DGS ───────────────────────────────────────────
 5     m ← pop random view (without replacement; stack refilled when empty)
                                                                          [repo: :107-109]
 6     Î, radii, S_i ← RASTERIZE_imp(G, view m)                           [repo: :115-116]
                        ▲ forked kernel also returns accum_weights, area_proj,
                          area_max(= S_i)                                 [paper §4.1] [repo: gaussian_renderer/__init__.py:189-191]
 7     L ← (1 − 0.2)·‖Î − I_m‖₁ + 0.2·(1 − SSIM(Î, I_m))                  [paper Eq. of 3DGS] [repo: :120-122]
 8     BACKWARD(L)                                                        [repo: :123]
                        ▲ NO new loss term anywhere in this method

      ═══ PHASE 1: DENSIFICATION  (i < densify_until_iter = 15 000) ═════════════════
 9     ⟨if i < 15 000⟩
10         max_radii2D[vis] ← max(max_radii2D[vis], radii[vis])
           add_densification_stats(viewspace_pts, vis)                    [repo: :147-148]

           ── BLUR SPLIT accumulator ──────────────────────────────────────────────
11         mask_blur ← mask_blur ∨ ( S_i > θ_blur·H·W )                   [paper Eq.2] [repo: :151]
                        ▲ S_i counts pixels where G_i is the ARGMAX contributor —
                          a criterion ORTHOGONAL to the positional gradient, which is
                          blind in smooth regions                          [paper §4.1]

12         ⟨if i > 500 AND i mod 100 == 0 AND i mod 5000 ≠ 0 AND N < num_max⟩
                                                                          [repo: :153]
                        ▲ "N < num_max" is repo-only — delta D-3
13             densify_and_prune_split(τ=2e-4, o_min=0.005, extent, size_thr, mask_blur):
14                 clone:  ‖∇_p L‖ ≥ τ  ∧  max(s) ≤ 0.01·extent           [repo: gaussian_model.py:374-378]
15                 split:  ( ‖∇_p L‖ ≥ τ ∧ max(s) > 0.01·extent )  ∨  mask_blur
                                                                          [repo: gaussian_model.py:434-440]
                        ▲ the blur mask is UNIONED with the gradient criterion, so
                          blur split is strictly additional capacity      [inferred]
16                 prune:  α < 0.005  ∨  radii2D > 20  ∨  max(s) > 0.1·extent
                                                                          [repo: gaussian_model.py:419-424]
17             mask_blur ← 0                                              [repo: :161]

           ── DEPTH REINITIALIZATION, every 5000 iterations ───────────────────────
18         ⟨if i mod 5000 == 0⟩                                           [repo: :164]
19             pts ← [] ; cols ← []
20             FOR every training view v (all M of them):
21                 out_pts, α_accum ← RASTERIZE_depth(G, v)               [repo: :172-174]
                        ▲ out_pts[x] = the ray/ellipsoid MID-POINT of the ARGMAX
                          Gaussian at pixel x, t^mid = −b/2a               [paper §4.1, App.D Eq.7]
                        ▲ NOT alpha-blended depth: blended depth gives PSNR 17.67
                          vs 27.54 (paper Tab.4) due to depth collapse /
                          object misalignment / blending boundary          [paper App.C]
22                 prob ← (1 − α_accum) ;  prob ← prob / Σprob            [repo: :177-179]
                        ▲ ⚠ IMPORTANCE-WEIGHTED, biased toward LOW-opacity pixels.
                          Paper §4.1 says "randomly select" — delta D-2
23                 n_v ← H·W · num_depth / (H·W·M)                        [repo: :183-187]
24                 idx ← np.random.choice(H·W, n_v, p = prob, replace = False)  ⧉
                                                                          [repo: :189-190]
                        ▲ ms_d/ uses replace=True then np.unique ⇒ FEWER points — delta D-9
25                 pts += out_pts[idx] ; cols += I_v[idx]     (GT colours) [repo: :192-196]

26             ⧉ REINITIAL_PTS(concat(pts), concat(cols)):                [repo: gaussian_model.py:460-483]
27                 p    ← pts                                             keep
28                 f_dc ← RGB2SH(cols)                                    keep (from GT)
29                 f_rest ← 0                                             ✗ DISCARDED
30                 s    ← log√(distCUDA2(pts))                            ✗ RESET
31                 q    ← identity quaternion                             ✗ RESET
32                 α    ← inverse_sigmoid(0.1)                            ✗ RESET
33             training_setup(opt)         ⧉ ALL ADAM MOMENT STATE DISCARDED
                                                                          [repo: :204]
34             mask_blur ← 0 ; refill viewpoint_stack                     [repo: :205-207]
                        ▲ a COMPLETE restart of the representation, 3× per run.
                          Clusters cannot survive the depth round-trip: a stack of 50
                          overlapping Gaussians yields ≤1 argmax point per pixel — this
                          is what resolves `overlapping'                   [inferred]

      ═══ PHASE 2: SIMPLIFICATION ═══════════════════════════════════════════════════
35     ⟨if i == it_simp1 (15 000)⟩                                        [repo: :211]
36         I ← 0 ∈ ℝ^N ;  A ← 0 ∈ ℝ^N                                     [repo: :213-214]
37         FOR every training view v:
38             accum_weights, area_proj, S ← RASTERIZE_imp(G, v)          [repo: :218-221]
39             A ← A + S
40             ⟨if imp_metric == outdoor⟩                                 [paper Eq.12] [repo: :225-228]
41                 I[S ≠ 0] ← (I + accum_weights / area_proj)[S ≠ 0]
                        ▲ I² : per-view intersection gate + projected-area normalisation,
                          to suppress sky / far-field Gaussians            [paper App.E]
42             ⟨else (indoor)⟩  I ← I + accum_weights                     [paper §3.2] [repo: :229-230]
                        ▲ I¹ : plain accumulated blending weight

           ── INTERSECTION PRESERVING (paper Eq.3), as a probability mask ─────────
43         I[A == 0] ← 0                                                  ⧉ [paper Eq.3] [repo: :232]
                        ▲ G^int = {G_i | i ∈ I_max}. A Gaussian that is never the argmax
                          in ANY view gets P = 0 and can never be sampled.
                          There is no function called Intersection() — delta D-8

           ── IMPORTANCE-WEIGHTED STOCHASTIC SAMPLING (paper §4.2) ────────────────
44         P ← I / ΣI                                                     [paper §4.2] [repo: :233]
45         n ← int( N · f_samp · |{P ≠ 0}| / N )                          [repo: :237-239]
46         idx ← np.random.choice(N, n, p = P, replace = False)           ⧉ [repo: :240-241]
                        ▲ STOCHASTIC, not top-k. Deterministic thresholding removes whole
                          REGIONS because importance is spatially autocorrelated;
                          sampling thins them instead. Validated by CHAMFER DISTANCE,
                          not PSNR                                         [paper §4.2, Fig.6]
47         prune_points(¬idx)                                             [repo: :248]
48         max_sh_degree ← dataset.sh_degree (3)                          [repo: :250]
49         ⧉ REINITIAL_PTS(own p, own SH2RGB(f_dc))   ⇒ s,q,α,f_rest RESET AGAIN
                                                                          [repo: :251-252]
50         training_setup(opt)             ⧉ Adam state discarded again   [repo: :254]

51     ⟨if i == it_simp2 (20 000)⟩                                        [repo: :259]
52         recompute I and A exactly as lines 36-43                       [repo: :261-281]
53         keep ← INIT_CDF_MASK(I, thres = 0.99):                         ⧉ [repo: :31-44, 282]
54             sort I ascending → cumsum → drop the Gaussians forming the
                bottom 1% of TOTAL importance mass
                        ▲ threshold 0.99 is repo-only; paper Alg.1:21 says only
                          "Directly Prune a Few Gaussians" — delta D-4
55         prune_points(¬keep) ; training_setup(opt)                      [repo: :284-285]

      ── optimizer step (3DGS, unchanged) ────────────────────────────────────────────
56     ⟨if i < it_end⟩  optimizer.step() ; optimizer.zero_grad()          [repo: :291-293]
                        ▲ ⚠ NO reset_opacity() ANYWHERE. grep → 0 in ms/ and ms_d/,
                          1 in gs/. 3DGS's periodic opacity reset is REMOVED,
                          unremarked — delta D-1

57  END FOR                        ⇒ a standard 3DGS .ply, ≈0.2–0.5 M Gaussians
────────────────────────────────────────────────────────────────────────────────────────
```

## Post-hoc: Mini-Splatting-C (`ms_c/run.py`)

```text
 1  load trained Mini-Splatting model
 2  p_v ← round( (p − min p)/(max p − min p) · (2¹⁶ − 1) )                [repo: ms_c/run.py:141-143]
 3  p_v, idx ← np.unique(p_v, axis = 0)          ⧉ DEDUPLICATES Gaussians  [repo: ms_c/run.py:144]
                        ▲ undocumented extra size reduction — delta D-10
 4  feat ← [f_dc, f_rest, s, q, α][idx]                                   [repo: ms_c/run.py:156-164]
 5  CT ← haar3D(p_v, feat, depth = 16)          RAHT, ref [6]             [paper App.F] [repo: ms_c/run.py:167]
 6  CT_q ← round(CT / 0.02)                     Qstep = 0.02              [paper App.F] [repo: ms_c/run.py:169]
 7  savez_compressed( p[idx] as float32, CT_q, Qstep, depth )             [paper App.F] [repo: ms_c/run.py:173]
```

## What the control flow makes visible

1. **Lines 7–8 are the whole objective.** Everything else in this algorithm is
   *non-differentiable bookkeeping*. There is no `.detach()` and no auxiliary loss in the
   entire method — a genuinely unusual property in this comparison set, and the reason
   every reported gain is attributable to the schedule alone.

2. **Five hard restarts (lines 26, 33, 49, 50, 55).** "Reinitialize" in the paper means a
   complete reconstruction of `s`, `q`, `α`, `f_rest` **and** the Adam state. Together with
   the LR rewind at line 3, the run is better described as *four short optimizations
   chained together* than as one 30 000-iteration optimization.

3. **Line 22 is the single most consequential undocumented line.** Changing `prob` from
   `(1 − α_accum)/Σ` to uniform changes which surfaces get resampled, which changes
   everything downstream.

4. **Line 43 is Eq. 3.** Intersection preserving exists only as a mask on the sampling
   probability. If you go looking for it as a step, you will not find it.

5. **Line 46 vs. line 53: the paper's own argument cuts both ways.** §4.2 argues at length
   that *deterministic* pruning destroys local geometry — and then line 53 does exactly
   deterministic pruning, at a 1% ratio. Not a contradiction (the argument is about *large*
   ratios) but it is an unstated asymmetry between the two simplification steps.

6. **Line 56's absent `reset_opacity()`** is the clearest example of a paper-vs-repo gap
   that a reader would never find from the text: the mechanism is missing, not modified.
