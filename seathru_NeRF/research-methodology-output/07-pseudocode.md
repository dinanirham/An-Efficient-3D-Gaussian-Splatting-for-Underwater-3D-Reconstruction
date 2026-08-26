# §7 — Pseudocode: the full SeaThru-NeRF train step

Notation follows the paper (`σ^obj, σ^attn, σ^bs, c^obj, c^med, T^obj, w^obj, δ_i, s_i, Ĉ`).
Tags: `[paper]` / `[repo: file:line]` / `[inferred]`. Schedule-gated lines are **⟨gate⟩**;
gradient-detached tensors are marked `⊘`.

```text
────────────────────────────────────────────────────────────────────────────────────────
ALGORITHM  SeaThru-NeRF — one training step (batch of B = 16 384 rays)
────────────────────────────────────────────────────────────────────────────────────────
INPUT   Θ_prop   PropMLP weights (4×256, density head only)     [repo: configs/llff_256_uw.gin]
        Θ_obj    UWMLP object trunk (8×256) + bottleneck + colour head
        Θ_med    mediumMLP (net_depth_water = 1 × 128)          [repo: models.py:716,678]
        {C*(r)}  linear, white-balanced GT pixels               [paper §5.1]
CONST   L = num_levels = 2, N_prop = 128, N_nerf = 32           [repo: configs/llff_256_uw.gin]
        λ = 1e-4, κ = uw_acc_loss_factor = 6                    [paper Eq.24] [repo: configs.py:173]
────────────────────────────────────────────────────────────────────────────────────────

 1  r ← sample B rays uniformly at random from the training images
                                                                [repo: datasets.py:472-487]
 2  (ŝ, ŵ) ← [0,1], weight 1                        initial interval
                                                                [repo: models.py:116-123]

    ── hierarchical sampling: L = 2 levels ────────────────────────────────────────────
 3  FOR level ℓ = 0 … L-1:
 4      is_prop ← (ℓ < L-1)
 5      tdist ← resample(ŝ, ŵ, N_prop if is_prop else N_nerf)   [repo: models.py, stepfun]
 6      (means, covs) ← conical frustums along r                [paper: mip-NeRF 360]
 7      x ← IPE(means, covs; max_deg_point = 16, octahedron basis)
                                                                [repo: models.py:774-777]
 8      ⟨if is_prop⟩ σ^obj ← PropMLP(x)                ; c^obj ← 0   (disable_rgb)
 9      ⟨else⟩
10          h        ← trunk_8x256(x)                            [repo: models.py:781-786]
11          σ^obj_i  ← softplus(Dense₁(h) + density_bias)   density_bias = 0
                                                                [repo: models.py:836; gin]
12          b        ← Dense_256(h)                     bottleneck  [repo: models.py:846]

            ── mediumMLP: ONE evaluation per RAY, viewing direction ONLY ─────────────
13          e        ← pos_enc(viewdirs; deg_view = 4, append_identity)
                                                                [repo: models.py:722-724]
14          u        ← softplus(Dense_128(e))         ⟵ ONE layer  [repo: models.py:716,865-869]
                        ▲ paper §4.5 says 6 layers × 256 — delta D-1
15          c^med    ← sigmoid(Dense₃(u))                        [paper §4.3] [repo: models.py:871]
16          σ^bs     ← softplus(Dense₃(u) + water_bias)          [paper Eq.21] [repo: models.py:878]
17          σ^attn   ← softplus(Dense₃(u) + water_bias)          [paper Eq.20] [repo: models.py:889]
                        ▲ σ^attn ≠ σ^bs is the §4.3 refinement (mechanism M-5)
                        ▲ NO positional input ⇒ the medium CANNOT be spatially localised.
                          This is the well-posedness mechanism, enforced by architecture.
                                                                [paper §4.1] [inferred]

18          ⟨if uw_rgb_dir⟩  b ← [b, e]                          [repo: models.py:898-900]
                        ▲ FALSE in the released gin ⇒ c^obj is VIEW-INDEPENDENT,
                          contradicting paper §4.3 — delta D-3
19          c^obj_i  ← sigmoid(Dense₃(viewdir_subMLP(b)))        [repo: models.py:913-925]

            ── quadrature weights ───────────────────────────────────────────────────
20          δ_i      ← (t_{i+1} − t_i)·‖d‖                       [repo: render.py:163-164]
21          δ^bs_i   ← ⊘(t_{i+1} − t_i)·‖d‖        SPACING DETACHED
                                                                [repo: render.py:179]
                        ▲ closes the σ·s scale ambiguity from the sampler side (M-3);
                          not mentioned in the paper — delta D-4

22          T^obj_i  ← exp( −Σ_{j<i} σ^obj_j δ_j )               [paper Eq.22] [repo: render.py:214-219]
23          α_i      ← 1 − exp( −σ^obj_i δ_i )                   [repo: render.py:213]
24          w^obj_i  ← α_i · T^obj_i                             [paper Eq.23] [repo: render.py:220]

25          A_i      ← exp( −Σ_{j<i} σ^attn · δ^bs_j )   attenuation transmittance
                                                                [paper Eq.20] [repo: render.py:205-210]
26          α^bs_i   ← 1 − exp( −σ^bs · δ^bs_i )                 [repo: render.py:185]
27          T^bs_i   ← exp( −Σ_{j<i} σ^bs · δ^bs_j )             [repo: render.py:187-192]

            ── the SPLIT rendering equation ─────────────────────────────────────────
28          Ĉ^obj    ← Σ_i  w^obj_i · A_i · c^obj_i              [paper Eq.20] [repo: render.py:320]
29          Ĉ^med    ← Σ_i  T^obj_i · (α^bs_i · T^bs_i) · c^med  [paper Eq.21] [repo: render.py:324]
30          Ĉ        ← Ĉ^obj + Ĉ^med                             [paper Eq.12] [repo: render.py:326]
31          J        ← ⊘( Σ_i w^obj_i · c^obj_i )   RESTORED IMAGE, OUTPUT ONLY
                                                                [repo: render.py:319]
                        ▲ stop-gradient: J appears in NO loss and NO metric — delta D-5
32      (ŝ, ŵ) ← (tdist, w^obj)          feed forward to next level

    ── losses ─────────────────────────────────────────────────────────────────────────
33  L ← 0
34  Ĉ_clip ← min(1, Ĉ)                                          [repo: train_utils.py:96]
                        ▲ clipping absent from paper Eq.25 — delta D-6
35  g      ← 1 / (1e-3 + ⊘Ĉ_clip)                    RawNeRF gradient scaling
                                                                [paper Eq.25] [repo: train_utils.py:99]
36  L ← L + 1.0 · mean_lossmult( (Ĉ_clip − C*)² · g² )          [paper Eq.25] [repo: train_utils.py:100,108-110]

37  ⟨if interlevel_loss_mult > 0⟩   (= 1)
38      L ← L + 1.0 · Σ_{ℓ<L-1} mean( lossfun_outer( ⊘ŝ_last, ⊘ŵ_last, ŝ_ℓ, ŵ_ℓ ) )
                                                                [paper Eq.24 L_prop] [repo: train_utils.py:115-127]
                        ▲ both NeRF-level args detached ⇒ trains the PROPOSAL MLP only

39  ⟨if distortion_loss_mult > 0⟩   (= 0 → SKIPPED)             [repo: gin; train_utils.py:129-136]
                        ▲ mip-NeRF 360's distortion loss is switched OFF — delta D-7

40  ⟨if use_uw_acc_trans_loss⟩      (= True)
41      mult ← uw_final_… if step ≥ uw_decay_acc(5000) else uw_initial_…
               (both = 1e-4 ⇒ the ramp is a NO-OP)              [repo: train.py:127-134; gin]
42      L ← L + mult · mean( −log( κ·e^{−|1 − T^obj|/0.1} + e^{−|T^obj|/0.1} ) )
                                                                [paper Eq.26-27] [repo: train_utils.py:160-162]
                        ▲ κ = 6: the mixture is ASYMMETRIC, biased toward T^obj = 1.
                          Paper Eq.26 is symmetric — delta D-2

43  ⟨if use_uw_acc_weights_loss⟩    (= False → SKIPPED)         [repo: gin; train_utils.py:138-150]
44  ⟨if use_uw_sig_med_loss⟩        (= False → SKIPPED, "not in the paper")
                                                                [repo: configs.py:168; train_utils.py:171-187]

    ── backward / update ──────────────────────────────────────────────────────────────
45  (L, stats), grad ← jax.value_and_grad(loss_fn)(Θ)           [repo: train_utils.py:304]
46  grad ← pmean(grad, axis_name='batch')          all-reduce across devices
                                                                [repo: train_utils.py:306]
47  FOR each MLP k in grad:                          PER-MLP clipping
48      grad_k ← clip(grad_k, −grad_max_val, +grad_max_val)     [repo: train_utils.py:194-196]
49      grad_k ← grad_k · min(1, grad_max_norm / ‖grad_k‖)      [repo: train_utils.py:200-205]
50  grad ← nan_to_num(grad)              NaNs silently zeroed   [repo: train_utils.py:313]
51  Θ ← Adam_step(Θ, grad; lr = cosine/log-lerp 2e-3 → 2e-5, eps = 1e-8)
                                                                [repo: gin; train_utils.py:315]
────────────────────────────────────────────────────────────────────────────────────────
                     Repeat for 250 000 steps (≈10 h on one A100)  [paper §4.5]
────────────────────────────────────────────────────────────────────────────────────────
```

