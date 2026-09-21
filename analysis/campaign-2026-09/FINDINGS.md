# Findings — campaign 2026-09

*Written section by section against `PLAN.md`, in order. Each section states what was
computed, what the plan predicted, and whether the prediction held. Numbers are per scene.
`UNRES` means |effect| < 2 SE and is a finding about resolution, not about the mechanism.*

---

## §0. Provenance and the noise floor

**Completeness.** 120 rows, 12 per cell, all flagged complete. Scenes 4, seeds 3. `medium_collapse`
covers all 120; 48 carry dispersion ratios (the M2 cells); 12 are final-state-only (SS).

**Provenance.** `effective_optimizer_steps` is 43 000 on every non-M2 cell and 43 400 on every M2
cell — exactly D-8's accounting plus two CD-6 bursts of 200. GPU is A100-SXM4-40GB on all 108
trained cells; SS's 12 are blank because `measure_reference` does not record it.

**Ledger.** 120 of 120 `done`, one stage per cell, 15–21 September 2026, one GPU type
throughout, 107 GPU-hours in total (9–13 h per cell). Four runs needed more than one attempt
(A0/JG s0, A3/JG s2, A6/JG s0 twice; A3/IUI3 s1 three times), each with an empty error field —
the Colab disconnect signature — and each completed on the retry that is in the table. The
ledger carries no commit sha.

**`git_commit` is empty in every row, and the reason is now known:** every run directory
holds a `run_config.json` with `git_sha` at the top level, and the collector read
`cfg["git"]["commit"]`, a key the manifest never wrote. Fixed in `collect_results.provenance()`
(verify_collect_results T1–T4); the column populates on the next `02_analysis` run. Until then
the one-code-version claim rests on the ledger's span and the worker log. The sampled manifest
from the archived campaign (`run_config_A3_Curasao_s0.json`, 10 Sept) reads
`3c165ae1c-dirty` — **a dirty tree** — which §11 needs.

**Noise floor — A0's per-scene sd over three repeats, this campaign.** Supersedes the prior.

| scene | PSNR sd | LPIPS sd | count CV | *prior count CV* |
|---|---:|---:|---:|---:|
| Curasao | 0.395 | 0.0025 | 8.6% | 14.7% |
| IUI3-RedSea | 0.245 | 0.0013 | 12.5% | 9.6% |
| JapaneseGardens | 0.126 | 0.0050 | **34.3%** | 6.0% |
| Panama | 0.481 | 0.0091 | **36.6%** | 29.3% |

PSNR and LPIPS dispersion match the prior range. **Count dispersion widened on two scenes** —
JapaneseGardens from 6% to 34%. At n=3 one outlier run moves the CV hard, and E.22 measured
same-seed non-determinism at a 21% median with a 59% tail, so 34% is inside what the process
produces. But it widens the floor for every count contrast on those scenes. Carried to §11
and §14 as written.

## §1. Baseline replication — PRE, held

All four scenes WITHIN MARGIN. Largest PSNR gap 0.245 dB and largest LPIPS gap 0.0067 — both
inside A0's own noise floor above. Count within, JapaneseGardens at 74% of the ±30% allowance.
A0 is equivalent to vanilla SeaSplat to within the pre-registered margin, on the metrics every
downstream contrast uses. **And neither A0 nor SS lost an attenuation channel in any of 24 runs
(§2 below)** — the baseline and its reference are both stable, which is the precondition for
attributing any collapse to a mechanism.

## §2. Main effects — PRE (H1), held on every target cost

**From below (Ax − A0), per scene. Effect, then z = effect/SE; `UNRES` below 2.**

**M1 — dense initialisation (A1).**

| scene | count | wall-clock | PSNR | LPIPS |
|---|---:|---:|---:|---:|
| Curasao | ×0.06 (−19.0) | −1096 s (−15.5) | +0.60 (1.7) UNRES | +0.002 UNRES |
| IUI3 | ×0.08 (−12.8) | −227 s (−4.3) | +0.21 (1.3) UNRES | **+0.059 (+48.4)** |
| JapaneseGardens | ×0.09 (−4.6) | −628 s (−6.1) | **+0.80 (+7.4)** | +0.000 UNRES |
| Panama | ×0.10 (−4.3) | −555 s (−2.8) | **+0.72 (+2.4)** | +0.006 UNRES |

M1 cuts the population **10–16×** on every scene, resolved on all four, and trains faster on all
four. PSNR is positive on every scene and resolves on two; **Panama, which reversed at n=1 in the
old campaign, now resolves positive at +0.72 dB.** LPIPS is at baseline on three scenes and
**48 SE worse on IUI3-RedSea** — the one place M1 costs perceptual quality, and it costs it
sharply.

**M2 — importance-weighted simplification (A2).**

| scene | count | fps | PSNR | LPIPS |
|---|---:|---:|---:|---:|
| Curasao | ×0.04 (−19.5) | ×3.51 (+15.7) | **+0.74 (+2.3)** | **+0.033 (+22.4)** |
| IUI3 | ×0.05 (−13.2) | ×1.90 (+15.1) | −0.26 (−1.4) UNRES | **+0.082 (+44.7)** |
| JapaneseGardens | ×0.05 (−4.8) | ×2.67 (+9.4) | **+0.53 (+2.6)** | **+0.032 (+7.7)** |
| Panama | ×0.07 (−4.4) | ×1.89 (+6.4) | +0.01 (0.0) UNRES | **+0.054 (+7.3)** |

