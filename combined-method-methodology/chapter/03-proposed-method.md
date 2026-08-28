# 3.4 Proposed Method

This section draws on the taxonomy, pipeline, variable, loss, constraint, pseudocode and
implementation-delta analyses of the technical breakdown. It is the chapter's core, and it is
organised so that the borrowed material is disposed of first and the work's own technical
content occupies the second half.

---

## 3.4.1 What the method is

The proposed method is a physically-grounded underwater three-dimensional Gaussian splatting
system, extended by three efficiency mechanisms that act at three disjoint points of its
training pipeline, together with a set of integration decisions that keep the physical medium
model identifiable while the geometry underneath it is being replaced, thinned, and
quantized.

The distinction between those two halves is deliberate and structural. The mechanisms are not
this work's contribution: each is an established technique with a published evaluation on
terrestrial data. What this work contributes is the account of what happens when they are
applied to a representation whose loss reads a *rendered depth map* into a *physical model of
the medium* — a condition none of the three was designed for, and one under which their
documented orthogonality does not automatically hold.

---

## 3.4.2 The baseline: reconstruction through an image formation model

### The representation

The scene is an explicit set of anisotropic three-dimensional Gaussian primitives. Each
primitive carries a position, a covariance factored into a scale vector and a rotation
quaternion, an opacity, and colour. Rendering is by differentiable rasterization: primitives
are projected to the image plane, sorted per tile, and alpha-blended front to back. The
representation is optimised per scene by gradient descent; it is not generalisable across
scenes, and it contains no neural network.

Colour is carried by **zero-order spherical harmonics only** — a single red-green-blue triple
per primitive. Unmodified Gaussian splatting uses third-order harmonics, forty-eight colour
numbers per primitive, to represent view-dependent appearance. The baseline discards this on
the reasoning that underwater object colour is treated as view-independent, the
view-dependence in the observed image being attributable to the medium rather than to the
surface. Per-primitive storage falls from fifty-nine floating-point numbers to fourteen. This
single decision reappears at three separate points later in the section, each time with
consequences that are not obvious in advance.

### The medium

Where unmodified Gaussian splatting compares its rendered image directly against the capture,
the baseline reinterprets that render as the **medium-free radiance** — the scene as it would
appear with the water removed — and composes it through a revised underwater image formation
model before any comparison is made.

Writing the rendered medium-free radiance as *J*, the rendered depth as *Z*, the attenuation
coefficients as *β*<sub>att</sub>, the backscatter coefficients as *β*<sub>bs</sub>, and the
water colour at infinity as *B*<sup>∞</sup>, the composed in-medium image is

> *Î* = *J* ⊙ exp(−*β*<sub>att</sub> *Z*) + σ(*B*<sup>∞</sup>) ⊙ (1 − exp(−*β*<sub>bs</sub> *Z*))

where ⊙ is elementwise product, σ the logistic function, and the exponentials act per colour
channel. The first term is the *direct* signal: scene radiance attenuated on its way to the
camera. The second is *backscatter*: light scattered into the ray by the medium, saturating
at the water colour as range grows. The two coefficient sets are **distinct**, which is the
substantive content of the revised formation model that the baseline adopts — earlier
underwater models assumed a single coefficient governed both processes, and the physical
optics literature established that they do not.

The photometric loss is applied to *Î*, not to *J*. This is the whole mechanism: the
optimiser sees photometric residual only *through* the medium composition, so the veiling
haze is paid for by the medium model rather than by inventing primitives in the water column.

**Nine scalars describe the medium for the entire scene.** Three attenuation coefficients,
three backscatter coefficients, one water colour triple — constant across every pixel of
every frame. This is the axis on which the underwater radiance-field literature divides most
sharply. The neural-radiance-field lineage grants the medium a learned function of viewing
direction, evaluated densely along every ray, and argues explicitly that per-scene constancy
is too restrictive. The baseline takes the opposite position, trading medium expressiveness
for a representation roughly three orders of magnitude cheaper. That trade is what makes an
efficiency study of this system worth doing at all — and, as §3.4.6 develops, the constancy
assumption is not merely an efficiency choice but one of the mechanisms that makes the
objective well-posed.

### The depth the medium consumes

The medium model needs a per-pixel range. The baseline obtains it with a **second full
rasterization pass** in which the primitive colour is overridden by its camera-frame depth,
producing an alpha-weighted depth image which is then divided by the accumulated opacity,
non-finite values are replaced, and — critically — the result is **renormalised to the unit
interval by its own minimum and maximum, independently for every frame.**

