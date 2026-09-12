# §10 — Reproducibility and protocol consistency

## 10.1 Seed handling — four sources, four different disciplines

| Source | Seed discipline | Consequence for this work |
|---|---|---|
| **SeaSplat** | `--seed` defaults to **`-1` → OS entropy**. Every run differs. Even with `--seed`, **`torch.cuda.manual_seed_all` is never called**; `cudnn.deterministic` and `use_deterministic_algorithms` are not set. No seed, repeat count, or variance appears anywhere in the paper `[../seasplat/10-reproducibility.md §10.1]` | ❌ **The baseline is non-deterministic by default.** This must be fixed before the matrix is run. |
| **EDGS** | `seed: 228` in `configs/train.yaml`, **undocumented** in the README `[../EDGS/03-variables.md]` | ⚠️ a seed exists but is not surfaced |
| **Mini-Splatting** | `random/np/torch` hard-coded to **0**, no CLI, no `cuda.manual_seed_all` `[../mini-splatting/11-…​ D-12]` | ⚠️ **and it does not help**: the two decisive steps are `np.random.choice` fed by **GPU-computed** probabilities, so `N_rend` after simplification **remains run-dependent even at a fixed seed** |
| **CompGS-VQ** | inherits 3DGS's `safe_state` hard-coded seed 0 via the file overlay; the **K-means initialisation scheme is not obviously seeded** `[../compact3d/11-…​, "Unverifiable"]` | ⚠️ `[unverified]` — bears directly on run-to-run variance of the reported model size |

### Random draws a seed would have to control in the combined method

`[inferred: assembled from all four folders' §10 and §3]`

| Draw | Source | Affects |
|---|---|---|
| `β_bs ← U(0,1)³`, `B^∞ ← U(0,1)³` | SS `[repo: models.py:54,61]` | the medium model's starting point — and D-1 is a *global optimum* of `L_GS`, so the start matters |
| `bg ← U(0,1)³` (before being overwritten with the fixed prior) | SS `[repo: train.py:126-129]` | via `bg_from_bs`, the warm start for `B^∞` |
| camera shuffle + per-iteration view sample | SS `[repo: scene/__init__.py; train.py:198]` | all |
| k-means over camera poses for reference selection | ED `[repo: corr_init.py:65-97]` | which views are references — **more consequential here**, since `K_ref = min(180, V)` is a large fraction of all views (CD-2) |
| RoMa's internal sampling at `M_match.sample(...)` | ED `[repo: corr_init.py:622]` | which correspondences become Gaussians |
| `np.random.choice(N, n_bud, p=P, replace=False)` | MS `[repo: ms/train.py:240]` | **which primitives survive — and therefore the exact `N_rend`** |
| K-means centroid initialisation | VQ `[unverified]` | the codebook, hence the model size |

> **`[PI]` The reproducibility floor for this study.** Every cell must be run with an explicit
> seed; `safe_state` must be patched to call `torch.cuda.manual_seed_all(k)`; and the run
> must **dump its fully-resolved configuration** (CD-1) plus the realised `N_rend`,
> `K_ref`, and codebook sizes to the output directory. Even then, bit-exact reproduction is
> not achievable: `diff-gaussian-rasterization` uses **atomic adds in the backward pass**,
> which are non-deterministic in floating point regardless of seeding
> `[../seasplat/10-reproducibility.md §10.1]`. The correct response is not to chase
> determinism but to **report dispersion** — §10.4.
>
> **Measured, and larger than assumed.** Three repetitions of both this implementation and
> unmodified SeaSplat give a ~21% spread in converged primitive count on Curasao — the same
> for an implementation that seeds host *and* device generators as for one that seeds
> neither, so seeding is not the operative variable. Across all four scenes the coefficient
> of variation ranges from **6.0% to 29.3%** `[08-computational-profile.md §8.2b]`. The
> mechanism is amplification: a primitive lands either side of `densify_grad_threshold` from
> run to run, changing the population that feeds the next densification event, 144 times over.
>
> **A single-run ratio on primitive count therefore carries no information.** This was
> established the expensive way — four hypotheses about a 6× discrepancy were tested against
> single pairs before the spread was measured, and one paired comparison showed 0.68× between
> two configurations later shown indistinguishable at n=3.

---

## 10.2 Train/test split — consistent across sources, with two traps

**The rule is the same everywhere in the 3DGS lineage:** every 8th frame held out by index
order after filename sort (`llffhold = 8`, 12.5% test).

