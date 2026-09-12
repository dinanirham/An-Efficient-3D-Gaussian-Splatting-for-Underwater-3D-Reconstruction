# §8 — Computational profile

## 8.0 The finding that governs this section

**Phase 0 searched `my-research/` outside the two excluded paths for any combined-method
measurement — CSV, JSON, log, checkpoint, render, or output directory — and found none.**
There is no `draft-thesis-output/`, no `master_metrics.csv`, no per-scene results, no
TensorBoard event files. The only directory named `results/` anywhere in scope belongs to
`../CompGS/` and holds that method's own artifacts.

When this section was written, **every cell of every combined-method table read
`NO RESULTS FOUND`** — the tables were laid out empty rather than omitted, because the shape
of a table is itself a deliverable: it specifies exactly what has to be measured, in what
units, with what normalisation, for the study to answer its own question.

**§8.3 is now populated for A0–A3 at n=12 per cell, and for A4 on one scene.** The units and
normalisation are unchanged from the empty version, which is the point of having specified
them in advance. A5–A7 and every interaction term remain unmeasured.

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

> ✅ **Confirmed by the implementation, 2026-08-28.** The storage accounting now computes this
> directly rather than estimating it: at `k = 4096` (12-bit indices) over three codebooks, the
> reported ratio against this baseline's 14 floats/primitive is **2.71×**
> `[implementation/tools/verify_quantize.py T9, executed]`. That sits just below the ~3.5×
> zero-index-cost ceiling above — as it must, since indices are not free — and it independently
> matches a third estimate of **≈2.8×** reached by a separate analysis of the same bottleneck.
> **Three estimates from different directions agreeing is the strongest evidence available
> that the ceiling analysis is right**, and it means the figure can be stated up front in the
> write-up rather than discovered at results time.
>
> The accounting also reports the unquantized remainder separately (position + opacity, which
> at 10⁶ primitives is 15.3 MB and is the entire residual budget once attributes are cheap) —
> the same diagnosis CompGS-VQ made, arriving here for the same structural reason.

### ⭐ The compression ratio depends on the primitive count — which M2 changes

Measuring the artifact on disk (rather than counting bits) exposed something the analytical
estimate hides: **the codebook is a fixed cost.** At `k = 4096` over three groups it is
`4096 × 10 floats × 4 B ≈ 160 KB` regardless of how many primitives exist, so it is amortised
over `N` and the achievable ratio *grows* with `N`.

Measured, and fitted by `ratio(N) = 56N / (20.5N + 163840)`:

| `N` | Ratio vs the 14-float baseline | Source |
|---|---|---|
| 5 000 | **1.05×** | measured `[verify_storage.py T4]` |
| 20 000 | **1.95×** | measured `[verify_storage.py T5]` |
| 100 000 | 2.53× | from the fit |
| 500 000 | 2.69× | from the fit |
| 1 000 000 | **2.71×** | analytical `[verify_quantize.py T9]` |
| `N → ∞` | 2.73× | asymptote, `56 / 20.5` |

The fit reproduces all three measured points, so the relationship is understood rather than
merely observed.

**Why this matters for the study.** M2 reduces `N`; M3's ratio improves with `N`. So the two
mechanisms interact on the **storage** axis, in a direction that is now predictable and
signed: *pruning makes quantization relatively less effective per primitive*, because the same
fixed codebook is spread over fewer of them.

Two consequences worth stating up front:

1. **The interaction is small at realistic budgets.** Between 500 k and 1 M primitives the
   ratio moves by only 0.02×. It becomes material only below ~50 k, which is well under any
   budget this study would set. So the effect exists, is real, and is probably not what makes
   A6 interesting — the quality-side sensitivity that `../OMG/` predicts remains the more
   likely story.
2. **A6 and A7 must report storage per primitive as well as total**, or a ratio that fell
   because `N` fell will be misread as quantization performing worse. That is a reporting
   requirement, not an analysis one, and it is now emitted automatically
   (`bytes_per_primitive` in every `model_size.json`).

