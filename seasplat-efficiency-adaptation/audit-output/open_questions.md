# Open questions

Things this audit could not resolve from the repository, ordered by how much they change the
conclusions. Q-3 through Q-6 all trace back to the same root cause: **`docs/ablation_design.md`,
`docs/experiment_plan.md` and `docs/reproducibility_notes.md` exist but are all 0 bytes.**

---

## 🔴 Q-3 — What `seathru_from_iter` value was actually used?

`self.seathru_from_iter = 9_000_000` `[repo: arguments/__init__.py:179]`, i.e. **larger than
the 30 000-iteration run, so the medium model is disabled unless the flag is passed on the
CLI.** This is the same "defaults disable the method" trap catalogued for compact3d
`[my-research/compact3d/…/11-paper-vs-repo-disagreements.md, D-6]`.

Nothing in the repo records the value. Every timing claim in this audit assumes the SeaSplat
README recipe value of **10 000**.

**Why it matters most.** If the flag was omitted, `L_gw`, `L_sat`, `L_bs`, `L_Z-recon` and the
medium parameters `β^D`, `β^B`, `B^∞` never activate — and then:

- A2's favourable interaction with `L_op` (`a2.md` A2-3) does not exist;
- the compounding risk in A5/A7 (`a1_a3.md` C5-1) is much reduced;
- **none of the eight branches is a study of underwater rendering** — they are variants of
  plain 3DGS, and the thesis's framing does not hold.

Binary, cheap to check, and it gates everything else.

## 🔴 Q-4 — How many points does `roma_init.py` actually produce (`N_init`)?

Controlled by `voxel = 0.001`, `matches = 5000`, `nns = 3`, `num_refs = -1`, `certainty = 0.02`.
Recorded nowhere; the output `.ply` is unversioned and unhashed.

With densification disabled, `N` can never grow — so `N_init` alone decides whether A2's
800 000 budget ever binds on the A1-derived branches. **If `N_init ≤ 800 000`, then
`A4 ≡ A1` and `A7 ≡ A5`, and two of the eight factorial cells do not exist**
(`a1_a2.md` C4-1, `a1_a2_a3.md` C7-1).

## 🔴 Q-5 — Does `max_gaussians = 800 000` ever bind on ordinary densified runs?

Same question for A2 and A6, where densification is enabled. SeaSplat never reports Gaussian
counts `[my-research/seasplat/…/08-computational-profile.md]`, so there is no published figure
to compare against.

`reorganize_gaussians` returns `0` early when under budget, and the `[A2] Reorg @ iter …` log
fires **only when `n_pruned > 0`** — so an empty log is ambiguous between "under budget" and
"never ran." If the budget never binds, A2 ≡ A0 and A6 ≡ A3, collapsing the factorial further.

Q-4 and Q-5 are both answered by one unconditional log line and **no retraining**
(`refit_recommendations.md` R-1).

## 🟡 Q-6 — Have these branches been run, and where are the results?

**No result artifacts exist in this repository.** The working tree is clean, there are no
`output/`, `results/`, `eval/` or `logs/` directories, and no `.ply`, `.npz`, `.pth`, `.json`
or `.csv` file has ever been added in the history of any branch.

If the runs happened on a cluster, the numbers, run commands and dense `.ply` files live
somewhere this audit cannot see. **If they have not happened yet, that is the good case** —
every cheap fix in `refit_recommendations.md` R-1…R-9 can be applied before any GPU time is
spent, and R-2 (remove `'opacity'` from `to_quantize`) costs nothing at all if applied now.

Also unrecorded: the dataset and scenes, the train/test split, `--resolution`, and whether
`--eval` was passed. `--eval` defaults to `False` `[repo: arguments/__init__.py:56]`, which
produces no `test/` directory for `metrics.py` to read — so any existing numbers imply it
*was* passed, but the value is not written down anywhere.

---

## 🟡 Q-7 — Design intent, unrecoverable from the code

Because the three `docs/` files are empty, this audit could establish deviation from the
**published** source methods but not from what the author intended. Four decisions look like
deviations but might be deliberate choices with reasons that were simply never written down:

| Decision | The question |
|---|---|
| `opacity` is in `to_quantize`, which compact3d explicitly excludes `[compact3d §3]` | Deliberate, or copied from a generic VQ example? |
| `k = 256` vs compact3d's 4096–32768 | A memory target, or a placeholder? |
| `quant_k` / `quant_group_size` / `quant_xyz` added to `arguments/__init__.py` but **read by nothing** | Was A3 meant to run in-loop (quantization-aware) and left unfinished, or was post-hoc always the plan and the params are leftovers? |
| A2's docstring cites Mini-Splatting, but `opacity × scale` is not its metric | Was the blending-weight metric considered and rejected on cost grounds, or was the citation aspirational? |

The last one matters most for the write-up: **the honest framing of A2 is stronger than the
borrowed one** (see `refit_recommendations.md` R-8), but only the author can say which was
intended.

## 🟡 Q-8 — Is `800 000` a principled budget?

It appears as a bare literal with no derivation. Mini-Splatting has no fixed budget — it
derives a count from its sampling procedure. Whether 800 000 comes from a VRAM limit, a
target model size, or a round number is not recorded, and it determines the outcome of four
branches.

---

## 🟢 Q-1 — Output path

The prompt specified `./seasplat-efficiency-adaptation/audit-output/`. The audited repo is at
`BINUS/Thesis/seasplat-efficient-3dgs-underwater`, while the session working directory is
`BINUS/my-research` — **neither matches the given path.**

Resolved relative to the working directory, so this audit sits at
`my-research/seasplat-efficiency-adaptation/audit-output/`, alongside the nine method
breakdowns it cites throughout. Move it into the Thesis repo if it should be version-
controlled with the code it audits.

## 🟢 Q-2 — Branch-name case discrepancy

The working tree was checked out on `feature/A1-deterministic-init` (capital A) while
`git branch -a` lists `feature/a1-deterministic-init` (lowercase) — Windows' case-insensitive
filesystem resolving one ref two ways. Harmless locally, but **it will produce two distinct
refs on the Linux side of a push**, and checkout scripts written with one casing will fail on
the other. Worth normalizing before pushing to `origin`.

---

## Not attempted in this pass

| | Why |
|---|---|
| Executing any branch | No GPU run was performed; all findings are static analysis of code + diffs against the source-method breakdowns. |
| Verifying `roma_init.py`'s triangulation maths line by line | Read for parameters and API usage, not audited for geometric correctness. |
| Checking `origin` for branches not present locally | `git branch -a` was read from the local clone; a branch pushed but never fetched would not appear. All eight expected arms resolved, so no gap was indicated. |
| Confirming EDGS/Mini-Splatting/compact3d line numbers against their upstream repos | Cited from `my-research/<method>/research-methodology-output/`, which recorded them with commit hashes at the time of that analysis. |
