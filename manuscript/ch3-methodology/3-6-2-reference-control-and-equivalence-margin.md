---
section: "3.6.2"
title: "Reference Control and Equivalence Margin"
chapter: 3
action: Add
evidence: ["PLAN", "FINDINGS §1", "run_ledger.json"]
figures: []
tables: []
citations: ["Yang et al., 2024"]
status: refined
word_count: 767
---

# 3.6.2 Reference Control and Equivalence Margin

A tenth configuration runs the unmodified upstream implementation of the
underwater baseline (Yang et al., 2024) at its published settings, on the same
prepared data and the same harness as every other configuration. It is not a
cell of the factorial and no mechanism is applied to it.

**Its purpose is to make the study's attributions defensible.** Every result in
Chapter IV is a difference between configurations that this study built. If the
configuration with no mechanism active did not behave as the published method
behaves, a difference attributed to a mechanism could equally be a difference
between two implementations, and no amount of internal consistency would
distinguish the two readings. A reference control is what converts "our
configuration A differs from our configuration B" into a statement about
mechanisms.

## The margin, and when it was fixed

Equivalence is assessed against a margin fixed **before the reference
configuration was run**: ±1.0 dB in peak signal-to-noise ratio, ±0.02 in
learned perceptual similarity, and ±30 per cent in primitive count. The
ordering matters and is verifiable from the campaign ledger, which records the
reference stage as the first of the seven (Section 3.2). A margin chosen after
seeing the comparison would be worthless, and a reader has no way to
distinguish a pre-specified margin from a post-hoc one except by the record.

The margin is deliberately wide. It is not a claim that the implementations are
identical; it is a bound on how different they can be, and the bound is set at
the level where a difference would begin to confound the mechanism results. The
largest main effect any mechanism produces on peak signal-to-noise ratio is
below one decibel, so a baseline discrepancy of a decibel would be the size of
the effects being measured. Section 4.2.1 reports the observed discrepancies,
the largest of which is 0.245 dB — well inside the margin and also inside that
scene's own repeat dispersion, which is a stronger result than the margin
required.

## Comparison on scene means, not paired seeds

Equivalence is assessed on scene means over three repeats rather than on
seed-paired differences. The reference implementation's seed does not reach the
stochastic draws that differentiate this study's repeats, so pairing would
compare a varying quantity against an effectively fixed one and would
understate the dispersion of the comparison.

**The reference was run at three repeats rather than one, and the reasoning for
that changed during the design.** An earlier version provided a single reference
run per scene, on the same argument — if the seed does not reach the draws,
repeats add nothing. That argument is correct about the draws and wrong about
the dispersion: the reference's repeats differ for other reasons, and its
per-scene peak signal-to-noise standard deviation turns out to exceed the
unmodified configuration's on all four scenes (Section 4.1.3). Running it
twelve times is what allows every evaluative contrast in Chapter IV to carry a
standard error that includes the reference's own variability. Had it been run
four times, the anchored comparisons of Chapter IV would have been reported
with a standard error that omitted a real and, as it turns out, larger source
of variation.

## What the control does not establish

It does not establish that this study's implementation reproduces the published
method. Equivalence within a margin bounds a difference; it does not show none
exists, and Section 4.2.1 states the claim in those terms throughout. It does
not cover quantities outside the margin — medium stability was not part of it,
and the two implementations agreeing there (Section 4.2.7) is independent
evidence rather than part of this test. And it is a control on *fidelity and
size only*: the reference records no stored size, which is why one axis of
Chapter IV cannot be anchored on it (Section 4.5.2).

---

## Review log

**Domain Researcher** — The draft stated the margin without saying why those
values. A margin is only defensible if its width is tied to something — here,
the size of the effects it must not confound. → *applied*: the largest PSNR
main effect is below a decibel, so a decibel of baseline discrepancy would be
the size of the signal. Second finding: the storage exception was not mentioned,
though it limits what the control covers. → *applied*, in the closing
subsection.

**Supervisor** — The draft described the three-repeat reference as a design
choice. It was a *revision* to a design choice, made for a reason that the
results then vindicated, and saying so is more useful than presenting it as
always having been the plan. → *applied*, including what the four-run version
would have cost. Devil's advocate: does admitting the original reasoning was
incomplete undermine confidence in the design? The alternative is a reader
noticing that Chapter IV's dispersion table makes the original argument
untenable, and wondering why the methodology does not say so.

**Journal Reviewer** — "Fixed before the campaign" was asserted without saying
how a reader could verify it. → *applied*: the ledger records the reference
stage as the first of seven. Second: the scene-means decision was stated
without its consequence. → *applied*: pairing would understate the dispersion
of the comparison.
