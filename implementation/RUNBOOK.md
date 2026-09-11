# Runbook — executing the campaign

The ordered steps, what each should print, and what to do when it doesn't.

For *why* the harness behaves as it does — stage ordering, prerequisites, guard
rails — see [`tools/CAMPAIGN.md`](tools/CAMPAIGN.md). For the design the runs
serve, see [`docs/ablation_design.md`](docs/ablation_design.md).

---

## Before you start: what this costs

**112 runs** — 96 factorial, 12 for the supplementary contrast, 4 for the
reference control. Colab Pro's monthly allowance is 100 compute units, so a
campaign this size is well beyond a single subscription whatever the exact
figure.

**The per-run cost is being re-derived and the old estimate is void.** This
runbook previously quoted ~1.5 h per run and ~$170 total, from a build whose
baseline converged to a sixth of the right primitive count. The corrected
baseline carries ~4.4M primitives and pays three rasterization passes per
iteration rather than two. For calibration: the unmodified upstream baseline
ran 30,000 iterations at 4.46M primitives in **~51 minutes** on this hardware.
Take the real figure from S1's first completed runs rather than from this
paragraph.

This is why the staging matters, and it is worth deciding how far to go before
starting rather than discovering the bill at S4:

| Through | Cumulative runs | Buys you |
|---|---:|---|
| **S1 + S2** | 24 | **H4 — the central hypothesis**, via the Ẑ/β diagnostics in A2 |
| + S3 | 48 | all three main effects |
| + S4 | 84 | the three two-way interactions |
| + S5 | 96 | the three-way term and the from-above contrasts |
| + S6 | 108 | mechanism D against the corrected baseline |
| + reference control | 112 | vanilla SeaSplat, one run per scene |

GPU-hours and cost are deliberately omitted until S1 supplies a measured
per-run figure. Multiply the runs by whatever S1 reports.

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

**1.2** Upload the notebooks from `notebooks/` to Drive and open each with
Colab. `00_setup` and `01_worker` are the campaign; `02_analysis` reads results;
`04_densify_diagnostic` is a one-off and is not needed to run the matrix.

Edit `DRIVE_ROOT` at the top of each **only** if your folder is not at
`/content/drive/MyDrive/e3dgsuw`.

---

## Phase 2 — `00_setup.ipynb`  *(once, ~20 min)*

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
| 5 **Verify rasterizer** | **9/9** | **stop** — see below |
| 6 Suites | ten × `PASSED` | stop and report |
| 7 Dataset | `21 / 29 / 20 / 18` | counts wrong → check the upload |
| 8 Undistort | ~5 min, `OPENCV → PINHOLE` ×4 | `colmap` missing → rerun the install cell |
| 9 Dense clouds | **~3 min total**, four `.ply`, each `points=… ok` | any `TOO HIGH` → lower `n_bud` |
| 10 Ledger | `108 runs  pending=108`, `budget : 200,000` | — |

**Cell 5 is the gate.** The rasterizer merge rests on one identity: for a
single Gaussian at depth `z` the probe gives `Z_raw = α·z`, so `Z_raw/α` must
recover `z` on every covered pixel. It was verified to ~1e-7 on sm_86 during
development, and 9/9 including T7 and T8, which assert where alpha's gradient
goes rather than what the renderer returns. If T3, T7 or T8 fails, **stop** —
every cell of the matrix is built on these and nothing downstream would be
trustworthy.

A session drop during cell 9 costs nothing: reopen and rerun the notebook, and
completed scenes are skipped.

---

## Phase 3 — S1, the A0 runs

Open `01_worker.ipynb`, run every cell, **edit nothing**.

Set `--max_minutes` to roughly **30 minutes below your real session limit**, so
the loop stops claiming new runs and exits cleanly instead of being killed
mid-run. The default 200 is conservative; if you reliably get 12-hour sessions,
use 690.

Repeat in fresh sessions until the ledger reports S1 complete.

