# §1 — Taxonomic placement and contribution statement

**Method:** *An Efficient 3D Gaussian Splatting for Underwater 3D Reconstruction*
**Date of synthesis:** 2026-08-26

Evidence tags used throughout this chapter:
`[paper]` source-method publication · `[recommended]` design plan/spec or draft thesis Ch. 3 ·
`[implemented]` shipped branch code · `[measured]` Colab Pro run outputs ·
`[unverified]` · `[inferred]`

---

## 1.1 Placement in one sentence

This method extends **SeaSplat** — an explicit, per-scene-optimized 3D Gaussian radiance field
carrying a physically grounded revised Akkaynak–Treibitz underwater image formation model as a
fixed constraint — with three representation-level efficiency mechanisms drawn from the
terrestrial 3DGS efficiency literature (**EDGS** for densification-free dense initialization,
**Mini-Splatting**-family primitive-count reduction, and **CompGS/Compact3D** vector
quantization), applied so that they touch only the structure and parameterization of the
Gaussian primitives and never the medium model itself.

The governing design principle is stated in the draft thesis and is verified to hold in code:

> "A central design principle of the proposed method is the separation between physical
> modeling and efficiency intervention. The underwater image formation model is treated as a
> fixed constraint throughout optimization, while efficiency mechanisms are applied only to the
> structure and attributes of the Gaussian representation." `[recommended: draft §3.5.1]`

**This separation is verified, not merely asserted** — see §5. It is a property of SeaSplat's
*global* 9-scalar medium parameterization (`β^D`, `β^B`, `B^∞` ∈ ℝ³ each), held in separate
`nn.Module`s under their own optimizers. No mechanism below can reach them.

---

## 1.2 What each component adapts — not merely applies

The word is *adapts*: in each case something had to change for the mechanism to be well-posed
under SeaSplat's constraints, and in each case the change is traceable.

### Component 1 (A1) — Deterministic initialization ← EDGS

EDGS eliminates densification and seeds from RoMa correspondences. The adaptation to SeaSplat
is a **re-implementation in pixel space rather than a port**: EDGS's `triangulate_points`
operates in 3DGS-specific 4×4 NDC space using `viewpoint_cam.full_proj_transform` with
keypoints in normalized [−1,1] device coordinates, whereas SeaSplat's scene loader exposes
COLMAP `K·[R|t]` in pixel space. Adapting EDGS's primitive would have required constructing a
3DGS-style projection transform from COLMAP intrinsics at every call
`[recommended: design spec §3.1]`. A vectorless pixel-space DLT was written instead.

Correspondence density was also rescaled: EDGS selects ~180 reference views by k-means over
camera poses; the SeaThru-NeRF scenes have only **15–25 training views**, so all training views
are used as references `[recommended: design spec §5]`.

**What was not adapted, and should have been.** EDGS's densification-free regime is survivable
because three counterweights remain active — an `α < 0.005` prune outside the densify gate, a
continuous `×0.99` opacity decay (`reduce_opacity`), and a position-LR clamp (`max_lr`)
`[paper: EDGS repo trainer.py:146-147, 258-264]`. In SeaSplat, `densify_and_prune` and
`reset_opacity` both live *inside* the block gated by `--no_densify`
`[implemented: train.py:517-547]`, so disabling densification also disables opacity hygiene
entirely, and no replacement was supplied. §1.3 argues this is where the thesis's most
defensible contribution actually lies.

### Component 2 (A2) — Spatial reorganization ← Mini-Splatting family

Mini-Splatting's importance is an **accumulated blending weight** integrated over training
views, consumed by *stochastic* importance-weighted sampling `[paper: mini-splatting §3.2,
§4.2]`. The implemented mechanism instead scores `opacity × max(scale)` and takes a
deterministic bottom-`n` cut to a fixed budget `[implemented: scene/gaussian_model.py]`.

That substitution is a genuine loss of fidelity to the source (§6), but the adaptation that
matters is different and is **specific to SeaSplat**: `self.get_opacity` is read *after*
SeaSplat's opacity prior `L_op` (λ = 0.01) has driven `α → 0` for Gaussians whose rendered
contribution is backscatter-only. The score therefore ranks medium-suppressed primitives
lowest and removes them first. Mini-Splatting has no such term because it has no medium model.

### Component 3 (A3) — Attribute-level quantization ← CompGS / Compact3D

CompGS's contribution is **quantization-aware training** with a straight-through estimator, so
parameters adapt to the centroids they will be snapped to `[paper: compact3d §3]`. The
adaptation here is a deliberate inversion: quantization is applied **post-training**, with a
stated SeaSplat-specific justification —

> "This choice preserves the stability of the joint optimization of geometric and
> medium-related parameters during training, and avoids introducing quantization-induced
> gradient perturbations into the SeaThru parameter estimation." `[recommended: draft §3.5.4]`

That is a defensible reason CompGS never had to weigh, and the measured outcome supports it
(mean ΔPSNR = **−0.075 dB** at **4.28×** bits-per-primitive reduction, §8). The forfeited
error-recovery path is the cost, and it is stated as such in §4 and §5.

