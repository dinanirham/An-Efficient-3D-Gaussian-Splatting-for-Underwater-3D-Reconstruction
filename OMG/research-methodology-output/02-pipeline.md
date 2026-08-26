# §2 — Pipeline flowcharts

`[R:file:line]` = `[repo: file:line]`; `[P §x]` = `[paper §x]`.
Stages A–B are **inherited unchanged from `../mini-splatting/`**; C–F are OMG's contribution.

---

## Stage A — The inherited Mini-Splatting backbone (iterations 1 → 15 000)

```mermaid
flowchart LR
    INIT["COLMAP SfM points → Gaussians<br/>sh_degree = 3<br/><i>[R:arguments/__init__.py:49]</i>"]
    BLUR["<b>blur split</b> — split Gaussians whose<br/>max-contribution area &gt; H·W/5000<br/><i>[mini-splatting]</i>"]
    DR["<b>depth reinitialization</b> every 5000 it<br/>num_depth = 3.5M, num_max = 4.5M<br/><i>[R:arguments/__init__.py:91-93]</i>"]
    S1["<b>simp_iteration1 = 15 000</b><br/>intersection preserving + importance sampling<br/>sampling_factor = 0.5, then reinit<br/><i>[R:arguments/__init__.py:89,95]</i>"]

    INIT --> BLUR --> DR --> S1
```

> ⚠️ **Everything documented in `../mini-splatting/research-methodology-output/` applies
> here**, including its *undocumented* mechanisms — the removed `reset_opacity()`, the
> `(1 − α_accum)`-weighted depth-reinit pixel sampling, and the LR-schedule rewind
> `update_learning_rate(i − simp_iteration1 + 5000)` `[R:train.py:73-77]`. OMG inherits all of
> them without comment.

---

## Stage B — The neural field switches on (iteration 15 000)

```mermaid
flowchart TD
    NET["<b>construct_net()</b> at net_itr = 15 000<br/><i>[R:train.py:178-180; arguments/__init__.py:97]</i>"]

    T["<b>T</b> = _features_static ∈ ℝ^{N×3}<br/>initialised from _features_dc[:,0].clone()<br/><i>[R:gaussian_model.py:724]</i>"]
    V["<b>V</b> = _features_view ∈ ℝ^{N×3}<br/>initialised to <b>zeros</b><br/><i>[R:gaussian_model.py:725]</i>"]

    MLPS["<b>mlp_cont</b> — the space feature MLP_s<br/>tcnn.NetworkWithInputEncoding<br/>3 → Frequency(<b>16 freqs</b>) → FullyFusedMLP(64, 1 hidden) → <b>13</b><br/><i>[P Eq.4]</i> <i>[R:gaussian_model.py:672-686]</i>"]

    OPT["Adam lr = 0.01, then<br/>LinearLR warm-up (100 it) ⊕ MultiStepLR(γ=0.33) at 1000/3500/6000<br/><i>[R:gaussian_model.py:737-751]</i>"]

    NET --> T & V & MLPS --> OPT
```

> **`D = 3`.** The paper writes `T ∈ ℝ^{N×D}`, `V ∈ ℝ^{N×D}` and says "`D` is the
> dimensionality of each feature" `[P §3.1]` **without ever giving its value**. Code: both are
> 3-dimensional `[R:gaussian_model.py:724-725]`, which is why the downstream MLPs take
> `n_input_dims = 16 = 3 + 13`.

---

## Stage C — Appearance decoding (per Gaussian, per frame)

```mermaid
flowchart LR
    P["Gaussian centre p_n ∈ ℝ³"]
    FN["<b>F_n = MLP_s(γ(p_n))</b> ∈ ℝ¹³<br/>Frequency encoding, 16 frequencies<br/><i>[P Eq.4]</i> <i>[R:gaussian_model.py:672-686]</i>"]

    CATT["cat(T_n, F_n) ∈ ℝ¹⁶"]
    CATV["cat(V_n, F_n) ∈ ℝ¹⁶"]

    DC["<b>MLP_t</b> → h_n^(0) ∈ ℝ³   (static colour)<br/>16→64→3, LeakyReLU<br/><i>[P Eq.3]</i> <i>[R:gaussian_model.py:698-708]</i>"]
    OP["<b>MLP_o</b> → o_n ∈ ℝ¹   (opacity)<br/>16→64→1<br/><i>[P Eq.3]</i> <i>[R:gaussian_model.py:710-720]</i>"]
    VW["<b>MLP_v</b> → h_n^(1,2,3) ∈ ℝ⁴⁵   (view-dependent SH)<br/>16→64→3·max_sh_rest<br/><i>[P Eq.4]</i> <i>[R:gaussian_model.py:687-697]</i>"]

    GEO["<b>scale s_n ∈ ℝ³, rotation r_n ∈ ℝ⁴</b><br/>PER-GAUSSIAN, no neural field<br/><i>[P §3.1]</i>"]

    RAST["rasterize (3DGS, unchanged)"]

    P --> FN --> CATT & CATV
    CATT --> DC & OP
    CATV --> VW
    DC & OP & VW --> RAST
    GEO --> RAST
```

