"""Generate the Colab notebooks.

    python -m tools.make_notebooks           # writes into notebooks/

Notebooks are generated rather than hand-maintained because `.ipynb` is JSON
with embedded outputs: it diffs badly, merges worse, and invites drift between
near-identical copies. This script is the reviewable source of truth; the
notebooks are build artifacts.

**By role, not one per ablation.** A notebook per cell would
mean eight copies of the same setup, preprocessing and aggregation code, each
free to drift, which is exactly the failure the configuration layer was built
to eliminate. It also cannot express "S1 must finish before S2", because no
notebook can see the others. The ledger sequences the campaign globally, so the
worker notebook is identical every session and the cell comes from the ledger.

04 is the exception to the role rule: it is a one-off diagnostic, kept apart
because running it inside the worker produced a notebook carrying outputs
from four sessions in an order that no longer matched the execution counts.
A diagnostic whose provenance is unclear is not evidence.
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

# Export them so the `!` cells below resolve "$DRIVE_ROOT" as a real shell
# variable. Relying on IPython to substitute notebook variables into magics
# works until it doesn't, and when it doesn't it substitutes nothing and the
# command runs against a silently truncated path rather than failing.
os.environ.update(
    DRIVE_ROOT=DRIVE_ROOT, DATASET_DIR=DATASET_DIR, DATA_UNDIST=DATA_UNDIST,
    DENSE_DIR=DENSE_DIR, ANALYSIS_DIR=ANALYSIS_DIR, LOCAL_DATA=LOCAL_DATA,
    REPO_DIR=REPO_DIR, IMPL_DIR=IMPL_DIR,
)


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

# verify_undistort's T1 -- the check that would catch the undistortion gap --
# reads the *original* dataset. Point it at wherever it actually landed on
# Drive, or T1 reports "dataset not found" and the one check that matters here
# quietly stops testing anything.
if DATA_ORIG:
    os.environ['E3DGSUW_DATASET'] = DATA_ORIG

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

# Private repo? Add a Colab secret named GITHUB_TOKEN (key icon in the left
# sidebar) with a fine-grained read token, and toggle notebook access on.
# Read from Secrets rather than pasted into the cell: a pasted token is saved
# inside the .ipynb, which then travels wherever the notebook does.
GITHUB_TOKEN = None
try:
    from google.colab import userdata
    GITHUB_TOKEN = userdata.get('GITHUB_TOKEN') or None
    print('GITHUB_TOKEN: loaded from Colab Secrets')
except ImportError:
    pass                                  # not running under Colab
except Exception as e:                    # secret absent, or access not granted
    print(f'GITHUB_TOKEN: not available ({type(e).__name__}) -- '
          'fine for a public repo')

url = REPO_URL
if GITHUB_TOKEN:
    url = REPO_URL.replace('https://', f'https://{GITHUB_TOKEN}@')

# Never let git fall back to an interactive credential prompt: in a notebook it
# hangs the cell indefinitely with nothing on screen to say why.
env = {**os.environ, 'GIT_TERMINAL_PROMPT': '0'}


def _redact(s):
    """Strip the token from git output -- git echoes the remote URL on failure,
    and notebook outputs are saved to the file and shared with it."""
    return s.replace(GITHUB_TOKEN, '***') if GITHUB_TOKEN else s


if os.path.isdir(REPO_DIR) and not os.path.isdir(f'{REPO_DIR}/.git'):
    raise RuntimeError(
        f'{REPO_DIR} exists but is not a git checkout -- probably a clone that '
        f'died partway. Delete it and re-run this cell.')

if not os.path.exists(REPO_DIR):
    r = subprocess.run(['git','clone','--depth','1',url,REPO_DIR],
                       capture_output=True, text=True, env=env)
    if r.returncode != 0:
        raise RuntimeError(
            'clone failed. If the repository is private, add a GITHUB_TOKEN '
            'secret in Colab and grant this notebook access.\\n'
            f'{_redact(r.stderr)[-800:]}')
else:
    # Repoint the remote before pulling. The stored URL was written by an
    # earlier clone, which may have run without a token (or with a stale one);
    # injecting the token into `url` alone never reaches the pull.
    subprocess.run(['git','-C',REPO_DIR,'remote','set-url','origin',url],
                   check=True, env=env)
    r = subprocess.run(['git','-C',REPO_DIR,'pull','--ff-only'],
                       capture_output=True, text=True, env=env)
    if r.returncode != 0:
        raise RuntimeError(
            'pull failed. If the repository is private, check the GITHUB_TOKEN '
            'secret is set and this notebook has access.\\n'
            f'{_redact(r.stderr)[-800:]}')

# Fail here, naming the directory, rather than letting a later cell run from
# whatever the working directory happened to be.
assert os.path.isdir(IMPL_DIR), (
    f'clone produced no {IMPL_DIR}. Contents of {REPO_DIR}: '
    f'{sorted(os.listdir(REPO_DIR)) if os.path.isdir(REPO_DIR) else "missing"}')

os.chdir(IMPL_DIR)
print(subprocess.run(['git','-C',REPO_DIR,'log','--oneline','-1'],
                     capture_output=True, text=True).stdout.strip())
print('cwd:', os.getcwd())
'''

BUILD = '''\
# Builds diff_gaussian_rasterization_ms and simple_knn against whatever torch
# Colab ships -- deliberately NOT installing our own, which would risk a
# mismatch between torch's CUDA and the toolkit the extensions compile with.
# Takes a few minutes; must be repeated each session.
#
# chdir explicitly rather than via `%cd $IMPL_DIR`: a magic whose variable fails
# to expand reports the *current* directory and continues, so the build then
# runs from the wrong place and fails two steps later with a bare
# "tools/setup_colab.sh: No such file or directory".
import os
assert os.path.isdir(IMPL_DIR), (
    f'{IMPL_DIR} not found -- run the "Clone the repository" cell above first.')
os.chdir(IMPL_DIR)
print('building in', os.getcwd())
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
import json as _j
N_BUD = _j.load(open(f'{IMPL_DIR}/configs/cells.json'))['defaults']['n_bud']
print(f'n_bud = {N_BUD:,} (from configs/cells.json)')
failures = []
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
                        '--preset',      'dense',
                        '--seed',        '0'],
                       capture_output=True, text=True)
    print(r.stdout[-900:], flush=True)

    # Check the exit code, and print stderr on its own. `r.stdout or r.stderr`
    # hides the traceback whenever stdout is non-empty -- and it always is
    # here, because the scene reader chatters before anything can fail. That
    # combination reported four crashed runs as four successes.
    if r.returncode != 0:
        print(f'!!! {s} FAILED (exit {r.returncode})', flush=True)
        print(r.stderr[-1500:], flush=True)
        failures.append(s)
    elif not os.path.exists(out):
        print(f'!!! {s} exited 0 but wrote no {out}', flush=True)
        failures.append(s)
    else:
        n = os.path.getsize(out) / 1e6
        print(f'{s}: {(time.time()-t0)/60:.1f} min   {out}  {n:.1f} MB')
        # The budget must lie below this, or M2 is inert under M1 and A4
        # collapses onto A1 (ablation_design.md 5). Preflight refuses such a
        # run, but seeing it here costs nothing and saves a wasted queue entry.
        import json as _json
        _side = out.replace('.ply', '.json')
        if os.path.exists(_side):
            _n = _json.load(open(_side)).get('kept')
            if _n:
                _ok = 'ok' if N_BUD < _n else 'TOO HIGH -- lower n_bud'
                print(f'    points={_n:,}   n_bud={N_BUD:,}   {_ok}')

if failures:
    raise RuntimeError(
        f'dense-cloud generation failed for {failures}. The M1 cells '
        f'(A1/A4/A5/A7) cannot run without these. A0/A2/A3/A6 are unaffected, '
        f'so S1 can still proceed.')
print('\\nall dense clouds present')
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
    md("""## 7. After S1 — check the budget against what A0 actually built

