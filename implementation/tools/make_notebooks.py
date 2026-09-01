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
#     dataset/SeathruNeRF_dataset/   original, as downloaded
#     dataset/undistorted/<scene>/   PINHOLE + sparse/0/  <- required
#     dense/<scene>.ply|.json        M1 clouds, SHA-256 sidecars
#     run_ledger.json                campaign state
#     runs/<cell>/<scene>/s<seed>/   one run, all of it together
#     analysis/                      analyse.py output, figures, tables
# ---------------------------------------------------------------------------
DRIVE_ROOT   = '/content/drive/MyDrive/e3dgsuw'
DATA_ORIG    = f'{DRIVE_ROOT}/dataset/SeathruNeRF_dataset'
DATA_UNDIST  = f'{DRIVE_ROOT}/dataset/undistorted'
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
for d in (DRIVE_ROOT, DATA_UNDIST, DENSE_DIR, ANALYSIS_DIR):
    os.makedirs(d, exist_ok=True)
print('drive root:', DRIVE_ROOT)
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

CLONE_BUILD = '''\
import os, subprocess
if not os.path.exists(REPO_DIR):
    subprocess.run(['git','clone','--depth','1',REPO_URL,REPO_DIR], check=True)
else:
    subprocess.run(['git','-C',REPO_DIR,'pull','--ff-only'], check=True)
os.chdir(IMPL_DIR)
print(subprocess.run(['git','-C',REPO_DIR,'log','--oneline','-1'],
                     capture_output=True, text=True).stdout)

# Builds diff_gaussian_rasterization_ms and simple_knn for sm_80, and installs
# only the dependencies Colab does not already ship.
!bash tools/setup_colab.sh
'''

VERIFY_RASTERIZER = '''\
# The gate. The whole rasterizer merge rests on one identity: for a single
# Gaussian at depth z the probe gives Z_raw = alpha*z, so Z_raw/alpha must
# recover z on every covered pixel. Verified on sm_86 during development; this
# confirms it on sm_80 before anything is trained on top of it.
%cd {IMPL_DIR}
!python -m tools.verify_rasterizer
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
# 00 -- setup, run once per Drive (and the build part once per session)
# ---------------------------------------------------------------------------

SETUP = notebook([
    md("""# 00 — Setup and preprocessing

Run this **once per Drive**. Cells 1–4 also run at the start of every session,
because Colab discards the compiled extensions; cells 5–8 are one-time.

Order matters: undistortion must precede the dense clouds, because
`roma_init` uses the same scene reader.
"""),
    md("## 1. Drive and paths"),
    code(DRIVE_HEADER),
    md("## 2. GPU — must be an A100"),
    code(GPU_CHECK),
    md("## 3. Clone and build"),
    code(CLONE_BUILD),
    md("## 4. Verify the rasterizer merge"),
    code(VERIFY_RASTERIZER.replace("{IMPL_DIR}", "$IMPL_DIR")),
    md("""## 5. The rest of the self-checks

Sixty-nine checks across nine suites. Cheap, and several encode findings that
are easy to reintroduce."""),
    code('''\
for t in ['verify_config_layer','verify_ledger','verify_metrics','verify_storage',
          'verify_analysis','verify_undistort','verify_dense_init','verify_simplify',
          'verify_quantize']:
    !python -m tools.{t} 2>&1 | tail -2
'''),
    md("""## 6. Dataset → Drive

Place `SeathruNeRF_dataset/` under `dataset/` on Drive once. The four scenes
are Curasao (21 images), IUI3-RedSea (29, note the capital-I `Images_wb`),
JapaneseGradens-RedSea (20) and Panama (18)."""),
    code('''\
import os
missing = [s for s in SCENES if not os.path.exists(f'{DATA_ORIG}/{s}')]
assert not missing, (
    f'Missing scenes under {DATA_ORIG}: {missing}\\n'
    f'Upload SeathruNeRF_dataset there first.')
for s in SCENES:
    d = [x for x in os.listdir(f'{DATA_ORIG}/{s}') if x.lower()=='images_wb'][0]
    n = len(os.listdir(f'{DATA_ORIG}/{s}/{d}'))
    print(f'{s:24s} {n:3d} images   image dir: {d}')
