# 13 — Campaign addendum: what execution changed

**Status of this file.** Sections 01–12 were written as a *synthesis pass* over the
nine reference-method breakdowns, before any code was executed. This file records
what changed once the method was implemented and run. Where the two disagree,
**this file supersedes**, and each item names the section it revises.

## Evidence tags

The reference breakdowns used `[paper]` / `[repo: file:line]` / `[unverified]`. Our
own method adds one, because most of what follows was not read anywhere — it was
observed:

| Tag | Meaning |
|---|---|
| `[repo: path:line]` | confirmed in our source |
| `[measured: n=k]` | observed by running it, with the number of runs behind it |
| `[pending]` | designed and implemented, not yet measured |

`[measured: n=1]` is deliberately distinguished from `[measured: n=3]`. §13.6
explains why that distinction turned out to matter more than any other item here.

---

## 13.1 Environment — the campaign stack differs from the development stack

*Revises §08 and §10.*

| | Development (Windows) | **Campaign (Colab A100)** |
|---|---|---|
| GPU | RTX 3050 Ti, sm_86 | **A100-SXM4-40GB, sm_80** |
| Python | 3.11 | **3.13** |
| torch | 2.6.0+cu124 | **2.11.0+cu128** |

Three torch minors and a CUDA minor apart. It builds and passes, but that is a
measured fact rather than a designed one, and it is why `verify_rasterizer` runs
at the start of every session rather than being trusted once.

Two in-tree build fixes were needed for the newer toolkit `[repo:
mini-splatting/submodules/simple-knn/simple_knn.cu, tools/setup_colab.sh]`:
`simple_knn.cu` uses `FLT_MAX` without including `<float.h>` (CUDA ≤11.x supplied
it transitively; 12.x does not), and `open3d` — present in SeaSplat's
`requirements.txt`, imported by nothing we run — has no wheel for Python 3.13 and
aborted the whole build script under `set -e`.

`fused-local-corr`, RoMa's optional fused correlation kernel, is **unavailable on
this stack**: its published wheel links against `libcudart.so.13` while the runtime
is 12.8. All four dense clouds were therefore built on the pure-torch correlation
path — the reference implementation the kernel optimises, not a different
computation. Recorded per cloud as `fused_local_corr: false` with the reason, since
preprocessing wall-clock is reported alongside A1's training cost.

---

## 13.2 CD-22 and CD-23 — the densification signal's gradient composition

*Revises §05 (constraints and well-posedness) and §06 (implementation deltas).
This is the most consequential finding of the execution phase.*

### The defect

3DGS decides what to clone or split from `‖∂L/∂means2D‖`, accumulated by
`add_densification_stats` and thresholded at `densify_grad_threshold`. Each
rasterization call owns one `means2D` tensor, so **whichever losses backpropagate
through a given pass, their gradients land in that pass's buffer.**

Upstream SeaSplat obtains `alpha` from the **colour pass** — dxyang's fork emits it
natively — so alpha-derived losses reach the buffer density control reads
`[repo: baseline train.py:201]`. CD-13 substituted Mini-Splatting's
`diff_gaussian_rasterization_ms`, which cannot emit alpha, and recovered it from a
probe pass holding its own buffer. Alpha's *value* was exact throughout; its
*gradient* was silently absent from the densification signal.

| Densification buffer receives | Converged primitives |
|---|---:|
| image only (as merged, pre-CD-22) | 743,457 `[measured: n=1]` |
| image + alpha **+ depth** (CD-22) | 635,038 `[measured: n=1]` |
| image + alpha (upstream) | 4,462,668 `[measured: n=1]` |

CD-22 shared the buffer and made it **worse**, which is what identified depth as
the cancelling term: our probe emits depth and alpha from one rasterization, so
sharing admits a gradient upstream never has there.

### The fix

**CD-23** gives alpha its own probe, colour `[0,1,0]` `[repo:
gaussian_renderer/__init__.py render_alpha]`. Channel 1 still accumulates
`1 − Π(1−aᵢ)`, so `L_op` sees exactly what it did; channel 0 carries no depth, so
only alpha reaches the shared buffer. Depth keeps its own pass.

