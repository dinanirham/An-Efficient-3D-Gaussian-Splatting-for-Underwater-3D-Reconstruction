# Reproducibility notes

What is pinned, what varies, and what cannot be made deterministic. Written on
the assumption that the reader is trying to work out whether two numbers are
comparable.

Companions: `experiment_plan.md` (what runs), `ablation_design.md` (how to read
the contrasts).

---

## 1. Seeding

Every run takes an explicit `--seed`; preflight **refuses to start without
one**, because the upstream default draws from OS entropy and would make
dispersion across seeds incidental rather than measurable.

`safe_state` now also calls `torch.cuda.manual_seed_all`. Upstream did not, so
`--seed` left every GPU-side draw uncontrolled — including the initial
backscatter coefficients and water colour, which matter because the "no medium"
degeneracy is a *global optimum* of the photometric loss and the starting point
decides whether the run escapes it.

### Draws a seed must control

| Draw | Where |
|---|---|
| `β_bs`, `B^∞` ~ U(0,1)³ | medium model init |
| `learned_bg` ~ U(0,1)³, before being overwritten with the fixed prior | background init |
| camera shuffle, per-iteration view sample | training loop |
| k-means over camera poses (reference selection) | `source/roma_init.py` |
| RoMa's internal correspondence sampling | `source/roma_init.py` |
| **importance-weighted survival draw** | `source/simplify.py` |
| k-means++ codebook seeding | `source/quantize.py` |

## 2. What cannot be made deterministic

**Bit-exact reproduction is unattainable**, and chasing it would be the wrong
response. Two independent reasons:

- The differentiable rasterizer uses **atomic accumulation in its backward
  pass**, which is non-deterministic in floating point regardless of seeding.
- The **realised primitive count after simplification is run-dependent even at
  a fixed seed**, because the survival draw is fed by device-computed
  probabilities.

The correct response is to **measure and report dispersion**: three seeds per
cell per scene, mean ± standard deviation. The realised `n_primitives_final` is
reported per run, never the target budget — a budget that lands within a few
per cent across seeds is a different experiment from one that scatters.

## 3. Versions and hardware

Recorded automatically in every `run_config.json`: git SHA (with a `-dirty`
marker), `nvidia-smi` output, GPU name and compute capability, torch version
and its CUDA version, Python version, platform, and the full `argv`.

**Hardware is a correctness constraint, not metadata.** The run aborts on a
non-A100 unless `--allow_any_gpu` is passed, because every conclusion is a
between-cell contrast and cells on different devices are not comparable. If the
override is used, those runs must be reported as not comparable with the rest.

### Verified environments

Two, and the campaign runs on the second.

| Component | Development (Windows) | **Campaign (Colab A100)** |
|---|---|---|
| GPU | RTX 3050 Ti, sm_86 | **A100-SXM4-40GB, sm_80** |
| Python | 3.11 | **3.13** |
| torch | 2.6.0+cu124 | **2.11.0+cu128** |
| CUDA toolkit | 12.4 | **12.8** |
| Host compiler | MSVC 2019 (14.29) — CUDA 12.4 rejects newer hosts | gcc (Colab default) |

Same in both: `diff_gaussian_rasterization_ms` and `simple_knn` built from
`mini-splatting/submodules`, and `romatch` as the matcher.

The gap between the two is wider than intended — the campaign stack is three
torch minors and a CUDA minor ahead of where the code was written. It builds
and passes, but that is a measured fact rather than a designed one, and it is
why the acceptance test is re-run every session rather than trusted.

**The rasterizer merge is verified on both.** `tools/verify_rasterizer.py`
reports 7/7 on sm_80, with T3 — `Z_raw/α` recovering true depth — at 0.00e+00
for opacity 0.3 and 0.7, and 2.38e-07 at 0.95. Identical to the sm_86 figures,
as the arithmetic argument predicted. Re-run it at the start of every session
regardless; it costs seconds and the whole merge rests on that identity.

**Two build fixes were needed for the newer toolkit**, both in-tree:

- `simple_knn.cu` uses `FLT_MAX` without including `<float.h>`. Up to CUDA
  ~11.x the CUDA headers supplied it transitively; under 12.x they do not.
- `open3d` has no wheel for Python 3.13 and is not imported by anything we
  run. It is in SeaSplat's `requirements.txt`, which is how it reached the
  install list; under `set -e` it aborted the build script entirely.

**`romatch` installs with `--no-deps`, and its dependencies are installed
explicitly.** RoMa declares `albumentations, einops, h5py, kornia, loguru,
matplotlib, opencv-python, poselib>=2.0.4, timm, torch>=2.5.1, torchvision,
tqdm, wandb`. The torch requirement is a floor that Colab's 2.11 already
satisfies — but leaving pip free to resolve torch/torchvision risks it
reinstalling torch from PyPI, replacing the CUDA build both extensions were
just compiled against. So those two are excluded and the rest installed by
name. A romatch failure is a warning rather than fatal: only the M1 cells
(A1/A4/A5/A7) need it, so A0/A2/A3/A6 are unaffected.

