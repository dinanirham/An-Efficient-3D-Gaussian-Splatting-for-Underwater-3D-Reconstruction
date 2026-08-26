# §4 — Full loss function

> ⚠️ **Everything in this section is `[paper-only]`.** The released package refuses to run in
> training mode — `assert not self.training, "Currently only inference mode released"`
> `[repo: src/romav2/romav2.py:172]` — and contains no loss functions, no optimizer loop and
> no data pipeline. I could not verify a single line of §4 against code. That is stated once
> here and assumed throughout.

RoMa v2 has **two disjoint objectives**, one per training stage, because the paper adopts
UFM's decoupled schedule: the matcher is trained to convergence, **frozen**, and only then
are the refiners trained `[paper §3.1, §3.3]`.

---

## 4.1 Stage 1 — the matching loss

> `L_matcher = L_NLL + L_warp(r_{θ_matcher}, p_GT) + λ·L_overlap(p_{θ_matcher}, p_GT)`,
> `λ = 0.1` `[paper Eq. 2]`

### 1. `L_NLL` — patch-level negative log-likelihood ⭐ **the paper's contribution #1**

- **Closed form** `[paper Eq. 1]`:
  `L_NLL = Σ_{m=1}^{M} −log( Softmax(S_m)_{n*} )`
  where `S ∈ ℝ^{M×N}` is the patch-similarity matrix, Softmax is over the **second**
  dimension, and `n*` is "the index of the patch closest to the GT warp for patch `m`".
- **Purpose.** It is a *replacement for lost supervision*. RoMa v1's Gaussian Process gave
  the coarse matcher an explicit correspondence prior; removing it (because "the gradients
  through the GP were not sufficiently informative … and caused stability issues"
  `[paper §3.2]`) left the similarity matrix `S` trained only indirectly through the
  regression head. `L_NLL` supervises `S` **directly**, as a per-patch classification over
  candidate targets.
- The paper's own framing: "This approach can be seen as a **dense directional version of,
  e.g. LoFTR**" `[paper §3.2]`.
- **What it prevents if removed:** `S` degenerating into an uninformative attention pattern.
  This is exactly the difference measured in Table 2 — see §4.4.
- **Note it is a `Σ`, not a mean**, over all `M` patches in image A — so its magnitude scales
  with patch count, i.e. with resolution. How that interacts with the mixed-resolution
  training of `[paper §3.5]` is not discussed. `[unverified]`

### 2. `L_warp` — robust regression

- The **generalized Charbonnier** loss `[paper §3.3, ref [2]]`, shared with the refiners:
  `L_warp = ((i·c)^α)·( r²/(i·c)² + 1 )^{α/2}`, with `α = 0.5`, `c = 1e-3`, `i` the stride.
  (The extracted form is partially mangled; the parameter values are unambiguous.)
- **Change from RoMa v1:** "we **replace the classification-by-regression term** from the
  matching loss for the robust regression term `L_warp` used in the refinement loss"
  `[paper §3.2]`. RoMa classified warps into bins; v2 regresses them directly. Together with
  the GP removal, the coarse matcher's entire supervision scheme is new.
- **Purpose:** `α = 0.5` makes the loss strongly sub-quadratic, so gross mismatches
  (inevitable at the coarse stage) do not dominate the gradient.

### 3. `λ·L_overlap` — co-visibility

- Pixel-wise binary cross-entropy against `p_GT ∈ {0,1}`, `λ = 0.1`, explicitly "the same
  overlap loss `L_overlap`, and weighting factor (λ = 0.1), as in RoMa" `[paper §3.2]`.
- Ground truth derived "from either **consistent depth** (for MVS style datasets) or from
  **warp cycle consistency** (for flow datasets)" `[paper §3.3]` — necessary because the
  10-dataset mixture has heterogeneous supervision.
- **What it prevents if removed:** the model asserting correspondences for occluded pixels.
  Confidence is what makes a *dense* matcher usable downstream — `../EDGS/` filters on
  exactly this signal `[EDGS paper Eq. 9]`.

---

## 4.2 Stage 2 — the refinement loss

> `L_refiners = Σ_{i∈S} L_warp(r_{θ_i}, p_GT) + λ_ov·L_ov(p_{θ_i}, p_GT) + λ_prec·L_prec(Σ⁻¹_{θ_i}, detach(r_{θ_i}))`
> with `S = {1, 2, 4}`, `λ_ov = 1e-2`, `λ_prec = 1e-3` `[paper Eq. 5]`

The first two terms mirror Stage 1 (same Charbonnier, same BCE), now **summed over the three
refiner strides** — deep supervision at every scale.

### `L_prec` — predictive covariance ⭐ **the paper's contribution #4**

