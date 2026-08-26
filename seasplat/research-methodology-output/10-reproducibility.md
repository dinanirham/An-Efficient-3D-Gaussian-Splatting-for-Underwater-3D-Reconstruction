# §10 — Reproducibility checklist

## 10.1 Seed handling — **non-deterministic by default**

`[repo: train.py:1026]` — `parser.add_argument("--seed", type=int, default=-1)`
`[repo: utils/general_utils.py:116-142]`:

```python
def safe_state(silent, seed:int):
    ...
    if seed == -1:
        random.seed()                    # seeded from OS entropy
        np.random.seed()                 # seeded from OS entropy
        torch.manual_seed(torch.seed())  # seeded from OS entropy
    else:
        random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
```

| Item | Status |
|---|---|
| Default seed | **`-1` → fully random**. Every run differs. |
| Deterministic path exists | Yes — `--seed <int>` seeds `random`, `numpy`, `torch` CPU. |
| `torch.cuda.manual_seed_all` | ❌ **not called** — CUDA RNG is never explicitly seeded even with `--seed`. |
| `torch.backends.cudnn.deterministic` / `.benchmark` | ❌ not set. |
| `torch.use_deterministic_algorithms` | ❌ not set. |
| Seed reported in the paper | ❌ no seed, no repeat count, no variance/error bars anywhere. |

**Consequences.** (a) Table I and Table III report single runs with no dispersion, so the
sub-0.5 dB differences between ablation rows (e.g. 27.13 vs 27.11 vs 26.64) are **not
demonstrated to exceed run-to-run noise**. (b) Even with `--seed`, the 3DGS rasterizer uses
atomic adds during backward, which are non-deterministic in floating point regardless of
seeding — so bit-exact reproduction is not achievable at this commit. `[unverified — not
measured here, but standard for `diff-gaussian-rasterization`]`

Random draws that a seed would have to control: initial `β^B, B^∞ ~ U(0,1)`
`[repo: models.py:54,61]`; `bg ~ U(0,1)` before being overwritten with the fixed prior
`[repo: train.py:126-129]`; camera shuffle `[repo: scene/__init__.py, shuffle=True]`; the
per-iteration `randint` view sample `[repo: train.py:198]`.

## 10.2 Train/test split

`[repo: scene/dataset_readers.py:223, 261-271]`

```python
def readColmapSceneInfo(path, images, eval, llffhold=8, ...):
    if eval:
        train_cam_infos = [c for idx, c in enumerate(cam_infos) if idx % llffhold != 0]
        test_cam_infos  = [c for idx, c in enumerate(cam_infos) if idx % llffhold == 0]
    else:
        train_cam_infos = cam_infos
        test_cam_infos  = []
```

| Item | Value |
|---|---|
| Split rule | **every 8th frame held out** (`llffhold = 8`), by COLMAP index order after filename sort |
| Test fraction | 12.5% |
| `llffhold` overridable from CLI? | ❌ no — it is a Python default with no `add_argument` |
| `--eval` default | **`False`** `[repo: arguments/__init__.py:58]` → test set is **empty** and all frames are trained on |
| README training command | `python train.py -s DATASET_PATH --exp NAME --do_seathru --seathru_from_iter 10000` — **omits `--eval`** `[repo: README.md]` |
| Paper's statement | "comparing rendering at held-out test frames to ground truth frames" `[paper §V.A.c]` — so `--eval` **must** have been used for Table I, but it is not documented anywhere. |

**Action item:** any reproduction must add `--eval`, or it will silently train on the test
set and report inflated numbers.

Additional split-affecting flags, all defaulting to no-op: `subsample=0`,
`skip_first_n_images=0`, `start_cam=-1`, `end_cam=-1` `[repo: arguments/__init__.py:59-62]`.

## 10.3 Exact metric computation — **full-frame, unmasked, per-channel-averaged, from disk**

This is the item the methodology singles out as varying silently across underwater papers.
SeaSplat's answer, precisely:

### (a) Masking: **none**

`[repo: train.py:629-644]` — every pixel of every test frame is included. There is **no**
sky mask, no water-column mask, no alpha mask, no valid-depth mask at metric time. (An
alpha-threshold mask `depth_alpha_threshold = 0.5` exists but is used **only** for
TensorBoard depth visualisation `[repo: train.py:814-816]`, never for PSNR/SSIM/LPIPS.)

### (b) What is compared: **`Î` (in-medium reconstruction) vs `I` (capture)**

Not `Ĵ`. The restored/medium-free output `Ĵ` is **never scored** — the paper states why:
no ground truth exists "without draining the ocean" `[paper §V.A.c]`. All of Table I and
Table III measure only in-medium novel-view synthesis. `[repo: train.py:595-621]` renders
into `train/with_water/` and `test/with_water/` when `do_seathru` is on.

### (c) PSNR formula — **mean of per-channel PSNRs, not PSNR of the pooled MSE**

`[repo: utils/image_utils.py:17-19]`

