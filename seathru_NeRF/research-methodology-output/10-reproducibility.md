# §10 — Reproducibility checklist

## 10.1 Seed handling — **deterministic and hard-coded** (the opposite of SeaSplat)

`[repo: train.py:51-54]`:
```python
rng = random.PRNGKey(20200823)
# Shift the numpy random seed by host_id() to shuffle data loaded by different hosts.
np.random.seed(20201473 + jax.host_id())
...
rng = rng + jax.host_id()   # Make random seed separate across hosts.   [repo: train.py:107]
```

| Item | Status |
|---|---|
| JAX PRNG seed | **fixed at `20200823`** — no CLI/gin override |
| NumPy seed (controls ray sampling, `datasets.py:472-487`) | **fixed at `20201473 + host_id`** |
| Multi-host determinism | seeds are offset per host, so a run is reproducible **for a fixed device count** but changes if you change the number of hosts/devices |
| Config-level toggle | `Config.randomized` gates whether the RNG key is passed into the model `[repo: train_utils.py:271]` |
| Seed reported in the paper | ❌ no mention of seeds, repeats, or variance anywhere |

**This is materially better than SeaSplat** (whose default seed is `-1` → OS entropy, and
which never seeds CUDA at all). A same-device-count rerun of SeaThru-NeRF should be close to
bit-reproducible, modulo XLA non-determinism in reductions.

**But:** still **single runs, no error bars**. That matters most for Table 1, where the
"Ours vs I" margin is **0.07 dB** — see [`04-loss.md`](04-loss.md) §4.4. A 0.07 dB claim
from one seed on one scene is not statistically supported, whatever the seeding hygiene.

## 10.2 Train/test split

`[repo: internal/datasets.py:717-719]`:
```python
train_indices = all_indices % config.llffhold != 0
...
utils.DataSplit.TEST: all_indices[all_indices % config.llffhold == 0],
```
with `llffhold: int = 8` `[repo: internal/configs.py:60]` — *"Use every Nth image for the
test set. Used only by LLFF."*

| Item | Value |
|---|---|
| Rule | every 8th image held out, by index order |
| Paper's statement | "a total of **20, 20 and 18** images respectively, from which **three are set aside for validation** in each set" `[paper §5.1]` |
| Consistency check | `20 → {0, 8, 16}` = 3 ✅; `18 → {0, 8, 16}` = 3 ✅ | 
| Override | `llffhold` is a gin-exposed `Config` field, so it *can* be changed; the released UW gin does not touch it (uses the default 8) |
| `eval_on_train` | `False` `[repo: configs/llff_256_uw.gin]` |

**Paper and code agree exactly, and the arithmetic confirms it.** `[inferred: paper §5.1 vs
repo datasets.py:717-719 + configs.py:60]` This is a notably cleaner situation than
SeaSplat's, where `--eval` defaults off and the README's command omits it.

⚠️ **Cross-method caveat.** SeaSplat evaluates on the *same* SeaThru-NeRF scenes with the
*same* `llffhold = 8` rule `[seasplat repo: scene/dataset_readers.py:262-263]`, so the
held-out frames coincide. Good — the splits are comparable. What is **not** comparable is
what is measured on them (§10.3).

## 10.3 Exact metric computation — **pooled-MSE PSNR on LINEAR, non-photofinished images**

This is the item the methodology singles out as silently varying across underwater papers,
and here it varies **in two independent ways** from SeaSplat.

### (a) PSNR formula: pooled MSE over all pixels *and* channels — the standard definition

`[repo: internal/image.py:136]`:
```python
psnr = float(mse_to_psnr(((rgb_pred - rgb_gt)**2).mean()))
```
with `[repo: internal/image.py:29-31]` `mse_to_psnr(mse) = -10/ln(10) · ln(mse)`.

`.mean()` with no axis argument pools **every** element — height, width and all three
channels — into a single MSE.

**Contrast with SeaSplat** `[seasplat repo: utils/image_utils.py:17-19]`, which computes
`mse` **per channel** (`view(img.shape[0], -1).mean(1)`), converts each to a PSNR, then
averages the three PSNRs. By Jensen's inequality
`mean_c(PSNR_c) ≥ PSNR(pooled MSE)`, with the gap growing as the channels' errors diverge —
**and underwater is the regime of maximum channel divergence** (red is attenuated to
near-nothing, blue is not).

