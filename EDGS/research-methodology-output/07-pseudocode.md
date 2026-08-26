# §7 — Pseudocode: EDGS initialization + train step

Notation follows the paper (`g_i^x, Σ_i, g_i^c, g_i^α, W_ij, c_ij, ε_ij^k, p_ij^corr,
p_ij^proj, p_i(k), Y_k, O_k, Ĥ_k, τ_corr, τ_proj`). Tags: `[paper]` (= arXiv:2504.13204v2)
/ `[repo: file:line]` / `[inferred]`. Schedule-gated lines **⟨gate⟩**; ⧉ marks
non-differentiable / one-shot steps. **`✗ NOT IMPLEMENTED`** marks paper content with no
code counterpart.

```text
════════════════════════════════════════════════════════════════════════════════════════
PART 1 — EDGS INITIALIZATION  (runs ONCE, before optimization step 1)
════════════════════════════════════════════════════════════════════════════════════════
INPUT  {I_m, P^m}_{m=1..V}  posed training images (COLMAP)          [paper §1]
       G ← Gaussians from SfM points                (N_splats_at_init)
CONST  K = num_refs = 180 ;  J = nns_per_ref = 3 ;  M = matches_per_ref = 15 000
       scaling_factor = 0.001 ;  τ_proj = proj_err_tolerance = 0.01
       roma_model ∈ {outdoors, indoors}                             [repo: configs/train.yaml]

 1  M_match ← roma_outdoor()                    pretrained dense matcher [paper §3.2, ref 13]
 2  M_match.upsample_preds ← False ;  M_match.symmetric ← False
                                                                    [repo: corr_init.py:533-539]
                        ▲ two RoMa features disabled — not in the paper — delta D-9
 3  τ_corr ← M_match.sample_thresh              ⧉ RoMa's OWN default [repo: corr_init.py:541]
                        ▲ paper Eq.9's τ_corr has no config key — delta D-8

    ── reference-view selection ────────────────────────────────────────────────────────
 4  C ← [ flatten(world_view_transform(cam)) ∈ ℝ¹⁶  for cam in train_cams ]
                                                                    [repo: corr_init.py:553]
 5  refs ← SELECT_CAMERAS_KMEANS(C, K)          ⧉ k-means over poses; keep the member
                                                  nearest each cluster centre
                                                                    [repo: corr_init.py:65-97, 555]
                        ▲ paper §3.2 says only "maximal overlap" — delta D-5
 6  𝓘_i ← K_CLOSEST_VECTORS(C, J)               Frobenius distance   [paper §3.2] [repo: corr_init.py:41, 561]

    ── per reference view ──────────────────────────────────────────────────────────────
 7  FOR each reference I_i ∈ refs:
 8      FOR each neighbour I_j ∈ 𝓘_i:                               [repo: corr_init.py:208-289]
 9          (W_ij, c_ij) ← M_match(I_i, I_j)     dense warp + confidence
                                                                    [paper Eq.3] [repo: corr_init.py:100-177]
10      (c_max, j_max) ← per-pixel argmax of c_ij over the J neighbours
                                                                    [repo: corr_init.py:208]
                        ▲ realises the max_{j∈𝓘_i} of paper Eq.11    [inferred]
11      matches ← M_match.sample(W, c_max, num = M)     ⧉ keeps only c > τ_corr
                                                                    [paper Eq.9] [repo: corr_init.py:541, 622]
12      (u_i^k, v_i^k), (u_j^k, v_j^k), colour_k ← to_pixel_coords(matches), read RGB at I_i
                                                                    [paper §3.3] [repo: corr_init.py:291-397]

    ── triangulation ───────────────────────────────────────────────────────────────────
13      FOR each match k:
14          build A, b from the 4 DLT rows of P^i, P^j:
              [g^x 1]·P^i_col,0 − u_i^k [g^x 1]·P^i_col,2 = 0    (and 3 more)
                                                                    [paper Eqs.4-6] [repo: corr_init.py:412-470]
15          g_k^x ← argmin_x ‖A x + b‖²   via torch.linalg.lstsq    [paper Eq.7] [repo: corr_init.py:471-472]
                        ▲ ill-conditioned for small-baseline pairs — the reason Eq.10 exists
16          ε_i^k ← ‖π(P^i, g_k^x) − (u_i^k,v_i^k)‖₂ ;  ε_j^k analogously
                                                                    [paper Eq.8]
17      ε_ij^k ← max(ε_i^k, ε_j^k)                                  [paper §3.4]
18      per match, keep the neighbour j minimising ε_ij^k           [paper Eq.11 max_j]
                                                                    [repo: corr_init.py:492-519, 647]

    ── seed one Gaussian per surviving correspondence ──────────────────────────────────
19      g^x   ← g_k^x                                               [paper Eq.7] [repo: corr_init.py:657]
20      g^c   ← RGB2SH( colour_k / 255 )        DC term only        [paper §3.5] [repo: corr_init.py:658]
21      f_rest ← 0                              ✗ NOT IMPLEMENTED   [repo: corr_init.py:659, 871]
        ┌──────────────────────────────────────────────────────────────────────────────┐
        │  paper §3.5 / Eqs.12-13 specify instead:                                     │
        │     O_k ← n RGB observations from directions v_1..v_n                        │
        │     Y_k ← [16 real SH basis fns (deg ≤ 3) evaluated at v_1..v_n] ∈ ℝ^{n×16}  │
        │     Ĥ_k ← argmin_H ‖Y_k H − O_k‖_F²   (Eq.12)                                │
        │     Ĥ_k ← Y_k⁺ O_k  when n < 16       (Eq.13, Moore–Penrose)                 │
        │  NO SUCH CODE EXISTS. grep "pinv|lstsq" → only corr_init.py:472, which is    │
        │  the TRIANGULATION solve of Eq.7. — delta D-1                                │
        └──────────────────────────────────────────────────────────────────────────────┘
22      g^α   ← 0  −  10·𝟙[ ε_ij^k > τ_proj ]   ⧉ logit space
                        ⇒ α = 0.5 for good points, α ≈ 4.5e-5 for bad ones
                                                                    [repo: corr_init.py:660-666]
                        ▲ paper Eq.10 defines p^proj as a SAMPLING distribution; the code
                          keeps bad points and makes them INVISIBLE. Source comment:
                          "TODO: remove those points instead" — delta D-2
23      Σ^scale ← inv_act( ‖g_k^x − campos_i‖ · 0.001 )   isotropic  [repo: corr_init.py:668-670]
                        ▲ distance-proportional ⇒ constant angular footprint, since each
                          Gaussian is seeded from ONE pixel. No formula in the paper [inferred]
24      Σ^rot   ← copy of gaussians._rotation[−1]                    [repo: corr_init.py:671]

25  APPEND all new Gaussians via densification_postfix(...)          [repo: corr_init.py:678-686]

    ── post-init cleanup (trainer) ─────────────────────────────────────────────────────
26  ⟨if NOT add_SfM_init⟩  PRUNE the original N_splats_at_init SfM Gaussians
                                                                    [repo: trainer.py:243-251]
27  Σ^scale ← Σ^scale · 0.5      ⧉ ALL scales halved, globally      [repo: trainer.py:252-254]
                        ▲ undocumented — delta D-6

════════════════════════════════════════════════════════════════════════════════════════
PART 2 — OPTIMIZATION  (stock 3DGS, plus two undocumented schedule changes)
════════════════════════════════════════════════════════════════════════════════════════
28  FOR i = 1 … gs_epochs   (README: 30 000; config default 0)      [repo: README.md; configs/train.yaml]

29      ⟨if max_lr (default True)⟩  update_lr( max(i, 8000) )       [repo: trainer.py:146-147]
        ⟨else⟩                      update_lr( i )
                        ▲ position LR CLAMPED to its step-8000 value. Follows from the
                          paper's own Fig.4 result (init is ~50× closer to the solution,
                          so a high early LR would scatter it) but is UNDOCUMENTED — delta D-4

30      ⟨if i mod 1000 == 0⟩  oneupSHdegree()                       [repo: trainer.py:151-152]
31      cam ← pop random from viewpoint_stack (no replacement)      [repo: trainer.py:155-157]
                        ▲ ONE camera. configs batch_size = 64 is read but never used — delta D-11

32      Î ← RASTERIZE(G, cam)                                       [repo: trainer.py:159]
33      L ← 0.8·‖Î − I‖₁ + 0.2·(1 − SSIM(Î, I))                     [paper §3.1] [repo: trainer.py:163-167]
                        ▲ THE ENTIRE OBJECTIVE. No regulariser, no correspondence loss.
                          (tv_loss exists in losses.py:78 but is never called)
34      BACKWARD(L) ; optimizer.step() ; zero_grad()                [repo: trainer.py:179, 189-190]

    ── density control ─────────────────────────────────────────────────────────────────
35      ⟨if no_densify⟩                        (README command: True; config default False)
36          PRUNE α < 0.005    while i < densify_until_iter (15 000)
                                                                    [repo: trainer.py:258-264]
37      ⟨else⟩  full 3DGS densify_and_prune(...)                    [repo: trainer.py:193-205]
                        ▲ reset_opacity() inside is UNREACHABLE: opacity_reset_interval
                          = 30 000 = iterations, and the branch is gated by i < 15 000
                                                                    [repo: configs/gs/base.yaml]

    ── the undocumented opacity decay ──────────────────────────────────────────────────
38      ⟨if reduce_opacity (default True) AND i < 15 000 AND i mod 10 == 0⟩
39          g^α ← log( exp(g^α) · 0.99 )        ⧉ = logit − 0.01005 [repo: trainer.py:81-85]
                        ▲ ~1500 applications ⇒ cumulative logit shift ≈ −15.
                          Paired with line 36 this is a CONTINUOUS decay-and-cull that
                          replaces 3DGS's periodic opacity reset. opacity_lr is also
                          halved (0.025 vs 0.05). NOT IN THE PAPER — delta D-3  [inferred]

40      ⟨if i ∈ save_iterations⟩ save ; ⟨periodically⟩ evaluate()   [repo: trainer.py:91-99]
════════════════════════════════════════════════════════════════════════════════════════
```

