---
section: "4.4.5"
title: "Discussion"
chapter: 4
action: Refine
evidence: ["FINDINGS §2", "FINDINGS §5a", "FINDINGS §9"]
figures: []
tables: []
citations: ["Fang & Wang, 2024"]
status: refined
word_count: 741
---

# 4.4.5 Discussion

Spatial reorganisation is the campaign's most effective efficiency mechanism
and its only one that damages the physical model. Both statements rest on the
same evidence and neither qualifies the other away.

**What it buys.** Fourteen to twenty-nine times fewer primitives against the
published reference, resolved on every scene; a render rate between 1.84 and
3.54 times higher, resolved on every scene; and no detectable change in
radiometric fidelity anywhere in the corpus. Measured on the two axes this
literature conventionally reports, it is an unambiguous success, and larger
than the corresponding result for deterministic initialisation on both.

**What it costs on those same axes.** Learned perceptual similarity is worse on
every scene at 8 to 36 standard errors, by between 0.033 and 0.082, where the
pre-registered equivalence margin is 0.020. The loss is high-frequency texture
(Section 4.4.4), which follows from an importance criterion that retains
primitives by their contribution to the rendered image and therefore
preferentially retains large ones (Fang & Wang, 2024). This cost is not
scene-conditional, unlike deterministic initialisation's: there is no scene on
which pruning to this budget is perceptually free.

**What it costs on the third axis.** Five of twelve runs lost an attenuation
channel, against none in twenty-four for the reference and the unmodified
configuration. This is the mechanism that makes the medium model fail, and
Section 4.7 is devoted to what can and cannot be said about why.

The three findings do not resolve into a single verdict, and this section does
not manufacture one. They resolve into a conditional that depends on what the
reconstruction is for. If the output is a rendered image, the mechanism costs
perceptual quality and nothing else, and 14 to 29 times fewer primitives is
likely to be worth 0.033 to 0.082 of learned perceptual similarity. If the
output is the decomposition — the medium-free image, the attenuation
coefficients, any quantity derived from the water column — then in roughly two
runs in five the output is physically meaningless, and no amount of storage
saving compensates. A physically grounded underwater estimator is chosen
precisely when the second case applies. That is why this mechanism's result is
reported as a coupling rather than as a trade-off between quality and size.

Three things the evidence does not support should be named.

It does not support the claim that the mechanism improves radiometric fidelity.
Against the unmodified configuration it resolves positive on two scenes, and a
reader seeing only those numbers could conclude as much; against the published
reference it resolves on none (Section 4.4.1). The defensible statement is that
it changes peak signal-to-noise ratio undetectably.

It does not support the claim that the mechanism speeds rendering in proportion
to what it removes. The fitted relationship between population and frame rate
has a slope between −0.11 and −0.28 where proportionality would give −1
(Section 4.4.2), so a fourteen- to twenty-nine-fold reduction returns a two- to
three-and-a-half-fold speed-up.

It does not support any causal account of the medium failure. Section 4.4.3
reports the rate; the explanation registered before the campaign was refuted by
the data it predicted (Section 4.7.3), and the replacement is descriptive. That
the mechanism is responsible is established by the contrast with configurations
that differ from it by this mechanism alone. Why it is responsible is open.

One asymmetry between this mechanism and the previous one deserves recording,
because it is the substance of Section 4.7 and the reason the two mechanisms
are not interchangeable efficiency options. Deterministic initialisation never
grows a population and therefore never cuts one; spatial reorganisation grows
the baseline's population and then removes nine tenths of it at a stroke. The
two arrive at similar final sizes — 197 000 to 243 000 primitives against
133 000 to 150 000 — by opposite routes, and only the second destabilises the
medium. The size of the final representation is therefore not what matters, a
point Section 4.7.2 establishes directly by showing that the configurations
combining both mechanisms finish *smaller* than this one and never collapse.

---

## Review log

**Domain Researcher** — The draft's verdict paragraph read as though perceptual
cost and medium collapse were two entries on one ledger. They are not
commensurable: one degrades an output, the other invalidates a different output
entirely. → *applied*: the conditional now turns on what the reconstruction is
for, and the section states why that makes this a coupling rather than a
trade-off. Second finding: the opposite-routes observation was missing, and it
is what makes Section 4.7.2's result intelligible in advance. → *applied*.

**Supervisor** — The draft opened by hedging between "effective" and
"dangerous" for a paragraph before committing. Say both in the first sentence
and let the section earn them. → *applied*. Devil's advocate: is "no amount of
storage saving compensates" too strong? It is correct as written, because it is
scoped to the case where the decomposition is the output; the preceding
sentence gives the other case, where the mechanism is plainly worth adopting.

**Journal Reviewer** — The perceptual cost was given in raw units without the
margin for a second time in this section. → *applied*: 0.020 stated inline.
Second: "roughly two runs in five" recurs from Section 4.4.3 without the exact
figure nearby. → *applied*: five of twelve stated in the same paragraph. Third:
the source method needed citation where its criterion is described.
→ *applied*, from the register.