**14–25× fewer primitives, 1.9–3.5× fps, and LPIPS worse on all four scenes at 7–45 SE** —
E.11 and E.21 replicate exactly. PSNR *improves* on two scenes at 2+ SE, which the old campaign
(max 1.05 sd) did not resolve. fps gain is sub-linear in count reduction: 25× → 3.5× on Curasao,
20× → 1.9× on IUI3, and the exponent differs by scene (E.9).

**M3 — quantization-aware VQ (A3).**

| scene | bytes/prim | fps | PSNR | LPIPS |
|---|---:|---:|---:|---:|
| Curasao | ×0.37 | ×1.21 UNRES | +0.38 UNRES | +0.005 (+2.5) |
| IUI3 | ×0.37 | ×0.94 UNRES | **−1.36 (−4.0)** | **+0.028 (+19.7)** |
| JapaneseGardens | ×0.37 | ×1.05 UNRES | **+0.59 (+3.1)** | −0.003 UNRES |
| Panama | ×0.37 | ×0.84 UNRES | +0.24 UNRES | +0.000 UNRES |

**2.72× compression on every scene; no frame-rate change on any** — the prediction registered
from CD-8 and `sh_degree = 0` before the instrument existed holds. bytes/prim is deterministic
(56.0 → 20.6) and is reported as a structural fact, not a test. Fidelity is scene-specific:
**a resolved 1.36 dB loss and +0.028 LPIPS on IUI3-RedSea**, a resolved gain on JapaneseGardens,
unresolved elsewhere.

**From above (A7 − A_without), the other inference direction.**

| | count | PSNR | LPIPS |
|---|---|---|---|
| **M1** (A7−A6) | ×0.84–0.88, resolved ×4 | +0.09 to +0.77, resolved on 3 | better on 2 (JG, Panama), resolved |
| **M2** (A7−A5) | ×0.52–0.60, resolved ×4 | −0.27 to +0.26, resolved on 1 | **worse on all 4, resolved (+0.03)** |
| **M3** (A7−A4) | bytes ×0.39 | IUI3 −0.48 resolved; JG +0.39 | **worse on all 4, resolved (+0.016–0.030)** |

**The two directions disagree on count, and the disagreement is the interaction.** M1 cuts count
16× from below and 1.15× from above; M2 cuts 20× from below and 1.8× from above. Once either is
present, the other has far less to remove — M2's budget of 200 000 caps whichever cell reaches it.
That is H5's degeneracy *not* occurring (the budget bound, so the cells are distinct) but its
sub-additivity occurring exactly as §8.4 predicted. Formalised in §3.

**M3's LPIPS cost is larger when stacked than alone** — unresolved on three scenes from below,
resolved worse on all four from above. That is the direction H3 predicts, and it is formalised in
§3.

**H1 verdict.** Each mechanism moves its own target cost beyond seed dispersion on every scene.
**Supported.** All three old-campaign directional priors replicated; one (M1 on Panama) improved
from unsettled to resolved positive.

**A scene finding.** IUI3-RedSea is where every mechanism costs perceptual quality — M1 +0.059,
M2 +0.082, M3 +0.028 LPIPS, each at 20–48 SE — and where M3 costs 1.36 dB PSNR. No other scene
shows this. It is the scene with the most training views (25) and, per CD-26, the worst-conditioned
camera pairing (consecutive views along a reef wall). Carried to §14; THESIS.md: *treat
inconsistent scenes as evidence requiring explanation.*

**The collapse covariate, which §5 will use and which is the campaign's most decisive number.**

| cell | mechanisms | Curasao | IUI3 | JapaneseGardens | Panama | **total** |
|---|---|:-:|:-:|:-:|:-:|:-:|
| A0 | — | 0/3 | 0/3 | 0/3 | 0/3 | **0/12** |
| SS | — (reference) | 0/3 | 0/3 | 0/3 | 0/3 | **0/12** |
| A2 | M2 | 1/3 | 0/3 | 2/3 | 2/3 | **5/12** |
| A6 | M2 + M3 | 2/3 | 0/3 | 1/3 | 1/3 | **4/12** |
| **A4** | **M1** + M2 | 0/3 | 0/3 | 0/3 | 0/3 | **0/12** |
| **A7** | **M1** + M2 + M3 | 0/3 | 0/3 | 0/3 | 0/3 | **0/12** |

**Every cell with M1: 0 of 24. Every M2 cell without M1: 9 of 24.** The baseline and the
reference: 0 of 24. That is plan §5a (A0 stable, A2 collapses seed-conditioned) and §5c (M1
protects) held at the strongest level the design can produce. Whether the *mechanism* is the one
registered — the depth-range dispersion — is §5b, next.

## §3. Two-way interactions — PRE, on LPIPS and count

Additive on LPIPS; log-multiplicative on count; PSNR tabulated but `UNDETERMINED` by construction
(plan §3). z = term / SE with SE from the four cell means. Per scene.

**M1×M2 — `A4−A1−A2+A0` — H5: degenerate or sub-additive on count.**

| scene | LPIPS | count (log ratio) |
|---|---:|---:|
| Curasao | −0.004 UNRES | **×14.3 (+49.8)** |
| IUI3 | **−0.048 (−17.1)** | **×10.9 (+33.1)** |
| JapaneseGardens | **−0.015 (−2.6)** | **×9.7 (+10.1)** |
| Panama | **−0.017 (−2.0)** | **×8.0 (+9.3)** |

