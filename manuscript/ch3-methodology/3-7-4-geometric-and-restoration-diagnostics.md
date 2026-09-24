---
section: "3.7.4"
title: "Geometric and Restoration Diagnostics"
chapter: 3
action: Add
evidence: ["FINDINGS §9", "FINDINGS §10", "j_consistency.json"]
figures: []
tables: ["Table 3.14"]
citations: []
status: refined
word_count: 794
---

# 3.7.4 Geometric and Restoration Diagnostics

Two further instrument groups are recorded. Both require the trained
representation rather than only its metrics, so both are bounded by the storage
policy of Section 3.7.5.

> **[TABLE 3.14]** *Geometric and restoration quantities.*

| Quantity | Definition | Used in |
|---|---|---|
| Visible fraction | Proportion of primitives whose opacity clears the renderer's visibility threshold | 4.2.6, 4.3.4, 4.4.4 |
| Bounding-box inflation | Full extent of the point cloud divided by its central 98 per cent extent | 4.2.6 |
| Footprint occupancy | Proportion of a spatial grid the cloud occupies | 4.4.4 |
| Radius ratio | Largest primitive radius divided by the median | 4.4.4 |
| Restored-image consistency | Difference between renderings of one model from its two attribute states | 4.5.7, 4.8.2 |

## Geometric diagnostics

These are failure detectors for the representation, and they are never used as
proxies for medium health — a compact, fully visible point cloud can carry a
collapsed medium model, and Chapter IV contains configurations that do.

**The visible fraction is the most consequential of them.** A primitive
contributes to an image only if its opacity survives alpha compositing, and
Section 4.2.6 reports that between 57 and 77 per cent of the reference's
primitives do not. That measurement changes how every count reduction in this
thesis should be read: a mechanism removing primitives is not, in general,
removing reconstruction, and the reductions are therefore reported against both
the total and the visible population.

The remaining three describe the cloud's spatial character. They are ratios and
are comparable across scenes because of the load-time normalisation of Section
3.4.3. Bounding-box inflation detects detached outlying primitives, which
Section 4.2.6 establishes as a baseline property rather than a mechanism
artefact; occupancy and radius ratio describe how concentrated the survivors of
a reduction are.

## Restoration consistency

This instrument was built to answer a question the fidelity metrics cannot
reach: whether the restored image — the estimator's distinguishing output — is
determined by what the training objective constrains.

**The measurement is within a single model.** A trained quantised model holds
each affected attribute in two states, the continuous parameters the optimiser
updates and the codebook entries the straight-through estimator commits them
to, and the model can be rendered from either. Nothing else differs — same
primitives, same positions, same medium scalars, same view — so any difference
between the two renderings is attributable to quantisation alone. The composed
image is rendered from each state as well, which is what allows the comparison
to be interpreted: if the continuous state rendered the composed image poorly,
it would not be a model and the comparison would be meaningless.

**It measures consistency, not accuracy.** It establishes whether two states of
one model agree about the restored image. It cannot say which is nearer the
true medium-free radiance, because that quantity has no ground truth here. This
is the same limit that bounds the medium diagnostics of Section 3.7.3, arriving
by a different route.

One further property of the instrument is recorded because Chapter IV depends
on it. Rendering a quantised model requires the codebook state to be applied
explicitly: the stored point cloud holds the *continuous* parameters, which the
campaign never evaluated. A collector that read the point cloud naively would
measure the wrong state, and an earlier version of the asset pipeline did
exactly that before the self-check described in Section 3.7.5 caught it.

---

## Review log

**Domain Researcher** — The draft grouped these as "diagnostics" without saying
that geometric health and medium health are independent, which is the
misreading a reader arrives with — a tidy point cloud looks like a healthy
model. → *applied*: stated explicitly, with the note that Chapter IV contains
compact clouds carrying collapsed media. Second finding: the restoration
instrument's within-model design was not distinguished from a between-model
comparison, and the distinction is what makes it evidence. → *applied*, with
the composed-image control that makes it interpretable.

**Supervisor** — The draft listed five quantities evenly. The visible fraction
changes how every count result in the thesis is read and deserves the weight.
→ *applied*. Devil's advocate: is reporting reductions against two populations
hedging? No — one figure determines storage and the other determines capacity
surrendered, and both are true; reporting only the larger would be the
misleading choice.

**Journal Reviewer** — The restoration instrument's dependence on applying the
codebook state was not recorded, and a reader attempting to reproduce it from
the stored artefacts would measure the wrong thing. → *applied*, including that
an earlier version of the pipeline made exactly that error. Second: the four
geometric quantities were given without saying why they are comparable across
scenes. → *applied*: they are ratios, under the normalisation of Section 3.4.3.
