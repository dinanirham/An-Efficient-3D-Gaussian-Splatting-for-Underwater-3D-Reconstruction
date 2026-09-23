---
section: "4.3.5"
title: "Discussion"
chapter: 4
action: Refine
evidence: ["FINDINGS §2", "FINDINGS §9", "FINDINGS §12"]
figures: []
tables: []
citations: ["Kerbl et al., 2023", "Kotovenko et al., 2026"]
status: refined
word_count: 704
---

# 4.3.5 Discussion

The preceding subsections report what deterministic initialisation does. This
one states what accounts for it, at the level of confidence the evidence
supports.

**The mechanism works because the baseline's population is largely
unnecessary, not because a correspondence cloud is a better starting point.**
This is the account the campaign's own evidence favours. Adaptive densification
clones and splits primitives on a gradient criterion and provides no procedure
for removing those that end up contributing nothing (Kerbl et al., 2023), and
Section 4.2.6 measured the result: 57 to 77 per cent of the reference's
primitives never clear the visibility threshold. Replacing that procedure with
a fixed cloud of approximately 200 000 primitives removes most of that
population and costs no radiometric fidelity on any scene in this corpus. The
reduction is large against the total precisely because the total contained a
great deal that was inert; against the visible population it is four to five
times, which is a real but much more modest claim.

That framing also explains the mechanism's cost. Fine structure is where the
densification procedure would have added primitives, and a fixed population
cannot. The result is a representation that agrees radiometrically while
carrying less high-frequency detail, which peak signal-to-noise ratio does not
penalise and learned perceptual similarity does. The effect is small on three
scenes and large on one, and the scene where it is large is the scene with the
fewest and worst-conditioned training views — the condition under which a
correspondence-derived cloud is sparsest exactly where geometry is least
constrained. That association is stated as an association. The campaign varied
neither view count nor camera baseline, so it cannot test it.

Three claims that the evidence does **not** support should be named, because
each is available to a reader and each would be wrong.

It does not support the claim that this mechanism improves reconstruction
quality. Peak signal-to-noise ratio is higher on all four scenes against the
reference, but resolves on only one, and perceptual similarity is worse on two.
The honest summary is fidelity-neutral with a scene-dependent perceptual cost.

It does not support the claim that the mechanism makes training cheaper in
proportion to the population it removes. Training time falls by 11 to 26 per
cent against a population reduction of nine to eighteen times, because the
optimizer-step count is fixed by the schedule and identical across
configurations (Section 4.1.1). A practitioner choosing this mechanism for
training cost should expect the smaller figure.

It does not support the claim that the mechanism protects the medium model.
It loses no attenuation channel, but neither does the reference, so on this
corpus there is nothing for it to protect against in isolation (Section 4.3.3).
The protection result of Section 4.7 concerns this mechanism in combination
with spatial reorganisation and is a property of the pair.

What a practitioner can take from this section is therefore conditional and
specific. On a scene with adequate view coverage, deterministic initialisation
gives an order-of-magnitude smaller representation, a 1.3 to 2.3 times faster
render, and 11 to 26 per cent faster training, at no measurable cost in
radiometric fidelity and a perceptual cost too small to resolve. On a scene
whose views are few and poorly conditioned, the same mechanism costs 0.059 in
learned perceptual similarity, which is three times the equivalence margin this
thesis pre-registered for that metric and is visible in the rendered crops.
Whether view coverage is the operative variable is untested; that the cost
appeared on the scene with the weakest coverage is what was observed.

One methodological point closes the section. The mechanism as measured here is
an implementation rather than a published description: the released
implementation of the source method predates its paper by approximately ten
months and contains behaviour the paper does not describe (Kotovenko et al.,
2026). This thesis measures what the implementation does, and Section 3.9
records the differences. A result reported here should be read as a result
about that implementation composed into this estimator, not as a replication of
a published claim.

---

## Review log

**Domain Researcher** — The draft's account was that a correspondence cloud
gives better geometric coverage than structure-from-motion points. The campaign
has no evidence for that and its own measurements point elsewhere: the
reduction is large because the baseline population is largely inert.
→ *applied*, and the account now rests on the visible-fraction measurement.
Second finding: the implementation-versus-paper distinction belongs in the
mechanism's discussion, not only in Chapter III, because it bounds what the
result replicates. → *applied*: closing paragraph.

**Supervisor** — The draft was a summary, not a discussion: it restated the
numbers with connectives. A discussion has to say what accounts for them and
what would be wrong to conclude. → *applied*: one account, stated as the one
the evidence favours, then three named claims the evidence does not support.
Devil's advocate: is "the baseline's population is largely unnecessary" too
strong, given the mechanism does cost perceptual quality? It is the right
strength — "largely", not "wholly", and the perceptual cost is exactly where
the necessary part was.

**Journal Reviewer** — The perceptual cost on IUI3 Red Sea was reported in raw
units with no interpretive scale. → *applied*: three times the pre-registered
equivalence margin, which is the scale this thesis has already defined. Second:
the practitioner summary originally gave ranges without saying they are
conditional on scene. → *applied*: split into the two cases the evidence
distinguishes, with the untested variable named as untested.
