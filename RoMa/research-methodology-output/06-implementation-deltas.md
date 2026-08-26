# §6 — Implementation deltas from the paper

**Repo state inspected:** `github.com/Parskatt/RoMa`, commit
`77f8d68803526dcddfd9b7a46bc76125bdc25f15`, `git describe --tags` → **`v0.1.2-4-g77f8d68`**,
branch `main`, 2026-01-23.

**Paper inspected:** `../../RoMa.pdf` = arXiv:2305.15404**v2**, 11 Dec 2023 (CVPR 2024).
The repo HEAD is ~2 years newer than the paper, so some deltas may be post-publication drift;
those are marked 🔶.

**Files read directly:** `romatch/losses/robust_loss.py`, `romatch/models/encoders.py`,
`romatch/models/model_zoo/roma_models.py`, `romatch/models/matcher.py` (partial),
`experiments/train_roma_outdoor.py`, `README.md`, plus `git log`/`git describe`.

> ✅ **Training code is released**, unlike `../RoMaV2/`. Everything below is a genuine
> code-vs-paper comparison rather than an absence.

---

## D-1 — ⭐ **The Charbonnier scale `c` is 1e-4 in code, 0.03 in the paper — 300× apart**

`[paper §3.4]`: "we model the output of the refinement at scale `i` as a generalized
Charbonnier [3] (with `α = 0.5`) distribution … and `s = 2^i c`. **In practice, we choose
c = 0.03.**"

`[repo: experiments/train_roma_outdoor.py:214-220]`:
```python
depth_loss = RobustLosses(
    ce_weight=0.01,
    local_dist={1:4, 2:4, 4:8, 8:8},
    local_largest_scale=8,
    depth_interpolation_mode=depth_interpolation_mode,
    alpha = 0.5,
    c = 1e-4,)
```

`α = 0.5` ✅ matches. **`c = 1e-4` ✗ does not.** (The class default is a third value, `1e-3`
`[repo: robust_loss.py:25]`.)

This is not a cosmetic constant: `c` **is** the transition point between the loss's quadratic
and sub-linear regimes — the very quantity Fig. 4 plots. `[repo: robust_loss.py:90-92]`:
```python
cs = self.c * scale
reg_loss = cs**a * ((x/(cs))**2 + 1**2)**(a/2)
```
With `c = 0.03` the loss behaves like L2 out to ~0.03 in normalized `[−1,1]` units (≈15 px at
512²); with `c = 1e-4` that window is ~0.05 px. **The deployed model is vastly more
aggressive about down-weighting residuals than the paper's analysis describes.**

**Severity: high.** Anyone reimplementing from §3.4 trains a materially different objective.
🔶 possible post-publication tuning, but the paper states 0.03 as what was used.

---

## D-2 — An entire supervision-gating mechanism is undocumented

`[repo: romatch/losses/robust_loss.py:138-141]`:
```python
if self.local_largest_scale >= scale:
    prob = prob * (
            F.interpolate(prev_epe[:, None], size=(h, w), mode="nearest-exact")[:, 0]
            < (2 / 512) * (self.local_dist[scale] * scale))
```
with `local_dist = {1:4, 2:4, 4:8, 8:8}`, `local_largest_scale = 8`
`[repo: train_roma_outdoor.py:216-217]`, and `prev_epe` detached from the coarser scale
`[repo: robust_loss.py:160]`.

**A refiner at scale `s` is supervised only at pixels where the previous, coarser scale was
already within ≈`local_dist[s]·s` pixels.** The paper describes refinement as conditional on
a previous estimate `[paper §3.1, §3.4]` but never mentions a hard supervision gate.

Two consequences worth stating:
- It **partly substitutes for** the robust loss — the extreme outliers `L_fine` was designed
  to tolerate are largely masked out before they reach it.
- The class also exposes `local_loss=True`, `smooth_mask=False`, `mask_depth_loss=False`,
  `relative_depth_error_threshold=0.05` `[repo: robust_loss.py:13-25]`, none of which appear
  in the paper.

**Severity: high.**

---

## D-3 — All warp losses are masked to `prob > 0.99`

`[repo: robust_loss.py:51, 71, 91]` — `cls_loss`, `delta_cls_loss` and `reg_loss` are each
indexed `[prob > 0.99]`. The certainty BCE is deliberately left unmasked (it needs negatives),
and there is a guard for the all-zero case:
```python
if not torch.any(cls_loss):
    cls_loss = (certainty_loss * 0.0)  # Prevent issues where prob is 0 everywhere
```
`[repo: robust_loss.py:53-54]`

The paper's Eqs. 13–18 approximate `q` "with a discrete set of known correspondences
`{x^A, x^B}`" `[paper §3.4]` — which is *consistent* with hard masking but does not specify a
threshold, let alone 0.99.

**Severity: medium.**

---

## D-4 — `λ` (the marginal/conditional weight) is never given a value in the paper

