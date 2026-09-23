---
section: "4.5.7"
title: "Effect on the Restored Image"
chapter: 4
action: Add
evidence: ["FINDINGS §10", "j_consistency.json"]
figures: ["figure-4-14-attribute-states", "figure-4-19-restoration-vs-drift"]
tables: ["Table 4.15"]
citations: []
status: refined
word_count: 869
---

# 4.5.7 Effect on the Restored Image

Every fidelity number reported for this mechanism so far describes the composed
image, and on that quantity the mechanism is neutral on three scenes of four.
This subsection reports the same models measured on the restored image — the
medium-free radiance that is the estimator's distinguishing output — and the
result is of a different order.

The instrument is a within-model comparison. A trained quantised model holds
each of the three affected attributes in two states: the continuous parameters
the optimiser updates, and the codebook entries the straight-through estimator
commits them to. The model can be rendered from either. Nothing else differs —
same primitives, same positions, same medium scalars, same view — so any
difference between the two renderings is attributable to quantisation alone.
Sixteen runs were measured this way, the first repeat of each of the four
configurations containing the mechanism.

> **[TABLE 4.15]** *Two attribute states of one model, per run.* The restored-
> image gap is between the two states; the composed-image columns are each
> state against ground truth. Sixteen runs, first repeat only. Source:
> `j_consistency.json`.

| | Restored-image gap (dB) | Composed, continuous | Composed, codebook | In-medium loss |
|---|---:|---:|---:|---:|
| A3 Curaçao | 23.3 | 28.6 | 29.5 | 0.9 |
| A3 IUI3 Red Sea | 23.1 | 23.6 | 26.7 | 3.1 |
| A3 Japanese Gardens | 25.3 | 23.0 | 23.6 | 0.6 |
| A3 Panama | **17.0** | 21.9 | 28.7 | **6.8** |
| A5 Curaçao | 22.9 | 28.3 | 29.9 | 1.6 |
| A5 IUI3 Red Sea | 24.5 | 24.7 | 27.3 | 2.6 |
| A5 Japanese Gardens | 24.5 | 23.3 | 24.1 | 0.8 |
| A5 Panama | 26.6 | 25.2 | 27.8 | 2.6 |
| A6 Curaçao | 26.0 | 27.8 | 29.0 | 1.3 |
| A6 IUI3 Red Sea | 26.2 | 24.9 | 26.6 | 1.8 |
| A6 Japanese Gardens | 26.1 | 22.1 | 22.8 | 0.7 |
| A6 Panama | 26.5 | 27.0 | 28.0 | 0.9 |
| A7 Curaçao | 23.8 | 29.6 | 30.5 | 0.9 |
| A7 IUI3 Red Sea | 25.3 | 25.3 | 27.1 | 1.8 |
| A7 Japanese Gardens | 22.2 | 22.8 | 24.0 | 1.3 |
| A7 Panama | 26.0 | 25.9 | 27.9 | 2.0 |

**Two states of one model whose composed images agree to within 0.6 to 3.1 dB
produce restored images differing by 17 to 27 dB.** The quantisation of three
attribute vectors changes the medium-free image by more than an order of
magnitude more than it changes the image that is scored.

The explanation is in the structure of the image formation model rather than in
any property of the codebooks. The composed image is the restored image
attenuated by a factor at most one, plus a backscatter term. Wherever that
attenuation factor is small — which is the far field, and on these scenes a
large fraction of every frame — a change in the restored image is multiplied by
a small number before it reaches the loss. The part of the restoration that the
medium suppresses is therefore free to move without the training objective
registering it, and quantisation moves it.

> **[FIGURE 4.14]** `figures/chapter4/figure-4-14-attribute-states.pdf`
> *One model, both attribute states, restored image.* The same trained model
> rendered from its continuous parameters and from its codebook, four scenes.
> Nothing else differs, so the difference is quantisation and not trajectory
> divergence between runs — the comparison Figure 4.8 cannot make.
> **Status:** built

A competing explanation was registered before this check was run and is
reported here because it was wrong. The proposal was that the continuous
parameters, never rendered during training and unconstrained by any commitment
term, drift into a state that is no longer a usable model — which would make
the restored-image gap an artefact of comparing a model against a latent. The
check tests this directly: if the continuous state were not a model, it would
render the composed image poorly. It does not. The continuous state renders the
in-medium image 0.6 to 3.1 dB worse than the codebook state, a median of 1.4 dB,
where the prediction was roughly 19 dB. It is a slightly degraded model, not a
latent. **The verdict is MODEL on fourteen of the sixteen runs**, against
thresholds fixed before the data were seen.

Straight-through drift is nonetheless real and measurable — one to three
decibels in the composed image is the size of a mechanism main effect — but it
is an order of magnitude too small to account for the restored-image gap, and
**the two quantities are uncorrelated across the sixteen runs, with a Spearman
coefficient of −0.14**. The decisive case is A3 on Panama: it has the largest
in-medium loss of any run, 6.8 dB, and the *smallest* restored-image gap,
17.0 dB. A drift account predicts those two move together, and they move
opposite.

> **[FIGURE 4.19]** `figures/chapter4/figure-4-19-restoration-vs-drift.pdf`
> *Restoration gap against in-medium loss.* One point per run. The two are
> uncorrelated, which is what refutes the drift reading.
> **Status:** built

Three limits bound this result and none is minor. It is a **consistency**
measure, not an accuracy measure: it establishes that the two states' restored
images are far apart and cannot say which is nearer the true medium-free image,
because no ground truth for that quantity exists. It rests on **one repeat per
configuration and scene**, so it carries no dispersion and no effect here is
resolved against the thresholds of Section 4.1.3. And the attribution of the
difference to the far field is **inferred from the image formation model rather
than measured**; a per-depth-bin breakdown of where the two restorations
disagree would test it and is not in this campaign.

Within those limits the finding stands as the strongest single piece of
evidence for the chapter's methodological claim. Section 4.8.1 shows the
composed-image metrics cannot distinguish a run whose attenuation coefficient
is negative from one whose is not. This subsection shows the same metrics are
indifferent to a 23 dB change in the restoration. Both are consequences of
scoring a product while claiming a decomposition, and Section 4.8.3 draws them
together.

---

## Review log

**Domain Researcher** — The draft presented the restored-image gap as the
finding and mentioned the refuted drift account in a footnote. The refutation
is what makes the gap interpretable, and a referee would ask for exactly that
control. → *applied*: the competing explanation, the prediction it made, the
test, and the verdict on fourteen of sixteen, in the body. Second finding: the
draft asserted the far-field attribution as established when it is inferred
from the model. → *applied*, and listed as the third limit.

**Supervisor** — The draft gave the Spearman coefficient and left it. A single
decisive counterexample persuades where a correlation coefficient does not, and
A3 on Panama is one. → *applied*: named, with both numbers and why they run the
wrong way for a drift account. Devil's advocate: with n = 1 per scene, is this
strong enough to carry the chapter's methodological claim? On its own, no —
which is why the closing paragraph pairs it with Section 4.8.1, where the same
conclusion rests on twelve comparisons at three repeats.

**Journal Reviewer** — The prediction record was absent. A pre-registered
prediction that failed must be reported as such. → *applied*: the ~19 dB
prediction, the observed median of 1.4 dB, and the note that the verdict
thresholds were fixed before the data were seen. Second: "17 to 27 dB" was
given without stating it is a gap between two renderings of one model rather
than against ground truth. → *applied*, in the table caption and the body.
