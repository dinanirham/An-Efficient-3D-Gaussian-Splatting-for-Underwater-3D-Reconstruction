---
section: "3.2"
title: "Research Stages"
chapter: 3
action: Refine
evidence: ["run_ledger.json", "FINDINGS §0"]
figures: []
tables: ["Table 3.2"]
citations: []
status: refined
word_count: 771
---

# 3.2 Research Stages

The campaign was executed in seven stages, one per configuration group, run
strictly in sequence on a single accelerator. The staging is not
administrative: each stage yields a usable result on its own, so a campaign
interrupted by the loss of its compute allocation still produces a defensible
finding rather than a partial matrix.

> **[TABLE 3.2]** *Stages as executed.* Dates and wall-clock are from the
> campaign run ledger, not from the plan. Retries are runs that required more
> than one attempt.

| Stage | Configurations | Runs | Executed | GPU-hours | Retries | What it establishes |
|---|---|---:|---|---:|---:|---|
| **S0** | SS | 12 | 15–16 Sep | 13.0 | 0 | The unmodified reference, and its own repeat dispersion |
| **S1** | A0 | 12 | 16–17 Sep | 12.2 | 1 | The configuration with no mechanism active, and the dispersion scale every contrast is judged against |
| **S2** | A2 | 12 | 17 Sep | 9.2 | 0 | RQ1 for spatial reorganisation; the medium-coupling test of RQ3 |
| **S3** | A1, A3 | 24 | 17–18 Sep | 22.9 | 2 | RQ1 for initialisation and quantisation |
| **S4** | A4, A5, A6 | 36 | 18–20 Sep | 30.3 | 1 | RQ2 — the three two-way interactions |
| **S5** | A7 | 12 | 20 Sep | 10.3 | 0 | RQ2 — the three-way term |
| **S6** | A0D | 12 | 21 Sep | 9.2 | 0 | The supplementary contrast of Section 3.5.5 |
| | | **120** | **15–21 Sep** | **107.0** | **4** | |

**The reference stage ran first, and this matters for the argument rather than
only for the schedule.** The equivalence margin of Section 3.6.2 was fixed
before the reference was run, and the reference was run before any mechanism
was measured. A reader can therefore be satisfied that the baseline validation
of Section 4.2.1 is not a post-hoc rationalisation of whatever the unmodified
configuration happened to produce.

**The reference was run at three repeats, not one.** An earlier version of this
design provided a single reference run per scene, on the reasoning that the
upstream implementation's seed does not reach the stochastic draws that
differentiate repeats. That reasoning is sound for the draws and wrong for the
dispersion: the reference's repeats differ for other reasons, and its
per-scene peak signal-to-noise standard deviation turns out to exceed the
unmodified configuration's on all four scenes (Section 4.1.3). Running it at
twelve rather than four is what allows every evaluative contrast in Chapter IV
to carry a standard error that includes the reference's own variability.

Stages ran sequentially with no overlap, each beginning as the previous
finished, across a continuous window from 15 to 21 September 2026 on one
accelerator type. This is what the one-implementation-state claim of Section
3.6.7 rests on, and Section 4.1.4 records why it rests on that rather than on a
recorded commit identifier.

Four runs required more than one attempt. Each carried an empty error field,
which is the signature of a platform disconnection rather than a fault in the
run, and each completed on a subsequent attempt; the completed attempt is the
one reported.

**Interrupted runs were restarted rather than resumed, and this was a
deliberate decision with a specific justification.** The compute environment
terminates sessions well before a stage completes, so resumption was the
obvious convenience. It was rejected because the checkpoint written by this
implementation omits the medium model, the learned background, the codebooks
and the training loop's schedule flags. A resumed run would silently
reinitialise the medium parameters and re-enter the schedule at the wrong
point, producing a run that reports as complete and is a different experiment
from the one specified. Restarting costs GPU-hours; resuming would have cost
the campaign's integrity, and the failure would not have been visible in any
result.

Campaign state was held in a durable ledger rather than in the driving process,
for the same reason: a process that dies takes its record with it. The ledger
is the source of Table 3.2 and of the completeness accounting in Section 4.1.1,
and it is the evidence for the execution window on which Section 3.6.7 depends.

---

## Review log

**Domain Researcher** — The draft described the planned staging, including a
reference control of four runs, and the campaign executed twelve. Reporting the
plan as though it were the execution is the specific defect this chapter is
being rewritten to remove. → *applied*: the table is now taken from the ledger,
with executed dates and measured GPU-hours, and the change from four reference
runs to twelve is stated with the reasoning that motivated it and the reason
that reasoning was incomplete. Second finding: that the reference stage ran
first was not remarked, and it is what makes the equivalence test credible.
→ *applied*.

**Supervisor** — The restart-not-resume decision was a sentence in the draft.
It is the clearest instance in the chapter of a methodological choice that
costs resources to protect validity, and a reader should see the reasoning.
→ *applied*: own paragraph, ending on the point that the failure it prevents
would have been invisible in the results. Devil's advocate: does the stage
table belong in the methodology or in the results? The plan belongs here and
the execution in Chapter IV — but the two differ, and showing the executed
figures here is what demonstrates the chapter describes what was done.

**Journal Reviewer** — GPU-hours and dates were given without their source.
→ *applied*, in the table caption. Second: the retry count appeared in the
table and in Section 4.1.1 with no cross-reference. → *applied*.
