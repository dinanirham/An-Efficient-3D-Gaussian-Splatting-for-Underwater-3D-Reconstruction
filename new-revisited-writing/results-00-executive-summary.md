# Executive summary — main effects, 48 runs

**Scope.** Four configurations complete at three seeds across four scenes: the baseline (A0)
and each efficiency mechanism in isolation — A1 initialization, A2 simplification, A3
quantization. Interaction cells A4–A7 are in progress and nothing here speaks to them.

---

## 0. How these results must be read

**Per scene. Never pooled.** This is a methodological requirement, not a presentational
preference, and two measurements force it:

**Scene difficulty spans 7.1 dB.** The baseline reaches 30.15 dB on Curasao and 23.01 on
JapaneseGardens. A scene-averaged fidelity figure describes no scene in the corpus.

**Baseline dispersion varies five-fold across scenes** — 6.0% on JapaneseGardens, 29.3% on
Panama. A pooled variance understates the stable scenes and overstates the noisy ones, so an
effect that resolves on one scene may be invisible on another *for reasons of measurement
rather than mechanism*.

Effects are therefore reported per scene with their own dispersion, and each carries `d/sd`
against the pooled within-cell standard deviation **for that scene**. `**` marks |d/sd| > 2,
`***` marks > 3. **No p-values** — three seeds on four scenes cannot support a formal test
with meaningful power. An effect that resolves nowhere is *unresolved*, not zero.

---

## 1. Fidelity, per scene

### PSNR (mean ± sd, n=3)

| scene | A0 | A1 init | A2 prune | A3 quant |
|---|---|---|---|---|
| Curasao | 30.153 ± 0.697 | 30.631 ± 0.425 | 30.545 ± 0.221 | 29.786 ± 0.568 |
| IUI3-RedSea | 26.888 ± 0.486 | 27.539 ± 0.328 | 27.262 ± 0.138 | 27.242 ± 0.253 |
| JapaneseGardens | 23.014 ± 0.220 | 23.700 ± 0.196 | 23.142 ± 0.568 | 23.191 ± 0.134 |
| Panama | 28.751 ± 0.619 | 28.946 ± 0.418 | 28.692 ± 0.099 | 29.158 ± 0.155 |

**Effect against baseline:**

| scene | A1 | A2 | A3 |
|---|---|---|---|
| Curasao | +0.478 (0.8) | +0.392 (0.8) | −0.367 (−0.6) |
| IUI3-RedSea | +0.651 (1.6) | +0.374 (1.0) | +0.354 (0.9) |
| **JapaneseGardens** | **+0.687 (3.3)** `***` | +0.128 (0.3) | +0.177 (1.0) |
| Panama | +0.195 (0.4) | −0.060 (−0.1) | +0.407 (0.9) |

**One PSNR effect resolves anywhere in the campaign**: M1 on JapaneseGardens. Every other
fidelity difference is inside the noise of the scene it was measured on.

### LPIPS — where the mechanisms actually separate

| scene | A1 | A2 | A3 |
|---|---|---|---|
| Curasao | +0.0001 (0.0) | **+0.0302 (4.1)** `***` | +0.0031 (0.4) |
| **IUI3-RedSea** | **+0.0573 (27.1)** `***` | **+0.0782 (13.2)** `***` | **+0.0257 (8.6)** `***` |
| JapaneseGardens | −0.0064 (−1.2) | **+0.0305 (5.4)** `***` | +0.0012 (0.2) |
| Panama | **+0.0150 (2.1)** `**` | **+0.0539 (19.4)** `***` | −0.0009 (−0.2) |

**A2 degrades perceptual quality on all four scenes. A1 on two. A3 on one.** These are the
largest effect sizes in the campaign, and none of them is visible in the PSNR table above.

---

## 2. Efficiency, per scene

