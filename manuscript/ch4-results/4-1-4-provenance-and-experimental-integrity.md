---
section: "4.1.4"
title: "Provenance and Experimental Integrity"
chapter: 4
action: Add
evidence: ["FINDINGS §0", "run ledger"]
figures: []
tables: []
citations: []
status: refined
word_count: 548
---

# 4.1.4 Provenance and Experimental Integrity

The campaign was executed from a single implementation state on a single
accelerator type, and the run ledger records one continuous execution window
with no configuration change during it. All 120 runs are marked complete, one
stage per configuration, across 107 GPU-hours. Two qualifications apply, and
both are reported here rather than in the limitations section because they
affect how the reader should weigh specific claims later in the chapter.

First, the results table does not carry a per-run commit identifier. Each run
directory contains a configuration manifest recording the implementation state
at the time the run started, but the collection tool read a field that the
manifest does not write, and the corresponding column is empty for all 120
rows. The defect has since been located and corrected, and the field is
populated by subsequent collections; for the campaign reported here, the claim
that all runs share one implementation state rests on the ledger's execution
window and the worker log rather than on the results table itself. That is a
weaker form of evidence than a recorded identifier, and it is reported as such.
It is worth being precise about what the weakness does and does not permit: the
ledger establishes that the runs were executed in one continuous window by one
worker, which makes a mid-campaign implementation change unlikely, but it could
not detect one.

Second, the same audit established that at least one run of the earlier,
archived campaign was executed from an uncommitted working tree. That
observation does not affect the campaign reported in this chapter, whose runs
were all executed within the single window described above. It bears instead on
the cross-campaign comparison of Section 4.10, where a discrepancy between the
two campaigns cannot be attributed to any specific implementation change,
because the provenance necessary to identify one was never recorded for the
archived runs. The comparison is therefore reported as a replication check with
a stated limit on what a disagreement could be traced to, rather than as an
analysis of what changed.

A third observation belongs here for completeness, though it is a property of
the storage policy rather than a defect. Full point clouds were retained for the
first repeat of each configuration and scene only, the remaining repeats keeping
metrics and diagnostics but not the representation itself. Every result in this
chapter computed from metrics or per-iteration diagnostics therefore rests on
all three repeats, while every result requiring the trained representation —
the representation characteristics of Section 4.2.6, the rendered comparisons of
Sections 4.2.3 and 4.2.5, and the attribute-state consistency check of Section
4.8.2 — rests on one repeat per configuration and scene. Where a claim depends
on a single repeat this is stated at the claim, because a quantity measured
once carries no dispersion and cannot
be resolved against the thresholds of Section 4.1.3.

Taken together, these qualifications constrain three specific claims rather than
the campaign as a whole: the one-implementation-state claim, which rests on
ledger evidence; the cross-campaign comparison, which cannot attribute a
disagreement; and any result drawn from the retained representations, which has
no repeat dispersion behind it.

---

## Review log

**Domain Researcher** — The draft stated the missing commit identifier and its
correction but not what the ledger evidence can and cannot establish, which is
the question a referee would ask. → *applied*: the sentence distinguishing
"makes a change unlikely" from "could detect one". Second finding: the storage
policy was not mentioned in this subsection at all, yet it limits more claims
in this chapter than either recorded qualification. → *applied*: third
paragraph added, with the affected sections named.

**Supervisor** — Two qualifications were listed and then the subsection simply
stopped, leaving the reader to work out the scope of the damage. → *applied*:
closing paragraph names the three claims actually constrained, which is
narrower than the reader would otherwise assume and therefore worth stating
explicitly. Devil's advocate: does reporting provenance failures this
prominently undermine confidence in the campaign? It would if they were
concealed and found later; stated at the front with their scope bounded, they
do the opposite.

**Journal Reviewer** — The cross-reference to Section 4.2.6 called it "per-view
metrics"; under Revision 3 that subsection is Representation Characteristics
and the Invisible Population. → *applied*: named correctly, and the rendered
comparisons given their real section numbers instead of "throughout". Second:
"107 GPU-hours" and the completeness figures were asserted here and also in
Section 4.1.1, with no cross-reference.
→ *applied*: retained here only as the integrity claim, with the scope table in
4.1.1 carrying the accounting. Third: the subsection promised that
qualifications appear "rather than in the limitations section" without saying
whether Section 4.12 repeats them. → *applied*: phrasing now says they are
reported here because they affect specific later claims, which is compatible
with 4.12 collecting them.