`[paper Eq. 14]`: "Following DKM [17] we add a hyperparameter `λ` that controls the weighting
of the marginal compared to that of the conditional."

`[repo: train_roma_outdoor.py:215]`: `ce_weight = 0.01`, applied as
`cls_loss + 0.01·certainty_loss` `[repo: robust_loss.py:145, 158]`.

**Severity: medium** — a two-orders-of-magnitude weighting that a reimplementation would have
to guess.

---

## D-5 — Training schedule, optimizer and data construction are all undocumented

`[paper §4.2]` says only: "We use the training setup as in DKM [17]", plus the two canonical
learning rates and the resolutions.

Absent from the paper but present in `[repo: experiments/train_roma_outdoor.py]`:

| Item | Value | Line |
|---|---|---|
| Optimizer | **AdamW**, `weight_decay = 0.01` | `:225` |
| Budget | `N = 32 × 250000` ⇒ **250k steps at batch 32** | `:193` |
| LR schedule | `MultiStepLR`, single milestone at **90%** | `:226-227` |
| Dataset | MegaDepth `train_loftr`, built **twice** and concatenated: `min_overlap=0.01` **and** `min_overlap=0.35` | `:201-210` |
| Scene weighting | `weight_scenes(..., alpha = 0.75)` | `:212` |
| Augmentation | `use_horizontal_flip_aug=True`, `shake_t=32`, `rot_prob=0` | `:199-206` |
| Precision | AMP `float16`; DDP; gradient clipping | `:187, 248` |
| `attenuate_cert` | **`False` during training** (default `True` at inference) | `:187` vs `roma_models.py:56` |

The **two-way `min_overlap` concatenation** is a deliberate easy/hard curriculum mixture and
is arguably a methodological choice, not a detail.

Also note `[paper §4.2]` says the training split "consists of randomly sampled pairs from the
MegaDepth **and ScanNet** sets", whereas `train_roma_outdoor.py` uses **MegaDepth only** — the
ScanNet model is a separate script `[repo: experiments/roma_indoor.py]`, consistent with the
paper's later sentence that ScanNet-1500 is evaluated with a ScanNet-trained model.

**Severity: medium** (reproduction), **low** (correctness).

---

## D-6 — The coarse scale is keyed `16` although the stride is `14`

`[repo: robust_loss.py:106]`: `scale_weights = {1:1, 2:1, 4:1, 8:1, 16:1}`;
`[repo: matcher.py:856]`: `corresps[16]["certainty"]`.

DINOv2's patch size is **14**, and the code asserts `resolution % 14 == 0`
`[repo: roma_models.py:71-72]`. The `16` key is a naming artifact inherited from a
power-of-two convention. Harmless, and a guaranteed source of confusion when reading the loss
against `[paper §3.1]`'s "strides {1, 2, 4, 8}" plus a stride-14 coarse level.

**Severity: cosmetic**, high trap value.

---

## D-7 — `scale_weights` exists, is documented in a comment, and is unused

`[repo: robust_loss.py:105-106]`:
```python
# scale_weights due to differences in scale for regression gradients and classification gradients
scale_weights = {1:1, 2:1, 4:1, 8:1, 16:1}
```
All ones — hard-coded, not a constructor argument. So the mechanism the comment describes is
inert. This is *consistent* with `[paper §3.4]`'s claim that no scaling needs tuning, but the
code implies it was once needed.

