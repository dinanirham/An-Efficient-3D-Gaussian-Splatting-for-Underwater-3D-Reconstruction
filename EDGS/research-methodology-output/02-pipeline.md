# §2 — Pipeline flowcharts

`[R:file:line]` = `[repo: file:line]`; `[P §x]` = `[paper §x]` (arXiv:2504.13204v2).
The initialization is the method, so it gets three of the six diagrams.

---

## Stage A — Data → poses → reference-view selection

```mermaid
flowchart LR
    IMG["Mip-NeRF 360 (9 scenes) / Tanks&amp;Temples (2) / Deep Blending (2)<br/><i>[P §4.1]</i>"]
    COL["COLMAP poses<br/><i>[P §1, ref [60]]</i>"]
    SFM["SfM points → initial Gaussians<br/>(N_splats_at_init)"]
    STACK["viewpoint_stack = scene.getTrainCameras()<br/><i>[R:corr_init.py:550]</i>"]
    FLAT["camera matrices flattened: world_view_transform → ℝ¹⁶<br/><i>[R:corr_init.py:553]</i>"]
    KM["<b>select_cameras_kmeans(K = num_refs = 180)</b><br/>k-means over pose vectors, keep the member<br/>nearest each cluster centre<br/><i>[R:corr_init.py:65-97, 555]</i><br/>⚠ paper §3.2 describes only 'maximal overlap'"]
    NN["<b>k_closest_vectors(k = nns_per_ref = 3)</b><br/>Frobenius distance between pose matrices<br/><i>[P §3.2]</i> <i>[R:corr_init.py:41, 561]</i>"]

    IMG --> COL --> SFM
    COL --> STACK --> FLAT --> KM
    FLAT --> NN
```

> The paper says reference neighbours are found "based on camera parameters and spatial
> proximity. We measure proximity between camera matrices using the Frobenius norm"
> `[P §3.2]` — that describes `k_closest_vectors` ✅. But the **selection of the reference
> views themselves is K-means over pose vectors** `[R:corr_init.py:555]`, which the paper
> does not mention. See D-5.

---

## Stage B — Dense matching (RoMa) → triangulation

```mermaid
flowchart TD
    RM["<b>RoMa</b> — roma_outdoor() / roma_indoor()<br/>upsample_preds = False, symmetric = False<br/><i>[P §3.2, ref [13]]</i> <i>[R:corr_init.py:533-539]</i>"]
    PAIR["for each reference I_i, for each of its 3 NNs I_j"]
    WARP["M(I_i, I_j) → (W_ij ∈ ℝ^{2×H×W}, c_ij ∈ ℝ^{H×W})<br/><i>[P Eq.3]</i> <i>[R:corr_init.py:100-177]</i>"]
    AGG["aggregate_confidences_and_warps():<br/>per-pixel argmax over the 3 neighbours →<br/>certainties_max, certainties_max_idcs<br/><i>[R:corr_init.py:208]</i>"]
    SAMP["roma_model.sample(...) → M = matches_per_ref = 15 000<br/>(README example: 20 000)<br/><i>[R:configs/train.yaml; README.md]</i>"]
    KPT["extract_keypoints_and_colors():<br/>normalized [−1,1] → pixel coords;<br/>read RGB at the reference pixel<br/><i>[R:corr_init.py:291-397, 869]</i>"]

    TRI["<b>triangulate_points()</b><br/>build A g = −b from the 4 DLT equations<br/><i>[P Eqs.4-6]</i><br/>solve by torch.linalg.lstsq<br/><i>[P Eq.7]</i> <i>[R:corr_init.py:412-490, 471-472]</i>"]
    ERR["reprojection errors ε_i^k, ε_j^k<br/><i>[P Eq.8]</i> <i>[R:corr_init.py returns errors_proj1/2]</i>"]
    BEST["select_best_keypoints(): per correspondence,<br/>keep the neighbour with the lowest max-reproj-error<br/><i>[R:corr_init.py:492-519, 647]</i>"]

    RM --> PAIR --> WARP --> AGG --> SAMP --> KPT --> TRI --> ERR --> BEST
```

---

## Stage C — Gaussian seeding (where the paper and the code diverge most)

```mermaid
flowchart TD
    PTS["surviving triangulated points, per reference view"]

    XYZ["μ ← triangulated 3D point<br/><i>[P Eq.7]</i> <i>[R:corr_init.py:657]</i>"]
    DC["f_dc ← RGB2SH( reference-image pixel colour / 255 )<br/><i>[P §3.5]</i> <i>[R:corr_init.py:658]</i>"]
    REST["f_rest ← <b>0</b><br/>⚠⚠ §3.5 / Eqs.12-13 (least-squares SH fit,<br/>Moore–Penrose pseudoinverse) is <b>NOT IMPLEMENTED</b><br/><i>[R:corr_init.py:659, 871]</i>"]
    OP["opacity logit ← 0  (⇒ α = 0.5)<br/><b>minus 10 if reproj-error &gt; proj_err_tolerance</b><br/>(⇒ α ≈ 4.5e-5, effectively invisible)<br/><i>[R:corr_init.py:660-666]</i>"]
    SC["scale ← inv_act( ‖μ − campos_i‖ · scaling_factor )<br/>scaling_factor = 0.001, isotropic<br/><i>[R:corr_init.py:668-670]</i>"]
    ROT["rotation ← copy of gaussians._rotation[−1]<br/><i>[R:corr_init.py:671]</i>"]

    POST["densification_postfix(...) — append all new Gaussians<br/><i>[R:corr_init.py:678-686]</i>"]
    DROP["<b>prune the original SfM points</b><br/>(unless add_SfM_init, default False)<br/><i>[R:trainer.py:243-251]</i>"]
    HALF["<b>ALL scalings × 0.5</b><br/><i>[R:trainer.py:252-254]</i>"]

    PTS --> XYZ & DC & REST & OP & SC & ROT
    XYZ --> POST
    DC --> POST
    REST --> POST
    OP --> POST
    SC --> POST
    ROT --> POST
    POST --> DROP --> HALF
```

