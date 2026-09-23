# Revised thesis outline — all five chapters

Gate 3 deliverable per `THESIS.md`: the full revised hierarchy, presented for
approval before any chapter is rewritten.

**Why this exists.** The approved draft (AoL Research Writing I, 153 pp.)
describes a study that was planned. The campaign that ran is a different
study: it has a reference control the draft does not mention, ten
configurations where the draft has four, three repeats where the draft has
one, an interaction analysis the draft could not perform, and a central
finding — a coupling between simplification and the learned medium model —
that the draft does not contain. The outline below realigns every chapter to
what was executed.

**Action vocabulary.** Retain · Refine · Reorganize · Replace · Remove · Add.

**Evidence keys.** §n refers to `analysis/campaign-2026-09/FINDINGS.md`;
PLAN refers to the pre-registered analysis plan beside it; CD refers to the
implementation-delta register.

---

## Summary of drift, by chapter

| Chapter | Existing | Principal drift | Severity |
|---|---|---|---|
| I Introduction | 1.1–1.5, 8 pp. | No research questions, no hypotheses, no contributions section; objectives phrased as proposing a method rather than characterising mechanisms; scope predates the executed design | High |
| II Literature Review | 2.1–2.6, 34 pp. | Source methods for the three mechanisms are under-covered; no coverage of factorial method, repeat uncertainty, or reference-controlled evaluation; the gap as stated is not the gap the campaign fills | High |
| III Methodology | 3.1–3.7, 27 pp. | Describes the intended implementation, not the executed one; no factorial, no reference control, no pre-registration, no diagnostics, no implementation deltas | **Highest** |
| IV Results | 4.1–4.7, 63 pp. | Scene-aggregated fidelity tables; four configurations; no interactions, no medium results, no reference comparison | High |
| V Conclusions | 5.1–5.3, 7 pp. | Ranks mechanisms from one operating point; conclusions derived against a baseline later shown defective | High |

The methodology chapter is the highest-severity item because every other
chapter's validity depends on it describing what actually ran.

---

# CHAPTER I — INTRODUCTION

Target: 9–11 pp. (from 8).

| § | Title | Action | Must contain | Must not |
|---|---|---|---|---|
| 1.1 | Background | Refine | Retain the radiance-field narrative. Add the two facts the campaign established that motivate the study: most of the baseline's representation is never rendered (§9), and the physical medium model is fragile under population reduction (§5) | Claim physical accuracy; claim no underwater pruning work exists |
| 1.2 | Problem Statement | Refine | State the problem as *uncharacterised interaction*: efficiency mechanisms are validated in isolation on terrestrial scenes, and their composition on a physically grounded underwater estimator is unmeasured | Frame the problem as absence of an efficient method |
| 1.3 | Research Objective | Refine | Objectives of characterisation, not invention: measure each mechanism's effect, measure composition, test whether reduction perturbs medium identifiability | Promise a new compression algorithm |
| 1.3.1 | Research Questions | **Add** | Four questions, matching the executed design and answerable from Chapter IV | Questions the design cannot answer |
| 1.3.2 | Hypotheses | **Add** | The pre-registered hypotheses and the falsification condition, stated as registered before the campaign (PLAN) | Post-hoc hypotheses presented as prior |
| 1.4 | Research Benefits | Refine | Benefit to practitioners choosing mechanisms; benefit as a reusable evaluation protocol | Operational or vehicle-deployment benefit |
| 1.5 | Scope and Limitations | Replace | Four scenes, three repeats, one simplification budget, one codebook size, one accelerator type, offline evaluation. Distinguish medium *stability* from medium *accuracy* | Deployment, real-time, AUV language |
| 1.6 | Contributions | **Add** | Six contributions at evidence level, mirroring Chapter V §5.2 | Any contribution not traceable to Chapter IV |

