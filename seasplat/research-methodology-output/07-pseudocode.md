# §7 — Pseudocode: the full SeaSplat train step

Notation follows the paper (`μ, Σ, S, R, o, c, Ĵ, Ẑ, Â, B̂, Î, β^D, β^B, B^∞, α`), not the
repo's Python identifiers. Every line is tagged `[paper]`, `[repo: file:line]`, or
`[inferred]`. Schedule-gated lines are marked **⟨gate⟩**; gradient-detached tensors are
marked `⊘`.

```text
────────────────────────────────────────────────────────────────────────────────────────
ALGORITHM  SeaSplat — one outer training iteration
────────────────────────────────────────────────────────────────────────────────────────
INPUT   G = {(μ_n, S_n, R_n, o_n, c_n)}_{n=1..N}            3D Gaussians          [paper §III.A]
        θ_med = (β^D ∈ ℝ³, β^B ∈ ℝ³, B^∞ ∈ ℝ³)              global medium         [repo: models.py:54,61,216]
        bg ∈ ℝ³                                             learned background    [repo: train.py:130]  ← NOT IN PAPER
        {I_v, K_v, T^cam_world,v}                           training views        [paper §IV.A]
GATES   it_st = seathru_from_iter (README: 10 000)                                [repo: README.md]
        it_gw = gw_from_iter = 10 000                                             [repo: arguments/__init__.py:157]
        Δ_med = update_bs_at_interval = 100,  n_med = update_bs_at_count = 50     [repo: arguments/__init__.py:180-181]
────────────────────────────────────────────────────────────────────────────────────────

 1  update_learning_rate(G, i)                                          [repo: train.py:177]

    ── freeze schedule ────────────────────────────────────────────────────────────────
 2  ⟨if i == it_st + 1⟩  freeze(μ, o, S, R);  keep c trainable          [repo: train.py:185-189]
 3  ⟨if i == it_st + 2⟩  unfreeze all                                   [repo: train.py:190-192]

    ── sample view ────────────────────────────────────────────────────────────────────
 4  v ← pop random from viewpoint_stack   (sample WITHOUT replacement,
                                           stack refilled when empty)   [repo: train.py:196-198]

    ── forward render: TWO rasterization passes ───────────────────────────────────────
 5  Ĵ, α, radii, viewspace_pts ← RASTERIZE(G, v)                        [paper §III.A / Eq.1] [repo: train.py:201-203]
 6  Z_raw               ← RASTERIZE(G, v; override_color = z_cam(μ))    [paper §IV.C]  [repo: gaussian_renderer/__init__.py:116-137]
 7  Ẑ ← Z_raw / α                                                       [repo: train.py:223]
 8  Ẑ ← nan_to_num(Ẑ, max(finite Ẑ))                                    [repo: train.py:224-231]
 9  Ẑ ← Ẑ / normalize_depth        (=1.0)                               [repo: train.py:232]
10  ⟨if norm_depth_max⟩  Ẑ ← (Ẑ − min Ẑ)/(max Ẑ − min Ẑ)                [repo: train.py:233-237]
                        ▲ per-frame min–max ⇒ β are in NORMALISED depth units,
                          not inverse metres                            [inferred: see 05-constraints §5.3]

    ── background composition (pre-SeaThru only) ──────────────────────────────────────
11  ⟨if learn_background AND NOT (bg_from_bs AND i > it_st)⟩
12      Ĵ ← Ĵ + σ(bg)·(1 − α)                                           [repo: train.py:214-216]  ← NOT IN PAPER
13  ⟨else if bg_from_bs AND i > it_st AND first time⟩
14      B^∞ ← bg ;  rebuild bs_optimizer                                [repo: train.py:209-212]  ← NOT IN PAPER
                        ▲ data-derived warm start for B^∞ (see 05-constraints M-5)

    ── medium composition ─────────────────────────────────────────────────────────────
15  ⟨if do_seathru AND i > it_st⟩                                       [repo: train.py:246]
16      Â   ← exp( −clamp(β^D ⊛ Ẑ, ≥0) )                                [paper §IV.A]  [repo: models.py:226-232]
17      Â⊘  ← exp( −clamp(β^D ⊛ Ẑ⊘, ≥0) )          ⊘ depth detached     [repo: train.py:255]
18      D̂   ← Ĵ ⊙ Â                                                     [paper §III.B] [repo: train.py:256]
19      B̂   ← σ(B^∞) ⊙ ( 1 − exp(−clamp(β^B ⊛ Ẑ, ≥0)) )                 [paper §III.B / Eq.3] [repo: models.py:70-85]
20      B̂⊘  ← σ(B^∞) ⊙ ( 1 − exp(−clamp(β^B ⊛ Ẑ⊘, ≥0)) )  ⊘            [repo: train.py:270]
21      Î   ← clamp( D̂ + B̂ , 0, 1 )                                     [paper §IV.A]  [repo: train.py:273]
22  ⟨else⟩  Î ← Ĵ                                                       [repo: train.py:285-292]

    ── losses ─────────────────────────────────────────────────────────────────────────
23  L ← (1−0.2)·‖Î − I‖₁ + 0.2·(1 − SSIM(Î, I))                         [paper Eq.2]  [repo: train.py:293]

24  ⟨if add_recon_depth_l1⟩                                             [repo: train.py:296]
25      L ← L + 1.0 · mean| Ẑ⊘ ⊙ (Î − I) |            ⊘ weight detached [paper Eq.7]  [repo: train.py:298-301]
                        ▲ detach here forbids the "shrink Ẑ" shortcut

26  ⟨if learn_background⟩                                               [repo: train.py:309]
27      ref ← σ(B^∞)⊘  if (do_seathru ∧ i>it_st)  else  σ(bg)⊘          [repo: train.py:310,319]
28      src ← Î⊘       if (do_seathru ∧ i>it_st)  else  Ĵ_raw⊘          [repo: train.py:310,319]
29      M   ← [ ‖src − ref‖₂ < 0.2·√3 ]                                 [repo: losses.py:248,283]
30      L ← L + 0.01 · mean| α[M] |                    only α gets grad [paper Eq.9]  [repo: train.py:331]
                        ▲ paper uses I (capture) and ‖·‖²₂; repo uses Î and ‖·‖₂ — delta D-6

31  ⟨if use_depth_smooth_loss⟩                                          [repo: train.py:340]
32      L ← L + 2.0 · ( mean|∂ₓẐ·e^{−∂ₓI}| + mean|∂_yẐ·e^{−∂_yI}| )     [paper Eq.8]  [repo: depth_losses.py:17-24]
                        ▲ SIGNED image gradient in the exponent (not |∂I|) — deviates
                          from Godard et al. [35]; paper Eq.8 has the same signed form
                                                                        [repo: depth_losses.py:26-40 shows the abs version, disabled]

33  ⟨if use_gw_loss AND i > it_gw⟩                                      [repo: train.py:354,370]
34      L ← L + 0.1 · mean_c( mean_{H,W}(Ĵ_c) − 0.5 )²                  [paper Eq.5]  [repo: losses.py:190-203]

35  ⟨if use_rgb_sat_loss AND do_seathru AND i > it_st⟩                  [repo: train.py:381-382]
36      L ← L + 2.0 · mean( relu(−Ĵ) + relu(Ĵ − 0.7) )²                 [paper Eq.6]  [repo: losses.py:228-232]
                        ▲ squared + two-sided; paper is linear + one-sided — delta D-5

37  ⟨if use_dcp_loss⟩                                                   [repo: train.py:396]
38      ⟨if do_seathru AND i > it_st⟩
39          D̃ ← I⊘ − B̂⊘                    both operands detached       [paper Eq.4]  [repo: train.py:400]
40          L ← L + 1.0 · [ 1000·SmoothL₁(relu(−D̃),0;β=0.2) + ‖relu(D̃)‖₁ ]
                                                                        [paper Eq.4]  [repo: losses.py:156-160]
                        ▲ k = 1000. Gradient reaches ONLY β^B and B^∞ — the Gaussians
                          are invisible to this term. This is the mechanism that makes
                          B̂ ≡ 0 (degeneracy D-1) expensive.             [paper §IV.A]
41      ⟨else⟩  compute L_bs for logging only, DO NOT add               [repo: train.py:404-407]

    ── backward ───────────────────────────────────────────────────────────────────────
42  zero_grad(opt_G);  ⟨if i>it_st⟩ zero_grad(opt_bs, opt_at);  zero_grad(opt_bg)
                                                                        [repo: train.py:421-426]
43  BACKWARD(L)                                                         [repo: train.py:428]

    ── ALTERNATING UPDATE — the well-posedness mechanism in control flow ──────────────
44  ⟨if do_seathru AND i > it_st⟩                                       [repo: train.py:433]
45      warming ← (¬bs_inited)                                          [repo: train.py:434]
46      if warming OR (i mod Δ_med == 0):
47          n_target ← 1000 if warming else n_med(=50)                  [repo: train.py:436]
48          if med_counter < n_target:
49              STEP(opt_bs); STEP(opt_at)     ── medium params ONLY    [repo: train.py:446-447]
50              med_counter ← med_counter + 1
51              CONTINUE  ⟵⟵ SKIPS `i ← i+1` at line 65                 [repo: train.py:453 vs 567]
                        ▲ so these steps consume NO iteration budget    [inferred]
52          else:
53              med_counter ← 0 ; bs_inited ← at_inited ← TRUE
54              colour_adjust ← TRUE                                    [repo: train.py:440-444]
55      ⟨if colour_adjust⟩                                              [repo: train.py:456]
56          if colour_counter < 2000:
57              STEP(opt_G)   ── with μ,o,S,R frozen since line 2, so
58                               EFFECTIVELY colour-only                [repo: train.py:461] [inferred from line 2]
59              colour_counter ← colour_counter + 1 ; CONTINUE ⟵ skips i←i+1
60          else: colour_adjust ← FALSE                                 [repo: train.py:457-459]

    ── densification / pruning (3DGS schedule, unchanged) ─────────────────────────────
61  ⟨if i < densify_until_iter (15 000)⟩                                [repo: train.py:517]
62      max_radii2D[vis] ← max(max_radii2D[vis], radii[vis])
        add_densification_stats(viewspace_pts, vis)                     [repo: train.py:520-521]
63      ⟨if i mod 100 == 0 AND i > 500⟩
            densify_and_prune(τ_grad=2e-4, min_opacity=0.005,
                              extent=cameras_extent,
                              size_threshold = 20 if i>3000 else None)  [repo: train.py:523-526]
64      ⟨if i mod 3000 == 0⟩  reset_opacity()                           [repo: train.py:528-530]

    ── parameter-group-specific update ────────────────────────────────────────────────
65  ⟨if i < iterations⟩  STEP(opt_G) ; ⟨if learn_background⟩ STEP(opt_bg)
                                                                        [repo: train.py:550-553]
66  i ← i + 1                                                           [repo: train.py:567]
────────────────────────────────────────────────────────────────────────────────────────
```