```python
def psnr(img1, img2):
    mse = ((img1 - img2) ** 2).view(img1.shape[0], -1).mean(1, keepdim=True)
    return 20 * torch.log10(1.0 / torch.sqrt(mse))
```

`img1.shape[0]` is the **channel** dimension for a `(3,H,W)` tensor, so `mse` is a
`(3,1)` vector of per-channel MSEs and the return is a `(3,1)` vector of per-channel
PSNRs, subsequently `.mean()`-ed `[repo: train.py:643]`.

`mean_c(PSNR_c) ≠ PSNR(mean_c(MSE_c))` by Jensen — the per-channel average is **always ≥**
the pooled-MSE PSNR, with the gap growing as the channels' errors diverge. **Underwater
imagery is precisely the regime where per-channel error diverges most** (red is attenuated
to near-nothing, blue is not), so this choice inflates PSNR more for underwater scenes than
it would for in-air scenes.

This formula is inherited verbatim from upstream 3DGS, so **it is consistent with the 3DGS
row of Table I** — but SeaThru-NeRF is a separate codebase and its published numbers were
not necessarily computed the same way. `[unverified — I have not read the SeaThru-NeRF
metric code in this pass; see that folder's §10.]` **This is a concrete cross-method
comparability risk in Table I.**

### (d) Data path: **re-read from 8-bit files on disk, possibly JPEG**

`[repo: train.py:584-644]`

```python
png_images = glob.glob(f"{gt_dir}/*.png")
use_jpeg   = len(png_images) == 0
...
render_set(..., save_as_jpeg=use_jpeg)
renders, gts, _ = readImages(image_dir, gt_dir, fnames)   # PIL.Image.open
```

Metrics are **not** computed on the in-memory float tensors. Renders are written to disk,
then re-opened. Two consequences:

1. **8-bit quantisation** of both render and GT before comparison.
2. **JPEG compression** of the render whenever the GT directory holds no `.png` files —
   which is the case for the SeaThru-NeRF dataset (DSLR `.JPG`; `readImages` explicitly
   falls back to `.JPG` at `[repo: metrics.py:62]`). So the reported numbers for the main
   benchmark are almost certainly **JPEG-round-tripped**, at PIL's default quality 75.

`[inferred: combining repo train.py:586-587 with metrics.py:59-62; not stated in the paper]`

### (e) SSIM and LPIPS

- SSIM: 11×11 Gaussian window, σ=1.5, `C1=0.01²`, `C2=0.03²`, averaged over all pixels and
  channels — standard 3DGS implementation `[repo: utils/loss_utils.py:41-77]`.
- LPIPS: `net_type='vgg'` `[repo: train.py:644]`, via the vendored `lpipsPyTorch`.
  Note VGG-LPIPS gives systematically different values from AlexNet-LPIPS; the paper does
  not state which it used. `[unverified in paper; repo confirms VGG]`

### (f) Aggregation

Per-image metrics → `mean` over the split `[repo: train.py:654-656]` → written to
`eval_metrics.json`. Table I reports per-scene; Table III reports "averaged across the
SeaThru-NeRF datasets" `[paper Tab. III caption]` — i.e. a mean of four per-scene means,
which is an unweighted scene average, not an image-weighted one. `[inferred]`

## 10.4 Stated non-determinism

**None stated in the paper.** No mention of seeds, repeats, variance, or hardware
determinism anywhere in the text.

## 10.5 Reproduction checklist for your cluster

| # | Action | Why |
|---|---|---|
| 1 | Add `--eval` to the README command | otherwise the test set is empty and all frames are trained on (§10.2) |
| 2 | Pass `--seed <k>` and additionally patch `torch.cuda.manual_seed_all(k)` into `safe_state` | CUDA RNG is unseeded even with `--seed` (§10.1) |
| 3 | Run ≥3 seeds per configuration and report dispersion | Table III's differences are ≤0.5 dB with no error bars (§10.1) |
| 4 | Add `90` to `CUDA_ARCHITECTURES` in `Dockerfile:15` and rebuild `diff-gaussian-rasterization` + `simple-knn` | the shipped container targets SM 8.6/8.9 only; H100 is SM 9.0 (see [`08-computational-profile.md`](08-computational-profile.md)) |
| 5 | Convert GT images to PNG **or** accept JPEG round-tripping — and apply the same choice to every method you compare | else the metric pipeline silently JPEG-compresses renders (§10.3d) |
| 6 | Decide one PSNR convention and recompute **all** methods with it | the per-channel-average formula inflates underwater PSNR relative to pooled-MSE PSNR (§10.3c) |
| 7 | To ablate, **edit `arguments/__init__.py` directly** | boolean flags defaulting `True` are `store_true` and cannot be disabled from the CLI (delta D-12) |
| 8 | Record the effective optimizer-step count, not the iteration count | `continue` bypasses `iteration += 1`; a "30 000-iteration" run does ≈43 000 steps (delta D-8) |
| 9 | Log `total_points` at the end of training | Gaussian count is unreported in the paper and needed for any storage comparison against `compact3d/`, `CompGS/`, `OMG/`, `mini-splatting/` |