**H5 held, in its sub-additive form.** The count interaction is ×8–14 on every scene at 9–50
SE: the two reductions do not multiply. M1 alone gives ~×0.08, M2 alone ~×0.05, and the
multiplicative prediction would be ~11 000 primitives; A4 lands near 130 000, because the budget
of 200 000 caps whichever cell reaches it and M1's cloud has less for M2 to remove. Preflight
ensured the budget bound (not degenerate), and the interaction is the sub-additivity §8.4
predicted. **Unregistered, and favourable:** the LPIPS interaction is *negative* on three
scenes — the pair costs *less* perceptual quality than the sum of its parts, by 0.048 on IUI3
at 17 SE. Reported as observed; interpretation (dense initialisation leaves M2 better-placed
primitives to keep) is post-hoc and labelled so.

**M1×M3 — `A5−A1−A3+A0` — registered: approximately additive.**

| scene | LPIPS | count (log ratio) |
|---|---:|---:|
| Curasao | **+0.021 (+4.8)** | ×1.21 UNRES |
| IUI3 | **−0.008 (−4.4)** | ×1.14 UNRES |
| JapaneseGardens | +0.005 UNRES | ×1.11 UNRES |
| Panama | **+0.027 (+4.9)** | ×0.81 UNRES |

**The registered prediction fails on LPIPS.** The falsification condition was *"resolved in
either direction at ≥2 SE"*; it resolves on three scenes at 4–5 SE. Additive on count, as
predicted. But the LPIPS sign is **inconsistent** — positive on Curasao and Panama, negative on
IUI3 — which is not the signature of a systematic coupling. LPIPS's per-scene sd is 0.001–0.009,
so absolute differences of 0.02 clear 2 SE easily; what resolves here may be scene-specific
sensitivity rather than an interaction between the mechanisms. Reported as a failed prediction
with that caveat attached, not explained away.

**M2×M3 — `A6−A2−A3+A0` — H3: sub-additive on quality.**

| scene | LPIPS | count (log ratio) |
|---|---:|---:|
| Curasao | **+0.020 (+6.5)** | ×1.18 UNRES |
| IUI3 | −0.006 UNRES | ×1.15 UNRES |
| JapaneseGardens | **+0.017 (+3.0)** | ×1.13 UNRES |
| Panama | +0.015 (+2.0, at the line) | ×0.82 UNRES |

**H3 held on three of four scenes.** The LPIPS interaction is positive — the pair costs *more*
than the sum of its parts — on Curasao and JapaneseGardens cleanly, Panama at the threshold.
That is OMG's premise transferring: a smaller population is more sensitive to lossy attribute
compression. IUI3, the scene that is anomalous everywhere else, is the exception here too.
Additive on count, as expected of a mechanism that does not touch count.

**PSNR interactions, tabulated and not interpreted.** Several clear 2 SE against the new,
tighter floor (M1×M2 Panama −0.95; M1×M3 IUI3 +0.91, Panama −1.30; M2×M3 Curasao −1.30,
Panama −0.66). They sit at 0.7–1.3 dB, on the resolvability edge, and **the sign flips scene to
scene within every pair** — the signature of noise at the limit, not of a mechanism. The plan's
rule stands: `UNDETERMINED` by construction, no claim rests on them.

## §4. Three-way — PRE, no directional prediction

`A7−A6−A5−A4+A3+A2+A1−A0`, SE from eight means.

| scene | LPIPS | count |
|---|---:|---:|
| Curasao | −0.016 (−2.0, at the line) | ×0.84 UNRES |
| IUI3 | +0.003 UNRES | ×0.88 UNRES |
| JapaneseGardens | −0.003 UNRES | ×0.89 UNRES |
| Panama | **−0.023 (−2.7)** | ×1.25 UNRES |

**`UNRESOLVED` on count everywhere and on LPIPS on three of four scenes.** Panama resolves
negative on LPIPS at 2.7 SE; Curasao sits on the line. Per the plan, no interpretation is offered
for a term that resolves on one scene. The design's resolution for an eight-mean contrast is
2√2 × the single-mean SE, and this is what that looks like.

**RQ2, answered as the plan required.** The mechanisms do not compose additively. M1×M2 is
strongly sub-additive on count (the budget binding) and favourably non-additive on LPIPS; M2×M3
is sub-additive on quality as OMG's premise predicts; M1×M3 is additive on count and resolves
inconsistently on LPIPS. Adjudicated on LPIPS and count. PSNR stays `UNDETERMINED`.

## §5. The central hypothesis — PRE, the decisive test

### 5a. The collapse itself — held

A0 0/12, SS 0/12. A2 5/12, A6 4/12, seed-conditioned within scene (Curasao 1/3 and 2/3;
JapaneseGardens 2/3 and 1/3; Panama 2/3 and 1/3; IUI3 0/6). **All 24 non-M1 M2 runs put their
largest attenuation drop at iteration 15 000 — the first simplification boundary — without
exception.** The lost channel is `b` in every case, `g` additionally in two. Boundary-aligned,
baseline-stable, exactly as registered.

### 5b. The mechanism — the dispersion prediction — **FAILED. The account is withdrawn.**

The registered claim: *collapse at a simplification event is governed by the change in
cross-frame dispersion of the depth range across that event — not by primitive count, not by
count ratio.* The registered test: within the M2 cells without M1, does `cv_after / cv_before`
at the first event separate the runs that collapsed from those that did not?

| stratum | n | ratio min | median | max |
|---|---:|---:|---:|---:|
| collapsed | 9 | 0.913 | 1.017 | 1.555 |
| intact | 15 | 0.845 | 1.002 | 1.396 |

