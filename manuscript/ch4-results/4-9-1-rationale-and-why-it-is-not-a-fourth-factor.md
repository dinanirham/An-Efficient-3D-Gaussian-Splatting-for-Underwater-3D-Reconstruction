---
section: "4.9.1"
title: "Rationale and Why It Is Not a Fourth Factor"
chapter: 4
action: Add
evidence: ["FINDINGS §6"]
figures: []
tables: []
citations: []
status: refined
word_count: 483
---

# 4.9.1 Rationale and Why It Is Not a Fourth Factor

The campaign contains a tenth configuration that stands outside the factorial.
It detaches the alpha-loss gradient from density control, so the adaptive
densification procedure no longer receives the signal that drives it to clone
and split primitives in response to opacity error. The population still grows,
but it grows less, and it grows continuously rather than being cut.

The reason it is not entered as a fourth factor is structural rather than a
matter of experimental economy. **Deterministic initialisation replaces density
control entirely**: when the initial cloud is fixed and cloning and splitting
are disabled, there is no densification signal for this mechanism to detach. It
is provably inert in any configuration containing initialisation, which is four
of the eight cells of the existing design. A 2⁴ factorial would therefore
contain eight cells in which the fourth factor does nothing, and the contrasts
estimating its effects would be averaging over those eight null cells and eight
live ones. The estimate would be halved in magnitude and uninterpretable as a
mechanism effect.

It is therefore measured as a supplementary contrast against the configuration
with no mechanism active, and **it is never differenced with the factorial**.
No interaction term in Section 4.6 contains it, no main effect is adjusted for
it, and no operating-point comparison treats it as commensurable with the three
factors. It appears in Section 4.6.6's fronts because it is a trained
configuration a practitioner could choose, not because the design estimates its
composition with anything.

A prediction about its behaviour was registered before it ran, and Section 4.9.2
reports the outcome against that prediction rather than descriptively. The
prediction was specific and had two halves, which is what makes it informative:
that the count effect would resolve, and that the pixel-metric effect would
not.

One further reason for reporting it at all is worth stating. This mechanism was
measured in an earlier campaign against a baseline later shown to be defective,
and the figure that campaign produced — a specific small pixel-metric loss —
was carried into the thesis as a point estimate. This campaign measures it
against a baseline shown equivalent to the published reference (Section 4.2.1),
at three repeats, and Section 4.9.2 retires the earlier figure.

---

## Review log

**Domain Researcher** — The draft justified excluding the mechanism from the
factorial on grounds of cost, which is not the reason and would invite a
referee to ask why a 2⁴ design was not run. → *applied*: the inertness argument,
with the arithmetic consequence that half the cells would be null and the
estimate correspondingly meaningless. Second finding: the draft did not say
what the mechanism does to the population, only what it detaches.
→ *applied*: grows less and continuously, which is what Section 4.9.3 needs.

**Supervisor** — The draft read as housekeeping. Its real content is that this
is a supplementary contrast with a registered prediction and a retired prior
figure, and both are worth the reader's attention. → *applied*: the prediction
named as two-part, and the retirement of the earlier estimate given its own
paragraph. Second: "never differenced with the factorial" was asserted without
saying what that rules out. → *applied*: interactions, adjusted main effects
and commensurable comparisons, each named.

**Journal Reviewer** — The mechanism's presence in Section 4.6.6's fronts
appeared to contradict the claim that it is never combined with the factorial.
→ *applied*: it appears as a choosable configuration, not as an estimated
composition, and the distinction is stated.
