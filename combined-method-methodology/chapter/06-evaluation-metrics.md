# 3.7 Evaluation Metrics

This section draws on the reproducibility, glossary, computational-profile and loss analyses
of the technical breakdown.

## 3.7.1 Why the definitions need this much care

Four superficially standard metrics — peak signal-to-noise ratio, structural similarity,
perceptual similarity, and model size — are computed in mutually incompatible ways across the
methods this study composes and compares against. The differences are not rounding: one of
them systematically inflates a quality figure by an amount that is *largest in underwater
imagery specifically*, and another changes what "model size" refers to by a factor of nearly
two. A methodology section that named the metrics without defining them would be reporting
numbers that cannot be interpreted.

There is also a domain-specific asymmetry that shapes the whole section. A
physically-grounded underwater method produces two images: the **in-medium reconstruction**,
which is what the training views show, and the **restored** medium-free image, which is the
scientific point of the exercise. Only the first has ground truth. The second cannot have any,
since obtaining it would require removing the water. Every quantitative claim in this
literature therefore measures reconstruction, and every restoration claim is qualitative — a
constraint this study inherits, and which has a specific and under-appreciated consequence for
a compression study developed in §3.7.5.

## 3.7.2 Primary metrics: reconstruction fidelity

Fidelity is measured between the composed in-medium render and the held-out capture,
full-frame and unmasked. No sky mask, water-column mask, opacity mask or valid-depth mask is
applied — matching the convention of every method compared against, and matching it
deliberately, since masking conventions are a common silent source of incomparability in this
literature.

### Peak signal-to-noise ratio

Reported under **two conventions**, both explicitly labelled.

The **per-channel convention** computes a mean squared error for each colour channel,
converts each to a signal-to-noise ratio, and averages the three. The **pooled convention**
computes a single mean squared error over all pixels and all channels and converts once.

By Jensen's inequality the per-channel convention is always the larger of the two, and the gap
grows as the channels' errors diverge. **Underwater imagery is the regime of maximum channel
divergence** — the red channel is attenuated to near-nothing over range while blue is barely
affected — so the convention inflates results more here than in any other domain. This is not
a small effect: measured on a synthetic pair with an underwater-like error profile, the two
conventions differ by nearly twelve decibels, while on uniformly distributed error they agree
to four decimal places.

A related hazard is worth stating carefully, because this study initially got it wrong. It is
tempting to assert that the baseline's published comparison table places its own per-channel
figures beside a competitor's pooled ones, in the direction that flatters the baseline. The
implementation showed this cannot be asserted. The baseline's peak-signal-to-noise routine
reduces along the tensor's leading dimension, so **which convention it computes is decided by
the shape of the tensor passed to it** — and the codebase passes both: the in-training report
supplies a three-channel image and obtains the per-channel figure, while the evaluation that
writes the results file supplies a single-image batch and obtains the pooled one. The number a
publication would quote therefore comes from the *stricter* convention, not the inflated one,
and nothing in either the paper or the repository records which path produced the published
table. The comparability concern is real and the conventions genuinely are incompatible; the
specific accusation of bias is not established, and this chapter does not make it.

Reporting both costs nothing and removes the entire class of ambiguity — including the one
just described, since a reader can select whichever convention the comparison at hand
requires without this study having had to guess. The pooled figure allows comparison with the
neural-radiance-field lineage and with competing underwater efficiency methods, which use the
standard definition, and it is also the figure most likely to match the baseline's own
published table. The per-channel figure is retained because the baseline's in-training
reporting uses it, so any comparison drawn against numbers logged during training rather than
at evaluation needs it.

The implementation also removes the mechanism that caused the confusion: the two conventions
are now separate named functions, each normalising its input first, and a genuine batch is
rejected rather than silently averaged. A call site can no longer change which quantity is
produced by changing a tensor's shape.

