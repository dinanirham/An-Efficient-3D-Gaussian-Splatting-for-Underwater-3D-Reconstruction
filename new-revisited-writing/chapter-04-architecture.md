# Chapter 4 — Results and Analysis: architecture for approval

Gate 5 package, per `THESIS.md` §16. This is not the chapter. It is the
section architecture, the table and figure inventory, and the list of results
the chapter cannot omit, presented for approval before any prose is written.

Evidence base: `analysis/campaign-2026-09/FINDINGS.md` (the analysis) and
`PLAN.md` beside it (what was registered in advance). Every number below is
cited to a section of the analysis and is not re-derived here.

---

## 0. Precondition status — read this first

`THESIS.md` §16.1 lists four preconditions. Three are unmet:

| Precondition | Status | Consequence if we proceed |
|---|---|---|
| Phase 4 completion and integrity checks pass | **Met in substance.** The campaign is complete and the analysis validated it: 120/120 runs, one GPU type, effective-step accounting verified per cell. | — |
| Phase 5 corrected findings ledger exists | **Not done.** `FINDINGS.md` has not been through the §12 interpretation audit. | I have written the analysis, so I am auditing my own work. The architecture below assigns a claim status per section, which is that audit in practice — but it is not independent. |
| Phase 7 framing approved | **Not done.** §14 offers a conservative and a stronger framing; neither has been chosen. | Chapter 4 reports results, so the framing changes its *emphasis and ordering*, not its numbers. Low risk to draft now, but §4.15 and every "contribution" phrasing must wait. |
| Chapters 2, 1, 3 stable | **Not done.** None has been revised. | This is the real exposure. Chapter 4 must use terms Chapter 3 defines — cell names, metric conventions, the collapse definition, the resolution rule. Drafting first means Chapter 3 later has to match Chapter 4's vocabulary rather than the reverse. |

**Recommendation.** Draft Chapter 4 now anyway, for one reason: it is the only
chapter whose content is already fixed by evidence, and writing it surfaces
exactly which definitions Chapter 3 owes it. Treat the vocabulary it uses as a
*requirements list for Chapter 3*, not as settled prose. I will maintain that
list as I draft.

If you would rather hold to the stated order, say so and I will stop here and
start with Chapter 2.

---

## 1. Section architecture

Fifteen sections, one per analysis section, in the analysis's own order so a
reader can move between the two documents. "Status" is the claim-discipline
label from `THESIS.md` §18.

### 4.1 The campaign as executed
**Source** §0 + `run_ledger.json`. **Status** Factual.
Ten cells × four scenes × three repeats = 120 runs, all complete; one GPU type
throughout; 107 GPU-hours over 15–21 September 2026; four runs needed a retry
after a disconnect and completed on it. Effective optimizer steps 43 000 per
non-simplification cell and 43 400 per simplification cell — the schedule's
own accounting plus two medium-only bursts of 200.
**Must state:** the commit column is empty in all 120 rows because the
collector read a key the manifest never wrote; the defect is fixed and the
column populates on the next collection, so the one-code-version claim
currently rests on the ledger's span and the worker log, not on the results
table.
**Must not:** present provenance as complete.

### 4.2 Noise floor and what this design can resolve
**Source** §0. **Status** Factual, and the basis of every later verdict.
Per-scene baseline dispersion over three repeats; the standard-error
arithmetic for main effects, two-way and three-way contrasts; the resulting
resolution threshold per metric per scene.
**Must state:** the smallest PSNR interaction this design can resolve exceeds
the largest PSNR main effect it measured. This is a property of the design,
known before the data, and it is why every PSNR interaction in 4.5 is marked
`UNDETERMINED`. Also: count dispersion widened on two scenes relative to the
archived campaign, which widens the floor for every count contrast there.
**Must not:** present the widening as a result.

### 4.3 Baseline validation against the unmodified reference
**Source** §1, `check_margin.txt`. **Status** Supported within a pre-specified margin.
Vanilla SeaSplat trained and measured on this harness, twelve runs, compared
with A0 as scene means over repeats against a margin fixed in the
configuration before the reference existed. Within margin on all four scenes;
largest fidelity gaps well inside A0's own dispersion.
**Must state:** the comparison is of scene means, not seed by seed, because
the upstream checkout's seed does not reach its GPU draws; and neither A0 nor
the reference lost an attenuation channel in any of 24 runs, which is the
precondition for attributing any later collapse to a mechanism.
**Must not:** say A0 "reproduces" SeaSplat.

