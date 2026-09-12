# 3.10 Chapter Summary

This section draws on every preceding subsection of the chapter and on the novelty-
defensibility analysis of the technical breakdown.

## 3.10.1 The method restated

This chapter has set out a quantitative, experimental methodology for evaluating whether three
efficiency mechanisms developed independently for terrestrial three-dimensional Gaussian
splatting can be composed onto a physically-grounded underwater reconstruction baseline, and
whether they remain mutually independent when the system they extend estimates a physical
model of the water from its own rendered geometry.

The baseline reinterprets the rasterized radiance field as a **medium-free** image and
composes it through a revised underwater image formation model — attenuation of the direct
signal and saturating backscatter, both wavelength-dependent and governed by distinct
coefficient sets — before applying any photometric loss. The medium is described by nine
global scalars for the entire scene, a deliberate trade of expressiveness for a representation
orders of magnitude cheaper than the per-ray alternative. Because the resulting objective is
massively underdetermined, admitting four named degenerate solutions of which the "no medium"
solution is a *global optimum* of the photometric loss, the baseline maintains well-posedness
through systematic gradient detachment, alternating block-coordinate optimization across three
disjoint optimisers, five auxiliary priors, a global homogeneity assumption, and a staged
warm-up.

Onto this, three mechanisms are grafted at three disjoint points of the training loop. A
**dense deterministic initialization** replaces gradient-triggered densification with a
one-shot triangulation of dense correspondences, computed before optimization begins. A
**budget-based simplification** reduces the primitive population to a fixed count by
importance-weighted stochastic sampling, chosen over deterministic thresholding because
importance is spatially autocorrelated and thresholding removes whole regions rather than
thinning them. An **attribute vector quantization** replaces per-primitive colour, scale and
rotation with indices into learned codebooks, trained with a quantization-aware forward pass
and a straight-through backward pass.

The chapter's central argument is that this composition is not the bolt-on exercise its
disjoint pipeline slots suggest. All three mechanisms write, directly or indirectly, to three
quantities the baseline's well-posedness argument depends upon: the opacity field, which four
independent forces now act upon and three of which were calibrated in systems lacking the
baseline's opacity prior; the per-primitive attribute vector; and the rendered depth map, which
is the medium model's only spatial input. The last of these produces the work's principal
technical claim. Because that depth map is renormalised to the unit interval independently for
each frame, and because the medium coefficients enter the image formation model only through
their product with depth, **removing a large fraction of the primitives rescales the medium
model's input by an uncontrolled factor mid-training** — instantiating the baseline's own
depth-medium degeneracy not as something the optimizer discovered but as a discontinuity
injected from outside the objective, against which none of the baseline's five mechanisms
defends. The remedy specified is a medium-only re-identification burst after each population
change, built from machinery the baseline already contains, together with a two-quantity
diagnostic that makes the problem and the remedy measurable at negligible cost.

## 3.10.2 The experimental logic restated

The design is a complete two-level, three-factor factorial: eight configurations from the
untreated baseline to the fully stacked system, on four underwater scenes, with three seeds
each — ninety-six training runs, with a ninth supplementary configuration and a four-run
reference control bringing the campaign to one hundred and twelve.

The choice of a factorial over the cumulative ladder every source method uses is the design's
load-bearing decision. A ladder supports one direction of inference and cannot say what
removing a component from the complete system would cost; a factorial matrix supports both,
and the disagreement between them *is* the interaction. Of the four methods composed here, one
publishes a ladder whose terminal row does not match its own reported complete model, two
publish several structurally different tables all labelled "ablation", and one publishes a
table whose direction cannot be determined even by careful reading. Declaring the inferential
structure in the methodology rather than in a table caption is a modest contribution in its own
right.

