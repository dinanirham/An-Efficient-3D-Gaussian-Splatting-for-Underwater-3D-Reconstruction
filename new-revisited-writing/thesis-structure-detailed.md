# Detailed thesis structure — sections and subsections, all five chapters

> **Superseded on 2026-09-24.** The structure now lives in `THESIS.md` §22.8,
> which the scaffold generator reads directly. This document is retained as the
> record of how the structure was derived, not as a source of truth. Edit
> `THESIS.md`, not this file.

Companion to `thesis-outline-revised.md`, which gives the diagnosis and the
per-chapter actions. This document is the hierarchy itself, at the level of
detail a table of contents requires, so that drafting can begin section by
section without further structural decisions.

**Action** — Retain · Refine · Reorganize · Replace · Remove · **Add** (new).
**Evidence** — §n = `analysis/campaign-2026-09/FINDINGS.md`; PLAN = the
pre-registered analysis plan; CD = implementation-delta register; LIT =
literature, not campaign evidence.
**Pages** — indicative, against a 153-page approved draft.

---

# CHAPTER I — INTRODUCTION  ·  10 pp (from 8)

| § | Title | Action | Content | Evidence |
|---|---|---|---|---|
| 1.1 | **Background** | Refine | | |
| 1.1.1 | Underwater 3D Reconstruction and Its Applications | Retain | Survey, inspection, marine science motivation | LIT |
| 1.1.2 | Radiance Fields and the Shift to Explicit Primitives | Retain | NeRF → 3DGS, why explicit representations won on speed | LIT |
| 1.1.3 | Physically Grounded Underwater Reconstruction | Refine | The medium model as a scientific output, not only a correction | LIT |
| 1.1.4 | The Representation Cost of Explicit Primitives | **Add** | Millions of primitives per scene; and that most of them are never rendered | §9 |
| 1.2 | **Problem Statement** | Refine | | |
| 1.2.1 | Efficiency Mechanisms Are Validated in Isolation | Refine | Each source method reports its own mechanism alone, on terrestrial scenes | LIT |
| 1.2.2 | Composition Is Unmeasured on a Physically Grounded Estimator | **Add** | The interaction question the thesis answers | §3, §4 |
| 1.2.3 | Reductions Are Claimed Without Establishing the Baseline | **Add** | Why a reference control precedes every contrast here | §1 |
| 1.2.4 | Fidelity Metrics May Not Detect Physical Failure | **Add** | Motivates the diagnostic instruments | §8 |
| 1.3 | **Research Questions and Hypotheses** | **Add** | | |
| 1.3.1 | Research Questions | **Add** | RQ1–RQ4 (appendix of the outline document) | PLAN |
| 1.3.2 | Hypotheses and Pre-Registration | **Add** | H1, H3, H5 and the falsification condition, registered before the campaign | PLAN |
| 1.4 | **Research Objectives** | Refine | Objectives of characterisation, mapped one-to-one to RQ1–RQ4 | PLAN |
| 1.5 | **Research Benefits** | Refine | | |
| 1.5.1 | Practical Benefits | Refine | Mechanism selection under a stated budget | §2, §7 |
| 1.5.2 | Methodological Benefits | **Add** | A reusable protocol: reference control, repeats, pre-registration | §1, §0 |
| 1.6 | **Contributions** | **Add** | Six, at evidence level; mirrors §5.2 | all |
| 1.7 | **Scope and Limitations** | Replace | | |
| 1.7.1 | Scope of the Experimental Campaign | Replace | 4 scenes, 10 configurations, 3 repeats, one budget, one codebook size, one accelerator | §0 |
| 1.7.2 | Delimitations | Replace | Offline evaluation; no embedded hardware; no multi-budget sweep | §14 |
| 1.7.3 | What This Thesis Does Not Claim | **Add** | Not physical accuracy; not deployment readiness; medium *stability* ≠ medium *accuracy* | §14 |
| 1.8 | **Thesis Organisation** | Retain | One paragraph per chapter | — |

---

# CHAPTER II — LITERATURE REVIEW  ·  38 pp (from 34)