## What the control flow makes visible

1. **Three optimizers are never stepped on the same pass.** Lines 49 and 65 are separated
   by a `CONTINUE`. When the medium steps, the Gaussians do not; when the Gaussians step,
   the medium does not. Block-coordinate descent, not joint descent — the mechanism M-2 of
   [`05-constraints.md`](05-constraints.md).

2. **Every auxiliary prior is routed to exactly one parameter group** by the `⊘` marks:
   - line 40 (`L_bs`): both operands detached from geometry ⇒ **`β^B, B^∞` only**.
   - line 30 (`L_op`): `src` and `ref` detached ⇒ **`α` (i.e. `o`) only**.
   - line 25 (`L_Z-recon`): the *weight* is detached but the residual is not ⇒ geometry
     receives a depth-modulated photometric gradient, but cannot cheat by shrinking `Ẑ`.
   - lines 23, 34, 36: no detach ⇒ these are the only terms that shape `Ĵ` and geometry
     jointly.

3. **`Ẑ` reaches the medium model live at line 16/19 but detached at 17/20.** This is the
   D-3 delta of [`06-implementation-deltas.md`](06-implementation-deltas.md): the paper's
   "detached to prevent gradients from flowing through" describes lines 17/20, while lines
   16/19 keep the geometry-constraining path open.

4. **Lines 51 and 59 are where a naive reading of "30 000 iterations" breaks.** The
   `CONTINUE` sits above the counter increment, so the real optimizer-step count at
   defaults is ≈ 43 000, not 30 000 (see D-8).
