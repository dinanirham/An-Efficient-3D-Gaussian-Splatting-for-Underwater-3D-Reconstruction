# §4 — Full loss function

> ⚠️ `[paper …]` = **arXiv:2404.09458v1** = `../../CompGS.pdf`.

## 4.1 The paper's statement

> `Ω, Γ = arg max L = arg max λR + D` `[paper Eq. 1]`
> "where λ denotes the Lagrange multiplier to control the trade-off between rate and
> distortion, and {Ω, Γ} denote the set of anchor primitives and coupled primitives."

**Two terms.** ⚠️ Note the printed operator: the PDF text layer renders Eq. 1 as
**`arg max`**, while the surrounding prose says the primitives "are jointly optimized via
rate-distortion cost **minimization**" `[paper §3.1]`, and `L` is called "the
rate-distortion **cost**". A cost is minimized. Either the equation carries a sign typo or
the extraction is unfaithful; I flag it rather than silently correcting it, since it is the
paper's only statement of the objective. The repo unambiguously **minimizes**
`loss.backward()` on `D + REG + λR` `[repo: TrainerCompGS.py:229-232]`.

## 4.2 The objective as actually implemented

`[repo: Modules/TrainerCompGS.py:213-232]`:

```python
# distortion
l1_loss   = F.l1_loss(render_results.rendered_img, sample.img)
ssim_loss = 1 - ssim(rendered.unsqueeze(0), gt.unsqueeze(0), data_range=1., size_average=True)
rendering_loss = (1 - 0.2) * l1_loss + 0.2 * ssim_loss

# regularization  ← NOT IN THE PAPER
reg_loss = 0.01 * render_results.scales.prod(dim=1).mean()

# rate
bpp       = render_results.bpp
rate_loss = lambda_weight * sum(v for v in bpp.values())

loss = rendering_loss + reg_loss + (rate_loss if iteration > 3000 else 0.)
loss.backward()

aux_loss = self.gaussian_model.aux_loss     # ← NOT IN THE PAPER
aux_loss.backward()                         #   separate graph, separate optimizer
```

```
L_total = 1.00 · D                 # 0.8·L₁ + 0.2·(1 − SSIM)
        + 0.01 · REG               # mean product of the 3 scales — undocumented
        + λ    · R                 # λ ∈ {0.001, 0.005, 0.01}; gated to iter > 3000
        ⊥ aux_loss                 # separate backward + separate Adam
```

So the deployed objective has **three** terms plus a detached auxiliary objective, where
the paper describes **two**.

## 4.3 Term-by-term

### 1. `D` — rendering distortion (3DGS's loss)

- **Form:** `D = 0.8·L₁(Î, I) + 0.2·(1 − SSIM(Î, I))`.
- `[paper §3.3]`: "the distortion item D is provided by the rendering loss [17]."
  `[repo: TrainerCompGS.py:214-217]`.
- ⚠️ **SSIM implementation differs from 3DGS.** The repo uses
  `pytorch_msssim.ssim(..., data_range=1., size_average=True)`
  `[repo: TrainerCompGS.py:9, 216]`, whereas 3DGS (and `seasplat/`, `mini-splatting/`,
  `compact3d/`) use their own 11×11 σ=1.5 Gaussian-window implementation. Numerically
  close, not identical — and `pytorch_msssim`'s default window is also 11×11 σ=1.5, so the
  practical difference is small. Worth noting since SSIM is a reported metric.
- **Failure mode if removed:** no image supervision; the rate term alone would drive all
  embeddings to a constant (`R → 0`).

### 2. `REG` — scale-volume regulariser ⚠️ **absent from the paper**

- **Form:** `REG = 0.01 · mean_k( s_kx · s_ky · s_kz )` — the mean **product** of the three
  scale components of every rendered coupled primitive, i.e. a penalty on Gaussian
  *volume*.
- `[repo: TrainerCompGS.py:220]`. Weight **0.01**, hard-coded, not exposed in any config.
- **Provenance:** this is Scaffold-GS's volume regularisation, inherited along with the
  rest of the anchor machinery (see [`01-taxonomy.md`](01-taxonomy.md)).
- **Purpose.** Coupled primitives get their scale as `sigmoid(·) ⊙ exp(s_ω[3:6])`
  `[repo: Prediction.py:77]`, which is unbounded above through `s_ω`. Nothing in `D`
  prevents a few enormous, low-opacity Gaussians from covering large image regions cheaply.
  `REG` makes volume expensive.
