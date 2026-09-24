---
section: "3.8.2"
title: "Uncertainty Estimation"
chapter: 3
action: Add
evidence: ["PLAN", "FINDINGS §0", "analyse.py"]
figures: []
tables: []
citations: []
status: refined
word_count: 688
---

# 3.8.2 Uncertainty Estimation

Every effect in this thesis is reported with a standard error computed from the
repeat dispersion of the cells entering it. This subsection states how.

**For an additive contrast**, the standard error is the root of the summed
squared per-cell standard deviations, divided by the root of the repeat count.
For a difference of two cell means at three repeats each, that is the
familiar combination of both cells' dispersion — which is why a comparison
against the reference implementation carries the reference's variability as
well as the mechanism's, and why Section 4.1.3 reports that this makes several
effects resolve less often than the corresponding factorial contrast does.

**For a log-multiplicative contrast**, the same combination is performed on
relative standard deviations and the interval is formed in log space before
being exponentiated. This matters because an additive interval on a ratio can
reach zero and then disappears from a logarithmic axis; a log-space interval
cannot, and is symmetric in the sense a ratio requires.

**The standard error grows with the order of the contrast.** A two-way
interaction combines four cell means and a three-way contrast eight, so their
standard errors are approximately twice and approximately 2√2 times that of a
single cell mean. This is the arithmetic behind the `UNDETERMINED` declaration
of Section 3.6.5 and is the reason the three-way term is the least resolvable
quantity the campaign estimates.

## What is not done

**No significance test is applied to a main effect or an interaction.** The
resolution rule of Section 3.6.5 is a threshold on the ratio of an effect to
its standard error, applied identically to effects of both signs, and no
p-value is computed for any continuous effect. The campaign reports one
hypothesis test — the collapse-incidence comparison of Section 4.7.1 — and it
is a test on counts, named with its result and its sidedness.

**No correction for multiplicity is applied, and none is claimed.** The
campaign computes many contrasts, and a reader should hold that in mind when
reading any single resolved result at the threshold. The defence is not a
correction but the structure of the reporting: effects are reported per scene,
and a mechanism effect that resolves on one scene of four is described that
way rather than as a finding about the mechanism. An effect resolving on all
four scenes with a consistent sign is a different kind of evidence from one
resolving once, and Chapter IV distinguishes them throughout rather than
adjusting a threshold.

**Dispersion is not pooled across scenes.** Each contrast uses the dispersion
of the scene on which it was measured, because Section 3.3.2 shows the scenes
differ by a factor of four in count dispersion and substantially in fidelity
dispersion. A pooled estimate would over-resolve effects on the noisy scenes
and under-resolve them on the quiet ones.

**Repeat dispersion is not an estimate of all uncertainty.** It captures
run-to-run variation under identical configuration on identical data. It does
not capture uncertainty from the choice of corpus, from the single operating
point at which each mechanism was run, or from the thirteen-frame evaluation
set. Those are addressed as limitations in Section 4.12 rather than folded into
an interval, because folding them in would produce a number with a false claim
to completeness.

---

## Review log

**Domain Researcher** — The draft gave the additive combination and not the
log-multiplicative one, though four of the study's measures use it and the
count interactions are unreadable without it. → *applied*, with the reason an
additive interval on a ratio fails on a logarithmic axis. Second finding: the
growth of standard error with contrast order was stated in Section 3.6.5 as a
conclusion and never derived. → *applied*: four and eight cell means, giving
the two factors.

**Supervisor** — The draft said nothing about multiplicity, which is the first
thing a statistically literate examiner will raise given how many contrasts the
campaign computes. → *applied*: no correction is applied, the reason is stated,
and the structural defence — per-scene reporting and consistency of sign — is
given rather than a threshold adjustment. Devil's advocate: is declining a
correction defensible? It is, provided single-scene results are never described
as mechanism findings, which is a discipline Chapter IV can be checked against.

**Journal Reviewer** — The scope of the uncertainty estimate was not bounded,
so a reader could take a 2 SE interval as covering corpus and operating-point
uncertainty too. → *applied*: closing paragraph, with the reason those are not
folded in.
