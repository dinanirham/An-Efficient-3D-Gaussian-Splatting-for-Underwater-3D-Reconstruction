---
section: "4.5.5"
title: "Discussion"
chapter: 4
action: Refine
evidence: ["FINDINGS §2", "FINDINGS §10", "FINDINGS §12"]
figures: []
tables: []
citations: ["Navaneet et al., 2024"]
status: refined
word_count: 727
---

# 4.5.5 Discussion

Attribute-level quantisation is the mechanism whose cost is hardest to see and
easiest to understate. On the two axes this literature conventionally reports
it is close to free; on the estimator's distinguishing output it is the largest
intervention in the campaign.

**What it buys.** A factor of 2.72 in bytes per primitive, identical on every
scene and every run, at no cost in primitive count and no cost in frame rate.
Total stored size falls to between 0.31 and 0.44 of the unmodified
configuration. The gain is structural rather than empirical — it follows from
replacing three of fourteen per-primitive floating-point values with codebook
indices — which is why it carries no uncertainty and why a prediction
registered before the instrument existed was able to state it in advance.

**What it costs on the conventional axes.** Nothing that resolves on three of
four scenes, on either metric. On IUI3 Red Sea it costs 1.21 dB and 0.028 in
learned perceptual similarity, both resolved, and this is the only place in the
chapter where the two fidelity metrics agree with each other about a mechanism.

**What it costs on the third axis.** The medium scalars are untouched and no
run loses an attenuation channel (Section 4.5.3). But two attribute states of a
single model, whose composed images agree to within 1.4 dB at the median,
produce restored images 17 to 27 dB apart (Section 4.5.7). The quantity the
mechanism perturbs most is the quantity the estimator exists to produce, and no
metric reported in Sections 4.5.1 or 4.5.2 detects it.

The account for this is structural and is worth stating as the mechanism-level
claim of the section. The training objective scores a product: a restored image
multiplied by an attenuation factor no greater than one, plus a backscatter
term. Wherever the attenuation factor is small, a change in the restored image
is attenuated before it reaches the loss, and the optimiser has no gradient with
which to prevent it. Quantisation perturbs the per-primitive attributes that
determine the restored image; the loss sees a fraction of that perturbation;
the restoration moves freely in the far field. This is not a defect of the
codebook method (Navaneet et al., 2024), which does what it was designed to do.
It is a consequence of composing a lossy attribute compression with an
estimator whose output is a decomposition, and it would not arise in the
terrestrial setting the compression method was validated in, where there is no
medium term to suppress the residual.

Three claims the evidence does not support.

It does not support the claim that quantisation is nearly free. That statement
is true of the composed image and false of the restoration, and a thesis whose
subject is a physically grounded estimator cannot report the first without the
second.

It does not support any statement about which attribute state is *correct*.
Section 4.5.7 measures consistency between two states, not accuracy against a
ground truth that does not exist for this quantity. The finding is that they
disagree, not that the codebook state is wrong.

It does not support a compression ratio against the published method. The
reference records no stored size, so the 2.72-fold figure is against the
unmodified configuration (Section 4.5.2), which is equivalent to the reference
within a ±30 % count margin rather than identical to it.

For a practitioner the recommendation separates cleanly by use. If the output
is a rendered image, this mechanism is the best value in the campaign: a
2.72-fold storage reduction for no measurable cost on three scenes of four, no
frame-rate penalty, and no interaction with the population that the other two
mechanisms reduce. If the output is the decomposition — the restored image, or
anything computed from it — then the mechanism changes that output by an amount
this campaign can measure but cannot validate, and the honest advice is that it
should not be adopted for that purpose without a restoration ground truth to
check it against. Section 5.4 carries the acquisition of such a reference as
the campaign's most valuable missing instrument.

---

## Review log

**Domain Researcher** — The draft blamed the codebook method for the
restoration effect. It is not a defect of that method; it is a consequence of
composing lossy attribute compression with a decomposition-producing estimator,
and it would not appear in the terrestrial setting the method was validated in.
→ *applied*, and this is now the section's mechanism-level claim. Second
finding: the structural nature of the compression ratio was stated in Section
4.5.2 but not carried into the discussion, where it explains why the figure has
no uncertainty. → *applied*.

**Supervisor** — The draft's opening called the mechanism "a good trade", which
pre-empts the section's own argument and is the reading Section 4.5.7 exists to
complicate. → *applied*: opens on the cost being hard to see and easy to
understate. Devil's advocate: is it fair to recommend against a mechanism on
the strength of n = 1 per scene? The recommendation is not against adoption; it
is against adoption for one purpose without an instrument the campaign lacks,
which is what the evidence supports.

**Journal Reviewer** — The compression claim was stated against "the baseline"
without the anchor exception being restated, in a section a reader may consult
alone. → *applied*: third unsupported claim names it. Second: the practitioner
recommendation gave no destination for the missing instrument.
→ *applied*: Section 5.4.
