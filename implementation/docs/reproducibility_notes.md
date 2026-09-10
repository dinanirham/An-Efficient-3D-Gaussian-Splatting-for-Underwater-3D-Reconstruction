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

### How large that variance actually is

Measured on Curasao, 16 000 iterations, two runs per implementation:

| | runs | spread |
|---|---|---|
| vanilla SeaSplat | 4,788,960 / 4,085,219 | 17% |
| ours (A0, after CD-23) | 3,025,374 / 4,510,298 | 49% |

Ours varies **despite** seeding both the CPU and CUDA generators. The mechanism
is amplification, not sloppiness: the rasterizer backward accumulates
atomically, so a primitive can land either side of `densify_grad_threshold`
from run to run, which changes the population feeding the next densification
event — 144 times over. The same compounding that turned a 2% per-event rate
difference into a 6× gap operates on floating-point noise.

**This has a direct methodological consequence.** A single-run ratio on
`n_primitives` carries no information at this scale, and an earlier phase of
the CD-22/CD-23 investigation spent effort chasing a 1.58× "residual" that sat
inside this spread. Any contrast reported on primitive count must clear the
dispersion, and `tools/replicate_baseline.py` is the tool for establishing it.

### S1 measured: A0's converged counts, all four scenes

Twelve runs, three seeds each, 30 000 iterations:

| scene | seeds 0 / 1 / 2 | mean | sd | CV |
|---|---|---:|---:|---:|
| Curasao | 4,285,043 / 3,186,018 / 3,802,363 | 3,757,808 | 550,866 | 14.7% |
| IUI3-RedSea | 2,280,526 / 2,761,801 / 2,571,227 | 2,537,851 | 242,367 | 9.6% |
| JapaneseGradens-RedSea | 2,377,216 / 2,220,485 / 2,109,283 | 2,235,661 | 134,610 | **6.0%** |
| Panama | 1,590,127 / 2,393,173 / 2,934,459 | 2,305,920 | 676,400 | **29.3%** |

Median across all twelve: **2,482,200**.

**Dispersion is heterogeneous across scenes, by a factor of five.** The 21%
figure measured earlier came from Curasao alone and is not a constant: Japanese
Gardens is stable at 6%, Panama scatters at 29% — its slowest and fastest seeds
differ by 1.85×. Any pooled variance estimate hides that, and a per-scene
contrast on Panama is far weaker than the same contrast on Japanese Gardens.
The analysis reports per-scene dispersion for this reason.

At the mean CV of 14.9% with three seeds, the standard error of a scene mean is
**8.6%**, so a difference on primitive count must exceed roughly **17%** to
clear it. The main effects are far larger than that — M2 targets a 92%
reduction — but the interaction terms are differences of differences and carry
about twice the variance.

**Curasao is not representative.** The replication that established A0 ≡ vanilla
SeaSplat ran on Curasao only, where A0 converges near 3.8–4.4M. The median
across all four scenes is 2.48M. Statements of the form "A0 converges to ~4.4M"
are Curasao statements and should be written as such.

### Replication: A0 and vanilla SeaSplat are indistinguishable

Three runs each, Curasao, 16 000 iterations:

| | runs | mean | sd | spread |
|---|---|---|---|---|
| ours (A0) | 4,260,571 / 3,990,523 / 4,906,223 | 4,385,772 | 470,514 | 20.9% |
| vanilla SeaSplat | 4,290,897 / 3,749,643 / 4,661,489 | 4,234,010 | 458,577 | 21.5% |

Mean ratio **1.036**, ranges fully overlapping. After CD-22 and CD-23, **A0 is
SeaSplat** to within the measurement's resolution, and the claim "we improve
SeaSplat" has a baseline that can carry it.

Two details worth keeping. The spreads are equal to within a point, so ours is
not the noisier implementation — the 49% quoted from two samples was an
artifact of n=2. And the spread is the same despite our seeding both the CPU
and CUDA generators, which confirms the variance is intrinsic to atomic
accumulation in the backward rather than anything seeding could control.

For contrast, the *paired single run* from the same session gave 3,183,805
against 4,711,324 — a ratio of 0.68, which read alone looks like a substantial
deficit in a pair the replication calls indistinguishable. That is the whole
argument for measuring distributions.

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
reported 7/7 on sm_80 before T7 was added, with T3 — `Z_raw/α` recovering true depth — at 0.00e+00
for opacity 0.3 and 0.7, and 2.38e-07 at 0.95. Identical to the sm_86 figures,
as the arithmetic argument predicted. Re-run it at the start of every session
regardless; it costs seconds and the whole merge rests on that identity.

