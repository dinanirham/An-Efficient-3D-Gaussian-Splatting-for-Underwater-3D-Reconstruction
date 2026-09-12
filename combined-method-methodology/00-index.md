# Combined-method research methodology — index and reading order

**Working title of the method:** *An Efficient 3D Gaussian Splatting for Underwater 3D
Reconstruction* — SeaSplat's physically-grounded underwater 3DGS baseline extended with
three efficiency mechanisms, applied individually, pairwise, and fully stacked.

> **The title carries a method claim the evidence does not support, and it is being
> withdrawn.** `new-revisited-writing/04-repositioning.md` (Framing A, approved
> 2026-09-10) reframes the work as a controlled factorial *study* rather than an efficient
> *method*. The mechanisms are also **not orthogonal on this baseline** — that is the
> study's central finding rather than an aside. §1 develops it and
> `13-campaign-addendum` §13.13 measures it.

**Location rationale.** This folder is `my-research/combined-method-methodology/`. It is a
new sibling of the nine reference-method folders, deliberately *not*
`seasplat-efficiency-adaptation/` or `seasplat-efficient-3dgs-underwater/` — both of which
were excluded from this pass by the task brief and are neither read nor cited anywhere in
this folder. Placing the synthesis beside its sources keeps every relative link
(`../seasplat/research-methodology-output/...`) valid.

---

## Sources of evidence

This is a **synthesis pass**. The primary evidence is the nine per-method breakdowns already
present under `my-research/`, each generated against its own paper PDF and repository
checkout. No paper was re-read from PDF for this pass; where a claim needed the paper
directly, it is tagged `[unverified]` instead.

| Role in the combined method | Folder | Paper / commit as recorded in that folder's `00-index.md` |
|---|---|---|
| **Underwater baseline** | `../seasplat/` | SeaSplat, arXiv:2409.17345v2 · repo `dxyang/seasplat` @ `ddc6259` |
| **Mechanism 1 — dense/deterministic initialization** | `../EDGS/` | EDGS, CVPR 2026, arXiv:2504.13204v2 · repo `CompVis/EDGS` @ `f90b022` (code frozen at `668e280`) |
| ↳ its hard dependency | `../RoMa/` | RoMa, CVPR 2024, arXiv:2305.15404v2 · repo `Parskatt/RoMa` @ `v0.1.2-4-g77f8d68` |
| **Mechanism 2 — spatial reorganization / budget pruning** | `../mini-splatting/` | Mini-Splatting, ECCV 2024, arXiv:2403.14166v3 · repo `fatPeter/mini-splatting` @ `c0d5581` |
| **Mechanism 3 — attribute quantization** | `../compact3d/` | CompGS / Compact3D, ECCV 2024, arXiv:2311.18159v3 · repo `UCDvision/compact3d` @ `dccc07e` |
| Context — the baseline's own baseline | `../seathru_NeRF/` | SeaThru-NeRF, CVPR 2023, arXiv:2304.07743v1 · repo @ `3f4ebfe` |
| Context — related-work positioning | `../CompGS/`, `../OMG/`, `../RoMaV2/` | Liu et al. ACM MM 2024 · OMG NeurIPS 2025 · RoMa v2 arXiv:2511.15706v3 |
| Cross-method notation and hazards | `../comparison-glossary.md` | merged from all nine `09-glossary.md` files |
| Dataset | `../dataset/SeathruNeRF_dataset/` | 4 scenes, inspected directly on disk |

**A naming hazard carried forward.** "CompGS" denotes two unrelated papers. Throughout this
folder, **Mechanism 3 is `../compact3d/`** (Navaneet et al., K-means VQ), written
**CompGS-VQ**. `../CompGS/` (Liu et al., predictive coding + entropy model) is written
**CompGS-Liu** and appears only as related work.

---

## Evidence tags

The per-source tags are carried forward verbatim wherever a claim originates in one of the
nine breakdowns, so a reader can always trace back one more level:

- `[paper §X / Eq. Y]` — stated explicitly in the named method's paper.
- `[repo: path:line]` — confirmed from that method's source at the commit above.
- `[inferred]` — derived here by combining two or more verified facts; the derivation is
  stated in place.
- `[unverified]` — plausible or commonly assumed, but not traceable to paper, repo, or an
  existing breakdown in this pass.
- **`[proposed integration]`** — *new in this folder.* Marks a design decision that belongs
  to the combined method itself: it is not stated by any source paper, not present in any
  source repository, and not measured. Every such line is a claim about what *would have to*
  be done, not a report of what *was* done.

