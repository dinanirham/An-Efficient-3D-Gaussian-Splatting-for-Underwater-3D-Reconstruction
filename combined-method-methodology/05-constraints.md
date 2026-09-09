# §5 — Constraints, well-posedness, and the per-configuration risk register

## 5.1 The baseline's well-posedness apparatus, carried forward

SeaSplat's forward model is

```
Î(x) = Ĵ(x) ⊙ exp(−β_att Ẑ(x))  +  σ(B^∞) ⊙ (1 − exp(−β_bs Ẑ(x)))
```

against a naive objective `min ‖Î − I‖`. Per pixel there are 3 observations and 4 free values
(`Ĵ ∈ ℝ³`, `Ẑ ∈ ℝ`) before counting 9 global scalars. The system is underdetermined by
construction, and `../seasplat/05-constraints.md` names four *specific* degenerate solutions
and five resolving mechanisms. Both lists are carried forward unchanged — no mechanism in
this work adds or removes one.

| Degeneracy | What it is | Killed by |
|---|---|---|
| **D-1** "no medium" | `β = 0 ⇒ Â = 1, B̂ = 0, Î = Ĵ`. Not a local minimum — a **global optimum of `L_GS`**, at least as good as the intended solution | M-3 (`L_bs`), M-5 (staging + `B^∞ ← learned_bg`) |
| **D-2** depth ↔ medium scale | `β` and `Ẑ` appear only as the product `βẐ`; `Ẑ ← cẐ, β ← β/c` leaves `Î` **exactly** invariant | M-1 (detachment), M-2 (alternating opt), M-4 (global homogeneity) |
| **D-3** colour gauge | `Ĵ_c ← γ_c Ĵ_c, β_att,c ← β_att,c + ln(γ_c)/Ẑ` leaves the direct term unchanged — the *restored* colour has an unconstrained per-channel gain | M-3 (`L_gw`, `L_sat`) |
| **D-4** water-column floaters | high-opacity low-texture Gaussians near the camera reproduce veiling haze as *geometry*. Photometrically excellent, geometrically nonsense — the failure 3DGS actually finds | M-3 (`L_op`), M-4 |

| Mechanism | What it is |
|---|---|
| **M-1** gradient detachment | every auxiliary prior is surgically routed to exactly one parameter group; medium losses see `Ẑ.detach()` |
| **M-2** alternating optimization | three disjoint Adam optimizers; 50 medium-only steps per 100 Gaussian steps, never on the same pass |
| **M-3** auxiliary priors | `L_bs`, `L_gw`, `L_sat`, `L_op`, `L_Zsmooth` |
| **M-4** global homogeneity | 9 scalars for the whole scene — "by far the strongest constraint in the system, and it is a **modelling choice, not a loss**" |
| **M-5** staged warm-up | `seathru_from_iter`; 1 000 medium-only + 2 000 colour-only steps; `B^∞ ← learned_bg` transfer |

**None of the three mechanisms introduces a `.detach()`, a new optimizer, or a new prior.**
M-1 and M-2 therefore survive the composition untouched, and this is verifiable rather than
hopeful: `../EDGS/07-pseudocode.md` pt.5 states "There is no `.detach()` anywhere in this
method", and `../mini-splatting/07-pseudocode.md` pt.1 states "There is no `.detach()` and no
auxiliary loss in the entire method." M3's straight-through estimator routes gradients to the
unquantized parameters the baseline's optimizer already holds
`[../compact3d/07-pseudocode.md line 20]`.

**What the mechanisms *do* touch is M-3, M-4 and M-5** — via the shared variables of
`03-variables.md` §3.5. That is the entire risk surface, and §5.3 enumerates it.

---

## 5.2 What each mechanism brings with it

Each mechanism has its own degeneracies, documented in its own folder. They arrive with it.

### M1 — EDGS `[../EDGS/05-constraints.md]`