This is a genuine interaction prediction with a closed form, derived from the implementation
rather than from either source paper — neither faced it, because neither varies `N` and the
codebook size together.

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

## 8.2b The A0 reference point, measured

§8.1 states that the baseline's own cost on *this* hardware "has to be measured, not looked
up", because every efficiency ratio in §8.3 divides by it. S1 supplies it.

**Twelve A0 runs, three seeds per scene, 30 000 iterations, A100-SXM4-40GB, sm_80.**

| scene | primitives (s0 / s1 / s2) | mean | sd | CV |
|---|---|---:|---:|---:|
| Curasao | 4 285 043 / 3 186 018 / 3 802 363 | 3 757 808 | 550 866 | 14.7% |
| IUI3-RedSea | 2 280 526 / 2 761 801 / 2 571 227 | 2 537 851 | 242 367 | 9.6% |
| JapaneseGradens-RedSea | 2 377 216 / 2 220 485 / 2 109 283 | 2 235 661 | 134 610 | **6.0%** |
| Panama | 1 590 127 / 2 393 173 / 2 934 459 | 2 305 920 | 676 400 | **29.3%** |

**Median across all twelve: 2 482 200.**

Per-run cost, from `A0/Curasao/s0` at 4 285 043 primitives:

| | measured | note |
|---|---|---|
| training wall clock | **4 682 s (78 min)** | the loop only; excludes scene load and evaluation |
| effective optimizer steps | **43 000** | against 30 000 iterations — the ratio §8.2 warns about, confirmed |
| render throughput | **69.2 fps**, 14.46 ms/frame | colour pass only, CUDA-synchronised, held-out views |
| peak render memory | **3 587 MB** | 9% of the card; memory is not a binding constraint here |

Two things this table settles that the published figures could not.

**Dispersion is heterogeneous across scenes by a factor of five.** Japanese Gardens has a
6.0% coefficient of variation; Panama has 29.3%, its slowest and fastest seeds differing by
1.85× at identical configuration. A pooled variance would hide that, and a per-scene contrast
on Panama is far weaker evidence than the same contrast on Japanese Gardens. **§8.3's ratios
must therefore be reported per scene with their own dispersion, never as a single pooled
number.** At the mean CV with three seeds the standard error of a scene mean is 8.6%, so a
difference on primitive count must exceed roughly **17%** to clear it — comfortable for the
main effects, which target 90%+, and not obviously comfortable for the interactions, which
are differences of differences.

**Curasao is not representative**, and earlier statements in this folder of the form "A0
converges to ~4.4M" are Curasao statements. The four-scene median is 2.48M. This matters
directly for §8.4's claim-(b) test, whose predicted effect sizes were sketched against the
higher figure.

---

## 8.3 The combined-method measurement tables — to be filled

These are the deliverable of this section. Units, normalisation, and hardware are fixed here
so that the numbers, when they exist, are comparable.

**Frame rate is now instrumented** (CD-24). It was not, when this table was written: the
`render_fps`, `render_ms_per_frame` and `render_peak_mem_mb` columns below had no source, and
the two predictions §8.4 rests on them — A3 showing ≈no gain, and sub-linear gains from count
reduction — had no instrument behind them.

**Protocol assumptions for every cell:** single GPU, named and reported; all eight cells on
the same device; ≥3 seeds per cell with dispersion reported; metrics per
`10-reproducibility.md` §10.3; `--eval` asserted non-empty; primitive counts measured as
**rendered Gaussians** (per `../comparison-glossary.md` §3.2).

### Table 8.3a — Quality, per scene `[measured n=3 per cell per scene]`

**Reported per scene, not pooled.** Per-scene dispersion differs roughly 5× across this
corpus, so a scene mean is a summary of four incommensurable quantities and is given only as
the last column, for continuity with the sources' reporting convention. Every contrast in
Chapter 4 is per scene.

**PSNR (pooled convention) ↑** — A0's own per-scene sd in parentheses, as the noise floor any
difference must clear.

