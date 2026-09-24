---
section: "4.11.3"
title: "What Remains Open"
chapter: 4
action: Add
evidence: ["FINDINGS §5", "FINDINGS §10", "FINDINGS §14"]
figures: []
tables: []
citations: []
status: refined
word_count: 664
---

# 4.11.3 What Remains Open

Three questions are left open by this campaign in a way that matters, meaning
that an answer would change how the results should be used rather than merely
extending them.

**Why a large cut moves the medium model at all.** Section 4.7.1 establishes
that spatial reorganisation destabilises the attenuation coefficients and that
deterministic initialisation prevents it. Section 4.7.3 reports that the
explanation registered in advance was refuted by its own test and withdrawn.
Section 4.7.4 offers a description — the loss is expressed in the medium-only
interval following the cut, and the outcome is decided by the absolute level
reached — but that account is post-hoc, drawn from the data it describes, and
confounded: deterministic initialisation sets the entering count, the entering
attenuation level and the removal fraction together, and no configuration in
this campaign varies one while holding the others. The campaign establishes a
rate and a boundary alignment. It does not establish a mechanism, and Chapter V
does not claim one.

The experiment that would begin to separate the candidates is specific and
cheap. A configuration running the existing pruning schedule with the
medium-only interval removed would show whether that interval causes the fall
or merely hosts it (Section 4.7.5). A configuration reaching the same final
population by continuous reduction, with no scheduled event, would test the
abruptness account that the gradient-detachment contrast is merely consistent
with (Section 4.9.3). Neither exists here.

**Whether the restoration is accurate, not merely inconsistent.** Section 4.5.7
establishes that two attribute states of one model produce restored images 17
to 27 decibels apart, and Section 4.8.1 that a physically meaningless
attenuation coefficient renders held-out views as well as a plausible one. Both
are statements about what the training objective fails to constrain. Neither is
a statement about which restoration is closer to the truth, because the
medium-free image has no ground truth in this corpus. Every instrument this
chapter uses on the third axis detects failure without measuring quality.

This is the campaign's most consequential absence. A reference for the restored
image — a scene imaged in water and in air, or a calibrated target at known
depths — would convert collapse incidence, consistency and plausibility from
failure detectors into quality measures, and would allow the chapter's
methodological result to be stated as a positive recommendation rather than as
a warning.

**Whether the mechanisms' ranking survives a change of operating point.** Each
mechanism was run at one setting: one initial cloud size, one pruning budget,
one codebook configuration. The operating points of Section 4.6.6 are nine
points, not a frontier, and the count interaction of Section 4.6.2 is
structural in a way that a proportional budget would change. Nothing here
establishes how any mechanism behaves at a different setting, and in one case
the question is pointed: whether deterministic initialisation's perceptual cost
on IUI3 Red Sea would disappear with a denser initial cloud is unknown and
directly testable.

Two smaller openings are recorded without elaboration. Which repeat of a
large-cut configuration crosses zero is not predicted by anything measured
here, with every pre-cut covariate at an area under the curve of 0.65 or below
(Section 4.7.4). And the cause of the single non-replication across campaigns
cannot be identified, because neither campaign recorded its code state per run
(Section 4.10.2).

What is not open is the set of measurements in Section 4.11.2. The distinction
this subsection draws is between results the campaign established and
explanations it did not, and the second list being long is a property of an
honest report rather than of a weak one.

---

## Review log

**Domain Researcher** — The draft listed open questions without saying which
would change how the results are used, so a reader could not prioritise.
→ *applied*: the opening states that criterion, and the three are ordered by
it. Second finding: the two missing configurations were described in their own
sections but never named together as the experiment that would resolve RQ3's
mechanism. → *applied*, in one paragraph.

**Supervisor** — The draft ended on the smaller openings, leaving the
impression of a campaign that answered little. → *applied*: closing paragraph
distinguishes established measurements from absent explanations, and says why
a long second list is a property of an honest report. Devil's advocate: is
naming the restoration ground truth as "most consequential" defensible when the
collapse result stands without it? Yes — the collapse result detects failure,
and without a reference the chapter can never move from detection to
measurement, which bounds every third-axis claim in the thesis.

**Journal Reviewer** — The missing-experiment paragraph gave no indication of
cost, which matters for a future-work claim. → *applied*: described as specific
and cheap, being two additional configurations on an existing schedule. Second:
the two smaller openings needed their sections named. → *applied*.
