# Chapter IV — Results and Discussion: writing specification

**Revision 3.** Supersedes the Chapter IV structure in
`chapter-04-architecture.md` (Rev. 2) and in `thesis-structure-detailed.md`.
Those remain valid for their diagnosis of the existing draft; this document is
the one to write from.

What changed in Revision 3, and why:

1. **Qualitative results were missing entirely.** A thesis on novel view
   synthesis that reports no rendered views is not recognisable as one. Rev. 2
   removed the old chapter's qualitative subsections because their content was
   obsolete; the correct action was to rebuild them, not delete them.
2. **The learned medium parameters were never reported.** The estimator's
   scientific output is a decomposition into a medium-free image and nine
   physical parameters. Rev. 2 reported whether those parameters *survived*
   and never what they *were*. §4.2.4 now reports them, and with them a new
   finding: one scene fits a physically inverted attenuation spectrum, in the
   unmodified reference as well as here.
3. **Interpretation was under-specified.** "Discussion" subsections risk
   restating the table in prose. Every interpretive subsection below now names
   the mechanism-level account it must give, in domain terms.
4. **Uniform subsection shape** across the three mechanism sections, so a
   reader can compare them without relearning the layout.

---

## 1. Reader model and purpose

Write for an examiner who knows radiance fields but not this codebase, and who
will ask three questions of every claim: *against what baseline*, *at what
uncertainty*, and *on which scene*. The chapter succeeds if that reader can
reconstruct every verdict from the tables without trusting the prose, and can
identify, unprompted, which claims the design cannot support.

The chapter reports **one campaign**: 10 configurations × 4 scenes × 3
repeats = 120 runs. It is `analysis/campaign-2026-09/FINDINGS.md` in thesis
form — reorganised for a reader, not re-analysed. No number is recomputed
here; if a needed quantity is absent from the analysis, it is added there
first and then cited.

---

## 2. Uniform shape for every results subsection

Five moves, in this order. Deviations must be deliberate.

1. **Claim sentence.** One sentence, the finding, in plain words, with its
   direction. Not "results are presented below".
2. **Evidence.** The table or figure, per scene, with effect sizes and their
   resolution markers.
3. **Resolution statement.** What resolved, what did not, and on how many
   scenes. `UNRESOLVED` is stated as a property of three repeats, never as
   absence of effect.
4. **Mechanism-level interpretation.** *Why* the numbers look as they do, in
   terms of the algorithm or the physics — not a restatement of the table.
   Section 4 of this specification gives the accounts that must appear.
5. **Boundary.** What this subsection does not establish, and where the
   reader should go for the part it defers.

---

## 3. Section and subsection structure

Bracketed tags: **[PRE]** pre-registered · **[POST]** post-hoc · **[EXP]**
exploratory · **[FACT]** descriptive fact · **[NEG]** a negative or
inconvenient result that must not be softened.

### 4.1 Experimental Overview · ~5 pp

| § | Title | Content | Tag |
|---|---|---|---|
| 4.1.1 | Scope of the Completed Campaign | 10 configurations, 4 scenes, 3 repeats, 120 runs, one accelerator type, 107 GPU-hours, 30 000 iterations, effective optimizer steps 43 000 / 43 400 | [FACT] |
| 4.1.2 | Evaluation Criteria and Reporting Conventions | The four conventions: per scene never pooled; two standard errors; PSNR interactions undetermined by construction; registered versus post-hoc labelled in text | [FACT] |
| 4.1.3 | Repeat Dispersion as the Measurement Baseline | Table of baseline standard deviation per scene per metric; the resolution threshold each implies | [FACT] |
| 4.1.4 | Provenance and Experimental Integrity | Ledger, retries, the empty commit column and its cause, and what the one-code-version claim therefore rests on | [FACT] [NEG] |

### 4.2 Baseline Characterisation and Validation · ~10 pp

The baseline must be shown faithful *and* characterised as a physical
estimator before any mechanism is measured against it.