**Cost: three rasterizations per iteration instead of two.** That lands in the
wall-clock this study reports as an efficiency result, so it sits behind
`separate_alpha_probe` and is recorded in every manifest rather than compiled in
`[repo: arguments/__init__.py]`.

### Why no acceptance check caught it

`verify_rasterizer` T0–T6 all passed, on both architectures, throughout. Every one
inspects a **returned tensor**, and alpha was numerically correct in both versions.
What was wrong was where its gradient went. Two checks now cover that
`[repo: tools/verify_rasterizer.py]`:

- **T7** — asserts the gradient's *destination* in both directions: non-zero with a
  shared buffer, untouched without one, so the check fails again if the sharing is
  ever dropped.
- **T8** — asserts the alpha-only probe matches the combined probe's alpha to 1e-6
  *and* that its depth channel is identically zero.

**The generalisable lesson for §05:** well-posedness arguments in this codebase have
been about *values* — degeneracies D-1 to D-4 are all statements about what the
objective admits. This defect was a statement about **where a gradient flows**, and
no value-level check could see it. That is a category of failure §05 did not
anticipate.

---

## 13.3 A0 ≡ SeaSplat, verified

*Revises §12 (novelty defensibility), which assumed a faithful baseline rather than
establishing one.*

The thesis claims "we improve SeaSplat", which makes the baseline load-bearing: a
claim about a difference is only as good as its reference point. A0 with the defect
distorted **in both directions at once** — per-mechanism effects understated
(reducing 635k by 40% is less than reducing 4.4M by 40%), end-to-end claims
overstated (a reader comparing the final model against SeaSplat's published size
would attribute a 10× gap to M1/M2/M3).

`tools/replicate_baseline.py`, Curasao, 16,000 iterations, 3 runs each:

| | runs | mean | sd | spread |
|---|---|---:|---:|---:|
| ours (A0) | 4,260,571 / 3,990,523 / 4,906,223 | 4,385,772 | 470,514 | 20.9% |
| vanilla SeaSplat | 4,290,897 / 3,749,643 / 4,661,489 | 4,234,010 | 458,577 | 21.5% |

Mean ratio **1.036**, ranges fully overlapping → **indistinguishable**
`[measured: n=3]`.

Supporting evidence that the implementations agree beyond the count: identical
initial primitive count (25,837 both), and medium parameters converging to the same
solution — B∞ within 3%, β_att ordered R > G > B on both sides, which is physically
correct for water and rules out the D-1 no-medium degeneracy in either.

---

## 13.4 Mechanism D — a fourth mechanism, deliberately outside the factorial

*Extends §01 and §12.*

The alpha-detached configuration is not merely a bug that was fixed. Measured
against vanilla it gave **6× fewer primitives for −0.107 dB** test PSNR
(30.268 vs 30.375, per-channel) `[measured: n=1]` — larger than M1, M2 or M3 is
likely to deliver, and free, since detaching removes the third rasterization rather
than adding one.

It is therefore promoted to a **named, flagged mechanism**
(`detach_alpha_gradient`) and measured as cell **`A0D`**, stage **S6**, 12 runs
`[repo: configs/cells.json, tools/run_ledger.py]`.

**It is not a fourth factor, and a 2⁴ design would be wrong.** M1 replaces
`densify_and_prune` with `prune_only`, so densification never runs under M1 — and D
modifies only the densification signal. D is therefore **provably inert in all eight
M1 cells**: half a 16-cell cube would be exact duplicates, 96 extra runs measuring
nothing. `A0D` is read against A0 alone and must never be differenced with the
factorial cells; `cells.json` says so in the cell's own description, because that is
where someone will look.

The `[measured: n=1]` tag is doing real work here. That figure came from comparing a
*defective* A0 against vanilla, with the pre/post runs at different seeds. As a
deliberate ablation against the corrected baseline it is `[pending]`.

---

## 13.5 `n_bud` — from a rule, before the campaign, not from A0 after it

*Revises §03 (variables) and §05.*

