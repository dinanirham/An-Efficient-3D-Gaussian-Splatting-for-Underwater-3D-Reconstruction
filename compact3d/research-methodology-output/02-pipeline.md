# §2 — Pipeline flowcharts

`[R:file:line]` = `[repo: file:line]`; `[P §x]` = `[paper §x]`.
Everything not shown is **stock 3DGS**, supplied by the upstream repo via the file overlay.

---

## Stage A — Setup: a file overlay onto 3DGS

```mermaid
flowchart LR
    C1["clone compact3d"]
    C2["clone + install <b>3DGS</b> (INRIA) inside it"]
    C3["pip install <b>bitarray</b><br/>(the only extra dependency)"]
    C4["<b>bash move_files_to_gsplat.sh</b><br/>copies 4 files over the 3DGS tree"]
    OUT["train_kmeans.py · kmeans_quantize.py<br/>gaussian_model.py · decompress_to_ply.py"]

    C1 --> C2 --> C3 --> C4 --> OUT
```

> `[R:README.md]`. This is why `utils/`, `scene/`, `arguments/` are absent from this folder —
> they are 3DGS's. It also means **`safe_state`'s seed 0, `llffhold = 8`, the standard metric
> harness and `reset_opacity()` are all inherited unchanged**, unlike `../mini-splatting/` and
> `../OMG/`, which modify them.

---

## Stage B — Training timeline

```mermaid
flowchart TD
    P0["<b>0 → 15 000</b>: vanilla 3DGS<br/>densification, opacity reset, no quantization"]
    P1["<b>15 000 → 20 000</b>: opacity regularization<br/>λ_reg·Σα added to the loss;<br/>prune(0.005) every 1000 iterations<br/><i>[P §4]</i> <i>[R:train_kmeans.py:158-166, 220-226]</i>"]
    P2["<b>&gt; kmeans_st_iter</b>: quantization-aware training<br/>forward on centroids, STE backward<br/><i>[P §3]</i> <i>[R:train_kmeans.py:126-143]</i>"]
    P3["<b>30 000</b>: save codebook + bit-packed indices"]

    P0 --> P1 --> P2 --> P3
```

⚠️ **The start of quantization differs between paper and repo:**

| | Quantization starts | Opacity reg. window | K-means iters | Codebooks |
|---|---|---|---|---|
| **Paper `[§4]`** | **20 000** | 15 000 → 20 000 | **1** | color **4096**, covariance **16384** |
| **`run.sh`** `[R:run.sh]` | **15 000** | 15 000 → 20 000 | **10** | dc 4096, **sh 512**, scale/rot **4096** |
| **CLI defaults** `[R:train_kmeans.py:367-378]` | `30000` (⇒ never) | — | **1** ✅ | all **4096** |

The `run.sh` recipe is the **post-paper "opacity regularization" configuration** announced in
the README (31 July 2024), not the configuration behind Table 1. See D-2.

---

## Stage C — Quantization-aware forward/backward (the core mechanism)

```mermaid
flowchart TD
    NQ["<b>non-quantized parameters</b> (the ones actually optimized)<br/>f_dc, f_rest, _scaling, _rotation"]

    ASSIGN{"iteration %% kmeans_freq == 1 ?<br/>freq = 100<br/><i>[R:train_kmeans.py:127-130]</i>"}
    A1["<b>assign = True</b> → run K-means:<br/>cdist to all centers → argmin → update centers<br/>(kmeans_iters = 1 by default)<br/><i>[R:kmeans_quantize.py:138-172]</i>"]
    A2["<b>assign = False</b> → reuse cached nn_index,<br/>only re-average the centers<br/><i>[R:kmeans_quantize.py:46-61]</i>"]

    Q["<b>ẑ = centers[nn_index]</b><br/>gather per Gaussian<br/><i>[R:kmeans_quantize.py:194,204]</i>"]
    STE["<b>Straight-Through Estimator</b><br/>forward uses ẑ; gradients flow to the<br/>non-quantized parameters<br/><i>[P §3, ref [7]]</i>"]

    REND["rasterize with ẑ (3DGS, unchanged)"]
    LOSS["L = 0.8·L₁ + 0.2·(1−SSIM) [+ λ_reg·Σα]"]
    BACK["backward → update the NON-quantized params"]

    NQ --> ASSIGN
    ASSIGN -- yes --> A1 --> Q
    ASSIGN -- no --> A2 --> Q
    Q --> STE --> REND --> LOSS --> BACK --> NQ
```

> **The asymmetric-cost trick** `[P §3]`: "K-means has two steps: updating centroids given
> assignments, and updating assignments given centroids. We note that the latter is **more
> expensive** while the former is a simple averaging. Hence, we update the centroids **after
> each iteration** and update the assignments **once every `t` iterations**. We observe that
> the modified approach works well even for values of `t` as high as **500**."
> ✅ Verified: `update_centers()` (cheap, cached indices) vs the full `cdist` path
> `[R:kmeans_quantize.py:46-61 vs 138-172]`.
>
> ⚠️ **`iteration % freq == 1`** — assignments happen at 15001, 15101, … (off-by-one, harmless).
>
> ⚠️ **The paper's assignment freeze does not exist.** `[P §4]`: "keep the assignments constant
> thereafter till the last iteration, 30K" (after 25K). In code, reassignment continues every
> 100 iterations to the end `[R:train_kmeans.py:127-130]`. See D-3.