It is worth recording that exactly one paper among the nine surveyed identifies this problem
explicitly, and it is one of the composed methods. Its authors observe that averaging
signal-to-noise ratios is dominated by the most accurate reconstructions because the logarithm
makes it a geometric average of errors, and introduce a corrected variant that averages the
error before taking the logarithm. That passage is the methodological warrant for reporting
under a stated convention rather than a default one.

### Structural similarity

Computed with the eleven-by-eleven Gaussian window, standard stabilising constants, averaged
over all pixels and channels — the implementation inherited from the Gaussian splatting
substrate and shared by three of the four composed methods.

Structural similarity is included because it responds to *structural* degradation in a way
signal-to-noise ratio does not, and the mechanisms under study degrade structure in
characteristic ways: pruning removes primitives, which thins fine detail before it dims it,
and quantization coarsens the covariance parameters, which blurs primitive footprints. It is
the metric most likely to separate a method that has lost geometry from one that has merely
lost contrast.

### Perceptual similarity

Computed with a **VGG** feature backbone, stated explicitly because the backbone matters and
no source publication names it in text. Perceptual similarity from a VGG backbone and from an
AlexNet backbone give systematically different values, and two of the methods compared against
report values whose backbone is unstated.

Perceptual similarity is the **most sensitive of the three quality metrics to the treatments
under study**, and this expectation comes from the sources rather than from theory. The
initialization mechanism's headline claim is a thirty-plus per cent perceptual-similarity
improvement, while its signal-to-noise gains are small enough that it is second-best on two of
three terrestrial benchmarks. The pruning mechanism's quality is carried by signal-to-noise
ratio and structural similarity while its perceptual similarity is slightly *worse* than the
substrate on two of three benchmarks. And every compression method surveyed degrades
perceptual similarity most of the three. Perceptual similarity is therefore the metric on
which the three mechanisms are most likely to disagree with each other, which makes it the
most informative single quality number in the study.

### Aggregation

Per-image values are averaged within a scene, then across scenes. Because the four scenes have
unequal frame counts, **both** the unweighted scene mean — matching the baseline's published
convention — and the image-weighted mean are reported. They differ, and stating which is used
removes an easy source of disagreement.

## 3.7.3 Primary metrics: efficiency

Four efficiency measures, corresponding to the three mechanisms' targets plus one that all
three affect.

### Rendered primitive count

The number of primitives actually rasterized at the end of training. The qualifier matters:
across the compression literature, reported counts variously mean rendered primitives,
*anchors* from which primitives are derived at up to ten to one, or derived splats from
anchors — and at least one published table mixes two of these in a single column with a
footnote.

Count is recorded at **five points**: immediately after initialization, after the opacity
dynamics have settled, and before and after each simplification event. The first two differ
under dense initialization, because correspondences that fail the reprojection test are
retained with near-zero opacity rather than deleted, so a single post-initialization number is
ambiguous by construction. The **realised** post-simplification count is reported rather than
the target budget, because the subsampling is stochastic and driven by device-computed
probabilities, and therefore varies run to run even at a fixed seed.

### Model size on disk

The complete stored artifact: unquantized attributes, index streams, codebooks and their
metadata, and the medium parameter files. All of it counts.

Two normalisations are required for any comparison to be meaningful, and both are stated
alongside every reported ratio. **First**, the baseline stores fourteen floating-point numbers
per primitive rather than the fifty-nine the compression literature assumes, because it uses
zero-order spherical harmonics; a compression ratio computed against a fifty-nine-number
baseline is not the same quantity as one computed against a fourteen-number baseline, and
placing the two in one table is a category error. **Second**, one of the two storage
mechanisms described by the quantization method's publication — sorting indices and
run-length-encoding them — is absent from its released implementation, so the achievable
figure is below the published one before any baseline difference is counted.

Model size is reported as an absolute figure in megabytes first and as a ratio second, because
the absolute figure is unambiguous and the ratio is not.