| § | Title | Action | Content | Evidence |
|---|---|---|---|---|
| 2.1 | **Fundamentals of 3D Reconstruction and Scene Representation** | Retain | | |
| 2.1.1 | Structure from Motion and Multi-View Geometry | Retain | Citation check only | LIT |
| 2.1.2 | Explicit and Implicit Scene Representations | Retain | Citation check only | LIT |
| 2.2 | **Neural Radiance Fields and Differentiable Rendering** | Retain | | |
| 2.2.1 | Volume Rendering Formulation | Retain | | LIT |
| 2.2.2 | Acceleration Strategies and Their Limits | Retain | | LIT |
| 2.3 | **Explicit Radiance Fields and 3D Gaussian Splatting** | Refine | | |
| 2.3.1 | Primitive Parameterisation and Rasterisation | Retain | | LIT |
| 2.3.2 | Adaptive Density Control | **Add** | The clone/split/prune signal. Chapter IV's results turn on this mechanism; the current draft does not describe it | LIT |
| 2.3.3 | Known Failure Modes of the Representation | **Add** | Floaters, detached clusters, invisible primitives | LIT, §9 |
| 2.4 | **Physical Image Formation in Underwater Environments** | Refine | | |
| 2.4.1 | Attenuation and Backscatter | Retain | | LIT |
| 2.4.2 | Physics-Aware Neural Rendering | Retain | SeaThru-NeRF lineage | LIT |
| 2.4.3 | Physics-Aware Gaussian Splatting | Refine | SeaSplat: the estimator this thesis extends | LIT |
| 2.4.4 | Identifiability of the Medium Parameters | **Add** | What the parameters are fitted against, and why that fit need not be unique. The conceptual basis for §4.7 | LIT |
| 2.5 | **Efficiency Mechanisms in Radiance-Field Modelling** | Reorganize | | |
| 2.5.1 | Initialisation and Densification Control | **Add** | Dense-correspondence initialisation lineage | LIT |
| 2.5.2 | Spatial Simplification and Pruning | **Add** | Importance-weighted simplification; budget formulations | LIT |
| 2.5.3 | Attribute Quantisation and Storage Compression | **Add** | Vector quantisation; the straight-through estimator and what it does not constrain | LIT |
| 2.5.4 | Domain-Transfer Risk | **Add** | Every source method was validated without a medium model. This is the transfer the thesis tests | LIT |
| 2.6 | **Methodological Foundations** | **Add** | New section; justifies Chapter III | |
| 2.6.1 | Factorial Design and Interaction Estimation | **Add** | | LIT |
| 2.6.2 | Repeated-Run Uncertainty in Stochastic Optimisation | **Add** | | LIT, §0 |
| 2.6.3 | Equivalence Testing Against a Margin | **Add** | | LIT |
| 2.6.4 | Pre-Registration and Falsifiability | **Add** | | LIT |
| 2.6.5 | Rate–Distortion and Pareto Evaluation | **Add** | And why one operating point per mechanism cannot yield a curve | LIT, §7 |
| 2.7 | **Literature Review** | Replace | | |
| 2.7.1 | Review Protocol | **Add** | Sources, inclusion criteria, extraction fields | LIT |
| 2.7.2 | Per-Paper Analysis | **Add — BLOCKED** | Problem, method, evaluation, dataset, metrics, results, limitations, relevance, per central paper | LIT |
| 2.7.3 | Synthesis Table | Retain | Existing Table 2.1, plus an evaluation-design column | LIT |
| 2.7.4 | Trends and Unresolved Limitations | Refine | | LIT |
| 2.8 | **Research Gap** | Replace | Composition unmeasured on a physically grounded underwater estimator; no prior work establishes baseline equivalence first; no prior work reports repeat dispersion | LIT |

**Blocker.** 2.7.2 requires reading not present in the repository. It is the
only item in this structure that cannot be written from existing material.

---

# CHAPTER III — RESEARCH METHODOLOGY  ·  42 pp (from 27)

Highest-severity chapter. Every subsection marked **Add** below is a
requirement Chapter IV already depends on.

