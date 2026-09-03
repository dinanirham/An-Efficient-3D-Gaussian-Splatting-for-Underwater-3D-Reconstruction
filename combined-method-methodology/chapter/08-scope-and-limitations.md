# 3.9 Scope and Limitations

This section draws on the novelty-defensibility analysis and the open-questions register of
the technical breakdown, together with the constraint and computational-profile analyses.

## 3.9.1 What is claimed

Two claims, stated at the strength the evidence supports.

**A prior-art gap.** No published method combines dense correspondence-based initialization,
budget-based primitive reduction, and attribute vector quantization on a physically-grounded
underwater reconstruction baseline, and no underwater Gaussian splatting method identified in
the literature scan applies clustering-based attribute quantization at all. The nearest
neighbours are distinguishable on specific grounds: the closest system prunes by uncertainty
to remove floating primitives rather than to a primitive budget, compresses the *medium field*
rather than the primitive attributes, and initialises from a standard sparse reconstruction;
another achieves compactness by changing the primitive type itself.

This claim is deliberately not leaned on. The composition move is not novel in air —
terrestrial work has produced joint structured pruning and quantization frameworks and
multi-stage pipelines that chain the same three ideas — and the initialization mechanism's own
authors demonstrated it composing with three unmodified competing systems. That an empty
region exists in the literature is a gap, not an insight.

**An integration and well-posedness finding.** A scene-global physical medium model whose only
spatial input is a per-frame-normalised rendered depth map is not invariant to changes in the
primitive population. Reducing the primitive count mid-training rescales that depth field, and
because the medium coefficients enter the image formation model only through their product
with depth, the rescaling is formally indistinguishable from a change in the coefficients — the
baseline's own depth-medium degeneracy, arriving as a discontinuity injected from outside the
objective rather than as something the optimizer discovered. Every well-posedness mechanism the
baseline provides addresses the latter case; none addresses the former. The work specifies the
remedy — a medium-only re-identification step after each population change, built from
machinery the baseline already contains — and the two-quantity diagnostic that makes both the
problem and the remedy measurable.

This is the load-bearing claim. It is derived from facts verified in separate source
analyses, it is stated by no source, it is falsifiable, and it is testable at negligible cost.

## 3.9.2 What is not claimed

**No efficiency or fidelity result for any treated configuration.** The evidence base
available to this pass contains no measurements for the combined method — no metrics tables,
no logs, no checkpoints, no renders. Every combined-method cell in the technical breakdown
reads "no results found", and that is a statement of fact rather than a placeholder. The
methodology specifies what must be measured, in what units, with what normalisation; it does
not report measurements.

**No measured interaction.** The most natural strengthening of the contribution — a
demonstrated non-additive interaction between two of the mechanisms — is unavailable for the
same reason. The interaction table in the technical breakdown is an analytical prediction and
is labelled as one. In particular, the prediction that pruning and quantization interact
sub-additively is inherited from another paper's stated premise, not established here.

**No claim that the composition is a better underwater reconstruction system.** The study
measures effects of mechanisms and interactions between them. A system co-designed for
compactness — as the most recent method in the pruning lineage is, entangling importance
scoring with quantization by construction — would very plausibly be a better artifact. It
would also be unable to answer the question this design asks, since it *assumes* the
interaction and fixes it rather than measuring it.

**No physical interpretation of the estimated medium coefficients.** They are expressed in
units of normalised per-frame depth, not inverse metres, and are therefore not comparable with
published attenuation measurements or with the constants used to synthesise the underwater
benchmarks in this literature. This limitation is inherited from the baseline, is documented
there, and is made worse rather than better by the mechanisms under study.

**No reproduction of any source method except the baseline.** Four deliberate departures make
the mechanisms into independent experimental factors and, in doing so, make each cell a
non-reproduction: the quantization mechanism's opacity sparsity penalty is disabled; the
pruning mechanism is scoped to its simplification stage only; the substrate's periodic opacity
reset is retained against the pruning mechanism's silent removal of it; and one of the
quantization mechanism's four codebooks is dropped because the parameter block it compresses
does not exist on this baseline. This is the correct design for a factorial study — but it
means the more flattering reading, that three published methods were run on underwater data,
is false and should not be offered.

## 3.9.3 Limitations of the empirical scope

**Four scenes, eighty-eight images, thirteen held-out frames.** All results are averaged over
four points from three geographic locations. This bounds fidelity claims more tightly than
efficiency claims: the fidelity differences of interest are fractions of a decibel measured on
thirteen images, while the efficiency effects are multiples measured once per run.

**Unrepresented conditions.** Very high turbidity, green inland water, deep low-light
environments, artificial illumination, caustics, dynamic content, and non-forward-facing
capture geometry are all absent. The last of these matters mechanically as well as
statistically: correspondence triangulation degrades as view rays approach parallelism, and
all four captures are forward-facing.

**A single camera and radiometric pipeline.** Nothing in the corpus separates method behaviour
from the specific camera, housing, and white-balance pipeline used throughout.

**An operating point outside the tuned range.** The initialization mechanism's reference-view
count must be reduced below its default because the default exceeds the total view count of
every scene here, placing the configuration off the saturation curve its published analysis
established.

**Single-device timing.** All wall-clock and frame-rate figures come from one accelerator.
Between-configuration ratios transfer; absolute figures do not, and they do not transfer
proportionally, because rasterization is bound by sorting and memory bandwidth rather than
arithmetic throughput.

## 3.9.4 Limitations of the instruments

