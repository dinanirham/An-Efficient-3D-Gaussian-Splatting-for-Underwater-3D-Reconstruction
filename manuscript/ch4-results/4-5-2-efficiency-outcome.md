---
section: "4.5.2"
title: "Efficiency Outcome"
chapter: 4
action: Refine
evidence: ["FINDINGS §2", "FINDINGS §12", "results_by_scene.csv"]
figures: ["figure-4-18-fps-vs-count"]
tables: ["Table 4.14"]
citations: []
status: refined
word_count: 788
---

# 4.5.2 Efficiency Outcome

This mechanism's target cost is stored size, and it is the one axis on which
the published reference cannot serve as the anchor.

**The exception, stated where it applies.** The reference implementation does
not record stored size: neither `total_bytes` nor `bytes_per_primitive` appears
in its results. Every other comparison in this chapter is made against the
reference, as Section 4.1.2 sets out; this one cannot be, and is made against
the unmodified configuration instead. That is a sound comparison — the two
differ by this mechanism alone — but it is a different comparison from the rest
of the chapter, and any reading of this subsection alongside Sections 4.3.2 and
4.4.2 must account for the change of anchor. The consequence is narrow and
worth naming: this thesis cannot state how much smaller a quantised model is
than the published method, only how much smaller it is than an implementation
shown equivalent to the published method within a ±30 % count margin
(Section 4.2.1).

> **[TABLE 4.14]** *Storage under attribute-level quantisation, against the
> unmodified configuration, per scene.* Bytes per primitive is deterministic
> given the attribute layout. Source: `results_by_scene.csv`.

| Scene | Bytes/primitive A0 | Bytes/primitive A3 | Total MB A0 | Total MB A3 | Total ratio |
|---|---:|---:|---:|---:|---:|
| Curaçao | 56.0 | 20.6 | 215.4 | 66.1 | 0.307 |
| IUI3 Red Sea | 56.0 | 20.6 | 150.3 | 48.4 | 0.322 |
| Japanese Gardens | 56.0 | 20.6 | 140.0 | 44.3 | 0.317 |
| Panama | 56.0 | 20.6 | 106.1 | 46.1 | 0.435 |

**Bytes per primitive falls from 56.0 to 20.6 on every scene, a factor of
2.72.** This figure is identical to three significant figures across all twelve
runs, and it is not a measurement in the sense the rest of this chapter uses the
word. It is determined by the attribute layout: with spherical-harmonic degree
zero each primitive carries fourteen floating-point values, three of which are
replaced by codebook indices, and the resulting size follows arithmetically. It
is reported as a structural fact rather than as a tested effect, and it carries
no uncertainty because there is none to carry. A prediction to this effect was
registered before the measuring instrument existed, and it holds.

Total stored size falls to between 0.307 and 0.435 of the unmodified
configuration. This ratio is *not* constant where bytes per primitive is,
because total size is the product of bytes per primitive and a primitive count
that varies from run to run. Panama's 0.435 is the outlier and reflects that
configuration finishing with more primitives than its comparator on that scene,
not weaker compression. Where a reader wants the mechanism's effect, bytes per
primitive is the figure; where they want the file on disk, the total is, and
the total carries the count's dispersion with it.

**The mechanism changes no frame rate.** Against the reference the render-rate
ratios are 1.22, 0.91, 0.96 and 0.85, and none resolves at three repeats. The
primitive count is likewise unchanged, with ratios between 0.789 and 1.120 and
none resolved. This is the expected result and it was registered in advance:
the codebooks are decoded before rasterisation, so the rendering path sees the
same number of primitives with the same attributes it would otherwise have had,
and no part of the frame cost is avoided. Section 4.4.2 established that frame
rate scales weakly even with primitive count; a mechanism that does not change
the count has no route to changing the rate at all.

The three mechanisms therefore target genuinely disjoint costs, which matters
for Section 4.6. Deterministic initialisation reduces the population by never
growing it; spatial reorganisation reduces the population by cutting it; this
mechanism leaves the population alone and reduces what each member costs to
store. Only the first two can interact on count, and only this one moves stored
bytes.

One consequence for Figure 4.15b should be stated so the figure is not
misread. On the count panel this mechanism sits at a ratio of approximately one
and is unresolved on every scene, which makes it appear inert beside the other
two. It is not inert; its axis is absent from that figure, because the
reference records no stored size and the figure is anchored on the reference.
Table 4.14 is where this mechanism's efficiency result lives.

---

## Review log

**Domain Researcher** — The draft reported the 2.72× compression as a measured
effect with the other results. It is arithmetic given the attribute layout and
carries no uncertainty, and presenting it as a measurement invites a referee to
ask for its confidence interval. → *applied*: reported as a structural fact,
with the fourteen-float layout and the registered prediction. Second finding:
the draft did not explain why the total ratio varies when bytes per primitive
does not. → *applied*, with Panama named as the case.

**Supervisor** — The anchor exception was a sentence in the middle. It is the
one place in the chapter where the chapter's own stated convention does not
hold, and it belongs at the top, with the consequence spelled out.
→ *applied*: opens the subsection, and states precisely what the thesis
therefore cannot claim. Devil's advocate: is the exception fatal to RQ1 for
this mechanism? No, but it is a real gap — the honest form is that the
comparison is against an implementation shown equivalent within a stated
margin, which is weaker than a direct comparison and is now written that way.

**Journal Reviewer** — Frame-rate and count ratios were described as unchanged
without the values or their resolution status. → *applied*: all four ratios
given for each, with `UNRESOLVED` stated. Second: Figure 4.15b shows this
mechanism as apparently inert, and nothing warned the reader.
→ *applied*: closing paragraph.
