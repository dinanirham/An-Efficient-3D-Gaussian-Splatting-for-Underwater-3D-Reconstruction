# §10 — Reproducibility checklist

## 10.1 Seed handling — ⚠️ **no seeding anywhere**

`grep -rn "manual_seed\|np.random.seed\|random.seed"` over `romatch/` and `experiments/`
returns **nothing**. There is no `set_seed` helper, no `--seed` argument, and no seeding in
`experiments/train_roma_outdoor.py`.

| Item | RoMa | `../RoMaV2/` | `../EDGS/` | `../CompGS/` |
|---|---|---|---|---|
| Seeds set | ❌ **none** | n/a (inference only) | ✅ 228 | ✅ 3407 |
| `torch.cuda.manual_seed_all` | ❌ | n/a | ✅ | ✅ |
| Seed in paper | ❌ | ❌ | ❌ | ❌ |

Sources of run-to-run variation that a seed would have to control: dataset pair sampling
(`WeightedRandomSampler` over `mega_ws` `[repo: train_roma_outdoor.py:236-237]`), horizontal-flip
augmentation and `shake_t=32` jitter `[repo: train_roma_outdoor.py:199-206]`, DDP shard order,
and AMP `float16` non-determinism.

**Consequence:** Table 2's ablation margins — several of which are **0.1** in 100-PCK@1px
(Setup IV vs V: 14.4 → 14.3) — have no dispersion and no way to obtain it without patching the
training script.

## 10.2 Train/test split

| Item | Value | Source |
|---|---|---|
| Outdoor training set | **MegaDepth**, `train_loftr` split, with `loftr_ignore=True`, `imc21_ignore=True` (i.e. LoFTR's and IMC21's test scenes excluded) | `[repo: train_roma_outdoor.py:197]` |
| ⚠️ Construction | built **twice and concatenated**: `min_overlap=0.01` **and** `min_overlap=0.35` | `[repo: train_roma_outdoor.py:201-210]` — **not in the paper** |
| Scene weighting | `mega.weight_scenes(megadepth_train, alpha=0.75)` | `[repo: train_roma_outdoor.py:212]` — **not in the paper** |
| Indoor model | separate script, ScanNet-trained | `[paper §4.2]` `[repo: experiments/roma_indoor.py]` |
| Which model per benchmark | "use a model trained on the **ScanNet** training set when evaluating on ScanNet-1500. **All other evaluation is done on a model trained only on MegaDepth**" | `[paper §4.2]` ✅ clearly stated |
| Ablation validation set | "random pairs from the MegaDepth scenes **[0015, 0022]** with overlap > 0" | `[paper §4.1]` ✅ specified |
| Ablation resolution | **448 × 448**; final model **560 × 560** | `[paper §4.2]` = `[repo: train_roma_outdoor.py:23, 301]` ✅ |

**The split discipline is good** — test-scene exclusion is enforced in code via the
`loftr_ignore` / `imc21_ignore` flags, and the paper states which model is used for which
benchmark. This is better documented than most folders in your set.

⚠️ But the **two-way `min_overlap` concatenation** is a real methodological choice (an
easy/hard curriculum mixture) that appears only in code.

## 10.3 Exact metric computation

RoMa reports **matching** and **pose** metrics, not PSNR/SSIM/LPIPS, so it is not directly
comparable to the radiance-field folders.

| Metric | Definition | Where |
|---|---|---|
| **AUC@{5,10,20}** | Area under the pose-error curve at 5°/10°/20° | `[paper Tabs. 5, 6, 7]` |
| **mAA@10 / @10px** | mean average accuracy — IMC2022, WxBS | `[paper Tabs. 3, 4]` |
| **EPE** | End-point error, at a **standardized 448×448** | `[paper §3.2]` |
| **Robustness %** | ⭐ % of matches with error **< 32 px**. Deliberately loose, and the paper explains why: "while these matches are not necessarily accurate, it is typically **sufficient for the refinement stage** to produce a correct adjustment" | `[paper §3.2]` |
| **100−PCK@{1,3,5}px** | **Lower is better** — Table 2 only | `[paper §4.1]` |
| InLoc | % localized within 0.25/0.5/1.0 m and 2/5/10° | `[paper Tab. 8]` |

