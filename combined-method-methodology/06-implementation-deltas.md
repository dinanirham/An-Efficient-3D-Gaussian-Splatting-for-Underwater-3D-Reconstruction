# §6 — Implementation deltas

Two parts. **§6.1–6.4** carry forward each source's own tagged deltas, filtered by whether
they actually bite the combined method — a delta that is inert here is worth knowing about
precisely so it is not chased. **§6.5** adds deltas that exist only because of the
combination, all of them `[proposed integration]`.

Severity is the source folder's own rating unless re-rated here, in which case the re-rating
is justified.

---

## 6.1 Inherited from the baseline — SeaSplat

Full table: `../seasplat/11-paper-vs-repo-disagreements.md` (17 deltas, D-1 … D-17, plus one
shared deviation S-1). Filtered:

| Src # | Delta | Bites the combined method? |
|---|---|---|
| D-1 | Paper's Eq. 10 is an unweighted sum; repo attaches six λ spanning 200× | ✅ **Yes.** Any write-up of the objective must give the weighted form. Carried into `04-loss.md` §4.2. |
| D-7 | `learned_bg` — a 4th learned parameter, its own optimizer, init `[0.05,0.25,0.80]`, **copied into `B^∞`** at the transition. **Not in the paper at all** | ✅ **Yes, and load-bearing.** It is the data-derived warm start for `B^∞` that keeps D-1 ("no medium") from winning `[../seasplat/05-constraints.md M-5]`. Must be preserved in all eight cells or A0 is not SeaSplat. |
| D-8 | `continue` bypasses `iteration += 1`; a "30 000-iteration" run does **≈43 000** optimizer steps | ✅ **Yes, and compounds.** The `[PI]` medium re-warm-up bursts add more. Wall-clock claims must report *effective optimizer steps*. `08-computational-profile.md` §8.4. |
| D-12 | ~12 boolean flags default `True` and are registered `action="store_true"`, so they **cannot be disabled from the CLI** | ✅ **Yes — this is the blocker for the whole feature-flag scheme.** A 2³ matrix requires toggling behaviour; SeaSplat's argument parser structurally prevents it. See §6.5 CD-1. |
| D-17 | `--eval` defaults `False`; README's command omits it ⇒ empty test set, trains on everything | ✅ **Yes, and doubled** — EDGS has the same defect independently (`../EDGS/11-…` D-12). |
| D-13, D-14 | Metrics recomputed from **8-bit files re-read from disk**, **JPEG** when the GT dir has no PNGs; PSNR is the **mean of per-channel PSNRs**, not pooled MSE | ✅ **Yes.** Both are comparability defects that this work inherits and must standardise. `10-reproducibility.md` §10.3. Note: the local dataset's `images_wb/` are **`.png`** (verified on disk), so the JPEG fallback should **not** trigger here — a small piece of good news worth confirming at runtime rather than assuming. |
| D-3 | Medium maps computed **twice** — live-`Ẑ` copies feed `Î`, detached copies feed `L_bs`; the paper describes only the detached direction | ⚠️ Informational. The gradient routing is unchanged by any mechanism, but a reimplementation that "fixed" this to match the paper would break M-1. |
| D-10 | Medium init `β_att ← [1.1, 0.95, 0.95]` hand-tuned, `β_bs`, `B^∞ ← U(0,1)³`; not stated in the paper | ⚠️ Informational — but it is a seeded random draw, so it belongs in the seed audit (`10-reproducibility.md` §10.1). |
| D-15 | Table III rows are **cumulative additions**, not leave-one-out; row 9 ≠ row 8 | ✅ **Yes** — the reading trap this work's factorial design exists to avoid. `04-loss.md` §4.5. |
| D-2, D-9, D-11, D-16 | kernel-shape notation, SH-degree wording, legend typo | ❌ Cosmetic. |
| D-4, D-5, D-6 | `L_bs` `k = 1000` + Huber; `L_sat` squared and two-sided; `L_op` uses `Î` not `I` and an unsquared norm | ❌ Inert **for the composition** (no mechanism touches these terms) but they must be quoted correctly if the objective is written out. |
| S-1 | Signed image gradient `e^{−∂I}` in `L_Zsmooth`, where Godard et al. uses `e^{−\|∂I\|}` — inverted on half of all edges; the correct version sits commented out in the repo | ⚠️ **Inherited deliberately unfixed** (`04-loss.md` §4.2). Fixing it would make A0 ≠ SeaSplat-as-published. |

