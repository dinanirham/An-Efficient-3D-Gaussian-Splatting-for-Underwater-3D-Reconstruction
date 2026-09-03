# Ablation design

What the experiment is, how its numbers may be read, and which readings are
invalid. This file records **design intent**: if the code and this document
ever disagree, that is a finding, and this document is what makes it findable.

Companions: `experiment_plan.md` (what gets run), `reproducibility_notes.md`
(what is pinned), `tools/CAMPAIGN.md` (how to operate the queue). The
thesis-facing prose lives in `../../combined-method-methodology/chapter/`.

---

## 1. The design is a 2³ factorial, not a ladder

Three binary factors — dense initialization (M1), budget simplification (M2),
attribute quantization (M3) — giving eight complete configurations:

| | M1 | M2 | M3 | | | M1 | M2 | M3 |
|---|---|---|---|---|---|---|---|---|
| **A0** | — | — | — | | **A4** | ✅ | ✅ | — |
| **A1** | ✅ | — | — | | **A5** | ✅ | — | ✅ |
| **A2** | — | ✅ | — | | **A6** | — | ✅ | ✅ |
| **A3** | — | — | ✅ | | **A7** | ✅ | ✅ | ✅ |

**Why factorial rather than cumulative.** A ladder supports one direction of
inference: it reports what each addition contributed *on top of what came
before*, and cannot say what removing a component from the complete system
would cost. That distinction is routinely elided in the literature this work
builds on — of the four source methods, one publishes a ladder whose terminal
row does not match its own reported complete model, two publish several
structurally different tables all labelled "ablation", and one publishes a
table whose direction cannot be determined even by careful reading.

A factorial removes the ambiguity: every cell is a complete configuration, and
a mechanism's effect is a **contrast between cells**.

## 2. How the numbers may be read

For a metric `m`, with `Δ_S = m(A_S) − m(A_0)`:

**Main effect, from below** — the mechanism added to the bare baseline:
`A1−A0`, `A2−A0`, `A3−A0`.

**Main effect, from above** — the mechanism removed from the complete system:
`A7−A6` removes M1, `A7−A5` removes M2, `A7−A4` removes M3.

**Interaction** — the difference between the two readings:

```
interaction(M1,M2) = (A4−A0) − [(A1−A0) + (A2−A0)]
```

and likewise for the other pairs; the three-way term follows from A7.

Combination is **additive** for quality metrics expressed in decibels or as
similarity indices, and **multiplicative** for ratio measures (storage,
primitive count, frame rate).

### Rules that are not negotiable

- Where the from-below and from-above estimates **agree** within pooled
  dispersion, either may be quoted.
- Where they **disagree**, *neither may be quoted alone*. The disagreement is
  the interaction and must be reported as such.
- No effect may be quoted from a single run. Interactions are differences of
  differences and carry roughly twice the variance of a main effect.
- No cell may be compared against another cell run on a different GPU.

## 3. What each cell is for

| Cell | Isolates | Notes |
|---|---|---|
| **A0** | the reference point | **Also a prerequisite**: the primitive budget is derived from its converged count, which no publication of the baseline reports. Doubles as the environment-validity check. |
| **A1** | initialization | Quality change is attributable to the starting geometry plus the two schedule behaviours EDGS brings with it. Carries the water-column matcher risk. |
| **A2** | primitive count | **The most important single cell.** The only single-mechanism cell in which the population changes discontinuously mid-training, so the only one that can test the medium-identifiability hypothesis. |
| **A3** | bits per primitive | Quantization touches neither position nor opacity, so it cannot perturb the two quantities the baseline's well-posedness argument leans on. Expected to be the best-behaved single-mechanism cell. |
| **A4** | M1 × M2 | Degeneracy risk — see §5. |
| **A5** | M1 × M3 | The least-coupled pair: non-adjacent pipeline stages, no shared variable. Predicted additive; a large interaction here would indicate something unmodelled. |
| **A6** | M2 × M3 | The one interaction with external theory behind it. |
| **A7** | three-way | Source of the from-above contrasts. |

## 4. Hypotheses, and the contrast that tests each

| | Hypothesis | Tested by |
|---|---|---|
| **H1** | individual gains transfer | `A1−A0`, `A2−A0`, `A3−A0` on the efficiency measures |
| **H2** | gains are attenuated vs published terrestrial figures | the same contrasts, after renormalising to 14 floats/primitive |
| **H3** | quality cost concentrates in the water column | `A1−A0`, `A2−A0` plus the primitive-count trajectory |
| **H4** | **primitive reduction perturbs medium estimation** | **A2, via `diagnostics.csv`** — not a between-cell comparison |
| **H5** | M2×M3 interacts, M1×M3 does not | `A6 − [A2+A3−A0]` and `A5 − [A1+A3−A0]` |

