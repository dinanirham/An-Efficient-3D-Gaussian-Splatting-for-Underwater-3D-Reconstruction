# Execution prompt — implementing the combined method

**Derived from:** `combined-method-methodology/01`–`12` (the spec) and `chapter/00`–`09`
(the write-up). This file is the *executable* refinement of that spec: it says what to build,
in what order, and how each step is proved done.

**Status of decisions taken before this prompt was written:**

| Decision | Answer | Consequence |
|---|---|---|
| First milestone | **Full 2³ matrix** — all 8 cells, 4 scenes, 3 seeds = **96 runs** | No science result until the whole stack lands. Staged run plan in §7 mitigates. |
| Prior adaptation code | **Do not port.** Reimplement from spec. | ~650 lines of existing `roma_init.py` / `quantize.py` / A2 code are *not* reused. `BINUS/Thesis/**` is **out of scope** and must not be read or written. |
| Spec vs existing implementation | **New spec wins throughout** | Includes R-12 (quantization-aware training with STE) and R-13 (accumulated-blending-weight importance). Requires the CUDA fork merge. **Chapter 4's reported numbers are fully superseded.** |
| Compute | **Colab Pro, A100** | Session limits and non-guaranteed allocation are first-class engineering constraints, not footnotes. See §7. |

---

## 0. Scope boundaries — read this before touching anything

### In scope (read, build against, install from)

| Path | Role |
|---|---|
| `my-research/implementation/` | **The working repository.** Created 2026-08-27 from `my-research/seasplat/`; all 37 files verified byte-identical by SHA-256; tagged `baseline/seasplat-ddc6259`. Work happens on branch `feat/e3dgs-uw-implementation`. |
| `my-research/seasplat/` | Reference implementation of the baseline, at commit `ddc6259`. Use for diffing and for line references. |
| `my-research/RoMa/` | **Reference implementation of the matcher.** `romatch/` is installable; this is where A1's correspondence stage comes from. |
| `my-research/mini-splatting/` | **Reference implementation of A2**, including `submodules/` which contains the **forked rasterizer** R-13 requires. |
| `my-research/compact3d/` | **Reference implementation of A3** — `kmeans_quantize.py` is the STE quantizer R-12 requires. |
| `my-research/EDGS/` | Reference for A1's opacity decay and LR clamp (R-5). |
| `my-research/*/research-methodology-output/` | The tagged breakdowns. Every `[repo: file:line]` citation resolves here. |
| `my-research/combined-method-methodology/` | The spec. `01`–`12` are normative. |
| ~~`my-research/seasplat-efficiency-adaptation/audit-output/`~~ | **Deleted 2026-08-27**, deliberately, mid-session. Its actionable content survives as the anti-requirements table in **§6**; the per-branch and combination audits themselves are gone and are not recoverable from git (the folder was never tracked). |
| `my-research/dataset/SeathruNeRF_dataset/` | The four scenes. |

> **"Reimplement from spec" forbids reusing the prior *adaptation*, not the *source methods*.**
> The four reference implementations above are the published methods this work composes, they
> sit under `my-research`, and building against them is the whole point. Copying
> `kmeans_quantize.py`'s STE logic or `mini-splatting`'s forked kernel is expected and correct.

### Out of scope — do not read, do not write, do not cite

- `BINUS/Thesis/**` — including its eight `feature/a*` branches. The mechanism code there is
  explicitly not being ported.
- `my-research/seasplat-efficiency-adaptation/` and
  `my-research/seasplat-efficient-3dgs-underwater/` — **both deleted 2026-08-27**, deliberately.
  Do not recreate either. The former held only markdown; the latter was a second copy of the
  same SeaSplat baseline that `my-research/seasplat/` still provides.

---

## 1. Repository and branch topology

Work in `my-research/implementation/`. ✅ **Done** — created from
`my-research/seasplat/`, committed on `feat/e3dgs-uw-implementation`, tagged
`baseline/seasplat-ddc6259`.