**There is nothing to set here.** `n_bud` is fixed ahead of the campaign by the
binding rule — it must lie below the smallest count any other enabled mechanism
produces — and `run_ledger init` reads it from `configs/cells.json`. It is not
derived from A0.

This cell is a check, because the rule was applied to *estimated* cloud sizes.
A0's realised counts tell you how much room M2 actually has, and section 9 of
`00_setup` reports the clouds. If the budget no longer sits below them, lower
it and re-run the affected cells — the rule holds, the number follows the
measurement.
"""),
    code('''\
import glob, csv, json, os, statistics
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
    led = json.load(open(f'{DRIVE_ROOT}/run_ledger.json'))
    bud = led.get('n_bud')
    print(f'\\nA0 median {med:,.0f}')
    if bud:
        print(f'n_bud     {bud:,}  (from {led.get("n_bud_source") or "set-budget"})')
        print(f'M2 would remove {100 * (1 - bud / med):.1f}% of A0')
        for path in sorted(glob.glob(f'{DENSE_DIR}/*.json')):
            side = json.load(open(path))
            pts = side.get('kept')
            if pts:
                ok = 'binds' if bud < pts else 'DOES NOT BIND -- lower n_bud'
                print(f'  {os.path.basename(path)[:-5]:<26} cloud={pts:>9,}  {ok}')
    else:
        print('n_bud NOT SET -- configs/cells.json has no defaults.n_bud, so '
              'every m2 cell is blocked.')
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

# ---------------------------------------------------------------------------
# 04 -- the densification diagnostic.  Self-contained on purpose.
#
# This lives apart from the worker because running it there produced a notebook
# carrying outputs from four different sessions, in an order that no longer
# matched the execution counts.  A diagnostic whose provenance is unclear is
# not evidence.  Nothing here touches the ledger or writes into runs/.
# ---------------------------------------------------------------------------

STAGE_ONE_SCENE = R"""import os, shutil, time
t0 = time.time()
os.makedirs(LOCAL_DATA, exist_ok=True)
for s in SCENES:
    src, dst = f'{DATA_UNDIST}/{s}', f'{LOCAL_DATA}/{s}'
    if not os.path.isdir(dst):
        shutil.copytree(src, dst)