---

## 6.2 Inherited from M1 — EDGS

Full table: `../EDGS/11-paper-vs-repo-disagreements.md` (D-1 … D-14). The headline context
matters: **the released code predates the paper by ~10 months and implements the v1 method**;
`git diff 668e280 HEAD` touches only `LICENSE.txt`, `README.md`, and a removed submodule
pointer `[../EDGS/00-index.md]`.

| Src # | Delta | Bites the combined method? |
|---|---|---|
| D-1 | **§3.5's SH initialization (Eqs. 12–13) is not implemented**; `f_rest ← 0`. Table 6's `SH Init.` column is not reproducible | ❌ **INERT HERE — and this is a genuine simplification.** `sh_degree = 0` means `f_rest` has shape `(N,0,3)` and does not exist `[../seasplat/03-variables.md]`. EDGS's highest-severity delta cannot manifest. `[inferred]` |
| D-3 | `reduce_opacity = True`: `logit ← logit + log(0.99)` every 10 steps for 15 000 steps (Σ ≈ **−15**); `opacity_lr` halved to 0.025; `reset_opacity()` unreachable. **Undocumented** | ✅ **Yes — the top inherited risk.** Directly collides with `L_op` (`03-variables.md` IC-1, `05-constraints.md` A1). |
| D-4 | `max_lr = True`: `update_learning_rate(max(step, 8000))`. **Undocumented** | ✅ **Yes** — collides with M2's LR rewind under A4/A7 (IC-3). |
| D-2 | `p^proj` is an **opacity mask** (logit −10), not a sampling distribution; failing points are kept | ✅ **Yes, mildly.** It inflates the post-init count and makes the "initial Gaussian count" ambiguous; combined with D-3 the bad points die within a few hundred steps. Report both pre- and post-settling counts. |
| D-5 | Reference views chosen by **k-means over flattened `world_view_transform`**, undescribed in the paper | ⚠️ **Yes, at this dataset size.** With `V` = 18–29 views and `num_refs = 180`, k-means over poses is asked for more clusters than points. `[inferred]` See CD-2. |
| D-8 | `τ_corr` has **no config key**; the code uses RoMa's own `sample_thresh` (= 0.05) | ✅ **Yes.** It is an unreported hyperparameter that silently changes if the matcher is swapped. Must be exposed and logged (`03-variables.md`). |
| D-9 | RoMa reconfigured: `upsample_preds = False`, `symmetric = False` — two of its features **disabled** for speed | ⚠️ **Yes.** `upsample_preds = False` reduces warp resolution, which matters more on 18–29-view scenes than on 100+-view ones. Candidate for a sensitivity check. |
| D-6, D-7 | Scale = `inv_act(‖μ−campos‖·0.001)` isotropic then **× 0.5** globally; rotation copies `_rotation[-1]` | ⚠️ Informational, but the ×0.5 is undocumented and matters for the initial `Ẑ`. |
| D-10 | **README contradicts the config** in four places: `no_densify` (config `False`, README "True by default"), `wandb.mode`, `gs_epochs = 0` (training is a no-op), `matches_per_ref` 15 000 vs 20 000 | ✅ **Yes, high trap value.** Every one must be set explicitly and asserted. |
| D-11 | `batch_size: 64` is read and **never used**; one camera per step | ❌ Inert, but do not "fix" it — SeaSplat also samples one camera. |
| D-12 | `dataset.eval: false` **and** `"eval": False` hard-coded into `cfg_args` | ✅ **Yes** — compounds SeaSplat D-17. |
| D-13 | `psnr()` written for `(3,H,W)` but **called with `(1,3,H,W)`**, so EDGS silently uses **pooled-MSE** PSNR | ❌ **Inert** — the combined method uses SeaSplat's metric harness, not EDGS's. But it is exactly the convention mismatch `10-reproducibility.md` §10.3 exists to standardise. |
| D-14 | Tables 3–6 are **four different kinds** of ablation; Tab. 6's direction is ambiguous and its checkmarks survive neither `pdftotext -layout` nor `-raw` | ⚠️ Only affects citation of EDGS's own numbers. |

---

## 6.3 Inherited from M2 — Mini-Splatting

Full table: `../mini-splatting/11-paper-vs-repo-disagreements.md` (D-1 … D-15). Paper and
repo are 4 days apart, so version drift explains nothing.

