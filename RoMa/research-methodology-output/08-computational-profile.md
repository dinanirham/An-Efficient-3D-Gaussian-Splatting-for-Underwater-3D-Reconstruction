# §8 — Computational profile

## 8.1 ⚠️ The paper reports **no** computational profile at all

Searching `../../RoMa.pdf` for hardware, timing or memory: **nothing**. No GPU named, no
training time, no inference throughput, no VRAM, no parameter count. §4.2 "Training Setup"
gives learning rates, the data split and the training resolutions — and stops.

This is the **weakest computational disclosure of any folder in your comparison set**, weaker
even than `../seasplat/` and `../CompGS/` (which at least report *some* timings on unnamed
hardware). Everything in this section is therefore either from the repo, from the successor
paper, or `[inferred]`.

| Quantity | Value | Source |
|---|---|---|
| GPU | **not stated** | `[unverified]` |
| Training time | **not stated** | `[unverified]` |
| VRAM | **not stated** | `[unverified]` |
| Inference throughput | **not stated** | `[unverified]` |
| Parameter count | **not stated** | `[unverified]` |

## 8.2 What the repo lets you reconstruct

| Item | Value | Source |
|---|---|---|
| Training budget | `N = 32 × 250 000` ⇒ **250k steps at batch 32** | `[repo: experiments/train_roma_outdoor.py:193]` |
| Per-GPU batch | `8` (default) | `[repo: train_roma_outdoor.py:302]` |
| ⇒ implied GPUs | **4** (`step_size = gpus × batch_size = 32`) | `[inferred: repo train_roma_outdoor.py:190-192]` |
| Training resolution | `560 × 560` (`medium`, default); ablations at `448 × 448` | `[paper §4.2]` = `[repo: train_roma_outdoor.py:23, 301]` ✅ |
| Distribution | **DDP**, `find_unused_parameters=False`, `gradient_as_bucket_view=True` | `[repo: train_roma_outdoor.py:248]` |
| Precision | AMP, `amp_dtype = torch.float16` (`float32` on CPU) | `[repo: roma_models.py:50, 69]` |
| Checkpointing | every `25000 // step_size` outer loops | `[repo: train_roma_outdoor.py:195]` |
| Coarse backbone | DINOv2 **ViT-L/14** (~300M params, frozen) | `[repo: encoders.py:42]` `[inferred]` |
| Fine backbone | VGG19-BN `features[:40]` (~20M params, trained) | `[repo: encoders.py:13]` `[inferred]` |
| Match decoder | 5 × `Block(1024, 8 heads)` + MLP 4096 (~63M params) | `[repo: roma_models.py:87-91]` `[inferred]` |
| Refiners | 4 ConvRefiners, `hidden_blocks=8`, depthwise, `kernel_size=5` | `[repo: roma_models.py:99-129]` |

> **The frozen ViT-L is ~300M of the parameter count but contributes no gradients, no
> optimizer state and no activations-for-backward.** That is the "significantly cheaper
> computationally and requires less memory" half of the freezing argument `[paper §3.2]` —
> the paper asserts it but never measures it.

There are inference-timing **tests** in the repo — `tests/test_roma_coarse_inference_time.py`,
`test_roma_coarse_inference_time_cpu.py`, `test_roma_upsample_inference_time.py` — but they
are harnesses, not recorded results. `[unverified]`

## 8.3 The numbers that *do* exist come from the successor paper

`../RoMaV2/` benchmarks RoMa as a baseline, on **640×640, batch 8, NVIDIA H200**
`[RoMaV2 paper Tab. 8]`:

| Method | Throughput (pairs/s) | Memory (GB) |
|---|---|---|
| UFM | 43.0 | 16.2 |
| **RoMa** | **18.5** | **4.7** |
| RoMa v2 (w/ kernel) | 30.9 | 4.8 |

† RoMa was run at **644 × 644** there, "due to patch size 14" `[RoMaV2 paper Tab. 8]`.

So: **RoMa is 1.67× slower than its successor at equal memory**, and 2.3× slower than UFM but
with **3.4× less memory**. The RoMa v2 paper attributes its speedup chiefly to predicting at
**stride 4** instead of RoMa's **stride 14**, which cuts the refiner count from **5 to 3**
`[RoMaV2 paper §3.3]`.

⚠️ **These are a competitor's measurements of this model.** They are the best available and
they are on hardware close to yours, but they were not produced by the RoMa authors.

## 8.4 Hardware transferability to your H100 96 GB

