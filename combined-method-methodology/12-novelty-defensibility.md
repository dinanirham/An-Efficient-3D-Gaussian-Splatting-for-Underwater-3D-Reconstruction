# §12 — Novelty defensibility

## 12.1 The claim, stated in one paragraph

> A scene-global physical medium model whose only spatial input is a **per-frame min–max
> normalised rasterized depth map** is **not invariant to changes in the primitive
> population**. Reducing the Gaussian count mid-training rescales that depth field, and
> because the medium enters the image formation model only through the product `β·Ẑ`, the
> rescale is indistinguishable from a change in the medium coefficients — SeaSplat's own
> degeneracy D-2, arriving not as something the optimizer can exploit but as a step
> discontinuity injected from outside the objective. Every well-posedness mechanism SeaSplat
> provides (gradient detachment, alternating optimization, global homogeneity) defends
> against the optimizer *finding* D-2; **none defends against D-2 being handed to it.**
> This work identifies that failure, specifies the fix (a medium-only re-identification burst
> immediately after each population change), and situates it inside a factorial study of
> three efficiency mechanisms on a physically-grounded underwater baseline.

**Claim type: (c) — a required well-posedness / integration fix — supported by (a), a
genuine prior-art gap. Claim (b) is not available: no combined-method measurements exist in
this evidence base.**

---

## 12.2 What a reviewer could not find elsewhere

Four things, in decreasing order of force.

### 12.2.1 The `Ẑ`-rescale / medium-identifiability interaction — claim (c)

**Where it comes from.** Two facts, each verified in a different folder, that no single
source puts together:

1. SeaSplat sets `norm_depth_max = True`, so `Ẑ` is min–max renormalised to `[0,1]`
   **per frame**, and consequently "the learned `β` are in units of *normalised per-frame
   depth*, **not** inverse metres" and "the same physical depth maps to different `Ẑ` in
   different frames, which is in tension with the global-`β` assumption"
   `[../seasplat/05-constraints.md §5.3; repo: train.py:233-237]`.
2. `β` and `Ẑ` appear only as the product `βẐ`; the substitution `Ẑ ← cẐ, β ← β/c` leaves
   `Î` **exactly** invariant — degeneracy D-2 `[../seasplat/05-constraints.md D-2]`.

Add a third fact from a different lineage — Mini-Splatting removes 60–90% of primitives at a
single iteration `[../mini-splatting/08-…​ §8.1]` — and the conclusion follows immediately:
`Ẑ_min` and `Ẑ_max` change discontinuously, `c ≠ 1`, and the medium model is now
mis-identified by an amount nothing measures.

**Why no source states it.** None of the four has both halves. SeaSplat has the normalisation
and the degeneracy but never changes its primitive population outside 3DGS's smooth ADC.
Mini-Splatting, EDGS and CompGS-VQ change the population dramatically but have **no medium
model at all** — their rendering equation contains no depth-dependent term, so a rescale of
rendered depth is invisible to their objectives. The interaction is a property of the
*composition*, and it is exactly the kind of finding a composition study exists to produce.

**Why it is checkable.** It makes a falsifiable prediction with a named diagnostic: log
`Ẑ_min`/`Ẑ_max` and `β_att`/`β_bs`/`B^∞` across the simplification boundary
(`08-computational-profile.md` Table 8.3c, CD-12). A large `β` jump at 15 000 iterations
confirms it; no jump refutes it. That costs one logging statement.

### 12.2.2 The domain-specific failure alignment — supporting claim (c)

Three independent folders name the *same region* as their weak point, for three different
reasons, and the region is the one this domain is about:

| Source | Its own words | The region |
|---|---|---|
| SeaSplat | 3DGS "places many floaters within the water column"; `L_op` exists to zero opacity there and is worth **+2.42 dB alone** | water column |
| EDGS | "Dense matchers are weakest on textureless, non-Lambertian and view-dependent surfaces — sky, water, glass … **the water column is exactly a region where RoMa will produce low-confidence or hallucinated matches**"; and "**No mechanism to add primitives**" | water column |
| Mini-Splatting | "This strategy fails in areas without a certain depth value, such as the sky"; and the depth-reinit sampler is **biased toward low-opacity pixels** | sky ⇒ water column by analogy, stated in that folder |

**The composition therefore concentrates three failure modes on one region**, and the
baseline's only defence there (`L_op`, λ = 0.01) is simultaneously being perturbed by both
mechanisms through the opacity variable (interaction candidate IC-1). That is a structural
observation about *this* combination on *this* domain. A terrestrial study cannot make it;
an underwater study of any single mechanism cannot make it.

