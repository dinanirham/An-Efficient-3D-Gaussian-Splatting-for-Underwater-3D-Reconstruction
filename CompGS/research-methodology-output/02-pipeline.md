# §2 — Pipeline flowcharts

`[R:file:line]` = `[repo: file:line]`; `[P §x]` = `[paper §x]` (**arXiv:2404.09458v1** = `../../CompGS.pdf`).

---

## Stage A — Data → preprocessing → anchor initialisation

```mermaid
flowchart LR
    IMG["Tanks&amp;Temples / Deep Blending / Mip-NeRF 360<br/>3DGS scene selection &amp; protocol<br/><i>[P §4.1]</i>"]
    COL["COLMAP sparse points (provided by 3DGS)<br/><i>[P §3.4, §4.1]</i>"]
    SPLIT["1 view in every 8 held out<br/>eval_interval = 8<br/><i>[P §4.1]</i> <i>[R:Modules/Common/Datasets.py:20,45-46]</i>"]
    VOX["voxel_size = 0.001 (Mip-NeRF360)<br/>or 0.01 (T&amp;T, DB)<br/>voxelize_sample()<br/><i>[R:Configs/*.yaml; Model.py:294]</i>"]
    ANC["N anchor primitives ω<br/>μ_ω ← voxel centres  <b>(FROZEN, lr = 0)</b><br/>s_ω ← log(voxel_size)·1₆<br/>q_ω ← identity<br/>f_ω ← learned, 32-D<br/>g_k ← learned, 8-D × K=10<br/><i>[R:Configs/*.yaml; Parameters.py]</i>"]

    IMG --> SPLIT
    COL --> VOX --> ANC
    SPLIT --> ANC
```

> **`means_lr_init = means_lr_final = means_lr_delay_mult = 0.0`** in all three configs
> `[R:Configs/MipNeRF360.yaml; TanksAndTemplates.yaml; DeepBlending.yaml]`. Anchor
> positions **never move**. This is what makes the lossless integer-grid G-PCC coding at
> `[R:Model.py:313-315]` sound — and it is not stated in the paper.

---

## Stage B — Inter-primitive prediction (one anchor → K = 10 coupled primitives)

```mermaid
flowchart TD
    FW["f_ω ∈ ℝ³² — reference embedding<br/>(one per anchor)"]
    GK["g_k ∈ ℝ⁸ — residual embedding<br/>(K = 10 per anchor)"]
    HK["h_k = f_ω ⊕ g_k ∈ ℝ⁴⁰<br/>channel-wise concat<br/><i>[P §3.2]</i> <i>[R:Prediction.py:46-47]</i>"]

    VD["view feats ∈ ℝ⁴ = [dir(3), dist(1)]<br/>computed from the ANCHOR mean μ_ω,<br/>then broadcast to all K<br/><i>[R:Prediction.py:53-57]</i>"]

    MM["means_pred_mlp: ℝ⁴⁰→ℝ³<br/>ResidualMLP, 1 res layer<br/><i>[R:Prediction.py:24]</i>"]
    CM["covariance_pred_mlp: ℝ⁴⁰→ℝ⁷<br/>ResidualMLP, 1 res layer<br/><i>[R:Prediction.py:25]</i>"]
    OM["opacity_pred_mlp: ℝ⁴⁴→ℝ¹<br/>1 res layer, <b>Tanh</b> tail<br/><i>[R:Prediction.py:28]</i>"]
    CO["color_pred_mlp: ℝ⁴⁴→ℝ³<br/><b>2</b> res layers, Sigmoid tail<br/><i>[R:Prediction.py:29]</i>"]

    MU["μ_k = μ_ω + Δμ_k ⊙ exp(s_ω[0:3])<br/><i>[P Eq.4]</i> <i>[R:Prediction.py:76]</i>"]
    SC["scales_k = σ(out[0:3]) ⊙ exp(s_ω[3:6])<br/><i>[R:Prediction.py:77]</i>"]
    RO["q_k = normalize(out[3:7])<br/><i>[R:Prediction.py:78]</i>"]
    AL["α_k = Tanh(·) ∈ [−1,1]"]
    CL["c_k = Sigmoid(·) ∈ [0,1]"]

    MASK{"α_k &gt; 0 ?<br/><i>[R:Prediction.py:65]</i>"}
    DROP["culled — never rasterized"]
    KEEP["rasterized as a 3D Gaussian"]

    FW --> HK
    GK --> HK
    HK --> MM --> MU
    HK --> CM --> SC
    CM --> RO
    HK --> OM --> AL
    HK --> CO --> CL
    VD --> OM
    VD --> CO
    AL --> MASK
    MASK -- no --> DROP
    MASK -- yes --> KEEP
    MU --> KEEP
    SC --> KEEP
    RO --> KEEP
    CL --> KEEP
```