### 4.4 Main effects
**Source** §2. **Status** Pre-registered (H1), supported.
Each mechanism against A0, per scene, on its own target cost and on fidelity,
reported in both directions — from the baseline up, and from the full
combination down.
**Must state:** each mechanism moves its own target cost beyond repeat
dispersion on every scene; the direction disagreement on count between the two
inference directions is itself the interaction, formalised in 4.5; and the one
scene on which every mechanism costs perceptual quality, named and carried
forward.
**Must not:** average fidelity across scenes anywhere in this section.

### 4.5 Interactions
**Source** §3, §4. **Status** Pre-registered, mixed.
Two-way and three-way terms, additive on LPIPS and log-multiplicative on count.
**Must state, each with its registered status:**
H5 held in its sub-additive form — the two reductions do not multiply, because
the budget caps whichever cell reaches it first. The accompanying LPIPS
interaction was *not* registered and is favourable; it is reported as observed
with its interpretation labelled post-hoc. H3 held on three scenes — a smaller
population is more sensitive to lossy attribute compression. The registered
"approximately additive" prediction for the initialization–quantization pair
**failed**: it resolves in the direction the falsification clause named, and
its sign is inconsistent across scenes. Three-way terms are unresolved except
on one scene and one metric, and are not interpreted.
**Must not:** report any PSNR interaction as a finding.

### 4.6 The medium model under simplification
**Source** §5a, §5c, §5d, §5e. **Status** Pre-registered.
Collapse counts per cell per scene; boundary alignment; the initialization
cells; final size versus discontinuity; the re-identification burst.
**Must state:** the baseline and the reference never collapse; the
simplification cells without dense initialization collapse at a
seed-conditioned rate; every one of those runs puts its largest attenuation
drop at the first simplification boundary; the lost channel is the same one in
every case; the cells with dense initialization finish *below* the
simplification-only cells on count and never collapse, which deconfounds size
from discontinuity; and the burst carries identical depth statistics to the
post-cut state on every run, as designed.
**Must not:** claim the initialization cells are protected *because* of the
registered mechanism — that is 4.7.

### 4.7 The registered explanation, and its refutation
**Source** §5b. **Status** Contradicted. Withdrawn, not qualified.
The dispersion account as written before the campaign; the instrument built to
test it; the rank test; the counterexample from the initialization cells.
**Must state:** the falsification condition was written in the plan before the
data existed, the test was run at the first opportunity, and it failed. The
account is withdrawn. Everything downstream that rested on it is rewritten as
description.
**Must not:** retain the account in weakened form, or bury this in a
limitations paragraph.

### 4.8 What the same diagnostics show instead
**Source** §5, closing. **Status** Post-hoc throughout.
The cut moves no medium parameter; the medium moves during the medium-only
steps that follow; the relationship with the fraction removed; the absence of
any pre-cut predictor of which repeat crosses zero; the confound in the
initialization cells' three simultaneous protections.
**Must state:** every paragraph carries its post-hoc label; the description is
not promoted to an explanation; and the question of *why* a large cut moves
the medium is open at the end of the campaign.
**Must not:** use a causal verb.

### 4.9 Mechanism D, a supplementary contrast
**Source** §6. **Status** Pre-registered; both halves held.
A0D against A0 on count, wall-clock, frame rate, peak render memory, PSNR,
LPIPS and collapse.
**Must state:** the prediction — count resolves, PSNR does not — was written
before the cell ran and both halves held; LPIPS resolves worse on all four
scenes and is reported as the cost; no A0D run lost a channel; and the earlier
figure from a single run against a defective baseline is retired.
**Must not:** difference A0D with the factorial cells.

