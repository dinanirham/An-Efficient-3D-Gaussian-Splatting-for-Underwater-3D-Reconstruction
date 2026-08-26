# §2 — Pipeline flowcharts

The full pipeline exceeds ~6 nodes, so it is split into one diagram per stage, as the
methodology requires. Node labels carry evidence tags; `[R:file:line]` abbreviates
`[repo: file:line]`.

---

## Stage A — Data → preprocessing

```mermaid
flowchart LR
    RAW["RAW DSLR frames<br/>(underwater housing, dome port)<br/>white-balanced<br/><i>[paper §V.A.a]</i>"]
    COLMAP["COLMAP SfM<br/>Schönberger &amp; Frahm 2016<br/><i>[paper §IV.A]</i>"]
    UND["undistorted images/<br/>+ sparse/0<br/><i>[R:README.md]</i>"]
    READ["readColmapSceneInfo<br/><i>[R:scene/dataset_readers.py:223]</i>"]
    SPLIT{"model_params.eval ?<br/><i>[R:arguments/__init__.py:58]</i>"}
    TR["train = idx %% 8 != 0<br/><i>[R:dataset_readers.py:262]</i>"]
    TE["test = idx %% 8 == 0<br/><i>[R:dataset_readers.py:263]</i>"]
    ALL["train = ALL frames<br/>test = &empty;<br/><i>[R:dataset_readers.py:270-271]</i>"]
    PCD["COLMAP sparse point cloud<br/>→ Gaussian means μ<br/><i>[R:scene/__init__.py]</i>"]

    RAW --> COLMAP --> UND --> READ --> SPLIT
    SPLIT -- "--eval" --> TR
    SPLIT -- "--eval" --> TE
    SPLIT -- "default (False)" --> ALL
    READ --> PCD
```

> **Trap:** `eval` defaults to `False` `[R:arguments/__init__.py:58]`. Without `--eval` the
> "test" set is empty and *every* frame is trained on. See [`10-reproducibility.md`](10-reproducibility.md).

---

## Stage B — Model initialisation

```mermaid
flowchart TD
    subgraph GS["3D Gaussian model — inherited from 3DGS"]
        MU["μ ← COLMAP points (N,3)"]
        SH["SH coeffs, degree 0 only<br/>sh_degree default = 0, NOT 3<br/><i>[R:arguments/__init__.py:49]</i>"]
        SO["S, R, o ← 3DGS defaults"]
    end

    subgraph MED["Medium model — new in SeaSplat"]
        BSN["BackscatterNetV2<br/>β^B ← U(0,1)³, B^∞ ← U(0,1)³<br/><i>[R:deepseecolor/models.py:54,61]</i>"]
        ATN["AttenuateNetV3 (default)<br/>β^D ← [1.1, 0.95, 0.95] fixed init<br/><i>[R:models.py:216-218]</i>"]
    end

    subgraph BG["Learned background — repo-only"]
        BGP["bg ← U(0,1)³ then r=0.05, g=0.25, b=0.80<br/>stored as logit<br/><i>[R:train.py:126-130]</i>"]
    end

    OPT1["Adam: gaussians.optimizer<br/>per-group lr (3DGS schedule)"]
    OPT2["Adam: bs_optimizer, at_optimizer<br/>lr = bs_at_lr = 1e-2<br/><i>[R:train.py:91-92]</i>"]
    OPT3["Adam: bg_optimizer<br/>lr = bg_lr = 1e-2<br/><i>[R:train.py:131]</i>"]

    GS --> OPT1
    MED --> OPT2
    BG --> OPT3
```

> Three **separate** Adam optimizers, stepped on different schedules — this separation is
> load-bearing for well-posedness, see [`05-constraints.md`](05-constraints.md).

---

## Stage C — Forward pass (one training iteration, after `seathru_from_iter`)

