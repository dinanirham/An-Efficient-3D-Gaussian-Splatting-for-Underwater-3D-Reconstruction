# §10 — Reproducibility checklist

> ⚠️ `[paper …]` = **arXiv:2404.09458v1** = `../../CompGS.pdf`.

## 10.1 Seed handling — **the most thorough in the comparison set**

`[repo: Train.py:10-24]`:
```python
# fix random seed
def setup_seed(seed: int) -> None:
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)      # ← the only folder in this set that does this
    np.random.seed(seed)
    random.seed(seed)
...
setup_seed(seed=3407)
```

| Item | CompGS | `seasplat/` | `seathru_NeRF/` | `mini-splatting/` |
|---|---|---|---|---|
| Deterministic by default | ✅ seed 3407 | ❌ `-1` → OS entropy | ✅ PRNGKey 20200823 | ✅ seed 0 |
| `torch.cuda.manual_seed_all` | ✅ | ❌ | n/a (JAX) | ❌ |
| cuDNN determinism flags | ❌ | ❌ | ❌ | ❌ |
| Seed exposed on CLI | ❌ hard-coded | ✅ `--seed` | ❌ | ❌ |
| Seed reported in paper | ❌ | ❌ | ❌ | ❌ |

**And the paper reports averaged repeats** — the only one in your set that does:

> "each method undergoes **five independent evaluations** in a consistent environment to
> mitigate the effect of randomness, and the average results of the five experiments are
> reported." `[paper §4.1]`

⚠️ But: **no dispersion is published** — only means. And it is ambiguous whether "five
independent evaluations" means five *trainings* or five *evaluations of one trained model*.
Given the deterministic seed, five re-evaluations of the same checkpoint would be nearly
identical, so the useful reading is five trainings — `[unverified]`.

Residual non-determinism regardless of seeding: the 3DGS rasterizer backward uses atomic
adds (non-deterministic in float), and adaptive-control growing draws random masks
`[repo: AdaptiveControl.py:57]`. So `N` remains run-dependent.

## 10.2 Train/test split

`[repo: Modules/Common/Datasets.py:20, 45-46]`:
```python
def __init__(self, ..., eval_interval: int = 8, ...):
    self.train_samples = {idx: s for idx, s in enumerate(samples) if idx % eval_interval != 0}
    self.test_samples  = {idx: s for idx, s in enumerate(samples) if idx % eval_interval == 0}
```

| Item | Value |
|---|---|
| Rule | every 8th view held out |
| Paper's statement | "one view is selected from every eight views for testing, with the remaining views used for training" `[paper §4.1]` |
| Match | ✅ **exact**, and explicitly stated in the paper — better than `seasplat/` |
| Scene selection | "the scenes specified by 3DGS [17] are involved in evaluations" `[paper §4.1]` |
| Initial points | "the sparse point clouds **provided by 3DGS** are utilized to initialize our anchor primitives" `[paper §4.1]` — i.e. not re-run COLMAP. Good for comparability. |
| `eval_interval` overridable | ❌ Python default only, no config key |

⚠️ **The training loop samples views without replacement from a shuffled stack**
`[repo: Datasets.py:63-67]` and `[repo: TrainerCompGS.py:73]` calls `self.dataset[0]` —
the index `0` is **ignored** in training mode, which is confusing but correct.

## 10.3 Exact metric computation

### (a) PSNR — **pooled MSE** (the `seathru_NeRF/` convention, NOT the 3DGS one)

`[repo: Modules/TesterCompGS.py:153-159]` (and identically `[repo: TrainerCompGS.py:155-161]`):
```python
original_img, rendered_img = Image.open(original_img_path), Image.open(rendered_img_path)
original_img = torch.tensor(np.array(original_img)).permute(2,0,1).float() / 255.
rendered_img = torch.tensor(np.array(rendered_img)).permute(2,0,1).float() / 255.
rendered_mse = F.mse_loss(original_img, rendered_img)
psnr = 10 * torch.log10(1. / rendered_mse).item()
```

`F.mse_loss` with default reduction pools **every** element — H, W and all 3 channels — into
one scalar. This is the standard definition, and it is **not** what 3DGS,
`seasplat/`, `mini-splatting/` or `compact3d/` compute (they average three per-channel
PSNRs, which by Jensen is always ≥).

> ⚠️ **This matters directly for Tables 1–3**, which place CompGS beside
> `Navaneet et al. [33]` (= `compact3d/`) and three other 3DGS-derived baselines. The
> paper says all baselines were re-run "in a consistent environment" `[paper §4.1]`, but
> does **not** say whether the *metric code* was unified. If the baselines' own metric
> scripts were used, the comparison mixes two PSNR conventions in the direction that
> **favours the baselines**. `[unverified — I could not confirm which metric code produced
> the baseline rows]`

### (b) 8-bit PNG disk round-trip

Both the render and the ground truth are written to PNG and re-opened before scoring
`[repo: TesterCompGS.py:71-75]`. Same situation as `seasplat/` (which additionally may use
JPEG) and `mini-splatting/`'s `ms_c`; **unlike** `mini-splatting/`'s main path, which scores
float tensors.

### (c) Masking: none. Full-frame.

### (d) SSIM / LPIPS

