# Chapter IV — table, figure and image manifest

Companion to `chapter-04-specification.md` (Rev. 3). Every table and figure the
chapter will carry, numbered, placed, and traced to the data or the render that
produces it.

**Status key**
`READY` — derivable now from a committed analysis artifact, and already
reported in `FINDINGS.md`.
`DERIVE` — the data exist in a committed artifact but the quantity is **not yet
in `FINDINGS.md`**. Per the chapter's own rule, it must be added to the
analysis first and then cited; it may not be computed in the chapter.
`RENDER` — requires re-rendering from stored checkpoints. Seed-0 checkpoints
are retained, so this is a rendering pass, not a retrain.
`PLOT` — a new plot over committed data; no rendering required.

---

## 1. Tables

| No. | Title | § | Columns / content | Source | Status |
|---|---|---|---|---|---|
| 4.1 | Scope of the completed campaign | 4.1.1 | Configurations, scenes, repeats, runs, iterations, effective optimizer steps, accelerator, GPU-hours, window | `run_ledger.json`, §0 | READY |
| 4.2 | Repeat dispersion of the baseline, per scene | 4.1.3 | PSNR sd, LPIPS sd, count CV; implied resolution threshold per metric | `_noise_floor.json`, §0 | READY |
| 4.3 | Provenance and integrity summary | 4.1.4 | Ledger completeness, retries and cause, commit-column status, what the one-version claim rests on | `run_ledger.json`, §0 | READY |
| 4.4 | Equivalence of the baseline to the unmodified reference | 4.2.1 | Per scene: ΔPSNR, ΔLPIPS, Δcount, fraction of count margin used, verdict | `check_margin.txt`, §1 | READY |
| 4.5 | Baseline reconstruction fidelity and efficiency, per scene | 4.2.2 | PSNR, SSIM, LPIPS, primitives, render rate, training time | `results_by_scene.csv`, §2 | READY |
| 4.6 | **Learned medium parameters, per scene** | 4.2.4 | β_att (r, g, b), B∞ (r, g, b), spectral ordering, for A0 and SS | `results_runs.csv` | **DERIVE** |
| 4.7 | Representation characteristics of the baseline | 4.2.6 | Visible fraction, bounding-box inflation, occupancy; A0 seed 0 and SS three repeats | `spatial_extent.csv`, §9 | READY |
| 4.8 | Effect of deterministic initialisation (M1) | 4.3.1–4.3.2 | Per scene: ΔPSNR, ΔSSIM, ΔLPIPS, count ratio, training-time ratio, each with z | `results_by_scene.csv`, §2 | READY |
| 4.9 | Effect of spatial reorganisation (M2) | 4.4.1–4.4.2 | Per scene: ΔPSNR, ΔSSIM, ΔLPIPS, count ratio, render-rate ratio, each with z | §2 | READY |
| 4.10 | Effect of attribute-level quantisation (M3) | 4.5.1–4.5.2 | Per scene: ΔPSNR, ΔSSIM, ΔLPIPS, bytes per primitive, compression ratio, render-rate ratio | §2 | READY |
| 4.11 | Two-way interaction terms | 4.6.2–4.6.4 | Per scene per pair: LPIPS term with z, count log-ratio with z; PSNR column marked undetermined | `analysis_unweighted.json`, §3 | READY |
| 4.12 | Three-way interaction term | 4.6.5 | Per scene: LPIPS and count, with z | §4 | READY |
| 4.13 | Non-dominated configurations, per scene | 4.6.6 | Fronts on count × LPIPS, bytes × LPIPS, count × PSNR | §7 | READY |
| 4.14 | Medium-model collapse incidence | 4.7.1 | Per cell per scene: runs retaining all channels, of three; channel lost; iteration of largest attenuation drop | `medium_collapse.json`, §5a | READY |
| 4.15 | Final representation size versus collapse | 4.7.2 | A2 and A4 final count per scene with sd, and collapse count for each | §5d | READY |
| 4.16 | Dispersion ratio by outcome stratum | 4.7.3 | Collapsed and intact strata: n, min, median, max ratio; U, AUC, exact one-sided p | §5b | READY |
| 4.17 | Cut magnitude and medium state, by configuration group | 4.7.4 | Entering count, fraction removed, entering β̄, post-burst β̄ as a fraction, collapses | diagnostics CSVs, §5 | READY |
| 4.18 | Fidelity by collapse stratum, within cell and scene | 4.8.1 | Per cell × scene: n collapsed / intact, ΔPSNR and ΔLPIPS in baseline sd units, β_att,b of each stratum | §8 | READY |
| 4.19 | Restored-image consistency under quantisation | 4.8.2 | Per run: Ĵ gap, Î-versus-truth from each attribute state, in-medium loss, verdict | `j_consistency.json`, §10 | READY |
| 4.20 | Effect of gradient detachment (A0D) | 4.9.2 | Per scene: count ratio, training-time ratio, render-rate ratio, peak-memory ratio, ΔPSNR, ΔLPIPS, collapse | §6 | READY |
| 4.21 | Replication against the archived campaign | 4.10 | Per cell × scene: ΔPSNR with z, ΔLPIPS with z, count ratio; replication verdict | §11 | READY |
| 4.22 | Alignment of research questions with evidence | 4.11.1 | RQ, answer, evidence section, resolution, boundary | all | READY |
| 4.23 | Summary of limitations and their consequences | 4.12 | Limitation, type, consequence for claims, where addressed | §14 | READY |

