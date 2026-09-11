# §7 — Canonical pseudocode: one flag-gated algorithm for all eight configurations

Notation follows `09-glossary.md` (which resolves the cross-method collisions catalogued in
`../comparison-glossary.md` §2). Tags per line:

- `[SS]` — SeaSplat baseline, with `[repo: file:line]` where the source folder gives one
- `[ED]` — EDGS · `[MS]` — Mini-Splatting · `[VQ]` — CompGS-VQ
- `[inferred]` — derived here from two or more verified facts
- **`[PI]`** — **`[proposed integration]`**: new to the combined method, unmeasured

`⟨gate⟩` marks a schedule- or flag-gated line. `⊘` marks a gradient-detached tensor.
`⧉` marks a non-differentiable / one-shot step.

**Flags:** `M1` (dense init), `M2` (simplification), `M3` (quantization) — the three bits of
the configuration ID `A0`–`A7`.

---

## 7.1 Why this composition order

The order is **M1 → M2 → M3**, and only one of the three positions is a free choice.

| Adjacency | Forced or chosen? | Argument |
|---|---|---|
| M1 before everything | **Forced.** | Initialization precedes optimization by definition. EDGS's Part 1 "runs exactly once, and Part 2 is stock 3DGS" `[../EDGS/07-pseudocode.md pt.1]`. |
| M2 before M3 | **Chosen, but strongly.** | Three reasons. (i) A codebook fitted before a 60–90% prune is fitted to a population that is about to be discarded — the centroids are stale by construction `[inferred from ../compact3d/05-constraints.md C-4]`. (ii) Quantization-aware training spends its gradient budget making parameters "amenable to quantization" `[../compact3d/05-constraints.md M-1]`; doing that for primitives scheduled for deletion is pure waste. (iii) `../OMG/`'s premise — smaller sets are *more* sensitive to lossy compression `[../OMG/00-index.md]` — means the codebook must see the final, sparse population to be sized correctly. |
| M3 last | **Forced by (ii) above**, and by the fact that M3 is the only mechanism whose output is the *stored artifact* rather than the model. |

The one genuinely free choice is **where `seathru_from_iter` sits relative to M1**. The
baseline runs vanilla 3DGS for the first 10 000 iterations so `Ẑ` becomes meaningful before
`β` is fitted to it `[../seasplat/05-constraints.md M-5]`. Under M1 the geometry is already
near-final at step 0, which argues for lowering the gate; but nothing measures how many steps
a dense-init model needs before its rendered depth is stable. `[PI]` The value is **kept at
10 000** so that A0 and A1 differ in exactly one factor, and the question is recorded in
`open-questions.md` as a first-order follow-up.

---

## 7.2 The algorithm

