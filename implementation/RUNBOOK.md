# Runbook — executing the campaign

The ordered steps, what each should print, and what to do when it doesn't.

For *why* the harness behaves as it does — stage ordering, prerequisites, guard
rails — see [`tools/CAMPAIGN.md`](tools/CAMPAIGN.md). For the design the runs
serve, see [`docs/ablation_design.md`](docs/ablation_design.md).

---

## Before you start: what this costs

**96 runs ≈ 145 GPU-hours ≈ ~1,700 Colab compute units ≈ roughly $170** at
pay-as-you-go rates. Colab Pro's monthly allowance is 100 units, so the full
matrix is well beyond a single subscription. Rates change — treat that as an
order of magnitude, not a quote.

This is why the staging matters, and it is worth deciding how far to go before
starting rather than discovering the bill at S4:

| Through | Runs | ~GPU-h | ~$ | Buys you |
|---|---|---|---|---|
| **S1 + S2** | 24 | 36 | 45 | **H4 — the central hypothesis**, via the Ẑ/β diagnostics in A2 |
| + S3 | 48 | 72 | 90 | all three main effects |
| + S4 | 84 | 126 | 155 | the three two-way interactions |
| + S5 | 96 | 145 | 170 | the three-way term and the from-above contrasts |

If compute is tight, `12-novelty-defensibility.md` §12.4 names the minimum
viable experiment: **A0 vs A2 with the diagnostics logged** — Phases 0–3 plus
one stage. Everything beyond that strengthens the claim; it is not the
foundation.

---

## Phase 0 — get the code onto `main`  *(local, ~2 min)*

The notebooks run `git clone --depth 1`, which takes the **default branch**.
Until the work is merged, Colab would clone a `main` with no notebooks and no
undistortion code.

```bash
git push -u origin <branch>
```

Then open a PR against `main` on GitHub, merge it with **"Create a merge
commit"** (not squash — the commit messages carry the reasoning), and locally:

```bash
git checkout main && git pull
```

✅ **Check:** `git log --oneline -1` on `main` shows the merge.

---

## Phase 1 — Drive prep  *(once, ~5 min)*

**1.1** Confirm the four scenes sit under `e3dgsuw/dataset/` — either directly,
or nested one level (e.g. `dataset/SeathruNeRF_dataset/`). Both work; the
notebook detects which.

**1.2** Upload the three notebooks from `notebooks/` to Drive and open each
with Colab.

Edit `DRIVE_ROOT` at the top of each **only** if your folder is not at
`/content/drive/MyDrive/e3dgsuw`.

---

## Phase 2 — `00_setup.ipynb`  *(once, ~1–2 h)*

Set the runtime to **A100** first (`Runtime → Change runtime type`). Cell 2
aborts otherwise, deliberately: every conclusion is a between-cell contrast,
and cells on different devices are not comparable.

Run top to bottom.

| Cell | Expect | If it fails |
|---|---|---|
| 1 Drive | your three paths | `DRIVE_ROOT` wrong → edit it |
| 2 GPU | `A100 … sm_80` | wrong GPU → change runtime type, rerun |
| 3 Clone | one-line git log | private repo → set `GITHUB_TOKEN` in the cell |
| 4 Build | ~5 min, then `extensions import OK` | see *Build fails* below |
| 5 **Verify rasterizer** | **7/7** | **stop** — see below |
| 6 Suites | nine × `PASSED` | stop and report |
| 7 Dataset | `21 / 29 / 20 / 18` | counts wrong → check the upload |
| 8 Undistort | ~5 min, `OPENCV → PINHOLE` ×4 | `colmap` missing → rerun the install cell |
| 9 Dense clouds | **40–100 min**, four `.ply` | session drop → rerun; done scenes skip |
| 10 Ledger | `96 runs  pending=96` | — |

**Cell 5 is the gate.** The rasterizer merge rests on one identity: for a
single Gaussian at depth `z` the probe gives `Z_raw = α·z`, so `Z_raw/α` must
recover `z` on every covered pixel. It was verified to ~1e-7 on sm_86 during
development. If T3 fails on sm_80, **stop** — every cell of the matrix is built
on this and nothing downstream would be trustworthy.

