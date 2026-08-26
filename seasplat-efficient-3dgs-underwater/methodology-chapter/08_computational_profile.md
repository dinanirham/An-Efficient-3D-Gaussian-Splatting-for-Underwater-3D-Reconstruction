# §8 — Computational profile and target claims

All figures below are `[measured]` from `master_metrics.csv` (20 completed runs: A0, A1, A1v2,
A2, A3 × 4 scenes) unless explicitly marked `[projected]`.

---

## 8.1 Hardware, and why cross-paper comparison is directional only

| Item | Value |
|---|---|
| Platform | **Google Colab Pro**, A100-class GPU |
| Peak training VRAM observed | **57 745 MB** (A1v2 Curasao) ⇒ an **80 GB** part on at least the A1v2 runs `[inferred]` |
| Scenes | 4 × SeaThru-NeRF: Curasao, JapaneseGardens-RedSea, IUI3-RedSea, Panama |
| Views | 18–29 total; **15–25 train / 3–4 test** (LLFF `i mod 8` holdout) |
| Iterations | 30 000, `seathru_from_iter = 10 000`, on every run |

> ⚠️ **Colab Pro is not the benchmark hardware of any source paper.** EDGS, Mini-Splatting and
> CompGS report on dedicated GPUs (CompGS on a single RTX-6000). **Any comparison of this
> thesis's timing or FPS figures against published numbers is directional, not literal**, and
> should be stated as such wherever a source-paper number appears in the same table.

> 🔴 **Each ablation ran on a different Colab VM.** TensorBoard event-file hostnames are
> distinct per configuration — A0 `ed3757dbda43`, A1 `4c4cf0cd2ff0`, A1v2 `ff84c356fe08`,
> A2 `19b4dd385f0f`, A3 `0973c73c9000` `[measured: log filenames]`. Within one ablation all four
> scenes share a VM, so **scene-to-scene comparisons are clean**; but **cross-ablation training
> time and FPS confound mechanism with hardware allocation.** Fidelity, model size and Gaussian
> count are hardware-independent and unaffected. This limitation compounds the draft's own
> caution that "training-time and training-memory conclusions should be interpreted cautiously"
> `[recommended: draft §4.7.1]`.

---

## 8.2 Measured results

Baseline means across the four scenes: **PSNR 27.43 dB**, **2 855 580** primitives,
**194.18 MB**, **2 566 s** training, **44.84 FPS**.

### Fidelity

| Config | Curasao | JapGardens | IUI3 | Panama | **Mean Δ vs A0** |
|---|---:|---:|---:|---:|---:|
| **A0** | 30.13 | 22.83 | 27.55 | 29.22 | — |
| **A1** | 30.97 **+0.84** | 22.47 −0.36 | 26.46 −1.09 | **14.29 −14.93** 🔴 | **−3.89** (−0.21 excl. Panama) |
| **A1v2** | 30.18 +0.05 | 21.59 −1.24 | 27.85 **+0.30** | 21.97 −7.26 🔴 | **−2.04** |
| **A2** | 29.82 −0.32 | 23.32 **+0.49** | 27.76 **+0.21** | 28.63 −0.59 | **−0.05** ✅ |
| **A3** | 29.88 −0.26 | 23.07 **+0.24** | 27.83 **+0.28** | 28.67 −0.56 | **−0.07** ✅ |

### Efficiency

| Config | Primitives | Model size | Size ratio | Train time | Render FPS |
|---|---|---|---|---|---|
| **A0** | 1.81 M – 4.46 M | 123 – 303 MB | 1× | 2 201 – 3 195 s | 30.8 – 50.4 |
| **A1** | **222 860 – 368 742** | 15.2 – 25.1 MB | **7.8× – 16.7×** | 0.89× – 1.24× | **1.11× – 1.75×** |
| **A1v2** | 888 706 – 1 460 514 | 60.4 – 99.3 MB | 1.97× – 4.18× | **0.75× – 1.00×** 🔴 | 1.00× – 1.38× |
| **A2** | **800 000 exactly, all scenes** | **54.4 MB flat** | **2.26× – 5.58×** | **1.10× – 1.33× faster (all 4)** ✅ | **1.32× – 2.06×** ✅ |
| **A3** | unchanged from its own run | 29.9 – 61.2 MB | **4.27× bits/primitive** ✅ | ≈1× (post-hoc) | 1.06× – 1.12×* |

\* confounded — see §8.3. Train-time ratios >1 mean faster than A0.

### The three headline claims, as measured

1. **A2 is near-lossless at a hard budget.** Mean **−0.05 dB** with two of four scenes
   *improving*, at exactly 800 000 primitives on every scene, **2.26–5.58×** smaller,
   **1.10–1.33×** faster to train, **1.32–2.06×** faster to render, and up to **3.76×** less
   peak training VRAM (Curasao: 9.1 GB vs 34.3 GB). This is the strongest result in the study
   and it agrees with the draft's own conclusion `[recommended: draft §5.1.2]`.
2. **A3 is near-lossless at 4.27× storage.** Mean **−0.07 dB** for **68.0 → 15.9 bytes per
   primitive**. ⚠️ The 4.27× exceeds the ~3.4× that uint16 indices alone would give, because
   the archive is `np.savez_compressed` — **zlib entropy coding contributes**. The thesis
   defines model size as the archive `[recommended: draft §3.5.4]`, so the figure is correct
   *as defined*, but it is **not comparable to CompGS's bit-packed `Mem` column** and should
   carry that note.