### 4.10 Operating points
**Source** §7. **Status** Descriptive only.
Non-dominated cells per scene on count × perceptual quality, bytes ×
perceptual quality, and count × PSNR.
**Must state:** one operating point per mechanism, so this is a description of
nine cells and not a curve; the PSNR fronts are drawn on a metric that does
not resolve the mechanisms' costs and are shown for completeness only; and
quantization costs frame rate once the population is small, which the
from-below comparison could not resolve.
**Must not:** call this a rate–distortion result, or rank the mechanisms from it.

### 4.11 What the fidelity metrics cannot see
**Source** §8, §10. **Status** Confirmatory (§8), exploratory (§10).
The collapsed-versus-intact stratification within cell and scene; the
restored-image comparison between the two attribute states of one model.
**Must state:** a physically meaningless medium renders held-out views as well
as a plausible one, because the medium-free radiance absorbs whatever the
medium model does not; the restored image moves by an order of magnitude more
than the composed image under the same quantization, and the two are
uncorrelated; the codebook-state figure reproduces each run's evaluated PSNR,
which is the check's own sanity check; and this is consistency, not accuracy.
**Must state, as process:** the first reading of this instrument was wrong —
recorded as drift — and the check that corrected it was added and run.
**Must not:** present the restored-image numbers as restoration quality.

### 4.12 Geometry
**Source** §9. **Status** Exploratory, one repeat per cell.
Visible fraction; bounding-box inflation; occupancy.
**Must state:** most of the baseline's primitives are never rendered and the
unmodified reference carries the same halo, so it is a property of the
baseline optimizer and not of anything this work did; the mechanisms' count
reductions should be read against the visible population; and the largest
detached-cluster inflation in the campaign appears on one of the reference's
own repeats.
**Must not:** use geometry as a proxy for medium health.

### 4.13 Replication against the archived campaign
**Source** §11. **Status** Mixed; one downgrade.
The four shared cells, per scene, on fidelity and count.
**Must state:** perceptual quality replicates on every comparison and dense
initialization's count replicates to three figures; four PSNR comparisons do
not replicate; one mechanism's PSNR effect on one scene reverses sign, is
downgraded to unresolved across campaigns, and the scene finding rests on the
metric that replicates; and the archived campaign's own provenance includes at
least one run trained from an uncommitted tree.
**Must not:** attribute the discrepancy to a named code change.

### 4.14 Computational cost
**Source** §12. **Status** Factual.
Wall-clock, frame rate and peak render memory per cell per scene; effective
optimizer steps; the sub-linear relationship between count reduction and frame
rate, with a scene-dependent exponent.
**Must state:** the mechanisms change what an iteration costs, not how many
there are; and the instrumentation's own cost is inside every wall-clock
figure reported.

### 4.15 Threats to validity and what cannot be concluded
**Source** §14. **Status** Explicit.
Every unresolved, undetermined, confounded, unmeasured and single-repeat item,
each with its consequence. Ordered by how much it constrains the thesis.
**Must not:** be written before 4.1–4.14 are stable.

---

## 2. Table inventory

One table per contrast family. Every table carries per-scene rows, the effect
with its resolution marker, and a caption naming its analysis section.

| # | Table | Source |
|---|---|---|
| 4.1 | Campaign completion, hardware, and provenance status | §0, ledger |
| 4.2 | Per-scene baseline dispersion and resolution thresholds | §0 |
| 4.3 | Reference versus baseline against the pre-registered margin | §1 |
| 4.4a–c | Main effects, one table per mechanism | §2 |
| 4.5a | Two-way interaction terms on perceptual quality and count | §3 |
| 4.5b | Three-way terms | §4 |
| 4.6 | Collapse counts per cell per scene | §5a |
| 4.7 | Dispersion-ratio strata and the rank test | §5b |
| 4.8 | Cut size, entering medium state, post-burst medium state | §5 |
| 4.9 | A0D against A0 across all measured axes | §6 |
| 4.10 | Non-dominated cells per scene | §7 |
| 4.11a | Collapsed versus intact fidelity, in units of baseline dispersion | §8 |
| 4.11b | Restored-image versus composed-image comparison | §10 |
| 4.12 | Visible fraction and inflation, seed 0 | §9 |
| 4.13 | Cross-campaign comparison, four shared cells | §11 |
| 4.14 | Cost per cell per scene | §12 |

