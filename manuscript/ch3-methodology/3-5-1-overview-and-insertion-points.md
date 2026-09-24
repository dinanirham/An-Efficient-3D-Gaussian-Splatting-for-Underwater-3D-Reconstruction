---
section: "3.5.1"
title: "Overview and Insertion Points"
chapter: 3
action: Refine
evidence: ["CD register", "results_runs.csv"]
figures: ["figure-1-pipeline", "figure-2-schedule"]
tables: ["Table 3.6"]
citations: []
status: refined
word_count: 574
---

# 3.5.1 Overview and Insertion Points

This section describes the three mechanisms as executed. Section 3.1.2 placed
them on the pipeline; this one gives the settings each ran at, and the
subsections that follow describe each in turn together with the adaptations
this study made to it.

The section is titled *Efficiency Mechanisms Under Test* rather than *Proposed
Method* because the thesis does not propose a method. It takes three mechanisms
whose behaviour is documented on terrestrial scenes, transfers each into a
physics-aware underwater estimator, and measures what happens — individually,
in every pairwise combination, and all together.

> **[TABLE 3.6]** *Mechanism settings as executed.* Realised quantities are
> means over twelve runs; target quantities are configuration. Source:
> `results_runs.csv`.

| | Mechanism | Setting | Realised |
|---|---|---|---|
| **M1** | Deterministic initialisation | Dense correspondence cloud; cloning and splitting disabled for the run | 244 197–293 642 initial primitives per scene |
| **M2** | Spatial reorganisation | Budget of 200 000 primitives, applied at iterations 15 000 and 20 000, each followed by 200 medium-only steps | 132 955–149 906 final primitives per scene |
| **M3** | Attribute-level quantisation | Three attribute groups; codebooks trained from a fixed iteration with a straight-through estimator | 20.6 bytes per primitive, from 56.0 |

For comparison, the inherited sparse initialisation supplies 21 140 to 25 837
primitives, and the configuration with no mechanism active converges to between
1.99 and 4.03 million. **The dense cloud is therefore an order of magnitude
larger than the sparse one and roughly a tenth of what the baseline grows to** —
between 7 and 12 per cent of the unmodified configuration's final population,
depending on scene.

That relationship is worth stating before any mechanism is described, because
it is easy to misread deterministic initialisation as a pruning method. It
removes nothing. It supplies a larger starting population than the baseline
does and then declines to grow it, and the reduction it achieves is entirely
the growth that does not happen.

Each mechanism's subsection follows one shape: the source it derives from, the
mechanism as executed, the adaptations this study made and why, and anything
carried from the source implementation that its published description does not
contain. That last heading is not decoration. One source implementation
predates its own paper by approximately ten months and contains behaviour the
paper does not describe, and this study measures implementations rather than
descriptions. Section 3.5.6 registers every such difference in one place.

---

## Review log

**Domain Researcher** — The draft gave the mechanisms' settings without the
populations they produce, so a reader could not tell that deterministic
initialisation starts *larger* than the baseline does. That misreading — as a
pruning method — is the most likely one and is worth pre-empting.
→ *applied*: the comparison with both sparse and converged populations, and the
paragraph stating that the mechanism removes nothing. Second finding: the draft
quoted initial cloud sizes of 299 368 to 471 531 from the pre-campaign plan;
the executed runs give 244 197 to 293 642. → *applied*: measured figures, with
the source named.

**Supervisor** — The draft did not explain the section's title, which changed
from "Proposed Method" and is a substantive repositioning rather than an
editorial one. → *applied*: one paragraph, stating what the thesis does instead
of proposing. Second: the common shape of the subsections was not announced, so
a reader meets "undocumented behaviours" in Section 3.5.2 without warning.
→ *applied*, with the reason that heading exists.

**Journal Reviewer** — Realised and target quantities were mixed in one column.
→ *applied*: separated, with the caption stating which is which and over how
many runs.