That final renormalisation is the hinge of this entire chapter. Its immediate consequences
are already visible: the learned coefficients are expressed in units of normalised per-frame
depth rather than inverse metres, so they are not physically comparable with published
attenuation measurements; and the same physical range maps to different normalised values in
different frames, which sits in tension with the assumption that the coefficients are global.
Its non-obvious consequence — that the coefficients are therefore not invariant to changes in
the primitive population — is the subject of §3.4.7.

### Why the naive objective is underdetermined, and what fixes it

Per pixel the model supplies four free values against three observations, before counting the
nine global scalars, so the system is underdetermined by construction. Four specific
degenerate solutions are admitted, and it is worth naming them because three of the four
become live again under the efficiency mechanisms.

The first is the **no-medium solution**: set both coefficient sets to zero and the composition
collapses to unmodified Gaussian splatting. This is not a local minimum to be escaped — it is
a *global optimum* of the photometric loss, at least as good as the intended solution, and no
amount of photometric gradient can distinguish it.

The second is the **depth–medium trade-off**: the coefficients and the depth enter only as
their product, so scaling depth by any factor and the coefficients by its reciprocal leaves
the composed image exactly unchanged. Because depth is produced by the geometry, the
optimiser can satisfy the medium model by moving primitives to implausible ranges.

The third is the **colour-gauge ambiguity**: per channel, multiplying the restored radiance by
a constant and adding its logarithm to the attenuation coefficient leaves the direct term
unchanged. The restored image — the entire scientific point of the method — has an
unconstrained per-channel gain under the photometric loss alone.

The fourth is the **water-column floater solution**, the one unmodified Gaussian splatting
actually finds: place opaque, low-texture primitives close to the camera to reproduce the
veiling haze directly as geometry. Photometrically excellent, geometrically meaningless.

Five mechanisms resolve these. **Gradient detachment** routes every auxiliary prior to exactly
one parameter group: the medium maps are computed twice, once on live depth for the
photometric path and once on detached depth for the medium-only priors, so a prior on the
water can never move a primitive. **Alternating optimization** runs three disjoint optimisers
on disjoint schedules — fifty medium-only steps for every hundred geometry steps, never on the
same pass — which is block-coordinate descent over a factorisation that simultaneous descent
would collapse. **Auxiliary priors** supply the missing constraints: an asymmetric dark-channel
prior that makes zero backscatter expensive and thereby kills the no-medium solution; a
grey-world prior that pins the restored image's channel means and thereby fixes the colour
gauge; a saturation cap; an opacity prior that zeroes opacity wherever a pixel is
indistinguishable from the water colour, which is what suppresses water-column floaters; and
an edge-aware depth-smoothness term that denies per-pixel depth noise as free capacity. The
**global homogeneity assumption** is itself a structural regulariser — nine scalars must
explain the medium everywhere, which is by far the strongest constraint in the system.
Finally, **staged warm-up** withholds the medium model for the first third of training so that
depth becomes meaningful before any coefficient is fitted to it, and transfers the learned
background colour into the water colour at the transition.

The full objective is a seven-term weighted sum: the photometric term, a depth-weighted
reconstruction term that re-weights residual toward the far field where the medium's effect
is strongest, the dark-channel prior, the grey-world prior, the saturation cap, the opacity
prior, and the depth-smoothness term. It is written in the source publication as an unweighted
sum; in practice six of the terms carry distinct weights spanning two orders of magnitude, and
the opacity prior — with the *smallest* weight of all — is the one term whose ablation moves
reconstruction quality materially, by well over two decibels.

---

## 3.4.3 Mechanism one: dense deterministic initialization

The first mechanism replaces gradient-triggered adaptive density control with a single dense
initialization computed once, before optimization begins.

Reference views are selected by clustering camera poses; each reference is paired with its
nearest neighbours; each pair is passed through a pretrained dense correspondence network
which returns a per-pixel warp and confidence; confident correspondences are triangulated by
direct linear transform; and each surviving correspondence becomes one primitive with
position from triangulation, colour read from the reference pixel, and scale proportional to
its distance from the reference camera. The structure-from-motion points are then discarded
and optimization proceeds with the ordinary photometric loss and **no densification at all**.

The argument for this is that a dense correspondence field already contains the geometry that
gradient-triggered densification spends fifteen thousand iterations rediscovering, and
contains it *uniformly* — including in high-frequency regions where the gradient-norm
criterion is documented to be blind. The published evidence is asymmetric in a way that
supports the claim strongly: unmodified Gaussian splatting loses nearly two decibels when its
densification is removed, whereas this method gains six hundredths of a decibel when
densification is added back.

