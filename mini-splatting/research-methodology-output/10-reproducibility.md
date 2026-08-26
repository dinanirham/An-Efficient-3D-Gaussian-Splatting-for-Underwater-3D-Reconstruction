# §10 — Reproducibility checklist

## 10.1 Seed handling — fixed at 0, but the method is *structurally* stochastic

`[repo: utils/general_utils.py:112-133]`:
```python
def safe_state(silent):
    ...
    random.seed(0)
    np.random.seed(0)
    torch.manual_seed(0)
    torch.cuda.set_device(torch.device("cuda:0"))
```
Called as `safe_state(args.quiet)` `[repo: ms/train.py:420]` — **note the signature takes
no seed argument at all**, unlike `seasplat/`'s `safe_state(quiet, seed)`.

| Item | Status |
|---|---|
| Python / NumPy / Torch CPU seeds | **hard-coded 0**, no CLI override |
| `torch.cuda.manual_seed_all` | ❌ not called |
| cuDNN determinism flags | ❌ not set |
| Seed reported in the paper | ❌ no mention of seeds, repeats, or variance |

**Why the fixed seed buys less here than elsewhere.** Mini-Splatting's two decisive steps
are `np.random.choice` calls:

- depth-reinit pixel selection, `p = (1 − α_accum)/Σ` `[repo: ms/train.py:189-190]`
- importance-weighted Gaussian sampling, `p = I/ΣI` `[repo: ms/train.py:240-241]`

Both consume the NumPy RNG *and* a probability vector computed on GPU. The rasterizer's
backward pass uses atomic adds, which are non-deterministic in float — so `α_accum` and
`accum_weights` differ slightly between runs, which perturbs `p`, which changes **which
Gaussians survive**, which changes `N`. A fixed NumPy seed does not close that loop.
`[inferred: repo ms/train.py:177-190, 233-241 combined with the standard non-determinism of `diff_gaussian_rasterization`]`

The consequence is that `N` itself — the paper's headline metric — is a random variable
here in a way it is not for `compact3d/` (deterministic K-means at a fixed codebook size)
or `CompGS/`. **Single-run Gaussian counts should be reported with dispersion.**

## 10.2 Train/test split

`[repo: scene/dataset_readers.py:132, 148-153]` — standard 3DGS:
```python
def readColmapSceneInfo(path, images, eval, llffhold=8):
    if eval:
        train_cam_infos = [c for idx, c in enumerate(cam_infos) if idx % llffhold != 0]
        test_cam_infos  = [c for idx, c in enumerate(cam_infos) if idx % llffhold == 0]
```

| Item | Value |
|---|---|
| Rule | every 8th image held out (`llffhold = 8`) |
| `--eval` default | `False` `[repo: arguments/__init__.py]` |
| **README commands include `--eval`** | ✅ **yes** — every training command in the README has it `[repo: README.md]` |
| Paper's statement | "we adopt identical processing details for these datasets, including scene selection, **train/test split**, and image resolution, as specified in the official implementation of 3DGS" `[paper §6]` |
| `llffhold` overridable | ❌ Python default only, no `add_argument` |

**Cleanly documented** — better than `seasplat/`, where the README omits `--eval`.

⚠️ One thing to pin down: the paper says "scene selection … as specified in the official
implementation of 3DGS". 3DGS's `full_eval.py` uses a specific 9-scene subset of
Mip-NeRF 360 (7 public + 2 restricted). The repo ships its own `ms/full_eval.py`
`[repo: ms/full_eval.py]` described as a "Modified full_eval script" `[repo: README.md]`.
Confirm the scene list matches before comparing numbers to any other paper's Mip-NeRF 360
average — this is a common silent discrepancy in the 3DGS literature. `[unverified]`

## 10.3 Exact metric computation

### (a) PSNR — mean of **per-channel** PSNRs (same as `seasplat/`, unlike `seathru_NeRF/`)

`[repo: utils/image_utils.py:17-19]`:
```python
def psnr(img1, img2):
    mse = (((img1 - img2)) ** 2).view(img1.shape[0], -1).mean(1, keepdim=True)
    return 20 * torch.log10(1.0 / torch.sqrt(mse))
```
`img1.shape[0]` is the channel dimension for `(3,H,W)`, so this is a `(3,1)` vector of
per-channel PSNRs, then `.mean()`-ed at `[repo: ms/train.py:359]`.

This is the **stock 3DGS formula**, inherited unmodified. Since the paper compares only
against 3DGS-family methods evaluated the same way, it is internally consistent.

> **Cross-set caveat:** `seathru_NeRF/` uses pooled-MSE PSNR
> `[seathru_NeRF repo: internal/image.py:136]`, which by Jensen is always ≤ the
> per-channel mean. Mini-Splatting's numbers are therefore on the **same footing as
> `seasplat/`, `compact3d/`, `CompGS/`, `OMG/`, `EDGS/`** (all 3DGS forks) but **not** as
> `seathru_NeRF/` or `nerf/`. See `../../comparison-glossary.md`.

### (b) Masking: none; images clamped to [0,1] before scoring

`[repo: ms/train.py:352-353]`:
```python
image    = torch.clamp(renderFunc(...)["render"], 0.0, 1.0)
gt_image = torch.clamp(viewpoint.original_image.to("cuda"), 0.0, 1.0)
```
Full-frame, no mask. **Note the clamp** — it is applied at eval but *not* in the training
loss `[repo: ms/train.py:120-122]`, so overshoot is penalised during training but forgiven
at test.

### (c) In-memory tensors, not disk round-trip — **for `ms/` and `ms_d/`**

