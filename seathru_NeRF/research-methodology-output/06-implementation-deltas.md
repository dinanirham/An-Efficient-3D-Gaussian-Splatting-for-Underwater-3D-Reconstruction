# §6 — Implementation deltas from the paper

**Repo state inspected:** `github.com/deborahLevy130/seathru_NeRF`, commit
`3f4ebfe2c9dcb93af7916a3c7e7e196b9b956160`, branch `master`, 2024-03-14. No tags.

**Paper version inspected:** arXiv:2304.07743v1 (CVPR 2023 camera-ready content).
The code is ~11 months newer than the arXiv v1.

**Files read directly:** `internal/models.py`, `internal/render.py`,
`internal/train_utils.py`, `internal/configs.py`, `internal/datasets.py`,
`internal/image.py`, `train.py`, `eval.py`, `configs/llff_256_uw.gin`,
`configs/llff_256.gin`, `scripts/train_llff_uw.sh`, `install.sh`, `README.md`,
`requirements.txt`. **Config values are taken from the gin file the released training
script passes** (`scripts/train_llff_uw.sh` → `configs/llff_256_uw.gin`), not from the
Python dataclass defaults, which differ in several places.

---

## D-1 — The mediumMLP is **1 layer × 128**, not "6 linear layers with 256 features"

`[paper §4.5]`:
> "For the mediumMLP, we use **6 linear layers with 256 features** and a softplus
> activation, followed by 3 branches of dense layers and a sigmoid activation for
> predicting `c^med` and softplus activations for `σ^attn` and `σ^bs`."

`[repo: internal/models.py:716]` — inside `UWMLP.setup()`:
```python
self.net_depth_water = 1
```
`[repo: internal/models.py:865-869]`:
```python
for i in range(self.net_depth_water):                       # → exactly one iteration
    dir_enc_for_water_1 = dense_layer(self.net_width_viewdirs)(dir_enc_for_water_1)
    dir_enc_for_water_1 = self.density_activation(dir_enc_for_water_1)   # softplus ✓
```
with `net_width_viewdirs: int = 128` `[repo: models.py:678]`, **not** `net_width = 256`.

The 3-branch head matches exactly (`sigmoid` for `c^med` at `:871-873`, `softplus` for
`σ^bs` at `:878` and `σ^attn` at `:889`). The **trunk does not**.

Order of magnitude: a 6×256 trunk is ≈ `27·256 + 5·256²` ≈ **335k** weights; the released
1×128 trunk is `27·128` ≈ **3.5k** — roughly **95× fewer**.
`[inferred: arithmetic from the layer specs above]`

`net_depth_water` is set in `setup()` and is **not a dataclass field**, so no gin binding
can change it — a reproduction cannot restore the paper's architecture without editing
`models.py`.

**Severity: high.** The whole well-posedness argument (§5, M-1) is capacity control on the
medium branch. The deployed capacity is far below the described capacity.

---

## D-2 — The Laplacian mixture prior is **asymmetric** (`6×`), the paper's is symmetric

`[paper Eq. 26]`: `P(x) ∝ e^{−|x|/0.1} + e^{−|1−x|/0.1}` — equal weights.

`[repo: internal/train_utils.py:160-162]`:
```python
data_loss += jnp.mean(
    -jnp.log(config.uw_acc_loss_factor * jnp.exp(-jnp.abs(1 - weights) / 0.1)
             +                            jnp.exp(-jnp.abs(weights)     / 0.1)))
```
with `uw_acc_loss_factor: float = 6` `[repo: internal/configs.py:173]` and the source
comment: *"factor which encourages one of the terms in the accuracy loss to be more
dominant - for the trans it encourages it to be 1 and for the weights zero."*

The mirror form used by the (disabled) weights variant puts the `6×` on the other mode
`[repo: train_utils.py:144]`.

**Severity: medium.** The `1/0.1` bandwidth matches; only the mixing weight differs. But
`log 6 ≈ 1.79` is a real bias in the NLL, and it is undocumented.

---

## D-3 — In the released config, `c^obj` is **view-independent**

`[paper §4.3]`:
> "the density `σ^obj` is a function of the position (x, y, z) only, **while color `c^obj`
> is determined by the viewing direction (θ, φ) as well**."