### 12.2.3 The prior-art gap — claim (a)

No published method combines dense correspondence-based initialization, budget-based
primitive reduction, and attribute vector quantization on a physically-grounded underwater
3DGS baseline; and **no underwater 3DGS method found uses K-means attribute quantization at
all**. The nearest neighbours are enumerated in `01-taxonomy.md` §4(a) and §5:

- **UW-3DGS** — closest: same domain, same scenes, physics-aware *uncertainty* pruning +
  VM tensor decomposition of the *medium field*, standard sparse COLMAP init.
- **TUGS** — strongest underwater efficiency result, but via a change of *primitive type*.
- **GETA-3DGS / LFGS** — prune+quantize composition, but terrestrial and medium-free.

**This claim is deliberately not leaned on.** "Nobody has run these three together on
underwater data" is a gap, not an insight, and GETA-3DGS/LFGS show the composition move
itself is unsurprising in air. Claim (a) establishes that the space is empty; claim (c)
establishes that it was worth entering.

### 12.2.4 Method-level bookkeeping that is genuinely non-trivial

Not novelty in the paper sense, but a reviewer asking "what did you actually have to work
out?" gets fourteen concrete answers in `06-implementation-deltas.md` §6.5. Four are worth
naming here because they change what the study *measures* rather than how it runs:

- **CD-8** — disabling CompGS-VQ's ℓ1 opacity regulariser, without which the M2 and M3
  factors are not independent and the factorial design does not measure what it claims.
- **CD-5** — replacing a sampling *ratio* with a primitive *budget*, without which A4 and A7
  can silently degenerate to A1 and A5 and produce a spurious null.
- **CD-9** — dropping the SH codebook, which caps the achievable compression ratio *a priori*
  and makes any comparison against CompGS-VQ's published 41–65× invalid unless renormalised
  against a 14-float-per-Gaussian baseline rather than 59.
- **CD-1** — a configuration layer above SeaSplat's argument parser, without which the
  matrix cannot be run reproducibly at all, because ~12 boolean flags default `True` and are
  registered `action="store_true"`.

---

## 12.3 The strongest counter-objection, and whether the evidence answers it

### The objection

> *"You have not measured anything. Claim (c) is a hypothesis about an interaction, dressed
> as a contribution. Any competent engineer combining these methods would hit the same
> issues and fix them the same way; that is integration work, not research. And if you run
> the matrix and find no interaction, you will have shown that three known mechanisms
> compose — which is what their authors already claimed."*

This is the objection to answer, and it has three parts.

### Part 1 — "you have not measured anything"

**The evidence does not answer this. It is conceded.** `08-computational-profile.md` §8.0
records it as a fact rather than working around it: no combined-method metrics, logs,
checkpoints, or renders exist anywhere in the evidence base available to this pass. Every
efficiency and quality cell reads `NO RESULTS FOUND`.

What the work does instead is make the measurement obligation **precise**: the eight-cell
matrix, the additive null hypothesis and its two contrast forms (`10-reproducibility.md`
§10.4), the three interaction terms with directional predictions
(`08-computational-profile.md` §8.4), the diagnostic quantities that localise a failure to
the medium model rather than to "pruning hurts" (Table 8.3c), and the seed/dispersion
discipline that would make an interaction claim survive review (§10.4). That is a genuine
deliverable, and it is not the same as a result.

**Verdict: the objection stands. Claim (b) is not made, and `01-taxonomy.md` §4(b) says so
explicitly rather than gesturing at "future work."**

### Part 2 — "any competent engineer would hit the same issues"

**The evidence partly answers this, in an unusual way: the source breakdowns themselves are
the counter-evidence.** Three of the four source repositories contain undocumented mechanisms
that their own papers omit — EDGS's opacity decay and LR clamp, Mini-Splatting's removed
opacity reset and LR rewind, SeaSplat's `learned_bg`. Each was found only by reading code
against paper. An engineer who *implemented from the papers* would compose four methods and
get a system in which:

- `reset_opacity()` never fires, without knowing it (Mini-Splatting D-1);
- opacity is decaying by a cumulative logit shift of −15, without knowing it (EDGS D-3);
- `B^∞` is being warm-started from an undocumented fourth parameter, without knowing it
  (SeaSplat D-7);
- the test set is empty (SeaSplat D-17 **and** EDGS D-12, independently);
- and the quantizer never fires at all (CompGS-VQ D-6, `kmeans_st_iter = 30000`).

**Four of those five are silent.** Nothing crashes, nothing warns. The "any competent
engineer" objection assumes the composition problems are visible; the documented evidence is
that they are not. That is a real answer, though a modest one: it argues the integration work
is *hard*, not that it is *novel*.

