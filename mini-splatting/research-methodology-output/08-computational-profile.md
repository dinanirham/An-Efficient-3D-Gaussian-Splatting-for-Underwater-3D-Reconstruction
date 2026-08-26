# §8 — Computational profile

This is the most thoroughly-reported computational profile in the whole comparison set:
the paper names its GPUs, gives training time, peak memory for **both** training and
rendering, FPS, and Gaussian counts, split by indoor/outdoor. Measurement method is stated:
"peak memory consumption is measured using `torch.cuda.max_memory_allocated()`"
`[paper §6.1]`.

## 8.1 As reported

`[paper Tab. 2]` — Mip-NeRF 360, **RTX 3090** unless marked `*`:

### Outdoor scenes

| Method | Num (M) | Train time | Train mem | FPS | Render mem |
|---|---|---|---|---|---|
| 3DGS [17] | 4.86 | 30 m 08 s | 7.45 GB | 98 | 2.79 GB |
| Mini-Splatting-D | **5.40** | 31 m 48 s | 7.45 GB | 83 | 3.12 GB |
| **Mini-Splatting** | **0.57** | **17 m 56 s** | **2.61 GB** | **410** | **0.40 GB** |
| Mini-Splatting* (GTX 1060 6G) | 0.57 | 101 m 11 s | 2.61 GB | 64 | 0.40 GB |

### Indoor scenes

| Method | Num (M) | Train time | Train mem | FPS | Render mem |
|---|---|---|---|---|---|
| 3DGS [17] | 1.46 | 24 m 41 s | 2.75 GB | 151 | 1.07 GB |
| Mini-Splatting-D | 3.80 | 40 m 13 s | 5.55 GB | 83 | 2.46 GB |
| **Mini-Splatting** | **0.40** | 27 m 02 s | 2.77 GB | **362** | **0.35 GB** |
| Mini-Splatting* (GTX 1060 6G) | 0.40 | 154 m | 2.82 GB | 40 | 0.35 GB |

### Derived ratios vs. 3DGS

| Quantity | Outdoor | Indoor |
|---|---|---|
| Gaussian count | **8.5× fewer** | **3.7× fewer** |
| Training time | **1.68× faster** | 0.91× (**9% slower**) |
| Training memory | **2.85× less** | 0.99× (parity) |
| Rendering FPS | **4.18× faster** | **2.40× faster** |
| Rendering memory | **7.0× less** | **3.06× less** |

> ⚠️ **The training-time and training-memory wins are outdoor-only.** Indoors,
> Mini-Splatting is *slower* than 3DGS (27 m 02 s vs 24 m 41 s) at essentially identical
> peak memory (2.77 vs 2.75 GB), despite ending with 3.7× fewer Gaussians. The paper
> acknowledges this obliquely — "In indoor scenes, both our Mini-Splatting-D and
> Mini-Splatting learn denser Gaussian distributions, yet the results still show an
> acceptable resource consumption" `[paper §6.1]` — but the headline framing
> ("significantly accelerates both training and rendering while reducing peak memory")
> is written from the outdoor column. **Rendering wins hold in both.** Quote both columns.

### The `sh_degree` explanation for Mini-Splatting-D's memory

Mini-Splatting-D holds **5.40 M** Gaussians in the *same* 7.45 GB as 3DGS's 4.86 M. The
paper gives the mechanism: "our strategy of constraining SH coefficients during
densification" `[paper §6.1]` — at SH degree 0 a Gaussian stores 14 floats instead of 59
`[repo: ms/train.py:56]`. See [`03-variables.md`](03-variables.md).

## 8.2 Hardware — named, and *not* comparable to your H100 96 GB