**Mann–Whitney U = 79 of 135, AUC = 0.585, exact one-sided p = 0.26.** The two distributions
lie on top of each other. Within-scene: on Curasao the *intact* runs have the larger ratios
(1.19, 1.26 vs 0.95, 1.07, 1.10); on Panama every ratio, collapsed or not, sits at 0.91–1.02.
Spearman between the ratio and the size of the β drop across the event is **−0.32 within the
non-M1 cells** (n = 24) and 0.18 across all 48. The ratio predicts nothing.

The direct counterexample the registration invited: at the second event, four M1 runs
(A7/Curasao s1 s2, A4/Curasao s1, A7/JapaneseGardens s1) show ratios of **3.5–7.3** — the
distribution broadened by a factor the non-M1 cells never approach — and none of them collapsed.

Per the plan, written before the data: *the identifiability account of `08-supervisory-review`
§2 is withdrawn rather than qualified, and CD-6's failure returns to "unexplained".* That is the
finding. The prediction in §2 of that review, that collapse tracks dispersion and not count, was
falsifiable, was tested at the first opportunity, and is false. Everything downstream that
rested on it — the `[08 §3.1]` explanation of why M1 protects, the `[06 §6.9]` derivation, the
instrument's own printed interpretation in `medium_collapse.py` — is to be rewritten as
description, not explanation.

### What the same data show instead — post-hoc, unregistered, labelled

The 48 diagnostics carry the full state at both sides of both events. Read without the
prediction:

1. **The cut does not move β. The 200 medium-only steps that follow it do.** On 48 of 48 runs at
   both events, β at `post_simp` equals β at `pre_simp` exactly — simplification touches
   geometry only. β then moves during the CD-6 burst, with geometry frozen. **Six of the nine
   collapses have their first negative channel at iteration 15 001 — at `rewarm_end`.** The
   sign crossing happens inside the remedy.

2. **What differs between the cells that collapse and the cells that never do is the size of
   the cut, and everything M1 changes with it.**

   | | non-M1 (A2, A6) | with M1 (A4, A7) |
   |---|---|---|
   | count entering the first event | 1.4–4.2 M | 196–247 k |
   | fraction removed at the first event | **86–95 %** | **29–36 %** |
   | β̄_att entering the event | 0.66–1.71 (median 1.2) | 1.60–5.35 (median 3.3) |
   | β̄_att after the burst, as a fraction of before | collapsed 0.00–0.47 (med 0.21); intact 0.26–0.60 (med 0.38) | **0.89–1.04 (med 0.97)** |
   | collapses | 9 / 24 | 0 / 24 |

   Every 86–95 % cut loses 40–100 % of its attenuation within 200 medium steps; nine of 24
   cross zero on the blue channel. No 29–36 % cut loses more than 11 %. Spearman between
   fraction removed and β drop at the first event is **0.83 across all 48** (0.46 within the
   non-M1 cells alone). The quantity the registration said would *not* govern collapse is the
   one that covaries with it.

3. **Within the large cuts, nothing measured before the cut predicts which seed crosses zero.**
   AUC for pre-event dispersion 0.42, for pre-event count 0.65, for pre-event β̄ 0.51, for
   pre-event min-channel β 0.55. The collapse is seed-conditioned and, on this instrument set,
   unpredictable from the pre-cut state. That is a limitation to state, not a pattern to
   explain.

4. **The second event.** The 23–36 % cut at 20 000 costs the non-M1 cells a further 10–40 % of
   β̄ and pushes three runs over the line (A2/JG s0 at 20 001, A2/JG s1 and A6/JG s1 at
   22 500) whose blue channel the first cut had already brought to 0.2–0.3. It costs M1 cells
   nothing on eight of twelve, and 60–70 % on the four high-ratio runs — from a base of 3.3–6.9,
   so no channel approaches zero.

5. **M1 is confounded with its own protections.** Removal fraction, entering β, and entering
   count all differ between M1 and non-M1 cells because M1 sets all three. This design cannot
   say which of them is the cause, and this document does not.

**The honest statement of the mechanism after this campaign:** the medium model survives the
removal of a third of the population and does not reliably survive the removal of nine
tenths; the loss is expressed in the medium-only steps immediately after the cut; whether it
crosses zero is not predicted by anything measured here. *Why* a large cut moves β is open.

### 5c. M1 protects — the rate held; the reason offered for it did not

0 of 24 against 9 of 24. The registered *reason* — "dense initialisation keeps per-frame
ranges uniform so the distribution translates rather than broadens" — is the withdrawn
account, and its own evidence contradicts it (the M1 second-event ratios of 3.5–7.3 above). What
can be said: M1's cloud enters the first event at ~224 k, so the 200 k budget removes a third
of it rather than nine tenths.

### 5d. Size versus discontinuity — held

| scene | A2 count | A4 count | A2 collapsed | A4 collapsed |
|---|---:|---:|:-:|:-:|
| Curasao | 149 906 ± 2 858 | **129 677** ± 4 220 | 1/3 | 0/3 |
| IUI3 | 132 955 ± 2 234 | **114 103** ± 1 066 | 0/3 | 0/3 |
| JapaneseGardens | 142 719 ± 2 086 | **127 632** ± 1 342 | 2/3 | 0/3 |
| Panama | 139 203 ± 9 728 | **115 174** ± 638 | 2/3 | 0/3 |

A4 finishes 13–17 % *below* A2 on every scene, with the same two events at the same iterations,
and does not collapse. Final size is not what breaks the medium; E.20's deconfounding replicates
at n=3.

### 5e. CD-6 — held, and worse than registered

