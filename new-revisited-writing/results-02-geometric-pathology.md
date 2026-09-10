# Results — geometric pathology in the baseline, and what simplification removes

**Status.** Seed 0 only, because the point cloud is written for one seed per cell. `[measured
n=1 per cell×scene]`. The effects are large and structural rather than marginal, but they are
single runs and are reported as such.

**Why this measurement exists.** Every fidelity measure in this study is photometric, and
SeaSplat's degeneracy **D-4** — opaque low-texture primitives placed near the camera to
reproduce veiling haze as geometry — is photometrically *excellent*. It is visible in the
geometry and nowhere else. Nothing else the campaign records would detect it.

The measurement was prompted by an observation in a splat viewer: the baseline's bounding box
is far larger than the simplified model's, and visibly mostly empty. The viewer's reported
dimensions match `full_extent_x/y/z` exactly, so the instrument measures what the observation
was about.

---

## 1. The baseline's bounding box is 96–99.96% empty

| scene | A0 occupancy | A2 occupancy | A2/A0 |
|---|---:|---:|---:|
| Curasao | **0.037%** | 1.899% | **51×** |
| IUI3-RedSea | 0.513% | 2.099% | 4.1× |
| Panama | 0.462% | 1.112% | 2.4× |
| **JapaneseGardens** | **3.696%** | 2.948% | **0.8×** |

Occupancy is the share of the axis-aligned bounding box containing any primitive, on a fixed
64³ grid. A low value means the box is held open by material occupying almost none of it.

**JapaneseGardens is the exception on every measure that follows**, and it is the control that
makes the rest interpretable.

---

## 2. Two distinct pathologies

The instructive result is that the three affected scenes do **not** share a mechanism.

### 2a. Detached rendered clusters — IUI3-RedSea and Panama

| | beyond 5× median radius | beyond 10× | gap between |
|---|---:|---:|---:|
| A0/IUI3-RedSea | 1.69% | 1.69% | **0.00%** |
| A0/Panama | 6.61% | 6.61% | **0.00%** |

**The zero gap is the finding.** A population sits beyond ten times the median radius, and
*nothing at all* lies between five and ten times it. A scene that is legitimately spread — a
reef wall receding into the distance — produces a smooth falloff. A bulk, then empty space,
then a separate cluster, is a **detached** population.

Opacity gating shows these clusters are **rendered**: dropping primitives below α = 0.05
changes occupancy by a factor of 0.9 and 0.8 respectively, so the material holding the box open
is material the rasteriser draws.

**This is degeneracy D-4, identified geometrically.** Panama — the most turbid scene, with the
strongest backscatter — carries the largest detached fraction at 6.61%, which is the direction
the degeneracy predicts: more veiling haze to explain, more geometry recruited to explain it.

**A2 removes them entirely.** 0.00% beyond 5× on both scenes.

### 2b. A diffuse invisible halo — Curasao

Curasao has **no** detached cluster: 0.00% of its primitives lie beyond five times the median
radius. Yet its box is the emptiest of all at 0.037%.

The gating separates the two cases immediately:

| | occupancy | visible-only occupancy | ratio |
|---|---:|---:|---:|
| **A0/Curasao** | 0.037% | **2.867%** | **77.5×** |
| A0/IUI3-RedSea | 0.513% | 0.463% | 0.9× |
| A0/Panama | 0.462% | 0.386% | 0.8× |
| A0/JapaneseGardens | 3.696% | 3.877% | 1.0× |

**Restricting to rendered primitives raises Curasao's occupancy 77-fold.** Its box is held
open by a thin, widely-spread population of near-invisible primitives — not by haze-geometry.
Curasao is also the scene with the fewest visible primitives overall (25.8%, against
32.9–43.6% elsewhere).

This is a different failure from D-4 and would be invisible to a metric that only counted
primitives or measured a bounding box without gating.

### 2c. JapaneseGardens — the baseline behaves

No tail (100% of primitives within twice the median radius), occupancy already at 3.7%, gating
ratio 1.0. Nothing is wrong with the geometry.

**And it is the one scene where A2's occupancy is *lower* than A0's (0.8×).** Where there is
no pathology, simplification has nothing to remove and slightly degrades the spatial
description instead. That is the control the other three scenes needed.

---

## 3. What simplification does, geometrically