3. **A1 trades a large, scene-dependent fidelity risk for the largest compaction.**
   **7.8–16.7×** fewer primitives and 15–25 MB models — but Panama collapses by **−14.93 dB**,
   and training is *slower* than baseline on three of four scenes.

### Three findings that qualify the efficiency story

- **A1 does not reliably reduce training time.** It is 1.24× faster only on Curasao (the
  densest baseline); on the other three it is **3–12 % slower**, and A1v2 is **23–25 % slower**
  on three scenes. The expected gain — "~0.5–0.7 hrs vs ~0.9 hrs" `[recommended: plan §12]` —
  **was not realised.** Removing densification does not by itself save wall-clock time when the
  seed population is already large. This should be reported, not omitted.
- **A1's offline preprocessing cost is unaccounted.** RoMa matching over all
  (train views × 3) pairs at 5 000–20 000 matches each, on the *slower* non-`upsample_preds`
  path (delta D-13), is not included in any reported training time. **A1 and A1v2 training
  times are therefore not like-for-like with A0's.**
- **A1v2 peak VRAM is 1.7–7.2× A0's** (44–58 GB vs 6–34 GB). Denser initialization moves the
  memory cost from *late training* to *the entire run*, which matters for the deployment
  framing the thesis invokes.

---

## 8.3 Two confounds that must be stated

**(a) A3's comparison against A0 is not controlled.** A3 does not modify `train.py`, so its
training should reproduce A0's. Final counts `[measured]`:

| Scene | A0 | A3 | Δ |
|---|---:|---:|---:|
| Curasao | 4 462 668 | 3 805 843 | −14.7 % |
| JapaneseGardens | 2 272 131 | 1 913 190 | −15.8 % |
| IUI3-RedSea | 2 877 685 | 2 080 947 | **−27.7 %** |
| Panama | 1 809 834 | 1 876 894 | +3.7 % |

Identical code and flags; counts differ by up to **27.7 %** `[inferred]`. So A3's reported
−0.07 dB **mixes the quantization effect with a ±28 % difference in primitive count**, and A3's
size ratio against A0 (4.12×–5.94×) partly reflects a smaller model, not compression. **The
defensible A3 number is the per-primitive one — 4.27× — because it is internal to a single
run.** The clean fidelity comparison (quantized vs. unquantized from the *same* checkpoint) is
cheap to produce and is not yet reported (§10.2).

**(b) One invalid record.** A3/Curasao carries `training_time_sec = 0` and
`peak_train_vram_mb = 0`. This is a known logging failure, already documented
`[recommended: draft Table 4.13]`. It must be excluded from any mean, not treated as zero.

---

## 8.4 Projected claims — A4 to A7

**No combination configuration has been run.** `[recommended: draft Table 4.13]`: "Only A0, A1,
A1v2, A2, and A3 were completed … Combined mechanisms are not empirically validated."

| Config | `[projected]` expectation | Basis | Confidence |
|---|---|---|---|
| **A6** = A2+A3 | ≈ **9.7–23.8× smaller** than A0 (A2's 2.26–5.58× count reduction × A3's 4.27× bits), ≈ **−0.12 dB** if the two effects are additive | Both measured independently; mechanisms target orthogonal axes; ordering safe by construction (§5.3) | **highest** — the draft names it "promising" `[§4.7.3]` |
| **A4** = A1+A2 | 🔴 **Identical to A1** at A1 density — A1's 222 k–369 k is below the 800 000 budget, and with densification off the count can never rise to meet it | measured counts | **certain, as configured** |
| **A7** = A1+A2+A3 | 🔴 **Identical to A5** at A1 density, for the same reason | measured counts | **certain, as configured** |
| **A5** = A1+A3 | ≈ A1 fidelity × A3's 4.27× storage, **plus** an unquantified risk from opacity quantization over an unpruned `L_op`-suppressed population (§5.3) | analytical only | **low** — the compounding risk is unmeasured |

### The actionable planning consequence

Running A4 and A7 at the A1 density would consume four GPU-days to reproduce A1 and A5 exactly.
**A1v2's counts (888 706 – 1 460 514) are all above the 800 000 budget**, so pairing the
combinations with the A1v2 initialization makes all four cells distinct and the factorial
complete. This costs nothing to decide and should be settled before any combination run is
launched (§10.4).

---

## 8.5 Claim register

| Claim | Status |
|---|---|
| Medium model isolated from all three mechanisms | ✅ **verified in code** (§5) |
| Loss function identical across all 8 configurations | ✅ **verified in code** (§4) |
| A2: −0.05 dB at 2.26–5.58× size, 1.10–1.33× faster training, 1.32–2.06× FPS | ✅ **measured**, 4 scenes |
| A3: −0.07 dB at 4.27× bits/primitive | ✅ **measured**, 4 scenes — ⚠️ fidelity delta confounded (§8.3a) |
| A1: 7.8–16.7× fewer primitives | ✅ **measured** |
| A1: faster training | ❌ **not supported** — slower on 3 of 4 scenes |
| A1: stability depends on scene optical conditions | ✅ **measured** (Panama), **mechanism identified** (§5.2) |
| A4–A7 efficiency gains | ⬜ **projected only** |
| A4 ≡ A1 and A7 ≡ A5 at A1 density | ✅ **provable from measured counts** |
| Deployment relevance (AUV, edge hardware) | ⬜ **inferred**, never tested `[recommended: draft §4.7.2]` |
| Physical correctness of recovered `β^D`, `β^B`, `B^∞` | ⬜ **not validated** — no ground-truth medium parameters exist for these scenes |