**23 tables.** Tables 4.1 and 4.3 may be merged if the chapter runs long;
everything else is load-bearing.

---

## 2. Figures

| No. | Title | § | Content | Source | Status |
|---|---|---|---|---|---|
| 4.1 | Resolvable effect size against observed effect size | 4.1.3 | Per scene, the 2 SE threshold for main, two-way and three-way contrasts, with the observed main effects overlaid. Shows graphically why PSNR interactions are undetermined | `_noise_floor.json`, §0 | PLOT |
| 4.2 | Baseline and reference against ground truth | 4.2.1, 4.2.3 | Four scenes × (ground truth, SS render, A0 render), with one far-field and one near-field crop per scene. The reference panel is what makes the equivalence claim visible rather than tabular | checkpoints | RENDER |
| 4.3 | **Learned attenuation spectra, per scene** | 4.2.4 | β_att by channel for each scene, A0 and SS side by side; physical ordering marked; the inverted scene highlighted | `results_runs.csv` | **DERIVE + PLOT** |
| 4.4 | Medium decomposition of a held-out view | 4.2.5 | One view per scene: composed image Î, restored image Ĵ, attenuation map, backscatter map | checkpoints | RENDER |
| 4.5 | The invisible population | 4.2.6 | Point cloud coloured by visibility, one scene; and the same view rendered with sub-threshold primitives removed, showing no visible difference | checkpoints | RENDER |
| 4.6 | Initialisation: input cloud and reconstruction | 4.3.4 | Sparse SfM cloud versus dense correspondence cloud; A0 and A1 renders at the same view and crop | checkpoints, `dataset/` | RENDER |
| 4.7 | Simplification: characteristic artefacts | 4.4.4 | A0 and A2 at the same view and crop, on the scene with the largest LPIPS cost; texture loss visible | checkpoints | RENDER |
| 4.8 | Quantisation: far-field behaviour | 4.5.4, 4.5.7 | A0 and A3 far-field crop; and the same crop of the restored image, where the difference is larger | checkpoints | RENDER |
| 4.9 | Operating points, per scene | 4.6.6 | 2 × 4 panel: count × LPIPS and bytes × LPIPS, one panel per scene, nine cells marked, non-dominated set connected | `results_by_scene.csv`, §7 | PLOT |
| 4.10 | Attenuation trajectory through the simplification events | 4.7.4 | β_att per channel against iteration for one collapsed and one intact run of the same cell and scene; both events and both bursts marked. Supersedes the exploratory `h4_*` plots, which show one channel and one run | diagnostics CSVs | PLOT |
| 4.11 | Dispersion ratio by outcome | 4.7.3 | The two strata as a strip or dot plot, showing the overlap that refutes the registered explanation; the four initialisation runs with ratios of 3.5–7.3 and no collapse marked | `medium_collapse.json`, §5b | PLOT |
| 4.12 | Fraction removed against attenuation loss | 4.7.4 | One point per run at each event, all 48 simplification runs, collapsed runs marked; the two groups separate on the x-axis | diagnostics CSVs, §5 | PLOT |
| 4.13 | A collapsed medium, visually | 4.7.6 | Same cell, scene and view: attenuation map and restored image for a collapsed and an intact run. The composed images look alike; the restorations do not | checkpoints | RENDER |
| 4.14 | Restored image under both attribute states | 4.8.2 | Ĵ from the continuous and the codebook state, plus their difference map, for one quantised run | checkpoints | RENDER |