> **The asymmetry is the design.** Appearance goes through the neural field; **geometry does
> not**. The paper's reason `[P §3.1]`: "Especially for geometry, each Gaussian covers a larger
> spatial region, requiring a more specific scale and rotation to accurately capture structural
> details. Therefore, we **retain the per-Gaussian parameterization** for scale `s` and
> rotation `r` as in 3DGS." This is the sharpest departure from LocoGS.
>
> **All four MLPs are `tcnn.FullyFusedMLP` with 64 neurons and 1 hidden layer**
> `[R:gaussian_model.py:672-720]` — "a **tiny MLP**" `[P §4.2]`. `mlp_cont` uses ReLU; the
> other three use LeakyReLU. None of this is in the paper.

---

## Stage D — Local distinctiveness scoring & pruning (iteration 20 000)

```mermaid
flowchart TD
    IP["<b>intersection_preserving()</b><br/>Mini-Splatting's routine, VERBATIM:<br/>accumulate blending weights over all train views;<br/>outdoor → accum_weights/area_proj, indoor → accum_weights;<br/>then imp_score[accum_area_max == 0] = 0<br/><i>[P Eq.7]</i> <i>[R:gaussian_model.py:627-650]</i>"]

    MORT["<b>sort_morton()</b><br/>quantize xyz to 21 bits, Morton-encode, argsort<br/><i>[P §3.3]</i> <i>[R:gaussian_model.py:752-760]</i>"]

    NB["order_l = clamp(order−1, 0)<br/>order_r = clamp(order+1, max)<br/>⚠ <b>exactly TWO neighbours</b><br/><i>[R:gaussian_model.py:654-655]</i>"]

    RES["res_color = mean( |T[order_l] − T| + |T[order_r] − T| )<br/><i>[P Eq.8]</i> <i>[R:gaussian_model.py:663]</i>"]

    LD["<b>imp_score ← imp_score · res_color^λ</b><br/>λ = lambda_ld = <b>2.0</b><br/>⚠ λ is an EXPONENT in code<br/><i>[P Eq.8]</i> <i>[R:gaussian_model.py:665; arguments/__init__.py:99]</i>"]

    CDF["<b>init_cdf_mask(imp_score, thres = τ)</b><br/>τ = importance_thresh ∈ {0.96, 0.98, 0.99, 0.999, 0.9999}<br/>= variants XS / S / M / L / XL<br/><i>[P §4.1]</i> <i>[R:gaussian_model.py:666; arguments/__init__.py:98]</i>"]

    PR["prune_points(¬mask)<br/><i>[R:gaussian_model.py:668]</i>"]

    IP --> MORT --> NB --> RES --> LD --> CDF --> PR
```

> **This one block replaces Mini-Splatting's plain CDF prune** at `simp_iteration2`. Everything
> before `res_color` is inherited; the `· res_color^λ` factor is OMG's contribution.
>
> ⚠️ **"K-nearest neighbors" is exactly 2.** `[P Eq. 8]` sums over `N_i^K`, "the set of
> K-nearest neighbors of Gaussian `i`", approximated "by sorting Gaussians in **Morton order**
> and selecting Gaussians with **adjacent indices**" `[P §3.3]`. In code that is precisely the
> Morton **predecessor and successor** — `K = 2`, not a tunable parameter. See D-1.
>
> ⚠️ **`res_color` uses `T` (the 3-D static appearance feature) once the net is enabled**, and
> falls back to `_features_dc[:,0]` before then `[R:gaussian_model.py:657-662]`. Since
> `net_itr = 15 000 < simp_iteration2 = 20 000`, the `T` branch is the one that runs.

---

## Stage E — Sub-vector quantization (iteration 29 000 → 30 000)