**Severity: low** (informational — it corroborates the paper's claim).

---

## D-8 — VGG19 fine features are **not** ImageNet-pretrained

`[repo: roma_models.py:197]`: `cnn_kwargs=dict(pretrained=False, amp=True)`, feeding
`VGG19(...)` which otherwise would load `tvm.vgg19_bn(weights=weights)`
`[repo: encoders.py:13]`.

`[paper §3.2]` and Table 2 Setup III say only "`F_fine,θ = VGG19`". Given that the paper's
argument is about *specialisation*, training the fine encoder from scratch is coherent — but
a reader would reasonably assume pretrained weights, especially since the coarse encoder is
explicitly a pretrained foundation model.

Note the same choice in `../RoMaV2/` `[RoMaV2 repo: features.py:182]`, and that both use the
**batch-norm** variant (`vgg19_bn`) where the papers say "VGG19".

**Severity: low–medium.**

---

## D-9 — `attenuate_cert`: an inference-only mechanism, trained without it

`[repo: matcher.py:854-860]`:
```python
if self.attenuate_cert:
    low_res_certainty = F.interpolate(corresps[16]["certainty"], size=(hs, ws), ...)
```
Default `True` at inference `[repo: roma_models.py:56]`, explicitly `False` in training
`[repo: train_roma_outdoor.py:187]`.

The certainty the model reports at test time is therefore **not** the certainty it was
trained to produce. Not mentioned in the paper.

**Severity: medium** — and directly relevant to `../EDGS/`, which thresholds on exactly this
signal.

---

## D-10 — `TinyRoMa`: a whole model variant absent from the paper

`[repo: romatch/models/tiny.py]`, `[repo: romatch/losses/robust_loss_tiny_roma.py]`,
`[repo: experiments/train_tiny_roma_v1_outdoor.py]`,
`[repo: experiments/eval_tiny_roma_v1_outdoor.py]`, `[repo: demo/demo_match_tiny.py]`,
`[repo: tests/test_match_modes.py]`.

A smaller architecture with its own loss, training script, evaluation and demo. Nothing in
`../../RoMa.pdf` mentions it. Almost certainly post-publication 🔶, but a reader browsing the
repo will find two models and no guidance on which is "RoMa".

**Severity: low**, high trap value.

---

## D-11 — Local correlation kernel silently disabled on non-Linux

`[repo: roma_models.py:60-62]`:
```python
if sys.platform != "linux":
    use_custom_corr = False
    warnings.warn("Local correlation is not supported on non-Linux platforms, ...")
```
Same situation as `../RoMaV2/`. Relevant to your Windows project root: results should be
identical, memory/throughput are not. `[unverified]` whether numerics are bit-identical.

**Severity: low.**

---

## ✅ Verified-correct (recorded because §6 is not only for disagreements)

| Paper claim | Code | |
|---|---|---|
| DINOv2 kept frozen throughout training `[§3.2]` | stored in a list to hide it from DDP `[encoders.py:50]`; `.eval()` `[:42]`; `torch.no_grad()` `[:61]` | ✅ (belt and braces) |
| Decoupled coarse/fine encoders `[§3.2, Eq. 7]` | `CNNandDinov2` = separate VGG19 + DINOv2 paths `[encoders.py:29-64]` | ✅ |
| Gaussian Process match encoder retained from DKM `[§3.1]` | `gp_dim = 512` `[roma_models.py:84]` | ✅ |
| Decoder: 5 blocks, 8 heads, hidden 1024, MLP 4096 `[§3.3]` | `[Block(1024, 8, MemEffAttention) for _ in range(5)]`, `decoder_dim = 512+512` `[roma_models.py:84-91]` | ✅ exact |
| `pos_enc = False` `[§3.3]` | `pos_enc=False` `[roma_models.py:96]` | ✅ |
| `K = 64 × 64` anchors, output `K + 1` `[§3.3]` | `cls_to_coord_res = 64`; output `64**2 + 1` `[roma_models.py:87, 91]` | ✅ |
| Anchors a tight cover with no overlap/holes `[footnote 2]` | `linspace(−1+1/64, 1−1/64, 64)` `[robust_loss.py:48]` | ✅ |
| `α = 0.5` `[§3.4]` | `alpha = 0.5` `[train_roma_outdoor.py:219]` | ✅ |
| Charbonnier form `[Eqs. 15-16]` | `cs**a * ((x/cs)**2 + 1)**(a/2)` `[robust_loss.py:92]` | ✅ |
| BCE on matchability `[§3.4]` | `binary_cross_entropy_with_logits` `[robust_loss.py:52, 88]` | ✅ |
| No scaling needed between coarse and fine `[§3.4]` | `scale_weights` all `1` `[robust_loss.py:106]` | ✅ |
| Canonical LRs 1e-4 / 5e-6 at batch 8 `[§4.2]` | `STEP_SIZE*1e-4/8`, `STEP_SIZE*5e-6/8` `[train_roma_outdoor.py:223-224]` | ✅ |
| Ablation at 448², final model at 560² `[§4.2]` | `resolutions = {"low":(448,448), "medium":(14*8*5,...)}`, default `'medium'` `[train_roma_outdoor.py:23, 301]` | ✅ |
| `sample_thresh = 0.05`, balanced sampling `[§4.3]` | `sample_thresh=0.05`, `sample_mode="threshold_balanced"` `[roma_models.py:54-55]` | ✅ |

---

## Items I could *not* verify in this pass

| Claim | Status |
|---|---|
| Table 1's linear-probe experiment (VGG19 / RN50 / DINOv2 frozen features) | `[unverified]` — "Further details … are provided in the supplementary material" `[paper §3.2]`; no probe script in the repo |
| Whether the shipped weights correspond to the paper's model | `[unverified]` — repo HEAD is ~2 years after publication; weights are downloaded from a release URL |
| GP match encoder internals vs. DKM | `[unverified]` — inherited wholesale; not traced |
| `get_gt_warp` correctness (depth → warp + covisibility) | `[unverified]` — `romatch/utils/utils.py` not read line-by-line |
| Full `matcher.py` inference path (symmetric matching, upsample_preds second pass) | `[unverified]` — read only around `attenuate_cert` |
| Whether the ScanNet (indoor) recipe matches `experiments/roma_indoor.py` | `[unverified]` |
| Supplementary material generally | `[unverified]` — not in the local PDF |
