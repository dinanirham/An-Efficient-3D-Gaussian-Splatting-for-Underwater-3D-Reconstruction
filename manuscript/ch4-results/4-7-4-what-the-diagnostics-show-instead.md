---
section: "4.7.4"
title: "What the Diagnostics Show Instead"
chapter: 4
action: Add
evidence: ["FINDINGS §5", "diagnostics CSVs"]
figures: ["figure-4-10-attenuation-trajectory", "figure-4-12-removal-vs-loss"]
tables: ["Table 4.24"]
citations: []
status: refined
word_count: 897
---

# 4.7.4 What the Diagnostics Show Instead

**Everything in this subsection is post-hoc and unregistered.** No prediction
was made about any of it, and it is offered as description rather than as a
replacement explanation. The distinction matters because the account it
replaces (Section 4.7.3) was registered and failed, and substituting an
unregistered account with the same confidence would be the error that
pre-registration exists to prevent.

The per-iteration diagnostics record the full state on both sides of both
pruning events for all 48 simplification runs. Read without the registered
prediction, they show five things.

**First, the cut does not move the medium; the interval after it does.** On 48
of 48 runs at both events, the attenuation coefficients immediately after
pruning are identical to those immediately before. Pruning touches geometry
only. The coefficients then move during the 200 medium-only optimisation steps
that follow, with geometry frozen. Six of the nine collapses have their first
negative channel at iteration 15 001 — inside that interval. The sign crossing
happens in the remedy, not in the cut, and Section 4.7.5 takes this up.

**Second, what distinguishes the configurations that collapse from those that
never do is the size of the cut, and everything deterministic initialisation
changes alongside it.**

> **[TABLE 4.24]** *State at the first pruning event, by configuration group.*
> Ranges over the twelve runs of each group. Source: diagnostics CSVs.

| | Without initialisation (A2, A6) | With initialisation (A4, A7) |
|---|---|---|
| Count entering the event | 1.4–4.2 M | 196–247 k |
| Fraction removed | **86–95 %** | **29–36 %** |
| Mean β_att entering | 0.66–1.71 (median 1.2) | 1.60–5.35 (median 3.3) |
| β_att after the burst, as a fraction of before | collapsed 0.00–0.47 (median 0.21); intact 0.26–0.60 (median 0.38) | **0.89–1.04 (median 0.97)** |
| Collapses | 9 / 24 | 0 / 24 |

Every cut of 86 to 95 per cent loses 40 to 100 per cent of its attenuation
within 200 medium-only steps, and nine of 24 cross zero on the blue channel. No
cut of 29 to 36 per cent loses more than 11 per cent. The Spearman correlation
between fraction removed and the size of the attenuation drop at the first
event is **0.83 across all 48 runs**, and 0.46 within the affected
configurations alone. The quantity the registration specifically excluded is
the one that covaries with the outcome.

> **[FIGURE 4.12]** `figures/chapter4/figure-4-12-removal-vs-loss.pdf`
> *Fraction removed against attenuation lost, and the level reached.* One point
> per run at each event. The two configuration groups separate on the
> horizontal axis, and the right-hand panel shows the level each run's weakest
> channel reaches.
> **Status:** built

**Third, fractional loss is not what decides the outcome; the absolute level
reached is.** This correction arose while building the figures for this
chapter, and it overturns the reading the table above invites. At the *second*
event, four runs containing deterministic initialisation lose 52 to 73 per cent
of their mean attenuation from cuts of only 18 to 22 per cent — 3.32 to 0.90,
3.49 to 0.96, 6.85 to 2.76, 3.78 to 1.80 — and none loses a channel. A large
fractional loss is therefore not sufficient. Across all 96 burst events, runs
that eventually lose a channel reach a weakest-channel level between −0.056 and
+0.314 (median −0.038), while runs that do not reach between +0.110 and +6.327
(median +1.694). Configurations with deterministic initialisation enter the
first event at a mean attenuation of 1.60 to 5.35 against 0.66 to 1.71 without
it, so even a 73 per cent loss leaves them clear of zero. The large-cut
association survives with its mechanism narrowed: a 86 to 95 per cent cut
matters because it produces a large fractional loss **from an already low
level**.

> **[FIGURE 4.10]** `figures/chapter4/figure-4-10-attenuation-trajectory.pdf`
> *Attenuation trajectory through the pruning events.* Coefficients per channel
> against iteration for one collapsed and one intact repeat of the same
> configuration and scene, with both events and both intervals marked.
> **Status:** built

**Fourth, nothing measured before the cut predicts which repeat crosses zero.**
Within the large-cut runs, the area under the curve for pre-event dispersion is
0.42, for pre-event count 0.65, for pre-event mean attenuation 0.51, and for
pre-event minimum-channel attenuation 0.55. All are close to the 0.5 of a
predictor with no power. The collapse is seed-conditioned and, on this
instrument set, unpredictable from the pre-cut state. That is a limitation to
report, not a pattern to explain.

**Fifth, and decisively for what may be concluded, the protection is
confounded with itself.** Deterministic initialisation sets the entering count,
the entering attenuation level and the fraction removed simultaneously, because
all three follow from having a small fixed population. This design contains no
configuration that varies one while holding the others, so it cannot say which
is the operative variable. Section 4.7.1 establishes that the mechanism
protects; this subsection establishes that the campaign cannot say by which of
its three consequences.

The honest statement of the mechanism after this campaign is therefore narrow.
The medium model survives the removal of a third of the population and does not
reliably survive the removal of nine tenths. The loss is expressed in the
medium-only steps immediately following the cut. Whether a channel is lost is
decided by the absolute level reached rather than the fraction lost, which is
why configurations entering at three times the attenuation survive comparable
fractional losses. Which repeat crosses zero is not predicted by anything
measured here. **Why a large cut moves the attenuation coefficients at all
remains open**, and Chapter V carries it as the campaign's principal unanswered
question.

---

## Review log

**Domain Researcher** — The draft presented the large-cut association as the
replacement explanation. It is an association in post-hoc data, and the
confounding in point five means it cannot be causal on this design.
→ *applied*: the unregistered status is now the opening statement, and point
five is framed as decisive for what may be concluded. Second finding: the
level-reached correction was written as a refinement of the fractional-loss
account when it in fact overturns the reading the table invites. → *applied*,
with the four counterexample runs given individually.

**Supervisor** — Five numbered findings with no closing statement left the
reader without the takeaway. → *applied*: the honest statement of the mechanism
in full, ending on what is open. Devil's advocate: having withdrawn one account,
is offering another responsible? Only at this confidence — the subsection says
"description", says the association is confounded, and names the open question
rather than closing it.

**Journal Reviewer** — The correction in point three arrived without saying when
or why it was made, which matters because it revises an earlier reading.
→ *applied*: noted as arising during figure construction for this chapter.
Second: areas under the curve were given without the comparison value.
→ *applied*: 0.5 for a predictor with no power.