- SSIM: `pytorch_msssim.ssim(..., data_range=1., size_average=True)`
  `[repo: TesterCompGS.py:9, 162]` — a *different implementation* from 3DGS's, though with
  matching default window (11×11, σ=1.5).
- LPIPS: **VGG**, `version='0.1'` `[repo: TesterCompGS.py:37]` — matches `seasplat/` and
  `mini-splatting/` ✅.

### (e) What is measured, and when

Two separate evaluation paths, and they are **not** equivalent:

| Path | When | What it measures |
|---|---|---|
| `TrainerCompGS.eval()` → `eval_training/results.json` | right after training, **before** compression | PSNR only, on the **uncompressed** model `[repo: TrainerCompGS.py:111-169]` |
| `TesterCompGS` → `eval/results.json` | after decompression | PSNR + SSIM + LPIPS on the **decompressed** model, plus `render_time`, `decompression_time` `[repo: TesterCompGS.py]` |

**The paper's tables must be the second path** (they report SSIM/LPIPS and sizes). Confirm
you use `Test.py`, not the in-training eval, or you will report numbers for a model that was
never actually coded.

### (f) Model size accounting — **honest, and unusual**

`[repo: Modules/TrainerCompGS.py:341-348]`:
```python
size_results = self.gaussian_model.save_compressed_params(...)   # bitstreams.npz
weights_size = os.path.getsize(weights_path) / 1024 / 1024       # weights.pth
size_results['weights_size'] = weights_size
size_results['total'] = size_results['total'] + weights_size     # ← MLPs ARE counted
```

The reported size = `bitstreams.npz` + `weights.pth`. Fig. 8 breaks the weights out as
**29.56% / 37.78% / 45.98%** of the bitstream at λ = 0.001 / 0.005 / 0.01 `[paper Fig. 8]`.

⚠️ **Before tabulating against other methods, verify they count their decoders too.**
`compact3d/` must store a codebook; `mini-splatting/`'s `ms_c` has no network at all.

## 10.4 Stated non-determinism

Partially addressed: five averaged runs `[paper §4.1]` — but **no variance, no error bars,
no seed reported**. Given that Table 6's `K=5` vs `K=10` gap is **0.08 dB** and Table 4's
PSNR deltas are ~0.1 dB, dispersion would be needed to support those readings.

## 10.5 Reproduction checklist for your cluster

| # | Action | Why |
|---|---|---|
| 1 | **Replace `../../CompGS.pdf`** with arXiv:2404.09458 | the local file is `compact3d`'s paper (identical MD5) — see [`00-index.md`](00-index.md) |
| 2 | **Download and compile G-PCC / MPEG TMC13**, then set `gpcc_codec_path` in every config | **hard blocker** — anchor positions are coded by G-PCC `[repo: Model.py:326]`; nothing compresses without it `[repo: README.md step 4]` |
| 3 | Fill in the `XXX` placeholders in `Configs/*.yaml` (`dataset.root`, `image_folder`, `save_directory`, `gpcc_codec_path`) | all four ship unset `[repo: Configs/*.yaml]` |
| 4 | Use `Scripts/derive_train_eval_scripts.py` to generate the **three λ** runs | the YAMLs ship only `λ = 0.001`; `0.005` and `0.01` come from `[repo: Scripts/derive_train_eval_scripts.py:47-52]` (delta D-13) |
| 5 | Report the **rendered** primitive count, not `num_gaussians` | `num_gaussians` = **anchors**; rendered is up to `10×` more `[repo: TrainerCompGS.py:367; README.md]` (delta D-9). Instrument `[repo: Prediction.py:65]` |
| 6 | **Decide one PSNR convention and recompute every method** | CompGS uses pooled-MSE; 3DGS/`seasplat/`/`mini-splatting/`/`compact3d/` use per-channel-mean (§10.3a) |
| 7 | Verify competitors' reported sizes include their decoders | CompGS counts `weights.pth`; at λ=0.01 that is 46% of the bitstream (§10.3f) |
| 8 | Run ≥3 seeds by parameterising `[repo: Train.py:24]` (currently hard-coded 3407) and report dispersion | Table 6's margins are 0.08 dB; Table 4's ~0.1 dB |
| 9 | Note that adaptive-control frequency **scales with view count** | intervals are `base × M` `[repo: TrainerCompGS.py:287, 303-304]` (delta D-7). A new dataset with a different `M` gets a different schedule for free |
| 10 | Re-tune `voxel_size`, `grad_threshold`, `opacity_threshold` for any new domain | they differ 10× / 1.25× / 1.6× between the shipped Mip-NeRF 360 and T&T configs, and appear nowhere in the paper (delta D-8) |
| 11 | Use `Test.py` (post-decompression) for reported metrics, not the in-training `eval()` | two different evaluation paths (§10.3e) |
| 12 | Expect the **most modern stack** in this comparison set | Python ≥ 3.10 `[repo: README.md]`; least likely to fight CUDA 12 / H100. Note `torch_scatter` needs matching torch/CUDA wheels |
| 13 | Log estimated `R` vs. actual `.npz`+`weights.pth` bytes | the train/eval quantization surrogates differ (noise vs STE); the paper never reports the gap `[unverified]` |