**Note on the research questions.** They must be fixed before Chapter IV's
headings are finalised, because Chapter IV answers them in order. Proposed
wording is in the appendix to this outline.

---

# CHAPTER II — LITERATURE REVIEW

Target: 36–40 pp. (from 34).

| § | Title | Action | Notes |
|---|---|---|---|
| 2.1 | Fundamentals of 3D Reconstruction and Scene Representation | Retain | Citation check only |
| 2.2 | Neural Radiance Fields and Differentiable Rendering | Retain | Citation check only |
| 2.3 | Explicit Radiance-Field Representations and 3D Gaussian Splatting | Refine | Add the densification mechanism explicitly — Chapter IV's results turn on it |
| 2.4 | Physical Image Formation in Underwater Environments | Refine | Add the identifiability question: what the medium parameters are fitted against, and why that fit is not unique |
| 2.5 | Efficiency Considerations in Radiance-Field Modelling | **Reorganize into 2.5.1–2.5.4** | One subsection per mechanism family, each ending with what the source method established and on what data | |
| 2.5.1 | Initialization and Densification | Add | The dense-correspondence initialisation lineage |
| 2.5.2 | Spatial Simplification and Pruning | Add | The importance-weighted simplification lineage and its budget formulation |
| 2.5.3 | Attribute Quantization and Storage Compression | Add | Vector quantization of primitive attributes; the straight-through estimator and what it does not constrain |
| 2.5.4 | Transfer Risk Across Domains | **Add** | Each source method was validated on terrestrial scenes without a medium model; this is the transfer the thesis tests |
| 2.6 | Literature Review | **Replace with 2.6.1–2.6.3** | The current catch-all becomes a structured synthesis |
| 2.6.1 | Per-paper analysis | Add | Paragraph form per central paper: problem, method, evaluation, dataset, metrics, results, limitations, relevance. **Blocked** — the six breakdowns do not yet exist (§13) |
| 2.6.2 | Synthesis table and trends | Refine | Retain the existing extraction table; add the evaluation-design column the gap argument needs |
| 2.6.3 | Research gap | **Replace** | The gap the campaign fills: composition of efficiency mechanisms on a physically grounded underwater estimator has not been measured, no prior work establishes baseline equivalence before measuring reductions, and no prior work reports repeat dispersion |
| 2.7 | Methodological Foundations | **Add** | Factorial design and interaction estimation; repeated-run uncertainty; equivalence testing against a margin; pre-registration. These justify Chapter III and are currently absent |

**Blocker.** 2.6.1 cannot be completed from the material presently in the
repository. It is the one outstanding item in the whole outline that needs
new reading rather than new writing.

---

# CHAPTER III — RESEARCH METHODOLOGY

Target: 38–44 pp. (from 27). This is the chapter that must change most.