print(f'staged in {time.time() - t0:.0f}s')

scene = f'{LOCAL_DATA}/Curasao'
assert os.path.isfile(f'{scene}/sparse/0/cameras.bin'), 'staging incomplete'
print('scene ok:', scene)
"""

REF_SETUP = R"""!rm -rf /content/seasplat_ref
!git clone -q --recursive https://github.com/dxyang/seasplat.git /content/seasplat_ref
!pip install -q /content/seasplat_ref/submodules/diff-gaussian-rasterization
!cd /content/seasplat_ref && git log -1 --format="reference at %H  %ad" --date=short
!python -m tools.instrument_reference /content/seasplat_ref
"""

REPLICATE = R"""!python -m tools.replicate_baseline \
  --data_root "$LOCAL_DATA" --ref_root /content/seasplat_ref \
  --out /content/replication --repeats 3 --iterations 16000
"""

READ_VERDICT = R"""import json
r = json.load(open('/content/replication/replication.json'))
for side in ('ours', 'ref'):
    d = r[side]
    if not d.get('n'):
        print(f"{d['name']}: no successful runs")
        continue
    sd = f"{d['sd']:,.0f}" if d['sd'] is not None else '-'
    print(f"{d['name']:<20} n={d['n']}  mean={d['mean']:>12,.0f}  sd={sd:>10}"
          f"  spread={d['spread_pct']:.1f}%")
    print(f"{'':<20} {', '.join(f'{x:,}' for x in d['runs'])}")
print('\nverdict:', r['verdict'])
if r['failures']:
    print('failures:', r['failures'])
"""

PAIRED_OURS = R"""!cd "$IMPL_DIR" && python train.py \
  -s "$LOCAL_DATA"/Curasao --images images \
  --model_path /content/diag_ours --cell A0 --seed 2 \
  --iterations 16000 --test_iterations 16000 \
  --save_iterations 16000 --checkpoint_iterations 16000 \
  2>&1 | tee /content/diag_ours_full.txt \
       | grep --line-buffered -a "\[densify\]" | tee /content/diag_ours.txt
"""

PAIRED_REF = R"""!cd /content/seasplat_ref && python train.py \
  -s "$LOCAL_DATA"/Curasao --images images --exp diag \
  --iterations 16000 --do_seathru --seathru_from_iter 10000 --eval --seed 2 \
  --test_iterations 16000 --save_iterations 16000 \
  --checkpoint_iterations 16000 \
  2>&1 | tee /content/diag_ref_full.txt \
       | grep --line-buffered -a "\[densify\]" | tee /content/diag_ref.txt
"""

SAVE_EVIDENCE = R"""import glob, os, shutil

# Copy the evidence, not the artifacts.  Each replication run is a real
# training run with --model_path under /content/replication, so it leaves
# rendered eval images there -- ~2 MB each, hundreds of them.  A copytree of
# the whole directory put several GB of PNGs on Drive last time.  What is worth
# keeping is the summary and the logs.
out = f'{DRIVE_ROOT}/analysis/baseline_replication'
os.makedirs(out, exist_ok=True)

kept = []
for src in (glob.glob('/content/replication/*.json')
            + glob.glob('/content/replication/*.log')
            + [f'/content/{f}' for f in ('diag_ours.txt', 'diag_ref.txt',
                                         'diag_ours_full.txt', 'diag_ref_full.txt')]):
    if os.path.isfile(src):
        shutil.copy(src, f'{out}/{os.path.basename(src)}')
        kept.append(os.path.basename(src))

print('saved to', out)
total = 0
for f in sorted(kept):
    n = os.path.getsize(f'{out}/{f}')
    total += n
    print(f'  {f:<30} {n / 1024:8.1f} KB')
print(f'  {"total":<30} {total / 1024:8.1f} KB')
"""


DIAG_ITERS = 16000
REPEATS = 3

DIAGNOSTIC = notebook([
    md("""# 04 — Baseline replication and densification diagnostic

**The question.** Is A0 distinguishable from vanilla SeaSplat?

