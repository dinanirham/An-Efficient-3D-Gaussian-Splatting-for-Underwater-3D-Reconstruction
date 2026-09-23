# Evidence-Grounded Thesis Repositioning and Surgical Revision After the Completed 120-Run Campaign

## 1. Research Context

I am revisiting my master’s thesis:

**An Efficient 3D Gaussian Splatting for Underwater 3D Reconstruction**

The study is based on a refactored SeaSplat implementation and investigates three efficiency mechanisms adapted to underwater 3D Gaussian Splatting:

* M1: Dense correspondence-based initialization.
* M2: Importance-weighted budgeted spatial simplification.
* M3: In-training vector quantization of Gaussian attributes.

The implementation evaluates these mechanisms individually, pairwise, and jointly using a \(2^3\) factorial design. An additional non-factorial configuration, A0D, evaluates continuous primitive reduction through modified densification-gradient routing.

The experimental campaign is now complete. The repository, implementation design, analysis scripts, analysis draft, Google Drive artifacts, latest thesis manuscript, source papers, thesis guideline, and SIGGRAPH Asia 2026 reviewer feedback must now be reconciled into one scientifically defensible thesis architecture.

This task is not a general proofreading exercise. It is a complete methodological and evidential realignment of the thesis.

---

# 2. Primary Objective

Conduct an evidence-grounded audit and produce a surgical revision plan for Chapters 2, 1, and 3 of the thesis so that:

1. The theoretical foundation accurately represents the cited literature.
2. The research gap follows from the literature rather than from unsupported novelty claims.
3. The research questions match what the completed experiment can actually answer.
4. The methodology describes the implementation and experiment that produced the final evidence.
5. Every claim is bounded by the experimental design, uncertainty, provenance, and available ground truth.
6. The revised positioning responds directly to the SIGGRAPH Asia reviewer feedback.
7. Failed hypotheses and unsuccessful methodological explanations are reported transparently.
8. The thesis distinguishes scientific findings, engineering contributions, implementation corrections, exploratory observations, and unresolved mechanisms.

Do not begin full thesis rewriting during this task. First produce the complete diagnostic package, revised positioning, and section-level surgical plan.

---

# 3. Required Academic Standard

Perform the audit at the standard expected of a research-track computer science thesis in:

* 3D Gaussian Splatting.
* Neural rendering and novel-view synthesis.
* Structure from Motion and multi-view geometry.
* Underwater image formation.
* Light attenuation, scattering, and backscatter.
* Physics-aware underwater reconstruction.
* Gaussian initialization and densification.
* Gaussian pruning, simplification, and spatial reorganization.
* Attribute quantization and representation compression.
* Factorial experimental design.
* Repeated-run uncertainty analysis.
* Rate-distortion and Pareto analysis.
* Reproducible computer-vision experimentation.

Use precise and restrained academic language.

Do not use promotional language, vague novelty claims, or causal explanations unsupported by the design.

Use APA 7th edition citations. Mark unsupported statements as:

* `[NEEDS CITATION]`
* `[NOT SUPPORTED BY THE CURRENT DESIGN]`
* `[NOT YET VERIFIED AGAINST SOURCE]`
* `[EXPLORATORY FINDING]`
* `[POST-HOC INTERPRETATION]`

Do not use em dashes.

---

# 4. Authoritative Evidence Snapshot

Begin by verifying the following snapshot rather than assuming that it is correct.

## 4.1 GitHub repository

Repository:

`dinanirham/An-Efficient-3D-Gaussian-Splatting-for-Underwater-3D-Reconstruction`

Current observed default branch:

`main`

Current observed repository HEAD at the time this prompt was prepared:

`29748992da8c3d7bb2d4d1916fc1afbcc5c9c453`

Relevant repository areas include:

### Source-method analyses

* `seasplat/research-methodology-output/`
* `seathru_NeRF/research-methodology-output/`
* `EDGS/research-methodology-output/`
* `mini-splatting/research-methodology-output/`
* `CompGS/research-methodology-output/`
* `OMG/research-methodology-output/`
* `compact3d/research-methodology-output/`
* `RoMa/research-methodology-output/`
* `RoMaV2/research-methodology-output/`

Each directory contains a structured methodology analysis from `00-index.md` through `11-paper-vs-repo-disagreements.md`.

### Combined intended methodology

* `combined-method-methodology/00-index.md`
* `combined-method-methodology/01-taxonomy.md`
* `combined-method-methodology/02-pipeline.md`
* `combined-method-methodology/03-variables.md`
* `combined-method-methodology/04-loss.md`
* `combined-method-methodology/05-constraints.md`
* `combined-method-methodology/06-implementation-deltas.md`
* `combined-method-methodology/07-pseudocode.md`
* `combined-method-methodology/08-computational-profile.md`
* `combined-method-methodology/09-glossary.md`
* `combined-method-methodology/10-reproducibility.md`
* `combined-method-methodology/11-paper-vs-repo-disagreements.md`
* `combined-method-methodology/12-novelty-defensibility.md`
* `combined-method-methodology/13-campaign-addendum.md`
* `combined-method-methodology/open-questions.md`
* `combined-method-methodology/chapter/`

### Executed implementation

* `implementation/configs/cells.json`
* `implementation/train.py`
* `implementation/source/roma_init.py`
* `implementation/source/simplify.py`
* `implementation/source/quantize.py`
* `implementation/source/storage.py`
* `implementation/source/undistort.py`
* `implementation/utils/diagnostics.py`
* `implementation/utils/metrics_conventions.py`
* `implementation/utils/render_profile.py`
* `implementation/tools/`
* `implementation/docs/ablation_design.md`
* `implementation/docs/experiment_plan.md`
* `implementation/docs/reproducibility_notes.md`
* `implementation/tools/CAMPAIGN.md`
* `implementation/RUNBOOK.md`
* `implementation/notebooks/`

### Previous thesis-realignment materials

* `new-revisited-writing/00-phase0-manifest.md`
* `new-revisited-writing/01-discrepancy-ledger.md`
* `new-revisited-writing/02-reviewer-traceability.md`
* `new-revisited-writing/03-claim-validity-ledger.md`
* `new-revisited-writing/04-repositioning.md`
* `new-revisited-writing/05-surgical-plan.md`
* `new-revisited-writing/06-experiment-and-literature-plan.md`
* `new-revisited-writing/08-supervisory-review.md`
* `new-revisited-writing/09-supervisory-review-ii.md`
* `new-revisited-writing/chapter-3-methodology.md`
* `new-revisited-writing/results-*.md`

These are prior audit and drafting artifacts. Do not treat them as authoritative without revalidation against the completed campaign.

### Final campaign analysis

* `analysis/campaign-2026-09/PLAN.md`
* `analysis/campaign-2026-09/FINDINGS.md`
* `analysis/campaign-2026-09/README.md`
* `analysis/campaign-2026-09/FINDINGS.html`

Treat `PLAN.md` as the record of pre-analysis commitments and `FINDINGS.md` as an interpretive draft. Do not treat `FINDINGS.md` as raw evidence.

## 4.2 Google Drive experiment workspace

Drive folder:

`https://drive.google.com/drive/folders/1fN8669gX8xxzNn-aWDdhQyYlOTON3nhw`

The observed workspace contains:

### Execution notebooks

* `00_setup.ipynb`
* `01_worker.ipynb`
* `02_analysis.ipynb`
* `04_densify_diagnostic.ipynb`

### Campaign control

* `run_ledger.json`
* `run_ledger.json.bak`

### Run directories

* `runs/SS/`
* `runs/A0/`
* `runs/A1/`
* `runs/A2/`
* `runs/A3/`
* `runs/A4/`
* `runs/A5/`
* `runs/A6/`
* `runs/A7/`
* `runs/A0D/`
* `runs/_archive/`

Each principal cell contains four scenes and three repeat runs per scene.

### Dense initialization artifacts

* `dense/Curasao.ply` and metadata.
* `dense/IUI3-RedSea.ply` and metadata.
* `dense/JapaneseGradens-RedSea.ply` and metadata.
* `dense/Panama.ply` and metadata.

### Generated analysis artifacts

* `analysis/results_runs.csv`
* `analysis/results_by_scene.csv`
* `analysis/results_by_cell.csv`
* `analysis/results_summary.md`
* `analysis/analysis_unweighted.json`
* `analysis/analysis_image_weighted.json`
* `analysis/medium_collapse.json`
* `analysis/spatial_extent.csv`
* `analysis/j_consistency.json`
* `analysis/baseline_replication/`
* `analysis/densify_diagnostic/`
* associated diagnostic figures.

The current ledger reports:

* 120 total runs.
* 120 completed runs.
* 10 configurations.
* 4 scenes.
* 3 repeats per cell and scene.
* A100-SXM4-40GB for the recorded trained configurations.
* Four runs requiring more than one attempt.
* No recorded run errors after completion.
* No populated commit field in the ledger.

A sampled final run manifest from `A7/Curasao/s0` records:

`git_sha = ef472509dab2f13bea956ef41aeba937794e7bb-dirty`

Therefore, do not accept a one-clean-version claim without enumerating the `git_sha` value from every available `run_config.json`.

## 4.3 Thesis and supporting documents

Use the supplied files:

* `General Overview of Thesis Proposal Contents.docx`
* `Thesis - An Efficient 3D Gaussian Splatting for Underwater 3D Reconstruction.docx`
* SIGGRAPH Asia 2026 reviewer-feedback document.
* Supplied source papers.

The current thesis manuscript contains Chapters 1, 2, and 3. It does not yet contain completed Chapters 4 and 5.

The current chapter structure includes:

### Chapter 1

* Background.
* Problem Statement.
* Research Objective.
* Research Benefits.
* Scope and Limitations.

### Chapter 2