```mermaid
flowchart LR
    CAM["viewpoint_cam<br/>sampled w/o replacement<br/><i>[R:train.py:196-198]</i>"]
    R1["rasterize colour<br/>render()<br/><i>[R:train.py:201]</i>"]
    R2["rasterize depth<br/>render_depth() — 2nd pass,<br/>override_color = z_cam<br/><i>[R:gaussian_renderer/__init__.py:128-137]</i>"]

    JHAT["Ĵ = rendered_image<br/>(medium-free colour)"]
    ALPHA["α = accumulated opacity"]
    ZRAW["Z_raw"]

    NORM["Ẑ = Z_raw / α<br/>NaN→max, ÷ normalize_depth,<br/>min-max renormalise<br/><i>[R:train.py:222-237]</i>"]

    AT["Â = exp(-β^D ⊛ Ẑ)<br/>1×1 conv, clamp≥0<br/><i>[R:models.py:226-232]</i>"]
    BS["B̂ = σ(B^∞)·(1 - exp(-β^B ⊛ Ẑ))<br/><i>[R:models.py:70-85]</i>"]
    D["D̂ = Ĵ ⊙ Â<br/><i>[paper §IV.A]</i> <i>[R:train.py:256]</i>"]
    I["Î = clamp(D̂ + B̂, 0, 1)<br/><i>[R:train.py:273]</i>"]

    CAM --> R1 --> JHAT
    R1 --> ALPHA
    CAM --> R2 --> ZRAW --> NORM
    ALPHA --> NORM
    NORM --> AT
    NORM --> BS
    JHAT --> D
    AT --> D
    D --> I
    BS --> I
```

**Detach map for this stage** (the well-posedness mechanism, made visible):

```mermaid
flowchart LR
    Z["Ẑ"] -->|"grad flows"| AT1["Â used in Î"]
    Z -->|"grad flows"| BS1["B̂ used in Î"]
    Z -.->|"DETACHED<br/>[R:train.py:255,270]"| ATD["Â', B̂' — depth-detached copies<br/>used only by medium-only losses"]
    Z -.->|"DETACHED<br/>[R:train.py:279,298]"| W["depth weight in L_Z-recon"]
    style ATD stroke-dasharray: 5 5
    style W stroke-dasharray: 5 5
```

> The repo computes each medium map **twice** — once on live `Ẑ` (used inside `Î` for the
> photometric loss) and once on `Ẑ.detach()` (used inside `L_bs`) `[R:train.py:254-255, 269-270]`.
> The paper describes only the detached direction: "B̂ is calculated using the estimated
> depth … which is detached to prevent gradients from flowing through" `[paper §IV.A]`.
> This is a genuine paper-vs-repo delta — see [`06-implementation-deltas.md`](06-implementation-deltas.md) D-3.

---

## Stage D — Loss composition

```mermaid
flowchart TD
    subgraph INPUTS["tensors entering the loss"]
        I_gt["I  (captured)"]
        I_hat["Î  (reconstructed in-medium)"]
        J_hat["Ĵ  (medium-free)"]
        Z_hat["Ẑ"]
        A_img["α"]
        Binf["σ(B^∞)"]
    end

    L1["L₁(Î, I)"]
    DSSIM["1 - SSIM(Î, I)"]
    LGS["L_GS = 0.8·L₁ + 0.2·D-SSIM<br/><i>[paper Eq.2]</i> <i>[R:train.py:293]</i>"]

    LZR["L_Z-recon = ‖Ẑ.detach ⊙ (Î - I)‖₁<br/>λ = dwr_lambda = 1.0<br/><i>[paper Eq.7]</i> <i>[R:train.py:296-301]</i>"]
    LBS["L_bs = 1000·SmoothL₁(relu(-D̃)) + L₁(relu(D̃))<br/>D̃ = I - B̂', λ = 1.0<br/><i>[paper Eq.4]</i> <i>[R:train.py:396-403]</i>"]
    LGW["L_gw = mean_c(mean(Ĵ_c) - 0.5)²<br/>λ = 0.1, gated iter &gt; 10 000<br/><i>[paper Eq.5]</i> <i>[R:train.py:354-371]</i>"]
    LSAT["L_sat = mean(relu(-Ĵ) + relu(Ĵ-0.7))²<br/>λ = 2.0<br/><i>[paper Eq.6]</i> <i>[R:train.py:381-385]</i>"]
    LOP["L_op = L₁(α[‖Î-B^∞‖₂ &lt; 0.2√3], 0)<br/>λ = bg_lambda = 0.01<br/><i>[paper Eq.9]</i> <i>[R:train.py:309-331]</i>"]
    LZS["L_Zsmooth = |∂ₓẐ·e^{-∂ₓI}| + |∂_yẐ·e^{-∂_yI}|<br/>λ = 2.0<br/><i>[paper Eq.8]</i> <i>[R:train.py:340-344]</i>"]

    TOTAL["L_total<br/><i>[paper Eq.10]</i>"]

    I_hat --> L1 --> LGS
    I_gt --> L1
    I_hat --> DSSIM --> LGS
    I_gt --> DSSIM

    I_hat --> LZR
    I_gt --> LZR
    Z_hat -.detached.-> LZR

    I_gt --> LBS
    Binf --> LOP
    A_img --> LOP
    I_hat -.detached.-> LOP

    J_hat --> LGW
    J_hat --> LSAT
    Z_hat --> LZS
    I_gt --> LZS

    LGS --> TOTAL
    LZR --> TOTAL
    LBS --> TOTAL
    LGW --> TOTAL
    LSAT --> TOTAL
    LOP --> TOTAL
    LZS --> TOTAL
```