| Src # | Delta | Bites the combined method? |
|---|---|---|
| D-1 | **`reset_opacity()` is never called** — `grep -c` → 0 in `ms/` and `ms_d/`, 1 in `gs/`. 3DGS's core anti-floater mechanism is **removed**, unremarked | ✅ **Yes, seriously.** SeaSplat retains opacity reset every 3 000 iterations and relies on it alongside `L_op` to suppress D-4 floaters. M2 deletes it. `[inferred: combining ../mini-splatting/11 D-1 with ../seasplat/07-pseudocode.md line 64]` See CD-3. |
| D-2 | Depth-reinit sampling probability is `(1 − α_accum)` — **importance-weighted toward low-opacity pixels**, where the paper says "randomly select" | ⚠️ **Only if the densification half of M2 is used.** Under the simplification-only scoping (`01-taxonomy.md` A2-a) this is inert — but the scoping decision must be stated for that to be true. |
| D-4 | `--sampling_factor = 0.5` and the CDF prune threshold `0.99` are **not in the paper** | ✅ **Yes.** `sampling_factor` is the knob that generates the paper's entire rate–quality curve, and it is replaced here by an explicit target count `[PI]`. |
| D-5 | LR-schedule **rewind** to step 5 000 after simplification. Undocumented | ✅ **Yes** — IC-3. |
| D-7 | "Reinitialize" additionally zeroes `f_rest`, resets `s` (kNN), `q` (identity) and `o` (0.1), and the caller discards **all Adam moment state**. Happens 5× per run | ✅ **Yes.** Under the simplification-only scoping it fires twice, not five times — but each firing still resets opacity *up* to 0.1 and discards Adam state, including the medium optimizers' co-adapted geometry. |
| D-3 | `--num_max = 4.5 M` hard cap, absent from the paper | ❌ Inert at this scene scale. |
| D-8 | `Intersection()` is not a function; Eq. 3 is one line, `imp_score[accum_area_max == 0] = 0` | ❌ Cosmetic, high trap value when reading the code. |
| D-9 | `ms/` uses `replace=False`; `ms_d/` uses `replace=True` + `np.unique` ⇒ fewer points than requested | ❌ Inert — `ms/` is the variant used. |
| D-10 | Mini-Splatting-**C** adds an undocumented `np.unique` voxel dedup that **drops colliding Gaussians**, folding primitive removal into the reported file size | ❌ Inert — **`ms_c` is not used**; M3 is CompGS-VQ, not RAHT. Worth stating explicitly so nobody cites `ms_c`'s rate figures as this work's. |
| D-12 | Seeds hard-coded to 0, no CLI, no `cuda.manual_seed_all`; but the decisive steps are `np.random.choice` fed by GPU-computed probabilities, so `N` remains run-dependent | ✅ **Yes.** `N` after simplification is stochastic even at a fixed seed — which means the *primitive budget itself* has run-to-run variance. `10-reproducibility.md` §10.1. |
| D-13 | "Seamless integration" applies to *inference* (output is a plain `.ply`) but **training requires the forked rasterizer** | ✅ **Yes** — the CUDA reconciliation problem, `01-taxonomy.md` A2-d. |
| D-14 | `ms/` scores float tensors in memory; `ms_c/` scores 8-bit PNGs from disk | ❌ Inert — the combined method uses SeaSplat's harness throughout. |
| D-6, D-11, D-15 | `sh_degree` hard-coded to 0 at construction; internal table count inconsistency; three ablation structures called "ablation" | ⚠️ D-6 is *convergent* with SeaSplat's `sh_degree = 0` — both arrive at the same value for different reasons (M2 for densification-phase memory, SeaSplat because underwater colour is treated as view-independent). Harmless, and mildly corroborating. |

---

## 6.4 Inherited from M3 — CompGS-VQ

Full table: `../compact3d/11-paper-vs-repo-disagreements.md` (D-1 … D-8). Repo is one day
before the arXiv revision, so drift explains nothing. That folder also records an unusually
high **verified-correct** rate on the method itself (13 confirmed claims).

