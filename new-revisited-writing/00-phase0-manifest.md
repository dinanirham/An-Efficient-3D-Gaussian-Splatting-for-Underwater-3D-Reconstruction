# Phase 0 — Version and Artifact Manifest

**Gate 1 deliverable.** What is treated as authoritative, what could not be reached, and what
must be resolved before any chapter is rewritten.

Date of audit: 2026-09-09.

---

## 0.1 Authoritative sources, in the hierarchy the brief specifies

| Rank | Source | Identifier | Status |
|---|---|---|---|
| 1 | Executed run artifacts | `MyDrive/e3dgsuw/` — ledger, `runs/`, `dense/`, `analysis/` | ⚠️ **partially reachable** — see §0.4 |
| 2 | Implementation at the recorded commit | `implementation/` @ **`3c165ae`** on `main` | ✅ authoritative |
| 3 | Repository methodology | `combined-method-methodology/` (13 files + 10-file chapter set) | ✅ authoritative |
| 4 | Source papers and official repos | 9 × `research-methodology-output/` (12 files each) + 13 PDFs | ✅ authoritative |
| 5 | Thesis manuscript | *An Efficient 3D Gaussian Splatting for Underwater 3D Reconstruction — Assurance of Learning Research Writing I*, 153 pp., modified **2026-05-22** | ✅ authoritative |
| 6 | Reviewer feedback | SIGGRAPH Asia 2026, submission `tcom_126`, 4 reviews + meta-review | ✅ authoritative |

### Repository state

```
origin/main            3c165ae   Merge branch 'fix/analyse-reports-fps'
tag                    baseline/seasplat-ddc6259   (pristine SeaSplat, upstream HEAD)
unmerged branch        docs/s1-results   2 commits — S1 results + methodology reconciliation
```

`implementation/` is 60 Python files. Ten acceptance suites, 81 checks; the nine
non-CUDA suites pass locally, the tenth (`verify_rasterizer`, 8 checks) requires the A100 and
passed there most recently at 8/8.

### Prior implementation — a separate codebase, not an ancestor

`previous-writings/previous-repo/seasplat-efficient-3dgs-underwater/` is **not** an earlier
state of `implementation/`. It is an independent fork whose `master` is pristine SeaSplat
`ddc6259` with a clean working tree, and whose mechanisms live on eight feature branches:

| branch | tip | date |
|---|---|---|
| `baseline/seasplat` | `ddc6259` | 2024-11-27 (upstream) |
| `feature/a1-deterministic-init` | `ce9c21e` | 2026-05-11 |
| `feature/a2-spatial-reorganization` | `bcd6eee` | 2026-05-12 |
| `feature/a3-attribute-quantization` | `980e915` | 2026-05-12 |
| `feature/a4-init-reorg` … `a7-full-integration` | `b4802fb` | 2026-05-12 |
| `research/efficiency-ablation-framework` | `d60336d` | 2026-05-11 |

**This matters for the rewrite.** The manuscript's Chapter IV and the SIGGRAPH submission
report results produced by *this* codebase, not by `implementation/`. The two are not
interchangeable, and §1 of the discrepancy ledger shows they are not equivalent.

---

## 0.2 Reviewer document — complete and recovered

`previous-writings/siggraph-submission/SIGGRAPH_ASIA_2026_rejected.pdf`, 4 pages.

The file carries **no text layer** — it is a page-image capture of the review portal, with no
fonts and only image-draw operators. Text was recovered by rasterising at 150 dpi and reading
the pages. Anyone re-checking this should not expect `pdftotext` to return anything.

| | Rating |
|---|---|
| Reviewer 1 | Borderline Reject (−1) |
| Reviewer 2 | Borderline Reject (−1) |
| Reviewer 3 | Borderline Reject (−1) |
| Reviewer 4 | Borderline Accept (+1) |
| **Average** | **−0.5** |
| **Meta-review** | **Borderline Reject (−1)** |
| Committee comments | None |

**Submission title differs from the thesis title**, and the difference is informative:

