---
section: "3.4.4"
title: "Data Partitioning"
chapter: 3
action: Refine
evidence: ["dataset", "per_view_metrics.csv", "FINDINGS §15"]
figures: []
tables: []
citations: []
status: refined
word_count: 613
---

# 3.4.4 Data Partitioning

Every eighth image by index order is held out for evaluation. The rule is
inherited rather than chosen, and inheriting it is the point: it is the
convention used throughout this lineage, so the held-out frames here are the
same frames the methods this study builds on and compares against also hold
out. Fidelity numbers produced in this thesis are measured on the same pixels
as published ones.

The partition yields **thirteen evaluation frames across the four scenes** —
three each from Curaçao, Japanese Gardens and Panama, and four from the
twenty-nine-image IUI3 Red Sea — leaving seventy-five training views. The
counts are confirmed against the campaign's own per-view evaluation records
rather than derived from the rule alone.

**No validation split is used, and no hyperparameter is selected on held-out
data.** Every configuration value in this study is either inherited from a
source method at its published setting or fixed in advance by a stated rule
(Section 3.6.6). This is a deliberate constraint rather than an oversight: with
thirteen evaluation frames, a validation-driven search would fit the evaluation
set, and the resulting figures would not be comparable with the published ones
the shared partition exists to enable.

The partition is applied at load time and the resulting counts are written into
each run's manifest, so a silently empty or mis-sized evaluation set cannot
pass unnoticed. This is a small safeguard against a failure that would be
invisible in the results: a run evaluating on zero frames, or on the training
frames, would report metrics that look ordinary.

Two consequences of a thirteen-frame evaluation set are recorded here because
they bound every fidelity number in this thesis.

**A scene mean rests on three or four images.** That is a small sample by any
standard, and it is why this study runs three repeats per configuration and
judges every effect against repeat dispersion rather than against a single
run's value (Section 3.6.3). It is not a hypothetical concern: differences below
half a decibel are reported in this literature from single runs, and Section
4.1.3 shows that half a decibel is inside the repeat dispersion on three of
these four scenes.

**The held-out views within a scene are of very unequal difficulty.** Views
within one run differ by 6.65 to 11.25 dB, which is fourteen to eighty-six
times the repeat dispersion, and the hardest view is the same view in every
configuration. Because every configuration is scored on the same fixed views,
comparisons between configurations are unaffected — this is what keeps the
contrasts sound. What is affected is any reading of a scene mean as the typical
quality achieved on that scene. Section 3.7.5 states the reporting consequence
and Section 4.12.2 carries it as a limitation.

---

## Review log

**Domain Researcher** — The draft gave the partition rule and the counts but
not the reason for inheriting rather than choosing it, which is the only thing
that makes an every-eighth-frame rule defensible. → *applied*: comparability
with published numbers on the same pixels, stated first. Second finding: the
per-view spread was reported in Chapter IV as a limitation but never as a
property of the partition, where a reader would first encounter it.
→ *applied*, with the reassurance that fixed views keep contrasts sound.

**Supervisor** — The draft stated the absence of a validation split as a fact.
It is a constraint with a cost, and saying why it was accepted is more
convincing than reporting it neutrally. → *applied*: with thirteen frames a
validation-driven search would fit the evaluation set. Devil's advocate: does
declining hyperparameter search weaken the study's mechanism results? It bounds
them to the source methods' own settings, which Section 4.3.6 and its
counterparts already record as the one-operating-point limitation.

**Journal Reviewer** — The held-out counts were asserted from the rule.
→ *applied*: confirmed against the campaign's per-view records. Second: the
manifest safeguard was described without saying which failure it catches.
→ *applied*: a run evaluating on zero or on training frames would report
ordinary-looking metrics.
