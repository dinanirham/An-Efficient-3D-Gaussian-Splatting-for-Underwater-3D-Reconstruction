# Thesis Repositioning

**Gate 2 deliverable.** Two candidate framings, a recommendation, and the revised research
apparatus that follows from it.

> ## ✅ APPROVED — Framing A, 2026-09-10
>
> Drafting proceeds in the order the brief sets: **Chapter 2 → Chapter 1 → Chapter 3 →
> Chapter 4 → Chapter 5**. Chapter 2 is blocked on the six literature breakdowns
> (`06-experiment-and-literature-plan.md` Part 1); Chapters 3 and §§4.1–4.3 are unblocked now.
>
> **What the approval commits to withdrawing:** the manuscript's headline M2 result under the
> Mini-Splatting name (D-1), the AUV deployment framing (D-10), the composite PSNR/MB and
> FPS/MB metrics (C.1), and the title's implicit method claim.

### Evidence that has arrived since this section was written

Three things strengthen Framing A rather than change it, and one narrows what may be claimed.

**H4 is established.** §4.5 listed RQ3 as pending. It is now answered at **n=12 against a
12-run control**: every A2 run's largest attenuation drop lands on a simplification boundary,
no A0 run loses a channel, and the collapse is **bistable and seed-conditioned**
`[13-campaign-addendum.md §13.13]`. Contribution #2 moves from "designed" to "demonstrated".

**A fourth integration-boundary instance.** The A1 investigation cost three partial fixes,
and the pattern is the finding: EDGS controls the periodic opacity reset *and* the size-based
prune with a single parameter, and reimplementing them site by site re-armed each in turn.
That is the same class as CD-22/CD-23 — a property of the seam, invisible to either
component's documentation — and it is the most legible instance of the four.

**E.7 answers the meta-review directly.** `A1/Curasao/s0` produced the campaign's best test
PSNR with two of three attenuation channels permanently dead. *The physics broke while the
fidelity improved.* This is the concrete answer to "why do these mechanisms behave differently
under underwater conditions" — and it is not an answer PSNR, SSIM or LPIPS could produce.

**What it narrows.** Because the collapse is seed-conditioned, cells with mixed seeds contain
two physically different models. Every aggregate must carry the collapse covariate, and
Chapter 4 must report it rather than pool over it. `analyse.py` now surfaces this before any
contrast.

---

## 4.1 Why repositioning is required, not optional

Three independent lines of evidence converge on the same conclusion.

**The reviewers read it as a comparison, and said the bar for a comparison is higher.**
R3: *"Since the paper does not contribute a new method, the comparison itself needs to be
broader and more carefully controlled."* R2 and the meta-review say the same in different
words. The paper was not rejected for being a comparison — it was rejected for being a
comparison that did not meet a comparison's evidentiary standard.

**The author's own submission title already conceded it.** The thesis says *An **Efficient**
3D Gaussian Splatting for Underwater 3D Reconstruction* — a method claim. The submission said
*Efficiency–Fidelity **Tradeoffs** in Compact 3D Gaussian Splatting* — a study claim. The
second is the honest one.

**The headline result does not survive audit.** B.1/B.2 in the claim ledger: the "best
mechanism" finding describes a pruning rule that is not Mini-Splatting (D-1), reported without
the dispersion needed to read it (D-5). A repositioning that rested on it would fail again.

What has *changed* since the submission is not the experiments — it is that the work now has
**two composition-level findings that no source method documents**, and an implementation
whose fidelity to the source methods is demonstrated rather than asserted.

---

## 4.2 Framing A — conservative, defensible today

> **A controlled factorial study of whether terrestrial 3DGS efficiency mechanisms transfer to
> physics-aware underwater reconstruction, and of the integration boundaries that determine
> whether they do.**

**Contribution type:** a controlled empirical study, plus two methodological findings about
method composition.

**What it claims**