* 2.1 Fundamentals of 3D Reconstruction and Scene Representation.
* 2.2 Neural Radiance Fields and Differentiable Rendering.
* 2.3 Explicit Radiance-Field Representations and 3D Gaussian Splatting.
* 2.4 Physical Image Formation in Underwater Environments.
* 2.5 Efficiency Considerations in Radiance-Field Modelling.
* 2.6 Literature Review.

### Chapter 3

* 3.1 Conceptual Framework.
* 3.2 Research Stages.
* 3.3 SeaThru-NeRF Dataset.
* 3.4 Data Preprocessing.
* 3.5 Proposed 3D Gaussian Splatting Method.
* 3.6 Experimental Design.
* 3.7 Evaluation Metrics.

Audit numbering defects, missing subsections, inconsistent heading levels, and structural gaps as part of the surgical plan.

---

# 5. Question-Specific Source-of-Truth Rules

Do not use a single universal source hierarchy. Use the hierarchy appropriate to the question being answered.

## 5.1 What was actually executed

1. Per-run `run_config.json`.
2. Training logs and diagnostics.
3. Saved model and evaluation artifacts.
4. Code at the recorded run commit, if recoverable.
5. Current implementation.
6. Methodology documentation.
7. Thesis description.

## 5.2 What numerical result was obtained

1. Per-run `eval_metrics.json` and raw diagnostics.
2. `results_runs.csv`.
3. `results_by_scene.csv`.
4. `results_by_cell.csv`.
5. `analysis_unweighted.json` and `analysis_image_weighted.json`.
6. `results_summary.md`.
7. `FINDINGS.md`.
8. Thesis prose.

## 5.3 What was planned before analysis

1. Timestamped or committed `PLAN.md`.
2. Configuration files fixed before execution.
3. Earlier hypothesis and experimental-design documentation.
4. Later interpretive writing.

Do not relabel a post-hoc analysis as pre-registered.

## 5.4 What an external method originally proposed

1. Peer-reviewed paper.
2. Official supplementary material.
3. Official implementation at the relevant release or commit.
4. Repository `research-methodology-output`.
5. Combined-method documentation.
6. Thesis interpretation.

## 5.5 What the thesis currently claims

1. Latest thesis manuscript.
2. Existing tables, figures, captions, and bibliography.
3. Previous revision plans only as historical context.

## 5.6 What reviewers requested

1. Exact SIGGRAPH Asia review text.
2. Reviewer-response interpretation.
3. Revision-plan summaries.

Never replace a reviewer’s empirical request with a prose-only correction.

---

# 6. Mandatory Logical Order

All reasoning, validation, restructuring, and future rewriting must follow this order:

1. Chapter 2: Theoretical Foundations and Literature Review.
2. Chapter 1: Introduction and Problem Context.
3. Chapter 3: Research Methodology.
4. Chapter 4: Results and Analysis.
5. Chapter 5: Conclusions.

Chapter 1 may not introduce a gap not derived in Chapter 2.

Chapter 3 may not introduce a design choice not justified by Chapters 1 and 2.

Chapter 4 may not report a result the executed design cannot support, and may not introduce a metric, cell, or convention Chapter 3 does not define.

Chapter 5 may not introduce evidence. Every claim in it resolves to a Chapter 4 section.

Results may be used to test whether the intended positioning remains defensible, but they must not be used to retroactively invent the original research gap.

---

# 7. Phase 0: Evidence Freeze and Artifact Reconciliation

Before interpreting results:

1. Record the current repository HEAD, timestamp, branches, and tags.
2. Determine which commit or dirty state produced each of the 120 runs.
3. Enumerate `git_sha` from every accessible `run_config.json`.
4. Identify all distinct SHAs and all `-dirty` manifests.
5. Compare the run SHAs with current `main`.
6. Determine whether the exact dirty working-tree changes are recoverable.
7. Verify that the 120-run ledger matches the physical run directories.
8. Confirm the presence and completeness of:

   * 120 `run_config.json` files.
   * 120 final evaluation records.
   * all expected diagnostics.
   * all required compressed artifacts.
   * all required dense-cloud metadata.
9. Identify retries, replaced attempts, archived outputs, and stale artifacts.
10. Establish whether `02_analysis.ipynb` was rerun after the commit-collection bug was fixed.
11. Verify whether the repository’s `analysis/campaign-2026-09/` materials correspond exactly to the current Drive outputs.

### Phase 0 deliverables

* Version and artifact manifest.
* Run-directory versus ledger reconciliation.
* Commit and dirty-state matrix.
* Missing-artifact report.
* Stale-artifact report.
* Exact reproducibility limitations.

Do not claim exact reproducibility if the training tree was dirty and the diff cannot be recovered.

---

# 8. Phase 1: Material-to-Research-Question Mapping

Map every material to its scientific role.

Use a table with the following structure:

| Material | Location | Evidence type | Research question supported | Thesis chapter | Authority level | Known limitation |
| -------- | -------- | ------------- | --------------------------- | -------------- | --------------- | ---------------- |

At minimum, map:

* Original papers.
* Official source repositories where available.
* Every `research-methodology-output` corpus.
* `combined-method-methodology/`.
* Current implementation code.
* Verification scripts.
* Drive notebooks.
* Dense clouds and metadata.
* Raw run outputs.
* Aggregated CSV and JSON files.
* `PLAN.md`.
* `FINDINGS.md`.
* Previous thesis-audit documents.
* Current thesis sections.
* Reviewer comments.

Explicitly distinguish:

* Source-method theory.
* Intended thesis design.
* Executed implementation.
* Execution evidence.
* Generated analysis.
* Interpretation.
* Thesis prose.
* Reviewer criticism.

---

# 9. Phase 2: Methodological Lineage Audit

For each source method, determine:

* Original problem.
* Original contribution.
* Pipeline stage affected.
* Mathematical formulation.
* Optimization schedule.
* Dataset.
* Evaluation protocol.
* Reported results.
* Computational assumptions.
* Known limitations.
* Official code behavior.
* Paper-code discrepancies.
* Thesis-adopted elements.
* Thesis-omitted elements.
* Thesis-modified elements.
* Whether the thesis adaptation remains equivalent, partial, or merely inspired by the method.

At minimum, audit:

* SeaThru-NeRF.
* SeaSplat.
* Standard 3D Gaussian Splatting.
* EDGS.
* RoMa and RoMaV2.
* Mini-Splatting.
* CompGS.
* OMG.
* Compact3D.
* EAGLES.
* LightGaussian.
* ReSplat.
* WaterSplatting.
* Aquatic-GS.
* Gaussian Splashing.
* Relevant underwater-pruning and underwater-compression methods.

Use the repository methodology analyses as structured notes, not as substitutes for the original papers.

### Required lineage matrix

| Source method | Original mechanism | Thesis adaptation | Deliberate departure | Code evidence | Experimental cell | Fidelity to source | Risk |
| ------------- | ------------------ | ----------------- | -------------------- | ------------- | ----------------- | ------------------ | ---- |

Do not call M1 “EDGS,” M2 “Mini-Splatting,” or M3 “CompGS” unless the implementation satisfies the defining properties of those methods. Otherwise use language such as “derived from,” “adapted from,” or “inspired by.”

---

# 10. Phase 3: Intended Framework Versus Executed Implementation

Audit the combined methodology against the implementation.

## 10.1 Experimental factors

Verify the executed definitions of:

| Cell | M1 | M2 | M3 | Role                    |
| ---- | -: | -: | -: | ----------------------- |
| A0   |  0 |  0 |  0 | Refactored baseline     |
| A1   |  1 |  0 |  0 | Dense initialization    |
| A2   |  0 |  1 |  0 | Budgeted simplification |
| A3   |  0 |  0 |  1 | Attribute quantization  |
| A4   |  1 |  1 |  0 | M1 and M2               |
| A5   |  1 |  0 |  1 | M1 and M3               |
| A6   |  0 |  1 |  1 | M2 and M3               |
| A7   |  1 |  1 |  1 | Fully combined system   |

Treat the following separately:

* SS: unmodified SeaSplat reference.
* A0D: non-factorial supplementary mechanism.

A0D must not be included in factorial contrasts.

## 10.2 Configuration values to verify

Do not rely only on documentation. Trace each value into code and run manifests:

* 30,000 nominal training iterations.
* 43,000 effective optimizer steps for non-M2 cells.
* 43,400 effective optimizer steps for M2 cells.
* M2 interventions at iterations 15,000 and 20,000.
* 200 medium-only steps after each M2 intervention.
* Primitive budget of 200,000.
* M3 activation at iteration 22,000.
* Codebook size \(K = 4096\).
* Assignment refresh frequency of 100.
* One k-means update iteration.
* `sh_degree = 0`.
* Final model save behavior.
* Evaluation iterations.
* Dense-cloud preprocessing configuration.
* Seed handling.
* Train-test partitioning.
* Undistortion requirements.
* Rendering benchmark protocol.
* Model-size container and accounting convention.

## 10.3 Conformity classifications

Classify every discrepancy as:

* Conformant.
* Documentation drift.
* Material methodological deviation.
* Analysis-affecting inconsistency.
* Experiment-invalidating inconsistency.
* Unable to verify.

### Required conformity table

| Claim or design choice | Intended documentation | Current code | Run-manifest evidence | Result artifact | Classification | Required correction |
| ---------------------- | ---------------------- | ------------ | --------------------- | --------------- | -------------- | ------------------- |

---

# 11. Phase 4: Completed Experiment and Analysis Validation

Independently reproduce or verify the analysis from the rawest available data.

Do not merely summarize `FINDINGS.md`.

## 11.1 Completion and integrity

Verify:

* 120 of 120 runs complete.
* 12 runs per configuration.
* 3 repeats per scene.
* Consistent scene naming, including the `JapaneseGradens-RedSea` spelling.
* No duplicated or omitted cell-scene-seed combinations.
* Retry handling.
* Absence of mixed-attempt diagnostics.
* Hardware consistency.
* Metric availability.
* Correct model-size accounting.
* Correct treatment of SS records.

## 11.2 Baseline validation

Assess SS versus A0 using the pre-specified margins.

Use wording such as:

* “within the pre-specified margin,” if supported.
* Not “identical.”
* Not “exact reproduction.”
* Not “statistically equivalent,” unless a valid equivalence test was specified and performed.

## 11.3 Main effects

Evaluate M1, M2, and M3:

* From below:

  * A1 minus A0.
  * A2 minus A0.
  * A3 minus A0.
* From above:

  * A7 minus A6.
  * A7 minus A5.
  * A7 minus A4.

Report effects per scene.

Use:

* Additive effects for PSNR, SSIM, and LPIPS.
* Log-scale or ratio effects for positive multiplicative efficiency quantities.
* Mean, standard deviation, and uncertainty across repeats.
* Resolution relative to the predeclared noise floor.
* “Unresolved” rather than “no effect” when the design cannot separate the effect from repeat dispersion.

## 11.4 Interactions

Evaluate:

$$
I_{12}=\frac{1}{2}\sum_{c=0}^{1}
\left(Y_{11c}-Y_{10c}-Y_{01c}+Y_{00c}\right)
$$

and equivalent two-way contrasts for M1-M3 and M2-M3.

Evaluate:

$$
I_{123}=Y_{111}-Y_{110}-Y_{101}-Y_{011}
+Y_{100}+Y_{010}+Y_{001}-Y_{000}
$$

Respect the pre-analysis decision that:

* LPIPS and primitive count are the primary interaction outcomes.
* PSNR interactions may be unresolved by construction at three repeats.
* An unresolved interaction is not evidence of additivity.

## 11.5 Medium-model collapse

Validate the reported collapse classification and timing.

Specifically verify:

* A0 and SS collapse rates.
* A2 and A6 collapse rates.
* A4 and A7 collapse rates.
* Lost channels.
* Iterations at which coefficients cross zero.
* Whether the crossing occurs during simplification or during the medium-only re-identification interval.
* Whether collapsed and intact repeats are improperly pooled.
* Whether fidelity metrics distinguish collapse.

Treat medium collapse as a model-state pathology, not automatically as proof of inaccurate physical reconstruction.

## 11.6 Failed registered explanation

Independently test the registered depth-range-dispersion explanation.

If the reported failure is reproduced:

* Withdraw the explanation.
* Do not weaken it into an unfalsifiable statement.
* Separate the observed association with large population cuts from causal explanation.
* State that the design does not isolate removal fraction, entering primitive count, entering attenuation coefficients, and M1 initialization.
* State that the reason for the medium failure remains unresolved.

## 11.7 A0D

Evaluate A0D only as a supplementary controlled contrast against A0.

Report:

* Primitive-count effect.
* Training-time effect.
* Rendering effect.
* PSNR resolution.
* LPIPS effect.
* Medium-collapse rate.
* Why it is outside the factorial design.

Do not describe A0D as a fourth factorial factor.

## 11.8 Secondary diagnostics

Audit:

* Spatial extent and visibility.
* Detached outliers.
* Opacity-gated visibility.
* Restored-image self-consistency.
* Continuous versus codebook state.
* Cross-campaign replication.
* Scene-specific anomalies.

Maintain the correct evidential status:

* Geometry and restored-image analyses based on one repeat per scene remain exploratory.
* Restored-image self-consistency is not restoration accuracy.
* A geometric detector is not a validated proxy for medium health.
* The earlier campaign may be used only for explicitly justified replication comparisons.

---

# 12. Phase 5: Interpretation Audit of FINDINGS.md

For every major conclusion in `FINDINGS.md`, classify it as:

* Directly reproduced from raw evidence.
* Reproduced with corrected wording.
* Numerically correct but overinterpreted.
* Exploratory only.
* Contradicted.
* Not reproducible from available artifacts.
* Dependent on unresolved provenance.

Audit at minimum:

1. Baseline-within-margin conclusion.
2. Main effects of M1, M2, and M3.
3. Two-way interactions.
4. Three-way interaction.
5. Collapse rates.
6. Failure of the dispersion hypothesis.
7. Post-hoc relationship with removal fraction.
8. A0D findings.
9. Pareto-front descriptions.
10. Fidelity metrics’ inability to detect medium collapse.
11. Geometric-pathology findings.
12. Restored-image self-consistency.
13. Cross-campaign replication.
14. Computational-cost claims.
15. Claims that the campaign established something “for the first time.”

Produce a corrected findings ledger before using the analysis draft to reposition the thesis.

---

# 13. Phase 6: Reviewer-Feedback Reconciliation

Analyze every SIGGRAPH Asia review separately.

For each reviewer comment:

1. Quote or precisely paraphrase the concern.
2. Classify it as:

   * Novelty.
   * Framing.
   * Related work.
   * Source-method fidelity.
   * Methodological justification.
   * Experimental control.
   * Statistical support.
   * Reproducibility.
   * Rate-distortion evaluation.
   * Mechanistic explanation.
   * Underwater-specific evaluation.
   * Figures or presentation.
   * Limitations.
3. Identify the affected thesis section.
4. Determine whether the completed campaign:

   * Fully resolves it.
   * Partially resolves it.
   * Does not resolve it.
   * Contradicts the previous response.
   * Introduces a new concern.
5. Identify the required evidence.
6. Identify the exact revision action.

### Required matrix

| Reviewer concern | Underlying issue | Final campaign response | Evidence available | Evidence missing | Thesis section | Resolution status |
| ---------------- | ---------------- | ----------------------- | ------------------ | ---------------- | -------------- | ----------------- |

A new explanation does not resolve a request for empirical evidence.

---

# 14. Phase 7: Thesis Repositioning

Develop at least two candidate framings.

## 14.1 Conservative framing

The default candidate should treat the thesis as:

> A controlled factorial investigation of how three efficiency mechanisms affect reconstruction fidelity, representation cost, rendering performance, optimization behavior, and learned underwater-medium stability in a SeaSplat-based estimator.

This framing does not require the thesis to claim a new general-purpose compression algorithm.

## 14.2 Stronger framing

A stronger candidate may emphasize:

* A reproducible coupling between large, abrupt primitive simplification and medium-model collapse.
* The inability of conventional view-synthesis metrics to detect invalid medium decompositions.
* A positive engineering result from dense initialization or A0D.
* A methodology for diagnosing efficiency interventions in physics-aware 3DGS.

Use this framing only to the extent supported by the design.

Do not claim that the campaign explains why the medium collapses if the registered explanation failed and no controlled replacement mechanism was tested.

## 14.3 Required positioning outputs

For each candidate, provide:

* Research problem.
* Research gap.
* Central thesis statement.
* Research questions.
* Objectives.
* Hypotheses.
* Independent variables.
* Dependent variables.
* Experimental blocks.
* Repeat structure.
* Control variables.
* Contributions.
* Scope.
* Limitations.
* Validity boundaries.
* Claims that must be removed.
* Additional evidence required.

Recommend one framing and justify it.

---

# 15. Phase 8: Chapter-by-Chapter Surgical Plan

Follow this mandatory order:

1. Chapter 2.
2. Chapter 1.
3. Chapter 3.

For every existing section and proposed subsection, assign one action:

* Retain.
* Retain with citation correction.
* Refine.
* Expand.
* Reorganize.
* Merge.
* Move.
* Replace.
* Remove.
* Add.
* Defer.

Use this table:

| Chapter and section | Current role | Diagnosis | Surgical action | Revised role | Evidence required | Citation requirement | Reviewer concern | Priority | Completion criterion |
| ------------------- | ------------ | --------- | --------------- | ------------ | ----------------- | -------------------- | ---------------- | -------- | -------------------- |

## 15.1 Chapter 2

Audit and redesign:

* 2.1 Fundamentals of 3D Reconstruction and Scene Representation.
* 2.2 Neural Radiance Fields and Differentiable Rendering.
* 2.3 Explicit Radiance-Field Representations and 3D Gaussian Splatting.
* 2.4 Physical Image Formation in Underwater Environments.
* 2.5 Efficiency Considerations in Radiance-Field Modelling.
* 2.6 Literature Review.

Determine whether Chapter 2 needs explicit subsections for:

* SeaThru-NeRF.
* SeaSplat.
* Underwater 3DGS.
* Initialization and densification.
* Spatial simplification and pruning.
* Attribute quantization and storage compression.
* Geometry-medium optimization coupling.
* Repeated-run uncertainty.
* Factorial effects and interactions.
* Rate-distortion and Pareto evaluation.
* Literature synthesis and research-gap derivation.

The literature-review section must discuss each central paper in paragraph form and identify:

* Authors.
* Research problem.
* Proposed method.
* Evaluation design.
* Datasets.
* Metrics.
* Main results.
* Limitations.
* Relevance to this thesis.

Include a literature-synthesis table followed by prose analysis of:

* Research trends.
* Current strongest approaches.
* Unresolved limitations.
* Domain-transfer risks.
* Gap addressed by this thesis.

## 15.2 Chapter 1

Audit and revise:

* Background.
* Problem Statement.
* Research Objective.
* Research Benefits.
* Scope and Limitations.

Determine whether explicit subsections for research questions and contributions should be added.

The revised Chapter 1 must:

* Derive its gap from Chapter 2.
* Avoid claiming that no underwater pruning method exists.
* Avoid claiming physical accuracy without physical ground truth.
* Avoid AUV deployment claims without device evaluation.
* Define efficiency outcomes separately.
* State the four-scene and A100-based scope.
* Present repeated-run and generalization limitations.
* Distinguish medium stability from medium accuracy.

