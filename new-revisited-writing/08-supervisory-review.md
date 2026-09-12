# Supervisory Review — implementation and results

*Read through the persona of `07-supervisor-persona.md`. Covers cells A0–A3 complete at twelve
runs each, A4 partial, against the implementation as committed. The review's purpose is not to
summarise `results-00` … `results-03`, which are accurate; it is to test whether the central
argument holds, and to say what the work has not yet noticed about its own result.*

---

## 1. Verdict

The campaign has produced one finding of genuine scientific weight, two corrections that a
careful reader of the source literature could not have derived without running the code, and a
measurement discipline that is better than most of what it will be compared against.

It has also **mis-stated its own central finding**, in a way that makes the finding smaller
than it is and leaves its most important negative result unexplained. §2 develops this and it
is the substance of the review. Everything else follows from it.

The working claim is: *efficiency mechanisms perturb the medium model through the shared depth
variable.* The evidence supports something stronger and more interesting: **the medium model
was never identified in absolute terms, and the efficiency mechanisms are the instrument that
reveals it.** That is a claim about SeaSplat — a published method — rather than about this
student's combination of three others, and it is a better thesis.

---

## 2. The central argument, restated

### 2.1 What the estimator actually estimates

The image formation model composes a rendered radiance through

```
Î = Ĵ ⊙ exp(−β_att · Ẑ)  +  σ(B∞) · (1 − exp(−β_bs · Ẑ))
```

with nine medium scalars held **global to the scene**. The depth `Ẑ` entering this expression
is not the rendered depth. For each frame *f* it is the rendered depth renormalised by that
frame's own extrema:

```
Ẑ_f(p) = ( Z_f(p) − m_f ) / ( M_f − m_f ),     m_f = min_p Z_f(p),  M_f = max_p Z_f(p)
```

`[repo: train.py:349–352]`. This is confirmed in code: the constants are captured immediately
before the normalisation is applied, "because afterwards they are 0 and 1 by construction and
carry no information."

Now impose the physical law the model is supposed to express. Attenuation over a true distance
`Z` is `exp(−β_phys · Z)` with `β_phys` in inverse length. Substituting the normalisation, the
model's attenuation for frame *f* is `exp(−β_att · (Z_f − m_f)/(M_f − m_f))`. For this to
reproduce the physical law across that frame, one requires

```
β_att = β_phys · ( M_f − m_f )
```

**The right-hand side depends on the frame.** A single global `β_att` therefore satisfies the
physical law on every frame simultaneously only if the depth range `M_f − m_f` is constant
across the training set. It is not, and nothing in the design makes it so.

### 2.2 The consequence

The fitted `β_att` is not an estimate of a medium property. It is a **compromise across the
training set's distribution of depth ranges**, weighted by each frame's contribution to the
photometric loss. Three things follow immediately, and the third is the one the project has
not drawn.

**First**, `β` has no physical units and no absolute meaning. *The work already knows this* —
`chapter/09-summary.md` records that "the estimated medium coefficients carry no physical
interpretation, being expressed in normalised per-frame depth rather than inverse metres." It
is stated there as a limitation of interpretation.

**Second**, `β` is a function of the geometry, not merely of the medium. The depth-range
distribution `{M_f − m_f}` is a property of the primitive population. Change the population and
the distribution moves; the compromise moves with it.

**Third — and this is the step not yet taken — those two statements are the same statement,
and together they dissolve the distinction between the acknowledged limitation and the measured
collapse.** The project treats the non-physicality of `β` as an interpretive caveat in one
document and the collapse of `β` as an empirical finding in another. They are one fact seen
twice. A parameter that is only defined relative to a per-frame normalisation *must* move when
the normalisation moves. The simplification boundary did not break the medium model. **It
revealed that the medium model had never been identified in the first place**, and it did so by
moving the only thing `β` was ever defined against.

### 2.3 Why this is a stronger claim, not a weaker one

The working version — *M2 perturbs the medium model* — is a claim about a composition, and it
invites the reply that the composition was done badly. The version the evidence supports is a
claim about **SeaSplat's estimator as published**, reachable by anyone who reads the
normalisation and the image formation model together, and demonstrated here at n = 12 against a
12-run control.

It also survives the Supervisor's third question. *Is that a property of the method or of your
implementation?* Under the working version the honest answer is "we believe the method, but a
reviewer may reasonably ask." Under the restated version the answer is **the method** — the
normalisation is SeaSplat's, the globality of the medium is SeaSplat's, and the incompatibility
between them is derivable from the source without running anything.

