# Chapter-by-Chapter Surgical Revision Plan

**Gate 3 deliverable.** Section-level actions against the existing 153-page manuscript.
Sections are the manuscript's own, from its table of contents.

Actions: *Retain* · *Retain with citation correction* · *Refine* · *Expand* · *Reorganize* ·
*Merge* · *Move* · *Replace* · *Remove* · *Defer*.

Revision order follows the brief's Gate 4: **Ch. 2 → Ch. 1 → Ch. 3 → Ch. 4 → Ch. 5.**

---

## Chapter II — Literature Review *(revise first)*

| § | Current role | Diagnosis | Action | Revised role | Evidence | Reviewer | Pri |
|---|---|---|---|---|---|---|---|
| 2.1 Fundamentals of 3D Reconstruction | Substrate | Sound but assumes the reader arrives informed | **Expand** | Entry point for a non-specialist — the reviewers' single most repeated complaint | `colmap`, `gaussian-splatting` breakdowns | R1.1 | **P1** |
| 2.2 NeRF and Differentiable Rendering | Substrate | Adequate | Retain w/ citation correction | Unchanged | `nerf`, `seathru_NeRF` | R1.1 | P3 |
| 2.3 Explicit Representations and 3DGS | Substrate | Adequate | **Refine** | Must introduce densification explicitly — it is where two of this thesis's findings live | `gaussian-splatting` §5 | R2.2 | **P1** |
| 2.4 Underwater Image Formation | Domain | Adequate | Retain w/ citation correction | Unchanged | `seathru_NeRF`, `seasplat` | — | P3 |
| 2.5 Efficiency Considerations | The gap | **Omits whole families** — D-8/R3.1, the single most concrete rejection reason | **Expand substantially** | A taxonomy of efficiency families: initialization · population reduction · attribute quantization · **rate–distortion optimization** · **entropy coding** · **structured representations** · **adaptive attribute pruning**; state which are evaluated and why | ⚠️ **6 breakdowns missing** — see `06-…` | **R3.1** | **P0** |
| 2.6 Literature Review (table) | Synthesis | Table exists; the *gap derivation* does not follow from it | **Reorganize** | Must logically generate Ch. 1's gap and Ch. 3's design | `01-taxonomy.md` §4 | R1.2, R3.1 | **P1** |
| — | *(new)* | No positioning of underwater-specific efficiency work | **Add §2.7** | WaterSplatting, Aquatic-GS, Gaussian Splashing, TUGS — prevents the unverified "no underwater compression exists" claim (D.3) | ⚠️ missing | R3.1, D.3 | **P0** |

**Chapter 2 is the highest-priority chapter and the one most blocked on missing work.**

---

## Chapter I — Introduction *(revise second)*

| § | Current role | Diagnosis | Action | Revised role | Evidence | Reviewer | Pri |
|---|---|---|---|---|---|---|---|
| 1.1 Background | Motivation | Opens too close to the subfield | **Expand** | Reach a general graphics reader by paragraph three | Ch. 2 | R1.1, R1.2 | **P1** |
| 1.2 Problem Statement | Gap | Frames the problem as *"reduce cost"* — a method framing | **Replace** | Frame as *"do these mechanisms transfer, and what governs whether they do"* | `04-repositioning.md` §4.5 | R2.1, R3.7 | **P0** |
| 1.3 Research Objective | Objectives | Follows the old framing | **Replace** | RQ1–RQ4 (RQ5 if Framing B) | §4.5 | R3.3 | **P0** |
| 1.4 Research Benefits | Impact | Leans on AUV deployment | **Refine** | Remove deployment claims (D-10); keep methodological benefit | — | R1 desc., D.1 | **P1** |
| 1.5 Scope and Limitations | Boundaries | Present and honest — R4 credited it | **Expand** | Add: single formulation, one operating point per mechanism, per-scene dispersion heterogeneity | D-5, D-9 | R3.5, R4.3 | P2 |
| — | *(new)* | Contributions never stated as a list | **Add §1.6** | The five contributions, methodological first | §4.5 | R2.1, meta M.1 | **P0** |