## 15.3 Chapter 3

Audit and revise:

* 3.1 Conceptual Framework.
* 3.2 Research Stages.
* 3.3 SeaThru-NeRF Dataset.
* 3.4 Data Preprocessing.
* 3.5 Proposed 3D Gaussian Splatting Method.
* 3.6 Experimental Design.
* 3.7 Evaluation Metrics.

Add or reorganize content as required for:

* Source-method adaptation.
* Implementation-delta register.
* SS reference.
* A0 baseline.
* M1.
* M2.
* M3.
* A0D.
* \(2^3\) factorial design.
* Scene blocking.
* Three-repeat design.
* Intervention schedules.
* Effective optimizer steps.
* Checkpoint and run lineage.
* Dense-cloud generation.
* Reproducibility.
* Model-size accounting.
* Rendering benchmark protocol.
* Medium-collapse definition.
* Underwater-conditioned diagnostics.
* Factorial contrast equations.
* Resolution and uncertainty rules.
* Threats to validity.

Correct numbering problems such as the current unnumbered scene subsection and the apparent `3.2.3` subsection under Section 3.3.

The methodology chapter must describe what produced the final campaign, not the earlier intended implementation.

---

# 16. Phase 9: Chapter 4 Construction — Results and Analysis

Chapter 4 is a surgical revision of an existing chapter, not a new one. The
AoL Research Writing I submission carries an approved Chapter IV at pages
70-132, with seven sections and thirteen tables, and a matching Chapter V. Its
component-wise organisation is preserved; its content is rebuilt, because the
campaign it reports is not the campaign that has now been run. Three of its
properties are prohibited going forward: fidelity metrics aggregated across
scenes, conclusions drawn without a reference control or interaction evidence,
and a ranking of mechanisms taken from one operating point.

## 16.1 Preconditions

Do not begin until all of the following hold:

* Phase 4 completion and integrity checks pass.
* The Phase 5 corrected findings ledger exists.
* The Phase 7 framing is approved.
* Chapters 2, 1, and 3 are stable, so that every term Chapter 4 uses is
  already defined.

If a precondition fails, report the blocker rather than drafting around it.

## 16.2 Source of truth

`analysis/campaign-2026-09/FINDINGS.md` is the sole source of results prose,
and `PLAN.md` beside it is the sole source of what was registered in advance.

* Do not recompute a number for the chapter. If a needed quantity is absent
  from the analysis, add it to the analysis first, then cite it.
* Do not soften, round, or re-average a reported figure to make a sentence
  read better.
* Where the chapter and the analysis disagree, the analysis is correct and the
  chapter is wrong.
* Cite the section of `FINDINGS.md` behind every table.

## 16.3 Mandatory reporting conventions

These are properties of the design, not stylistic preferences. State them once,
early in the chapter, and hold them everywhere.

1. **Per scene, never pooled.** Scene difficulty spans about 7 dB and the
   baseline's own dispersion varies several-fold across scenes. A
   scene-averaged fidelity figure describes no scene in the corpus.
2. **Resolution rule.** An effect is reported as resolved only at two or more
   standard errors against that scene's baseline dispersion. Everything else is
   `UNRESOLVED`, which is a statement about three repeats, never a statement
   that the effect is zero.
3. **PSNR interactions are `UNDETERMINED` by construction.** The smallest
   interaction the design can resolve at three repeats exceeds the largest PSNR
   main effect observed. Tabulate them for completeness, mark them, and rest no
   claim on them. Adjudicate interactions on LPIPS and primitive count.
4. **Registered and post-hoc are labelled in the text, not only in a
   footnote.** Every quantitative statement carries its status: pre-registered
   prediction, pre-registered instrument reporting an unregistered direction,
   or post-hoc description.
5. **No causal verb for an observed association.** Reserve causal language for
   contrasts the design isolates.

## 16.4 Required section architecture

One chapter section per analysis section, in this order. The chapter follows
the evidence's own structure so that a reader can move between them.

| Chapter 4 section | Analysis source | Content | Status to assign |
| ----------------- | --------------- | ------- | ---------------- |
| 4.1 Campaign as executed | §0 | Cells, scenes, repeats, hardware, GPU-hours, retries, effective optimizer steps, provenance including the empty commit column and its cause | Factual |
| 4.2 Noise floor and resolution | §0 | Per-scene baseline dispersion; the resolution arithmetic; the count-dispersion widening on two scenes | Factual, and the basis of every later verdict |
| 4.3 Baseline validation against the reference | §1 | SS versus A0 per scene against the pre-registered margin | Supported within a pre-specified margin |
| 4.4 Main effects | §2 | M1, M2, M3 against A0, per scene, from below and from above | Pre-registered |
| 4.5 Interactions | §3, §4 | Two-way and three-way on LPIPS and count | Pre-registered, with PSNR marked undetermined |
| 4.6 Medium-model behaviour | §5a, §5c, §5d, §5e | Collapse rates, boundary alignment, M1 cells, size versus discontinuity, the re-identification burst | Pre-registered |
| 4.7 The registered explanation and its failure | §5b | The dispersion prediction, its test, and its refutation | Contradicted — withdrawn, not qualified |
| 4.8 Post-hoc description of the coupling | §5 closing | Removal fraction, the interval in which the medium falls, and what does not predict which repeat crosses zero | Post-hoc, labelled throughout |
| 4.9 Mechanism D | §6 | A0D against A0, and the prediction written before it ran | Pre-registered, both halves held |
| 4.10 Operating points | §7 | Non-dominated cells per scene | Descriptive only; not a rate-distortion curve |
| 4.11 What the fidelity metrics cannot see | §8, §10 | Collapsed versus intact strata; the restored-image comparison | Confirmatory and exploratory respectively |
| 4.12 Geometry | §9 | Visible fraction, bounding-box inflation, including the reference's own pathology | Exploratory, single repeat |
| 4.13 Cross-campaign replication | §11 | What replicates, what does not, and the provenance limit on explaining it | Mixed; one downgrade |
| 4.14 Cost | §12 | Wall-clock, frame rate, memory, and the sub-linear relationship to count | Factual |
| 4.15 Threats and what cannot be concluded | §14 | Every unresolved, confounded, unmeasured, and single-repeat item | Explicit |

## 16.5 Required tables

Do not exceed one table per contrast family. Each carries per-scene rows,
effect sizes with their resolution marker, and a caption naming the analysis
section it comes from.

1. Campaign completion and provenance.
2. Per-scene baseline dispersion.
3. Reference-versus-baseline margin verdicts.
4. Main effects, one table per mechanism.
5. Interaction terms on LPIPS and count.
6. Collapse counts per cell per scene.
7. The dispersion-ratio strata and the rank test that refuted the prediction.
8. Cut size, entering medium state, and post-burst medium state by cell group.
9. A0D against A0 across all measured axes.
10. Non-dominated cells per scene.
11. Collapsed-versus-intact fidelity differences in units of baseline
    dispersion.
12. Cross-campaign comparison for the four shared cells.

## 16.6 Required figures

Use the exported files in `figures/`; do not rebuild figures for the chapter.

* The pipeline figure, to locate each mechanism's insertion point.
* The schedule figure, to locate the events and the burst on the iteration
  axis. This figure carries most of Section 4.6 and 4.8 visually.
* A per-scene effect plot for the main effects, if one can be drawn without
  pooling scenes.

Every figure needs a caption that states what the reader should conclude and
what the figure does not show.

## 16.7 Negative and inconvenient results that must appear

The chapter is not complete unless each of these is stated in its own right,
in the body, not relegated to a limitations paragraph:

1. The registered dispersion explanation failed its own pre-written test, and
   the account is withdrawn rather than qualified.
2. The re-identification burst is the interval in which the medium falls; it
   is this work's own remedy and it did not work.
3. The restored-image instrument's first reading was wrong, and the check that
   corrected it was added and run.
4. One mechanism's effect on one scene reverses sign across campaigns and is
   downgraded accordingly.
5. The scene on which every mechanism costs perceptual quality is identified
   and not explained away.
6. Most of the baseline's primitives are never rendered, and the unmodified
   reference carries the same property.
7. Nothing measured before a cut predicts which repeat loses a channel.

## 16.8 Prohibited in Chapter 4

In addition to the general claim discipline:

* Reporting a scene-averaged fidelity number.
* Reporting a PSNR interaction as a finding.
* Describing an unresolved effect as absent, negligible, or insignificant.
* Presenting the post-hoc account of §5 as an explanation rather than a
  description.
* Presenting the Pareto description as a rate-distortion result.
* Presenting the restored-image figures as restoration accuracy.
* Attributing the cross-campaign discrepancy to a specific code change without
  provenance to support it.
* Any sentence in which a mechanism "causes" an outcome the design associates
  but does not isolate.

## 16.9 Completion criteria

Chapter 4 is done when:

* Every table traces to a section of `FINDINGS.md`.
* Every claim carries a status from the claim-discipline list.
* Every item in 16.7 appears in the body.
* No number in the chapter is absent from the analysis.
* A reader who disagrees with the interpretation can still reuse the numbers.

---

# 17. Phase 10: Chapter 5 Construction — Conclusions

Chapter 5 states what the work established, what it did not, and what follows.
It introduces no evidence.

## 17.1 Preconditions

Chapter 4 is stable and approved. Do not draft Chapter 5 in parallel with
Chapter 4: the conclusions depend on which claims survive the results chapter.

## 17.2 Required architecture

* 5.1 Summary of the work.
* 5.2 Answers to the research questions.
* 5.3 Contributions, each at the level the evidence supports.
* 5.4 Limitations.
* 5.5 Future work.
* 5.6 Closing statement.

## 17.3 Answers to the research questions