## What the control flow makes visible

1. **Part 1 runs exactly once, and Part 2 is stock 3DGS.** That separation is the paper's
   whole thesis and is why Table 3's drop-in composability works: any other method's Part 2
   can be substituted wholesale.

2. **Line 21 is where the released code and the published method part ways.** The entire
   §3.5 contribution — three equations and one column of Table 6 — has no implementation.
   Everything else in Part 1 is faithful.

3. **Line 22 turns a *selection* rule into an *initialization* rule.** Eq. 10's sampling
   distribution becomes an opacity penalty; the points survive until line 36 prunes them.
   The count of Gaussians immediately after initialization is therefore **larger** than the
   paper's formulation implies.

4. **Lines 29 and 39 are the two undocumented optimizer changes.** Both are individually
   well-motivated by the paper's own Fig. 4 analysis, and both mean the claim "improves
   reconstruction **without modifying the optimization algorithm**" `[paper §1]` holds for
   the *loss* and for *densification*, but not literally for the *schedule*.

5. **There is no `.detach()` anywhere in this method.** Unlike `seasplat/` and
   `seathru_NeRF/`, whose well-posedness rests on gradient routing, EDGS's rests entirely on
   *what happens before gradients exist*. The filters at lines 11, 17–18 and 22 are all
   one-shot, non-differentiable selections.

6. **Line 33 is two terms.** Every number in the paper is attributable to Part 1 plus the
   two schedule tweaks — no objective confound.