The `[proposed integration]` tag is the honest core of this document *as it was first
written*. The combined method has no published paper, and at the time of the synthesis pass
**no measured results existed anywhere under `my-research/` outside the two excluded
paths**, so anything that would normally be `[paper]` or `[repo]` for the combined method
was either inherited from a source or `[proposed integration]`.

**That is no longer the state.** The campaign has since produced measured results for cells
A0–A3 at twelve runs each, plus A4 on one scene, and a fifth tag is now in use
throughout: `[measured n=k]`, where `k` is the number of runs behind the statement. Where a
`[proposed integration]` has been executed and measured, the measurement supersedes the
proposal — including where it **refuted** it, which is what happened to the most
substantive one (CD-6, `03-claim-validity-ledger` E.6).

---

## Deliverable set 1 — technical, evidence-tagged files

| § | File | Contents |
|---|---|---|
| 1 | [`01-taxonomy.md`](01-taxonomy.md) | Confirmed baseline/mechanism mapping; per-ablation "adapt, not merely apply"; the novelty claim and its gating; closest related works |
| 2 | [`02-pipeline.md`](02-pipeline.md) | Baseline train loop with three labelled insertion points and trigger conditions; composition view of all eight configurations |
| 3 | [`03-variables.md`](03-variables.md) | Merged variable table tagged by origin; shared variables flagged as interaction candidates |
| 4 | [`04-loss.md`](04-loss.md) | The baseline's full seven-term objective plus the one mechanism-required term, tagged needed / implemented / validated |
| 5 | [`05-constraints.md`](05-constraints.md) | Baseline well-posedness mechanisms; per-ablation and per-combination risk register |
| 6 | [`06-implementation-deltas.md`](06-implementation-deltas.md) | Inherited deltas by source, plus deltas specific to the combination |
| 7 | [`07-pseudocode.md`](07-pseudocode.md) | One canonical flag-gated algorithm; composition order justified; per-line origin tags |
| 8 | [`08-computational-profile.md`](08-computational-profile.md) | Individually reported gains; the combined-method measurement gap stated as a fact; what a non-additive effect would look like |
| 9 | [`09-glossary.md`](09-glossary.md) | Merged symbol table restricted to the four composition members, with collisions flagged and a recommended write-up notation |
| 10 | [`10-reproducibility.md`](10-reproducibility.md) | Protocol consistency across sources; the additive-vs-leave-one-out framing, stated explicitly |
| 11 | [`11-paper-vs-repo-disagreements.md`](11-paper-vs-repo-disagreements.md) | Which inherited disagreements actually bite the combined method, and the combination-specific ones |
| 12 | [`12-novelty-defensibility.md`](12-novelty-defensibility.md) | What a reviewer could not find elsewhere; the strongest counter-objection; the narrower contribution the evidence actually supports |
| **13** | [**`13-campaign-addendum.md`**](13-campaign-addendum.md) | **What execution changed. Supersedes 01-12 wherever they disagree** — CD-22/CD-23, the verified baseline, mechanism D, `n_bud`, and the run-to-run variance that invalidates single-run comparisons |

## Deliverable set 2 — narrative methodology chapter

Committee-facing academic prose, one file per subsection, in [`chapter/`](chapter/):

| File | Subsection |
|---|---|
| [`chapter/00-overview.md`](chapter/00-overview.md) | Research design and overview |
| [`chapter/01-dataset.md`](chapter/01-dataset.md) | Dataset |
| [`chapter/02-preprocessing.md`](chapter/02-preprocessing.md) | Preprocessing |
| [`chapter/03-proposed-method.md`](chapter/03-proposed-method.md) | Proposed method — the intellectual core |
| [`chapter/04-implementation-details.md`](chapter/04-implementation-details.md) | Implementation details |
| [`chapter/05-experimental-design.md`](chapter/05-experimental-design.md) | Experimental design |
| [`chapter/06-evaluation-metrics.md`](chapter/06-evaluation-metrics.md) | Evaluation metrics |
| [`chapter/07-validity-and-reproducibility.md`](chapter/07-validity-and-reproducibility.md) | Statistical validity and reproducibility |
| [`chapter/08-scope-and-limitations.md`](chapter/08-scope-and-limitations.md) | Scope and limitations |
| [`chapter/09-summary.md`](chapter/09-summary.md) | Chapter summary |

Plus [`open-questions.md`](open-questions.md) — gaps, unresolved items, and everything the
excluded paths would have answered.

---

