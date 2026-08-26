# §7 — Canonical pseudocode

One algorithm. Setting all three flags `False` recovers vanilla SeaSplat exactly; every other
configuration is a flag subset. Line tags:

`[SeaSplat]` inherited · `[A1]` `[A2]` `[A3]` borrowed mechanism ·
`[integration]` composition logic original to this work ·
`[proposed]` **not implemented** — audit recommendation, shown for completeness and clearly
marked so it is never mistaken for shipped behaviour.

---

## 7.1 Stage 0 — Offline dense initialization `[A1]`

Runs once per scene. Skipped entirely when `use_dense_init = False`.

```python
def build_dense_cloud(                                             # [A1]
    scene_path: Path,
    num_refs: int = -1,          # all training views  [A1: adapted from EDGS's 180]
    nns: int = 3,
    matches_per_pair: int = 5_000,
    certainty_thr: float = 0.05,
    reproj_thr: float = 2.0,
    voxel: float = 0.005,
) -> BasicPointCloud:
    K, R, t, paths = load_colmap_cameras(scene_path)               # [integration] SeaSplat-side glue
    train_views = [v for i, v in enumerate(sorted_views) if i % 8 != 0]   # [SeaSplat] LLFF split
    refs = train_views if num_refs == -1 else subsample(train_views, num_refs)

    matcher = roma_outdoor(device="cuda")                          # [A1]
    points, colors = [], []

    for ref in refs:                                               # [A1]
        for nn in nearest_by_index(ref, train_views, k=nns):
            warp, cert = matcher.match(paths[ref], paths[nn])
            cert = cert * (cert > certainty_thr)                   # [A1]
            kp_a, kp_b = matcher.sample(warp, cert, num=matches_per_pair)

            # Pixel-space DLT — re-implemented, not ported: EDGS triangulates in
            # 3DGS NDC space, which SeaSplat's COLMAP loader does not expose.
            X, valid = triangulate_dlt(K[ref], R[ref], t[ref],     # [integration]
                                       K[nn],  R[nn],  t[nn],
                                       kp_a, kp_b, reproj_thr)
            points.append(X)
            colors.append(sample_source_colors(paths[ref], kp_a[valid]))

    pts, cols = voxel_dedup(concat(points), concat(colors), voxel) # [A1]
    return BasicPointCloud(points=pts, colors=cols, normals=zeros_like(pts))
```

> ⚠️ **Non-determinism enters here.** No seed is set, and RoMa matching is GPU-nondeterministic,
> so `len(pts)` — which *is* the experimental condition for A1 — varies between invocations
> (§10.3). Record the point count and a content hash of the emitted `.ply`.

---

## 7.2 Stage 1 — Training loop (canonical, flagged)

