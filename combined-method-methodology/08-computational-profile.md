# §8 — Computational profile

## 8.0 The finding that governs this section

**Phase 0 searched `my-research/` outside the two excluded paths for any combined-method
measurement — CSV, JSON, log, checkpoint, render, or output directory — and found none.**
There is no `draft-thesis-output/`, no `master_metrics.csv`, no per-scene results, no
TensorBoard event files. The only directory named `results/` anywhere in scope belongs to
`../CompGS/` and holds that method's own artifacts.

Consequently **every cell of every combined-method table in this section reads
`NO RESULTS FOUND`.** They are laid out as empty tables rather than omitted, because the
shape of the table is itself a deliverable: it specifies exactly what has to be measured,
in what units, with what normalisation, for the study to answer its own question.

The individually reported figures below are real and citable; they belong to *other papers
on other hardware and (except SeaSplat) other data*, and the section is organised so that
the two categories can never be confused.

---

## 8.1 Individually reported gains, as published

### The baseline — SeaSplat `[../seasplat/08-computational-profile.md §8.1]`

Averaged across training and evaluation on the SeaThru-NeRF datasets — **the same four
scenes this work uses.**

| Method | Train time | Render time | VRAM |
|---|---|---|---|
| **SeaSplat** | **1 h 25 m** | **0.012 s** (≈83 FPS) | **4.0 GB** |
| SeaThru-NeRF | 21 h | 10.184 s (≈0.098 FPS) | 33.2 GB |
| 3DGS | 40 m | 0.006 s (≈167 FPS) | 3.8 GB |

Overheads vs 3DGS: **2.13×** train, **2.00×** render, **1.05×** VRAM. The 2× render cost has
an identified structural cause — the second rasterization pass for depth — so it persists on
any device `[../seasplat/08-computational-profile.md §8.5]`.

⚠️ **Hardware is not stated.** The paper says only "a consistent set of hardware." The
Dockerfile targets SM 8.6/8.9 with SM 9.0 (Hopper) **explicitly commented out**, which is
suggestive of a consumer Ampere/Ada card but not conclusive
`[../seasplat/08-computational-profile.md §8.2]`.

⚠️ **Gaussian count and model size are never reported** — only logged to TensorBoard
`[../seasplat/08-computational-profile.md §8.4]`. **This is the single largest gap for this
work**, because the baseline's primitive count is what CD-5 sets the budget from and what
every efficiency ratio must be normalised against. It has to be measured, not looked up.

### M1 — EDGS `[../EDGS/08-computational-profile.md §8.1]`

**NVIDIA A100, competitors re-run on the same hardware**, and reported training time
*includes* initialization — the best measurement discipline in the comparison set.

| Dataset | vs 3DGS\* (the strong baseline) |
|---|---|
| Tanks&Temples | LPIPS **−22%**, `#G` **−13%**, PSNR +0.52 dB, train **+21%** |
| Mip-NeRF 360 | LPIPS **−34%**, `#G` **−32%**, PSNR +0.53 dB, train **+4%** |
| Deep Blending | LPIPS **−8%**, `#G` **−38%**, PSNR +0.04 dB, train **+11%** |

⚠️ **"The consistent story is LPIPS and Gaussian count, not PSNR."** EDGS is second-best on
PSNR on two of three datasets. Its own framing is "best or **second-best**"
`[../EDGS/08-computational-profile.md §8.1]`. **Do not import "EDGS improves quality" into
this work's hypotheses; import "EDGS improves LPIPS and reduces count at roughly equal
wall-clock."**

⚠️ VRAM never reported; peak memory is **at initialization**, not during training, because
up to `num_refs × matches_per_ref` candidate Gaussians exist before pruning `[inferred]`.

### M2 — Mini-Splatting `[../mini-splatting/08-computational-profile.md §8.1]`

RTX 3090. The most thoroughly reported profile in the set — train time, peak memory for both
training and rendering, FPS, and counts, split indoor/outdoor.

| vs 3DGS | Outdoor | Indoor |
|---|---|---|
| Gaussian count | **8.5× fewer** | **3.7× fewer** |
| Training time | **1.68× faster** | **0.91× — 9% SLOWER** |
| Training memory | **2.85× less** | 0.99× — parity |
| Rendering FPS | **4.18× faster** | **2.40× faster** |
| Rendering memory | **7.0× less** | **3.06× less** |

⚠️ **The training-time and training-memory wins are outdoor-only.** The headline framing
("significantly accelerates both training and rendering while reducing peak memory") is
written from the outdoor column. **Rendering wins hold in both.**
`[../mini-splatting/08-computational-profile.md §8.1]`

⚠️ Note also that 8.5× fewer Gaussians buys only 4.18× FPS — **sub-linear**, as expected,
because sorting is `O(n log n)` and per-pixel blending saturates. Any prediction for A2 must
be sub-linear too.