---

## 3. Why the remedy failed — derived, not guessed

`03-claim-validity-ledger` E.6 records that CD-6's 200-step medium re-identification burst did
not restore `β` in any of the six collapsed runs, and `05-constraints.md` now records that
*why* it fails "is not established."

§2 establishes it. **There is nothing to restore.**

A medium-only re-fit after a population change re-converges to the compromise defined by the
*new* depth-range distribution. That is the correct behaviour of the estimator, not a failure
of it. The burst was specified on the premise that `β` has a true value which the population
change disturbed and which additional optimisation could recover. The premise is false: the
pre-simplification `β` was itself only a compromise over the pre-simplification distribution,
and it has no claim to be the target.

This reclassifies the negative result, and the reclassification is favourable. CD-6 is not an
under-budgeted remedy that needs more steps — a reading which leaves open the embarrassing
possibility that the student simply did not try hard enough. It is a **correctly implemented
remedy resting on a false premise**, and identifying the false premise is worth more than the
remedy would have been. The open question in `open-questions.md` OQ-10 should be closed in
these terms rather than left as "under-budgeted or misconceived": the analysis says
misconceived, and says why.

### 3.1 It also explains the shape of the collapse

Three observations currently reported without a mechanism fall out of §2.

**Why count does not predict it** (E.20 — A1 at ~230k primitives loses 0 of 10 channels; A2 at
~145k loses 6 of 12). Population *size* does not enter the argument anywhere. What enters is
the depth-range distribution. M1's dense initialisation produces a population that is
spatially uniform with respect to the training views, so the per-frame ranges stay comparable;
M2's importance-weighted subsampling removes near-camera and low-contrast material
*differentially across views*, which moves `m_f` for some frames far more than others. Equal
counts, unequal effect on the distribution — which is exactly what E.20 observes and labels
"discontinuity, not size." §2 supplies the missing *why*.

**Why it is seed-conditioned and bistable** (E.2 — 6 of 12, across all four scenes). M2's
subsampling is stochastic. *Which* frames' ranges move is therefore a draw, so whether the
post-event compromise is satisfiable is a draw. Bistability is what one expects from a
compromise that either remains attainable or does not.

**Why collapse presents as a dead channel rather than a shifted one.** When no single `β` fits
the post-event distribution, the loss can still be reduced by abandoning the attenuation term
on a channel and letting the saturating backscatter term carry the image — `β_bs` large,
`σ(B∞)` absorbing the rest. That is SeaSplat's own degeneracy **D-1, the no-medium solution,
reached through the normalisation rather than by the optimiser finding it directly.** The
observed "backscatter runaway" and the observed channel death are the same event. This unifies
two phenomena the results documents currently treat separately.

---

## 4. A falsifiable prediction, and the instrument that cannot yet test it

§2 is an argument, not a measurement, and the Supervisor's second question applies to it as to
anything else. What would have to be false for it to be wrong?

> **Prediction.** The probability of medium collapse at a simplification event is governed by
> the **change in the cross-frame dispersion** of the depth range `{M_f − m_f}` across that
> event — not by the primitive count, not by the count ratio, and not by the mean depth range.
> Runs whose depth-range distribution merely translates should survive; runs whose distribution
> broadens or fragments should collapse.

This is sharp, it distinguishes §2 from the working version of the hypothesis, and it can be
falsified by data of a kind the campaign already produces.

**It cannot be tested with the data on disk, and the reason is a defect worth naming.** The
diagnostics record `z_min`, `z_max` and `z_range` at every checkpoint — but they are captured
from `depth_image.min()` / `.max()` on the **single training view sampled at that iteration**
`[repo: train.py:349–350, 561–562]`. The logged `z_range` is therefore one draw from the
distribution the hypothesis is about, not a statistic of it.

Two consequences, and the first is a live threat to work already written:

1. **`z_range` is noisy by construction**, and its variation across iterations conflates the
   sampled frame with the population change. Any trend read from that column — including any
   already read from it — carries an uncontrolled term. Nothing in the results documents
   currently rests on such a trend, which should be verified rather than assumed.
2. **The quantity the central hypothesis actually needs has never been measured.** Not once, in
   112 planned runs.

