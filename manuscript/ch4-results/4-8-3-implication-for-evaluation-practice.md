---
section: "4.8.3"
title: "Implication for Evaluation Practice"
chapter: 4
action: Add
evidence: ["FINDINGS §8", "FINDINGS §10", "FINDINGS §2b"]
figures: []
tables: []
citations: ["Wang et al., 2004", "Zhang et al., 2018"]
status: refined
word_count: 826
---

# 4.8.3 Implication for Evaluation Practice

This is the methodological result of the thesis, and it is stated here in the
form the evidence supports rather than in the strongest form available.

**Composed-image fidelity metrics cannot certify the physical component of a
physically grounded estimator.** Peak signal-to-noise ratio, structural
similarity (Wang et al., 2004) and learned perceptual similarity (Zhang et al.,
2018) are computed on the composed image. That image is the product of a
restored radiance and an attenuation term, plus a backscatter term. The metrics
constrain the product. They do not constrain either factor, and this chapter
provides two independent demonstrations that the factors move freely while the
product does not.

The first is at scale. Within configuration and scene, runs whose attenuation
coefficient has been driven below zero differ from runs whose has not by a
median 0.8 of a baseline standard deviation on the composed image, across
twelve comparisons at three repeats, with the sign inconsistent between them
(Section 4.8.1). A model describing water that amplifies light with distance
renders held-out views as well as one describing water that absorbs it.

The second is within a single model. Two attribute states of one trained model,
agreeing on the composed image to within 1.4 decibels at the median, produce
restored images 17 to 27 decibels apart (Section 4.8.2). The quantity the
estimator exists to produce is not determined by the quantity the objective
constrains.

The consequence for how such methods are evaluated is direct. An efficiency
mechanism selected on fidelity and size — the procedure Section 4.6.6
describes, and the one this literature conventionally applies — will select
configurations whose medium model has failed, without any indication that it
has done so. This is not a failure of diligence that more careful application
of the same metrics would catch. The metrics are measuring a quantity that
remains correct while the decomposition beneath it becomes wrong, and no
threshold on them separates the two cases.

**What follows is a requirement on evaluation, not a criticism of the metrics.**
Peak signal-to-noise ratio and the others do what they were designed to do, on
the quantity they were designed for, and this chapter uses them throughout for
exactly that. The requirement is that a method claiming a physical
decomposition must be evaluated on the decomposition as well as on the image,
and that such evaluation needs instruments the composed-image metrics cannot
supply. This campaign used three, and their properties are worth stating
because they are the practical content of the recommendation.

The first is **collapse incidence**: whether a coefficient leaves its feasible
range and fails to return. It requires no ground truth, is determined from the
optimisation trace rather than from any image, and cannot be tuned after the
fact. It is the strongest of the three and detects only outright failure.

The second is **internal consistency**: whether two states of one model, or two
halves of one physical description, agree where the physics requires them to.
Section 4.5.7 compares two attribute states; Section 4.2.4 compares the
attenuation and backscatter coefficient orderings, which must describe the same
water and on one scene do not. Consistency checks need no ground truth either,
and they detect a broader class of problem than collapse, but they establish
only that something is wrong, never which part.

The third is **physical plausibility**: whether the fitted parameters respect
what is known about the medium, such as the spectral ordering of attenuation.
This is the weakest, because the depth renormalisation of Section 4.2.4 leaves
only within-scene ordering interpretable, and because a fit can be plausible
and still wrong.

None of the three measures accuracy, and this chapter cannot. **The instrument
this campaign most conspicuously lacks is a ground truth for the restored
image.** Without it, every statement in this chapter about the medium model is
a statement about stability, consistency or plausibility, and none is a
statement about correctness. Acquiring such a reference — a scene imaged in
water and in air, or with a calibrated target at known depths — would convert
the entire third axis from detecting failure to measuring quality. Section 5.4
carries it as the campaign's most valuable missing instrument.

The scope of this result should be stated precisely, because it is easy to
overstate in either direction. It is not a claim that the reconstructions in
this chapter are poor: on the composed image they are equivalent to the
published reference, and that is a real result on a real quantity. Nor is it a
claim specific to underwater reconstruction as a domain. It applies to any
estimator whose output is a decomposition and whose objective scores only the
composition — which includes intrinsic-image decomposition, relighting, and
any physically grounded inverse rendering. The underwater setting is where this
campaign met it, and the medium model is what made it visible, because a water
column that amplifies light is obviously wrong in a way that many latent
factors are not.

---

## Review log

**Domain Researcher** — The draft wrote that the metrics "fail", which is the
overstatement a referee would seize on; they succeed at what they measure.
→ *applied*: the claim is now that they cannot certify the physical component,
with an explicit paragraph separating a requirement on evaluation from a
criticism of the instruments. Second finding: the draft recommended
"decomposition-aware evaluation" without saying what that would consist of.
→ *applied*: the three instruments used here, each with what it needs, what it
detects and what it cannot do.

**Supervisor** — The draft's two demonstrations were narrated in the order they
appear in the chapter rather than in order of evidential weight.
→ *applied*: the twelve-comparison result first as the load-bearing one, the
single-model result second. Second: the closing scope paragraph was absent, and
without it the result reads either as an attack on the corpus or as a claim
about underwater work alone. → *applied*, with the generalisation named and
bounded. Devil's advocate: is claiming relevance to intrinsic-image
decomposition and inverse rendering reaching beyond the evidence? The argument
is structural rather than empirical — it follows from scoring a composition
while claiming a decomposition — and it is phrased as applying to that class,
not as demonstrated there.

**Journal Reviewer** — The missing ground truth was mentioned as a limitation
without saying what acquiring it would change. → *applied*: it would convert
the third axis from detecting failure to measuring quality, with two concrete
acquisition routes and a destination section. Second: metrics were named
without citation in the subsection that criticises their scope, where
attribution matters most. → *applied*, both from the register.