**`fused-local-corr` is optional and may be absent.** RoMa's refiner blocks
call a fused CUDA correlation kernel whenever `use_custom_corr` is set, and the
import failure surfaces mid-forward rather than at construction. `roma_init`
probes for it and, if missing, clears the flag on every refiner block and uses
the pure-torch correlation — the reference path the kernel optimises, not a
different computation. Whether the fused kernel was used is printed and
recorded as `fused_local_corr` in the cloud's sidecar, since it affects
preprocessing wall-clock, which is reported alongside A1's training cost.

**Windows build note.** `torch/include/ATen/ops/…` header paths overrun the
260-character limit from a deep working directory, producing a misleading
`cannot open include file` error. Build through a short path (a junction is
enough) and set a short `TMP`.

## 3b. The dataset is preprocessed, and must be

Training and `roma_init` both read the **undistorted** copy, not the
distributed one. All four scenes ship as COLMAP **OPENCV** with real distortion
coefficients; the reader accepts only PINHOLE/SIMPLE_PINHOLE. This is a hard
prerequisite rather than a refinement — an un-undistorted scene fails at load,
every time.

`source/undistort.py` writes an `undistort.json` sidecar per scene recording
the camera model before and after, the image counts in and out, and whether the
`sparse/` → `sparse/0/` relocation was needed. Preflight re-checks the model at
startup, so a scene that slipped through fails with a message naming the fix
rather than a bare assertion inside the loader.

Note the image directory changes: the originals use `images_wb` (and
`Images_wb` for IUI3-RedSea), while COLMAP's undistorter writes `images`.

## 4. The dense cloud is an experimental condition

For A1/A4/A5/A7 the cloud, not just the configuration, determines the result:
with densification disabled the count can never grow, so the cloud decides the
starting and largely the final geometry — and whether the budget binds.

Each cloud is therefore written with a sidecar recording its SHA-256, point
count, and every parameter that produced it, including the realised
reference-view count and the confidence threshold. **The loader verifies the
hash and refuses to run if it has changed.** An unversioned cloud from an
unseeded matcher would make four cells unattributable: two runs would give
different counts and different efficiency numbers, indistinguishable from a
real effect.

`τ_corr` is exposed and logged. Upstream has no configuration key for it and
silently inherits the matcher's internal threshold, so it changes identity
whenever the matcher is swapped.

## 5. Metric conventions

Both PSNR conventions are computed and labelled at every evaluation. This is
not belt-and-braces: the inherited routine reduces along the leading tensor
dimension, so **which convention it computes is decided by the shape it is
handed** — and the codebase passes both. The in-training report supplies
`(3,H,W)` and gets per-channel; the disk evaluation supplies `(1,3,H,W)` and
gets pooled. Measured, the same function returned 27.881 dB and 16.068 dB on
one image pair.

Also recorded per run: the LPIPS backbone (VGG — the two backbones give
systematically different values and no source paper states which it used), that
masking is none, and **which container format was actually written**, since the
harness silently falls back to JPEG when the ground-truth directory holds no
PNGs. The local corpus is PNG, so it should read `png`; it is logged rather
than assumed.

Aggregation is reported under **both** weightings, because scene image counts
are unequal (21/29/20/18) and the two differ by ~0.27 dB — larger than many
ablation differences in this literature.

## 6. Timing

Reported as wall-clock **and effective optimizer steps**. They are not
proportional: the medium warm-up, the colour-adjustment phase, the periodic
medium bursts and the CD-6 re-identification all bypass the iteration counter,
each performing a full forward, backward and optimizer step. A nominally
30 000-iteration run does roughly 43 000 of them, each paying both
rasterization passes. A figure reported only in iterations is not comparable
with one reported in steps.

## 7. Known reproducibility gaps

| Gap | Status |
|---|---|
| **Checkpoints are incomplete** — no medium model, learned background, codebooks or schedule flags | Interrupted runs are **restarted, not resumed**. Correct resume needs that state in the checkpoint first. |
| Which convention produced the baseline's *published* PSNR | Unrecorded upstream. Reporting both makes this work immune, but the comparability claim about the baseline should not be repeated until settled. |
| k-means++ seeding deviates from the source method's uniform seeding | Deliberate — uniform seeding wastes codewords (worst-case error 5.14 → 0.20 on the test fixture). Its effect at k=4096 on real data is unmeasured. |
| Rasterizer verified on sm_86, campaign runs sm_80 | Re-verify on the first A100 session. |

## 8. Self-checks

Ten suites, **76 checks**, no GPU required except the first:

```bash
python -m tools.verify_rasterizer     # 7  -- needs CUDA; T3 is decisive
python -m tools.verify_config_layer   # 6
python -m tools.verify_ledger         # 11
python -m tools.verify_metrics        # 7
python -m tools.verify_storage        # 8
python -m tools.verify_analysis       # 9
python -m tools.verify_undistort      # 7  -- T1 runs against the real dataset
python -m tools.verify_dense_init     # 6
python -m tools.verify_simplify       # 6
python -m tools.verify_quantize       # 9
```

Run them after any environment change. They are cheap, and several encode
findings that are easy to reintroduce — the shape-dependence of the PSNR
routine, the index bit-width, the stage-ordering rule, and the probe-channel
identity that the whole rasterizer merge rests on.
