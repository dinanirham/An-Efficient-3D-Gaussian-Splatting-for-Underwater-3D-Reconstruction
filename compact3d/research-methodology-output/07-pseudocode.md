# §7 — Pseudocode: the full CompGS train step

Notation follows the paper (`N, K, d, α, λ_reg, t, μ, Σ, S, R`). Tags: `[paper]` /
`[repo: file:line]` / `[inferred]`. ⧉ = non-differentiable / cached. **⚠ = undocumented or
divergent.** Everything unmarked is stock 3DGS supplied by the file overlay.

```text
════════════════════════════════════════════════════════════════════════════════════════
ALGORITHM  CompGS / Compact3D — one training iteration
════════════════════════════════════════════════════════════════════════════════════════
INPUT   3DGS model: μ (N,3), α (N,1), f_dc (N,3), f_rest (N,45), s (N,3), r (N,4)
        four Quantize_kMeans objects: dc, sh, scale, rot
CONST   kmeans_st_iter   : paper 20 000 · run.sh 15 000 ⚠ · CLI default 30 000 (⇒ off)
        kmeans_freq (t)  = 100                                   [paper §3] [repo: :377]
        kmeans_iters     : paper 1 · CLI default 1 ✅ · run.sh 10 ⚠
        K                : dc 4096 · sh 4096 (run.sh: 512 ⚠) · scale/rot 4096 (paper: 16384/32768 ⚠)
        λ_reg = 1e-7, active 15 000 < i ≤ max_prune_iter (20 000)  [paper §4] [repo: :158-166]
────────────────────────────────────────────────────────────────────────────────────────

 1  FOR i = 1 … 30 000:
 2      cam ← pop random training view                            (3DGS)

        ═══ QUANTIZATION-AWARE FORWARD ═══════════════════════════════════════════════
 3      ⟨if i > kmeans_st_iter⟩                                   [repo: train_kmeans.py:126]
 4          assign ← (i mod t == 1)                               ⚠ off-by-one, harmless
                                                                  [repo: train_kmeans.py:127-130]
                        ▲ paper §4 also says assignments FREEZE after 25K.
                          NO SUCH FREEZE EXISTS in code — delta D-3
 5          FOR each group g ∈ {dc, sh, scale, rot}:              [repo: train_kmeans.py:131-144]
 6              z ← the group's NON-quantized parameters
                        ▲ scale is taken BEFORE exp(); rotation BEFORE normalization
                          — clustering in activated space would warp the metric
                                                                  [paper §4] [inferred]
 7              ⟨if assign⟩   ── the EXPENSIVE branch, once every t iterations ──
 8                  dist ← cdist(z, C_g)                          [repo: kmeans_quantize.py:41-43]
 9                  nn_index ← argmin(dist, dim=−1)               ⧉ [repo: kmeans_quantize.py:143,168]
10                  C_g ← mean of z within each cluster
11                  cls_ids ← nn_index                            [repo: kmeans_quantize.py:118]
12              ⟨else⟩        ── the CHEAP branch, every other iteration ──
13                  C_g ← Σ z[cluster_ids] / cluster_len          re-average with CACHED indices
                                                                  [repo: kmeans_quantize.py:46-61]
                        ▲ THE ENABLING TRICK: "updating assignments given centroids" is the
                          expensive half; "updating centroids given assignments" is a simple
                          averaging. Do the cheap half every step, the costly half every t.
                          "crucial in limiting the training time"        [paper §3]
14              ẑ_g ← C_g[nn_index]                               ⧉ gather
                                                                  [repo: kmeans_quantize.py:194,204]
15              substitute ẑ_g into the model for rendering       [paper §3]

16      Î ← RASTERIZE(μ, α, ẑ_dc, ẑ_sh, ẑ_scale, ẑ_rot, cam)      (3DGS, unchanged)
                        ▲ μ and α are NEVER quantized: sharing positions "results in
                          overlapping Gaussians"; opacity "is a single scalar"  [paper §3]

        ═══ LOSS ═════════════════════════════════════════════════════════════════════
17      L ← 0.8·‖Î − I‖₁ + 0.2·(1 − SSIM(Î, I))                   [repo: train_kmeans.py:167]
18      ⟨if opacity_reg AND 15 000 < i ≤ max_prune_iter⟩          ⚠ 15000 HARD-CODED
                                                                  [repo: train_kmeans.py:158-162]
19          L ← L + λ_reg · Σ_j α_j        (α = sigmoid(·) ≥ 0 ⇒ .sum() IS the ℓ1 norm)
                                                                  [paper §3] [repo: :164-166]
                        ▲ WHY: after quantization, the UNQUANTIZED position + opacity are
                          ">80% of memory", so "quantization cannot improve the compression
                          any further". The only remaining lever is FEWER GAUSSIANS —
                          and that is also where the 2–3× FPS gain comes from.   [paper §3]

        ═══ BACKWARD — the STE step ══════════════════════════════════════════════════
20      BACKWARD(L)                                               [repo: train_kmeans.py:168]
                        ▲ STRAIGHT-THROUGH ESTIMATOR: the forward used ẑ, but gradients are
                          routed to the NON-QUANTIZED parameters, which are what the
                          optimizer holds. This is what makes the parameters "amenable to
                          quantization" — post-hoc clustering alone degrades quality.
                                                                  [paper §3, ref 7]

        ═══ 3DGS DENSITY CONTROL — UNCHANGED ═════════════════════════════════════════
21      ⟨if i < densify_until_iter⟩ densify_and_prune(2e-4, 0.005, extent, size_thr)
22      ⟨if i mod opacity_reset_interval == 0⟩  reset_opacity()   [repo: train_kmeans.py:217-218]
                        ▲ NOTE: reset_opacity() IS still called here — unlike
                          ../mini-splatting/ and ../OMG/, which silently remove it. [inferred]

        ═══ OPACITY PRUNING ══════════════════════════════════════════════════════════
23      ⟨if opacity_reg AND 15 000 < i ≤ max_prune_iter AND i mod 1000 == 0⟩
24          gaussians.prune(0.005, extent, size_threshold=None)   [paper §4] [repo: :220-226]

25      optimizer.step() ; zero_grad()                            (3DGS)

        ═══ SAVE (at save_iterations) ════════════════════════════════════════════════
26      ⟨if i > kmeans_st_iter⟩
27          save NON-quantized attributes only → .ply             [repo: train_kmeans.py:190-196]
28          FOR each group g:
29              n_bits ← ceil(log2(len(cls_ids)))                 ⚠ = ceil(log2(N)), NOT log2(K)
                                                                  [repo: train_kmeans.py:263]
                        ▲ cls_ids is the per-Gaussian assignment vector (length N), so for
                          N≈1M this is 20 bits where 12 would do — delta D-4  [inferred]
30              bitarray.extend( dec2binary(cls_ids, n_bits) )    [repo: train_kmeans.py:264-266]
                        ▲ ⚠ NO SORTING, NO RUN-LENGTH ENCODING.
                          paper §3 + abstract describe sorting by one index and storing run
                          counts ("n integers to k integers"). ABSENT — delta D-1
31          write kmeans_inds.bin, kmeans_centers.pth, kmeans_args.npy
                                                                  [repo: train_kmeans.py:267-279]
════════════════════════════════════════════════════════════════════════════════════════
POST-TRAINING (optional)
  · BitQ: position → 16 bits, opacity → 8 bits, rest 32       [paper Tab.1] [unverified]
  · decompress_to_ply.py → standard 3DGS .ply for SIBR viewers   [repo: decompress_to_ply.py]
════════════════════════════════════════════════════════════════════════════════════════
```