## What the control flow makes visible

1. **Line 13 has no `x` in it.** The mediumMLP's input is *only* `viewdirs`. That single
   fact is the entire well-posedness argument (mechanism M-1 of
   [`05-constraints.md`](05-constraints.md)): a medium that cannot see position cannot
   pretend to be a localised object. Contrast SeaSplat, which achieves the same end with
   nine global constants plus five auxiliary priors.

2. **Lines 28–29 are structurally different summands, not a post-hoc composition.**
   SeaSplat computes `Î = Ĵ ⊙ Â + B̂` *after* rendering; SeaThru-NeRF's two terms are both
   inside the quadrature sum, each carrying its own transmittance. The medium therefore
   participates in occlusion reasoning; in SeaSplat it cannot.

3. **Line 21 is the analogue of SeaSplat's `Ẑ.detach()`.** Both methods sever the gradient
   between the medium model and whatever produces the range coordinate — SeaSplat detaches
   the rasterized depth, SeaThru-NeRF detaches the sample spacing. Neither paper mentions
   its own version prominently (SeaSplat mentions it in one sentence; SeaThru-NeRF not at
   all).

4. **Line 31 is a dead end in the computation graph.** The headline capability ("render
   clear views … removing the medium", `[paper §1]`) is produced by a `stop_gradient` and
   is never scored. Any restoration claim from either underwater paper is necessarily
   qualitative.

5. **Line 42 carries `λ = 1e-4` against two unit-weight reconstruction terms.** The prior
   is a nudge; the architecture does the work. This is a genuinely different design
   philosophy from SeaSplat's six-λ, 200×-spread objective.

6. **Lines 38 and 42 both operate on quantities the object branch produces
   (`ŵ`, `T^obj`) — nothing in the loss touches `c^med`, `σ^bs`, `σ^attn` directly.**
   The medium parameters are trained *only* through the reconstruction term at line 36.
   There is no medium prior at all, which is why the optional `L_sig_med` (line 44) exists
   in the code.