**Topology: one `main` carrying all three mechanisms behind feature flags.** Not eight
branches. The prior attempt used eight branches and its own audit found they were clean
file-level unions — `git diff a4..a7` on the mechanism files was empty — meaning the branch
topology encoded a flag matrix as refs and did no real work. A single flagged `main` matches
the canonical pseudocode in `07-pseudocode.md`, makes combination cells trivial, and removes
the class of bug where a fix lands on three of seven branches.

**Before the first commit:**

1. `git tag baseline/seasplat-ddc6259` at the current HEAD, so every later diff has an anchor.
2. Confirm the tag's tree matches `my-research/seasplat/` for the method-bearing files
   (`train.py`, `arguments/__init__.py`, `scene/`, `gaussian_renderer/`, `deepseecolor/`).
   Record any difference before building on it.

**Commit discipline:** conventional commits. One mechanism per commit series. Every commit
that changes training dynamics states which cells it invalidates.

---

## 2. Milestones

Each milestone has a **binary acceptance test**. Do not start the next until the current one
passes, and record the evidence.

### M1 — Environment and rasterizer merge  ⬅ hardest, do first

**Build one environment** (CUDA 12, Python ≥3.10) that runs all three mechanisms. The four
source stacks cannot coexist as published (`08-computational-profile.md` §8.6): the baseline
targets SM 8.6/8.9 with 9.0 commented out, mini-splatting pins Python 3.7 / CUDA 11.6,
compact3d is a file overlay, EDGS is the only modern one.

**The rasterizer merge (CD-13).** A2's importance metric (R-13) needs per-primitive
accumulators the stock kernel does not return: `accum_weights`, `area_proj`, `area_max`, plus
`out_pts` and `accum_alpha`. The baseline needs a second rasterization pass with
`override_color = z_cam`. One kernel must do both.

### ✅ RESOLVED 2026-08-27 — no CUDA merge is required

Investigation found the problem is **not** the one anticipated above. Three forks are in play:

| Fork | Forward returns | Alpha? |
|---|---|---|
| INRIA stock | `color, radii` | ❌ |
| `_ms` (Mini-Splatting) | `color, radii, accum_weights, accum_weights_count, accum_max_count` | ❌ |
| `dxyang/…` (SeaSplat) — submodule **empty** in this checkout | `color, alpha, radii` | ✅ |

The `_ms` fork *does* accept `colors_precomp`, so the depth pass composes fine. What it does
not return is **alpha** — and SeaSplat needs a *differentiable* one, because `L_op`'s gradient
reaches opacity through alpha alone. `_ms`'s `render_depth()` exposes `accum_alpha` but is not
an autograd `Function`, so it cannot supply it.

**Resolution — a probe channel, no CUDA changes and no extra pass.** Alpha compositing is
applied per channel and does not depend on the colour values:
`C_ch = Σᵢ Tᵢaᵢc_{i,ch} + T_final·bg_ch`. Setting `c = 1` on a channel with `bg = 0` gives
`C = Σᵢ Tᵢaᵢ = 1 − Πᵢ(1−aᵢ) = α`, differentiable through the ordinary autograd path.
SeaSplat already ran a depth pass **every iteration** with `override_color = [z,z,z]`, reading
channel 0 only — channels 1 and 2 were redundant. The probe reuses it:

    ch0 = z → Z_raw     ch1 = 1 → α     ch2 = 0

Verified applicable: `white_background = False` and `random_background = False` are the
defaults, so the scene background is already zero and this is behaviourally identical at the
default configuration.

**This retires the single largest schedule risk in the build.** Implemented in commit
`a720a51`; `render_depth()` is kept as a compatibility alias.

**Acceptance** — `tools/verify_rasterizer.py`, seven checks, GPU-only:
- T0: extension builds, `sm_80+`.
- T1: α ∈ [0,1] and monotone in opacity. T2: α composites as `1−(1−a₁)(1−a₂)`.
- **T3 (decisive):** for one Gaussian at depth `z`, the probe gives `Z_raw = α·z`, so
  `Z_raw/α` must recover `z` on every covered pixel, at every opacity. A wrong channel, a
  leaking background, or an α that is not accumulated α all break this identity.
- T4: α is differentiable w.r.t. opacity (what `L_op` needs).
- T5: the three importance accumulators are present and non-degenerate.
- T6: zero background does not leak into the probe.

