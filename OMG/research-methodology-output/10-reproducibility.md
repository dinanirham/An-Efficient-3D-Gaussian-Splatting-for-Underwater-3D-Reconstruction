# §10 — Reproducibility checklist

## 10.1 Seed handling — fixed at 0, but the pipeline is stochastic

`[repo: utils/general_utils.py:130-132]` (inherited from Mini-Splatting / 3DGS):
```python
random.seed(0)
np.random.seed(0)
torch.manual_seed(0)
```

| Item | Status |
|---|---|
| Python / NumPy / Torch-CPU seeds | **hard-coded 0**, no CLI override |
| `torch.cuda.manual_seed_all` | ❌ not called |
| cuDNN determinism flags | ❌ not set |
| Seed reported in the paper | ❌ no mention of seeds, repeats or variance |

**Three stochastic stages survive the seed:**
1. Mini-Splatting's `np.random.choice` for depth-reinit pixel sampling and importance sampling
   (inherited) — see `../mini-splatting/research-methodology-output/10-reproducibility.md`.
2. **cuML K-Means** with `n_init = 1` `[repo: gaussian_model.py:846]` — a single random
   initialisation, on GPU, **not** covered by `np.random.seed(0)`.
3. The 3DGS rasterizer's atomic adds in backward.

⇒ **The final Gaussian count and the codebook are both run-dependent.** Since `#Gauss` and
`Size` are two of the paper's four headline metrics, single-run numbers should carry
dispersion. None is reported.

## 10.2 Train/test split

Standard 3DGS, inherited through Mini-Splatting: `--eval` ⇒ every 8th view held out
(`llffhold = 8`), applied via `scene/dataset_readers.py`.

| Item | Value |
|---|---|
| README commands | **include `--eval`** ✅ `[repo: README.md]` |
| Datasets | Mip-NeRF 360, Tanks&Temples, Deep Blending `[paper §4.1]` |
| `--imp_metric` | **required**: `outdoor` for M360-outdoor + T&T, `indoor` for M360-indoor + DB `[repo: README.md]` |
| Scene subsets | "Following the previous works" `[paper §4.1]` — not enumerated `[unverified]` |

⚠️ Baseline numbers in Tables 1–2 are **"sourced from the LocoGS [53] paper"**
`[paper Tab. 1 caption]`, not re-run by the OMG authors. Only OMG's own **FPS** was
re-measured on the same 3090. So PSNR/SSIM/LPIPS/Size for the baselines carry LocoGS's
protocol, whatever that was.

## 10.3 Exact metric computation

### (a) PSNR — **pooled MSE**, via a call-site subtlety

`[repo: utils/image_utils.py:17-19]` (inherited verbatim from 3DGS):
```python
def psnr(img1, img2):
    mse = (((img1 - img2)) ** 2).view(img1.shape[0], -1).mean(1, keepdim=True)
    return 20 * torch.log10(1.0 / torch.sqrt(mse))
```

This function is written for `(3,H,W)` input, where `shape[0] == 3` gives the 3DGS
**per-channel-mean** convention. But the **reported** numbers come from `metrics.py`, which
loads `(1,3,H,W)` tensors `[repo: metrics.py:31-32]` — so `.view(1, -1)` pools **all channels
and pixels** ⇒ **pooled-MSE PSNR**, the stricter convention.

> ⚠️ **Exactly the same call-site subtlety documented for `../EDGS/`**
> (`research-methodology-output/10-reproducibility.md` §10.3a). Two folders, same inherited
> function, same accidental convention flip.
>
> **Consequence for your master table:** OMG's reported PSNR is on the **pooled-MSE**
> convention — the same as `../seathru_NeRF/` and `../CompGS/`, and **not** the
> per-channel-mean convention that `../seasplat/`'s in-training path uses. Since OMG's
> baselines come from the LocoGS paper, whether *those* are on the same convention is
> `[unverified]`.

### (b) 8-bit PNG disk round-trip

`[repo: metrics.py:29-32]` — renders and ground truth are re-opened from disk with
`PIL.Image.open` and converted by `tf.to_tensor`. So metrics are computed on **8-bit quantised
images**, as in `../seasplat/`, `../CompGS/` and `../mini-splatting/`'s `ms_c`.

### (c) Masking: none. Full-frame.

### (d) SSIM / LPIPS

- SSIM: 3DGS's implementation `[repo: utils/loss_utils.py]`.
- LPIPS: the vendored `lpipsPyTorch` `[repo: metrics.py:18]` — **VGG** by default in this
  codebase, matching `../seasplat/`, `../mini-splatting/`, `../CompGS/`. `[unverified]` whether
  `net_type` is passed explicitly.