- **What it prevents if removed:** oversized "blob" primitives — the same
  under-reconstruction failure `mini-splatting/` attacks from the opposite direction. It
  also interacts with the rate term: large Gaussians cover more pixels, so **fewer**
  primitives are needed, so `R` drops. Without `REG`, the rate term would actively *reward*
  blobbing. **This makes `REG` load-bearing specifically because `R` is in the loss** —
  which is precisely why omitting it from the paper matters. `[inferred]`
- **Never ablated** anywhere in the paper (it is not mentioned).

### 3. `λR` — the rate term (the paper's contribution)

- **Form** `[paper Eqs. 9-13]`:
  ```
  R_f  = E[−log p(f̃_ω) − log p(z_f)]                                 (Eq. 9)
  R_Σ  = E[−log p(Σ̃_ω)],           p(Σ̃_ω) = N(μ_Σ, σ_Σ) | f̃_ω        (Eqs. 10, 12)
  R_gk = E[−log p(g̃_k) − log p(z_g)], p(g̃_k) = N(μ_g, σ_g) | f̃_ω ⊕ z_g (Eqs. 11, 12)
  R_ω,Γ = R_f + R_Σ + Σ_{k=1..K} R_gk                                (Eq. 13)
  ```
  and `R` = the sum over all anchors.
- `[repo: TrainerCompGS.py:223-224]`: `rate_loss = lambda_weight * sum(bpp.values())`.
- **λ = `{0.001, 0.005, 0.01}`** `[paper §3.4]`; the shipped YAMLs contain only `0.001`,
  the other two coming from `[repo: Scripts/derive_train_eval_scripts.py:47-52]`.
- ⚠️ **Gated to `iteration > rate_loss_start_iteration = 3000`**
  `[repo: TrainerCompGS.py:229; Configs/*.yaml]` — **not in the paper**. A 10% warm-up in
  which the representation is fit with no rate pressure at all.
- **Differentiability:** rounding is replaced by additive uniform noise during training
  `[paper Eqs. 6-7]` and by a straight-through estimator at eval
  `[repo: EntropyModel.py:246 — quantize_ste]`.
- **What it prevents if removed:** exactly what Table 4 measures — the bitstream balloons
  from 8.60 MB to 48.58 MB on *Train* (−82.3%) and from 10.61 MB to 30.38 MB on *Truck*
  (−65.1%) `[paper Tab. 4]`. Without `λR` the embeddings have no pressure toward
  low-entropy distributions and the entropy coder has nothing to exploit.

### 4. `aux_loss` — entropy-bottleneck CDF fitting ⚠️ **absent from the paper**

- `[repo: TrainerCompGS.py:235-236, 299-300; Model.py:159-163]`. Standard CompressAI
  practice: the factorized entropy bottleneck's learned CDF is fitted by a **separate**
  objective, backpropagated on its own graph, and stepped by a **separate Adam**.
- **Not a regulariser** — it does not shape the representation; it makes the *rate estimate*
  accurate. But it is a second optimization problem running concurrently, and any faithful
  reimplementation needs it or the reported bitrates will not match the actual coded sizes.

## 4.4 Reading the ablations

### Table 4 — hybrid structure + rate-constrained optimization: **CUMULATIVE-ADDITIVE**

`[paper Tab. 4]`, Tanks&Templates, per-scene:

| Hybrid struct. | Rate-constr. opt. | *Train* PSNR/SSIM/LPIPS/Size | *Truck* PSNR/SSIM/LPIPS/Size |
|---|---|---|---|
| ✗ | ✗ | 22.02 / 0.81 / 0.21 / **257.44 MB** | 25.41 / 0.88 / 0.15 / **611.31 MB** |
| ✓ | ✗ | 22.15 / 0.81 / 0.23 / **48.58 MB** | 25.20 / 0.86 / 0.19 / **30.38 MB** |
| ✓ | ✓ | 22.12 / 0.80 / 0.23 / **8.60 MB** | 25.28 / 0.87 / 0.18 / **10.61 MB** |

**Precisely what each row represents.** Row 1 is "the baseline 3DGS [17]" — the paper says
"we incorporate it into the baseline 3DGS [17]" `[paper §4.3]`. Row 2 adds the hybrid
primitive structure. Row 3 adds rate-constrained optimization **on top of** row 2. This is
a **cumulative-additive** ladder, **not** leave-one-out.

