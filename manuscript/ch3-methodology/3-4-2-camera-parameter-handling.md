---
section: "3.4.2"
title: "Camera Parameter Handling"
chapter: 3
action: Retain
evidence: ["CD register", "implementation"]
figures: []
tables: []
citations: ["Schönberger & Frahm, 2016"]
status: refined
word_count: 452
---

# 3.4.2 Camera Parameter Handling

Camera poses are taken as distributed with the dataset, having been recovered
by structure from motion (Schönberger & Frahm, 2016). They are not re-estimated
for this study, and no pose refinement is performed during training.

That decision has a consequence worth stating plainly. Any error in the
distributed poses is common to every configuration in this campaign, including
the reference implementation, and therefore cancels from every contrast this
thesis reports. It does not cancel from the absolute fidelity figures, which
are accordingly bounded below by whatever pose error the reconstruction
inherits. This study measures differences between configurations, and the
choice is made deliberately to keep that quantity clean rather than to optimise
the absolute one.

Intrinsics are converted alongside the images of Section 3.4.1: after
undistortion each camera carries a pinhole intrinsic matrix with no distortion
coefficients, and the field of view is recomputed from the rectified focal
length rather than carried over. The camera manifest written by preprocessing
records, per view, the intrinsic parameters, the pose, the image path and the
partition assignment of Section 3.4.4.

**The manifest is the interface between preprocessing and training, and it is
written once per scene rather than derived per run.** Every configuration in
every stage reads the same file. This is what makes the claim that all
configurations trained on identical data checkable rather than asserted: the
manifest is hashed, and each run records the hash it consumed. Two runs
reporting the same hash consumed the same cameras, the same images and the same
partition.

One property of the corpus interacts with pose handling and is recorded for
Section 4.12.4 rather than being discovered there. The camera baselines differ
substantially between scenes, and on IUI3 Red Sea the views were acquired
consecutively along a reef wall, which gives the narrowest baseline range in
the corpus. Narrow baselines constrain depth weakly, and this study's medium
model reads depth. No correction is applied for this and none is available; the
consequence is recorded as a threat to external validity rather than treated.

---

## Review log

**Domain Researcher** — The draft stated that poses are used as distributed
without saying what follows from it, which is the question a referee asks:
inherited pose error cancels from contrasts and does not cancel from absolute
figures. → *applied*, with the explicit statement that the study optimises the
former. Second finding: the interaction between narrow baselines and a
depth-reading medium model belongs here, where pose handling is described.
→ *applied*, pointing to Section 4.12.4 rather than arguing it.

**Supervisor** — The draft described the manifest as an implementation detail.
It is the mechanism by which "all configurations trained on identical data"
becomes checkable, and that is worth a sentence of emphasis. → *applied*:
bolded, with what a matching hash establishes.

**Journal Reviewer** — Whether field of view was recomputed after undistortion
or carried over was unstated, and the two give different results.
→ *applied*: recomputed from the rectified focal length.
