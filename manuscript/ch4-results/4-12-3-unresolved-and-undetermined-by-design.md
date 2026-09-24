---
section: "4.12.3"
title: "Unresolved and Undetermined by Design"
chapter: 4
action: Add
evidence: ["FINDINGS §14", "FINDINGS §0"]
figures: ["figure-4-01-resolution"]
tables: []
citations: []
status: refined
word_count: 626
---

# 4.12.3 Unresolved and Undetermined by Design

This subsection enumerates the quantities this design cannot separate from
repeat dispersion. It exists because `UNRESOLVED` appears throughout the
chapter and is easy to misread, and because a reader is entitled to see the
full extent of what the design could not resolve in one place rather than
distributed across ten sections.

**The label means one thing throughout: not separable from repeat dispersion at
three repeats.** It does not mean the effect is absent, and no argument in this
chapter treats it as though it did. An unresolved effect and a zero effect are
not distinguishable in this design, and where a chapter claim would change under
either reading, that is stated at the claim.

**Undetermined by construction.** Every peak signal-to-noise ratio interaction,
two-way and three-way, in Sections 4.6.2 to 4.6.5. The smallest resolvable PSNR
interaction is 0.51 to 1.61 dB depending on scene, against a largest PSNR main
effect of 0.80 dB, so no interaction on that metric can be resolved whatever
its true magnitude. This is a property of the design and was identified before
the analysis rather than discovered in it. Several such terms nonetheless
exceed two standard errors, and their signs flip from scene to scene within
every pair, which is the pattern expected of noise at the limit.

> **[FIGURE 4.1]** `figures/chapter4/figure-4-01-resolution.pdf`
> *Resolvable effect size against observed effect size, per scene.* The
> threshold for each contrast order against the observed main effects.
> **Status:** built

**Unresolved at three repeats.** Peak signal-to-noise ratio main effects
against the reference on ten of twelve scene–mechanism pairs (Sections 4.3.1,
4.4.1, 4.5.1); the gradient-detachment pixel-metric effect on all four scenes,
every value under 1.1 standard errors (Section 4.9.2); every count interaction
beyond the initialisation-simplification pair (Sections 4.6.3 to 4.6.5); the
three-way term on count everywhere and on perceptual similarity on three scenes
of four (Section 4.6.5).

**Unresolved across campaigns.** Attribute-level quantisation's pixel-metric
effect on IUI3 Red Sea. It resolves within this campaign at −1.21 dB against
the reference and reverses sign against the archived campaign, where it was
+0.35 dB (Section 4.10.1). The scene finding rests on perceptual similarity,
which replicates on all sixteen comparisons.

**Unpredictable at this instrument set.** Which repeat of a large-cut
configuration loses a channel. Every pre-cut covariate tested gives an area
under the curve of 0.65 or below against 0.5 for a predictor with no power
(Section 4.7.4). The collapse is reproducible as a rate and not as an event,
and this is a limitation of the instruments available rather than evidence that
no predictor exists.

**Not established, as distinct from unresolved.** Three items belong in a
different category because no measurement was attempted rather than because a
measurement failed to separate: the accuracy of any restored image, the causal
role of the medium-only interval, and which of deterministic initialisation's
three simultaneous consequences protects the medium. These are recorded in
Section 4.11.3 and are not resolution failures.

---

## Review log

**Domain Researcher** — The draft mixed quantities that failed to resolve with
quantities never measured, which are different kinds of gap and invite
different responses — more repeats against a new instrument. → *applied*: a
final category separating the two explicitly. Second finding: the
undetermined-by-construction entry did not say the property was identified in
advance, which is what distinguishes it from a post-hoc excuse. → *applied*.

**Supervisor** — The draft was an inventory with no statement of what the
reader should do with it. → *applied*: the opening now says why the section
exists, and the meaning of the label is restated once at the top rather than
assumed. Devil's advocate: does enumerating this much unresolved material
undermine the chapter? The resolved results are listed in Section 4.11.2 and
are substantial; a reader who can see both lists can judge, and one who is
shown only the first cannot.

**Journal Reviewer** — "Ten of twelve" needed to agree with Section 4.11.2,
where the same count is now stated. → *applied*, both corrected together.
Second: the unpredictability entry read as a finding about the phenomenon
rather than about the instruments. → *applied*.
