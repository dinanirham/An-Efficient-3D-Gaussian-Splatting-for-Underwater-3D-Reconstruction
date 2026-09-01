"""Generate the three Colab notebooks.

    python -m tools.make_notebooks           # writes into notebooks/

Notebooks are generated rather than hand-maintained because `.ipynb` is JSON
with embedded outputs: it diffs badly, merges worse, and invites drift between
near-identical copies. This script is the reviewable source of truth; the
notebooks are build artifacts.

**Three notebooks, by role -- not one per ablation.** A notebook per cell would
mean eight copies of the same setup, preprocessing and aggregation code, each
free to drift, which is exactly the failure the configuration layer was built
to eliminate. It also cannot express "S1 must finish before S2", because no
notebook can see the others. The ledger sequences the campaign globally, so the
worker notebook is identical every session and the cell comes from the ledger.
"""

from __future__ import annotations

import json
from pathlib import Path

NB_DIR = Path(__file__).resolve().parent.parent / "notebooks"

DRIVE_HEADER = '''\
from google.colab import drive
drive.mount('/content/drive')

# ---------------------------------------------------------------------------
# The one place paths are defined. Everything else derives from DRIVE_ROOT.
#
#   e3dgsuw/
#     dataset/     the four scenes (original) + undistorted/  <- created below
#     dense/       M1 clouds, with SHA-256 sidecars
#     runs/        <cell>/<scene>/s<seed>/  -- one run, all of it together
#     analysis/    analyse.py output, figures, tables
#     run_ledger.json
# ---------------------------------------------------------------------------
DRIVE_ROOT   = '/content/drive/MyDrive/e3dgsuw'
DATASET_DIR  = f'{DRIVE_ROOT}/dataset'
DATA_UNDIST  = f'{DATASET_DIR}/undistorted'
DENSE_DIR    = f'{DRIVE_ROOT}/dense'
ANALYSIS_DIR = f'{DRIVE_ROOT}/analysis'

# Training reads from local disk, not Drive: the scene loader pulls every image
# at startup, and Drive's FUSE layer makes that far slower than a single copy.
LOCAL_DATA   = '/content/data'

REPO_URL  = 'https://github.com/dinanirham/An-Efficient-3D-Gaussian-Splatting-for-Underwater-3D-Reconstruction.git'
REPO_DIR  = '/content/e3dgsuw'
IMPL_DIR  = f'{REPO_DIR}/implementation'
SCENES    = ['Curasao', 'IUI3-RedSea', 'JapaneseGradens-RedSea', 'Panama']

import os
assert os.path.isdir(DRIVE_ROOT), (
    f'{DRIVE_ROOT} not found. Check the folder name, or edit DRIVE_ROOT above.')
for d in (DATA_UNDIST, DENSE_DIR, f'{DRIVE_ROOT}/runs', ANALYSIS_DIR):
    os.makedirs(d, exist_ok=True)


def find_originals():
    """Locate the four scenes under dataset/, however they were arranged.

    Accepts the scenes directly under dataset/, or nested one level (e.g.
    dataset/SeathruNeRF_dataset/). Returns the directory that contains them.
    """
    candidates = [DATASET_DIR] + [
        os.path.join(DATASET_DIR, d) for d in sorted(os.listdir(DATASET_DIR))
        if os.path.isdir(os.path.join(DATASET_DIR, d)) and d != 'undistorted'
    ]
    for base in candidates:
        if all(os.path.isdir(os.path.join(base, s)) for s in SCENES):
            return base
    return None


DATA_ORIG = find_originals()
print('drive root :', DRIVE_ROOT)
print('originals  :', DATA_ORIG or 'NOT FOUND')
print('undistorted:', DATA_UNDIST)
'''

GPU_CHECK = '''\
import subprocess, torch
print(subprocess.run(['nvidia-smi','--query-gpu=name,memory.total,driver_version',
                      '--format=csv,noheader'], capture_output=True, text=True).stdout)
name = torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'NONE'
cap  = torch.cuda.get_device_capability(0) if torch.cuda.is_available() else (0,0)
print(f'torch {torch.__version__}  cuda {torch.version.cuda}  {name}  sm_{cap[0]}{cap[1]}')

# Every conclusion in this study is a between-cell contrast, and cells on
# different devices are not comparable. Stop now rather than produce a run
# that has to be discarded later.
assert 'A100' in name, f'Expected an A100, got {name!r}. Restart the runtime.'
'''

