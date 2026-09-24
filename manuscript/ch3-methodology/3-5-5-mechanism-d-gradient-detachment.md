---
section: "3.5.5"
title: "Mechanism D — Gradient Detachment"
chapter: 3
action: Add
evidence: ["CD register", "FINDINGS §6"]
figures: []
tables: []
citations: []
status: refined
word_count: 597
---

# 3.5.5 Mechanism D — Gradient Detachment

A tenth configuration in the campaign applies a mechanism that is not one of
the three factors. It detaches the alpha-loss gradient from density control, so
the adaptive densification procedure no longer receives the signal that drives
it to clone and split primitives in response to opacity error. The population
still grows, but less, and it grows continuously rather than being cut.

## Why it is not a fourth factor

The argument is structural, and it is worth giving in full because it justifies
a design decision rather than merely explaining one.

Deterministic initialisation disables density control entirely. The mechanism
described here modifies a gradient that only density control consumes.
Therefore **wherever deterministic initialisation is active, this mechanism has
no code path to execute and is provably inert** — not approximately inert, not
empirically inert, but inert by construction.

A 2⁴ factorial would contain sixteen cells, eight of which include
deterministic initialisation and in which this factor would do nothing. The
contrasts estimating its main effect would average eight live cells against
eight null ones, halving the estimate and rendering it uninterpretable as a
mechanism effect; its interaction terms with the other factors would be
similarly contaminated. Running the design would cost forty-eight additional
runs to produce an estimate that could not be read.

It is therefore measured as a **supplementary contrast** against the
configuration with no mechanism active, in a single stage of twelve runs, and
Section 3.8.1 excludes it from every contrast equation in the factorial. No
interaction term contains it, no main effect is adjusted for it, and no
composition involving it is estimated. It appears in the operating-point
description of Section 4.6.6 because it is a trained configuration a
practitioner could choose, which is a different thing from being a factor.

## Why it is in the campaign at all

Two reasons, both stated because a supplementary contrast needs to justify its
twelve runs.

First, it reduces the population by a different route from either of the
reduction mechanisms under test: continuously, with no scheduled event and no
medium-only interval. Section 4.9.3 sets it beside spatial reorganisation for
that reason, while stating plainly that the comparison is consistent with the
descriptive account of Section 4.7.4 rather than a test of it.

Second, it was measured in an earlier campaign against a baseline subsequently
shown to be defective, and the figure that campaign produced was carried into
this thesis as a point estimate. Re-measuring it against a baseline shown
equivalent to the published reference, at three repeats, is what allows Section
4.9.2 to retire that figure. A prediction about the outcome was registered
before the stage ran, in two parts, and Section 4.9.2 reports both.

---

## Review log

**Domain Researcher** — The draft asserted inertness without the argument. A
referee will ask why a 2⁴ design was not run, and "provably inert" needs the
code-path reason and the arithmetic consequence. → *applied*: both, with the
run cost of the alternative. Second finding: "provably" was doing work the
draft had not earned. → *applied*: the proof is one sentence — the mechanism
modifies a gradient only density control consumes, and initialisation disables
density control.

**Supervisor** — The draft did not justify spending twelve runs on a
non-factor. → *applied*: two reasons, the second being that it retires a figure
measured against a defective baseline, which is a correction the thesis owes
rather than an optional extra. Devil's advocate: is retiring one's own earlier
figure worth a campaign stage? It is, if the figure would otherwise stand in
the thesis — and it would have.

**Journal Reviewer** — The exclusion from the factorial was stated in general
terms. A reader needs to know exactly what it is excluded from.
→ *applied*: interaction terms, adjusted main effects and estimated
compositions, each named, with Section 3.8.1 as the place it is enforced.
