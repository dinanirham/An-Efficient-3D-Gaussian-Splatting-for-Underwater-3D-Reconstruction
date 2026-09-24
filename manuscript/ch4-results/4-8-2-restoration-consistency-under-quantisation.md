---
section: "4.8.2"
title: "Restoration Consistency Under Quantisation"
chapter: 4
action: Add
evidence: ["FINDINGS §10", "j_consistency.json"]
figures: ["figure-4-14-attribute-states", "figure-4-19-restoration-vs-drift"]
tables: []
citations: []
status: refined
word_count: 641
---

# 4.8.2 Restoration Consistency Under Quantisation

Section 4.8.1 shows that the fidelity metrics cannot distinguish a run whose
attenuation coefficient is negative from one whose is not. This subsection
shows the same metrics are indifferent to a change in the restored image of
roughly twenty-three decibels. The two findings are independent — different
mechanisms, different instruments, different runs — and they establish the same
limitation from opposite directions.

The measurement is reported in full in Section 4.5.7, where it belongs as a
result about attribute-level quantisation. What matters here is what it
establishes about the instruments. A single trained model holds its quantised
attributes in two states, continuous and codebook, and can be rendered from
either. Rendered from the two states, sixteen models produce composed images
agreeing to within 0.6 to 3.1 decibels — a median of 1.4 — and restored images
differing by 17 to 27 decibels. **The quantity every fidelity number in this
chapter measures moves by about one decibel while the estimator's
distinguishing output moves by twenty-three.**

> **[FIGURE 4.14]** `figures/chapter4/figure-4-14-attribute-states.pdf`
> *One model, both attribute states, restored image.* The same trained model
> rendered from its continuous parameters and from its codebook, four scenes.
> Nothing else differs, so the difference is quantisation rather than
> divergence between separately trained runs.
> **Status:** built

The reason is the same structural fact that Section 4.7.6 identifies for
collapse, arrived at independently. The training objective scores a product of
a restored image and an attenuation factor no greater than one. Wherever that
factor is small, a change in the restored image reaches the loss attenuated,
and the loss has correspondingly little to say about it. In Section 4.8.1 the
attenuation factor itself was driven to a meaningless value and the restoration
absorbed the difference; here the restoration is perturbed directly and the
attenuation factor hides it. The product is constrained; neither factor
separately is.

That a competing explanation was registered, tested and refuted is reported in
Section 4.5.7 and is not repeated. The relevant point for this section is that
the refutation strengthens the instrument claim: the restored-image gap is not
an artefact of comparing a model against an unusable latent, because the
continuous state renders the composed image within 1.4 decibels of the codebook
state and is therefore a working model. Two working models of the same scene,
trained identically, disagree about the water by twenty-three decibels and
agree about the image by one.

Three limits carry over from Section 4.5.7 and bound what this contributes to
Section 4.8.3. The measurement is of **consistency, not accuracy**: it
establishes that the two restorations are far apart and cannot say which is
nearer the true medium-free image, because that image has no ground truth in
this corpus. It rests on **one repeat per configuration and scene**, so it
carries no dispersion and is not resolved against the thresholds of Section
4.1.3. And the attribution of the disagreement to the far field is **inferred
from the image formation model rather than measured**.

Those limits are why this subsection supports Section 4.8.3 rather than
carrying it. The strata comparison of Section 4.8.1 rests on twelve comparisons
at three repeats and is the load-bearing evidence; this is a second, weaker
line arriving at the same conclusion by a different route. Two independent
routes to one conclusion is worth more than either alone, provided the weaker
is not asked to carry the weight of the stronger.

---

## Review log

**Domain Researcher** — The draft re-reported the sixteen-run table already
given in Section 4.5.7, which duplicates without adding. → *applied*: the
measurement is cited to its home section and this subsection develops only what
it establishes about the instruments. Second finding: the shared structural
cause with Section 4.7.6 was not drawn, and it is the reason the two findings
are not coincidental. → *applied*: the product is constrained, neither factor
separately is.

**Supervisor** — The draft gave the two findings equal weight, which invites a
referee to attack the weaker one and treat the section as refuted.
→ *applied*: closing paragraph states plainly which is load-bearing and which
is corroborating. Devil's advocate: does n = 1 per scene make this worth
including at all? Yes, as a second route to a conclusion established elsewhere
at three repeats — and the paragraph says exactly that rather than implying
more.

**Journal Reviewer** — The refuted drift prediction was summarised here as well
as in Section 4.5.7, in slightly different terms. → *applied*: referred to its
home section, with only the consequence for the instrument claim retained.
Second: "roughly twenty-three decibels" was used where the table gives a range.
→ *applied*: the 17 to 27 range is stated before any summary figure.