CLONE = '''\
import os, subprocess

# If the repository is private, create a fine-grained token with read access
# and set it here (or in Colab's Secrets). Leave as None for a public repo.
GITHUB_TOKEN = None

url = REPO_URL
if GITHUB_TOKEN:
    url = REPO_URL.replace('https://', f'https://{GITHUB_TOKEN}@')

if not os.path.exists(REPO_DIR):
    r = subprocess.run(['git','clone','--depth','1',url,REPO_DIR],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(
            'clone failed. If the repository is private, set GITHUB_TOKEN '
            f'above.\\n{r.stderr[-800:]}')
else:
    subprocess.run(['git','-C',REPO_DIR,'pull','--ff-only'], check=True)

os.chdir(IMPL_DIR)
print(subprocess.run(['git','-C',REPO_DIR,'log','--oneline','-1'],
                     capture_output=True, text=True).stdout.strip())
'''

BUILD = '''\
# Builds diff_gaussian_rasterization_ms and simple_knn against whatever torch
# Colab ships -- deliberately NOT installing our own, which would risk a
# mismatch between torch's CUDA and the toolkit the extensions compile with.
# Takes a few minutes; must be repeated each session.
%cd $IMPL_DIR
!bash tools/setup_colab.sh
'''

BUILD_CHECK = '''\
import importlib, torch
for m in ('diff_gaussian_rasterization_ms', 'simple_knn'):
    importlib.import_module(m)
print('extensions import OK  |  torch', torch.__version__,
      '| cuda', torch.version.cuda)
'''