### There is no budget to set

Earlier versions of this runbook had you derive `n_bud` from A0 after S1. That
is superseded. **The budget is fixed before the campaign** by the binding rule
— it must lie below the smallest primitive count any other enabled mechanism
produces — and `run_ledger init` reads it from `configs/cells.json`. See
`docs/ablation_design.md` §3.6.7.

Cell 7 is now a **check**, not an instruction: it reports A0's realised counts
against the budget and each dense cloud against it. If it ever says a cloud no
longer clears the budget, lower `n_bud` and re-run the affected cells — the
rule holds, the number follows the measurement.

---

## Phase 4 — the remaining stages

The same worker notebook, unchanged, until the ledger empties. Stages
self-sequence:

```
S2  A2            12 runs   the central hypothesis
S3  A1, A3        24 runs   remaining main effects
S4  A4, A5, A6    36 runs   the two-way interactions
S5  A7            12 runs   three-way term, from-above contrasts
S6  A0D           12 runs   supplementary: mechanism D against A0
```

---

## When the session disconnects  *(it will, repeatedly)*

Nothing is lost and nothing needs cleaning up by hand. An interrupted run
**restarts rather than resumes** — deliberately, because the checkpoint omits
the medium model, the codebooks and the loop's schedule flags, so resuming
would silently reinitialise β and produce a run that looks complete and is a
different experiment. Losing up to an hour is much cheaper than one invisibly
invalid cell.

**Step by step, in a fresh runtime:**

| | Do | Expect |
|---|---|---|
| 1 | Confirm the runtime is an **A100** | `Runtime → Change runtime type` |
| 2 | `01_worker.ipynb` sections **1–3** | git log line, `cwd: .../implementation` |
| 3 | Section **4** — rebuild extensions | `--- import check ---` at the end, ~5 min |
| 4 | Section **5** — re-stage the data | `staged in ~120s`, then ledger status |
| 5 | **Reclaim the dead row** (below) | `reclaimed 1 stale run(s)` |
| 6 | Section **6** | claims a run within a minute |

Steps 3 and 4 are not optional: Colab recycles the VM, so the compiled
extensions and `/content/data` are both gone.

### Step 5 in detail

The interrupted row is still marked `running`, with a heartbeat that stopped
when the VM died. The queue only reclaims rows idle for **45 minutes**, so if
you restart sooner it will skip that run and claim the next one, leaving the
first stuck. Force it:

```bash
!python -m tools.run_ledger reap --stale_minutes 2 --output_root "$DRIVE_ROOT"
```

Safe with a single worker. With several sessions running concurrently this
would steal a live run — that is exactly what the 45-minute default protects,
so do not lower it in the queue command itself.

### What you should see on the restarted run

```
[queue] reclaimed 1 stale run(s) from a dead session
[queue] === A0/Curasao/s0 (attempt 2) ===
[diagnostics] previous attempt kept as diagnostics.attempt1.csv
```

That last line matters. Each attempt owns its own `diagnostics.csv`; the dead
attempt's partial file is rotated aside rather than appended to. Two runs
concatenated into one file are non-monotonic in iteration while the *final row
stays correct*, which is what makes that corruption easy to miss — the
converged count reads fine and every trajectory is wrong.

### If the ledger itself disappears

`run_ledger.json` lives on Drive, where `os.replace` is not reliably atomic — a
write can leave neither the target nor its temp file. This happened once, mid
S1.

Every write now refreshes `run_ledger.json.bak` once the write has landed, and
a load restores from it automatically, printing:

```
[ledger] run_ledger.json is missing; restoring from run_ledger.json.bak.
```

Nothing to do. The backup holds the last state that reached disk, so at most
the final write is lost — one run's status, which a `reap` or a re-run
recovers.

