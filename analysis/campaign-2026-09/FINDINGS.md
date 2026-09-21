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
trained cells; SS's 12 are blank because `measure_reference` does not record it. **`git_commit`
is empty in every row** — the collector did not capture it, so the one-code-version claim cannot
be verified from this table. *Action: sample `run_config.json` from three cells on Drive.*

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
