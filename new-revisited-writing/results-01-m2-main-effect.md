# Results — the simplification main effect

**Status.** First complete main effect of the campaign. A0 and A2 are finished at three seeds
across all four scenes (twelve runs each); A1 and A3 have one run each and are reported
separately and provisionally. Every figure is recomputed from run artifacts by
`tools/collect_results.py`.

**Effect sizes are given as the difference divided by the pooled within-group standard
deviation.** No p-values are reported: three seeds on four scenes does not support a formal
test with meaningful power, and quoting one would give a false impression of rigour. `**`
marks |d/sd| > 2, `***` marks > 3.

---

## 1. The headline

**Simplification removes 18.7× of the primitive population. PSNR does not resolve a change.
LPIPS degrades on every scene at effect sizes up to 19 standard deviations.**

| measure | effect | resolvable? |
|---|---|---|
| primitive count | **18.7× fewer** | — |
| PSNR (pooled) | +0.21 dB | **no** — max 1.05 sd |
| SSIM | −0.004 | 2 of 4 scenes `**` |
| **LPIPS** | **+0.048 (worse)** | **all 4** `***` (4.1–19.4 sd) |
| render throughput | **2.69× faster** | all 4 `***` |
| training wall clock | **0.76× (24% faster)** | all 4 `***` |
| peak render memory | **0.385×** | all 4 `***` |

---

## 2. The fidelity metrics disagree, and they disagree in order

This is the section's principal finding.

| scene | ΔPSNR | d/sd | ΔSSIM | d/sd | ΔLPIPS | d/sd |
|---|---:|---:|---:|---:|---:|---:|
| Curasao | +0.392 | 0.76 | +0.0002 | 0.03 | +0.0302 | **4.14** |
| IUI3-RedSea | +0.374 | 1.05 | −0.0127 | **−2.98** | +0.0782 | **13.21** |
| JapaneseGardens | +0.128 | 0.30 | +0.0045 | 0.58 | +0.0305 | **5.43** |
| Panama | −0.060 | −0.14 | −0.0099 | **−2.76** | +0.0539 | **19.44** |
| **mean** | **+0.21** | | **−0.004** | | **+0.048** | |

The three measures do not merely differ in magnitude — **they order by perceptual
sensitivity**:

- **PSNR**, a pixel-wise squared-error measure, shows a small *positive* effect that the
  design cannot resolve.
- **SSIM**, which reads local structure, shows a small negative effect resolvable on two
  scenes.
- **LPIPS**, a deep perceptual measure, shows a large negative effect resolvable on **all
  four**, at up to 19 standard deviations.

The monotone ordering is the interpretation. **Simplification removes detail that is
perceptually relevant and pixel-wise cheap.** Removing high-frequency structure can *lower*
squared error while unambiguously degrading perceived quality, and that is what the three
measures jointly describe.

**Reporting PSNR alone would have inverted the conclusion.** It would have supported "M2
improves fidelity while removing 95% of the model", which the perceptual evidence
contradicts at effect sizes an order of magnitude above the noise. This is the concrete
justification for reporting all three measures rather than leading with PSNR, and it is not a
methodological precaution — it is a result.

---

## 3. Efficiency: large, uniform, and sub-linear

| scene | fps A0 → A2 | ratio | wall clock | peak memory |
|---|---|---:|---:|---:|
| Curasao | 76.0 → 300.9 | 3.96× | 0.686× | 0.330× |
| IUI3-RedSea | 132.8 → 249.8 | 1.88× | 0.798× | 0.396× |
| JapaneseGardens | 131.4 → 388.3 | 2.96× | 0.782× | 0.397× |
| Panama | 130.1 → 307.8 | 2.37× | 0.772× | 0.421× |
| **geometric mean** | | **2.69×** | **0.758×** | **0.385×** |

All three are resolvable on every scene.

### Sub-linearity, quantified

**An 18.7× reduction in primitives buys 2.69× in frame rate.** Expressed as a power law:

```
log(2.69) / log(18.7) = 0.338          frame rate
log(1/0.385) / log(18.7) = 0.326       peak memory
```

Both scale as approximately the **cube root** of primitive count, and the near-identity of
the two exponents is worth noting: it suggests a common cause rather than two coincidences.
The natural reading is that **both quantities are dominated by a component that does not
scale with the population** — rasterisation cost follows covered pixels and tile occupancy,
and peak render memory is dominated by working buffers and context rather than by parameter
storage. At 147,032 primitives the parameters occupy roughly 8 MB while peak render memory is
1,071 MB.

**The practical consequence is a reporting rule.** A primitive-count ratio does not predict a
frame-rate ratio, and any efficiency claim that quotes "18.7× fewer Gaussians" without the
2.69× alongside implies a speedup that does not exist.

### Training time

M2 makes training **24% faster**, resolvable on all four scenes. The mechanism is
straightforward and worth stating so the figure is not over-read: the budget is reached at
iteration 15,000, so the saving is confined to the second half of training. It is not
evidence that simplification accelerates optimisation in general.

---

## 4. Storage

`bytes_per_primitive` is **56.00 for A0 and 56.01 for A2** — identical, as it must be, since
M2 reduces population and does not touch attribute encoding. Total model size therefore falls
by the population ratio, **18.7×**.

The 0.01-byte difference is not noise: it is the fixed per-run overhead (the medium model at
1,058 bytes, plus metadata) amortised over 18.7× fewer primitives. That it appears at all is a
small confirmation that the size accounting is doing what it claims.

---

## 5. What must be qualified

### 5.1 Every A2 group mixes collapsed and intact medium models

All four A2 cell×scene groups are flagged: **six of twelve A2 runs lost an attenuation channel
permanently**, and no group is uniform.