| § | Title | Action | Content | Evidence |
|---|---|---|---|---|
| 3.1 | **Conceptual Framework** | Refine | | |
| 3.1.1 | The Baseline Estimator and Its Coupled Medium Model | Refine | Image formation; the nine scalars; the depth the medium reads | CD |
| 3.1.2 | Insertion Points of the Efficiency Mechanisms | **Add** | Three mechanisms, disjoint stages, no shared code | Figure 0 |
| 3.1.3 | Framework Diagram | Refine | `figures/figure-0-optimisation-loop` | Figure 0 |
| 3.2 | **Research Stages** | Refine | Executed stage sequence, reference control first | §0 |
| 3.3 | **SeaThru-NeRF Dataset** | Retain | | |
| 3.3.1 | Acquisition and Provenance | Retain | | LIT |
| 3.3.2 | Scene Composition and Characteristics | Refine | Per-scene view counts; the camera-pairing property that §4.x's anomalous scene turns on | CD |
| 3.3.3 | Data Structure and Input–Output Definition | Retain | | CD |
| 3.4 | **Data Preprocessing** | Refine | | |
| 3.4.1 | Image Preparation and Undistortion | Refine | The undistortion decision as executed | CD |
| 3.4.2 | Camera Parameter Handling | Retain | | CD |
| 3.4.3 | Scene Normalisation and Coordinate Consistency | Retain | | CD |
| 3.4.4 | Data Partitioning | Refine | Every eighth frame by index; 75 train / 13 held out | CD |
| 3.4.5 | Output of the Preprocessing Stage | Retain | | CD |
| 3.5 | **Efficiency Mechanisms Under Test** | Reorganize | Renamed from "Proposed Method": the thesis composes and measures, it does not propose one method | |
| 3.5.1 | Overview and Insertion Points | Refine | `figures/figure-1-pipeline` | Figure 1 |
| 3.5.2 | M1 — Deterministic Initialisation | Refine | Dense correspondence, triangulation, rejection rule, disabled densification, schedule change | CD |
| 3.5.3 | M2 — Spatial Reorganisation | Refine | Importance weighting, the 200 000 budget, both events, the medium-only burst after each | CD |
| 3.5.4 | M3 — Attribute-Level Quantisation | Refine | Three codebooks, straight-through estimator, activation iteration | CD |
| 3.5.5 | Mechanism D — Gradient Detachment | **Add** | Supplementary, not a fourth factor: provably inert wherever M1 is present | CD |
| 3.5.6 | Implementation-Delta Register | **Add** | Integration decisions the source methods do not specify, each with justification | CD |
| 3.6 | **Experimental Design** | Replace | | |
| 3.6.1 | Factorial Structure and Cell Definition | **Add** | $2^3$; cells A0–A7; what each contrast estimates | PLAN |
| 3.6.2 | Reference Control and Equivalence Margin | **Add** | The unmodified upstream implementation; margin fixed before it ran | §1, PLAN |
| 3.6.3 | Scene Blocking and Repeats | **Add** | 4 × 3; why results are reported per scene and never pooled | §0 |
| 3.6.4 | Pre-Registration of the Analysis Plan | **Add** | Hypotheses and the falsification condition, committed before results were examined | PLAN |
| 3.6.5 | Resolution Rule and Claim Vocabulary | **Add** | Two standard errors; SE arithmetic for interactions; the claim-status labels | PLAN |
| 3.6.6 | Training Procedure and Intervention Schedule | Refine | 30 000 iterations; medium activation; event schedule; effective optimizer steps | §0, CD |
| 3.6.7 | Execution Environment, Provenance and Reproducibility | **Add** | Accelerator, ledger, manifests, storage policy, and the provenance limitation | §0 |
| 3.7 | **Evaluation Metrics** | Reorganize | | |
| 3.7.1 | Reconstruction Fidelity | Refine | Pooled-PSNR convention stated explicitly; SSIM; LPIPS with backbone | CD |
| 3.7.2 | Representation and Computational Cost | Refine | Count; stored bytes with container defined; render-rate protocol; peak render memory | CD |
| 3.7.3 | Medium-Model Diagnostics | **Add** | Collapse definition; cross-frame depth-range sweep; what each can and cannot detect | CD |
| 3.7.4 | Geometric and Restoration Diagnostics | **Add** | Spatial extent; restored-image self-consistency, with its consistency-not-accuracy caveat | CD |
| 3.7.5 | Scope and Repeat Coverage of Each Metric | **Add** | Which metrics exist at three repeats and which at one | §0 |
| 3.8 | **Analysis Procedure** | **Add** | New section | |
| 3.8.1 | Contrast Equations | **Add** | Main effects, two-way, three-way; additive on LPIPS, log-multiplicative on count | PLAN |
| 3.8.2 | Uncertainty Estimation | **Add** | Repeat dispersion as the error term | §0 |
| 3.8.3 | Treatment of Unresolved and Undetermined Effects | **Add** | And why PSNR interactions are undetermined by construction | §0 |

