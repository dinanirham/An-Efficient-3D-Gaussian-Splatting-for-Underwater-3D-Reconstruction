---
section: "4.10.2"
title: "What the Provenance Limit Prevents"
chapter: 4
action: Add
evidence: ["FINDINGS §11", "FINDINGS §0"]
figures: []
tables: []
citations: []
status: refined
word_count: 546
---

# 4.10.2 What the Provenance Limit Prevents

Section 4.10.1 establishes that one result does not replicate across campaigns.
This subsection states why the cause cannot be identified, because the reason
is specific, avoidable, and worth recording as a methodological lesson rather
than as an apology.

The training code changed between the two campaigns. Three changes are known
from the development record: a correction to alpha-gradient routing on 2
September, fixes to the opacity schedule used by deterministic initialisation
on 10 September, and a further change on 12 to 13 September. Any of these could
plausibly bear on a pixel-metric difference of the size observed, and the
discrepancy falls on the two configurations most likely to be affected by the
first and third.

**Which of those changes the archived runs predate is unrecorded.** Neither
campaign populated its per-run commit identifier: the collection tool read a
field the configuration manifest does not write, and the column is empty in
both (Section 4.1.4). The archived campaign is worse placed still — a sampled
manifest from it records a working tree with uncommitted modifications, so even
a recorded identifier would not have described the code that ran.

The consequence is that the non-replication can be reported but not attributed.
It is not possible to say whether the archived figure reflects a defect that a
named change corrected, whether the new figure reflects a regression, or
whether the difference is unrelated to any of the three changes. Section 4.10.1
adjudicates which figure is *anchored* — the new one, because it agrees with
the published reference on that scene — which is a different and weaker
statement than identifying a cause.

Two things follow, and both are narrow. The downgrade of that result stands
regardless of cause: an effect that reverses sign between executions is
`UNRESOLVED` across campaigns whatever produced the reversal. And the
comparison in Section 4.10.1 remains informative about stability, because
sixteen of sixteen perceptual comparisons and most count comparisons replicate
despite the same unrecorded code drift applying to all of them.

The methodological lesson is stated in Chapter V rather than argued here, but
the form of it belongs with the evidence. A campaign that records its code
state per run can attribute a non-replication to a change; a campaign that does
not can only observe it. The defect that prevented this has been located and
corrected, and the field populates in subsequent collections — which serves
future work and does nothing for the comparison in this section.

---

## Review log

**Domain Researcher** — The draft listed the three code changes without saying
why they are the candidates, which makes the paragraph look like an alibi.
→ *applied*: the discrepancy falls on the configurations most plausibly touched
by two of them, stated. Second finding: the dirty-working-tree observation was
omitted, and it is what makes the archived campaign unattributable even in
principle. → *applied*.

**Supervisor** — The draft was apologetic in tone and buried the point that the
downgrade holds regardless. → *applied*: both consequences stated plainly, with
the observation that the replication check remains informative because the same
drift applies to the comparisons that did replicate. Devil's advocate: does a
subsection about a missing field earn its place? Yes — it is the only thing
standing between a reported non-replication and an explained one, and a reader
is entitled to know which they have.

**Journal Reviewer** — "Anchored" was used in Section 4.10.1's sense without
distinguishing it from identifying a cause. → *applied*: named as a weaker
statement, explicitly.
