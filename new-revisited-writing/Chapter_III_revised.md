# Chapter III. Research methodology

This chapter specifies how the study evaluates three efficiency mechanisms within a physics-aware underwater 3D Gaussian Splatting pipeline. Section 3.1 establishes the comparison logic. Sections 3.2 to 3.8 describe the executed stages, input data, preprocessing, baseline and interventions, experimental controls, measurements, and limits of inference. The configuration and measurement details in those sections must be reconciled with individual run manifests before submission.

## 3.1 Conceptual framework

### 3.1.1 Research setting and design

This study uses a controlled factorial experiment to examine whether efficiency mechanisms developed for terrestrial 3D Gaussian Splatting transfer to an underwater reconstruction pipeline and how they behave in combination. Its internal control, A0, is a refactored SeaSplat implementation; SS is a separately executed upstream SeaSplat reference. In SeaSplat, rendered scene radiance and depth enter an underwater image formation model before the resulting image is compared with a captured view (Yang et al., 2025; Levy et al., 2023). The image comparison constrains the composition, while neither medium-free radiance nor the medium coefficients has independent reference supervision in this dataset. Auxiliary losses and structural assumptions impose additional constraints; they do not turn the fitted coefficients into calibrated physical measurements. Figure 3.1 locates the relevant computational dependencies.

The three interventions enter at different points in the representation lifecycle, but their measured effects need not be independent. M1 replaces the sparse initial cloud with a dense correspondence cloud and disables subsequent densification. M2 changes the Gaussian population at scheduled importance-based simplification events. M3 uses codebook-quantized values for selected Gaussian attributes in its training forward path. Their effects can meet through the rendered radiance, depth, and medium model even though their immediate operations differ. Sections 3.5.2 to 3.5.4 define the implemented adaptations of EDGS (Kotovenko et al., 2026), Mini-Splatting (Fang & Wang, 2024), and CompGS-VQ (Navaneet et al., 2024), respectively. [CITATION CHECK — three of four resolved against the repository reference register: Kotovenko et al. (2026), Fang and Wang (2024), and Navaneet et al. (2024) match. SeaSplat is cited here as Yang et al. (2025) but as Yang et al. (2024) throughout the repository, which records arXiv:2409.17345v2. Both are defensible — the preprint is 2024, the conference version 2025 — but one must be chosen and applied in all five chapters. Resolve from the PDF actually consulted and record the venue in the reference list.]

The principal comparison crosses three binary factors in eight configurations, A0 through A7. Each factor is disabled at level 0 and enabled at level 1. The complete matrix permits stand-alone effects and interactions to be calculated within the refactored implementation. SS provides a separate reference check on A0. A0D changes the gradient received by adaptive density control and is compared only with A0; D is not a fourth factorial treatment. Table 3.1 follows `implementation/configs/cells.json`; resolved run settings remain the authority for individual executions.

**Table 3.1. Experimental configuration matrix and inferential role.**

| Configuration | M1: dense initialization | M2: spatial simplification | M3: attribute quantization | Supplementary D | Role |
|---|---:|---:|---:|---:|---|
| SS | N/A | N/A | N/A | N/A | Upstream SeaSplat reference; separate execution and A0 comparison |
| A0 | 0 | 0 | 0 | 0 | Refactored internal control and zero-factor corner |
| A1 | 1 | 0 | 0 | 0 | M1 alone |
| A2 | 0 | 1 | 0 | 0 | M2 alone |
| A3 | 0 | 0 | 1 | 0 | M3 alone |
| A4 | 1 | 1 | 0 | 0 | M1 with M2 |
| A5 | 1 | 0 | 1 | 0 | M1 with M3 |
| A6 | 0 | 1 | 1 | 0 | M2 with M3 |
| A7 | 1 | 1 | 1 | 0 | Combined M1, M2, and M3 |
| A0D | 0 | 0 | 0 | 1 | Separate D intervention; compare only with A0 |

*Source: `implementation/configs/cells.json`. D is displayed to distinguish A0D from A0, but it is excluded from the three-factor design. N/A denotes an external reference, not a factorial treatment. Resolved `run_config.json` records determine the realized settings.*

### 3.1.2 Mechanism pathways and research questions

Figure 3.1 shows how the interventions enter the optimization loop. M1 changes the starting positions and population, and disables the later growth path. M2 removes primitives at two scheduled events; its events have different selection rules, specified in Section 3.5.3. M3 changes the color, scale, and rotation values used by the quantized forward path and their final storage representation. Supplementary D changes the gradient routed to density control. These dependencies motivate an interaction analysis; the diagram does not assert an observed improvement or identify a physical cause for any medium-parameter change.