### (e) What `Size` means — ✅ honest

`[repo: train.py:116-123]`:
```python
save_dict = gaussians.encode()
save_comp(scene.model_path + "/comp.xz", save_dict)
actual_storage = os.path.getsize(scene.model_path + "/comp.xz")
byte = {'xyz': 0, 'scale': 0, 'rotation': 0, 'app': 0, 'MLPs': 0}
```

The reported figure is **the actual file on disk**, and the per-component breakdown explicitly
includes **`MLPs`**. Same practice as `../CompGS/`. Verify that `../compact3d/`'s codebook and
`../mini-splatting/`'s `ms_c` numbers are on the same footing before tabulating.

### (f) What `#Gauss` means — ✅ comparable

Rendered Gaussians, as in `../mini-splatting/` and `../compact3d/`. **Not** comparable to
`../CompGS/`, which reports anchors.

## 10.4 Stated non-determinism

**None stated.** No seeds, repeats or error bars.

Margins that would need them, from `[paper Tab. 4]`:
- OMG-M "w/o LD scoring": **0.12 dB**.
- OMG-M "w/o SVQ" is **better** on quality (27.26 vs 27.21) — a **−0.05 dB** difference used to
  argue SVQ is nearly lossless.
- OMG-XL vs LocoGS-L: **+0.01 dB**, +0.005 SSIM `[paper Tab. 1]`.

The **robust** results are the storage ratios (**1.9–2.0× smaller than LocoGS**, **203× smaller
than 3DGS**), the training-time gap (**20 min vs 1 h**), and the FPS gap versus HAC (**3.2×**).
Cite those.

## 10.5 Reproduction checklist for your cluster

| # | Action | Why |
|---|---|---|
| 1 | **Read `../mini-splatting/research-methodology-output/` first** | OMG inherits its parameter block and `intersection_preserving` verbatim, plus all of its undocumented mechanisms (no `reset_opacity()`, `(1−α)`-weighted depth-reinit sampling, LR-schedule rewind) — delta D-5 |
| 2 | **Compile TMC13 / G-PCC** and set its path | **hard blocker** for any size figure. Either add `tmc3` to `PATH` or edit **`utils/gpcc_utils.py` lines 243 and 258** `[repo: README.md]` |
| 3 | Install **tiny-cuda-nn** and **cuML/RAPIDS** | all four MLPs and the SVQ K-means. The README links the RAPIDS guide and pre-emptively acknowledges install trouble |
| 4 | Always pass `--eval` **and** `--imp_metric {indoor,outdoor}` | `imp_metric` is **required** with no default `[repo: README.md]` |
| 5 | Set `--importance_thresh` explicitly per variant | the config ships **0.96 (XS) only**; XS→XL = 0.96 / 0.98 / 0.99 / 0.999 / 0.9999 (delta D-8) |
| 6 | ✅ **Modern stack** — CUDA 12.1, Python 3.11, torch 2.5.1 `[repo: README.md]` | H100-compatible out of the box, unlike `../mini-splatting/` (Py 3.7 / CUDA 11.6) |
| 7 | Run ≥3 seeds (patch `utils/general_utils.py:130-132`) and report dispersion on **`#Gauss` and `Size`**, not just PSNR | cuML K-means uses `n_init = 1` and is not covered by the NumPy seed (§10.1) |
| 8 | Decide **one PSNR convention** and recompute every method | OMG's reported PSNR is **pooled-MSE** via the `metrics.py` call site (§10.3a) |
| 9 | Verify competitors' `Size` includes their decoders | OMG counts its MLPs; `../CompGS/` counts its; check `../compact3d/` and `ms_c` |
| 10 | Quote the **GPU** with any FPS number | "600+ FPS" is the **4090**; on the 3090 OMG-XS is **350** |
| 11 | Note that **Mini-Splatting renders faster** despite more Gaussians | 1095 vs 887 FPS on T&T — the per-frame MLP decode costs more than the primitive reduction saves (see [`08-computational-profile.md`](08-computational-profile.md) §8.2) |
| 12 | Baseline rows in Tab. 1–2 come from the **LocoGS paper**, not re-run | only OMG's FPS was re-measured `[paper Tab. 1 caption]` |
| 13 | If applying to underwater data, expect the **water column** to defeat depth reinitialization | inherited from Mini-Splatting, whose depth-driven reinit "fails in areas without a certain depth value, such as the sky" `[MS App. G]` |
| 14 | The output is **not** a plain 3DGS `.ply` | appearance requires the four MLPs + codebooks to decode; `render.py --decode` is needed `[repo: README.md]`. (A `.ply` *is* also written, but it is the pre-compression model) |