| Aspect | Assessment |
|---|---|
| **Original hardware** | **Unknown.** `[unverified]` — nothing in the paper. |
| **The usable proxy** | `../RoMaV2/`'s **H200** measurements (§8.3) — same Hopper generation as your H100. Expect throughput within ~10–20% and memory essentially unchanged. |
| **Memory headroom** | 4.7 GB at batch 8 / 640² ⇒ enormous headroom on 96 GB. You can raise resolution or batch substantially. |
| **Training feasibility** | 250k steps at batch 32 across (implied) 4 GPUs `[repo: train_roma_outdoor.py:190-193]`. On a single H100 at batch 8 that is ~1M steps — **retraining is a multi-day job**, and you almost certainly want the released weights instead. |
| **Software stack** | Python 3.12 tested, `uv`-managed, **`uv.lock` present** `[repo: README.md; uv.lock]`. Modern and pinned — better than `../RoMaV2/`, which ships no lockfile. |
| ⚠️ **Linux-only CUDA kernel** | `use_custom_corr` forced `False` on non-Linux with a warning `[repo: roma_models.py:60-62]`. On your Windows root you get the PyTorch fallback; on a Linux cluster, the fused kernel. Install with `uv sync --extra fused-local-corr` `[repo: README.md]`. |
| **Resolution constraint** | `assert resolution % 14 == 0` `[repo: roma_models.py:71-72]` — DINOv2 patch size. Choose 448 / 560 / 672 / 700 …, **not** 512 or 640. A frequent integration error. |

## 8.5 Accuracy, for the record

`[paper Tabs. 3-8]` — RoMa is SotA on every benchmark it reports:

| Benchmark | Metric | Best prior | **RoMa** | Gain |
|---|---|---|---|---|
| **WxBS** | mAA@10px | DKM 58.9 | **80.1** | **+36%** ⭐ |
| IMC2022 | mAA@10 | ASpanFormer 83.8 | **88.0** | +5.0% |
| MegaDepth-1500 | AUC@5 | PMatch 61.4 | **62.6** | +2.0% |
| ScanNet-1500 | AUC@5 | DKM/PMatch 29.4 | **31.8** | +8.2% |
| MegaDepth-8-Scenes | AUC@5 | DKM 60.5 | **62.2** | +2.8% |
| InLoc DUC1 | (0.25m,2°) | PATS 55.6 | **60.6** | +9.0% |
| InLoc DUC2 | (0.25m,2°) | DKM 63.4 | **66.4** | +4.7% |

**The distribution of gains is the story.** On in-distribution MegaDepth the margin is **+2%**;
on **WxBS — extreme viewpoint, illumination and modality change — it is +36%**. That asymmetry
is precisely what the frozen-foundation-backbone argument predicts, and it is the single
result to cite from this paper.

## 8.6 ⭐ What this means for `../EDGS/`

EDGS calls RoMa for **all** of its geometry `[EDGS repo: source/corr_init.py:17]` and runs
`num_refs × nns_per_ref = 540` pairs per scene `[EDGS repo: configs/train.yaml]`.

**Cost.** At ~18.5 pairs/s `[RoMaV2 paper Tab. 8]`, 540 pairs ≈ **29 s** of pure matching per
scene — before triangulation. EDGS reports total initialization plus training within 23–30 min
`[EDGS paper Tab. 1]`, so matching is a small but not negligible slice. `[inferred]`

**EDGS runs RoMa in a non-default configuration**, which matters for interpreting both papers:

| Setting | RoMa default | EDGS override | Effect |
|---|---|---|---|
| `upsample_preds` | `True` | **`False`** `[EDGS repo: corr_init.py:538]` | no second high-res pass ⇒ faster, coarser |
| `symmetric` | `True` | **`False`** `[EDGS repo: corr_init.py:539]` | one-directional ⇒ ~2× faster |
| `sample_thresh` | `0.05` | read as EDGS's `τ_corr` `[EDGS repo: corr_init.py:541]` | EDGS's confidence threshold *is* this constant |

So **EDGS's Table 5 result ("RoMa, 28.02 PSNR") was obtained with a deliberately cheapened
RoMa.** A fairer or stronger initialization is available simply by re-enabling those two
flags — an easy, self-contained experiment.

**Upgrade path.** See `../RoMaV2/research-methodology-output/08-computational-profile.md` §8.5
for the v2 comparison: **1.67× faster**, 37–85% lower EPE across six dense benchmarks, but a
**real port** (v2 has no `sample_thresh`, `w_resized`, `upsample_preds`, `symmetric` or
`attenuate_cert` attributes) and **worse on cross-modal** data.