> **[INSERT EXISTING VECTOR FIGURE 3.1]** Repository asset: [`figures/figure-0-optimisation-loop.svg`](https://github.com/dinanirham/An-Efficient-3D-Gaussian-Splatting-for-Underwater-3D-Reconstruction/blob/main/figures/figure-0-optimisation-loop.svg). PNG fallback: `figures/figure-0-optimisation-loop.png`. Caption: *Figure 3.1. Conceptual optimization loop of the underwater Gaussian estimator and the four intervention points. M1 changes the initial cloud and disables densification; M2 changes the population at scheduled events; M3 substitutes quantized attributes in the forward render; D changes the density-control gradient in A0D. Rendered radiance and depth enter the underwater image formation model before comparison with captured images. Arrows indicate computational dependencies, not measured effects.* The asset's compact image-formation equation shows the sigmoid activation on B∞ but omits two things Section 3.5.1 specifies: the clamp applied to the attenuation–depth product, and the per-view depth normalization. The attenuation and backscatter coefficients carry no activation to omit — they are unconstrained, and the forward pass clamps their product with depth at zero (`implementation/tools/analyse.py`). That clamp is not cosmetic: it is the mechanism by which a channel driven negative loses its gradient and stays negative, which Chapter IV reports as operational collapse. The figure should therefore not be described as omitting “activation” in general.
>
> **SVG verified against this caption.** Seventeen text labels were extracted and compared. Three require action before typesetting. (a) The caption states that M1 “disables densification”; the M1 node reads only “dense correspondences replace the sparse cloud”, so either the node gains that clause or the caption drops it. (b) Spelling is mixed within the single asset — *Initialise*, *rasterisation*, *colour*, *optimisation* alongside *initialization*, *quantization*, *simplification*, *color*. Choose one convention and regenerate. (c) The string “Figure 0 — the optimisation loop” sits in the SVG's `<title>` element, so it is invisible in print but is exposed as a browser tooltip and to screen readers; replace it with the thesis figure number. All other labels are consistent with the caption as written.

The current research-question revision organizes the evaluation around four questions. RQ1 asks how far the mechanisms reduce reconstruction cost relative to the upstream reference and what image-fidelity trade-off accompanies each configuration. RQ2 asks whether the three mechanisms compose additively on specified metric scales. RQ3 asks whether primitive reduction compromises the fitted medium model and whether any combination changes the incidence of operational collapse. RQ4 asks whether conventional image-fidelity metrics discriminate collapsed from intact medium-model runs. The first two questions use image fidelity and cost; the latter two require medium-integrity diagnostics as a third evaluation axis. These diagnostics assess model behavior and internal consistency, not independently measured restoration or medium accuracy. [CHAPTER I DEPENDENCY — Chapter I is not yet drafted, so no reconciliation is possible today. The four questions above are transcribed from `new-revisited-writing/research-questions-revised.md`, which is the approved current source and already uses this three-axis framing. Action: when Chapter I §1.3.1 is written, copy the wording from that file rather than paraphrasing it here, then delete this marker. Do not renumber: RQ1–RQ4 in that file are already in the order this chapter and Chapter IV §4.11.1 both assume.]

Table 3.2 maps these questions to measurable comparisons. The question wording follows `new-revisited-writing/research-questions-revised.md` provisionally; the final Chapter I wording and Chapter II evidence must be reconciled before submission. In particular, the diagnostic question must not be restated as proof of physical correctness.

**Table 3.2. Traceability from research questions to comparisons and measures.**

| Research question [wording from `research-questions-revised.md`] | Chapter II rationale | Design decision | Comparison | Outcome and evidence source |
|---|---|---|---|---|
| RQ1: cost reduction and fidelity relative to SS | Kotovenko et al. (2026); Fang & Wang (2024); Navaneet et al. (2024); Yang et al. (2024/25) — all in register | Compare each implemented configuration on common scenes and views | Configuration outcomes versus SS where available; M3 storage versus A0; A1, A2, A3 effects versus A0 | Per-scene PSNR, SSIM, LPIPS, primitive count, timing, and stored bytes where recorded |
| RQ2: additivity and interactions | **[REGISTER GAP — no design-of-experiments source exists in the twelve-entry register; a factorial-method citation must be added before this row can be filled]** | Full A0–A7 matrix | Four-cell two-factor and eight-cell three-factor contrasts; effects from below and above | Per-scene LPIPS and count interactions as designated primary outcomes, with estimates and repeat uncertainty; other outcomes described on their stated scales |
| RQ3: medium behavior under population change | Akkaynak & Treibitz (2018); Levy et al. (2023) — both in register | Log medium and depth behavior around M2 events and across combinations | Within-run event records; M2 configurations with and without M1, by scene and repeat | Collapse incidence, coefficient trajectories, depth-range dispersion; labels are operational, not physical ground truth |
| RQ4: sensitivity of fidelity metrics to medium failure | Wang et al. (2004); Zhang et al. (2018) — both in register | Retain per-run fidelity and medium classifications together | Collapsed and intact runs within comparable cell–scene strata where both occur | PSNR, SSIM, LPIPS differences with group counts and uncertainty; inconclusive strata remain explicit |

### 3.1.3 Units, outcomes, and comparison boundaries

One executed training run for one configuration, one scene, and one repeat is the observational unit for run-level outcomes. A scene supplies a distinct evaluation setting; held-out views within that scene contribute to its metric summary. Views and pixels from one trained model are correlated and cannot be counted as independent training repeats. The completed campaign comprises ten configurations across four scenes with three repeats per configuration and scene, totaling 120 runs. Run-level records still determine which measurements are available for each comparison. The SS repeat labels must not be assumed to denote random draws paired with the same labels in A0.

The study reports three outcome axes. Image fidelity comprises the implemented PSNR conventions, SSIM, and LPIPS on composed held-out renders. Cost includes Gaussian count, actual serialized bytes, training time, rendering latency or throughput, and measured memory where records exist. Medium integrity comprises operational collapse and trajectory diagnostics and limited internal consistency checks. Gaussian count does not substitute for model size or training cost; medium integrity does not establish calibrated attenuation or correct medium-free color. Section 3.7 defines the units, instruments, aggregation, and available coverage.

Two reference roles must be distinguished. SS is the upstream method against which configuration outcomes are presented where the measurements are comparable. A0 is the zero-factor corner used for factorial effects: A1 minus A0, A2 minus A0, and A3 minus A0 are the stand-alone effects, and all interaction terms are built from A0 through A7. Subtracting a common SS reference from every factorial cell cancels it in these contrasts; it does not create an extra factorial cell. SS lacks a matching stored-byte outcome in the current analysis specification, so actual storage comparisons use A0 as their declared reference. SS versus A0 checks baseline correspondence, and A0D versus A0 is supplementary. Each comparison keeps scene as a block and distinguishes training-run dispersion from differences among scenes. Section 3.8 specifies the metric scale, contrast, and uncertainty rule.

The design tests one implemented operating point for each mechanism under the recorded scene and training conditions. A plotted set of eight configurations can describe observed fidelity and resource trade-offs, but it cannot establish a within-method rate-distortion curve or a ranking across untested budgets. Interpretation of medium-related diagnostics must also separate a measured parameter trajectory, an image-level reconstruction score, and physical validity. The available image supervision does not automatically establish the last of these.

**Table 3.3. Evaluation axes, comparison references, and limits.**

| Axis | Principal outcomes | Comparison reference | What it can establish | Principal limit |
|---|---|---|---|---|
| I. Composed-image fidelity | PSNR, SSIM, LPIPS | SS for configuration reporting; A0 for factorial effects | Held-out view agreement under the stated image protocol | Does not independently validate medium-free color or 3D geometry |
| II. Representation and computation cost | Count, saved bytes, training time, render rate and memory where available | SS where comparable; A0 for stored bytes and factorial effects | Measured resource trade-offs at the tested operating point | Count, bytes, time, and memory are distinct dimensions |
| III. Medium integrity | Collapse incidence, coefficient and depth trajectories, limited restoration consistency | SS where diagnostics match; otherwise within-run or within-cell absolute criteria | Operational model failures and associations | Neither physical medium accuracy nor causal explanation follows from these diagnostics alone |

*The complete artifact-availability inventory belongs in Section 3.7. All comparisons are conditional on the metric and diagnostic coverage actually retained for the relevant runs.*

### Editorial verification status for Section 3.1 (outside thesis prose)

1. **Verified — Table 3.1 against `implementation/configs/cells.json`:** every cell's
   factor levels match the executed file. A0 `{m1:F, m2:F, m3:F}`; A1 `{T,F,F}`;
   A2 `{F,T,F}`; A3 `{F,F,T}`; A4 `{T,T,F}`; A5 `{T,F,T}`; A6 `{F,T,T}`; A7 `{T,T,T}`;
   A0D carries the three factors false plus `detach_alpha_gradient: true`; SS has an empty
   `set` and an `external` block naming the upstream checkout `dxyang/seasplat @ ddc6259`.
   The ledger confirms 120 runs, all `done`. Table 3.1 needs no change.
1b. **Verified — the equivalence margin and its timing:** `cells.json` carries the margin
   inside the SS cell as `psnr_pooled_db: 1.0`, `lpips: 0.02`, `n_primitives_fraction: 0.3`,
   with a note stating it was fixed *before* S0 ran and set to “what this design can certify,
   not to what would be impressive”. This substantiates §3.6's margin values and the
   before-the-fact ordering from the configuration file itself, not only from the ledger's
   stage order. Cite the file when §3.6.2 states the margin.
2. **Verified — Figure 3.1 asset exists in both formats:**
   `figures/figure-0-optimisation-loop.svg` and `.png`. Seventeen text labels extracted
   and compared with the proposed caption; three typesetting actions are recorded in the
   figure block above (M1 densification clause, mixed spelling, `<title>` string).
3. **Corrected — the figure's technical note:** an earlier draft of this block stated the
   asset omits “activation”. It does not: the sigmoid on B∞ is drawn. What it omits is
   the clamp on the attenuation–depth product and the per-view depth normalization. The
   attenuation and backscatter coefficients are unconstrained and carry no activation
   (`implementation/tools/analyse.py`, `implementation/utils/diagnostics.py`).
4. **Partly resolved — Table 3.2 citation column:** three of four rows filled from the
   repository's twelve-entry reference register. RQ2's row cannot be filled: the register
   contains no design-of-experiments or factorial-method source. A citation of that class
   must be added to Chapter II before the row is complete.
5. **Open — SeaSplat citation year:** this chapter uses Yang et al. (2025); the repository
   uses Yang et al. (2024) and records arXiv:2409.17345v2. Choose one against the consulted
   PDF and apply it across all five chapters.
6. **Blocked — Chapter I reconciliation:** Chapter I is undrafted. The research-question
   wording here is transcribed from `research-questions-revised.md`; that file is the source
   of truth until §1.3.1 exists.
7. **Resolved — the SS repeat-label restriction is documented, not merely asserted:**
   `cells.json` records that `s0`–`s2` are repeat indices rather than matched seeds, because
   the upstream implementation seeds only the CPU generator while this one seeds both and
   still measures a 49 per cent spread, the rasteriser backward accumulating atomically. It
   directs that SS and A0 be compared as scene means over repeats and never run against run,
   “which would look paired and carry the pairing noise as though it were signal”. §3.1.3 and
   §3.6 should cite this rather than asserting it. One item remains open: the 49 per cent
   figure's provenance is not given in the file and should be traced before it is quoted in
   prose.

## 3.2 Research stages

The research stages connect the source-method review and baseline implementation to the executed configuration matrix. Figure 3.2 organizes the implemented pipeline into preprocessing, initialization, training, and evaluation. Those phases are distinct from campaign stages S0 to S6 in Table 3.4, which label the ledger's execution order. The stage labels do not imply that every run was executed in one uninterrupted session or that later analysis followed the same order as training.

> **[FIGURE 3.2 PLACEHOLDER: CORRECT EXISTING VECTOR BEFORE INSERTION]** Repository asset: [`figures/figure-1-pipeline.svg`](https://github.com/dinanirham/An-Efficient-3D-Gaussian-Splatting-for-Underwater-3D-Reconstruction/blob/main/figures/figure-1-pipeline.svg). PNG fallback: `figures/figure-1-pipeline.png`. Caption: *Figure 3.2. Implemented pipeline from camera preprocessing and Gaussian initialization through training and held-out evaluation. Branches identify the baseline, M1, M2, M3, and supplementary D pathways. The separate S0 to S6 configuration stages are reported in Table 3.4.* **Both annotation faults confirmed, and three more found on audit.** (a) The SVG reads `M3 · i ≥ 22 000`; `train.py` lines 271 and 965 both gate on `iteration > opt_params.kmeans_st_iter` with `kmeans_st_iter = 22_000`, so quantisation is first active at iteration 22 001. The label should read `M3 · i > 22 000`. (b) The M2 node reads “cut to 200 000 primitives” for both events, but `cells.json` sets `cdf_thres: 0.99` and the schedule asset `figure-2-schedule.svg` distinguishes them as “cut to 200 k” and “CDF prune”; the pipeline figure must make the same distinction or it contradicts its companion. (c) “COLMAP sparse cloud · ~26 000 points” is the maximum, not a typical value: the executed range is 21 140 to 25 837, so “21 k – 26 k” is the honest label. (d) “Per-run record · 45 fields” does not match `results_runs.csv`, which carries 51 columns; confirm whether the figure counts the run manifest or the results row and correct the number. (e) “CD · Reject — 24% of triangulations” cannot be verified from the repository, since the dense-cloud sidecars are not held here; trace it to a sidecar before it is typeset. **Verified correct and needing no change:** “4 scenes · 88 images”, “75 training views · 13 held-out frames”, “244k – 294k points”, “i > 10 000” for the image-formation gate, and the per-frame depth normalisation node. Its `<title>` element reads “Figure 1 — detailed pipeline by phase”; replace with the thesis number, as for Figure 3.1.

### 3.2.1 Method specification and baseline preparation

The first stage identifies the components of the underwater baseline and specifies what each efficiency intervention changes. The baseline is the refactored SeaSplat implementation, denoted A0. A separate SS configuration executes the source SeaSplat implementation as a reference for checking the refactor. This distinction matters: a comparison against A0 estimates the effect of a study intervention within the refactored pipeline, whereas SS versus A0 examines baseline correspondence under the stated measurement conditions. The configuration matrix is given in Table 3.1. Section 3.5 defines the actual computation at each intervention point.

The study next prepares the four dataset scenes for the renderer. The campaign documentation requires camera undistortion to a pinhole model before training and a dense point cloud for each scene used by M1. Dense-cloud preparation is a separate offline step; its duration should not be silently included in one training condition and excluded from another. Section 3.4 specifies the inputs, partitioning, transformations, and provenance checks. The preparation stage produces scene images and cameras suitable for training, a baseline sparse initialization, and scene-specific dense clouds with metadata. [PARTLY RESOLVED — realized point counts verified at 244 197 to 293 642 across the four scenes from the per-run records, matching the dense-cloud figures quoted in §3.4. File hashes and train-view exclusion remain open: the dense-cloud sidecars are not present in this repository, so the four hashes tabulated in §3.4 cannot be checked against a generating artifact here, and the exclusion of held-out frames from correspondence matching cannot be confirmed. Retrieve the sidecars from the campaign workspace, or re-derive the exclusion from the generation code, before either claim is made in prose.]

### 3.2.2 Factorial training campaign

The ledger records the SS reference first (S0), then A0 (S1), A2 (S2), A1 and A3 (S3), A4 to A6 (S4), A7 (S5), and supplementary A0D (S6). S1 establishes the refactored baseline in each scene. S2 introduces the population intervention and records the associated medium-model diagnostics. S3 supplies the remaining stand-alone mechanism comparisons. S4 and S5 complete the paired and three-factor configurations. S6 examines a separate modification to the densification-gradient path. These roles follow the repository runbook and analysis plan; an observed result should not be described as a successful hypothesis test merely because it occupies a planned stage.

**Table 3.4. Campaign stages and intended comparisons.**

| Stage | Configuration(s) | Completed runs across four scenes and three repeats | Comparison enabled |
|---|---|---:|---|
| S1 | A0 | 12 | Refactored baseline and dispersion |
| S2 | A2 | 12 | M2 versus A0; medium diagnostics |
| S3 | A1, A3 | 24 | M1 and M3 versus A0 |
| S4 | A4, A5, A6 | 36 | Two-factor combinations |
| S5 | A7 | 12 | Full combination and conditional contrasts |
| S6 | A0D | 12 | Supplementary contrast with A0 |
| S0 reference | SS | 12 | SS versus A0, outside the factorial matrix |
| **Total runs** | **Ten configurations** | **120** | **96 factorial, 12 supplementary A0D, and 12 SS reference runs** |

*Source: archived `run_ledger.json` for run counts, statuses, and stage labels; `implementation/RUNBOOK.md` for scheduling logic. Per-run artifact coverage and comparison eligibility are examined separately.*

The schedule was administered through a persistent run ledger and a worker that selected the next available cell. This arrangement allowed training to proceed across sessions without manually editing a separate notebook for each configuration. A run was associated with its cell, scene, repeat identifier, output directory, and attempt count. The final ledger marks all 120 entries `done`: 116 required one attempt, three required two, and one required three. According to the campaign documentation, an interrupted run was restarted from the beginning because the checkpoint did not preserve every state needed to resume the medium model and the intervention schedule. The ledger does not retain prior attempts' files or causes; those require the corresponding run directories. The mechanism and validity implications are treated in Section 3.6.

### 3.2.3 Evaluation and analysis

After training, the evaluation stage extracts fidelity, representation, resource, and diagnostic records at the documented checkpoint. The analysis plan calls for per-scene summaries of three repeats, comparisons of individual mechanisms with A0, factorial contrasts, and separate checks of SS and A0D. Medium-model trajectories and geometry diagnostics are examined only for the configurations and runs in which those outputs were recorded. The plan distinguishes analyses fixed before inspection of campaign outputs from exploratory analyses; Section 3.8 documents each rule and its timing.

For each table and figure in Chapter IV, the analysis stage must retain the path back to the configuration, scene, repeat, final evaluation record, and relevant diagnostic. This is necessary because the repository's later analysis files are derived summaries, while run-level outputs are the evidence for what a particular training execution measured. The repository README lists a run ledger, per-run and per-scene result tables, factorial-analysis JSON files, medium diagnostics, and selected geometry and restoration checks. Its inventory does not by itself verify that all files are present or that all run configurations share an identical code state. Section 3.6 records that provenance check, and Section 3.7 records coverage for each measurement.

### Editorial verification status for Section 3.2 (outside thesis prose)

1. **Publication years verified; Chapter II alignment open:** Cite SeaSplat as Yang et al. (2025), EDGS as Kotovenko et al. (2026), RoMa as Edstedt et al. (2024), Mini-Splatting as Fang and Wang (2024), and CompGS-VQ as Navaneet et al. (2024). Compare the exact bibliography entries with current Chapter II. Match the exact research questions and objectives to the current Chapter I; decide whether medium-model behavior is an explicit objective or a supporting diagnostic.
2. **Verified — ledger completeness and attempt counts:** 120 unique cell–scene–repeat keys across ten configurations, all `done`. The attempt distribution stated in §3.2.2 is exact: 116 runs at one attempt, three at two, one at three. The four multi-attempt runs are A0/JapaneseGradens s0 (2), A3/IUI3-RedSea s1 (3), A3/JapaneseGradens s2 (2), and A6/JapaneseGradens s0 (2) — name them in prose if the restart discussion needs instances. **Still open:** per-run availability of each final evaluation file and optional diagnostic; ledger completion does not establish it, and §3.7 carries that audit.
3. **Verified from the ledger — Table 3.4 needs no change:** stages are S0=SS (12), S1=A0 (12), S2=A2 (12), S3=A1/A3 (24), S4=A4/A5/A6 (36), S5=A7 (12), S6=A0D (12), totalling 120. Start and finish spans occur strictly in that order with no overlap, from 15 to 21 September 2026, for 107.0 GPU-hours. The reference stage running first is what allows §3.6.2's margin to be described as fixed in advance; §3.1's status block records that `cells.json` carries the margin values directly. **Still open:** the restart *cause* — the ledger holds an empty error field for all four, so the cause must come from the run directories, not from the ledger.
4. **Diagnosed, not yet closed — the provenance column is empty and the cause is known:** `git_commit` is blank in all 120 rows of `results_runs.csv`. The cause is recorded in `implementation/tools/collect_results.py`: the manifest writes `git_sha` at top level, the collector previously read a different key, and the fix now composes `git_commit` from `git_sha` with a `-dirty` suffix preserved. The identifiers therefore exist in the per-run manifests and are absent only from the collected table, which is a materially weaker defect than the data being unrecorded. **Action:** re-run the collector over the archived run directories to populate the column, rather than enumerating manifests by hand. The SS checkout is already pinned in `cells.json` as `dxyang/seasplat @ ddc6259`, so that half of the item is closed.
4b. **Recorded — an asymmetry between the two provenance sources:** the ledger carries `NVIDIA A100-SXM4-40GB` for all 120 runs, whereas `results_runs.csv` leaves the GPU field blank for SS's twelve because the reference harness does not record it. §3.6's single-accelerator claim is therefore supportable from the ledger but not from the results table alone; cite the ledger for it.
5. **Methodological restriction:** Matching `s0`–`s2` suffixes do not establish paired stochastic draws between SS and A0; verify the reference seed routine and report the repetitions as independent unless a matching stochastic mechanism can be demonstrated.
6. **Partly closed — the configuration freeze is evidenced; the analysis plan's dating is not:** `implementation/configs/cells.json` carries the equivalence margin with an explicit note that it was fixed before S0 ran, and carries the `n_bud` rule stating that a budget which does not bind would make A4 equivalent to A1 and A7 to A5, “and a null interaction measured in that state is a configuration artifact”. That is contemporaneous evidence of a pre-specified decision rule inside the executed configuration. It does not date the wider analysis plan. **Action:** obtain the dated commit for the analysis-plan document before any test is called prospective; the ledger timestamps establish execution chronology only, as this item correctly states.
7. **Placement verified, and a consistency risk between the two assets:** `figures/figure-2-schedule.svg` belongs with the within-run iteration schedule in Section 3.5 or 3.6. Its eighteen labels were extracted and are internally consistent with the executed configuration — marks at 15 000, 20 000 and 22 000, “cut to 200 k · 200 medium-only steps”, a separate “CDF prune · 200 steps”, and “30 000 iterations · 43 000 optimiser steps (43 400 with M2's two bursts)”, which matches the step accounting used in Chapter IV. **The risk is that the two figures disagree:** the schedule asset distinguishes the two M2 events and the pipeline asset does not. Correct the pipeline figure rather than the schedule one. The Section 3.2 pipeline SVG requires the five corrections listed in its placeholder block before typesetting.

## 3.3 Dataset and evaluation inputs

### 3.3.1 Dataset provenance and scene selection

The evaluation uses four named scenes from the SeaThru-NeRF underwater image collection (Levy et al., 2023). Each scene supplies captured images and a COLMAP camera reconstruction used by the Gaussian scene loader. The repository's campaign specification lists Curasao, IUI3-RedSea, JapaneseGradens-RedSea, and Panama. Table 3.5 reports the input image and evaluation-view counts specified by the dataset reader and campaign plan. These counts describe the selected corpus, not independent subjects or an estimate of underwater scene diversity.

**Table 3.5. Selected SeaThru-NeRF scenes and nominal view partition.**

| Repository scene key | Captured views | Training views | Held-out evaluation views |
|---|---:|---:|---:|
| Curasao | 21 | 18 | 3 |
| IUI3-RedSea | 29 | 25 | 4 |
| JapaneseGradens-RedSea | 20 | 17 | 3 |
| Panama | 18 | 15 | 3 |
| **Total** | **88** | **75** | **13** |

*Source: `implementation/scene/dataset_readers.py` and `implementation/docs/experiment_plan.md`. Preserve the repository's `JapaneseGradens-RedSea` spelling in artifact paths even if prose uses a corrected geographic name. Confirm these nominal counts from the final run manifests before treating them as per-run facts.*

The four scenes provide the study's evaluated underwater conditions. The dataset paper motivates the use of captured underwater views for testing a scattering-aware radiance field (Levy et al., 2023). Claims that one scene has more backscatter or poorer visibility than another require a defined image or model diagnostic; scene labels alone do not establish those properties. Section 3.7 therefore identifies any measured scene-condition variables used to interpret results.

Figure 3.3 will show one input view per scene using a declared display transform. It provides visual context for the evaluated scenes and does not substitute for measurements of attenuation, scattering, or reconstruction error.

> **[FIGURE 3.3 PLACEHOLDER: REPRESENTATIVE INPUT VIEWS]** Four panels in the order of Table 3.5, each drawn from the training partition. State the image filename, whether the displayed input is the original white-balanced image or the COLMAP-undistorted output, and any shared exposure or display transformation. Caption: *Figure 3.3. Representative input views from the four evaluated SeaThru-NeRF scenes. Panels show [INSERT EXACT FILENAMES AND DISPLAY PROCESSING]; visual appearance is descriptive and does not quantify medium parameters.* Do not substitute a Chapter IV reconstruction comparison for an input-data illustration.

### 3.3.2 View partition and evaluation unit

The executed reader sorts cameras by image name and, when evaluation mode is enabled, assigns the camera at zero-based indices divisible by eight to the test partition (`llffhold = 8`). The remaining cameras form the training partition. On the nominal counts in Table 3.5, this produces four held-out views for IUI3-RedSea and three for each other scene. The reader contains a separate hard-coded list of scene-specific image names, but that list is commented out in the inspected implementation; it is not the active split rule. The resolved `eval` setting, `llffhold`, any subsampling or camera-range arguments, and the final partition sizes must be confirmed in the run records.

During training, camera poses and training images provide the observations from which Gaussian attributes and medium parameters are fitted. Held-out images serve as reference observations for rendered-view fidelity. A held-out image is an evaluation view of a scene represented by one trained model; it is not an independent training repeat. Chapter IV should therefore retain scene and run identifiers alongside per-view scores and should report repeat variation at the run level. The corpus does not include an independent validation partition in the stated design. [VERIFY FROM RUN CONFIGURATIONS: any exploratory tuning based on test scores must be disclosed rather than treated as validation-free selection.]

The same index rule can facilitate comparison with prior work, but matching the phrase “every eighth frame” does not establish pixel-for-pixel comparability with a published result. That stronger claim would require verifying the source method's exact filenames, image version, undistortion, resolution, crop, color processing, and metric conventions. Accordingly, external published scores are contextual references until those conditions are checked; the controlled comparisons in this study are among configurations evaluated through the same local harness.

### 3.3.3 Camera and initialization inputs

The reader consumes COLMAP extrinsics, intrinsics, and an associated sparse point cloud under each scene's `sparse/0` directory. For the supplied image set, the preprocessing utility locates white-balanced inputs under `images_wb` or `Images_wb`, undistorts an OPENCV camera model with COLMAP, and places the output images and pinhole reconstruction in the layout accepted by the reader. Section 3.4 specifies how these operations were carried out and how the prepared inputs were checked. This section names them as inputs because an image or camera-model mismatch changes the comparison independently of M1, M2, and M3.

A0, A2, A3, and A6 use the prepared sparse point cloud as their initial Gaussian source. The M1 configurations A1, A4, A5, and A7 use a separately prepared dense correspondence cloud for the same scene. That cloud must be reconstructed only from eligible training views if the held-out partition is to remain excluded from initialization. The dense cloud's realized provenance, hash, and per-scene count are checked in Section 3.4 rather than inferred from a prior draft. Camera normalization is computed from the training cameras in the inspected reader; its radius is 1.1 times the maximum distance from their mean center. The coordinate handling and any further scene scaling must be verified from the executed configuration before reporting a normalized physical distance.

### 3.3.4 Scope of the evaluation inputs

The four scenes and 13 held-out views define the observed evaluation domain. Three run repeats per cell and scene describe training variation under this domain; they do not add new independent scenes. The design can compare configurations on the same captured views, but it cannot by itself establish transfer to other cameras, water bodies, lighting conditions, or scene distributions. It also cannot validate medium coefficients as physical measurements unless independent ground truth or an adequate calibration procedure exists. These limits govern the analysis in Section 3.8.

### Editorial verification queue for Section 3.3 (outside thesis prose)

1. Verify the final manifest's `eval`, split sizes, image directory, camera restrictions, and scene spelling for all compared runs.
2. Extract exact held-out filenames from the resolved camera list, especially if undistortion changes the image set or ordering.
3. Confirm whether M1's offline matcher excluded all held-out images by inspecting dense-cloud sidecars and generation code.
4. Check dataset license and image credit before selecting the four Figure 3.3 panels.
5. Avoid claiming identical evaluation pixels with published methods until preprocessing and metric conventions are verified for each method.

## 3.4 Data preprocessing

The preprocessing stage makes the supplied COLMAP scenes compatible with the Gaussian renderer and produces the alternative initialization input for M1. Its outputs are prepared per scene and used across relevant configurations. Table 3.6 separates the transformations from their checks and downstream users. The methodological distinction is that camera undistortion applies to every configuration, while dense correspondence generation applies only to M1 configurations.

**Table 3.6. Preprocessing operations and evidence needed for comparison.**

| Operation | Input and output | Implemented check or record | Used by |
|---|---|---|---|
| Camera undistortion | Original white-balanced images and OPENCV COLMAP reconstruction to undistorted images and pinhole reconstruction | `undistort.json` records camera models and input/output image counts; startup checks accept only `PINHOLE` or `SIMPLE_PINHOLE` | Every configuration |
| View partition | Image-name-sorted cameras to training and held-out lists | Loader uses index modulo eight when `eval` is enabled; run configuration records resolved partition sizes [VERIFY PER-RUN RECORD] | Training, evaluation, and M1 cloud generation |
| Sparse cloud loading | COLMAP `points3D` to initial Gaussian point cloud | Reader loads `sparse/0/points3D.ply`, converting the binary or text points if needed | Configurations without M1 |
| Dense cloud generation | Undistorted training views and cameras to colored `.ply` and metadata sidecar | Sidecar records matching settings, exclusion count, filtering, point count, elapsed time, and cloud hash [VERIFY FINAL SIDECARS] | A1, A4, A5, A7 |

### 3.4.1 Camera rectification and scene layout

The original scene reconstructions use COLMAP's `OPENCV` camera model. The inspected reader implements only `PINHOLE` and `SIMPLE_PINHOLE`; passing an unrectified scene to it raises an error. The `source/undistort.py` utility calls COLMAP's `image_undistorter`, using the source image directory and sparse reconstruction, and writes a compatible image set and camera reconstruction. It moves the generated sparse reconstruction into `sparse/0`, the directory expected by the scene reader. The utility checks whether an output scene has already been rectified before processing it again, preventing an inadvertent second resampling.

The prepared scene has an `images` directory. The original input directory is commonly `images_wb`; for IUI3-RedSea its capitalization is `Images_wb`. The utility matches that directory without depending on capitalization. Its `undistort.json` reports the input and output image counts, camera model and dimensions before and after rectification, and any sparse-directory relocation. These records should be inspected for each scene alongside the loaded camera counts. A warning about an image-count mismatch does not by itself abort the preprocessing utility, so the absence of an exception is insufficient evidence that all views survived unchanged.

The reader sorts loaded cameras by image name and then partitions them as described in Section 3.3. It computes a scene center and radius from the training cameras for renderer normalization. The input camera poses and point cloud must remain in a consistent coordinate system after rectification. Section 3.6 checks that all compared runs consumed the same prepared scene and partition; this cannot be assumed from a common scene name alone.

### 3.4.2 Sparse initialization input

For configurations without M1, the reader loads the sparse COLMAP point cloud from the prepared scene. If the `.ply` is absent, it converts `points3D.bin` or `points3D.txt` to `.ply`; it then reads positions and RGB values. This step establishes the baseline's starting geometry. The prepared PLY headers report 25,837 points for Curasao, 21,907 for IUI3-RedSea, 21,140 for JapaneseGradens-RedSea, and 22,501 for Panama. These are input-cloud counts, not the final Gaussian populations. The renderer's conversion from input point to Gaussian attributes, and any later density control, are specified in Section 3.5 because they are part of the model rather than a camera-data transformation. Per-run input identity and any further filtering remain subject to manifest checks.

### 3.4.3 Dense correspondence cloud for M1

The M1 preprocessing path runs `source/roma_init.py` once for each scene used by M1. It loads the same prepared COLMAP scene with evaluation mode active and selects only training cameras as candidate references and neighbors. It caps the number of reference cameras at the available training-view count. For each reference, a pretrained RoMa matcher generates dense correspondences with nearby cameras; the script selects the most confident neighbor for each sampled reference pixel and triangulates candidate 3D points. It colors surviving points from the reference image. This is an adaptation of correspondence-based initialization, not a claim that the complete EDGS training method was reproduced (Kotovenko et al., 2026; Edstedt et al., 2024).

Candidate points are retained only when their maximum two-view reprojection error is below the configured pixel threshold, they lie in front of both cameras, and their triangulation angle reaches the configured minimum. The four final cloud sidecars record thresholds of 8 pixels and 1 degree. The latter two tests matter in this forward-view setting because a small reprojection error alone does not guarantee a well-conditioned depth estimate. This is a geometric rationale for the filter, not evidence that all surviving points are physically correct. The script exposes two sampling presets and several matcher overrides. All four inspected sidecars record the `dense` preset: 20,000 sampled matches per reference, three candidate neighbors per reference, certainty threshold 0.02, RoMa `outdoor` model, and seed 0. The resulting retained point counts are given in Table 3.7. The sidecars also record `fused_local_corr: false` and an unavailable `local_corr` module; the exact matcher weight release still needs verification. The recorded settings and counts describe the archived assets, while cross-run consumption requires a separate manifest check.

The generation script seeds the matcher-related random generators and writes the resulting `.ply` with a metadata sidecar. The recorded fields include requested and realized reference count, training and excluded held-out view counts, sampling and filtering parameters, rejection counts, wall time, and the correlation implementation used by the matcher. The cloud hash is intended to link subsequent training runs to the exact initialization asset. Verify that the run manifest's cloud hash equals the sidecar and file hash before claiming identical initialization across repeats. Offline matching and triangulation time are measured separately from training wall time; a total cost comparison involving M1 should identify whether this one-time preprocessing expense is included, amortized, or reported separately.

**Algorithm 3.1. Offline construction of a dense correspondence cloud.**

```text
Input : rectified scene and training-view set V_tr; RoMa settings;
        seed s; reference cap K; samples per reference M
Output: colored point cloud P and metadata sidecar R
 1: Seed the generators; load only V_tr with evaluation split enabled
 2: Select min(K, |V_tr|) reference cameras by pose-based K-means
        (use all cameras when the cap covers V_tr)
 3: Initialize P ← ∅ and the filtering counters ← 0
 4: for each reference camera r do
 5:     Select three nearest training cameras by camera-matrix distance
 6:     Run the RoMa matcher for each pair (r, neighbor)
 7:     For every reference pixel, choose the neighbor with maximum
            match certainty; sample up to M correspondences
 8:     if sampling fails for r then continue end if
 9:     Group sampled matches by their selected neighbor
10:     for each nonempty group (r, n) do
11:         Triangulate points from the two calibrated views
12:         Keep a point only if maximum two-view reprojection error
                < 8 pixels, both camera depths > 0, and parallax ≥ 1°
13:         Append kept positions and RGB sampled from r to P
14:     end for
15: end for
16: if P is empty then report failure end if
17: Save P as PLY; write R with split counts, settings, filtering
        counts, elapsed time, and the recorded cloud SHA-256
```

The four archived clouds used the `dense` preset ($M=20{,}000$, certainty threshold $0.02$), RoMa `outdoor` model, and seed 0. The operation ran once per scene before M1 training; Algorithm 3.2 describes how a run consumes the resulting asset. The sidecars record whether the optional fused correlation path was available. The algorithm describes the archived preprocessing path and does not imply that each training seed generated a separate cloud.

> **[FIGURE 3.4 PLACEHOLDER: DENSE INITIALIZATION AUDIT]** If the final sidecars and outputs are available, show one scene's training-view selection and filtered correspondence cloud alongside the sparse COLMAP cloud. Label the view pair, retained point count, and coordinate convention. Caption: *Figure 3.4. Sparse and dense initialization inputs for [SCENE], before Gaussian optimization. The dense cloud contains only correspondences formed from the training partition; filtering and point counts follow the archived sidecar.* If a reliable geometry visualization is unavailable, use Table 3.6 and a per-scene count table instead; do not fabricate a schematic as execution evidence.

### 3.4.4 Frozen inputs and leakage checks

All factorial configurations for a scene should use the same rectified images, camera poses, training/test partition, and sparse reconstruction where applicable. M1 cells should share the same generated dense cloud for that scene. A training view may contribute to optimization and to construction of that cloud; a held-out view should contribute to neither. The code's use of `info.train_cameras` supports the intended exclusion, but final verification requires the sidecar's excluded-view count and the training-run provenance. A hash recorded for one cloud does not establish that its camera or image inputs were unchanged unless those inputs are separately versioned or the preparation record can be reconstructed.

Table 3.7 reports the prepared scene files and dense-cloud sidecars in Drive. Each `undistort.json` records equal input and output image counts and a change from `OPENCV` to `PINHOLE`. The sidecar counts are after the parallax filter. These asset-level records do not by themselves prove that every training run used the same bytes; compare the corresponding run manifest and input hashes before making that broader claim.

**Table 3.7. Preprocessed scene and dense-cloud provenance from archived assets.**

| Scene | Original and rectified camera model | Images in/out | Train/test filenames or manifest | Sparse points | M1 cloud points | Cloud SHA-256 | Matcher preset and seed | Preprocessing time |
|---|---|---|---|---:|---:|---|---|---:|
| Curasao | `OPENCV` → `PINHOLE` | 21/21 | 18/3 in cloud sidecar; filenames [VERIFY] | 25,837 | 292,707 | `efbdba479fca00121953b76cdcb9f8814e245f92bdb689bb14b47cbcf9527477` | `dense`, seed 0 | 52.8 s |
| IUI3-RedSea | `OPENCV` → `PINHOLE` | 29/29 | 25/4 in cloud sidecar; filenames [VERIFY] | 21,907 | 288,609 | `bfc24d317217be7a5e37c85cd3c73c9186d8b8ec1f80da36a93d0b7288c438bd` | `dense`, seed 0 | 48.2 s |
| JapaneseGradens-RedSea | `OPENCV` → `PINHOLE` | 20/20 | 17/3 in cloud sidecar; filenames [VERIFY] | 21,140 | 293,642 | `e9f3655dcca2b0f8e18dc66c48418525df35bc9ab721b2d5a98cc088a2b349d8` | `dense`, seed 0 | 35.1 s |
| Panama | `OPENCV` → `PINHOLE` | 18/18 | 15/3 in cloud sidecar; filenames [VERIFY] | 22,501 | 244,197 | `2c84d9baff0a3784a23792f318a8953c538694ca87faa73b25021ffdf2387788` | `dense`, seed 0 | 38.2 s |

*The sparse counts come from `dataset/undistorted/<scene>/sparse/0/points3D.ply` headers; the dense counts, seeds, hashes, and times come from `dense/<scene>.json`. Hashes are recorded sidecar values pending independent file-byte verification. The sidecar's training/test numbers give split sizes, not an archived filename manifest. Preprocessing times exclude subsequent model training.*

### Editorial verification queue for Section 3.4 (outside thesis prose)

1. Check the undistortion logs, if available, for warnings; the four `undistort.json` records already show matching input and output counts, but do not establish pixel-level equality after rectification.
2. Recompute the four dense PLY hashes and compare sidecar hashes with `run_config.json` for every M1 run in each scene.
3. Identify the exact matcher model release or weight file and any unrecorded command-line overrides; the preset and correlation fallback are recorded in the sidecars.
4. Verify that held-out filenames are absent from the matcher input list and that no earlier dense cloud was substituted after the parallax-filter change.
5. Confirm preprocessing time boundaries before making any end-to-end efficiency claim about M1.

## 3.5 Baseline and efficiency mechanisms

### 3.5.1 Baseline representation and underwater rendering

The refactored baseline A0 initializes an explicit set of Gaussian primitives from the prepared sparse COLMAP cloud. Each primitive has a 3D position, scale, rotation, opacity, and direct-current color coefficients. With spherical-harmonic degree zero, the representation has 14 scalar float attributes per primitive before additional file metadata or compression. The model renders a color image, opacity, and depth for a selected training camera. The source SeaSplat implementation, denoted SS, is evaluated separately under the reference protocol. The distinction between A0 and SS is retained throughout Chapters III and IV (Yang et al., 2025; Kerbl et al., 2023).

Once the underwater branch activates, the color render is interpreted as estimated medium-free radiance, $\hat{J}$. The implementation obtains a depth image from a separate rasterization pass, divides the depth accumulation by accumulated opacity on covered pixels, and normalizes the result per view. Distinct attenuation and backscatter model components act on that normalized depth. In schematic notation, the resulting observation is

$$
\hat{I}=\hat{J}\odot A(\hat{Z};\boldsymbol{\beta}_{\mathrm{att}})
        +B(\hat{Z};\boldsymbol{\beta}_{\mathrm{bs}},\mathbf{B}_{\infty}),
$$

where $\hat{I}$ is the composed image compared with the capture, $\hat{Z}$ is rendered and normalized depth, $A$ is direct-signal attenuation, and $B$ is modeled backscatter. The two coefficient groups are distinct. This equation gives the dependency structure; the exact activation, clamping, per-channel operations, and normalization order must follow `implementation/train.py` and `deepseecolor/models.py` in the final mathematical specification. Do not treat the fitted coefficients as calibrated physical attenuation without independent validation.

Training begins with a geometry-only regime and switches to medium-aware composition after the configured threshold. The code enables `do_seathru` and sets `seathru_from_iter` to 10,000 in the shared cell configuration; the training loop checks `iteration > seathru_from_iter`. The total objective combines image reconstruction with depth, backscatter, color, saturation, opacity, and smoothness terms from the refactored SeaSplat training path. Its exact active terms and coefficients are configuration-dependent and will be stated in a verified loss table rather than copied uncritically from an earlier method note. All three primary mechanisms retain this baseline objective in the intended factorial design; M3 changes the attributes used during the forward render, and D changes a density-control gradient route. [VERIFY AGAINST RUN MANIFESTS AND `train.py`: every active coefficient and conditional branch.]

**Table 3.8. Baseline rendering and optimization specification [TO COMPLETE FROM EXECUTED CONFIGURATION].**

| Component | Implemented choice to document | Evidence anchor |
|---|---|---|
| Primitive attributes | Position, scale, rotation, opacity, zero-order color | `scene/gaussian_model.py`; resolved `sh_degree` |
| Color and depth rendering | Color pass, depth/opacity handling, per-view normalization | `gaussian_renderer`; `train.py`; `utils/depth_stats.py` |
| Medium formation | Attenuation, backscatter, channel constraints, scene-level parameters | `deepseecolor/models.py`; `train.py` |
| Reconstruction and auxiliary losses | Active term, weight, activation phase, gradient destination | `train.py`; resolved options in `run_config.json` |
| Density control | Densification, pruning, opacity reset, optimization schedule | `train.py`; resolved options |
| Model outputs | Final checkpoint or point cloud, medium parameters, quantized artifact where applicable | Saved run directory and evaluation record |

### 3.5.2 M1: dense correspondence initialization

M1 replaces the initial sparse point cloud with the scene-specific dense correspondence cloud specified in Section 3.4.3. It turns off Gaussian densification during subsequent training. The resulting intervention changes both the starting spatial distribution and the population-growth pathway; an M1 versus A0 contrast cannot isolate those two subcomponents. The method is adapted from EDGS's dense initialization concept, with RoMa correspondences, but the filter, source-view count, opacity schedule, and retained pruning path follow this implementation rather than the source paper by name (Kotovenko et al., 2026; Edstedt et al., 2024).

Training with M1 still permits scheduled opacity-based removal. The implementation positions an opacity-decay gate relative to the medium-aware phase so that the early geometry-only objective does not exhaust the dense population before the medium term becomes active. That schedule was revised during development; describing a previous gate as the executed method would mischaracterize all M1 cells. State the realized `m1_decay_after_seathru`, opacity-decay rate, pruning threshold, reset behavior, and learning-rate clamp from each run manifest. Because densification is disabled, a cloud that falls below the M2 budget would make simplification ineffective in A4 and A7. The preflight check compares the cloud's PLY vertex count with the configured budget before training starts.

**Algorithm 3.2. Dense correspondence initialization for M1.**

```text
Input : precomputed scene cloud P_dense and metadata R_dense;
        M1 configuration; optional M2 budget B
Output: initialized Gaussian set G and density-control configuration
 1: Resolve the scene-specific P_dense and R_dense
 2: Load P_dense and initialize G from its positions and colors
 3: if M2 is enabled then require B < |P_dense| end if
 4: Disable training-time clone/split densification for M1
 5: Retain scheduled opacity-based removal and applicable resets
 6: Train G under the shared baseline objective and M1 schedule
```

Algorithm 3.1 specifies the separate preprocessing procedure and Table 3.7 gives its archived outputs. Cloud identity across all M1 repeats still requires comparing the run manifests and asset hashes.

### 3.5.3 M2: importance-weighted spatial simplification

M2 implements the population-reduction part of Mini-Splatting, without its depth reinitialization and blur-driven splitting (Fang & Wang, 2024). The code accumulates each primitive's rendering contribution over the training views. In the configured `outdoor` mode, its importance adds blending weight divided by projected area only for a view in which that primitive is recorded as a dominant pixel contributor. Primitives with no dominant contribution across training views receive zero importance. This choice is an adaptation: the source's motivation for the area-normalized mode does not establish that it is optimal for the underwater far field. The study tests the selected mode; it does not compare it against every alternative importance definition.

The two M2 events have different selection rules. At iteration 15,000, the implementation samples without replacement with probability proportional to positive importance, targeting at most the configured budget of 200,000 eligible primitives. If fewer eligible primitives exist, the achieved count can be below the target. At iteration 20,000, it uses a cumulative-importance mask configured to retain the upper 99% of importance mass. Therefore the phrase “cut to 200,000 twice” would be incorrect. Both events remove primitives and require the optimizer's parameter groups to remain aligned with the surviving set. The first event's binding condition and the actual post-event population must be reported from run diagnostics.

After each M2 event, the training code schedules 200 extra medium-only optimization steps with Gaussian geometry held fixed. This is an implemented re-identification attempt, not an established correction for medium-model drift. Its effectiveness belongs in Chapter IV. The shared configuration disables the optional M2 learning-rate rewind (`m2_lr_rewind = false`); earlier combined-method diagrams that show the rewind as active are outdated for this configuration. The effect of M2 combines selection, event timing, and medium-only continuation. Without a separate no-continuation cell, the factorial contrast does not identify those components individually.

**Algorithm 3.3. Scheduled M2 simplification and medium continuation.**

```text
Input : Gaussian set G; training views V_tr; event index t;
        budget B = 200,000; retained mass q = 0.99
Output: pruned Gaussian set G and aligned optimizer state
 1: if t ∉ {15,000, 20,000} then return G end if
 2: Record pre-event diagnostics
 3: Initialize per-primitive importance w and dominant count a to zero
 4: for each v ∈ V_tr do
 5:     Render v without gradient tracking
 6:     Accumulate w using blending weight / max(projected area, 1)
            only for primitives dominant in v; accumulate a
 7: end for
 8: Set w_i ← 0 for every primitive with a_i = 0
 9: if t = 15,000 then
10:     Sample min(B, #{i : w_i > 0}) indices without replacement,
            with probabilities proportional to positive w_i
11: else
12:     Sort w in ascending order; discard indices whose cumulative
            mass remains below (1 − q) times total importance
13: end if
14: Prune G and align its optimizer state; align or invalidate any
        existing per-primitive quantization assignments
15: Record post-event diagnostics; schedule 200 medium-only steps
        with Gaussian geometry fixed; record continuation diagnostics
16: return G
```

### 3.5.4 M3: in-training attribute quantization

M3 applies vector quantization to three raw Gaussian parameter groups: direct-current color, scale, and rotation. `source/quantize.py` constructs a codebook for each group, assigns a codeword index per primitive, and exposes a straight-through quantized value to the forward render while retaining trainable underlying parameters. Scale is quantized before its exponential activation and rotation before normalization. Position and opacity stay unquantized. The baseline uses spherical-harmonic degree zero, so it has no higher-order coefficients to place in a corresponding codebook. This intervention is a restricted adaptation of the source vector-quantization approach, not the source method's full compression system (Navaneet et al., 2024). [VERIFY ALIGNMENT WITH CURRENT CHAPTER II REFERENCE LIST.]

The configured activation gate is at iteration 22,000, after both M2 events. The shared configuration specifies 4,096 codewords per group, assignment refresh every 100 iterations, and one codebook-update iteration. The inspected training loop activates M3 when `iteration > kmeans_st_iter`; its exact first active optimizer step should be reported using that inequality rather than describing 22,000 as an active quantized iteration. On a simplification event, assignment vectors must remain aligned with surviving primitives and are invalidated for reassignment. Because M2's scheduled events precede M3 activation in this configuration, that integration guard primarily prevents a future schedule change from producing stale assignments.

At zero-order color, the 14-float baseline has ten scalars in the three quantized groups and four unquantized position/opacity scalars. The `storage_report` calculates index and codebook bits together with the four-float remainder. This analytical bit count is distinct from the actual serialized artifact size, which also depends on file encoding, headers, and any additional stored state. Section 3.7 measures both with separate names and denominators. The source opacity regularizer is not introduced as an M3-specific loss in this factorial design; verify its resolved weight is zero across M3 cells before claiming that only the attribute encoding changed.

The trained model contains continuous underlying attributes and the codebook assignments used by the quantized forward path. Evaluation or restoration checks of M3 must apply the saved codebook state before rendering; reading a saved point cloud's continuous attributes alone does not reconstruct the quantized state used during training. The final protocol should identify the artifact, loader, and state-switch used for each reported image and metric, with a same-checkpoint consistency check before comparing continuous and quantized renderings. [VERIFY AGAINST FINAL EVALUATION AND RELOAD CODE.]

**Algorithm 3.4. M3 attribute substitution during training.**

```text
Input : iteration t; raw Gaussian parameters G; M3 flag;
        codebooks C and cached assignments z
Output: rendered training image and updated parameters
 1: if M3 is enabled and t > 22,000 then
 2:     for each group g ∈ {DC color, raw scale, raw rotation} do
 3:         if z_g is absent or an assignment refresh is due then
 4:             Reassign each parameter vector to its nearest codeword
 5:         else
 6:             Update codeword centers using the cached assignments
 7:         end if
 8:         Substitute the assigned codeword using a straight-through
                quantized value in the rendering path
 9:     end for
10: end if
11: Render and optimize with the baseline training objective
12: Retain position and opacity as unquantized trainable fields
13: At final save, serialize codebooks, assignments, and remaining
        fields according to the implemented compressed-artifact path
```

### 3.5.5 Composition, timing, and supplementary D

The intervention order is initialization before training, M2 at its scheduled population events, and M3 after those events. Figure 3.5 locates these events on the nominal 30,000-iteration axis, including the transition to the medium-aware loss. The figure is a schedule of operations within one run, not the order in which cells S1 to S6 were completed. It labels a larger effective optimizer-step count than the nominal iteration count because some medium optimization steps do not advance the main iteration counter; the actual count for a particular run must come from its evaluation cost record.

> **[INSERT EXISTING VECTOR FIGURE 3.5]** Repository asset: [`figures/figure-2-schedule.svg`](https://github.com/dinanirham/An-Efficient-3D-Gaussian-Splatting-for-Underwater-3D-Reconstruction/blob/main/figures/figure-2-schedule.svg). PNG fallback: `figures/figure-2-schedule.png`. Caption: *Figure 3.5. Nominal training-iteration schedule of the baseline loss transition and the M2 and M3 interventions. M1 changes initialization and density control; D changes the density-control gradient in A0D. Extra medium-only optimizer steps are recorded separately from nominal iterations.* Audit the figure's printed effective-step values against per-run records before inclusion.

The paired cells combine mechanisms according to Table 3.1. M1 plus M2 is subject to the budget-binding check. M2 plus M3 uses the post-simplification population before quantization starts. A7 applies all three in that same order. A0D is outside this composition: it changes whether an opacity-derived gradient contributes to the screen-space signal used by adaptive density control. M1 disables densification, so D has no intended density-control recipient when M1 is enabled. The supplementary A0D versus A0 comparison tests D where that path is active; it does not add a fourth factor to the eight-cell matrix or justify a four-factor interaction claim. This concerns the identified gradient path, not every possible side effect of a hypothetical combined run.

**Algorithm 3.5. Screen-space gradient routing in A0 and A0D.**

```text
Input : camera v; Gaussian set G; configuration c ∈ {A0, A0D}
Output: training loss and screen-space statistics for density control
 1: Render color with screen-space buffer p_color
 2: if c = A0 then
 3:     Render the separate alpha probe with p_color shared
 4: else  // A0D sets detach_alpha_gradient = true
 5:     Render the separate alpha probe with its own buffer
 6: end if
 7: Render depth with a separate screen-space buffer in both cells
 8: Compute the same configured training losses and backpropagate
 9: During the density-control window, accumulate visible-primitives'
        screen-space gradient statistics from p_color
10: Apply the baseline densification/pruning schedule to G
```

Both cells use the separate alpha probe and separate depth pass. A0 shares the color pass's screen-space buffer with the alpha probe, allowing alpha-derived gradients into the buffer read by density control. A0D gives that probe its own buffer; the alpha loss can still affect trainable Gaussian parameters through the probe, so D is specifically a change in the density-control signal, not a global removal of the alpha loss. The depth probe has its own buffer in both cells. Confirm the resolved `separate_alpha_probe` and `detach_alpha_gradient` flags in the run manifests before claiming this route for every execution.

### 3.5.6 Implementation decisions and source-method boundary

The names M1, M2, and M3 specify implemented mechanisms and protect the distinction from their cited sources. M1 uses correspondence initialization with study-specific filtering and a constrained view count. M2 uses Mini-Splatting's importance-based reduction without its population-regrowth procedures. M3 uses three codebooks and a zero-order-color baseline, excludes position and opacity, and must be assessed with actual serialized bytes. The modifications are evaluated together with SeaSplat's medium-aware optimization. Table 3.9 records differences that a reader needs to interpret each contrast. Its scope labels distinguish adaptations, components omitted from this study, and settings imposed by the dataset or baseline; the exact source-method behavior and executed options must be checked before a row is treated as a documented departure.

**Table 3.9. Mechanism lineage and implemented scope.**

| Mechanism | Source-method element adopted | Deliberate limitation or integration decision | Code anchor |
|---|---|---|---|
| M1 | Dense correspondence-derived initialization | Training-view-only generation; reprojection, cheirality, and parallax filtering; densification disabled and configured opacity pruning retained | `source/roma_init.py`; `train.py` |
| M2 | Importance-weighted population reduction | First event samples to budget; second applies a cumulative-importance mask; source depth reinitialization and blur splitting omitted; medium-only continuation added | `source/simplify.py`; `train.py` |
| M3 | In-training vector quantization with straight-through substitution | Three codebooks for color, raw scale, and raw rotation; no higher-order spherical harmonics, position, or opacity codebook | `source/quantize.py`; `source/storage.py`; `train.py` |
| D | Gradient routing within the refactored baseline | Supplementary A0D contrast, excluded from factorial combinations | `train.py`; `configs/cells.json` |

The implementation register should additionally record the rasterizer and gradient-routing decision at the baseline, the M1 opacity-reset and position-learning-rate behavior, the codebook initialization and empty-cluster rule, and the M3 opacity-regularizer setting. These are integration choices that can change measured populations or compressed-state behavior. Their executed values and source-method lineage require code and manifest checks before this table is finalized. The extra medium-only interval after each M2 event belongs to this study's combined implementation and is inseparable from the measured M2 factor.

This table states the implementation's scope, not equivalence with any full published method. Exact causal attribution remains conditional on matched settings, realized events, checkpoint lineage, and measurement coverage described in Sections 3.6 to 3.8.

### Editorial verification queue for Section 3.5 (outside thesis prose)

1. Resolve all source-method author, year, and venue entries against the locked Chapter II papers, including the quantization source.
2. Extract the active loss branches, coefficients, gradient detach points, and medium-model activations from the recorded code and per-run configuration before finalizing Table 3.8 or a full equation.
3. Verify the M1 opacity schedule, M2 achieved counts and event timing, M3 first active iteration, codebook settings, and final storage decoder from each applicable run.
4. Compare the effective optimizer-step totals and medium-only continuation in Figure 3.5 with the per-run `eval_metrics.json` cost records.
5. Confirm that `m2_lr_rewind` is false and any M3-only opacity regularizer is disabled in the executed manifests; the earlier combined-method notes contain superseded prospective paths.

## 3.6 Experimental design and execution

### 3.6.1 Configuration matrix and comparison references

The principal design crosses M1, M2, and M3 at two levels each, producing the eight configurations A0 to A7 in Table 3.1. Each scene is evaluated under all eight configurations. Three repeat identifiers, 0, 1, and 2, define separate training executions for each scene and configuration. This yields 96 factorial runs. A0D adds 12 supplementary runs and SS adds 12 reference runs, bringing the completed campaign to 120 runs. Run completion does not imply that every optional diagnostic or cost measurement is present or that every contrast is comparable; those properties require a separate artifact and provenance check.

The contrast for each intervention alone is its corresponding single-factor cell against A0. The remaining cells support conditional effects and factorial interactions as defined in Section 3.8. SS is compared with A0 to assess the refactored baseline under stated margins, but SS is not a ninth corner of the factorial design. A0D is compared only with A0. The labels s0, s1, and s2 on SS and A0 are repeat identifiers; they should not be treated as paired random realizations merely because the filenames match.

**Table 3.10. Planned comparison sets and inference boundaries.**

| Question | Configurations | Comparison unit | Boundary |
|---|---|---|---|
| Refactored baseline check | SS and A0 | Scene means over independently executed repeats | Margin and its chronology must be established; matching suffixes do not imply pairing |
| Individual M1, M2, M3 effects | A1, A2, A3 versus A0 | Within-scene run summaries | M1 changes initialization and densification together; M2 includes medium-only continuation |
| Two-factor composition | A4, A5, A6 and corresponding lower-order cells | Within-scene contrasts on a specified metric scale | All four required cells must have comparable measurements |
| Three-factor composition | A0 to A7 | Within-scene eight-cell contrast | Requires complete comparable matrix and uncertainty across repeats |
| Supplementary gradient routing | A0D versus A0 | Within-scene run summaries | Not included in M1 to M3 factorial estimates |

The study fixes one reported operating point for the M2 budget and one codebook-size setting for M3. Variation across the eight configurations describes observed trade-offs at these settings. It does not test budget sensitivity within M2 or codebook-size sensitivity within M3. A claim of sustained superiority across resource budgets would require additional operating points.

### 3.6.2 Shared settings and intervention schedule

The inspected `configs/cells.json` defines a nominal 30,000 iterations; enables the underwater branch and evaluation split; sets the medium-model threshold to 10,000; places M2 events at 15,000 and 20,000 with 200 additional medium-only steps after each; and sets M3's gate to 22,000. It specifies a 200,000-primitive M2 budget, three 4,096-entry M3 codebooks, assignment refresh every 100 iterations, and one codebook-update iteration. The shared evaluation checkpoints are listed as 7,000, 15,000, 22,000, and 30,000, with a final model save at 30,000 in the inspected configuration. Figure 3.5 depicts the event order. The command-line parser can override cell-file values, so these settings describe the configuration source and must be checked against the resolved values in `run_config.json` before being stated as universal properties of the executed runs.

The M2 budget was selected under a binding rule: it should be below the initial dense-cloud population in M1 plus M2 cells. The code's preflight check rejects an M1 plus M2 run if the specified budget is at least the cloud's vertex count. This is a necessary condition for the budget to matter at initialization; the actual achieved count and whether the event changed the trained population remain empirical quantities. Dense cloud creation occurs offline and precedes M1 training. The training run records effective optimizer steps separately from the nominal iteration counter because baseline medium updates and M2 continuation steps can add optimizer work without advancing that counter.

### 3.6.3 Execution environment and run control

The worker obtains the next eligible cell, scene, and repeat from a persistent ledger. `run_ledger.py` schedules lower-numbered stages before later stages when their work is runnable, and it records attempts and status. `run_queue.py` launches a command with the selected cell and explicit repeat index and writes output to `runs/<cell>/<scene>/s<repeat>/`. The queue can reclaim a stale running entry after an interrupted session. The intended recovery is a new run from the beginning, because the legacy checkpoint does not restore all medium, quantizer, and schedule state required to continue the same execution. An archived partial attempt must not be mixed with the final attempt's diagnostic trajectory.

The archived ledger records NVIDIA A100-SXM4-40GB for all 120 entries. Its first start timestamp is 15 September 2026 at 13:54:53 UTC and its last finish is 21 September 2026 at 15:09:13 UTC. It labels seven stages, S0 to S6. Summing the recorded final-attempt `wall_seconds` gives 385,353.2 seconds (107.04 hours). This is a sum of run wall times, not a measured total of GPU utilization or a complete accounting of discarded attempts. The queue and preflight code require an A100 unless an explicit override is used. The run manifest is designed to record GPU name, software versions, resolved arguments, and a Git commit hash with a `-dirty` marker when applicable. A `-dirty` suffix establishes that the working tree contained changes; the hash alone does not recover those changes. The manuscript reports a blank collected per-run commit field for all 120 runs; the present collector code reads a `git_sha` field and appears to correct that earlier extraction mismatch. Table 3.11 must therefore distinguish a blank historical result-table column from the code identifier retained in each actual manifest. The ledger's continuous execution window supports, but does not establish by itself, identical implementation state. Section 3.6.6 specifies the reproducibility record.

**Table 3.11. Ledger-level run inventory and remaining provenance checks.**

| Configuration set | Scenes | Repeat indices | Ledger status and attempts | Final evaluation and checkpoint | Code identifier and dirty state | GPU and software | Input and dense-cloud hashes, if applicable | Effective optimizer steps |
|---|---|---|---|---|---|---|---|---|
| SS, A0–A7, A0D (12 each) | Curasao, IUI3-RedSea, JapaneseGradens-RedSea, Panama (30 each) | 0, 1, 2 (40 each) | 120 `done`; 116 × 1 attempt, 3 × 2, 1 × 3 | [VERIFY PER-RUN FILES] | [VERIFY PER-RUN MANIFESTS] | A100-SXM4-40GB in all ledger entries; software [VERIFY] | [VERIFY PER-RUN MANIFESTS] | [VERIFY PER-RUN METRICS] |

*The ledger identifies each final run by cell, scene, repeat, stage, attempt count, timestamps, and output directory; it does not establish artifact completeness, code identity, or metric coverage. Retain a one-row-per-run appendix after reconciling those files. For SS, record the separate source checkout and its different seeding behavior.*

### 3.6.4 Baseline correspondence and campaign lineage

A0 represents the refactored study baseline. The SS runs use the original SeaSplat source checkout as a separate reference. The cell configuration contains candidate baseline margins of 1.0 dB for pooled PSNR, 0.02 for LPIPS, and 30% for Gaussian count, with a note asserting that the margins were fixed before the SS runs. The analysis plan also records a margin check as already known when that plan was written. These sources indicate the intended comparison, but a prospective equivalence claim requires verification of their dated versions relative to run execution. Section 3.8 specifies how a margin verdict is calculated, including whether all metrics and scenes satisfy it. A small difference or a nonsignificant test by itself is not evidence of equivalence.

The 120-run campaign is the analysis population. Each reported comparison must trace to its run configuration, evaluation record, and applicable diagnostic or resource record. Code identifiers, preprocessing inputs, checkpoints, and measurement procedures remain comparison-level provenance checks.

### 3.6.5 Repeats, independence, and recorded deviations

The run is the repeated training unit within a cell and scene. Distinct random seeds are intended to expose optimization variability, but deterministic seed labels do not guarantee identical CUDA execution or pairing across implementations. Multiple held-out frames rendered from one run are repeated observations of the same fitted scene representation. Their scores can be aggregated per run or described per view, but they should not inflate the number of independent training repeats. Scene-specific summaries preserve differences in input view count and conditions; a mean across the four scenes is a descriptive aggregate and must state its weighting.

Four ledger entries had more than one attempt: A0/JapaneseGradens-RedSea/s0 (two), A3/IUI3-RedSea/s1 (three), A3/JapaneseGradens-RedSea/s2 (two), and A6/JapaneseGradens-RedSea/s0 (two). These counts identify cases for attempt-specific artifact inspection; they do not establish why a retry occurred. Any missing artifact, retry, code change, mismatched dense cloud, hardware override, different checkpoint, or metric unavailable for one configuration affects comparison eligibility. Section 3.7 defines measurement coverage, and Section 3.8 admits a contrast only when its participating cells share the required scene, evaluation inputs, checkpoint policy, and outcome definition. The 120 completed runs should be mapped to physical directories, final evaluation JSON files, and attempt-specific logs. A run can be complete while an optional diagnostic is missing or belongs to an earlier attempt.

### 3.6.6 Reproducibility record

The reproducibility unit is a completed run identified by configuration, scene, repeat index, and final attempt. The campaign ledger defaults to indices 0, 1, and 2, and `run_queue.py` passes the index as `--seed` to the refactored trainer or the separate SS reference runner. In the inspected refactored implementation, `safe_state` seeds Python's `random`, NumPy, PyTorch CPU, and all PyTorch CUDA generators with that value. The SS reference accepts the seed argument but does not seed its CUDA generator through the same path. Thus equal labels across SS and A0 do not define paired stochastic draws. GPU rasterization and density control can also vary between repetitions despite fixed seeds; the three executions quantify observed run variation rather than certify bitwise reproducibility. Record the realized seed, seeding routine, and reference checkout for each run rather than describing all ten configurations as having identical randomness controls.

For each run, retain the full launch command and resolved `run_config.json`, including cell overrides, image directory, evaluation split, nominal iteration limit, event times, primitive budget, quantization parameters, and save and test iterations. Pair these with the Git revision and dirty-tree state, relevant source or patch when dirty, Python and PyTorch versions, CUDA runtime and driver, rasterizer and other compiled extension revisions, and GPU model. The queue normally requires an A100; an `--allow_any_gpu` override must be recorded for its affected runs. The manifest fields establish what the software attempted to capture, while the completed per-run files determine what can actually be reported. [VERIFY RUN-LEVEL COVERAGE: device memory, driver, extension build, exact commands, and all software versions.] For a timing comparison, identify any hardware or software mismatch and give the held-out resolution and profiling settings specified in Section 3.7.3.

Input provenance requires the prepared image and COLMAP reconstruction versions, camera and held-out filename lists, and the sparse cloud used by configurations without M1. For M1, retain the dense-cloud PLY and sidecar with cloud hash, matcher weights and settings, generation seed, and training-view exclusion evidence. The same scene key alone does not demonstrate identical pixel and camera inputs across runs. A reproducible report should name the actual dataset snapshot or checksums when available and disclose an input whose byte identity cannot be reconstructed. Similarly, a run's Git commit followed by `-dirty` cannot reconstruct the uncommitted source without a saved diff or source archive.

Finally, retain the final attempt log, final checkpoint or serialized artifact, `eval_metrics.json`, diagnostic files where present, and the scripts and versioned settings used to aggregate Chapter IV tables. A stale queue entry is retried from the beginning because a legacy Gaussian checkpoint omits medium, quantizer, and schedule state; an earlier partial attempt is not a resumable continuation. The run inventory should mark any absent optional PLY or profiler output explicitly. These records support reanalysis of the 120 completed executions; their presence does not guarantee that a new execution on another machine will reproduce identical floating-point values.

### Editorial verification queue for Section 3.6 (outside thesis prose)

1. The final ledger contains all 120 expected cell-scene-repeat keys marked `done`; reconcile each with its physical run directory, `run_config.json`, and `eval_metrics.json`, particularly the four retried keys.
2. Enumerate every distinct run code hash and `-dirty` state, determine whether the changed tree can be reconstructed, and group comparisons by compatible lineage.
3. Check the actual command-line overrides, per-run hardware and software, scene split, M2/M3 event settings, and effective optimizer steps.
4. Inspect retries and archived attempts to prevent mixed diagnostic series or double counting.
5. Verify when baseline margins and analysis rules were recorded relative to the runs and outcome inspection; distinguish pre-run decisions from retrospective rules.
6. Populate the reproducibility record with actual per-run seed, GPU, software and extension versions, driver, launch command, data hashes, code revision or dirty diff, final checkpoint, and aggregation script. Mark fields not archived as unavailable rather than inferring them from the queue's defaults.

## 3.7 Measurements and diagnostic instruments

This section defines the measured quantities before Chapter IV interprets their values. The primary fidelity unit is a rendered held-out image paired with its reference image; the repeat unit remains one trained run. Efficiency and medium diagnostics are attached to the run or to recorded events within it. Table 3.12 lists the source file and the inferential limit for each class of measure. An absent field, failed profiling probe, or unrecorded diagnostic is missing evidence, not a zero value.

**Table 3.12. Measurement definitions and source records.**

| Measure | Unit and operational definition | Primary record | Interpretation limit |
|---|---|---|---|
| PSNR, pooled and per-channel | dB per full-frame held-out image; formulas below | Per-image entries in `eval_metrics.json` | Convention and image processing must match before external comparison |
| SSIM | Unitless per-image structural similarity; 11 × 11 Gaussian window, $\sigma=1.5$ in the recorded convention note | `eval_metrics.json` | Image similarity, not validated 3D geometry |
| LPIPS | Unitless per-image perceptual distance with VGG backbone in the inspected convention | `eval_metrics.json` | Backbone and image scaling affect cross-study comparison |
| Gaussian count | Number of live primitives at a recorded checkpoint or event | Final `cost` block and `diagnostics.csv` | Count alone does not equal bytes, latency, or geometric accuracy |
| Serialized model size | Bytes of all files in the named compressed artifact, including metadata and medium state | `model_size.json` | Distinguish measured bytes from analytical attribute bits and raw PLY size |
| Training duration and work | Seconds of recorded wall time; nominal iteration and effective optimizer-step count reported separately | `eval_metrics.json` cost block | Offline M1 preparation is outside training wall time |
| Rendering latency and throughput | ms/frame and frames/s for color-only rendering of held-out views | `eval_metrics.json` cost block | Excludes training depth and alpha probes; not end-to-end underwater composition latency |
| Rendering peak memory | MiB of peak CUDA allocated memory after profiler reset | `eval_metrics.json` cost block | A render-probe measurement, not training peak memory or total device occupancy |
| Medium and depth diagnostics | Per-channel coefficients, sampled-view depth range, and cross-view depth-range dispersion | `diagnostics.csv`; derived `medium_collapse.json` | Model states and associations, not direct physical ground truth |
| Spatial extent | Coordinate-space extent, box inflation, coarse occupancy, radius and opacity-filtered variants from saved Gaussian centers | `spatial_extent.csv`, derived from final `point_cloud.ply` | Available only where a PLY was saved; neither low occupancy nor a large box alone proves a floater or physical geometry error |

### 3.7.1 Held-out image fidelity

For one reconstructed image $R$ and reference image $I$, with channelwise mean squared error $m_c$, the code records two peak signal-to-noise ratio conventions for image values scaled to the nominal $[0,1]$ range:

$$
\operatorname{PSNR}_{\mathrm{pooled}}
=10\log_{10}\!\left(\frac{1}{\frac{1}{C}\sum_{c=1}^{C}m_c}\right),
\qquad
\operatorname{PSNR}_{\mathrm{channel}}
=\frac{1}{C}\sum_{c=1}^{C}10\log_{10}\!\left(\frac{1}{m_c}\right).
$$

The implementation floors the argument to each logarithm at $10^{-20}$, applying the floor to each channel error in the channelwise convention and to their mean in the pooled convention. The two values need not agree when the color channels have different errors. Every result table must name the convention it uses; a table headed only “PSNR” is ambiguous for this implementation. The evaluation function also calculates SSIM and LPIPS for each image pair without a region mask. The inspected metric note specifies VGG for LPIPS and describes evaluation on 8-bit images reread from a recorded disk container. The final run record must confirm the actual backbone, container, image range, and any color conversion. The metric values cannot establish medium-parameter correctness or geometric fidelity on their own.

The code averages valid per-image scores to produce each run's scene result. Within a cell and scene, three independent run results are summarized with their mean and dispersion where present. For a descriptive across-scene summary, the analysis can average four scene means equally or weight them by held-out image count (3, 4, 3, and 3). Both summaries have a different estimand and must carry explicit labels. Neither makes the 13 held-out images independent training repeats. Per-scene comparisons remain the primary presentation.

### 3.7.2 Representation, storage, and training resources

Final Gaussian count is read at the stated checkpoint and cross-checked against diagnostics and the saved artifact. M2's 200,000 figure is a configured target for its first event, not necessarily the final count: the importance filter can leave fewer eligible primitives, and subsequent optimization can change the population. For M1 cells the initial cloud count is an input property; the final count reflects later pruning. A count reduction is therefore reported together with fidelity and actual storage or rendering measurements, without equating one proxy to another.

`source/storage.py` writes a compressed artifact and counts the byte size of each file in its directory. The total includes unquantized attributes, packed indices and codebooks when M3 applies, metadata, and saved medium parameters. It also reports a theoretical 14-float-per-primitive baseline size and an analytical M3 bit estimate. The measured file total is the storage outcome; the analytical estimate is explanatory. A ratio should identify its denominator and whether numerator and denominator use actual saved artifacts or a calculated raw-float baseline. In particular, a ratio against a 59-float higher-order 3DGS representation is not the same comparison as a ratio against A0's 14-float representation.

The run cost record supplies training wall time and effective optimizer steps in addition to the nominal 30,000-iteration schedule. An M2 cell adds two intervals of 200 medium-only steps, and baseline optimization may also contain steps that do not increment the nominal counter. The repository manuscript reports 43,000 effective steps without M2 and 43,400 with M2; those values should be confirmed against run cost records before treating them as uniform across all runs. Even when step totals match, wall-time differences can reflect the work per step, GPU and software context, data access, or measurement variation. Compare wall time under matched hardware, evaluation schedule, and recorded step counts. M1 dense-cloud generation is an offline operation with its own elapsed time; report it separately or define an explicit allocation rule when claiming end-to-end cost. No monetary cost is estimated from these proxies without a documented rate and calculation.

### 3.7.3 Rendering time and memory

`utils/render_profile.py` profiles a trained model over its held-out cameras. It executes five unrecorded warm-up renders and then 20 timed passes over the same view set. CUDA synchronization occurs around timed passes. The total elapsed seconds are divided by the number of timed frames to obtain ms/frame; FPS is timed frames divided by total seconds. The script also records the standard deviation and coefficient of variation of pass-level mean frame time. The 20 passes characterize measurement variation over repeated rendering of the same few views; they are not 20 independent scenes or trained models.

The probe times the Gaussian color pass used to produce medium-free radiance. It excludes the separate depth and alpha passes used by the training objective, as well as any full downstream image-formation or application pipeline unless those are explicitly added to the benchmark. Peak CUDA allocated memory is reset after warm-up and read after timing. If profiling fails, the implementation records a reason and leaves the timing fields empty instead of invalidating the completed training run. A report should preserve that missingness and state the checkpoint, resolution, view set, device, and software version for every compared timing result.

### 3.7.4 Medium, depth, and failure diagnostics

`utils/diagnostics.py` writes run-specific rows with iteration and event labels, live Gaussian count, sampled-view pre-normalization depth minimum and maximum, and the scene's attenuation, backscatter, and far-field color parameters when available. It also provides fields for a sweep of depth ranges across training views: number of views, mean, standard deviation, coefficient of variation, and extrema. Sweeps are collected at selected boundaries and coarse intervals, so an empty sweep field means “not measured at this row.” A sampled view's $z_{\min}$ and $z_{\max}$ are not substitutes for cross-view dispersion.

Event labels distinguish before simplification, after simplification, and the end of medium-only continuation. The `medium_collapse.py` instrument identifies the first logged negative attenuation value by channel, checks whether subsequent logged values are frozen, and records the largest measured attenuation drop. Its backscatter-saturation flag uses a specified threshold of five for the minimum final channel coefficient. These are operational classifications of the learned model under this implementation. They do not prove a physical attenuation value or rule out unobserved behavior between logged rows. SS may have only a terminal medium state, so a missing SS trajectory is not evidence that no transition occurred.

The same instrument pairs pre-event and post-event cross-view depth-range coefficients of variation and reports their ratio when both values exist. Such a ratio can test whether a recorded event is associated with a change in dispersion; it cannot establish that dispersion caused a coefficient collapse without further controls. Likewise, a visually plausible restored image or self-consistency check cannot establish physical color accuracy without suitable reference information. Chapter IV will separate these model diagnostics from held-out-image fidelity and from causal interpretation.

### 3.7.5 Spatial-extent and population-geometry diagnostics

`tools/spatial_extent.py` reads positions, stored opacity logits, and stored log scales directly from each available final binary PLY. It analyzes the centers of the saved Gaussians in the scene's coordinate frame. For each axis, it calculates the full minimum-to-maximum extent and the extent between the first and ninety-ninth percentiles of center positions. The product of the three axis extents gives a box volume. The script reports full-to-percentile ratios for volume and diagonal length, plus each axis separately. A high ratio identifies an outlying tail relative to the central box, but the ratio is sensitive to a few points and the coordinate frame. It does not locate a floater in an image or establish that its depth is physically wrong.

The script also converts saved opacity logits with a sigmoid and calculates the fraction of primitives at or above its operational threshold $\alpha=0.05$. Its output calls this `frac_visible`, reflecting the intended opacity-based visibility proxy. It repeats full-box and occupancy calculations on that subset when at least ten primitives meet the threshold. This threshold selects primitives that may contribute appreciably in a render; it does not measure visibility over actual viewpoints, because a high-opacity primitive can remain occluded or outside the view. A large difference between the full and filtered boxes suggests that low-opacity primitives influence the spatial extent, but visual or view-conditioned evidence is needed to identify the rendered artifact. Gaussian log scales are exponentiated; an additional footprint extent expands each center by three times its largest recovered scale on each axis. That conservative axis-aligned approximation is separate from the center-only box and does not model the full rotated covariance.

For a second description of spatial concentration, the code partitions each cloud's own full box into a $64^3$ grid and reports the fraction of occupied voxels. It computes an analogous value for the opacity-filtered subset using that subset's own box. Since the grids are rescaled separately for each cloud, an occupancy difference describes relative distribution within each model's extent, not occupancy of identical physical voxels across configurations. The instrument additionally reports radial percentiles around the coordinatewise median center, the ratio of maximum to median radius, fractions within multiples of the median radius, and median and upper-percentile Gaussian scale. These quantities can help select cases for matched render and geometry inspection. None is an independent surface-reconstruction metric.

The script scans `runs/<cell>/<scene>/s<repeat>/point_cloud/iteration_*/point_cloud.ply` and uses the last path found for each run. The campaign storage policy describes saving PLYs for seed 0 only unless an override was enabled. Accordingly, `spatial_extent.csv` may provide one model per cell and scene, while fidelity and other outcomes have three repeats. The observed coverage, selected iteration, and file identity must be checked before reporting a spatial comparison or treating its apparent pattern as repeat-stable. The final analysis must not fill absent seeds with values inferred from the other two repeats or from compressed-model counts.

**Table 3.13. Diagnostic availability matrix [TO POPULATE].**

| Configuration group | Run-level fidelity | Population trajectory | Medium coefficient trajectory | Cross-view depth sweep | Serialized artifact | Render profile | Geometry/restoration checks |
|---|---|---|---|---|---|---|---|
| SS | [VERIFY] | [VERIFY] | Terminal state only [VERIFY] | [VERIFY] | [VERIFY] | [VERIFY] | [VERIFY] |
| A0, A1, A3, A5, A0D | [VERIFY] | [VERIFY] | [VERIFY] | [VERIFY] | [VERIFY] | [VERIFY] | Final PLY where saved, likely seed 0 only [VERIFY] |
| A2, A4, A6, A7 | [VERIFY] | [VERIFY] | [VERIFY] | Event sweeps [VERIFY] | [VERIFY] | [VERIFY] | Final PLY where saved, likely seed 0 only [VERIFY] |

### Editorial verification queue for Section 3.7 (outside thesis prose)

1. Check the exact disk reread, image scaling, SSIM implementation, LPIPS backbone, and final-checkpoint selection against each `eval_metrics.json` and the evaluation call site.
2. Reconcile model-size totals with the actual saved files, including whether any point-cloud and medium files sit outside the counted artifact directory.
3. Verify warm-up, timed pass count, CUDA synchronization, hardware, resolution, and profiler failure notes in run cost records.
4. Populate Table 3.13 by scene, configuration, checkpoint, and repeat rather than assuming group-wide coverage from the logger's code.
5. Treat absent depth sweeps and SS trajectories as missing measurements; do not turn operational collapse flags into physical-ground-truth labels.
6. Inspect every row of `spatial_extent.csv` against a final PLY and its iteration. Identify omitted cells and repeat IDs; distinguish center-only extent, the approximate footprint extent, and opacity-filtered statistics in Chapter IV.

## 3.8 Analysis procedure and validity boundaries

### 3.8.1 Analysis population and ordering

Analysis begins by matching the 120 runs across ten configurations, four scenes, and three repeat identifiers to the final execution ledger and run directories. A run enters a given metric comparison only if the needed final evaluation or diagnostic record exists and its code, data split, checkpoint, hardware, and measurement convention are sufficiently comparable with the other cells in that contrast. An absent cost metric can exclude a run from a timing comparison without discarding its valid fidelity record. Retries contribute only their final successful attempt.

The primary result layout is per scene and per configuration, with the three run values, mean, and sample standard deviation displayed or recoverable. The across-scene summary is secondary and labels either equal scene weighting or weighting by the number of held-out views. In the inspected `tools/analyse.py`, `per_cell` first averages repeats within each scene, then combines scene means and their standard errors into a cell estimate before calculating contrasts. Its generated JSON contrasts are therefore across-scene summaries, not per-scene effects. Chapter IV must calculate and present the corresponding scene-specific contrasts from `results_runs.csv` or `results_by_scene.csv` before interpreting an aggregate as consistent across scenes. The variance used by the aggregate tool propagates within-scene repeat standard errors and does not measure how effects vary across a broader population of underwater scenes.

### 3.8.2 Baseline and stand-alone comparisons

The SS versus A0 baseline check is evaluated separately in each scene on pooled PSNR, LPIPS, and Gaussian count. The configuration records candidate margins of $\pm1.0$ dB, $\pm0.02$, and $\pm30\%$, respectively. Before reporting a result as within a previously fixed margin, verify that each margin was recorded before the relevant outcomes were inspected and that the comparison used the declared scene-level repeat summaries. A difference within a margin describes the observed comparison under that margin; formal statistical equivalence requires an appropriate test and uncertainty criterion. Do not use “identical” or “exact reproduction” for two independently trained implementations.

For metric $Y$, the stand-alone effects in scene $s$ are $\Delta_{1,s}=\bar Y_{A1,s}-\bar Y_{A0,s}$, $\Delta_{2,s}=\bar Y_{A2,s}-\bar Y_{A0,s}$, and $\Delta_{3,s}=\bar Y_{A3,s}-\bar Y_{A0,s}$. The full matrix also supports the effect of each factor when the other two are enabled: $\bar Y_{A7,s}-\bar Y_{A6,s}$ for M1, $\bar Y_{A7,s}-\bar Y_{A5,s}$ for M2, and $\bar Y_{A7,s}-\bar Y_{A4,s}$ for M3. The from-below and from-above effects need not agree; a difference between them indicates dependence on the other active mechanisms under the tested conditions. The A0D versus A0 comparison is supplementary and is not used to construct any M1 to M3 interaction.

The subtraction above applies to fidelity metrics and other outcomes analyzed additively. For positive resource outcomes, the inspected analysis code uses the log of each cell mean and exponentiates the contrast so that a two-cell effect is a ratio. Its multiplicative set includes saved bytes, bytes per primitive, Gaussian count, training seconds, effective optimizer steps, and FPS. Peak rendering memory is analyzed additively because a hardware-dependent floor weakens a ratio interpretation. The metric, scale, reference, and preferred direction must be printed with each contrast. In particular, the mean of log run values is not generally equal to the log of their arithmetic mean; Chapter IV must use the same convention as the calculation it cites.

### 3.8.3 Factorial interaction contrasts

With the third factor disabled, the three two-factor interaction contrasts for each scene are

$$
\begin{aligned}
I_{12,s}&=\bar Y_{A4,s}-\bar Y_{A1,s}-\bar Y_{A2,s}+\bar Y_{A0,s},\\
I_{13,s}&=\bar Y_{A5,s}-\bar Y_{A1,s}-\bar Y_{A3,s}+\bar Y_{A0,s},\\
I_{23,s}&=\bar Y_{A6,s}-\bar Y_{A2,s}-\bar Y_{A3,s}+\bar Y_{A0,s}.
\end{aligned}
$$

The three-factor contrast is

$$
I_{123,s}=\bar Y_{A7,s}-\bar Y_{A4,s}-\bar Y_{A5,s}-\bar Y_{A6,s}
+\bar Y_{A1,s}+\bar Y_{A2,s}+\bar Y_{A3,s}-\bar Y_{A0,s}.
$$

For a multiplicative outcome, replace each cell mean $\bar Y$ in these signed sums with $\log\bar Y$ and report either the signed log contrast or its exponentiated ratio. The additive null is zero; the exponentiated multiplicative null is one. The formulas are contrasts at the one tested budget and schedule, not evidence of general synergy or a Pareto frontier. `tools/analyse.py` implements these terms on its across-scene cell estimates. Per-scene terms need a separate calculation with the same sign and scale conventions.

### 3.8.4 Dispersion and decision language

For a cell and scene with $n$ valid runs, the code uses the sample standard deviation across run values and $\mathrm{SE}=s/\sqrt n$ for the scene mean. It propagates the component standard errors in quadrature for a contrast, using a delta-method relative error for a positive log-scale quantity. If only one run contributes, its standard error is unknown rather than zero. The analysis plan uses a descriptive resolution rule of approximately two propagated standard errors for each contrast. The actual code flags interactions when the absolute additive effect, or absolute log ratio, is strictly greater than $2\mathrm{SE}$. Because the plan says “at least” while the code uses “greater than,” exact boundary cases require a stated convention. This rule is a study decision threshold, not by itself a formal multiple-comparison-adjusted significance test.

Report an effect with its estimated magnitude, direction, sample count, and uncertainty. If the estimated contrast is below the declared resolution threshold, call it unresolved at the available repeat count; do not call it zero or absent. If a participating cell is missing, the interaction is unidentifiable from the campaign. If two effect directions disagree beyond their propagated uncertainty, do not quote either as a universal mechanism effect. If preprocessing or code lineage differs materially, report the comparison as confounded even if the estimated difference is large. The analysis plan designates LPIPS and Gaussian count as its primary interaction outcomes and notes limited resolution for PSNR interactions. The date and provenance of that designation must be verified before calling it prospective.

### 3.8.5 Medium, geometry, and qualitative analyses

The medium analysis first reports observable trajectories and classifications: per-channel attenuation and backscatter parameters, first negative and frozen attenuation channels, model population at intervention events, and changes in cross-frame depth-range dispersion. Where a cell and scene contain both classified collapsed and intact runs, report their counts and conditional metric summaries. Avoid a single medium-parameter mean over that mixture as though it described one behavior. The inspected `analyse.py` warns about such mixtures but still computes aggregate cell estimates from all runs; Chapter IV must perform or display the stratified analysis separately. Moreover, its helper returns an empty collapse list when diagnostic data are absent, so an unmeasurable run must not be recoded as intact in an independent scientific summary.

Spatial-extent statistics are analyzed on the available final PLYs, likely a smaller subset than the three-repeat fidelity campaign. A large bounding box, low grid occupancy, or radial tail identifies a case for inspection, not a proven water-column floater. For qualitative comparisons, use the same scene, held-out viewpoint, crop, display transform, and color pipeline across configurations. Report examples that contradict the aggregate direction as well as those that illustrate it. Interpret a coefficient change or appearance difference as a possible mechanism only when the timing, diagnostic, and comparison controls support that account; an observed association is not a unique causal explanation.

### 3.8.6 Limits on inference and retrospective analysis

The experimental domain comprises four selected scenes, the recorded split, the implemented SeaSplat refactor, one principal M2 budget, one M3 codebook setting, and the available run repeats. The design can estimate differences among these configurations at those settings. It cannot establish generalization to other underwater datasets, physically correct medium parameters, a stable rate-distortion frontier across untested budgets, or the effect of a source method component deliberately omitted from M1, M2, or M3. Different code trees, dirty-state changes that cannot be recovered, missing diagnostic coverage, and unbalanced retries further restrict a particular contrast as indicated by the manifest audit.

The campaign plan separates predictions documented before their corresponding execution stages from analyses written after some campaign information was already available. Its opening explicitly says the baseline-margin verdict and diagnostic-file completeness were known when the plan was written. Some entries point to earlier dated documents as evidence of prior prediction. Accordingly, the final thesis should use an item-level chronology: call a prediction prospective only when a dated source precedes the relevant run and outcome access; label the known baseline verdict as an already observed check; and label analyses formulated after inspecting their data as exploratory. Do not describe the entire plan as preregistered. Chapter IV should report negative and unresolved outcomes under the same rules as favorable ones and identify analyses developed after seeing the results.

**Table 3.14. Analysis eligibility and inferential status [TO POPULATE].**

| Contrast or diagnostic | Required cells and artifacts | Matching conditions | Repeat coverage | Rule or status chronology | Eligible scenes | Principal limit |
|---|---|---|---|---|---|---|
| SS versus A0 | [VERIFY] | [VERIFY] | [VERIFY] | [VERIFY MARGIN DATE] | [VERIFY] | [VERIFY] |
| Individual M1, M2, M3 | [VERIFY] | [VERIFY] | [VERIFY] | [VERIFY] | [VERIFY] | [VERIFY] |
| Two- and three-factor interactions | [VERIFY] | [VERIFY] | [VERIFY] | [VERIFY] | [VERIFY] | [VERIFY] |
| A0D versus A0 | [VERIFY] | [VERIFY] | [VERIFY] | [VERIFY] | [VERIFY] | [VERIFY] |
| Medium and spatial diagnostics | [VERIFY] | [VERIFY] | [VERIFY] | [VERIFY] | [VERIFY] | [VERIFY] |

### Editorial verification queue for Section 3.8 (outside thesis prose)

1. Compute the per-scene contrasts from raw run records and compare them with any across-scene output; do not present `analyse.py` aggregates as per-scene estimates.
2. Resolve the analysis plan's inclusive two-SE wording against the code's strict inequality and record the applied rule.
3. Verify the timeline of each proposed hypothesis, margin, and diagnostic against dated commits and outcome access; reserve “preregistered” for items with sufficient evidence.
4. Stratify mixed collapsed/intact groups and distinguish missing medium diagnostics from documented intact models.
5. Complete Table 3.14 after reconciling all run manifests, retries, artifacts, and software revisions; withhold causal or equivalence language where comparability fails.
