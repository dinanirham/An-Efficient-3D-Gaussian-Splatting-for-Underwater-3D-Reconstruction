---
section: "3.5.2"
title: "M1 — Deterministic Initialisation"
chapter: 3
action: Refine
evidence: ["CD register", "results_runs.csv"]
figures: []
tables: []
citations:
  - "Kotovenko et al., 2026"
  - "Edstedt et al., 2024"
status: refined
word_count: 812
---

# 3.5.2 M1 — Deterministic Initialisation

**Source.** EDGS (Kotovenko et al., 2026).

**Mechanism as executed.** Rather than initialising from a sparse structure-
from-motion cloud and growing the population by adaptive density control, this
mechanism initialises from dense correspondences computed by a learned matcher
(Edstedt et al., 2024) and disables cloning and splitting entirely for the
whole run. Reference views are selected by k-means over camera poses, each is
matched against its nearest neighbours, correspondences are triangulated, and
surviving points become primitives. Opacity-based removal still operates, so
the population can fall during training but cannot rise.

## Adaptations made by this study

**Correspondences are drawn from training views only.** The source does not
specify the restriction because it is not evaluating under a held-out
partition in the way this study does. Including held-out frames would leak the
evaluation set into the model as geometry, which no fidelity metric could
reveal (Section 3.4.5).

**A cheirality check is added alongside the reprojection filter.** A
correspondence is kept only if its triangulated point lies in front of both
cameras. The source specifies a reprojection-error filter alone, which is
insufficient on this corpus: near-parallel view rays, common in the
forward-facing captures here, produce confident matches that triangulate
*behind* a camera while still scoring a small reprojection error. With
densification disabled there is no downstream process to remove them, so a
filter that admits them leaves permanent artefacts.

**The reference-view count is constrained by the corpus.** The number of
reference views is the smaller of the configured value and the training-view
count. The source
default of 180 exceeds the total view count of every scene here — 15 to 25
training views — so the realised value collapses to the view count on every
scene. The resulting clouds hold 244 197 to 293 642 points, between 7 and 12
per cent of what the unmodified configuration converges to, where the source
method reports building clouds an order of magnitude larger.

**This configuration therefore sits off the saturation curve the source method
published, and that is recorded rather than glossed.** It is a property of the
corpus rather than of the implementation: there are not enough views to build a
larger cloud. It bounds what this mechanism can be expected to do here, and it
is the most likely explanation available for the perceptual cost Section 4.3.1
reports on the scene with the weakest view coverage — available, but untested,
since the campaign varied neither view count nor cloud size.

## Behaviours carried from the source implementation

The released implementation applies a continuous opacity decay and a clamped
position learning rate. **Neither appears in the source paper.** Both are
ported, both are exposed as configuration rather than buried, and the
scheduling of the decay is itself an integration decision recorded in Section
3.5.6.

This is the clearest instance of a distinction that runs through the whole
chapter. The mechanism measured in this thesis is an implementation, not a
published description, and the two differ. Results reported for it in Chapter
IV are results about that implementation composed into this estimator; they are
not a replication of a published claim, and Section 4.3.5 states so where the
mechanism's discussion might otherwise imply it.

## What the mechanism does not do

It does not prune. It supplies a larger initial population than the baseline's
sparse cloud and removes the procedure that would have grown it (Section
3.5.1). It does not read or modify any medium parameter. And because it
disables density control entirely, it renders the gradient-detachment mechanism
of Section 3.5.5 inert wherever it is active — which is the argument for
treating that mechanism as a supplementary contrast rather than as a fourth
factor.

---

## Review log

**Domain Researcher** — The draft gave the cheirality check as an
implementation detail. The reason it is necessary *here* and not in the source
setting — near-parallel rays in forward-facing captures, with no densification
downstream to clean up — is what justifies deviating from a published method.
→ *applied*, in full. Second finding: the cloud sizes were quoted from the
plan and are wrong for the executed campaign. → *applied*: 244 197 to 293 642,
with the percentage against the converged baseline recomputed.

**Supervisor** — The off-the-saturation-curve point was stated and left. It is
the single most important bound on this mechanism's results and it connects
directly to the one scene where the mechanism is costly. → *applied*: stated
as the most likely available explanation and immediately marked untested.
Devil's advocate: does admitting the configuration is off the published curve
invalidate the mechanism's results? No — it bounds them to this corpus, which
is what Section 4.3.6 already says, and concealing it would leave a referee to
find it.

**Journal Reviewer** — "Undocumented behaviours" needed to say what follows for
the reader, not only that they exist. → *applied*: the paragraph distinguishing
an implementation from a description, with Section 4.3.5 named. Second: the
subsection did not state that the mechanism never touches the medium, which
matters given Section 4.3.3. → *applied*, in the closing paragraph.