The fix is one pass over the held-out or training views at each checkpoint, recording the
distribution of `(m_f, M_f)` rather than one sample: on the order of 75 renders, a few seconds
against a 50-minute run, and no change to any trained model. It should be added before S5, and
if S4 can be paused cheaply, before S4 completes.

That this gap survived twenty-six methodology documents, a claim ledger, and a reproduction
checklist is itself the finding to take seriously. The instrument was specified as "log `Ẑ_min`
and `Ẑ_max`" (CD-12), implemented exactly as specified, and verified to be present. **The
specification was wrong in a way no amount of checking the implementation against it could
detect** — which is the same class of error as CD-22/CD-23, where every forward value was
correct and the gradient went to the wrong place. The project now has three instances of that
class and should name it as a pattern in its own right.

---

## 5. What the contribution is, stated so a committee can grade it

`04-repositioning.md` adopts Framing A: a controlled factorial study plus composition findings.
That was the right call on the evidence available when it was made. §2 permits a sharper
statement, and the sharper statement is also *narrower*, which is what makes it defensible.

> **A scene-global medium model whose only spatial input is per-frame renormalised depth is
> not identified in absolute terms. Its fitted coefficients are a compromise over the training
> set's depth-range distribution, and therefore a function of the primitive population rather
> than of the medium alone. Efficiency mechanisms that change the population are the instrument
> that makes this visible; the fidelity metrics cannot see it; and the obvious remedy —
> re-identification after the change — cannot work, because there is no prior value to
> return to.**

Four supports, all already measured:

| | Support | Status |
|---|---|---|
| The coupling exists | 12 of 12 A2 runs drop on a simplification boundary; 0 of 12 controls | **Supported** `[n=12 + 12 control]` |
| It is not a size effect | A1 ~230k loses 0 of 10; A2 ~145k loses 6 of 12 | **Supported** `[n=10 vs n=12]` |
| Fidelity metrics cannot detect it | best test PSNR in the campaign, 30.97 vs A0's 30.48, with two attenuation channels dead | **Supported** `[n=1, decisive]` |
| Re-identification does not restore it | 200 steps, 0 of 6 recovered | **Supported** `[n=12]` |

And one falsifiable prediction, §4, currently unmeasurable — which is a healthy position for a
thesis to be in, provided the instrument is added rather than the prediction quietly dropped.

**What this costs.** The title's method claim was already being withdrawn. This goes further:
the thesis's principal contribution is now a **negative characterisation of a published
method's estimator**, with the efficiency factorial serving as the apparatus that produces it.
The student should be clear-eyed that this reads as a less flattering thesis than "we built an
efficient method" and is a considerably more defensible one. A committee cannot argue with the
12-of-12 against 0-of-12; it can argue endlessly about whether an 18× reduction was worth 0.05 dB.

**What it does not license.** Nothing here establishes that the alternative — scene-global
depth normalisation, or fitting against unnormalised depth — works. That is the obvious next
method and it is outside this thesis. Saying "the fix is X" without running X is exactly the
error CD-6 already made once.

---

## 6. Assessment of the writing

The documentation is, in its evidentiary discipline, better than most published work in this
area. Three practices deserve to be kept and named in the thesis as methodology:

- **Sample size attached to every empirical statement** (`[measured n=k]`), so that a reader
  never has to ask the Supervisor's first question.
- **A claim-validity ledger with explicit verdicts**, including *Contradicted* applied to the
  work's own prior headline result.
- **Negative results about the work's own proposals recorded as results** (E.6, E.17), rather
  than omitted. E.17 in particular — reporting a correlation that came out the wrong sign — is
  the single most credibility-earning paragraph in the corpus.

Four defects of clarity, in descending order of how much damage they do.

**W-1 — Eight parallel identifier schemes, with collisions.** `CD-n`, `D-n`, `E-n`, `OQ-n`,
`S-n`, `IC-n`, `M-n`, `A-n`, `R-n`, `G-n`, `P-n` are all in use. Two collide outright:

- **`D-1`** denotes SeaSplat's no-medium degeneracy, *and* a discrepancy in the ledger
  ("D-1. The implemented mechanism was `opacity × scale`"), *and* one of EDGS's own numbered
  degeneracies. `D-2` likewise means both SeaSplat's depth–medium degeneracy and EDGS's
  near-parallel triangulation failure, in documents that cite both.
- **`M-1`** (a baseline well-posedness mechanism) and **`M1`** (the dense-initialisation
  factor) differ by one hyphen and appear in the same tables.

