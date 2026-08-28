# 3.8 Statistical Validity and Reproducibility

This section draws on the reproducibility, constraint and implementation-delta analyses of the
technical breakdown, together with the open-questions register.

## 3.8.1 Seed handling

The four codebases composed here have four different seeding disciplines, and the weakest of
them belongs to the baseline.

The baseline's seed argument **defaults to random**: unless a seed is supplied it draws from
operating-system entropy, so every run differs. Even when a seed *is* supplied, the device
random-number generator is never explicitly seeded, and neither deterministic algorithm
selection nor deterministic convolution backends are enabled. The dense-initialization
codebase carries a seed in its configuration file that its documentation never mentions. The
pruning codebase hard-codes a seed with no way to change it, and — more importantly — that
seed does not achieve what it appears to, because the two decisive random draws in its
simplification stage are fed by probabilities computed on the device, so the surviving
primitive population varies run to run regardless. The quantization codebase inherits a
hard-coded seed from the substrate, but its codebook initialisation is not known to be seeded
at all.

The protocol adopted is therefore: **every run receives an explicit seed; the baseline's
state-initialisation routine is patched to seed the device generator as well; and every run
records the seed alongside its fully resolved configuration.**

Bit-exact reproduction remains unattainable, and this is stated rather than glossed. The
differentiable rasterizer uses atomic accumulation in its backward pass, which is
non-deterministic in floating-point arithmetic irrespective of seeding. The correct response
is not to pursue determinism but to **measure and report dispersion**, which the next
subsection describes. This is also why the seed audit matters more than seeding itself: the
draws that a seed would need to control include the initial backscatter coefficients and water
colour, the background-colour initialisation that is later transferred into the water colour,
the camera shuffle and per-iteration view sample, the pose clustering that selects reference
views, the correspondence sampler, the importance-weighted survival draw, and the codebook
initialisation. Knowing which are controlled and which are not is more useful than a false
claim of determinism.

## 3.8.2 Run repetition and variance reporting

**Three seeds per configuration per scene**: eight configurations, four scenes, three seeds,
ninety-six training runs. Results are reported as mean and standard deviation across seeds,
at both the per-scene and aggregate level, for every quality and efficiency measure.

This is the study's dominant cost and it is not negotiable, for a reason visible in the source
literature. **No source method reports error bars.** The baseline's published ablation table
contains differences of a few hundredths of a decibel between rows, reported from single runs
with a randomly seeded default; those differences are not demonstrated to exceed run-to-run
noise, and the table is nonetheless read as establishing component contributions. Its
neural-radiance-field predecessor is deterministic by construction and still reports single
runs, with a headline margin of seven hundredths of a decibel.

The requirement is stricter here than in any of the sources, because the quantities of primary
interest are **interactions** — differences of differences — which carry approximately twice
the variance of a main effect. An interaction claimed from single runs would repeat the
sources' error while making a stronger claim than any of them attempts.

One variance source cannot be removed by seeding and is reported explicitly: the realised
primitive count after simplification is stochastic even at a fixed seed. **The realised count
is reported per run, with its dispersion, rather than the target budget.** A budget that lands
within a few per cent of target across seeds is a different experiment from one that scatters,
and the reader should be able to tell which occurred.

## 3.8.3 Statistical treatment of comparisons

Main effects are estimated in **both** directions — the mechanism added to the bare baseline,
and the mechanism removed from the complete system — and both estimates are reported. Where
the two agree within pooled dispersion, the mechanism is independent of the others and either
figure may be quoted. Where they disagree, **neither may be quoted alone**; the disagreement
is the interaction and is reported as such.

Interactions are computed as the deviation of a compound configuration from the additive
prediction built from its components: additively for quality measures expressed in decibels or
as similarity indices, multiplicatively for ratio measures such as storage, count and frame
rate. Deviations are assessed against the pooled standard error of the configurations entering
the calculation, not against a single run's difference.

The study makes **no claim of statistical significance in the hypothesis-testing sense**, and
this is a deliberate restraint rather than an oversight. Three seeds on four scenes does not
support a formal test with meaningful power, and reporting a p-value from that sample would
give a false impression of rigour. What is reported is effect size against measured
dispersion — an interaction that is several times the pooled standard deviation is evidence;
one that is a fraction of it is not — with the sample size stated plainly so the reader can
calibrate. Where an effect is of the same order as its dispersion, the finding is reported as
inconclusive rather than as a null.

## 3.8.4 Threats to internal validity

**Undocumented schedule behaviours travel with their mechanisms.** This is the most serious
internal threat and it cannot be fully removed. Three of the four codebases contain behaviours
that their publications omit: a continuous opacity decay and a clamped position learning rate
in the initialization codebase, a rewound learning-rate schedule and a wholly removed periodic
opacity reset in the pruning codebase, and an undocumented fourth learned parameter in the
baseline whose value is transferred into the medium model at a schedule boundary. These arrive
attached to their mechanisms; separating them would depart further from the methods as
evaluated. The residual risk is that a measured mechanism effect is partly an effect of its
attached schedule behaviour. Each is recorded as active, and where two conflict a precedence
rule is stated. The threat is shared with all four source publications, none of which
separates the two either.