CompGS additionally excludes **position and opacity** from quantization `[paper: compact3d §3]`.
This implementation preserves the position exclusion but **quantizes opacity**
`[implemented: source/quantize.py]` — a deviation the draft thesis does not mention (§6).

---

## 1.3 The novelty claim

**What this is not.** It is not a new algorithm, and it is not "three known tricks combined."
The combined configurations were specified and implemented but **never run**: the completed
experiments are A0, A1, A1v2, A2, A3 only `[measured: master_metrics.csv]`, and the draft
thesis states this plainly — "Only A0, A1, A1v2, A2, and A3 were completed … Combined
mechanisms are not empirically validated" `[recommended: draft Table 4.13]`. Any claim resting
on A4–A7 is currently a projection (§8).

**What it is.** Three findings, in descending order of how well they are supported.

**(a) A medium-aware pruning criterion, discovered rather than designed — and empirically
strong.** Because `opacity × scale` reads post-`L_op` opacity, A2 removes precisely the
population SeaSplat's underwater model has already declared invisible. The measured result is
the best in the study: at a hard 800 000-primitive cap on all four scenes, mean ΔPSNR is
**−0.05 dB** (JapaneseGardens and IUI3 *improve*), with **1.10–1.33×** faster training,
**1.32–2.06×** faster rendering, and **2.3–5.6×** smaller models `[measured]`. The draft
thesis already reaches this conclusion independently — §5.1.2 names spatial reorganization the
most balanced mechanism. **The contribution is the explanation**: this works because the
scoring function is coupled to the medium model through `L_op`, a coupling that does not exist
in the terrestrial source method. It should be claimed deliberately and tested directly
(§10), not left as an unremarked empirical win.

**(b) A diagnosed compactness–stability boundary, not merely an observed one.** A1 at
222 k–369 k primitives fails catastrophically on Panama (PSNR **14.29** vs baseline **29.22**,
**−14.93 dB**); A1v2 at 889 k–1.46 M recovers to 21.97 dB, still −7.26 dB `[measured]`. The
draft thesis reports this as a sensitivity boundary `[recommended: draft §4.3.2, §5.1.4]`.
The implementation audit supplies the **mechanism**: with `--no_densify` set, SeaSplat loses
densification, the `α < 0.005` prune, and `reset_opacity` simultaneously, while EDGS's
`reduce_opacity` and `max_lr` counterweights were never ported. The population is therefore
frozen at whatever the offline matcher produced, and `L_op` suppresses primitives that nothing
can remove. A scene whose turbidity starves the matcher of correspondences has no recovery
path at all. **Naming that mechanism converts a scene-dependent anomaly into a stated
limitation with a known fix** (§6, §8) — which is a stronger methodological result than the
sensitivity sweep alone.

**(c) A design flaw in the planned combinations, provable from the completed runs.** With
densification disabled the primitive count can never grow, and A2 is a no-op whenever the
population is under budget. A1's measured counts (222 k–369 k) are **all below the 800 000
budget** `[measured]`. Therefore, **as currently configured, A4 (A1+A2) would reproduce A1
exactly and A7 (A1+A2+A3) would reproduce A5 exactly** — two of the four planned combination
runs are degenerate before they are launched. A1v2's counts (889 k–1.46 M) are all *above*
budget, so pairing the combinations with the A1v2 density instead makes them non-degenerate.
This is actionable now and costs no GPU time to act on (§8, §10).

**Recommended contribution statement.** *This thesis provides an empirical characterization of
three representation-level efficiency mechanisms under a physically grounded underwater image
formation model, establishing that (i) the medium model remains structurally isolated from all
three interventions, (ii) budget-constrained primitive removal scored on post-medium opacity is
near-lossless at a 2.3–5.6× size reduction, (iii) post-training vector quantization is
near-lossless at 4.28× bits-per-primitive, and (iv) densification-free dense initialization
exhibits a scene-dependent stability boundary whose mechanism is identified as the loss of
opacity hygiene rather than insufficient initial density alone.*

---

## 1.4 Position relative to the source methods

| | This method | SeaSplat | EDGS | Mini-Splatting | CompGS/Compact3D |
|---|---|---|---|---|---|
| Medium model | ✅ inherited, fixed | ✅ 9 global scalars | ❌ | ❌ | ❌ |
| Dense init | ✅ A1 (adapted) | ❌ COLMAP SfM | ✅ origin | ❌ | ❌ |
| Count reduction | ✅ A2 (budget cap) | ❌ | ❌ | ✅ origin (stochastic) | ✅ ℓ1 opacity reg |
| Quantization | ✅ A3 (post-hoc) | ❌ | ❌ | RAHT (`ms_c`) | ✅ origin (QAT) |
| Densification | disabled under A1 | ✅ 500→15 000 | eliminated | ✅ modified | ✅ stock |
| Opacity reset | disabled under A1 | ✅ every 3 000 | replaced by decay | removed | ✅ retained |
| Loss changes | **none** | 7 terms | none | none | +ℓ1 opacity |

The row that matters is the last: **all three mechanisms are structural or offline; none adds
or modifies a loss term.** That is what makes the physical model's isolation checkable rather
than merely intended, and it is established in §4.
