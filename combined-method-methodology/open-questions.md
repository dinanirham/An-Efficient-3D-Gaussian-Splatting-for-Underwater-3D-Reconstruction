# Open questions, gaps, and stop-condition findings

Recorded per the brief's Phase 0 stop condition: anything that could not be resolved inside
the pass's scope is reported here rather than filled in silently.

Each entry states **what is unknown**, **why it could not be resolved here**, **what it
blocks**, and **how to close it**.

---

## A. Scope-imposed gaps

### OQ-1 — The combined method's implementation is out of scope

**Unknown.** Whether an implementation of the combined method exists, what it does, and
whether any of the fourteen `[proposed integration]` decisions of
`06-implementation-deltas.md` §6.5 are already made there — differently or at all.

**Why unresolved.** The task brief excludes `seasplat-efficiency-adaptation/` and
`seasplat-efficient-3dgs-underwater/` entirely: "Do not open, list, or cite anything under
either path, even in passing." Both were excluded. Nothing in this folder derives from them.

**What it blocks.** `11-paper-vs-repo-disagreements.md` cannot be a paper-vs-repo table and
is instead a specification-vs-implementation risk register (§11.0). Every `[PI]` decision is
stated as *what would have to be done*, never as *what was done*.

**How to close.** Re-run §11 with those paths in scope. It is the first section to revisit.

### OQ-2 — No combined-method results exist anywhere in scope

**Unknown.** Every quality and efficiency figure for cells A1–A7.

**Why unresolved.** Phase 0 searched all of `my-research/` outside the excluded paths for
CSV, JSON, log, checkpoint, render, and output directories. **Nothing was found.** The only
`results/` directory in scope belongs to `../CompGS/` and holds that method's own artifacts.

**What it blocks.** Novelty claim **(b)** — a measured non-additive interaction effect — is
unavailable. `08-computational-profile.md` §8.0 states this and leaves every combined-method
cell as `NO RESULTS FOUND`.

**How to close.** Run the matrix (`10-reproducibility.md` §10.6). Minimum viable version:
**A0 vs A2 with `Ẑ`/`β` logging**, per `12-novelty-defensibility.md` §12.4 Fallback 1.

### OQ-3 — A stale memory pointer

**Finding.** A persistent note in this project's memory directs analysis to
`my-research/draft-thesis-output/drive-download-*.zip` as the location of an authoritative
20-row `master_metrics.csv`, and to the two excluded folders for an implementation audit and
a synthesised methodology chapter.

**Status.** `draft-thesis-output/` **does not exist** under `my-research/` — verified by
directory listing at the top level and by a recursive search for `*.zip` (the only zip in
scope is `dataset.zip`, 622 MB). The other two pointers are the excluded paths of OQ-1.

**What it blocks.** Nothing in this pass, which took no evidence from any of the three
locations. It is recorded because the note is misleading as written and should be corrected
or removed.

**How to close.** Locate or restore `draft-thesis-output/`, or update the memory note.

---

## B. Evidence-quality gaps in the sources

### OQ-4 — SeaSplat never reports Gaussian count or model size

**Unknown.** `N_rend` and on-disk size for the baseline, on these exact scenes.

**Why unresolved.** "Never reported in the paper; logged to TensorBoard only"
`[../seasplat/08-computational-profile.md §8.4]`, and no TensorBoard logs are in scope.

**What it blocks.** This is the **largest single practical gap**. `CD-5` sets the primitive
budget from A0's converged count; every compression and count ratio is normalised against it;
and the A4/A7 degeneracy check (`02-pipeline.md` §2.8) requires it. **The matrix cannot be
configured until A0 has been run and measured.**

**How to close.** Run A0 on all four scenes and log `total_points` at end of training —
checklist item 11 of `10-reproducibility.md` §10.6.

### OQ-5 — SeaSplat's hardware is unnamed

**Unknown.** The GPU behind SeaSplat's Table II (1 h 25 m train, 0.012 s render, 4.0 GB).

**Why unresolved.** The paper says only "a consistent set of hardware." Circumstantially, the
Dockerfile targets SM 8.6/8.9 with **SM 9.0 explicitly commented out**, suggesting a consumer
Ampere/Ada card `[../seasplat/08-…​ §8.2]` — suggestive, not conclusive. `[unverified]`

**What it blocks.** Any comparison of this work's timings against SeaSplat's published ones.
VRAM (an absolute footprint) transfers; wall-clock and FPS do not.

**How to close.** Re-measure A0 locally, or state explicitly that Table II is reproduced
as-published on unspecified hardware. Do not mix the two — it is "the single most likely
source of an unfair comparison in this project" `[../seasplat/08-…​ §8.2]`.

### OQ-6 — The three closest related works are known only from web fetches