---

## Stage D — Four independent codebooks

```mermaid
flowchart LR
    G["each Gaussian: 59 parameters"]

    subgraph QUANT["quantized — 4 separate K-means"]
        DC["<b>DC colour</b> f_dc, d = 3<br/>forward_dc()"]
        SH["<b>higher-order SH</b> f_rest, d = 45<br/>forward_frest()"]
        SC["<b>scale</b>, d = 3<br/>⚠ quantized BEFORE exp activation<br/>forward_scale()"]
        RO["<b>rotation</b>, d = 4<br/>⚠ quantized BEFORE normalization<br/>forward_rot()"]
    end

    subgraph KEEP["NOT quantized"]
        POS["<b>position</b> — 'sharing them results in<br/>overlapping Gaussians'"]
        OP["<b>opacity</b> — a single scalar"]
    end

    G --> DC & SH & SC & RO
    G --> POS & OP
```

> **Why grouped rather than one codebook** `[P §3]`: "Performing a single K-means for the whole
> `d` dimensional parameters requires a **huge codebook** since the different parameters of the
> Gaussian are **not necessarily correlated**. Hence, we group similar types of parameters …
> and cluster them independently."
>
> **Why position and opacity are excluded** `[P §3]`: position because "sharing them results in
> **overlapping Gaussians**"; opacity because it "is a single scalar".
>
> **Activation-order detail** `[P §4]`: "The scale parameters of covariance are quantized
> **before applying the exponential activation**… quaternion based rotation parameters are
> quantized **before normalization**." Confirmed by the `forward_scale` / `forward_rot` entry
> points `[R:kmeans_quantize.py]`. This matters — quantizing post-activation would cluster in a
> distorted space.
>
> The code also supports joint variants `scale_rot` and `sh_dc` `[R:train_kmeans.py:141-144]`,
> matching the paper's Table 9 ablation.

---

## Stage E — Opacity regularization and pruning

```mermaid
flowchart LR
    R["<b>L_reg = Σ_i α_i</b><br/>(α ≥ 0 via sigmoid ⇒ sum = ℓ1 norm)<br/><i>[P §3]</i> <i>[R:train_kmeans.py:164]</i>"]
    W{"15 000 &lt; iter ≤ max_prune_iter (20 000)?<br/><i>[R:train_kmeans.py:160-162]</i>"}
    ON["λ_reg = 1e-7"]
    OFF["λ_reg = 0"]
    PR["every 1000 iterations:<br/>gaussians.prune(0.005, extent, None)<br/><i>[R:train_kmeans.py:220-226]</i>"]

    R --> W
    W -- yes --> ON --> PR
    W -- no --> OFF
```

> `[P §3]`: "we add ℓ1 norm of the opacity to the loss as a regularizer to encourage zero
> values… `L = L_3DGS + λ_reg Σ_i α_i`". ✅ `[R:train_kmeans.py:164-166]`.
>
> ⚠️ **The 15 000 boundary is hard-coded**, not a CLI argument
> `[R:train_kmeans.py:160-161, 221]` — only the *upper* bound (`--max_prune_iter`) is
> configurable.
>
> This is the **only** loss modification in the method, and it is what produces the 2–3×
> rendering speedup — see [`01-taxonomy.md`](01-taxonomy.md).

---

## Stage F — Storage

```mermaid
flowchart LR
    SV["at save: non-quantized attributes → .ply<br/><i>[R:train_kmeans.py:190-196]</i>"]
    IDX["indices → dec2binary(cls_ids, n_bits) → bitarray → <b>kmeans_inds.bin</b><br/><i>[R:train_kmeans.py:261-268]</i>"]
    CB["codebooks → <b>kmeans_centers.pth</b><br/><i>[R:train_kmeans.py:276-279]</i>"]
    META["params, n_bits, total_len → <b>kmeans_args.npy</b><br/><i>[R:train_kmeans.py:270-275]</i>"]
    DEC["<b>decompress_to_ply.py</b> → standard 3DGS .ply for SIBR viewers"]

    SV --> IDX --> CB --> META --> DEC
```

> ⚠️ **Run-length encoding is absent.** `[P §3]` describes sorting Gaussians by one index "so
> that Gaussians using the same code appear together in the list. Then … we store how many
> times each code appears… reducing the storage from `n` integers to `k` integers. This is
> similar to run-length-encoding." **No sorting and no RLE exist in the repo** —
> `grep -rn "rle\|RLE\|run_length\|argsort"` finds nothing relevant; `save_kmeans` performs
> plain bit-packing. See D-1.
>
> ⚠️ **Bit width is derived from the Gaussian count, not the codebook size:**
> `n_bits = int(np.ceil(np.log2(len(kmeans.cls_ids))))` `[R:train_kmeans.py:263]`, and
> `cls_ids` is set to `nn_index` — the **per-Gaussian assignment vector of length N**
> `[R:kmeans_quantize.py:118]`. For `N ≈ 10⁶` that is **20 bits** where `log2(4096) = 12`
> would do. See D-4.
