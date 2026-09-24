---
section: "3.6.3"
title: "Scene Blocking and Repeats"
chapter: 3
action: Add
evidence: ["PLAN", "FINDINGS §0"]
figures: []
tables: []
citations: []
status: refined
word_count: 704
---

# 3.6.3 Scene Blocking and Repeats

Every configuration is run on all four scenes, and every configuration–scene
combination is run three times with different seeds. Scene is a blocking factor
rather than a replicate: results are reported per scene and never pooled across
them, for the reasons Section 3.3.2 establishes from the corpus itself.

**Three repeats is this design's dominant cost and it was not negotiable.** Of
the campaign's 120 runs, eighty are repeats of a configuration already
observed, and the same compute would have measured 120 distinct configurations.
It was spent on dispersion instead, and the justification is that without it
almost nothing in Chapter IV could be reported.

The reason is specific to this literature. **No source method in this study's
lineage reports error bars.** Published ablations in this area contain
differences of a few hundredths of a decibel between rows, from single runs at
a randomly seeded default, presented as though they were measurements. Section
4.1.3 shows what the dispersion here actually is: peak signal-to-noise standard
deviations between 0.126 and 0.733 dB depending on scene and configuration, and
primitive-count variation reaching 34 per cent on two scenes. A single-run
difference of a few tenths of a decibel is, on this corpus, indistinguishable
from reseeding.

## Bit-exact reproduction is unattainable and is not pursued

The rasteriser accumulates gradients atomically in its backward pass, which is
non-deterministic in floating-point arithmetic irrespective of seeding: the
order in which contributions are summed varies between executions, and floating
addition is not associative. Two runs with identical seeds and identical data
therefore need not produce identical models.

The correct response is to measure the resulting dispersion rather than to
chase determinism, and that is what the repeats are for. Independent
measurement of same-seed non-determinism in this implementation found a median
variation in final primitive count of 21 per cent with a tail reaching 59 per
cent, which is the scale the repeats are estimating.

One mechanism is an exception worth recording. Deterministic initialisation
produces its cloud offline, before training, and Section 4.10.1 reports that
its primitive count replicates across campaigns to three significant figures.
The determinism is in the artefact rather than in the optimisation, which is
the consequence of the placement decision of Section 3.4.5.

## What three repeats buys, and what it does not

Three is enough to establish a dispersion scale and to resolve effects that are
large relative to it — the mechanisms' count reductions, at nine to
twenty-nine times, resolve on every scene at nine to sixty standard errors. It
is not enough to resolve fidelity differences of a few tenths of a decibel, and
Chapter IV reports a substantial number of quantities as unresolved for exactly
this reason.

Section 3.6.5 defines what "unresolved" means and, more importantly, what it
does not. The label is a statement about three repeats; it is not a measurement
of zero, and the distinction is enforced throughout Chapter IV rather than
stated once here.

A consequence for the medium results is recorded because it shapes how Section
4.7 can report them. Attenuation-channel collapse is seed-conditioned: the same
configuration on the same scene collapses on one repeat and survives on
another. With three repeats the campaign can establish a *rate* and cannot
establish which repeat will fail — Section 4.7.4 reports that nothing measured
before the pruning event predicts it. A design with more repeats per cell would
estimate the rate more precisely; it would not, on this instrument set, make
the event predictable.

---

## Review log

**Domain Researcher** — The draft justified repeats by asserting that source
methods do not report error bars. The stronger form gives the observed
dispersion beside the differences those papers report, so a reader can see the
problem rather than accept the claim. → *applied*: 0.126 to 0.733 dB against
published differences of hundredths. Second finding: the deterministic-artefact
exception for M1 was absent, and it is the one place the campaign achieves
reproducibility. → *applied*.

**Supervisor** — The draft did not acknowledge what the repeats cost. Eighty of
120 runs is the dominant design decision in the study and stating it plainly
makes the justification carry weight. → *applied*, with the alternative the
compute could have bought. Devil's advocate: would more configurations have
been the better trade? Not for this study's questions — an interaction
estimated without a dispersion scale cannot be resolved at all, so the extra
configurations would have produced numbers nobody could interpret.

**Journal Reviewer** — Non-determinism was asserted without its cause.
→ *applied*: atomic accumulation, and floating addition not being associative.
Second: the seed-conditioned collapse consequence belonged here, where repeats
are specified, rather than only in Chapter IV. → *applied*, with the note that
more repeats would sharpen the rate and not make the event predictable.