| § | Title | Action | Must now contain |
|---|---|---|---|
| 3.1 | Conceptual Framework | Refine | The framework as executed: a baseline estimator, three mechanisms at three insertion points, and a medium model coupled to all of them through the rendered depth |
| 3.2 | Research Stages | Refine | The executed stage sequence, including the reference-control stage that precedes the factorial |
| 3.3 | SeaThru-NeRF Dataset | Retain | Four scenes, 88 images, held-out partition; add the per-scene view counts and the camera-pairing characteristic that Chapter IV's anomalous scene turns on |
| 3.4 | Data Preprocessing | Refine | Add the undistortion decision and the hold-out rule as executed (every eighth frame by index) |
| 3.5 | Proposed Method | **Reorganize** | Rename to *Efficiency Mechanisms Under Test*. The thesis does not propose a single method; it composes three and measures them |
| 3.5.1 | Overview and insertion points | Refine | Use the pipeline figure; state that the three act at disjoint stages and share no code |
| 3.5.2 | M1 Deterministic Initialization | Refine | As executed, including the disabled densification and the schedule change |
| 3.5.3 | M2 Spatial Reorganization | Refine | The 200 000-primitive budget, both events, and the medium-only burst that follows each |
| 3.5.4 | M3 Attribute-Level Quantization | Refine | Codebooks, the straight-through estimator, and the iteration from which it is active |
| 3.5.5 | Mechanism D: Gradient Detachment | **Add** | Why it is a supplementary contrast and not a fourth factor: it is provably inert wherever M1 is present |
| 3.5.6 | Implementation Delta Register | **Add** | The integration decisions the source methods do not specify, each with its justification. Currently undocumented in the thesis |
| 3.6 | Experimental Design | **Replace** | |
| 3.6.1 | Factorial structure | Add | The $2^3$ design, cell labelling A0–A7, and what each contrast estimates |
| 3.6.2 | Reference control | **Add** | The unmodified upstream implementation, its role, and the equivalence margin fixed in advance |
| 3.6.3 | Scene blocking and repeats | Add | Four scenes × three repeats; why results are reported per scene |
| 3.6.4 | Pre-registration | **Add** | The analysis plan, its hypotheses, and the falsification condition, all committed before results were examined |
| 3.6.5 | Resolution and claim vocabulary | **Add** | The two-standard-error rule; the standard-error arithmetic for interactions; the claim-status labels used throughout Chapter IV |
| 3.6.6 | Training procedure and schedule | Refine | Iterations, the medium-model activation point, the intervention schedule, and effective optimizer steps |
| 3.6.7 | Execution environment and reproducibility | **Add** | Accelerator, run ledger, manifests, storage policy, and the provenance limitation |
| 3.7 | Evaluation Metrics | **Reorganize** | |
| 3.7.1 | Reconstruction fidelity | Refine | Pooled PSNR convention stated explicitly, SSIM, LPIPS with its backbone |
| 3.7.2 | Representation and computational cost | Refine | Primitive count, stored bytes with the container defined, render rate protocol, peak render memory |
| 3.7.3 | Medium-model diagnostics | **Add** | The collapse definition; the cross-frame depth-range sweep; what each instrument can and cannot detect |
| 3.7.4 | Geometric and restoration diagnostics | **Add** | Spatial extent; restored-image self-consistency, with its consistency-not-accuracy caveat |
| 3.7.5 | Scope of the metrics | Refine | Which metrics exist at three repeats and which at one |

**Requirements this chapter owes Chapter IV.** Cell labelling; repeat versus
seed; the resolution rule; the pooled-PSNR convention; the collapse
definition; the equivalence margin; the budget and event schedule; the
medium-only burst; effective optimizer steps; the depth-range sweep; the
restored-image check; the storage policy that leaves geometry and restoration
results at one repeat per scene.

---

# CHAPTER IV — RESULTS AND DISCUSSION

Target: 55–65 pp. Detailed architecture in `chapter-04-architecture.md`
(Revision 2); §4.1 and §4.2 are drafted in `chapter-04-draft.md`.

| § | Title | Action | Source |
|---|---|---|---|
| 4.1 | Experimental Overview | Rewrite | §0, ledger |
| 4.2 | Baseline Validation | Reframe — now opens with equivalence to the reference | §1, §2, §9, §5a |
| 4.3 | Component 1: Deterministic Initialization | Rewrite; remove the A1v2 density study, not in this campaign | §2, §12, §5c |
| 4.4 | Component 2: Spatial Reorganization | Rewrite; gains the medium-stability result | §2, §12, §5a |
| 4.5 | Component 3: Attribute-Level Quantization | Rewrite; gains the restored-image result | §2, §10 |
| 4.6 | Combined Configurations and Interactions | **Add** | §3, §4, §7 |
| 4.7 | Coupling Between Simplification and the Medium Model | **Add** — the chapter's centre | §5 |
| 4.8 | Detecting Failure: the Limits of Fidelity Metrics | **Add** | §8, §10 |
| 4.9 | Supplementary Contrast: Gradient Detachment | **Add** | §6 |
| 4.10 | Replication Against the Archived Campaign | **Add** | §11 |
| 4.11 | Synthesis and Alignment with Research Objectives | Retain from old 4.6.4, rewrite | all |
| 4.12 | Limitations of the Study | Retain, expand | §14 |

