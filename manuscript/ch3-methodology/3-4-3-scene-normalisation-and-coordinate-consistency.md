---
section: "3.4.3"
title: "Scene Normalisation and Coordinate Consistency"
chapter: 3
action: Retain
evidence: ["CD register", "implementation"]
figures: []
tables: []
citations: []
status: refined
word_count: 511
---

# 3.4.3 Scene Normalisation and Coordinate Consistency

Scene loading applies the normalisation inherited from the baseline
implementation: cameras are centred on their common centroid and the scene is
scaled so that the camera extent is unity. The transform is computed once per
scene from the training views and applied to cameras and to the initial point
cloud alike.

Normalisation matters more in this study than in a purely geometric one,
because two downstream quantities are expressed in the normalised frame and one
of them is a reported result.

**Primitive scales and positions are in normalised units.** The geometric
diagnostics of Section 3.7.4 — bounding-box inflation, footprint occupancy, the
ratio of the largest to the median primitive radius — are therefore ratios and
are comparable across scenes. That is a property of the normalisation rather
than a coincidence, and it is why those quantities are reported without units
in Chapter IV.

**Rendered depth is normalised again, per frame, before it reaches the medium
model.** This is a second and separate rescaling, applied inside the
optimisation loop rather than at load time, and it is the one with consequences
for interpretation. Because each frame's depth is mapped to the unit interval
independently, the medium coefficients are fitted against a quantity whose
scale is not fixed across frames and bears no stable relation to metric
distance. Section 3.1.1 states the consequence and Section 3.7.3 states what it
permits the diagnostics to claim: channel ordering within a scene is
interpretable, magnitudes are not, and no coefficient reported in this thesis
is in physical units.

The two normalisations are independent and are not composed. Load-time
normalisation fixes a common coordinate frame for a scene; per-frame depth
normalisation is applied to the rasteriser's output every iteration. A reader
should not infer from the first that the second gives a consistent scale: it
does not, and that is precisely the limitation the medium results carry.

Coordinate consistency across configurations is guaranteed by the same
mechanism as the data itself. The normalisation transform is a function of the
training cameras alone, which are identical across configurations by Section
3.4.2, so every configuration in every stage operates in the same frame. No
mechanism under test modifies the transform, and none reads it.

---

## Review log

**Domain Researcher** — The draft described one normalisation and the thesis
depends on two, applied at different times for different reasons. Conflating
them would let a reader conclude that the medium coefficients are in a
consistent scale because the scene was normalised at load. → *applied*: both
described, explicitly stated to be independent and not composed, with the
misinference named. Second finding: that the geometric diagnostics are
comparable across scenes *because* of load-time normalisation was not stated.
→ *applied*.

**Supervisor** — The draft read as a configuration note. Its actual content is
the origin of the single most restrictive limitation on the thesis's medium
claims, and that should be visible here rather than only where the limitation
bites. → *applied*: the per-frame renormalisation is now the subsection's
centre, with its consequence stated and located.

**Journal Reviewer** — The transform's inputs were unstated, leaving it unclear
whether held-out views influence it. → *applied*: computed from the training
views alone, which also establishes cross-configuration consistency.
