---
section: "4.2.3"
title: "Qualitative Reconstruction Characteristics"
chapter: 4
action: Add
evidence: ["renders", "FINDINGS §15"]
figures: ["figure-4-02-baseline-vs-reference", "figure-4-02b-baseline-crops"]
tables: []
citations: []
status: refined
word_count: 671
---

# 4.2.3 Qualitative Reconstruction Characteristics

The tables of Section 4.2.2 establish what the two implementations score. This
subsection establishes what they look like, and does so before any mechanism is
introduced, because several of the artefacts attributed to mechanisms in
Sections 4.3 to 4.5 are already present in the reference.

> **[FIGURE 4.2b]** `figures/chapter4/figure-4-02b-baseline-crops.pdf`
> *The reference and the baseline at far field (left) and near field (right).*
> One held-out view per scene, seed 0, at two crops. The far field is where the
> medium term dominates and the near field where geometry does. Peak
> signal-to-noise ratio is given for the view shown, not the scene mean.
> **Status:** built

Two crops are used throughout this chapter rather than one, and the reason is
physical rather than presentational. In the image formation model the observed
radiance is a medium-free radiance attenuated with depth, summed with a
backscatter term that saturates with depth. At short range the attenuation
term is near unity and the backscatter term near zero, so the near-field crop
is dominated by the reconstructed geometry and its texture. At long range the
attenuation term has decayed and the backscatter term has saturated, so the
far-field crop is dominated by the medium model, and the geometry behind it
contributes little. A mechanism that damages geometry and a mechanism that
damages the medium are therefore separable by eye, and Sections 4.4.4 and 4.5.4
use exactly this separation.

The far-field columns show how little is recoverable at range on two of the
four scenes. On IUI3 Red Sea and Japanese Gardens the far field is close to
featureless in the ground truth itself: the water has removed the signal before
it reaches the camera, and both implementations reproduce a smooth gradient
because a smooth gradient is what is there. No conclusion about representational
quality can be drawn from those panels, and none is drawn in this chapter. It
is worth stating plainly, because a reader who sees a featureless far field
beside a detailed near field may read it as a reconstruction failure when it is
a property of the scene. Curaçao and Panama retain structure at range and are
the scenes on which far-field claims in Section 4.5 are made.

The near-field columns show the two implementations to be closely comparable,
which is the qualitative counterpart of the equivalence result of Section 4.2.1.
Texture, relief and colour agree; neither implementation shows an artefact the
other lacks. The corpus's characteristic failure modes belong to both: a soft,
slightly over-smoothed rendering of fine branching structure, most visible on
Curaçao, and a loss of contrast in shadowed regions, most visible on Panama.
These are baseline properties, and where Section 4.4.4 reports that
simplification costs texture, the comparison is against this already-soft
starting point rather than against the ground truth.

One number in the figure should be read carefully, because it illustrates a
limitation rather than a result. On Japanese Gardens the reference scores
26.8 dB at the view shown and the baseline 25.0 dB, a gap of 1.8 dB. The
scene-mean difference between the two, reported in Section 4.2.1, is 0.245 dB.
A single view is therefore capable of showing a difference seven times the
scene mean in either direction, because a scene mean here is a mean over
thirteen held-out frames of very unequal difficulty. The figures in this
chapter are chosen at a fixed view index per scene and are held fixed across
every configuration, so they are comparable with one another; they are not
substitutes for the tabulated means, and no claim rests on a rendered panel
alone.

The qualitative evidence in this chapter is bounded in one further way, stated
here once. Full point clouds were retained for the first repeat only
(Section 4.1.4), so every rendered comparison shows one repeat. Where the
quantity being illustrated varies substantially between repeats — primitive
count on two scenes, and medium collapse, which is seed-conditioned — a single
rendered repeat illustrates the phenomenon without establishing its rate. The
rates are established in Sections 4.6 and 4.7 from all three repeats.

---

## Review log

**Domain Researcher** — The draft justified the two crops by saying they "show
different things", which is true and uninformative. The justification is the
image formation model: attenuation near unity and backscatter near zero at
short range, the reverse at long range. → *applied*, with the consequence that
geometry damage and medium damage become separable by eye. Second finding: the
featureless far field on two scenes would read as a reconstruction failure to a
reader unfamiliar with these datasets. → *applied*: stated explicitly, with the
two scenes on which far-field claims are made named.

**Supervisor** — The subsection originally claimed the baseline "reconstructs
the scenes well", which is an assessment the figure cannot support and which
the tables already quantify. → *applied*: replaced with the specific artefacts
both implementations share, which is what a qualitative subsection can
establish. Devil's advocate: if both implementations look alike, is the figure
worth its page? Yes — it is the visible form of the equivalence claim, and it
sets the starting point against which Section 4.4.4's texture loss is judged.

**Journal Reviewer** — A per-panel number differing from the tabulated scene
mean by a factor of seven appeared with no explanation, which a referee would
read as an inconsistency. → *applied*: own paragraph, with the fixed-view
convention and the explicit statement that no claim rests on a panel. Second:
the single-repeat limitation of every rendered figure was not stated anywhere
in the chapter's qualitative material. → *applied*: closing paragraph, with the
distinction between illustrating a phenomenon and establishing its rate.