### CD-22: the alpha gradient must reach density control

The rasterizer substitution changed more than the forward pass, and the
difference went undetected for the whole build.

Upstream SeaSplat reads `alpha` from the **colour pass** — dxyang's fork emits
it natively — so every alpha-derived loss backpropagates into the same
`viewspace_point_tensor` that `add_densification_stats` consumes. The `_ms`
fork cannot emit alpha, so CD-13 recovered it from the probe pass, which
allocated its own gradient buffer. Alpha's *value* was exact; its *gradient*
was silently removed from the densification signal.

Measured on Curasao at 30 000 iterations:

| | vanilla SeaSplat | before CD-22 |
|---|---|---|
| primitives | 4,462,668 | 743,457 |
| model on disk | 303.5 MB | 48.2 MB |
| test PSNR (per-channel) | 30.375 | 30.268 |

The trajectories agree to iteration 5000 (665,106 against 652,416) and diverge
after, which is the signature of a *missing* gradient term rather than a
mis-scaled one: early on the photometric gradient clears the threshold
unaided, and only later does the alpha contribution decide.

The fix threads one `screenspace_points` buffer through both rasterizations,
so the accumulated gradient equals upstream's by linearity. **A known
deviation remains**: our probe emits depth and alpha from a single
rasterization, so depth-loss gradients now also reach density control, where
upstream excludes them. Separating them would need a third pass per iteration,
inflating the wall-clock this study reports as an efficiency result. The
two-pass form is used deliberately and is re-checked against vanilla's
trajectory rather than assumed equivalent.

**None of T0–T6 could have caught this.** Every one inspects a returned
tensor, and alpha was correct in both versions. `verify_rasterizer` T7 now
asserts the gradient's *destination* in both directions — non-zero when the
buffer is shared, and untouched when it is not, so the check still fails if
the sharing is ever quietly dropped.

#### Outcome: CD-22 did not close the density gap

The first post-fix run converged to **635,038** primitives against vanilla's
4,462,668 — **0.142×**, essentially unchanged. The alpha gradient path was a
real divergence from upstream and is worth having corrected, but it is **not**
the cause of the 6× gap. The hypothesis is refuted.

One caveat on the numbers: the pre-fix run was seed 0 and the post-fix run
seed 2, so 743,457 → 635,038 confounds the change with the seed. CD-22's own
effect is therefore unquantified. It does not affect the verdict, since
neither figure is near 4.46M, but "CD-22 reduced the count" is not a claim
this supports.

CD-22 is kept regardless: it makes the gradient routing structurally match
upstream, and reverting would trade one known deviation for another. It is
simply no longer described as a fix for the density gap.

**Where the evidence now points.** Vanilla grows 6.7× between iterations 5000
and 15000. Across 100 densification events that is only ~1.9% growth per
event, so the cause is a *small* per-event difference that compounds, not a
structural one. Two quantities decide each event and both come out of the
rasterizer backward, where no forward-output test can reach them:
`means2D.grad`, whose norm `add_densification_stats` accumulates and
`densify_grad_threshold` filters, and `radii`, which `size_threshold` prunes
against. Mini-Splatting exists to replace 3DGS densification, so a modified
densification signal in its fork is plausible.

`tools/compare_rasterizers.py` feeds both forks identical Gaussians, camera
and loss and reports the ratios directly. It needs SeaSplat's reference
rasterizer built alongside ours — the module names differ, so they coexist.

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

**`fused-local-corr` is optional, and installing it is not the same as it
working.** RoMa's refiner blocks call a fused CUDA correlation kernel whenever
`use_custom_corr` is set, and the failure surfaces mid-forward rather than at
construction. `roma_init` probes for it and, if unusable, clears the flag on
every refiner block and uses the pure-torch correlation — the reference path
the kernel optimises, not a different computation.

The probe **imports** the module rather than asking whether it is findable.
`importlib.util.find_spec` reports that a module exists; it says nothing about
whether it loads. The PyPI wheel is linked against `libcudart.so.13` while
Colab ships CUDA 12.8, so the package installs cleanly, satisfies `find_spec`,
and then dies inside the forward pass — with the fallback skipped, because the
probe had already concluded the kernel was available. All four scenes failed
that way once.

