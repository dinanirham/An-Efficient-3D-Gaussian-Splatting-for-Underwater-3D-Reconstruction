# 3.3 Preprocessing

This section draws on the pipeline, variable, and reproducibility analyses of the technical
breakdown, and is written as a procedure that a replication attempt can follow step by step.

The preprocessing stage has an unusual property in this study: it must produce not one but
two kinds of initialization input. Every configuration needs camera geometry and a sparse
point cloud in the form the baseline expects; configurations that enable the dense
initialization mechanism additionally need a set of reference-view assignments and dense
correspondences, computed before optimization begins. The two are described in sequence
below, with the rationale for each step given alongside it rather than deferred.

## 3.3.1 Step 1 — Acquire and verify the corpus

Obtain the SeaThru-NeRF dataset and verify, for each of the four scenes, that the image
directory, the sparse reconstruction directory, and the pose-and-bounds array are all
present. Record the image count per scene; these are the numbers every later aggregation
depends on, and they are unequal across scenes.

Two verification steps are not optional. First, normalise the image-directory name, or make
the loader case-insensitive: three scenes use lower case and one uses an initial capital,
which fails silently on a case-sensitive filesystem. Second, confirm the image file extension.
The evaluation harness inherited from the baseline decides whether to write renders as
lossless or lossy files by testing whether the ground-truth directory contains any
lossless images, and falls back to lossy compression without warning if it finds none. The
distributed corpus is lossless, so the fallback should not trigger — but the decision is
silent, so the run must log which branch it took.

*Rationale.* Both failures are silent rather than fatal. A path that resolves on one
filesystem and not another produces a scene that is quietly skipped; a fallback to lossy
compression produces evaluation numbers that are systematically depressed by an amount that
varies with image content. Neither would be visible in the results.

## 3.3.2 Step 2 — Pose estimation and sparse reconstruction

The corpus ships with a COLMAP reconstruction for every scene, comprising camera intrinsics,
per-image extrinsics, and a sparse triangulated point cloud in COLMAP's binary format. **Use
the distributed reconstruction; do not re-run structure-from-motion.**

*Rationale.* This is a controlled experiment on efficiency mechanisms, not on
structure-from-motion. Re-running COLMAP would introduce a source of between-configuration
variance entirely unrelated to the treatments, since feature detection and bundle adjustment
are not deterministic across runs and the resulting point cloud seeds the baseline's
primitives directly. Reusing the distributed reconstruction guarantees that every cell of the
experimental matrix begins from byte-identical camera geometry, which is what makes the
between-cell contrasts attributable to the treatments. It also guarantees comparability with
published results on these scenes, which used the same reconstruction.

If a replication must regenerate the reconstruction — for instance to add scenes — it should
do so once, freeze the output, and use the frozen copy for every configuration.

## 3.3.3 Step 3 — Scene loading, normalisation and the train/test split

Load the reconstruction through the baseline's COLMAP reader. Three things happen here that
must be controlled explicitly.

**The split.** Every eighth image by index order, after filename sort, is held out for
evaluation; the remainder are training views. At these image counts this yields three test
frames per scene. The rule is inherited unchanged from the forward-facing light-field
convention and is the same rule the baseline's predecessor and the competing underwater
methods use, which is what makes the held-out frames coincide across the literature.

**The split must be requested explicitly.** The evaluation flag defaults to off in the
baseline, and the baseline's own documentation gives a training command that omits it. With
the flag off, the test set is empty and every frame is used for training — a silent leak that
produces inflated numbers with no error and no warning. The dense-initialization codebase
carries the same defect independently, both in its configuration and hard-coded into the
arguments it emits. The run script must therefore pass the flag *and* assert that the test
set is non-empty, logging the training and test frame counts per scene.

**Scene scaling.** The loader computes a scene extent from the camera positions, which the
densification thresholds and the initial primitive scales are expressed relative to. The
baseline exposes a unit-rescaling factor that defaults to unity; it is left at unity. No
additional scene normalisation is applied.

*Rationale.* Scene scale is fixed only up to a global factor by structure-from-motion, and
the method's depth handling introduces a second normalisation downstream (Step 6), so
imposing a third here would obscure rather than clarify. Leaving the factor at unity keeps
the configuration identical to the baseline as published.

## 3.3.4 Step 4 — Radiometric handling

No radiometric preprocessing is applied. The distributed images are already globally
white-balanced, and they are consumed as eight-bit values divided by two hundred and
fifty-five into the unit interval.

*Rationale.* This is the input the baseline was designed and tuned for. Its grey-world colour
prior assumes the per-channel means of the restored image should approach one half, which is
a statement about white-balanced imagery; applying a second balance, or reverting to linear,
would invalidate that prior's calibration. It is worth recording explicitly that this differs
from the neural-radiance-field predecessor's protocol, which computes losses and metrics on
linear pre-photofinished images — a difference that makes the two methods' reported
signal-to-noise ratios non-interchangeable, and one of the reasons the evaluation section
reports under multiple conventions.

## 3.3.5 Step 5 — Primitive initialization, baseline path

For configurations without dense initialization, primitives are seeded from the sparse
reconstruction in the standard way. Each point supplies a primitive position; its colour
becomes the zero-order spherical-harmonic coefficient; scale is initialised from the mean
distance to the three nearest neighbouring points; rotation is the identity quaternion; and
opacity is initialised to one tenth in probability, stored as a logit.

