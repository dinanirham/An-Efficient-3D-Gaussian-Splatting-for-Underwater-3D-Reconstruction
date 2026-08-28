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
| **CD-5** | **Replace `sampling_factor` with an explicit primitive budget**, set from A0's converged count | makes the budget bind in every cell and removes the A4/A7 no-op degeneracy (`02-pipeline.md` §2.8); also makes "count" an independent variable rather than a ratio of a varying quantity | requires an A0 run before the matrix can be configured — a sequencing dependency in the experimental protocol |
| **CD-6** | **Medium-only re-warm-up burst after each simplification event** | required by the `Ẑ` rescale (`05-constraints.md` A2, `03-variables.md` IC-2). This is the single most substantive `[PI]` in the work | the burst length is unvalidated; it consumes wall-clock that does not appear in the iteration count; and it is itself a candidate for its own ablation |
| **CD-7** | **LR precedence: M2's rewind overrides M1's clamp from `simp_iteration1` onward** | the two have contradictory intents and both default on (IC-3). After simplification the population genuinely is new, so the rewind's premise holds and the clamp's does not | arbitrary in the sense that no source supports it; an equally defensible alternative is to disable `max_lr` entirely under A4/A7 |
| **CD-8** | **Disable CompGS-VQ's ℓ1 opacity regulariser** | otherwise M2 and M3 are not independent factors (`04-loss.md` §4.3) | M3's numbers are not a reproduction of CompGS-VQ; its FPS gain in particular will be smaller, because CompGS-VQ's speedup came from that regulariser |
| **CD-9** | **Drop the SH codebook; three codebooks (dc, scale, rot)** | `f_rest` is empty under `sh_degree = 0` | the compression ceiling is structurally lower; ratios against CompGS-VQ's 59-float baseline are invalid (`01-taxonomy.md` A3-a) |
| **CD-10** | **`kmeans_st_iter > simp_iteration2`** | a codebook fitted before the prune is fitted to a population that is about to be discarded (`03-variables.md` IC-4) | leaves <10 000 iterations of quantization-aware training; `../OMG/` suggests 1 000 suffices, but that is a different quantizer |
| **CD-11** | **Fix the index bit-width to `ceil(log2(K_cb))`** | a 1.7× storage inflation is not a property worth reproducing `[../compact3d/11-… D-4]` | the reported size is no longer comparable to CompGS-VQ's published `Mem` column |
| **CD-12** | **Report `Ẑ_min`, `Ẑ_max`, and the nine medium scalars at every save iteration** | converts IC-2 and the medium-error-absorption hypothesis (`04-loss.md` §4.4) from assertions into measurements, at essentially zero cost | none; this is the cheapest high-value addition in the list |
| **CD-13** | **Port SeaSplat's depth pass onto Mini-Splatting's forked rasterizer**, rather than the reverse | SeaSplat's addition is a Python-level second call with an overridden colour; Mini-Splatting's additions are inside the CUDA kernel `[../seasplat/02-pipeline.md; ../mini-splatting/08-… §8.4]` | one CUDA extension must be built and validated against both methods' expectations; it must also be rebuilt for the target GPU architecture in any case |
| **CD-14** | **Keep `norm_depth_max = True` and `Z_raw/α` blended depth**, despite `05-constraints.md` §5.4 | changing either would make A0 ≠ SeaSplat-as-published and destroy the matrix's reference point | the baseline is fed a depth quantity a sibling method demonstrates to be unreliable in this regime. Declared as the top follow-up in `open-questions.md` |

> **Read CD-3, CD-4, CD-8 and CD-9 together.** Each one is a deviation from a source method
> *as published*. Cumulatively they mean **no cell of this matrix reproduces any source paper
> except A0.** That is the correct design — a factorial study needs independent factors, not
> faithful reproductions — but it must be stated plainly, because the alternative reading
> ("we ran EDGS, Mini-Splatting and CompGS-VQ on underwater data") is both more flattering
> and false.
