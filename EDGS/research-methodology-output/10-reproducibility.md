# §10 — Reproducibility checklist

## 10.1 Seed handling

`[repo: source/utils_aux.py:27-32]`:
```python
def set_seed(seed=42, cuda=True):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if cuda:
        torch.cuda.manual_seed_all(seed)
```
called as `set_seed(cfg.seed)` `[repo: train.py:20]` with `seed: 228`
`[repo: configs/train.yaml]`.

| Item | Status |
|---|---|
| Deterministic by default | ✅ seed **228** |
| `torch.cuda.manual_seed_all` | ✅ — one of only two folders in the set that call it (with `CompGS/`) |
| Exposed via config | ✅ `seed:` is a Hydra key, overridable on the CLI |
| cuDNN determinism flags | ❌ not set |
| Seed reported in the paper | ❌ no mention of seeds, repeats, or variance |

Second-best seeding hygiene in your comparison set, after `CompGS/` (which also averages
five runs).

**Residual non-determinism:** the 3DGS rasterizer backward uses atomic adds; `scipy`'s
`kmeans` for reference selection `[repo: corr_init.py:84]` is seeded via `np.random` ✅; RoMa's
`sample()` draws from the certainty map and consumes the torch RNG ✅. So a same-hardware
rerun should be close, but the **final Gaussian count is still run-dependent** because it
emerges from the opacity-decay-and-prune interaction (§10.4).

## 10.2 Train/test split — **the least documented part of this repo**

| Item | Status |
|---|---|
| Paper's statement | "Following standard protocol, we use **9, 2, and 2 scenes**" for Mip-NeRF 360 / T&T / Deep Blending `[paper §4.1]`. **Scene** counts are given; the **view** split is not stated. |
| Config | `gs.dataset.eval: false` `[repo: configs/gs/base.yaml]` |
| `train.py` | writes `"eval": False` **hard-coded** into the emitted `cfg_args` `[repo: train.py:38]` |
| Consequence | with `eval=False`, the vendored 3DGS `Scene` puts **all** views in train and leaves the test set **empty** — the same trap as `seasplat/` |
| Where the real split happens | presumably `full_eval.py` / `metrics.py` `[repo: full_eval.py, metrics.py]`, **not read in depth this pass** `[unverified]` |
| `llffhold` | not referenced anywhere in `source/`; inherited from the 3DGS submodule (default 8) `[unverified]` |

⚠️ **Action:** before reproducing, confirm how `full_eval.py` sets `eval=True`. A bare
`python train.py …` as documented in the README trains on **every** view and its
`evaluate()` call `[repo: trainer.py:107]` will find `getTestCameras()` empty.

One useful cross-check: the paper notes it **re-evaluated** ScaffoldGS and 3DGS-MCMC because
"they originally reported results for only **7 of the 9** Mip-NeRF360 scenes"
`[paper §4.2]` — good practice, and a reminder that Mip-NeRF 360 scene subsets differ across
the literature. Verify the subset before comparing to any other folder's numbers.

## 10.3 Exact metric computation

### (a) PSNR — mean of **per-channel** PSNRs (the 3DGS convention)

`[repo: source/losses.py:63-76]`:
```python
def psnr(img1, img2):
    """... NOT BATCHED! Shape should be (channels, height, width)."""
    mse = (((img1 - img2)) ** 2).view(img1.shape[0], -1).mean(1, keepdim=True)
    return 20 * torch.log10(1.0 / torch.sqrt(mse))
```

⚠️ **But it is called with a batch dimension**: `psnr(image.unsqueeze(0), gt_image.unsqueeze(0))`
`[repo: trainer.py:123]`, despite the docstring's "NOT BATCHED!". With shape `(1,3,H,W)`,
`img1.shape[0] == 1`, so `.view(1, -1).mean(1)` pools **all channels and pixels** into one
MSE — i.e. the call site accidentally produces **pooled-MSE PSNR**, the `seathru_NeRF`/
`CompGS` convention, *not* the per-channel-mean convention the function was written for.

> **This is a genuine, load-bearing subtlety.** Called as documented (`(3,H,W)`), this
> function is the standard 3DGS per-channel-mean PSNR. Called as it actually is
> (`(1,3,H,W)`), it is pooled-MSE PSNR — which is **lower** by Jensen. So EDGS's logged
> PSNR is on the *stricter* convention, while `seasplat/`, `mini-splatting/` and
> `compact3d/` use the looser one. If the paper's Table 1 numbers came from this code path,
> EDGS is being compared *against itself unfavourably* relative to 3DGS-family baselines
> evaluated with their own scripts. `[inferred from repo losses.py:75 + trainer.py:123;
> which code produced Table 1 is `[unverified]`]`

### (b) No disk round-trip ✅

Metrics are computed on in-memory float tensors, clamped to `[0,1]`
`[repo: trainer.py:120-121]`. Cleaner than `seasplat/` (8-bit PNG/JPEG), `CompGS/` (8-bit
PNG) and `mini-splatting/`'s `ms_c` (8-bit PNG); on a par with `mini-splatting/`'s main path.

### (c) Masking: none. Full-frame.

