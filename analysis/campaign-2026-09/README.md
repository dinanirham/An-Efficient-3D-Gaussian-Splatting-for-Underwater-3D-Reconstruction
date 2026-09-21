# Campaign 2026-09 — analysis inputs

The 120-run campaign: SS + A0–A7 + A0D, 4 scenes × 3 seeds, one code version
(`3f2af29` or later). Everything here is produced on Colab by `02_analysis`
and the ledger; nothing is edited by hand.

**Do not mix with the files at the repository root** — those are the earlier
74-run campaign (pre-CD-27, mixed code versions), kept for the two-campaign
comparison and nothing else.

## Layout

```
analysis/campaign-2026-09/
  README.md                        this file
  run_ledger.json                  completion matrix, attempts, wall-clock, failures
  results_runs.csv                 the master table, one row per run (120)
  results_by_scene.csv             mean / sd per cell per scene
  results_by_cell.csv              mean per cell
  results_summary.md
  analysis_unweighted.json         factorial contrasts, unweighted scene mean
  analysis_image_weighted.json     factorial contrasts, image-weighted
  medium_collapse.json             collapse verdicts + CD-27 dispersion ratios
  spatial_extent.csv               geometry per run
  j_consistency.json               J-hat self-consistency, M3 cells
  check_margin.txt                 the SS-vs-A0 verdict, four scenes (paste stdout)
  diagnostics/
    A2_Curasao_s0.csv              diagnostics.csv for the 48 M2 runs,
    A2_Curasao_s1.csv              renamed <cell>_<scene>_s<seed>.csv
    ...                            (A2, A4, A6, A7 × 4 scenes × 3 seeds)
```

## Producing it

On Colab, after A0D completes, run `02_analysis.ipynb` top to bottom. Then:

```python
import shutil, glob, os
SRC = f'{DRIVE_ROOT}/analysis'
# 1. the collectors' outputs
for f in ['results_runs.csv','results_by_scene.csv','results_by_cell.csv',
          'results_summary.md','analysis_unweighted.json',
          'analysis_image_weighted.json','medium_collapse.json',
          'spatial_extent.csv','j_consistency.json']:
    print(f, os.path.getsize(f'{SRC}/{f}') if os.path.exists(f'{SRC}/{f}') else 'MISSING')
# 2. the ledger
shutil.copy(f'{DRIVE_ROOT}/run_ledger.json', SRC)
# 3. the M2 diagnostics, renamed so the path is in the filename
os.makedirs(f'{SRC}/diagnostics', exist_ok=True)
for p in glob.glob(f'{DRIVE_ROOT}/runs/A[2467]/*/s*/diagnostics.csv'):
    cell, scene, seed = p.split('/runs/')[1].split('/')[:3]
    shutil.copy(p, f'{SRC}/diagnostics/{cell}_{scene}_{seed}.csv')
# 4. the margin verdict, captured
!python -m tools.measure_reference --check_margin --output_root "$DRIVE_ROOT" > "$SRC/check_margin.txt"
!zip -qr campaign-2026-09.zip "$SRC" && ls -la campaign-2026-09.zip
```

Download the zip, unpack it here. One bundle, one place.

Artifact source: `FINDINGS.html` renders FINDINGS.md as a page; published at
https://claude.ai/artifact/RjJZsWg1CXVpg1oMmfCedj (same link as the 48-run page it replaced).
