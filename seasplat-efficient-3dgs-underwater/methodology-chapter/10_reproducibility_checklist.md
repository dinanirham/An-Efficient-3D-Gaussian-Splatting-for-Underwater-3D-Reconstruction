# §10 — Reproducibility and validation checklist

---

## 10.1 Evaluation-protocol identity — ✅ **resolved**

This was flagged as a precondition in the implementation audit. **It is satisfied**, and this
section restates the resolution rather than re-deriving it.

> `git diff --name-only <baseline>..<branch> -- metrics.py render_uw.py utils/image_utils.py`
> returns **zero changed files for all seven feature branches**
> `[implemented: audit validation_alignment.md V-4]`.

| Protocol element | Value | Status |
|---|---|---|
| **Masking** | ❌ **none — full-frame** | ✅ identical on all 8 branches. No mask is loaded or applied anywhere in `metrics.py`. |
| **PSNR convention** | **pooled-MSE** — tensors are `(1,3,H,W)`, so channels and pixels flatten together | ✅ identical; matches the draft's Eq. 3.1 `[recommended: draft §3.7.1]` |
| **Split** | LLFF-style holdout, `i mod 8` | ✅ identical; `[recommended: draft §3.6.2]` "The same data splits are used across all experimental configurations" |
| **Test views** | 3 / 3 / 4 / 3 per scene | ✅ constant across all 20 runs `[measured]` |
| **`--eval`** | passed on every run | ✅ confirmed — `metrics.py` reads `<model>/test/`, which does not exist otherwise |
| **Metric code** | `metrics.py`, `render_uw.py`, `utils/image_utils.py` | ✅ byte-identical |

**Consequence:** differences between configurations are attributable to the mechanisms, not the
harness. Combined with the identical loss function (§4), this is the study's strongest
internal-validity property and should be stated once, explicitly, in the thesis.

**Two caveats that do not affect internal comparison:**

- GT images are read from disk as 8-bit, with a `.JPG` fallback when no `.png` exists — JPEG
  artifacts can enter the reference, putting a floor under absolute PSNR. Applies equally to all
  branches.
- Full-frame PSNR on the *rendered underwater* image `Î` is the weakest available instrument for
  several risks identified in §5: `α ≈ 0` primitives contribute nothing to `Î` by construction,
  and colour drift in the *restored* image `Ĵ` is partly re-absorbed by the medium model before
  reaching `Î` (§4.3). **Report at least one measurement on `Ĵ`** — see 10.5.

---

## 10.2 Ablation framing — **additive**, no leave-one-out

**The 8-configuration comparison is reported additively: each configuration is the baseline plus
a subset of mechanisms**, matching SeaSplat's own Table III convention. **No leave-one-out claim
will be made from it.**

| Reading | Used? |
|---|---|
| Single-mechanism vs baseline — A0→A1, A0→A2, A0→A3 | ✅ **the completed study** |
| Additive subsets — A0 + {A1}, + {A1,A2}, + {A1,A2,A3} | ✅ the intended framing for A4–A7 |
| Leave-one-out — A7 vs A4/A5/A6 | ❌ **not claimed** |

⚠️ **Terminology to align in the thesis.** Draft §3.6.4 currently describes the matrix as *"a
full-factorial ablation study"*. The **design matrix** is indeed a full 2³ factorial (all eight
cells), but the **claims** are additive. Those are compatible statements, but the phrase
"full-factorial" invites interaction-term and leave-one-out readings that this study will not
support — especially since (a) A4–A7 are unrun, and (b) two of them are degenerate as configured
(§8.4). **Recommended wording:** *"a full 2³ configuration matrix, reported as additive
mechanism subsets."*

⚠️ **Additivity is not expected to hold** even when A4–A7 are run: A1 and A2 both act on the
population count `N`, and A1 determines the opacity distribution A3 quantizes (§3.5). This is a
further reason not to present results as a ladder of independent increments.

**A1v2 is a sensitivity boundary, not a ninth cell** — it differs from A1 only in offline matcher
density and is reported alongside A1 `[recommended: draft §3.6.4]`.

---

## 10.3 Seeds, non-determinism, and what actually varies

### 🔴 Demonstrated: the baseline is not reproducible to better than ~28 %

A3 does not modify `train.py`, so its runs should reproduce A0's exactly. Final primitive counts
differ by up to **27.7 %** (§8.3a) `[inferred]`. Densification is gradient-triggered and the
CUDA rasteriser backward uses non-deterministic atomics, so **`safe_state`'s hard-coded seed 0
does not make runs reproducible.**

This is a genuine reproducibility limitation — and it also **empirically supports A1's stated
motivation** that densification is stochastic `[recommended: plan §1]`. It should be reported as
both.

### Per-mechanism non-determinism

| Mechanism | Deterministic? | Notes |
|---|---|---|
| **A1 offline** (`roma_init.py`) | 🔴 **No** | No seed is set; RoMa matching is GPU-nondeterministic; `voxel_down_sample` output order is implementation-dependent. **`N_init` — the experimental condition for A1/A4/A5/A7 — varies between invocations.** |
| **A1 training** | inherits baseline non-determinism | Population is frozen, so the *count* is stable within a run — but fixed by an unstable offline stage |
| **A2** | 🟡 mostly | `torch.sort` tie-breaking on CUDA is unspecified; float importances make exact ties unlikely. `prune_points` is deterministic given the mask. Inherits baseline non-determinism up to iteration 15 500. |
| **A3** | ✅ **Yes** | `MiniBatchKMeans(random_state=42)`; `n_clusters=min(k,N)` and `batch_size=min(4096,N)` guard small inputs. **Given the same input PLY, output is reproducible.** |

