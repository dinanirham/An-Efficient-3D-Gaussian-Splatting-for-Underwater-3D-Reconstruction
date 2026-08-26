# §6 — Implementation deltas: paper vs. recommended vs. implemented

Reconciled across four columns rather than two, because the completed runs revealed a fourth
that the prompt's three do not cover:

| Tag | Source |
|---|---|
| `[paper]` | the source method's publication / reference repository |
| `[recommended]` | A1 design spec & implementation plan; draft thesis Chapter 3 |
| `[implemented]` | the shipped branch code and its defaults |
| `[measured]` | the values actually passed by the Colab notebooks, and the resulting outputs |

⚠️ **`[implemented]` and `[measured]` diverge repeatedly**, because the notebooks pass explicit
keyword arguments that override the shipped defaults. A reader who reproduces from the repo
defaults will reproduce **no executed configuration**. This is the most systematic finding in
this section.

---

## 6.1 Component 1 — A1 Deterministic initialization

### Parameters

| # | Parameter | `[paper]` EDGS | `[recommended]` | `[implemented]` default | `[measured]` A1 | `[measured]` A1v2 |
|---|---|---|---|---|---|---|
| D-1 | `num_refs` | 180, k-means over poses | all train views | `−1` | all (15–25) ✅ | all ✅ |
| D-2 | `nns` | 3 | 3 | `3` | 3 ✅ | 3 ✅ |
| D-3 | `matches` per pair | 20 000 | 5 000 | `5000` | **5 000** | **20 000** |
| D-4 | `certainty` threshold | ≈0.05 | 0.02 | `0.02` | **0.05** | **0.02** |
| D-5 | `voxel` dedup | implicit | 0.001 | `0.001` | **0.005** | **0.002** |
| D-6 | `reproj_thr` | implicit | 2.0 | `2.0` | 2.0 ✅ | 2.0 ✅ |

> 🔴 **D-3/D-4/D-5 — the repo defaults match neither executed run.** `certainty` is
> *recommended* at 0.02 and *shipped* at 0.02, but A1 actually ran at **0.05** — which happens
> to match EDGS more closely than the recommendation did. `voxel` was recommended and shipped
> at 0.001 and ran at **0.005** (A1) and **0.002** (A1v2) — **neither run used the shipped
> value.** Reproducing A1 from the repository is impossible without the notebook.

### Outcomes vs. targets

| # | Claim | `[recommended]` | `[measured]` | Verdict |
|---|---|---|---|---|
| D-7 | Initial/final cloud size | **20 000 – 80 000 points** (stated twice: plan §3, spec §5) | **A1: 222 860 – 368 742**<br/>**A1v2: 888 706 – 1 460 514** | 🔴 **2.8×–18× above the stated target on every scene.** The design's own pass criterion ("Cell 7 produces a PLY with 20k–80k points") was never met. |
| D-8 | OOM risk register | ">200 k → OOM on Colab; tighten voxel 0.001→0.005" `[recommended: spec §8]` | A1 *did* use voxel 0.005 and still produced 222 k–369 k | 🟡 Mitigation applied, target still missed by ~3×. |
| D-9 | Validation gate | "PSNR within ±2 dB of A0 … **Curasao only**, 12 000 iters" `[recommended: spec §2]` | Curasao A1 = **30.97** vs A0 **30.13** → **+0.84 dB, PASS** | ✅ Gate passed as written. ⚠️ Because it was Curasao-only, it could not catch Panama. |
| D-10 | Scope | "other 3 scenes only after Curasao go/no-go"; "full 30 k run — **out of scope**" `[recommended: spec §7]` | All 4 scenes, 30 000 iters | 🟢 Scope expanded (legitimate), but the go/no-go decision is not recorded anywhere. |

### Code-level deltas

| # | Item | `[paper]` | `[recommended]` | `[implemented]` |
|---|---|---|---|---|
| D-11 | Triangulation | EDGS: batched GPU, 4×4 NDC space, keypoints in [−1,1] | spec §3.3: "vectorized … **single `np.linalg.svd(A_batched)` call** → all points at once" | 🔴 **per-pair Python loop** with `np.linalg.svd(A)` inside — the un-vectorized form the spec explicitly rejected |
| D-12 | Certainty post-processing | EDGS bypasses RoMa's high-level API and applies `sigmoid` + low-res attenuation manually | spec §3.1 decides to use `roma_model.match()`, which "already applies the sigmoid internally" — ✅ correct reasoning | matches the decision ✅ ⚠️ but spec §4's data-flow diagram still lists "`cert.sigmoid()` + low-res attenuation **[from EDGS]**", contradicting §3.1. **The spec contradicts itself.** |
| D-13 | RoMa call | EDGS sets `upsample_preds=False, symmetric=False` for speed | not mentioned | `roma_outdoor(device, use_custom_corr=False)` — both left at default, i.e. the **slower, higher-quality** path. Not an error; a cost choice that inflates preprocessing time and should be stated. |
| D-14 | **`α < 0.005` prune** | EDGS keeps it running **outside** the densify gate | plan §11 lists only "Opacity reset: **Disabled** (inside densify gate)" — **the prune loss is never mentioned** | 🔴 **Disabled together with densification.** `densify_and_prune` carries `min_opacity = 0.005` and lives inside the gated block. The author noticed the reset loss and documented it; the prune loss went unnoticed. |
| D-15 | `reduce_opacity` (×0.99 decay) | EDGS default **True** | not mentioned | 🔴 absent |
| D-16 | `max_lr` (position-LR clamp) | EDGS default **True** | not mentioned | 🔴 absent |
| D-17 | `--pcd_path` default | — | `None` `[plan §5]` | `""` — cosmetic |
| D-18 | `--no_densify` default | EDGS README/config disagree | `False` `[plan §5]` | `False` — a bare run densifies *and* loads the dense cloud: an undocumented fourth configuration |