### Training cost

Reported as **both** wall-clock time and **effective optimizer steps**. The two are decoupled
in this system by a margin large enough to invalidate naive comparison: the baseline's
alternating schedule advances its loop counter only on geometry steps, so a nominally
thirty-thousand-iteration run performs roughly forty-three thousand optimizer steps, and this
study's medium re-identification bursts add further steps that likewise do not appear in the
count. A figure reported only in iterations is not comparable with one reported in steps, and
this study reports both so the question does not arise.

**Each step of this implementation pays three rasterization passes where the baseline pays
two.** The baseline obtains the accumulated alpha channel from the same pass that produces the
image; the rasterizer adopted here cannot, so alpha is recovered from a dedicated probe pass
and depth from a second, for the reason given in §3.4 — combining them routes depth gradients
into the densification signal, which the baseline excludes and which measurably suppresses the
converged model. The cost is real, falls on every cell equally, and is therefore visible in
absolute wall-clock while cancelling in every between-cell contrast. It is stated here rather
than absorbed silently, because wall-clock is one of the efficiency measures this study
reports.

Wall-clock is device-dependent and is presented with the device named. Effective step count is
device-independent and is the quantity to compare against a method that reports its own.

### Rendering frame rate and peak memory

Frame rate is measured over the held-out views on the named device. Peak memory is recorded
for both training and rendering.

One expectation should be set in advance to avoid a misreading. The quantization mechanism's
published two-to-three-fold rendering speedup comes from its opacity sparsity penalty and the
pruning it drives, **not** from the quantization — its own authors say so — and this study
disables that penalty so that the factors remain independent. The quantization-only cell is
therefore expected to show **approximately no frame-rate gain**. That is a correct result, not
a failure to reproduce.

A second expectation: frame-rate gains from reduced primitive count are **sub-linear**.
Rasterization sorting is superlinear in primitive count per tile and per-pixel blending
saturates, so the pruning mechanism's terrestrial eight-and-a-half-fold count reduction bought
a four-fold frame-rate improvement. Predictions for the pruning cell should be sub-linear
accordingly.

## 3.7.4 Secondary metrics: restoration and diagnostics

These are reported but never aggregated into a headline figure, because none has ground truth
or an external reference.

**Restored-image self-consistency.** For quantized configurations, the signal-to-noise ratio
between the restored image produced by the quantized model and the restored image produced by
the otherwise-identical unquantized model. This is the only available quantitative proxy for
quantization damage to restoration, and its limitations are stated in §3.7.5. It is a
consistency measure, not an accuracy measure, and it is labelled as such.

**Medium parameter trajectories.** The nine coefficients and the water colour, logged at every
checkpoint, together with the per-frame depth normalisation constants before and after each
simplification event. These test the study's central hypothesis directly and are the only
instrument that can distinguish "pruning cost quality" from "pruning broke medium
identifiability", since both present identically in the quality metrics.

**Geometric extent and occupancy.** This replaces a diagnostic specified earlier in the
design and never built. The original specification was a population count of high-opacity,
low-texture primitives near the camera, by analogy with a competing underwater method that
reports a floater ratio moving from over eight per cent to just over one per cent when its
pruning branch is enabled. That specification was abandoned for a practical reason: "near the
camera" and "low-texture" both require thresholds with no principled value on this corpus, and
the resulting number would have been a tuned quantity presented as a measurement. What was
built instead measures the *geometry of the primitive cloud itself*, which needs no such
choice, and it is described here in the form it actually takes.

Five families of quantity are computed from each stored model, all in the scene's own
coordinate units and therefore comparable only within a scene:

*Extent.* The full axis-aligned bounding box, and a **robust box** taken between the first and
ninety-ninth percentile of each axis independently — the scene proper. The ratio of the two,
per axis, is the **inflation**, and the worst axis is named. A cloud whose geometry is compact
but whose bounding box is enormous has inflation concentrated on one or two axes.

