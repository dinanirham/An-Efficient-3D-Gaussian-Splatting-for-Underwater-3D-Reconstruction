---
section: "4.2.1"
title: "Equivalence to the Unmodified Reference"
chapter: 4
action: Add
evidence: ["FINDINGS §1", "FINDINGS §0"]
figures:
  - "figure-4-02-baseline-vs-reference"
  - "figure-4-15b-configurations-vs-reference"
tables: ["Table 4.3"]
citations: ["Yang et al., 2024"]
status: refined
word_count: 724
---

# 4.2.1 Equivalence to the Unmodified Reference

Every mechanism result in this chapter is a comparison against the unmodified
reference implementation, and every factorial contrast is constructed from the
configuration in which no mechanism is active. Both roles depend on one prior
question: does the configuration with all mechanisms disabled behave as the
published method (Yang et al., 2024) behaves? If it does not, a difference
attributed to a mechanism could equally be a difference between two
implementations. This
subsection settles that question before any mechanism is measured, which is why
it precedes Section 4.3 rather than appearing as an appendix.

The test is one of equivalence rather than of difference, and its margin was
fixed before the reference configuration was run: ±1.0 dB in peak
signal-to-noise ratio, ±0.02 in learned perceptual similarity, and ±30 % in
primitive count. Equivalence is assessed on scene means over three repeats
rather than on paired seeds, because the reference implementation's seed does
not reach the stochastic draws that differentiate repeats, so a paired
comparison would be comparing a varying quantity against an effectively fixed
one. The comparison is made per scene, and the conclusion requires every scene
to fall within the margin.

> **[TABLE 4.3]** *Equivalence of the unmodified configuration (A0) to the
> reference implementation (SS), per scene, against the pre-registered margin.*
> Source: FINDINGS §1.

| Scene | ΔPSNR (dB) | ΔLPIPS | Count ratio | Within margin |
|---|---:|---:|---:|:-:|
| Curaçao | −0.042 | +0.0001 | 0.943 | yes |
| IUI3 Red Sea | +0.147 | −0.0005 | 0.915 | yes |
| Japanese Gardens | −0.245 | +0.0067 | 1.287 | yes |
| Panama | −0.122 | +0.0036 | 0.946 | yes |

All four scenes fall within the margin on all three metrics. The largest
fidelity discrepancy is 0.245 dB on Japanese Gardens, which is smaller than
that scene's own repeat dispersion for either configuration (Section 4.1.3),
and the largest perceptual discrepancy is 0.0067, roughly a third of the
allowance. The primitive-count comparison is the loosest: Japanese Gardens
consumes 74 % of its ±30 % allowance, the unmodified configuration finishing
with a larger population than the reference on that scene. That scene also
carries the campaign's widest count dispersion, so the discrepancy is within
what repetition alone produces there.

The conclusion is stated deliberately: the unmodified configuration is
**equivalent to the reference within the pre-registered margin, on the metrics
every downstream contrast uses**. It is not claimed that the implementation
reproduces the published method. A margin of ±1.0 dB is wide enough to
accommodate real differences, and equivalence within a margin is a bounded
statement about the size of any difference, not a demonstration that none
exists. What the result licenses is narrower and sufficient: a mechanism effect
larger than the margin cannot be an artefact of the reimplementation, and the
configuration with no mechanism active is a sound corner from which to build
the factorial contrasts of Section 4.6.

> **[FIGURE 4.2]** `figures/chapter4/figure-4-02-baseline-vs-reference.pdf`
> *Reference and unmodified configuration against ground truth.* Full held-out
> frame, one per scene. The two implementations are equivalent within the
> pre-registered margin; this is what that equivalence looks like.
> **Status:** built

A second, independent line of evidence supports the same conclusion and is
reported here because it concerns a quantity the margin does not cover.
Neither the unmodified configuration nor the reference lost an attenuation
channel in any of their 24 runs (Section 4.2.7). The equivalence margin was
defined over fidelity and size; medium stability was not part of it, and the
two implementations agreeing there as well is what allows Section 4.7 to
attribute any later collapse to a mechanism rather than to the estimator.

> **[FIGURE 4.15b]** `figures/chapter4/figure-4-15b-configurations-vs-reference.pdf`
> *Each configuration against the published reference.* Two-standard-error
> intervals per scene. The topmost group is the unmodified configuration, whose
> intervals straddle zero on peak signal-to-noise ratio on all four scenes and
> whose count ratio is approximately one — the equivalence established here,
> drawn on the same axes as every mechanism result that follows.
> **Status:** built · **Anchored on:** SS

One limitation of this test should be recorded where the reader meets it rather
than deferred. Equivalence is established at n = 3 per scene, so the margin is
tested against a dispersion estimated from three observations. A difference
smaller than the margin but larger than zero would not be detected, and the
design does not claim otherwise. This is the same resolution limit that governs
the mechanism results, applied to the baseline itself.

---

## Review log

**Domain Researcher** — Draft wrote "A0 reproduces SeaSplat", which the
pre-registration explicitly forbids and which the data cannot support at a
±1.0 dB margin. → *applied*: "equivalent within the pre-registered margin"
throughout, with a sentence stating what the margin does and does not license.
Second finding: the rationale for comparing scene means rather than paired
seeds was absent, and a referee familiar with the upstream implementation would
ask. → *applied*: the reference's seed does not reach the stochastic draws, so
a paired comparison is ill-posed.

**Supervisor** — The subsection read as a check being ticked. Its real function
is to license everything downstream, and that should be its opening sentence,
not its closing one. → *applied*: opens with why both roles depend on it.
Devil's advocate: is a ±1.0 dB margin so wide that equivalence is trivial? Partly
— and the honest response is not to defend the margin but to report that the
largest observed gap, 0.245 dB, is well inside it and inside repeat dispersion
too, which is a stronger result than the margin required. → *applied*.

**Journal Reviewer** — Equivalence claimed without stating n or that the margin
was pre-registered before the reference ran. → *applied*, both. Second: the
count column was given as a percentage in one place and a ratio in another.
→ *applied*: ratio in the table, allowance consumption in the prose. Third: the
limitation of testing equivalence at n = 3 belonged in the subsection rather
than only in Section 4.12. → *applied*: closing paragraph. Fourth: SeaSplat
required a citation at first substantive mention in this chapter.
→ *applied*: Yang et al. (2024), from the register.