**Four forces act on one variable.** Primitive opacity is written by the baseline's opacity
prior, by the substrate's periodic reset, by the initialization mechanism's continuous decay
and halved learning rate, and by the pruning mechanism's rebuild. Three of the four were
calibrated in systems where the opacity prior does not exist. Any effect attributed to a
mechanism may in part be an effect of miscalibrated opacity dynamics. The study cannot
disentangle this within its matrix; it reports the opacity trajectory as a diagnostic so that
the possibility is visible rather than hidden.

**A confounded factor, controlled.** The quantization mechanism ships its own count-reduction
machinery, which its authors identify as the source of its published rendering speedup. Left
enabled, the pruning and quantization factors would not be independent. It is disabled, and
the quantization-only configuration's primitive count is compared against the baseline's as a
check that it stayed disabled.

**A degenerate cell, controlled.** If dense initialization converges below the pruning budget,
the pruning step becomes a no-op and two configurations collapse onto two others, producing a
spurious null interaction. The budget is set from the untreated baseline's converged count so
that it binds everywhere, and whether it bound is reported per run.

**Silent no-ops.** Two of the three mechanisms are inert at their upstream defaults — one
defaults its training-epoch count to zero, the other defaults its quantization start iteration
to the end of training — and the evaluation flag defaults off in two of the four codebases,
producing an empty test set and inflated numbers. None of these raises an error. Every run
asserts that each enabled mechanism fired and that the test set is non-empty.

**Environment validity.** The untreated configuration must reproduce the baseline's published
quality on these scenes within run-to-run variation. If it does not, the environment is wrong
and no other configuration is interpretable. This is the study's first check, not its last.

## 3.8.5 Threats to external validity

**Single-hardware measurement.** All timing and frame-rate figures come from one device. They
are internally comparable across configurations — which is what the conclusions rest on — but
they do not transfer to other devices, and specifically they do not transfer proportionally,
because rasterization is bound by sorting, atomic accumulation and memory bandwidth rather
than by arithmetic throughput. Absolute figures should be read as device-specific; the
between-configuration ratios are the transferable quantity.

**Four scenes.** Every claim is an average over four points from three geographic locations,
with twelve held-out evaluation frames in total. Water types beyond these — very high
turbidity, green inland water, deep low-light environments — are unrepresented. This bounds
generalisation more tightly for fidelity claims, which rest on twelve images, than for
efficiency claims, which rest on four per-run measurements of effects that are multiples
rather than fractions.

**A single capture geometry.** All four scenes are forward-facing, captured with one camera and
housing, in daylight, with static content. The initialization mechanism's triangulation quality
depends on baseline geometry between views, and the pruning mechanism's importance metrics
were developed on object-centric and unbounded terrestrial scenes. Both are being applied
outside the capture geometry they were tuned for, and nothing here separates method behaviour
from camera-specific radiometry.

**An operating point off the tuned curve.** The initialization mechanism's reference-view count
must be reduced from its default because the default exceeds the total view count of every
scene in this corpus. The published saturation analysis that justifies the default was measured
on corpora with an order of magnitude more views, so this study operates outside the range
where that analysis applies.

**Compression figures are not portable.** The baseline stores fourteen numbers per primitive
rather than the fifty-nine assumed by the compression literature, and one of the two storage
mechanisms described by the quantization method's publication is absent from its
implementation. Compression ratios reported here describe this baseline and are not
transferable to systems that retain higher-order spherical harmonics.

## 3.8.6 Reproducibility protocol

The following are fixed before the matrix is run and recorded with every result.

**Frozen inputs.** The distributed structure-from-motion reconstruction is used unchanged;
structure-from-motion is not re-run. Per-scene training and test frame lists are recorded. The
image-directory naming inconsistency is normalised and the container format of written renders
is logged.

**Per-run artifacts.** Fully resolved configuration; seed; realised reference-view count and
correspondence confidence threshold; realised primitive count at five checkpoints; effective
optimizer-step count; device identification and software versions; the medium coefficient and
depth-normalisation trajectories; and the complete stored model with every component
itemised.

**Assertions at startup.** Non-empty test set; each enabled mechanism confirmed to have fired;
the quantization mechanism's opacity penalty confirmed disabled.

**Declared conventions.** Signal-to-noise ratio reported under both the per-channel and pooled
definitions; perceptual-similarity backbone named; aggregation reported under both unweighted
and image-weighted scene means; primitive counts reported as rendered primitives; model size
reported as an absolute figure with the per-primitive normalisation stated alongside any
ratio.

**A stated sequencing dependency.** The untreated configuration runs first, on all scenes and
seeds, because its converged primitive count sets the pruning budget and is not reported
anywhere in the baseline's publication.

## 3.8.7 What reproducibility cannot reach here

Three limits are acknowledged rather than engineered around.

Bit-exact reproduction is unattainable because of non-deterministic accumulation in the
rasterizer's backward pass. Dispersion reporting replaces it.

The realised primitive population after simplification is stochastic even at a fixed seed,
because the survival draw is fed by device-computed probabilities. It is reported, not
controlled.

And the baseline's published timing figures cannot be reproduced or compared against, because
the hardware behind them is not named — only that a consistent set of hardware was used. Any
comparison against those figures is between an identified device and an unidentified one, and
is labelled accordingly rather than presented as a speedup.
