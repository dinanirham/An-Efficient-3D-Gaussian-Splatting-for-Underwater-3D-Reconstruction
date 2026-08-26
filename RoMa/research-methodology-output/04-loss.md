# §4 — Full loss function

✅ **Verified against code** — `romatch/losses/robust_loss.py` and
`experiments/train_roma_outdoor.py` are both released, unlike `../RoMaV2/`.

## 4.1 The paper's statement

> `L = L_coarse + L_fine` `[paper Eq. 19]`

and, notably:

> "Note that we do **not need to tune any scaling** between these losses as the coarse
> matching and fine stages are **decoupled as gradients are cut in the matching**, and
> encoders are not shared." `[paper §3.4]`

That is a real structural argument, not a convenience: because gradients are detached between
refiners `[paper §3.1]` and the coarse/fine encoders are separate `[paper §3.2]`, the two
losses optimize **disjoint parameter sets** and cannot compete. It is confirmed in code by
`scale_weights = {1:1, 2:1, 4:1, 8:1, 16:1}` — all ones `[repo: robust_loss.py:106]`, with a
comment describing a weighting mechanism that is then not used.

## 4.2 The derivation — why two *different kinds* of loss

This is the paper's most transferable contribution, and it is derived rather than tuned.

**The theoretical model** `[paper Eq. 10]`:
`q(x^A, x^B; s) = 𝒩(0, s²I) ∗ p(x^A, x^B; 0)`
— matchability at scale `s` is the exact infinite-resolution matching **diffused** by a
Gaussian of width `s`.

**The consequence** `[paper §3.4, Fig. 3]`: at **motion boundaries** (discontinuities where
different objects project to adjacent pixels) that diffusion mixes two distinct correct
answers, so the coarse conditional `p(x^B | x^A)` becomes **multimodal**. Conditioned on a
previous estimate, as in refinement, it is **locally unimodal**.

**Therefore:**

| Stage | Distribution | Required capability | Loss |
|---|---|---|---|
| Coarse | multimodal | represent multiple modes | **regression-by-classification** |
| Fine | unimodal, but the initialisation may be far outside the support | tolerate gross outliers | **robust regression** |

The paper states the second half explicitly: "if this initial choice is far outside the
support of the distribution, using a non-robust loss function is problematic. It is therefore
motivated to use a robust regression loss for this stage" `[paper §3.4]`.

Both losses are then obtained as **KL divergences** against `q` `[paper Eqs. 11-18]` — the
objective is derived from the model, not chosen empirically. Compare DKM, which used
non-robust L2 at both stages `[paper §1]`.

## 4.3 Term-by-term

### 1. `L_coarse` — regression-by-classification

- **Model** `[paper Eq. 8]`: `p_coarse,θ(x^B | x^A) = Σ_{k=1}^{K} π_k(x^A) B_{m_k}`, with
  `K = 64 × 64` anchors "positioned uniformly as a tight cover of the image grid" and
  `B = U` uniform — "This ensures that there is **no overlap between anchors and no holes**
  in the cover" `[paper footnote 2]`.
- **KL form** `[paper Eq. 14]`:
  `−∫ [ log π_{k(x^A)} + λ log p_coarse,θ(x^A) ] dq`, where `k(x) = argmin_k ‖m_k − x‖`.
- **Repo** `[repo: robust_loss.py:43-61]`:
  ```python
  G  = meshgrid(linspace(-1+1/64, 1-1/64, 64))          # the K anchor coordinates
  GT = (G[None,:,None,None,:] - x2[:,None]).norm(dim=-1).min(dim=1).indices   # nearest anchor
  cls_loss      = F.cross_entropy(scale_gm_cls, GT, reduction='none')[prob > 0.99]
  certainty_loss = F.binary_cross_entropy_with_logits(gm_certainty[:,0], prob)
  ```
  combined as `cls_loss + 0.01 · certainty_loss` `[repo: robust_loss.py:145]`.
  ✅ Cross-entropy against the nearest anchor is exactly Eq. 13/14, and the BCE on
  matchability is the `λ log p_coarse,θ(x^A)` term.
- **`λ = ce_weight = 0.01`** `[repo: train_roma_outdoor.py:215]` — **the paper never gives
  this value.**
- **Decoding to a warp** `[paper Eq. 9]`: `argmax` over anchors, then a **local softargmax**
  over `N₄(k̂)` (the anchor and its four neighbours). Classification for expressiveness,
  local regression for precision.
