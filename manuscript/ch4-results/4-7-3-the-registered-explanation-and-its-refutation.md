---
section: "4.7.3"
title: "The Registered Explanation and Its Refutation"
chapter: 4
action: Add
evidence: ["FINDINGS §5b", "medium_collapse.json"]
figures: ["figure-4-11-dispersion-strata"]
tables: ["Table 4.23"]
citations: []
status: refined
word_count: 803
---

# 4.7.3 The Registered Explanation and Its Refutation

An explanation for the collapse was written and committed before the campaign
ran, together with the test that would falsify it. The test was run at the
first opportunity. **The explanation is false, and it is withdrawn rather than
qualified.**

The registered claim was that collapse at a pruning event is governed by the
change in cross-frame dispersion of the depth range across that event — and
specifically *not* by primitive count or by the proportion removed. The
reasoning was an identifiability argument: the medium model reads a per-frame
renormalised depth, so a pruning operation that changes the spread of depth
ranges across frames changes what the medium parameters are being fitted
against, and a large enough change would leave them unidentifiable.

The registered test followed directly. Within the configurations that apply
spatial reorganisation without deterministic initialisation, does the ratio of
depth-range dispersion after the first event to dispersion before it separate
the runs that collapsed from those that did not?

> **[TABLE 4.23]** *Depth-range dispersion ratio across the first pruning
> event, by outcome.* Coefficient of variation after the event divided by
> before, for the 24 runs applying spatial reorganisation without deterministic
> initialisation. Source: `medium_collapse.json`.

| Stratum | n | Minimum | Median | Maximum |
|---|---:|---:|---:|---:|
| Collapsed | 9 | 0.913 | 1.017 | 1.555 |
| Intact | 15 | 0.845 | 1.002 | 1.396 |

**The two distributions lie on top of one another.** Mann–Whitney U = 79 of a
possible 135, giving an area under the curve of 0.585 and an exact one-sided
p = 0.26. A test with no discriminating power would give 0.5. The ratio does
not separate the outcomes.

Within scenes the failure is worse than the pooled figure suggests. On Curaçao
the *intact* runs carry the larger dispersion ratios — 1.19 and 1.26 against
0.95, 1.07 and 1.10 for the collapsed — which is the opposite of the predicted
direction. On Panama every ratio, collapsed or not, sits between 0.91 and 1.02.
The Spearman correlation between the dispersion ratio and the size of the
attenuation drop across the event is **−0.32** within the affected
configurations and 0.18 across all 48 simplification runs. The quantity
predicted to govern the outcome does not even correlate with the quantity it
was meant to govern.

> **[FIGURE 4.11]** `figures/chapter4/figure-4-11-dispersion-strata.pdf`
> *Dispersion ratio by outcome.* The two strata as a strip plot, showing the
> overlap that refutes the registered explanation, with the four
> initialisation runs of ratio 3.5 to 7.3 marked.
> **Status:** built

The registration invited a direct counterexample, and the data supply one. At
the second pruning event, four runs containing deterministic initialisation
show dispersion ratios between **3.5 and 7.3** — the distribution broadened by
a factor the affected configurations never approach — and none of them loses a
channel. If dispersion change governed collapse, these four runs should be the
most damaged in the campaign. They are undamaged.

Per the analysis plan, written before the data were seen, the consequence is
stated without softening: the identifiability account is withdrawn rather than
qualified, and everything downstream that rested on it is rewritten as
description rather than explanation. That includes the account of *why*
deterministic initialisation protects the medium, which Section 4.7.1
establishes as a rate and which now has no mechanism attached to it; the
derivation that motivated the re-identification interval; and the interpretive
text the measuring instrument itself printed. The rate, the boundary alignment
and the protection all survive. The explanation does not.

This is the second pre-registered prediction in this chapter to fail, after the
additivity prediction of Section 4.6.4, and the treatment is deliberately
identical. A falsifiable claim was made in advance, the test was specified in
advance, the test was run, and the claim did not survive it. Reporting that is
the value of having registered it. The alternative — reclassifying the
explanation as exploratory once its test failed, or retaining it with
qualifications that the evidence does not support — would leave a reader unable
to distinguish the claims this campaign tested from the claims it merely
asserted.

What replaces it is descriptive and weaker, and Section 4.7.4 sets it out. The
size of the cut covaries with the outcome, which is the quantity the
registration specifically excluded.

---

## Review log

**Domain Researcher** — The draft stated the registered claim without its
reasoning, so a reader could not see why it was plausible enough to register.
→ *applied*: the identifiability argument in full, which also makes the
refutation informative rather than merely negative. Second finding: the draft
gave the Mann–Whitney result without an interpretive anchor. → *applied*: the
area under the curve against 0.5 for a test with no power.

**Supervisor** — The draft's closing paragraph hedged: "the account may require
revision". The plan said withdrawn, and the data say withdrawn. → *applied*:
withdrawn rather than qualified, stated twice, with the specific downstream
items named. Devil's advocate: does withdrawing the explanation weaken the
chapter's central finding? No — the finding is the rate and the protection,
both of which stand. What is lost is a mechanism the campaign never
established, and saying so is the honest position.

**Journal Reviewer** — The counterexample was described without saying it was
invited by the registration, which is what makes it decisive rather than
anecdotal. → *applied*. Second: the parallel with Section 4.6.4 needed stating
so the two failures are seen to be treated by one standard. → *applied*.
Third: the Spearman figures were given without their n. → *applied*.
