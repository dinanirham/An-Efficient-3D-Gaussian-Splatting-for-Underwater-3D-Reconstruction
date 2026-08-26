# §4 — Full loss function

## 4.1 The objective is 3DGS's, unmodified

`[repo: train.py:100-102]`:
```python
Ll1 = l1_loss(image, gt_image)
loss = (1.0 - opt.lambda_dssim) * Ll1 + opt.lambda_dssim * (1.0 - ssim(image, gt_image))
loss.backward()
```
with `lambda_dssim = 0.2` `[repo: arguments/__init__.py:83]`.

```
L = 0.8 · L₁(Î, I) + 0.2 · (1 − SSIM(Î, I))
```

**No rate term, no regulariser, no auxiliary loss.** The paper writes no loss equation at all
— it presents only 3DGS's rendering equations `[paper Eqs. 1-2]` and then the architecture.
The one explicit statement is about the SVQ fine-tuning stage: "we freeze the indices and
finetune only the codebook **using the rendering loss, without introducing any additional
losses**" `[paper §3.2]`.

Loss-term count across your comparison set:

| Method | Terms | New terms added |
|---|---|---|
| 3DGS | 2 | — |
| **OMG** | **2** | **0** |
| `../mini-splatting/` | 2 | 0 |
| `../EDGS/` | 2 | 0 |
| `../compact3d/` | 3 | 1 (opacity regulariser) |
| `../CompGS/` (Liu) | 3 (+aux) | 2 (`λR` + volume reg.) |

### Why this matters

OMG achieves ~200× compression **without a rate–distortion objective**. `../CompGS/` puts
`λR` directly in the loss and sweeps λ; OMG instead gets its rate–distortion curve from a
**single post-hoc pruning threshold** τ, with quantization applied only in the last 1000
iterations. That is a genuinely different design philosophy, and it is why OMG's training time
(20–22 min) is close to Mini-Splatting's (19 min) while `../CompGS/`'s is 37.8 min
`[paper Tab. 3]` `[CompGS paper Tab. 7]`.

⚠️ **But the loss being unchanged does not make the pipeline unchanged.** OMG inherits
Mini-Splatting's undocumented *optimization* modifications — the removed `reset_opacity()`,
the LR-schedule rewind at 15 000 `[repo: train.py:73-77]` — and adds three optimizers of its
own (Group 3 and Group 4 in [`03-variables.md`](03-variables.md)).

## 4.2 What replaces "loss terms" as the object of study

OMG's analytical quantities are **selection and quantization rules**. Each is given with its
purpose and the failure it addresses.

### `Ī_i` — base importance (inherited from Mini-Splatting)