---

# CHAPTER IV — RESULTS AND DISCUSSION  ·  60 pp (from 63)

> **Superseded by `chapter-04-specification.md` (Revision 3)**, which adds the
> qualitative and medium-parameter subsections this table omits.


Detailed rationale in `chapter-04-architecture.md` (Revision 2). §4.1 and §4.2
are drafted.

| § | Title | Action | Evidence |
|---|---|---|---|
| 4.1 | **Experimental Overview** | Rewrite | §0 |
| 4.1.1 | Scope of the Completed Campaign | Rewrite | §0 |
| 4.1.2 | Evaluation Criteria and Reporting Conventions | **Add** | §0 |
| 4.1.3 | Repeat Dispersion as the Measurement Baseline | **Add** | §0 |
| 4.1.4 | Provenance and Experimental Integrity | **Add** | §0 |
| 4.2 | **Baseline Validation** | Reframe | |
| 4.2.1 | Equivalence to the Unmodified Reference | **Add** | §1 |
| 4.2.2 | Baseline Reconstruction and Efficiency per Scene | Retain, de-aggregate | §2 |
| 4.2.3 | Baseline Representation Characteristics | Rewrite | §9 |
| 4.2.4 | Baseline Medium Stability | **Add** | §5a |
| 4.3 | **Component 1: Deterministic Initialisation** | Rewrite | |
| 4.3.1 | Quantitative Comparison per Scene | Rewrite | §2 |
| 4.3.2 | Representation Size and Training Cost | Rewrite | §2, §12 |
| 4.3.3 | Effect on Medium Stability | **Add** | §5c |
| 4.3.4 | Geometry After Initialisation | Refine | §9 |
| 4.3.5 | Discussion | Refine | — |
| 4.4 | **Component 2: Spatial Reorganisation** | Rewrite | |
| 4.4.1 | Quantitative Comparison per Scene | Rewrite | §2 |
| 4.4.2 | Rendering Throughput and Representation Size | Rewrite | §2, §12 |
| 4.4.3 | Effect on Medium Stability | **Add** | §5a |
| 4.4.4 | Discussion | Refine | — |
| 4.5 | **Component 3: Attribute-Level Quantisation** | Rewrite | |
| 4.5.1 | Quantitative Comparison per Scene | Rewrite | §2 |
| 4.5.2 | Storage–Fidelity Relationship | Refine | §2 |
| 4.5.3 | Effect on the Restored Image | **Add** | §10 |
| 4.5.4 | Discussion | Refine | — |
| 4.6 | **Combined Configurations and Interactions** | **Add** | |
| 4.6.1 | Two-Way Interactions | **Add** | §3 |
| 4.6.2 | Three-Way Interaction | **Add** | §4 |
| 4.6.3 | Composition on Representation Size: the Budget Bound | **Add** | §3 |
| 4.6.4 | Operating Points Across Configurations | **Add** | §7 |
| 4.7 | **Coupling Between Simplification and the Medium Model** | **Add** | |
| 4.7.1 | Collapse Rates and Boundary Alignment | **Add** | §5a |
| 4.7.2 | Size Versus Discontinuity | **Add** | §5d |
| 4.7.3 | The Registered Explanation and Its Refutation | **Add** | §5b |
| 4.7.4 | Post-Hoc Characterisation of the Coupling | **Add** | §5 |
| 4.7.5 | The Re-Identification Burst | **Add** | §5e |
| 4.8 | **Detecting Failure: the Limits of Fidelity Metrics** | **Add** | |
| 4.8.1 | Collapsed Versus Intact Strata | **Add** | §8 |
| 4.8.2 | Restored-Image Consistency | **Add** | §10 |
| 4.9 | **Supplementary Contrast: Gradient Detachment** | **Add** | |
| 4.9.1 | Quantitative Comparison Against the Baseline | **Add** | §6 |
| 4.9.2 | Discussion | **Add** | §6 |
| 4.10 | **Replication Against the Archived Campaign** | **Add** | §11 |
| 4.11 | **Synthesis** | Rewrite | |
| 4.11.1 | Alignment with Research Objectives | Retain from old 4.6.4 | all |
| 4.11.2 | What the Campaign Establishes and What Remains Open | **Add** | all |
| 4.12 | **Limitations of the Study** | Retain, expand | |
| 4.12.1 | Experimental Limitations | Refine | §14 |
| 4.12.2 | Methodological Limitations | Refine | §14 |
| 4.12.3 | Unresolved and Undetermined by Design | **Add** | §0, §14 |

