# §10 — Reproducibility checklist

⚠️ **Two-tier situation.** Training reproducibility is **zero** (no code). Inference
reproducibility is **the best in this comparison set** (pinned checkpoint, semver tag,
shipped benchmark harnesses). Both halves are documented below.

---

## 10.1 Seed handling

| Item | Status |
|---|---|
| Training seeds | ❌ **no training code at all** `[repo: src/romav2/romav2.py:172]`; the paper reports no seed, no repeats, no variance |
| Inference determinism | ✅ the forward pass runs under `@torch.inference_mode()` `[repo: romav2.py:162]` with **no stochastic layers**; the model is `.eval()`-ed at construction `[repo: romav2.py:107]` |
| `float32_matmul_precision` | ✅ **enforced** to `"highest"` with a `RuntimeError` `[repo: romav2.py:169-170]` — this is a *determinism* guarantee: it forbids TF32, whose reduced mantissa would make results hardware- and kernel-dependent |
| Sampling | ⚠️ `model.sample(preds, N)` draws matches from the confidence distribution `[repo: romav2.py:372]` — **the only stochastic step**, and it is not seeded internally. Seed `torch` yourself before calling it if you need repeatability |
| CUDA-kernel path | ⚠️ `local_corr` present (Linux) vs. the PyTorch fallback may differ at floating-point precision `[repo: local_correlation.py:4-7]`. Table 8 shows identical accuracy is expected, but bit-exactness across the two paths is `[unverified]` |

**The `float32_matmul_precision` guard is unusually principled** and worth noting: no other
folder in your set enforces numerical-precision settings at all.

## 10.2 Checkpoint and version pinning — **best-in-set**

`[repo: src/romav2/romav2.py:95-98]`:
```python
weights = torch.hub.load_state_dict_from_url(
    "https://github.com/Parskatt/RoMaV2/releases/download/v2.0.1/romav2.0.1.pt",
    map_location=device
)
```

| Item | Status |
|---|---|
| Checkpoint URL | ✅ **version-pinned to the `v2.0.1` release asset**, not a floating "latest" |
| Repo tag | ✅ `git describe` → `v2.0.1-2-g95c9968` — **the only tagged repo in your nine folders** |
| Package version | ✅ `version = "2.0.1"` `[repo: pyproject.toml]`, consistent with the tag |
| Dependency pinning | ⚠️ **lower bounds only** (`einops>=0.8.1`, `torchvision>=0.23.0`, bare `torch`) `[repo: pyproject.toml]`. A `uv.lock` is **not** present in this checkout — contrast `../RoMa/`, which does ship one |
| Network required | ⚠️ the checkpoint downloads on first construction. Pre-stage it in `TORCH_HOME` for an offline cluster |

⚠️ **The commit predates the paper.** Repo `95c9968` is 2026-04-20; arXiv v3 is 2026-07-06.
Whether the `v2.0.1` weights are the ones behind the paper's tables is `[unverified]` — the
shipped benchmark harnesses (§10.3) are the way to check.

## 10.3 Evaluation — reproducible, and the harnesses ship

`[repo: src/romav2/benchmarks/]` contains `mega1500.py`, `scannet1500.py`, `wxbs.py`,
`satast.py` — i.e. the harnesses for **Tables 4, 11**. Plus `[repo: scripts/eval_prep.sh]`
and tests `[repo: tests/test_mega1500.py, test_scannet1500.py, test_fps.py,
test_bidirectional.py, test_smoke.py]`.

Optional eval dependencies are declared explicitly: `kornia`, `opencv-python`, `wandb`,
`wxbs-benchmark`, `matplotlib` `[repo: pyproject.toml, extras "eval"]`.

⚠️ **Not shipped:** harnesses for Tables 6, 7 (dense matching on TA-WB, FlyingThings3D,
AerialMegaDepth, MapFree, ScanNet++ v2), Table 12 (Hypersim covariance), Table 13
(quantile perturbation), and the Table 8 memory benchmark. `[unverified]`

### ⚠️ Which setting produces which table

`[repo: src/romav2/romav2.py:119-160]` — this is the trap:

| Paper table | Required setting | Coarse | Fine | Bidir. | Threshold |
|---|---|---|---|---|---|
| Tab. 4 (MegaDepth-1500, ScanNet-1500) | `mega1500` / `scannet1500` | 800² | 1024² | ✅ | 0.05 |
| Tab. 11 (WxBS, SatAst) | `wxbs` / `satast` | 800² | 1024² | ✅ | 0.05 |
| Tab. 6, 7 (dense matching) | `base` | 640² | — | ❌ | None |
| Tab. 8 (runtime) | `base`, batch 8, H200 | 640² | — | ❌ | None |
| — | **`precise`** ← **library default** | 800² | **1280²** | ✅ | **None** |

