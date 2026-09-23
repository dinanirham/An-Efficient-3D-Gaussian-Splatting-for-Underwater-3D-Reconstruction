---
section: "4.5.6"
title: "Boundary"
chapter: 4
action: Add
evidence: ["FINDINGS §14", "FINDINGS §10", "FINDINGS §0"]
figures: []
tables: []
citations: []
status: refined
word_count: 528
---

# 4.5.6 Boundary

What this section does not establish.

**One codebook size.** The mechanism was run at a single codebook
configuration, applied to three attributes from one fixed iteration onward.
Nothing here establishes the rate–distortion behaviour of the method, which
would require sweeping codebook size and is the obvious follow-up the campaign
does not provide. The 2.72-fold ratio is one point on a curve this thesis does
not draw, and Section 4.6.6 reports operating points across configurations
rather than a rate–distortion analysis, for the same reason.

**No compression figure against the published method.** The reference records
no stored size, so every storage result here is against the unmodified
configuration (Section 4.5.2). That configuration is equivalent to the
reference within a ±30 % count margin, not identical to it, so the compression
ratio does not transfer directly to the published method.

**The restoration result is consistency, not accuracy.** Section 4.5.7
establishes that two attribute states of one model produce restored images 17
to 27 dB apart. It cannot establish which is nearer the true medium-free image,
because no ground truth for that image exists in this corpus. Any reading of
that section as showing quantisation *degrades* the restoration goes beyond the
evidence; what it shows is that the restoration is not determined by what the
training objective constrains.

**One repeat for the restoration result.** The sixteen runs of Section 4.5.7
are the first repeat of each configuration and scene, because full point clouds
were retained for that repeat alone. The result carries no dispersion, is not
resolved against the thresholds of Section 4.1.3, and is reported as secondary
throughout.

**Far-field attribution is inferred, not measured.** The account in Section
4.5.5 — that the restoration moves where the attenuation factor is small —
follows from the image formation model and is consistent with the far-field
appearance in Figure 4.8. It was not measured. A per-depth-bin breakdown of
where the two restorations disagree would test it directly and is not in this
campaign.

**Fidelity resolution.** The mechanism's effects are `UNRESOLVED` on both
metrics on three scenes of four. At three repeats that is a statement about
what this design can separate, not a measurement of zero, and the neutrality
claimed in Section 4.5.5 is neutrality at this resolution.

**One scene carries the only resolved loss.** The 1.21 dB and 0.028 costs are
on IUI3 Red Sea alone, and that scene is anomalous on four other counts
(Section 4.12.4). Whether the loss is a property of the mechanism meeting a
poorly conditioned scene, or of that scene alone, is not separable here.

---

## Review log

**Domain Researcher** — The draft omitted the codebook-size limitation, which
is the first thing a referee would raise about a compression result: one
operating point is not a rate–distortion characterisation. → *applied*, placed
first. Second finding: the consistency-versus-accuracy limit was in Section
4.5.7 but not restated here, and this subsection is where a reader checks what
the section did not do. → *applied*, with the specific misreading named.

**Supervisor** — The draft repeated Section 4.4.6 on the corpus limitation.
→ *applied*: dropped, since Section 4.12 carries it, and the space used for the
two limits specific to this mechanism — the missing anchor for storage and the
single-repeat restoration result. Second: the IUI3 entry originally asserted the
scene was the cause. → *applied*: stated as not separable.

**Journal Reviewer** — "Unresolved" was used as though synonymous with neutral
in one entry. → *applied*: neutrality is now explicitly qualified as
neutrality at this resolution. Second: the inferred far-field attribution needed
to name the measurement that would test it. → *applied*.