> **This is Scaffold-GS offset prediction, not the affine transform of `[P Eqs. 2-4]`.**
> The paper describes **three** networks `{𝒯, 𝒮, ℛ}` producing a translation vector,
> a scaling matrix and a rotation matrix `[P Eq. 3]`. The repo has **two** geometry MLPs;
> scale and rotation come from a single 7-channel head (3 scales + 4 quaternion), and both
> the offset and the scale are modulated by the **anchor's own** 6-D scaling vector, which
> Eq. 4 does not mention. See D-1.
>
> Also note `[P Eq. 4]` writes `Σ_k = S_k R_k`, which is not a valid covariance
> factorisation (it should be `R S Sᵀ Rᵀ`); the repo stores scale and quaternion separately
> and lets the rasterizer build `Σ`. Treat Eq. 4 as loose notation.

---

## Stage C — Entropy estimation (the rate model)

```mermaid
flowchart TD
    subgraph REF["Reference embeddings f_ω — Ballé hyperprior"]
        Z1["z_f = h_a(f_ω), hyperprior, dim 4<br/><i>[P Eq.8]</i> <i>[R:EntropyModel.py:13-104]</i>"]
        FB1["factorized entropy bottleneck<br/>→ p(z_f), rate R_z<br/><i>[P Eq.9]</i> <i>[ref [1]]</i>"]
        GC1["p(f̃_ω) = N(μ_f, σ_f), (μ_f,σ_f) = E_f(z_f)<br/><i>[P Eq.8]</i>"]
    end

    subgraph SIG["Anchor scaling vector Σ_ω — conditioned on f̃_ω"]
        GC2["p(Σ̃_ω) = N(μ_Σ, σ_Σ), (μ_Σ,σ_Σ) = E_Σ(f̃_ω)<br/><i>[P Eq.10]</i> <i>[R:EntropyModel.py:219-250]</i>"]
        QS["quant_step s_Σ: <b>learnable, per-dim (6), init 0.01</b><br/><i>[P §3.4]</i> <i>[R:EntropyModel.py:220,228]</i>"]
    end

    subgraph RES["Residual embeddings g_k — conditioned on f̃_ω ⊕ z_g"]
        Z2["z_g hyperprior, dim 1<br/><i>[R:Configs/*.yaml res_hyper_dim: 1]</i>"]
        FB2["factorized bottleneck → p(z_g)<br/><i>[P Eq.12]</i>"]
        GC3["p(g̃_k) = N(μ_g, σ_g), (μ_g,σ_g) = E_g(f̃_ω ⊕ z_g)<br/><i>[P Eq.11]</i> <i>[R:EntropyModel.py:106-217]</i>"]
    end

    RATE["R_ω,γ = R_f + R_Σ + Σ_k R_gk<br/><i>[P Eq.13]</i>"]
    NOISE["training: additive U(−½,½) quantization noise<br/>(differentiable surrogate for rounding)<br/><i>[P Eqs.6-7]</i>"]

    Z1 --> FB1 --> GC1
    GC1 --> GC2
    QS --> GC2
    GC1 --> GC3
    Z2 --> FB2 --> GC3
    GC1 --> RATE
    GC2 --> RATE
    GC3 --> RATE
    NOISE -.-> GC1 & GC2 & GC3
```

> `f̃_ω` is used as the **context** for both `Σ_ω` and `g_k` — a one-level spatial context
> model, exactly the Ballé-2018 hyperprior pattern. Quantization steps: `s_f = s_g = 1`
> (fixed) and `s_Σ` **learnable, init 0.01** `[P §3.4]` — the repo matches, but makes
> `s_Σ` a **6-vector** (one per scale dimension) rather than a scalar
> `[R:EntropyModel.py:228]`.

---

## Stage D — Loss composition

```mermaid
flowchart TD
    IMG["rendered image Î"]
    GT["ground truth I"]

    L1["L₁(Î, I)"]
    SS["1 − MS-SSIM_pkg(Î, I), data_range = 1<br/><i>[R:TrainerCompGS.py:216]</i>"]
    D["<b>D</b> = 0.8·L₁ + 0.2·SSIM<br/><i>[P §3.3 'rendering loss [17]']</i> <i>[R:TrainerCompGS.py:217]</i>"]

    REG["<b>REG</b> = 0.01 · mean(∏ scales_k)<br/>⚠ ABSENT FROM THE PAPER<br/>(Scaffold-GS volume regulariser)<br/><i>[R:TrainerCompGS.py:220]</i>"]

    BPP["bpp dict from entropy model"]
    R["<b>λ·R</b>, λ = lambda_weight ∈ {0.001, 0.005, 0.01}<br/>gated: iter &gt; rate_loss_start_iteration = 3000<br/><i>[P Eq.1]</i> <i>[R:TrainerCompGS.py:224,229]</i>"]

    TOT["L = D + REG + λR<br/>(paper: L = λR + D)"]
    AUX["aux_loss — entropy-bottleneck CDF fitting<br/>SEPARATE optimizer, separate backward<br/>⚠ absent from the paper<br/><i>[R:TrainerCompGS.py:235-236]</i>"]

    IMG --> L1 --> D
    GT --> L1
    IMG --> SS --> D
    GT --> SS
    D --> TOT
    REG --> TOT
    BPP --> R --> TOT
    AUX -.->|"backward separately"| AUX2["aux_optimizer.step()<br/><i>[R:TrainerCompGS.py:299]</i>"]
```