| § | Title | Content | Tag |
|---|---|---|---|
| 4.2.1 | Equivalence to the Unmodified Reference | SS versus A0 per scene against the margin fixed before the reference ran; scene means over repeats, not paired seeds; "equivalent within margin", never "reproduces" | [PRE] |
| 4.2.2 | Reconstruction Fidelity and Efficiency per Scene | PSNR, SSIM, LPIPS, count, render rate, training time. Note the 7.17 dB span and that PSNR and LPIPS rank the scenes differently | [FACT] |
| 4.2.3 | Qualitative Reconstruction Characteristics | Rendered held-out views against ground truth, one per scene, with crops on a far-field and a near-field region. Failure modes visible in the baseline | [EXP] |
| 4.2.4 | The Learned Medium Model | **New.** Per-scene β_att and B∞ per channel, with the spectral-ordering check. Includes the inverted-spectrum finding below | [FACT] [NEG] |
| 4.2.5 | Medium Decomposition, Qualitatively | Î, Ĵ, attenuation map and backscatter map for one view per scene: what the estimator claims the water is doing | [EXP] |
| 4.2.6 | Representation Characteristics and the Invisible Population | 27–41 % of primitives rendered in A0, 23–43 % in SS; bounding-box inflation; why later reductions must be read against the visible population | [EXP] |
| 4.2.7 | Baseline Medium Stability | 0 of 24 runs lose a channel across A0 and SS — the precondition for attributing any later loss to a mechanism | [PRE] |

### 4.3 – 4.5 The Three Mechanisms · ~9 pp each

Identical six-part shape. `M` denotes the mechanism, `Ax` its cell.

| Sub | Title | Content |
|---|---|---|
| x.1 | Reconstruction Fidelity per Scene | PSNR, SSIM, LPIPS versus A0, per scene, with effect and resolution marker |
| x.2 | Efficiency Outcome | The mechanism's own target cost: count and training time (M1), count and render rate (M2), stored bytes and render rate (M3) |
| x.3 | Effect on the Medium Model | Collapse rate for this cell; the learned parameters if they moved. **Reports the rate; defers the analysis to 4.7** |
| x.4 | Qualitative and Geometric Behaviour | Rendered crops showing the characteristic artefact; visible fraction and spatial extent |
| x.5 | Discussion | The mechanism-level account required by §4 of this specification |
| x.6 | Boundary | What this section does not establish |

Section titles: **4.3 Component 1 — Deterministic Initialisation (M1)**,
**4.4 Component 2 — Spatial Reorganisation (M2)**,
**4.5 Component 3 — Attribute-Level Quantisation (M3)**.

4.5 carries one extra subsection, **4.5.7 Effect on the Restored Image**,
because quantisation is the only mechanism whose damage is invisible in the
composed image and visible in the restoration. It states the result and defers
the instrument's limits to 4.8.2.

### 4.6 Combined Configurations and Interactions · ~8 pp

| § | Title | Content | Tag |
|---|---|---|---|
| 4.6.1 | Estimating Interactions in This Design | The contrast equations; additive on LPIPS, log-multiplicative on count; why PSNR terms are undetermined *by construction* and are tabulated but not interpreted | [FACT] |
| 4.6.2 | Initialisation × Simplification | H5: strongly sub-additive on count on all four scenes. The budget bound is the cause and must be stated as structural, not physical. The favourable LPIPS interaction was not registered | [PRE] + [POST] |
| 4.6.3 | Simplification × Quantisation | H3: sub-additive on quality on three scenes — a smaller population is more sensitive to lossy attribute compression | [PRE] |
| 4.6.4 | Initialisation × Quantisation | **The registered additivity prediction failed**: it resolves on three scenes with inconsistent sign | [PRE] [NEG] |
| 4.6.5 | Three-Way Interaction | Unresolved on count everywhere and on LPIPS on three scenes; not interpreted | [PRE] |
| 4.6.6 | Operating Points Across Configurations | Non-dominated cells per scene on count × LPIPS, bytes × LPIPS, count × PSNR. Description of nine cells, **not** a rate–distortion curve | [EXP] |

### 4.7 Coupling Between Simplification and the Medium Model · ~10 pp

The centre of the chapter. Nothing here may be softened.

| § | Title | Content | Tag |
|---|---|---|---|
| 4.7.1 | Incidence and Boundary Alignment | Collapse counts per cell per scene; every affected run places its largest attenuation drop at the first simplification event; blue is lost in every case and green simultaneously in two of the nine, so the invariant is the spectral direction rather than a single channel | [PRE] |
| 4.7.2 | Final Size Is Not the Cause | The initialisation-plus-simplification cells finish 13–17 % *below* the simplification-only cells and never collapse. Deconfounds magnitude of the final representation from the discontinuity that produced it | [PRE] |
| 4.7.3 | The Registered Explanation and Its Refutation | The dispersion account as written before the campaign; the instrument; the rank test; the counterexample. **The account is withdrawn, not qualified** | [PRE] [NEG] |
| 4.7.4 | What the Diagnostics Show Instead | The cut moves no medium parameter; the medium moves in the 200 medium-only steps that follow; association with removal fraction; no pre-cut predictor of which repeat crosses zero; the three protections of dense initialisation are mutually confounded | [POST] |
| 4.7.5 | The Re-Identification Burst | This work's own remedy is the interval in which the medium falls. Whether it causes or merely hosts the fall is untested, because every simplification cell contains it | [PRE] [NEG] |
| 4.7.6 | Physical Consequence | What a collapsed channel means for the decomposition: the water becomes transparent in that channel and the medium-free image absorbs its appearance | [FACT] |