| Aspect | Assessment |
|---|---|
| **Reported GPUs** | **RTX 3090** (24 GB, SM 8.6, Ampere consumer) for the main table; **GTX 1060 6G** (SM 6.1, Pascal) for the `*` row. Both named — better disclosure than `seasplat/` (none) and comparable to `seathru_NeRF/` (A100). |
| **vs H100 96 GB** | A generation-and-a-half behind and consumer-class. The 3090→H100 gap on 3DGS-style workloads is **not** the FLOP ratio: rasterization is bound by tile sorting, atomics and memory bandwidth, not tensor cores. Expect a real but sub-linear speedup. `[unverified — not measured here]` |
| **Memory headroom** | Every number here fits trivially on 96 GB: peak training memory is 7.45 GB. **You could raise `--num_max` (4.5 M) substantially** — it exists to bound memory on a 24 GB card `[repo: ms/train.py:153, 406]` and is not a methodological constraint. |
| **Software stack** | Python 3.7, torch 1.12.1+cu116 `[repo: README.md]`. **CUDA 11.6 predates Hopper (SM 9.0).** You must rebuild the two CUDA submodules — `diff_gaussian_rasterization_ms` (the *fork*, not upstream) and `simple-knn` — against CUDA 12 with `TORCH_CUDA_ARCH_LIST` including `9.0`. Python 3.7 is EOL and will not accept a modern torch; budget a full environment migration. |
| **The `*` row is genuinely useful** | The GTX 1060 result (5.6× / 5.7× slower training, 6.4× / 9.1× slower rendering than the 3090) gives you an actual hardware-scaling data point for this workload — rare in this literature. It shows the method is bandwidth-sensitive, which supports the sub-linear H100 expectation above. `[inferred: paper Tab. 2 rows 3 vs 4]` |

## 8.3 Storage compression (Mini-Splatting-C)

`[paper §6.1, Fig. 9]` — rate-distortion curves against Lee et al. [20] and
Niedermayr et al. [27].

The reported claim is qualitative: Mini-Splatting-C "demonstrates superior performance
compared to other methods primarily tailored for storage compression", attributed to
starting from an already-simplified model — "solely integrates **basic post-processing
techniques**" `[paper §6.1]`.

⚠️ **No numeric rate-distortion values are published** — Fig. 9 is a plot. `[unverified]`
The pipeline computes and prints the actual file size at
`[repo: ms_c/run.py:176-180]` (`print('filezie: %fmb' % ...)`), so exact numbers are
obtainable by running it, but none are in the paper.

**For a fair comparison against `compact3d/`, `CompGS/`, `OMG/`:** note that
Mini-Splatting-C's size includes an **undocumented voxel-deduplication** step
`[repo: ms_c/run.py:144]` (see delta D-10), so part of the compression is primitive
removal, not coding efficiency. Report `N` before and after.

## 8.4 Complexity claims — asymptotic vs. empirical

| Claim | Type | Verdict |
|---|---|---|
| Fewer Gaussians ⇒ faster rendering | **Asymptotic in `N`, and true.** Rasterization cost is `O(Σ_tiles Gaussians-per-tile)`, linear in density. | ✅ 8.5× fewer Gaussians → 4.18× FPS outdoor. **Sub-linear**, as expected: sorting is `O(n log n)` and per-pixel blending saturates. The paper does not make an asymptotic claim, only reports the measurement — correct practice. |
| "integrates seamlessly with the original rasterization pipeline" `[paper Abstract]` | **Qualitative, and slightly overstated.** | ⚠️ The *output* is a standard 3DGS `.ply` renderable by any viewer ✅. But **training requires a forked CUDA rasterizer** (`diff_gaussian_rasterization_ms`) that returns `accum_weights`, `area_proj`, `area_max`, `out_pts`, `accum_alpha` `[repo: gaussian_renderer/__init__.py:173, 189-191, 210]`. "Seamless" applies to inference, not to training. |
| Densification is nearly free | **Empirical, outdoor-only.** | ⚠️ 31 m 48 s vs 30 m 08 s outdoor (+5%) ✅ — but 40 m 13 s vs 24 m 41 s **indoor (+63%)**. The claim does not generalise. |
| Simplification pays for itself | **Empirical, outdoor-only.** | ⚠️ −40% training time outdoor, **+10% indoor**. |
| Mini-Splatting-C beats dedicated compression methods | **Empirical**, from a figure, with baselines "collected from their respective papers" `[paper §6.1]` — i.e. **not re-run on the same hardware or protocol**. | ⚠️ Cite with that caveat, and with the dedup caveat from §8.3. |

## 8.5 The hidden cost the table does not show

Depth reinitialization renders **every training view** three times per run (at 5 K, 10 K,
and implicitly at 15 K), and each simplification step renders **every training view** again
`[repo: ms/train.py:170, 216, 264]`. On Mip-NeRF 360 that is ≈100–300 views per pass, so
roughly **5 × M** extra full-resolution rasterizations per run.

That cost is real but small against 30 000 training iterations, and it is *already included*
in the reported wall-clock — but it scales with `M`, so on a dataset with many more views
the overhead grows while the training-iteration count does not. Worth knowing before
applying this to a large capture. `[inferred: repo ms/train.py:170, 216, 264 counted against arguments/__init__.py:73]`