`rewarm_end` carries `zr_*` identical to `post_simp` on 48/48 runs at both events: the burst
moves no geometry, as designed. It also does not restore β. Point 1 above is the stronger
negative: **the burst is the interval in which β falls**, on every large cut, and in six of
nine collapses the interval in which it crosses zero. Whether the same fall would occur over
the next 200 ordinary iterations without the burst is not tested by this design (the burst is
present in every M2 cell). What is established is that 200 medium-only steps against the cut
geometry are not a remedy; they are where the damage is written.

**H4 / RQ3 verdict.** *Does primitive reduction perturb medium identifiability?* Yes —
reproducibly, boundary-aligned, in 9 of 24 large-cut runs and 0 of 48 others. *Why?* **The
registered answer is false and is withdrawn.** The replacement is descriptive: the size of the
cut, and the medium re-fit that follows it. RQ3's *why* is open at the end of this campaign, and
the thesis says so.

## §6. Mechanism D — PRE

Prediction written before A0D ran: *the count effect will resolve; the PSNR effect will not.*

| scene | count ratio (z) | wall-clock (z) | fps (z) | PSNR (z) | LPIPS (z) | SSIM (z) |
|---|---:|---:|---:|---:|---:|---:|
| Curasao | **×0.19 (−16.3)** | ×0.68 (−21.3) | ×2.31 (+13.1) | +0.28 UNRES | **+0.011 (+3.9)** | +0.000 UNRES |
| IUI3 | **×0.32 (−9.4)** | ×0.78 (−14.8) | ×1.35 (+6.5) | −0.09 UNRES | **+0.024 (+32.6)** | +0.003 (+3.4) |
| JapaneseGardens | **×0.25 (−3.8)** | ×0.76 (−6.9) | ×1.70 (+6.5) | +0.30 UNRES | **+0.009 (+3.0)** | +0.007 UNRES |
| Panama | **×0.33 (−3.1)** | ×0.81 (−3.4) | ×1.56 (+4.8) | +0.25 UNRES | **+0.026 (+4.7)** | +0.000 UNRES |

**Both halves of the prediction held.** Count resolves on all four scenes: 3–5× fewer
primitives, and with it 20–32 % less training time, 1.4–2.3× frame rate, and 40–60 % less peak
render memory. PSNR is unresolved on all four — +0.25 to +0.30 on three and −0.09 on IUI3, every
one under 1.1 SE — and is reported as `UNRESOLVED at n=3`, not as a point estimate. The old
figure of "−0.107 dB" is retired; the honest figure is "within ±0.5 dB at this resolution".

**LPIPS resolves worse on all four scenes** (+0.009 to +0.026; 3–33 SE). This was the metric
flagged as the one that might resolve, and it resolves against D. The perceptual cost is real
and smaller than M2's (+0.03 to +0.08) for a smaller count reduction (3–5× vs 14–25×). SSIM
does not move.

**No A0D run lost a channel** (0/12). D removes primitives by starving the densifier of the
alpha-loss gradient, continuously, with no event — and the medium survives it. Read beside §5:
the continuous 3–5× reduction leaves β intact where the two-step 14–25× cut does not. It is
one more observation consistent with "the size and abruptness of the cut", and it is not a
test of that account.

**E.4 verdict.** Alive. A 3–5× count reduction at a resolved but small perceptual cost and an
unresolved PSNR cost, from a *sound* baseline this time (§1). Reported as the supplementary
contrast it is, never differenced with the factorial.

## §7. Rate–distortion and Pareto — description only, by design

One operating point per mechanism; no curve within a mechanism; R3.4 unanswered. Per scene,
the non-dominated cells over the nine trained cells (SS excluded as the reference):

| scene | count × LPIPS | bytes × LPIPS | count × PSNR | bytes × PSNR |
|---|---|---|---|---|
| Curasao | A0, **A1**, A4, A7 | A0, A1, A5, A6, A7 | A2, A4, A7 | A2, A4, A7 |
| IUI3 | A0, A0D, **A1**, A2, A4, A5 | A0, A0D, A1, A5, A6, A7 | A1, A4 | A1, A4, A5, A7 |
| JapaneseGardens | **A1**, A3, A4, A5 | A1, A3, A5, A7 | A4, A5, A7 | A5, A7 |
| Panama | A0, **A1**, A4, A5 | A0, A1, A3, A5, A7 | A1, A2, A4 | A1, A2, A4, A7 |

What the fronts show, described and not ranked:

- **A1 is on the count × LPIPS front on all four scenes.** A 10–16× reduction at baseline LPIPS
  on three scenes is the single most favourable operating point in the design, and it is the
  one mechanism that is initialisation rather than removal.
- **A2 and A6 are dominated on count × LPIPS on three scenes** — by A4 and A7, which have both
  fewer primitives (§5d) and lower LPIPS (Curasao 0.215 vs 0.216, JapaneseGardens 0.202 vs
  0.217, Panama 0.193 vs 0.203). M2 alone is not on the perceptual front where M1 + M2 is. IUI3
  is again the exception.
- **A7 is on the bytes front everywhere** — 2.4–2.7 MB against SS's 114–240 MB, a 45–90×
  reduction in stored bytes — at an LPIPS cost of +0.06 to +0.11 over baseline.
- **On PSNR the fronts are the M2-containing cells,** because PSNR does not resolve the
  mechanisms' costs (§2, §3); a front drawn on an unresolved metric is a front drawn on noise,
  and is shown for completeness only.
- **M3 costs frame rate once the population is small.** A7 renders 8–18 % slower than A4 on every
  scene; A6 5–22 % slower than A2 on three. Unresolved from below (§2), consistent from above.
  Decoding a codebook is not free at 130 k primitives the way it is at 3 M.

