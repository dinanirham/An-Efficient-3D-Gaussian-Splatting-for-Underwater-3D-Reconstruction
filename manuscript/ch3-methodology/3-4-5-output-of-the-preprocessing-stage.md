---
section: "3.4.5"
title: "Output of the Preprocessing Stage"
chapter: 3
action: Retain
evidence: ["CD register", "implementation"]
figures: []
tables: ["Table 3.5"]
citations: []
status: refined
word_count: 574
---

# 3.4.5 Output of the Preprocessing Stage

Preprocessing produces, per scene, a frozen set of artefacts that every
training run consumes and none modifies.

> **[TABLE 3.5]** *Preprocessing artefacts, per scene.* All are written once
> and hashed; the hash of each consumed artefact is recorded in the run's
> manifest.

| Artefact | Content | Consumed by |
|---|---|---|
| Undistorted image set | Pinhole-rectified images (Section 3.4.1) | All configurations |
| Camera manifest | Intrinsics, poses, image paths, partition assignment | All configurations |
| Sparse point cloud | The structure-from-motion cloud distributed with the dataset, one primitive per point | Configurations without deterministic initialisation |
| Dense point cloud | A correspondence-derived cloud with a provenance sidecar | Configurations with deterministic initialisation |

The sparse cloud is used as distributed. Each point becomes one primitive with
a fixed initial opacity, an isotropic scale derived from its nearest-neighbour
distance, and colour from the sparse reconstruction — the inherited
initialisation of the baseline method, unmodified.

**The dense cloud is produced offline and treated as data rather than as part
of the model.** This is a deliberate placement. The alternative — generating
correspondences inside the training loop — would make the initialisation a
function of the run, and the mechanism's defining property, that it is
*deterministic*, would no longer be checkable. Each cloud is written once,
hashed, and accompanied by a sidecar recording the matcher configuration, the
number of reference views, the correspondence count, the filter thresholds, and
the number of held-out frames excluded. Section 4.10.1 reports that this
mechanism's primitive count replicates across campaigns to three significant
figures, which is the determinism this placement was intended to deliver,
observed.

**Correspondences are drawn from training views only, and the exclusion is
recorded rather than asserted.** Including held-out frames would leak the
evaluation set into the model through its geometry — a leak no fidelity metric
could reveal, because it arrives as structure rather than as supervision, and a
leaked model would simply look better. The count of excluded frames is written
into the sidecar so that the exclusion can be verified after the fact by anyone
reading the artefact, rather than being a claim in this text.

Every training run records the hash of each artefact it consumed. Two runs
reporting the same hashes consumed the same data, which is what allows the
campaign to claim that configurations differ only in the mechanisms enabled.
Section 3.6.7 sets out what the campaign can and cannot establish about the
code that consumed them, which is a weaker claim and is stated as such.

---

## Review log

**Domain Researcher** — The draft described the dense cloud's offline
generation as an implementation convenience. It is what makes the mechanism's
determinism checkable, and the three-figure count replication across campaigns
is the evidence that it worked. → *applied*: stated as a deliberate placement
with the alternative named and the observed consequence cited. Second finding:
the sparse path was described without saying it is the inherited
initialisation, unmodified. → *applied*.

**Supervisor** — The test-set leak paragraph stated the safeguard but not why
the leak would be undetectable, which is what makes the safeguard necessary
rather than merely prudent. → *applied*: it arrives as structure rather than
supervision, and a leaked model would simply look better.

**Journal Reviewer** — The artefacts were described in prose and could not be
checked as a set. → *applied*: tabulated, with which configurations consume
each. Second: the hashing claim ran into the code-provenance claim, which is
weaker. → *applied*: the two are now separated, with Section 3.6.7 named.