`ms/train.py`'s in-training evaluation scores the **float tensors directly**
`[repo: ms/train.py:352-362]` — no 8-bit quantisation, no JPEG. This is materially
**cleaner than `seasplat/`**, which re-reads saved PNG/JPEG files
`[seasplat repo: train.py:584-644]`.

⚠️ **But `ms_c/` does round-trip through disk.** `[repo: ms_c/run.py:31-40, 105-125]`
renders to `test_compressed/*/renders/`, saves with `torchvision.utils.save_image`, then
`readImages()` re-opens with PIL. So Mini-Splatting-C's rate-distortion numbers are
computed on **8-bit PNGs**, while Table 1's numbers are computed on floats. The two are not
directly comparable, and the paper does not flag it. `[inferred: comparing repo ms/train.py:352 with ms_c/run.py:36-38]`

### (d) SSIM / LPIPS

- SSIM: standard 3DGS 11×11 Gaussian window, σ = 1.5 `[repo: utils/loss_utils.py]`.
- LPIPS: **VGG** backbone, `lpips(image, gt_image, net_type='vgg')`
  `[repo: ms/train.py:362; ms_c/run.py]`. The paper does not state the backbone
  `[unverified in paper]`; the repo confirms VGG. Same as `seasplat/` ✅.

### (e) Aggregation

Per-image → mean over the split `[repo: ms/train.py:365-369]`. Table 1's dataset columns
are means over scenes; the paper does not state whether scene means are image-weighted.
`[unverified]`

### (f) What the reported `Num` means

`Num` in Tables 1–5 is Gaussians in **millions**, printed at the end of training
`[repo: ms/train.py:299 — print(gaussians._xyz.shape)]`. For Mini-Splatting-C the count
after voxel deduplication `[repo: ms_c/run.py:144]` is **not** reported anywhere — see
delta D-10.

## 10.4 Stated non-determinism

**None stated in the paper.** No seeds, repeats, error bars, or variance anywhere — despite
the method being explicitly built on stochastic sampling and arguing (§4.2) that stochasticity
is *better* than determinism.

This matters most for:
- **Table 3** (densification ablation): PSNR moves 27.47 → 27.47 → 27.54, i.e. **0.07 dB
  total**, with no dispersion.
- **Table 4** Center vs Mid: 27.57 vs 27.54, **0.03 dB**, and the paper chooses `Mid` on
  non-metric grounds anyway.
- **`Num` itself**, which is a stochastic outcome (§10.1).

## 10.5 Reproduction checklist for your cluster

| # | Action | Why |
|---|---|---|
| 1 | **Budget a full environment migration.** Python 3.7 + torch 1.12.1+cu116 `[repo: README.md]` predates Hopper; Python 3.7 is EOL | CUDA 11.6 has no SM 9.0 support |
| 2 | Rebuild **`diff_gaussian_rasterization_ms`** (the fork, *not* upstream 3DGS's) and `simple-knn` with `TORCH_CUDA_ARCH_LIST` including `9.0` | the method needs `accum_weights`/`area_proj`/`area_max`/`out_pts`/`accum_alpha`, which upstream does not return `[repo: gaussian_renderer/__init__.py:173, 189-191, 210]` |
| 3 | Always pass `--imp_metric {indoor,outdoor}` — it is **required with no default** | `[repo: ms/train.py:409]`; the paper calls the metric "case-dependent and hand-crafted … an experimental trick" `[paper App. E]` |
| 4 | Use the README's per-dataset resolution flags (`-i images_4` outdoor, `-i images_2` indoor) | `[repo: README.md]`; resolution changes `θ_blur·H·W` and hence which Gaussians are blur-split |
| 5 | **Consider raising `--num_max` (4.5 M)** | it exists to bound memory on a 24 GB RTX 3090; peak reported usage is 7.45 GB against your 96 GB `[repo: ms/train.py:406]`, and it is absent from `ms_d/` entirely |
| 6 | Run ≥3 seeds by patching `utils/general_utils.py:130-132`, and report dispersion **on `N` as well as on PSNR** | `N` is a stochastic outcome (§10.1); Table 3/4 margins are 0.03–0.07 dB |
| 7 | Record which **variant** every number belongs to | Mini-Splatting-D *increases* `N` (4.69 M) while Mini-Splatting *decreases* it (0.49 M) — same paper, opposite direction `[paper Tab. 1]` |
| 8 | If comparing `ms_c/` sizes against `compact3d/` or `CompGS/`, log `N` **before and after** `np.unique` | undocumented voxel deduplication `[repo: ms_c/run.py:144]` (delta D-10) folds primitive removal into the reported file size |
| 9 | Do not tabulate `ms/` metrics against `ms_c/` metrics without noting the disk round-trip | `ms/` scores float tensors; `ms_c/` scores 8-bit PNGs (§10.3c) |
| 10 | Verify the Mip-NeRF 360 **scene list** in `ms/full_eval.py` against whatever you compare to | "Modified full_eval script" `[repo: README.md]`; scene-subset mismatches silently shift dataset averages (§10.2) |
| 11 | Expect **no training-time win indoors** | 27 m 02 s vs 3DGS's 24 m 41 s `[paper Tab. 2]`; the speed claims are outdoor-only (see [`08-computational-profile.md`](08-computational-profile.md)) |
| 12 | If applying to underwater data, expect the **water column to behave like sky** | the depth-driven reinit fails "in areas without a certain depth value" `[paper App. G]` — the same regions where `seasplat/` reports 3DGS floaters |
