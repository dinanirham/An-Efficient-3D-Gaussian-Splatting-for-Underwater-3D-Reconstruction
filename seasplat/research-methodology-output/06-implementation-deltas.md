# §6 — Implementation deltas from the paper

**Repo state inspected:** `github.com/dxyang/seasplat`, commit
`ddc6259db238a5cc72fcc9e0e99a6589fd20d48f`, branch `master`, committed 2024-11-27.
No tags exist (`git describe --tags` falls back to the abbreviated SHA `ddc6259`).
Defaults below are read from `arguments/__init__.py` **at that commit** and can differ at
other commits.

**Paper version inspected:** arXiv:2409.17345**v2**, dated 2 Jun 2025 — i.e. the paper
revision is ~6 months *newer* than the code. Where a delta could be revision drift rather
than genuine disagreement, that is stated.

Files read directly for this section: `train.py`, `arguments/__init__.py`,
`deepseecolor/models.py`, `deepseecolor/losses.py`, `deepseecolor/depth_losses.py`,
`utils/loss_utils.py`, `utils/general_utils.py`, `utils/image_utils.py`, `metrics.py`,
`scene/gaussian_model.py`, `scene/dataset_readers.py`, `gaussian_renderer/__init__.py`,
`README.md`, `Dockerfile`. The README was **not** used as a source for any claim except
the documented training command.

---

## D-1 — Eq. 10 is an unweighted sum in the paper; the code uses six distinct λ

`[paper Eq. 10]` writes `L = L_GS + L_bs + L_gw + L_sat + L_op + L_Zsmooth + L_Z-recon`.

`[repo: arguments/__init__.py:115,130,144,147,150,153]` gives
`bg_lambda=0.01`, `gw_loss_lambda=0.1`, `dcp_loss_lambda=1.0`, `dwr_lambda=1.0`,
`depth_smooth_lambda=2.0`, `sat_loss_lambda=2.0` — a 200× spread. Full table in
[`04-loss.md`](04-loss.md) §4.3.

**Severity: high.** Any reimplementation from Eq. 10 alone reproduces a different objective.

---

## D-2 — Attenuation uses the *simplified* V3 model, not DeepSeeColor Eq. 12

The paper says attenuation coefficients "are each implemented as a (1,1,1,3) kernel"
`[paper §IV.C]`, implying a single per-channel coefficient — consistent with V3.

But `deepseecolor/models.py` ships three attenuation models, and the docstrings of V1/V2
carry the DeepSeeColor two-exponential form `β^D(z) = a·e^{−bz} + c·e^{−dz}`
`[repo: models.py:105-110]`. The default is `use_at_v3 = True`
`[repo: arguments/__init__.py:176]` → `AttenuateNetV3`, which drops `a, c` entirely
(`self.attenuation_coef = None`, `[repo: models.py:219]`) and computes simply
`Â = exp(−clamp(β^D ⊛ Ẑ, 0))` `[repo: models.py:226-232]`.

Similarly `BackscatterNetV2` is used with `use_bs_residual = False`
`[repo: arguments/__init__.py:174; train.py:84]`, dropping SeaThru's residual term
`J′e^{−β z}` — the repo comment acknowledges this: *"use the residual terms in equation 10
from SeaThru ('depending on the scene, the residual can be left out…')"*.

**So the effective physical model is the 9-scalar minimal one.** Reasonable and consistent
with the paper's headline claim, but the paper does not say that V1/V2 exist or that the
richer forms were tried and dropped.

**Severity: low** (paper and default code agree); **worth knowing** because the codebase
contains three mutually exclusive attenuation models and a reader skimming
`models.py` top-down will find `AttenuateNet` (V1) first and mis-describe the method.

---

## D-3 — Medium maps are computed twice: live-depth and detached-depth

`[paper §IV.A]` describes only the detached path.
`[repo: train.py:254-256, 269-273]` computes **both**:

```python
attenuation_map                = at_model(depth_image_batch)            # live Ẑ  → used in Î
attenuation_map_depth_detached = at_model(depth_image_batch.detach())   # detached → aux losses
backscatter                    = bs_model(depth_image_batch)            # live Ẑ  → used in Î
backscatter_depth_detached     = bs_model(depth_image_batch.detach())   # detached → L_bs
```

The live copies feed `Î` (`train.py:256, 273`), so `L_GS` and `L_Z-recon` **do** send
gradient from the medium model back into the Gaussian depths — which is the intended
constraint. The detached copies isolate the auxiliary priors. The paper's sentence, read
alone, would suggest the depth path is severed everywhere.

**Severity: medium** — it changes the qualitative story of *how* the medium constrains
geometry. The paper's own following sentence ("the learned backscatter parameters do
constrain the image formation model used in other losses") is consistent with the code;
the first sentence, in isolation, is not.

---