### 4.8 Detecting Failure: the Limits of Fidelity Metrics · ~6 pp

| § | Title | Content | Tag |
|---|---|---|---|
| 4.8.1 | Fidelity Does Not Separate Collapsed from Intact Runs | Twelve within-cell, within-scene comparisons; median difference 0.8 baseline standard deviations; inconsistent sign | [PRE] |
| 4.8.2 | Restoration Consistency Under Quantisation | Two attribute states of one model differ by 17–27 dB in the restored image and 0.6–3.1 dB in the composed image; the two are uncorrelated. Consistency, not accuracy; one repeat per scene | [EXP] [NEG] |
| 4.8.3 | Implication for Evaluation Practice | Composed-image metrics cannot certify the physical component of a physically grounded estimator. The methodological result of the thesis | [POST] |

### 4.9 Supplementary Contrast: Gradient Detachment · ~4 pp

| § | Title | Content | Tag |
|---|---|---|---|
| 4.9.1 | Rationale and Why It Is Not a Fourth Factor | Provably inert wherever initialisation is active; measured against the baseline alone | [FACT] |
| 4.9.2 | Quantitative Comparison Against the Baseline | Count, training time, render rate, peak render memory, PSNR, LPIPS, collapse | [PRE] |
| 4.9.3 | Discussion | A continuous reduction leaves the medium intact where a two-step cut does not — consistent with 4.7.4 and not a test of it | [POST] |

### 4.10 Replication Against the Archived Campaign · ~4 pp

Perceptual similarity replicates on all sixteen comparisons; dense
initialisation's count replicates to three figures; four PSNR comparisons do
not; one mechanism's PSNR effect on one scene reverses sign and is downgraded
to unresolved across campaigns. The provenance limit prevents attribution to a
named change. **[EXP] [NEG]**

### 4.11 Synthesis · ~5 pp

| § | Title | Content |
|---|---|---|
| 4.11.1 | Alignment with the Research Questions | One row per research question: the answer, the evidence, the resolution, the boundary |
| 4.11.2 | What the Campaign Establishes | Stated at the level the evidence supports |
| 4.11.3 | What Remains Open | The mechanism of the coupling; restoration accuracy; the confounded protections |

### 4.12 Limitations of the Study · ~5 pp

4.12.1 Experimental · 4.12.2 Methodological · 4.12.3 Unresolved and
undetermined by design · 4.12.4 Threats to external validity.

---

## 4. Domain accounts that must appear, stated correctly

These are the interpretations that make the chapter a piece of research rather
than a report. Each is a claim about mechanism; each must be written at the
level of confidence indicated.

**A. What collapse is, physically.** *(state as established)* The estimator
composes the observed image as a medium-free radiance attenuated by
`exp(−β_att·z)` plus backscatter saturating at `B∞`. Driving β_att to zero or
below in a channel makes the water transparent in that channel: the attenuation
map becomes unity, and the medium-free image must then explain the veiling
appearance itself. The composed image remains a good fit — which is why the
fidelity metrics do not react (4.8.1) — while the decomposition the method
exists to produce has ceased to be physical. This is an identifiability
failure, not a numerical instability.

**B. Why a large cut and not a small one.** *(state as post-hoc description,
never as cause)* Removing 86–95 % of the population in one step changes the
rendered depth field that the medium parameters were fitted against, and the
optimiser then re-fits those parameters against a geometry that no longer
supports the previous solution. Cuts of 29–36 % do not produce the effect. The
association with removal fraction is strong; the mechanism is not established,
and the registered explanation that was tested failed (4.7.3).

**C. Why dense initialisation protects.** *(state as confounded)* Cells with
dense initialisation enter the first simplification event with ~224 000
primitives rather than 1.4–4.2 million, so a fixed budget removes a third
rather than nine tenths. They also enter with a different medium state and a
different count. The design sets all three together and cannot separate them.
Do not attribute the protection to any one of them.