`[repo: internal/models.py:898-900]`:
```python
if self.uw_rgb_dir:
    # Append view direction encoding to bottleneck vector.
    x.append(dir_enc)
```
and `[repo: configs/llff_256_uw.gin]`: `UWMLP.uw_rgb_dir = False`
(also the dataclass default, `[repo: configs.py:182]`, whose comment reads
*"If True use view_dir also as input for rgb_obj"*).

With the flag off, `x` remains `[bottleneck]` `[repo: models.py:851]` and the colour head
`[repo: models.py:921-925]` sees only position-derived features. **The object colour is
Lambertian in the released configuration.**

**Severity: high.** This removes the model's ability to represent specularity/view-dependent
appearance on the object — a capability the paper claims and which mip-NeRF 360 has by
default. It also has a subtle interaction with D-1: with `c^obj` view-independent, the
*only* view-dependent quantity in the whole model is the medium, so any view-dependent
residual is forced into `c^med(v)`, `σ^bs(v)`, `σ^attn(v)`.

---

## D-4 — Sample spacing is gradient-detached in all medium terms

`[repo: internal/render.py:179]`:
```python
delta_bs = jax.lax.stop_gradient(t_delta) * jnp.linalg.norm(dirs[..., None, :], axis=-1)
```
versus the object's live `delta` at `[repo: render.py:164]`. `δ^bs` feeds `α^bs`, `T^bs`
and `A` (attenuation) `[repo: render.py:185-210]`.

Not mentioned anywhere in the paper. This is a genuine well-posedness mechanism (closes the
`σ·s` scale ambiguity from the sampler side) — see [`05-constraints.md`](05-constraints.md) M-3.

**Severity: medium** (behaviour-relevant, absent from the paper).

---

## D-5 — `J` (the restored image) is `stop_gradient`-ed

`[repo: internal/render.py:319]`:
```python
J = jax.lax.stop_gradient((weights[..., None] * rgbs).sum(axis=-2))  # clean Images
```

The paper presents colour restoration as capability #1 `[paper §1]` but never states that
`J` is a pure diagnostic that carries no gradient and enters no loss or metric. Not a
contradiction — just an unstated and important fact about what is (not) being optimized.

**Severity: low** (clarifying), **high relevance** to any claim about restoration quality.

---

## D-6 — `L_recon` clips the prediction at 1; `[paper Eq. 25]` does not

`[repo: internal/train_utils.py:95-102]`:
```python
rgb_render_clip = jnp.minimum(1., rendering['rgb'])   # "match sensor overexposure behavior"
resid_sq_clip   = (rgb_render_clip - batch.rgb[..., :3]) ** 2
scaling_grad    = 1. / (1e-3 + jax.lax.stop_gradient(rgb_render_clip))
data_loss       = resid_sq_clip * scaling_grad ** 2
```
`[paper Eq. 25]` is `((Ĉ − C*) / (sg(Ĉ) + ε))²` with no clip. `ε = 1e-3` matches.

Consequence: once `Ĉ > 1` the gradient through `jnp.minimum` is zero, so **overexposed
predictions receive no corrective gradient**. Inherited from upstream RawNeRF/multinerf,
but it changes the stated objective.

**Severity: low–medium.**

---

## D-7 — mip-NeRF 360's distortion loss is **explicitly disabled**

`[repo: configs/llff_256_uw.gin]`: `Config.distortion_loss_mult = 0.`

`[paper §4.5]` says "We keep the learning rate and optimization parameters the same as in
[5]", and Eq. 24 lists only three terms — so the paper is *consistent*, but it never
states that a standard component of the named base method was switched off. Since the
distortion loss is mip-NeRF 360's main anti-floater regulariser, and floaters are exactly
this paper's subject matter, the omission is worth flagging.

**Severity: medium.**

---

## D-8 — Learning rate is **8× the non-underwater config**, not "the same as [5]"

`[paper §4.5]`: "We keep the learning rate and optimization parameters the same as in [5]."

| Config | `batch_size` | `lr_init` | `lr_final` | `max_steps` | `factor` |
|---|---|---|---|---|---|
| `configs/llff_256.gin` (base) | 2 048 | 2.5e-4 | 2.5e-5 | 2 000 000 | 4 |
| `configs/llff_256_uw.gin` (used) | **16 384** | **2e-3** | **2e-5** | **250 000** | **1** |