**20 figures.** Thirteen are plots or derivations over committed data and are
built; seven require rendering.

### Added after review

Six figures added on review, each answering a question the earlier set left to
prose. All are generated by `figures/make_chapter4_figures.py` and need no
checkpoints.

| No. | Title | § | Why it was added | Status |
|---|---|---|---|---|
| 4.15 | Main effects with two-standard-error intervals | 4.3–4.5 | Three tables carried the central result; a reader could not see which effects clear the threshold | PLOT |
| 4.16 | Interaction plots | 4.6.2–4.6.4 | A factorial study with no interaction plot is conspicuous; parallel lines would mean additivity, and they are not parallel | PLOT |
| 4.17 | Primitive population through training | 4.1.1, 4.6.3 | Nothing showed *when* each mechanism acts, or the budget binding | PLOT |
| 4.18 | Frame rate against population, log–log | 4.4.2, 4.5.2 | The sub-linear claim with a scene-dependent exponent had no visual support. Fitted slopes −0.11 to −0.28 against −1 for inverse proportionality | PLOT |
| 4.19 | Restoration gap against in-medium loss | 4.8.2 | The two are uncorrelated (ρ = −0.14), which is what refutes the drift reading; a table states it, a scatter shows it | PLOT |
| 4.15b | Each configuration against the published reference (SS) | 4.2.1, 4.9 | The forest plot's null is A0, so the reference appears as a deviation rather than an anchor. A thesis claiming efficiency over SeaSplat also needs the distance from SeaSplat read directly. Same construction, null SS; not mechanism effects, and the caption says so | PLOT |
| 4.20 | Onset of medium collapse | 4.7.1 | Boundary alignment was asserted in prose. Six onsets at 15 001, one at 20 001, two at 22 500 | PLOT |

File names carry the chapter number, so `figure-4-15-main-effects-forest` is
Figure 4.15 and nothing else. They did not at first: the generator numbered
these six from 4.13, which collided with the two rendered figures that hold
4.13 and 4.14 — two different images under one number is how a draft ends up
citing the wrong one, so the generator was renumbered rather than the collision
documented.

### The two anchors

Figure 4.15 and Figure 4.15b are the same construction with different nulls,
and they answer different questions:

* **4.15, null A0.** A1 differs from A0 by exactly M1, so the difference *is*
  the mechanism effect. This is the pre-registered contrast and the one the
  main-effects tables of 4.3–4.5 report. The reference appears here as a
  fourth group, SS − A0, which is the equivalence claim of 4.2.1 drawn.
* **4.15b, null SS.** Not mechanism effects: A0 already differs from SS, so a
  row carries that difference plus whatever the mechanism does. It answers
  where each configuration stands against the published method, which is the
  claim of the thesis rather than of the factorial.

Neither null is an absolute zero, and no scene is ever compared with another
scene's anchor: every row is against the null cell *on that same scene*. The
count panel is a ratio on a log axis, so its null is 1, not 0.

### The reference implementation in the figures

SS appears in every figure whose data supports it, drawn hollow so it is never
mistaken for a configuration under test: the resolution figure, the operating
points (count axis only — it has no stored-size accounting), the main-effects
forest as a fourth group, the population trajectory as its two available
anchors, the per-view distribution, the medium convergence as a final state,
and the radius distribution. Its row in the forest plot is the equivalence
claim of §4.2.1 drawn rather than tabulated.

It is necessarily absent from three: the dispersion strata, the cut-against-loss
panel and the depth-range sweeps all need per-event diagnostics, and the
reference records one final row per run rather than a trajectory.

### Collected on Colab — `03_figures.ipynb`

Six products that need the run directories or a GPU, and so cannot come from
the analysis bundle. Collected by `tools/chapter_assets.py`; the four data
products are plotted locally by `figures/make_chapter4_figures.py`, which skips
them with a note until the bundle is unpacked.