## D-4 — `L_bs`'s negative branch is a Huber, and `k = 1000`

`[paper Eq. 4]`: `Σ max{D̂_c, 0} + k·min{D̂_c, 0}` with `k > 1`.

`[repo: deepseecolor/losses.py:146-161]` (`DarkChannelPriorLossV3`):
`pos = L1Loss(relu(D̃), 0)`; `neg = SmoothL1Loss(relu(−D̃), 0, beta=0.2)`;
`return 1000·neg + pos`.

Two deltas: (a) `k` is **1000**, not merely ">1" — three orders of magnitude, which the
paper's phrasing does not convey; (b) the negative branch is quadratic below `|D̃| = 0.2`
and linear above, not linear throughout. Also note the paper's `min{·,0}` is negative,
so `k·min{·,0}` *reduces* the loss as written — the code's `relu(−D̃)` (positive) is the
sign-correct intent.

**Severity: medium.**

---

## D-5 — `L_sat` is squared, averaged, and two-sided

`[paper Eq. 6]`: `Σ_{i,j} max_c ( Ĵ_c − T_sat , 0 )`.
`[repo: deepseecolor/losses.py:228-232]`: `(relu(−rgb) + relu(rgb − 0.7)).square().mean()`.

Deltas: squared vs linear; `mean` vs `sum`; an added lower-bound term `relu(−Ĵ)` absent
from the paper. `T_sat = 0.7` agrees `[repo: train.py:98]`.

**Severity: low–medium** (the extra `relu(−Ĵ)` branch is a real additional constraint —
it forbids negative restored radiance, which the paper never states).

---

## D-6 — `L_op` compares against `Î`, not `I`, and uses an unsquared norm

`[paper Eq. 9]`: `Σ α · 1[ ‖I − B‖²₂ < T_sim ]` — the **captured** image vs `B`.

`[repo: train.py:319; deepseecolor/losses.py:252-292]`: at defaults
(`alpha_binf_uw=True`, `add_bg_binf=False`, `bg_from_bs=True`) the call is
`alpha_bg_criterion(underwater_image.detach(), σ(B_inf).detach(), image_alpha)` — the
**model's own reconstruction** `Î`. The mask is `‖·‖₂ < 0.2·√3` — an unsquared L2 norm
against a hard-coded threshold; `T_sim` is not exposed as a flag.

**Severity: medium.** Using `Î` makes the loss self-referential (the model decides which
pixels are "background" using its own output), which is a materially different constraint
from using the capture.

---

## D-7 — `learned_bg` exists and is undocumented

`[repo: train.py:123-131, 204-216, 309-331, 552-553, 564-565; arguments/__init__.py:114-124]`

A learnable RGB background colour, on its own Adam optimizer at `lr = 1e-2`, initialised to
`[0.05, 0.25, 0.80]`, composited as `Ĵ + σ(bg)·(1 − α)` for the whole pre-SeaThru phase,
and then **transferred into `B^∞`** when SeaThru switches on `[repo: train.py:209-212]`.
It appears nowhere in the paper — neither in Eq. 10, the variable list, nor §IV.C.

**Severity: high for reproduction.** It supplies a data-derived warm start for `B^∞`,
replacing `U(0,1)`, in a problem where the "no medium" solution is a global optimum of the
photometric loss (see [`05-constraints.md`](05-constraints.md) D-1).

---

## D-8 — The medium warm-up and colour-adjustment inner loops do not advance `iteration`

`[repo: train.py:433-463]` vs `[repo: train.py:567]`

`continue` at lines 453 and 463 lies above `iteration += 1` at line 567. Therefore:

- At the SeaThru transition: **1000** medium-only Adam steps, then **2000** colour-only
  Gaussian steps, all at a frozen `iteration`.
- Steady state: **50** medium-only steps every 100 outer iterations.

A "30 000 iteration" run at defaults therefore performs roughly
`30 000 + 3 000 + 50·(20 000/100) = 43 000` optimizer steps.
`[inferred: arithmetic from repo train.py:434-453 with update_bs_at_interval=100, update_bs_at_count=50, seathru_from_iter=10 000, iterations=30 000]`

The paper mentions "interleaving" `[paper §IV.B]` but gives no schedule, counts, or the
freeze pattern.

**Severity: high for reproduction and for the wall-clock comparison in Table II.**

---

## D-9 — Attenuation kernel shape is `(3,1,1,1)`, not `(1,1,1,3)`

`[paper §IV.C]`: "implemented as a (1, 1, 1, 3) kernel".
`[repo: models.py:216]`: `nn.Parameter(torch.rand(3, 1, 1, 1))`, consumed by
`F.conv2d(depth, params)`.

