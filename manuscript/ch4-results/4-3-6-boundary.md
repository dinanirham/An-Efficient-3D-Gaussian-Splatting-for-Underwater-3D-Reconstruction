---
section: "4.3.6"
title: "Boundary"
chapter: 4
action: Add
evidence: ["FINDINGS §14", "FINDINGS §0"]
figures: []
tables: []
citations: []
status: refined
word_count: 476
---

# 4.3.6 Boundary

Each mechanism section closes by stating what it does not establish. The
purpose is to make the limits of a result travel with the result, rather than
accumulate in a terminal section a reader may reach after forming a view.

**One operating point.** The mechanism was run at a single configuration of the
correspondence stage, producing final populations between 197 000 and 243 000
primitives. Nothing here establishes how the mechanism behaves at a larger or
smaller initial cloud, and in particular nothing establishes whether the
perceptual cost on IUI3 Red Sea would be removed by a denser initialisation.
That is the most obvious follow-up the campaign does not answer, and it is
carried to Section 5.4 as future work rather than speculated about here.

**Four scenes, one corpus.** All four scenes come from one dataset with a
common acquisition style. The mechanism's behaviour on scenes with wider
baselines, more views, or different water is untested. The association drawn in
Section 4.3.5 between view coverage and the perceptual cost rests on one scene
being the extreme of both, which is a sample of one.

**Resolution.** At three repeats, an effect smaller than roughly 0.5 dB in peak
signal-to-noise ratio is not separable from repeat dispersion on most scenes
(Section 4.1.3). The mechanism's pixel-metric effect against the reference
resolves on one scene of four; the other three are `UNRESOLVED`, which means
not separable at this n and not that the effect is zero. Any reading of this
section that treats the three unresolved scenes as showing no effect is a
misreading.

**Render rate is not a target cost.** The mechanism's 1.25 to 2.25 times rate
improvement follows from the smaller population. It is not evidence about the
rendering path, which the mechanism does not touch, and Figure 4.18 shows the
relationship between population and rate to be strongly sub-linear and
scene-dependent.

**Medium behaviour in isolation only.** Section 4.3.3 reports that the
mechanism loses no attenuation channel. Because the reference loses none
either, this establishes nothing about protection. The protective result
belongs to the combination with spatial reorganisation and is established in
Section 4.7.

**One repeat for everything visual and geometric.** The rendered comparisons,
the visible-fraction figures and the bounding-box observations all rest on the
first repeat, because full point clouds were retained for that repeat alone
(Section 4.1.4). These quantities are reported without dispersion and no
resolution claim is made for any of them.

**The implementation, not the published method.** As Section 4.3.5 records, the
source implementation predates its paper and contains behaviour the paper does
not describe. Results here concern that implementation composed into this
estimator.

---

## Review log

**Domain Researcher** — The draft omitted the operating-point limitation, which
is the first thing a referee in this area would raise: a single initial cloud
size cannot support a claim about the mechanism, only about that setting.
→ *applied*, and placed first. Second finding: the render-rate boundary was
absent, and without it Section 4.3.2's rate figure reads as a property of the
mechanism. → *applied*.

**Supervisor** — The draft listed limitations without saying why a boundary
subsection exists at all, which made it look like a disclaimer. → *applied*:
opening sentence states the purpose — limits travel with results. Second: two
entries restated Section 4.12 verbatim. → *applied*: each entry is now specific
to this mechanism, with the general limitations left to Section 4.12.

**Journal Reviewer** — `UNRESOLVED` was used without restating what it means,
in a subsection a reader may consult in isolation. → *applied*, with the
explicit warning against the misreading. Second: the future-work pointer was
phrased as a suggestion; it should name the destination section.
→ *applied*: Section 5.4.