If **both** files are gone, check for a stray `*.tmp` in `$DRIVE_ROOT` (that is
a complete ledger needing only a rename) and Drive's trash. Failing that,
`init --force` rebuilds the shape and you lose only the record of which runs
finished — the run directories themselves are untouched, so completed work can
be identified from `eval_metrics.json` on disk.

### If the same run keeps dying

After **three** attempts the ledger stops claiming it, and `status` marks it
`spent` with an `OUT OF ATTEMPTS` banner. Fix the cause, then:

```bash
!python -m tools.run_ledger reset --output_root "$DRIVE_ROOT"
```

`reset` clears attempts on failed runs. It does **not** touch completed ones —
that is `invalidate --cells <...> --reason <...>`, which is for when a code
change makes finished runs measure a different thing.

### Reduce how often this bites

Set `--max_minutes` **30 below your real session limit**. The loop then stops
claiming new work and exits cleanly rather than being killed mid-run, turning a
lost hour into a clean stop. Disconnections are routine over a campaign this
size; that one parameter is what makes them cheap.

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

## Diagnostics — run these alongside the campaign, not after it

Three tools read the run artifacts and need no GPU. A CPU runtime in a second
notebook is enough, and none of them interferes with a worker session.

```bash
python -m tools.collect_results  --output_root "$DRIVE_ROOT"   # everything, one view
python -m tools.medium_collapse  --output_root "$DRIVE_ROOT"   # is the physics intact?
python -m tools.spatial_extent   --output_root "$DRIVE_ROOT"   # is the geometry intact?
```

### `collect_results` — the single view

Merges `eval_metrics.json`, `model_size.json`, `run_config.json` and
`diagnostics.csv` into `analysis/results_runs.csv` (45 fields per run), per-scene
and per-cell aggregates, and a readable `results_summary.md`.

It is a *view*, not a source — everything recomputes from the artifacts, so run
it at any point and nothing depends on it having been run.

Three conventions it enforces rather than leaving to the reader: dispersion is
**never pooled across scenes** (the measured CV runs 6.0%–29.3% by scene), both
aggregation rules are emitted (frame counts are 3/4/3/3, so unweighted and
image-weighted differ), and `n = 1` reports `n/a` rather than `0.0` — the
standard deviation of one sample is undefined, and printing zero reads as
perfect reproducibility.

### `medium_collapse` — is the physics intact?

`beta_att` is unconstrained but its product with depth is clamped at zero, so a
channel driven negative has no gradient and is **frozen for the rest of
training**, with its attenuation fixed at `exp(0) = 1`. That is SeaSplat's D-1
"no medium" degeneracy reached one channel at a time.

**No fidelity metric can see it.** They score the composed image, which a model
with `Â ≈ 1` and a saturated backscatter term still fits. One run in this
campaign produced the highest test PSNR recorded *with two of three channels
dead*.

Run it after every stage. A collapsed channel invalidates any physical claim
about that run, and — because the collapse is seed-conditioned — a cell whose
seeds are mixed cannot be averaged at all.

### `spatial_extent` — is the geometry intact?

Bounding box, robust box, per-axis inflation, **occupancy** (the share of the box
containing anything), opacity-gated variants, and radial concentration.

Occupancy is the one to read. A box that is 99.96% empty is being held open by
material occupying almost none of it — which is what a detached floater cluster
looks like, and what SeaSplat's D-4 predicts. The gated variants separate
*rendered* pathology from *cosmetic* pathology.

Reads `point_cloud.ply`, written for **seed 0 only** unless
`--save_ply_all_seeds` was passed.

---

## What "done" looks like

- `run_ledger status` — 96 `done`, 0 pending, 0 failed
- `analysis/analysis_unweighted.json` and `analysis_image_weighted.json` written
- every run directory holds `run_config.json`, `diagnostics.csv`,
  `eval_metrics.json`, `compressed_30000/`, `train.log`
- all 108 runs report the same GPU in their manifests

That last one is not bookkeeping: the analysis warns if runs span devices,
because every conclusion in the study is a between-cell contrast.
