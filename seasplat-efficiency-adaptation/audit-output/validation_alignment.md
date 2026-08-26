# §6 — Validation-plan alignment

Two questions: is the ablation framing internally consistent, and is the metric protocol
identical across the branches being compared?

---

## Part 1 — Ablation framing: additive vs. leave-one-out

### What the design actually is

The README (identical on all seven feature branches) states:

> A0: SeaSplat baseline · A1: Deterministic initialization · A2: Spatial reorganization ·
> A3: Attribute-level quantization · A4: A1+A2 · A5: A1+A3 · A6: A2+A3 · A7: Full integrated framework

That is a **complete 2³ full factorial** — all eight cells of three binary factors, with none
missing. This is a stronger instrument than most of the nine source methods use:

| Method | Ablation structure |
|---|---|
| **This study** | **full 2³ factorial (8/8 cells)** |
| EDGS | 2×2 factorial (method × densification) `[EDGS Tab. 4]` |
| compact3d | *variants*, not an ablation ladder — 16K vs 32K differ only in codebook size `[compact3d Tab. 1]` |
| Mini-Splatting | cumulative-additive ladder |
| SeaSplat | leave-one-out over losses |

### ✅ The framing supports both readings — that is the point of a factorial

A full factorial does not have to choose. All three contrast families are available from the
same eight runs:

| Reading | Contrasts |
|---|---|
| **Single-factor (main effects)** | A0→A1, A0→A2, A0→A3 |
| **Cumulative-additive** | A0→A1→A4→A7 (or any of the 6 orderings) |
| **Leave-one-out** | A7 vs A6 (drop A1), A7 vs A5 (drop A2), A7 vs A4 (drop A3) |

**There is no inconsistency to resolve.** The risk is the opposite one: reporting the
factorial *as if* it were a cumulative ladder.

### 🔴 V-1 — Additivity does not hold, so the ladder reading is invalid

Presenting results as "A1 gives +X, adding A2 gives a further +Y" requires the main effects to
be additive. They are not, for reasons established in the combination audits:

| Pair | Why they interact |
|---|---|
| **A1 × A2** | Both act on the *same state variable*, `N`. A1 sets its initial value and freezes its dynamics; A2 caps it. With densification disabled `N` can never grow, so A2's budget is binding at iteration 15 500 or binding never — **A4 ≡ A1 whenever `N_init ≤ 800 000`** (`a1_a2.md` C4-1). A2 also partially restores the α-prune A1 removed, so its *effect* differs entirely depending on A1. |
| **A1 × A3** | Data-flow coupling: A1 determines the opacity distribution written to the `.ply`, which is exactly what A3's codebook is fit over. A1's unpruned α ≈ 0 mass is the ingredient that makes A3's opacity quantization dangerous (`a1_a3.md` C5-1). |
| **A2 × A3** | Weakest coupling, and the only near-separable pair — though A2 truncates the opacity tail before A3's codebook is fit (`a2_a3.md` C6-2), and the two compete for credit on model size. |

**Requirement:** report the **interaction terms**, not just main effects. A 2³ factorial is
precisely the right design for this — the interactions are estimable — but they must be
stated. A large A1×A2 interaction is *expected*, not an anomaly.

### 🔴 V-2 — Four of the eight cells may not be distinct

Restating the consequence for the validation plan specifically:

| If | Then |
|---|---|
| `N_init ≤ 800 000` | A4 ≡ A1 and A7 ≡ A5 — the factorial has **6 distinct cells, not 8**, and the A2 main effect is unestimable within the A1-derived half |
| `max_gaussians` never binds on densified runs either | A2 ≡ A0 and A6 ≡ A3 — **4 distinct cells** |
| `seathru_from_iter` was left at its `9_000_000` default | the medium model never activated; **all eight cells are 3DGS variants and none of the study is about underwater rendering** |

None of these is currently checkable from the repo: `docs/experiment_plan.md` is 0 bytes and
A2's log fires only when pruning occurs. See `refit_recommendations.md` R-1.

### 🟡 V-3 — "Full integrated framework" mislabels A7

A7 is a **file-level union** — verified: `git diff a4..a7 -- train.py scene/gaussian_model.py`
is empty, `quantize.py` is byte-identical across all A3-derived branches. There is no
integration code: no shared budget between `max_gaussians` and `k`, no rate–distortion
objective, no coordination between A2's prune cadence and A3's codebook. That is the *correct*
construction for a factorial cell, but "integrated framework" claims a designed composition
that does not exist. Use "combined" or "A1+A2+A3".

---

## Part 2 — Metric protocol identity

### ✅ V-4 — The evaluation path is byte-identical across all eight branches

Verified directly:

```
git diff --name-only baseline/seasplat..<branch> -- metrics.py render_uw.py utils/image_utils.py
```

returns **zero changed files for all seven feature branches**. Whatever the protocol's
absolute merits, **cross-branch comparison within this study is internally consistent** —
differences in reported PSNR/SSIM/LPIPS are attributable to the branches, not the harness.
This is the cleanest result in the audit and it should be stated explicitly in the thesis.

### The protocol, precisely

```python
def psnr(img1, img2):
    mse = (((img1 - img2)) ** 2).view(img1.shape[0], -1).mean(1, keepdim=True)
    return 20 * torch.log10(1.0 / torch.sqrt(mse))
```
`[repo: utils/image_utils.py]`

