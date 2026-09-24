---
section: "4.12.2"
title: "Methodological Limitations"
chapter: 4
action: Refine
evidence: ["FINDINGS §14", "FINDINGS §10", "FINDINGS §15"]
figures: []
tables: []
citations: []
status: refined
word_count: 683
---

# 4.12.2 Methodological Limitations

These concern what the campaign's instruments can establish, as distinct from
how much of it was run.

**Every fidelity metric in this chapter describes the composed image.** Peak
signal-to-noise ratio, structural similarity and learned perceptual similarity
are computed against ground-truth photographs, which exist only for the
composed image. The restored image, the attenuation map and the backscatter map
have no ground truth in this corpus. Section 4.8 makes this a finding rather
than only a limitation, but it remains a limitation: no number in this chapter
measures the quality of the decomposition that the method exists to produce.

**The third axis detects failure and does not measure accuracy.** Collapse
incidence, internal consistency and physical plausibility each work without a
ground truth, which is why they are available at all, and each is correspondingly
limited. Collapse detects only outright departure from the feasible range.
Consistency establishes that something is wrong without identifying which part.
Plausibility is bounded by the depth renormalisation described below.

**The medium parameters are dimensionless with respect to a renormalised
depth.** Depth is rescaled to the unit interval per frame before reaching the
attenuation and backscatter networks, so the fitted coefficients cannot be
compared with published measurements of natural water or across scenes of
differing depth range. Only the ordering of channels within a scene is
interpretable, and every claim in Section 4.2.4 is a claim about ordering.

**The restoration measurement is a consistency check.** Section 4.5.7
establishes that two attribute states of one model differ by 17 to 27 decibels
in the restored image. It cannot say which is nearer the truth. The attribution
of the difference to the far field follows from the image formation model and
was not measured; a per-depth-bin breakdown would test it and is not in this
campaign.

**Scene means are means over very unequal views.** Held-out views within a
single run differ by 6.65 to 11.25 dB, which is 14 to 86 times the repeat
dispersion, and the hardest view is the same view in every configuration.
Because every configuration is scored on the same fixed views, comparisons
between configurations are unaffected — this is why the chapter's contrasts are
sound. What is affected is any reading of a scene mean as the typical quality
achieved on that scene. Every per-scene fidelity number in this chapter should
be read as a comparison instrument, not as an estimate of scene quality, and
Section 4.2.3 shows a rendered view where the gap between two configurations is
seven times the scene-mean difference.

**The replication is internal.** Section 4.10 compares two campaigns by the
same author using overlapping code. Agreement establishes stability under
re-execution, not independent reproduction, and a systematic error present in
both would replicate perfectly.

**Two post-hoc accounts are reported.** The characterisation of the collapse in
Section 4.7.4 and the reading of the favourable perceptual interaction in
Section 4.6.2 were both formed after seeing the data they describe. Each is
labelled at the point of use and neither is presented as a tested explanation.
They are included because withholding a description of what the diagnostics
show would be its own distortion, but a reader should weight them differently
from the pre-registered results.

---

## Review log

**Domain Researcher** — The draft treated the composed-image limitation and the
third axis as one entry. They are distinct: the first says the metrics measure
one quantity, the second says the instruments that measure the other quantity
detect rather than measure. → *applied*: separated, with each instrument's
specific limit given. Second finding: the per-view spread was reported without
its reassuring half — that comparisons are unaffected because the views are
fixed — which would leave a reader doubting the chapter's contrasts.
→ *applied*.

**Supervisor** — The draft omitted the post-hoc accounts entirely, which is the
limitation a supervisor would raise first given that the chapter withdrew a
pre-registered explanation and then offered a description in its place.
→ *applied*: named, both located, with the reason for including them at all.
Devil's advocate: does listing them here weaken Section 4.7.4? It states there
that it is post-hoc; repeating it here is consistency, not retreat.

**Journal Reviewer** — "Internal replication" needed the consequence spelled
out. → *applied*: a systematic error present in both would replicate perfectly.
Second: the renormalised-depth entry restated Section 4.2.4 without adding the
limitation it implies for Section 4.12.4's plausibility instrument.
→ *applied*: cross-referenced to the third-axis entry.
