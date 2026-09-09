# Minimum Additional Work

Two kinds: literature that requires no compute, and experiments that do. Prioritised by
ability to answer a named reviewer objection, per the brief.

---

## Part 1 — Literature (no compute) · **P0**

Answers **R3.1** and prevents the unverified gap claim **D.3**. This is the most concrete
reason the paper was rejected, and it is entirely tractable.

Six methods have no `research-methodology-output` breakdown. Each needs at minimum the
taxonomy, mechanism, and computational-profile sections of the standard 12-file template —
enough to place it in Chapter 2's family table and to state why it is or is not evaluated.

| Method | Family the reviewer named | Why it matters here |
|---|---|---|
| **LightGaussian** | adaptive attribute pruning + distillation | The obvious comparator to M2; prunes by global significance and distils SH |
| **EAGLES** | quantized attributes + entropy | Quantization *with* entropy coding — the direct extension of M3 |
| **ReSplat** | structured / residual representation | "Structured representations", named explicitly |
| **WaterSplatting** | underwater 3DGS | Prevents claiming no underwater alternatives exist |
| **Aquatic-GS** | underwater 3DGS + medium modelling | Direct alternative formulation to SeaSplat |
| **Gaussian Splashing** | underwater//water-interaction 3DGS | Completes the underwater family |

Plus, from the corpus already analysed but never used in the manuscript: **CompGS (Liu et
al.)** supplies the *rate–distortion optimization and entropy coding* family, and **OMG**
supplies the sub-additivity premise behind H3.

**Deliverable:** Chapter 2 §2.5 as a family taxonomy — initialization · population reduction ·
attribute quantization · rate–distortion optimization · entropy coding · structured
representation — with each family represented, and an explicit statement of which three are
evaluated and **why those three** (they act at disjoint pipeline stages, which is what makes
the factorial interpretable).

That last sentence is also the answer to *"why not evaluate the others?"* — a factorial
requires factors that can be independently switched, and entropy coding is not independent of
quantization.

---

## Part 2 — Experiments

### Already scheduled (no decision required)

| Stage | Runs | Answers |
|---|---:|---|
| S2 (A2) | 12 | RQ1 for M2; **H4** — the medium-identifiability test; meta-review M.2 |
| S3 (A1, A3) | 24 | RQ1 for M1, M3 |
| S4 (A4, A5, A6) | 36 | RQ2 — two-way interactions |
| S5 (A7) | 12 | RQ2 — three-way, effect-from-above |
| S6 (A0D) | 12 | Mechanism D (E.4) |
| SS control | 4 | Baseline fidelity across all four scenes |

At the measured **78 min/run**, S2–S5 is ~110 GPU-hours.

### Priority 1 — the budget sweep · answers **R3.4**, converts C.2 from untestable to testable

The single highest-value addition, and the only reviewer concern requiring compute.

**The problem it solves.** Each mechanism currently has one operating point, so no Pareto
surface exists and mechanism ranking cannot be shown to persist across budgets. The thesis's
conclusions are phrased as selection guidance, which needs exactly this.

**Design.** M2 is the mechanism with a continuous dial. Sweep `n_bud` at three additional
values spanning an order of magnitude around the current 200 000:

| variant | `n_bud` | vs A0 median (2.48M) |
|---|---:|---|
| A2-a | 800 000 | 3.1× reduction |
| A2 *(existing)* | 200 000 | 12.4× |
| A2-b | 100 000 | 24.8× |
| A2-c | 50 000 | 49.6× |

All three clear the binding rule against the smallest dense cloud (299 368), so they remain
valid in combination.

| option | design | runs | GPU-h | gives |
|---|---|---:|---:|---|
| **1a — minimum** | 3 budgets × 4 scenes × **2 seeds** | 24 | ~31 | A four-point curve per scene with a crude spread. Sufficient to show whether ranking *flips*; not to put error bars on the flip point |
| **1b — recommended** | 3 budgets × 4 scenes × **3 seeds** | 36 | ~47 | Consistent with the rest of the campaign; every point carries the same dispersion treatment |
| **1c — reduced scope** | 3 budgets × **2 scenes** × 3 seeds | 18 | ~23 | Full dispersion on the two extreme scenes (JapaneseGardens at 6% CV, Panama at 29%) — deliberately spanning the dispersion range rather than averaging it |

**Recommendation: 1c, then 1b if compute allows.** 1c is defensible on its own terms — it
tests whether the ranking is stable in both the best and worst-conditioned scenes, which is a
sharper question than a four-scene mean, and it costs half of 1b.

**Not recommended:** sweeping M3's codebook size in the same pass. `k` affects storage but not
primitive count, so M2 and M3 do not share an x-axis; a joint Pareto plot would need storage as
the common abscissa and that comparison is cleaner *after* the M2 curve exists.

### Priority 2 — the CD-6 ablation · answers **R2.1** and **meta M.1**

The medium re-identification burst is this thesis's own proposed remedy, and it is currently
**always on**. Its effect is therefore unmeasured — the contribution is asserted, not
demonstrated.

`m2_rewarm_steps = 0` is already a valid configuration and warns loudly rather than failing.

| design | runs | GPU-h | gives |
|---|---:|---:|---|
| A2 with `m2_rewarm_steps = 0`, 4 scenes × 3 seeds | 12 | ~16 | Whether the burst restores β after the simplification discontinuity — a direct test of the thesis's own mechanism |

**This is arguably better value than the budget sweep for the *thesis*** (as opposed to for
the reviewers), because it converts contribution #2 from designed to demonstrated. It is
cheap, and it tests something no source method has tested.

### Priority 3 — deferred

| | Why deferred |
|---|---|
| More scenes | The four are the complete public corpus (R3.5) — intractable, must remain a stated limitation |
| A second underwater formulation | Would require reimplementing WaterSplatting or Aquatic-GS; out of scope for a thesis at this stage |
| Embedded/AUV profiling | Requires hardware not available; the framing is withdrawn instead (D-10) |

---

## Recommended plan

| Order | Work | Runs | GPU-h | Blocks |
|---|---|---:|---:|---|
| 1 | Six literature breakdowns | — | — | **Ch. 2, and Ch. 2 blocks Ch. 1** |
| 2 | S2–S5 *(already running)* | 84 | ~110 | Ch. 4 |
| 3 | CD-6 ablation | 12 | ~16 | Contribution #2 |
| 4 | Budget sweep, option 1c | 18 | ~23 | R3.4, Framing B |
| 5 | SS control, 4 scenes | 4 | ~5 | Ch. 4 §4.2 |
| 6 | S6 mechanism D | 12 | ~16 | Contribution, optional |

**Without items 3–6 the thesis is Framing A and defensible.** With 3 it gains a demonstrated
contribution; with 4 it reaches Framing B.

Item 1 costs no compute, blocks the most criticised chapter, and can begin immediately.