| # | Degeneracy | Its own remedy | Survives on this baseline? |
|---|---|---|---|
| E-2 | Triangulation is ill-posed for near-parallel view rays | `p^proj` reprojection filter | ✅ but see E-5 |
| E-3 | Dense matchers hallucinate — a warp for **every** pixel, including sky, water, textureless surfaces | `p^corr` confidence filter | ⚠️ **the water column is the named worst case** |
| E-4 | Confidence and geometry are independent failure modes | both filters + `max_j`, `Π_i` | ✅ |
| E-5 | `p^proj` is implemented as an **opacity mask** (logit −10), not a sampling distribution — failing points are kept | the `α < 0.005` prune, plus the ×0.99 decay | ⚠️ interacts with `L_op` |
| E-6 | Triangulation gives position only; scale is unconstrained | distance-proportional isotropic scale, × 0.5 | ✅ |
| — | **No mechanism to add primitives.** A region the matcher misses stays empty forever | none | ❌ **unresolved, and worse underwater** |

### M2 — Mini-Splatting `[../mini-splatting/05-constraints.md]`

| # | Degeneracy | Its own remedy | Survives on this baseline? |
|---|---|---|---|
| S-1 | `overlapping` — redundant clustered Gaussians | depth reinit; intersection preserving | ✅ (reinit only if the densification half is used) |
| S-2 | `under-reconstruction` — oversized smooth-region Gaussians the gradient criterion never splits | blur split (a criterion **orthogonal to the gradient**) | ✅ |
| S-3 | Blended depth is not identified — collapse, misalignment, blending boundary. Reinit from blended depth gives PSNR **17.67** vs **27.54** from mid-point depth, a **9.87 dB** collapse | mid-point depth of the single **argmax** Gaussian, no blending | ⚠️ **see §5.4 — the baseline uses blended depth** |
| S-4 | Deterministic top-`k` pruning destroys local geometry because importance is **spatially autocorrelated** | importance-weighted **stochastic** sampling, validated by Chamfer distance rather than PSNR | ✅ — and this is why M2 is the right pruning mechanism for a budget |
| — | **No depth ⇒ no reinitialization** ("fails in areas without a certain depth value, such as the sky") | none | ❌ **unresolved; the water column is the analogue** |
| — | `imp_metric` is hand-picked per scene type, with no automatic selection | none | ❌ **no underwater option exists** |

### M3 — CompGS-VQ `[../compact3d/05-constraints.md]`

| # | Degeneracy | Its own remedy | Survives on this baseline? |
|---|---|---|---|
| C-1 | Post-hoc clustering degrades quality — nothing in the objective makes parameters clusterable | quantization-**aware** training | ⚠️ only ~10 000 iterations remain after the ordering fix (`03-variables.md` IC-4) |
| C-2 | Quantization is non-differentiable | straight-through estimator | ✅ |
| C-3 | A single codebook over heterogeneous parameters is meaningless | grouped independent codebooks | ✅ — but with **three** groups, not four |
| C-4 | K-means per iteration is intractable | centroids every step, assignments every `t = 100` | ✅ — the enabling trick, and cheaper here because `N` is smaller under M2 |
| C-5 | Position and opacity must not be shared — "sharing them results in **overlapping Gaussians**"; opacity is a scalar | excluded from VQ outright | ✅ **structurally important**: it means M3 cannot reach the two variables the baseline's `L_op` and `D-4` argument depend on |
| C-6 | Quantization hits a memory floor: after VQ, position + opacity are >80% of the budget | ℓ1 opacity reg → fewer Gaussians | ⚠️ **disabled here** (`04-loss.md` §4.3); M2 takes over the role |
| C-7 | Clustering in activated space distorts the metric | quantize `s` **before `exp`**, `q` **before normalization** | ✅ |

> **C-5 is quietly the best news in this section.** Because position and opacity are never
> quantized, M3 cannot corrupt `μ` (which produces `Ẑ`) or `o` (which `L_op` polices). The
> quantization mechanism is structurally isolated from both of the baseline's most fragile
> quantities. `[inferred: combining ../compact3d/05-constraints.md M-5 with
> ../seasplat/05-constraints.md D-2 and D-4]` It is the reason A3 and A5 are expected to be
> the best-behaved cells of the matrix.

---

## 5.3 Per-configuration risk register

For each cell: the specific degeneracy at risk, the mechanism that would normally prevent it,
whether that mechanism still applies, and — as the brief requires — **whether the evidence
shows the risk avoided, mitigated, or occurred.**

**Almost every "evidence" column below reads `NOT MEASURED`.** That is not an oversight in
this document; it was Phase 0's finding, and stating it once per row is the only honest way
to present a risk register built without results.

