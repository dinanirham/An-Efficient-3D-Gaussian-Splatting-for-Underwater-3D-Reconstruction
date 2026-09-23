---
section: "4.4.1"
title: "Reconstruction Fidelity per Scene"
chapter: 4
action: Rewrite
evidence: ["FINDINGS §2", "results_by_scene.csv"]
figures: ["figure-q1-a2-simplification", "figure-4-15b-configurations-vs-reference"]
tables: ["Table 4.10"]
citations: ["Fang & Wang, 2024"]
status: refined
word_count: 796
---

# 4.4.1 Reconstruction Fidelity per Scene

Spatial reorganisation prunes the primitive population to a fixed budget at two
scheduled points during training, retaining primitives by an importance
criterion and redistributing the survivors (Fang & Wang, 2024). The budget in
this campaign is 200 000 primitives, and the two events are followed by short
intervals in which only the medium parameters are optimised. This subsection
reports what the pruning costs in fidelity.

> **[TABLE 4.10]** *Spatial reorganisation against the reference, per scene.*
> Effect with z against repeat dispersion at three repeats; |z| below 2 is
> reported `UNRESOLVED`. Source: `results_by_scene.csv`.

| Scene | ΔPSNR (dB) | z | ΔLPIPS | z | Verdict |
|---|---:|---:|---:|---:|---|
| Curaçao | +0.70 | +1.4 | **+0.033** | **+8.0** | LPIPS resolved worse |
| IUI3 Red Sea | −0.11 | −0.4 | **+0.082** | **+36.1** | LPIPS resolved worse |
| Japanese Gardens | +0.28 | +0.9 | **+0.039** | **+12.3** | LPIPS resolved worse |
| Panama | −0.11 | −0.3 | **+0.057** | **+9.7** | LPIPS resolved worse |

The result is unusually clean, and the two metrics separate completely. **Peak
signal-to-noise ratio is unresolved on every scene**, with effects between
−0.11 and +0.70 dB and no z exceeding 1.4; the mechanism is radiometrically
indistinguishable from the published reference across the corpus. **Learned
perceptual similarity is worse on every scene, and resolved on every scene**,
at 8 to 36 standard errors. There is no scene on which this mechanism is
perceptually free.

The magnitude of the perceptual cost varies fivefold across the corpus, from
0.033 on Curaçao to 0.082 on IUI3 Red Sea, and every value exceeds the ±0.02
margin this thesis pre-registered as the threshold for equivalence on that
metric. Where deterministic initialisation was perceptually free on two scenes
of four (Section 4.3.1), this mechanism is free on none. That is the sharpest
fidelity distinction between the two mechanisms, and it is not visible in the
pixel metric at all.

The comparison with the factorial contrast is more consequential here than it
was for the previous mechanism, and it runs in the direction Section 4.1.3
predicted. Measured against the unmodified configuration, this mechanism's
pixel-metric effect **resolves positive on two scenes** — Curaçao at +0.74 dB
and Japanese Gardens at +0.53 dB. Measured against the reference it resolves on
none. The effects themselves are close to identical; the reference is the
noisier comparator on peak signal-to-noise ratio, and the same effect no longer
clears the threshold. A reader encountering only the factorial numbers could
reasonably conclude that pruning to a fixed budget *improves* radiometric
fidelity on half the corpus. Against the published method, the defensible
statement is that it changes it undetectably. Both are reported, and this
chapter treats the second as the one a practitioner should act on, because the
published method is what they would be replacing.

> **[FIGURE Q1-A2]** `figures/chapter4/figure-q1-a2-simplification.pdf`
> *Spatial reorganisation against the reference and the baseline.* Near-field
> crop of one held-out view per scene, seed 0, with ground truth, the
> reference, the unmodified configuration and the mechanism in that order.
> Each panel carries the peak signal-to-noise ratio and learned perceptual
> similarity of the view shown. An accent border marks a run that lost an
> attenuation channel.
> **Status:** built · **Anchored on:** SS

The perceptual cost is the mechanism's principal fidelity finding, and it is
also the point at which the two metrics' disagreement stops being a curiosity
and becomes a practical problem. A configuration that is radiometrically
indistinguishable from the published method on all four scenes, and
perceptually worse than it on all four, cannot be summarised by either metric
alone. Section 4.4.4 shows what the perceptual cost looks like, and Section
4.4.5 argues that the character of the loss — high-frequency texture, not
structure — is what makes the two metrics diverge so completely here.

One feature of Figure Q1-A2 should be noted now and is developed in
Section 4.4.3. On Japanese Gardens the mechanism's panel carries an accent
border: that run lost an attenuation channel. Its peak signal-to-noise ratio at
the view shown is 24.8 dB against the unmodified configuration's 25.0 dB, and
the two panels are not distinguishable by eye. A medium-model failure has
occurred in a run whose fidelity numbers are unremarkable, which is the finding
Section 4.8 establishes at scale and the reason this chapter reports a third
evaluation axis at all.

---

## Review log

**Domain Researcher** — The draft described the mechanism as "pruning", which
omits the redistribution of survivors and the medium-only intervals that follow
each event, both of which matter for Section 4.7. → *applied*: described as
executed, with the budget and the two events named and the citation given.
Second finding: the draft compared the perceptual cost across scenes without
relating it to the pre-registered equivalence margin, leaving the reader without
a scale. → *applied*: every value exceeds ±0.02, stated.

**Supervisor** — The draft reported the anchor discrepancy neutrally — "two
scenes against A0, none against SS" — and left the reader to decide which
matters. For this mechanism the difference is the difference between claiming
an improvement and claiming no detectable change, which is too large to leave
open. → *applied*: both reported, with an explicit statement of which a
practitioner should act on and why. Devil's advocate: is preferring the
reference comparison here motivated by it being the less flattering one? The
justification is stated and is not about flattery — the published method is
what a practitioner would be replacing.

**Journal Reviewer** — The collapsed-run panel appeared in the figure with an
accent border explained only in the caption, while the body text made no
mention of it, which would read as an unexplained annotation.
→ *applied*: closing paragraph, with the two peak signal-to-noise values and a
forward reference. Second: "unusually clean" was an editorial judgement without
support. → *applied*: retained but immediately substantiated by the complete
separation of the two metrics.