Answer each research question in one paragraph that begins with the answer,
then its evidence, then its boundary. Required shapes:

* **Whether the mechanisms transfer.** Supported. Each moves its own target
  cost beyond repeat dispersion on every scene. State the fidelity cost
  alongside, per scene, and name the scene where every mechanism costs
  perceptual quality.
* **Whether they compose.** Answered on the metrics that resolve, and only
  those. Report the budget-bound sub-additivity on count, the sub-additive
  quality effect for the pair that shares no code path, the failed additivity
  prediction with its inconsistent sign, and the undetermined PSNR terms.
* **Whether reduction perturbs medium identifiability, and why.** Split the
  answer in two, and do not let the first half carry the second. *Whether* is
  established: reproducible, boundary-aligned, seed-conditioned, absent from
  the baseline and the reference. *Why* is open. The registered explanation
  was tested and refuted; what replaces it is descriptive and post-hoc.
* **Integration properties.** Unchanged by the campaign; each found by running
  the pipeline rather than by reading the source methods.

## 17.4 Contributions at evidence level

Claim each of these, and no more:

1. A reference-controlled factorial study of three efficiency mechanisms on a
   physically grounded underwater estimator, in which the baseline is shown
   equivalent to the published method within a pre-registered margin before any
   contrast is drawn.
2. A measured, reproducible, boundary-aligned coupling between large-cut
   simplification and the stability of the learned medium model, with its rate
   quantified per cell and per scene.
3. A pre-registered explanation of that coupling, tested at the first
   opportunity and refuted — reported as a falsified prediction, with the
   replacement description labelled post-hoc.
4. A supplementary engineering result: a continuous reduction of the primitive
   population at a resolved but small perceptual cost and an unresolved
   fidelity cost, measured against a validated baseline.
5. Instrumentation that makes the above measurable: the reference-control
   harness, the medium-collapse detector, the cross-frame depth-range sweep,
   and the restored-image self-consistency check.
6. Evidence that the composed-image metrics standard in this literature cannot
   detect the failure mode the physical model exhibits.

Do not claim a new compression algorithm, a general-purpose method, physical
accuracy, or deployment readiness.

## 17.5 Limitations

Carry forward, each in one sentence with its consequence:

* Four scenes, three repeats, one simplification budget, one codebook size.
* PSNR interactions undetermined by construction, not by outcome.
* The mechanism behind the coupling is open.
* The protections conferred by dense initialization are mutually confounded and
  cannot be separated by this design.
* Restoration accuracy is unmeasured, and the location of the restored-image
  difference is inferred from the image-formation model rather than mapped.
* One scene behaves unlike the others throughout, without an established cause.
* Whether the medium-only burst causes or merely hosts the fall is untested,
  because every simplification cell contains it.
* Provenance for the archived campaign is incomplete, and at least one archived
  run was trained from an uncommitted tree.
* No embedded hardware, power, latency, or on-vehicle evaluation was performed.

## 17.6 Future work

Derive each item from a specific failure or open question in this work. Reject
generic proposals.

1. **Deconfound the cut.** Run simplification at a removal fraction matched to
   the dense-initialization cells rather than to a fixed budget. This isolates
   the size of the cut from everything else dense initialization changes, and
   is the direct successor to the withdrawn explanation.
2. **Test the remedy.** Add a simplification cell without the medium-only
   burst. The present design cannot say whether the burst causes the fall or
   merely hosts it.
3. **Locate the restored-image damage.** Report the difference between the two
   attribute states per depth bin, which turns an inferred far-field argument
   into a measured one.
4. **Add a commitment term to the quantizer.** The straight-through estimator
   used here constrains nothing to stay near its codebook entry.
5. **Multiple operating points per mechanism**, to answer the
   rate-distortion question this design cannot.
6. **Raise the repeat count** to the level at which the interaction terms that
   matter would resolve, and state that level explicitly from the observed
   dispersion.

## 17.7 Prohibited in Chapter 5

* Introducing a number that does not appear in Chapter 4.
* Restating the withdrawn explanation as a hypothesis the work supports.
* Converting a post-hoc description into a contribution.
* Generalizing from four scenes to underwater reconstruction as a field.
* Deployment, real-time, or vehicle-readiness language.
* A future-work item that does not answer a question this work left open.

## 17.8 Completion criteria

Chapter 5 is done when every claim in it is traceable to a Chapter 4 section,
every limitation in 17.5 appears, and the research question whose *why* is open
is stated as open in the closing paragraph.

---

# 18. Claim Discipline

For every major thesis claim, assign one of:

* Supported.
* Supported within a pre-specified margin.
* Partially supported.
* Supported only for particular scenes.
* Exploratory.
* Post-hoc.
* Contradicted.
* Obsolete.
* Not tested.
* Unresolved at the current repeat count.
* Not identifiable with the current design.
* Not reproducible due to provenance limitations.

Specifically prohibit the following unless separately demonstrated:

* “Physically accurate.”
* “Physically consistent” as a synonym for non-collapsed parameters.
* “Deployment ready.”
* “Suitable for AUV deployment.”
* “Real-time” without the relevant operational threshold.
* “Statistically insignificant” when only unresolved.
* “Equivalent to SeaSplat” without the stated margin.
* “Best method” from one operating point.
* “Rate-distortion curve” from one point per mechanism.
* “The mechanism causes” where only an association was observed.
* “M1 prevents collapse because of depth-range dispersion” if the registered explanation failed.
* “The re-identification burst restores the medium” if the evidence shows otherwise.

---

# 19. Required Diagnostic Deliverables

Before drafting replacement thesis prose, produce:

1. Executive methodological verdict.
2. Final version and artifact manifest.
3. Complete material-to-research-question map.
4. Run provenance and dirty-state audit.
5. Methodology-lineage matrix.
6. Intended-design versus implementation conformity table.
7. Experiment-completion and evidence-strength audit.
8. Independent validation of the final analysis.
9. `FINDINGS.md` interpretation audit.
10. Reviewer-feedback traceability matrix.
11. Claim-validity ledger.
12. Revised research gap.
13. Candidate thesis framings.
14. Recommended framing.
15. Revised research questions.
16. Revised objectives.
17. Revised hypotheses.
18. Revised contributions.
19. Revised scope and limitations.
20. Chapter 2 section and subsection plan.
21. Chapter 1 section and subsection plan.
22. Chapter 3 section and subsection plan.
23. Citation-repair list.
24. Figure and table plan.
25. Remaining methodological blockers.
26. Ordered rewriting roadmap.
27. Explicit approval gates.
28. Chapter 4 section architecture with per-section claim status.
29. Chapter 4 table and figure inventory.
30. The list of negative results Chapter 4 must carry.
31. Chapter 5 architecture.
32. Contribution statements at evidence level.
33. Consolidated limitations list.
34. Future-work items, each traced to a specific open question.

---

# 20. Execution Gates

## Gate 1: Evidence Integrity

Complete:

* Repository and Drive reconciliation.
* Provenance audit.
* Raw-result validation.
* Reviewer-document identification.
* Thesis-version identification.

Stop and report blockers if the final run evidence cannot be reliably associated with an implementation state.

## Gate 2: Scientific Positioning

Present:

* Conservative framing.
* Stronger conditional framing.
* Recommended framing.
* Revised research questions, objectives, hypotheses, and contributions.

Obtain approval before restructuring the thesis.

## Gate 3: Thesis Architecture

Present the full revised hierarchy for:

1. Chapter 2.
2. Chapter 1.
3. Chapter 3.

Obtain approval before drafting replacement prose.

## Gate 4: Sequential Revision

Revise in this order:

1. Chapter 2.
2. Chapter 1.
3. Chapter 3.

At each stage:

* Preserve valid material.
* Preserve the author’s academic voice.
* Remove obsolete configurations.
* Correct citations and attributions.
* Eliminate duplication.
* Trace every methodological claim to evidence.
* Flag unsupported dependencies across chapters.

## Gate 5: Results-Chapter Preparation

After Chapters 2, 1, and 3 are stable, propose the Chapter 4 architecture of
Section 16 against the validated final campaign.

Present before drafting:

* The section architecture with a claim status for each section.
* The table and figure inventory.
* The list of negative results the chapter will carry, from 16.7.

Obtain approval before drafting the results prose.

## Gate 6: Conclusions

Do not draft Chapter 5 until Chapter 4 is stable and approved.

Present before drafting:

* The research-question answers in the split form required by 17.3.
* Contribution statements at evidence level.
* The consolidated limitations list.
* Future-work items, each traced to an open question in this work.

A contribution that cannot be traced to a Chapter 4 section is removed, not
reworded.

---

# 21. Required First Response

The first execution response must not rewrite the thesis.

It must report:

1. The evidence base actually accessed.
2. Repository and Drive versions.
3. Whether the 120-run completion claim is verified.
4. Provenance findings.
5. Material-to-prompt mapping.
6. Major contradictions between documentation, implementation, runs, analysis, and thesis.
7. Whether the completed campaign changes the previously approved framing.
8. Which findings remain defensible.
9. Which previous explanations must be withdrawn.
10. The complete Chapter 2, Chapter 1, and Chapter 3 surgical plan.
11. Questions or blockers requiring approval.

Do not conceal contradictory evidence for narrative convenience.

---

# 22. Manuscript Composition — Structure, Protocol and Deliverables

Merged into this document on 2026-09-24. This section is **authoritative for
the thesis structure**: `implementation/tools/make_manuscript_scaffold.py`
reads the tables below to generate the deliverable files, so the structure and
the files on disk cannot drift apart. `new-revisited-writing/thesis-structure-detailed.md`
is superseded and retained only as the record of how the structure was derived.

## 22.1 The unit of work

