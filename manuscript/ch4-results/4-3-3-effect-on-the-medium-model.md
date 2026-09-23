---
section: "4.3.3"
title: "Effect on the Medium Model"
chapter: 4
action: Add
evidence: ["FINDINGS §5c", "FINDINGS §2b", "medium_collapse.json"]
figures: ["figure-4-c5-medium-convergence"]
tables: []
citations: []
status: refined
word_count: 497
---

# 4.3.3 Effect on the Medium Model

The third evaluation axis is reported for every mechanism, and for this one the
result is quickly stated. Deterministic initialisation lost no attenuation
channel in any of its twelve runs, matching the reference and the unmodified
configuration (Section 4.2.7). On the axis that distinguishes configurations in
Section 4.7, this mechanism alone is indistinguishable from doing nothing.

The fitted medium parameters also move very little. Across the four scenes the
attenuation coefficients under this mechanism retain the spectral ordering
reported for the baseline in Section 4.2.4 — physical on three scenes, inverted
on IUI3 Red Sea — and the mechanism neither introduces the inversion nor
corrects it. That the anomaly survives a mechanism which replaces the entire
population-growth procedure is itself informative: whatever makes the IUI3 Red
Sea fit incoherent is not a property of how the primitives came to exist.

> **[FIGURE C5]** `figures/chapter4/figure-4-c5-medium-convergence.pdf`
> *Medium parameters over training, all configurations.* Attenuation
> coefficients per channel against iteration. This mechanism's traces remain
> within the envelope established by the reference throughout.
> **Status:** built

**This subsection reports a rate and defers the analysis.** The result that
matters about this mechanism and the medium model is not what it does alone but
what it does in combination: configurations pairing it with spatial
reorganisation lose no channel in 24 runs, where configurations applying
spatial reorganisation without it lose one in nine of 24. That is the
campaign's largest finding on the third axis, and it is a property of the
combination rather than of either mechanism separately, so it belongs to
Section 4.7.1 where the incidence across all configurations is reported
together, and to Section 4.7.4 where what the diagnostics show is examined.
Reporting it here would attribute to one mechanism a protection that only
appears when a second is present.

One consequence should nonetheless be recorded at this point, because it
constrains how Section 4.3.5 may state the mechanism's benefits. A mechanism
that is inert on an axis cannot be credited with safety on it. The absence of
collapse here is the same absence the reference exhibits, and on a corpus where
the baseline never fails there is no room for this mechanism to demonstrate
that it would not. The protection established in Section 4.7 is evidence about
what happens when this mechanism is combined with one that does destabilise the
medium; it is not evidence that the mechanism is intrinsically protective, and
the distinction is maintained throughout this chapter.

---

## Review log

**Domain Researcher** — The draft credited this mechanism with medium stability
on the strength of 0 of 12, which is the same result the reference produces and
therefore evidence of nothing. → *applied*: stated as indistinguishable from
doing nothing on this axis, with the closing paragraph making the logical point
explicit. Second finding: that the IUI3 spectral anomaly survives a mechanism
replacing the whole densification procedure is a real piece of evidence about
where the anomaly is not. → *applied*.

**Supervisor** — The draft pulled the protection result forward into this
subsection, which reads well and is wrong: the protection is a property of the
combination, and stating it here would let a reader attribute it to this
mechanism alone. → *applied*: bolded statement that the subsection reports a
rate and defers, with both destination sections named. Devil's advocate: is
deferring the most interesting result to Section 4.7 a loss of impact? It is,
and the alternative is a misattribution the rest of the chapter would have to
walk back.

**Journal Reviewer** — The collapse denominators were given without saying what
a run is counted over. → *applied*: twelve runs, four scenes, three repeats,
consistent with the accounting in Section 4.1.1. Second: Figure C5 was cited in
Section 4.2.7 and again here without distinguishing what each citation is for.
→ *applied*: the caption here names what this mechanism's traces do.