- **What it prevents if removed:** L2 regression on a multimodal target converges to the
  *mean of the modes* — a coordinate that is correct for neither object at a motion boundary.
  Setup V→VI in Table 2 measures exactly this swap: **14.3 → 13.6** 100-PCK@1px.

### 2. `L_fine` — robust generalized-Charbonnier regression

- **Model** `[paper §3.4]`: refinement output at scale `i` is generalized-Charbonnier
  distributed with `α = 0.5`, giving the log-likelihood
  `log p(x^B_i | x^A_i, Ŵ_{i+1}) = −(‖μ(x^A_i, Ŵ_{i+1}) − x^B_i‖₂ + s)^{1/4}`, `s = 2^i c`
  `[paper Eqs. 15-16]`.
- **Repo** `[repo: robust_loss.py:82-100]`:
  ```python
  epe      = (flow.permute(0,2,3,1) - x2).norm(dim=-1)
  ce_loss  = F.binary_cross_entropy_with_logits(certainty[:, 0], prob)
  a        = self.alpha            # 0.5
  cs       = self.c * scale        # c · 2^i
  x        = epe[prob > 0.99]
  reg_loss = cs**a * ((x/cs)**2 + 1**2)**(a/2)
  ```
  combined as `reg_loss + 0.01 · ce_loss` `[repo: robust_loss.py:158]`.
  ✅ The functional form matches; `α = 0.5` ⇒ exponent `α/2 = 1/4`, i.e. the paper's `^{1/4}`.
- ⚠️ **`c = 1e-4` in code vs `c = 0.03` in the paper** — `[repo: train_roma_outdoor.py:220]`
  vs `[paper §3.4]` "In practice, we choose c = 0.03." A **300× difference** in the loss's
  transition point between quadratic and sub-linear behaviour. See
  [`06-implementation-deltas.md`](06-implementation-deltas.md) D-1.
- **Why robust:** Fig. 4 plots the gradient — "locally matches L2 gradients, but globally
  decays with `|x|^{-1/2}` toward zero" `[paper Fig. 4]`. Gross outliers contribute almost no
  gradient.
- **What it prevents if removed:** a single badly-initialised pixel dominating the refiner's
  update. Setup VI→VII: **13.6 → 13.1** 100-PCK@1px.

### 3. Two undocumented supervision masks

Both gate *every* loss term, and neither appears in the paper.

**(a) `prob > 0.99`** `[repo: robust_loss.py:51, 71, 91]` — losses are computed only where the
ground-truth co-visibility probability is essentially certain. The certainty BCE is
unmasked (it needs the negatives). There is even a guard for the degenerate case:
`if not torch.any(cls_loss): cls_loss = certainty_loss * 0.0  # Prevent issues where prob is 0 everywhere`
`[repo: robust_loss.py:53-54]`.

**(b) The local-EPE gate** `[repo: robust_loss.py:138-141]`:
```python
if self.local_largest_scale >= scale:
    prob = prob * (F.interpolate(prev_epe[:, None], size=(h,w), mode="nearest-exact")[:, 0]
                   < (2 / 512) * (self.local_dist[scale] * scale))
```
with `local_dist = {1:4, 2:4, 4:8, 8:8}`, `local_largest_scale = 8`
`[repo: train_roma_outdoor.py:216-217]` and `prev_epe` detached from the coarser scale
`[repo: robust_loss.py:160]`.

**In words:** a refiner at scale `s` is supervised **only at pixels where the previous,
coarser scale was already within ~`local_dist[s] · s` pixels**. Refiners are not asked to fix
matches the coarse stage got badly wrong — consistent with the paper's own framing that
refinement is *conditional* on a previous estimate, but it is a hard gate, not a soft one,
and it is invisible in the paper. See D-2.

## 4.4 The objective, as implemented

```
L = Σ_{s ∈ {16, 8, 4, 2, 1}}  1.0 · [
        s == 16 :  CrossEntropy(anchor logits, nearest anchor)|_{prob>0.99}
                   + 0.01 · BCE(gm_certainty, prob)
        else    :  (c·s)^0.5 · ((epe/(c·s))² + 1)^0.25 |_{prob>0.99 ∧ prev_epe < τ(s)}
                   + 0.01 · BCE(certainty, prob)
    ]
where c = 1e-4  (paper: 0.03),  τ(s) = (2/512)·local_dist[s]·s
```
`[repo: robust_loss.py:102-161; train_roma_outdoor.py:214-220]`