| Source | Split | Note |
|---|---|---|
| SeaSplat | `idx % 8 != 0` train / `== 0` test | `llffhold` is a Python default with **no `add_argument`** — not overridable from the CLI `[../seasplat/10-…​ §10.2]` |
| SeaThru-NeRF | identical rule, `llffhold: int = 8` | paper and code agree exactly, and the arithmetic checks: "20, 20 and 18 images … three set aside for validation in each set" → `{0,8,16}` = 3 ✅ `[../seathru_NeRF/10-…​ §10.2]` |
| Mini-Splatting | "identical processing details … as specified in the official implementation of 3DGS"; README commands **do** include `--eval` ✅ | |
| CompGS-VQ | inherits `llffhold = 8` via the file overlay | |
| EDGS | same rule in principle | ❌ `dataset.eval: false` **and** `"eval": False` hard-coded into `cfg_args` |

✅ **The good news, and it is load-bearing:** because SeaSplat evaluates on the *same*
SeaThru-NeRF scenes with the *same* `llffhold = 8` rule, **the held-out frames coincide with
SeaThru-NeRF's**, so the splits are directly comparable
`[../seathru_NeRF/10-reproducibility.md §10.2]`. Any published number on these four scenes
that used the standard harness is on the same frames as this work's.

⚠️ **Trap 1 — `--eval` defaults off in two of the four sources.** SeaSplat's `eval` defaults
`False` and its README command omits it, so the test set is **empty and every frame is
trained on** `[../seasplat/11-…​ D-17]`; EDGS has the same defect independently
`[../EDGS/11-…​ D-12]`. `[PI]` The run script must pass `--eval` and **assert a non-empty
test set at startup**, then log `|train|` and `|test|` per scene.

⚠️ **Trap 2 — the split is index-based, and the local dataset has a case-sensitivity
inconsistency.** Three scenes use `images_wb/`; `IUI3-RedSea` uses **`Images_wb/`** (capital
I), verified on disk. On a case-sensitive filesystem a hard-coded `images_wb` path silently
fails for that scene. `[inferred: directory listing of ../dataset/SeathruNeRF_dataset/]`

---

## 10.3 Exact metric computation — the standardisation this work must impose

This is the item the source methodology singles out as varying silently across underwater
papers, and it varies across **all four** of this work's sources.

### 10.3a — Masking: **none, in every source**

No sky mask, no water-column mask, no alpha mask, no valid-depth mask at metric time —
full-frame, every pixel of every test frame. SeaSplat has a `depth_alpha_threshold = 0.5`
but it is used **only** for TensorBoard depth visualisation, never for PSNR/SSIM/LPIPS
`[../seasplat/10-…​ §10.3a]`. SeaThru-NeRF likewise `[../seathru_NeRF/10-…​ §10.3c]`.

> ⚠️ **SeaThru-NeRF's Table 2 "red square" rows are a *zoomed crop* of a far-field region**,
> not a mask — and the gap between crop and full-frame is up to **12 dB** on the same scene
> (21.83 vs 33.80 on Red Sea). They must never be quoted as full-frame numbers
> `[../seathru_NeRF/10-…​ §10.3c]`.

### 10.3b — What is scored: `Î` vs `I`, never `Ĵ`

The restored medium-free output is **never scored** in either underwater method — SeaSplat's
`Ĵ` and SeaThru-NeRF's `J` are both unsupervised outputs with no ground truth, "unobtainable
without draining the ocean" `[../seasplat/10-…​ §10.3b]`; SeaThru-NeRF's is literally
`stop_gradient(...)` `[../seathru_NeRF/10-…​ §10.3d]`. All restoration comparisons in both
papers are qualitative.

**This is the structural reason restoration quality is a *secondary* metric in this work**
and why quantization damage to `Ĵ` needs a self-consistency proxy (`01-taxonomy.md` A3-b,
`08-computational-profile.md` Table 8.3c).

### 10.3c — PSNR formula — three conventions

Covered in full in `09-glossary.md` §9.4. `[PI]` **This work reports both `PSNR_perchan` and
`PSNR_pooled`, each labelled, at every evaluation** (implemented in
`utils/metrics_conventions.py`; tested in `tools/verify_metrics.py`).

