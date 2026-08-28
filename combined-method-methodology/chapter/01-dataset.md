# 3.2 Dataset

This section draws on the variable and reproducibility analyses of the technical breakdown,
on the SeaThru-NeRF reference breakdown, and on a direct inspection of the dataset as it
exists on disk.

## 3.2.1 Provenance

All experiments use the **SeaThru-NeRF dataset**, introduced alongside the neural radiance
field method of the same name and subsequently adopted as the de facto benchmark for
physically-grounded underwater novel-view synthesis. It is the dataset the baseline method
evaluates on, the dataset the closest competing underwater efficiency methods evaluate on,
and therefore the only corpus on which this study's results can be placed beside published
numbers without re-running other people's systems.

The imagery was captured by Matan Yuval at three geographic locations — Curaçao in the
Caribbean, two sites in the Red Sea, and Panama — using a digital single-lens reflex camera
in an underwater housing behind a dome port. The frames distributed with the dataset are
resized and globally white-balanced versions of the original linear captures; the full-size
linear images are available only on request from the original authors. Each scene directory
contains the white-balanced images, a sparse structure-from-motion reconstruction produced by
COLMAP, and a pose-and-bounds array in the format used by the forward-facing light-field
literature.

The dataset is distributed for research use. The camera pipeline used to produce the
white-balanced images follows a documented software platform for camera imaging pipelines,
which matters because it means the radiometric transformation applied to the raw sensor data
is a known and reproducible one rather than an opaque in-camera process.

## 3.2.2 Scene composition and diversity

The corpus comprises four scenes and eighty-eight images in total, verified by direct
inspection rather than taken from the literature:

| Scene | Images | Location | Character |
|---|---|---|---|
| Curasao | 21 | Caribbean | Coral reef structure, moderate visibility |
| IUI3-RedSea | 29 | Red Sea (Eilat) | Reef with substantial far-field extent |
| JapaneseGradens-RedSea | 20 | Red Sea | Reef, densely structured foreground |
| Panama | 18 | Pacific coast of Panama | Turbid, strongly attenuated |

The optical diversity is the dataset's principal virtue and the reason it became a benchmark.
The three regions differ substantially in water type. Red Sea water is comparatively clear
and blue-shifted; Caribbean water is clear but with a different particulate signature; and
the Panama site is markedly more turbid, with visibility short enough that the far field is
almost entirely veiling light. Because the physical image formation model separates
wavelength-dependent attenuation from wavelength-dependent backscatter, and because those two
coefficient sets are genuinely distinct in natural water rather than proportional to one
another, a corpus that spans several water types exercises the medium model in a way a
single-site corpus would not. A method that fits one water type by absorbing model error into
its colour estimates will be visibly worse on another.

Scene geometry also varies in a way that matters for the mechanisms under study. All four
captures are forward-facing rather than object-centric or unbounded: the camera translates
across a reef face rather than orbiting an object or exploring a large open environment. This
constrains the baseline distribution between views, which is directly consequential for the
initialization mechanism, since triangulation from dense correspondences becomes
ill-conditioned as view rays approach parallelism. The depth range within each scene also
varies considerably — the Red Sea and Curaçao scenes contain substantial far field, while the
Panama scene is effectively depth-truncated by turbidity — which exercises the depth-dependent
terms of the medium model across a useful range.

## 3.2.3 Capture characteristics

Three characteristics of the capture bear on the methodology and are stated here because they
constrain decisions taken later in the chapter.

**The images are white-balanced, not linear.** The distributed frames have already had a
global white balance applied. This is the input the baseline expects and trains on, and it is
what makes its grey-world colour prior sensible. It also means that any comparison against
methods that evaluate on linear pre-photofinished imagery is comparing two different
quantities: peak signal-to-noise ratio computed on linear data and on eight-bit
display-referred data are not interchangeable, because linear data concentrates most of its
mass at low values where squared error is small. This is one of two independent reasons the
evaluation-metrics section reports results under more than one convention.

**View counts are small.** Between eighteen and twenty-nine images per scene is an order of
magnitude fewer than the terrestrial benchmarks on which the three efficiency mechanisms were
developed and tuned. This has a direct and specific consequence for the initialization
mechanism, whose default configuration selects one hundred and eighty reference views by
clustering camera poses — a number that exceeds the total view count of every scene here.
The reference count must be re-derived per scene rather than inherited, and the resulting
operating point sits well off the saturation curve the initialization method published. The
implementation-details section states how this is handled and the limitations section states
what it costs.

**Every scene ships with a COLMAP reconstruction.** Camera intrinsics, extrinsics, and a
sparse point cloud are provided, in the binary format the baseline's data loader expects.
This removes pose estimation as a source of variance between configurations — every cell of
the experimental matrix begins from byte-identical camera geometry — and it means the study
measures reconstruction and efficiency rather than structure-from-motion robustness.