> 🔴 **D-14 is the most consequential mismatch in the chapter.** The recommendation documents
> one side-effect (opacity reset) and misses the other (α-pruning). Together with D-15/D-16 —
> EDGS's two counterweights, never ported — this is the mechanism behind the Panama collapse
> (§5.2). It is also the cheapest to fix: move the prune outside the gate.

---

## 6.2 Component 2 — A2 Spatial reorganization

| # | Item | `[paper]` Mini-Splatting | `[recommended]` | `[implemented]` | `[measured]` |
|---|---|---|---|---|---|
| D-19 | **Removal vs. reorganization** | — | 🟡 draft §3.5.3 carries **two layers**. The superseded one — *"**Rather than removing primitives through pruning** … this component focuses on **reorganizing** primitives"* — is still physically present and ends with the author's own `(removed)` marker. The **revised** layer is correct: *"the lowest-importance primitives are **pruned** until the budget is satisfied"* | **`self.prune_points(prune_mask)`** — removal of the bottom-`n` primitives, matching the revised layer ✅ | Final `N` = **exactly 800 000** on all four scenes — a hard cap achieved by deletion |
| D-20 | Trigger schedule | — | ✅ **draft §3.5.3 is correct**: *"designed to occur **continuously after adaptive densification has completed** … Applying reorganisation during the densification phase would allow newly densified Gaussians to refill the pruned positions"*<br/>🔴 **notebook** is stale: `--reorganize_from_iter 12000`, *"single-shot"* | Trigger is `iter > 15 000 ∧ iter mod 500 == 0` — 30 events. **No `reorganize_from_iter` parameter exists on any branch.** | `N` = exactly 800 000 ⟹ the final prune occurred after densification ended ⟹ the every-500 version ran, matching **the draft** and not the notebook `[inferred]` |
| D-21 | Importance metric | accumulated blending weight `I¹`/`I²`, integrated over training views | draft: "inspired by **surface-aware Gaussian grouping**"; notebook: "importance = opacity × max_scale" | `Φ_i = α_i · max(s_i)` — instantaneous, **no visibility or occlusion term** | — |
| D-22 | Selection rule | **stochastic**, sampled without replacement ∝ importance (§4.2 argues *against* top-k) | not specified | **deterministic ascending sort, prune bottom `n`** | mean ΔPSNR −0.05 dB ⇒ coverage loss not manifest at this budget |
| D-23 | `imp_metric` semantics | selects `I¹` vs `I²` | — | selects `max` vs `mean` over scale axes — **same name, unrelated meaning** | `outdoor` used throughout |
| D-24 | Blur split · depth reinit · intersection preserving | all three are core | not mentioned | ❌ all absent | — |
| D-25 | Off switch | — | — | `hasattr(opt_params,'max_gaussians')` is **always True** — no way to disable A2 on its own branch | — |

> 🟡 **D-19 is an incomplete edit, not a live contradiction.** §3.5.3 was revised at some point
> and the superseded paragraphs — including the sentence disclaiming pruning — were marked
> `(removed)` but never cut. The revised text describes pruning correctly. **One sentence did
> survive the revision and is still wrong**: *"spatial reorganisation is treated as a geometric
> regularisation mechanism rather than a compression or **parameter reduction technique**"*,
> which contradicts Chapter 4's own *"reorganization, which directly reduces the number of
> Gaussian primitives"* (p. 108). Corrected text: `draft-correction-3.5.3.md`.
>
> ✅ **D-20 is a notebook-vs-code mismatch, not a thesis-vs-code one.** The draft states the
> post-densification trigger *and its rationale* correctly. The notebook markdown describing a
> single-shot prune at iteration 12 000 is the stale artifact — such a prune would sit inside
> the densification window, allow regrowth to 15 000, and could not produce a flat 800 000. The
> data therefore confirms the draft's account. **Update the notebook**, not the thesis.

---

## 6.3 Component 3 — A3 Attribute-level quantization