Still outstanding: a 100-iteration run with all flags off, compared against
`baseline/seasplat-ddc6259` on **loss trajectory**, not just "it ran". Note this can only be a
*mathematical* equivalence check, not a bitwise one — the true baseline cannot be executed
here at all, because its rasterizer submodule was never checked out.

### M2 — Config layer, assertions, manifest, diagnostics

Nothing scientific runs until this is in place, because the failure modes it prevents are all
**silent**.

**Config layer (CD-1).** The baseline registers ~12 booleans that default `True` using
`action="store_true"`, which can only *set* a flag, never clear it. A 2³ matrix is impossible
as shipped. Add a config layer above the parser: one file per cell naming the three mechanism
flags plus overrides; resolve against parser defaults; write resolved values before
`ModelParams` is constructed.

Three flags, and nothing else selects a cell:
`--m1_dense_init`, `--m2_simplify`, `--m3_quantize`.

**Startup assertions — all fatal:**
- `--eval` passed **and** the test set is non-empty. It defaults `False` in the baseline and
  its own README omits it, which silently trains on everything.
- Each enabled mechanism will actually fire. Two of three are silent no-ops at upstream
  defaults (EDGS's `gs_epochs=0`; compact3d's `kmeans_st_iter = total_iterations`).
- `densify_until_iter > seathru_from_iter` — the medium-aware pruning property depends on this
  ordering and is otherwise satisfied only incidentally.
- `seathru_from_iter != 9_000_000`. The default disables the medium model entirely, which
  would make every cell a study of plain 3DGS rather than of underwater rendering.
- **GPU is an A100.** Colab does not guarantee allocation. Every cell must land on the same
  device or the between-cell contrasts are worthless. Abort with a clear message otherwise.

**Run manifest (`run_config.json`, written at startup, per run):** all resolved CLI args, git
SHA, `nvidia-smi -L` output, driver and library versions, the seed, the scene, the cell ID, the
train/test frame lists, and the SHA-256 of the dense `.ply` if A1 is active.

**Diagnostics (CD-12) — the cheapest high-value item in the whole build:**
- `Ẑ_min`, `Ẑ_max` per frame, logged **before and after** each simplification event.
- `β_att`, `β_bs`, `B^∞` at every checkpoint.
- Primitive count at **five** points: post-init, post-settling, and before/after each
  simplification event — logged **unconditionally**, not only when something was pruned.
  Ambiguous silence is how the previous attempt lost the answer to whether its budget ever
  bound.

**Acceptance:** a dry-run of all eight configs on one scene at 200 iterations produces eight
distinct resolved-config dumps, all assertions fire correctly when deliberately violated, and
the diagnostic CSVs contain the expected columns.

### M3 — A1: dense deterministic initialization

Offline stage producing a dense `.ply`, plus training-loop changes.

**Offline (`source/roma_init.py`, new):**
- Reference selection by k-means over flattened `world_view_transform`, with
  **`K_ref = min(num_refs, V)`** (CD-2). `V` is 18–29 here; the upstream default of 180
  exceeds every scene's total view count.
- `J = 3` nearest neighbours by Frobenius distance.
- RoMa dense match. **Expose and log `τ_corr`** — upstream it has no config key and silently
  inherits the matcher's `sample_thresh`.
- Batched DLT triangulation via a single `torch.linalg.lstsq` / batched SVD. Not a per-pair
  Python loop.
- Seed the matcher (`torch.manual_seed`, `np.random.seed`, `torch.cuda.manual_seed_all`), and
  emit point count + SHA-256 into a sidecar `.json`. **The cloud is the experimental condition
  for A1/A4/A5/A7**; an unversioned one makes those four cells unattributable.
- Pin `romatch` in `requirements.txt`.
- Ship **two density presets** and record which was used. See the §5 gate.

**In-loop:**
- `--m1_dense_init` disables densification only. **It must not disable α-pruning or opacity
  reset** (R-4). In the baseline all three live in one gated block; splitting them is the
  single most consequential correctness requirement in A1. EDGS keeps its `α < 0.005` prune
  running outside the densify gate.