1. Three efficiency mechanisms, faithfully reimplemented against a **verified** baseline, are
   evaluated as a 2³ factorial with three seeds — both directions of inference, dispersion
   reported per scene.
2. **Composition changes behaviour in ways no component documents.** Two demonstrated
   instances: the medium model's non-invariance to primitive-count reduction (analytical, with
   a remedy), and the gradient-destination defect (empirical, with a fix and a regression
   test).
3. The dispersion of the outcome variable is itself a finding: 6–29% per scene, which bounds
   what any single-run comparison in this literature can support — including the prior
   version of this work.

**Evidence required:** S1 ✅ · S2–S5 · per-scene dispersion ✅ · faithful implementation ✅ ·
verified baseline ✅.

**Reviewer concerns answered:** R2.2, R3.2, R3.3, R3.6, R4.3 fully; R2.1, R2.3 partially.
**Not answered:** R3.1 (related work), R3.4 (Pareto).

**Risk:** an examiner may still ask "what is new?" The answer — *composition properties at
integration boundaries* — is real but abstract, and rests on two instances.

---

## 4.3 Framing B — stronger, requires additional evidence

> **An efficiency–fidelity characterisation of underwater 3DGS across operating points,
> identifying which mechanism dominates at which budget and why underwater image formation
> changes the answer.**

Framing A plus **a rate–distortion sweep**: multiple `n_bud` values, multiple codebook sizes,
producing a Pareto surface rather than one point per mechanism.

**What it adds**

4. Mechanism ranking as a **function of budget**, not a single verdict — directly answering
   R3.4 and converting C.2 from *untestable* to *testable*.
5. Underwater-conditioned explanation: whether the ranking shifts with scene attenuation,
   backscatter contribution, or depth range — R2.3 and the meta-review's M.2.

**Additional evidence required:** a budget sweep (costed in
`06-experiment-and-literature-plan.md`), and the medium-parameter analysis that S2's
diagnostics enable.

**Reviewer concerns answered:** all of R3 except R3.5 (four scenes, intractable).

**Risk:** compute. And the sweep must not be allowed to displace the factorial, which is what
answers the interaction question.

---

## 4.4 Recommendation

**Adopt Framing A now; build toward Framing B.**

Reasoning:

1. **Framing A is supportable with runs already scheduled.** It requires nothing beyond
   S2–S5, which are queued. Framing B requires an experiment not yet designed into the
   campaign.
2. **The two framings are nested, not alternatives.** Framing B is A plus one axis. Writing A
   first costs nothing if the sweep later happens; writing B first risks a thesis whose
   central claim depends on runs that may not complete.
3. **The gap between them is exactly one reviewer concern** — R3.4. That is worth knowing
   precisely: if compute allows one more experiment, this is the one, and its value is
   traceable to a named reviewer objection rather than to a general wish for more data.
4. **Framing A already answers the meta-review's first two demands.** M.1 (contribution beyond
   transfer) is met by the two composition findings; M.2 (why they behave differently) is met
   by the diagnostics, once S2 lands.

**What must be abandoned either way:** the thesis title's implicit method claim, the AUV
deployment framing, the composite PSNR/MB and FPS/MB metrics, and the prior A2 result under
the Mini-Splatting name.

---

## 4.5 Revised research apparatus

### Central thesis statement

> Efficiency mechanisms developed for terrestrial 3D Gaussian Splatting do not transfer to
> physics-aware underwater reconstruction as independent, behaviour-preserving modules. Their
> integration with a scene-global medium model introduces couplings that are invisible to the
> component methods' own validation, and that determine whether the efficiency gains are
> realised.

### Research questions