## What the control flow makes visible

1. **Lines 7–13 are the paper's cleverest idea, and they are a cost decomposition, not an
   approximation of K-means quality.** Both branches produce valid centroids; only the
   *partition* goes stale. That is why `t` can be as large as 500 without harm `[paper §3]` and
   why training overhead is 1.4–1.7× rather than 100×.

2. **Line 20 is the whole reason this works.** The forward pass renders the *quantized* model,
   so the loss measures quantization error; the backward pass updates the *unquantized*
   parameters, so the optimizer can move them somewhere that quantizes better. Post-hoc
   clustering has neither property.

3. **Lines 16 and 19 encode the paper's causal chain.** Position and opacity are excluded from
   VQ at line 16 → they dominate the residual budget → line 19's regulariser exists solely to
   reduce their *count*. Compression and speedup come from **different** mechanisms.

4. **Line 22 is worth noting for the comparison set.** CompGS is the only compression folder
   here that leaves 3DGS's `reset_opacity()` intact — `../mini-splatting/` and `../OMG/` both
   remove it silently.

5. **Line 30 is where the abstract's second storage claim disappears.** Sorting + RLE is
   described in both the abstract and §3; the code bit-packs and stops.

6. **Line 29 is a probable bug with a measurable cost.** Bit width tracks the Gaussian count
   rather than the codebook size.
