---
section: "4.6.1"
title: "Estimating Interactions in This Design"
chapter: 4
action: Add
evidence: ["FINDINGS §0", "FINDINGS §3", "analysis_unweighted.json"]
figures: ["figure-4-01-resolution", "figure-4-16-interaction-plots"]
tables: []
citations: []
status: refined
word_count: 741
---

# 4.6.1 Estimating Interactions in This Design

Sections 4.3 to 4.5 report each mechanism against the reference with the other
two disabled. This section asks whether their effects combine, which is the
question the factorial design exists to answer and the one a reader cannot
resolve from three separate main effects.

An interaction is estimated as a difference of differences. For two mechanisms
the two-way term is the effect of the pair minus the effects of each alone,
taken from the corner at which neither is active:

> M1 × M2  =  A4 − A1 − A2 + A0

and the three-way term extends this over all eight cells of the design. These
contrasts are constructed from the configuration in which no mechanism is
active, not from the reference implementation, and that is deliberate: the
arithmetic requires the corner of the design cube, and the reference is not a
corner of it. As Section 4.1.2 records, the choice of anchor does not change
the value of any contrast — the reference cancels from a difference of
differences — so these terms are identical whether the underlying quantities
are expressed against A0 or against SS.

Two metrics are combined differently, and the difference is not cosmetic.
Perceptual similarity is treated additively, so its interaction term is in the
metric's own units. Primitive count is treated as log-multiplicative, so its
term is a ratio: mechanisms that each reduce count by a factor would, if they
composed independently, multiply their factors, and the interaction measures
departure from that product. A count interaction of ×1.0 means the reductions
multiply as predicted; ×10 means the pair removes ten times less than
independent composition would give.

**Interactions are adjudicated on perceptual similarity and primitive count.
Peak signal-to-noise ratio interactions are `UNDETERMINED` by construction and
no claim in this thesis rests on them.** This is a property of the design
rather than a finding about the mechanisms, and the arithmetic is worth setting
out because the conclusion is unusual. The standard error of a two-way contrast
is approximately twice that of a single cell mean, and of a three-way contrast
approximately 2√2 times. Applying the two-standard-error rule of Section 4.1.2
to the observed dispersion gives a smallest resolvable PSNR interaction of 0.51
to 1.61 dB depending on scene. The largest PSNR main effect the campaign
measured is 0.80 dB. An interaction cannot be resolved when the threshold for
resolving it exceeds the largest effect the mechanisms produce, whatever the
interaction's true magnitude.

> **[FIGURE 4.1]** `figures/chapter4/figure-4-01-resolution.pdf`
> *Resolvable effect size against observed effect size, per scene.* The
> two-standard-error threshold for main, two-way and three-way contrasts, with
> the observed main effects overlaid. The gap between the PSNR interaction
> threshold and the largest observed PSNR main effect is what `UNDETERMINED`
> means here.
> **Status:** built

The PSNR terms are tabulated in the subsections that follow and marked
accordingly. Several of them exceed two standard errors against the campaign's
tighter noise floor — M1 × M2 on Panama at −0.95 dB, M1 × M3 on IUI3 Red Sea at
+0.91 dB and on Panama at −1.30 dB, M2 × M3 on Curaçao at −1.30 dB. They are
not interpreted, and the reason is visible in the pattern rather than only in
the threshold: **the sign flips from scene to scene within every pair.** A
mechanism-driven interaction would be expected to hold its direction across a
corpus; terms that change sign scene to scene at the edge of resolvability are
the signature of noise at the limit. Reporting them without interpreting them
is the honest treatment, and discarding them silently would not be.

> **[FIGURE 4.16]** `figures/chapter4/figure-4-16-interaction-plots.pdf`
> *Interaction plots on perceptual similarity.* One panel per mechanism pair,
> one line pair per scene. Parallel lines would indicate additive composition.
> **Status:** built

One consequence of the resolution arithmetic should be stated before the
results rather than discovered among them. The three-way term is resolved least
often of all, because its standard error is the largest in the design. Its
appearance as `UNRESOLVED` in Section 4.6.5 is the expected outcome of the
design rather than evidence that three-way composition is additive, and that
section says so rather than reporting an absence as a result.

---

## Review log

**Domain Researcher** — The draft did not state why the contrasts are built
from A0 when the chapter is anchored on SS, which a reader who has absorbed
Section 4.1.2 will immediately query. → *applied*: the corner-of-the-cube
reason, with the note that the anchor cancels so the values are unchanged.
Second finding: the log-multiplicative treatment of count was named but not
explained, leaving the ×8–14 figures of Section 4.6.2 uninterpretable.
→ *applied*: what ×1.0 and ×10 each mean.

**Supervisor** — The draft asserted `UNDETERMINED` and moved on. It is the most
counter-intuitive claim in the chapter — a factorial study declining to report
its interactions on the headline metric — and it has to be argued, not
declared. → *applied*: the arithmetic in full, the threshold against the
largest main effect, and the sign-flip pattern as independent corroboration.
Devil's advocate: is declining to interpret terms that clear 2 SE a convenient
way to avoid inconvenient results? The defence is that the rule was
pre-registered, applies to terms of both signs, and the terms are tabulated
rather than suppressed.

**Journal Reviewer** — The three-way term's poor resolution was not flagged in
advance, so Section 4.6.5 would read as a null result. → *applied*: closing
paragraph. Second: the interaction equation was given in prose only.
→ *applied*: displayed, with the three-way described.