**Removed from the existing chapter:** all scene-aggregated fidelity tables
(old 4.3, 4.5, 4.8, 4.10); the A1v2 sensitivity analysis; old 4.6's
cross-component discussion, whose successor is 4.6 and 4.11.

---

# CHAPTER V — CONCLUSIONS AND RECOMMENDATIONS

Target: 9–12 pp. (from 7). Construction rules in `THESIS.md` §17.

| § | Title | Action | Notes |
|---|---|---|---|
| 5.1 | Conclusions | **Replace** | Reorganised by research question, not by mechanism |
| 5.1.1 | The mechanisms transfer, at scene-specific cost | Replace | Answers RQ1. Supersedes old 5.1.1 |
| 5.1.2 | The mechanisms do not compose additively | Replace | Answers RQ2 on the metrics that resolve. **Supersedes old 5.1.2**, which ranked one mechanism as the most balanced tradeoff — a ranking one operating point cannot support |
| 5.1.3 | Population reduction perturbs medium identifiability | Add | Answers RQ3's *whether*: reproducible, boundary-aligned, seed-conditioned, absent from baseline and reference |
| 5.1.4 | The mechanism of that coupling is open | Add | Answers RQ3's *why*: the registered explanation was refuted. **Supersedes old 5.1.4**, whose compactness-stability boundary was derived against a baseline later shown defective |
| 5.1.5 | Composed-image metrics cannot detect the failure | Add | The methodological conclusion; no equivalent in the existing chapter |
| 5.1.6 | Overall conclusion | Refine | Must state the open question, not conclude past it |
| 5.2 | Research Contributions | Replace | Six contributions at evidence level; each traceable to a Chapter IV section |
| 5.3 | Limitations | **Add** as its own section | Currently distributed; consolidate |
| 5.4 | Recommendations for Future Work | Replace | Six items, each answering a question this campaign left open — deconfounding the cut, testing the burst, locating the restoration damage, constraining the quantizer, multiple operating points, and the repeat count needed to resolve interactions |

**Removed:** old 5.1.5 cross-mechanism interpretation, which predates the
interaction evidence and is replaced by 5.1.2.

---

# Appendix — proposed research questions

These fix the ordering of Chapter IV's headings and Chapter V's conclusions,
so they are the first thing to settle.

**RQ1.** To what extent does each efficiency mechanism reduce its target cost,
and at what cost to reconstruction fidelity, when transferred to a physically
grounded underwater estimator?
*Answerable.* §2. Resolved on every scene for every target cost.

**RQ2.** How do the mechanisms compose when applied together?
*Partially answerable.* §3, §4. Resolved on perceptual similarity and
primitive count; undetermined on PSNR by construction.

**RQ3.** Does population reduction perturb the identifiability of the learned
medium model, and if so, by what mechanism?
*Split answer.* §5. The first half is established; the second is open after
the registered explanation was refuted.

**RQ4.** What integration properties emerge from composing these mechanisms
that the source methods do not specify?
*Answerable.* The implementation-delta register, CD items.

---

# Recommended order of work

1. **Settle the research questions** (appendix above). Everything downstream
   keys to them.
2. **Chapter III**, highest severity and the largest gap between document and
   reality. Chapter IV cannot be finished until Chapter III defines its terms.
3. **Chapter II**, excluding the blocked per-paper subsection.
4. **Chapter I**, which derives from II and III.
5. **Chapter IV**, resuming from §4.3.
6. **Chapter V**.

Chapter IV §4.1 and §4.2 are already drafted and will need only terminology
alignment once Chapter III is settled.