**`RoMaV2()` with no arguments reproduces none of the paper's tables.** Always pass
`Cfg(setting=...)` explicitly.

## 10.4 Metric computation

Not directly comparable to the radiance-field folders — RoMa v2 reports **matching** and
**pose** metrics, not PSNR/SSIM/LPIPS. For completeness:

| Metric | Definition | Where |
|---|---|---|
| **AUC@{5,10,20}** | Area under the pose-error curve at 5°/10°/20° thresholds | `[paper Tab. 4]` |
| **EPE** | End-point error of the dense warp, in pixels at 640×640 | `[paper Tab. 6, 7]` |
| **PCK@{1,3,5}px** | % of pixels with warp error below the threshold | `[paper Tab. 2, 6, 7]` |
| **Robustness %** | Share of matches with error < 32 px (Table 1's linear probe) | `[paper Tab. 1]` |
| **mAA@10px** | mean average accuracy, WxBS | `[paper Tab. 11]` |
| **Success %** | rotation error < 5° **and** translation error < 2 m, RUBIK | `[paper §4.7]` |

⚠️ **All dense-matching metrics are resolution-dependent.** "Images are resized to 640 × 640"
`[paper Tab. 6, 7]`, and for UFM the paper resizes to 560×420 then **bilinearly upsamples**
back to 640×640 "as their precision degrades significantly for higher resolutions"
`[paper §4.3]`. That is a defensible accommodation, and it is disclosed — but it means UFM's
EPE includes an upsampling penalty. Note it when citing Tables 6–7.

## 10.5 Stated non-determinism

**None stated.** No seeds, repeats, or error bars anywhere in the paper.

Margins that would need them:
- **Table 4, MegaDepth-1500: RoMa 62.6 vs RoMa v2 62.8** — a **0.2 AUC** difference presented
  as "consistently outperforms all prior matchers" `[paper §4.1]`. Effectively a tie.
- Table 10 (backbone): WxBS 35.6 vs 34.2, Hypersim 78.1 vs 79.2 — ~1 point, opposite signs.
- Table 9 (EMA): ScanNet-1500 differs by **0.1–0.3** AUC.

The **large** margins — Tables 6/7 (37–85% EPE reduction), Table 2 (2.7× PCK@1px), Table 12
(+20.9 AUC@1), Table 13 (62.8 → 46.3 under perturbation) — are far more robust. **Cite those.**

## 10.6 Reproduction checklist for your cluster

| # | Action | Why |
|---|---|---|
| 1 | **Do not expect to retrain.** `assert not self.training` `[repo: romav2.py:172]` | no losses, no dataloaders, no EMA, no schedule (delta D-0) |
| 2 | **Pass `setting=` explicitly** for every experiment and record it | the default `precise` matches no published table (§10.3) |
| 3 | Ensure `torch.set_float32_matmul_precision("highest")` **process-wide** | hard `RuntimeError` otherwise `[repo: romav2.py:169-170]`; and note this **disables TF32 for everything else in the process** — important if you embed the matcher in a 3DGS run |
| 4 | Feed images in `[0, 1]`, and convert outputs with `to_pixel_coordinates` | matches are in **normalized `[−1,1]²`** `[repo: README.md]` — a classic integration bug |
| 5 | On Linux, install `fused-local-corr`; on Windows expect the fallback | 5.6 GB vs 4.8 GB, same results `[repo: pyproject.toml; local_correlation.py:4-7]` |
| 6 | Pre-stage the `v2.0.1` checkpoint in `TORCH_HOME` | auto-downloaded from GitHub releases on first construction `[repo: romav2.py:95-98]` |
| 7 | **Pin dependencies yourself** | `pyproject.toml` has lower bounds only and this checkout has **no `uv.lock`** (unlike `../RoMa/`) |
| 8 | Seed `torch` before `model.sample()` | the only stochastic step (§10.1) |
| 9 | Verify the checkpoint reproduces Table 4 using the shipped harnesses | the commit predates arXiv v3 by ~2.5 months `[unverified]` |
| 10 | **Hardware is your best match in the set** — H200 vs your H100 | same Hopper generation; timings and memory should transfer nearly unchanged (see [`08-computational-profile.md`](08-computational-profile.md)) |
| 11 | **If matching across modalities, benchmark `../RoMa/` v1 too** | v2 loses on WxBS (55.4 vs 60.8 mAA), conceded in `[paper §5]` and traced to IR↔RGB |
| 12 | For the `../EDGS/` integration, budget a **real port, not a swap** | EDGS reaches into v1-specific attributes (`sample_thresh`, `w_resized`, `upsample_preds`, `symmetric`, `attenuate_cert`) that do not exist in v2 `[EDGS repo: source/corr_init.py:137-177, 541]` |