**Removed:** all scene-aggregated fidelity tables; the A1v2 density study;
old 4.6 cross-component discussion, whose successors are 4.6 and 4.11.

---

# CHAPTER V — CONCLUSIONS AND RECOMMENDATIONS  ·  11 pp (from 7)

| § | Title | Action | Content | Evidence |
|---|---|---|---|---|
| 5.1 | **Conclusions** | Replace | Organised by research question, not by mechanism | |
| 5.1.1 | The Mechanisms Transfer, at Scene-Specific Cost | Replace | Answers RQ1 | §2 |
| 5.1.2 | The Mechanisms Do Not Compose Additively | Replace | Answers RQ2 on the metrics that resolve. Supersedes the old ranking conclusion | §3, §4 |
| 5.1.3 | Population Reduction Perturbs Medium Identifiability | **Add** | Answers RQ3, *whether* | §5a |
| 5.1.4 | The Mechanism of That Coupling Remains Open | **Add** | Answers RQ3, *why*. Supersedes the old compactness–stability conclusion | §5b |
| 5.1.5 | Composed-Image Metrics Cannot Detect the Failure | **Add** | The methodological conclusion | §8, §10 |
| 5.1.6 | Integration Properties of the Composition | Refine | Answers RQ4 | CD |
| 5.1.7 | Overall Conclusion | Refine | States the open question rather than concluding past it | all |
| 5.2 | **Research Contributions** | Replace | Six, each traceable to a Chapter IV section | all |
| 5.3 | **Limitations** | **Add** as its own section | Consolidated from 4.12 | §14 |
| 5.4 | **Recommendations for Future Work** | Replace | | |
| 5.4.1 | Deconfounding the Size of the Cut | **Add** | Simplify at a removal fraction matched to the initialisation cells | §5 |
| 5.4.2 | Testing the Re-Identification Burst | **Add** | A simplification cell without the burst | §5e |
| 5.4.3 | Locating the Restoration Difference | **Add** | Per-depth-bin comparison of the two attribute states | §10 |
| 5.4.4 | Constraining the Quantiser | **Add** | A commitment term the straight-through estimator lacks | §10 |
| 5.4.5 | Multiple Operating Points per Mechanism | **Add** | To answer the rate–distortion question this design cannot | §7 |
| 5.4.6 | Repeat Count Required to Resolve Interactions | **Add** | Derived from the observed dispersion | §0 |
| 5.5 | **Closing Remarks** | **Add** | | — |

**Removed:** old 5.1.5 cross-mechanism interpretation, superseded by 5.1.2.

---

# Cross-chapter dependencies

Settle in this order; each row depends on the rows above it.

| Decision | Fixes | Blocks |
|---|---|---|
| Research questions RQ1–RQ4 | 1.3.1, 1.4 | Chapter IV heading order; all of 5.1 |
| Claim vocabulary and resolution rule | 3.6.5, 3.8.3 | Every verdict in Chapter IV |
| Cell labelling and repeat-versus-seed terminology | 3.6.1, 3.6.3 | Every table in Chapter IV |
| Metric conventions (pooled PSNR, LPIPS backbone, size container) | 3.7.1, 3.7.2 | Tables 4.2–4.14 |
| Collapse definition | 3.7.3 | 4.2.4, 4.3.3, 4.4.3, 4.7 |
| Framing (conservative or stronger) | 1.2, 1.6 | 5.2, 5.1.7 |

# Figure and table placement

| Asset | Chapter | Section |
|---|---|---|
| `figure-0-optimisation-loop` | III | 3.1.3 |
| `figure-1-pipeline` | III | 3.5.1 |
| `figure-2-schedule` | III | 3.6.6, referred back to from 4.7 |
| Table 2.1 synthesis (retained) | II | 2.7.3 |
| Tables 4.1–4.14 | IV | per `chapter-04-architecture.md` §2 |