**Unknown.** Whether the reported figures for **UW-3DGS** (27.604 PSNR / 0.868 SSIM /
0.134 LPIPS, ~48 min on a V100, floater ratio 1.3% vs 8.2%), **TUGS** (~20% of 3DGS
parameters, 21 MB, 106 FPS), and **GETA-3DGS** are accurate, and whether their methods are as
summarised.

**Why unresolved.** All three come from Phase 0 web searches and one arXiv HTML fetch. No
local PDF exists for any of them, and the summariser used for the fetch over-read at least
once — it described UW-3DGS's standard sparse COLMAP initialization as "dense
initialization," which is corrected in `01-taxonomy.md` §5. Every figure is `[unverified]`.

**What it blocks.** The prior-art gap of claim (a) rests on these three not occupying the
space. The *qualitative* distinctions (medium-field compression vs attribute compression;
uncertainty pruning vs budget pruning; tensorized primitives vs standard Gaussians) are
clear enough from abstracts to support the gap claim. The *numeric* comparisons are not
citable until the PDFs are obtained.

**How to close.** Download the three PDFs into `my-research/` and give each a
`research-methodology-output/` breakdown, at least for §1 and §8. **UW-3DGS is the priority**
— same domain, same four scenes.

### OQ-7 — CompGS-VQ's K-means initialisation is not known to be seeded

**Unknown.** How the codebook is initialised and whether that draw is seeded.

**Why unresolved.** `[../compact3d/11-paper-vs-repo-disagreements.md, "Unverifiable"]`
`[unverified]`.

**What it blocks.** Run-to-run variance of the *reported model size*, which is a headline
efficiency metric here. If the codebook init is unseeded, model size has dispersion that must
be reported.

**How to close.** Read `kmeans_quantize.py`'s initialisation path directly, or measure size
across three seeds of an A3 run.

### OQ-8 — EDGS Table 6's ablation direction is undetermined

**Unknown.** Whether EDGS's component ablation is leave-one-out or cumulative removal.

**Why unresolved.** "Row labels say 'w/o X' but the monotone ladder suggests cumulative
removal; the checkmark column survives neither `pdftotext -layout` nor `-raw`"
`[../EDGS/11-…​ D-14]` `[unverified]`.

**What it blocks.** Only the citation of EDGS's own component contributions in a related-work
paragraph. It does not affect this work's design, which is factorial.

**How to close.** Open `../EDGS.pdf` and look at Table 6 visually.

---

## C. Design questions this work raises and does not answer

### OQ-9 — Should `seathru_from_iter` change under dense initialization?

The baseline waits 10 000 iterations so `Ẑ` becomes meaningful before `β` is fitted to it,
and the process that makes it meaningful is 3DGS's adaptive density control — which M1
switches off (`01-taxonomy.md` A1-a). EDGS's own measurement that its Gaussians start ~50×
closer to their final positions argues the depth map stabilises far earlier, but **nothing
measures how many steps a dense-init model needs before its rendered depth is stable.**

The value is **kept at 10 000** so that A0 and A1 differ in exactly one factor
(`07-pseudocode.md` §7.1). This is a defensible choice for a factorial design and a possibly
wrong choice for the method. **A first-order follow-up**, and cheap: log per-frame `Ẑ`
variance across iterations in an A1 run.

### OQ-10 — How long must the post-simplification medium re-warm-up be?

CD-6 is the central `[proposed integration]` of this work, and its length is specified only
by analogy with SeaSplat's existing 1 000-step warm-up and 50-step bursts. **Whether `n`
steps suffice to re-identify `β` after a 60–90% prune is unknown and untested**
(`05-constraints.md` §5.5). It is itself a candidate for a nested ablation.

### OQ-11 — Should the medium model be fed mid-point depth instead of blended depth?

`05-constraints.md` §5.4 develops this at length and it is **the most promising single
follow-up in the whole document**: the baseline feeds its physical medium model an
alpha-normalised *blended* depth, which Mini-Splatting's Appendix C demonstrates to be
unidentified in exactly this regime — depth collapse against a dark background and
corruption by floaters are two of its three named artifacts, and both are underwater failure
modes SeaSplat exists to fix. Mini-Splatting's forked rasterizer already computes the
better-posed alternative (`out_pts`, the ray/ellipsoid mid-point of the argmax Gaussian) as a
by-product, and reinitializing from blended rather than mid-point depth cost that paper
**9.87 dB**.

It is **deliberately not adopted** (CD-14): changing it would alter what `β` is fitted to in
*every* cell including A0, so A0 would no longer be SeaSplat-as-published and the matrix
would lose its reference point. It is the obvious second study.

### OQ-12 — What is the right importance metric for a scattering medium?