| group | collapsed seeds |
|---|---|
| A2/Curasao | 2 of 3 |
| A2/IUI3-RedSea | 1 of 3 |
| A2/JapaneseGardens | 1 of 3 |
| A2/Panama | 2 of 3 |

**Every number in §2 and §3 is therefore a mean over two physically different models.** No
fidelity metric can separate them, because they score the composed image and a model with
attenuation clamped to unity plus a saturated backscatter term still fits it.

Whether this contaminates the conclusions depends on which conclusion. The LPIPS effect
(4.1–19.4 sd) and the efficiency effects (3.2–26.9 sd) are far too large to be artifacts of
the mixture. **The PSNR non-result is more exposed**: an effect already below the noise floor
cannot be defended against a covariate that splits the group.

The remedy is not to re-run — it is to report the effect **split by collapse state** once
enough runs exist to do so. At six collapsed and six intact that is three per side per two
scenes, which is not yet enough.

### 5.2 The frame-rate figures mix profiling sample sizes

A0's runs were profiled before the timing sample was raised (`render_frames_timed: 9`); later
runs use 60 frames. A0's frame-rate dispersion — 11.5% and 17.8% CV on two scenes — is
therefore partly a small-sample artifact rather than genuine run-to-run variation. The
direction and magnitude of the effect survive this easily; the exact ratios should not be
quoted to three significant figures.

### 5.3 Scene difficulty spans 7 dB

A0's test PSNR ranges from **23.01** (JapaneseGardens) to **30.15** (Curasao). Any
scene-averaged fidelity figure conceals that range, which is why every table here is reported
per scene first.

---

## 6. What this retires

**The prior manuscript's headline claim cannot be sustained.** It reported *"budget pruning
gives the best overall balance, reducing model size and Gaussian count by about 72% with a
0.05 dB average PSNR decrease."*

Three independent problems, all now measured:

1. **The mechanism was not the one named.** The prior implementation scored importance as
   `opacity × scale` and selected by deterministic top-k — the procedure Mini-Splatting's own
   paper rejects. `[discrepancy D-1]`
2. **0.05 dB is an order of magnitude below the noise floor.** A0's per-scene PSNR standard
   deviation is **0.22–0.70 dB**. This design resolves roughly ±0.5 dB at three seeds; the
   claimed effect is a tenth of that, and it was reported from single runs.
3. **The fidelity conclusion inverts under a perceptual measure.** LPIPS degrades on every
   scene at up to 19 sd. A claim of near-free compression rests entirely on the choice of
   metric.

The correctly-implemented mechanism achieves a **larger** reduction than was claimed — 18.7×,
against 72% (3.6×) — and the honest fidelity statement is *no resolvable PSNR change, a small
SSIM cost, and a substantial perceptual cost.*

---

## 7. Provisional: M3 and M1 at n=1

Reported because they bear on stated hypotheses, and explicitly **not claims**. Both are single
runs on Curasao, against A0's three-seed Curasao distribution.

### M3 (A3) — quantization

| measure | A0 (n=3) | A3 (n=1) | d/sd |
|---|---:|---:|---:|
| bytes/primitive | 56.00 | **20.54** | — |
| PSNR | 30.15 ± 0.70 | 29.44 | −1.02 |
| render fps | 76.03 ± 8.75 | 74.59 | **−0.16** |
| peak render memory | 3241 ± 361 | 3658 | +1.15 |

**H2 is supported, and the direction is exactly as predicted.** M3 delivers **2.73×** storage
compression and **no frame-rate gain whatsoever** (−0.16 sd). This was predicted before the
run on the grounds that CompGS-VQ's published speedup is credited by its own authors to an
opacity regulariser this study disables (CD-8), and that at `sh_degree = 0` only ten of
fourteen floats are quantizable.

Note also that peak render memory does **not** fall: the model is dequantized for rendering,
so M3 buys storage and nothing else.

### M1 (A1) — dense initialization

| measure | A0 (n=3) | A1 (n=1) | d/sd |
|---|---:|---:|---:|
| primitives | 3,757,808 | 299,196 | 12.6× fewer |
| PSNR | 30.15 ± 0.70 | 30.97 | +1.17 |
| render fps | 76.03 ± 8.75 | 102.37 | **+3.01** |
| training wall clock | 4457 ± 253 | 5088 | **+2.49** |
| peak render memory | 3241 ± 361 | 1245 | **−5.53** |

The fidelity difference is **not resolvable** even at 1.17 sd, so the earlier reading that
"A1 beats A0" is not supportable — the honest statement is *no resolvable fidelity change at
12.6× fewer primitives*, which remains a strong efficiency result.

**Training is slower, and the effect is resolvable at 2.49 sd even from one run.** A1 has 93%
fewer primitives and takes 14% longer. No claim that M1 accelerates training is available, and
the mechanism is not yet identified.

`A1/Curasao/s0` also lost two attenuation channels at the seathru boundary — a different route
to collapse than M2's, since A1 has no simplification event. Whether it recurs is the most
useful thing the remaining eleven A1 runs will tell us.

---

## 8. What the remaining runs are needed for

| | |
|---|---|
| **S3 (A1, A3)** | Turns §7 from provisional into main effects. Highest value. |
| **Collapse split** | With more runs, report M2's effect separately for collapsed and intact seeds — the only way to know whether the PSNR non-result survives the covariate. |
| **S4, S5** | The interactions, which carry roughly twice the variance of a main effect and may not resolve. |

**One thing already will not resolve**: whether any of these mechanisms is preferable at a
given operating point. Each is measured at a single budget and a single codebook size, so the
design supports statements about interaction and not about ranking. A rate–distortion sweep
remains the highest-value extension.