- **Parameterisation** `[paper §3.3]`: the network emits three raw values per pixel and maps
  them to Cholesky factors
  `l11 = Softplus(z11) + 1e-6`, `l21 = z21`, `l22 = Softplus(z22) + 1e-6`,
  `L = [[l11, 0], [l21, l22]]`, `Σ⁻¹ = L Lᵀ` — **positive-definite by construction**, no
  constraint or projection needed.
  ✅ **This one part *is* verifiable in code**: `chol_eps = 1e-6`,
  `l00 = F.softplus(delta_confidence[..., 1]) + chol_eps`,
  `l11 = F.softplus(delta_confidence[..., 3]) + chol_eps` `[repo: refiner.py:201-204]`,
  assembled by `prec_mat_from_prec_params` `[repo: geometry.py:168-174]`.
- **Objective** `[paper Eq. 4]`: the Gaussian NLL of the residual,
  `L_prec(r) = −log 𝒩(r | 0, Σ) = ½ rᵀΣ⁻¹r − ½ log det(Σ⁻¹) + log(2π)`.
  The two terms are the classic uncertainty trade-off: the first rewards **large** precision
  where the residual is small, the second penalises **inflating** precision everywhere.
- **Two stability devices, both essential and both stated:**
  1. **`detach(r)`** — "We **detach the residuals r** before the loss" `[paper §3.3]`. Without
     it, the model could reduce `L_prec` by making residuals *larger* wherever it had
     predicted low precision — a self-fulfilling degeneracy. This is the same gradient-routing
     pattern as `../seasplat/`'s `Ẑ.detach()` and `../seathru_NeRF/`'s detached sample
     spacing: **isolate the auxiliary head so it explains, rather than shapes, the primary
     prediction.**
  2. **Gating**: "we only train the model to predict this covariance for co-visible regions
     where `r < 8` pixels" `[paper §3.3]` — outliers would otherwise dominate a
     Gaussian NLL, which has no robustness at all.
- **Accumulation across strides:** `Σ⁻¹_i = Σ_{j≥i} Σ⁻¹_j`, "using the fact that information
  is **additive** in the precision parameterization" `[paper §3.3]` — the correct fusion rule
  for independent Gaussian estimates, and a neat justification for predicting precision
  rather than covariance.
- **λ_prec = 1e-3** — two orders below the warp loss. This is an *auxiliary* head; it is not
  allowed to steer the matcher.

---

## 4.3 The objective, assembled

```
STAGE 1  (300k steps, batch 128, lr 4e-4, ≈38M pairs)     [paper §3.2]
  L_matcher = 1.0 · L_NLL
            + 1.0 · L_warp        (Charbonnier, α=0.5, c=1e-3)
            + 0.1 · L_overlap     (BCE)
  → then FREEZE the matcher entirely

STAGE 2  (300k steps, batch 64, lr 4e-4, ≈19M pairs)      [paper §3.3]
  L_refiners = Σ_{i∈{1,2,4}} [ 1.0   · L_warp
                             + 1e-2 · L_ov
                             + 1e-3 · L_prec(Σ⁻¹, detach(r)) ]
  + EMA(decay 0.999) on the refiner weights                [paper §3.3]
```

Weight spread within Stage 2: **1000×**. Unlike `../seasplat/`, every one of these
coefficients is **stated in the paper** — the objective is fully specified, it simply cannot
be checked.

---

## 4.4 Reading the ablations — four kinds, all small and all clean

### Table 2 — matching architecture: **two complete alternatives**

`[paper Tab. 2]`, PCK on held-out Hypersim scenes, both trained "on a subset of the data
using the training setup outlined below":

| Method | PCK@1px | @3px | @5px |
|---|---|---|---|
| UFM | 11.2 | 48.3 | 67.4 |
| **RoMa v2** | **30.5** | **76.7** | **86.7** |

**Mutually-exclusive variants** — a reimplementation of UFM's matching architecture versus
RoMa v2's, trained identically. Not additive, not leave-one-out.

- ✅ **The largest margin in the paper** (2.7× PCK@1px), and the stated purpose is to isolate
  `L_NLL`: "In contrast to UFM, our matching objective **incorporates the auxiliary target
  `L_NLL`**. We compare these architectures in Table 2" `[paper §3.2]`.
- ⚠️ **But it is an architecture comparison, not a loss ablation.** The two systems differ in
  more than `L_NLL` (attention pattern, position embeddings, head). **There is no
  `L_NLL`-on/off row anywhere in the paper.** Do not attribute the 19-point PCK@1px gap to
  `L_NLL` alone — the paper does not, and neither should a citation.
- ⚠️ Held-out Hypersim only, one training subset, one run.

### Table 1 — frozen backbone: **two variants, linear probe**

| Backbone | EPE | Robustness % (err < 32 px) |
|---|---|---|
| DINOv2 | 27.1 | 77.0 |
| **DINOv3** | **19.0** | **86.4** |

A **linear probe** on frozen features + kernel-NN matching — deliberately minimal, so it
measures the *features*, not the matcher. Methodologically the cleanest comparison in the
paper, and inherited from RoMa v1's own methodology ("Inspired by RoMa [12], we compare the
encoders (frozen) by training a single linear layer" `[paper §3.2]`).