> **Therefore SeaSplat's Table I, which places its own numbers beside "STN" (SeaThru-NeRF)
> numbers, is comparing two different PSNR conventions, in the direction that favours
> SeaSplat.** This is a first-class, citable comparability defect. Verified from both
> codebases at the commits listed in each folder's `00-index.md`. `[inferred: repo
> internal/image.py:136 vs seasplat repo utils/image_utils.py:17-19]`

### (b) Colour space: **linear**, pre-photofinishing

`[paper §4.5]`: "The loss function and metrics are calculated on the output **before any
post-processing**."
`[paper §5.1]`: "we apply photofinishing on all linear reconstructed scenes to enhance
scene contrast and appearance … This is done to improve visualization for easier
qualitative comparisons, while **PSNR is calculated on the original non-photofinished
linear images**."

So both the render and the GT are **linear** (the input RAW frames, white-balanced with
0.5% clipping). SeaSplat's inputs are white-balanced RAW too `[seasplat paper §V.A.a]`, but
its metric pipeline re-reads **8-bit PNG/JPEG files from disk**
`[seasplat repo: train.py:584-644]` — i.e. quantised, and possibly JPEG-compressed.

**PSNR on linear data and PSNR on 8-bit sRGB-ish data are not the same quantity.** Linear
data has most of its mass at low values, where squared error is small, which generally
*raises* PSNR. This is a second, independent axis on which the two papers' numbers are not
interchangeable.

### (c) Masking: none

No mask is applied at metric time `[repo: internal/image.py:136]`. Full-frame.

The **"red square" rows of Table 2 are a form of spatial restriction** — they are metrics
computed on a *zoomed crop* of a far-field region `[paper Tab. 2; Fig. 5 caption]`, not on
a mask. They should never be quoted as full-frame numbers; the gap between the two
(21.83 vs 33.80 on Red Sea) is 12 dB.

### (d) What is scored

`Ĉ` (in-medium render) vs `C*`. **`J` (the restored image) is never scored** — it is a
`stop_gradient` output `[repo: render.py:319]` with no ground truth. Identical epistemic
situation to SeaSplat's `Ĵ`. All restoration comparisons in Fig. 6 are qualitative.

### (e) SSIM / LPIPS

Reported in Table 2 but the paper does not state the SSIM window or the LPIPS backbone.
`[unverified]` — I did not trace `internal/image.py`'s metric harness in full this pass.
Since SeaSplat uses **VGG**-LPIPS `[seasplat repo: train.py:644]` and the two papers'
LPIPS values are placed side by side in SeaSplat's Table I, the backbone should be
confirmed before quoting them together.

## 10.4 Stated non-determinism

**None stated in the paper.** No seeds, repeats, or variance reported. The code is
deterministic by construction (§10.1) but the paper does not claim or characterise this.

Two sources of residual non-determinism regardless of seeding:
- XLA reduction ordering on GPU is not guaranteed bitwise-stable across compilations.
- `grad = jax.tree_util.tree_map(jnp.nan_to_num, grad)` `[repo: train_utils.py:313]`
  silently converts NaN/Inf gradients to finite values. A run that produces NaNs will not
  crash — it will quietly train differently. Worth logging if you reproduce.

## 10.5 Reproduction checklist for your cluster

| # | Action | Why |
|---|---|---|
| 1 | **Budget a JAX/CUDA upgrade.** `install.sh` pins `jaxlib-0.4.1+cuda11.cudnn82`; H100 needs CUDA 12. Also Python 3.9, `flax==0.6.1`, `chex==0.1.5` | `[repo: install.sh; requirements.txt; README.md]` — the stack is late-2022 and predates Hopper support |
| 2 | Use `scripts/train_llff_uw.sh` → `configs/llff_256_uw.gin` as the reference config, **not** `internal/configs.py` defaults | several dataclass defaults (`density_bias`, `water_bias`, `distortion_loss_mult`) are overridden in gin (delta D-12, D-7) |
| 3 | If you want the paper's architecture, **edit `internal/models.py:716`** (`net_depth_water = 1 → 6`) and use `net_width` (256) instead of `net_width_viewdirs` (128) | `net_depth_water` is set in `setup()` and is not gin-bindable (delta D-1) |
| 4 | If you want view-dependent object colour as §4.3 describes, set `UWMLP.uw_rgb_dir = True` | released gin has it `False` (delta D-3) |
| 5 | To reproduce ablation III, set **both** `Config.gen_eq = True` **and** `UWMLP.gen_eq = True` | the gin file's own comment warns about this (delta D-11) |
| 6 | Ablation I → `uw_fog_model = True`; ablation II → `uw_old_model = True` (both `Config.` and `UWMLP.` bindings) | `[repo: configs.py:177,181]` |
| 7 | Run ≥3 seeds by patching `train.py:51,54`, and report dispersion | Table 1's margins are 0.07–0.40 dB with no error bars |
| 8 | Keep batch 16 384 if memory allows; if you reduce it, **scale `lr_init` proportionally** | `[repo: README.md]` says so explicitly; the UW gin's 8× LR over the base config is exactly this scaling (delta D-8) |
| 9 | **Decide one PSNR convention and one colour space, then recompute every method** | this method uses pooled-MSE PSNR on linear images; SeaSplat uses per-channel-mean PSNR on 8-bit files. Numbers from the two papers cannot be tabulated together as-published (§10.3a, §10.3b) |
| 10 | Report full-frame and "red square" crop metrics separately and label them | the gap is up to 12 dB on the same scene (§10.3c) |
| 11 | Log whether `nan_to_num` ever fires on the gradient tree | silent NaN suppression at `train_utils.py:313` (§10.4) |