**D. Why frame rate is sub-linear in primitive count.** *(state as
established, mechanism as standard)* Tile-based rasterisation cost has a
per-primitive component — projection, sorting, tile binning — and a per-pixel
component — blending over the primitives covering each pixel. Reducing the
population reduces the first and only partially the second, because the
surviving primitives still cover the image. A 20× reduction in count
therefore buys roughly 2–3.5× in throughput, and the exponent differs by scene
with depth complexity.

**E. Why PSNR and LPIPS disagree under simplification.** *(state as
established for this corpus)* Removing primitives removes high-frequency
detail and some floaters. PSNR, a pixel-wise error measure, is rewarded by the
smoothing; LPIPS, a feature-space measure, penalises the lost texture. This is
why simplification improves PSNR on two scenes while degrading LPIPS on all
four, and it is the reason the chapter adjudicates on LPIPS.

**F. Why quantisation moves the restoration far more than the composed
image.** *(state as inference from the image formation model, and label it as
such)* The quantised attributes enter the medium-free image directly, but that
image is multiplied by an attenuation map bounded above by one and approaching
zero at range before any metric sees it. Error in the far field is therefore
attenuated out of the measured image while remaining in the restoration. The
per-depth-bin measurement that would confirm this was not made.

**G. Why most primitives are invisible.** *(state as established, cause as
plausible)* Before the medium model activates, the loss compares the raw
render against the capture, so veiling haze must be paid for by geometry; the
optimiser recruits low-opacity primitives near the camera to supply it. That
the unmodified reference carries the same 23–43 % visible fraction establishes
the property belongs to the baseline optimiser, not to this implementation.

**H. The inverted attenuation spectrum on IUI3 Red Sea.** *(state as
established fact, cause as unknown)* Water attenuates long wavelengths
fastest, so a physically plausible fit orders β_att as red > green > blue.
Three scenes do so. IUI3 Red Sea fits the reverse ordering — blue > green >
red — in the baseline **and in the unmodified reference**, so it is a property
of the scene and its fit rather than of anything done here. This is the same
scene on which every mechanism costs perceptual quality, on which no
simplification run collapses, and on which PSNR does not replicate across
campaigns. The chapter must connect these observations and must not claim to
have explained them.

---

## 5. Qualitative assets required

The chapter needs rendered evidence. Available in the repository: baseline and
simplified viewer captures for two scenes, one reference capture, one point
cloud animation. **Not yet produced** and needed:

| Asset | Sections | Note |
|---|---|---|
| Held-out view: ground truth, A0, A1, A2, A3 — one per scene | 4.2.3, 4.3.4, 4.4.4, 4.5.4 | Same view and crop across cells, or the comparison is not one |
| Medium decomposition: Î, Ĵ, attenuation, backscatter — one view per scene | 4.2.5 | The render path already writes these |
| Collapsed versus intact run, same cell and scene: Ĵ and attenuation map | 4.7.6 | The visual counterpart of 4.8.1 |
| Restored image from both attribute states, quantised cell | 4.8.2 | The visual counterpart of the 17–27 dB gap |
| Far-field crop under quantisation | 4.5.7 | Supports account F |

Render all from stored checkpoints at fixed view and crop. Every figure caption
states what the reader should conclude **and what the figure does not show**.

---

## 6. Writing rules

* Lead each subsection with the finding, not with the procedure.
* Give direction in words before symbols: "fewer primitives", "worse
  perceptual similarity", then the number.
* Every effect carries scene, magnitude, unit and resolution. No bare number.
* Never "significant" — the study performs no significance test. Use
  "resolved", "unresolved", "undetermined".
* Never "dramatic", "substantial improvement", "clearly superior".
* Prefer "associated with" to "causes" unless the design isolates it. Section
  4.7.4 contains no causal verb.
* Name the scene whenever a claim is scene-specific, which is most of them.
* When a prediction failed, say it failed in the sentence that introduces it.
* Do not close a subsection with a sentence that overstates it to sound
  conclusive; close with the boundary.

---

## 7. Verification checklist, per subsection

Before a subsection is considered drafted:

1. Every number traces to a section of `FINDINGS.md`.
2. Every effect has a resolution marker.
3. No fidelity figure is averaged across scenes.
4. Registered and post-hoc statements are labelled in the body text.
5. The mechanism-level account from §4 of this specification is present, at
   the confidence level stated there.
6. The boundary sentence is present.
7. No prohibited term from §6 appears.
8. Any [NEG] item in the section appears in full, in the body, not in a note.
