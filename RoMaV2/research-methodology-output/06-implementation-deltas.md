# §6 — Implementation deltas from the paper

**Repo state inspected:** `github.com/Parskatt/RoMaV2`, commit
`95c9968145c8906b7b59383258e9f73b02853d89`, `git describe --tags` → **`v2.0.1-2-g95c9968`**,
branch `main`, 2026-04-20. Package version `2.0.1` `[repo: pyproject.toml]`.

**Paper inspected:** `../../RoMaV2.pdf` = arXiv:2511.15706**v3**, 6 Jul 2026 — ~2.5 months
**newer** than the commit.

**Files read directly:** `src/romav2/romav2.py`, `matcher.py`, `refiner.py`, `features.py`,
`geometry.py`, `local_correlation.py`, `types.py`, `dpt.py` (structure), `pyproject.toml`,
`README.md`, plus `git log`/`git describe`.

---

## D-0 — **Training code is not released** (the delta that subsumes the others)

`[repo: src/romav2/romav2.py:172]`:
```python
assert not self.training, "Currently only inference mode released"
```

The package ships four modules, a checkpoint loader, four benchmark harnesses and two demos.
It ships **no loss functions, no optimizer loop, no dataloaders, no EMA, no data mixture**.

Therefore **paper §3.2 (matching loss), §3.3 (refinement loss, EMA), §3.4 (data), and the
training half of §3.5 are entirely unverifiable** — Eqs. 1, 2, 4, 5 have no code counterpart.

Vestiges of the training code do survive in the type definitions
`[repo: src/romav2/types.py]`: `Batch` (with `depth_A/B`, `K_A/B`, `pose_A/B`, `T_AB`,
`warp_A_to_B`, `mask_A_to_B`), `GTSource = Literal["depth", "warp"]` — which matches
§3.3's "consistent depth (for MVS style datasets) or … warp cycle consistency (for flow
datasets)" ✅ — plus `SampleMode`, `ConfidenceMode`, `OptimizerName = Literal["adamw"]`.
These corroborate the paper's description without verifying it. `[inferred]`

**Severity: high**, and it is a disclosure choice rather than an error. Note the README makes
no claim to release training.

---

## D-1 — `temp` changed from 0.2 to 0.1, **unmentioned in the paper**

`[repo: src/romav2/matcher.py:75-76]`:
```python
# NOTE: 0.2 in RoMa
temp: float = 0.1
```

The repo's own comment flags this as a change from RoMa v1. The paper documents the
neighbouring `scale` change in §3.5 with a full paragraph of justification — but says
**nothing** about halving the similarity temperature, which directly sharpens the
`Softmax(S)` distribution that `L_NLL` and the position-embedding aggregation both consume.

**Severity: medium.** A hyperparameter the authors thought worth annotating in code but not
in the paper.

---

## D-2 — `scale` 8 → 1: ✅ **documented and verified**

`[paper §3.5]`: "Compared to RoMa, which initializes the scale to λ = 8 and lets it be
trained, we set it **fixed to λ = 1**."
`[repo: src/romav2/matcher.py:77-78]`:
```python
# NOTE: 8 in RoMa
scale: float = 1
```
✅ Exact match, including the fixed (non-`nn.Parameter`) status. Recorded as a positive.

---

## D-3 — The paper's stated inference resolution is **not** the default setting

`[paper §4.1]`: "We use a coarse resolution of **800 × 800** and a fine resolution of
**1024 × 1024**."

`[repo: src/romav2/romav2.py:78]`: `setting: Setting = "precise"` — and `precise` is
**800 → 1280** with `threshold = None` `[repo: romav2.py:152-159]`. The 800 → 1024 + 
`threshold = 0.05` configuration is the *benchmark* branch (`mega1500`, `scannet1500`,
`wxbs`, `satast`) `[repo: romav2.py:120-127]`.

Meanwhile Tables 6 and 7 state "Images are resized to **640 × 640**", i.e. the `base` setting.

So **three distinct configurations back three different result tables**, and the library
default matches **none** of them. A user calling `RoMaV2()` with no arguments gets `precise`,
not the benchmark configuration.

**Severity: medium**, high trap value for anyone reproducing Table 4.

---

## D-4 — `p̂ = max(𝟙_{p>0.05}, p)` is a benchmark-only behaviour

`[paper Eq. 6]` presents the thresholded sampling distribution as the sampling procedure.
In code, `threshold = 0.05` is set **only** for the four benchmark settings; `base`, `fast`,
`turbo` and `precise` all set `threshold = None` `[repo: romav2.py:126, 134, 142, 150, 158]`,
in which case `_map_confidence` skips the threshold entirely `[repo: romav2.py:61-66]`.

**Severity: low–medium.**

---

## D-5 — Two hard runtime preconditions, neither in the paper

`[repo: src/romav2/romav2.py:169-174]`:
```python
if torch.get_float32_matmul_precision() != "highest":
    raise RuntimeError("Float32 matmul precision must be set to highest")
assert not self.training, ...
# assumes images between [0, 1]
```

The `float32_matmul_precision` requirement is a **hard error**, not a warning — PyTorch's
default is `"highest"`, but any code that has enabled TF32 elsewhere in the process (common
for speed) will crash on the first forward. Not mentioned in the paper or README.

**Severity: medium** for integration into an existing pipeline — e.g. dropping RoMa v2 into
`../EDGS/`, which trains 3DGS in the same process.

---

## D-6 — VGG19-BN fine features are **not pretrained**

`[repo: src/romav2/features.py:179-182]`:
```python
type: Literal["vgg19", "vgg19bn"] = "vgg19bn"
patch_size: int = 4
pretrained: bool = False
```
`[paper Fig. 4]` labels the refiner input branch "VGG19" without further comment. The
released config uses the **batch-norm** variant, trained **from scratch**. RoMa v1 used
pretrained VGG19 features. `[unverified for v1 — not cross-checked in this pass]`