The `Ẑ`-rescale finding (§12.2.1) is a stronger answer, because it is not a bookkeeping trap
— it is a statement about identifiability that follows from two published facts and is
falsifiable by one logging statement. **A competent engineer would very plausibly not hit it,
because it does not manifest as an error. It manifests as slightly worse numbers in the
pruned configurations, which is exactly what one expects from pruning.** That is the strongest
single sentence in the defence: *the failure mode is camouflaged as the expected result.*

**Verdict: partly answered. The claim survives as "non-obvious," not as "unreachable."**

### Part 3 — "if you find no interaction, you have shown nothing"

**This is wrong, and the evidence supports saying so.** A null result would show that three
efficiency mechanisms developed independently for terrestrial, medium-free 3DGS compose
cleanly on a physically-grounded underwater baseline **once the fourteen integration
decisions of §6.5 are applied** — which is a conditional nobody has established, and which
directly contradicts the premise of `../OMG/`, the most recent method in the composition's
own lineage: "a smaller set of Gaussians becomes increasingly sensitive to lossy attribute
compression" `[../OMG/00-index.md, paper Abstract]`.

A clean null on A6 would be a *refutation of OMG's premise in this regime*, which is
publishable. A sub-additive A6 would be a *confirmation of it in a new domain*, which is also
publishable. **The design has no uninformative outcome on that cell** — which is the property
a factorial design is chosen for.

**Verdict: answered.**

### A fourth objection worth pre-empting: "why not just use OMG?"

`../OMG/` already co-designs count reduction and attribute compression, is built directly on
Mini-Splatting, and reports 4.06 MB at 27.06 PSNR with 350 FPS `[../OMG/00-index.md]`. The
honest answer is that **OMG would very likely be a better *system*, and that is not what this
study measures.** OMG's co-design deliberately entangles the two mechanisms — local
distinctiveness scoring feeds the pruning, sub-vector quantization is sized against the
pruned population — so it cannot answer whether they interact; it *assumes* they do and fixes
it. The factorial study answers the question OMG's design presupposes, on a baseline OMG has
never been applied to. Stating this in the related-work section converts the objection into a
positioning argument. It should be stated, not dodged.

---

## 12.4 The narrower contribution, if the evidence supports only that

The brief asks for an honest naming of a narrower contribution if that is what the evidence
supports. It partly is. Three fallback positions, in decreasing order of ambition:

### Fallback 1 — the identifiability finding as a standalone note

*"Primitive-count reduction breaks medium-parameter identifiability in scene-global
underwater 3DGS, and here is the diagnostic and the fix."*

This needs only **A0 and A2** — two cells, four scenes, three seeds — plus the `Ẑ`/`β`
logging of CD-12. It is the smallest experiment that could support a real claim, it targets
claim (c) directly, and it does not depend on the initialization or quantization axes at all.
**If time or compute is short, this is the experiment to run.**

### Fallback 2 — an integration and reproducibility study

*"Composing four 3DGS-family methods requires fourteen undocumented decisions; here they
are, here is why each is forced, and here is the protocol that makes the composition
measurable."*

This is what `06-implementation-deltas.md` §6.5, `10-reproducibility.md` and
`11-paper-vs-repo-disagreements.md` already constitute. It is a **methods contribution**, not
a method contribution — the kind of thing that is genuinely useful and rarely publishable
alone at a vision venue, but is entirely appropriate as the methodology chapter of a thesis,
and defensible in front of a committee precisely because it is verifiable line by line.

### Fallback 3 — a domain-transfer benchmark

*"Three terrestrial 3DGS efficiency mechanisms, transferred to underwater scattering media
and measured against their published terrestrial gains."*

The weakest framing, and the one to avoid unless the interaction analysis fails entirely: it
reduces the work to "we ran known methods on new data." It is listed because it is the
honest floor — and because even at the floor, the 4.2×-smaller per-Gaussian baseline
(`08-computational-profile.md` §8.2) means the transferred compression numbers will *not*
match the published ones, and explaining why is a small but real result.

---

## 12.5 Summary verdict