```python
def train(                                                          # [SeaSplat]
    scene: Scene,
    use_dense_init: bool = False,        # A1
    use_spatial_pruning: bool = False,   # A2
    dense_cloud: BasicPointCloud | None = None,
    max_gaussians: int = 800_000,
    imp_metric: str = "outdoor",
) -> GaussianModel:

    # ── Seed selection ────────────────────────────────────────────────────────
    seed = scene.sfm_point_cloud                                    # [SeaSplat] ~500 pts
    if use_dense_init and dense_cloud is not None:                  # [A1]
        seed = dense_cloud                                          # [A1] 222k–1.46M pts
    gaussians = GaussianModel(sh_degree=0)                          # [SeaSplat]
    gaussians.create_from_pcd(seed, scene.cameras_extent)           # [SeaSplat]

    medium = MediumModel()          # BackscatterNet + AttenuateNet — 9 global scalars
    optimizers = [gaussians.optimizer, medium.bs_opt, medium.att_opt]   # [SeaSplat] 3 separate

    for it in range(1, ITERATIONS + 1):                             # ITERATIONS = 30_000
        cam = next_training_camera()                                # [SeaSplat]

        # ── Forward ───────────────────────────────────────────────────────────
        J_hat, Z_hat, radii, vis = rasterize(gaussians, cam)        # [SeaSplat] clean image + depth
        if it > SEATHRU_FROM_ITER:                                  # [SeaSplat] W-2 staged activation
            I_hat = medium.apply(J_hat, Z_hat)                      # [SeaSplat] I = J·e^(−β^D·Z) + B^∞(1−e^(−β^B·Z))
        else:
            I_hat = J_hat                                           # [SeaSplat] medium inactive before 10k

        # ── Loss — IDENTICAL in all 8 configurations (§4) ─────────────────────
        loss = (  L_GS(I_hat, cam.gt)                               # [SeaSplat]
                + 1.0  * L_bs(detach(cam.gt - B_hat))               # [SeaSplat] W-1 detachment
                + 0.1  * L_gw(J_hat)     if it > SEATHRU_FROM_ITER else 0
                + 2.0  * L_sat(J_hat)                               # [SeaSplat] W-4 range anchor
                + 0.01 * L_op(gaussians.get_opacity)                # [SeaSplat] drives α→0 for backscatter-only
                + 2.0  * L_Zsmooth(Z_hat)                           # [SeaSplat]
                + 1.0  * L_Zrecon(detach(Z_hat)))                   # [SeaSplat] W-1 detachment
        loss.backward()                                             # [SeaSplat]

        # ── Insertion 2a: densification, gated by A1 ──────────────────────────
        if not use_dense_init and it < DENSIFY_UNTIL_ITER:          # [A1] one-line gate, it < 15_000
            gaussians.add_densification_stats(vis, radii)           # [SeaSplat]
            if it % DENSIFICATION_INTERVAL == 0 and it > DENSIFY_FROM_ITER:
                gaussians.densify_and_prune(τ_grad, 0.005, extent)  # [SeaSplat] ← densify AND α<0.005 prune
            if it % OPACITY_RESET_INTERVAL == 0:
                gaussians.reset_opacity()                           # [SeaSplat] every 3_000

        # ⚠️ The α-prune and opacity reset sit INSIDE the A1 gate. Setting
        #    use_dense_init=True disables all three at once, leaving L_op with
        #    no executor. This is delta D-14 and the Panama failure mechanism.
        #
        # [proposed] NOT IMPLEMENTED — restore opacity hygiene independent of densification:
        # if it < DENSIFY_UNTIL_ITER and it % DENSIFICATION_INTERVAL == 0:
        #     gaussians.prune_points(gaussians.get_opacity.squeeze(-1) < 0.005)
        # [proposed] port EDGS's counterweights (D-15, D-16):
        # if use_dense_init and it % 10 == 0 and it < DENSIFY_UNTIL_ITER:
        #     gaussians._opacity.data += log(0.99)                  # reduce_opacity
        # gaussians.update_learning_rate(max(it, 8000))             # max_lr clamp

        # ── Insertion 2b: spatial reorganization ──────────────────────────────
        # [integration] Placed as a SIBLING of the densification block and gated on
        #   it > DENSIFY_UNTIL_ITER so the two can never overlap, and on
        #   it > SEATHRU_FROM_ITER (implied: 15_500 > 10_000) so importance is scored
        #   on a population already co-adapted with the medium model. Both orderings
        #   are load-bearing — see the note below.
        if use_spatial_pruning and it > DENSIFY_UNTIL_ITER and it % 500 == 0:   # [A2]
            n = gaussians.count
            if n > max_gaussians:                                   # [A2] no-op when under budget
                phi = gaussians.get_opacity.squeeze(-1) * reduce_scale(   # [A2] Φ = α · ρ(s)
                    gaussians.get_scaling, imp_metric)
                order = argsort(phi)                                # [A2] ASCENDING — lowest first
                gaussians.prune_points(bottom_k_mask(order, n - max_gaussians))
                # [proposed] Mini-Splatting §4.2 argues for stochastic sampling here:
                # keep = multinomial(phi, max_gaussians, replacement=False)

        # ── Optimizer step ────────────────────────────────────────────────────
        for opt in optimizers:                                      # [SeaSplat]
            opt.step(); opt.zero_grad()

    return gaussians, medium                                        # medium saved as separate .pth
```

### Why the two A2 gates are load-bearing `[integration]`

| Gate | If removed |
|---|---|
| `it > DENSIFY_UNTIL_ITER` | A2 and densification would interleave — densification adds primitives that A2 immediately removes, wasting the optimizer state rebuild and thrashing the population. |
| implied `it > SEATHRU_FROM_ITER` | Importance would be scored on opacities `L_op` had not yet shaped. The medium-aware pruning effect (§1.3a) — the thesis's strongest measured result — **depends on this ordering** and would silently disappear. |

The second is currently satisfied only *incidentally*, because `15 500 > 10 000` given the
default schedule. **It should be asserted explicitly**, since raising `seathru_from_iter` above
15 000 would invert the ordering with no warning.

---

## 7.3 Stage 2 — Offline attribute quantization `[A3]`