Two properties matter for the composition. First, **the loss is completely untouched** — the
contribution is upstream of the objective and indeed upstream of optimization itself. Second,
the mechanism's reported gains are in perceptual similarity and primitive count rather than
in peak signal-to-noise ratio, on which it is second-best on two of three terrestrial
benchmarks. The correct hypothesis to import is "improves perceptual quality and reduces
count at roughly equal wall-clock," not "improves quality."

Two undocumented behaviours arrive with it and are consequential here. The released
implementation applies a **continuous opacity decay** — a multiplicative reduction every ten
steps for the first half of training, cumulatively a very large shift in logit space — paired
with a halved opacity learning rate, which together replace the periodic opacity reset of the
underlying system. And it **clamps the position learning-rate schedule**, never using the high
early learning rate that a sparse initialization requires, on the entirely sensible reasoning
that a good initialization should not be scattered. Neither appears in the method's
publication. Both act on quantities the baseline's own machinery also acts on.

---

## 3.4.4 Mechanism two: spatial reorganization and budget pruning

The second mechanism attacks primitive *count*. Its source method rewrites adaptive density
control from a point-cloud perspective, arguing that gradient-driven densification produces a
spatial distribution with two defects: primitives cluster redundantly in some regions while
missing detail in others, and oversized primitives in smoothly-varying regions are never split
because their positional gradient is small — a blind spot of the gradient criterion rather
than a tuning failure.

The method's densification half adds a blur-triggered split, using a criterion orthogonal to
the gradient, and periodically destroys and rebuilds the entire representation from
backprojected depth points. Its simplification half — which is what this work uses — proceeds
in two stages. First, an **importance score** is accumulated over every training view, then
**intersection preservation** zeroes the score of any primitive that is never the dominant
contributor to any pixel in any view, and finally the surviving population is subsampled by
**importance-weighted stochastic sampling** to a target count. Later, a light deterministic
prune removes primitives making up the bottom fraction of total importance mass.

The stochastic sampling deserves emphasis because it is the reason this is the right pruning
mechanism for a budget. Deterministic top-*k* selection by importance fails at high pruning
ratios for a specific reason: importance is **spatially autocorrelated**, so neighbouring
primitives have similar scores and a threshold removes entire *regions* rather than thinning
uniformly. Randomising survival within a uniform-importance patch thins the patch instead of
deleting it. The source method validates this with a point-cloud distance metric rather than
a rendering metric, which is a stronger form of evidence for a distributional claim than peak
signal-to-noise ratio would be.

Three properties matter for the composition. The **loss is untouched** — the entire mechanism
is non-differentiable bookkeeping around an unchanged objective. The importance metric is
**hand-picked per scene type**, with only indoor and outdoor variants implemented and the
source authors describing the choice as an experimental trick; neither variant was designed
for a scattering medium, and the outdoor variant's area normalisation exists specifically to
suppress sky. And the mechanism requires a **modified rasterization kernel** that returns
per-primitive importance accumulators the standard kernel does not.

---

## 3.4.5 Mechanism three: attribute vector quantization

The third mechanism attacks *bits per primitive*. Its premise is that many primitives carry
similar parameter values, so the parameters can be replaced by indices into a small learned
codebook.

Clustering after training degrades quality, because nothing in the objective encourages
parameters to be clusterable. The mechanism therefore runs clustering **during** training: the
forward pass renders using centroids, the backward pass updates the *unquantized* parameters
through a straight-through estimator, and the optimiser is thereby free to move parameters
somewhere that quantizes well. Parameters are grouped by type, each group receiving its own
independent codebook, because a single codebook over heterogeneous parameters in different
units has no meaningful distance metric. Position and opacity are excluded outright: sharing
positions would make distinct primitives literally coincide, and opacity is a single scalar
with nothing to gain.

The cost problem is solved by an elegant asymmetry. Clustering has two steps — updating
centroids given assignments, and updating assignments given centroids — of which only the
second is expensive. Centroids are therefore re-averaged every iteration using cached
assignments, while assignments are recomputed only every hundredth iteration. Both branches
produce valid centroids; only the *partition* goes stale. This is what keeps training overhead
at a factor of one and a half rather than two orders of magnitude.