§03 specified the budget as "derived from A0's converged count". That is now
**wrong twice**: it makes the number unknowable before S1, and at A0's measured
~4.4M the 60% rule gives ~2.6M — above every dense cloud.

> **The binding rule.** `n_bud` must lie below the smallest primitive count any
> other enabled mechanism produces.

A precondition for measuring M2 in combination, not a tuning choice. Under M1 the
count is fixed by the cloud and can never grow, so a budget above it is **provably
inert before a single iteration**: A4 would be an exact duplicate of A1, A7 of A5,
and the interaction those cells exist to measure would read as a null result rather
than as a missing experiment.

Measured clouds, `dense` preset, 20,000 matches per reference view
`[measured: n=1 per scene]`:

| scene | reference views | points kept | M2 removes |
|---|---:|---:|---:|
| **Panama** | 15 | **299,368** | **33%** — the binding scene |
| JapaneseGradens-RedSea | 17 | 334,931 | 40% |
| Curasao | 18 | 356,674 | 44% |
| IUI3-RedSea | 25 | 471,531 | 58% |

**`n_bud` = 200,000** — 67% of the binding cloud, 22× reduction from A0.

The count is `num_refs × matches_per_ref`; `nns_per_ref` selects *which* neighbours
each reference is matched against and does not multiply it. An earlier value of
400,000 came from treating it as a multiplier, was 3× high, and exceeded three of
four clouds. Preflight refuses any M1+M2 run whose budget does not bind — it reads
the vertex count straight from the PLY header — and the error surfaced before a
single training run consumed it `[repo: utils/preflight.py]`.

---

## 13.6 Run-to-run variance, and what it invalidates

*Revises §10 (reproducibility), which stated the policy but not the magnitude.*

§10 already said bit-exact reproduction is unattainable and dispersion must be
reported. The magnitude was unknown, and it dominates several contrasts:

**`n_primitives` carries ~21% run-to-run spread on both implementations**
`[measured: n=3 each]` — 20.9% ours, 21.5% vanilla, despite our seeding both the
CPU and CUDA generators and vanilla seeding neither.

The mechanism is amplification. The rasterizer backward accumulates atomically, so
a primitive lands either side of `densify_grad_threshold` from run to run; that
changes the population feeding the next densification event, 144 times over. The
same compounding that turned a 2% per-event rate difference into a 6× gap operates
on floating-point noise.

**The methodological consequence, stated plainly because it cost real effort.** The
CD-22/CD-23 investigation tested four hypotheses, three of them against *single-run
ratios* of this quantity. A paired run showed 0.68× for two implementations later
shown indistinguishable at n=3. Three of the four hypotheses were wrong. **A
single-run ratio on primitive count carries no information at this scale**, and the
per-event comparison tool now requires a difference to exceed a 20% floor and
persist across three consecutive events before calling it a divergence
`[repo: tools/compare_densification.py]`.

For the results: any contrast reported on primitive count must clear this
dispersion. Main effects should — M2 targets 22×. **The two-way interactions may
not**, and `analyse.py` reports `UNDETERMINED` rather than a confident number when
they do not. That is the tooling being honest, and it should be read as a finding
about resolution rather than a defect.

---

## 13.7 Design shape as executed

*Revises §05 of `docs/ablation_design.md` and §1 of `docs/experiment_plan.md`.*

| | |
|---|---|
| Factorial | 8 cells, 2³ over M1/M2/M3 — **unchanged** |
| Supplementary | `A0D` (mechanism D), stage S6 — **new** |
| Reference control | `SS`, vanilla SeaSplat, 4 runs, one per scene — **new** |
| Total | **108 factorial+supplementary runs**, plus 4 SS, plus verification |
| `n_bud` | 200,000, fixed pre-campaign |
| Dense-cloud preset | `dense`, not `sparse` |