| Question | Answer |
|---|---|
| Which claim type does the evidence support? | **(c)**, supported by **(a)** |
| Is (b) supported? | **No.** No combined-method measurements exist in this evidence base. `01-taxonomy.md` §4(b) and `08-computational-profile.md` §8.0 state this rather than working around it. |
| Is the novelty claim defensible as written? | **Yes, as a methodological claim.** The `Ẑ`-rescale identifiability finding is derived from two verified facts in different folders, is not stated by any source, is falsifiable, and has a named diagnostic. |
| What is the strongest objection? | "You have not measured anything." |
| Does the evidence answer it? | **No.** It is conceded. What the work supplies is a precise measurement obligation, not a measurement. |
| What would upgrade the claim from (c) to (c)+(b)? | Running the eight-cell matrix with ≥3 seeds and reporting the three interaction terms against the additive null. The A6 cell is informative in both directions. |
| What is the minimum experiment that supports a real claim? | **A0 vs A2, with `Ẑ_min`/`Ẑ_max` and `β` logged across the simplification boundary.** Two cells. |
| What must not be claimed? | Any efficiency or quality number for A1–A7; any statement about non-additivity; any compression ratio compared to CompGS-VQ's published 41–65× without renormalising to a 14-float-per-Gaussian baseline. |

---

## 12.6 What execution changed — a second claim-(c) instance, and a candidate claim (a)

§12.1–§12.5 were written before any code ran. Two things have changed and one has not.

### 12.6.1 Claim (c) gains a second, independently discovered instance

§12.2.1 argues claim (c) from one case: a scene-global medium model whose only spatial input
is a per-frame min–max-normalised depth map is not invariant to primitive-population change,
so pruning injects degeneracy D-2 from outside the objective.

Execution produced a second case of the same *kind*, by a completely different route.
Substituting the rasterizer (CD-13) preserved every forward value — `α` in range,
compositing correct, `Z_raw/α` recovering depth to seven decimal places — and silently
changed **which loss gradients reach density control**. The baseline configuration then
converged to a sixth of the baseline's primitive count `[measured n=1]`, and no check in this
methodology could have seen it, because every check was a check on returned values
`[05-constraints.md §5.6]`.

That strengthens claim (c) in a specific way. One instance invites the reading "you found a
quirk of this particular medium model." Two instances, one derived analytically and one found
empirically, at different seams, support the more general statement:

> **A composed method has properties at its integration boundaries that belong to neither
> component and appear in neither component's documentation. Some are reachable by analysis;
> some are reachable only by execution; and the second class cannot be enumerated in
> advance.**

That is a claim about method composition, which is what this work is. It is also
uncomfortable for the field it sits in, since the standard practice — a cumulative ablation
ladder on a composed system — has no step at which such a property would surface.

### 12.6.2 Mechanism D is a candidate claim (a), and is not yet claimable

The defective configuration is not merely a bug. Detaching alpha-loss gradients from
densification gave **6× fewer primitives for −0.107 dB** test PSNR `[measured n=1]` — larger
than M1, M2 or M3 is expected to deliver, and *cheaper than doing nothing*, since detaching
removes a rasterization pass rather than adding one.

Nothing in the SeaSplat, Mini-Splatting, CompGS-VQ or EDGS literature reports that alpha-loss
gradients inflate 3DGS densification. If it holds, it is a **prior-art gap — claim (a)** — and
not an integration fix.

**It is not claimable yet, and the reason is worth stating precisely.** That figure comes
from a single pair of runs, at different seeds, against a baseline now known to be defective.
Replication subsequently established that primitive count carries a 6–29% run-to-run spread
depending on scene `[08-computational-profile.md §8.2b]`, which is the same order as many
effects this study will report. A single-run ratio on that quantity is not evidence — a
lesson this project paid for, having tested four hypotheses against exactly such ratios
before measuring the spread.

It is therefore measured as cell `A0D`, stage S6, twelve runs against the corrected baseline,
and **must not appear in any draft before that contrast completes**. It is deliberately not a
fourth factor: M1 disables densification, so D is provably inert in all eight M1 cells and a
2⁴ design would be half duplicates.

### 12.6.3 What has not changed

**Claim (b) remains unavailable**, and §12.3's concession still stands in full. The matrix is
running; no interaction has been measured.

There is now a sharper reason for caution than "no measurements exist". The measured
dispersion means an interaction term — a difference of differences, carrying roughly twice
the variance of a main effect — may not clear the noise floor even after all 108 runs. If it
does not, the honest report is `UNDETERMINED`, which the analysis tooling emits rather than
rounding to zero. **A null interaction and an unresolvable one are different findings**, and
the distinction has to survive into the write-up.

### 12.6.4 Revised verdict

