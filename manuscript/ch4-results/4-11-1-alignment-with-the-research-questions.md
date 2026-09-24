---
section: "4.11.1"
title: "Alignment with the Research Questions"
chapter: 4
action: Rewrite
evidence: ["all"]
figures: []
tables: ["Table 4.27"]
citations: []
status: refined
word_count: 738
---

# 4.11.1 Alignment with the Research Questions

Each of the four research questions stated in Section 1.3.1 is answered by this
chapter, and each answer carries a boundary. This subsection places them side
by side so that a reader can see what was asked, what was found, at what
resolution, and what the finding does not extend to.

> **[TABLE 4.27]** *Research questions, answers and boundaries.* Section
> references are to this chapter.

| | Question | Answer | Evidence | Resolution | Boundary |
|---|---|---|---|---|---|
| **RQ1** | How far do the mechanisms reduce cost relative to the published method, and at what fidelity cost? | All three reduce their target cost, resolved on every scene. Fidelity cost is mechanism-specific and falls almost entirely on perceptual similarity | 4.3, 4.4, 4.5 | Count and bytes resolved throughout; PSNR unresolved on most scene–mechanism pairs | Stored size cannot be compared with the reference; one operating point per mechanism |
| **RQ2** | Do the mechanisms compose additively, or do they interact? | They do not compose additively. Initialisation × simplification is strongly sub-additive on count and favourably non-additive on perceptual similarity; simplification × quantisation is sub-additive on quality; initialisation × quantisation resolves inconsistently | 4.6 | Adjudicated on LPIPS and count; PSNR interactions `UNDETERMINED` by construction | The count interaction is structural, a consequence of an absolute budget; the three-way term is unresolved |
| **RQ3** | Does population reduction compromise medium identifiability, and does anything protect it? | Yes, and yes. Simplification loses an attenuation channel in 9 of 24 runs without dense initialisation and 0 of 24 with it, Fisher exact p = 0.0016 | 4.7 | Rate established and boundary-aligned without exception | The registered explanation was refuted and no replacement is claimed; the protection is confounded with itself; *why* a large cut moves the medium is open |
| **RQ4** | Are the conventional fidelity metrics sensitive to medium-model failure? | No. Collapsed and intact runs differ by a median 0.8 baseline standard deviation on the composed image with inconsistent sign; two attribute states of one model differ by 17–27 dB in restoration and ~1 dB in composition | 4.8 | Twelve comparisons at three repeats; the second line n = 1 per scene | Establishes insensitivity, not restoration accuracy — no ground truth exists for the restored image |

Two observations about the set as a whole are worth making here rather than
leaving to a reader to assemble.

**The first three questions are answered on axes the literature already
reports; the fourth is answered on an axis it does not.** RQ1 and RQ2 concern
cost and fidelity, and a competent study of any efficiency mechanism would
report them. RQ3 requires a physical model to be present at all, and RQ4
requires one to have failed while the conventional metrics said nothing. The
campaign's distinctive contribution is therefore concentrated in the second
half of the chapter, and the first half is what makes it interpretable: without
the equivalence of Section 4.2.1 and the main effects of Sections 4.3 to 4.5,
the collapse result would be a curiosity rather than an attribution.

**Two of the four answers rest on predictions that failed.** RQ2's
initialisation × quantisation prediction of additivity was falsified by its own
registered criterion (Section 4.6.4), and RQ3's explanation of the collapse
mechanism was refuted and withdrawn (Section 4.7.3). In both cases what
survives is the measurement and not the account. This is visible in the table
as the gap between the Answer and Boundary columns for those two rows, and it
is the honest state of the work: the campaign established what happens more
securely than why.

One question from the original set is not answered and is not listed. Whether
the mechanisms' ranking persists across operating points would require a sweep
of budget, cloud size and codebook size that the campaign did not run. It is
carried to Section 5.4 as future work rather than presented here as an open
research question, because a question the design was never capable of answering
does not belong in a results chapter's alignment table.

---

## Review log

**Domain Researcher** — The draft's table had Answer and Evidence columns only,
which invites a reader to take each answer at face value. Resolution and
Boundary are what make the answers usable. → *applied*: five columns, with each
boundary stating what the finding does not extend to. Second finding: RQ4's
answer risked reading as a claim about restoration quality. → *applied*:
boundary names insensitivity rather than accuracy, and the absent ground truth.

**Supervisor** — A table alone is an index, not a synthesis. The two
observations that can only be made by looking across all four rows are the
subsection's actual contribution. → *applied*: the concentration of the
contribution in the second half, and the fact that two answers rest on failed
predictions. Devil's advocate: does admitting that two predictions failed
undercut the chapter? It would if the measurements depended on them; they do
not, and saying which survives is stronger than implying all of it does.

**Journal Reviewer** — The retired fifth question was omitted silently, which a
reader comparing against Chapter I would notice. → *applied*: named, with the
reason it is not in the table and its destination. Second: the Fisher result
appeared in the table without its test. → *applied*.
