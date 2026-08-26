# §6 — Implementation deltas from the paper

**Repo state inspected:** `github.com/fatPeter/mini-splatting`, commit
`c0d55811930dec3bfd3d61cad927093d166aaf82`, branch `main`, 2024-10-12. No tags.

**Paper version:** arXiv:2403.14166**v3**, 16 Oct 2024 — only 4 days after the commit, so
paper and code are unusually well-aligned in time. Deltas below are therefore unlikely to
be revision drift.

**Files read directly:** `ms/train.py`, `ms_d/train.py`, `gs/train.py`, `ms_c/run.py`,
`scene/gaussian_model.py`, `scene/dataset_readers.py`, `gaussian_renderer/__init__.py`,
`arguments/__init__.py`, `utils/general_utils.py`, `utils/image_utils.py`, `README.md`.
The README was used only for the documented training commands.

---

## D-1 — **Opacity reset is entirely removed**, and the paper never says so

`grep -c "reset_opacity"`:

| File | Count |
|---|---|
| `ms/train.py` | **0** |
| `ms_d/train.py` | **0** |
| `gs/train.py` (vanilla baseline in the same repo) | **1** |

3DGS resets every Gaussian's opacity to a low value every `opacity_reset_interval = 3000`
iterations — its principal mechanism for killing floaters and freeing capacity. Both
Mini-Splatting variants delete it. The parameter survives only as a magic number in the
screen-size gate: `size_threshold = 20 if iteration > opt.opacity_reset_interval else None`
`[repo: ms/train.py:155; arguments/__init__.py:85]`.

