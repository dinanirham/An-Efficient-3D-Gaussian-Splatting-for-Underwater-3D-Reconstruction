# §2 — Pipeline flowcharts

Split by stage. `[R:file:line]` abbreviates `[repo: file:line]`; `[P §x]` abbreviates `[paper §x]`.

---

## Stage A — Data → preprocessing

```mermaid
flowchart LR
    RAW["RAW frames, Nikon D850 SLR<br/>Nauticam housing + dome port<br/>20 / 20 / 18 imgs<br/>Red Sea, Curaçao, Panama<br/><i>[P §5.1]</i>"]
    WB["white-balance, 0.5%% clipping per channel<br/>(removes extreme noisy pixels)<br/><i>[P §5.1]</i>"]
    DS["downsample → ≈900×1400<br/><i>[P §5.1]</i>"]
    CM["COLMAP poses<br/><i>[P §5.1]</i> <i>[R:internal/pycolmap/]</i>"]
    NDC["forward-facing + NDC<br/>near=0, far=1<br/><i>[R:configs/llff_256_uw.gin:2-5]</i>"]
    SPLIT["llffhold = 8<br/>test = idx %% 8 == 0<br/><i>[R:internal/datasets.py:717-719]</i>"]
    T["train: 17 / 17 / 15"]
    V["val: 3 / 3 / 3<br/><i>[P §5.1: 'three are set aside for validation']</i>"]

    RAW --> WB --> DS --> CM --> NDC --> SPLIT
    SPLIT --> T
    SPLIT --> V
```

> **The split checks out arithmetically:** `20 // 8 → indices {0,8,16}` = 3 held-out;
> `18 // 8 → {0,8,16}` = 3. Paper and code agree exactly. `[inferred: paper §5.1 vs repo datasets.py:717-719]`
> Contrast with SeaSplat, where `--eval` defaults off and the split is undocumented.

---

## Stage B — Model initialisation / architecture

```mermaid
flowchart TD
    subgraph L0["Level 0 — proposal (mip-NeRF 360, unchanged)"]
        PM["PropMLP<br/>net_depth 4 × width 256<br/>disable_rgb = True<br/>128 samples<br/><i>[R:configs/llff_256_uw.gin]</i>"]
    end

    subgraph L1["Level 1 — SeaThru-NeRF UWMLP (32 samples)"]
        direction TB
        POS["IPE(mean, cov)<br/>max_deg_point 16<br/>octahedron basis<br/><i>[R:models.py:774-777]</i>"]
        TRUNK["density trunk<br/>8 dense × 256, skip @4<br/><i>[R:models.py:781-786]</i>"]
        SIG["σ^obj = softplus(raw + density_bias)<br/>density_bias = 0 in gin<br/><i>[R:models.py:836]</i>"]
        BOT["bottleneck, width 256"]
        COBJ["c^obj = sigmoid(Dense₃(x))<br/><i>[R:models.py:921-925]</i>"]

        POS --> TRUNK --> SIG
        TRUNK --> BOT --> COBJ
    end

    subgraph MED["mediumMLP — once per RAY, viewdir only"]
        DENC["dir_enc = pos_enc(viewdirs, deg_view = 4)<br/><i>[R:models.py:722-724]</i>"]
        WTRUNK["net_depth_water = <b>1</b> dense layer<br/>width = net_width_viewdirs = <b>128</b><br/>softplus activation<br/><i>[R:models.py:716, 678, 865-869]</i><br/>⚠ paper says 6 layers × 256"]
        B1["c^med = sigmoid(Dense₃)<br/><i>[R:models.py:871-873]</i>"]
        B2["σ^bs = softplus(Dense₃ + water_bias)<br/><i>[R:models.py:878-879]</i>"]
        B3["σ^attn = softplus(Dense₃ + water_bias)<br/><i>[R:models.py:889-890]</i>"]
        DENC --> WTRUNK --> B1 & B2 & B3
    end

    L0 -->|"resample<br/>interlevel"| L1
    MED -.->|"per-ray constants<br/>broadcast to all samples"| L1
```

> **`uw_rgb_dir = False`** in the released gin `[R:configs/llff_256_uw.gin]`, and the code
> only appends the direction encoding to the colour branch when that flag is set
> `[R:models.py:898-900]`. So in the released configuration **`c^obj` is a function of
> position only** — view-independent — contradicting `[P §4.3]`. See D-3.

---