| Tag | Product | Answers | Bound |
|---|---|---|---|
| C1 | `per_view_metrics.csv` | Whether a scene mean rests on one bad view — the held-out set is 13 frames | **Collected, §15.** Seed 0 only; 40/40 runs agree with their own `eval_metrics.json` within 0.5 dB |
| C2 | depth renders | The medium reads depth and the coupling acts through it, yet no figure showed depth | Fixed view per scene |
| C3 | restoration renders | Ĵ is the method's scientific output and appeared only inside the decomposition figure | Fixed view per scene |
| C4 | `depth_range_sweeps.csv` | Makes the refuted explanation tangible: the distribution moves, the outcome does not follow | All runs with sweeps |
| C5 | `medium_trajectories.csv` | The baseline's medium converging and staying put — currently asserted from a collapse count | All 120 runs; the bundle carried 48 |
| C6 | `radius_histograms.csv` | Direct evidence for the invisible-population account | Seed 0 only |

The view and both crop rectangles are fixed per scene in `tools/chapter_assets.py`
and reused by every configuration. A figure comparing configurations at
different cameras or crops is not a comparison, and nine tests in
`verify_chapter_assets.py` hold that contract — including that clamping a crop
moves it and never resizes it.

### Qualitative family — `qualitative-figure-spec.md`

Built by `figures/make_chapter4_renders.py` to the comparison rule: every
qualitative figure carries **ground truth, the reference, the baseline, and the
configuration under test**, in that order. Per-panel PSNR and LPIPS are for the
view shown, not the scene mean, so a reader can connect what they see to the
tables — and can see the cases where the eye and the metric disagree.

| Figure | Content |
|---|---|
| `figure-q1-<cell>-<label>` | One per mechanism: A0D, A1–A7, four columns × four scenes |
| `figure-q2-all-configurations` | All ten configurations on one scene, one crop |
| `figure-q3-error-maps` | Absolute error against ground truth, identically scaled |

Highlighting is restricted to what the analysis establishes: an accent border
marks a run that lost an attenuation channel (§5a). Nothing is highlighted for
being unresolved, invisible, or merely this study's own mechanism.

**Collection requirement.** Four configurations — A0D, A5, A6, A7 — are not yet
rendered, and their figures currently show explicit "not collected" panels. The
collector now renders all ten; a re-run fills them.

### Considered and not supportable

* **Storage composition by attribute** — would show where the 2.72× comes
  from. No `model_size.json` carries a per-attribute breakdown; it needs a
  collection change and a re-run of the size accounting.
* **Cross-campaign replication scatter** for 4.10 — the archived campaign's
  `results_by_scene.csv` is no longer in the repository. Restoring that bundle
  unblocks it.
* ~~Per-view fidelity distribution~~ — **collected**; see C1 above and
  `FINDINGS.md` §15. Views within one run differ by 6.65–11.25 dB and the
  hardest view is the same view in every configuration, so the spread is view
  difficulty and cancels in a cell-versus-cell contrast. Figure
  `figure-4-c1-per-view` carries it.

---

## 3. What must be added to the analysis first

Two assets are `DERIVE`: the data exist but `FINDINGS.md` does not report the
quantity, and the chapter may not be the first place a number appears.

1. **Learned medium parameters per scene** (Table 4.6, Figure 4.3). Add a
   subsection to `FINDINGS.md` reporting β_att and B∞ per channel for A0 and
   SS, with the spectral-ordering check. The finding it carries — one scene
   fitting an inverted attenuation spectrum, in the reference as well as the
   baseline — is new, belongs to the analysis, and connects to three other
   observations about that scene.

I can produce this from `results_runs.csv` and add it to the analysis as §2b
before drafting §4.2.4.

---

## 3b. Collected renders — what exists

144 images: six kinds × six configurations × four scenes, one fixed held-out
view per scene.

| Kind | Configurations | Feeds |
|---|---|---|
| `gt` ground truth | SS, A0, A1, A2, A3, A4 | 4.2, 4.6, 4.7, 4.8 |
| `composed` in-medium render | same | 4.2, 4.6, 4.7, 4.8 |
| `restored` medium-free Ĵ | same | 4.4, 4.5.7, 4.8 |
| `depth` normalised depth | same | C2, and 4.7 |
| `attenuation` map | same | 4.4, 4.13 |
| `backscatter` map | same | 4.4 |