| | Question | Answered by | Status |
|---|---|---|---|
| **RQ1** | Do the three mechanisms individually transfer to a physics-aware underwater baseline, and at what efficiency–fidelity cost? | A1−A0, A2−A0, A3−A0 | S3, S2 |
| **RQ2** | Do they compose additively, or do they interact? | two-way and three-way factorial contrasts, both directions | S4, S5 |
| **RQ3** | Does primitive-population reduction perturb medium identifiability, and does a re-identification burst restore it? | Ẑ/β diagnostics across the simplification boundary; CD-6 ablation | S2 |
| **RQ4** | What integration properties, invisible to each component's own validation, govern whether the composition behaves as intended? | the CD ledger; the gradient-destination and Ẑ-rescale findings | ✅ partly answered |
| **RQ5** *(Framing B)* | Does mechanism ranking persist across operating points? | budget sweep | **not designed** |

### Hypotheses

| | Hypothesis | Test | Prior |
|---|---|---|---|
| **H1** | Each mechanism moves its own target cost beyond seed dispersion | main effects vs pooled sd | directional |
| **H2** | Gains are attenuated relative to published terrestrial magnitudes | renormalised comparison | **structural for M3**: 14 floats/primitive, not 59 |
| **H3** | M2×M3 is sub-additive | `A6 − A2 − A3 + A0` | OMG's premise |
| **H4** | Primitive reduction rescales Ẑ and thereby perturbs β; CD-6 mitigates | β drift across iteration 15 000 | **central** |
| **H5** | M1×M2 is degenerate unless the budget binds | `A4 − A1 − A2 + A0` | controlled by preflight |

### Variables

- **Independent:** M1, M2, M3 (binary); *(Framing B: `n_bud`, `k` as ordinal)*
- **Dependent:** PSNR (both conventions), SSIM, LPIPS, primitive count, model size, render fps,
  ms/frame, peak render memory, training wall clock, effective optimizer steps
- **Blocks:** scene (4) · **Repeats:** seed (3)
- **Controlled:** hardware (A100 enforced), undistorted data, iteration schedule, evaluation
  schedule, container format, LPIPS backbone, `n_bud` fixed pre-campaign
- **Measured-not-controlled:** run-to-run dispersion, which is itself reported

### Contributions, in the order they should be claimed

1. **A verified baseline.** A0 demonstrated indistinguishable from unmodified SeaSplat at
   n=3 — the reference point the prior version asserted but never established.
2. **Two integration-boundary findings** with remedies and regression tests: the medium
   model's non-invariance to primitive reduction (CD-6), and the gradient-destination
   invariant (CD-22/CD-23, `verify_rasterizer` T7/T8).
3. **A faithful reimplementation** of three mechanisms whose prior implementation deviated
   materially (D-1, D-2), with the deviations documented.
4. **A dispersion measurement** that bounds interpretation of single-run comparisons in this
   literature — including the prior version of this work.
5. **The factorial results themselves** — pending S2–S5.

Note the ordering: the *methodological* contributions are ranked above the empirical ones,
because they are established and the empirical ones are not yet.

### Scope and validity boundaries

**In scope:** four SeaThru-NeRF scenes; one underwater formulation (SeaSplat); one hardware
configuration; `sh_degree = 0`; three mechanisms at one operating point each.

**Out of scope, stated explicitly:** AUV or embedded deployment (D-10); generalisation to
water types beyond the corpus; comparison against rate-distortion, entropy-coding or
structured-representation families (D-8) — *unless* the Chapter 2 work in
`06-experiment-and-literature-plan.md` is done, which changes this to "surveyed but not
evaluated"; any claim that ranking persists across budgets (D-9).

---

## 4.6 What this repositioning costs

Honestly stated, because the brief asks for claims to be withdrawn where required:

- The manuscript's **most-cited result is withdrawn** (B.1/B.2).
- The **title changes** to reflect a study rather than a method.
- **Chapter 4 must be rebuilt from new runs.** Its current tables are from a different
  codebase with documented fidelity gaps; they cannot be retained "for continuity", which the
  brief prohibits directly.
- **Chapter 5's conclusions all fall**, since they rest on Chapter 4.

What is retained: Chapters 1–3 in structure, most of Chapter 2's literature, the dataset and
preprocessing account, and the author's framing of the underlying question — which the
reviewers consistently described as practical and worth asking.
