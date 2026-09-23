---
section: "4.5.3"
title: "Effect on the Medium Model"
chapter: 4
action: Add
evidence: ["FINDINGS §5a", "FINDINGS §2b", "medium_collapse.json"]
figures: []
tables: []
citations: []
status: refined
word_count: 486
---

# 4.5.3 Effect on the Medium Model

Attribute-level quantisation lost no attenuation channel in any of its twelve
runs. On the collapse criterion that separates configurations in Section 4.7,
it behaves as the reference, the unmodified configuration and deterministic
initialisation do.

The fitted medium parameters are likewise undisturbed. The spectral ordering
reported for the baseline in Section 4.2.4 — physical on three scenes, inverted
on IUI3 Red Sea — survives this mechanism unchanged in direction on every
scene. The mechanism quantises per-primitive attributes and does not touch the
nine global medium scalars, which are stored and optimised separately, so an
absence of effect on them is the expected result rather than a surprising one.

Two observations qualify this apparently clean outcome, and both point forward
rather than being resolvable here.

The first is that quantisation appears in the two configurations that *do*
collapse. Pairing this mechanism with spatial reorganisation gives four
collapsed runs in twelve, against five in twelve for spatial reorganisation
alone (Section 4.7.1). The rate is not raised by adding quantisation, and on
the evidence available it is not lowered either; what the pairing shows is that
this mechanism neither causes collapse nor prevents it. The protection that
does exist belongs to deterministic initialisation and is established in
Section 4.7.

The second is more consequential and is the subject of Section 4.5.7. That this
mechanism leaves the *medium parameters* intact does not mean it leaves the
*decomposition* intact. The medium term and the restored image are two halves
of one product, and quantising the per-primitive attributes changes the
restored image substantially — by 17 to 27 dB between a single model's two
attribute states — while changing the composed image by one to three decibels.
A subsection reporting that the medium scalars did not move would, read alone,
give a reader entirely the wrong impression of this mechanism's effect on the
estimator's physical output.

**This subsection therefore reports an absence on one axis and defers to
Section 4.5.7 for the axis on which this mechanism does act.** Collapse
incidence is the right instrument for spatial reorganisation and the wrong one
for quantisation; the third evaluation axis contains more than one measurement,
and this is the mechanism that demonstrates why.

---

## Review log

**Domain Researcher** — The draft reported 0 of 12 and stopped, which would
leave a reader believing quantisation is benign for the physical model — a
conclusion Section 4.5.7 contradicts. → *applied*: second observation added,
with the magnitudes, and the subsection now closes by naming collapse as the
wrong instrument for this mechanism. Second finding: the draft did not say why
an absence of effect on the medium scalars is expected. → *applied*: the
scalars are global and stored separately from the quantised attributes.

**Supervisor** — Three subsections have now reported collapse incidence and
this is the first where the number means something different. Saying that
explicitly is worth more than the number itself. → *applied*: the closing
statement that the third axis contains more than one measurement, and that this
mechanism is what demonstrates it. Devil's advocate: does the A6 pairing show
quantisation reduces collapse, four in twelve against five? Not at these
counts; the draft's "does not raise the rate" is stated symmetrically so
neither direction is claimed.

**Journal Reviewer** — The forward reference to Section 4.5.7 originally gave
no magnitude, so a reader had no way to judge whether the deferral mattered.
→ *applied*: 17 to 27 dB against one to three, stated here.