The method also ships a secondary contribution: an opacity sparsity penalty with periodic
pruning, motivated by the observation that once the compressible attributes are cheap, the
*incompressible* ones dominate what remains. **This work disables it**, for reasons developed
in §3.4.8.

---

## 3.4.6 Where the composition breaks: the shared-variable analysis

Everything to this point is inherited. This subsection begins the work's own content.

The three mechanisms are called orthogonal because each edits a different pipeline stage — one
before optimization, one at two mid-training events, one continuously after a start gate — and
none touches the others' code. That is true, and it is verifiable in the pseudocode: the seven
loss terms are identical across all eight configurations, and every difference lives in three
disjoint regions of the training loop.

But orthogonality of *code paths* is not orthogonality of *effects*. All three mechanisms
write, directly or indirectly, to three quantities that the baseline's well-posedness argument
depends on.

**Opacity has four writers.** The baseline's opacity prior drives opacity toward zero wherever
a pixel is indistinguishable from the water colour — the single most valuable term in the
objective, worth over two decibels alone, and the mechanism that suppresses the water-column
floater degeneracy. The baseline also resets all opacities periodically, which is the
substrate's core anti-floater device. The initialization mechanism adds a continuous global
opacity decay and halves the opacity learning rate, and renders the periodic reset
unreachable. The pruning mechanism removes the periodic reset entirely and resets every
opacity back *up* to its initialization value at each rebuild. The quantization mechanism adds
a sparsity penalty. Under the fully stacked configuration, four independent forces act on the
same scalar within a single iteration, and three of them were calibrated in systems where the
opacity prior does not exist. The prediction that follows is concrete: the opacity prior's
weight is not the right value in any configuration except the untreated baseline.

**Rendered depth has three writers.** It is the medium model's only spatial input. The
initialization mechanism replaces the geometry that produces it and removes the density
control that refines it. The pruning mechanism changes which primitives contribute to it. The
quantization mechanism perturbs scale and rotation and therefore the rendered surface.

**The per-primitive attribute vector has three writers.** It is seeded by triangulation under
the initialization mechanism, partially reset at every rebuild under the pruning mechanism,
and replaced by codebook entries under quantization.

Reading these three together is the argument that the mechanisms are **not orthogonal on this
baseline even though they are orthogonal on unmodified Gaussian splatting**. The terrestrial
systems on which their independence was demonstrated have no loss term that reads depth, no
physical model, and no prior that targets opacity for a semantic reason.

---

## 3.4.7 The central integration problem: primitive reduction breaks medium identifiability

This is the work's principal technical claim, and it follows from three facts that no single
source method holds together.

**Fact one.** The medium model's spatial input is renormalised to the unit interval by its own
per-frame minimum and maximum. The learned coefficients are consequently in units of
normalised per-frame depth.

**Fact two.** The coefficients and the depth enter the image formation model *only as their
product*. Scaling the depth field by a constant and the coefficients by its reciprocal leaves
the composed image exactly invariant — the baseline's own second degeneracy.

**Fact three.** Budget pruning removes a large fraction of the primitives at a single
iteration. On terrestrial data the analogous mechanism removes between seventy and ninety per
cent.

The conclusion is immediate. Removing that many primitives changes which surfaces are nearest
and farthest in each frame, therefore changes the normalisation constants, therefore
**rescales the medium model's only input by an uncontrolled factor, discontinuously, in the
middle of training**. Formally this is the second degeneracy — but it does not arrive as
something the optimiser has discovered and is exploiting. It arrives as a step change
*injected from outside the objective*.

Every one of the baseline's well-posedness mechanisms is designed for the former case and is
silent about the latter. Gradient detachment prevents the medium losses from dragging the
geometry; it does not help when the geometry changes for reasons unrelated to any gradient.
Alternating optimization prevents simultaneous descent on both factors of a bilinear
product; it does not help when one factor is replaced between steps. The global homogeneity
assumption constrains the coefficients to explain every pixel; it does not tell them which
scale they are now expressed in.

**No source method faces this**, and the reason is structural rather than accidental. The
baseline has the normalisation and the degeneracy but never changes its primitive population
except through the substrate's smooth, gradual density control. The three efficiency
mechanisms change the population dramatically but have **no medium model at all** — their
rendering equations contain no depth-dependent term, so a rescaling of rendered depth is
simply invisible to their objectives. The interaction is a property of the composition.

### The fix