| scene | A0 size | A1 | A2 | A3 |
|---|---:|---|---|---|
| Curasao | 200.7 MiB | 13.0 (**15.5×**) | 7.9 (**25.6×**) | 62.5 (3.2×) |
| IUI3-RedSea | 135.5 | 11.8 (11.5×) | 7.3 (18.6×) | 51.5 (2.6×) |
| JapaneseGardens | 119.4 | 12.3 (9.7×) | 7.7 (15.4×) | 57.0 (2.1×) |
| Panama | 123.2 | 10.5 (11.8×) | 7.4 (16.6×) | 37.2 (3.3×) |

**Reductions are not a single number.** A1 ranges 9.7–15.5×, A2 15.4–25.6×, A3 2.1–3.3×. The
budget is absolute, so M2 reduces most where the baseline converges highest — the ratio partly
measures the *baseline*, not the mechanism.

### Render throughput (fps)

| scene | A0 | A1 | A2 | A3 |
|---|---|---|---|---|
| Curasao | 76.0 ± 8.7 | 193.4 ± 14.0 | 300.9 ± 8.0 | 100.7 ± 23.6 |
| IUI3-RedSea | 132.8 ± 7.6 | 179.1 ± 22.7 | 249.8 ± 51.3 | 139.6 ± 6.0 |
| JapaneseGardens | 131.4 ± 4.7 | 265.1 ± 10.0 | 388.3 ± 27.3 | 134.6 ± 7.2 |
| Panama | 130.1 ± 23.1 | 221.3 ± 20.4 | 307.8 ± 34.2 | 145.4 ± 21.6 |

A1 and A2 resolve on all four scenes. **A3 resolves on none** — quantization delivers storage
and no rendering benefit, exactly as predicted in advance from the zero-order colour
representation and a deliberately disabled opacity regulariser.

---

## 3. Geometry, per scene

Measured from the stored point cloud, **seed 0 only** — the model is written for one seed per
cell. This is the only instrument in the study that reads geometry rather than photometry, and
it exists because SeaSplat's degeneracy D-4 — primitives placed near the camera to reproduce
veiling haze as geometry — is photometrically *excellent* and invisible to every fidelity
measure above.

### Box occupancy — the share of the bounding box containing anything

| scene | A0 | A1 | A2 | A3 |
|---|---|---|---|---|
| Curasao | **0.04%** | 0.96% | 1.90% | 0.10% |
| IUI3-RedSea | 0.51% | 1.63% | 2.10% | 2.97% |
| **JapaneseGardens** | **3.70%** | 0.89% | 2.95% | 4.71% |
| Panama | 0.46% | 1.11% | 1.11% | 0.44% |

### Rendered fraction — primitives above the visibility threshold

| scene | A0 | A1 | A2 | A3 |
|---|---|---|---|---|
| Curasao | 25.8% | 86.7% | 94.2% | 24.3% |
| IUI3-RedSea | 41.5% | 94.1% | 89.4% | 27.6% |
| JapaneseGardens | 32.9% | 86.4% | 96.1% | 29.5% |
| Panama | 43.6% | 77.2% | 92.6% | 40.8% |

### Detached population beyond five times the median radius

| scene | A0 | A1 | A2 | A3 |
|---|---|---|---|---|
| Curasao | 0.00% | 0.65% | 0.40% | 0.87% |
| **IUI3-RedSea** | **1.69%** | 0.22% | 0.00% | 0.00% |
| JapaneseGardens | 0.00% | 1.11% | 0.00% | 0.00% |
| **Panama** | **6.61%** | 0.13% | 0.00% | 5.83% |

**Three results here.**

**The baseline carries three different geometric states, not one.** Curasao has an *invisible
halo* — 0.04% occupancy with only 25.8% rendered, and opacity gating raises its occupancy
77-fold. IUI3-RedSea and Panama carry *detached rendered clusters*, 1.69% and 6.61% of
primitives sitting beyond ten times the median radius with nothing in between. JapaneseGardens
has **neither**.