PyTorch conv weights are `(out_channels, in_channels, kH, kW)`, so the correct shape for
"1 input depth channel → 3 output colour channels, 1×1 spatial" is `(3,1,1,1)`. The
paper's `(1,1,1,3)` is a transposed/typo'd statement of the same object.

**Severity: cosmetic**, but it will trip a reimplementation written from the paper text.

---

## D-10 — `β^D` has a hand-tuned deterministic init; `β^B` and `B^∞` are `U(0,1)`

`[repo: models.py:211-218; train.py:88]`

`AttenuateNetV3(..., init_vals = not opt_params.do_sigmoid_at)` and `do_sigmoid_at`
defaults `False` `[repo: arguments/__init__.py:173]`, so `init_vals = True` and
`β^D ← [1.1, 0.95, 0.95]` — red attenuating fastest, matching the physics. Meanwhile
`β^B ← U(0,1)³` and `B^∞ ← U(0,1)³` `[repo: models.py:54, 61]`.

The paper states no initialisation scheme for any medium parameter.

**Severity: medium.** An asymmetric, physically-informed init on `β^D` is a soft prior.

---

## D-11 — `sh_degree` default is 0

`[repo: arguments/__init__.py:49]` — `self.sh_degree = 0 #3 # dxy: default to SH 0`.
Upstream 3DGS uses 3. Consistent with `[paper §IV.C]`, which states zero-order SH.
Listed here because it changes the per-Gaussian parameter count from 59 to 14, which
matters for any storage comparison against `compact3d/`, `CompGS/`, `OMG/`,
`mini-splatting/`.

**Severity: low** (paper and repo agree) but **high relevance** to the comparison set.

---

## D-12 — Boolean flags that default `True` cannot be disabled from the CLI

`[repo: arguments/__init__.py:35-38]`

```python
if t == bool:
    group.add_argument("--" + key, default=value, action="store_true")
```

Every boolean is registered as `store_true`. For the ~10 flags whose default is `True`
(`learn_background`, `bg_from_bs`, `use_depth_smooth_loss`, `filter_depth`,
`norm_depth_max`, `add_recon_depth_l1`, `use_dcp_loss`, `use_rgb_sat_loss`,
`use_gw_loss`, `use_at_v3`, `shuffle`, `alpha_binf_uw`) there is **no command-line way to
turn them off** — the source must be edited.

**Severity: high for ablation reproduction.** The paper's Table III ablations cannot be
reproduced with CLI flags alone at this commit.

---

## D-13 — Metrics are recomputed from files round-tripped through disk, possibly as JPEG

`[repo: train.py:584-644]`

```python
png_images = glob.glob(f"{gt_dir}/*.png")
use_jpeg   = len(png_images) == 0          # → renders saved as JPEG
...
renders, gts = readImages(image_dir, gt_dir, fnames)   # PIL re-open from disk
psnrs.append(psnr(renders[idx], gts[idx]))
```

Final PSNR/SSIM/LPIPS are therefore measured on **8-bit quantised** images, and on
**JPEG-compressed** images whenever the ground-truth directory contains no PNGs. The paper
does not mention this. Also `sh_degree`/`eval` etc. — see [`10-reproducibility.md`](10-reproducibility.md).

**Severity: medium.**

---

## D-14 — Default `iterations = 30 000` but `save/checkpoint/test` schedules assume up to 60 000

`[repo: arguments/__init__.py:88]` vs `[repo: train.py:1020-1023]`
(`test_iterations` default `range(0, 60_000, 1000)`, `save_iterations` up to `60_000`).
Harmless, but indicates longer runs were used during development. The paper reports no
iteration count at all.

**Severity: low.**

---

## Items I could *not* verify in this pass

| Claim | Status |
|---|---|
| GPU model used for Table II timings | `[unverified]` — the paper says only "a consistent set of hardware" `[paper §V.A.c]` and never names a device. The `Dockerfile` pins `CUDA_ARCHITECTURES=89;86` `[repo: Dockerfile:15]`, i.e. Ada/Ampere consumer class, with `9.0` (Hopper/H100) present only in a commented-out line `[repo: Dockerfile:13]`. Suggestive, not conclusive. |
| Gaussian count / model size for SeaSplat scenes | `[unverified]` — not reported in the paper; the repo logs `total_points` to TensorBoard `[repo: train.py:1007]` but no value is committed. |
| Exact `--eval` usage for the reported numbers | `[unverified]` — `eval` defaults `False` `[repo: arguments/__init__.py:58]` and the README's training command omits it, but Table I clearly reports held-out test frames, so `--eval` must have been passed. Not documented. |
| Whether `L_bs` was active before `seathru_from_iter` in the reported runs | `[repo: train.py:404-407]` shows it is computed but **not added** in that branch; consistent, but the paper implies Eq. 10 holds throughout. |
| Which `k` the paper intended | `[unverified]` — paper says only `k > 1`; repo says 1000. |