The remedy adopted here follows the baseline's own architecture rather than inventing a new
device. The baseline already possesses a mechanism for identifying medium parameters against
a fixed geometry: at the moment the medium model is switched on, it runs a thousand
medium-only optimizer steps with the primitives frozen, followed by a colour-only adjustment
phase, and thereafter runs fifty medium-only steps for every hundred geometry steps. The
proposal is to **fire that same medium-only burst immediately after each simplification
event**, giving the coefficients an opportunity to re-identify themselves against the new
depth distribution before the geometry is allowed to move again.

Three properties recommend it. It reuses machinery that exists and is already trusted. It is
consistent with the alternating-optimization discipline that makes the factorisation tractable
in the first place. And it is cheap relative to the events it responds to, which occur twice
per run.

Two alternatives were considered and rejected. Freezing the normalisation constants at their
pre-pruning values preserves the medium model's scale but leaves the depth field's actual
range and its assumed range inconsistent, trading one inconsistency for another. Disabling the
per-frame normalisation entirely is arguably the *correct* long-term answer — it removes the
frame-to-frame inconsistency that already sits in tension with the global-coefficient
assumption — but it changes what the coefficients are fitted to in every configuration
including the untreated baseline, which would mean the baseline is no longer the published
method and the experimental matrix loses its reference point.

### The diagnostic

The claim is falsifiable, and cheaply. The normalisation constants and the nine medium
coefficients are logged at every checkpoint. If pruning rescales the medium model's input,
there is a visible discontinuity in the coefficients at the simplification boundary; if the
re-identification burst works, the discontinuity is absorbed within the burst. If neither
appears, the hypothesis is refuted. This costs one logging statement and converts an
analytical argument into a measurement.

It is worth stating why this failure mode would otherwise go undetected. It does not crash, it
does not warn, and it does not produce a visibly broken image. **It manifests as slightly
worse numbers in the pruned configurations — which is precisely what one expects from
pruning.** The failure is camouflaged as the expected result. That is the strongest reason to
believe an engineer composing these methods would not find it, and the strongest reason to
report it.

---

## 3.4.8 The remaining integration decisions

The medium re-identification burst is the most substantive of this work's integration
decisions but not the only one. Those that change what the experiment *measures*, as opposed
to how it runs, are set out here; the full set, with justifications and costs, appears in the
technical breakdown.

**The quantization mechanism's opacity sparsity penalty is disabled.** Its source method
attributes its compression to quantization and its rendering speedup to this penalty and the
pruning it drives — the two are separable, and the published speedup is the second, not the
first. Leaving the penalty enabled would make the quantization factor a
*quantization-plus-pruning* factor, so the pruning and quantization columns of the matrix
would not be independent and the paired cells would prune twice. The matrix would stop
measuring what it claims to. The cost of disabling is that this study's quantization cell is
**not a reproduction** of its source method and its numbers must not be compared to that
method's published table — in particular, its rendering speedup should be expected to be
approximately none.

**The pruning mechanism is scoped to simplification only.** Its densification half is
excluded, because its depth-driven rebuild fails wherever no reliable depth exists and its
resampling is biased toward low-opacity pixels — which is the water column, twice over. What
is tested is therefore *the simplification stage of* that method, and it must be named as
such throughout, or a reader will assume the complete method.

**The substrate's periodic opacity reset is retained under pruning**, contrary to its silent
removal in the pruning mechanism's implementation. That removal is plausibly justified in its
original setting, where the depth-driven rebuild resets every opacity every few thousand
iterations anyway; under the simplification-only scoping adopted here that compensating
mechanism largely disappears, and the reset is a co-mechanism of the opacity prior in
suppressing water-column floaters.

**The primitive budget is an explicit count, not a sampling ratio**, and it is set from the
untreated baseline's converged count. This makes the budget bind in every configuration. Left
as a ratio, the budget might not bind at all when dense initialization has already produced a
small population, in which case the pruning step becomes a no-op and two cells of the matrix
silently collapse onto two others — producing a "no interaction" result that is an artifact of
configuration rather than a finding. This is a sequencing dependency: the baseline must be run
and measured before the matrix can be configured, because the baseline's primitive count is
not reported anywhere in its publication.

**One codebook is dropped.** The quantization mechanism groups parameters into four codebooks:
zero-order colour, higher-order harmonics, scale, and rotation. On this baseline the
higher-order harmonic block **does not exist**, because spherical-harmonic order is zero.
Three codebooks remain. The deeper consequence is that the compression ceiling is capped a
priori: of fourteen floating-point numbers per primitive, quantization can address ten,
leaving position and opacity uncompressed, so even at zero index cost the achievable ratio is
a factor of a few rather than the order of magnitude the terrestrial literature reports.
**Any compression figure from this study compared against published terrestrial ratios without
renormalising to a fourteen-number baseline is a category error.**