Mini-Splatting's `--imp_metric` is required, has no default, and offers only `indoor` and
`outdoor`; the paper itself calls it "case-dependent and hand-crafted … an experimental
trick." `outdoor`'s projected-area normalisation exists to suppress **sky**
(`01-taxonomy.md` A2-a). Underwater far fields are systematically low-contrast but are
*scene*, not sky. **A medium-aware importance — weighting by `Â`, so that heavily-attenuated
primitives are not penalised twice — is identified as available in principle** (the baseline
already computes `Â` per pixel) **and is not implemented.** Whichever metric is used must be
justified, not defaulted.

### OQ-13 — Should the SfM points be kept under M1?

EDGS deletes the COLMAP points after initialization (`add_SfM_init = False`). In this domain
they are the only geometry **not** derived from a matcher with a documented failure mode in
water, and M1 leaves no mechanism to add primitives later (`01-taxonomy.md` A1-b). Flipping
the flag is a one-line change and a legitimate sensitivity check.

### OQ-14 — Can correspondences be extracted on a backscatter-removed image?

The cleanest fix for matcher hallucination in the water column would be to match on `I − B̂`
rather than `I`. **It is not implementable at initialization time**, because `B̂` does not
exist until the medium model has been trained. That is itself a finding
(`01-taxonomy.md` A1-b) and it suggests a two-pass variant — initialize, train to
`seathru_from_iter`, then re-initialize from backscatter-removed correspondences — which is
outside this work's scope and is a plausible follow-up method in its own right.

---

## D. Data questions

### OQ-15 — A minor image-count discrepancy in the dataset

SeaThru-NeRF's paper states "a total of **20, 20 and 18** images respectively" for three
scenes, and the arithmetic checks against `llffhold = 8`
`[../seathru_NeRF/10-reproducibility.md §10.2]`. The local copy holds:

| Scene | Images on disk | Directory name |
|---|---|---|
| Curasao | **21** | `images_wb/` |
| IUI3-RedSea | **29** | **`Images_wb/`** ← capital I |
| JapaneseGradens-RedSea | 20 | `images_wb/` |
| Panama | 18 | `images_wb/` |

Two observations. **(i)** Curasao has 21, not 20 — a one-frame discrepancy against the paper's
count, unexplained. It changes the test split from `{0,8,16}` to `{0,8,16}` (still 3 frames,
since 21 → indices 0–20), so it is probably harmless, but it should be confirmed rather than
assumed. **(ii)** `IUI3-RedSea` is not among the three scenes the paper enumerates and has
29 images; it is the fourth scene SeaSplat evaluates on. **(iii)** The capital-I directory
name will silently break a hard-coded path on a case-sensitive filesystem
(`10-reproducibility.md` §10.2).

**How to close.** Compare the local `sparse/0/images.bin` frame list against the paper's
count for Curasao; normalise the directory name or make the loader case-insensitive.

### OQ-16 — Is the four-scene dataset sufficient for the claims?

Four scenes, 88 images total, from three geographic locations (Caribbean, Red Sea, Panama).
Every efficiency claim is therefore averaged over four points. `../seasplat/10-…​` §10.1
already notes that the baseline's own ablation differences (≤0.5 dB) are not demonstrated to
exceed run-to-run noise on this data. **This bounds external validity and is stated as such
in `chapter/08-scope-and-limitations.md`**; it is listed here because the obvious remedy —
adding scenes from UWBundle, SeaSplat's SaltPond capture, or the SimWater/SimFog synthetic
sets — is available and was not pursued in this pass.

---

## E. Stop-condition assessment

The brief's stop condition: report rather than fill silently if (i) any expected breakdown is
missing or incomplete, or (ii) the literature scan surfaces a method already occupying the
novelty space.

| Condition | Assessment |
|---|---|
| **(i) Missing or incomplete breakdowns** | ❌ **Not triggered.** All nine folders that carry a `research-methodology-output/` have the complete 12-file set (`00-index` … `11-paper-vs-repo-disagreements`), none truncated. Four folders — `colmap/`, `gaussian-splatting/`, `nerf/`, `dataset/` — have no breakdown, but none is a composition member; `gaussian-splatting/` is the substrate, adequately documented through the four members' own §1 files. |
| **(ii) Occupied novelty space** | ❌ **Not triggered, but narrowly.** **UW-3DGS** is the closest and combines a physical underwater formation model with pruning and a compressed medium representation on the same four scenes. It does *not* occupy this space: its pruning targets floaters by uncertainty rather than a primitive budget, its compression targets the *medium field* rather than Gaussian attributes, and its initialization is standard sparse COLMAP. The distinction is real but should be argued explicitly in the related-work section, not assumed. Its figures remain `[unverified]` pending OQ-6. |
| **Additional finding** | ⚠️ **Claim (b) is unavailable** for a reason that is *not* a stop condition but is reported with equal prominence: no combined-method measurements exist in scope (OQ-2). The brief's instruction — "state honestly that current evidence doesn't yet support one" rather than overclaim — is applied to (b) specifically, while (a) and (c) are claimed. |