> ⚠️ **CORRECTION 2026-08-28 — this section previously attributed the per-channel convention
> to SeaSplat's *reported* numbers, and that is wrong.** `utils/image_utils.py:psnr` reduces
> with `.view(img.shape[0], -1)`, so **its convention is decided by the shape it is handed**,
> and the repository hands it both: the in-training report passes `(3,H,W)` → per-channel,
> while the disk-based evaluation that writes `eval_metrics.json` passes `(1,3,H,W)` (because
> `metrics.py:readImages` does `.unsqueeze(0)`) → **pooled MSE**. Measured: the same function
> returns **27.881 dB** from `(3,H,W)` and **16.068 dB** from `(1,3,H,W)` on one synthetic
> pair with underwater-like channel divergence — 11.8 dB from input shape alone
> `[implementation/tools/verify_metrics.py T4, executed]`.
>
> **Consequence.** The figure a paper would quote is the *stricter* pooled one, not the
> inflated per-channel one. The claim below — that SeaSplat's Table I comparison against
> SeaThru-NeRF is biased in SeaSplat's favour by its PSNR convention — therefore **does not
> hold if both used pooled MSE**, and which path produced SeaSplat's published numbers is
> recorded nowhere. Treat that comparability argument as open, not established.

### 10.3d — Data path — the 8-bit disk round-trip

SeaSplat computes metrics **not** on in-memory float tensors but by writing renders to disk
and re-opening them, in **JPEG** whenever the GT directory holds no PNGs
`[../seasplat/10-…​ §10.3d]`. Mini-Splatting's `ms/` scores float tensors in memory — cleaner
— while its `ms_c/` scores 8-bit PNGs from disk `[../mini-splatting/11-…​ D-14]`.

✅ **Good news, verified on disk:** the local dataset's `images_wb/` contain **`.png`** files
in all four scenes. The JPEG fallback should therefore **not** trigger. `[inferred: directory
listing]` `[PI]` The run must nonetheless **log whether it wrote JPEG or PNG**, because the
fallback is silent and file-format-dependent.

⚠️ 8-bit quantisation of both render and GT still occurs. SeaThru-NeRF, by contrast, scores
**linear, pre-photofinishing** images — "PSNR is calculated on the original non-photofinished
linear images" `[../seathru_NeRF/10-…​ §10.3b]`. **PSNR on linear data and PSNR on 8-bit
sRGB-ish data are not the same quantity**, and this is a *second, independent* axis on which
the two papers' numbers are not interchangeable.

### 10.3e — SSIM and LPIPS

SSIM: 11×11 Gaussian window, σ = 1.5, `C1 = 0.01²`, `C2 = 0.03²` — standard 3DGS
implementation `[../seasplat/10-…​ §10.3e]`. LPIPS: **VGG** backbone
`[repo: train.py:644]`. ⚠️ VGG-LPIPS and AlexNet-LPIPS give systematically different values
and SeaSplat's paper does not state which it used; SeaThru-NeRF states neither window nor
backbone `[../seathru_NeRF/10-…​ §10.3e]`. `[PI]` **Report the backbone.**

### 10.3f — Aggregation

Per-image metrics → mean over the split → per scene; then an **unweighted mean of the four
per-scene means**, not an image-weighted one `[../seasplat/10-…​ §10.3f]`. `[PI]` Since the
scenes have unequal frame counts (21, 29, 20, 18 — see §10.6), **report both** the unweighted
scene mean and the image-weighted mean; they will differ, and stating which is used removes
an easy source of disagreement.

---

## 10.4 Statistical treatment — and the framing the brief requires

### Additive vs leave-one-out: stated explicitly

**This work's design is a 2³ FACTORIAL matrix. It is neither a cumulative-additive ladder
nor a leave-one-out ablation.** Every cell A0–A7 is a complete configuration; the effect of
a mechanism is estimated as a *contrast* between cells, and both directions are available:

- **Additive-style contrast (main effect from below):** `A1 − A0`, `A2 − A0`, `A3 − A0`.
- **Leave-one-out contrast (main effect from above):** `A7 − A6` (removing M1),
  `A7 − A5` (removing M2), `A7 − A4` (removing M3).
- **Interaction:** the difference between the two, e.g. `(A4 − A0) − [(A1 − A0) + (A2 − A0)]`.

**A factorial design supports both readings; a ladder supports only one.** That is the
reason for the design, and it is a direct response to a hazard documented in three of the
four sources:

| Source | Its ablation structure | The trap |
|---|---|---|
| SeaSplat Tab. III | **cumulative-additive** | "You may **not** say 'removing BS costs 0.47 dB'." And **row 9 ≠ row 8** — the ladder does not enumerate the full objective `[../seasplat/04-loss.md §4.4]` |
| Mini-Splatting | **three different kinds** called "ablation": Tab. 3 cumulative-additive, Tab. 4 mutually-exclusive variants, Fig. 10 a curve family. **None is leave-one-out** `[../mini-splatting/11-…​ D-15]` | |
| EDGS | **four different kinds**; Tab. 6's **direction is ambiguous** — labels say leave-one-out, the monotone ladder suggests cumulative removal, and the checkmark column survives neither `pdftotext -layout` nor `-raw` `[../EDGS/11-…​ D-14]` | |
| CompGS-VQ Tab. 1 | **variants, not an ablation ladder** — 16K vs 32K differ only in codebook size; BitQ is post-training on top of 32K `[../compact3d/11-…​]` | |

`../comparison-glossary.md` §3.4 tabulates this across all nine folders and concludes that
four distinct structures are in circulation, with one ambiguous. **Declaring the structure
up front, in the methodology chapter rather than a table caption, is a small contribution in
its own right.**

### Dispersion

**No source reports error bars.** SeaSplat's Table III differences are ≤0.5 dB with no
dispersion and a random default seed, so "the sub-0.5 dB differences between ablation rows
(27.13 vs 27.11 vs 26.64) are **not demonstrated to exceed run-to-run noise**"
`[../seasplat/10-…​ §10.1]`. SeaThru-NeRF is deterministic by construction but still reports
single runs, with a 0.07 dB headline margin `[../seathru_NeRF/10-…​ §10.1]`.

`[PI]` **This work runs ≥3 seeds per cell per scene and reports mean ± standard deviation.**
With 8 cells × 4 scenes × 3 seeds = **96 training runs**, this is the dominant cost of the
study and it must be budgeted for, not discovered. It is also non-negotiable: the interaction
terms of `08-computational-profile.md` §8.4 are differences of differences, so they carry
roughly twice the variance of a main effect. Claiming an interaction without dispersion would
repeat exactly the error the four sources make.

⚠️ **One variance source cannot be removed by seeding.** Mini-Splatting's `np.random.choice`
is fed by GPU-computed probabilities, so `N_rend` after simplification is run-dependent even
at a fixed seed `[../mini-splatting/11-…​ D-12]`. `[PI]` **Report the realised `N_rend` per
run, not the target `n_bud`**, and report its dispersion — a budget that lands at
±5% is a different experiment from one that lands exactly.

---

## 10.5 Protocol consistency across sources — summary

| Protocol element | SeaSplat | Mini-Splatting | CompGS-VQ | EDGS | Consistent? |
|---|---|---|---|---|---|
| Iteration budget | 30 000 (≈43 000 steps) | 30 000 | 30 000 | 30 000 | ✅ nominally; ❌ in effective steps |
| `λ_dssim` | 0.2 | 0.2 | 0.2 | 0.2 | ✅ **the one universally shared constant** `[../comparison-glossary.md §1.5]` |
| Split rule | `llffhold = 8` | 3DGS default | 3DGS default | 3DGS default | ✅ |
| `--eval` default | ❌ off | ✅ on in README | ✅ inherited | ❌ off + hard-coded | ⚠️ |
| `sh_degree` | **0** | 0 until 15 K, then 3 | 3 | 3 | ❌ — and SeaSplat's 0 is fixed throughout |
| Metric data path | 8-bit from disk | float in memory (`ms/`) | 3DGS harness | own harness | ❌ |
| PSNR convention | per-channel mean | inherited | inherited | pooled (by accident) | ❌ |
| Seeding | random by default | 0, hard-coded | 0, inherited | 228, in config | ❌ |
| Hardware named | ❌ **none** | ✅ RTX 3090 | ✅ RTX 6000 | ✅ A100 | ❌ |
| Reported `#G` semantics | not reported at all | rendered Gaussians | rendered Gaussians | rendered Gaussians | ⚠️ baseline gap |

**Three of these rows are the reason this work must re-measure rather than cite.** Metric
data path, PSNR convention, and hardware are all inconsistent across the sources, and
SeaSplat — the baseline — does not report Gaussian count or model size at all
`[../seasplat/08-…​ §8.4]`. **Every efficiency number in this study is therefore a
measurement obligation, not a lookup.**

---

## 10.6 Reproduction checklist

Assembled from the four sources' own checklists, deduplicated, with the combination-specific
items marked `[PI]`.