⚠️ **Table 2's metric is inverted relative to every other table in the paper.** It reports
`100−PCK`, so smaller numbers are better. Easy to misread when quoting.

**Sampling protocol** `[paper §4.3]`: "We follow DKM [17] and sample correspondences using a
**balanced sampling** approach, producing **10,000 matches**, which are then used for
estimation." Confirmed: `sample_mode = "threshold_balanced"`, `sample_thresh = 0.05`
`[repo: roma_models.py:54-55]`.

**Benchmark harnesses ship** — 5 of them `[repo: romatch/benchmarks/]`:
`megadepth_pose_estimation_benchmark.py` (+ a `_poselib` variant),
`megadepth_dense_benchmark.py`, `scannet_benchmark.py`,
`hpatches_sequences_homog_benchmark.py`. Plus `experiments/eval_roma_outdoor.py` and tests
`[repo: tests/test_mega1500.py, test_mega_dense.py, ...]`.

⚠️ **No WxBS or IMC2022 harness ships** — the two benchmarks carrying the paper's headline
+36% and +5% results. `[unverified]`

## 10.4 Stated non-determinism

**None stated.** No seeds, repeats or error bars anywhere.

Margins that would need them:
- Table 2, Setup IV vs V: **0.1** at 1px (14.4 → 14.3) — the DINOv2 row, which the paper
  nonetheless calls "a significant improvement" `[paper §4.1]`. It *is* significant at 3px
  (5.4 → 4.6) and 5px (4.1 → 3.2); at 1px it is noise.
- Table 5, MegaDepth-1500 AUC@5: RoMa 62.6 vs PMatch 61.4 — **1.2**.
- Table 7, MegaDepth-8-Scenes AUC@5: RoMa 62.2 vs DKM 60.5 — **1.7**.

The **robust** results are Table 4 (**WxBS +21.2 mAA**, 58.9 → 80.1) and Table 3
(**IMC2022 +4.2 mAA**). Cite those.

## 10.5 Reproduction checklist for your cluster

| # | Action | Why |
|---|---|---|
| 1 | **Use the released weights.** Retraining is 250k steps at batch 32 across (implied) 4 GPUs `[repo: train_roma_outdoor.py:190-193]` — a multi-day job on a single H100 | and there is no seeding, so you cannot reproduce a specific run anyway (§10.1) |
| 2 | **Resolution must be a multiple of 14** | `assert resolution % 14 == 0` `[repo: roma_models.py:71-72]` — DINOv2 patch size. Use 448 / 560 / 672, **not** 512 or 640. A very common integration error |
| 3 | On Linux, `uv sync --extra fused-local-corr`; on Windows expect the fallback | `use_custom_corr` forced `False` on non-Linux with a warning `[repo: roma_models.py:60-62]` |
| 4 | ✅ **`uv.lock` is present** — use `uv sync` for an exactly pinned environment | better than `../RoMaV2/`, which ships no lockfile `[repo: uv.lock; README.md]` |
| 5 | Convert outputs with `to_pixel_coordinates` | warps are normalized `[−1,1]²` |
| 6 | Record which **variant** you used: `roma_outdoor` vs `roma_indoor` vs **`TinyRoMa`** | `TinyRoMa` is a repo-only model absent from the paper (delta D-10) |
| 7 | Record `symmetric`, `upsample_preds`, `attenuate_cert` | defaults are `True/True/True` at inference; **`../EDGS/` sets the first two to `False`** `[EDGS repo: source/corr_init.py:538-539]` |
| 8 | If retraining, note `c = 1e-4` in the script vs **0.03 in the paper** | a 300× difference in the robust loss's transition point (delta D-1) |
| 9 | If retraining, note the undocumented `prob > 0.99` mask and the local-EPE gate | deltas D-2, D-3 — both materially change what is supervised |
| 10 | For WxBS or IMC2022 numbers, expect to build your own harness | not shipped (§10.3) |
| 11 | **Hardware:** nothing in the paper. Use `../RoMaV2/`'s H200 measurements as the proxy — **18.5 pairs/s, 4.7 GB at 640², batch 8** | `[RoMaV2 paper Tab. 8]`; same Hopper generation as your H100 |
| 12 | **For cross-modal imagery, prefer RoMa v1 over v2** | v2 loses on WxBS, 55.4 vs 60.8 mAA, conceded in `[RoMaV2 paper §5]` |
