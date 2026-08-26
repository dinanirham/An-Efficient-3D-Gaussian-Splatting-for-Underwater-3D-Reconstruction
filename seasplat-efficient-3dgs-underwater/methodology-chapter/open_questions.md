# Open questions

Blocked by missing inputs, unresolved repository state, or claims that could not be reconciled
across `[paper]` / `[recommended]` / `[implemented]` / `[measured]`.

---

## Missing required inputs

### 🔴 Q-1 — No compatibility matrices exist

The task specified `./seasplat-efficiency-adaptation/` compatibility matrices as a required
input. That directory contains **only `audit-output/`** — the 8-branch implementation audit.
The efficiency-adaptation study that would have produced per-mechanism compatibility matrices
was never run; it was superseded before execution.

**Consequence.** Every `[recommended]` claim in this chapter is sourced from one of three
places instead: the A1 design spec and implementation plan, the draft thesis Chapter 3, or the
implementation audit's refit recommendations. Where §4.3 reports the status of a proposed
mitigation, "proposed" means *proposed in the audit* — **no mitigation was ever proposed in a
compatibility matrix, because none exists.** This is stated inline in §4.3 and repeated here so
it is not lost.

### 🔴 Q-2 — Design documentation exists for A1 only

A1 has an implementation plan and an approved design spec (goal, approach decision with
rationale, validation gate, parameter table, risk register, out-of-scope list). **A2 and A3
have neither.** Their `[recommended]` column is reconstructed from draft thesis Chapter 3 and
the notebook markdown cells alone.

This is why the A2 contradiction (§6, D-19: the thesis says the mechanism does *not* prune; the
code prunes) could not be resolved as either an intentional reframing or an error — there is no
design document to adjudicate it. **Only the author can say which was intended.**

### 🟡 Q-3 — The canonical source folder for A2 is ambiguous

A1 → `EDGS/` and A3 → `compact3d/` are unambiguous: both the code and the draft name them. For
A2, the code docstring cites **Mini-Splatting**, while draft §3.5.3 says only "inspired by
**surface-aware Gaussian grouping approaches** developed for terrestrial scenes" — naming no
method. `OMG/` (which builds on Mini-Splatting) is also present in the folder set.

This chapter treats **`mini-splatting/`** as the canonical source, following the code. If the
thesis intends a different lineage, §6.2 and §9.2 need revisiting.

---

## Repository state

### 🔴 Q-4 — The local repo copy is an empty repository

`my-research/seasplat-efficient-3dgs-underwater/` reports *"On branch main, No commits yet"* and
its `origin` points at a **different remote** —
`An-Efficient-3D-Gaussian-Splatting-for-Underwater-3D-Reconstruction.git` — not
`seasplat-efficient-3dgs-underwater.git`. Earlier in this same session it resolved all eight
branches; it no longer does.

**Consequence.** Code claims in this chapter are cited from the completed implementation audit,
which was performed against a full clone carrying all eight branches with commits recorded
(`baseline/seasplat` `ddc6259`, `a1` `ce9c21e`, `a2` `bcd6eee`, `a3` `980e915`, `a4` `788b325`,
`a5` `fd56225`, `a6` `26ea058`, `a7` `b4802fb`). They were **not re-verified in this pass**.
Unresolved: whether the new repository will carry the same eight branches, and which commits
map onto it.

**This chapter has been written into that empty repository**, at
`methodology-chapter/`, per the task's specified output path.

### 🟡 Q-5 — Which A1 implementation does the branch correspond to?

`feature/a1-deterministic-init` ships `roma_init.py` defaults `matches=5000`,
`certainty=0.02`, `voxel=0.001`. The executed runs used:

| | `matches` | `certainty` | `voxel` |
|---|---|---|---|
| Branch default | 5 000 | 0.02 | 0.001 |
| **A1 run** | 5 000 | **0.05** | **0.005** |
| **A1v2 run** | **20 000** | 0.02 | **0.002** |

**The defaults match neither run.** The branch commit date (2026-05-11) falls in the A1v2 run
window (2026-05-11), and `certainty=0.02` matches A1v2 — but `matches` and `voxel` match
neither. Unresolved: whether the branch is meant to represent A1, A1v2, or an untested third
configuration. Until settled, **the notebooks are the authoritative record of what ran**, not
the repository.

---

## Claims that could not be fully reconciled

### ✅ Q-6 — Which A2 trigger actually ran — **resolved**

Closed on a full reading of draft §3.5.3, which states the trigger **and its rationale**
correctly: *"designed to occur continuously after adaptive densification has completed …
Applying reorganisation during the densification phase would allow newly densified Gaussians to
refill the pruned positions, defeating the budget enforcement."* This matches the shipped
`iter > 15 000 ∧ iter mod 500 == 0`.