```python
def quantize_model(                                                 # [A3]
    ply_path: Path,
    k: int = 256,
    group_size: int = 4,
    quantize_xyz: bool = False,
) -> tuple[Path, Path]:
    attrs = load_ply_attributes(ply_path)                           # [A3] 17 float32/primitive

    to_quantize = ["f_dc", "f_rest", "opacity", "scale", "rotation"]  # [A3]
    #                                 ^^^^^^^ ⚠️ CompGS excludes opacity (D-27)
    if quantize_xyz:
        to_quantize.insert(0, "xyz")                                # [A3] default False ✅ matches CompGS

    codebooks, indices, recon = {}, {}, {}
    for name in to_quantize:
        data = attrs[name]                                          # (N, D)
        if data.shape[1] == 0:                                      # [A3] f_rest at sh_degree=0
            continue
        for g in range(ceil(data.shape[1] / group_size)):           # [A3] inert at sh_degree=0 (D-31)
            chunk = pad_to(data[:, g*group_size:(g+1)*group_size], group_size)
            km = MiniBatchKMeans(n_clusters=min(k, len(data)),
                                 random_state=42).fit(chunk)        # [A3] seeded ✅
            codebooks[name, g] = km.cluster_centers_
            indices[name, g]   = km.labels_.astype(uint16)          # ⚠️ uint8 suffices (D-33)
            recon[name]        = km.cluster_centers_[km.labels_]

    # [integration] Two artifacts, deliberately: the NPZ is the deployed footprint
    #   (the thesis DEFINES model size as this archive — D-34); the reconstructed PLY
    #   lets render_uw.py evaluate through the full underwater path with the medium
    #   .pth files intact, so quantization damage is measured in situ.
    save_npz(out_npz, codebooks, indices, xyz=attrs["xyz"])          # [A3] xyz float32, protected
    save_ply(out_ply, recon | {"xyz": attrs["xyz"]})                 # [A3]
    # backscatter.pth / attenuate.pth are NEVER touched                [A3] ✅ verified (W-3)
    return out_npz, out_ply
```

---

## 7.4 Composition driver — order is explicit `[integration]`

```python
def run_configuration(scene: Scene, cfg: AblationConfig) -> Results:
    # ORDER IS FIXED AND JUSTIFIED — see the note below.
    dense = build_dense_cloud(scene.path) if cfg.use_dense_init else None    # [A1] stage 0

    gaussians, medium = train(                                              # stages 1 + 2
        scene,
        use_dense_init=cfg.use_dense_init,
        use_spatial_pruning=cfg.use_spatial_pruning,
        dense_cloud=dense,
    )
    ply = save_ply(gaussians)

    if cfg.use_quantization:                                                # [A3] stage 3
        npz, ply = quantize_model(ply)                                      # AFTER all pruning
        model_size = size_of(npz)                                           # [D-34] archive = deployed size
    else:
        model_size = size_of(ply)

    return evaluate(ply, medium, scene.test_views)   # identical harness for all 8 configs
```

### Order-sensitivity, stated once

| Pair | Order | Why it must be this way |
|---|---|---|
| **A1 → A2** | init, then prune | A2 needs a converged, medium-adapted population to score. Reversed is meaningless (nothing exists to prune before initialization). |
| **A2 → A3** | 🔴 **prune, then quantize** | If quantization came first, A2's pruning would invalidate the codebook: centroids would describe a distribution that no longer exists, and per-primitive index vectors would go stale. **Currently safe by construction** because A3 is offline — the codebook cannot be fit before training ends. ⚠️ Making A3 quantization-aware would *create* this conflict and would require `prune_points` to index-select the assignment vector, plus an assignment refresh after every prune (A2 prunes every 500; CompGS refreshes every 100). |
| **A1 → A3** | init, then quantize | Trivially ordered, but the *content* matters: A1 determines the opacity distribution the codebook is fit over. With A1's α-prune disabled, that distribution carries a large `L_op`-suppressed mass — the A5 compounding risk (§5.3). |

The order A1 → A2 → A3 is stated as intentional in the draft: *"Following deterministic
initialization and spatial reorganization, the Gaussian representation is sufficiently
stabilized to permit parameter reduction"* `[recommended: draft §3.5.4]`, and it agrees with
CompGS's own argument that count reduction should precede quantization because position
dominates the residual afterwards `[paper: compact3d §3]`.

---

## 7.5 What is genuinely new here

Lines tagged `[integration]` are the whole of the original contribution at the code level, and
they amount to four decisions:

1. **The pixel-space DLT re-implementation** — required because EDGS's triangulation lives in
   3DGS NDC space that SeaSplat's COLMAP loader does not expose.
2. **The two A2 gates** (`> densify_until_iter`, implied `> seathru_from_iter`) — which together
   produce the medium-aware pruning effect that is the thesis's best measured result.
3. **A3's two-artifact output** — NPZ as deployed footprint, reconstructed PLY so that
   evaluation runs through the underwater path with the medium model intact.
4. **The composition order**, justified rather than incidental.

Everything else is borrowed. Stating this plainly is stronger than implying a larger algorithmic
contribution, because items 2 and 3 are genuinely non-obvious and are the ones the measurements
support.
