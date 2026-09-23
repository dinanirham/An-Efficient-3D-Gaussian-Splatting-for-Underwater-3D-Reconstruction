# Writing protocol — how every subsection of this thesis is composed

**Status:** authoritative. Governs every drafting task from 2026-09-24 onward.
Merged into `THESIS.md` §22. Supersedes ad-hoc drafting instructions in
`chapter-04-specification.md`, which remains authoritative for Chapter IV's
*content* but not for its *process*.

---

## 1. What this document is for

The campaign is finished and the evidence is frozen. What remains is writing,
and writing is where a defensible result becomes an indefensible thesis: by
overclaiming, by citing what was not read, by presenting a figure the data does
not support, or by burying the finding that matters under the finding that was
easy to compute.

This protocol exists so that none of that happens by accident. It defines one
unit of work, one composition loop, and three standing reviewers.

## 2. The unit of work is one subsection

**One subsection = one Markdown file = one deliverable.** Not one chapter, not
one section. A subsection is small enough to hold in view and large enough to
make an argument.

```
manuscript/
  ch1-introduction/
    1-1-1-underwater-reconstruction-and-applications.md
    1-1-2-radiance-fields-and-explicit-primitives.md
    ...
  ch4-results/
    4-7-3-dense-initialisation-protects-the-medium.md
    ...
```

Each file is a complete, readable passage of continuous prose — **paragraphs,
not bullets**. Bullets are permitted only inside a subsection that is genuinely
a list (a scope statement, a limitations enumeration). A subsection that is
mostly bullets has not been written; it has been outlined.

Target length: 300–900 words of body prose. Below 300 the subsection is not
carrying its own weight and should be merged upward. Above 900 it is two
subsections.

### File format

Every deliverable opens with a fenced metadata block, then the prose.

````markdown
---
section: "4.7.3"
title: "Dense Initialisation Protects the Medium"
chapter: 4
action: Add
evidence: ["FINDINGS §5c", "RQ3", "H6"]
figures: ["figure-4-13-collapsed-medium"]
tables: ["Table 4.14"]
citations: ["Fang & Wang, 2024"]
status: draft | reflected | reviewed | refined | final
word_count: 0
---

Prose begins here.
````

`status` advances only through the loop in §3. A file may not be marked `final`
while any `[CITE-NEEDED]`, `[DATA-NEEDED]` or `[TODO]` marker remains in it.

## 3. The composition loop

Every subsection passes through four passes. **The passes are not optional and
are not merged.** Writing and judging the writing are different cognitive acts,
and doing them at once produces prose that is defended rather than improved.

### Pass 1 — Draft

Write the argument through, start to finish, without stopping to polish. Get
the claim, the evidence and the qualification onto the page in that order.
Resist the urge to hedge while drafting; hedging is added deliberately in
Pass 4, where it can be calibrated against what the evidence actually supports.

### Pass 2 — Reflect

Put the draft beside its evidence and check the correspondence, not the prose:

- Does every number in the text appear in the cited artefact, to the same
  precision and sign?
- Does every claim's strength match its resolution status? `UNRESOLVED` is not
  zero. `UNDETERMINED` is not "no effect".
- Is anything asserted here that the design cannot establish?
- Is the qualification present in the same paragraph as the claim, rather than
  deferred to a limitations section the reader may not reach?

Reflection produces a list of corrections, not a rewrite.

### Pass 3 — Review

The three personas of §4 read the corrected draft, **in order**, each leaving
written findings. Their findings are recorded in the deliverable's review log
(§5), not silently applied.

### Pass 4 — Refine

Apply the review findings. Where a finding is rejected, record why in the
review log. A rejected finding is legitimate — reviewers are sometimes wrong —
but an unrecorded rejection is not.

Refinement is also where prose quality is addressed: sentence rhythm,
paragraph openings that state the point rather than approach it, transitions
that carry an argument rather than announce one.

## 4. The three personas