| Src # | Delta | Bites the combined method? |
|---|---|---|
| D-1 | ⭐ **Run-length encoding of sorted indices is not implemented.** The abstract and §3 both describe it ("reducing the storage from `n` integers to `k` integers"); `save_kmeans()` does plain bit-packing | ✅ **Yes.** One of the two storage mechanisms in the paper cannot be reproduced, so the achievable compression is below the published figure before any baseline difference is accounted for. |
| D-2 | ⭐ **`run.sh` ≠ the paper's configuration**: `st_iter` 15 000 vs 20 000, `kmeans_iters` 10 vs 1, `ncls` 4096 vs 16384/32768, `ncls_sh` 512 vs 4096 — and it requires a **two-stage workflow** (`--start_checkpoint` from a prior unquantized run) the paper never mentions | ✅ **Yes.** Every value must be chosen explicitly and reported. The two-stage workflow is also a hint that post-hoc quantization from a checkpoint is a supported path — relevant if quantization-aware training proves too short after the ordering fix. |
| D-4 | **Index bit-width bug**: `n_bits = ceil(log2(len(cls_ids)))` = `ceil(log2(N))`, not `ceil(log2(K_cb))`. For `N ≈ 10⁶` that is 20 bits where 12 suffice — `kmeans_inds.bin` ≈ **1.7× larger than necessary** | ✅ **Yes.** `[PI]` The combined method fixes it (`03-variables.md` §3.3), which means its compression ratio is **not** directly comparable to CompGS-VQ's published one. Declared in `11-paper-vs-repo-disagreements.md`. |
| D-3 | The paper's **assignment freeze at 25 K does not exist**; reassignment continues to 30 000 | ⚠️ Informational; harmless. |
| D-6 | CLI defaults **disable the method**: `--kmeans_st_iter` = 30 000 = `total_iterations`, `--lambda_reg = 0.`, `--opacity_reg = False`. A bare run trains plain 3DGS | ✅ **Yes, high trap value.** Assert that quantization fired. Note the `--opacity_reg = False` default happens to be what this work wants (`04-loss.md` §4.3). |
| D-5 | Opacity-reg window lower bound 15 000 is **hard-coded** in two places | ❌ Inert — the regulariser is disabled. |
| D-7 | No entropy coding of indices despite a non-uniform code distribution; both successors add it | ⚠️ Informational — an obvious, un-taken improvement. |
| D-8 | The "CompGS" name collision | ⚠️ Naming hygiene; handled in `00-index.md`. |

---

## 6.5 Combination-specific deltas — all `[proposed integration]`

These do not exist in any source. Each is a decision this work makes, with its justification
and its cost. They are the honest answer to "what did you actually build?"

