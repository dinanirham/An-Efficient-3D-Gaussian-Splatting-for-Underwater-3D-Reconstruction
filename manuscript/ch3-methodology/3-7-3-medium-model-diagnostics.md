---
section: "3.7.3"
title: "Medium-Model Diagnostics"
chapter: 3
action: Add
evidence: ["results_runs.csv", "medium_collapse.json", "diagnostics CSVs"]
figures: []
tables: ["Table 3.13"]
citations: []
status: refined
word_count: 826
---

# 3.7.3 Medium-Model Diagnostics

The fidelity metrics of Section 3.7.1 describe the composed image and can say
nothing about the decomposition beneath it. This subsection describes the
instruments this study added in order to observe the medium model directly.
They are the third evaluation axis, and they exist because the campaign's
central hypothesis concerns a failure the standard metrics cannot see.

> **[TABLE 3.13]** *Medium-model quantities recorded.*

| Quantity | Recorded | Purpose |
|---|---|---|
| Attenuation coefficient, per channel | Final value, and at a fixed interval through training | Collapse detection; spectral ordering |
| Backscatter saturation rate, per channel | Final value, and through training | Cross-coefficient consistency |
| Veiling light, per channel | Final value, and through training | Spectral plausibility |
| Depth normalisation constants | At every intervention boundary | The registered hypothesis of Section 3.6.4 |
| Collapse flag and affected channels | Per run | Incidence |
| Largest attenuation drop, and the iteration of it | Per run | Boundary alignment |

**All nine medium scalars and the depth normalisation constants are logged at a
fixed interval and at every intervention boundary.** Logging at boundaries
specifically is what converts the central hypothesis from an argument into a
measurement: the registered claim concerned what happens *across* a reduction
event, so the state on both sides of every event is recorded rather than only
the final state.

## The three instruments, and what each can establish

**Collapse incidence.** A run is recorded as having lost a channel when an
attenuation coefficient is driven to or below zero and does not recover before
training ends. The criterion reads the optimisation trace rather than any
image, so it cannot have been tuned to produce a result, and it requires no
ground truth. It is the strongest of the three instruments and it detects only
outright departure from the feasible range.

**Internal consistency.** Two quantities that must agree are compared. The
attenuation and backscatter coefficient sets describe the same water column and
should order their channels alike; Section 4.2.4 reports one scene where they
do not. This needs no ground truth either, and it detects a broader class of
problem than collapse — but it establishes only that something is wrong, never
which part.

**Physical plausibility.** Water attenuates long wavelengths fastest, so the
attenuation coefficients should order red above green above blue. This is the
weakest of the three and its weakness is structural, for the reason given next.

## What the renormalised depth permits

The medium model reads a depth renormalised to the unit interval per frame
(Sections 3.1.1 and 3.4.3). The fitted coefficients are therefore dimensionless
with respect to a normalised depth, not attenuation in inverse metres. Two
consequences bind every claim in this thesis about the medium:

**Magnitudes cannot be compared with published measurements of natural water**,
and cannot be compared across scenes of differing depth range. No coefficient
reported in this thesis is in physical units, and none is presented as though
it were.

**Only the ordering of the three channels within one scene is interpretable**,
because all three are fitted against the same normalised depth within a scene.
Every plausibility claim in Chapter IV is accordingly a claim about ordering —
including the spectral inversion reported on one scene, which is reported as a
direction and not as a magnitude.

## What none of these instruments does

**None measures accuracy.** They detect failure, inconsistency and
implausibility; they cannot establish that a medium model which passes all
three is correct, because the quantity that would settle it — a reference for
the medium-free image — does not exist in this corpus. Section 4.8.3 states
this as the campaign's most consequential missing instrument, and Section 5.4
carries its acquisition as future work.

This limitation is stated here, where the instruments are specified, rather
than only where their results are reported. A reader should carry it into
Chapter IV: every statement there about the medium model is a statement about
stability, consistency or plausibility, and none is a statement about
correctness.

---

## Review log

**Domain Researcher** — The draft described the diagnostics as logging without
saying why boundary logging specifically matters. The registered hypothesis is
about what happens across an event, so recording both sides of every event is
what makes it testable. → *applied*. Second finding: the three instruments were
not distinguished by what each can establish, so a reader could not tell that
they detect different classes of problem with different strength.
→ *applied*: each with what it needs, what it detects and its limit.

**Supervisor** — The draft stated the renormalised-depth caveat as a
measurement detail. It is the reason the weakest of the three instruments is
weak, and placing it immediately after the instruments makes that connection.
→ *applied*. Devil's advocate: does an axis on which nothing measures accuracy
justify being called an evaluation axis at all? Yes — collapse is an objective
failure and the campaign's largest result rests on it — but the closing
subsection says plainly what it cannot do rather than letting the word
"evaluation" overclaim.

**Journal Reviewer** — The collapse criterion was given without stating that it
is independent of any image metric, which is what makes it immune to the
circularity a referee would suspect. → *applied*. Second: the missing
restoration reference was mentioned in Chapter IV but never in the methodology,
where the instrument set is specified. → *applied*, with both destinations.