| | beyond 5× r50 | gating ratio |
|---|---:|---:|
| A2/Curasao | 0.40% | 0.9× |
| A2/IUI3-RedSea | 0.00% | 0.9× |
| A2/JapaneseGardens | 0.00% | 1.0× |
| A2/Panama | 0.00% | 1.0× |

**A2 is clean on every scene**: no detached population, no invisible halo, 89–96% of its
primitives rendered against A0's 26–44%.

Importance-weighted sampling removes both pathologies without being designed for either. The
importance metric normalises accumulated blending weight by projected area — a construction
intended in the source method to suppress *sky*. Underwater, near-camera haze geometry and
diffuse low-opacity halos both present as large projected area with low per-pixel
contribution, and are removed for the same reason sky is.

**That is an accidental fit, not a designed one**, and it should be reported as such: the
mechanism transfers well here for a reason its authors did not have in view.

---

## 4. This revises the reported reduction

**A0 carries 36% visible primitives; A2 carries 93%** (means over four scenes).

| | reduction |
|---|---:|
| raw primitive count | 18.7× |
| **visible primitives** | **6.7×** |

Both are honest and they answer different questions. **18.7× is correct for storage** — every
primitive is written to disk. **6.7× is correct for scene representation**, because roughly
two thirds of the baseline's population is below the visibility threshold.

Quoting 18.7× as an efficiency headline without the visible figure overstates how much
*representation* was removed.

---

## 5. A defect, not a finding: the dense initialization

`A1/Curasao/s0` has a bounding box of **38,895 × 31,415 × 156,172** and a maximum radius
**23,863×** its median. Occupancy 0.006%, and gating does not recover it (0.004%) — the
distant material is **rendered**.

The cause is in the initializer's filters. Correspondences are kept if reprojection error is
small and the point lies in front of both cameras. Near-parallel rays satisfy both while
triangulating to arbitrary distance: angular error stays tiny at any depth. Nothing bounds the
distance, and with densification disabled nothing downstream removes the result.

**The consequence is not cosmetic.** Rendered depth is normalised per frame by its own
minimum and maximum, and A1's `z_max` reaches 122,673 against the baseline's ~50:

| | z_min | z_max |
|---|---:|---:|
| A0/IUI3-RedSea | 7.2 | ~50 |
| A2/IUI3-RedSea | 7.3 | ~40 |
| **A1/Curasao** | 10.0 | **~60,000** |

The real scene therefore compresses into `Ẑ ∈ [0, 0.0007]`, so `Â = exp(−β_att·Ẑ) ≈ 1` for
any β, attenuation has no effect, and β is unidentifiable. **A1/Curasao/s0's red and blue
attenuation channels both ended clamped dead** — the mechanism §3.5.6(a) describes, reached
not by primitive *reduction* but by primitive *placement*.

The remedy is a minimum parallax angle between the triangulating rays: the standard
structure-from-motion filter, rejecting points because their geometry is ill-conditioned
rather than because they are distant. It requires regenerating the dense clouds and re-running
every M1 cell.

---

## 6. What this adds to the thesis

**A geometric failure mode invisible to every photometric metric in the study.** The baseline
carries detached rendered clusters on two scenes and a diffuse invisible halo on a third, and
no PSNR, SSIM or LPIPS figure would reveal any of it.

It is the mirror image of §13.13, where the medium model collapsed while fidelity *improved*.
Together they make the same point from opposite directions: **in this pipeline, the standard
fidelity metrics are insufficient to certify either the physics or the geometry.**

**The pathology is scene-conditioned, and the conditioning is legible.** Panama — most turbid,
strongest backscatter — has the largest detached fraction. JapaneseGardens has none.
That is the underwater-conditioned analysis the reviewers asked for, and it comes from
geometry rather than from another table of fidelity numbers.

### Caveats

- **Seed 0 only.** The PLY is written for one seed per cell; `--save_ply_all_seeds` would be
  needed to attach dispersion to any of this.
- **Occupancy depends on grid resolution.** 64³ is fixed across clouds so the comparison is
  internally consistent, but the absolute percentages are not meaningful on their own.
- **α ≥ 0.05 is a chosen threshold.** Many low-α primitives can accumulate along a ray, so
  "invisible" means individually negligible, not collectively irrelevant.
- **The correlation between A0's fidelity rank and its occupancy rank is perfect across the
  four scenes but n = 4**, and the mechanisms differ by scene, so no single causal story is
  claimed from it.