```text
════════════════════════════════════════════════════════════════════════════════════════
ALGORITHM  Efficient underwater 3DGS — full run, all eight configurations
════════════════════════════════════════════════════════════════════════════════════════
INPUT   {I_v, K_cam,v, T^cam_world,v}_{v=1..V}   posed white-balanced frames   [SS paper §IV.A]
        P_sfm                                    COLMAP sparse point cloud     [SS paper §IV.A]
FLAGS   M1, M2, M3 ∈ {0,1}                                                     [PI]
GATES   it_st  = seathru_from_iter = 10 000                       [SS repo: README.md]
        it_gw  = gw_from_iter      = 10 000                       [SS repo: arguments/__init__.py:157]
        it_s1  = simp_iteration1   = 15 000                       [MS repo: ms/train.py:403]
        it_s2  = simp_iteration2   = 20 000                       [MS repo: ms/train.py:404]
        it_vq  = kmeans_st_iter    > it_s2                        [PI — CD-10, see 06-…]
        Δ_med  = 100, n_med = 50                                  [SS repo: arguments/__init__.py:180-181]
        n_bud  = 200 000, fixed pre-campaign by the binding rule   [PI — CD-5, revised]
                        ▲ NOT from A0's converged count. A0's median is
                          2 482 200, so a fraction of it would exceed every M1
                          cloud (299 368 – 471 531) and IP2 would be inert
                          under M1. The rule is: n_bud below the smallest count
                          any other enabled mechanism produces.
                                                    [measured — 13-campaign-addendum §13.5]
        t      = kmeans_freq = 100                                [VQ paper §3]
────────────────────────────────────────────────────────────────────────────────────────

════════ PART 0 — INITIALIZATION ═══════════════════════════════════════════════════════

 1  G ← GAUSSIANS_FROM(P_sfm)                                      [SS repo: scene/__init__.py]
       μ ← P_sfm.xyz ; f_dc ← RGB2SH(P_sfm.rgb)
       f_rest ← ∅                          ⚠ sh_degree = 0        [SS repo: arguments/__init__.py:49]
       o ← inverse_sigmoid(0.1) ; s ← log√(kNN) ; q ← identity

 2  ⟨if M1⟩  ── INSERTION POINT 1 : dense correspondence init ──────────────────────
 3      M_match ← roma_outdoor()                                   [ED paper §3.2] [ED repo: corr_init.py:17]
 4      M_match.upsample_preds ← False ; M_match.symmetric ← False [ED repo: corr_init.py:538-539]
                        ▲ two RoMa features disabled for speed — ED delta D-9. On 18–29-view
                          scenes the resolution loss matters more than on 100+-view ones [inferred]
 5      τ_corr ← M_match.sample_thresh (= 0.05)  ⧉ LOG THIS        [ED repo: corr_init.py:541] [PI: expose it]
 6      K_ref ← min(num_refs, V)               ⧉                   [PI — CD-2]
                        ▲ EDGS default 180 EXCEEDS the view count here [inferred]
 7      refs ← SELECT_CAMERAS_KMEANS(flatten(T^cam_world), K_ref)  [ED repo: corr_init.py:65-97,555]
 8      FOR each reference I_i ∈ refs:
 9          𝓘_i ← J nearest views by Frobenius dist on T^cam_world [ED paper §3.2]
10          (W_ij, c_ij) ← M_match(I_i, I_j)  ∀ j ∈ 𝓘_i            [ED paper Eq.3]
11          (c_max, j_max) ← per-pixel argmax of c_ij over j       [ED repo: corr_init.py:208]
12          matches ← M_match.sample(W, c_max, num = matches_per_ref)   ⧉ keeps c > τ_corr
13          FOR each match k:
14              μ_k ← argmin_x ‖A x + b‖²  via lstsq   ⧉           [ED paper Eq.7] [ED repo: corr_init.py:471-472]
15              ε_ij^k ← max( ‖π(P^i,μ_k) − (u_i,v_i)‖₂ , ‖π(P^j,μ_k) − (u_j,v_j)‖₂ )   [ED paper Eq.8]
15a             θ_k ← ∠( C_i − μ_k , C_j − μ_k )   ⧉ parallax      [PI — CD-26]
15b             KEEP only if  ε < τ_proj  AND  z_i > 0  AND  z_j > 0  AND  θ ≥ 1°
                        ▲ cheirality [PI — CD-16] and parallax [PI — CD-26].
                          EDGS has NEITHER.
                        ▲▲ EDGS's D-2 states the degeneracy exactly — "nearly
                           parallel ⇒ unstable in depth, ARBITRARILY FAR,
                           ARBITRARILY WRONG" — and assigns it to ε (Eq.8).
                           ε cannot detect it: the point lies ON both rays, so
                           it reprojects close to both pixels and the error is
                           small BECAUSE the geometry is ill-conditioned.  ε
                           addresses ED's D-4 (confident hallucinations that
                           happen to triangulate), a different failure.
                           At 0.5 px matcher noise a 0.0014° pair recovers
                           median depth 3.1 against a true 4 000, with 48.6%
                           behind a camera.  Invisible at EDGS's 180 reference
                           views; dominant at this corpus's 15–25.
                           Measured consequence of omitting it: z_max 122 673
                           against a baseline ~50, Ẑ ∈ [0, 0.0007], and two
                           attenuation channels clamped dead.
                                                    [06-implementation-deltas §6.8]
16          APPEND Gaussians:
17              f_dc  ← RGB2SH(I_i[u_i,v_i] / 255)                 [ED repo: corr_init.py:658]
18              f_rest ← ∅        ⚠ NOT 0 — the field does not exist here
                        ▲ EDGS's highest-severity delta (D-1: §3.5 SH init unimplemented) is
                          INERT on this baseline, because sh_degree = 0        [inferred]
19              o     ← 0 − 10·𝟙[ ε_ij^k > τ_proj ]   ⧉ logit      [ED repo: corr_init.py:660-666]
                        ▲ Eq.10's SAMPLING distribution is an OPACITY MASK in code — ED D-2
20              s     ← inv_act( ‖μ_k − campos_i‖ · 0.001 ) isotropic   [ED repo: corr_init.py:668-670]
21              q     ← copy of _rotation[−1]                      [ED repo: corr_init.py:671]
22      ⟨if NOT add_SfM_init⟩  PRUNE the original SfM Gaussians    [ED repo: trainer.py:243-251]
                        ▲ [PI] CANDIDATE TO FLIP: SfM points are the only geometry not derived
                          from a matcher that is known to fail on water        [PI — 01-taxonomy A1-b]
23      s ← s · 0.5    ⧉ ALL scales halved, globally               [ED repo: trainer.py:252-254]

24  ── medium model (baseline; identical in all eight cells) ──────────────────────────
25      β_bs ← U(0,1)³ ; B^∞ ← U(0,1)³ (as logit)                  [SS repo: models.py:54,61]
26      β_att ← [1.1, 0.95, 0.95]                                  [SS repo: models.py:216-218]
27      bg   ← logit([0.05, 0.25, 0.80])       ⚠ NOT IN THE PAPER  [SS repo: train.py:126-131]
28      opt_G, opt_bs, opt_at, opt_bg ← four Adam groups           [SS repo: train.py:91-92,131]

29  ⟨if M3⟩  Q ← { kmeans_dc(K_cb,3), kmeans_scale(K_cb,3), kmeans_rot(K_cb,4) }
                        ▲ THREE codebooks, not four: the SH group is dropped   [PI — CD-9]
                                                                   [VQ paper §3] [VQ repo: train_kmeans.py:131-144]

════════ PART 1 — TRAINING LOOP ════════════════════════════════════════════════════════
30  i ← 1
31  WHILE i ≤ 30 000:

     ── learning-rate schedule: M2's rewind is default-OFF, so no conflict ────────────
32     ⟨if M2 AND m2_lr_rewind AND i ≥ it_s1⟩  update_lr( i − it_s1 + 5000 )
                                        ⚠ DEFAULT OFF                  [MS repo: ms/train.py:98-99]
33     ⟨elif M1⟩              update_lr( max(i, 8000) )            [ED repo: trainer.py:146-147]
34     ⟨else⟩                 update_lr( i )                       [SS repo: train.py:177]
                        ▲ M1 CLAMPS DOWN because the init is already near-correct.
                          M2's REWIND is DISABLED BY DEFAULT (CD-7, reversed 2026-08-28):
                          it exists so freshly REINITIALIZED primitives can still move, and
                          under CD-4's simplification-only scoping nothing is reinitialized —
                          survivors keep their parameters AND their Adam state, since
                          prune_points index-selects the optimizer state. With no
                          reinitialization there is nothing for the rewind to compensate for.
                          So there is no precedence conflict to resolve: only line 33 fires.
                                                                   [PI — CD-7; see 03-variables IC-3]

     ── freeze schedule around the SeaThru transition ─────────────────────────────────
35     ⟨if i == it_st + 1⟩  freeze(μ, o, s, q) ; keep f_dc trainable   [SS repo: train.py:185-189]
36     ⟨if i == it_st + 2⟩  unfreeze all                               [SS repo: train.py:190-192]

37     v ← pop random from viewpoint_stack (without replacement)    [SS repo: train.py:196-198]

     ── INSERTION POINT 3 : quantization-aware substitution ───────────────────────────
38     ⟨if M3 AND i > it_vq⟩                                        [VQ repo: train_kmeans.py:126]
39         assign ← ( i mod t == 1 )                                [VQ repo: train_kmeans.py:127-130]
40         FOR g ∈ {dc, scale, rot}:
41             z_g ← the group's NON-quantized parameters
                        ▲ scale taken BEFORE exp(); rotation BEFORE normalization —
                          clustering in activated space would warp the metric  [VQ paper §4]
42             ⟨if assign⟩  nn_idx_g ← argmin cdist(z_g, C_g)  ⧉  EXPENSIVE, every t
                                                                   [VQ repo: kmeans_quantize.py:143,168]
43             ⟨else⟩       C_g ← Σ z_g[cls_ids] / cls_len       CHEAP, every iteration
                                                                   [VQ repo: kmeans_quantize.py:46-61]
                        ▲ THE ENABLING TRICK — both branches yield valid centroids; only the
                          PARTITION goes stale. This is why overhead is 1.4–1.7×, not 100×
                                                                   [VQ paper §3]
44             ẑ_g ← C_g[nn_idx_g]   ⧉ gather ; substitute into the render
                        ▲ μ and o are NEVER quantized: sharing positions "results in
                          overlapping Gaussians"; opacity is a scalar          [VQ paper §3]
                          ⇒ M3 CANNOT corrupt the two variables the baseline's
                            D-2 and D-4 arguments depend on                    [inferred]

     ── forward render: THREE rasterization passes ───────────────────────────────────
                        ▲ SeaSplat uses TWO. The third exists because of which
                          gradient buffer each pass writes into — see 46b.
                                                                   [PI — CD-23]
45     Ĵ, radii, vs_pts, w_acc, a_proj, a_max ← RASTERIZE(G, v)     [SS paper Eq.1] [SS repo: train.py:201-203]
                        ▲ the _ms fork returns Mini-Splatting's importance
                          accumulators and NO alpha, where SeaSplat's fork
                          returns alpha and no accumulators           [PI — CD-13]
46a    α     ← RASTERIZE(G, v; override_color = [0,1,0], bg = 0; means2D ← vs_pts)  ⧉
                                                                   [PI — CD-23] [repo: gaussian_renderer/__init__.py render_alpha]
                        ▲ SHARES vs_pts, so ∂L_α/∂means2D reaches the
                          densification accumulator — as it does in SeaSplat,
                          where α comes from line 45 itself
46b    Z_raw ← RASTERIZE(G, v; override_color = z_cam(μ), bg = 0; means2D ← OWN)
                                                                   [SS repo: gaussian_renderer/__init__.py:116-137]
                        ▲ keeps its OWN buffer, so depth gradients do NOT reach
                          density control — matching SeaSplat, whose depth pass
                          is likewise separate
                        ▲▲ THE GRADIENT-DESTINATION INVARIANT. A control-flow
                           property, invisible to any test of returned values:
                               density control must see      image + α
                               density control must NOT see  depth
                           A single [z,1,0] probe sharing vs_pts (CD-22) admits
                           depth, and the terms partially cancel — measured
                           635,038 primitives against vanilla's 4,462,668.
                           Sharing nothing, as first merged, omits α: 743,457.
                           Splitting as above reproduces vanilla within its
                           run-to-run spread.
                                                    [measured n=3 — 13-campaign-addendum §13.2, §13.3]
47     Ẑ ← Z_raw / α ; nan_to_num ; ÷ normalize_depth               [SS repo: train.py:222-232]
48     Ẑ_min, Ẑ_max ← min Ẑ, max Ẑ    ⧉ LOG THESE                   [PI — CD-12]
49     Ẑ ← (Ẑ − Ẑ_min)/(Ẑ_max − Ẑ_min)      ⚠ PER-FRAME min–max     [SS repo: train.py:233-237]
                        ▲ ⇒ β are in units of NORMALISED per-frame depth, not inverse metres.
                          A change in the primitive population changes Ẑ_min/Ẑ_max and hence
                          RESCALES the medium model's only input — SeaSplat degeneracy D-2,
                          injected externally. This is the reason line 74 exists.
                                                                   [SS 05-constraints §5.3] [inferred]

     ── background composition / B^∞ warm start ───────────────────────────────────────
50     ⟨if learn_background AND NOT (bg_from_bs AND i > it_st)⟩
51         Ĵ ← Ĵ + σ(bg)·(1 − α)                    ⚠ NOT IN PAPER  [SS repo: train.py:214-216]
52     ⟨elif bg_from_bs AND i > it_st AND first time⟩
53         B^∞ ← bg ; rebuild opt_bs                ⚠ NOT IN PAPER  [SS repo: train.py:209-212]
                        ▲ replaces U(0,1) with a DATA-DERIVED water colour. Load-bearing
                          against degeneracy D-1, which is a GLOBAL OPTIMUM of L_GS
                                                                   [SS 05-constraints M-5]

     ── medium composition ────────────────────────────────────────────────────────────
54     ⟨if do_seathru AND i > it_st⟩                                [SS repo: train.py:246]
55         Â  ← exp( −clamp(β_att ⊛ Ẑ, ≥0) )                        [SS paper §IV.A]
56         Â⊘ ← exp( −clamp(β_att ⊛ Ẑ⊘, ≥0) )        ⊘              [SS repo: train.py:255]
57         D̂  ← Ĵ ⊙ Â                                               [SS paper §III.B]
58         B̂  ← σ(B^∞) ⊙ ( 1 − exp(−clamp(β_bs ⊛ Ẑ, ≥0)) )          [SS paper Eq.3]
59         B̂⊘ ← σ(B^∞) ⊙ ( 1 − exp(−clamp(β_bs ⊛ Ẑ⊘, ≥0)) )   ⊘     [SS repo: train.py:270]
60         Î  ← clamp( D̂ + B̂ , 0, 1 )                               [SS repo: train.py:273]
61     ⟨else⟩  Î ← Ĵ                                                [SS repo: train.py:285-292]

     ── losses: SEVEN TERMS, UNCHANGED BY ALL THREE MECHANISMS ────────────────────────
62     L ← 0.8·‖Î − I_v‖₁ + 0.2·(1 − SSIM(Î, I_v))                  [SS paper Eq.2] [SS repo: train.py:293]
63     L ← L + 1.00 · mean| Ẑ⊘ ⊙ (Î − I_v) |            ⊘ weight    [SS paper Eq.7] [SS repo: train.py:298-301]
64     L ← L + 0.01 · mean| α[ ‖Î⊘ − σ(B^∞)⊘‖₂ < 0.2√3 ] |          [SS paper Eq.9] [SS repo: train.py:331]
                        ▲ THE +2.42 dB TERM. Its gradient reaches ONLY α — and α is exactly
                          the variable M1 decays, M2 resets, and M3 leaves alone
                                                                   [SS 04-loss §4.4] [03-variables IC-1]
65     L ← L + 2.00 · ( mean|∂ₓẐ·e^{−∂ₓI}| + mean|∂_yẐ·e^{−∂_yI}| ) [SS paper Eq.8]
                        ▲ SIGNED image gradient — inherited deviation from Godard et al.,
                          shared by paper AND repo. Left unfixed so A0 = SeaSplat  [SS S-1] [PI]
66     ⟨if i > it_gw⟩  L ← L + 0.10 · mean_c( mean(Ĵ_c) − 0.5 )²    [SS paper Eq.5]
67     ⟨if i > it_st⟩  L ← L + 2.00 · mean( relu(−Ĵ) + relu(Ĵ−0.7) )²   [SS paper Eq.6]
68     ⟨if i > it_st⟩  D̃ ← I_v⊘ − B̂⊘   ;  ⊘ BOTH operands          [SS paper Eq.4] [SS repo: train.py:400]
69         L ← L + 1.00 · [ 1000·SmoothL₁(relu(−D̃),0;β=0.2) + ‖relu(D̃)‖₁ ]
                        ▲ gradient reaches ONLY β_bs, B^∞. The Gaussians are invisible to this
                          term — which is why NO mechanism can perturb it       [SS 04-loss term 2]
70     ✗ NOT ADDED: λ_reg·Σα  (CompGS-VQ's ℓ1 opacity regulariser)
                        ▲ DISABLED — it would confound the M2 × M3 factorisation and add a
                          fifth writer to opacity                              [PI — CD-8] [04-loss §4.3]

71     zero_grad(all) ; BACKWARD(L)                                 [SS repo: train.py:421-428]
                        ▲ under M3 this is the STRAIGHT-THROUGH ESTIMATOR: forward used ẑ_g,
                          gradients route to the NON-quantized parameters opt_G holds
                                                                   [VQ paper §3, ref 7]

     ── alternating medium update (the well-posedness mechanism, in control flow) ─────
72     ⟨if do_seathru AND i > it_st⟩                                [SS repo: train.py:433]
73         warming ← ¬bs_inited
74         if warming OR (i mod Δ_med == 0) OR post_simp_rewarm:    [PI — CD-6 adds the 3rd clause]
75             n_target ← 1000 if warming else n_med (= 50)         [SS repo: train.py:436]
76             if med_counter < n_target:
77                 STEP(opt_bs) ; STEP(opt_at)    ── MEDIUM PARAMS ONLY
                                                                   [SS repo: train.py:446-447]
78                 med_counter += 1 ; CONTINUE ⟵ SKIPS i ← i+1 at line 96
                        ▲ these steps consume NO iteration budget. At defaults a
                          "30 000-iteration" run does ≈43 000 optimizer steps  [SS 08-… §8.3]
79             else: med_counter ← 0 ; bs_inited ← TRUE ; colour_adjust ← TRUE
                                                                   [SS repo: train.py:440-444]
80         ⟨if colour_adjust AND colour_counter < 2000⟩
81             STEP(opt_G)  ── effectively colour-only (μ,o,s,q frozen at line 35)
82             colour_counter += 1 ; CONTINUE ⟵ skips i ← i+1       [SS repo: train.py:456-463]

     ── density control ───────────────────────────────────────────────────────────────
83     ⟨if M1⟩                                                       ── densification OFF
                        ▲▲ opacity_reset_interval ← iterations, as EDGS sets it
                           `[ED 03-variables:116]`.  ONE parameter gates TWO
                           mechanisms and the name mentions only one:
                             (a) reset_opacity(), and
                             (b) size_threshold, which arms the size-based
                                 prune on line 85.
                           3DGS ties (b) to (a) because after a reset the
                           survivors have been re-grown by densification and
                           their scales are meaningful.  Under M1 densification
                           never runs and scales come from correspondence
                           distance, so arming (b) removes most of the cloud
                           with nothing to replace it: 325 875 → 36 575 at the
                           first armed event, iteration 3 100.
                                                    [PI — measured n=1, 13-addendum §13.11]
84         ⟨if i mod 10 == 0 AND it_st ≤ i < 15 000⟩  o ← log(exp(o)·0.99)
                                                                   [ED repo: trainer.py:81-85]
                        ▲ EDGS decays from step 0.  Here the window starts at
                          seathru_from_iter, NOT before it.
                        ▲▲ EDGS's cull removes "Gaussians the photometric loss
                           does not defend", which is sound when the loss is a
                           complete statement of the objective.  Before it_st
                           there is no medium term, so veiling haze must be
                           explained by GEOMETRY and the photometric optimum is
                           a few large blobs — degeneracy D-4.  A cull run in
                           that window decides what is "needed" against an
                           objective missing half the model, and M1 has no
                           densification to restore it: 471 531 → 6 291 before
                           iteration 10 000.
                                                    [PI — measured n=1, 13-addendum §13.11]
                        ▲ opacity_lr is ALSO halved upstream (0.025 vs 0.05);
                          not adopted here.  Collides with L_op either way
                                                                   [ED 05-constraints M-5] [03-variables IC-1]
85         ⟨if i < 15 000⟩  PRUNE o < 0.005  (size_threshold DISABLED, see 83)
                                                                   [ED repo: trainer.py:258-264]
86     ⟨else⟩                                                        ── 3DGS ADC
87         ⟨if i < 15 000⟩  add_densification_stats(vs_pts, vis)
88             ⟨if i mod 100 == 0 AND i > 500⟩ densify_and_prune(τ=2e-4, o_min=0.005)
                                                                   [SS repo: train.py:523-526]
89             ⟨if i mod 3000 == 0⟩  reset_opacity()                [SS repo: train.py:528-530]
                        ▲ RETAINED under M2, contrary to Mini-Splatting's silent removal —
                          it is a co-mechanism of L_op against water-column floaters
                                                                   [PI — CD-3] [MS delta D-1]

     ── INSERTION POINT 2 : simplification to budget ──────────────────────────────────
90     ⟨if M2 AND i ∈ {it_s1, it_s2}⟩                               [MS repo: ms/train.py:211,259]
91         I_imp ← 0 ; A_max ← 0
92         FOR every training view v':                              [MS repo: ms/train.py:216]
93             accum_w, area_proj, S ← RASTERIZE_imp(G, v')         [MS repo: gaussian_renderer/__init__.py:189-191]
94             A_max += S
95             I_imp += accum_w / area_proj  (outdoor)  |  accum_w  (indoor)
                                                                   [MS paper Eq.12 / §3.2]
                        ▲ NEITHER metric was designed for a scattering medium. `outdoor`'s
                          area normalisation exists to suppress SKY. Choice must be justified
                                                                   [MS App.E] [01-taxonomy A2-a] [PI]
96         I_imp[A_max == 0] ← 0    ⧉ INTERSECTION PRESERVING       [MS paper Eq.3] [MS repo: ms/train.py:232]
97         ⟨if i == it_s1⟩
98             P ← I_imp / Σ I_imp
99             idx ← np.random.choice(N, n_bud, p = P, replace=False)   ⧉
                        ▲ STOCHASTIC, not top-k: importance is SPATIALLY AUTOCORRELATED, so
                          thresholding removes whole REGIONS. Validated by CHAMFER DISTANCE,
                          not PSNR                                 [MS paper §4.2, Fig.6]
                        ▲ n_bud is an explicit BUDGET, not sampling_factor·N   [PI — CD-5]
100        ⟨if i == it_s2⟩  idx ← INIT_CDF_MASK(I_imp, thres = 0.99)  ⧉
                                                                   [MS repo: ms/train.py:31-44,282]
101        prune_points(¬idx) ; training_setup(opt)   ⧉ ADAM STATE DISCARDED
                                                                   [MS repo: ms/train.py:248-254]
102        post_simp_rewarm ← TRUE ; med_counter ← 0                [PI — CD-6]
                        ▲▲ THE CENTRAL [PI] OF THIS WORK. Ẑ_min/Ẑ_max (line 48) have just
                           changed discontinuously, so β_att and β_bs are now fitted to a
                           depth field that has been RESCALED. Without a medium-only
                           re-warm-up, SeaSplat's degeneracy D-2 is not merely available to
                           the optimizer — it has been INJECTED.
                           No source method faces this: none of them has a physical medium
                           model whose only spatial input is a per-frame-normalised depth map.
                                                                   [PI] [05-constraints §5.3 A2]

     ── parameter update ──────────────────────────────────────────────────────────────
103    STEP(opt_G) ; ⟨if learn_background⟩ STEP(opt_bg)             [SS repo: train.py:550-553]
104    i ← i + 1                                                    [SS repo: train.py:567]
105 END WHILE

════════ PART 2 — SAVE ═════════════════════════════════════════════════════════════════
106 SAVE μ (float32), o → .ply                                      [VQ repo: train_kmeans.py:190-196]
107 ⟨if M3⟩ FOR g ∈ {dc, scale, rot}:
108     n_bits ← ceil(log2(K_cb))          ⚠ NOT ceil(log2(N))      [PI — CD-11] [VQ delta D-4]
109     bitarray.extend( dec2binary(cls_ids_g, n_bits) )            [VQ repo: train_kmeans.py:264-266]
110     ✗ NOT IMPLEMENTED: sort + run-length encoding of indices    [VQ delta D-1]
111 SAVE kmeans_centers.pth, kmeans_args.npy                        [VQ repo: train_kmeans.py:267-279]
112 SAVE backscatter_<i>.pth, attenuate_<i>.pth                     [SS repo: train.py:562-563]
113 SAVE Ẑ_min/Ẑ_max history, β_att/β_bs/B^∞ history                [PI — CD-12]
114 REPORTED MODEL SIZE ← 106 + 109 + 111 + 112                     [PI]
════════════════════════════════════════════════════════════════════════════════════════
```