| Cell | Curasao | IUI3-RedSea | JapaneseGardens | Panama | scene mean |
|---|---:|---:|---:|---:|---:|
| **A0** baseline | 30.15 (±0.70) | 26.89 (±0.49) | 23.01 (±0.22) | 28.75 (±0.62) | 27.20 |
| **A1** init | 30.63 | 27.54 | 23.70 | 28.95 | 27.70 |
| **A2** prune | 30.54 | 27.26 | 23.14 | 28.69 | 27.41 |
| **A3** quant | 29.79 | 27.24 | 23.19 | 29.16 | 27.34 |
| **A4** init+prune | 30.55 | — | — | — | *(Curasao only)* |
| A5 – A7 | *pending S4/S5* | | | | |

**LPIPS ↓** — the metric that separates the mechanisms; PSNR does not.

| Cell | Curasao | IUI3-RedSea | JapaneseGardens | Panama | scene mean |
|---|---:|---:|---:|---:|---:|
| **A0** baseline | 0.185 | 0.210 | 0.185 | 0.147 | 0.182 |
| **A1** init | 0.185 | 0.268 | 0.179 | 0.162 | 0.198 |
| **A2** prune | 0.215 | 0.289 | 0.216 | 0.201 | 0.230 |
| **A3** quant | 0.188 | 0.236 | 0.186 | 0.147 | 0.189 |
| **A4** init+prune | 0.215 | — | — | — | *(Curasao only)* |

**SSIM ↑** — A0 0.904 / 0.867 / 0.866 / 0.903 (mean 0.885); A1 0.908 / 0.857 / 0.890 / 0.905
(0.890); A2 0.904 / 0.854 / 0.871 / 0.893 (0.881); A3 0.903 / 0.864 / 0.870 / 0.907 (0.886).
SSIM separates nothing here and is reported for completeness.

> **The A2 column carries a covariate.** Six of its twelve runs have a collapsed attenuation
> channel — Curasao 2/3, IUI3 1/3, JapaneseGardens 1/3, Panama 2/3 — so every A2 cell above
> averages over two physically different models. The figure is correct as an average and
> misleading as a description of a model. `analyse.py` surfaces the collapse count before any
> contrast `[13-campaign-addendum §13.13]`.

### Table 8.3b — Efficiency, scene means `[measured n=12 per cell]`

Efficiency quantities are ratios against A0 on the same scene, so the scene mean is better
behaved here than for quality. Per-scene figures are in `results_by_scene.csv`.

| Cell | `N_rend` | vs A0 | Model size (MB) | vs A0 | Train wall-clock | Eff. steps | Render FPS | vs A0 | Peak render VRAM (MB) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **A0** baseline | 2 709 310 | 1.00× | 144.7 | 1.00× | 60.0 min | 43 000 | 117.6 | 1.00× | 2 518 |
| **A1** init | 222 498 | **12.2×** | 11.9 | **12.2×** | 49.5 min | 43 000 | 214.7 | 1.83× | 936 |
| **A2** prune | 141 856 | **19.1×** | 7.6 | **19.1×** | 45.2 min | 43 400 | 311.7 | 2.65× | 959 |
| **A3** quant | 2 653 827 | 1.02× | 52.0 | **2.78×** | 62.9 min | 43 000 | 130.1 | 1.11× | 2 639 |
| **A4** init+prune | 129 473 | 20.9× | 6.9 | 20.9× | 54.8 min | 43 400 | 223.1 | 1.90× | 935 |
| A5 – A7 | *pending S4/S5* | | | | | | | | |

*A4 is Curasao only (n=3); its ratios are against A0 on Curasao, not against the scene mean.*

**Two of §8.4's advance predictions are now settled by this table.** Frame-rate gain is
**sub-linear in count reduction and not a single exponent** — A1 buys 1.83× from 12.2×, A2
buys 2.65× from 19.1×, so per-primitive rasterization cost differs by cell and a count ratio
does not predict a frame-rate ratio. And **A3 delivers storage compression with essentially no
frame-rate gain** (2.78× bytes, 1.11× fps), as predicted in advance from CD-8 and
`sh_degree = 0`. Both predictions were registered before the instrument existed (CD-24).