- **Form** `[paper Eq. 7]`: `Ī_i = Σ_{ρ=1}^{NR} w_{i,ρ}` if `∃ρ : w_{i,ρ} = max_j w_{j,ρ}`,
  else `0`. Two factors combined: (1) *has this Gaussian been the dominant contributor for at
  least one ray* (refs [14, 15] = Mini-Splatting's intersection preserving), and (2) *its total
  blending weight* (refs [46, 19]).
- **Repo** `[repo: scene/gaussian_model.py:627-650]` — Mini-Splatting's routine verbatim,
  including the `imp_metric` branch (`outdoor` → `accum_weights / area_proj`, `indoor` →
  `accum_weights`) and `imp_score[accum_area_max == 0] = 0`, which is the `∃ρ` gate.
- **Purpose:** a global relevance measure. **Failure it leaves open:** it is *blind to
  redundancy* — see below.

### `res_color` — local distinctiveness ⭐ **OMG's contribution (1)**

- **The problem, stated precisely** `[paper §3.3]`: "In cases where multiple Gaussians are
  located in close proximity, their blending weights tend to be **highly similar**, thus
  naively thresholding them can lead to two potential issues: (1) **abrupt performance
  degradation when all similar Gaussians are simultaneously removed**, and (2) **redundancy
  when multiple Gaussians with near-identical contributions are retained**."
  Note this is the *same* spatial-autocorrelation argument `../mini-splatting/` §4.2 makes
  against deterministic pruning — but where Mini-Splatting's answer was **stochastic
  sampling**, OMG's is a **deterministic distinctiveness term**.
- **Form** `[paper Eq. 8]`:
  `I_i = Ī_i · ( (1/D) Σ_{j ∈ N_i^K} ‖T_i − T_j‖₁ )^λ`
- **Repo** `[repo: gaussian_model.py:652-668]`:
  ```python
  order   = self.sort_morton()
  order_l = torch.clamp_min(order - 1, 0)
  order_r = torch.clamp_max(order + 1, torch.amax(order))
  ...
  res_color = torch.mean(torch.abs(ordered_color[order_l] - ori_color)
                       + torch.abs(ordered_color[order_r] - ori_color), dim=-1)
  imp_score = imp_score * res_color ** lambda_ld
  ```
- ⚠️ **`N_i^K` is exactly 2 neighbours** — the Morton predecessor and successor. The paper says
  "As computing exact K-nearest neighbors for every Gaussian is computationally expensive, we
  **approximate** neighbor selection by sorting Gaussians in **Morton order** and selecting
  Gaussians with **adjacent indices**" `[paper §3.3]`, so the approximation is disclosed —
  but `K` is not a free parameter, it is fixed at 2. See D-1.
- ⚠️ **`λ = 2.0` is an exponent, and its value is never stated** `[repo: arguments/__init__.py:99]`.
- **What it prevents if removed:** measured directly — see Table 4 in §4.4.
- **Which feature is compared:** `T` (the 3-D static appearance feature) once the net exists,
  falling back to `_features_dc[:, 0]` before iteration 15 000
  `[repo: gaussian_model.py:657-662]`. Since `net_itr (15 000) < simp_iteration2 (20 000)`, the
  `T` branch is the one that runs.

### `F_n` — the space feature ⭐ **OMG's contribution (2)**

- **Form** `[paper Eqs. 3-4]`:
  `h_n^(0) = MLP_t(cat(T_n, F_n))`, `o_n = MLP_o(cat(T_n, F_n))`,
  `h_n^(1,2,3) = MLP_v(cat(V_n, F_n))`, `F_n = MLP_s(γ(p_n))`.
- **Purpose — the paper's core architectural argument** `[paper §3.1]`: neural fields exploit
  local continuity, but "this assumption **weakens as Gaussians become sparser**". Conversely,
  "entirely disregarding local continuity leads to an inefficient representation". So OMG
  keeps *both*: a tiny per-Gaussian feature (irregularity) **concatenated with** a
  position-decoded feature (continuity).
- **And geometry is excluded on purpose:** "Especially for geometry, each Gaussian covers a
  larger spatial region, requiring a more specific scale and rotation … Therefore, we retain
  the per-Gaussian parameterization for scale and rotation as in 3DGS" `[paper §3.1]`.
- **What it prevents if removed:** measured — Table 4, and the paper offers a mechanism:
  "The absence of spatial information introduces **instability in attribute learning,
  hindering effective importance scoring**" `[paper §4.3]`. I.e. `F` helps LD scoring
  *indirectly*, by making `T` a better-behaved signal to compare between neighbours.

### SVQ ⭐ **OMG's contribution (3)**

- **Form** `[paper Eqs. 5-6]`: partition `z ∈ ℝ^{ML}` into `M` sub-vectors of length `L`; each
  partition `m` gets its own codebook `C^(m) ∈ ℝ^{B×L}`; `ẑ = cat(C^(1)[i_1], …, C^(M)[i_M])`
  with `i_m = argmin_j ‖z_m − C^(m)[j]‖²₂`.
- **The trade-off it navigates** `[paper §3.2]`: plain **VQ** needs a large codebook ⇒ heavy
  computation; **R-VQ** reduces per-codebook size but "multiple code indices per attribute
  result in **increased storage overhead**". SVQ reduces *dimensionality* per quantized unit
  instead, so codebooks shrink **and** there is one index per sub-vector.
- **Repo config** `[repo: arguments/__init__.py:100-105]`: scale `(M=1, B=64)`, rotation
  `(M=2, B=512)`, appearance `(M=2, B=1024)`. ⚠️ `M = 1` for scale means it is **plain VQ**,
  not SVQ.
- **Training strategy** `[paper §3.2]`: K-means init at 29 000, indices **frozen**, codebook
  finetuned for the final 1000 iterations. ⚠️ At `lr = 1e-8` `[repo: gaussian_model.py:818]`
  that finetuning is nominal. See D-2.

## 4.3 Reading the ablations

### Table 4 — component ablation: **leave-one-out, plus a joint removal**

`[paper Tab. 4]`, Mip-NeRF 360, reported for **two** variants:

| OMG-M | PSNR | SSIM | LPIPS | #Gauss | Size |
|---|---|---|---|---|---|
| **full** | **27.21** | **0.814** | **0.229** | 0.56 M | 5.31 |
| w/o Space feature | 26.96 | 0.811 | 0.232 | 0.59 M | 5.58 |
| w/o LD scoring | 27.09 | 0.813 | 0.230 | 0.57 M | 5.36 |
| w/o Both | 26.81 | 0.809 | 0.234 | 0.59 M | 5.59 |
| w/o SVQ | 27.26 | 0.817 | 0.226 | 0.56 M | **26.1** |

| OMG-XS | PSNR | SSIM | LPIPS | #Gauss | Size |
|---|---|---|---|---|---|
| **full** | **27.06** | **0.807** | **0.243** | 0.43 M | 4.06 |
| w/o Space feature | 26.85 | 0.804 | 0.246 | 0.44 M | 4.17 |
| w/o LD scoring | 26.83 | 0.804 | 0.246 | 0.43 M | 4.12 |
| w/o Both | 26.52 | 0.798 | 0.252 | 0.45 M | 4.24 |
| w/o SVQ | 27.06 | 0.809 | 0.241 | 0.43 M | **19.8** |

**Precisely what each row represents.** Rows 2–3 are **leave-one-out** from the full model
(each removes exactly one component); row 4 removes **both**; row 5 removes SVQ only. This is
a genuine leave-one-out table — **the cleanest ablation structure in your entire comparison
set**, and notably it is *not* the cumulative-additive form used by `../mini-splatting/`,
`../CompGS/` and `../seasplat/`.

- ✅ You **may** attribute: "removing LD scoring costs 0.23 dB on OMG-XS", "removing the space
  feature costs 0.21 dB", "removing both costs 0.54 dB."
- ⭐ **The paper's orthogonality claim is directly supported.** On XS: −0.23 (LD) + −0.21
  (space) = −0.44 individually, versus **−0.54** jointly. Near-additive, and the paper says
  so: "when both … are removed, the model experiences the most substantial performance drop.
  This indicates that the two contributions are **orthogonal**, independently contributing"
  `[paper §4.3]`. ✅ Supported by the arithmetic.
- ⚠️ **Both components matter more at the smaller variant.** LD scoring: **−0.12 dB** on M vs
  **−0.23 dB** on XS. The paper predicts this: "This effect becomes even more pronounced when
  the target Gaussian number is lower" `[paper §4.3]` — consistent with its whole thesis that
  sparsity is where these problems bite.
- ⚠️ **"w/o SVQ" is *better* on quality** (M: 27.26 vs 27.21; XS: 27.06 vs 27.06, SSIM 0.809 vs
  0.807) at **~5× the size**. So SVQ costs ≤0.05 dB for a 4.9× reduction — an excellent
  trade, correctly framed by the paper as "performance-storage efficiency" `[paper §4.3]`,
  not as a quality improvement.

### Figure 5 — LD scoring **without** attribute compression

`[paper Fig. 5, §4.3]`: a PSNR-vs-#Gaussians curve on Mip-NeRF 360 and T&T. Claim: OMG + LD
scoring "achiev[es] similar performance compared to Mini-Splatting that use **20–30% more
Gaussians**". Published only as a plot — `[unverified]` for exact numbers.

This is the cleanest isolation of contribution (1), because it removes SVQ and the neural
field from the comparison entirely.

### Table 5 — SVQ vs VQ vs R-VQ: **mutually-exclusive variants**

`[paper Tab. 5, §4.3]`. Three quantizers, same "clever training strategy" (one K-means before
the final 1K iterations, then codebook-only updates).

- **VQ**: "incurs a **13–18× increase in codebook initialization time**" because it needs
  `2¹⁴` entries per attribute, "**Nevertheless, VQ leads to lower rendering quality and/or
  increased storage costs across variants**."
- **R-VQ**: "slightly faster codebook initialization than SVQ but performs **poorly in terms of
  rate-distortion efficiency**, yielding higher storage and lower quality."
- ⚠️ The table's numeric cells did not survive text extraction cleanly. `[unverified]` for
  exact values; the directional claims above are quoted verbatim.

### Table 3 — the variant family (efficiency)

| Method | Training | #Gauss | Size | PSNR | SSIM | LPIPS |
|---|---|---|---|---|---|---|
| Mini-Splatting | 19m 25s | 531 K | 119.5 | 27.39 | 0.822 | 0.216 |
| LocoGS-S | 1h | 1.09 M | 7.90 | 27.04 | 0.806 | 0.232 |
| LocoGS-L | 1h | 1.32 M | 13.89 | 27.33 | 0.814 | 0.219 |
| **OMG-XS** | **20m 15s** | **427 K** | **4.06** | 27.06 | 0.807 | 0.243 |
| OMG-S | 20m 57s | 501 K | 4.75 | 27.14 | 0.811 | 0.235 |
| OMG-M | 21m 10s | 563 K | 5.31 | 27.21 | 0.814 | 0.229 |
| OMG-L | 21m 32s | 696 K | 6.52 | 27.28 | 0.818 | 0.220 |
| **OMG-XL** | 22m 26s | 727 K | **6.82** | **27.34** | **0.819** | **0.218** |

**A genuinely clean rate–distortion family from one knob** (τ), and the strongest single
comparison in the paper: **OMG-XL beats LocoGS-L on every metric at half the size and a third
of the training time**.

⚠️ **But OMG never matches its own base method on quality.** Mini-Splatting: 27.39 / 0.822 /
0.216 at 119.5 MB; OMG-XL: 27.34 / 0.819 / 0.218 at 6.82 MB. So the honest framing is
**−0.05 dB for 17.5× smaller** — excellent, and not "better than Mini-Splatting".

## 4.4 What is *not* ablated

| Component | Ablated? |
|---|---|
| `λ = lambda_ld = 2.0` (the LD exponent) | ❌ — value not even stated |
| `K = 2` Morton neighbours | ❌ — no sweep over neighbourhood size |
| `D = 3` feature dimensionality | ❌ |
| Space-feature dimension (13), MLP width (64), depth (1), `n_frequencies` (16) | ❌ |
| **Keeping geometry per-Gaussian** (vs neural-fielding it) | ❌ — the paper's sharpest design claim `[paper §3.1]`, argued but never measured. LocoGS does the opposite; no head-to-head ablation isolates this choice |
| SVQ partition counts `M` and codebook sizes `B` per attribute | ❌ |
| `svq_itr = 29 000` (the 1K finetuning window) | ❌ |
| `net_itr = 15 000` | ❌ |
| Codebook finetuning lr (`1e-8`) | ❌ — and see D-2 |
