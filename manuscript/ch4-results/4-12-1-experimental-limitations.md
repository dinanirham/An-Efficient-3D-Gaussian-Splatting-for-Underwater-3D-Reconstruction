---
section: "4.12.1"
title: "Experimental Limitations"
chapter: 4
action: Refine
evidence: ["FINDINGS §14", "FINDINGS §0"]
figures: []
tables: []
citations: []
status: refined
word_count: 651
---

# 4.12.1 Experimental Limitations

The limitations that follow have been stated at the points where they bear on
particular claims. They are collected here so that a reader assessing the
campaign as a whole can see their extent together.

**Four scenes from one corpus.** All four come from a single dataset with a
common acquisition style. The corpus spans a 7 dB range in reconstruction
difficulty and includes one scene that behaves anomalously in five respects
(Section 4.12.4), so it is not homogeneous — but it is not a sample of
underwater scenes in general, and nothing here establishes behaviour under
different water types, wider camera baselines, or acquisition geometries other
than those represented.

**Three repeats.** The resolution consequences are set out in Section 4.1.3 and
enumerated in Section 4.12.3. Three repeats is enough to establish a dispersion
scale and to resolve effects of a factor of ten; it is not enough to resolve
fidelity differences of a few tenths of a decibel, and the chapter reports a
substantial number of quantities as `UNRESOLVED` for that reason.

**One operating point per mechanism.** One initial cloud size, one pruning
budget applied at two fixed iterations, one codebook configuration. The
campaign therefore has no rate–distortion curve within any mechanism, and the
operating points of Section 4.6.6 describe nine configurations rather than an
achievable frontier. One reported result — the count interaction of Section
4.6.2 — is a direct consequence of the budget being absolute rather than
proportional, and would change under a different formulation.

**Full point clouds retained for one repeat per configuration and scene.** The
storage policy kept metrics and per-iteration diagnostics for all three repeats
but the trained representation for the first only. Every result requiring the
representation therefore rests on a single run: the geometric statistics of
Section 4.2.6, all rendered comparisons, and the sixteen-run restoration
measurement of Section 4.5.7. These carry no dispersion and are not resolved
against any threshold. Where a chapter claim depends on one of them, the
dependence is stated at the claim.

**No collapsed and intact pair at the retained repeat.** No configuration has
both outcomes at the first repeat, so every rendered illustration of the
collapse compares runs differing in configuration as well as in outcome
(Figure 4.13). The incidence of Section 4.7.1 and the strata comparison of
Section 4.8.1 rest on all three repeats and are unaffected.

**Missing per-run provenance.** The commit identifier is empty in all 120 rows
of this campaign and in the archived one, because the collection tool read a
field the configuration manifest does not write. The one-implementation-state
claim rests on the execution window and the worker log rather than on a
recorded identifier (Section 4.1.4), and the single non-replication across
campaigns cannot be attributed to a named code change (Section 4.10.2). The
defect is corrected for future collections and cannot be repaired for these.

**Widened count dispersion on two scenes.** Repeat variation in final primitive
count reaches 34 per cent on Japanese Gardens and 37 per cent on Panama, against
9 to 13 per cent on the other two. Independent measurement of same-seed
non-determinism found a median of 21 per cent with a tail to 59 per cent, so
this is within what the training process produces. Its consequence is that
count contrasts on those two scenes need to be large to resolve; the
mechanisms' main effects are, at ten to twenty-five times, and the interactions
on count are not.

---

## Review log

**Domain Researcher** — The draft described the corpus as small without
acknowledging that it spans a wide difficulty range, which overstates the
limitation in one direction while understating the acquisition-style concern.
→ *applied*: both stated, with the 7 dB span and the single acquisition style
distinguished. Second finding: the widened count dispersion was listed without
its consequence, which is what a reader needs. → *applied*: main effects
resolve, interactions do not.

**Supervisor** — The draft opened as though these limitations were being
disclosed for the first time. They have all appeared at their point of use, and
saying so changes how the section reads — as a summary rather than a
confession. → *applied*, in the opening sentence. Second: the single-repeat
entry did not name which results it affects. → *applied*: three named.

**Journal Reviewer** — The provenance entry conflated the two consequences.
→ *applied*: the implementation-state claim and the unattributable
non-replication separated, each with its section.