**A3 reproduces the baseline's pathology and A1/A2 remove it.** A3 does not touch geometry, and
its numbers track A0's — including Panama's 5.83% detached against A0's 6.61%. That is the
control confirming the instrument reads geometry rather than an artefact of primitive count.

**JapaneseGardens is the control scene.** It is the only scene where the baseline's geometry is
sound, and the only one where **both** A1 and A2 have *lower* occupancy than the baseline
(0.89% and 2.95% against 3.70%). Where there is no pathology, neither mechanism improves the
spatial description.

---

## 4. What each scene is

| | Curasao | IUI3-RedSea | JapaneseGardens | Panama |
|---|---|---|---|---|
| baseline PSNR | 30.15 | 26.89 | **23.01** | 28.75 |
| baseline dispersion | 14.7% | 9.6% | **6.0%** | **29.3%** |
| pathology | invisible halo | detached 1.69% | **none** | **detached 6.61%** |
| M1's PSNR gain | +0.478 | +0.651 | **+0.687** `***` | **+0.195** |
| M2's LPIPS cost | +0.0302 | **+0.0782** | +0.0305 | +0.0539 |
| A2 medium collapse | 2/3 | 1/3 | 1/3 | 2/3 |

### Two cross-scene patterns, offered as observations

**M1 helps most where the baseline is geometrically soundest.** Its largest and only resolvable
PSNR gain is on JapaneseGardens (no pathology, lowest dispersion); its smallest is on Panama
(6.61% detached, highest dispersion).

That inverts the naive expectation, and D-4 supplies a mechanism: **detached floaters are
photometrically rewarded.** They reproduce veiling haze as geometry, so the baseline's PSNR on
Panama is partly purchased with them. M1 removes them — 6.61% to 0.13% — and loses that crutch
along with the pathology. The measured gain understates what it did to the model.

**M2's perceptual cost is largest where the baseline has detached clusters.** IUI3-RedSea and
Panama, the two scenes with a detached population, carry M2's largest LPIPS effects.

**Both are four-point observations and neither is a claim.** Each is consistent with a stated
mechanism, but four scenes cannot distinguish a mechanism from a coincidence, and the geometry
is a single seed.

### One scene behaves unlike the others

**IUI3-RedSea is where PSNR and LPIPS disagree most sharply.** M1 produces its second-largest
PSNR gain there (+0.651) *and* the largest LPIPS degradation in the entire campaign (+0.0573 at
27.1 sd). All three mechanisms record their worst LPIPS on that scene. It is also the only
scene where the medium model's attenuation coefficients are ordered B > G > R rather than the
physically expected R > G > B — **in the baseline as well as in every mechanism**, so it is a
property of the scene rather than of anything this study does. Why is unresolved.

---

## 5. The medium model

| cell | runs intact | largest β drop | where the drop lands |
|---|---|---|---|
| A0 | **12 / 12** | 4.8–33.6% | the medium warm-up |
| A1 | **12 / 12** | 3.6–44.0% | scattered, no boundary |
| **A2** | **6 / 12** | **25–195%** | **a simplification boundary, 12 of 12** |
| A3 | **12 / 12** | 6.4–38.8% | the medium warm-up |

Failures by scene: Curasao 2/3, IUI3-RedSea 1/3, JapaneseGardens 1/3, Panama 2/3.

**The collapse is not scene-conditioned.** It occurs on every scene and spares at least one seed
on every scene. The same configuration on the same scene collapses on one seed and survives on
another — a **bistable** outcome of a stochastic process.

**The discontinuity is the mechanism, not the count.** A1 converges to ~222,000 primitives and
A2 to ~142,000 — comparable populations, opposite outcomes. A population low from the start
lets the medium parameters be fitted to it; a population cut by 94% at iteration 15,000, after
those parameters have converged against a different depth distribution, breaks them.

---

## 6. Research questions

**RQ1 — do the mechanisms individually transfer?** Answered. All three run to convergence and
produce their intended effect, but not equally. M1 carries the only positive and resolvable
fidelity effect and leaves the medium model intact in all twelve runs. M2 buys the largest
reduction and is the only mechanism that breaks the physics. M3 delivers storage and nothing
else — no frame-rate gain on any scene, no memory reduction, training 5% slower.