**Title change required.** *An Efficient 3D Gaussian Splatting…* → a tradeoff/transfer
framing consistent with §1.2.

---

## Chapter III — Research Methodology *(revise third)*

The brief: *"The chapter must describe the implementation that produced the results, not an
obsolete planned method."* The current chapter describes the **prior** implementation.

| § | Current role | Diagnosis | Action | Revised role | Evidence | Reviewer | Pri |
|---|---|---|---|---|---|---|---|
| 3.1 Conceptual Framework | Design | Fig 3.1 reflects the old pipeline | **Replace** | New framework figure; factorial, not ladder | `02-pipeline.md` | R3.3 | **P0** |
| 3.2 Research Stages | Process | Broadly retainable | Refine | Add the staged campaign S1–S6 | `tools/CAMPAIGN.md` | — | P2 |
| 3.3 Dataset | Data | Sound | **Retain** | Correct one fact: **13** held-out frames, not 12 | `chapter/01-dataset.md` | — | P2 |
| 3.4.x Preprocessing | Data prep | Missing the undistortion requirement | **Expand** | OPENCV→PINHOLE is a hard prerequisite; state it | `source/undistort.py` | R3.2 | **P1** |
| 3.5.1 Proposed Method Overview | Method | Describes prior design | **Replace** | Baseline + three mechanisms + the integration decisions | `chapter/03-proposed-method.md` | R2.1 | **P0** |
| 3.5.2 Component 1: Deterministic Init | M1 | Prior pipeline | **Replace** | RoMa, train-views-only, cheirality, hashed clouds | `source/roma_init.py`, CD-15/16 | R3.2 | **P0** |
| 3.5.3 Component 2: Spatial Reorganization | M2 | **Describes a method that was not implemented** (D-1) | **Replace** | Accumulator importance, stochastic sampling, two iterations, CD-6 burst | `source/simplify.py` | **R3.6** | **P0** |
| 3.5.4 Component 3: Quantization | M3 | Post-hoc k=256 described (D-2) | **Replace** | Quantization-aware, STE, k-means++, k=4096 | `source/quantize.py` | **R3.6** | **P0** |
| — | *(new)* | No account of integration decisions | **Add §3.5.5** | The CD register — where the thesis's own technical content lives | `06-implementation-deltas.md` | R2.1, meta M.1 | **P0** |
| 3.6.1 Experimental Configuration | Design | Ladder-shaped | **Replace** | 2³ factorial, both directions of inference | `chapter/05-experimental-design.md` | R3.3 | **P0** |
| 3.6.4 Ablation Study Design | Design | Superseded | **Merge** into 3.6.1 | — | — | — | P1 |
| — | *(new)* | No repeated-run design | **Add §3.6.6** | 3 seeds; scenes as blocks; **measured dispersion** and what it bounds | D-5 | **R3.2** | **P0** |
| 3.7.1 Fidelity Metrics | Metrics | PSNR convention unstated | **Refine** | Both conventions, labelled; LPIPS backbone named | `utils/metrics_conventions.py`, CD-19 | R3.2 | **P1** |
| 3.7.2 Efficiency Metrics | Metrics | Composite ratios (C.1); no timing protocol | **Replace** | Count, size **with container stated**, fps with a defined protocol, peak memory. Drop PSNR/MB and FPS/MB | D-4, D-7, `utils/render_profile.py` | **R3.2** | **P0** |
| — | *(new)* | No hardware/reproducibility protocol | **Add §3.8** | Hardware, seeds, manifest, acceptance suites, threats to validity | `10-reproducibility.md` | **R3.2** | **P0** |
| — | *(new)* | No underwater-conditioned diagnostics | **Add §3.9** | Ẑ_min/Ẑ_max and the nine medium scalars per interval; what they test (H4) | CD-12 | **R2.3, meta M.2** | **P0** |