One detail carries disproportionate weight for the rest of the study. The baseline sets the
spherical-harmonic order to **zero**, not the three that unmodified Gaussian splatting uses,
on the stated grounds that underwater object colour is treated as view-independent. Each
primitive therefore stores fourteen floating-point numbers rather than fifty-nine. This is a
fourfold reduction in per-primitive storage before any compression mechanism is applied, and
it is the single most consequential inherited value in the study: it caps what attribute
quantization can achieve, it removes the parameter block that the quantization mechanism's
largest codebook exists to compress, and it makes every published compression ratio in the
terrestrial literature non-comparable without renormalisation.

## 3.3.6 Step 6 — Primitive initialization, dense-correspondence path

For configurations that enable the initialization mechanism, an additional procedure runs
once, before the first optimization step.

**Select reference views.** Camera-to-world transforms are flattened into vectors and
clustered; the view nearest each cluster centre becomes a reference. The number of clusters
is a configuration parameter whose default, one hundred and eighty, exceeds the total view
count of every scene in this corpus. It is therefore set to the minimum of the default and
the number of training views, and the realised value is logged per scene.

*Rationale.* Asking a clustering procedure for more clusters than it has points is not
meaningful, and the published saturation analysis that justifies the default was measured on
corpora with an order of magnitude more views. The operating point here is necessarily off
that curve, and saying so is preferable to inheriting a number that cannot apply.

**Find neighbours.** For each reference, the three nearest views are selected by Frobenius
distance between camera transforms.

**Match densely.** Each reference-neighbour pair is passed through a pretrained dense
correspondence network, which returns a per-pixel warp field and a per-pixel confidence map.
Two of the network's features — prediction upsampling and symmetric matching — are disabled by
the initialization codebase for speed. This is a documented deviation from the matcher's
defaults; it reduces warp resolution, which matters more at these view counts than at the
counts the deviation was validated on, and it is therefore logged and flagged as a candidate
for a sensitivity check rather than accepted silently.

**Sample and triangulate.** Per pixel, the most confident neighbour is selected, and a fixed
number of correspondences is sampled from those exceeding a confidence threshold. Each
sampled correspondence is triangulated by a direct linear transform, solved in the
least-squares sense, giving a three-dimensional position. The reprojection error is computed
in both views and the larger of the two is retained as that correspondence's geometric
quality.

*A recorded gap.* The confidence threshold has **no configuration key** in the initialization
codebase; the code silently uses the matcher's own internal default. Since the threshold
governs how many correspondences survive, and since it would change if the matcher were
swapped, it is exposed and logged explicitly here rather than left implicit.

**Seed primitives.** Each surviving correspondence becomes one primitive: position from
triangulation; colour read directly from the reference image pixel; scale proportional to the
distance from the reference camera, isotropic, and then globally halved; rotation copied from
an existing primitive. Correspondences whose reprojection error exceeds tolerance are *not*
discarded — they are kept with their opacity logit set to a large negative value, rendering
them effectively invisible, and are removed later by the ordinary opacity prune. This is a
documented divergence between the initialization method's published formulation, which
describes a sampling distribution, and its implementation, which describes an opacity mask;
the practical consequence is that the primitive count immediately after initialization is
larger than the formulation implies, so both the immediate and the post-settling counts are
recorded.

**Discard the sparse points.** The structure-from-motion primitives are pruned once the
correspondence primitives have been appended.

*Rationale, and a caveat.* The triangulated set is denser and better informed, and the sparse
points would otherwise persist as low-information primitives that nothing removes. The caveat
is domain-specific and is flagged for a sensitivity check: in underwater scenes the sparse
points are the only geometry *not* derived from a matcher whose documented failure cases
include water, and with densification disabled there is no mechanism to add primitives later.
Retaining them is a one-line change and a legitimate alternative configuration.

**A convenient absence.** The initialization method's published formulation also specifies a
least-squares fit of higher-order spherical-harmonic coefficients from multi-view
observations, which its released implementation does not contain. On this baseline that gap
cannot manifest: with spherical-harmonic order zero, there are no higher-order coefficients
to fit. The composition inherits the implemented method without inheriting its largest
reproducibility problem.

## 3.3.7 Step 7 — Medium-model initialization

The medium model is initialised identically in every configuration, and no efficiency
mechanism modifies it.

The attenuation coefficients are set to a fixed hand-chosen triple that attenuates red
fastest; the backscatter coefficients and the water colour at infinity are drawn uniformly at
random. A fourth parameter — a learned background colour, initialised to a fixed blue-green
prior — is optimised throughout the pre-medium phase of training against the opacity loss,
and is then **copied into the water colour at infinity** at the moment the medium model is
switched on.

*Rationale.* This transfer is the mechanism that replaces a uniform random initialization of
the water colour with a data-derived estimate, and it matters more than its obscurity
suggests. The degenerate solution in which the medium does nothing — no attenuation, no
backscatter, restored image equal to the capture — is a *global optimum* of the photometric
loss, at least as good as the intended solution, and the auxiliary dark-channel prior is the
only force pushing away from it. Starting the water colour at an observed value rather than
at noise is plausibly load-bearing for convergence. It is recorded here because the parameter
and the transfer appear nowhere in the baseline's publication, only in its code, and a
replication built from the paper would omit both.

## 3.3.8 Step 8 — Freeze and record the preprocessing state

Before the matrix is run, freeze and record: the reconstruction used, the per-scene training
and test frame lists, the realised reference-view count and confidence threshold for the
dense-initialization path, the initial primitive count on each path, and the random seed.
Write this alongside the fully resolved configuration for each run.

*Rationale.* Three of the four codebases involved contain parameters that are set in
configuration files but contradicted by their own documentation, or read from the command
line and then ignored, or defaulted to values that silently disable the mechanism entirely.
The only defence that scales to a campaign of this size is to have each run write down what it
actually did.