It was chased through four hypotheses using one run per side. Two of the fixes
were real — CD-22 routed alpha's gradient into density control, CD-23 kept
depth out of it — and the count moved 636k → 3.0M → 4.5M. Then a second run of
each, with nothing functional changed, came back:

| | runs | spread |
|---|---|---|
| vanilla SeaSplat | 4,788,960 / 4,085,219 | 17% |
| ours (A0) | 3,025,374 / 4,510,298 | 49% |

`n_primitives` is a high-variance outcome. The rasterizer backward accumulates
atomically, so a primitive lands either side of `densify_grad_threshold` from
run to run, and that changes the population feeding the next event — 144 times
over. So **a single-run ratio carries no information at this scale**, and the
residual still being chased after CD-23 sat inside the noise.

This notebook measures the spread on both sides instead.

**It never touches the ledger.** These are truncated single-scene runs; the
campaign must not record them as cells.

Budget: ~2.5 hours. Run top to bottom.
"""),
    md("## 1. Drive and paths"),
    code(DRIVE_HEADER),
    md("## 2. GPU — must be an A100"),
    code(GPU_CHECK),
    md("## 3. Clone and build"),
    code(CLONE),
    code(BUILD),
    code(BUILD_CHECK),
    md("""## 4. Stage the dataset locally

**Not optional.** Colab recycles the VM, so `/content/data` is empty in a fresh
session and every run below dies at scene load — ours naming the missing file,
the reference with `Could not recognize scene type!`.
"""),
    code(STAGE_ONE_SCENE),
    md("""## 5. Reference: clean checkout, build, instrument

**The `rm -rf` is deliberate.** `instrument_reference` refuses to patch a tree
whose `densify_and_prune` does not match pristine upstream byte-for-byte — so a
tree instrumented in an earlier session is rejected, correctly, and the
reference then runs without the breakdown. That happened once and cost a
25-minute run. Starting clean every session is cheaper than diagnosing it
again.
"""),
    code(REF_SETUP),
    md("""## 6. Confirm the rasterizers still agree

Seconds, and it guards everything below: if the two forks ever stop matching
here, any difference downstream is explained by that instead.
"""),
    code("!python -m tools.compare_rasterizers\n"),
    md("""## 7. Replication — the main event, ~2.2 h

Both implementations, same scene, same schedule, three repeats each, reporting
both distributions.

Split across sessions with `--skip_ours` / `--skip_ref` if your session limit
is tight; `replication.json` is written either way.

The reference accepts `--seed` but seeds only the CPU generator —
`torch.cuda.manual_seed_all` is our addition — so its GPU draws vary
regardless. That is not a flaw in the experiment; it is the quantity being
measured.
"""),
    code(REPLICATE),
    md("""## 8. Read the verdict

**Overlapping ranges** → A0 and vanilla SeaSplat are not distinguishable by
primitive count, CD-22 and CD-23 did their job, and baseline fidelity is
closed.

**Disjoint ranges** → a real difference remains, and section 9 is where to look
for it.

Either way the two `spread` figures matter beyond this question: every
efficiency contrast in the thesis has to clear that dispersion.
"""),
    code(READ_VERDICT),
    md("""## 9. Optional — one paired run, event by event

Worth running only if section 8 says **DISTINGUISHABLE**. It compares a single
pair of runs at every densification event and reports the first quantity to
diverge: `over_grad` means the gradient signal differs, `clone`/`split` at
equal `over_grad` means the decision boundary does, `prune` means pruning —
with the alpha/screen/world split naming the reason and the opacity
percentiles alongside.

Single runs of a noisy quantity, so read it as *where* they differ, never as
*whether*. Section 8 answers whether.

The `grep` has no `^` anchor and passes `-a`: tqdm writes its bar with a
carriage return and no trailing newline, so our line is appended to it and an
anchored pattern silently matches nothing.
"""),
    code(PAIRED_OURS),
    code(PAIRED_REF),
    code("!python -m tools.compare_densification /content/diag_ours.txt /content/diag_ref.txt\n"),
    md("""## 10. Keep the evidence

`/content` dies with the session, and section 7 is over two hours of
measurement.
"""),
    code(SAVE_EVIDENCE),
])


def main() -> int:
    NB_DIR.mkdir(parents=True, exist_ok=True)
    for name, nb in (("00_setup.ipynb", SETUP),
                     ("01_worker.ipynb", WORKER),
                     ("02_analysis.ipynb", ANALYSIS),
                     ("04_densify_diagnostic.ipynb", DIAGNOSTIC)):
        path = NB_DIR / name
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(nb, fh, indent=1, ensure_ascii=False)
            fh.write("\n")
        print(f"wrote {path}  ({len(nb['cells'])} cells)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