**Storage policy** `[repo: train.py, arguments/__init__.py]`. At ~4.4M primitives a
run would write ~300 MB of PLY and ~1 GB of Adam checkpoint — over 100 GB across the
campaign, against a Drive that holds 15. Checkpoints are off (CD-18 restarts rather
than resumes, so they support a path deliberately never taken); PLYs are written for
seed 0 only (figures are illustrative, and `analyse.py` reads `model_size.json` from
`compressed_*/` instead). The medium-model tensors are kept unconditionally — β_att,
β_bs and B∞ are the physically interpretable output of the whole method, and they
are kilobytes. Campaign storage: **~35 GB**.

---

## 13.8 Still pending

Nothing here is claimed. Listed so the gap between design and evidence stays visible:

- **S1–S5, the factorial itself.** In flight at the time of writing.
- **Mechanism D against the corrected baseline.** Its headline figure is `n=1`
  against a defective A0.
- **The SS control**, 4 runs.
- **Every fidelity and cost result.** §08's computational profile still carries the
  *reference methods'* reported numbers, not ours.
- **A 4.6% accounting gap.** In one pre-fix run `diagnostics.csv` reported 743,457
  primitives at iteration 30000 where the 48.2 MB PLY implies ~709k and the 39 MB
  compressed artifact ~696k. The two artifacts agree with each other and disagree
  with the log. Unexplained; it should be resolved before any model-size figure is
  quoted.

---

## 13.9 What §12's novelty argument should now say

§12 concluded: claim (c) — a well-posedness/integration fix — supported by (a) prior
art gap; claim (b), a measured non-additive interaction, **unavailable** because no
measurements existed.

Two updates.

**Claim (c) is now stronger and differently grounded.** §12 argued from the medium
model's non-invariance to primitive-count reduction. CD-22/CD-23 add a second,
independently discovered instance of the same theme: substituting a rasterizer
preserved every forward value and silently changed the *densification signal*. Both
are cases of an integration boundary carrying a property no component's own
documentation mentions.

**Mechanism D is a candidate claim (a) in its own right** — a prior-art gap, not an
integration fix. Nothing in the SeaSplat, Mini-Splatting, CompGS-VQ or EDGS
literature reports that alpha-loss gradients inflate 3DGS densification, and the
preliminary figure is 6× for a tenth of a decibel. It is `[measured: n=1]` against a
defective baseline. It is not claimable until `A0D` runs, and it should not appear in
any draft before then.

**Claim (b) remains unavailable** until S4 completes — and §13.6 is a warning that
it may remain unavailable afterwards, if the interaction effects do not clear the
21% dispersion.

---

## 13.10 First direct evidence on H4: simplification collapses the attenuation model

*Extends §5.1's degeneracy D-1 and §5.4. First measurement bearing on the thesis's central
hypothesis. `[measured n=1]` — one scene, one seed; see the caveats before using it.*

### The observation that prompted it

Loading the trained models into a splat viewer, A2/IUI3-RedSea showed a **reddish seabed**
where A0 and the prior work's models were neutral, together with visibly fewer water-column
floaters and a tighter bounding box.

A viewer displays the `.ply`'s `f_dc`, which is **Ĵ — the medium-free radiance**, not the
composed image. A colour cast there is a statement about the medium model, and it turned out
to be diagnostic.

### What the diagnostics show

A2/IUI3-RedSea/s0, across the first simplification (`simp_iteration1 = 15000`):

| | iteration 15000 (pre-simp) | 15001 (post-simp, **after** the CD-6 burst) |
|---|---|---|
| primitives | 2 437 342 | 200 000 — **−92%** |
| `z_min` / `z_max` | 7.27 / 40.08 | 8.27 / 37.92 |
| **β_att** (R/G/B) | 0.525 / 0.609 / 0.674 | 0.061 / 0.089 / **−0.046** |

β_att,B crosses zero **at the simplification step itself**. β_att,G follows at iteration
19500. Neither ever recovers. **A0 never goes negative in any channel**, and its β_att
trajectory across the same range is smooth (1.10 → 1.15 → 1.19 → 1.21).

### Why recovery is impossible

`deepseecolor/models.py:83` clamps the *product*, not the parameter:

```python
beta_d_conv = torch.clamp(conv2d(depth, self.residual_conv_params), 0.0)
```