## 3. Figure inventory

Exported files are in `figures/` as `.svg` and `.png`. **Figures 0 and 1
belong to Chapter 3** — they describe the method, not the results. Chapter 4
references them and does not repeat them.

| Figure | File | Chapter | Role |
|---|---|---|---|
| Optimisation loop | `figure-0-optimisation-loop` | 3 | Where each mechanism inserts |
| Detailed pipeline | `figure-1-pipeline` | 3 | The executed pipeline by phase |
| Training schedule | `figure-2-schedule` | **decide — see D3** | Carries 4.6 and 4.8 visually |

A per-scene effect plot for the main effects is worth adding if it can be
drawn without pooling scenes; otherwise Table 4.4 carries it.

## 4. Negative results the chapter is not complete without

`THESIS.md` §16.7. Each appears in the body, in its own right:

1. The registered dispersion explanation failed its pre-written test; the
   account is withdrawn.
2. The re-identification burst — this work's own remedy — is the interval in
   which the medium falls.
3. The restored-image instrument's first reading was wrong; the correcting
   check was added and run.
4. One mechanism's effect on one scene reverses sign across campaigns and is
   downgraded.
5. The scene on which every mechanism costs perceptual quality is identified
   and not explained away.
6. Most of the baseline's primitives are never rendered, reference included.
7. Nothing measured before a cut predicts which repeat loses a channel.

---

## 5. Decisions I need from you

**D1 — Research-question numbering and wording.** Chapter 4's section
headings should answer the questions in Chapter 1's numbering. Phase 7 framing
is not approved, so I will draft with neutral headings and map them to RQ
numbers once Chapter 1 settles. Confirm, or give me the numbering now.

**D2 — Where the schedule figure lives.** It is methodological in content but
does most of its work in 4.6 and 4.8. Options: place in Chapter 3 and refer
back; place in Chapter 4; or place in Chapter 3 and repeat a simplified
version in 4.6. My recommendation: Chapter 3, referred back to, and no repeat.

**D3 — Scene display names.** The data directories carry
`JapaneseGradens-RedSea` (a misspelling of "Gardens") and `IUI3-RedSea`. The
thesis should use corrected, human-readable names with a footnote mapping them
to the directory names, so that anyone reading the artifacts can follow. I
will use "Japanese Gardens", "IUI3 Red Sea", "Curaçao", "Panama" unless you
prefer otherwise.

**D4 — Related work.** The analysis's §13 is a blocker for Chapter 2, not a
result. It is excluded from Chapter 4.

**D5 — Drafting order.** I propose 4.2 → 4.3 → 4.4 → 4.5 → 4.6 → 4.7 → 4.8,
then the remainder, then 4.1 and 4.15 last, because the first and last
sections depend on what the middle ones end up claiming.

---

## 6. Vocabulary this chapter will require Chapter 3 to define

Maintained as I draft, so Chapter 3's revision has a requirements list rather
than a guess: cell names and the factorial labelling; repeat versus seed; the
resolution rule and the standard-error arithmetic; the pooled-PSNR convention;
the collapse definition; the equivalence margin and its pre-registration; the
simplification budget and event schedule; the medium-only burst; effective
optimizer steps; the depth-range sweep; the restored-image consistency check;
the storage policy that leaves geometry and restored-image results at one
repeat per scene.

---

# Revision 2 — reconciliation with the existing Chapter IV

## R2.1 What exists

`previous-writings/draft-thesis-to-be-revisited/…AoL Research Writing I.pdf`
carries an approved Chapter IV at pages 70–132 and Chapter V at 133–139:

| Existing section | Subsections | Verdict against the 2026-09 campaign |
|---|---|---|
| 4.1 Experimental Overview | scope, criteria, reporting strategy | **Retain, rewrite.** The skeleton is right; the content describes a smaller campaign. |
| 4.2 Baseline Performance Analysis | quantitative, qualitative, underwater behaviour, limitations | **Retain, reframe.** Must now open with equivalence to the unmodified reference, which did not exist when it was written. |
| 4.3 Component 1: Deterministic Initialization | A0 vs A1, A1v2 sensitivity, qualitative, stability | **Retain, rewrite.** Remove the A1v2 density sensitivity: that cell is not in this campaign. |
| 4.4 Component 2: Spatial Reorganization | A0 vs A2, distribution, degradation regions, efficiency | **Retain, rewrite.** Gains the medium-stability result, which is the campaign's centre. |
| 4.5 Component 3: Attribute-Level Quantization | A0 vs A3, tradeoff, artifacts, robustness | **Retain, rewrite.** Gains the restored-image result. |
| 4.6 Cross-Component Comparative Discussion | tradeoffs, efficiency-fidelity, geometry-optics, objective alignment | **Replace.** Its successor is the interaction analysis, which the earlier campaign could not run. |
| 4.7 Limitation of the Study | experimental, methodological, future integration | **Retain, expand.** "Future integration opportunities" moves to Chapter 5. |

Three structural defects in the existing chapter, each now prohibited:

1. **Aggregate fidelity tables.** Tables 4.3, 4.5, 4.8 and 4.10 report metrics
   averaged across scenes. Scene difficulty spans about 7 dB, so a
   scene-averaged fidelity figure describes no scene in the corpus.
2. **No reference control, no interactions, no medium-collapse results.** The
   campaign those tables report could not produce them.
3. **Ranking from one operating point.** Chapter V's 5.1.2 concludes that one
   mechanism "provides the most balanced efficiency-fidelity tradeoff". One
   budget and one codebook size cannot support a ranking.

## R2.2 Revised architecture

The author's component-wise organisation is preserved. Sections 4.6 to 4.10
are new because the evidence is new.

| § | Title | Source | Action |
|---|---|---|---|
| 4.1 | Experimental Overview | §0, ledger | Rewrite |
| 4.1.1 | Scope of the Completed Campaign | §0 | Rewrite |
| 4.1.2 | Evaluation Criteria and Reporting Conventions | §0 | **Add** — per scene, two standard errors, undetermined-by-construction, registered versus post-hoc |
| 4.1.3 | Repeat Dispersion as the Measurement Baseline | §0 | **Add** |
| 4.1.4 | Provenance and Experimental Integrity | §0 | **Add** |
| 4.2 | Baseline Validation | §1, §2, §9, §5a | Reframe |
| 4.2.1 | Equivalence to the Unmodified Reference | §1 | **Add** |
| 4.2.2 | Baseline Reconstruction and Efficiency per Scene | §2 | Retain, de-aggregate |
| 4.2.3 | Baseline Representation Characteristics | §9 | Rewrite |
| 4.2.4 | Baseline Medium Stability | §5a | **Add** |
| 4.3 | Component 1: Deterministic Initialization | §2, §12, §5c | Rewrite |
| 4.4 | Component 2: Spatial Reorganization | §2, §12, §5a | Rewrite |
| 4.5 | Component 3: Attribute-Level Quantization | §2, §10 | Rewrite |
| 4.6 | Combined Configurations and Interactions | §3, §4, §7 | **Add** |
| 4.7 | Coupling Between Simplification and the Medium Model | §5 | **Add** — the chapter's centre |
| 4.8 | Detecting Failure: the Limits of Fidelity Metrics | §8, §10 | **Add** |
| 4.9 | Supplementary Contrast: Gradient Detachment | §6 | **Add** |
| 4.10 | Replication Against the Archived Campaign | §11 | **Add** |
| 4.11 | Synthesis and Alignment with Research Objectives | all | Retain from old 4.6.4, rewrite |
| 4.12 | Limitations of the Study | §14 | Retain, expand |

The fifteen analysis sections map onto these without loss; the mapping is in
the draft's section headers.

## R2.3 Consequences for Chapter V

The existing Chapter V concludes per component and ranks them. Three of its six
conclusion subsections do not survive:

* 5.1.2, ranking one mechanism as the most balanced tradeoff — prohibited from
  one operating point.
* 5.1.4, on a compactness-stability boundary — derived against a baseline later
  shown defective.
* 5.1.5, cross-mechanism interpretation — predates the interaction evidence.

Chapter V is rebuilt under `THESIS.md` §17 once Chapter IV is stable.