These are standing reviewers, applied to every subsection. They are read in
order because each depends on the one before: there is no point reviewing the
prose of a claim that is scientifically wrong, and no point formatting a
passage whose argument does not flow.

### 4.1 The Domain Researcher

*A top-tier researcher in 3D Gaussian splatting, novel view synthesis, 3D
reconstruction, and underwater image formation. Has published in this exact
area and has refereed for CVPR and TOG.*

Reads for scientific correctness and for whether the work earns its claims.
Asks:

- Is the mechanism described as it actually behaves, or as its source paper
  advertises it? (This thesis measures an *implementation*, and in at least one
  case the implementation and the paper disagree.)
- Is the image formation model stated correctly, and are the learned medium
  parameters interpreted within what a per-frame renormalised depth permits?
- Would a reader who knows this literature find the comparison fair — the same
  views, the same conventions, the same number of repeats?
- Is the novelty claim the right size? Efficiency alone is a crowded field; the
  contribution here is the coupling between efficiency and medium
  identifiability, and the blindness of fidelity metrics to it.
- Is anything here a well-known result presented as a finding?

### 4.2 The Supervisor

*The thesis supervisor. Reads for writing flow, clarity of argument, and
structural soundness. Takes the devil's advocate position deliberately when a
passage is too comfortable.*

Asks:

- Does the subsection open by stating what it will establish, rather than by
  recapping what came before?
- Is there one argument here, or three tangled together?
- Where is the weakest sentence, and is it weak because the thought is weak?
- What would a hostile examiner attack first, and does the text meet that
  attack or avoid it?
- Is a negative or inconvenient result being softened by word choice?
- Does the reader know, at the end, what changed in their understanding?

The Supervisor has explicit licence to argue the opposite case. If a passage
claims dense initialisation protects the medium, the Supervisor argues it does
not — and the passage must survive that or be weakened until it does.

### 4.3 The Journal Reviewer

*A reviewer for a Q1 venue. Reads for formatting, reporting standards, and
whether the manuscript would survive desk review.*

Asks:

- Are all statistics reported with the quantity, the uncertainty, the n, and
  the test? Is every p-value accompanied by the test that produced it?
- Is every figure and table called out in the text, numbered in order of
  appearance, and captioned so it stands alone?
- Are citations in APA 7th, present in the reference list, and — critically —
  actually read? (See §6.)
- Are abbreviations defined at first use in the chapter?
- Is the tense consistent: past for what was done, present for what the data
  show?
- Would a reader be able to reproduce this from the text and the repository?

## 5. The review log

Each deliverable carries its review log at the foot of the file, below a
horizontal rule. It is part of the working document and is stripped only at
final assembly.

```markdown
---
## Review log

**Domain Researcher** — Interprets β magnitudes as physical. Depth is
renormalised per frame; only within-scene channel ordering is comparable.
→ *applied*: magnitude claims removed, ordering claim retained.

**Supervisor** — Opens with a recap of 4.7.2. Cut the first two sentences and
begin at the result. → *applied*.

**Journal Reviewer** — "p = 0.0016" without the test. → *applied*: named as
Fisher exact, two-sided, with the 2×2 table.
```

## 6. Citation discipline

**A citation asserts that the cited work says what you claim it says.** In a
thesis whose own contribution is that claims must be checkable, an unread
citation is a self-inflicted wound.

The controlled register is the reference list in
`new-revisited-writing/chapter-3-methodology.md` §"Sources cited in this
chapter" — twelve entries, all in APA 7th, all already carrying the warning
that author names and venues need verification against the PDFs before
submission.

Rules:

1. **Cite only from the register.** A work not in the register may be cited
   only after it is added to the register, which requires having the paper.
2. **Anything else is marked `[CITE-NEEDED: claim]`** in the text. These are
   visible, greppable, and block `final` status. They are not placeholders to
   be quietly resolved by plausible-looking references.
3. **Never invent a citation**, and never infer an author, year, venue, or DOI
   that has not been seen. A fabricated reference found at viva is fatal.