*Opacity gating.* Every extent quantity is computed twice: over all primitives, and over
**rendered** primitives only, defined as opacity at or above 0.05. The threshold is not tuned
to an outcome; it marks the point below which a primitive contributes nothing visible to an
image. The distinction is load-bearing rather than cosmetic, because **a bounding box held
open by invisible material is a different pathology from one held open by rendered material**,
and the two call for different remedies. On this corpus the distinction separated a diffuse
low-opacity halo on one scene, where gating raised occupancy seventy-seven-fold, from
genuinely rendered detached clusters on two others.

*Occupancy.* The fraction of a fixed sixty-four-cubed voxel grid, spanning the full box, that
contains at least one primitive. This exists because the percentile box has a blind spot that
took a viewer to notice: **it only catches a tail thinner than its own percentile.** At two
million primitives the outer one per cent is twenty thousand points, so a dense detached blob
of that size sits *inside* the robust box and never registers as inflation at all, while being
immediately obvious to anyone rotating the model in a viewer. Occupancy is the measure that
matches what the eye sees — a low value means the box is being held open by material that
fills almost none of it.

*Radial concentration.* The share of primitives within two, five and ten times the median
radius about the **median** primitive position, the median rather than the mean because the
statistic must not be dragged by the very outliers it is meant to detect. A cloud whose box is
held open by detached clusters shows a high share near the centre together with a populated
tail far beyond it — which is a different signature from a cloud that is merely diffuse.

*Radial spread.* The fiftieth, ninetieth, ninety-ninth and hundredth percentiles of that
radius, and the ratio of the last to the first. This single ratio is the most legible summary:
a value in the low tens is an ordinary scene, and four figures indicate a triangulation
placing primitives at distances unrelated to the geometry.

**What the protocol found is why it is reported.** Across the untreated baseline the bounding
box is between ninety-six and ninety-nine point nine six per cent empty, and the emptiness has
**two mechanisms that no single number separates** — detached rendered clusters beyond ten
times the median radius with a zero gap below them, and a diffuse invisible halo. One of the
four scenes has neither and serves as the control. The simplification mechanism removes both,
and removes them *incidentally*: its importance metric normalises by projected area, which was
designed to suppress sky, and near-camera haze and diffuse halos present to that metric the
same way sky does.

**It also makes one reported efficiency figure ambiguous, which is a result in itself.**
Primitive-count reduction under simplification is nineteen-fold measured raw
`[measured n=12]`. Gating at the same opacity threshold, the untreated baseline is only about
thirty-six per cent rendered while the simplified model is about ninety-three per cent, so the
reduction in *rendered* primitives is closer to seven-fold `[measured n=1 per scene]`. Both
figures are honest and they answer different questions — how much storage was saved, and how
much of the model was ever contributing. A reduction ratio quoted without saying which one it
is cannot be interpreted, and this study reports both.

**Qualitative restoration comparison.** Side-by-side restored renders across configurations,
presented as evidence about a quantity with no ground truth and labelled accordingly. Every
method in this literature does this; the honest form is to say why.

## 3.7.5 Why each metric is the right instrument, and where the instruments fail

The three quality metrics measure different things and are not substitutes. Peak
signal-to-noise ratio measures pixel-level radiometric agreement and is dominated by
large-area, low-frequency error; structural similarity measures local structural agreement and
responds to lost geometry; perceptual similarity measures agreement in a learned feature space
and correlates best with human judgement of detail. The mechanisms under study degrade these
differently — initialization improves perceptual similarity while barely moving
signal-to-noise ratio, pruning does the reverse, quantization degrades perceptual similarity
most — so reporting fewer than three would systematically favour one mechanism.

The efficiency metrics correspond one-to-one with the three mechanisms' stated targets:
initialization targets optimization path length, observable in training cost; pruning targets
primitive count, observable directly; quantization targets bits per primitive, observable in
model size. Frame rate is the one measure all three affect, and it is the one that matters
most for the deployment scenario that motivates the study.