A session drop during cell 9 costs nothing: reopen and rerun the notebook, and
completed scenes are skipped.

---

## Phase 3 — S1, the A0 runs  *(~18 GPU-hours)*

Open `01_worker.ipynb`, run every cell, **edit nothing**.

Set `--max_minutes` to roughly **30 minutes below your real session limit**, so
the loop stops claiming new runs and exits cleanly instead of being killed
mid-run. The default 200 is conservative; if you reliably get 12-hour sessions,
use 690.

Repeat in fresh sessions until the ledger reports S1 complete — 12 runs at
about 1.5 h each.

### Then set the budget

Cell 7 prints A0's converged primitive counts and suggests ~60% of the median.

```bash
!python -m tools.run_ledger set-budget <count> --output_root "$DRIVE_ROOT"
```

Choose a value **below** those counts. This matters more than it looks: the
primitive budget is derived from A0 because no publication of the baseline
reports its count, and **a budget that does not bind makes A4 equivalent to A1
and A7 to A5** — a null interaction measured in that state is a configuration
artifact rather than a finding. The run also warns loudly if it fails to bind.

✅ **Check:** `run_ledger status` shows a budget, and A2 is no longer blocked.

---

## Phase 4 — the remaining stages  *(~126 GPU-hours)*

The same worker notebook, unchanged, until the ledger empties. Stages
self-sequence:

```
S2  A2            12 runs   the central hypothesis
S3  A1, A3        24 runs   remaining main effects
S4  A4, A5, A6    36 runs   the two-way interactions
S5  A7            12 runs   three-way term, from-above contrasts
```

If a session dies mid-run, **do nothing** — the row is left with a stale
heartbeat and the next session reclaims it. Interrupted runs restart rather
than resume, deliberately: the checkpoint omits the medium model, the codebooks
and the loop's schedule flags, so resuming would silently reinitialise β and
produce a run that looks complete and is a different experiment.

---

## Phase 5 — `02_analysis.ipynb`

No GPU. Run it whenever; a partial campaign produces partial contrasts rather
than invented ones — missing cells are reported and the affected contrasts
omitted.

Two rules the output enforces, worth remembering when reading it:

- Where a main effect's **from-below and from-above estimates disagree**,
  neither may be quoted alone. The disagreement *is* the interaction.
- Nothing is quotable without dispersion. A single seed yields `nan` error bars
  and `UNDETERMINED`, not a confident-looking number.

---

## Troubleshooting

**Build fails.** Almost always a torch/CUDA mismatch. The build deliberately
compiles against whatever torch Colab ships rather than installing its own —
if you pinned a torch by hand, remove that. Check `nvcc --version` and
`torch.version.cuda` are the same major version.

**`verify_rasterizer` fails.** Stop. Do not train. Report which check failed;
T3 in particular is the identity the whole merge depends on.

**A scene fails at load with a camera-model assert.** Undistortion did not run
for it. Rerun cell 8 of `00_setup`; it is idempotent.

**The queue says everything is blocked.** Either the budget is unset (expected
before S1 finishes) or the dense clouds are missing (rerun cell 9 of
`00_setup`). The queue prints which.

**A run keeps failing.** After three attempts the ledger stops claiming it.
`run_ledger status` shows the error; the run's `train.log` has the detail.

**Drive is filling up.** It should not — the save schedule is trimmed to the
final iteration precisely because the upstream default would have written ~86 GB
across the campaign. If it is growing faster than ~120 MB per run, check that
`save_iterations` and `checkpoint_iterations` in `configs/cells.json` are still
`[30000]`.

---

## What "done" looks like

- `run_ledger status` — 96 `done`, 0 pending, 0 failed
- `analysis/analysis_unweighted.json` and `analysis_image_weighted.json` written
- every run directory holds `run_config.json`, `diagnostics.csv`,
  `eval_metrics.json`, `compressed_30000/`, `train.log`
- all 96 runs report the same GPU in their manifests

That last one is not bookkeeping: the analysis warns if runs span devices,
because every conclusion in the study is a between-cell contrast.