**Five figures are assembled** by `figures/make_chapter4_renders.py` — 4.2,
4.4, 4.6, 4.7 and 4.8 — from these images, with crops applied at assembly so
the full frames stay available. Crops are fractions of the image, not pixel
boxes: the scenes were captured at four different resolutions and a fixed pixel
box would cover a different share of each.

**Figure 4.13 needed no new collection** — the collapsed run and an intact one
on the same scene were already rendered. It is assembled.

Still outstanding, and now collectable with `--only extras`: 4.5 (the
invisible population needs a render with sub-threshold primitives removed),
4.14 (both attribute states of one quantised run). Both are produced by
`--only extras`, which silences the sub-threshold primitives and re-renders for
4.5, and renders one quantised model from each of its two attribute states for
4.14.

**A limitation figure 4.13 carries in its caption.** Full point clouds are kept
for seed 0 only, and no cell has both a collapsed and an intact repeat at that
seed, so the collapsed run is shown against the baseline on the same scene and
view. The two differ in configuration as well as in outcome.

**Rendering is deterministic.** Independently collected runs of the same
configuration produced byte-identical images, verified by SHA-256 across three
separate collections. Figures can be regenerated exactly rather than
approximately.

## 4. Rendering plan

Seven figures need renders from stored checkpoints. All are seed 0, which the
storage policy retains.

**Constraints that make the figures comparable.** Fix the held-out view index
per scene and reuse it in every figure; fix the crop rectangles per scene and
reuse them across cells; render at the evaluation resolution; disable any
tone mapping that is not applied during evaluation; write PNG, not JPEG.

| Batch | Figures | Cells needed | Outputs |
|---|---|---|---|
| A | 4.2, 4.6, 4.7, 4.8 | A0, A1, A2, A3 × 4 scenes | Composed render at the fixed view; two crops each |
| B | 4.4, 4.8 (restored half) | A0, A3 × 4 scenes | Î, Ĵ, attenuation map, backscatter map |
| C | 4.5 | A0 × 1 scene | Render with and without sub-threshold primitives; visibility-coloured cloud |
| D | 4.13 | A2 × 1 scene, one collapsed and one intact repeat | Attenuation map and Ĵ for each |
| E | 4.14 | A3 × 1 scene | Ĵ from both attribute states, plus difference map |

Batches A and B are one pass of the existing render path with the medium
outputs enabled. Batch D needs a collapsed and an intact repeat of the same
cell and scene — Curaçao A2 has both. Batch E needs the continuous/codebook
switch the restoration check already implements.

**Scene choices where a figure shows only one scene.** Use Curaçao for 4.5 and
4.13, the scene with the largest primitive population and a collapsed repeat
available; use IUI3 Red Sea for 4.7, the scene with the largest perceptual cost
from simplification; use Panama for 4.14, the run with the largest restored-image
gap.

---

## 5. Placement summary

| § | Tables | Figures |
|---|---|---|
| 4.1 Experimental overview | 4.1, 4.2, 4.3 | 4.1 |
| 4.2 Baseline characterisation | 4.4, 4.5, 4.6, 4.7 | 4.2, 4.3, 4.4, 4.5 |
| 4.3 M1 initialisation | 4.8 | 4.6 |
| 4.4 M2 simplification | 4.9 | 4.7 |
| 4.5 M3 quantisation | 4.10 | 4.8 |
| 4.6 Interactions | 4.11, 4.12, 4.13 | 4.9 |
| 4.7 Medium coupling | 4.14, 4.15, 4.16, 4.17 | 4.10, 4.11, 4.12, 4.13 |
| 4.8 Limits of fidelity metrics | 4.18, 4.19 | 4.14 |
| 4.9 Gradient detachment | 4.20 | — |
| 4.10 Replication | 4.21 | — |
| 4.11 Synthesis | 4.22 | — |
| 4.12 Limitations | 4.23 | — |

Every caption states what the reader should conclude and what the asset does
not show. Figures whose data exist at one repeat per scene say so in the
caption: 4.4, 4.5, 4.13, 4.14 and Table 4.7 and 4.19.