## Stage C — Forward pass: the split rendering equations

```mermaid
flowchart LR
    subgraph PERSAMPLE["per sample i along ray r"]
        SIGO["σ^obj_i"]
        CO["c^obj_i"]
    end
    subgraph PERRAY["per ray r (broadcast)"]
        SB["σ^bs ∈ ℝ³"]
        SA["σ^attn ∈ ℝ³"]
        CM["c^med ∈ ℝ³"]
    end

    D["δ_i = (t_{i+1} - t_i)·‖d‖"]
    DBS["δ^bs_i = <b>stop_grad</b>(t_{i+1}-t_i)·‖d‖<br/><i>[R:render.py:179]</i>"]

    TOBJ["T^obj_i = exp(-Σ_{j&lt;i} σ^obj_j δ_j)<br/><i>[P Eq.22]</i> <i>[R:render.py:214-219]</i>"]
    WOBJ["w^obj_i = T^obj_i·(1-e^{-σ^obj_i δ_i})<br/><i>[P Eq.23]</i> <i>[R:render.py:220]</i>"]
    TATT["A_i = exp(-Σ_{j&lt;i} σ^attn δ^bs_j)<br/><i>[R:render.py:205-210]</i>"]
    ABS["α^bs_i = 1-e^{-σ^bs δ^bs_i}<br/>T^bs_i = exp(-Σ_{j&lt;i} σ^bs δ^bs_j)<br/><i>[R:render.py:184-192]</i>"]

    DIRECT["Ĉ^obj = Σ_i w^obj_i · A_i · c^obj_i<br/><i>[P Eq.20]</i> <i>[R:render.py:320]</i>"]
    BS["Ĉ^med = Σ_i T^obj_i · α^bs_i T^bs_i · c^med<br/><i>[P Eq.21]</i> <i>[R:render.py:324]</i>"]
    OUT["Ĉ(r) = Ĉ^obj + Ĉ^med<br/><i>[P Eq.12]</i> <i>[R:render.py:326]</i>"]
    J["J = <b>stop_grad</b>(Σ_i w^obj_i c^obj_i)<br/>= the RESTORED image<br/><i>[R:render.py:319]</i>"]

    SIGO --> TOBJ --> WOBJ
    D --> TOBJ
    DBS --> TATT
    DBS --> ABS
    SA --> TATT
    SB --> ABS
    WOBJ --> DIRECT
    TATT --> DIRECT
    CO --> DIRECT
    TOBJ --> BS
    ABS --> BS
    CM --> BS
    DIRECT --> OUT
    BS --> OUT
    WOBJ --> J
    CO --> J
```

Two detachments are visible here and both are load-bearing:

| Detach | Line | Why it matters |
|---|---|---|
| `δ^bs = stop_gradient(t_delta)·‖d‖` | `[R:render.py:179]` | the medium's transmittances depend on **sample spacing**. Without the stop-gradient, the proposal network could reduce loss by *moving the samples*, i.e. by changing the quadrature rather than the physics. |
| `J = stop_gradient(…)` | `[R:render.py:319]` | the restored image is a **pure diagnostic output**. No gradient flows through it and it appears in no loss. |

---

## Stage D — Loss composition

```mermaid
flowchart TD
    RGB["Ĉ(r)"]
    GT["C*(r) — linear, white-balanced"]
    W["w = {w^obj_i}"]
    TR["T^obj"]
    SD["proposal vs. NeRF weight histograms"]

    REC["L_recon (RawNeRF)<br/>((min(1,Ĉ) - C*) / (1e-3 + sg(min(1,Ĉ))))²<br/>mult = data_loss_mult = 1<br/><i>[P Eq.25]</i> <i>[R:train_utils.py:95-102]</i>"]
    PROP["L_prop (interlevel, mip-NeRF 360)<br/>mult = interlevel_loss_mult = 1<br/><i>[P Eq.24]</i> <i>[R:train_utils.py:115-127]</i>"]
    ACC["λ·L_objnorm on T^obj<br/>−log( <b>6</b>·e^{−|1−T|/0.1} + e^{−|T|/0.1} )<br/>λ = 1e-4<br/><i>[P Eq.26-27]</i> <i>[R:train_utils.py:153-167]</i>"]
    DIST["L_distortion<br/><b>mult = 0 → DISABLED</b><br/><i>[R:configs/llff_256_uw.gin]</i>"]
    SIGM["L_sig_med (std of σ)<br/><b>use_uw_sig_med_loss = False</b><br/>'not in the paper!!'<br/><i>[R:configs.py:174]</i>"]
    WACC["L_objnorm on Σw<br/><b>use_uw_acc_weights_loss = False</b><br/><i>[R:configs/llff_256_uw.gin]</i>"]

    TOTAL["L = L_recon + L_prop + λ·L_objnorm<br/><i>[P Eq.24]</i>"]

    RGB --> REC
    GT --> REC
    SD --> PROP
    TR --> ACC
    W -.->|disabled| WACC

    REC --> TOTAL
    PROP --> TOTAL
    ACC --> TOTAL
    DIST -.->|"×0"| TOTAL
    SIGM -.->|off| TOTAL
    WACC -.->|off| TOTAL
```

