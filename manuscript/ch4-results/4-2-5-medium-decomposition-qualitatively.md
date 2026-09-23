---
section: "4.2.5"
title: "Medium Decomposition, Qualitatively"
chapter: 4
action: Add
evidence: ["renders", "FINDINGS §2b"]
figures: ["figure-4-04-medium-decomposition"]
tables: []
citations: []
status: refined
word_count: 623
---

# 4.2.5 Medium Decomposition, Qualitatively

Section 4.2.4 reports the medium parameters as numbers. This subsection shows
what those numbers produce, because the decomposition is the estimator's
distinguishing output and it is not visible in any fidelity metric this thesis
reports.

> **[FIGURE 4.4]** `figures/chapter4/figure-4-04-medium-decomposition.pdf`
> *What the reference claims the water is doing.* One held-out view per scene
> from the reference implementation, shown as the composed image Î, the
> restored image Ĵ, the attenuation map and the backscatter map. Only the
> composed image has ground truth; the other three are the model's own account
> and are not validated against a measurement.
> **Status:** built · **Anchored on:** SS

The four panels correspond directly to the terms of the image formation model.
The composed image is what the estimator renders and what every fidelity number
in this chapter scores. The restored image is the medium-free radiance the
estimator infers the scene would have if the water were removed. The
attenuation map shows how strongly the medium is judged to absorb along each
ray, and the backscatter map shows how much veiling light is judged to be added
along it. The composed image is the product and sum of the other three, so the
decomposition is exact by construction: the four panels always compose back to
the first, whatever the parameters are.

That last property is the reason this subsection exists, and the reason it is
placed in the baseline section rather than left to Section 4.7. **The
decomposition being exact by construction means it is not evidence that the
decomposition is correct.** Any assignment of radiance between the restored
image and the medium that reproduces the observation is equally consistent with
the data the estimator is trained on. The restored image has no ground truth in
this corpus, and neither do the two medium maps. What Figure 4.4 shows is what
the model claims, and the claim is checkable only in the limited ways Section
4.2.4 sets out — the ordering of the channels, and the agreement of the two
coefficient sets with each other.

Read with that limit in mind, the panels are informative about the scenes. The
restored images recover warm tones absent from the composed images, most
visibly on Curaçao and Panama, which is the expected consequence of removing a
blue-green water column. The attenuation maps track depth structure, being
darkest where the geometry is nearest and brightest at range, which is what a
depth-driven attenuation term should produce and a check that the term is
reading depth at all. The backscatter maps are smoother than the attenuation
maps on every scene, consistent with a term that saturates with distance and
therefore varies little across the far field.

Two scenes deserve comment. On IUI3 Red Sea and Japanese Gardens the restored
image is substantially brighter and bluer than on the other two, and the
attenuation map carries less structure. These are the two scenes whose far
field is close to featureless in the ground truth (Section 4.2.3), so the
medium model is being fitted where there is least geometric signal to separate
it from. IUI3 Red Sea is also the scene whose fitted spectrum is inverted and
whose two coefficient sets disagree. The qualitative appearance is consistent
with the numerical anomaly, and it is reported as consistent rather than as
confirming, since a visual impression of a quantity with no ground truth cannot
confirm anything.

This subsection makes no claim about restoration quality. It establishes what
the decomposition looks like when the medium model is intact, which is the
comparison Section 4.7.6 needs when it shows what the same panels look like
after a channel has collapsed.

---

## Review log

**Domain Researcher** — The draft described the restored images as "recovering
true colour", which asserts accuracy the corpus cannot support. → *applied*:
"recover warm tones absent from the composed images", with the explicit
statement that Ĵ has no ground truth. Second finding: the draft did not say
that the decomposition is exact by construction, which is the single most
important thing a reader needs in order not to over-read the figure.
→ *applied*, and promoted to its own paragraph as the reason the subsection
sits in the baseline section.

**Supervisor** — The subsection was a caption expanded to a page: four panels
described in turn with no argument. → *applied*: restructured so the
construction-versus-correctness point carries it, and the panel description
serves that point rather than standing alone. Second: it ended without saying
what it is for. → *applied*: closing paragraph naming Section 4.7.6 as the
comparison this one enables.

**Journal Reviewer** — "Consistent with the numerical anomaly" risked being
read as corroboration. → *applied*: the sentence now states why a visual
impression of a quantity without ground truth cannot confirm. Second: the
figure was anchored on the reference while the surrounding text said "the
estimator" throughout, leaving the configuration shown ambiguous.
→ *applied*: the caption names the reference and the anchor line is carried.