### 🔴 Hardware variance across Colab Pro sessions

Each ablation ran on a **different Colab VM** — hostnames `ed3757dbda43` (A0),
`4c4cf0cd2ff0` (A1), `ff84c356fe08` (A1v2), `19b4dd385f0f` (A2), `0973c73c9000` (A3)
`[measured: TensorBoard event filenames]`.

- Within an ablation, all four scenes share a VM ⇒ **scene-to-scene comparisons are clean**.
- Across ablations, **training-time and FPS comparisons confound mechanism with hardware
  allocation.** Colab Pro does not guarantee a consistent GPU SKU, clock, or thermal envelope
  between sessions — unlike a dedicated cluster.
- Fidelity, model size and primitive count are hardware-independent and unaffected.

This is a reproducibility risk **specific to this environment** and it compounds the draft's own
caution about training-time metrics `[recommended: draft §4.7.1]`.

---

## 10.4 Checklist

### Must record before any further run

- [ ] **`N_init` and a SHA-256 of every `dense_<scene>.ply`.** It is the experimental condition
      for four configurations and is produced by an unseeded stage.
- [ ] **Seed `roma_init.py`** (`torch.manual_seed`, `np.random.seed`) and pin `romatch` — the
      only import missing from `requirements.txt`.
- [ ] **The exact notebook keyword arguments per run.** The shipped `roma_init.py` defaults
      (`matches=5000`, `certainty=0.02`, `voxel=0.001`) match **neither** executed configuration
      (§6, D-3/4/5). Reproduction from the repository alone is currently impossible.
- [ ] **GPU SKU per session** (`nvidia-smi -L`) alongside every timing number.
- [ ] **Unconditional Gaussian-count logging.** A2's `[A2] Reorg @ iter …` prints only when
      `n_pruned > 0`, so silence is ambiguous between "under budget" and "not running."

### Decide before launching A4–A7

- [ ] 🔴 **Pair the combinations with A1v2 density, not A1.** A1's counts (222 k–369 k) are all
      below `max_gaussians = 800 000`, and with densification disabled the count can never rise
      to meet it — so **A4 ≡ A1 and A7 ≡ A5 exactly**, wasting two runs. A1v2's counts
      (889 k–1.46 M) all exceed the budget and make every cell distinct (§8.4).
- [ ] **Run A6 (A2+A3) first.** Both constituents are measured, the composition order is safe by
      construction, the mechanisms target orthogonal axes, and the draft already names it the
      most promising `[recommended: draft §4.7.3]`.
- [ ] **Decide on `'opacity'` in `to_quantize`.** CompGS excludes it deliberately; including it
      is the ingredient that makes A5/A7 risky (§5.3). Removing it costs ~2 bytes per 20 and one
      line of code, and requires **no retraining**.

### Cheap corrections with no retraining cost

- [x] **§3.5.3 corrected** — replacement text in `draft-correction-3.5.3.md`: superseded
      paragraphs cut, the surviving "not a parameter reduction technique" sentence rewritten,
      Mini-Splatting attribution qualified, medium-aware property of `Φ` added (§6, D-19).
- [ ] Update the **A2 notebook** markdown, which still describes a single-shot prune at
      iteration 12 000. The draft thesis and the code are both correct; only the notebook is
      stale (§6, D-20).
- [ ] Resolve the **duplicate equation number (3.1)** — used for both the importance score
      (§3.5.3) and PSNR (§3.7.1); see `draft-correction-3.5.3.md` X-1.
- [ ] Report A3's size as **per-primitive (4.27×)**, and note that the archive figure includes
      `savez_compressed` zlib, so it is not comparable to CompGS's bit-packed `Mem`.
- [ ] Exclude the A3/Curasao record (`training_time_sec = 0`, `peak_train_vram_mb = 0`) from all
      means — already documented `[recommended: draft Table 4.13]`.
- [ ] State that A1's offline RoMa preprocessing is **excluded from reported training times**, so
      A1/A1v2 timings are not like-for-like with A0's (§8.2).
- [ ] Rename `imp_metric` → `scale_reduction`, or define it explicitly (§9.2).

### 10.5 Recommended additional measurements (no retraining)

| Measurement | Answers | Cost |
|---|---|---|
| Quantized vs. unquantized PSNR **from the same checkpoint** | Removes the ±28 % count confound from A3's fidelity claim (§8.3a) — this is the number the thesis should report for A3 | one eval pass over saved PLYs |
| A metric on the **restored image `Ĵ`** before/after quantization | Directly tests the `L_gw`/`L_sat` colour-drift risk instead of assuming it (§4.3). No reference `Ĵ` exists, so use a no-reference measure (UIQM/UCIQE) or paired visual comparison | one render pass |
| Count of primitives with `α < 0.005` in each saved model | Quantifies how many `L_op`-suppressed primitives A1 leaves unremoved — the mechanism behind the Panama failure (§5.2) and the A5 risk (§5.3) | reads existing PLYs |
| A0 re-run on one scene with a fixed seed | Establishes the actual reproducibility envelope rather than inferring it from the A0-vs-A3 divergence | one training run |

The first three cost no GPU training time and between them convert three currently-analytical
claims into measured ones.