`[repo: configs/llff_256.gin; configs/llff_256_uw.gin]`

Batch ×8 and `lr_init` ×8 is textbook linear LR scaling, and steps ÷8 keeps the epoch count
roughly constant — so the choice is principled. But it is not "the same", and a reproduction
that literally uses mip-NeRF 360's LR at batch 16384 will not converge the same way.
`[inferred: comparing the two gin files]`

**Severity: low–medium.**

---

## D-9 — The `uw_decay_acc` ramp is a no-op in the released config

`[repo: train.py:127-134]` selects between `uw_initial_*` and `uw_final_*` multipliers at
`step ≥ uw_decay_acc` (5 000). `[repo: configs/llff_256_uw.gin]` sets initial = final =
`1e-4` for the trans loss and `1e-3` for the (disabled) weights loss. So the schedule never
changes anything. The paper reports a single `λ = 0.0001` `[paper Eq. 24]`, consistent.

**Severity: cosmetic**, but it means the ramp machinery in the code was not used for the
published numbers.

---

## D-10 — Undocumented optional loss: `uw_sig_med_loss`

`[repo: internal/train_utils.py:171-187]`, gated by `use_uw_sig_med_loss = False`
`[repo: configs/llff_256_uw.gin]`. It penalises `mean(std(σ^attn)) + mean(std(σ^bs))`
across the batch — a smoothness prior on the medium field. The source comment is explicit:
*"use std loss on medium's densities to imply smoothness on the densities — **not in the
paper**"* `[repo: configs.py:168]` and *"mult factor for std loss — **not in the paper!!**"*
`[repo: configs.py:174]`.

Disabled, so it does not affect published numbers — but its existence indicates the authors
found the view-dependence of `c^med`/`σ` needed damping, which bears on §5.3.

**Severity: low** (informational).

---

## D-11 — A `gen_eq` code path exists that never gets fully wired from the main gin

`[repo: internal/models.py:232-238, render.py:231, 383]` implement the "general equations
(11)–(14)" model (ablation variant III). The gin comment is candid about the fragility:

```
Config.gen_eq = False  #need to update the values twice, I know it's annoying, I will solve it soon and update the code
UWMLP.gen_eq = False
```
`[repo: configs/llff_256_uw.gin]`

Reproducing ablation III requires setting **both** bindings; setting only one silently
produces a mismatched model.

**Severity: medium for ablation reproduction.**

---

## D-12 — `density_bias` and `water_bias` are 0 in gin but `-1.` in the dataclass

`[repo: models.py:693-694]` declares `density_bias: float = -1.` and
`water_bias: float = -1.`; `[repo: configs/llff_256_uw.gin]` overrides both to `0`
(`UWMLP.density_bias = 0`, `UWMLP.water_bias = 0`, `PropMLP.density_bias = 0`).

Anyone reading `models.py` alone will describe the wrong initialisation of the density and
medium-coefficient heads. Not a paper-vs-repo disagreement (the paper states neither), but
a repo-reading trap.

**Severity: low**, high trap value.

---

## Items I could *not* verify in this pass

| Claim | Status |
|---|---|
| VRAM used for training | `[unverified]` — the paper reports time and GPU but not memory. **SeaSplat's Table II attributes 33.2 GB and 21 h to this method** `[seasplat paper Tab. II]`, which contradicts the 10 h here; SeaSplat measured on its own unnamed hardware. See [`08-computational-profile.md`](08-computational-profile.md). |
| Parameter count | `[unverified]` — never reported. Derivable from the architecture but not stated. |
| Whether published runs used `factor = 1` | `[repo: configs/llff_256_uw.gin Config.factor = 1]` implies full ≈900×1400 resolution, consistent with `[paper §5.1]`; not independently confirmed. |
| Which LPIPS backbone was used for Table 2 | `[unverified]` — the paper does not say; the repo imports `dm-pix`/`lpips` via `internal/image.py`, not inspected in depth this pass. |
| Whether the paper's numbers came from this exact commit | `[unverified]` — the commit is 11 months after the arXiv v1 and there are no tags. |
