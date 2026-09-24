---
section: "3.3.2"
title: "Scene Composition and Characteristics"
chapter: 3
action: Refine
evidence: ["FINDINGS §0", "FINDINGS §2", "results_by_scene.csv"]
figures: ["figure-4-02b-baseline-crops"]
tables: ["Table 3.4"]
citations: []
status: refined
word_count: 668
---

# 3.3.2 Scene Composition and Characteristics

The four scenes are not four samples of one problem. They differ enough that
this study reports every result per scene and never pools across them, and this
subsection gives the evidence for that decision before Chapter IV relies on it.

> **[TABLE 3.4]** *Scene characteristics as measured by the reference
> implementation.* Fidelity and population are means over three repeats;
> dispersion is the standard deviation over those repeats. Source:
> `results_by_scene.csv`.

| Scene | PSNR (dB) | LPIPS | Primitives | PSNR dispersion | Count dispersion |
|---|---:|---:|---:|---:|---:|
| Curaçao | 29.91 | 0.183 | 4 276 736 | 0.733 | 17.2 % |
| IUI3 Red Sea | 27.50 | 0.208 | 3 077 310 | 0.434 | 19.5 % |
| Japanese Gardens | 22.95 | 0.179 | 2 036 893 | 0.455 | 7.4 % |
| Panama | 28.69 | 0.146 | 2 100 267 | 0.539 | 27.9 % |

Three features of this table govern how results are reported.

**Reconstruction difficulty spans approximately 7 dB.** A mechanism effect of a
few tenths of a decibel is therefore an order of magnitude smaller than the
difference between the easiest scene and the hardest. A fidelity figure
averaged over the corpus would be dominated by which scenes were included
rather than by what the mechanism did, and this is the arithmetical reason for
the per-scene convention of Section 3.8.3.

**The two fidelity metrics rank the scenes differently.** By peak
signal-to-noise ratio the order is Curaçao, Panama, IUI3 Red Sea, Japanese
Gardens; by perceptual similarity it is Panama, Japanese Gardens, Curaçao, IUI3
Red Sea. Japanese Gardens is the worst scene by a wide margin on the pixel
metric and mid-ranked on the perceptual one. The two are not measuring the same
property, and where they disagree this study reports the disagreement rather
than selecting the metric that resolves it.

**Representation size varies by a factor of two, and its dispersion by a factor
of four.** Curaçao converges to twice the population of Japanese Gardens, and
repeat-to-repeat variation in final count ranges from 7 per cent to 28 per cent
on the reference and reaches 34 and 37 per cent on two scenes under the
unmodified configuration (Section 4.1.3). Any count contrast must therefore be
judged against a per-scene dispersion that differs substantially between
scenes.

One characteristic is not captured by any column of the table and is the most
consequential of all. **On two scenes the far field carries almost no
recoverable signal.** On IUI3 Red Sea and Japanese Gardens the water has
removed the image content before it reaches the camera, so the far field of the
ground truth itself is close to a smooth gradient. Far-field claims in this
study are therefore made on Curaçao and Panama, which retain structure at
range, and the qualitative comparisons of Section 3.7.4 use two crops per scene
for this reason.

> **[FIGURE 3.4]** `figures/chapter4/figure-4-02b-baseline-crops.pdf`
> *The reference at far field and near field, one view per scene.* The far
> field is where the medium term dominates and the near field where geometry
> does; on two scenes the far field carries little recoverable content in the
> ground truth itself.
> **Status:** built

Nothing in this subsection is a result. It describes the corpus as the
reference implementation reconstructs it, in order to justify three reporting
decisions — per scene rather than pooled, both fidelity metrics rather than
one, and two crops rather than one — that Chapter IV then applies without
re-arguing.

---

## Review log

**Domain Researcher** — The draft characterised the scenes qualitatively —
"turbid", "moderate visibility" — which is the dataset's own description and
not a measurement. A methodology chapter that will report per-scene results
needs the measured characteristics. → *applied*: the table is now reference
measurements with dispersion, and the qualitative description stays in Section
3.3.1 where it belongs. Second finding: the featureless far field on two scenes
was not recorded anywhere in the methodology, though it determines the crop
convention. → *applied*.

**Supervisor** — The draft presented scene differences as context. They are the
justification for three reporting decisions that Chapter IV applies throughout,
and framing them that way makes the subsection do work rather than set scene.
→ *applied*, with the three decisions named in the closing paragraph. Devil's
advocate: is it circular to justify a methodology decision with measurements
from the campaign that decision governs? The measurements are of the reference
implementation, which is not a configuration under test, so no contrast is
being used to justify its own treatment.

**Journal Reviewer** — Dispersion was quoted for the reference here and for the
unmodified configuration in Chapter IV, with no indication that the two differ.
→ *applied*: the table is labelled as the reference's, and the higher figures
under A0 are cross-referenced. Second: the figure was built and uncited.
→ *applied*.