**One row has since been settled**, and is marked as such: the A4/A7 budget degeneracy is
now resolved by construction and confirmed by measurement. The rest await the campaign.
Rows will be updated in place as evidence arrives, so that the register reads as a live
document rather than a record of what was once unknown — the `[measured n=k]` tag from
`13-campaign-addendum.md` carries the sample size behind each.

| Cell | Risk | Baseline mechanism at stake | Still applies? | Mitigation adopted | Evidence |
|---|---|---|---|---|---|
| **A1** | `β` fitted to an un-refined depth map: with ADC off, `Ẑ` at `seathru_from_iter` reflects the triangulated init, not a densification-refined surface → **D-2** | M-5 (staged warm-up) | ⚠️ partially — the staging still runs, but the process it relies on is gone | re-derive `seathru_from_iter` for the dense-init regime, or justify keeping 10 000 `[PI]` | **NOT MEASURED** |
| **A1** | Matcher hallucination in the water column seeds floaters; matcher failure leaves holes nothing can fill → **D-4** and a new "permanent hole" mode | M-3 (`L_op`) kills floaters; nothing fills holes | ⚠️ half — `L_op` still fires; there is no hole remedy | consider `add_SfM_init = True` so COLMAP points survive as a fallback geometry source `[PI]` | **NOT MEASURED** |
| **A1** | Opacity over-suppression: EDGS's ×0.99 decay (Σ logit ≈ −15) + halved `opacity_lr` + `L_op` all push `α` down | M-3 (`L_op` at λ = 0.01, tuned without the decay) | ⚠️ the tuning is invalidated | re-tune `bg_lambda` or disable `reduce_opacity`; report which `[PI]` | **NOT MEASURED** |
| **A2** | **The scale discontinuity.** Pruning changes `Ẑ_min`/`Ẑ_max`, rescaling the medium model's only input mid-training → **D-2 arrives as an injected step change** | M-1/M-2/M-4 all defend D-2 against *optimization* exploiting it, none defends against an *externally injected* rescale | ❌ **no baseline mechanism covers this case** | **medium-only re-warm-up burst immediately after each simplification event** `[PI]`; log `Ẑ_min`, `Ẑ_max` and `β` across the event | **NOT MEASURED** |
| **A2** | Wrong importance metric: `outdoor`'s `I²` suppresses far-field primitives by design (built for sky); underwater far field is systematically low-contrast but *is* the scene | M-4 (global homogeneity assumes the medium explains far-field dimming, not that far-field geometry is disposable) | ⚠️ tension, not contradiction | choose and **justify** `imp_metric`; the medium-aware alternative (weight importance by `Â`) is identified but **not implemented** `[PI]` | **NOT MEASURED** |
| **A2** | Depth reinit resamples preferentially where `α_accum` is low — i.e. the water column — and fails where there is no depth, also the water column | M-3 (`L_op`) | ⚠️ | **scope M2 to simplification only**, leaving 3DGS ADC for densification `[PI]` | **NOT MEASURED** |
| **A3** | The medium parameters absorb codebook error, so `β` stops being interpretable as a medium estimate | M-4 (global homogeneity) is precisely what makes the absorption *global* and therefore harmful | ❌ M-4 is the vector, not the defence | log medium-parameter drift, quantized vs unquantized `[PI]` (`04-loss.md` §4.4) | **NOT MEASURED** |
| **A3** | Quantization damage concentrates in `Ĵ`, which is never scored; the metric multiplies the damage by `Â ≤ 1` before measuring it | none — this is a *measurement* gap, not a well-posedness gap | n/a | report a `Ĵ`-space self-consistency metric as **secondary**; declare the limitation `[PI]` | **NOT MEASURED** |
| **A4** | **Degenerate cell.** If M1's converged count already sits below M2's budget, IP2 is a no-op and **A4 ≡ A1** | n/a — a design failure, not a degeneracy | n/a | `n_bud` fixed **pre-campaign** below the smallest cloud, not from A0 — see the note below the table; preflight refuses any M1+M2 run where it would not bind, reading the count from the cloud's PLY header `[repo: utils/preflight.py]` | ✅ **RESOLVED.** All four clouds clear `n_bud = 200 000`: Panama 299 368, JapaneseGardens 334 931, Curasao 356 674, IUI3 471 531 `[measured n=1/scene]` |
| **A4** | ~~LR schedule conflict~~ — **DISSOLVED 2026-08-28.** M2's rewind is disabled by default, so only M1's clamp fires and there is no conflict to resolve | none | n/a | the rewind exists for *reinitialized* primitives; under CD-4 nothing is reinitialized (survivors keep parameters and Adam state), so its premise never holds `[PI — CD-7]` | **N/A — risk removed rather than mitigated** |
| **A4** | Four writers to `_opacity` in a single iteration (`L_op`, EDGS decay, EDGS prune, M2 reset-on-reinit) | M-3 (`L_op`) | ⚠️ | the same re-tuning as A1; **and** note M2 resets opacity *up* while M1 decays it *down* | **NOT MEASURED** |
| **A5** | The least-coupled pair — IP1 and IP3 never touch the same stage — but inherits A1's opacity issue and A3-a's ratio cap | — | ✅ mostly intact | none beyond A1's and A3's | **NOT MEASURED** |
| **A6** | `../OMG/`'s premise: "a smaller set of Gaussians becomes increasingly sensitive to lossy attribute compression" `[../OMG/00-index.md, paper Abstract]` → expect **sub-additive** quality | none in any source | n/a | this is the *hypothesis*, not a risk to mitigate — it is what A6 exists to test | **NOT MEASURED** |
| **A6** | Codebook fitted to a post-prune population that is 60–90% smaller: fewer vectors per centroid, higher quantization error at fixed `K_cb` | C-4 (assignment refresh) partly compensates | ⚠️ | `kmeans_st_iter > simp_iteration2` so the codebook is only ever fitted to the final population `[PI]` (`03-variables.md` IC-4) | **NOT MEASURED** |
| **A7** | Every risk above, simultaneously; plus both degeneracy risks (A4's no-op and A6's sub-additivity) | — | — | all of the above | **NOT MEASURED** |