**Quantization begins after simplification.** A codebook fitted before a large prune is fitted
to a population about to be discarded, and quantization-aware training would spend its
gradient budget adapting parameters that are then deleted. This leaves a shorter
quantization-aware phase than the source method uses; the most recent work in that lineage
reports that clustering in only the final thousand iterations costs almost nothing, which is
the reason to expect the shortened phase is sufficient.

**The learning-rate conflict dissolves rather than being adjudicated, and only implementation
revealed why.** The initialization mechanism clamps the position learning rate on the grounds
that a good initialization should not be scattered; the pruning mechanism rewinds it on the
grounds that a freshly reinitialised population needs enough learning rate to move. Both
default on in their source implementations, and their intents are contradictory, so the design
initially specified a precedence rule in favour of the rewind — reasoning that after
simplification the population is genuinely new.

Writing the simplification stage showed that premise to be false under this work's own
scoping. Because the pruning mechanism is scoped to simplification only, nothing is
reinitialised: the surviving primitives keep their parameters *and* their optimiser state,
since the underlying pruning routine index-selects the second-moment estimates rather than
rebuilding them. There is no new population for the rewind to compensate for. Enabling it
would inject a correction for a condition that does not arise, so it is **disabled by
default** and the clamp stands alone; the rewind is retained as a flag purely for sensitivity
analysis. This is a case where the specification was wrong in a way that reading could not
have exposed — the error was in an assumption about optimiser-state handling that only becomes
visible when the two mechanisms are made to coexist.

---

## 3.4.9 One opportunity identified and deliberately not taken

The composition surfaces a finding that neither part could produce alone, and it is recorded
rather than acted on.

The baseline feeds its physical medium model an alpha-normalised **blended** depth. The
pruning mechanism's source publication devotes an appendix to arguing that blended depth is
*not identified*, naming three artifacts: collapse toward the near plane when dark background
content is explained by the background colour rather than by geometry; corruption of the
weighted mean by large primitives and floaters; and smoothing across occlusion boundaries,
because a weighted sum cannot represent a step. It quantifies the consequence at nearly ten
decibels in its own setting, and replaces blended depth with the ray-ellipsoid midpoint of the
single dominant primitive.

Two of those three artifacts describe underwater failure modes precisely. Collapse when dark
content is absorbed into the background is a description of a heavily attenuated far field.
Corruption by floaters is the water-column degeneracy the baseline exists to fix. **The
baseline is therefore feeding its physical model a depth quantity that a sibling method
demonstrates to be unreliable in exactly this regime** — and the modified rasterization kernel
that the pruning mechanism already requires computes the better-posed alternative as a
by-product.

Substituting it is not done here, because it would change what the medium coefficients are
fitted to in every configuration including the untreated baseline, destroying the matrix's
reference point. It is the clearest single follow-up the work identifies, and it is a finding
the composition produced: neither source states it, because neither has both a
depth-driven physical medium model and a midpoint depth estimator in the same system.

---

## 3.4.10 Summary of the method's own technical content

Stripped of the borrowed mechanisms, the proposed method contributes:

1. The identification that a scene-global physical medium model whose spatial input is a
   per-frame-normalised rendered depth map is **not invariant to primitive-population
   changes**, and that this instantiates the baseline's own depth–medium degeneracy as an
   externally injected discontinuity that none of its well-posedness machinery addresses.
2. A remedy built from the baseline's existing alternating-optimization machinery — a
   medium-only re-identification burst after each population change — together with a
   two-column diagnostic that makes the problem and the remedy measurable at negligible cost.
3. The observation that three of the four composed methods independently name the same
   region — depth-ambiguous, low-texture water column — as their weak point, so that the
   composition concentrates three failure modes on one region while simultaneously perturbing
   the single loss term that defends it.
4. A set of integration decisions, each with a stated justification and a stated cost, that
   make the three mechanisms into **independent experimental factors** rather than a stack of
   partially-reproduced methods — including the disabling of a source method's secondary
   count-reduction machinery, the scoping of another to a single stage, and the replacement of
   a sampling ratio by an explicit budget.
5. An analysis of why the compression ceiling on this baseline is structurally lower than the
   terrestrial literature's, arising from a single inherited configuration choice, together
   with the renormalisation required for any cross-paper comparison to be valid.