β_att is unconstrained; depth is non-negative. Once β_att < 0 the product clamps to zero,
`d(clamp)/dβ = 0`, and the channel is **frozen for the remainder of training with no path
back**. Confirmed empirically: after going negative, β_att,G takes exactly **one** distinct
value across every subsequent logged iteration, and β_att,B likewise.

`exp(−0) = 1` means no attenuation is modelled for those channels — **SeaSplat's own D-1
"no medium" degeneracy, reached one channel at a time.** D-1 was described in §5.1 as a global
optimum that the staged warm-up and `L_bs` defend against. Neither defence addresses a
channel-wise entry through a clamp boundary, because neither anticipated the parameter being
driven there by an external population change.

This is an inherited SeaSplat design flaw — a one-way trap — that only becomes reachable under
an intervention SeaSplat does not have.

### Why the seabed is red

Ĵ = (Î − B̂) / Â, so a channel's restoration is `exp(+β_att,c · Ẑ)`. With β_att,G ≈ β_att,B ≈ 0
(clamped) and β_att,R surviving at 0.1–0.44, **only red is restored**. A0's three channels sit
near 1.0–1.15 and restore together, which is why it looks neutral.

The visual signature and the parameter collapse are the same fact.

### What is *not* attributable to M2

**Backscatter runaway occurs in the baseline too.** β_bs reaches 15.8 in A2 and **13.6 in A0**,
large enough in both that `exp(−β_bs Ẑ)` ≈ 0 and the backscatter term saturates to a constant
`σ(B^∞)`. An earlier reading of this data attributed the runaway to simplification; that was
wrong. It is a property of the baseline, and it is a separate finding worth reporting on its
own — SeaSplat's backscatter coefficients are not identified either, they simply saturate.

What is M2-specific is the **attenuation** collapse.

### Why no fidelity metric would have caught it

PSNR, SSIM and LPIPS score **Î**, the composed image. A model with Â ≈ 1 and a saturated,
constant B̂ can still fit Î — it has become plain 3DGS plus a global colour offset. The physics
is gone; the photometry is intact.

This is the concrete case for the standing instruction that physical correctness must not be
inferred from fidelity metrics, and it is the strongest available answer to the reviewers who
asked *why* the mechanisms behave differently under underwater conditions.

### Consequences for the design

**H4 is supported, and the effect is more severe than the hypothesis stated.** §5.4 predicted
that primitive reduction would *perturb* medium identifiability through the Ẑ rescale. The
measured Ẑ change is modest — `z_min` +14%, `z_max` −5% — while β_att falls by 94% in one
step. The rescale alone does not account for it; removing 92% of the population appears to
remove the structure the medium term was explaining, and the optimiser answers by switching
the medium off.

**CD-6 is insufficient as configured.** The 15001 row is the state *after* the 200-step
re-identification burst. The burst ran and β_att was already collapsed when it finished. The
remedy this work proposes does not, at 200 steps, do what it was designed to do — and this is
the first evidence either way, because the burst has been unconditionally enabled.

**The budget may be the operative variable, not M2.** `n_bud = 200 000` removes 92% here.
Whether the collapse is a property of simplification or of *this budget* cannot be separated
from a single operating point. This converts the rate–distortion sweep from a reviewer request
into a scientific necessity `[new-revisited-writing/01-discrepancy-ledger.md D-9]`.

### Caveats

- **n = 1.** One scene, one seed.
- **A0 and A2 already differed before the intervention** — β_att ≈ 1.10 vs 0.54 at iteration
  12500, a factor of two with M2 not yet active. Given the 6–29% run-to-run dispersion
  (§13.6) this needs seeds before the pre-existing gap means anything. The *step change* at
  15001 is coincident with the intervention and is not noise.
- The reddish cast is a **gauge-visible** quantity. §5.1's D-3 says Ĵ has an unconstrained
  per-channel gain under the photometric loss alone, so a colour shift is not by itself
  evidence of anything. It is evidence *here* because the parameter trace shows the mechanism.