| # | Decision | Why | Cost / risk |
|---|---|---|---|
| **CD-1** | **A feature-flag layer above SeaSplat's argument parser.** SeaSplat registers ~12 booleans that default `True` with `action="store_true"`, so they cannot be disabled from the CLI `[../seasplat/11-… D-12]`. A 2³ matrix requires toggling. The combined method adds an explicit config layer (a per-cell config file or `--set key=value` override) that writes the resolved values before `ModelParams` is constructed | otherwise the matrix cannot be run at all without editing source between cells, which is unreproducible | a config layer is one more place for a value to be silently wrong; every run must **dump its fully-resolved config** to the output directory |
| **CD-2** | **`num_refs ← min(num_refs, V)`** and report `V` per scene | `V` = 18–29 here; EDGS's default 180 exceeds the total view count, so pose k-means is asked for more clusters than points `[inferred from ../EDGS/11-… D-5 + dataset counts]` | EDGS's saturation analysis `[paper Fig. 6]` was measured with far more views; the operating point is off its measured curve, and this must be declared |
| **CD-3** | **Retain SeaSplat's `reset_opacity()` under M2**, contrary to Mini-Splatting's silent removal | opacity reset is a co-mechanism of `L_op` in suppressing water-column floaters (D-4); M2 removed it plausibly because *its* depth reinit already resets `o` every 5 000 iterations `[../mini-splatting/05-constraints.md M-7]` — but under the simplification-only scoping, reinit fires only twice, so the compensating mechanism is largely absent | deviates from Mini-Splatting-as-published; M2's numbers are not reproduced |
| **CD-4** | **Scope M2 to simplification only** (intersection preserving + importance-weighted stochastic sampling + CDF prune), leaving 3DGS's ADC for densification | depth reinit fails in depth-less regions and resamples preferentially toward low-`α` pixels — i.e. the water column, twice over `[../mini-splatting/05-constraints.md §5.3; 11-… D-2]` | M2 as tested is *not* Mini-Splatting; it is Mini-Splatting's simplification stage. This must be named as such throughout, or a reader will assume the full method |
| **CD-5** | **Replace `sampling_factor` with an explicit primitive budget** ⚠️ *the source of the budget is revised by CD-25 — it is fixed pre-campaign by the binding rule, not taken from A0* | makes the budget bind in every cell and removes the A4/A7 no-op degeneracy (`02-pipeline.md` §2.8); also makes "count" an independent variable rather than a ratio of a varying quantity | requires an A0 run before the matrix can be configured — a sequencing dependency in the experimental protocol |
| **CD-6** | **Medium-only re-warm-up burst after each simplification event** | required by the `Ẑ` rescale (`05-constraints.md` A2, `03-variables.md` IC-2). This is the single most substantive `[PI]` in the work | the burst length is unvalidated; it consumes wall-clock that does not appear in the iteration count; and it is itself a candidate for its own ablation |
| **CD-7** | ~~M2's rewind overrides M1's clamp~~ → **REVERSED 2026-08-28: the LR rewind is OFF by default.** M1's clamp stands alone; the rewind survives as `--m2_lr_rewind`, default `false` | The original reasoning was "after simplification the population is genuinely new, so the rewind's premise holds." Implementing CD-4 showed it is not: under simplification-only scoping **nothing is reinitialized** — the survivors keep their parameters *and* their Adam state, because 3DGS's `prune_points` index-selects the optimizer state rather than rebuilding it. Mini-Splatting's rewind exists so that freshly *reinitialized* primitives still have enough LR to move; with no reinitialization there is nothing for it to compensate for, and applying it would inject a correction for a condition that does not occur | none. This is strictly less intervention than the original decision. Retained as a flag because it is the natural sensitivity check `[implementation: arguments/__init__.py m2_lr_rewind; train.py LR block]` |
| **CD-8** | **Disable CompGS-VQ's ℓ1 opacity regulariser** | otherwise M2 and M3 are not independent factors (`04-loss.md` §4.3) | M3's numbers are not a reproduction of CompGS-VQ; its FPS gain in particular will be smaller, because CompGS-VQ's speedup came from that regulariser |
| **CD-9** | **Drop the SH codebook; three codebooks (dc, scale, rot)** | `f_rest` is empty under `sh_degree = 0` | the compression ceiling is structurally lower; ratios against CompGS-VQ's 59-float baseline are invalid (`01-taxonomy.md` A3-a) |
| **CD-10** | **`kmeans_st_iter > simp_iteration2`** | a codebook fitted before the prune is fitted to a population that is about to be discarded (`03-variables.md` IC-4) | leaves <10 000 iterations of quantization-aware training; `../OMG/` suggests 1 000 suffices, but that is a different quantizer |
| **CD-11** | **Fix the index bit-width to `ceil(log2(K_cb))`** | a 1.7× storage inflation is not a property worth reproducing `[../compact3d/11-… D-4]` | the reported size is no longer comparable to CompGS-VQ's published `Mem` column |
| **CD-12** | **Report `Ẑ_min`, `Ẑ_max`, and the nine medium scalars at every save iteration** | converts IC-2 and the medium-error-absorption hypothesis (`04-loss.md` §4.4) from assertions into measurements, at essentially zero cost | none; this is the cheapest high-value addition in the list |
| **CD-13** | ~~Port SeaSplat's depth pass onto the forked rasterizer~~ → **RESOLVED 2026-08-28 with no CUDA changes at all: a probe channel.** | The anticipated problem was the wrong one. The `_ms` fork *does* accept `colors_precomp`, so the depth pass composes fine; what it does not return is **alpha**, and SeaSplat needs a *differentiable* one because `L_op`'s gradient reaches opacity through alpha alone (`_ms`'s `render_depth()` exposes `accum_alpha` but is not an autograd `Function`). Since alpha compositing is per-channel and independent of the colour values, a probe colour `[z, 1, 0]` against a zero background makes channel 1 accumulate `Σ Tᵢaᵢ = 1 − Πᵢ(1−aᵢ) = α`, differentiable through the ordinary autograd path. SeaSplat already ran that depth pass **every iteration** reading only channel 0, so channels 1 and 2 were redundant | **none — this removed the largest schedule risk in the build.** Zero CUDA changes, and at the time zero extra passes (CD-23 later adds a third, for a reason CD-13 could not have seen), and behaviourally identical at the default configuration (`white_background` and `random_background` are both `False`, so the background is already zero). **Verified on real CUDA:** `Z_raw/α` recovers true depth to `0.00e+00` at opacities 0.3 and 0.7 and `2.38e-07` at 0.95 `[implementation/tools/verify_rasterizer.py T3, executed on sm_86]` |
| **CD-14** | **Keep `norm_depth_max = True` and `Z_raw/α` blended depth**, despite `05-constraints.md` §5.4 | changing either would make A0 ≠ SeaSplat-as-published and destroy the matrix's reference point | the baseline is fed a depth quantity a sibling method demonstrates to be unreliable in this regime. Declared as the top follow-up in `open-questions.md` |

> **Read CD-3, CD-4, CD-8 and CD-9 together.** Each one is a deviation from a source method
> *as published*. Cumulatively they mean **no cell of this matrix reproduces any source paper
> except A0.** That is the correct design — a factorial study needs independent factors, not
> faithful reproductions — but it must be stated plainly, because the alternative reading
> ("we ran EDGS, Mini-Splatting and CompGS-VQ on underwater data") is both more flattering
> and false.

---

## 6.6 Decisions that only emerged during implementation

CD-1 … CD-14 were derived from reading. The following were forced by *writing* the code, and
are recorded here so the specification and the implementation describe the same method.

| # | Decision | Why it was not foreseen | Cost / status |
|---|---|---|---|
| **CD-15** | **Correspondences are drawn from training views only.** The offline stage loads the scene with `eval=True` and iterates `train_cameras`; held-out frames are excluded and the count of excluded frames is written into the cloud's sidecar | The spec treated initialization as a preprocessing detail and never asked *which* views feed it. Using held-out frames would leak the test set into the model **through the geometry** — a leak no metric could reveal, because it arrives as structure rather than as supervision | none; strictly a correctness requirement. Verified in the sidecar (`test_views_excluded`) |
| **CD-16** | **Cheirality check alongside the reprojection filter**: a correspondence is kept only if the triangulated point lies in front of *both* cameras | The spec specified a reprojection-error filter, following EDGS. That is insufficient here: near-parallel view rays — common in a forward-facing capture — produce *confident* matches that triangulate behind a camera with small reprojection error. With densification disabled nothing downstream removes them | none. Tested: `verify_dense_init.py` T5 |
| **CD-17** | **k-means++ seeding and empty-cluster reseeding**, replacing the reference's uniform `randperm` initialization | The spec inherited the reference's initialization without examining it. It is a real defect, not a stylistic difference: two seeds can land in one dense region while another gets none, and Lloyd iterations cannot recover — a centroid straddling two clusters plus a wasted codeword, i.e. **higher quantization error at identical storage**, which is the quantity M3 is measured on | one-off `O(k·m)` on a capped subsample. Measured: worst-case error on the test fixture fell from **5.14 to 0.20**, a 25× reduction `[verify_quantize.py T1]` |
| **CD-18** | **Interrupted runs restart rather than resume.** The harness never passes `--start_checkpoint` | The spec assumed checkpoint/resume was available because `train.py` checkpoints the Gaussians and can restore them. It does not checkpoint the **medium model, the learned background, the codebooks, or the loop's schedule flags** — so resuming would silently reinitialise `β` and `B^∞` and produce a run that looks complete and is a different experiment | up to ~1.5 h of recomputation per killed session, which is far cheaper than one invisibly invalid cell. Correct resume requires that state in the checkpoint first; see `open-questions.md` OQ-17 |
| **CD-19** | **Both PSNR conventions computed and labelled at every evaluation**, and a real batch is *refused* rather than averaged | The spec said "report both", but assumed the inherited function had one fixed convention. It does not — see the correction in `09-glossary.md` §9.4 | none. Tested: `verify_metrics.py` T1–T7 |
| **CD-20** | **Effective optimizer steps counted at the top of the loop** and written into every `eval_metrics.json` | The spec required reporting them; nothing counted them. Every loop pass is exactly one optimizer step of some kind, so counting there is the quantity a timing comparison needs | none |
| **CD-21** | **`--model_path` is respected when given.** Upstream always derived it from the source path *and today's date* | Not visible from the source breakdowns. It breaks Drive-backed output, and the date makes the path change at midnight — so a re-attempted run would land somewhere new | none |

> **CD-15 and CD-18 are the two that would have produced invalid results silently.** CD-16 and
> CD-17 degrade quality without erroring. CD-19 through CD-21 are reporting correctness. None
> of the seven was reachable from the papers or from the source breakdowns alone; each needed
> the code to exist first. That is worth stating in the write-up, because it is the honest
> answer to "what did implementing it actually establish?"

---

## 6.7 Discovered by *running* it — CD-22 … CD-25

CD-15 … CD-21 were forced by writing the code. These four were forced by executing it, and
three of them corrected something that reading could not have caught: in each case the code
was doing exactly what it was written to do.

| # | Decision | Why it was invisible until execution | Cost |
|---|---|---|---|
| **CD-22** | **Share one `screenspace_points` buffer between the colour pass and the alpha probe**, so `α`'s gradient reaches density control | CD-13 solved alpha's *value* and never asked where its *gradient* went. SeaSplat reads `α` from the colour pass, so `α`-derived losses feed `add_densification_stats`; a probe with its own buffer silently removes that term. Every forward-output check passed throughout `[05-constraints.md §5.6]` | none in isolation — but see CD-23, which shows this fix alone is insufficient and slightly harmful |
| **CD-23** | **Give `α` its own `[0,1,0]` probe** and leave depth on a separate pass, so density control sees image + `α` and **not** depth | Sharing the combined `[z,1,0]` probe admits depth-loss gradients that SeaSplat's separate depth pass excludes. The two partially cancel: image-only gives 743 457 primitives, image+`α`+depth gives **635 038** — *worse* than not fixing it — and image+`α` reproduces vanilla's 4.46M. That ordering is not derivable from the source; it had to be measured `[measured n=1 each]` | **a third rasterization per iteration.** Falls on every cell equally, so it cancels in every between-cell contrast, but it is visible in absolute wall-clock and wall-clock is a reported result. Behind `separate_alpha_probe`, recorded in every manifest |
| **CD-24** | **Measure rendering throughput and peak render memory**, over the held-out views, colour pass only, CUDA-synchronised, after discarded warm-up frames | The methodology chapter asserted frame rate "is measured"; nothing measured it. Two stated predictions — that A3 shows ≈no frame-rate gain, and that gains from count reduction are sub-linear — had no instrument behind them. Adding the instrument was also not enough: `analyse.py`'s default metric list omitted it, so the contrasts that actually run would still have skipped it | ~1 s per 78-minute run. **An instrument is not finished until something reads it** |
| **CD-25** | **`n_bud` fixed pre-campaign by a binding rule**, replacing CD-5's "set from A0's converged count" | A0's median is 2 482 200, so any fraction of it exceeds every M1 cloud (299 368 – 471 531) and M2 would be inert under M1 — A4 ≡ A1, A7 ≡ A5, read as a null interaction. The rule is: `n_bud` below the smallest count any other enabled mechanism produces. It also removes S1 as a hard prerequisite for S2 | none. Preflight enforces it from the cloud's PLY header and has already rejected one wrong value `[repo: utils/preflight.py]` |

> **CD-22 and CD-23 are the two that mattered**, and they are a matched pair: CD-22 alone
> makes the result *worse* than leaving the defect in place. Neither was reachable from the
> papers, the source breakdowns, or this document's own analysis — the first evidence of a
> problem was A0 failing to reproduce SeaSplat's primitive count, and the mechanism was
> located only by instrumenting both implementations and comparing them event by event.
>
> The honest summary for the write-up: **implementing it established that a composed method
> has properties at its seams that belong to neither component, and that some of them are
> invisible to any check on returned values.** `05-constraints.md` §5.6 states the invariant
> that now guards this one.

---

## 6.8 CD-26 — a parallax filter the source method does not have

*Extends §6.7. Recorded separately because it is a deviation from EDGS **as
published**, not merely from its undocumented behaviour.*

### What was added

Triangulations are rejected when the angle at the point between the two view
rays falls below `min_parallax_deg` (default **1.0°**)
`[repo: source/roma_init.py]`. The test is the **conditioning of the estimate**,
not the distance of the result, so it needs no per-scene constant.

### EDGS names this degeneracy and does not fix it

Its **D-2** states the failure exactly `[../EDGS/05-constraints.md:40]`:

> *"When the two view rays are nearly parallel (small baseline) or nearly
> collinear with the point, `A` is ill-conditioned and the least-squares
> solution is unstable in depth — **arbitrarily far, arbitrarily wrong**. Dense
> matchers happily return matches for such pairs."*

EDGS ships two filters, both of which this implementation already had:
`p^corr` on matcher confidence, and `p^proj` on reprojection error. **Neither
measures ray geometry**, and D-2 is assigned to `p^proj`.

**`p^proj` cannot detect D-2.** A near-parallel pair yields a point lying on
both rays, so it reprojects close to both original pixels. The error is small
*because* the geometry is ill-conditioned. `p^proj` addresses D-4 — confident
hallucinations that happen to triangulate — which is a different failure.

Measured on a synthetic pair with a 10 cm baseline and 0.5 px of matcher noise,
2000 realisations:

| parallax | true depth | recovered, median | 5th–95th | behind a camera |
|---:|---:|---:|---|---:|
| 1.91° | 3.0 | 3.0 | 2.8 – 3.2 | 0.0% |
| **0.0014°** | **4 000** | **3.1** | **−129 – +115** | **48.6%** |

The depth is not *far*; it is **undetermined**, and the recovered value bears no
relation to the truth. Cheirality removes 48.6% of such points by accident; the
remainder pass every filter and land wherever the noise puts them.

### Why it does not bite EDGS

`num_refs = 180`. With dense viewpoint coverage most pairs have healthy
parallax, so the unfixed degeneracy is rare enough for the `α < 0.005` prune to
absorb. **This corpus has 15–25 training views**, so `K_ref = min(180, V)`
collapses to the view count and near-collinear pairs become common. The same
view-count constraint drives the initialization deficit in §13.12.

### The measured consequence of omitting it

`A1/Curasao/s0` `[measured n=1]`:

- bounding box **38 895 × 31 415 × 156 172**, maximum radius **23 863×** the
  median, and the distant material is **rendered**, not low-opacity;
- rendered `z_max` reached **122 673** against a baseline of roughly 50;
- per-frame depth normalisation therefore compressed the scene into
  `Ẑ ∈ [0, 0.0007]`, so `Â = exp(−β_att·Ẑ) ≈ 1` for any β;
- **both red and blue attenuation channels ended clamped dead.**

This is §5.4's mechanism reached by primitive *placement* rather than primitive
*reduction*.

### Measured on this corpus `[measured n=1 per scene]`

Regenerating all four clouds with the filter active:

| scene | views | triangulated | **parallax-rejected** | `p^proj` + cheirality | kept |
|---|---:|---:|---:|---:|---:|
| Curasao | 18 | 360 000 | **66 438** (18.5%) | 855 | 292 707 |
| IUI3-RedSea | 25 | 500 000 | **194 802** (39.0%) | 16 589 | 288 609 |
| JapaneseGardens | 17 | 340 000 | **43 879** (12.9%) | 2 479 | 293 642 |
| Panama | 15 | 300 000 | **55 530** (18.5%) | 273 | 244 197 |

**EDGS's two filters together removed 20 196 of 1 500 000 triangulations —
1.3%. The parallax filter removed 360 649 — 24.0%, which is 95% of all
rejections.** Between 13.1% and 41.3% of each previously-accepted cloud was
ill-conditioned geometry.

This does not merely show that filtering helps. It shows that on this corpus the
filters EDGS ships were doing almost nothing, while the degeneracy they are
assigned to catch accounted for a quarter of everything triangulated.

**The scene that lost most has the most views**, which inverts the naive
expectation. The cause is the pairing rule rather than the view count: each
reference is matched against its *nearest* views by pose distance, and nearest
means smallest baseline, which means worst parallax. EDGS's neighbour selection
systematically chooses the worst-conditioned pairs available, and how badly that
bites depends on capture geometry — IUI3-RedSea's 29 frames along a reef wall
put consecutive views nearly on top of one another. **The pairing heuristic and
the missing filter interact, and neither alone explains 41%.**

### Effect on the budget

The clouds shrank and also became more uniform — a 1.58× spread across scenes
before, 1.20× after, which is what a conditioning-based filter should do.

`n_bud = 200 000` still binds on every scene and still clears preflight's 90%
warning, but the margin narrowed on the binding scene: Panama went from 66.8% to
**81.9%** of its cloud, so M2 now removes 18.1% of the M1 population there rather
than 33%. That is the lever the A4 and A7 interactions have to work with, and it
is smaller than it was.

### Cost and status

**M1's results are not a reproduction of EDGS**, and that was already true — M2
omits its densification half, M3 disables its opacity regulariser. CD-26 adds a
third such deviation and it is the only one that corrects a defect in a
published method rather than adapting one.

Requires regenerating every dense cloud and re-running every M1 cell. Guarded by
`verify_dense_init.py` **T8**, which asserts both halves: that the filter
rejects the ill-conditioned pair, **and that the existing filters accept it** —
so the reason for the deviation is encoded in a test rather than described in a
comment.