def md(text: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": text.splitlines(True)}


def code(text: str) -> dict:
    return {"cell_type": "code", "execution_count": None, "metadata": {},
            "outputs": [], "source": text.splitlines(True)}


def notebook(cells: list[dict]) -> dict:
    return {
        "cells": cells,
        "metadata": {
            "accelerator": "GPU",
            "colab": {"provenance": [], "gpuType": "A100"},
            "kernelspec": {"display_name": "Python 3", "name": "python3"},
            "language_info": {"name": "python"},
        },
        "nbformat": 4,
        "nbformat_minor": 0,
    }


# ---------------------------------------------------------------------------
# 00 -- setup and preprocessing. Once per Drive; cells 1-4 also per session.
# ---------------------------------------------------------------------------

SETUP = notebook([
    md("""# 00 — Setup and preprocessing

Run **once per Drive**. Cells 1–4 also run at the start of every session,
because Colab discards the compiled extensions.

Order matters: undistortion must precede the dense clouds, because
`roma_init` uses the same scene reader.

Every cell is safe to re-run.
"""),
    md("## 1. Drive and paths"),
    code(DRIVE_HEADER),
    md("## 2. GPU — must be an A100"),
    code(GPU_CHECK),
    md("## 3. Clone the repository"),
    code(CLONE),
    md("## 4. Build the CUDA extensions  *(a few minutes, every session)*"),
    code(BUILD),
    code(BUILD_CHECK),
    md("""## 5. Verify the rasterizer merge

The gate. The whole merge rests on one identity: for a single Gaussian at depth
`z` the probe gives `Z_raw = α·z`, so `Z_raw/α` must recover `z` on every
covered pixel. Verified on sm_86 during development — this confirms it on the
A100 before anything is trained on top of it.
"""),
    code("!python -m tools.verify_rasterizer\n"),
    md("""## 6. The remaining self-checks

Seventy-six checks across ten suites. Cheap, and several encode findings that
are easy to reintroduce.
"""),
    code('''\
for t in ['verify_config_layer','verify_ledger','verify_metrics','verify_storage',
          'verify_analysis','verify_undistort','verify_dense_init','verify_simplify',
          'verify_quantize']:
    !python -m tools.{t} 2>&1 | tail -2
'''),
    md("""## 7. Locate the dataset

Expects the four scenes under `dataset/` — either directly, or nested one level
(e.g. `dataset/SeathruNeRF_dataset/`). Both layouts are accepted.
"""),
    code('''\
import os
assert DATA_ORIG, (
    f'Could not find the four scenes under {DATASET_DIR}.\\n'
    f'Expected {SCENES}\\n'
    f'either directly in dataset/ or one level down.\\n'
    f'Found: {sorted(os.listdir(DATASET_DIR))}')

for s in SCENES:
    d = [x for x in os.listdir(f'{DATA_ORIG}/{s}') if x.lower() == 'images_wb'][0]
    n = len(os.listdir(f'{DATA_ORIG}/{s}/{d}'))
    print(f'{s:24s} {n:3d} images   dir: {d}')
print('\\nExpect 21 / 29 / 20 / 18. Note IUI3-RedSea uses a capital-I Images_wb.')
'''),
    md("""## 8. COLMAP undistortion — **required**

All four scenes ship with the COLMAP **OPENCV** camera model and real
distortion coefficients, while the scene reader accepts only
PINHOLE/SIMPLE_PINHOLE. Without this step every run fails at scene load.

Idempotent — re-running this notebook will not resample the images again.
"""),
    code('''\
import shutil, subprocess
if shutil.which('colmap') is None:
    !apt-get -qq update > /dev/null 2>&1
    !apt-get -qq install -y colmap > /dev/null 2>&1
assert shutil.which('colmap'), (
    'colmap not installed. Try:  !apt-get install -y colmap\\n'
    'Undistortion cannot be skipped -- the scenes are OPENCV-model.')
print(subprocess.run(['colmap','-h'], capture_output=True, text=True).stdout[:150])
'''),
    code('''\
import subprocess, time
t0 = time.time()
for s in SCENES:
    print(f'--- {s} ---', flush=True)
    r = subprocess.run(['python','-m','source.undistort',
                        '--source', f'{DATA_ORIG}/{s}',
                        '--output', f'{DATA_UNDIST}/{s}'],
                       capture_output=True, text=True)
    print((r.stdout or r.stderr)[-700:], flush=True)
    if r.returncode != 0:
        raise RuntimeError(f'undistortion failed for {s}')
print(f'\\ntotal {(time.time()-t0)/60:.1f} min')
'''),
    code('''\
# Confirm every scene will now load.
import sys
from pathlib import Path
sys.path.insert(0, IMPL_DIR)
from source.undistort import verify_undistorted
for s in SCENES:
    i = verify_undistorted(Path(DATA_UNDIST) / s)
    n = len(list((Path(DATA_UNDIST) / s / 'images').iterdir()))
    print(f'{s:24s} {i["model"]:16s} {i["width"]}x{i["height"]}  {n} images')
'''),
    md("""## 9. Dense clouds — for the M1 cells (A1, A4, A5, A7)

One per scene, roughly 10–25 minutes each. The preset is a real experimental
choice: with densification disabled the primitive count can never grow, so a
cloud below the budget makes A4 collapse onto A1 and A7 onto A5. Compare these
counts against the budget once S1 has produced one.

Preprocessing wall-clock is **not** part of training time — report it
alongside, or A1's cost is understated relative to A0's.
"""),
    code('''\
import subprocess, time
for s in SCENES:
    out = f'{DENSE_DIR}/{s}.ply'
    if os.path.exists(out):
        print(f'{s}: already present, skipping'); continue
    print(f'--- {s} ---', flush=True)
    t0 = time.time()
    r = subprocess.run(['python','-m','source.roma_init',
                        '--source_path', f'{DATA_UNDIST}/{s}',
                        '--output',      out,
                        '--images',      'images',
                        '--preset',      'sparse',
                        '--seed',        '0'],
                       capture_output=True, text=True)
    print((r.stdout or r.stderr)[-900:], flush=True)
    print(f'{s}: {(time.time()-t0)/60:.1f} min')
'''),
    md("""## 10. Initialise the ledger

96 rows: 8 cells × 4 scenes × 3 seeds. Refuses to overwrite a campaign in
progress unless `--force`.
"""),
    code('''\
!python -m tools.run_ledger init   --output_root "$DRIVE_ROOT"
!python -m tools.run_ledger status --output_root "$DRIVE_ROOT"
'''),
    md("""---
**Next:** open `01_worker.ipynb` and run it. Repeat every session until the
ledger reports everything done.
"""),
])

# ---------------------------------------------------------------------------
# 01 -- worker. Run unchanged, every session.
# ---------------------------------------------------------------------------

WORKER = notebook([
    md("""# 01 — Worker

**Run this unedited, every session.** It claims whatever the ledger says is
next and runs it.

There is nothing to configure. The cell, scene and seed come from the ledger,
which enforces stage order and prerequisites globally — which is precisely why
this is one notebook rather than eight.

If a session dies mid-run, do nothing: the row is left with a stale heartbeat
and the next session reclaims it. Interrupted runs **restart** rather than
resume, deliberately — the checkpoint omits the medium model, the codebooks and
the loop's schedule flags, so resuming would silently reinitialise β and
produce a run that looks complete and is a different experiment.
"""),
    md("## 1. Drive and paths"),
    code(DRIVE_HEADER),
    md("## 2. GPU — must be an A100"),
    code(GPU_CHECK),
    md("## 3. Clone and build  *(a few minutes)*"),
    code(CLONE),
    code(BUILD),
    code(BUILD_CHECK),
    md("## 4. Verify the rasterizer"),
    code("!python -m tools.verify_rasterizer\n"),
    md("""## 5. Stage the dataset locally

The loader reads every image at startup; from Drive that is markedly slower
than one bulk copy.
"""),
    code('''\
import os, shutil, time
missing = [s for s in SCENES if not os.path.isdir(f'{DATA_UNDIST}/{s}')]
assert not missing, (
    f'Undistorted scenes missing: {missing}. Run 00_setup.ipynb first — the '
    f'scenes are OPENCV-model and will not load undistorted.')

os.makedirs(LOCAL_DATA, exist_ok=True)
t0 = time.time()
for s in SCENES:
    if not os.path.exists(f'{LOCAL_DATA}/{s}'):
        shutil.copytree(f'{DATA_UNDIST}/{s}', f'{LOCAL_DATA}/{s}')
print(f'staged in {time.time()-t0:.0f}s')
!python -m tools.run_ledger status --output_root "$DRIVE_ROOT"
'''),
    md("""## 6. Work

`--max_minutes` sits **below** the session limit so the loop stops claiming new
runs and exits cleanly rather than being killed mid-run. Raise it if your
sessions run longer.

Until the budget is set, every M2 cell is blocked and the queue says so — that
is expected during S1.
"""),
    code('''\
!python -m tools.run_queue \\
    --output_root "$DRIVE_ROOT" \\
    --data_root   "$LOCAL_DATA" \\
    --max_minutes 200
'''),
    md("""## 7. After S1 (A0) completes — set the budget

The primitive budget comes from A0's converged count, which no publication of
the baseline reports. Until it is set, A2, A4, A6 and A7 stay blocked.

Pick a value **below** the counts below so the budget actually binds. A budget
that does not bind makes A4 equivalent to A1 and A7 to A5, and a null
interaction measured in that state is a configuration artifact, not a finding.
"""),
    code('''\
import glob, csv, statistics
counts = []
for f in sorted(glob.glob(f'{DRIVE_ROOT}/runs/A0/*/s*/diagnostics.csv')):
    rows = list(csv.DictReader(open(f)))
    if rows:
        counts.append((f.split('/runs/')[1].rsplit('/', 1)[0],
                       int(rows[-1]['n_primitives'])))
for name, n in counts:
    print(f'{n:>12,}  {name}')
if counts:
    med = statistics.median(n for _, n in counts)
    print(f'\\nmedian {med:,.0f}   suggested budget ~{int(med*0.6):,} (60%)')
    print('Then run:')
    print(f'  !python -m tools.run_ledger set-budget <count> --output_root "$DRIVE_ROOT"')
else:
    print('No A0 diagnostics yet.')
'''),
    md("""---
Re-run this notebook in a fresh session to continue. Nothing changes between
sessions.
"""),
])

# ---------------------------------------------------------------------------
# 02 -- analysis
# ---------------------------------------------------------------------------

ANALYSIS = notebook([
    md("""# 02 — Analysis

Main effects in both directions, interactions against an explicit null, and
dispersion across seeds. No GPU needed.

Two rules the tool enforces, worth remembering when reading the output. Where
the from-below and from-above estimates of a main effect **disagree**, neither
may be quoted alone — the disagreement *is* the interaction. And nothing is
quotable without dispersion, so a partial campaign shows `nan` error bars and
`UNDETERMINED` rather than a confident-looking number.
"""),
    md("## 1. Drive and repo"),
    code(DRIVE_HEADER),
    code(CLONE),
    md("## 2. Campaign state"),
    code('!python -m tools.run_ledger status --output_root "$DRIVE_ROOT"\n'),
    md("""## 3. Contrasts

Quality metrics combine additively; ratio measures (storage, primitive count,
frame rate) combine multiplicatively, in log space.
"""),
    code('''\
!python -m tools.analyse \\
    --output_root "$DRIVE_ROOT" \\
    --weighting unweighted \\
    --json "$ANALYSIS_DIR/analysis_unweighted.json"
'''),
    code('''\
# Scene image counts are unequal (21/29/20/18), so the two weightings differ by
# more than many ablation differences in this literature. Reporting both
# removes an easy source of disagreement.
!python -m tools.analyse \\
    --output_root "$DRIVE_ROOT" \\
    --weighting image_weighted \\
    --json "$ANALYSIS_DIR/analysis_image_weighted.json"
'''),
    md("""## 4. The central hypothesis (H4)

Not a between-cell comparison: the depth normalisation constants and the medium
coefficients across the simplification boundary in A2. A jump in β at 15 000 is
the signature of the identifiability failure; its absorption inside the
re-identification burst is the signature of the fix.
"""),
    code('''\
import glob, csv
import matplotlib.pyplot as plt

paths = sorted(glob.glob(f'{DRIVE_ROOT}/runs/A2/*/s0/diagnostics.csv'))
if not paths:
    print('No A2 runs yet — that is stage S2.')
for p in paths:
    rows  = [r for r in csv.DictReader(open(p)) if r['beta_att_r']]
    if not rows:
        continue
    scene = p.split('/runs/A2/')[1].split('/')[0]
    it    = [int(r['iteration']) for r in rows]
    beta  = [float(r['beta_att_r']) for r in rows]
    zmax  = [float(r['z_max']) if r['z_max'] else float('nan') for r in rows]

    fig, ax = plt.subplots(1, 2, figsize=(11, 3.2))
    ax[0].plot(it, beta);  ax[0].axvline(15000, ls='--', c='r')
    ax[0].set_title(f'{scene}: beta_att (red channel)')
    ax[1].plot(it, zmax);  ax[1].axvline(15000, ls='--', c='r')
    ax[1].set_title('z_max — depth normalisation')
    for a in ax: a.set_xlabel('iteration')
    plt.tight_layout(); plt.savefig(f'{ANALYSIS_DIR}/h4_{scene}.png', dpi=140)
    plt.show()
'''),
    md("""## 5. Storage — per primitive as well as total

The codebook is a fixed cost, so the compression ratio grows with primitive
count. M2 reduces that count, so a ratio that fell because *N* fell would
otherwise read as quantization performing worse.
"""),
    code('''\
!python -m tools.analyse --output_root "$DRIVE_ROOT" \\
    --metric bytes_per_primitive --metric total_bytes --metric n_primitives_final
'''),
    md("""---
Outputs land in `analysis/` on Drive.
"""),
])

def main() -> int:
    NB_DIR.mkdir(parents=True, exist_ok=True)
    for name, nb in (("00_setup.ipynb", SETUP),
                     ("01_worker.ipynb", WORKER),
                     ("02_analysis.ipynb", ANALYSIS)):
        path = NB_DIR / name
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(nb, fh, indent=1, ensure_ascii=False)
            fh.write("\n")
        print(f"wrote {path}  ({len(nb['cells'])} cells)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