---

## 5.4 One risk the register above understates: two incompatible notions of depth

This deserves its own section because it is the place where the composition could be made
*better* than either part, and because getting it wrong is silent.

SeaSplat's `Ẑ` is **alpha-normalised blended depth**: a second rasterization pass with
`override_color = z_cam`, divided by `α` `[../seasplat/02-pipeline.md Stage C]`.
Mini-Splatting's entire Appendix C is an argument that blended depth is **not identified**,
listing three named artifacts — depth collapse against the background, object misalignment
from floaters, and smoothing across occlusion boundaries — and quantifying the consequence:
reinitializing from blended depth gives **17.67 dB** where mid-point depth gives **27.54 dB**
`[../mini-splatting/05-constraints.md D-3, paper Tab. 4]`.

Two of those three artifacts are *precisely* the underwater failure modes SeaSplat exists to
fix. "Depth collapse: dark background objects are explained by the background, so accumulated
opacity along the ray stays low and the blended depth collapses toward the near plane" — that
is a description of a heavily-attenuated far field. "Object misalignment: large Gaussians and
floaters carry non-trivial weight, corrupting the weighted mean" — that is D-4.

**So the baseline feeds its physical medium model a depth quantity that a sibling method
demonstrates to be unreliable in exactly this regime**, and M2's forked rasterizer already
computes the better-posed alternative (`out_pts`, the ray/ellipsoid mid-point of the argmax
Gaussian) as a by-product `[../mini-splatting/03-variables.md §3.2]`.

`[PI]` **This is deliberately left as an identified opportunity, not adopted.** Substituting
mid-point depth for `Z_raw/α` would change what `β` is fitted to in *every* cell including
A0, so A0 would no longer be SeaSplat-as-published and the whole matrix would lose its
reference point. It is recorded here, in `open-questions.md`, and in the narrative chapter's
limitations section as the most promising single follow-up — and it is worth noting that it
is a finding the composition *produced*: neither paper alone states it, because neither has
both a physical depth-driven medium model and a mid-point depth estimator in the same system.

---

## 5.5 What is *not* resolved, in the combined method

Carried forward from the baseline and still true:

- **Absolute scale.** COLMAP fixes scene scale only up to a global factor, and `Ẑ` is
  additionally min–max renormalised per frame. The learned `β` are in units of normalised
  per-frame depth, **not inverse metres**, and are not physically comparable to published
  attenuation coefficients `[../seasplat/05-constraints.md §5.3]`. Nothing in this work
  changes that; M2 makes it worse (§5.3, A2).
