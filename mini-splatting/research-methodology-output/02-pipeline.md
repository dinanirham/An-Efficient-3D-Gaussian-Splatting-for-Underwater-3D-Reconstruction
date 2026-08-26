# §2 — Pipeline flowcharts

`[R:file:line]` = `[repo: file:line]`; `[P §x]` = `[paper §x]`. Line numbers refer to `ms/`.

---

## Stage A — Data → preprocessing → init

```mermaid
flowchart LR
    IMG["Mip-NeRF 360 / Tanks&amp;Temples / Deep Blending<br/><i>[P §6]</i>"]
    RES["resolution: -i images_4 (outdoor)<br/>-i images_2 (indoor)<br/>default for T&amp;T / DB<br/><i>[R:README.md]</i>"]
    COL["COLMAP sparse points + poses"]
    SPLIT["--eval → llffhold = 8<br/>test = idx %% 8 == 0<br/><i>[R:scene/dataset_readers.py:148-153]</i>"]
    G0["GaussianModel(sh_degree = <b>0</b>)<br/>← hard-coded, ignores --sh_degree<br/><i>[R:ms/train.py:56]</i>"]
    INIT["μ ← COLMAP points<br/>s ← log√(kNN dist), q ← identity<br/>o ← inverse_sigmoid(0.1)"]

    IMG --> RES --> COL --> SPLIT --> G0 --> INIT
```

> `sh_degree=0` at init is **not** the config default (`ModelParams.sh_degree = 3`
> `[R:arguments/__init__.py:49]`). The constructor argument is hard-coded, and the model's
> `max_sh_degree` is only raised to `dataset.sh_degree` at 15 K `[R:ms/train.py:250]`.

---

## Stage B — Phase 1: densification (iterations 1 → 15 000)

```mermaid
flowchart TD
    IT(["iteration i"]) --> LR["update_learning_rate(i)<br/><i>[R:ms/train.py:96-97]</i>"]
    LR --> REN["render_imp() → image, radii,<br/><b>area_max</b> (max-contribution area S_i)<br/><i>[R:gaussian_renderer/__init__.py:173,191]</i>"]
    REN --> LOSS["L = 0.8·L₁ + 0.2·(1-SSIM)<br/>UNCHANGED from 3DGS<br/><i>[R:ms/train.py:122]</i>"]
    LOSS --> BW["loss.backward()"]

    BW --> BLUR["<b>BLUR SPLIT accumulator</b><br/>mask_blur |= (area_max &gt; H·W/5000)<br/>⇒ θ_blur = 2×10⁻⁴ ✓<br/><i>[P Eq.2]</i> <i>[R:ms/train.py:151]</i>"]

    BLUR --> C1{"i &gt; 500 AND i %% 100 == 0<br/>AND i %% 5000 ≠ 0<br/>AND N &lt; num_max (4.5M)"}
    C1 -- yes --> DP["densify_and_prune_split():<br/>• clone (grad ≥ 2e-4, small)<br/>• split (grad ≥ 2e-4, large) <b>OR mask_blur</b><br/>• prune (o &lt; 0.005, radii &gt; 20, scale &gt; 0.1·extent)<br/>then mask_blur ← 0<br/><i>[R:scene/gaussian_model.py:412-457]</i>"]
    C1 -- no --> C2

    DP --> C2{"i %% 5000 == 0"}
    C2 -- yes --> DR["<b>DEPTH REINITIALIZATION</b> (see Stage C)"]
    C2 -- no --> STEP

    DR --> STEP["optimizer.step(); zero_grad()<br/><i>[R:ms/train.py:291-293]</i>"]
    STEP --> NEXT([i+1])
```

> **⚠ There is no `reset_opacity()` anywhere in `ms/train.py` or `ms_d/train.py`.**
> `grep -c reset_opacity` returns **0** for both, and **1** for `gs/train.py` (the vanilla
> baseline in the same repo). 3DGS's periodic opacity reset — its main floater-suppression
> device — has been removed, and the paper never says so. `opacity_reset_interval` survives
> only as a magic number in `size_threshold = 20 if i > opacity_reset_interval else None`
> `[R:ms/train.py:155]`. See D-1.

---

## Stage C — Depth reinitialization (every 5 000 iterations)