**Restoration quality cannot be measured.** The restored medium-free image is the scientific
point of a physically-grounded method, and it has no ground truth — obtaining one would
require removing the water. Every quantitative figure in this study, as in every study in this
literature, measures the in-medium reconstruction.

This has a specific consequence for a compression study that is worth stating plainly rather
than filing under general caveats. Quantization error enters the restored image directly,
since the restored image is built from the quantized colour coefficients; but before that
error reaches the measured in-medium image it is multiplied by the attenuation map, which is at
most one and approaches zero with range. **The metric attenuates the evidence of quantization
damage in exactly the far-field, red-starved regions where restoration matters most.** The
self-consistency measure introduced as a secondary metric partially compensates by comparing
restored images against an unquantized reference directly, but it can only establish that
quantization changed the restoration — never whether the change was toward or away from truth.

**A compression ceiling that is structural, not achieved.** The baseline stores fourteen
floating-point numbers per primitive rather than the fifty-nine the compression literature
assumes, because it uses zero-order spherical harmonics. Of those fourteen, quantization can
address ten; position and opacity are excluded for reasons that are structural rather than
tunable. Even at zero index cost the achievable ratio is a factor of a few rather than the
order of magnitude reported terrestrially. Compression figures from this study compared
against published terrestrial ratios without renormalisation are not conservative or
optimistic — they are a different quantity.

**Undocumented behaviours cannot be separated from their mechanisms.** Each of the three
mechanisms arrives with schedule modifications its publication does not describe, and
disabling them would depart further from the methods as evaluated than including them does.
Any measured mechanism effect is therefore partly an effect of its attached schedule
behaviour. This limitation is shared with all four source publications.

**No formal significance testing.** Three seeds on four scenes does not support a hypothesis
test with meaningful power. Effect sizes are reported against measured dispersion, with the
sample size stated, and effects of the same order as their dispersion are reported as
inconclusive rather than as null results.

## 3.9.5 Scope decisions made deliberately, and their costs

Three choices narrow the work in ways worth naming, because each closes off something
valuable.

**The medium model continues to consume alpha-blended depth.** The pruning mechanism's own
publication demonstrates blended depth to be unidentified, naming three artifacts — collapse
toward the near plane when dark content is absorbed by the background, corruption of the
weighted mean by large primitives and floaters, and smoothing across occlusion boundaries —
and quantifies the consequence at nearly ten decibels in its own setting. Two of those three
describe underwater failure modes precisely, and the modified rasterization kernel this study
already requires computes the better-posed alternative as a by-product. Substituting it is not
done, because it would change what the medium coefficients are fitted to in every configuration
including the untreated baseline, which would cease to be the published method and would
destroy the matrix's reference point. This is the clearest single follow-up the work
identifies, and it is a finding the composition produced rather than one either part supplies.

**The medium warm-up transition is held fixed.** Under dense initialization there is a
reasonable argument for triggering the medium model earlier, since the initialization places
primitives close to their final positions and the rendered depth should stabilise sooner.
Nothing measures how much sooner. The gate is held constant so that the untreated and
initialization configurations differ in exactly one factor, which is a correct choice for the
design and a possibly wrong one for the method.

**The correspondence matcher operates on the raw capture.** The cleanest remedy for matcher
hallucination in the water column would be to match on a backscatter-removed image, but the
backscatter estimate does not exist until the medium model has been trained. That impossibility
is itself informative — it suggests a two-pass variant in which initialization is repeated
after the medium model converges — and it is outside this work's scope.

## 3.9.6 The narrower contribution, if the empirical work does not follow

The methodological claim of §3.9.1 stands on analysis and is falsifiable, but it is
unmeasured. If the experimental matrix is not completed, three progressively narrower
positions remain available, and they are named here rather than left implicit.

The narrowest experiment that supports a real claim is **two configurations**: the untreated
baseline and the pruning-only configuration, with the depth-normalisation constants and medium
coefficients logged across the simplification boundary. That is sufficient to establish or
refute the identifiability finding, and it does not depend on the initialization or
quantization axes at all.

Failing that, the work stands as an **integration and reproducibility study**: a documented
account of the fourteen decisions required to compose four Gaussian splatting systems, each
with its justification and its cost, together with the protocol that would make the
composition measurable. That is a methods contribution rather than a method contribution, and
it is verifiable line by line, which is the property that makes it appropriate as a
methodology chapter even where it would not stand alone as a paper.

At its floor, the work is a **domain-transfer study** — three terrestrial efficiency mechanisms
measured on underwater scattering media against their published terrestrial gains. Even at
that floor the fourfold-smaller per-primitive baseline guarantees the transferred compression
figures will not match the published ones, and explaining why is a small but real result.

## 3.9.7 Open questions carried forward

Six questions are raised by the methodology and not answered by it. They are listed so the
results chapter and any successor work inherit them explicitly rather than rediscovering them.

Whether the medium warm-up transition should move under dense initialization. How long the
post-simplification medium re-identification burst must be to actually re-identify the
coefficients. Whether the medium model should be fed midpoint rather than blended depth. What
the right importance metric is for a scattering medium, given that neither implemented variant
was designed for one and the available medium-aware alternative — weighting importance by the
attenuation map, which the baseline already computes per pixel — is identified but not
implemented. Whether the sparse structure-from-motion points should be retained under dense
initialization, since they are the only geometry not derived from a matcher with a documented
failure mode in water. And whether a two-pass initialization, re-matching on a
backscatter-removed image after the medium model converges, would remove the matcher's
water-column failure at its source.