An examiner who mis-resolves one of these reads a sentence backwards. Namespace the schemes —
`SS-D1` for SeaSplat degeneracies, `EDGS-D2` for EDGS's — and rename the baseline mechanisms so
they cannot be confused with the factors. This is mechanical and it is the highest-value
editorial change available.

**W-2 — Number conventions differ between the register and the chapter.** The technical files
write `2 482 200` and `n=12`; the chapter writes "two million four hundred thousand" and
"twelve runs". Both are defensible; using both is not. The chapter's spelled-out convention
becomes actively hard to read at "ninety-six training runs, with a ninth supplementary
configuration and a four-run reference control bringing the campaign to one hundred and
twelve." Adopt digits for all quantities above ten in both, and reserve words for counts under
ten.

**W-3 — Qualification stacking.** Sentences carrying three or more hedges lose the claim
inside them. The remedy is not fewer qualifications but **fewer per sentence**: state the claim
in one sentence and its conditions in the next. Where a finding is strong, the persona's rule
applies — twelve runs and a twelve-run control do not need "may suggest".

**W-4 — Self-reference density.** Several passages are unreadable without four other
documents open. This is appropriate in the technical register and fatal in the chapter, which
must stand alone for an examiner. Every cross-reference in `chapter/` should either be
accompanied by the one-clause summary a reader needs, or removed.

---

## 7. Defence risk register

| | The question | Preparedness | What to do |
|---|---|---|---|
| **R-1** | *"Isn't this just a bug in your integration?"* | **Strong after §2, weak before it.** The restated claim is derivable from SeaSplat's own published components | Lead with the derivation, not the measurement. The 12-of-12 then confirms an argument rather than standing alone |
| **R-2** | *"You propose a fix that does not work. What have you contributed?"* | **Adequate, and improved by §3** | A correctly implemented remedy resting on a false premise, with the premise identified. Do not let this be framed as an untried remedy |
| **R-3** | *"Four scenes."* | **Weak, and irreducible** | Concede immediately. The 12-vs-0 control is a within-corpus contrast, not a generalisation, and should be stated that way before it is challenged |
| **R-4** | *"Your geometric metric doesn't correlate with your medium metric."* | **Strong** — already reported as E.17 | The pre-emption is the answer. It detects failure modes directly and is never used as a proxy; this is in `chapter/06` §3.7.5 |
| **R-5** | *"Why should we believe A0 is SeaSplat?"* | **Partial** — n=3, Curasao only | Do not state it for all scenes. The claim ledger already restricts it; ensure the chapter does too |
| **R-6** | *"You never measured the quantity your hypothesis is about."* | **Currently indefensible** — see §4 | Add the instrument. This is the one row on this table that can still be converted from a weakness into a strength before submission |

---

## 8. Actions, in order

1. ~~**Add the cross-frame depth-range instrument** (§4).~~ ✅ **DONE — CD-27**
   `[repo: utils/depth_stats.py, tools/verify_depth_stats.py, 13 checks]`. Sweeps every
   training view at each simplification boundary and at `zsweep_interval`; `zr_cv` is the
   predicted driver, and `medium_collapse.py` reports the pre/post dispersion ratio beside
   the collapse verdict. Two invariants are tested: one implementation shared with the
   optimiser, and no randomness consumed. **Completed runs cannot be retrofitted** — the
   distribution was never stored — so the prediction is *untested* rather than unsupported,
   and applies from S5 onward. Extracting the shared path immediately caught a real
   divergence: the degenerate `min == max` branch divides by the maximum rather than leaving
   the frame alone, which a second implementation would have got wrong.
2. **Restate the central claim** per §5 in `04-repositioning.md` and the abstract. No new runs
   required; this is the highest-value change in the list and costs only writing.
3. **Close OQ-10 as *misconceived*** with the §3 derivation, rather than leaving it open
   between two readings.
4. **Namespace the identifier schemes** (W-1). Mechanical, and it removes a class of examiner
   misreading.
5. **Run S6 / A0D.** Mechanism D remains the only route back to an engineering contribution,
   and E.4's figure is measured against a baseline now known to be defective. Until it runs,
   the thesis has no positive result of its own.
6. **Verify that nothing already written rests on a trend in the single-frame `z_range`
   column** (§4). Likely clean; must be checked rather than assumed.

Items 2, 3 and 4 require no compute and should be done first.
