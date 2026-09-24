---
section: "4.10.1"
title: "Replication Outcome per Comparison"
chapter: 4
action: Add
evidence: ["FINDINGS §11"]
figures: []
tables: ["Table 4.26"]
citations: []
status: refined
word_count: 719
---

# 4.10.1 Replication Outcome per Comparison

An earlier campaign ran four of these configurations on the same four scenes at
three repeats. Comparing the two is not a validation of either — both are this
work, using overlapping code — but it does establish which of this chapter's
results are stable across a re-execution and which are not.

> **[TABLE 4.26]** *Comparison against the archived campaign.* New minus old,
> with z on the pooled standard error; only comparisons beyond two standard
> errors are listed. Four configurations, four scenes, three repeats in each
> campaign. Source: FINDINGS §11.

| Configuration | PSNR beyond 2 SE | LPIPS beyond 2 SE | Count ratio |
|---|---|---|---|
| A0 | IUI3 Red Sea **+0.76** (2.4); Japanese Gardens −0.31 (−2.1) | none | ×0.86–1.17 |
| A1 | none | none | **×1.00 on all four** |
| A2 | none | none | ×0.97–1.02 |
| A3 | IUI3 Red Sea **−0.95** (−2.8); Panama −0.35 (−3.3) | none | ×0.78–1.24 |

**Perceptual similarity replicates on all sixteen comparisons.** Not one
exceeds two standard errors in either direction. Since Sections 4.3 to 4.6
adjudicate every mechanism effect and every interaction on that metric, the
chapter's principal fidelity results are the ones that replicate.

**Primitive count replicates to three significant figures for deterministic
initialisation on all four scenes**, which is the expected consequence of a
mechanism whose population is fixed by a deterministic correspondence stage
before optimisation. Spatial reorganisation replicates within 3 per cent. Its
collapse rate replicates in form as well: seed-conditioned, at roughly half the
runs.

**Twelve of sixteen pixel-metric comparisons replicate. Four do not, and two of
them matter.** On IUI3 Red Sea the unmodified configuration rose by 0.76 dB
between campaigns, with non-overlapping ranges — 26.35 to 27.29 then, 27.38 to
27.86 now — and quantisation fell by 0.95 dB, also non-overlapping. The
direction of the discrepancy can be adjudicated: this campaign's unmodified
configuration agrees with the published reference on that scene, 27.0 to 27.8,
and the archived one does not. It is the new figure that is anchored.

**The consequence is a downgrade, and it falls on a result reported earlier in
this chapter.** In the archived campaign, quantisation's pixel-metric effect on
IUI3 Red Sea was +0.35 dB. In this one it is −1.36 dB against the unmodified
configuration and −1.21 dB against the reference (Section 4.5.1). That is not a
change of magnitude; it is a change of sign. The effect is resolved *within*
this campaign and reversed *across* campaigns, and it is therefore reported as
**`UNRESOLVED` across campaigns**. Section 4.5.1's finding for that scene rests
on perceptual similarity, which replicates, and not on peak signal-to-noise
ratio, which does not.

This is the only quantitative claim in Chapter IV that the replication check
downgrades, and it is downgraded in the text of Section 4.5.1 as well as here,
rather than being corrected only in this section where a reader might not reach
it.

Two properties of this comparison bound what it can show. Both campaigns are
this work, so agreement demonstrates stability under re-execution rather than
independent reproduction, and a systematic error present in both would replicate
perfectly. And the comparison covers four configurations of the ten: the
interaction results of Section 4.6, the medium-coupling results of Section 4.7
beyond the collapse rate's form, and the restoration measurements of Section
4.5.7 have no archived counterpart and are unreplicated.

---

## Review log

**Domain Researcher** — The draft described the comparison as a replication
without qualifying what kind. Two campaigns by the same author with overlapping
code establish stability, not independent reproduction, and a referee will make
that point if the text does not. → *applied*, in the opening and again in the
closing bounds. Second finding: the draft reported the four non-replications
without adjudicating which figure is anchored, leaving the reader unable to
judge which campaign to believe. → *applied*: the reference control agrees with
the new baseline, which settles it.

**Supervisor** — The downgrade was stated here and left here. A reader of
Section 4.5.1 would carry away a resolved 1.21 dB loss with no indication that
it does not replicate. → *applied*: the downgrade is now stated as applying in
both places, and Section 4.5.1's own text carries it. Second: "four do not" was
followed immediately by detail, with no signal of which mattered.
→ *applied*: two of them matter, said first.

**Journal Reviewer** — Non-overlapping ranges were asserted without being
given. → *applied*: both campaigns' ranges for the unmodified configuration on
that scene. Second: the unreplicated portions of the chapter were not
enumerated, so the scope of the check was unclear. → *applied*: the three
result classes with no archived counterpart are named.