- ✅ "The hybrid primitive structure alone reduces *Train* from 257.44 MB to 48.58 MB
  (5.3×) and *Truck* from 611.31 MB to 30.38 MB (20.1×)."
- ✅ "Adding rate-constrained optimization on top gives a further 82.3% / 65.1% reduction."
- ❌ You may **not** report a size for "rate-constrained optimization applied to plain
  3DGS" — that row does not exist.
- ⚠️ **PSNR barely moves and SSIM/LPIPS get slightly worse.** *Train*: 22.02 → 22.15 →
  22.12; *Truck*: 25.41 → 25.20 → 25.28, with LPIPS worsening 0.15 → 0.18. The honest
  reading is **~70× compression at ≈0.1 dB cost**, which is a strong result — but the
  method is not free.
- ⚠️ **Only 2 of the 9 T&T scenes** are shown, so this is not a dataset-level ablation.

### Table 5 — residual embeddings: **ONE ALTERNATIVE VARIANT**

`[paper Tab. 5]`, *Train* scene:

| | PSNR | SSIM | LPIPS | Size |
|---|---|---|---|---|
| w.o. Res. Embed. | 20.50 | 0.73 | 0.31 | 5.75 MB |
| Proposed | **21.49** | **0.78** | **0.26** | **5.51 MB** |

**Precisely:** "w.o. Res. Embed." removes `g_k` entirely, making the model follow
Scaffold-GS's "primitive derivation paradigm [27]" `[paper §4.3]`. It is a
**mutually-exclusive variant**, not an additive step and not a leave-one-out from row 3 of
Table 4 — note the sizes (5.51 MB) differ from Table 4's *Train* row (8.60 MB), so this is
a **different operating point** (presumably a larger λ). Do not cross-reference the two
tables' numbers.

- ✅ **+0.99 dB at slightly smaller size** — the strongest single result in the paper, and
  it is a comparison against **its own base method**, Scaffold-GS.
- The stated mechanism: "such indiscriminate derivation of coupled primitives can hardly
  capture unique characteristics of coupled primitives" `[paper §4.3]`.

### Table 6 — proportion of coupled primitives `K`: **MUTUALLY-EXCLUSIVE VARIANTS**

`[paper Tab. 6]`, *Train* scene:

| `K` | PSNR | SSIM | LPIPS | Size |
|---|---|---|---|---|
| 5 | 22.04 | 0.80 | 0.24 | **7.87 MB** |
| **10** | **22.12** | 0.80 | **0.23** | 8.60 MB |
| 15 | 21.90 | 0.80 | 0.24 | 8.28 MB |

Three retrainings at different `K`. The paper's reading: `K = 10` "yields the best
rendering quality", and going to 15 costs 0.22 dB, "because excessive coupled primitives
could lead to an inaccurate prediction" `[paper §4.3]`.

- ⚠️ **The margins are tiny**: `K=10` beats `K=5` by **0.08 dB** while being **9% larger**.
  On a rate-distortion basis `K = 5` is arguably the better operating point, and the paper
  does not compute BD-rate. `[inferred]`
- ⚠️ Size is **non-monotonic** in `K` (7.87 → 8.60 → 8.28), which is worth noting: more
  coupled primitives means more `g_k` to code, but also fewer anchors needed. The paper
  does not comment.
- Single scene, single run.

### Figure 8 — bitstream composition (not an ablation, but load-bearing)

`[paper Fig. 8]`, *Train*, three λ values:

| λ | Anchor | Coupled | Network weights |
|---|---|---|---|
| 0.001 | 32.05% | 38.39% | **29.56%** |
| 0.005 | 32.89% | 29.33% | **37.78%** |
| 0.01 | 29.87% | 24.14% | **45.98%** |

Bits per primitive: anchors **128.26 → 102.1 → 80.65**; coupled **15.36 → 9.11 → 6.52**.

- ✅ The paper's key structural claim is verified here: coupled primitives cost **~8–12×
  fewer bits** than anchors, despite being 10× more numerous.
- ⚠️ **The network weights are a fixed cost that comes to dominate**: at λ = 0.01 they are
  **46%** of the bitstream. Any claim about compression ratio at the high-λ end is really a
  claim about MLP size. Since the repo *does* count `weights.pth` in the reported total
  `[repo: TrainerCompGS.py:346-348]`, the accounting is honest — but this is the number to
  check when comparing against `compact3d/`, whose codebook is also a fixed cost, and
  against `mini-splatting/`'s `ms_c`, which has **no** network to store.