### (d) SSIM / LPIPS

- SSIM: `from source.losses import ssim` `[repo: trainer.py:11]` — the 3DGS implementation.
- LPIPS: **VGG**, `lpips.LPIPS(net='vgg')` `[repo: trainer.py:53]` ✅ — same backbone as
  `seasplat/`, `mini-splatting/`, `CompGS/`. Good: **LPIPS is the metric EDGS's claims rest
  on**, and it is comparable across the set.

### (e) Aggregation and cadence

Per-image → mean over the split `[repo: trainer.py:129-132]`. Evaluation runs every 500
steps up to 3000, then **every 1000 steps at offset 228** (`training_step % 1000 == 228`)
`[repo: trainer.py:97-99]` — a seed-flavoured magic number worth knowing about if you diff
logs.

### (f) What `#G` means

`len(self.GS.gaussians._xyz)` `[repo: trainer.py:112]` — the **rendered** Gaussian count ✅,
the same meaning as `mini-splatting/` and 3DGS, and **unlike** `CompGS/` (anchors).
⚠️ But `[paper Tab. 1]` footnotes that **ScaffoldGS's `#G` denotes derived splats from
anchors** — so even within this one table the column is not homogeneous.

## 10.4 Stated non-determinism

**None stated.** No seeds, repeats, or error bars in the paper — despite margins that need
them:

- Table 6: the full model beats "w/o SH init." by **0.22 dB**, and SSIM is **non-monotone**
  (0.839 vs 0.840).
- Table 5: LoFTR 27.79 vs DKM 27.81 — **0.02 dB**.
- Table 4: EDGS with vs without densification — **0.06 dB**.
- Table 3: AbsGS +0.12 dB, 3DGS-MCMC +0.14 dB.

The LPIPS margins (0.141 vs 0.176–0.202) are far larger and much more likely to survive
repetition. **Cite LPIPS.**

## 10.5 Reproduction checklist for your cluster

| # | Action | Why |
|---|---|---|
| 1 | **Know that the released code is arXiv-v1-era.** Only one code commit exists (`668e280`, 2025-04-21); the README promises updated code that has not shipped | `[repo: git log]`; **§3.5 SH init is absent** (delta D-1), so Table 6's `SH Init.` row is not reproducible |
| 2 | Pass **`train.gs_epochs=30000`** and **`train.no_densify=True`** explicitly | config defaults are `0` and `False`; the README's *prose* claims `no_densify` is "True by default" but the YAML says otherwise (delta D-10) |
| 3 | Set `wandb.mode=disabled` unless you want online logging | config default is `"online"`, contradicting the README (delta D-10) |
| 4 | **Confirm the train/test split** before trusting any metric | `eval` is `false` in the config and hard-coded `False` in `train.py:38`; the paper reports held-out numbers (§10.2) |
| 5 | Pre-stage **RoMa weights** on the cluster | downloaded at first use `[repo: corr_init.py:533-537]`; needs network access |
| 6 | Build the two CUDA extensions with `TORCH_CUDA_ARCH_LIST` including `9.0` | `diff-gaussian-rasterization`, `simple-knn` from the vendored 3DGS submodule `[repo: install.sh]` |
| 7 | **Least stack friction in the set** — CUDA 12.1, Python 3.10 | `[repo: install.sh]`; compare `mini-splatting/` (Py 3.7/CUDA 11.6), `seathru_NeRF/` (JAX 0.4.1) |
| 8 | Budget peak VRAM for **initialization**, not training | up to `180 × 15 000 = 2.7 M` candidate Gaussians (3.6 M at the README's 20 000) plus RoMa activations `[inferred]`; never reported in the paper |
| 9 | Decide one **PSNR convention** and recompute every method | EDGS's call site yields **pooled-MSE** PSNR despite a per-channel function (§10.3a) — an easy source of a 0.1–0.5 dB phantom difference |
| 10 | Run ≥3 seeds (`seed=` is a Hydra key) and report dispersion | Tables 3–6 have 0.02–0.22 dB margins with no error bars (§10.4) |
| 11 | Record whether `reduce_opacity` and `max_lr` were on | both default `True` and are undocumented optimizer changes (deltas D-3, D-4); Table 3's composability result presumably used them |
| 12 | Use **`nns_per_ref ≥ 2`** for the paper's method | `nns_per_ref=1` silently switches to `init_gaussians_with_corr_fast`, a different code path `[repo: trainer.py:230-233]` |
| 13 | For the Table 1 comparison, verify the **Mip-NeRF 360 scene subset** | the paper re-evaluated ScaffoldGS and 3DGS-MCMC because they used **7 of 9** scenes `[paper §4.2]` |
| 14 | Normalise `#G` on **rendered** primitives | Table 1's own footnote flags ScaffoldGS's column as derived-splats, and `CompGS/` reports anchors (§10.3f) |
| 15 | **If applying to underwater data**, expect the matcher to be the bottleneck | RoMa confidence collapses on water/textureless regions; Table 5 shows a bad matcher (RAFT, 26.90) drops EDGS *below* 3DGS (27.49). Consider swapping in `../RoMaV2/` and re-running Table 5's protocol |
