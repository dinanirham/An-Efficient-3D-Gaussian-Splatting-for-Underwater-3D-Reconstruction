---
section: "3.7.2"
title: "Representation and Computational Cost"
chapter: 3
action: Refine
evidence: ["results_runs.csv", "FINDINGS §12"]
figures: []
tables: ["Table 3.12"]
citations: []
status: refined
word_count: 785
---

# 3.7.2 Representation and Computational Cost

Each mechanism targets a different cost, so the campaign records several and
each mechanism is judged primarily on its own.

> **[TABLE 3.12]** *Cost measures recorded per run.*

| Measure | Definition | Primary for |
|---|---|---|
| Final primitive count | Primitives surviving to the end of training | M1, M2 |
| Stored bytes; bytes per primitive | Serialised model size, and that divided by count | M3 |
| Training wall-clock; effective optimizer steps | Time to train; the step count the schedule performed | M1 |
| Render rate; milliseconds per frame, with its coefficient of variation | Throughput over a timed sequence of held-out views | M2 |
| Peak render memory | Maximum device memory during rendering | — |

**Primitive count is recorded at four points**, not only at the end: at
initialisation, at iteration 10 000, at 15 000, and at completion. A single
final count cannot distinguish a mechanism that never grows a population from
one that grows and then prunes it, and those are exactly the two mechanisms
under test. The trajectory is what makes Section 4.3.5's account — that
deterministic initialisation works because the baseline's population is largely
inert rather than because its cloud is better — checkable rather than asserted.

**Stored size is recorded for configurations this study built and is not
available for the reference.** The unmodified upstream implementation does not
emit a serialised-size figure, so the compression result of Section 4.5.2 is
reported against the configuration with no mechanism active rather than against
the reference, which is the one place the chapter's anchoring convention does
not hold. Section 4.6.6 derives a reference size arithmetically from its
primitive count where a comparison is unavoidable, and labels it as derived.

**Render rate is measured over a timed sequence rather than from a single
frame**, and its coefficient of variation is recorded alongside it so that a
rate quoted from an unstable measurement can be identified as such. The number
of frames timed is also recorded. These are small safeguards against a class of
result that is easy to produce and hard to challenge: a frame-rate improvement
measured once, on one view, with a warm cache.

## What the cost measures do not capture

**Training wall-clock is not proportional to primitive count**, and the design
makes that visible rather than leaving it to be inferred. Effective optimizer
steps are constant within each configuration group by construction (Section
3.6.6), so a mechanism that removes nine tenths of the population still
performs the same number of steps. Section 4.3.2 reports training time falling
by 11 to 26 per cent against a population reduction of nine to eighteen times,
and the step-count accounting is what makes the two figures compatible rather
than contradictory.

**Render rate is not proportional to primitive count either.** Section 4.4.2
reports fitted slopes between −0.11 and −0.28 where inverse proportionality
would give −1. This thesis reports the relationship as measured and does not
model it: the campaign varied no rendering parameter and cannot decompose the
cost into rasterisation, compositing and fixed per-frame overheads.

**Stored bytes are specific to the attribute layout.** With spherical-harmonic
degree zero a primitive carries fourteen floating-point values (Section 3.1.1),
and the compression figure follows arithmetically from replacing three of them
with codebook indices. It is reported as a structural fact rather than as a
measured effect, and it would differ under any other layout.

Peak render memory is recorded and is reported only for the supplementary
contrast of Section 4.9.2, where it moves substantially. It is not a target
cost of any factorial mechanism and no claim rests on it.

---

## Review log

**Domain Researcher** — The draft recorded only the final primitive count. The
population trajectory is what distinguishes never-growing from
growing-then-pruning, which is the difference between the two reduction
mechanisms. → *applied*: four measurement points, with what the trajectory makes
checkable. Second finding: the unavailability of a reference stored size was
not stated here, though it is a property of the instrument set rather than of
Chapter IV's reporting. → *applied*.

**Supervisor** — The draft listed measures without saying what they fail to
capture, which is where the misreadings live: both time and rate are assumed
proportional to count and neither is. → *applied*: own subsection, with both
made compatible by the step-count accounting rather than left as an apparent
contradiction. Devil's advocate: is recording peak memory without using it
padding? It is reported once, where it moves; recording a measure and reporting
that it does nothing is preferable to omitting it.

**Journal Reviewer** — Render rate was described without its measurement
protocol, and a frame rate without one is not a measurement. → *applied*: timed
sequence, coefficient of variation, frame count, with the failure mode those
safeguard against named. Second: the layout-specific nature of the compression
figure needed stating here as well as in Section 3.5.4. → *applied*.