> Thesis: *An Efficient 3D Gaussian Splatting for Underwater 3D Reconstruction*
> Submission: *Efficiency–Fidelity Tradeoffs in Compact 3D Gaussian Splatting for Underwater
> Scene Reconstruction*

The submission title already concedes the repositioning this audit recommends (§4): the work
is a study of *tradeoffs*, not a proposal of *an efficient method*. The thesis title still
claims the latter.

Full text and classification: `02-reviewer-traceability.md`.

---

## 0.3 Source-paper corpus

Nine methods analysed to a common 12-file template, each against its paper and repository
checkout:

`seasplat` · `seathru_NeRF` · `mini-splatting` · `compact3d` (CompGS-VQ) · `CompGS` (Liu et
al.) · `EDGS` · `RoMa` · `RoMaV2` · `OMG`, plus `gaussian-splatting`, `nerf` and `colmap` as
substrate.

**Gap against the brief's Phase 1 list.** The brief names four methods with no
`research-methodology-output` folder: **EAGLES**, **LightGaussian**, **ReSplat**,
**WaterSplatting**, **Aquatic-GS**, **Gaussian Splashing**. These are exactly the families
Reviewer 3 says are missing from related work. They are a Chapter 2 obligation and are listed
in `06-experiment-and-literature-plan.md`.

---

## 0.4 What could not be reached — declared rather than worked around

| Artifact | Status | Consequence |
|---|---|---|
| **Google Drive folder** (`1fN8669gX…`) | ❌ **not directly accessible from this environment** | Run artifacts were read only as pasted excerpts and downloaded files. The experiment-status audit in `01-discrepancy-ledger.md` §5 is built from those, and is marked with its provenance. A full Phase 4 per-cell inventory (checkpoint paths, retry history, per-run configs for all 108 rows) **cannot be completed from here** and needs either the ledger JSON or a directory listing. |
| **`analysis/` outputs** | ❌ none exist yet | No aggregated contrasts have been produced. Chapter 4 cannot be written from analysis output; only S1's raw counts are available. |
| **Prior-implementation run artifacts** | ❌ not present | The manuscript's Chapter IV numbers cannot be traced to configs or logs. They are treated as *reported* values of unknown provenance, not as verifiable evidence. |
| **Prior manuscript source** (`.docx`/LaTeX) | ❌ only the compiled PDF | Revision must produce new source; there is no editable original to patch. |

**None of these blocks the audit.** Two of them constrain what Chapter 4 may claim, and that
constraint is recorded in the claim-validity ledger rather than absorbed silently.

---

## 0.5 Experiment status at the time of audit

From the campaign ledger and pasted run output:

| Stage | Cells | Runs | Status |
|---|---|---:|---|
| S1 | A0 | 12 | ✅ **complete** — all four scenes, three seeds |
| S2 | A2 | 12 | ⏳ in progress |
| S3 | A1, A3 | 24 | pending |
| S4 | A4, A5, A6 | 36 | pending |
| S5 | A7 | 12 | pending |
| S6 | A0D | 12 | pending (supplementary contrast) |
| — | SS reference control | 4 | pending |
| | **total** | **112** | **12 complete (11%)** |

Preprocessing is complete: four scenes undistorted (OPENCV → PINHOLE), four dense clouds
built and SHA-256 hashed.

**The rewrite must therefore be staged.** Chapters 2, 1 and 3 can be written now. Chapter 4
can be written only as far as S1 supports, and Chapter 5 not at all. The brief anticipates
this — its Gate 4 orders revision the same way.

---

## 0.6 Phase 0 verdict

The repository revision and the latest manuscript are both established reliably, and the
reviewer document is complete. **Phase 0 passes; the audit may proceed.**

Two qualifications carried forward:

1. The manuscript's results and the current implementation's results come from **two
   different codebases**, and §1 of the discrepancy ledger establishes that they are not
   equivalent on the mechanism the manuscript reports as its headline result.
2. Direct Drive access is unavailable, so the per-cell experiment inventory is partial and
   marked as such wherever it is used.