`setup_colab.sh` now verifies by importing after installing, and uninstalls the
package if it cannot load: a broken extension left in place is worse than an
absent one, because it makes the fallback look unnecessary.

That diagnostic then broke the build. The script runs under `set -euo
pipefail`, and the line printing *why* the import failed is a `python -c` that
exits non-zero by design; the pipeline inherited its status and `set -e`
aborted the script before either CUDA extension was compiled. The failure
surfaced one cell later as `ModuleNotFoundError: diff_gaussian_rasterization_ms`
— a missing extension, with nothing to connect it to the message above it. Any
command that is *expected* to fail needs `|| true` under these flags, and the
script now carries an `ERR` trap that names the line it died on, so an aborted
build says so instead of stopping quietly.

Whether the kernel was used is printed and recorded as `fused_local_corr` in
the cloud's sidecar, with `fused_local_corr_error` giving the reason when it
was not — a wheel built against the wrong CUDA is indistinguishable from "not
installed" in the timing, and preprocessing wall-clock is a reported figure.

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

### Measured clouds, and the estimate they corrected

`dense` preset, 20,000 matches per reference view, built in 0.5-0.7 min each:

| scene | reference views | points kept | filtered |
|---|---:|---:|---:|
| Panama | 15 | 299,368 | 99.8% |
| JapaneseGradens-RedSea | 17 | 334,931 | 98.5% |
| Curasao | 18 | 356,674 | 99.1% |
| IUI3-RedSea | 25 | 471,531 | 94.3% |

The count is `num_refs × matches_per_ref`, filtered by cheirality and
reprojection error. `nns_per_ref` selects *which* neighbouring views each
reference is matched against; it does not multiply the count. An earlier
estimate treated it as a multiplier, came out 3× high, and set `n_bud` above
three of the four clouds — caught by the binding check before any run used it.

All four were built on the **pure-torch correlation**, since
`fused-local-corr`'s wheel is linked against CUDA 13 and this stack is 12.8.
Recorded per cloud as `fused_local_corr: false` with the reason. Preprocessing
wall-clock is reported alongside A1's training cost, so which path produced a
cloud is part of that figure.

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

## 5b. Rendering throughput

Frame rate is the one efficiency measure all three mechanisms affect, and two
of the design's predictions are stated against it — that the quantization cell
shows approximately **no** gain, since the source method credits its published
2–3× speedup to an opacity penalty this study disables, and that gains from
primitive reduction are **sub-linear**. Neither was testable until now: the
harness measured model size and training time but never render speed.

What is timed is the **colour pass alone**, over the held-out views, with
`torch.cuda.synchronize()` around the loop and five warm-up frames discarded.
Both details decide whether the number means anything — CUDA launches are
asynchronous, so timing without synchronising measures how fast Python enqueues
work, and the first render of a session pays autotuning and allocator growth.

The probe passes are excluded. They serve the training objective, not
rendering, and including them would measure this study's training arrangement
rather than the model's rendering cost — and would not be comparable with any
published figure.

Each pass over the held-out views is timed separately rather than as one
block. The scenes hold only three or four such views, so a single block is
under a fifth of a second and gives no way to distinguish a stable figure from
a noisy one. Twenty passes cost about a second and yield a dispersion —
reported as `render_ms_per_frame_sd` and `_cv`. **A frame rate quoted without
its dispersion cannot be compared against another cell's**, and the design's
sub-linearity prediction is a claim about a ratio of two such figures.

Recorded per run as `render_fps`, `render_ms_per_frame` with its standard
deviation and coefficient of variation, `render_frames_timed` and
`render_peak_mem_mb`, with `render_note` carrying the reason when profiling did
not produce a figure. Profiling never raises: a failure there must not lose a
finished training run.

First measured value, A0/Curasao/s0 at 4,285,043 primitives: **69.17 fps**,
14.46 ms/frame, 3,587 MB peak. Training wall clock 4,682 s.

## 5c. Build fragility: transitive includes

Two in-tree fixes to the reference CUDA sources, both the same defect class and
both invisible until a host-compiler change exposed them.