| Property | Value | Evidence |
|---|---|---|
| **Masking** | ❌ **none — full-frame** | no mask is loaded or applied anywhere in `metrics.py` |
| **Convention in `metrics.py`** | **pooled-MSE** | tensors are `(1,3,H,W)` via `.unsqueeze(0)`, so `shape[0]=1` and `.view(1,-1)` flattens **C,H,W together** `[metrics.py:65-66]` |
| **Convention in `train.py` logging** | **per-channel-mean** | the training tensor is `(3,H,W)`, so `shape[0]=3` → three per-channel PSNRs → `.mean()` at the call site |
| Inputs | 8-bit, **read back from disk** | `Image.open` → `tf.to_tensor` |
| GT format | `.png`, falling back to **`.JPG`** | `[metrics.py:59-62]` |
| Split | `<model_path>/test/{gt,render}` | `[metrics.py:107-108]` |
| `--eval` | defaults to **`False`** | `[arguments/__init__.py:56]` |

### 🔴 V-5 — Two PSNR conventions coexist, and the gap is unusually large underwater

The same `psnr()` function yields **different numbers depending on the call site**: the
training log is per-channel-mean, the reported metric is pooled-MSE. By Jensen's inequality
(`−log` is convex),

> **per-channel-mean PSNR ≥ pooled-MSE PSNR**, with equality only when all three channel MSEs
> are equal.

For terrestrial scenes the channel MSEs are similar and the gap is small. **For underwater
scenes they are not.** Attenuation is strongly wavelength-dependent — that is the entire
premise of the revised Akkaynak–Treibitz model SeaSplat implements, with a separate `β^D`
per channel `[my-research/seasplat/…/03-variables.md]`. The red channel attenuates fastest and
carries the largest residual, so the per-channel MSEs diverge by design, and **the Jensen gap
between the two conventions is systematically wider here than in any of the terrestrial
methods in the set.**

Practical consequences:

1. **Never quote a training-log PSNR next to a `metrics.py` PSNR.** They are different
   statistics and the difference is not small.
2. State which convention the reported table uses. `metrics.py` = pooled-MSE.
3. compact3d is the one source method that discusses this directly, introducing **PSNR-AM**
   and explaining why averaging PSNRs is problematic — "dominated by very accurate
   reconstructions … because it is based on the geometric average of the errors due to the log
   operation" `[compact3d §4]`. **Cite that passage when justifying the chosen convention.**

### 🟡 V-6 — Full-frame PSNR is the weakest available instrument for these findings

Several of the audit's most severe findings are **specifically invisible to full-frame,
unmasked PSNR against a raw underwater GT**:

| Finding | Why the metric misses it |
|---|---|
| A1-1 — α ≈ 0 Gaussians never removed | They contribute nothing to the rendered image *by construction*. PSNR is exactly unchanged; only memory and frame time move. |
| C5-1 — quantization re-materializes suppressed floaters | Appears in backscatter-dominated regions and in the restored image `Ĵ`, both partly masked by the medium model in the rendered comparison. |
| A3-2 / C5-3 — post-hoc `f_dc` snapping undoes `L_gw`/`L_sat` | These losses act on **aggregate colour statistics of `Ĵ`**. The reported metric compares the rendered *underwater* image to the raw GT, where a global colour shift in the restored image barely registers. |

**Recommendation:** report at least one metric on the **restored** image `Ĵ`, and report
Gaussian count and model size as first-class results rather than footnotes. Otherwise the
study's efficiency mechanisms are being validated with an instrument that cannot see their
principal failure modes. Since no reference `Ĵ` exists for real underwater scenes, a
no-reference measure (UIQM/UCIQE) or SeaSplat's own qualitative comparison is the practical
option.

### 🟡 V-7 — Protocol elements that are unrecorded

`--eval` defaults to **`False`**, which yields an empty test camera list and hence no
`test/` directory for `metrics.py` to read — so any existing numbers imply `--eval` *was*
passed. But that, the dataset, the split, the resolution (`_resolution = -1`), and the
`seathru_from_iter` value are all recorded nowhere (`docs/experiment_plan.md` is 0 bytes).
For eight runs that must be identical in every respect except the branch, **none of the
"identical" parts is written down.**

### 🟡 V-8 — These numbers are not comparable to published tables

Two independent reasons, both worth a footnote in the thesis:

1. **Convention.** Pooled-MSE PSNR is one of at least three conventions across the nine
   source methods `[my-research/comparison-glossary.md]`. Cross-paper PSNR comparisons in this
   family are unreliable without checking each call site.
2. **Pipeline.** Metrics are computed on 8-bit images round-tripped through disk, with a
   `.JPG` fallback on the GT path `[metrics.py:59-62]` — so JPEG artifacts can enter the
   reference. This is inherited from SeaSplat and applies equally to all eight branches, so it
   does not affect internal comparison, but it does put a floor under absolute PSNR.

Likewise, **"number of Gaussians" is not comparable across the source methods** — CompGS-Liu
reports *anchors*, OMG and compact3d report primitives, and model-size accounting differs on
whether neural decoders are included `[my-research/comparison-glossary.md]`. If the thesis
tabulates this study beside published figures, that column needs a definition note.

---

## Summary

| ID | Finding | Class |
|---|---|---|
| V-1 | Additivity does not hold (A1×A2 share `N`; A1×A3 are data-flow coupled) — interaction terms must be reported, ladder framing invalid | 🔴 correctness |
| V-2 | 4 of 8 cells may not be distinct; 3 unrecorded numbers decide | 🔴 correctness |
| V-5 | Two PSNR conventions in one repo; Jensen gap systematically wider underwater | 🔴 correctness |
| V-6 | Full-frame unmasked PSNR cannot see the audit's most severe findings | 🟡 correctness |
| V-3 | "Full integrated framework" mislabels a file-level union | 🟡 reporting |
| V-7 | No protocol element of the eight runs is recorded | 🟡 correctness |
| V-8 | Not comparable to published tables (convention + JPEG GT + count definitions) | 🟡 reporting |
| **V-4** | **Evaluation path byte-identical across all 8 branches — internally consistent** | ✅ **verified** |