> **Three deltas visible here at once:** the undocumented `REG` term (D-2), the
> undocumented `aux_loss` / second optimizer (D-3), and the undocumented 3 000-iteration
> warm-up before the rate term switches on (D-4).

---

## Stage E — Optimization + adaptive control (Scaffold-GS)

```mermaid
flowchart TD
    IT(["iteration i, 1 → 30 000"]) --> LR["cosine/exp LR decay per param group<br/><i>[R:TrainerCompGS.py:76]</i>"]
    LR --> FW["render: predict K·N primitives, cull α ≤ 0, rasterize"]
    FW --> BW["L.backward(); aux_loss.backward()"]
    BW --> ST["gaussian_optimizer.step(); aux_optimizer.step()<br/><i>[R:TrainerCompGS.py:296-300]</i>"]

    ST --> AUXC{"3·M &lt; i &lt; 15 000 ?<br/>(M = #train views)"}
    AUXC -- yes --> UPD["accumulate ∇μ, opacities, denoms<br/><i>[R:TrainerCompGS.py:287-289]</i>"]
    AUXC -- no --> CTRL

    UPD --> CTRL{"5·M &lt; i &lt; 15 000<br/>AND i mod (2·M) == 0 ?"}
    CTRL -- yes --> GROW["<b>growing</b>: 3 hierarchy levels<br/>τ_level = grad_thr·2^level<br/>random keep-prob 0.5^(level+1)<br/>voxelize candidate coupled means,<br/>dedupe against existing anchors,<br/>new f_ω ← scatter_max of parents,<br/>new g_k ← <b>0</b><br/><i>[R:AdaptiveControl.py:38-113]</i>"]
    GROW --> PRUNE["<b>prune</b>: Σα_accum &lt; opacity_thr · denom<br/><i>[R:AdaptiveControl.py:116-131]</i>"]
    PRUNE --> RST["reset_aux_params()"]
    CTRL -- no --> NEXT
    RST --> NEXT([i+1])

    NEXT --> STOP{"i == 15 000 ?"}
    STOP -- yes --> REL["remove_aux_params() — adaptive control ends<br/><i>[R:TrainerCompGS.py:292-293]</i>"]
```

> **The control schedule is view-count-relative, not iteration-absolute.** Intervals are
> `base × num_training_views` `[R:TrainerCompGS.py:284-304; Configs/*.yaml comments]`, so a
> scene with 300 views densifies ~6× less often than one with 50 views at the same
> iteration count. Unusual, undocumented in the paper, and important for reproduction.

---

## Stage F — Compression, decompression, evaluation

```mermaid
flowchart LR
    TR["trained model"]
    VOXR["μ_ω / voxel_size → integers<br/>assert no duplicates<br/><i>[R:Model.py:313-315]</i>"]
    MORT["Morton-order sort of all params<br/><i>[R:Model.py:318-320]</i>"]
    AC["arithmetic coding of f_ω, Σ_ω, g_k + hyperpriors<br/>(CompressAI)<br/><i>[P §3.4]</i> <i>[R:Model.py:323]</i>"]
    GPCC["<b>G-PCC (MPEG TMC13)</b> on integer anchor positions<br/><i>[P §3.4]</i> <i>[R:Model.py:326]</i>"]
    NPZ["bitstreams.npz<br/><i>[R:Model.py:331]</i>"]
    W["weights.pth — MLPs + entropy model<br/><b>counted in the reported size</b><br/><i>[R:TrainerCompGS.py:346-348]</i>"]

    DEC["decompress → render_inference()<br/>measures predict_time + render_time separately<br/><i>[R:TesterCompGS.py:63-66,147]</i>"]
    PNG[("save PNG to disk, re-open with PIL")]
    MET["PSNR = 10·log₁₀(1/MSE) — POOLED MSE<br/>SSIM = pytorch_msssim<br/>LPIPS = VGG, v0.1<br/><i>[R:TesterCompGS.py:153-167]</i>"]

    TR --> VOXR --> MORT --> AC --> NPZ
    MORT --> GPCC --> NPZ
    TR --> W
    NPZ --> DEC --> PNG --> MET
    W --> DEC
```

> Two things worth carrying into the comparison:
> **(a)** the reported model size **includes `weights.pth`** — honest, and unusual;
> **(b)** PSNR is **pooled-MSE** on **8-bit PNGs round-tripped through disk**
> `[R:TesterCompGS.py:153-159]` — the same convention as `seathru_NeRF/`, and *different*
> from the per-channel-mean PSNR used by `seasplat/`, `mini-splatting/` and 3DGS itself.
> See [`10-reproducibility.md`](10-reproducibility.md).