## §8. Fidelity metrics cannot see collapse — E.7, confirmatory at scale

Within each cell × scene of A2 and A6 that has both strata (six of eight; IUI3 has no collapsed
run in either cell), collapsed minus intact, in units of A0's per-scene sd:

| cell × scene | n (coll/int) | PSNR | LPIPS | β_att,b collapsed → intact |
|---|:-:|---:|---:|---|
| A2 Curasao | 1/2 | +1.42 | −0.21 | −0.048 → 1.17, 1.36 |
| A2 JapaneseGardens | 2/1 | −0.89 | +1.19 | −0.02, −0.04 → 1.00 |
| A2 Panama | 2/1 | −0.38 | +1.63 | −0.06, −0.05 → 1.21 |
| A6 Curasao | 2/1 | −0.27 | +1.93 | −0.03, −0.06 → 1.18 |
| A6 JapaneseGardens | 1/2 | **+4.54** | −0.70 | −0.056 → 1.21, 1.07 |
| A6 Panama | 1/2 | −0.05 | +0.24 | −0.038 → 0.93, 1.27 |

**E.7 holds at 48 runs.** Twelve comparisons; median |difference| 0.8 sd; PSNR sign 2+/4−,
LPIPS 4+/2−. The one comparison beyond 2 sd (A6/JapaneseGardens PSNR, +4.5 sd) has the collapsed
run *better*, at n = 1 against 2, on the scene whose PSNR sd is 0.126 dB — so +0.57 dB is
4.5 sd. Fidelity does not distinguish a run whose blue attenuation is −0.05 from one whose blue
attenuation is +1.2. Train PSNR does not either (every stratum pair within 0.6 dB).

That is the finding stated precisely: a physically meaningless medium — negative attenuation
— renders held-out views as well as a physically plausible one, because Ĵ absorbs whatever β
does not model. The per-image metrics measure Î; the thesis's claim of *decomposition* is not
something they can check, and every LPIPS or PSNR number in this document is a statement about
Î alone. Ĵ self-consistency (§10) is the only instrument here that looks past Î, and it is
n = 1 per scene.

## §9. Geometric pathology — EXP, seed 0 only (SS all three seeds)

Detector of failure modes; never a proxy for medium health (E.17). 48 rows.

**The invisible population.** Fraction of primitives above the visibility threshold:

| | A0 | SS (3 seeds) | A0D | A1 | A2 | A4 |
|---|---|---|---|---|---|---|
| Curasao | 27 % | 23–26 % | 68 % | 87 % | 96 % | 98 % |
| IUI3 | 40 % | 29–43 % | 76 % | 94 % | 88 % | 100 % |
| JapaneseGardens | 41 % | 36–37 % | 74 % | 87 % | 93 % | 99 % |
| Panama | 36 % | 26–37 % | 65 % | 78 % | 94 % | 95 % |

**Sixty to seventy-five per cent of the baseline's primitives are invisible, and vanilla
SeaSplat carries the same fraction.** This is the population M2 and D remove, and the one M1
never creates. It is the single clearest description of *what* the mechanisms are cutting: not
the reconstruction, but a halo the baseline optimiser grows and never renders. The
mechanisms' count reductions (§2) should be read against the ~30 % of A0 that is visible, not
against its total: A2's 25× reduction on Curasao is a ~7× reduction of the visible population.

**Detached outliers.** Bounding-box inflation (full box over the 1–99 % box) is 2–25× on most
rows and pathological on a few: A3/Curasao **1 301×** (z-axis 15×; 40 % of primitives within
2× the median radius), SS/Panama s2 **313×**, A0D/Panama 138×, A3/Panama 43×, A4 and
A7/JapaneseGardens 38–39×. **Vanilla SeaSplat produces a 313× inflation on one of three
seeds** — the detached-cluster pathology belongs to the baseline optimiser and its seed, not
to any mechanism. A3's two large values are noted; with one seed per cell they cannot be
attributed.

**M2 cells have the tightest geometry:** inflation 1.8–6.8×, occupancy 1.3–3.3 % of the
footprint grid, the smallest radius ratios (2.5–7.5). What survives the cut is compact.

## §10. Ĵ self-consistency — EXP, n = 1 per scene — **the check ran; the drift reading was wrong**

Sixteen runs (seed 0 of A3, A5, A6, A7), each the same model rendered twice with the three
quantized attributes in their continuous and their codebook states. The first version of this
section read the 17–27 dB Ĵ gap as straight-through drift — the continuous parameters a
latent, never rendered, unconstrained by any commitment term — and predicted that the
continuous state would score ~10 dB in the water against ~29 for the codebook state. The
check was added to the tool and run. Codebook-state Î reproduces each run's `eval_metrics.json`
Test PSNR to within 0.00–0.26 dB on all sixteen, so the composition path is right and the
columns mean what they say.