```mermaid
flowchart TD
    subgraph PERVIEW["for every training view (all of them, not a batch)"]
        RD["render_depth(view)<br/>forked rasterizer<br/><i>[R:ms/train.py:172]</i>"]
        OP["out_pts — per-pixel 3D point from the<br/>ray/ellipsoid <b>mid-point</b> of the argmax Gaussian<br/><i>[P §4.1, Appendix D / Eq.7]</i>"]
        AA["accum_alpha — accumulated opacity"]
        PR["prob ∝ (1 − accum_alpha), normalised<br/><i>[R:ms/train.py:177-180]</i><br/>⚠ paper says 'randomly select'"]
        NS["num_sampled = N_pix / (H·W·|views| / num_depth)<br/>num_depth = 3.5M total<br/><i>[R:ms/train.py:183-187]</i>"]
        CH["np.random.choice(p = prob, replace = False)<br/><i>[R:ms/train.py:189-190]</i>"]
        KEEP["keep out_pts[idx] + GT colour[idx]<br/><i>[R:ms/train.py:192-196]</i>"]
        RD --> OP & AA
        AA --> PR --> CH
        NS --> CH
        OP --> KEEP
        CH --> KEEP
    end

    MERGE["concat over all views ⇒ ≈3.5M points<br/><i>[R:ms/train.py:200-201]</i>"]
    REINIT["<b>reinitial_pts(pts, rgb)</b> — HARD RESET:<br/>μ ← pts, f_dc ← RGB2SH(GT colour)<br/>f_rest ← <b>0</b>, s ← log√(kNN), q ← identity,<br/>o ← inverse_sigmoid(0.1)<br/><i>[R:scene/gaussian_model.py:460-483]</i>"]
    OPT["training_setup(opt) ⇒ <b>Adam state discarded</b><br/><i>[R:ms/train.py:204]</i>"]
    CLR["mask_blur ← 0; empty_cache(); refill viewpoint_stack<br/><i>[R:ms/train.py:205-207]</i>"]

    PERVIEW --> MERGE --> REINIT --> OPT --> CLR
```

> **Two things the diagram makes plain that the prose hides.**
> (a) `reinitial_pts` discards **every learned attribute except position and colour** —
> scale, rotation, opacity and all higher-order SH are reset to their initialisation values.
> This is a full restart of the representation, three times over (at 5 K and 10 K, since
> 15 K is the densification boundary), not an incremental refinement.
> (b) The pixel sampling is **weighted by `1 − α_accum`**, biasing point selection toward
> *low-opacity, poorly-reconstructed* pixels. `[P §4.1]` says only "we randomly select a
> certain number of points". See D-2.

---

## Stage D — Simplification step 1 (iteration 15 000)

```mermaid
flowchart TD
    ACC["for every training view: render_imp()<br/>accumulate accum_weights, area_proj, area_max<br/><i>[R:ms/train.py:216-223]</i>"]

    M{"--imp_metric<br/>(REQUIRED arg)<br/><i>[R:ms/train.py:409]</i>"}
    OUT["<b>outdoor</b> ⇒ I², paper Eq.12<br/>imp += accum_weights / area_proj,<br/>assigned only where area_max ≠ 0<br/><i>[R:ms/train.py:225-228]</i>"]
    IND["<b>indoor</b> ⇒ I¹, paper §3.2<br/>imp += accum_weights<br/><i>[R:ms/train.py:229-230]</i>"]

    INT["<b>INTERSECTION PRESERVING</b><br/>imp_score[accum_area_max == 0] = 0<br/>⇒ Gaussians never argmax anywhere get P = 0<br/><i>[P Eq.3]</i> <i>[R:ms/train.py:232]</i>"]

    SAMP["<b>IMPORTANCE-WEIGHTED SAMPLING</b><br/>P_i = I_i / ΣI<br/>n = int(N · 0.5 · |{P≠0}|/N)<br/>np.random.choice(p = P, replace = False)<br/><i>[P §4.2]</i> <i>[R:ms/train.py:233-244]</i>"]

    PRUNE["prune_points(¬mask)<br/><i>[R:ms/train.py:248]</i>"]
    SH["max_sh_degree ← dataset.sh_degree (3)<br/><i>[R:ms/train.py:250]</i>"]
    RE2["<b>reinitial_pts(own μ, own colour)</b><br/>⇒ s, q, o, f_rest RESET again<br/><i>[R:ms/train.py:251-252]</i>"]
    LR2["LR schedule REWOUND to step 5000<br/>update_learning_rate(i − 15000 + 5000)<br/><i>[R:ms/train.py:98-99]</i>"]
    SHUP["thereafter: oneupSHdegree() every 1000 it<br/><i>[R:ms/train.py:102-103]</i>"]

    ACC --> M
    M --> OUT --> INT
    M --> IND --> INT
    INT --> SAMP --> PRUNE --> SH --> RE2 --> LR2 --> SHUP
```