### M3 — CompGS-VQ `[../compact3d/08-computational-profile.md §8.1]`

RTX 6000 (Turing or Ada, ambiguous), 3DGS re-run on the same card.

| vs reproduced 3DGS | Mip-NeRF 360 | Tanks&Temples |
|---|---|---|
| Compression, 32K | **41×** (778 → 19 MB) | **33×** (433 → 13 MB) |
| Compression, 32K BitQ | **65×** (778 → 12 MB) | **54×** (433 → 8 MB) |
| Rendering | **2.3×** (149 → 344 FPS) | **2.3×** (206 → 475 FPS) |
| PSNR, 32K | **−0.30 dB** | −0.24 dB |
| **Training** | **+36%** (21.6 → 29.4 min) | **+69%** (12.2 → 20.6 min) |

⚠️ **The 2.3× FPS gain comes from the ℓ1 opacity regulariser and pruning, not from the
quantization** — the paper says so, and this work **disables that regulariser** (CD-8).
**A3's expected FPS gain is therefore ≈ 1.0×, not 2.3×.** `[inferred]`

⚠️ **Training is 1.4–1.7× slower** for the 32K variant; K-means is the acknowledged cost.
`../CompGS/` (Liu) independently measures this method's encode time at **68.29 s vs
0.54–2.23 s** for four other compression methods `[../compact3d/08-… §8.2]`.

---

## 8.2 The three reasons these numbers cannot simply be multiplied

Before any table, three normalisation problems that make naive composition arithmetic wrong:

**(1) The per-Gaussian storage baseline differs by 4.2×.** SeaSplat stores **14 floats** per
Gaussian (`sh_degree = 0`); the compression literature assumes **59**
`[../seasplat/08-computational-profile.md §8.4]`. `../comparison-glossary.md` §3.2 states it
directly: "Normalising compression ratios against a 59-float baseline for one and 14 for the
other is a category error waiting to happen." **CompGS-VQ's 41–65× cannot be expected here,
because the 45 SH floats it compresses hardest do not exist.**

A crude ceiling, `[inferred]`: of SeaSplat's 14 floats, M3 can quantize `f_dc` (3), `s` (3)
and `q` (4) = **10 floats to 3 indices**, leaving `μ` (3 floats) and `o` (1 float)
uncompressed. Even at zero index cost, that is a floor of ~4/14 ≈ **3.5× compression from
quantization alone**, before the count reduction M2 provides. This is an order of magnitude
below CompGS-VQ's headline and it is a *structural* consequence of the baseline, not a
failure of the method.

**(2) Hardware is not comparable across the four sources.** `../comparison-glossary.md` §3.6
ranks disclosure: RoMa v2 (H200) > SeaThru-NeRF and EDGS (A100) > Mini-Splatting (3090),
CompGS-VQ (RTX 6000) > **SeaSplat and CompGS-Liu (none named)**. Three GPU generations and
two form factors are represented. 3DGS rasterization is bound by tile sorting, atomics and
memory bandwidth rather than tensor cores, so speedups across generations are consistently
**sub-linear** in FLOPs — Mini-Splatting's GTX-1060 row is a rare direct data point for this
`[../mini-splatting/08-… §8.2]`.

**(3) Wall-clock and "iterations" are decoupled in the baseline.** The `continue` statements
bypass the iteration counter, so a "30 000-iteration" SeaSplat run performs **≈43 000**
optimizer steps, each paying the **full two-rasterization forward cost**
`[../seasplat/08-computational-profile.md §8.3]`. CD-6's re-warm-up bursts add more. **This
work reports effective optimizer steps alongside wall-clock**, and any comparison that
reports only "30 000 iterations" is not comparable to one that reports steps.

---

## 8.3 The combined-method measurement tables — to be filled

These are the deliverable of this section. Units, normalisation, and hardware are fixed here
so that the numbers, when they exist, are comparable.

**Protocol assumptions for every cell:** single GPU, named and reported; all eight cells on
the same device; ≥3 seeds per cell with dispersion reported; metrics per
`10-reproducibility.md` §10.3; `--eval` asserted non-empty; primitive counts measured as
**rendered Gaussians** (per `../comparison-glossary.md` §3.2).

### Table 8.3a — Quality (per scene, then unweighted scene mean)