**One subsection = one Markdown file = one deliverable.** 123 subsections
across five chapters, under `manuscript/`. Each file is continuous prose of
300–900 words — paragraphs, not bullets — carrying its own front matter,
figure and table placeholders, and review log.

Regenerating the scaffold never overwrites a file that exists, so the structure
may be revised at any time while drafting is under way.

## 22.2 The composition loop

Every subsection passes through four passes, which are not merged: **draft**
(argument through, start to finish, no polishing), **reflect** (the draft
against its evidence — every number, every claim's strength against its
resolution status), **review** (the three personas of §22.3, in order),
**refine** (apply the findings; record any rejected finding and why).

## 22.3 The three standing reviewers

Applied to every subsection, read in order, each leaving written findings in
the deliverable's review log.

| | Persona | Reads for |
|---|---|---|
| 1 | **Domain Researcher** — publishes and referees in 3DGS, novel view synthesis, 3D reconstruction and underwater image formation | Scientific correctness; whether the mechanism is described as it behaves rather than as its source paper advertises; whether medium parameters are interpreted within what a renormalised depth permits; whether the novelty claim is the right size |
| 2 | **Supervisor** — reads for argument and prose, and takes the devil's advocate position deliberately | Whether the subsection opens by stating what it establishes; whether there is one argument or three; where the weakest sentence is; what a hostile examiner attacks first; whether an inconvenient result is being softened by word choice |
| 3 | **Journal Reviewer** — reviews for a Q1 venue | Statistics reported with quantity, uncertainty, n and test; every figure and table called out and captioned to stand alone; APA 7th throughout; consistent tense; reproducibility from text plus repository |

Full definitions, the review-log format and the definition of done are in
`new-revisited-writing/writing-protocol.md`.

## 22.4 Citation discipline

The controlled register is the twelve-entry APA reference list in
`new-revisited-writing/chapter-3-methodology.md`, which already carries the
warning that author names and venues require verification against the PDFs.

**Cite only from the register.** Anything else is marked `[CITE-NEEDED: claim]`
— visible, greppable, and blocking `final` status. Never invent a reference,
and never infer an author, year, venue or DOI that has not been seen. Chapter II
§2.6.1 remains blocked because the source reading is not in the repository, and
that block stays visible until the reading is done.

## 22.5 Figures and tables

Every figure gets a placeholder at first mention naming its **real path** when
the asset exists — `figures/chapter4/` holds 34 built figures — and its final
caption. An asset that does not exist is marked `[DATA-NEEDED]` with one line
saying what would have to be collected, and is never described as though built.
Captions stand alone.

## 22.6 Reporting conventions

Inherited from the campaign and not negotiable during writing: evaluation is
anchored on **SS** with stored size the stated exception; an effect is
**resolved** when its 2 SE interval excludes the null at n = 3, and
`UNRESOLVED` never means zero; **PSNR interactions are `UNDETERMINED` by
construction**; β magnitudes are dimensionless against a per-frame renormalised
depth; every fidelity metric describes Î alone; negative results appear in the
body where they bear on the claim.

## 22.7 Order of work

**IV → III → V → I → II.** Chapter IV first: it has approved research
questions, a complete evidence base and its figures built. Chapter III next as
the most wrong. Chapter V follows from IV directly. I and II last, because an
introduction should be written once the thing it introduces exists.

## 22.8 The structure

# CHAPTER I — INTRODUCTION  ·  10 pp (from 8)

Deliverables in `manuscript/ch1-introduction/`.

| § | Title | Action | Evidence | RQ | Deliverable |
|---|---|---|---|---|---|
| **1.1** | **Background** | Refine | — | — | *(section)* |
| 1.1.1 | Underwater 3D Reconstruction and Its Applications | Retain | LIT | — | `1-1-1-underwater-3d-reconstruction-and-its-applications.md` |
| 1.1.2 | Radiance Fields and the Shift to Explicit Primitives | Retain | LIT | — | `1-1-2-radiance-fields-and-the-shift-to-explicit-primitives.md` |
| 1.1.3 | Physically Grounded Underwater Reconstruction | Refine | LIT | — | `1-1-3-physically-grounded-underwater-reconstruction.md` |
| 1.1.4 | The Representation Cost of Explicit Primitives | Add | §9 | — | `1-1-4-the-representation-cost-of-explicit-primitives.md` |
| **1.2** | **Problem Statement** | Refine | — | — | *(section)* |
| 1.2.1 | Efficiency Mechanisms Are Validated in Isolation | Refine | LIT | — | `1-2-1-efficiency-mechanisms-are-validated-in-isolation.md` |
| 1.2.2 | Composition Is Unmeasured on a Physically Grounded Estimator | Add | §3, §4 | — | `1-2-2-composition-is-unmeasured-on-a-physically-grounded-estimator.md` |
| 1.2.3 | Reductions Are Claimed Without Establishing the Baseline | Add | §1 | — | `1-2-3-reductions-are-claimed-without-establishing-the-baseline.md` |
| 1.2.4 | Fidelity Metrics May Not Detect Physical Failure | Add | §8 | — | `1-2-4-fidelity-metrics-may-not-detect-physical-failure.md` |
| **1.3** | **Research Questions and Hypotheses** | Add | — | — | *(section)* |
| 1.3.1 | Research Questions | Add | PLAN | — | `1-3-1-research-questions.md` |
| 1.3.2 | Hypotheses and Pre-Registration | Add | PLAN | — | `1-3-2-hypotheses-and-pre-registration.md` |
| **1.4** | **Research Objectives** | Refine | PLAN | — | *(section)* |
| **1.5** | **Research Benefits** | Refine | — | — | *(section)* |
| 1.5.1 | Practical Benefits | Refine | §2, §7 | — | `1-5-1-practical-benefits.md` |
| 1.5.2 | Methodological Benefits | Add | §1, §0 | — | `1-5-2-methodological-benefits.md` |
| **1.6** | **Contributions** | Add | all | — | *(section)* |
| **1.7** | **Scope and Limitations** | Replace | — | — | *(section)* |
| 1.7.1 | Scope of the Experimental Campaign | Replace | §0 | — | `1-7-1-scope-of-the-experimental-campaign.md` |
| 1.7.2 | Delimitations | Replace | §14 | — | `1-7-2-delimitations.md` |
| 1.7.3 | What This Thesis Does Not Claim | Add | §14 | — | `1-7-3-what-this-thesis-does-not-claim.md` |
| **1.8** | **Thesis Organisation** | Retain | — | — | *(section)* |

---

# CHAPTER II — LITERATURE REVIEW  ·  38 pp (from 34)

Deliverables in `manuscript/ch2-literature-review/`.

| § | Title | Action | Evidence | RQ | Deliverable |
|---|---|---|---|---|---|
| **2.1** | **Fundamentals of 3D Reconstruction and Scene Representation** | Retain | — | — | *(section)* |
| 2.1.1 | Structure from Motion and Multi-View Geometry | Retain | LIT | — | `2-1-1-structure-from-motion-and-multi-view-geometry.md` |
| 2.1.2 | Explicit and Implicit Scene Representations | Retain | LIT | — | `2-1-2-explicit-and-implicit-scene-representations.md` |
| **2.2** | **Neural Radiance Fields and Differentiable Rendering** | Retain | — | — | *(section)* |
| 2.2.1 | Volume Rendering Formulation | Retain | LIT | — | `2-2-1-volume-rendering-formulation.md` |
| 2.2.2 | Acceleration Strategies and Their Limits | Retain | LIT | — | `2-2-2-acceleration-strategies-and-their-limits.md` |
| **2.3** | **Explicit Radiance Fields and 3D Gaussian Splatting** | Refine | — | — | *(section)* |
| 2.3.1 | Primitive Parameterisation and Rasterisation | Retain | LIT | — | `2-3-1-primitive-parameterisation-and-rasterisation.md` |
| 2.3.2 | Adaptive Density Control | Add | LIT | — | `2-3-2-adaptive-density-control.md` |
| 2.3.3 | Known Failure Modes of the Representation | Add | LIT, §9 | — | `2-3-3-known-failure-modes-of-the-representation.md` |
| **2.4** | **Physical Image Formation in Underwater Environments** | Refine | — | — | *(section)* |
| 2.4.1 | Attenuation and Backscatter | Retain | LIT | — | `2-4-1-attenuation-and-backscatter.md` |
| 2.4.2 | Physics-Aware Neural Rendering | Retain | LIT | — | `2-4-2-physics-aware-neural-rendering.md` |
| 2.4.3 | Physics-Aware Gaussian Splatting | Refine | LIT | — | `2-4-3-physics-aware-gaussian-splatting.md` |
| 2.4.4 | Identifiability of the Medium Parameters | Add | LIT | — | `2-4-4-identifiability-of-the-medium-parameters.md` |
| **2.5** | **Efficiency Mechanisms in Radiance-Field Modelling** | Reorganize | — | — | *(section)* |
| 2.5.1 | Initialisation and Densification Control | Add | LIT | — | `2-5-1-initialisation-and-densification-control.md` |
| 2.5.2 | Spatial Simplification and Pruning | Add | LIT | — | `2-5-2-spatial-simplification-and-pruning.md` |
| 2.5.3 | Attribute Quantisation and Storage Compression | Add | LIT | — | `2-5-3-attribute-quantisation-and-storage-compression.md` |
| 2.5.4 | Domain-Transfer Risk | Add | LIT | — | `2-5-4-domain-transfer-risk.md` |
| **2.6** | **Methodological Foundations** | Add | — | — | *(section)* |
| 2.6.1 | Factorial Design and Interaction Estimation | Add | LIT | — | `2-6-1-factorial-design-and-interaction-estimation.md` |
| 2.6.2 | Repeated-Run Uncertainty in Stochastic Optimisation | Add | LIT, §0 | — | `2-6-2-repeated-run-uncertainty-in-stochastic-optimisation.md` |
| 2.6.3 | Equivalence Testing Against a Margin | Add | LIT | — | `2-6-3-equivalence-testing-against-a-margin.md` |
| 2.6.4 | Pre-Registration and Falsifiability | Add | LIT | — | `2-6-4-pre-registration-and-falsifiability.md` |
| 2.6.5 | Rate–Distortion and Pareto Evaluation | Add | LIT, §7 | — | `2-6-5-rate-distortion-and-pareto-evaluation.md` |
| **2.7** | **Literature Review** | Replace | — | — | *(section)* |
| 2.7.1 | Review Protocol | Add | LIT | — | `2-7-1-review-protocol.md` |
| 2.7.2 | Per-Paper Analysis | Add — BLOCKED | LIT | — | `2-7-2-per-paper-analysis.md` |
| 2.7.3 | Synthesis Table | Retain | LIT | — | `2-7-3-synthesis-table.md` |
| 2.7.4 | Trends and Unresolved Limitations | Refine | LIT | — | `2-7-4-trends-and-unresolved-limitations.md` |
| **2.8** | **Research Gap** | Replace | LIT | — | *(section)* |