> **Intersection preserving is not a separate pass in the code** — `[P Alg. 1]` lists
> `Intersection()` and `Sampling()` as two calls, but the implementation folds Eq. 3 into a
> single line, `imp_score[accum_area_max==0] = 0` `[R:ms/train.py:232]`, which zeroes the
> sampling probability of any Gaussian that is never the argmax contributor in any view.
> Mathematically equivalent to Eq. 3; structurally invisible if you go looking for a
> function named after it.

---

## Stage E — Simplification step 2 (iteration 20 000) and the tail

```mermaid
flowchart LR
    ACC2["recompute imp_score over all views<br/>(same metric as Stage D)<br/><i>[R:ms/train.py:261-281]</i>"]
    CDF["<b>init_cdf_mask(imp, thres = 0.99)</b><br/>sort ascending, cumsum,<br/>drop the Gaussians forming the<br/>bottom 1%% of TOTAL importance mass<br/><i>[R:ms/train.py:31-44, 282]</i>"]
    PR2["prune_points(¬mask); training_setup(opt)<br/>⇒ Adam state discarded again<br/><i>[R:ms/train.py:284-285]</i>"]
    TAIL["20 000 → 30 000: plain 3DGS optimization<br/>SH degree ramping, no further structural change"]
    OUT2["output: a standard 3DGS .ply,<br/>≈0.2–0.5 M Gaussians"]

    ACC2 --> CDF --> PR2 --> TAIL --> OUT2
```

> `[P Alg. 1:21]` calls this step only "`Pruning()` ▷ Directly Prune a Few Gaussians".
> The threshold **0.99** and the CDF-over-importance-mass formulation appear nowhere in the
> paper. Note this is a *deterministic* prune — the paper's own §4.2 argument against
> deterministic pruning applies to large ratios, and 1% is small, so there is no
> inconsistency; it just is not documented.

---

## Stage F — Mini-Splatting-C: post-hoc compression

```mermaid
flowchart LR
    M0["trained Mini-Splatting model"]
    VOX["voxelize μ to a 2¹⁶ grid<br/>μ_v = round( (μ−min)/(max−min) · (2¹⁶−1) )<br/><i>[R:ms_c/run.py:135,141-143]</i>"]
    UNIQ["<b>np.unique(μ_v, axis=0)</b><br/>⇒ deduplicates colliding Gaussians<br/>(an extra, undocumented reduction)<br/><i>[R:ms_c/run.py:144]</i>"]
    FEAT["feat = [f_dc, f_rest, s, q, o] concatenated<br/><i>[R:ms_c/run.py:156-163]</i>"]
    RAHT["RAHT / Haar3D transform, depth = 16<br/><i>[P App.F, ref [6]]</i> <i>[R:ms_c/run.py:167]</i>"]
    Q["CT_q = round(CT / Qstep), Qstep = 0.02<br/><i>[P App.F]</i> <i>[R:ms_c/run.py:136,169]</i>"]
    ZIP["np.savez_compressed(pos_remain(float32), CT_q, Qstep, depth)<br/><i>[R:ms_c/run.py:173]</i>"]
    DEC["inv_haar3D → render → PSNR/SSIM/LPIPS<br/><i>[R:ms_c/run.py:214, 105-125]</i>"]

    M0 --> VOX --> UNIQ --> FEAT --> RAHT --> Q --> ZIP --> DEC
```

> `depth = 16` and `Qstep = 0.02` match `[paper Appendix F]` exactly. The **`np.unique`
> deduplication** at `[R:ms_c/run.py:144]` does not appear in Appendix F and silently drops
> any Gaussians that land in the same 65 536³ voxel — a second source of size reduction
> attributed to "transform coding + zip".
