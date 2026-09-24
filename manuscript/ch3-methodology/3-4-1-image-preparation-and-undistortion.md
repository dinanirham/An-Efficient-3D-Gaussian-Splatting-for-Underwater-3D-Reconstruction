---
section: "3.4.1"
title: "Image Preparation and Undistortion"
chapter: 3
action: Refine
evidence: ["CD register", "implementation"]
figures: []
tables: []
citations: ["Kerbl et al., 2023"]
status: refined
word_count: 486
---

# 3.4.1 Image Preparation and Undistortion

Preprocessing is deterministic, executed once per scene, and frozen before any
training run begins. Its output is hashed, so a run's manifest records exactly
which data it consumed and two runs claiming the same input can be shown to
have had it.

**One preparation step is a correction rather than a convention, and it is
recorded here because it changes the data every configuration trains on.** The
poses distributed with the dataset use a camera model carrying radial and
tangential distortion coefficients. The rasteriser this study builds on assumes
a pinhole projection and ignores distortion parameters entirely (Kerbl et al.,
2023). Training directly on the distributed data therefore introduces a
systematic geometric error: the optimiser is asked to reconcile images formed
under one projection with a renderer implementing another, and it does so by
deforming the geometry. No downstream mechanism can correct that, and no
fidelity metric would attribute it to its cause — it would appear as
reconstruction error and be charged to whatever configuration was being
measured.

Every scene is therefore undistorted to a pinhole model before use. The
conversion is asserted rather than assumed: the pipeline refuses to proceed if
any camera in a scene still reports a distorted model after the conversion
step. This matters because a silent failure here would be invisible
downstream — the run would complete, the metrics would be plausible, and the
error would be indistinguishable from ordinary reconstruction difficulty.

The undistortion is applied identically to every scene and every configuration,
including the unmodified reference implementation. This is worth stating
because it is a departure from training on the data exactly as distributed, and
a reader comparing this study's absolute fidelity figures against published
ones should know that both sides of every comparison in this thesis received
the same correction, while a published figure may not have. It is one reason
this study's equivalence claim (Section 3.6.2) is made against a reference
implementation run on the same prepared data rather than against a published
number.

No other image transformation is applied. Images are not resized, colour
corrected, denoised or white balanced, and no water-removal preprocessing of
any kind is performed — the medium model exists to account for the water, and
removing it beforehand would make the study's central object unmeasurable.

---

## Review log

**Domain Researcher** — The draft stated the undistortion as a preparation step
without explaining the failure it prevents, so a reader could not judge whether
it was necessary. → *applied*: the optimiser reconciles the mismatch by
deforming geometry, and the resulting error would be charged to whichever
configuration was being measured. Second finding: that the correction is also
applied to the reference was not stated, and it bears on how this study's
absolute numbers compare with published ones. → *applied*.

**Supervisor** — The draft did not say what preprocessing deliberately does
*not* do, which in an underwater study is the more surprising half — a reader
may assume some water correction is applied. → *applied*: closing paragraph,
with the reason removing the water would make the study's object unmeasurable.

**Journal Reviewer** — "Asserted rather than assumed" was used without saying
what happens on failure. → *applied*: the pipeline refuses to proceed, and the
reason a silent failure would be invisible.