> **Weighting delta.** The paper writes Eq. 10 as a bare sum of seven terms with no
> coefficients. The repo attaches a distinct λ to six of them, spanning two orders of
> magnitude (0.01 → 2.0). Detailed in [`04-loss.md`](04-loss.md) and [`11-paper-vs-repo-disagreements.md`](11-paper-vs-repo-disagreements.md).

---

## Stage E — Optimization / update schedule

```mermaid
flowchart TD
    START(["iteration i"]) --> GATE{"do_seathru AND<br/>i &gt; seathru_from_iter?"}

    GATE -- no --> PLAIN["plain 3DGS step<br/>Ĵ compared directly to I"]
    PLAIN --> DENS

    GATE -- yes --> INIT{"first time here?<br/>(not bs_inited)"}

    INIT -- yes --> WARM["1000 medium-only Adam steps<br/>bs_optimizer.step(); at_optimizer.step()<br/><b>iteration counter NOT advanced</b><br/><i>[R:train.py:436,446-453]</i>"]
    WARM --> CADJ["2000 colour-only GS Adam steps<br/>(xyz/opacity/scale/rot frozen at<br/>seathru_from_iter+1)<br/><b>iteration counter NOT advanced</b><br/><i>[R:train.py:189,456-463]</i>"]
    CADJ --> NORMSTEP

    INIT -- no --> PER{"i %% update_bs_at_interval == 0?<br/>(interval = 100)"}
    PER -- yes --> BURST["50 medium-only Adam steps<br/>counter not advanced<br/><i>[R:train.py:434-453]</i>"]
    PER -- no --> NORMSTEP
    BURST --> NORMSTEP

    NORMSTEP["gaussians.optimizer.step()<br/>bg_optimizer.step()<br/><i>[R:train.py:550-553]</i>"]
    NORMSTEP --> DENS

    DENS{"i &lt; densify_until_iter (15 000)?"}
    DENS -- yes --> DP["add_densification_stats<br/>every 100: densify_and_prune(τ=2e-4, min_op=0.005)<br/>every 3000: reset_opacity<br/><i>[R:train.py:517-543]</i>"]
    DENS -- no --> END
    DP --> END([next iteration])
```

> **The single most easily-missed control-flow fact in this repo:** the `continue`
> statements at `train.py:453` and `train.py:463` sit *above* the `iteration += 1` at
> `train.py:567`. The medium warm-up and colour-adjustment inner loops therefore consume
> **no iteration budget at all** — they are 3000 extra optimizer steps that do not appear
> in the 30 000-iteration count. This is reflected in the pseudocode
> ([`07-pseudocode.md`](07-pseudocode.md)) and in the wall-clock discussion
> ([`08-computational-profile.md`](08-computational-profile.md)).

---

## Stage F — Outputs

```mermaid
flowchart LR
    TRAINED["trained state"]
    G["Gaussians (.ply / chkpnt.pth)<br/><i>[R:train.py:557,560]</i>"]
    BSP["backscatter_&lt;it&gt;.pth<br/>attenuate_&lt;it&gt;.pth<br/><i>[R:train.py:562-563]</i>"]

    RSET["render_set()<br/><i>[R:render_uw.py]</i>"]
    OUT1["Î — in-medium novel view<br/>(dir: with_water/)"]
    OUT2["Ĵ — restored true colour"]
    OUT3["Ẑ — depth map"]
    OUT4["B̂, Â — medium maps"]

    DISK[("8-bit PNG **or JPEG**<br/>on disk<br/><i>[R:train.py:586-587]</i>")]
    MET["PSNR / SSIM / LPIPS(vgg)<br/>re-read from disk<br/><i>[R:train.py:639-644]</i>"]
    JSON["eval_metrics.json"]

    TRAINED --> G
    TRAINED --> BSP
    TRAINED --> RSET --> OUT1 & OUT2 & OUT3 & OUT4
    OUT1 --> DISK --> MET --> JSON
```

> Metrics are computed on **quantised files round-tripped through disk**, and the container
> format is JPEG whenever the ground-truth directory contains no PNGs
> `[R:train.py:586-587]`. See [`10-reproducibility.md`](10-reproducibility.md).