```mermaid
flowchart TD
    SVQ["<b>apply_svq()</b> at svq_itr = 29 000<br/>i.e. the FINAL 1 000 iterations<br/><i>[P §3.2]</i> <i>[R:train.py:88-89; arguments/__init__.py:96]</i>"]

    KS["<b>scale</b> s ∈ ℝ³<br/>slice_scale = <b>1</b> → 1 sub-vector of length 3<br/>cluster_scale = 2⁶ = <b>64</b> codewords<br/>⇒ this is plain VQ, not SVQ<br/><i>[R:arguments/__init__.py:100-101]</i>"]
    KR["<b>rotation</b> r ∈ ℝ⁴<br/>slice_rot = <b>2</b> → 2 sub-vectors of length 2<br/>cluster_rot = 2⁹ = <b>512</b> each<br/><i>[R:arguments/__init__.py:102-103]</i>"]
    KA["<b>appearance</b> cat(T, V) ∈ ℝ⁶<br/>slice_app = <b>2</b> → 2 sub-vectors of length 3<br/>cluster_app = 2¹⁰ = <b>1024</b> each<br/><i>[R:arguments/__init__.py:104-105; gaussian_model.py:816]</i>"]

    KM["<b>cuML K-Means</b>, max_iter = 1000, n_init = 1<br/>indices FROZEN thereafter<br/><i>[P §3.2]</i> <i>[R:gaussian_model.py:842-855]</i>"]

    FT["codebook finetuning for 1000 it<br/>Adam <b>lr = 1e-8</b>, eps = 1e-15<br/>⚠ effectively frozen<br/><i>[R:gaussian_model.py:818; train.py:191-192]</i>"]

    SVQ --> KS & KR & KA --> KM --> FT
```

> **The paper's stated strategy** `[P §3.2]`: "we adopt a **fine-tuning strategy in the final
> 1K iterations**: after initializing with K-means, we **freeze the indices** and **finetune
> only the codebook** using the rendering loss, without introducing any additional losses."
> ✅ The schedule matches exactly. ⚠️ But `lr = 1e-8` over 1000 Adam steps moves each codeword
> by ~1e-5 — the codebook is finetuned in name only. See D-2.
>
> ⚠️ **`slice_scale = 1` means the scale attribute is *not* sub-vector quantized** — it gets a
> single 64-entry codebook, i.e. ordinary VQ. Only rotation and appearance are actually
> partitioned. The paper presents SVQ as applied uniformly to "geometric attributes `s_n`,
> `r_n`" and the concatenated appearance features `[P §3.2]`.

---

## Stage F — Loss and post-processing

```mermaid
flowchart LR
    L["<b>L = 0.8·L₁ + 0.2·(1 − SSIM)</b><br/>λ_dssim = 0.2 — STOCK 3DGS, UNCHANGED<br/><i>[R:train.py:100-102]</i>"]

    ENC["<b>encode()</b> at iteration 30 000<br/><i>[R:train.py:116-124; gaussian_model.py:857]</i>"]
    XYZ["positions → float16 → uint16 → Morton sort → <b>G-PCC</b><br/><i>[P §4.1]</i> <i>[R:gaussian_model.py:859-863]</i>"]
    HUF["SVQ indices → <b>Huffman</b><br/><i>[P §4.1]</i>"]
    LZ["everything → single file, <b>LZMA</b> (comp.xz)<br/><i>[P §4.1]</i> <i>[R:train.py:117]</i>"]
    REP["storage.txt — per-component byte breakdown<br/>{xyz, scale, rotation, app, MLPs}<br/><i>[R:train.py:120-123]</i>"]

    L --> ENC --> XYZ --> HUF --> LZ --> REP
```

> **The objective is untouched 3DGS** `[R:train.py:100-102]` — no rate term, no regulariser, no
> auxiliary loss. Same situation as `../mini-splatting/` and `../EDGS/`, and unlike
> `../CompGS/` (which puts `λR` in the loss) and `../compact3d/` (opacity regulariser).
>
> ✅ **The MLPs are counted in the reported size** — `byte = {'xyz':0, 'scale':0, 'rotation':0,
> 'app':0, **'MLPs':0**}` `[R:train.py:121]`, and the reported figure is
> `os.path.getsize(comp.xz)` — the **actual file on disk**, not an estimate
> `[R:train.py:119]`. Honest accounting, matching `../CompGS/`'s practice.