| Cell | PSNR ↑ | SSIM ↑ | LPIPS ↓ |
|---|---|---|---|
| A0 baseline | NO RESULTS FOUND | NO RESULTS FOUND | NO RESULTS FOUND |
| A1 init | NO RESULTS FOUND | NO RESULTS FOUND | NO RESULTS FOUND |
| A2 prune | NO RESULTS FOUND | NO RESULTS FOUND | NO RESULTS FOUND |
| A3 quant | NO RESULTS FOUND | NO RESULTS FOUND | NO RESULTS FOUND |
| A4 init+prune | NO RESULTS FOUND | NO RESULTS FOUND | NO RESULTS FOUND |
| A5 init+quant | NO RESULTS FOUND | NO RESULTS FOUND | NO RESULTS FOUND |
| A6 prune+quant | NO RESULTS FOUND | NO RESULTS FOUND | NO RESULTS FOUND |
| A7 stacked | NO RESULTS FOUND | NO RESULTS FOUND | NO RESULTS FOUND |

### Table 8.3b — Efficiency

| Cell | `N_rend` (10⁶) | Model size (MB) | Train wall-clock | **Effective optimizer steps** | Render FPS | Peak VRAM |
|---|---|---|---|---|---|---|
| A0 … A7 | NO RESULTS FOUND | NO RESULTS FOUND | NO RESULTS FOUND | NO RESULTS FOUND | NO RESULTS FOUND | NO RESULTS FOUND |

> **Model size must include**: unquantized `.ply` (`μ` float32 + `o`) + index streams +
> codebooks + `kmeans_args.npy` + `backscatter_*.pth` + `attenuate_*.pth` (`02-pipeline.md`
> §2.7). CompGS-VQ's `Mem` column has "no decoder network to account for"
> `[../compact3d/08-… §8.2]`; this work has the nine medium scalars instead. Small, but it is
> the difference between a size and a claim.

### Table 8.3c — Diagnostic quantities specific to this study `[PI — CD-12]`

Nothing in the sources logs these; they exist to make the interaction hypotheses measurable.

| Cell | `Ẑ_min`/`Ẑ_max` **before → after** each simplification event | `β_att`, `β_bs`, `B^∞` at 15 K / 20 K / 30 K | `N` immediately post-init vs post-settling | `Ĵ` self-consistency PSNR vs the unquantized run |
|---|---|---|---|---|
| A0 … A7 | NO RESULTS FOUND | NO RESULTS FOUND | NO RESULTS FOUND | NO RESULTS FOUND |

Column 1 tests interaction candidate **IC-2** — whether pruning actually rescales the medium
model's input, and by how much. Column 2 tests whether the CD-6 re-warm-up re-identifies `β`,
and (under M3) whether the medium parameters absorb quantization error (`04-loss.md` §4.4).
Column 3 disambiguates EDGS's opacity-masked candidates from surviving primitives
(`../EDGS/11-…` D-2). Column 4 is the only available proxy for quantization damage to the
restoration output, which has no ground truth (`01-taxonomy.md` A3-b).

---

## 8.4 What a non-additive effect would look like — the claim-(b) test

Claim (b) requires a **measured** interaction. This subsection specifies the test in advance
so that the result, whichever way it falls, is interpretable.

**The additive null hypothesis.** For a metric `m` and a cell `A_S` with mechanism set `S`,
define the effect `Δ_S = m(A_S) − m(A_0)`. The additive prediction for a compound cell is

```
Δ̂_{S∪T} = Δ_S + Δ_T          (for quality metrics, in dB / SSIM / LPIPS units)
r̂_{S∪T} = r_S × r_T          (for multiplicative efficiency ratios: size, count, FPS)
```