## 3.2.4 Suitability for reconstruction-fidelity claims

The dataset supports fidelity claims within clear limits.

Its principal strength is that the held-out evaluation frames are *the same frames* other
published methods hold out. The convention throughout this lineage is to reserve every eighth
image by index order, which yields three test frames per scene at these counts. Because the
baseline, its neural-radiance-field predecessor, and the competing underwater efficiency
methods all use this rule on these scenes, the test frames coincide, and a fidelity number
produced here is measured on the same pixels as a published one. That is a stronger form of
comparability than most cross-paper comparisons in this literature enjoy, and it is worth
protecting.

Its principal weakness is that three test frames per scene, across four scenes, is twelve
evaluation images in total. Differences of a few tenths of a decibel — the magnitude at which
the source methods' own ablations operate — cannot be distinguished from run-to-run variation
on that sample without repeated runs and reported dispersion. This is not a hypothetical
concern: the baseline's published ablation table contains differences below half a decibel
reported from single runs with a random default seed and no error bars. The validity section
sets out the repetition protocol that follows from this.

A second and more fundamental limitation is that the dataset provides **no ground truth for
restoration**. The scientific interest of a physically-grounded underwater method is that it
separates the scene from the water and can render the scene as it would appear without the
water. There is no reference for that output, and there cannot be one — obtaining it would
require draining the ocean, as the baseline's authors put it. Every restoration comparison in
this literature is qualitative, and every quantitative metric measures the *in-medium*
reconstruction only. This has a specific and under-appreciated consequence for a compression
study, developed in the evaluation-metrics section: quantization error enters the restored
image directly, but is multiplied by the attenuation map before it reaches the measured
in-medium image, so the metric systematically under-reports quantization damage in exactly
the far-field, red-starved regions where restoration matters most.

## 3.2.5 Suitability for efficiency claims

The dataset supports efficiency claims more strongly than fidelity claims, and the asymmetry
is worth making explicit because it shapes which of this study's conclusions are robust.

Efficiency quantities — primitive count, model size on disk, training wall-clock, effective
optimizer steps, rendering frame rate, peak memory — are measured per run rather than per
test frame. A four-scene corpus therefore yields four independent measurements of each
efficiency quantity per configuration per seed, not twelve pixel-level comparisons, and the
effects under study are large. Where the fidelity differences of interest are fractions of a
decibel, the efficiency differences are multiples: the pruning mechanism reports an
eight-and-a-half-fold reduction in primitive count on terrestrial data, and quantization
reports storage reductions of an order of magnitude or more. Effects of that size survive a
small sample in a way that sub-decibel quality differences do not.

The four scenes also differ enough in content to stress the efficiency mechanisms
differentially, which is more informative than four replicates of the same scene would be. A
densely structured foreground scene and a turbid depth-truncated scene will converge to very
different primitive counts under the same budget policy, and the importance-based sampling
that selects which primitives survive is explicitly acknowledged in its source literature to
be scene-type-dependent.

## 3.2.6 Limitations that bound external validity

Four limitations follow from the corpus and are carried forward to the limitations section.

**Four scenes is a small sample for generalisation.** Every claim is an average over four
points from three geographic locations. Water types beyond these — very high turbidity, green
inland water, deep low-light environments — are unrepresented, and the medium model's
behaviour outside the represented range is untested.

**All captures are forward-facing.** No orbital or unbounded capture is present. Since the
initialization mechanism's quality depends on baseline geometry between matched views, and
since the pruning mechanism's importance metrics were developed and validated on
object-centric and unbounded terrestrial scenes, both mechanisms are being applied outside
the capture geometry they were tuned for.

**All imagery is from a single camera and housing.** Lens, dome port, sensor and the
white-balance pipeline are constant across the corpus, so nothing here separates method
behaviour from camera-specific radiometry.

**The imagery is static and daylit.** Caustics, dynamic scene content, and artificial
illumination are absent — conditions the baseline explicitly places out of scope, and which
this work inherits without change.

A natural extension, available and not pursued in this study, is to add the synthetic
underwater and fog corpora the baseline constructs by applying known medium constants to a
terrestrial scene, together with its robot-captured saltpond sequence. Synthetic data would
supply the one thing this corpus cannot: known ground-truth medium coefficients, against
which the central hypothesis about medium-parameter perturbation could be tested directly
rather than through a proxy diagnostic.

## 3.2.7 A practical note on the distributed copy

Two details of the local copy are recorded because they will otherwise cause silent failures
in replication. First, three scenes place their imagery in a directory named in lower case
while `IUI3-RedSea` uses an initial capital, which breaks a hard-coded path on a
case-sensitive filesystem. Second, the Curaçao scene contains twenty-one images where the
original publication describes twenty for that scene; the discrepancy is a single frame and
does not change the number of held-out test frames, but it should be confirmed against the
sparse reconstruction's frame list rather than assumed harmless.