- Port EDGS's two undocumented counterweights (R-5, CD-7): `reduce_opacity`
  (`logit += log(0.99)` every 10 steps while `iter < densify_until_iter`) and `max_lr`
  (`update_learning_rate(max(step, 8000))`).
- ⚠️ `reduce_opacity` and the baseline's `L_op` both push opacity down and neither source
  faced the other. Gate `reduce_opacity` to `iter < seathru_from_iter`, **or** reduce `λ_op`
  while it is active — and make the choice a logged config value, not a constant.

**Acceptance:** a run with `--m1_dense_init` shows densification off, α-pruning still firing
(visible in the unconditional count log), opacity decay applied, and LR clamped. The `.ply`
hash is reproducible across two invocations at the same seed.

### M4 — A2: simplification to budget

**New spec wins**, so this is R-13, not the prior magnitude heuristic.

- Accumulate **per-primitive blending weight** over all training views using the forked
  kernel: `I¹ = Σ_v accum_weights` (indoor) or `I² = Σ_v accum_weights / area_proj` gated on
  intersection (outdoor).
- **Intersection preserving:** `I_imp[area_max == 0] ← 0`.
- **Importance-weighted stochastic sampling without replacement** to the budget
  (`torch.multinomial`), **not** deterministic top-k. Mini-Splatting §4.2 argues explicitly
  against top-k because importance is spatially autocorrelated and thresholding removes whole
  regions; with densification off in A4/A7 there is nothing left to recover what gets stripped.
- Second event at 20 000: deterministic CDF prune retaining the top 99% of importance mass.
- **Explicit primitive budget `n_bud`, not a sampling ratio** (CD-5), set from A0's converged
  count. A real `--no_reorg` off-switch (R-9) — not a `hasattr` guard, which is always true.
- **Scope: simplification only** (CD-4). No blur split, no depth reinitialization. Name it
  *Mini-Splatting's simplification stage* in every artifact, or a reader assumes the full
  method.
- **Retain the baseline's periodic `reset_opacity()`** (CD-3), contrary to mini-splatting's
  silent removal of it. Its removal is defensible upstream because depth reinit resets opacity
  anyway; under simplification-only scoping that compensating mechanism is gone.
- Choose and **justify** `imp_metric`; neither variant was designed for a scattering medium
  and the outdoor variant's area normalisation exists to suppress sky. Do not name the
  parameter `imp_metric` if it means anything other than `I¹` vs `I²`.

**⭐ CD-6 — the medium re-identification burst.** Immediately after each simplification event,
run medium-only optimizer steps with geometry frozen, reusing the baseline's existing warm-up
machinery. This is the work's principal technical claim: pruning changes `Ẑ_min`/`Ẑ_max`,
which rescales the medium model's only input, which is formally indistinguishable from a
change in `β`. Burst length is a logged config value, not a constant — it is itself a
candidate ablation (`open-questions.md` OQ-10).

**Acceptance:** the diagnostic CSV shows `Ẑ_min`/`Ẑ_max` changing across the event and `β`
recovering within the burst. Whether it recovers is a *result*, not an acceptance criterion —
what must pass is that both quantities are captured.

### M5 — A3: quantization-aware attribute VQ

**New spec wins**, so this is R-12: in-loop QAT with STE, not post-hoc snapping.

- **Three codebooks: `f_dc`, `scale`, `rotation`** (CD-9). No SH codebook — `f_rest` is
  `(N,0,3)` under `sh_degree=0`.
- **Never quantize `xyz` or `opacity`** (R-2). compact3d excludes both deliberately; sharing
  positions makes primitives coincide, and the prior attempt's inclusion of opacity is the
  sharpest defect in the audit.
- Quantize `scale` **before `exp`** and `rotation` **before normalisation**.
- Asymmetric K-means schedule: centroids re-averaged every iteration on cached assignments,
  full reassignment every `t = 100`.
- **`k ≥ 4096`** (CD-9 / R-12), not 256. At `sh_degree=0` the group-size machinery is inert,
  so `k` is the only quality dial.
- STE: quantized forward, gradients to the unquantized parameters.
- **`kmeans_st_iter > simp_iteration2`** (CD-10). A codebook fitted before the prune is fitted
  to a population about to be discarded.