- **Spatially varying media, caustics, shadows, dynamic objects** — conceded out of scope by
  the baseline `[seasplat paper §VI]`.
- **D-1 is only penalised, never excluded.** If `L_bs` were disabled, nothing prevents
  collapse to vanilla 3DGS — and the flag cannot be turned off from the CLI without editing
  the source `[../seasplat/05-constraints.md §5.3]`.

New, and specific to the combination:

- ~~**No mechanism guarantees the budget binds.**~~ **RESOLVED.** Preflight reads the point
  count from the M1 cloud's PLY header and refuses any run combining M1 and M2 where
  `n_bud` is not below it, naming the collapse it would have produced; within 10% it warns
  instead, since a budget that binds by a few per cent measures the interaction over almost
  no lever `[repo: utils/preflight.py]`. It has already rejected one wrong value before a
  run consumed it.
- **No mechanism validates that the medium re-warm-up actually re-identifies `β`.** The
  `[PI]` burst is specified by analogy with SeaSplat's existing warm-up; whether `n` steps
  suffice after a prune is unknown and untested.
- **The composition has no recovery mechanism for missing geometry.** Under A1 (no
  densification) and A2 (only removal), primitives can only ever decrease after
  initialization. In a domain where the initializer's matcher is known to fail on the water
  column, that is a one-way ratchet.

---

## 5.6 A degeneracy class this file did not anticipate: gradient destination

Everything above — D-1 through D-4, M-1 through M-5, the whole register in §5.3 — is a
statement about **values**. What solutions the objective admits; what a variable is allowed
to be; which term penalises which collapse. That framing was inherited from the baseline's
own well-posedness argument and it is the right one for the questions it was built to
answer.

It does not cover the defect that execution actually produced, and the gap is worth naming
because it is structural rather than incidental.

**The observation.** With all three mechanisms disabled, the implementation converged to
743 457 primitives where unmodified SeaSplat reaches 4 462 668 on the same scene — a sixth
— at a fidelity cost of about a tenth of a decibel `[measured n=1]`. Nothing in §5.1–§5.5
predicts or detects this. No degeneracy was entered: the objective, its terms, its
gradients and every rendered value were correct.

**The mechanism.** 3DGS's density control reads `‖∂L/∂means2D‖`, accumulated over an
interval. Each rasterization call owns one such buffer, so *whichever losses backpropagate
through a given pass, their gradients land in that pass's buffer and nowhere else.*
SeaSplat obtains `α` from the colour pass, so every `α`-derived term contributes. CD-13
substituted a rasterizer that cannot emit `α`, recovering it from a probe holding its own
buffer. `α`'s **value** was exact throughout; its **gradient** was absent from the signal
that decides how the model grows.

**Why nothing caught it.** The acceptance suite tests what the renderer returns — `α` in
range, compositing correctly, `Z_raw/α` recovering depth to seven decimal places. All
correct, on both architectures, throughout. A value-level check cannot observe a
gradient's destination, and every check in this methodology was a value-level check.

**The generalisation.** A composed method has, at every seam, a set of properties that
belong to *neither* component and appear in *neither* component's documentation. §5.4
identified one analytically — two incompatible notions of depth. This one was found only
by running the baseline configuration and noticing it did not reproduce the baseline. The
class is: **an integration boundary can preserve every value and still change which
gradients flow where.** That admits no purely analytical audit, because the property is
not local to either side of the seam.

**What now guards it** `[repo: tools/verify_rasterizer.py]`:

| | asserts |
|---|---|
| **T7** | `α`'s gradient reaches the shared buffer when passed, and does **not** when it is not — both directions, so removing the fix fails a test rather than silently changing a result |
| **T8** | the alpha-only probe's `α` matches the combined probe's to 1e-6, and its depth channel is identically zero |

And the invariant they encode, stated once so it can be checked against any future change to
the render path:

> **Density control must see the image and `α`, and must not see depth.**

Both halves are load-bearing. Omitting `α` gives 743 457 primitives; admitting depth as
well gives 635 038 — *worse*, because the two gradients partially cancel. Satisfying both
reproduces the baseline within its run-to-run spread `[measured n=3 — see
13-campaign-addendum §13.2–§13.3]`.