**Plausible reason** (mine, not the paper's): depth reinitialization resets `o` to
`inverse_sigmoid(0.1)` for *every* Gaussian every 5 000 iterations
`[repo: scene/gaussian_model.py:475]`, subsuming the periodic reset. `[inferred]`

**Severity: high.** Removing a core component of the named base method, unremarked, means
the `3DGS*` baseline and Mini-Splatting differ in a way not attributable to the paper's
stated contributions.

---

## D-2 — Depth-reinit point sampling is **importance-weighted**, not random

`[paper §4.1]`:
> "For each image, we **randomly select** a certain number of points as initial points and
> assign the ground truth colors as their corresponding colors."

`[repo: ms/train.py:174-190]`:
```python
accum_alpha = render_depth_pkg["accum_alpha"]
prob = 1 - accum_alpha              # ← weight by INVERSE accumulated opacity
prob = prob / prob.sum()
...
indices = np.random.choice(N_xyz, size=num_sampled, p=prob, replace=False)
```

Pixels are sampled with probability proportional to `1 − α_accum`, i.e. **biased toward
low-opacity, poorly-reconstructed pixels**. This is a targeted "spend new Gaussians where
the model is weak" heuristic, not uniform sampling — and it is arguably the most
consequential single line in the depth-reinitialization mechanism.

**Severity: high.** A reimplementation following §4.1 literally would sample uniformly and
get a different algorithm.

---

## D-3 — `--num_max` (4.5 M) hard cap on `N` during densification

`[repo: ms/train.py:153]`:
```python
if iteration > opt.densify_from_iter and iteration % opt.densification_interval == 0 \
   and iteration % 5000 != 0 and gaussians._xyz.shape[0] < args.num_max:
```
with `--num_max` defaulting to `4_500_000` `[repo: ms/train.py:406]`.

Densification simply stops once the cap is hit. Not in the paper. **Absent from `ms_d/`**
`[repo: ms_d/train.py:133]`, which is consistent with Mini-Splatting-D reporting 4.69 M and
5.40 M Gaussians — above the cap that constrains `ms/`.

**Severity: medium.** It bounds the very quantity the paper is about.

---

## D-4 — `--sampling_factor = 0.5` and the CDF threshold `0.99` are undocumented

- `[repo: ms/train.py:407]` — `--sampling_factor` default `0.5`; used as
  `num_sampled = int(N · factor · (|{P≠0}|/N))` `[repo: ms/train.py:237-239]`, i.e. keep
  half of the *intersecting* Gaussians. This is the knob that generates the
  number-quality curve of `[paper Fig. 7]`, and its operating point is never stated.
- `[repo: ms/train.py:282]` — `init_cdf_mask(imp_score, thres=0.99)`: sort importance
  ascending, cumulative-sum, and drop the Gaussians that together account for the bottom
  **1%** of total importance mass `[repo: ms/train.py:31-44]`.
  `[paper Alg. 1:21]` says only "`Pruning()` ▷ Directly Prune a Few Gaussians".

**Severity: medium** — the headline "7× fewer Gaussians" number is a direct function of
these two constants.

---

## D-5 — The LR schedule is **rewound** after simplification

`[repo: ms/train.py:96-99]`:
```python
if iteration < simp_iteration1: gaussians.update_learning_rate(iteration)
else:                           gaussians.update_learning_rate(iteration - simp_iteration1 + 5000)
```
At `simp_iteration1 = 15 000`, the position learning rate jumps back to its value at step
5 000 and re-decays over the remaining 15 000 iterations. Without this the reinitialized
Gaussians would be born into a nearly-decayed schedule and could not move.

Not in the paper. Present in `ms_d/` too, keyed on `densify_until_iter`
`[repo: ms_d/train.py:76-79]`.

**Severity: medium.**

---

## D-6 — `sh_degree` is hard-coded to 0 at construction, ignoring the CLI

`[repo: ms/train.py:56]`: `gaussians = GaussianModel(sh_degree=0)` — the `--sh_degree`
argument (`ModelParams.sh_degree = 3` `[repo: arguments/__init__.py:49]`) is not passed. It
is read back later only to *raise* the cap: `gaussians.max_sh_degree = dataset.sh_degree`
`[repo: ms/train.py:250]`.

Consistent with `[paper §5]` in effect, but it means `--sh_degree 2` (say) would have no
influence on the first 15 000 iterations. A repo-reading trap rather than a contradiction.

**Severity: low.**

---

## D-7 — `reinitial_pts` resets far more than the paper implies

`[paper §4.1]` describes depth reinitialization as reinitializing "our Gaussian
representation with these points". `[repo: scene/gaussian_model.py:460-483]` shows it also:

- sets `f_rest` to **0** (all higher-order SH discarded) — line 466;
- recomputes `s` from `distCUDA2` kNN — lines 470-471;
- resets `q` to identity — lines 472-473;
- resets `o` to `inverse_sigmoid(0.1)` — line 475;

and the caller then runs `gaussians.training_setup(opt)`, **discarding all Adam moment
state** `[repo: ms/train.py:204, 254, 285]`.

At default settings the representation is fully restarted **five times** (5 K, 10 K,
15 K sampling, 15 K reinit, 20 K prune). `[inferred: repo ms/train.py:164, 203-204, 251-254, 285]`

**Severity: medium** — the word "reinitialize" undersells a complete restart.

---

## D-8 — "Intersection preserving" has no corresponding function

`[paper Alg. 1:15, 20]` lists `Intersection()` as a distinct call. The implementation folds
Eq. 3 into one line, `imp_score[accum_area_max == 0] = 0` `[repo: ms/train.py:232, 281]`,
which zeroes the sampling probability of Gaussians that are never the argmax anywhere.

Mathematically equivalent; structurally invisible. Worth recording because a reader
grepping for the mechanism will conclude it is missing.

**Severity: cosmetic**, high trap value.

---

## D-9 — `ms/` and `ms_d/` sample depth points differently

| | `ms/` | `ms_d/` |
|---|---|---|
| Call | `np.random.choice(N, n, p=prob, replace=False)` | `np.random.choice(N, n, p=prob)` then `np.unique(indices)` |
| Effect | exactly `n` distinct points | **fewer than `n`** distinct points (collisions collapse) |
| Source | `[repo: ms/train.py:189-190]` | `[repo: ms_d/train.py:169-170]` |

Sampling with replacement then deduplicating yields, in expectation, `N(1 − (1−1/N)^n)`
unique points under a uniform prior — and materially fewer under the skewed `1 − α`
prior. So Mini-Splatting-D's effective `num_depth` is **below** the stated 3.5 M.
`[inferred]` The paper describes one procedure for both variants `[paper §4.1, App. F]`.

**Severity: medium for reproduction** of the D-variant's Gaussian counts.

---

## D-10 — Mini-Splatting-C silently deduplicates Gaussians by voxel

`[repo: ms_c/run.py:141-149]`:
```python
pos_voxlized = round( (pos - pos.min())/(pos.max() - pos.min()) * (2**16 - 1) )
pos_voxlized, pos_idx = np.unique(pos_voxlized..., axis=0, return_index=True)
pos_remain = pos[pos_idx];  rgb = rgb[pos_idx];  feat = feat[pos_idx]
```

Any Gaussians colliding in the 65 536³ grid are **dropped** — only the first survivor's
attributes are kept. `[paper App. F]` describes only voxelization for RAHT, transform
coding at depth 16 / `Qstep` 0.02, and zip. The count reduction from deduplication is
folded into the reported file size.

Also note `num_g = pos.shape[0]` is computed **before** the dedup `[repo: ms_c/run.py:153]`
and used to reshape `feat`, which is then indexed by `pos_idx` — correct, but easy to
misread.

**Severity: medium** for any rate-distortion comparison against `compact3d/` or `CompGS/`.

---

## D-11 — Table 3's final row does not equal Mini-Splatting-D

`[paper Tab. 3]` "+ Depth Reinit" reports **4.32 M** Gaussians and SSIM/PSNR/LPIPS of
0.832 / 27.54 / 0.175. `[paper Tab. 1]` Mini-Splatting-D reports **4.69 M** and
0.831 / 27.51 / 0.176. `[paper Tab. 4]` "Mid" reports **4.69 M** and 0.832 / 27.54 / 0.175
— i.e. Table 4's "Mid" matches Table 3's metrics but Table 1's count.

The three tables are mutually inconsistent on `Num` for what should be the same
configuration, and the paper offers no explanation.

**Severity: low** (metrics agree; only the count differs), but worth a footnote if you cite
Gaussian counts. `[inferred: comparing paper Tab. 1, 3, 4]`

---

## D-12 — Fixed seed 0, but `np.random.choice` makes it insufficient

`[repo: utils/general_utils.py:130-132]`: `random.seed(0)`, `np.random.seed(0)`,
`torch.manual_seed(0)` — hard-coded, no CLI override, **no `torch.cuda.manual_seed_all`**.

Unlike `seasplat/` (seed `-1` by default) this is deterministic-by-intent. But
Mini-Splatting's two most important steps are **stochastic** (`np.random.choice` at
`[repo: ms/train.py:189, 240]`), so run-to-run variance is structurally higher here than in
a deterministic pipeline even with the seed fixed, once CUDA non-determinism perturbs the
importance scores that feed the sampler. See [`10-reproducibility.md`](10-reproducibility.md).

**Severity: medium.**

---

## Items I could *not* verify in this pass

| Claim | Status |
|---|---|
| Exact CUDA implementation of `accum_max_count`, `out_pts`, `accum_alpha` | `[unverified]` — these come from the forked `diff_gaussian_rasterization_ms` submodule; I read the Python call sites `[repo: gaussian_renderer/__init__.py:173, 189-191]` but not the `.cu` kernels. |
| Whether `out_pts` uses the mid-point or the center formulation in the shipped kernel | `[unverified]` — `[paper §6.2]` says the main pipeline uses `Mid`, and Table 4 lists both; the Python side just receives `out_pts`. |
| Numeric values behind `[paper Fig. 7]`, `Fig. 10`, `Fig. 14` | `[unverified]` — published only as plots. |
| Which `--sampling_factor` produced each point of the Fig. 7 curve | `[unverified]`. |
| Whether the reported timings used the `num_max` cap | `[unverified]` — the cap exists only in `ms/`, and Table 2's Mini-Splatting counts (0.57 M / 0.40 M) are far below it, so it likely never bound in those runs. `[inferred]` |