**H4 is the one to run first and the cheapest to answer.** It needs two logged
quantities observed across one scheduled event in one configuration. It is also
the only hypothesis whose failure mode is invisible in the quality numbers: a
mis-identified medium model presents as slightly worse reconstruction in the
pruned cells, which is exactly what pruning is expected to look like anyway.

### A prediction with a closed form

Storage compression is primitive-count dependent, because the codebook is a
fixed cost: `ratio(N) = 56N / (20.5N + 163840)` at k=4096. M2 reduces `N`, so
**M2 and M3 interact on the storage axis by construction**. The effect is small
at realistic budgets (0.02× between 500k and 1M primitives), so it is unlikely
to be what makes A6 interesting — but A6 and A7 must report storage **per
primitive** as well as total, or a ratio that fell because `N` fell will read as
quantization performing worse.

## 5. Two hazards controlled by design

**A non-binding budget.** If M1 converges below the budget, the simplification
step is a no-op and **A4 collapses onto A1, A7 onto A5**. A null interaction
measured in that state is a configuration artifact, not a finding — and the
worst kind, because the two cells simply agree and nothing in the results table
distinguishes "no interaction" from "no experiment".

### The binding rule

> **`n_bud` must lie below the smallest primitive count any other enabled
> mechanism produces.**

This is a precondition for measuring M2 in combination, not a tuning choice,
and it is fixed **before S1** rather than derived from A0's result afterwards.
Deriving it after the fact would be fitting the design to the data.

An earlier draft set the budget at 60% of A0's converged count. Replication
puts A0 near **4.4M** primitives (three runs, 21% spread), which makes that
rule give ~2.6M — far above every dense cloud, so M2 would have been inert in
all four M1 cells. The rule above replaces it.

| | value | source |
|---|---:|---|
| A0 converged count | ~4.39M | measured, 3 runs |
| M1 cloud, `sparse` preset | ~150–220k | 18 refs × 3 neighbours × 5,000 matches |
| M1 cloud, `dense` preset | ~600–800k | same, 20,000 matches |
| **`n_bud`** | **400,000** | below `dense` with margin; 11× reduction from A0 |

`dense` is chosen over `sparse` for two reasons beyond the budget: a 150k cloud
makes M1 read as aggressive subsampling rather than informed initialisation,
and the wider margin keeps the budget binding across scene-to-scene variation
in cloud size. It costs ~4× the RoMa preprocessing time — minutes, once, per
scene.

The cloud counts are arithmetic estimates until section 9 of `00_setup` reports
the real ones. If `dense` returns lower, **`n_bud` follows the measurement**:
the rule holds and the number moves.

**Preflight enforces it.** Any run with both M1 and M2 enabled reads the vertex
count from the cloud's PLY header and refuses to start if `n_bud` is not below
it, naming the collapse it would have produced. Within 10% it warns instead —
the budget binds, but over so short a lever that the interaction is measured
against almost nothing. The run also records `budget_bound` either way.

**A confounded factor.** The quantization method ships its own ℓ1-opacity
regulariser, which its authors credit for their 2–3× rendering speedup rather
than the quantization. Left enabled, M2 and M3 would not be independent and the
compound cells would prune twice. **It is not implemented.** Consequently
**A3 is expected to show approximately no frame-rate gain — that is the correct
result, not a failed reproduction.**

## 6. What this design cannot establish

- **Nothing about restoration quality.** The restored medium-free image has no
  ground truth and cannot acquire one. Every quantitative figure measures the
  in-medium reconstruction. Quantization error enters the restored image
  directly but is multiplied by the attenuation map before reaching the metric,
  so the instrument under-reports that damage precisely in the far-field regions
  where restoration matters most.
- **No cell except A0 reproduces any source method.** Four deliberate
  departures make the mechanisms independent factors: the quantizer's opacity
  regulariser is dropped, the pruning method is scoped to its simplification
  stage, the baseline's periodic opacity reset is retained against that method's
  removal of it, and one of four codebooks does not exist because
  `sh_degree = 0`. This is the correct design for a factorial study, but it
  means "we ran EDGS, Mini-Splatting and CompGS-VQ on underwater data" is both
  more flattering and false.
- **No claim of statistical significance.** Three seeds on four scenes does not
  support a test with meaningful power. Effect sizes are reported against
  measured dispersion, with the sample size stated; effects of the same order as
  their dispersion are reported as inconclusive rather than as nulls.