The **notebook markdown** (`--reorganize_from_iter 12000`, "single-shot") is the stale artifact;
no such parameter exists on any branch, and an `A2_spatial_reorganization_old.ipynb` sits
alongside the current notebook, consistent with a revision that was not propagated to the
notebook text. The measured flat **800 000 on all four scenes** corroborates the draft: a single
prune at 12 000 would sit inside the densification window and allow regrowth before 15 000.

Remaining residue: the deduction from the flat count is still `[inferred]` rather than read from
a run log — but the draft and the code now agree, so nothing turns on it. **Action: update the
notebook**, not the thesis.

### 🟡 Q-7 — Attribution of the A0-vs-A3 count divergence

A3 does not modify `train.py`, yet its runs produced primitive counts differing from A0's by up
to **27.7 %** (§8.3a). This chapter attributes the divergence to densification's
gradient-triggered stochasticity plus CUDA non-determinism `[inferred]`.

**Not excluded:** a different GPU SKU between the A0 and A3 sessions (they ran on different VMs
— §8.1), a driver or library version change between 2026-05-06 and 2026-05-12, or an
unnoticed code difference. Resolving this matters because §10.3 uses it as the study's headline
reproducibility figure. **One A0 re-run on a single scene would settle it** (§10.5).

### 🟡 Q-8 — A1v2 contradicts the plan's own stated rationale

The implementation plan justifies `matches_per_pair = 5000` on the grounds that *"20k produces
too many duplicates"* and *"20k saturates"* `[recommended: plan §3, spec §5]`. A1v2 then uses
**20 000** — the value the plan rejected — and produces the denser cloud that partially
recovers Panama (14.29 → 21.97 dB). Unresolved whether the original rationale was wrong, or
whether A1v2's density helps for a different reason than duplicate-avoidance predicts.

### 🟢 Q-9 — The A1 go/no-go gate result is unrecorded

The design spec defines a validation gate: Curasao only, 12 000 iterations, PSNR within ±2 dB
of A0, flat Gaussian count, visible loss-curve shift at iteration 10 000, and cloud size in the
20 k–80 k band `[recommended: spec §2]`. Two 12k test notebooks exist
(`..._test_12k_curasao` and `..._v2`), but **no recorded gate decision** was found. From the
full runs, the PSNR criterion passed on Curasao (+0.84 dB) and the **cloud-size criterion
failed on every scene** (§6, D-7). The spec instructs: *"If any pass criterion fails, treat as
a finding worth documenting; do not silently adjust until results match A0."*

---

## Data gaps

| # | Gap | Impact |
|---|---|---|
| 🟡 **Q-10** | Two versions of `master_metrics.csv` exist — a 12-row copy (A0/A1/A1v2 only) and a complete 20-row copy in the Drive archive. **This chapter uses the 20-row version.** | The shorter copy is stale; ensure the thesis draws on the complete one |
| 🟡 **Q-11** | **A1's offline RoMa preprocessing time is recorded nowhere.** | A1/A1v2 training times are not like-for-like with A0's (§8.2). The offline stage runs the slower non-`upsample_preds` RoMa path over (train views × 3) pairs. |
| 🟡 **Q-12** | `peak_render_vram_mb` is **empty in all 20 rows** | Render-side memory cannot be reported |
| 🟡 **Q-13** | A3/Curasao has `training_time_sec = 0`, `peak_train_vram_mb = 0` | Known invalid record `[recommended: draft Table 4.13]`; must be excluded from means, not averaged as zero |
| 🟢 **Q-14** | The `dense_<scene>.ply` files are unversioned and unhashed | The experimental condition for A1/A4/A5/A7 cannot be reproduced (§10.4) |

---

## Evidence-tag audit

| Tag | Count | Note |
|---|---:|---|
| `[measured]` | 30 | Colab outputs — `master_metrics.csv` (20 runs), TensorBoard filenames |
| `[recommended]` | 45 | draft thesis Ch. 3 · A1 plan · A1 design spec · audit refit recommendations |
| `[paper]` | 23 | EDGS · Mini-Splatting · CompGS-VQ · RoMa · SeaThru-NeRF |
| `[implemented]` | 17 | branch code, cited via the implementation audit (see Q-4) |
| `[inferred]` | 5 | Q-6 (A2 trigger), Q-7 (count divergence, ×3 restatements), GPU capacity from peak VRAM |
| **`[unverified]`** | **0** | **No claim carried into the final chapter rests on unverified evidence.** |

Every substantive claim traces to a measurement, a source publication, the shipped code, a
design document, or an explicitly labelled inference. The five `[inferred]` items are listed in
Q-6 and Q-7 with the evidence that would settle them.
