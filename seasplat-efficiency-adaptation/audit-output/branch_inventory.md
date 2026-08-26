# §1 — Branch inventory and pre-flight

**Audit date:** 2026-08-25
**Repo audited:** `C:/Users/Irham/Documents/2025/master-degree/BINUS/Thesis/seasplat-efficient-3dgs-underwater`

| Remote | URL |
|---|---|
| `origin` | `git@github.com:dinanirham/seasplat-efficient-3dgs-underwater.git` |
| `upstream` | `https://github.com/dxyang/seasplat.git` |

> ⚠️ The audited repo is **not** under `my-research/`. It sits in a sibling `Thesis/`
> directory. The prompt's `./seasplat-efficiency-adaptation/audit-output/` was resolved
> relative to the session working directory (`my-research/`), which keeps this audit next to
> the nine method breakdowns it cites. See `open_questions.md` Q-1.

---

## Pre-flight: prerequisite artifacts

The prompt instructed me to read `REPO_ACTION_PLAN.md`, `METHOD_ALIGNMENT_AUDIT.md`, and any
`compatibility_matrix.md` **before** producing new analysis, and to build on them rather than
duplicate them. **None of them exist.**

| Artifact | Status |
|---|---|
| `REPO_ACTION_PLAN.md` | ❌ does not exist (searched repo root + all subdirs, all branches) |
| `METHOD_ALIGNMENT_AUDIT.md` | ❌ does not exist |
| `compatibility_matrix.md` | ❌ does not exist anywhere in repo or in `my-research/` |
| `docs/ablation_design.md` | ⚠️ **exists but is 0 bytes** |
| `docs/experiment_plan.md` | ⚠️ **exists but is 0 bytes** |
| `docs/reproducibility_notes.md` | ⚠️ **exists but is 0 bytes** |

**Consequence for this audit.** There is no recorded statement of design intent to audit the
implementation *against*. So "canonical methodology" throughout §2–§3 is taken from the
primary sources — the nine papers and repos broken down under
`my-research/<method>/research-methodology-output/` — and SeaSplat's own constraints from
`my-research/seasplat/research-methodology-output/`. Every claim about what a source method
*should* do carries a `[paper §X]` or `[repo: file:line]` tag pointing at those breakdowns.

**This also means design intent is unrecorded.** Where the audit says a branch "deviates," it
can only establish deviation from the *published* method, not from what the author intended.
Several findings below would resolve immediately if the three empty `docs/` files were filled
in. That is itself the highest-value cheap action in `refit_recommendations.md`.

---

## Resolved branches

All eight branches resolved. The prompt listed the four combination branches as "TBD"; they
are `a4`–`a7`, confirmed by diff content rather than by name alone.

| Label | Branch | Commit | Date | Diff vs baseline |
|---|---|---|---|---|
| **Baseline** | `baseline/seasplat` | `ddc6259` | 2024-11-27 | — |
| **A1** | `feature/a1-deterministic-init` | `ce9c21e` | 2026-05-11 | 9 files, +340 / −1 |
| **A2** | `feature/a2-spatial-reorganization` | `bcd6eee` | 2026-05-12 | 7 files, +95 / −5 |
| **A3** | `feature/a3-attribute-quantization` | `980e915` | 2026-05-12 | 7 files, +325 / −0 |
| **A1+A2** | `feature/a4-init-reorg` | `788b325` | 2026-05-12 | 10 files, +421 / −6 |
| **A1+A3** | `feature/a5-init-quant` | `fd56225` | 2026-05-12 | 10 files, +651 / −1 |
| **A2+A3** | `feature/a6-reorg-quant` | `26ea058` | 2026-05-12 | 9 files, +403 / −5 |
| **A1+A2+A3** | `feature/a7-full-integration` | `b4802fb` | 2026-05-12 | 11 files, +729 / −6 |

Two further branches exist and are **not** ablation arms:

| Branch | Commit | Note |
|---|---|---|
| `research/efficiency-ablation-framework` | `d60336d` | 4 files, +17 — creates the three empty `docs/` files. Scaffolding only. |
| `master` | `ddc6259` | identical to `baseline/seasplat` |

**Branches unresolved: none.**

### Baseline provenance ✅

`baseline/seasplat` @ `ddc6259` is the unmodified upstream SeaSplat commit — the same tree
analysed in `my-research/seasplat/research-methodology-output/`. All findings below are
therefore anchored to a baseline whose behaviour is already documented section by section.

### Case discrepancy (cosmetic)

The working tree was checked out on `feature/A1-deterministic-init` (capital A), while
`git branch -a` lists `feature/a1-deterministic-init` (lowercase). This is Windows'
case-insensitive filesystem resolving the same ref two ways. It is harmless locally but
**will produce two distinct refs on the Linux side of a push**, and `git checkout` scripts
written with one casing will fail on the other. Noted in `open_questions.md` Q-2.

---

## Files touched, by branch

Only the method-bearing files are listed; each branch also touches `README.md` (+17) and, for
A1/A3, adds a file under `source/`.

| File | A1 | A2 | A3 |
|---|---|---|---|
| `scene/__init__.py` | ✅ +20 | — | — |
| `scene/gaussian_model.py` | — | ✅ +45 | — |
| `train.py` | ✅ 1 line | ✅ +33 / −5 | ❌ **untouched** |
| `arguments/__init__.py` | ✅ +2 | ✅ +2 | ✅ +3 (dead) |
| `source/roma_init.py` | ✅ new, 300 lines | — | — |
| `source/quantize.py` | — | — | ✅ new, 303 lines |
| `metrics.py`, `render_uw.py`, `utils/image_utils.py` | ❌ | ❌ | ❌ |
| `requirements.txt` | ❌ | ❌ | ❌ |

**Verified: the evaluation path is byte-identical across all eight branches.**
`git diff baseline/seasplat..<branch> -- metrics.py render_uw.py utils/image_utils.py`
returns zero changed files for every one of the seven feature branches. Whatever else is
true, the branches are being scored by the same code. See `validation_alignment.md`.

---

## Combination branches are clean file-level unions

Verified rather than assumed:

| Check | Result |
|---|---|
| `git diff a2..a4 -- train.py` | only A1's one-line `no_densify` gate |
| `git diff a4..a7 -- train.py scene/gaussian_model.py` | **empty** |
| `source/quantize.py` across a3 / a5 / a6 / a7 | **identical** (hash-compared) |
| `source/roma_init.py` across a1 / a4 / a5 / a7 | identical |

No constituent mechanism was re-implemented or altered when combined. **Every conflict
identified in `combination_audit/` is therefore semantic, not a merge artifact** — which is
the good case, because it means the fixes are local to the individual arms.

---

## Dependency status

`requirements.txt` is unmodified on every branch. Checked against baseline contents:

| New import | In baseline `requirements.txt`? |
|---|---|
| `open3d` (A1, `scene/__init__.py` + `roma_init.py`) | ✅ `open3d==0.18.0` |
| `plyfile` (A3, `quantize.py`) | ✅ `plyfile==0.8.1` |
| `sklearn.cluster.MiniBatchKMeans` (A3) | ✅ `scikit-learn==1.5.1` |
| **`romatch`** (A1, `roma_init.py`) | ❌ **absent** |

`romatch` is the only genuinely missing dependency, and it is needed only by the offline A1
preprocessing step, not by training. Since `roma_init.py` is run manually, this fails loudly
at import rather than silently — low severity, but it should be pinned for reproducibility
(RoMa's outdoor weights and API have changed across releases; see
`my-research/RoMa/research-methodology-output/10-reproducibility.md`).