**Severity: low–medium.**

---

## D-7 — The CUDA kernel is **optional and Linux-only**

`[repo: src/romav2/local_correlation.py:4-7]`:
```python
try:
    import local_corr
except ImportError:
    local_corr = None
```
`[repo: pyproject.toml]`: `"fused-local-corr ; sys_platform == 'linux'"`.

`[paper §3.3]` presents the kernel as a contribution ("we write a custom CUDA kernel as a
PyTorch extension, which significantly reduces the memory consumption") without noting that
it is an optional, platform-gated dependency with a pure-PyTorch fallback. Table 8 does give
both rows (w/ and w/o K), so the paper is not misleading — but a Windows or macOS user
silently gets the 5.6 GB path, not the 4.8 GB one.

**Severity: low**, relevant to your environment (the project root is on Windows).

---

## D-8 — Refiner count and channel widths: ✅ **documented and verified**

`[paper §3.3]`: "we construct **three refiners at strides {4, 2, 1}**" and "change all channel
dimensions to be **powers of two**."

`[repo: src/romav2/refiner.py:228, 239-265]`: `refiner_type = "roma-4-pow2"`, with three
entries keyed `4`, `2`, `1` and inline comments computing the input widths as
`512`, `128`, `32`. ✅ Exact.

---

## D-9 — Precision parameterisation: ✅ **documented and verified**

`[paper §3.3]` specifies `l11 = Softplus(z11) + 1e-6`, `l21 = z21`,
`l22 = Softplus(z22) + 1e-6`, `Σ⁻¹ = LLᵀ`.

`[repo: src/romav2/refiner.py:201-204]`:
```python
chol_eps = 1e-6
l00 = F.softplus(delta_confidence[..., 1]) + chol_eps  # this is in pixels
l11 = F.softplus(delta_confidence[..., 3]) + chol_eps
```
with assembly in `prec_mat_from_prec_params` `[repo: geometry.py:168-174]`. ✅ Exact, including
the epsilon. The code comment "**this is in pixels**" adds a unit that the paper does not
state — useful when propagating the covariance downstream.

---

## D-10 — The paper's §3.5 training-resolution sentence is **unrecoverable from the PDF**

`[paper §3.5]`, "Training:" paragraph. Every extraction I attempted (`pdftotext -layout` and
`pdftotext -raw`) renders the resolution/aspect-ratio list as reversed, interleaved garbage.
Only the tail survives cleanly: "**refiners are trained exclusively with size 640 × 640**."

The coarse matcher's training resolutions are therefore **`[unverified]`** — I did not guess
them. If you need them, read that paragraph in the PDF directly.

**Severity: low** (a PDF artifact, not a paper-vs-repo disagreement), but it is a gap in
this breakdown and is flagged rather than filled.

---

## Verified-correct items (recorded because §6 is not only for disagreements)

| Paper claim | Code | Status |
|---|---|---|
| Frozen DINOv3 ViT-L/16 backbone `[§3.2]` | `name="dinov3_vitl16"`, `frozen=True` `[features.py:83-85]` | ✅ |
| ViT-B multi-view Transformer `[§3.2]` | `mv_vit="vit_base"` `[matcher.py:70]` | ✅ |
| Alternating frame-wise/global attention, following VGGT `[§3.2]` | `mv_vit_attention_mode="alternating"` `[matcher.py:73]` | ✅ |
| RoPE for frame-wise attention only `[§3.2]` | `mv_vit_use_rope=True` `[matcher.py:71]`; `vit/rope.py`, `vit/rope_mixed.py` | ✅ (per-attention scoping not traced in depth) |
| DPT head `[§3.2, ref 32]` | `head="dpt-no-pos"` `[matcher.py:74]`; `dpt.py` | ✅ |
| Bidirectional warps + confidences `[§1]` | `warp_AB/warp_BA`, `confidence_AB/BA` `[romav2.py:186-196]` | ✅ |
| Additive precision accumulation across strides `[§3.3]` | precision summed over refiner outputs `[refiner.py]` | ✅ |
| Normalized `[−1,1]²` output coordinates `[§4.1 implied]` | `to_pixel_coordinates`, `get_normalized_grid` `[README.md; geometry.py]` | ✅ |
| Balanced KDE sampling `[§4.1]` | `balanced_sampling = True` in all settings `[romav2.py:119-160]` | ✅ |

---

## Items I could *not* verify in this pass

| Claim | Status |
|---|---|
| **All training losses** (Eqs. 1, 2, 4, 5), λ values, EMA, two-stage schedule | `[unverified]` — no training code (D-0) |
| Data mixture and weights (Tab. 3) | `[unverified]` — no dataloaders |
| Coarse-matcher training resolutions | `[unverified]` — PDF extraction failure (D-10) |
| Whether RoPE is genuinely restricted to frame-wise attention | `[unverified]` — `vit/attention.py` and `vit/rope*.py` not traced line-by-line |
| DPT head internals vs. ref [32] | `[unverified]` — `dpt.py` (516 lines) read only structurally |
| The `local_corr` CUDA kernel source | `[unverified]` — `fused-local-corr` is an external package, not vendored |
| Supplementary-material details (matcher architecture, refiner details, GT warp/overlap computation, SatAst construction) | `[unverified]` — repeatedly deferred to the supplement `[paper §3.2, §3.3, §3.4, §4.6, §4.8]`, which is not in the local PDF |
| Whether the shipped `v2.0.1` checkpoint is the one used for the paper's tables | `[unverified]` — the commit predates arXiv v3 by ~2.5 months |
