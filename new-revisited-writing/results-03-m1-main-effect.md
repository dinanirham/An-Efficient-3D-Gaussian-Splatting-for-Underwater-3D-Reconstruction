# Results — the dense-initialization main effect

**Status.** A0 complete at three seeds across four scenes. A1 complete on three
scenes, **n=1 on Panama**, which matters because Panama is the one scene where the
sign of the fidelity effect reverses. Every figure is recomputed from run
artifacts by `tools/collect_results.py` and `tools/medium_collapse.py`.

**These are runs against the corrected initializer** (CD-26). The prior A1 runs
are void: 13–41% of the initialization was ill-conditioned geometry, and on
Curasao that drove two attenuation channels permanently dead.

Effect sizes are the difference over the pooled within-group standard deviation.
No p-values: three seeds on four scenes does not support a formal test with
meaningful power. `**` marks |d/sd| > 2, `***` marks > 3.

---

## 1. Fidelity

| scene | A0 | A1 | ΔPSNR | d/sd | ΔLPIPS | d/sd |
|---|---:|---:|---:|---:|---:|---:|
| Curasao | 30.153 | 30.631 | **+0.478** | 0.83 | +0.0001 | 0.01 |
| IUI3-RedSea | 26.888 | 27.539 | **+0.651** | 1.57 | **+0.0573** | **27.13** `***` |
| JapaneseGardens | 23.014 | 23.700 | **+0.687** | **3.30** `***` | −0.0064 | −1.20 |
| Panama `[n=1]` | 28.751 | 28.492 | −0.259 | — | +0.0262 | — |
| **mean (3 scenes)** | | | **+0.605** | | +0.0170 | |

**PSNR is higher on every complete scene**, and resolvable on JapaneseGardens.
That is the first fidelity *improvement* the campaign has resolved.

**LPIPS is where M1 separates from M2.** Curasao is unchanged, JapaneseGardens
is *better*, and only IUI3-RedSea is worse. The contrast with simplification is
the substantive comparison:

| | reduction | PSNR | LPIPS |
|---|---|---|---|
| **M1** | ~12× | +0.605 dB | ≈ baseline (1 of 3 scenes worse) |
| **M2** | ~19× | +0.209 dB (unresolvable) | **worse on all four**, 4.1–19.4 sd |

**M1 buys a smaller reduction at roughly baseline perceptual quality; M2 buys a
larger one at a substantial perceptual cost.** Reporting PSNR alone would make
them look similar. They are not.

---

## 2. Efficiency

| scene | primitives A0 → A1 | × fewer | fps A0 → A1 | Δfps | d/sd |
|---|---|---:|---|---:|---:|
| Curasao | 3,757,808 → 243,099 | 15.5× | 76.0 → 193.4 | +117.4 | **10.03** `***` |
| IUI3-RedSea | 2,537,851 → 220,898 | 11.5× | 132.8 → 179.1 | +46.3 | **2.74** `**` |
| JapaneseGardens | 2,235,661 → 229,973 | 9.7× | 131.4 → 265.1 | +133.8 | **17.08** `***` |
| Panama `[n=1]` | 2,305,920 → 196,773 | 11.7× | 130.1 → 205.2 | +75.1 | — |

Roughly **12× fewer primitives** and **+99 fps** on average, resolvable on every
complete scene.

Sub-linear again, and by a similar exponent to M2's: a 12× reduction buys about
1.8×, giving `log(1.8)/log(12) ≈ 0.24`. **A primitive-count ratio does not
predict a frame-rate ratio**, and the two mechanisms agree on that despite
differing in almost everything else.

---

## 3. M1 nearly removes run-to-run variance

This was not anticipated and is the most methodologically consequential result
here.

| scene | A0 CV | **A1 CV** | ratio |
|---|---:|---:|---:|
| Curasao | 14.7% | **1.16%** | 13× |
| IUI3-RedSea | 9.6% | **0.18%** | **52×** |
| JapaneseGardens | 6.0% | **0.94%** | 6× |

**Converged primitive count becomes nearly deterministic under M1.**

The mechanism is structural. §13.6 attributes the baseline's dispersion to
amplification: a primitive lands either side of `densify_grad_threshold` from run
to run, changing the population that feeds the next densification event, and the
schedule performs that event 144 times. **Under M1 densification never runs.**
The count is fixed by a hashed cloud and reduced only by opacity pruning, so
there is nothing to amplify.