'''),
    md("""## 7. COLMAP undistortion — **required**

All four scenes ship with the COLMAP **OPENCV** camera model and real
distortion coefficients, while the scene reader accepts only
PINHOLE/SIMPLE_PINHOLE. Without this step every run fails at scene load.

The step is idempotent, so re-running this notebook is harmless."""),
    code('''\
!apt-get -qq install colmap > /dev/null 2>&1 || pip install -q pycolmap
import subprocess
for s in SCENES:
    print(f'--- {s} ---')
    r = subprocess.run(['python','-m','source.undistort',
                        '--source', f'{DATA_ORIG}/{s}',
                        '--output', f'{DATA_UNDIST}/{s}'],
                       capture_output=True, text=True)
    print(r.stdout[-800:] or r.stderr[-800:])
'''),
    code('''\
# Confirm every scene will now load.
from pathlib import Path
import sys; sys.path.insert(0, IMPL_DIR)
from source.undistort import verify_undistorted
for s in SCENES:
    info = verify_undistorted(Path(DATA_UNDIST)/s)
    print(f'{s:24s} {info["model"]:16s} {info["width"]}x{info["height"]}')
'''),
    md("""## 8. Dense clouds — for the M1 cells (A1, A4, A5, A7)

One per scene. The preset is a real experimental choice: with densification
disabled the primitive count can never grow, so a cloud below the budget makes
A4 collapse onto A1 and A7 onto A5. Check the reported point counts against the
budget once S1 has produced one.

Preprocessing wall-clock is **not** part of training time — report it
alongside, or A1's cost is understated relative to A0's."""),
    code('''\
import subprocess
for s in SCENES:
    print(f'--- {s} ---')
    r = subprocess.run(['python','-m','source.roma_init',
                        '--source_path', f'{DATA_UNDIST}/{s}',
                        '--output',      f'{DENSE_DIR}/{s}.ply',
                        '--images',      'images',
                        '--preset',      'sparse',
                        '--seed',        '0'],
                       capture_output=True, text=True)
    print(r.stdout[-900:] or r.stderr[-900:])
'''),
    md("""## 9. Initialise the ledger

96 rows: 8 cells × 4 scenes × 3 seeds. Refuses to overwrite an existing
campaign unless forced."""),
    code('''\
!python -m tools.run_ledger init --output_root "$DRIVE_ROOT"
!python -m tools.run_ledger status --output_root "$DRIVE_ROOT"
'''),
    md("""---
Next: open **01_worker.ipynb** and run it. Repeat it every session until the
ledger reports everything done.
"""),
])

# ---------------------------------------------------------------------------
# 01 -- worker, run unchanged every session
# ---------------------------------------------------------------------------

WORKER = notebook([
    md("""# 01 — Worker

**Run this unedited, every session, as many times as you like.** It claims
whatever the ledger says is next and runs it.

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
    md("## 3. Clone and build"),
    code(CLONE_BUILD),
    md("## 4. Verify the rasterizer, then the dataset"),
    code(VERIFY_RASTERIZER.replace("{IMPL_DIR}", "$IMPL_DIR")),
    code('''\
# Copy the undistorted scenes to local disk. The loader reads every image at
# startup; from Drive that is markedly slower than one bulk copy.
import os, shutil, time
os.makedirs(LOCAL_DATA, exist_ok=True)
t0 = time.time()
for s in SCENES:
    dst = f'{LOCAL_DATA}/{s}'
    if not os.path.exists(dst):
        shutil.copytree(f'{DATA_UNDIST}/{s}', dst)
print(f'dataset staged locally in {time.time()-t0:.0f}s')
!python -m tools.run_ledger status --output_root "$DRIVE_ROOT"
'''),
    md("""## 5. Work

`--max_minutes` should sit **below** the session limit so the loop stops
claiming new runs and exits cleanly rather than being killed mid-run.

If the budget has not been set yet, every M2 cell is blocked and the queue will
say so — that is expected until S1 (A0) completes."""),
    code('''\
!python -m tools.run_queue \\
    --output_root "$DRIVE_ROOT" \\
    --data_root   "$LOCAL_DATA" \\
    --max_minutes 200
'''),
    md("""## 6. After S1 completes — set the budget

The primitive budget comes from A0's converged count, which no publication of
the baseline reports. Until it is set, every M2 cell (A2, A4, A6, A7) stays
blocked.

A budget that does not bind makes A4 equivalent to A1 and A7 to A5, and a null
interaction measured in that state is a configuration artifact rather than a
finding — so check the counts before setting it."""),
    code('''\