4. Chapter II §2.6.1 per-paper breakdowns remain **blocked** — the source
   reading is not in the repository — and that block is honest and stays
   visible until the reading is done.

In-text form is APA 7th: `(Kerbl et al., 2023)` narratively, or
`Kerbl et al. (2023) showed…`. Direct quotation requires a page number.

## 7. Figures and tables

Every figure and table gets a placeholder at its point of first mention, in
this exact form:

```markdown
> **[FIGURE 4.13]** `figures/chapter4/figure-4-13-collapsed-medium.pdf`
> *A lost attenuation channel — Japanese Gardens.* One scene and view across
> three configurations — the reference, the unmodified configuration, and the
> collapsed simplification run — as attenuation map and restored image. The
> collapsed attenuation map is unmistakable; the composed images the metrics
> score are not.
> **Status:** built · **Anchored on:** SS
```

Rules:

- **If the asset exists, the placeholder names its real path** and the caption
  is the final caption. `figures/chapter4/` currently holds 34 built figures.
- **If it does not exist, the status is `[DATA-NEEDED]`** with one line saying
  what would have to be collected. It is never described as though built.
- Captions stand alone. A reader who reads only figures and captions should get
  the argument.
- Every number quoted in a caption must appear in the artefact it describes.
- Tables are authored in Markdown in the deliverable and converted at assembly.

## 8. Reporting conventions inherited from the campaign

These are not stylistic. They are the conditions under which the numbers mean
what they say, and they were settled before the analysis.

- **Evaluation is anchored on SS**, the published reference. The one exception
  is stored size, which SS does not record, and which is therefore reported
  against A0 with that stated at the point of use. See
  `research-questions-revised.md`.
- **An effect is resolved** when its 2 SE interval excludes the null, against
  per-scene repeat dispersion at n = 3. `UNRESOLVED` means not separable at
  three repeats — it does not mean zero, and must never be written as though
  it does.
- **PSNR interactions are `UNDETERMINED` by construction.** The smallest
  resolvable interaction is 0.51–1.61 dB against a largest main effect of
  0.80 dB. This is a property of the design, and every mention says so.
- **β magnitudes are dimensionless** with respect to a per-frame renormalised
  depth. Channel ordering within a scene is comparable; magnitudes across
  scenes are not physical quantities.
- **Every fidelity metric in this thesis describes Î**, the composed image. The
  decomposition into Ĵ and the medium is not something PSNR, SSIM or LPIPS can
  check, and §4 of the results says so explicitly rather than leaving it
  implied.
- **Negative and inconvenient results appear in the body**, at the point where
  they bear on the claim, not in a terminal limitations dump. The withdrawn
  dispersion explanation (FINDINGS §5b) and the two failed pre-check
  predictions (§10) are part of the record.

## 9. Definition of done

A subsection is `final` when all of the following hold:

1. All four passes are complete and the review log records each persona.
2. No `[CITE-NEEDED]`, `[DATA-NEEDED]`, `[TODO]` markers remain.
3. Every number traces to a named artefact; every figure path resolves.
4. Claim strength matches resolution status throughout.
5. Word count is within 300–900, or the deviation is justified in the log.
6. The subsection reads as continuous prose.

A chapter is `final` when every subsection is `final`, the figures are numbered
in order of first mention, and the chapter has been read once end to end for
flow — a reading that belongs to the Supervisor persona and is logged at
chapter level.

## 10. Order of work

Per `THESIS.md` §6 the highest-severity chapter is III, which describes an
implementation that was never executed. But Chapter IV now has approved
research questions, a complete evidence base and 34 built figures, and the
material is fresh.

The order is therefore: **IV → III → V → I → II.** Chapter IV first because it
is ready and because every other chapter's claims are downstream of it; III
next because it is the most wrong; V then follows from IV directly; I and II
last, because an introduction should be written once the thing it introduces
exists. Chapter II §2.6.1 stays blocked throughout.