### Table 10 — backbone, end-to-end: **and it disagrees with Table 1 on WxBS**

| Backbone | WxBS | Hypersim |
|---|---|---|
| DINOv2 | **35.6** | 78.1 |
| DINOv3 | 34.2 | **79.2** |

⚠️ **DINOv2 wins on WxBS.** Table 1 (linear probe, MegaDepth) says DINOv3 is uniformly more
robust; Table 10 (end-to-end, multi-modal) says otherwise. The paper is honest about the
consequence in §5: "Compared to RoMa, our model is **slightly less robust to extreme changes
in modality**", and traces it in §4.5: "RoMa v2 and UFM both struggle with the **IR-to-RGB**
multi-modal subset of WxBS."

**This is the one regime where `../RoMa/` v1 is the better choice**, and Table 11 confirms it
at the system level: RoMa **60.8** vs RoMa v2 **55.4** mAA on WxBS.

### Table 9 — refiner EMA: **on/off, a true two-row ablation**

| | Mega-1500 (AUC@5/10/20) | ScanNet-1500 |
|---|---|---|
| w/o EMA | 61.4 / 75.8 / 85.7 | 33.6 / 56.1 / 73.5 |
| **EMA** | **62.8 / 77.0 / 86.6** | 33.6 / **56.2** / **73.8** |

The **only genuine leave-one-out ablation in the paper**, and its selectivity is the point:
**+1.4 AUC@5 on MegaDepth** (sub-pixel-sensitive) versus **+0.0 on ScanNet** (not). The
caption states the mechanism: "Refiner EMA improves results **specifically on benchmarks that
require subpixel precision**" `[paper Tab. 9]`, backed by the measured ±0.1 px bias in
Fig. 5a and its disappearance in Fig. 5b.

### Table 8 — CUDA kernel: **on/off**

| Method | Throughput (pairs/s) | Mem (GB) |
|---|---|---|
| UFM | 43.0 | 16.2 |
| RoMa | 18.5 | 4.7 |
| RoMa v2 (w/o K) | 30.3 | 5.6 |
| **RoMa v2 (w/ K)** | **30.9** | **4.8** |

The kernel is a **memory** optimisation, not a speed one (+2% throughput, **−14% memory**).
The 1.7× speedup over RoMa comes from elsewhere — chiefly the stride-4 DPT head reducing the
refiner count from 5 to 3 `[paper §3.3]`. `[inferred]`

### Table 12 — predictive covariance downstream: **cumulative-additive**

| Method | AUC@1 | @3 | @5 |
|---|---|---|---|
| RoMa v2 (w/o Σ⁻¹) | 54.9 | 79.5 | 85.9 |
| + Σ⁻¹ Refine | **75.8** | 89.0 | 92.6 |
| + Σ⁻¹ RANSAC + Refine | **76.4** | **89.3** | **92.8** |

Rows nest: post-hoc refinement first, then covariance-weighted scoring *inside* RANSAC as
well. **+20.9 AUC@1 from post-processing alone**, +0.6 more from the RANSAC change — so
essentially all the benefit comes from the refinement step, and the paper says so
("we improve by ∼20 points on AUC@1" `[paper §4.8]`). Hypersim only.

### Table 13 — the sub-pixel argument, by construction

| Method | MegaDepth-1500 AUC@5/10/20 |
|---|---|
| UFM | 41.5 / 57.9 / 72.4 |
| RoMa v2 | 62.8 / 77.0 / 86.6 |
| **RoMa v2 (perturbed to UFM's error distribution)** | **46.3 / 63.7 / 77.4** |

A quantile-mapping experiment `[paper Eq. 7]`: perturb RoMa v2's residuals so their
distribution matches UFM's, and 62.8 collapses to 46.3 — within 5 points of UFM's 41.5.
**This is the strongest methodological move in the paper**: it converts "we win because we are
more precise" from a hypothesis into a near-controlled experiment. Cite it.

---

## 4.5 What is *not* ablated

| Component | Ablated? |
|---|---|
| `L_NLL` on/off | ❌ — only the UFM-vs-v2 *architecture* comparison of Tab. 2 |
| `L_prec` on/off during training | ❌ — Tab. 12 ablates only its *downstream use* |
| `λ` values (0.1, 1e-2, 1e-3) | ❌ |
| Two-stage vs joint training | ❌ — adopted from UFM on the stated grounds of "rapid experimentation" `[paper §3.1]` |
| Data-mixture weights (Tab. 3) | ❌ — motivated qualitatively in §3.4 (Figs. 6a, 6b) |
| `temp` 0.2 → 0.1 | ❌ — and not even mentioned; see D-1 |
| `scale` 8 → 1 | ❌ ablated, but argued in §3.5 |
| Charbonnier `α`, `c` | ❌ — inherited from RoMa |