**RQ2 — do they compose additively or interact?** Not yet answerable. One early signal: A4
(M1+M2) has lost no attenuation channel where M2 alone loses half.

**RQ3 — does population reduction perturb medium identifiability?** Answered, and more sharply
than the hypothesis stated: the operative variable is the discontinuity, not the resulting
size.

**RQ4 — what integration properties govern the composition?** Five documented, every one found
by running the pipeline rather than analysing it — including a defect in a published method
whose own stated remedy cannot detect the degeneracy it names, and which accounted for 95% of
all rejected triangulations on this corpus.

---

## 7. Cross-cutting findings

**PSNR cannot rank these mechanisms; LPIPS can.** One PSNR effect resolves in the entire
campaign. Eight LPIPS effects resolve, and they order the mechanisms cleanly. The conclusion
inverts with the choice of metric, which is why all three fidelity measures are reported and
none is used alone.

**A primitive-count ratio does not predict a speedup.** 11.9× fewer primitives buys 1.83× the
frame rate; 18.7× buys 2.65×. Sub-linear, and by different exponents — per-primitive
rasterisation cost is not constant across cells.

**Most of the baseline is invisible.** It renders 25.8–43.6% of its primitives depending on
scene; the reduced cells render 77–96%. The honest reduction figure is therefore
**15.4–25.6× for storage** and roughly **6.7× for scene representation**.

**M1 nearly eliminates run-to-run variance.** Dispersion on primitive count falls from
6.0–29.3% to **0.18–1.16%**. Densification never runs under M1, so the amplification that
drives the baseline's dispersion has nothing to act on. This scopes an earlier claim of this
study: "a single-run ratio carries no information" is true of the *baseline*, not of M1.

**Same-seed reproducibility has a wide tail.** Twelve matched-seed A0/A3 pairs — identical
processes until after the population freezes — differ by a median of 21.1% and a maximum of
**58.8%**. Interaction terms carry roughly twice a main effect's variance, so `UNDETERMINED` is
a likely outcome for S4 and S5, and that is a different finding from a null.

---

## 8. What cannot be concluded

- **Nothing about interactions.** A4–A7 are incomplete.
- **Nothing about operating points.** One budget, one codebook size. The design answers whether
  the mechanisms interact; it cannot show a ranking persists across budgets.
- **Nothing about deployment.** No embedded hardware, power, latency or memory constraint
  tested.
- **Nothing beyond four scenes and thirteen held-out frames**, whose behaviour differs enough
  that scene-averaged figures were removed from this summary.
- **The geometry is one seed per cell.** A0 and A3 at matched seeds differ by up to 56% in
  primitive count, so the geometric comparison between them carries that confound.
- **The A2 aggregates mix two populations.** All four A2 scene groups contain both collapsed
  and intact medium models. The perceptual and efficiency effects are far too large to be
  artefacts of that; **the PSNR non-result is more exposed**, since an effect already below the
  noise floor cannot be defended against a covariate that splits the group.

---

## 9. Provisional ranking

**M1 transfers best.** The only positive and resolvable fidelity effect, perceptual quality at
baseline on two of three complete scenes, an intact medium model in all twelve runs,
near-deterministic behaviour, 9.7–15.5× reduction. It costs a preprocessing stage the others do
not — 35–53 s per scene, excluded from the training clock and reported separately.

**M2 buys the most reduction and is the only mechanism that breaks the physics.** Whether that
matters depends on what the model is for: a reconstruction judged on composed-image fidelity
tolerates it; one whose medium parameters are the scientific output does not.

**M3 is cheap, safe and small.** The only mechanism whose result was predicted exactly in
advance, and the only one delivering a single-axis benefit with no side effects.

**Provisional.** The interaction cells could change this ordering — particularly if M1 proves
to protect M2's medium model.