---

## Chapter IV — Results and Discussion *(revise after evidence)*

**Every numeric table and figure in this chapter must be rebuilt.** They come from a codebase
with documented fidelity gaps (D-1, D-2), reported without dispersion (D-5), using a different
size convention (D-4) and an undefined timing protocol (D-7). The brief prohibits retaining
them for continuity.

| § | Current role | Action | Revised role | Blocked on |
|---|---|---|---|---|
| 4.1 Experimental Overview | Scope | **Replace** | Campaign scope, completion matrix, what is and is not concluded | — |
| 4.2 Baseline Performance | A0 | **Replace** | A0 **plus the replication against unmodified SeaSplat** — new, and answers R3.6's control concern | ✅ **S1 complete** |
| — | *(new)* | | **Add §4.3** | **Measurement dispersion**, per scene. Framing: this bounds every contrast that follows | ✅ **S1 complete** |
| 4.3 Component 1 (A1) | M1 | **Replace** | Main effect of M1, both directions | S3 |
| 4.4 Component 2 (A2) | M2 | **Replace** | Main effect of M2 **plus H4** — the medium-identifiability test | S2 |
| 4.5 Component 3 (A3) | M3 | **Replace** | Main effect of M3, renormalised compression (C.3) | S3 |
| — | *(new)* | | **Add §4.6** | **Interactions** — two-way and three-way, against pooled dispersion; `UNDETERMINED` where unresolvable | S4, S5 |
| — | *(new)* | | **Add §4.7** | **Underwater-conditioned analysis** — mechanism behaviour vs attenuation, backscatter, depth range | S2–S5 |
| 4.6 Cross-Component Discussion | Synthesis | **Reorganize** | Mechanism-level synthesis, not cell-by-cell | S4, S5 |
| — | *(new)* | | **Add §4.9** | **Mechanism D** contrast — only if S6 completes | S6 |
| 4.7 Limitations | Limits | **Expand** | Add D-9 (one operating point), heterogeneous dispersion, four scenes | — |

**Writable now:** §4.1, §4.2, §4.3 — the baseline, its replication, and the dispersion. That
is a genuine, self-contained result section answering R3.2 and R3.6.

---

## Chapter V — Conclusions *(revise last)*

Every subsection is downstream of Chapter 4. **Defer all**, with two exceptions:

| § | Action | Note |
|---|---|---|
| 5.1.1 *"feasible but representation-heavy"* | **Retain in substance** | Survives — supported by A.1/A.2 |
| 5.1.2 *"Spatial reorganization provides the most balanced…"* | **Remove** | This is B.1 — contradicted (D-1) |
| 5.1.3–5.1.6 | Defer | — |
| 5.2 Research Contributions | **Replace** | §4.5's five, methodological first | — |
| 5.3 Future Works | **Refine** | Include the budget sweep (D-9) as the named next step | — |

---

## Sequencing and gates

| Stage | Work | Depends on | Gate |
|---|---|---|---|
| **0** | Six missing method breakdowns (D-8) | — | none — start now |
| **1** | Ch. 2 rewrite | stage 0 | — |
| **2** | Ch. 1 rewrite | Ch. 2 | **repositioning approval (Gate 2)** |
| **3** | Ch. 3 rewrite | implementation @ `3c165ae` ✅ | — |
| **4a** | Ch. 4 §§4.1–4.3 | ✅ S1 | — |
| **4b** | Ch. 4 §§4.4–4.8 | S2–S5 | evidence sufficiency |
| **5** | Ch. 5 | Ch. 4 stable | — |

**Stages 0, 1, 3 and 4a are unblocked by the running campaign.** That is roughly 60% of the
thesis, and it includes the two chapters the reviewers criticised most.