Five hypotheses map onto specific contrasts. That individual gains transfer, tested by the
single-mechanism configurations against the baseline. That their magnitudes are attenuated
relative to published terrestrial figures — predicted structurally for quantization, since the
baseline stores fourteen numbers per primitive where the compression literature assumes
fifty-nine, and the forty-five-coefficient block that quantization compresses hardest simply
does not exist. That quality cost concentrates in the water column, a prediction supported in
advance by three of the four composed methods independently naming that same region as their
weak point. That primitive reduction perturbs medium estimation — tested not by a between-cell
quality comparison but by a within-run diagnostic, and the only hypothesis in the set that
could be answered by a two-configuration experiment. And that pruning and quantization
interact sub-additively while initialization and quantization do not, the first inherited from
another paper's founding premise and testable in both directions.

Two design hazards are controlled in advance rather than discovered: a primitive budget fixed
before the campaign, below the smallest population any other enabled mechanism produces, so
that it binds in every configuration, preventing two cells from silently collapsing onto two
others; and the disabling of the quantization
mechanism's own count-reduction machinery, without which the pruning and quantization factors
would not be independent.

## 3.10.3 What the chapter deliberately does not claim

The methodology specifies a measurement obligation; it does not discharge it. No efficiency or
fidelity result is reported for any treated configuration, and no interaction is demonstrated.
The interaction analysis is analytical and is labelled as such throughout. Four deliberate
departures from the source methods — necessary to make them independent experimental factors —
mean that no configuration except the untreated baseline reproduces any published method, and
the more flattering reading is therefore unavailable. The estimated medium coefficients carry
no physical interpretation, being expressed in normalised per-frame depth rather than inverse
metres. And restoration quality, which is the scientific point of a physically-grounded
method, cannot be measured at all, in a way that systematically under-reports quantization
damage in exactly the regions where restoration matters most.

## 3.10.4 What the results chapter must establish

The results chapter inherits four obligations, in order of priority.

**First, environment validity.** The untreated configuration must reproduce the baseline's
published reconstruction quality on these four scenes within run-to-run variation. Until it
does, no other configuration is interpretable, and this is the first check rather than the
last. It also produces the converged primitive count that no publication of the baseline
reports — the quantity the pruning budget was originally to be derived from, and which is now
recorded for its own sake rather than as a precondition.

**Second, the identifiability hypothesis.** The depth-normalisation constants and medium
coefficients across the simplification boundary must be reported, for the pruning
configuration at minimum. A discontinuity in the coefficients confirms that primitive reduction
rescales the medium model's input; its absorption within the re-identification burst confirms
the remedy; the absence of both refutes the hypothesis. This is the cheapest of the four
obligations and the one that carries the chapter's principal claim. It matters that the failure
mode this diagnostic detects is otherwise invisible: a mis-identified medium model presents as
slightly worse reconstruction in the pruned configurations, which is precisely what one expects
from pruning. The failure is camouflaged as the expected result.

**Third, the main effects and their attenuation.** Each mechanism's effect on its own target
cost, estimated in both directions and reported with dispersion, and compared against published
terrestrial figures *after* renormalisation to the fourteen-number-per-primitive baseline. A
compression ratio placed beside a terrestrial figure without that renormalisation is not
conservative or optimistic; it is a different quantity.

**Fourth, the interactions.** The three two-way interaction terms and the three-way term,
computed as deviations from additive predictions and assessed against pooled dispersion. The
pruning-quantization term is informative in both directions: a sub-additive result confirms in
a new domain the premise that motivated the most recent method in the pruning lineage, while a
clean null refutes that premise in this regime and establishes that three independently
developed efficiency mechanisms compose cleanly on a physically-grounded underwater baseline
once the integration decisions of this chapter are applied. That conditional has not been
established by anyone, and it is not a lesser finding than the alternative.

The chapter has been written so that whichever way those measurements fall, the reasoning that
produced the design remains inspectable. That was the intent: to specify a study whose null
results are as interpretable as its positive ones, on a baseline whose most fragile component
is the one that makes it scientifically interesting.