---

# CHAPTER III — RESEARCH METHODOLOGY  ·  42 pp (from 27)

Deliverables in `manuscript/ch3-methodology/`.

| § | Title | Action | Evidence | RQ | Deliverable |
|---|---|---|---|---|---|
| **3.1** | **Conceptual Framework** | Refine | — | — | *(section)* |
| 3.1.1 | The Baseline Estimator and Its Coupled Medium Model | Refine | CD | — | `3-1-1-the-baseline-estimator-and-its-coupled-medium-model.md` |
| 3.1.2 | Insertion Points of the Efficiency Mechanisms | Add | Figure 0 | — | `3-1-2-insertion-points-of-the-efficiency-mechanisms.md` |
| 3.1.3 | Framework Diagram | Refine | Figure 0 | — | `3-1-3-framework-diagram.md` |
| **3.2** | **Research Stages** | Refine | §0 | — | *(section)* |
| **3.3** | **SeaThru-NeRF Dataset** | Retain | — | — | *(section)* |
| 3.3.1 | Acquisition and Provenance | Retain | LIT | — | `3-3-1-acquisition-and-provenance.md` |
| 3.3.2 | Scene Composition and Characteristics | Refine | CD | — | `3-3-2-scene-composition-and-characteristics.md` |
| 3.3.3 | Data Structure and Input–Output Definition | Retain | CD | — | `3-3-3-data-structure-and-input-output-definition.md` |
| **3.4** | **Data Preprocessing** | Refine | — | — | *(section)* |
| 3.4.1 | Image Preparation and Undistortion | Refine | CD | — | `3-4-1-image-preparation-and-undistortion.md` |
| 3.4.2 | Camera Parameter Handling | Retain | CD | — | `3-4-2-camera-parameter-handling.md` |
| 3.4.3 | Scene Normalisation and Coordinate Consistency | Retain | CD | — | `3-4-3-scene-normalisation-and-coordinate-consistency.md` |
| 3.4.4 | Data Partitioning | Refine | CD | — | `3-4-4-data-partitioning.md` |
| 3.4.5 | Output of the Preprocessing Stage | Retain | CD | — | `3-4-5-output-of-the-preprocessing-stage.md` |
| **3.5** | **Efficiency Mechanisms Under Test** | Reorganize | — | — | *(section)* |
| 3.5.1 | Overview and Insertion Points | Refine | Figure 1 | — | `3-5-1-overview-and-insertion-points.md` |
| 3.5.2 | M1 — Deterministic Initialisation | Refine | CD | — | `3-5-2-m1-deterministic-initialisation.md` |
| 3.5.3 | M2 — Spatial Reorganisation | Refine | CD | — | `3-5-3-m2-spatial-reorganisation.md` |
| 3.5.4 | M3 — Attribute-Level Quantisation | Refine | CD | — | `3-5-4-m3-attribute-level-quantisation.md` |
| 3.5.5 | Mechanism D — Gradient Detachment | Add | CD | — | `3-5-5-mechanism-d-gradient-detachment.md` |
| 3.5.6 | Implementation-Delta Register | Add | CD | — | `3-5-6-implementation-delta-register.md` |
| **3.6** | **Experimental Design** | Replace | — | — | *(section)* |
| 3.6.1 | Factorial Structure and Cell Definition | Add | PLAN | — | `3-6-1-factorial-structure-and-cell-definition.md` |
| 3.6.2 | Reference Control and Equivalence Margin | Add | §1, PLAN | — | `3-6-2-reference-control-and-equivalence-margin.md` |
| 3.6.3 | Scene Blocking and Repeats | Add | §0 | — | `3-6-3-scene-blocking-and-repeats.md` |
| 3.6.4 | Pre-Registration of the Analysis Plan | Add | PLAN | — | `3-6-4-pre-registration-of-the-analysis-plan.md` |
| 3.6.5 | Resolution Rule and Claim Vocabulary | Add | PLAN | — | `3-6-5-resolution-rule-and-claim-vocabulary.md` |
| 3.6.6 | Training Procedure and Intervention Schedule | Refine | §0, CD | — | `3-6-6-training-procedure-and-intervention-schedule.md` |
| 3.6.7 | Execution Environment, Provenance and Reproducibility | Add | §0 | — | `3-6-7-execution-environment-provenance-and-reproducibility.md` |
| **3.7** | **Evaluation Metrics** | Reorganize | — | — | *(section)* |
| 3.7.1 | Reconstruction Fidelity | Refine | CD | — | `3-7-1-reconstruction-fidelity.md` |
| 3.7.2 | Representation and Computational Cost | Refine | CD | — | `3-7-2-representation-and-computational-cost.md` |
| 3.7.3 | Medium-Model Diagnostics | Add | CD | — | `3-7-3-medium-model-diagnostics.md` |
| 3.7.4 | Geometric and Restoration Diagnostics | Add | CD | — | `3-7-4-geometric-and-restoration-diagnostics.md` |
| 3.7.5 | Scope and Repeat Coverage of Each Metric | Add | §0 | — | `3-7-5-scope-and-repeat-coverage-of-each-metric.md` |
| **3.8** | **Analysis Procedure** | Add | — | — | *(section)* |
| 3.8.1 | Contrast Equations | Add | PLAN | — | `3-8-1-contrast-equations.md` |
| 3.8.2 | Uncertainty Estimation | Add | §0 | — | `3-8-2-uncertainty-estimation.md` |
| 3.8.3 | Treatment of Unresolved and Undetermined Effects | Add | §0 | — | `3-8-3-treatment-of-unresolved-and-undetermined-effects.md` |

---

# CHAPTER IV — RESULTS AND DISCUSSION  ·  60 pp (from 63)

Deliverables in `manuscript/ch4-results/`. Structure per
`new-revisited-writing/chapter-04-specification.md` Revision 3, which is
authoritative for this chapter's content.