**Three limitations are acknowledged rather than worked around.**

The first is structural and cannot be fixed. The restored image is what a
physically-grounded method exists to produce, and it has no ground truth. Quantization error
enters the restored image directly — it is built from the quantized colour coefficients — but
before that error reaches the measured in-medium image it is **multiplied by the attenuation
map**, which is at most one and approaches zero at range. The metric therefore attenuates the
evidence of quantization damage in exactly the far-field, red-starved regions where
restoration quality matters most. The self-consistency measure of §3.7.4 partially addresses
this by comparing restored images directly, but it can only show that quantization *changed*
the restoration, never that the change was toward or away from truth.

The second is inherited and is a consequence of the evaluation harness. Metrics are computed
not on in-memory floating-point tensors but on eight-bit files written to disk and re-read, and
the harness selects a lossy container format automatically when it finds no lossless
ground-truth images. The distributed corpus is lossless, so the fallback should not trigger —
but the decision is silent, so the run logs which branch it took. The eight-bit quantisation
itself remains, and it means these figures are not comparable with the neural-radiance-field
lineage's, which are computed on linear pre-photofinished data where most of the mass sits at
low values and squared error is correspondingly small. That is a *second, independent* axis of
incomparability beyond the signal-to-noise convention, and both are stated wherever a
cross-method number appears.

The third concerns the geometric protocol of §3.7.4 and bounds what may be claimed for it.
**The geometric measures have no demonstrated external validity.** The obvious hypothesis —
that a geometrically pathological model also has a perturbed medium model, so that extent
could serve as a cheap proxy for identifiability — was tested and **failed**. The correlation
between detached primitive fraction and medium-coefficient perturbation came out at minus
zero point four zero: not weak, but the **wrong sign**. The more general form, occupancy
against the same perturbation, reached minus zero point eight zero at a significance of zero
point three three three, which on four scenes is not evidence of anything. The two diagnostics
disagree, and the disagreement is recorded as a negative result rather than resolved by
choosing the flattering one.

The consequence is a restriction on how the protocol is used, not a reason to drop it. It is
justified **by the failure modes it detects directly** — an eighty-thousand-unit bounding box,
a cloud ninety-nine point nine per cent empty, a maximum radius twenty-three thousand times
the median — each of which is a defect on its own terms and each of which is invisible to
every photometric metric in §3.7.2. It is *not* justified as a proxy for medium health, it is
never substituted for the medium-parameter trajectories that test the central hypothesis, and
no claim in this study rests on a correlation between the two. The honest description is a
**direct instrument for a failure mode the fidelity metrics cannot see**, which is a narrower
claim than the one originally hoped for and is the one the measurements support.

## 3.7.6 Summary of the metric hierarchy

**Primary — fidelity:** peak signal-to-noise ratio under both conventions, structural
similarity, perceptual similarity with a VGG backbone; full-frame, unmasked, on the composed
in-medium render against the held-out capture; reported as mean and standard deviation over
three seeds, per scene and aggregated under both weightings.

**Primary — efficiency:** rendered primitive count at five checkpoints, complete model size in
megabytes, training wall-clock and effective optimizer steps, rendering frame rate, peak
memory for training and rendering.

**Secondary:** restored-image self-consistency against the unquantized model, medium
parameter and depth-normalisation trajectories, geometric extent and occupancy — full and
opacity-gated bounding boxes, per-axis inflation, voxel occupancy, radial concentration and
spread — and qualitative restoration comparisons.

**Not reported as a headline:** any compression ratio without its per-primitive
normalisation stated; any timing figure without its device named; any signal-to-noise value
without its convention labelled; any primitive-count reduction without saying whether it is
raw or opacity-gated; and no geometric quantity as a proxy for medium identifiability, which
it has been measured not to be.