> **Three undocumented mechanics live in this stage:**
> **(a)** `f_rest ← 0` — the entire §3.5 SH-fitting contribution is missing from the code
> (D-1). **(b)** `p^proj` is realised as an **opacity penalty**, not a sampling
> distribution — bad points are *kept but made invisible*, with the source comment
> *"new version that sets points with large error invisible // TODO: remove those points
> instead"* `[R:corr_init.py:660-661]` (D-2). **(c)** every scale is halved right after
> initialization `[R:trainer.py:254]` (D-6).

---

## Stage D — Loss composition

```mermaid
flowchart LR
    I["rendered image"]
    GT["ground truth"]
    L1["L₁"]
    SS["1 − SSIM"]
    L["<b>L = 0.8·L₁ + 0.2·(1 − SSIM)</b><br/>λ_dssim = 0.2 — STOCK 3DGS, UNCHANGED<br/><i>[R:trainer.py:163-167; configs/gs/base.yaml]</i>"]

    I --> L1 --> L
    GT --> L1
    I --> SS --> L
    GT --> SS
```

> **That is the entire objective.** No regulariser, no auxiliary term, no correspondence
> loss. The paper writes no loss equation at all beyond "Gaussians `G` are optimized with
> photometric loss" `[P §3.1]`. Same situation as `mini-splatting/`, and the same
> methodological virtue: **every reported gain is attributable to the initialization
> alone.**

---

## Stage E — Optimization (stock 3DGS, plus two undocumented tweaks)

```mermaid
flowchart TD
    IT(["step i, 1 → gs_epochs (README: 30 000)"])
    LR["update_learning_rate( <b>max(i, 8000)</b> )<br/>if max_lr (default True)<br/><i>[R:trainer.py:146-147]</i><br/>⚠ position LR is CLAMPED to its step-8000 value —<br/>never uses 3DGS's high early LR"]
    SH["oneupSHdegree() every 1000 steps<br/><i>[R:trainer.py:151-152]</i>"]
    CAM["pop one random camera (no replacement)<br/><i>[R:trainer.py:155-157]</i><br/>⚠ configs batch_size = 64 is UNUSED"]
    FW["render → loss → backward → optimizer.step()<br/><i>[R:trainer.py:159-190]</i>"]

    ND{"train.no_densify?<br/>config default False,<br/>README says 'True by default',<br/>README command passes True<br/><i>[R:configs/train.yaml vs README.md]</i>"}
    PR["<b>prune only</b>: drop α &lt; 0.005<br/>while i &lt; densify_until_iter<br/><i>[R:trainer.py:258-264]</i>"]
    DP["densify_and_prune() — full 3DGS ADC<br/><i>[R:trainer.py:193-205]</i>"]

    RO{"train.reduce_opacity?<br/>default <b>True</b>"}
    DEC["<b>every 10 steps (while i &lt; 15 000):</b><br/>opacity_logit ← log( exp(opacity_logit) · 0.99 )<br/>= logit − 0.01005<br/><i>[R:trainer.py:81-85]</i><br/>⚠ NOT IN THE PAPER"]

    IT --> LR --> SH --> CAM --> FW --> ND
    ND -- True --> PR
    ND -- False --> DP
    PR --> RO
    DP --> RO
    RO -- yes --> DEC --> NEXT([i+1])
    RO -- no --> NEXT
```

> **`reduce_opacity` replaces 3DGS's periodic opacity reset with a continuous decay.**
> `opacity_reset_interval` is set to `30000` = `iterations` `[R:configs/gs/base.yaml]`, and
> the reset is additionally gated by `gs_step < densify_until_iter = 15000`
> `[R:trainer.py:195-205]`, so **`reset_opacity()` never fires**. Instead the logit is
> reduced by `log(0.99) ≈ −0.01005` every 10 steps for the first 15 000 steps — about
> **1500 applications**, a cumulative logit shift of ≈ **−15**. Paired with the
> `α < 0.005` prune at `[R:trainer.py:261]`, this is an aggressive, continuous
> *decay-and-cull* that steadily removes Gaussians the photometric loss does not defend.
> Neither mechanism appears in the paper. See D-3.

---

## Stage F — Evaluation

```mermaid
flowchart LR
    M["trained model"]
    EV["evaluate() — in-memory float tensors,<br/>clamped to [0,1]<br/><i>[R:trainer.py:104-142]</i>"]
    P["PSNR = mean of PER-CHANNEL PSNRs<br/><i>[R:source/losses.py:63-76]</i>"]
    S["SSIM (3DGS implementation)"]
    LP["LPIPS — VGG<br/><i>[R:trainer.py:53]</i>"]
    WB["Weights &amp; Biases<br/>(config default mode = 'online')<br/><i>[R:configs/train.yaml]</i>"]

    M --> EV --> P & S & LP --> WB
```

> **No disk round-trip** — metrics are computed on the in-memory float tensors
> `[R:trainer.py:120-125]`, the same clean path as `mini-splatting/`'s main variant and
> **unlike** `seasplat/`, `CompGS/` and `ms_c/`. But the PSNR *formula* is the 3DGS
> per-channel-mean one `[R:losses.py:75-76]`, **not** the pooled-MSE definition used by
> `seathru_NeRF/` and `CompGS/`. See [`10-reproducibility.md`](10-reproducibility.md).