| # | Item | `[paper]` CompGS | `[recommended]` | `[implemented]` | `[measured]` |
|---|---|---|---|---|---|
| D-26 | Training integration | **quantization-aware**, STE, centroids every iter, assignments every 100 | ✅ **post-hoc, deliberately** — "avoids introducing quantization-induced gradient perturbations into the SeaThru parameter estimation" `[draft §3.5.4]` | post-hoc ✅ | mean ΔPSNR **−0.075 dB** ⇒ **the decision is empirically vindicated** |
| D-27 | **Opacity** | 🔴 **excluded** — "a single scalar" | draft says "appearance- and geometry-related attributes"; **opacity is never named** | 🔴 **included** in `to_quantize` | — |
| D-28 | Position | excluded — "sharing them results in overlapping Gaussians" | excluded | ✅ excluded (`quant_xyz=False`) | — |
| D-29 | Medium parameters | n/a | "explicitly excluded from quantization" | ✅ `.pth` protected and printed | ✅ |
| D-30 | Codebook size `k` | 4 096 / 16 384 / 32 768 | **256** `[draft §3.5.4]` | 256 ✅ | 256 ✅ |
| D-31 | Group size | per-attribute `d` | **4** `[draft §3.5.4]` | 4 — but **inert at `sh_degree = 0`**, where every attribute forms one group | — |
| D-32 | Scale/rotation space | pre-`exp`, pre-normalization | — | ✅ reads `_scaling`/`_rotation` from PLY | — |
| D-33 | Index width | `ceil(log2 k)` = 8 bits | — | 🟡 `uint16` — 2× waste | absorbed by zlib |
| D-34 | Model-size definition | bit-packed indices + codebooks | ✅ **explicit**: "the size of this **compressed archive**, which constitutes the deployed storage footprint" `[draft §3.5.4]` | `np.savez_compressed` NPZ ✅ | **4.28×** per-primitive |
| D-35 | In-loop wiring | — | post-hoc by design | 🟡 `quant_k`/`quant_group_size`/`quant_xyz` added to `arguments/__init__.py` are **read by nothing** — dead config implying an abandoned in-loop path | — |
| D-36 | ℓ1 opacity regularizer | present; **source of CompGS's 2–3× FPS gain** | not mentioned | absent | — |

> ✅ **D-26 and D-34 are the model cases for this chapter.** Both are deviations from the source
> paper, both are *stated in advance with a rationale*, and both are borne out by the
> measurements. This is what a defensible adaptation looks like, and it is the standard the A1
> and A2 deviations should be held to.
>
> 🟡 **D-27 is the gap.** Opacity quantization is neither justified nor mentioned in the thesis,
> and it is the ingredient that makes A5/A7 risky (§5.3). Cost to fix: delete one string.

---

## 6.4 A3's training runs are not A0's runs

A3 does not touch `train.py`, so its training should be identical to A0's. Final primitive
counts `[measured]`:

| Scene | A0 | A3 | Δ |
|---|---:|---:|---:|
| Curasao | 4 462 668 | 3 805 843 | **−14.7 %** |
| JapaneseGardens-RedSea | 2 272 131 | 1 913 190 | **−15.8 %** |
| IUI3-RedSea | 2 877 685 | 2 080 947 | **−27.7 %** |
| Panama | 1 809 834 | 1 876 894 | +3.7 % |

Identical code, identical flags, counts differing by up to **27.7 %** `[inferred]`. Two
consequences:

1. **Run-to-run non-determinism in the baseline is large** — densification is gradient-triggered
   and CUDA-nondeterministic. This is a §10 reproducibility finding, and it also *supports* A1's
   stated motivation ("densification is stochastic").
2. **A3's ΔPSNR against A0 is confounded.** The correct comparison is quantized vs. unquantized
   **from the same run**, which the current tables do not report. The reported −0.075 dB mixes
   quantization effect with a ±28 % difference in primitive count (§8.3, §10.2).

---

## 6.5 Summary of recommended-vs-implemented mismatches

| Severity | Mismatch |
|---|---|
| 🔴 | **D-14** A1's `α`-prune loss undocumented (only the reset loss was noted) |
| 🟡 | **D-19** §3.5.3 superseded paragraphs never cut; one surviving sentence still denies that A2 reduces parameters — fixed in `draft-correction-3.5.3.md` |
| 🟡 | **D-20** A2 notebook markdown stale (single-shot at 12 000); **the draft thesis is correct** |
| 🔴 | **D-7** A1 cloud size 2.8×–18× above the stated 20 k–80 k design target |
| 🔴 | **D-3/4/5** repo defaults match neither executed run |
| 🟡 | **D-27** opacity quantized without mention; CompGS excludes it |
| 🟡 | **D-11** triangulation shipped un-vectorized, contrary to the spec |
| 🟡 | **D-12** design spec internally contradictory on certainty handling |
| 🟡 | **D-35** dead quantization config in `arguments/__init__.py` |
| ✅ | **D-26/D-34** post-hoc quantization and archive-based size definition: deviations stated in advance, justified, and empirically supported |