| | Ĵ gap (cont vs code) | Î vs truth, continuous | Î vs truth, codebook | in-medium loss | verdict |
|---|---:|---:|---:|---:|---|
| A3 Curasao | 23.3 | 28.6 | 29.5 | 0.9 | MODEL |
| A3 IUI3 | 23.1 | 23.6 | 26.7 | 3.1 | DRIFT |
| A3 JapaneseGardens | 25.3 | 23.0 | 23.6 | 0.6 | MODEL |
| A3 Panama | **17.0** | 21.9 | 28.7 | **6.8** | DRIFT |
| A5 Curasao | 22.9 | 28.3 | 29.9 | 1.6 | MODEL |
| A5 IUI3 | 24.5 | 24.7 | 27.3 | 2.6 | MODEL |
| A5 JapaneseGardens | 24.5 | 23.3 | 24.1 | 0.8 | MODEL |
| A5 Panama | 26.6 | 25.2 | 27.8 | 2.6 | MODEL |
| A6 Curasao | 26.0 | 27.8 | 29.0 | 1.3 | MODEL |
| A6 IUI3 | 26.2 | 24.9 | 26.6 | 1.8 | MODEL |
| A6 JapaneseGardens | 26.1 | 22.1 | 22.8 | 0.7 | MODEL |
| A6 Panama | 26.5 | 27.0 | 28.0 | 0.9 | MODEL |
| A7 Curasao | 23.8 | 29.6 | 30.5 | 0.9 | MODEL |
| A7 IUI3 | 25.3 | 25.3 | 27.1 | 1.8 | MODEL |
| A7 JapaneseGardens | 22.2 | 22.8 | 24.0 | 1.3 | MODEL |
| A7 Panama | 26.0 | 25.9 | 27.9 | 2.0 | MODEL |

**MODEL on 14 of 16.** The continuous state renders the water 0.6–3.1 dB worse than the
codebook state (median 1.4), not ~19 dB worse. It is a slightly degraded model, not a latent.
The STE does let it drift, and the drift is visible — 1–3 dB in-medium is the size of a
mechanism's main effect — but it is an order of magnitude too small to account for the Ĵ gap,
and **the two are uncorrelated across the sixteen runs (Spearman −0.14)**. A3/Panama, the one
run with a large in-medium loss (6.8 dB), is also the one with the smallest Ĵ gap (17 dB), and
that is the wrong direction for a drift account.

**So the Ĵ gap is what the tool was built to expose, and the section is rewritten as it said
it would be.** Two states of one model that render the in-medium image within ~1.4 dB of each
other produce restored images that differ by 17–27 dB PSNR from each other. The quantization
of three attributes changes Ĵ far more than it changes Î. That is the founding premise of the
instrument, demonstrated: what the composed metrics score is Ĵ ⊙ A + B with A ≤ 1, and the
part of Ĵ that A suppresses is free to move without the loss noticing. Every LPIPS and PSNR
number in this document is a statement about Î, and §8 already showed Î is indifferent to a
negative attenuation coefficient; this section shows it is indifferent to a ~23 dB change in
the restoration as well.

**What it is not.** A consistency measure — the tool cannot say whether the codebook Ĵ or the
continuous Ĵ is nearer the true medium-free image, only that they are far apart. n = 1 per
scene. And the far-field attribution is inferred from the image-formation model, not measured:
a per-depth-bin breakdown of the Ĵ difference would show *where* the two states disagree, and
is not in this campaign. Reported as secondary; never a headline.

**The prediction record.** Both figures I wrote before the check ran — ~10 dB for drift, ~29
dB for a model — were wrong; the result sat between them and closer to the second. The
instrument was right and its author was not. The verdict thresholds (3 dB) were fixed before
the data were seen and are kept.

## §11. Replication across campaigns — EXP

A0–A3, four scenes, n = 3 in both campaigns; new minus old, z on the pooled SE.

| | PSNR beyond 2 SE | LPIPS beyond 2 SE | count |
|---|---|---|---|
| A0 | IUI3 **+0.76** (2.4); JG −0.31 (−2.1) | none | ×0.86–1.17 |
| A1 | none | none | **×1.00 on all four** |
| A2 | none | none | ×0.97–1.02 |
| A3 | IUI3 **−0.95** (−2.8); Panama −0.35 (−3.3) | none | ×0.78–1.24 |

**LPIPS replicates on all sixteen comparisons. Count replicates for A1 to three figures — dense
initialisation is deterministic — and for A2 within 3 %.** A2's collapse rate replicates in form
(seed-conditioned, roughly half). Twelve of sixteen PSNR comparisons replicate.

**Four do not, and two of them matter.** On IUI3-RedSea, A0 rose by 0.76 dB (old 26.35–27.29;
new 27.38–27.86, non-overlapping) and A3 fell by 0.95 dB (old 27.08–27.53; new 25.68–26.67,
non-overlapping). The new A0 agrees with vanilla SeaSplat on the same scene (27.0–27.8), so it
is the new figure that is anchored. But the consequence for §2 is direct: **in the old campaign
M3's PSNR effect on IUI3 was +0.35 dB; in this one it is −1.36 dB.** The "resolved 1.36 dB loss
on IUI3" in §2 is resolved *within* this campaign and reversed *across* campaigns. It is
downgraded: M3's PSNR effect on IUI3-RedSea is `UNRESOLVED across campaigns`, and the §2 scene
finding rests on LPIPS (which replicates) and not on PSNR.

**Why is not established.** The training code changed between the campaigns — CD-22/23 (alpha
gradient routing, 2 Sept), the M1 opacity-schedule fixes (10 Sept), CD-27 (12–13 Sept) — and
**neither campaign's `git_commit` column is populated**, so which of those the old A3 runs
predate is unrecorded. A discrepancy of this size on one scene in two cells, with the reference
control agreeing with the new baseline, is reported here as what it is: a non-replication with
an unidentified cause, on the scene that is anomalous in every other section.

## §12. Computational cost — EXP

| | wall-clock vs A0 | fps vs A0 | peak render memory vs A0 |
|---|---|---|---|
| M1 (A1) | ×0.76–0.93 | ×1.3–2.2 | — |
| M2 (A2) | ×0.67–0.81 | ×1.9–3.5 | — |
| M3 (A3) | ×0.99–1.12 | ×0.84–1.21 UNRES | — |
| D (A0D) | ×0.68–0.81 | ×1.35–2.31 | ×0.41–0.60 |
| all three (A7) | ×0.76–0.95 | ×1.2–2.5 | — |