import glob, csv
counts = []
for f in sorted(glob.glob(f'{DRIVE_ROOT}/runs/A0/*/s*/diagnostics.csv')):
    rows = list(csv.DictReader(open(f)))
    if rows:
        counts.append((f.split('/runs/')[1], int(rows[-1]['n_primitives'])))
for name, n in counts:
    print(f'{n:>10,}  {name}')
if counts:
    import statistics
    print(f'\\nmedian {statistics.median(n for _, n in counts):,.0f}')
    print('Set a budget BELOW these, so it binds:')
    print(f'  !python -m tools.run_ledger set-budget <count> --output_root "$DRIVE_ROOT"')
'''),
    md("""---
Re-run this notebook in a fresh session to continue. Nothing needs changing
between sessions.
"""),
])

# ---------------------------------------------------------------------------
# 02 -- analysis
# ---------------------------------------------------------------------------

ANALYSIS = notebook([
    md("""# 02 — Analysis

Main effects in both directions, interactions against an explicit null, and
dispersion across seeds.

Two rules the tool enforces, worth remembering when reading the output: where
the from-below and from-above estimates of a main effect **disagree**, neither
may be quoted alone — the disagreement is the interaction. And nothing is
quotable without dispersion, so a partial campaign will show `nan` error bars
and `UNDETERMINED` rather than a confident-looking number.
"""),
    md("## 1. Drive and repo"),
    code(DRIVE_HEADER),
    code(CLONE_BUILD.replace("!bash tools/setup_colab.sh",
                             "# no build needed: analysis is pure Python")),
    md("## 2. Campaign state"),
    code('!python -m tools.run_ledger status --output_root "$DRIVE_ROOT"\n'),
    md("""## 3. Contrasts

Quality metrics combine additively; ratio measures (storage, primitive count,
frame rate) combine multiplicatively, in log space."""),
    code('''\
!python -m tools.analyse \\
    --output_root "$DRIVE_ROOT" \\
    --weighting unweighted \\
    --json "$ANALYSIS_DIR/analysis_unweighted.json"
'''),
    code('''\
# Scene image counts are unequal (21/29/20/18), so the two weightings differ.
# Reporting both removes an easy source of disagreement.
!python -m tools.analyse \\
    --output_root "$DRIVE_ROOT" \\
    --weighting image_weighted \\
    --json "$ANALYSIS_DIR/analysis_image_weighted.json"
'''),
    md("""## 4. The central hypothesis (H4)

Not a between-cell comparison: the depth normalisation constants and the medium
coefficients across the simplification boundary in A2. A large jump in β at
15 000 is the signature of the identifiability failure; its absorption inside
the re-identification burst is the signature of the fix."""),
    code('''\
import glob, csv
import matplotlib.pyplot as plt

paths = sorted(glob.glob(f'{DRIVE_ROOT}/runs/A2/*/s0/diagnostics.csv'))
if not paths:
    print('No A2 runs yet — this is the S2 stage.')
for p in paths:
    rows = [r for r in csv.DictReader(open(p)) if r['beta_att_r']]
    if not rows:
        continue
    it  = [int(r['iteration']) for r in rows]
    br  = [float(r['beta_att_r']) for r in rows]
    zmx = [float(r['z_max']) if r['z_max'] else None for r in rows]
    scene = p.split('/runs/A2/')[1].split('/')[0]

    fig, ax = plt.subplots(1, 2, figsize=(11, 3.2))
    ax[0].plot(it, br); ax[0].axvline(15000, ls='--', c='r')
    ax[0].set_title(f'{scene}: beta_att (red)'); ax[0].set_xlabel('iteration')
    ax[1].plot(it, [z for z in zmx if z is not None][:len(it)])
    ax[1].axvline(15000, ls='--', c='r')
    ax[1].set_title('z_max (depth normalisation)'); ax[1].set_xlabel('iteration')
    plt.tight_layout(); plt.show()
'''),
    md("## 5. Storage — per primitive as well as total"),
    code('''\
# A ratio that fell because N fell would otherwise read as quantization
# performing worse. The codebook is a fixed cost, so the ratio grows with N.
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