> **Only three terms are live.** Unlike SeaSplat's seven-term objective, SeaThru-NeRF's
> deployed loss is exactly the three of Eq. 24, with `distortion_loss_mult = 0` explicitly
> switching off mip-NeRF 360's distortion regulariser
> `[R:configs/llff_256_uw.gin]` — a change from the mip-NeRF 360 baseline that the paper
> does not mention.
>
> **But the Laplacian mixture is asymmetric in code (`factor = 6`) and symmetric in the
> paper (Eq. 26).** See D-2.

---

## Stage E — Optimization

```mermaid
flowchart LR
    B["batch: 16 384 rays<br/><i>[P §4.5]</i> <i>[R:configs/llff_256_uw.gin]</i>"]
    F["forward (2 levels: 128 prop + 32 nerf)"]
    L["L = L_recon + L_prop + λ L_objnorm"]
    G["jax.value_and_grad → pmean across devices<br/><i>[R:train_utils.py:305-307]</i>"]
    CL["clip_gradients: per-MLP clip by value then by norm<br/><i>[R:train_utils.py:190-208]</i>"]
    NAN["tree_map(nan_to_num)<br/><i>[R:train_utils.py:313]</i>"]
    A["Adam, lr 2e-3 → 2e-5, eps 1e-8<br/>250 000 steps<br/><i>[R:configs/llff_256_uw.gin]</i>"]
    SCHED{"step ≥ uw_decay_acc (5000)?<br/><i>[R:train.py:127]</i>"}
    S1["sig_mult = uw_initial_acc_trans_loss_mult = 1e-4"]
    S2["sig_mult = uw_final_acc_trans_loss_mult = 1e-4"]

    B --> F --> L --> G --> CL --> NAN --> A
    SCHED -- no --> S1 --> L
    SCHED -- yes --> S2 --> L
```

> The `uw_decay_acc = 5000` schedule is a **no-op in the released config**: initial and
> final multipliers are both `1e-4` `[R:configs/llff_256_uw.gin]`. The machinery exists for
> a ramp that was not used in the published runs. `[inferred]`
>
> Note `jnp.nan_to_num` on the gradient tree `[R:train_utils.py:313]` — NaN gradients are
> silently zeroed rather than raising. Worth knowing when debugging a reproduction.

---

## Stage F — Outputs

```mermaid
flowchart LR
    M["trained UWMLP + PropMLP"]
    R1["Ĉ — in-medium novel view"]
    R2["J — restored / medium-free (stop-grad output)"]
    R3["bs — backscatter-only image"]
    R4["distance_mean / _median — depth"]
    R5["E_map = E[exp(-σ^attn s)] — attenuation map"]
    R6["c_med, σ^bs, σ^attn — estimated medium params"]

    PF["photofinishing (Karaimer &amp; Brown [18])<br/>VISUALISATION ONLY<br/><i>[P §5.1]</i>"]
    MET["PSNR / SSIM / LPIPS<br/>on <b>linear, non-photofinished</b> images<br/><i>[P §5.1, §4.5]</i>"]

    M --> R1 & R2 & R3 & R4 & R5 & R6
    R1 --> PF
    R1 --> MET
```

> `[P §4.5]`: "The loss function and metrics are calculated on the output before any
> post-processing." `[P §5.1]`: "PSNR is calculated on the original non-photofinished
> linear images." **PSNR on linear HDR-ish data is not numerically comparable to PSNR on
> tone-mapped sRGB data** — a critical caveat when placing this method's numbers beside
> SeaSplat's. See [`10-reproducibility.md`](10-reproducibility.md) §10.3.