**Non-additivity is `Δ_{S∪T} − Δ̂_{S∪T}` exceeding the seed dispersion of the cells
involved.** With `k` seeds per cell, the comparison must be against a pooled standard error,
not a single-run difference — this is the discipline `../seasplat/10-reproducibility.md`
§10.1 says the baseline itself lacks ("Table III's differences are ≤0.5 dB with no error
bars").

**The three interaction terms and their directional predictions:**

| Interaction | Predicted direction | Warrant |
|---|---|---|
| **M2 × M3** (A6) | **Sub-additive on quality** — quantization should cost more PSNR after pruning than before | `../OMG/`'s founding premise: "a smaller set of Gaussians becomes increasingly sensitive to lossy attribute compression" `[../OMG/00-index.md, paper Abstract]`. **This is the single strongest external prediction available and the most citable claim-(b) target.** |
| **M1 × M2** (A4) | **Degenerate or sub-additive on count** — if the budget does not bind, no effect at all; if it binds, EDGS's already-reduced count leaves M2 less to remove | `../EDGS/08-… §8.1` (EDGS reduces `#G` by 13–38%) + the budget's one-sided nature `[inferred]`; see `02-pipeline.md` §2.8 |
| **M1 × M3** (A5) | **Approximately additive** — the least-coupled pair; IP1 and IP3 share no stage and M3 cannot touch `μ` or `o` | `07-pseudocode.md` pt.2 `[inferred]` |
| **Three-way** (A7) | unpredicted | — |

**A domain-specific prediction that no terrestrial study can make**, and the one most worth
testing: **`L_op`'s effectiveness should degrade under M1 and M2.** The term is worth
+2.42 dB alone on this baseline `[../seasplat/04-loss.md §4.4]`, and both mechanisms rewrite
the opacity dynamics it was tuned against (IC-1). If A1 and A2 lose more quality than their
terrestrial analogues predict, the water-column floater mechanism is the first place to look
— and Table 8.3c column 3 plus a floater-ratio count (as `UW-3DGS` reports: 1.3% with its
pruning branch vs 8.2% without `[unverified — Phase 0 web fetch]`) would localise it.

> **If none of the interaction terms exceeds seed dispersion, that is a publishable
> result**, and it is the honest one to report: it would show that three efficiency
> mechanisms developed independently for terrestrial 3DGS *do* compose cleanly on a
> physically-grounded underwater baseline, once the integration fixes of §CD-1–CD-14 are
> applied. That is a weaker claim than a discovered interaction, but it is a real one, and
> it makes the claim-(c) integration work the load-bearing contribution rather than a
> preamble. `12-novelty-defensibility.md` develops this.

---

## 8.5 Complexity claims that survive the composition

| Claim | Type | Verdict |
|---|---|---|
| The medium model adds `O(1)` parameters — 9 scalars, independent of `N`, resolution, and view count | **Asymptotic, true, and unaffected by any mechanism** | ✅ No mechanism adds a medium parameter. The claim survives all eight cells intact. `[../seasplat/08-… §8.5]` |
| Fewer Gaussians ⇒ faster rendering | **Asymptotic in `N`**, since rasterization is `O(Σ_tiles Gaussians-per-tile)` | ✅ but **sub-linear**: Mini-Splatting's 8.5× count reduction bought 4.18× FPS `[../mini-splatting/08-… §8.4]`. Predict sub-linear for A2. |
| VQ storage goes from `N·d` floats to `K_cb·d` floats + `N` indices | **Structural, true for `N ≫ K_cb`** | ✅ — but the *ratio* is capped by §8.2(1). `[../compact3d/08-… §8.4]` |
| EDGS's initialization is `O(num_refs × nns × H·W)`, **independent of the iteration count** | **Structural, and correctly not framed as an asymptotic win** | ✅ `[../EDGS/08-… §8.4]`. Here `num_refs = min(180, V) ≤ 29` (CD-2), so the constant is far smaller than in EDGS's own experiments — the initialization should be cheap. |
| "SeaSplat preserves the computational efficiency of 3DGS" | **Empirical, unnamed hardware, 4 scenes** | ⚠️ It is a **2×** regression on both train and render. Cite the numbers, not the adjective. `[../seasplat/08-… §8.5]` |
| **Any combined-method efficiency claim** | — | ❌ **NO RESULTS FOUND.** Nothing may be claimed. |

---

## 8.6 Hardware and environment obligations

Not results, but they determine whether results are obtainable, and all four sources flag the
same problem from different directions.

| Source | Stack | Obstacle |
|---|---|---|
| SeaSplat | CUDA 11.8, torch 2.1.0+cu121; `Dockerfile` targets **SM 8.6/8.9 with 9.0 commented out** | must add `90` to `CUDA_ARCHITECTURES` and rebuild `diff-gaussian-rasterization` + `simple-knn` for Hopper `[../seasplat/08-… §8.2]` |
| EDGS | **CUDA 12.1, Python 3.10, current PyTorch** — the most modern in the set | RoMa weights are **downloaded at first use**; needs network access or pre-staged weights `[../EDGS/08-… §8.2]` |
| Mini-Splatting | **Python 3.7, torch 1.12.1+cu116** — Python 3.7 is EOL and will not accept a modern torch | budget a **full environment migration**; the **forked** rasterizer must be rebuilt against CUDA 12 `[../mini-splatting/08-… §8.2]` |
| CompGS-VQ | 3DGS-of-late-2023 plus `bitarray` — the lightest footprint of any compression method in the set | same `TORCH_CUDA_ARCH_LIST` rebuild `[../compact3d/08-… §8.3]` |

`[PI]` **These four cannot coexist as published.** The combined method requires a single
environment — CUDA 12, Python ≥3.10 — into which Mini-Splatting's forked rasterizer is
back-ported (CD-13) and CompGS-VQ's four method files are overlaid (that repo is "a **file
overlay**, not a standalone project" `[../compact3d/00-index.md]`, which is convenient here:
its method is four files, and overlaying them onto SeaSplat rather than onto stock 3DGS is a
small, well-defined port). Environment construction is therefore a real, non-trivial part of
the method's implementation and belongs in `chapter/04-implementation-details.md`, not in a
footnote.