---

## 7.3 What the control flow makes visible

1. **The seven loss terms (lines 62–69) are byte-identical across all eight cells.** Every
   difference between A0 and A7 lives in lines 2–23, 38–44, and 90–102 — three disjoint
   regions. That is the composition claim, made structurally checkable rather than asserted.

2. **Line 44 is the reason A3 and A5 are the safe cells.** `μ` and `o` are never quantized,
   so M3 cannot reach the two variables that carry the baseline's D-2 and D-4 arguments.
   The isolation is structural, not a tuning outcome. `[inferred]`

3. **Line 64 and line 84 write to the same variable, ~1500 times, in opposite directions.**
   `L_op` pushes `α` down where the pixel looks like water; EDGS's decay pushes *every*
   `α` down regardless; M2's reinit pushes every `α` back *up* to 0.1. Reading lines 64, 84
   and 101 together is the clearest statement of interaction candidate IC-1.

4. **Lines 48–49 and 102 are the claim-(c) mechanism.** Line 49 makes the medium model's
   input a *relative* quantity; line 101 changes the population that determines the relative
   scale; line 102 is the remedy. Nothing in any of the four source methods contains this
   pattern, because no source method has both a per-frame-normalised depth input to a
   physical model and a mid-training population change. This is the pair of lines the
   novelty argument in `12-novelty-defensibility.md` rests on.

5. **Lines 78 and 82 are where "30 000 iterations" stops meaning what it says**, and line 74's
   third clause makes it worse. Every wall-clock figure in `08-computational-profile.md` is
   reported against *effective optimizer steps* for this reason.

6. **Lines 18 and 110 are two paper-claims-without-code that survive into this method** in
   opposite ways. Line 18 renders EDGS's largest gap **inert** (there is no `f_rest` to
   initialize). Line 110 leaves CompGS-VQ's second storage mechanism **missing**, so the
   compression ceiling is below the published figure before any baseline difference is
   counted.

7. **There is exactly one place the algorithm needs a CUDA extension that does not exist in
   any single source repository**: line 46 under M2, which needs SeaSplat's depth override on
   Mini-Splatting's forked kernel (CD-13). Everything else composes at the Python level.