| § | Title | Action | Evidence | RQ | Deliverable |
|---|---|---|---|---|---|
| **4.1** | **Experimental Overview** | Rewrite | §0 | — | *(section)* |
| 4.1.1 | Scope of the Completed Campaign | Rewrite | §0 | — | `4-1-1-scope-of-the-completed-campaign.md` |
| 4.1.2 | Evaluation Criteria and Reporting Conventions | Add | §0 | — | `4-1-2-evaluation-criteria-and-reporting-conventions.md` |
| 4.1.3 | Repeat Dispersion as the Measurement Baseline | Add | §0 | — | `4-1-3-repeat-dispersion-as-the-measurement-baseline.md` |
| 4.1.4 | Provenance and Experimental Integrity | Add | §0 | — | `4-1-4-provenance-and-experimental-integrity.md` |
| **4.2** | **Baseline Characterisation and Validation** | Reframe | §1 | validation | *(section)* |
| 4.2.1 | Equivalence to the Unmodified Reference | Add | §1 | validation | `4-2-1-equivalence-to-the-unmodified-reference.md` |
| 4.2.2 | Reconstruction Fidelity and Efficiency per Scene | Rewrite | §2 | validation | `4-2-2-reconstruction-fidelity-and-efficiency-per-scene.md` |
| 4.2.3 | Qualitative Reconstruction Characteristics | Add | renders | validation | `4-2-3-qualitative-reconstruction-characteristics.md` |
| 4.2.4 | The Learned Medium Model | Add | §2b | validation | `4-2-4-the-learned-medium-model.md` |
| 4.2.5 | Medium Decomposition, Qualitatively | Add | renders | validation | `4-2-5-medium-decomposition-qualitatively.md` |
| 4.2.6 | Representation Characteristics and the Invisible Population | Rewrite | §9 | validation | `4-2-6-representation-characteristics-and-the-invisible-population.md` |
| 4.2.7 | Baseline Medium Stability | Add | §5a | validation | `4-2-7-baseline-medium-stability.md` |
| **4.3** | **Component 1 — Deterministic Initialisation (M1)** | Rewrite | §2 | RQ1 | *(section)* |
| 4.3.1 | Reconstruction Fidelity per Scene | Rewrite | §2 | RQ1 | `4-3-1-reconstruction-fidelity-per-scene.md` |
| 4.3.2 | Efficiency Outcome | Rewrite | §2, §12 | RQ1 | `4-3-2-efficiency-outcome.md` |
| 4.3.3 | Effect on the Medium Model | Add | §5c | RQ3 | `4-3-3-effect-on-the-medium-model.md` |
| 4.3.4 | Qualitative and Geometric Behaviour | Refine | §9 | RQ1 | `4-3-4-qualitative-and-geometric-behaviour.md` |
| 4.3.5 | Discussion | Refine | — | RQ1 | `4-3-5-discussion.md` |
| 4.3.6 | Boundary | Add | §14 | RQ1 | `4-3-6-boundary.md` |
| **4.4** | **Component 2 — Spatial Reorganisation (M2)** | Rewrite | §2 | RQ1 | *(section)* |
| 4.4.1 | Reconstruction Fidelity per Scene | Rewrite | §2 | RQ1 | `4-4-1-reconstruction-fidelity-per-scene.md` |
| 4.4.2 | Efficiency Outcome | Rewrite | §2, §12 | RQ1 | `4-4-2-efficiency-outcome.md` |
| 4.4.3 | Effect on the Medium Model | Add | §5a | RQ3 | `4-4-3-effect-on-the-medium-model.md` |
| 4.4.4 | Qualitative and Geometric Behaviour | Refine | renders | RQ1 | `4-4-4-qualitative-and-geometric-behaviour.md` |
| 4.4.5 | Discussion | Refine | — | RQ1 | `4-4-5-discussion.md` |
| 4.4.6 | Boundary | Add | §14 | RQ1 | `4-4-6-boundary.md` |
| **4.5** | **Component 3 — Attribute-Level Quantisation (M3)** | Rewrite | §2 | RQ1 | *(section)* |
| 4.5.1 | Reconstruction Fidelity per Scene | Rewrite | §2 | RQ1 | `4-5-1-reconstruction-fidelity-per-scene.md` |
| 4.5.2 | Efficiency Outcome | Refine | §2, §12 | RQ1 | `4-5-2-efficiency-outcome.md` |
| 4.5.3 | Effect on the Medium Model | Add | §5a | RQ3 | `4-5-3-effect-on-the-medium-model.md` |
| 4.5.4 | Qualitative and Geometric Behaviour | Refine | renders | RQ1 | `4-5-4-qualitative-and-geometric-behaviour.md` |
| 4.5.5 | Discussion | Refine | — | RQ1 | `4-5-5-discussion.md` |
| 4.5.6 | Boundary | Add | §14 | RQ1 | `4-5-6-boundary.md` |
| 4.5.7 | Effect on the Restored Image | Add | §10 | RQ1 | `4-5-7-effect-on-the-restored-image.md` |
| **4.6** | **Combined Configurations and Interactions** | Add | §3, §4 | RQ2 | *(section)* |
| 4.6.1 | Estimating Interactions in This Design | Add | §0, §3 | RQ2 | `4-6-1-estimating-interactions-in-this-design.md` |
| 4.6.2 | Initialisation × Simplification | Add | §3 | RQ2 | `4-6-2-initialisation-simplification.md` |
| 4.6.3 | Simplification × Quantisation | Add | §3 | RQ2 | `4-6-3-simplification-quantisation.md` |
| 4.6.4 | Initialisation × Quantisation | Add | §3 | RQ2 | `4-6-4-initialisation-quantisation.md` |
| 4.6.5 | Three-Way Interaction | Add | §4 | RQ2 | `4-6-5-three-way-interaction.md` |
| 4.6.6 | Operating Points Across Configurations | Add | §7 | RQ2 | `4-6-6-operating-points-across-configurations.md` |
| **4.7** | **Coupling Between Simplification and the Medium Model** | Add | §5 | RQ3 | *(section)* |
| 4.7.1 | Incidence and Boundary Alignment | Add | §5a | RQ3 | `4-7-1-incidence-and-boundary-alignment.md` |
| 4.7.2 | Final Size Is Not the Cause | Add | §5d | RQ3 | `4-7-2-final-size-is-not-the-cause.md` |
| 4.7.3 | The Registered Explanation and Its Refutation | Add | §5b | RQ3 | `4-7-3-the-registered-explanation-and-its-refutation.md` |
| 4.7.4 | What the Diagnostics Show Instead | Add | §5 | RQ3 | `4-7-4-what-the-diagnostics-show-instead.md` |
| 4.7.5 | The Re-Identification Burst | Add | §5e | RQ3 | `4-7-5-the-re-identification-burst.md` |
| 4.7.6 | Physical Consequence | Add | §5a | RQ3 | `4-7-6-physical-consequence.md` |
| **4.8** | **Detecting Failure: the Limits of Fidelity Metrics** | Add | §8, §10 | RQ4 | *(section)* |
| 4.8.1 | Collapsed Versus Intact Strata | Add | §8 | RQ4 | `4-8-1-collapsed-versus-intact-strata.md` |
| 4.8.2 | Restoration Consistency Under Quantisation | Add | §10 | RQ4 | `4-8-2-restoration-consistency-under-quantisation.md` |
| 4.8.3 | Implication for Evaluation Practice | Add | §8, §10 | RQ4 | `4-8-3-implication-for-evaluation-practice.md` |
| **4.9** | **Supplementary Contrast: Gradient Detachment** | Add | §6 | supplementary | *(section)* |
| 4.9.1 | Rationale and Why It Is Not a Fourth Factor | Add | §6 | supplementary | `4-9-1-rationale-and-why-it-is-not-a-fourth-factor.md` |
| 4.9.2 | Quantitative Comparison Against the Baseline | Add | §6 | supplementary | `4-9-2-quantitative-comparison-against-the-baseline.md` |
| 4.9.3 | Discussion | Add | §6 | supplementary | `4-9-3-discussion.md` |
| **4.10** | **Replication Against the Archived Campaign** | Add | §11 | replication | *(section)* |
| 4.10.1 | Replication Outcome per Comparison | Add | §11 | replication | `4-10-1-replication-outcome-per-comparison.md` |
| 4.10.2 | What the Provenance Limit Prevents | Add | §0, §11 | replication | `4-10-2-what-the-provenance-limit-prevents.md` |
| **4.11** | **Synthesis** | Rewrite | all | all | *(section)* |
| 4.11.1 | Alignment with the Research Questions | Rewrite | all | all | `4-11-1-alignment-with-the-research-questions.md` |
| 4.11.2 | What the Campaign Establishes | Add | all | all | `4-11-2-what-the-campaign-establishes.md` |
| 4.11.3 | What Remains Open | Add | all | all | `4-11-3-what-remains-open.md` |
| **4.12** | **Limitations of the Study** | Retain, expand | §14 | — | *(section)* |
| 4.12.1 | Experimental Limitations | Refine | §14 | — | `4-12-1-experimental-limitations.md` |
| 4.12.2 | Methodological Limitations | Refine | §14 | — | `4-12-2-methodological-limitations.md` |
| 4.12.3 | Unresolved and Undetermined by Design | Add | §0, §14 | — | `4-12-3-unresolved-and-undetermined-by-design.md` |
| 4.12.4 | Threats to External Validity | Add | §14 | — | `4-12-4-threats-to-external-validity.md` |

---

# CHAPTER V — CONCLUSIONS AND RECOMMENDATIONS  ·  11 pp (from 7)

Deliverables in `manuscript/ch5-conclusions/`.

| § | Title | Action | Evidence | RQ | Deliverable |
|---|---|---|---|---|---|
| **5.1** | **Conclusions** | Replace | — | — | *(section)* |
| 5.1.1 | The Mechanisms Transfer, at Scene-Specific Cost | Replace | §2 | — | `5-1-1-the-mechanisms-transfer-at-scene-specific-cost.md` |
| 5.1.2 | The Mechanisms Do Not Compose Additively | Replace | §3, §4 | — | `5-1-2-the-mechanisms-do-not-compose-additively.md` |
| 5.1.3 | Population Reduction Perturbs Medium Identifiability | Add | §5a | — | `5-1-3-population-reduction-perturbs-medium-identifiability.md` |
| 5.1.4 | The Mechanism of That Coupling Remains Open | Add | §5b | — | `5-1-4-the-mechanism-of-that-coupling-remains-open.md` |
| 5.1.5 | Composed-Image Metrics Cannot Detect the Failure | Add | §8, §10 | — | `5-1-5-composed-image-metrics-cannot-detect-the-failure.md` |
| 5.1.6 | Integration Properties of the Composition | Refine | CD | — | `5-1-6-integration-properties-of-the-composition.md` |
| 5.1.7 | Overall Conclusion | Refine | all | — | `5-1-7-overall-conclusion.md` |
| **5.2** | **Research Contributions** | Replace | all | — | *(section)* |
| **5.3** | **Limitations** | Add as its own section | §14 | — | *(section)* |
| **5.4** | **Recommendations for Future Work** | Replace | — | — | *(section)* |
| 5.4.1 | Deconfounding the Size of the Cut | Add | §5 | — | `5-4-1-deconfounding-the-size-of-the-cut.md` |
| 5.4.2 | Testing the Re-Identification Burst | Add | §5e | — | `5-4-2-testing-the-re-identification-burst.md` |
| 5.4.3 | Locating the Restoration Difference | Add | §10 | — | `5-4-3-locating-the-restoration-difference.md` |
| 5.4.4 | Constraining the Quantiser | Add | §10 | — | `5-4-4-constraining-the-quantiser.md` |
| 5.4.5 | Multiple Operating Points per Mechanism | Add | §7 | — | `5-4-5-multiple-operating-points-per-mechanism.md` |
| 5.4.6 | Repeat Count Required to Resolve Interactions | Add | §0 | — | `5-4-6-repeat-count-required-to-resolve-interactions.md` |
| **5.5** | **Closing Remarks** | Add | — | — | *(section)* |

## 22.9 Gate 7: Manuscript Composition

A chapter passes when every subsection is `final` under the definition in
`writing-protocol.md` §9: four passes complete with all three personas logged;
no `[CITE-NEEDED]`, `[DATA-NEEDED]` or `[TODO]` markers; every number traced to
a named artefact and every figure path resolving; claim strength matching
resolution status throughout; and one end-to-end reading for flow, logged at
chapter level by the Supervisor persona.