## 4.5 Reading the ablation — **Table 2 is a CUMULATIVE-ADDITIVE ladder**

`[paper Tab. 2]`, on a custom MegaDepth validation set (scenes 0015, 0022), at **448×448**
`[paper §4.1, §4.2]`. **Metric is 100−PCK, so LOWER IS BETTER.**

| Setup | Change (relative to the row above) | 1px | 3px | 5px |
|---|---|---|---|---|
| I | **Baseline: DKM**, retrained | 17.0 | 7.3 | 5.8 |
| II | + decouple coarse/fine encoders (both RN50) | 16.0 | 6.1 | 4.5 |
| III | + `F_fine = VGG19` | 14.5 | 5.4 | 4.5 |
| IV | + `D = Transformer` (still regression) | 14.4 | 5.4 | 4.1 |
| V | + `F_coarse = DINOv2` | 14.3 | 4.6 | 3.2 |
| VI | + `L_coarse = reg.-by-class.` | 13.6 | 4.1 | 2.8 |
| **VII** | **+ `L_refine = robust` → RoMa** | **13.1** | **4.0** | **2.7** |
| VIII | VII, but `D = ConvNet` (revert IV) | 14.0 | 4.9 | 3.5 |

**Precisely what each row represents.** Rows I–VII are **cumulative**: each is the previous
row plus one change. The paper's own wording confirms it — "In Setup II we do not share
weights…", "In Setup III we **replace** the RN50 fine features…", "We **then add** the
proposed Transformer match decoder in Setup IV", "Next, in Setup VI **change** the loss
function…" `[paper §4.1]`.

**Setup VIII is different in kind** — it is a **leave-one-out from the full model**, reverting
only the decoder. The paper is explicit: "When we change back to the original ConvNet match
decoder in Setup VIII **from this final setup**" `[paper §4.1]`. This is the one row that
licenses an isolated attribution.

### What this licenses

- ✅ "Decoupling the encoders alone improves 100-PCK@1px from 17.0 to 16.0."
- ✅ "Swapping the fine encoder to VGG19, on top of decoupling, gives a further 1.5."
- ✅ **"Removing the Transformer decoder from the full model costs 0.9 (13.1 → 14.0) at 1px
  and 0.8 at 5px"** — from Setup VIII, a genuine leave-one-out.
- ❌ You may **not** read row IV's small gain (14.4 vs 14.3 at 1px) as "the Transformer decoder
  contributes 0.1". The paper anticipates this: the decoder "**particularly improves
  performance when used to predict anchor probabilities**" `[paper §1]` — i.e. it interacts
  with Setup VI. **Setups IV and VIII measure the same component in different contexts and
  disagree by 9×.** That interaction is the paper's point, and it is exactly the kind of
  claim an additive table alone cannot support — which is why Setup VIII exists.
- ⚠️ Single validation set, two scenes, 448×448, single run, no error bars.

### Component-wise, from the ladder

| Contribution | Rows | Δ 100-PCK@1px |
|---|---|---|
| (a) Feature decoupling + specialisation | I→III | **−2.5** |
| (a) DINOv2 coarse | IV→V | −0.1 @1px, but **−0.8 @3px, −0.9 @5px** |
| (b) Transformer decoder | VIII→VII | **−0.9** |
| (c) Regression-by-classification | V→VI | **−0.7** |
| (c) Robust refinement | VI→VII | **−0.5** |

⚠️ **DINOv2's benefit is almost invisible at 1px and clear at 3–5px** — consistent with the
paper's own framing that DINOv2 supplies *robustness* (getting roughly right), while VGG19
fine features supply *precision*. Table 1's "Robustness %" metric (matches with error < 32px)
is defined for exactly this reason: "while these matches are not necessarily accurate, it is
typically sufficient for the refinement stage to produce a correct adjustment" `[paper §3.2]`.

**The headline benchmark result is far larger than any ablation row**: **WxBS 58.9 → 80.1
mAA (+36%)** over DKM `[paper Tab. 4]`, on a benchmark of extreme viewpoint/illumination/
modality change — precisely where a frozen foundation backbone should help and where the
in-distribution MegaDepth validation set cannot show it.