`tools/medium_collapse.py` scans every run for negative-and-frozen attenuation channels and
saturated backscatter, so this is detected across the campaign rather than found by eye.


---

## 13.11 A1's population collapse: a cull run against the wrong objective

*Revises §05 (the A1 risk register) and §06 (R-5). `[measured n=1 trajectory, n=12 outcome]`*

### What happened

All twelve A1 runs produced test images of 4–5 KB — essentially solid colour — and
`train.log` repeatedly printed `[training] everything is nan`. That message is upstream
SeaSplat's `[repo: seasplat/train.py:227]` and fires when `Z_raw / alpha` is non-finite at
**every** pixel, which happens only when alpha is zero everywhere. It does not indicate
numerical instability. It indicates an empty frame.

A1/IUI3-RedSea/s0:

| phase | window | primitives | |
|---|---|---:|---|
| dense-cloud init | 0 | 471 531 | |
| EDGS decay + `prune_only`, **medium off** | 1 – 10 000 | 6 291 | −98.7% |
| `L_op` + `prune_only`, **medium on** | 10 000 – 15 000 | 74 | −98.8% of survivors |
| frozen (`prune_only` gated by `densify_until_iter`) | 15 000 – 30 000 | 74 | |

**74 primitives represented the scene for the final half of training.**

### The mechanism

EDGS's decay-and-cull removes "Gaussians the photometric loss does not defend"
`[../EDGS/02-pipeline.md]`. That is sound **when the loss is a complete statement of the
objective**. Under SeaSplat it is not.

Before `seathru_from_iter` there is no medium term, so veiling haze must be explained by
geometry — and the photometric optimum for a hazy image is a handful of large blobs, which is
SeaSplat's own degeneracy **D-4**. The original gate stopped the decay *at*
`seathru_from_iter`, on the reasoning that stacking with `L_op` risked over-pruning. That gate
confined the entire cull to the window where the objective was missing the medium model, so
the cull decided what was "needed" against half a model. With densification disabled, nothing
restored any of it.

The two forces never stacked; **they relayed.** The decay emptied the cloud before iteration
10 000, and `L_op` took over at exactly the point the decay stopped.

### What was corrected, and what was not

`m1_decay_stops_at_seathru` is replaced by **`m1_decay_after_seathru`** (default `True`): the
decay now runs in `[seathru_from_iter, densify_until_iter)`. An undefended primitive reaches
the prune floor at iteration ~10 690 instead of ~3 090 — after the medium model is live rather
than 7 000 iterations before it.

`verify_dense_init.py` **T7** encodes the invariant, and it is deliberately framed as a
scheduling property rather than as a parameter value: *an undefended primitive must not reach
the prune floor before `seathru_from_iter`.* It fails against the old configuration and passes
against the new one.

**A wrong first diagnosis, recorded because it shaped the fix.** The periodic opacity reset —
retained under CD-3, and disabled outright by EDGS, which sets `opacity_reset_interval` to the
iteration count — looked like the cause: `reset_opacity()` is `min(opacity, 0.01)`, a cap, and
it leaves every primitive only 690 iterations above the prune floor. The schedule test refuted
it. By iteration 3 000 the decay has already carried an undefended primitive *below* the cap,
so `min` changes nothing and the cull happens at 3 090 either way. The reset remains a
fidelity deviation from EDGS worth revisiting; it is **not** what emptied A1.

### The gap this exposed independent of the cause

**All twelve runs completed, were marked `done`, and produced an `eval_metrics.json`.** No
assertion checked that a model still rendered anything. A cell could fail this completely and
be indistinguishable from a result in the ledger.

`cost.population_collapsed` is now written into every run's metrics, with a loud terminal
banner, against `min_primitives_floor = 1000` `[repo: train.py, arguments/__init__.py]`.

### Consequences

- **The twelve A1 runs are invalidated** and re-queued.
- **A4, A5 and A7 are affected** — every M1 cell — but had not run.
- §5.5's standing warning that "primitives can only ever decrease after initialization … a
  one-way ratchet" is upgraded from a risk to a **measured failure**, with the specific
  mechanism identified.