## Reading order

**If you are assessing the contribution:** `01-taxonomy.md` → `12-novelty-defensibility.md`
→ `05-constraints.md` → `open-questions.md`. That path reaches the honest answer fastest.

**If you are implementing:** `02-pipeline.md` → `07-pseudocode.md` → `03-variables.md` →
`06-implementation-deltas.md` → `10-reproducibility.md`.

**If you are writing the thesis chapter:** read the `chapter/` files in order; consult the
numbered files only when a reviewer asks "where does that come from?"

---

## One-paragraph summary of the combined method

The baseline is **SeaSplat**: vanilla 3DGS whose rasterized output is reinterpreted as the
*medium-free* radiance `Ĵ`, composed through the Akkaynak–Treibitz revised underwater image
formation model `Î = Ĵ ⊙ Â + B̂` — with `Â = e^{-β^D Ẑ}`, `B̂ = σ(B^∞)(1 - e^{-β^B Ẑ})` and a
rasterized depth `Ẑ` — before the photometric loss is applied. The medium is **nine global
scalars** for the whole scene, kept well-posed by five auxiliary priors, systematic gradient
detachment, and a bursty alternating-optimization schedule. Onto this baseline the combined
method grafts three mechanisms that are orthogonal *in air*: **(1)** EDGS's one-shot dense
initialization, which triangulates RoMa correspondences into a dense cloud — **244 000
to 294 000 points on this corpus** `[measured n=1/scene]`, far below EDGS's own ~10⁶,
because this corpus has 15–25 training views and because CD-26's parallax filter rejects
24% of all triangulations — and switches densification off; **(2)** Mini-Splatting's importance-weighted stochastic subsampling to a
fixed primitive budget, optionally with its depth-reinitialization densifier; and **(3)**
CompGS-VQ's K-means vector quantization of per-Gaussian attributes. The eight resulting
configurations form a 2³ factorial matrix.

**What makes this more than a bolt-on exercise** is that all three mechanisms turn out to
act on quantities the baseline's well-posedness argument depends on — the *rasterized depth
map*, the *opacity field*, and the *per-Gaussian attribute vector* — and two of them
(EDGS's initialization, Mini-Splatting's depth reinitialization) fail precisely in the
water column, which is the exact region SeaSplat's `L_op` exists to police. The combined
method's own technical content is therefore the set of integration decisions that keep the
medium model identifiable while the geometry underneath it is being replaced, thinned, and
quantized. Those decisions are enumerated in `01-taxonomy.md` §3 and `05-constraints.md` §5,
and they are the basis of the novelty claim assessed in `12-novelty-defensibility.md`.

**The claim type the evidence supports is (c) — a required well-posedness / integration
fix — supported by (a), a genuine prior-art gap. Claim (b), a measured non-additive
interaction effect, is *still not* supported**, though the reason has changed: measurements
now exist for the single-mechanism cells, but no interaction term has been estimated, and
the measured run-to-run dispersion means an interaction — a difference of differences,
carrying roughly twice the variance of a main effect — may not clear the noise floor even
after all 108 runs. **A null interaction and an unresolvable one are different findings**,
and the analysis tooling emits `UNDETERMINED` rather than rounding the second to the first.
See `12-novelty-defensibility.md` §12.6 for the reasoning and `open-questions.md` for
what would close it.

> **Read `13-campaign-addendum.md` first if you are reading this after implementation.**
> Sections 01–12 were a synthesis pass written *before any code ran*. Section 13 records what
> changed once it did.
>
> **They have since been reconciled rather than left to disagree.** Each file that carried a
> superseded claim now carries the correction in place, tagged `[measured n=k]` so the sample
> size behind every empirical statement is visible: `05-constraints.md` §5.6 (a degeneracy
> class the original analysis had no category for), `06-implementation-deltas.md` §6.7
> (CD-22 … CD-25), `07-pseudocode.md` (three rasterization passes, and which gradient buffer
> each writes into), `08-computational-profile.md` §8.2b (the measured A0 reference point),
> `10-reproducibility.md` §10.4 (the magnitude of the non-determinism), and
> `12-novelty-defensibility.md` §12.6 (the revised novelty verdict). In particular: the
> baseline is now empirically verified against vanilla SeaSplat, `n_bud` is fixed
> pre-campaign rather than derived from A0, a fourth mechanism exists as a supplementary
> contrast, and `n_primitives` turns out to carry ~21% run-to-run spread — which
> invalidates any single-run comparison, including several made during the investigation
> that produced these corrections.