Effective optimiser steps are 43 000 for every non-M2 cell and 43 400 for every M2 cell; the
mechanisms change what an iteration costs, not how many there are. **fps is sub-linear in count
reduction on every scene**: A2's 25× on Curasao buys 3.5×, its 20× on IUI3 buys 1.9×; A4's
31× buys 2.7× and 1.5×. The exponent is scene-dependent (E.9), and the residual is the
per-frame cost that does not scale with primitives. M3 adds decode cost that shows once the
population is small (§7). The instrumented sweep costs ~3 s per run and is in every wall-clock
above; the archived A6/Curasao/s0 with its 75 s of over-firing is not in this bundle.

## §13. Related work — BLOCKED

Unchanged. The numbers this chapter needs exist; the six literature breakdowns Chapter 2 needs
do not, and nothing in this bundle changes that.

## §14. Limitations and anomalies — written last

**Unresolved by construction.** Every PSNR interaction (§3, §4); PSNR main effects on 5 of 12
scene × mechanism cells (§2); every count interaction beyond M1×M2 (§3, §4); the three-way term
on three of four scenes on LPIPS; A0D's PSNR effect on all four scenes (§6). Each is a statement
about n = 3, not about the mechanism.

**Unresolved across campaigns.** M3's PSNR effect on IUI3-RedSea (§11). The §2 figure of
−1.36 dB is carried nowhere else in this document.

**Unpredictable at this instrument set.** Which large-cut seed crosses zero (§5, point 3). AUC ≤
0.65 for every pre-cut covariate. The collapse is reproducible as a rate and not as an event.

**Unmeasured.** Restoration *accuracy* (§10): the instrument shows the two states' Ĵ differ
by 17–27 dB and cannot say which is nearer the truth, and the far-field location of the
difference is inferred from the formation model, not mapped. Whether the medium-only burst
*causes* the β fall or merely hosts it (§5e) — every M2 cell has the burst; no cell lacks it.

**Confounded.** M1's three protections — removal fraction, entering β, entering count — are set
together by M1 and cannot be separated by this design (§5, point 5). Any of the three, or
initialisation itself, may be the operative one.

**IUI3-RedSea.** The scene where every mechanism costs LPIPS (M1 +0.059, M2 +0.082, M3 +0.028,
each ≥ 20 SE); where A1's LPIPS front position is lost; where no M2 run collapses in six tries;
where H3 does not resolve; where the M1×M3 LPIPS interaction has the opposite sign to the other
three scenes; where PSNR does not replicate across campaigns. It has the most training views
(25) and, per CD-26, consecutive views along a reef wall — the worst-conditioned camera pairing
in the set. THESIS.md asks that inconsistent scenes be treated as evidence requiring
explanation; this document has none to offer beyond that conditioning, and records IUI3 as the
scene on which every per-scene claim in this chapter must be checked before it is generalised.

**The count noise floor on JapaneseGardens and Panama** widened to 34 % and 37 % CV at A0 (§0).
Every A0-anchored count contrast on those scenes carries that floor; the mechanisms' count
effects still resolve because they are 10–25×, and a 37 % floor is a 1.4× floor. Interactions
on count do not resolve on those scenes for the same reason.

**One seed per cell for geometry and Ĵ.** §9 and §10 are n = 1 per scene. A3/Curasao's 1 301×
inflation and A3/Panama's 17 dB are single observations and are labelled so.

**Provenance.** `git_commit` is empty in all 120 rows and in the archived campaign because the
collector read a key the manifest never wrote (§0); fixed, and the column populates on the next
collection. The archived campaign's sampled A3 manifest reads `-dirty`: at least one old A3 run
was trained from an uncommitted tree, which is the most likely home of §11's non-replication and
cannot be recovered now.

---

## What changed the thesis

Ranked as PLAN.md ranked it, with the outcome.

1. **§5b failed.** The dispersion account is withdrawn. The thesis reverts to Framing A: a
   controlled factorial study of three efficiency mechanisms on a physically-grounded
   estimator, with a measured, reproducible, boundary-aligned coupling between large-cut
   simplification and the medium model — and with an unexplained failed remedy. The *why* is
   open, and Chapter 4 says so in those words. What replaces the account is description
   (§5, "what the same data show instead"), labelled post-hoc, and not promoted to a claim.
2. **§6 held.** D resolves on count at a resolved perceptual cost and an unresolved PSNR cost.
   The thesis has a positive engineering result from a sound baseline.
3. **§5c held on rate, failed on mechanism.** M1 cells do not collapse — 0 of 24 — and the
   stated reason was the withdrawn account.
4. **§3's M2×M3 resolved positive on LPIPS on three scenes.** H3 holds; OMG's premise
   transfers. M1×M3's additivity prediction failed with inconsistent sign, and is reported as a
   failure.
5. **§1 held.** A0 is vanilla SeaSplat to within the margin on every scene.

Three things this campaign established that no prior run had: the baseline is sound (§1); 60–75 %
of the baseline's primitives are invisible and vanilla carries the same halo (§9); the medium
falls during the burst after every large cut and never after a small one (§5); and the
restored image moves ~23 dB under a quantization the in-medium image barely registers (§10).
Two things it retired: the dispersion account, and the "−0.107 dB" figure for D. One thing it
could not do: say why the medium falls.