**The compression ratio is smaller than the count ratio suggests it should be**, and the
reason is structural: `bytes_per_primitive` is 56.0 in every unquantized cell and 20.6 under
M3, a 2.72× ratio against CompGS-VQ's published 41–65×, because this baseline stores 14 floats
per primitive where the compression literature assumes 59. §8.2(1) develops this.

> **Model size must include**: unquantized `.ply` (`μ` float32 + `o`) + index streams +
> codebooks + `kmeans_args.npy` + `backscatter_*.pth` + `attenuate_*.pth` (`02-pipeline.md`
> §2.7). CompGS-VQ's `Mem` column has "no decoder network to account for"
> `[../compact3d/08-… §8.2]`; this work has the nine medium scalars instead. Small, but it is
> the difference between a size and a claim.

### Table 8.3c — Diagnostic quantities specific to this study `[PI — CD-12]`

Nothing in the sources logs these; they exist to make the interaction hypotheses measurable.
They are the reason H4 is answerable at all, and the column that carries the campaign's
central finding is the second.

| Cell | `Ẑ` range across each simplification event | `β` across 15 K / 20 K / 30 K | `N` post-init vs post-settling | `Ĵ` self-consistency |
|---|---|---|---|---|
| **A0** | no event | **stable — 0 of 12 runs lose a channel** | n/a | n/a |
| **A1** | no event | 0 of 10 runs lose a channel post-CD-26; pre-CD-26, `z_max` reached 122 673 and two channels died | 244k–294k init → 196k–243k final | n/a |
| **A2** | rescaled at both events | **12 of 12 runs place their largest attenuation drop on a simplification boundary; 6 of 12 collapse outright** | n/a | n/a |
| **A3** | no event | 0 of 12 | n/a | *not yet computed* |
| **A4** | rescaled at both events | **0 of 3 collapse** (Curasao) — if this survives the remaining scenes it is the campaign's most interesting interaction | 292 707 init → 129 473 final | n/a |

Column 1 tests interaction candidate **IC-2**; column 2 tests whether the CD-6 re-warm-up
re-identifies `β` — **it does not** `[E.6]`. Column 3 disambiguates EDGS's opacity-masked
candidates from surviving primitives. Column 4 is the only available proxy for quantization
damage to the restoration output, which has no ground truth, and is **still not computed** —
the one diagnostic obligation of this table that remains open.

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
| Fewer Gaussians ⇒ faster rendering | **Asymptotic in `N`**, since rasterization is `O(Σ_tiles Gaussians-per-tile)` | ✅ and **confirmed sub-linear here** `[measured n=12]`: A2's 19.1× count reduction bought 2.65× fps, A1's 12.2× bought 1.83×. The prediction held; the exponent is not shared between cells. Mini-Splatting's own figure was 8.5× → 4.18× `[../mini-splatting/08-… §8.4]`. |
| VQ storage goes from `N·d` floats to `K_cb·d` floats + `N` indices | **Structural, true for `N ≫ K_cb`** | ✅ — but the *ratio* is capped by §8.2(1). `[../compact3d/08-… §8.4]` |
| EDGS's initialization is `O(num_refs × nns × H·W)`, **independent of the iteration count** | **Structural, and correctly not framed as an asymptotic win** | ✅ `[../EDGS/08-… §8.4]`. Here `num_refs = min(180, V) ≤ 29` (CD-2), so the constant is far smaller than in EDGS's own experiments — the initialization should be cheap. |
| "SeaSplat preserves the computational efficiency of 3DGS" | **Empirical, unnamed hardware, 4 scenes** | ⚠️ It is a **2×** regression on both train and render. Cite the numbers, not the adjective. `[../seasplat/08-… §8.5]` |
| **Combined-method efficiency claims for A0–A3** | **Measured** `[n=12 per cell]` | ✅ Claimable per scene, with dispersion, and with the A2 collapse covariate carried. See §8.3. |
| **Any A5–A7 efficiency claim, and any interaction term** | — | ❌ **Not yet measured.** S4 is partially complete (A4 on Curasao only); S5 has not run. Nothing may be claimed for the compound cells. |

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