- **`--opacity_reg` disabled** (CD-8). Its count reduction would confound the M2×M3
  factorisation and its own authors attribute compact3d's FPS gain to it, not to quantization.
  Expect A3's frame-rate gain to be ≈1.0×; that is correct, not a failure to reproduce.
- **Index bit-width `ceil(log2(k))`** (CD-11), and report **raw quantized size beside** any
  zlib-compressed figure (R-6) — otherwise generic entropy coding is credited to the quantizer.

**⚠️ QAT creates a conflict that post-hoc quantization does not have.** Once clustering runs
in-loop, A2's `prune_points` invalidates the assignment vector. Required alongside:
1. `prune_points` must index-select `nn_index` with every other per-primitive tensor;
2. force an assignment refresh immediately after each simplification event;
3. handle clusters emptied by pruning.
compact3d solves this upstream — its own ℓ1-opacity pruning coexists with QAT — so the pattern
is available to read at `compact3d/train_kmeans.py`.

**Acceptance:** an A6 smoke run (M2+M3 both on) completes without an index-length assertion,
and the codebook refresh after the simplification event is visible in the log.

### M6 — Full matrix

Per §7.

---

## 3. What "model size" means

Reported size = unquantized attributes (`xyz` float32, `opacity`) + index streams + codebooks
+ `kmeans_args` + `backscatter_*.pth` + `attenuate_*.pth`. All of it. The medium scalars are
negligible in magnitude but must appear or it is a claim rather than an accounting.

**State the per-primitive normalisation beside every ratio.** The baseline stores **14 floats
per primitive**, not the 59 the compression literature assumes. Of those, quantization can
address 10; `xyz` and `opacity` are excluded structurally. The ceiling is a factor of a few,
not the 40–65× compact3d reports. A ratio quoted against a 59-float baseline is a different
quantity, and the previous attempt's own audit put its ceiling at ≈2.8×, ≈3.5× with uint8
indices.

---

## 4. Metrics

Per `06-evaluation-metrics.md`. The non-negotiables:

- **PSNR reported under both conventions**, labelled: per-channel-mean (the baseline's, keeping
  A0 comparable to its published table) and pooled-MSE (the standard, enabling comparison with
  SeaThru-NeRF / UW-3DGS / TUGS).
- LPIPS backbone stated (VGG).
- Full-frame, unmasked.
- Log whether renders were written as PNG or JPEG — the fallback is silent and the local GT is
  PNG, so it should not fire.
- Both unweighted-scene-mean and image-weighted aggregation (scene counts are 21/29/20/18).
- Realised `N_rend` reported, never the target budget.
- Timing reported as wall-clock **and effective optimizer steps** — the `continue` statements
  bypass the iteration counter, so a "30 000-iteration" run does ≈43 000 steps, and CD-6's
  bursts add more.

---

## 5. Gates that must be resolved with data, not assumption

**G-1 — A0's converged primitive count.** Sets `n_bud` (CD-5). Unreported in any publication
of the baseline. **The matrix cannot be configured until A0 has run.** This is a hard
sequencing dependency, not a preference.

**G-2 — Does the budget bind?** If A1's converged count sits below `n_bud`, the pruning step is
a no-op and **A4 ≡ A1, A7 ≡ A5** — two of eight cells silently do not exist. The previous
attempt hit exactly this: its A1 counts were 222k–369k against an 800k budget, with
densification off so the count could never rise to meet it. Resolve by setting `n_bud` from A0
so it binds everywhere, **and** by selecting the A1 density preset (via `matches_per_ref`) so
that A1's count exceeds it. Report per run whether the budget bound. A null interaction from a
non-binding budget is an artifact, not a finding.

**G-3 — Environment validity.** A0 must reproduce the baseline's published quality on these
four scenes within run-to-run variation. If it does not, the environment is wrong and no other
cell is interpretable. This is the first check, not the last.

---

## 6. Anti-requirements — defects the previous attempt hit, do not recreate

From `audit-output/`, reframed as things this build must not do:

| Do not | Because |
|---|---|
| Let `--m1_dense_init` disable α-pruning or opacity reset | Backscatter-only primitives that `L_op` suppresses then persist for all 30 000 iterations, costing memory and sort time while contributing nothing to PSNR — **so the metric cannot see the problem** |
| Quantize `opacity` or `xyz` | compact3d excludes both deliberately; the prior attempt included opacity and it is the sharp end of the worst compounding defect in its set |
| Use deterministic top-k for A2 | The method being adapted argues explicitly against it |
| Log primitive count only when something was pruned | Silence becomes ambiguous between "under budget" and "never ran" |
| Ship `hasattr(opt, 'max_gaussians')` as an off-switch | Always true on a branch that defines the attribute; A2 then has no control run |
| Credit `np.savez_compressed` to the quantizer | Report raw and compressed separately |
| Use uint16 indices for `k ≤ 256`, or `k = 256` at all | 2× waste on the index payload; and `k=256` is 16–128× coarser than the reference |
| Leave `docs/` files empty | The prior audit could establish deviation from published methods but not from intent, because design intent was never written down |
| Assume the GPU is an A100 | Colab does not guarantee allocation; assert and record |

---

## 7. Run plan for Colab Pro A100

**Budget reality.** 8 cells × 4 scenes × 3 seeds = **96 runs**. The baseline is 1 h 25 m on
unnamed hardware; QAT adds 36–69%; expect ≈1.5 h/run on an A100 → **≈145 GPU-hours**, plus
offline RoMa preprocessing per scene per density preset. Colab Pro sessions terminate well
before that, and allocation is not guaranteed.

**Therefore the harness is as much a deliverable as the method:**

- **Checkpoint and resume.** Every run must survive a session kill and restart from its last
  checkpoint without corrupting its diagnostics.
- **A run ledger** in Drive: one row per (cell, scene, seed) with status, GPU seen, start/end,
  and output path. The queue is driven from the ledger, so a fresh session picks up the next
  unfinished run automatically.
- **Outputs to Drive**, not to the session filesystem.
- **Abort on non-A100** rather than silently producing a run that cannot be compared.

**Staging — each stage produces a usable result on its own:**

| Stage | Runs | Cumulative | Unblocks |
|---|---|---|---|
| **S1** — A0 | 12 | 12 | G-1 (the budget), G-3 (environment validity). **Nothing else can start.** |
| **S2** — A2 | 12 | 24 | H4, the central claim — via the `Ẑ`/`β` diagnostics. This is the minimum viable scientific result. |
| **S3** — A1, A3 | 24 | 48 | H1, H2 — main effects, and G-2 (does the budget bind) |
| **S4** — A4, A5, A6 | 36 | 84 | H5 — the three two-way interactions |
| **S5** — A7 | 12 | 96 | The three-way term and the effect-from-above contrasts |

Run S1 to completion before writing any more mechanism code than M3 requires — it is the only
stage whose output changes the configuration of everything after it.

---

## 8. Definition of done

- All eight cells run at three seeds on four scenes, on A100s, with manifests.
- `docs/ablation_design.md`, `docs/experiment_plan.md`, `docs/reproducibility_notes.md`
  written — not empty. Source their content from `chapter/05`, `chapter/04`, `chapter/07`.
- Every `[proposed integration]` decision CD-1…CD-14 is either implemented and traceable to a
  commit, or explicitly recorded as not implemented with a reason.
- The three interaction terms of `08-computational-profile.md` §8.4 computed against pooled
  seed dispersion.
- `open-questions.md` updated: OQ-2 (no results) closed; OQ-4 (A0's count) closed; OQ-10
  (burst length) either closed or restated with data.

---

## 9. First actions

1. Tag `baseline/seasplat-ddc6259`; verify the tree against `my-research/seasplat/`.
2. Stand up the environment; build the merged rasterizer; pass M1's acceptance test.
3. Build the config layer, assertions, manifest and diagnostics; pass M2's acceptance test.
4. Implement A1's offline stage and in-loop changes (M3).
5. **Run S1 (A0 × 4 scenes × 3 seeds) and read off `n_bud`.**
6. Then M4, M5, and stages S2–S5.

Steps 1–3 need no GPU beyond a smoke test and remove every silent-failure mode in the build.
Step 5 is the sequencing dependency everything downstream waits on.