| # | Action | Why |
|---|---|---|
| 1 | Pass `--eval`; **assert a non-empty test set**; log `\|train\|`, `\|test\|` per scene | two sources default it off (§10.2) |
| 2 | Pass `--seed k` **and patch `safe_state` to call `torch.cuda.manual_seed_all(k)`** | CUDA RNG is unseeded even with `--seed` `[../seasplat/10-…​]` |
| 3 | Run **≥3 seeds per cell per scene**; report mean ± sd | no source reports dispersion; interaction terms carry double variance (§10.4) |
| 4 | Rebuild the CUDA extensions for the target architecture (`TORCH_CUDA_ARCH_LIST` must include the target SM) | SeaSplat's Dockerfile targets SM 8.6/8.9 with 9.0 **commented out**; Mini-Splatting ships CUDA 11.6 `[../seasplat/08-…​ §8.2; ../mini-splatting/08-…​ §8.2]` |
| 5 | **`[PI]`** Build **one** environment (CUDA 12, Python ≥3.10) with Mini-Splatting's forked rasterizer back-ported and CompGS-VQ's four method files overlaid | the four stacks cannot coexist as published (`08-computational-profile.md` §8.6) |
| 6 | Handle the `Images_wb` / `images_wb` case inconsistency for `IUI3-RedSea` | verified on disk (§10.2) |
| 7 | Confirm renders are written as **PNG**, not JPEG, and log which | the fallback is silent `[../seasplat/10-…​ §10.3d]`; local GT is PNG, so it should not fire |
| 8 | Standardise on **one** PSNR convention and report **both** values | three conventions across four sources (§10.3c) |
| 9 | **`[PI]`** Add a config layer above SeaSplat's argument parser (CD-1) and **dump the fully-resolved config** per run | ~12 booleans default `True` with `action="store_true"` and cannot be disabled from the CLI `[../seasplat/11-…​ D-12]` |
| 10 | **Record effective optimizer steps**, not the nominal iteration count | `continue` bypasses `iteration += 1`; CD-6's bursts add more (§10.5) |
| 11 | Log `N_rend` at end of training — and at **five** points: post-init, post-settling, at 15 K pre/post, at 20 K pre/post | SeaSplat never reports it; EDGS's opacity-masked candidates inflate the post-init count; M2's realised count is stochastic |
| 12 | **`[PI]`** Log `Ẑ_min`, `Ẑ_max`, and the nine medium scalars at every save iteration (CD-12) | converts interaction candidates IC-2 and the medium-absorption hypothesis into measurements at zero cost |
| 13 | **`[PI]`** Assert that each enabled mechanism actually **fired** | both EDGS (`gs_epochs = 0`) and CompGS-VQ (`kmeans_st_iter = 30000`) are **silent no-ops** at their CLI defaults `[../EDGS/03-variables.md; ../compact3d/11-…​ D-6]` |
| 14 | ✅ **DONE.** Preflight refuses any M1+M2 run whose budget cannot bind, reading the count from the cloud's PLY header; all four clouds clear `n_bud = 200 000` `[measured]` | otherwise a null interaction result is an artifact of configuration (`02-pipeline.md` §2.8) |
| 14b | **`[PI]`** Report dispersion **per scene**, never pooled | measured CVs differ by 5×: JapaneseGardens 6.0%, Panama 29.3% (`08-computational-profile.md` §8.2b). A pooled figure would understate the weak scenes and overstate the strong |
| 14c | **`[PI]`** Record `render_fps`, `render_ms_per_frame` and peak render memory (CD-24) | frame rate is the one efficiency measure all three mechanisms affect, and two stated predictions rest on it; it was not instrumented until the campaign had begun |
| 14d | **`[PI]`** Record the **geometric extent protocol** from each stored model: full and opacity-gated bounding boxes (gate at α ≥ 0.05), per-axis inflation against the 1st–99th percentile box, occupancy on a fixed 64³ grid, and radial concentration and spread about the median primitive `[repo: tools/spatial_extent.py]` | it detects two failure modes no photometric metric registers — detached rendered clusters and diffuse invisible halos — and the opacity gate separates them, which a single extent figure cannot. **Report it as a direct instrument, never as a proxy for medium identifiability**: that correlation was tested and came out the wrong sign (ρ = −0.40), recorded as a negative result `[E.17]` |
| 14e | **`[PI]`** State whether any primitive-count reduction is **raw or opacity-gated** | the two differ by roughly 3× on this corpus — 19× raw against ~7× gated — because the untreated baseline is only ~36% rendered while the simplified model is ~93%. Both are honest; an unlabelled ratio is not interpretable |
| 15 | Report the aggregation rule (unweighted scene mean vs image-weighted) and give both | scene frame counts are unequal: 21 / 29 / 20 / 18 |
| 16 | State the LPIPS backbone (VGG) explicitly | no source states it in text (§10.3e) |
