---
section: "4.2.7"
title: "Baseline Medium Stability"
chapter: 4
action: Add
evidence: ["FINDINGS §5a", "medium_collapse.json"]
figures: ["figure-4-c5-medium-convergence"]
tables: []
citations: []
status: refined
word_count: 512
---

# 4.2.7 Baseline Medium Stability

Section 4.7 reports that a substantial minority of simplification runs drive an
attenuation channel to a physically meaningless value and never recover it.
That result is an attribution — it holds a mechanism responsible — and an
attribution requires establishing that the estimator does not do this on its
own. This subsection establishes it, which is why it closes the baseline
section rather than opening Section 4.7.

A run is recorded as having lost a channel when one of the three attenuation
coefficients is driven to or below zero and does not return for the remainder
of training. The condition is a property of the optimisation trace rather than
a judgement about image quality, so it is determined without reference to any
fidelity metric and without a threshold chosen after the fact.

**Neither the unmodified configuration nor the reference implementation lost a
channel in any run: 0 of 24, across four scenes and three repeats each.** The
two implementations agree, and they agree on a quantity the equivalence margin
of Section 4.2.1 does not cover. That margin was defined over fidelity and
size; medium stability was not part of it, and the agreement here is therefore
independent evidence that the reimplementation behaves like the published
method in a respect the pre-registered test did not examine.

> **[FIGURE C5]** `figures/chapter4/figure-4-c5-medium-convergence.pdf`
> *Medium parameters over training.* Attenuation coefficients per channel
> against iteration, for every configuration. The baseline and reference traces
> settle and remain positive; the collapsed traces of Section 4.7 leave this
> envelope and do not return.
> **Status:** built

Two qualifications keep this result the size it is. First, stability is
established at 24 runs on four scenes, and a failure mode with an incidence
below approximately one run in twenty-four would not have been observed. The
claim is that the estimator does not do this at a rate the campaign could
detect, not that it cannot do it. Second, stability is not accuracy. A medium
model that remains within its feasible range throughout training may still be
recovering parameters that do not describe the water, and Section 4.2.4 reports
exactly that situation on one scene, where the fit is stable and internally
inconsistent at the same time. The two properties are independent, and this
chapter keeps them apart: Section 4.7 is about stability, Section 4.2.4 about
plausibility, and neither is evidence for the other.

With this established, the attribution in Section 4.7 has the form it needs. A
configuration differing from the unmodified one by a single mechanism, on the
same scenes with the same seeds, collapsing where the unmodified configuration
and the published reference both do not, isolates the mechanism as the cause of
the collapse. What it does not isolate is *why*, and Section 4.7.3 reports that
the explanation registered in advance for that mechanism was refuted by the
data it predicted.

---

## Review log

**Domain Researcher** — The draft stated the collapse criterion loosely, as
"the channel goes negative". The operative condition is that it does not
recover, which is what distinguishes a transient excursion from the failure
mode. → *applied*, with the note that the criterion reads the optimisation
trace and not any fidelity metric, so it cannot have been tuned to produce the
result. Second finding: the subsection asserted stability without bounding the
detectable incidence at n = 24. → *applied*.

**Supervisor** — The draft buried its purpose. This subsection exists to
license an attribution three sections later, and saying so in the first
paragraph makes the whole thing read as argument rather than inventory.
→ *applied*, and the closing paragraph now states the form the attribution
takes. Devil's advocate: does 0 of 24 risk being read as proving the estimator
is safe? It does, which is why the incidence bound is stated as a qualification
rather than left implicit.

**Journal Reviewer** — "Stability" and "accuracy" were used interchangeably in
two places, and the distinction matters because Section 4.2.4 reports a stable
fit that is not plausible. → *applied*: second qualification, with both
sections named and the explicit statement that neither property is evidence for
the other. Second: Figure C5 was built but uncited. → *applied*.