**This bounds a claim made earlier in this study.** §13.6 states that "a
single-run ratio on primitive count carries no information at all". That is
true *of the baseline*, and it is the reason the prior manuscript's headline was
withdrawn. It is **not** true under M1, where three seeds agree to within 0.2%
on one scene. The claim must be scoped to the configuration it was measured on.

---

## 4. The medium model

| cell | runs | lost an attenuation channel | largest β drop | where |
|---|---:|---:|---|---|
| A0 | 12 | **0** | 4.8–33.6% | mostly the seathru warm-up |
| **A1** | **10** | **0** | **3.6–11.4%** (one outlier at 38.9%) | scattered, no intervention |
| A2 | 12 | **6** | 25–195% | **on a simplification boundary, 12/12** |

**No A1 run lost a channel**, and its perturbations are an order of magnitude
smaller than A2's and land at no particular iteration — which is what drift looks
like, and A1 has no intervention boundary for them to land on.

### This sharpens H4

A1 and A2 converge to comparable populations — roughly 230k against 145k — yet
one leaves the medium model intact and the other breaks it in half its runs.
**The count is therefore not the operative variable; the discontinuity is.**

A population that is *low from the start* lets β be fitted to it. A population
that *drops discontinuously at iteration 15,000*, after β has already been fitted
to a different one, does not. That is a sharper statement of H4 than the
hypothesis made, and it is available only because both cells exist.

### Two supporting observations

**β_att is 1.2–3.4× higher under A1**, consistent with the medium model
absorbing what a smaller population of geometry cannot explain — the same
coupling as H4, acting continuously rather than as a shock.

**`A1/IUI3-RedSea/s2` is the first run in the campaign** with neither a collapsed
channel nor saturated backscatter. Backscatter saturation has otherwise been
universal, including in every baseline run, so it is a property of the baseline
rather than of any mechanism `[§13.10]`.

**β_att is ordered R > G > B on 8 of 10 A1 runs**, which is physically correct
for water. The exceptions are both on IUI3-RedSea — where the *baseline* also
inverts on two of its three seeds, so it is a scene property, not an M1 artefact.
Why that scene inverts is unresolved and is recorded as an open question.

---

## 5. What must be qualified

**Panama is n=1, and it is the only scene where the PSNR effect reverses**
(−0.259 dB). It is also the scene with the baseline's largest dispersion (29.3%
CV on primitive count) and the largest detached-floater fraction (6.61%,
`[results-02 §2a]`). **The two remaining Panama runs carry more weight than the
rest of S3**, and no scene-averaged M1 figure should be quoted until they exist.

**IUI3-RedSea's LPIPS is 27 sd worse**, which is the single largest fidelity
effect measured in the campaign and sits alongside M1's *best* PSNR gain on that
same scene. PSNR and LPIPS disagree in direction there, as they did for M2 but in
the opposite arrangement. That is unexplained.

**A1's dispersion being small does not make its effects significant.** The
pooled standard deviation is dominated by A0's, so the effect sizes above are
essentially "how large is this against baseline noise", and only JapaneseGardens
clears 2 sd on fidelity.

**These are runs against one cloud generation.** The clouds were regenerated with
CD-26 and are hashed in every manifest; comparisons against the prior A1 runs are
invalid and those runs are archived rather than deleted.

---

## 6. Where this leaves the three mechanisms

| | reduction | PSNR | LPIPS | fps | medium model | dispersion |
|---|---|---|---|---|---|---|
| **M1** | ~12× | +0.61 dB | ≈ baseline | +99 | **intact 10/10** | **near-zero** |
| **M2** | ~19× | +0.21 dB (ns) | **worse, 4–19 sd** | +170 | **broken 6/12** | low |
| **M3** `[n=1]` | 2.73× storage only | −0.71 dB (ns) | +0.005 | **no gain** | intact 1/1 | — |

On present evidence **M1 is the mechanism that transfers best**: the largest
fidelity gain, perceptual quality at baseline, an intact medium model in every
run, and near-deterministic behaviour. It buys less reduction than M2 and it
costs a preprocessing stage the others do not — 35–53 s per scene, excluded from
the training wall clock and reported separately, or M1's cost is understated.

**This ordering is provisional.** S3 is not complete, the interaction cells have
not run, and no mechanism has been evaluated at more than one operating point —
so nothing here supports a claim that the ranking persists across budgets.
