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