`simple_knn.cu` used `FLT_MAX` without `<float.h>`. Thirteen files across both
rasterizer forks and simple-knn used `uint32_t`, `uint64_t` and
`std::uintptr_t` while including only `<iostream>`, `<vector>` and CUDA
headers — relying on libstdc++ to pull `<cstdint>` in transitively. Recent
libstdc++ releases dropped many such transitive includes.

**The failure mode is what makes this worth recording.** nvcc, CUDA, torch and
Python all reported the exact known-good stack — `torch 2.11.0+cu128`,
`cuda 12.8`, `python 3.13.15` — while the build failed on code that had
compiled in the same configuration earlier in the campaign. The variable that
moved was the host compiler, and nothing in the diagnostic showed it. `g++` and
`libstdc++` are now printed alongside the rest.

Both fixes are strictly additive: an explicit include of a header the code
already depends on cannot change behaviour, so runs before and after remain
comparable.

## 5d. Collecting results

`tools/collect_results.py` merges the four per-run sources — `eval_metrics.json`,
`model_size.json`, `run_config.json` and `diagnostics.csv` — into one view:

```
python -m tools.collect_results --output_root <root>
```

writing `results_runs.csv` (one row per run, 45 fields), `results_by_scene.csv`,
`results_by_cell.csv` and a readable `results_summary.md`.

It is a *view*, not a source: everything in it is recomputed from the run
artifacts, so it can be regenerated at any point in the campaign and nothing
depends on it having been run.

Four conventions are enforced rather than left to the reader:

- **Dispersion is never pooled across scenes**, because the measured
  coefficient of variation ranges from 6.0% to 29.3% by scene.
- **Both aggregation rules are emitted** — unweighted mean of scene means, and
  image-weighted — because held-out frame counts are unequal (3/4/3/3) and the
  two are different numbers.
- **`n = 1` reports `n/a`, never `0.0`.** The standard deviation of one sample is
  undefined, and printing zero reads as perfect reproducibility.
- **Collapse state travels with every row**, and groups mixing collapsed and
  intact seeds are flagged before any mean over them is shown.

## 5e. Spatial extent — a geometric test for floaters

```
python -m tools.spatial_extent --output_root <root>
```

Every fidelity measure in this study is photometric, and SeaSplat's degeneracy
D-4 — opaque low-texture primitives placed near the camera to reproduce veiling
haze as geometry — is photometrically *excellent*. It is visible in the geometry
and nowhere else, so nothing else the campaign records would detect it.

Reported per stored cloud: the full min/max box, the 1st–99th percentile box,
and the **inflation ratio** between them. A cloud whose inflation is near 1 has
no significant tail; one inflated by an order of magnitude is being stretched by
a small number of outlying primitives.

Extents are also computed over primitives above a visibility threshold
(α ≥ 0.05), because a primitive at α = 0.001 contributes nothing to the render
and should not enlarge a reported extent. **The gap between gated and ungated
extent is itself the diagnostic**: a large gap means the tail is invisible and
cosmetic, a small gap means it is being rendered.

Opacity is stored as a logit and scale as a logarithm; both are inverted before
use, since comparing raw stored values across cells would be meaningless.

Reads `point_cloud.ply`, which is written for **seed 0 only** unless
`--save_ply_all_seeds` was passed.

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
| **Checkpoints are incomplete** — no medium model, learned background, codebooks or schedule flags | Interrupted runs are **restarted, not resumed**. Correct resume needs that state in the checkpoint first. A restarted run rotates the previous attempt's `diagnostics.csv` to `diagnostics.attemptN.csv` rather than appending, since two runs concatenated into one file are non-monotonic in iteration while the final row stays correct — which is what makes that corruption easy to miss. |
| Which convention produced the baseline's *published* PSNR | Unrecorded upstream. Reporting both makes this work immune, but the comparability claim about the baseline should not be repeated until settled. |
| k-means++ seeding deviates from the source method's uniform seeding | Deliberate — uniform seeding wastes codewords (worst-case error 5.14 → 0.20 on the test fixture). Its effect at k=4096 on real data is unmeasured. |
| Rasterizer verified on sm_86, campaign runs sm_80 | Re-verify on the first A100 session. |

## 8. Self-checks

Ten suites, **81 checks**, no GPU required except the first:

```bash
python -m tools.verify_rasterizer     # 9  -- needs CUDA; T3, T7, T8 decisive
python -m tools.verify_config_layer   # 6
python -m tools.verify_ledger         # 15 -- T11 image dirs, T12 attempt cap, T14 file loss
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