| Question | Answer |
|---|---|
| Which claim type does the evidence support? | **(c)**, supported by **(a)**, now with **two** independent instances of (c) — one analytical, one empirical |
| Is (b) supported? | **Still no.** The matrix is in progress. |
| Is there a new candidate claim? | **Yes — mechanism D**, a possible prior-art gap in its own right. `[measured n=1, against a defective baseline]`. Not claimable until S6. |
| What did execution add that reading could not? | Two integration defects invisible to value-level checking (CD-22, CD-23), a missing instrument the design depended on (CD-24), a budget rule that would have collapsed two cells (CD-25), and the measured dispersion that bounds every effect size this study can report. |
| What must not be claimed? | Everything in §12.5's row, **plus** any figure for mechanism D until `A0D` completes, **plus** any statement of the form "A0 converges to ~4.4M" — that is a Curasao figure; the four-scene median is 2.48M. |

---

## 12.7 A defect in a published method, not in the composition

*Added after CD-26. This is a different claim type from everything in §12.6 and
is separated for that reason.*

Every finding recorded so far is about **composition**: a property of a seam
between two methods, belonging to neither. §12.6.1 argues that as the general
form of claim (c), and it is the honest description of the gradient-destination
defect, the medium-identifiability analysis, and the coupled-parameter finding
from the M1 schedule sequence.

**CD-26 is not that.** It is a defect in EDGS as published, reachable without
composing it with anything.

### The structure of the claim

EDGS states the degeneracy itself `[../EDGS/05-constraints.md D-2]`:

> *"When the two view rays are nearly parallel … the least-squares solution is
> unstable in depth — arbitrarily far, arbitrarily wrong. Dense matchers happily
> return matches for such pairs."*

It then assigns that degeneracy to its reprojection filter `p^proj`. **The
filter cannot detect it.** A near-parallel pair yields a point lying on both
rays, so it reprojects close to both original pixels; the error is small
*because* the geometry is ill-conditioned. `p^proj` addresses EDGS's own D-4 —
confident hallucinations that happen to triangulate — which is a different
failure mode that the paper lists separately.

So the method identifies a degeneracy, names a remedy, and the remedy does not
address it. No composition is required to reach that conclusion.

### Why it has not been observed

`num_refs = 180`. At that viewpoint density most pairs have healthy parallax, so
ill-conditioned triangulations are rare enough for the `α < 0.005` prune to
absorb, and the published evaluation never approaches a regime where they are
not. **This corpus has 15–25 training views.** `K_ref = min(180, V)` collapses to
the view count, near-collinear pairs become common, and a latent flaw becomes
the dominant failure.

**The finding is therefore conditional and the condition is stateable**: the
remedy is adequate above some view-count threshold and inadequate below it. This
study does not locate that threshold — it observes one point on the wrong side
of it.

### What it is worth, and what it is not

**It is a genuine claim (a)** — a prior-art gap — in the narrow sense that the
gap is a defect rather than a missing method. It is defensible from the source
material alone: the degeneracy is quoted from EDGS's own analysis, and the
inadequacy of `p^proj` follows from the geometry rather than from measurement.

**It is not a contribution to efficient 3DGS.** A parallax filter is textbook
structure-from-motion; COLMAP has applied one for a decade. The contribution is
noticing that a recent method omitted it, and that the omission is invisible in
the regime the method was evaluated in.

**It must not be overstated.** The correct framing is *"we found that EDGS's
stated remedy for its own D-2 does not address D-2, and that this matters at low
view counts"* — not *"we improved EDGS"*. The distinction matters because the
first is supported by the source text plus a simulation, and the second would
require a controlled comparison this study is not running.

### Evidence status

| | |
|---|---|
| The degeneracy exists and EDGS names it | quoted from the source `[../EDGS/05-constraints.md]` |
| `p^proj` cannot detect it | analytical, plus simulation at 0.5 px matcher noise: a 0.0014° pair recovers median depth 3.1 against a true 4 000, 48.6% behind a camera |
| **`p^proj` and cheirality demonstrably do not catch it on real data** | `[measured n=1 per scene]` — across four scenes they removed **1.3%** of 1 500 000 triangulations; the parallax filter removed **24.0%**, which is **95% of all rejections**. 13.1–41.3% of each previously-accepted cloud was ill-conditioned |
| It has a measurable consequence here | `[measured n=1]` — `z_max` 122 673, `Ẑ ∈ [0, 0.0007]`, two attenuation channels clamped dead |
| The corrected initializer behaves better | **Supported** `[measured n=1 per scene]` — `z_max` 122 673 → 74–123 on all four scenes, no negative attenuation channel anywhere, bounding box 156 172 → 112 on the worst axis, occupancy 0.01% → 0.96%, and β_att ordered R > G > B on three of four `[06-implementation-deltas §6.8]` |

Every row is now supported. The claim is bounded as stated above: EDGS's remedy
for its own D-2 does not address D-2, and it matters below a view-count
threshold this study observes one point on the wrong side of.
