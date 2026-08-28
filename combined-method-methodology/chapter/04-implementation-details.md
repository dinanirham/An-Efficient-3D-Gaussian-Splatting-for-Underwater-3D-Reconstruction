# 3.5 Implementation Details

This section draws on the variable, pipeline, implementation-delta, computational-profile and
reproducibility analyses of the technical breakdown, and is written as a procedure.

## 3.5.1 Hardware

All experiments are run on a single graphics processing unit, and **the device is named in
the results**. This is not a formality. Of the four methods composed here, two name their
hardware and re-run their baselines on it, one names hardware without re-running, and the
underwater baseline names none at all, stating only that a consistent set of hardware was
used. Any comparison of this study's timings against that baseline's published figures is
therefore between an identified device and an unidentified one, and must be labelled as such
rather than presented as a like-for-like speedup.

Two practical consequences follow. Peak memory is an absolute footprint and transfers between
devices without adjustment; the baseline's reported four gigabytes is a real constraint that
any modern accelerator satisfies comfortably. Wall-clock time and frame rate do **not**
transfer. Gaussian rasterization is bound by tile sorting, atomic accumulation and memory
bandwidth rather than by dense arithmetic throughput, so speedups across device generations
are consistently sub-linear in nominal compute. The pruning mechanism's source publication
provides a rare direct data point for this — the same method measured on two devices several
generations apart shows a five- to six-fold difference in training time against a much larger
difference in nominal capability.

Because every cell of the matrix is measured on the same device with the same software build,
the **between-cell contrasts** — which is what the study's conclusions rest on — are internally
valid regardless of which device is used. Only the absolute figures and the comparisons
against published numbers are device-sensitive.

## 3.5.2 Software environment

The four source codebases cannot coexist as published. The underwater baseline targets a
mid-generation compute architecture in its container definition, with the current generation
explicitly commented out; the dense-initialization codebase is the most modern of the four and
uses a current toolkit and Python release; the pruning codebase pins a Python release that has
reached end of life and a compute toolkit that predates the current architecture entirely; and
the quantization codebase is not a standalone project at all but a **file overlay** — four
files copied over an unmodified Gaussian splatting checkout.

A single environment is therefore constructed rather than four maintained. The construction is
part of the method's implementation and is described here rather than relegated to a
footnote.

**Base.** A current compute toolkit and Python release, with the underwater baseline as the
root project. Its dependency set is the least modern of the four but the most central, since
it supplies the medium model, the loss, the data loader and the evaluation harness.

**Rasterization extension.** One kernel must serve two purposes: the baseline's second
depth-rendering pass, which overrides primitive colour with camera-frame depth, and the
pruning mechanism's per-primitive importance accumulators, which the standard kernel does not
return. The baseline's addition is a Python-level second invocation with an overridden colour
argument; the pruning mechanism's additions are inside the kernel itself. **The baseline's
depth pass is therefore ported onto the pruning mechanism's forked kernel**, rather than the
reverse, and the combined extension is rebuilt for the target compute architecture. Both
outputs are unit-checked against a synthetic scene before the matrix is run, because a build
that produces one correct tensor set and one incorrect one will not crash.

**Quantization.** The quantization mechanism's four method files are overlaid onto the
baseline rather than onto stock Gaussian splatting. Because the mechanism is distributed as an
overlay in the first place, this is a small and well-defined port: everything not overridden
is inherited from whatever project it sits on top of.

**Correspondence matcher.** The dense matcher is installed as a package and its pretrained
weights are **pre-staged**, not downloaded at first use. The initialization codebase fetches
them on demand, which fails on a compute node without outbound network access and, worse,
succeeds intermittently on one that has it.

## 3.5.3 The feature-flag scheme

The experimental matrix requires eight configurations differing only in three binary flags.
The underwater baseline's argument parser makes this structurally impossible as shipped: it
registers roughly a dozen boolean options that default to enabled using a parser action that
can only *set* a flag, never clear it. A dozen behaviours that default on cannot be turned off
from the command line at all.

A **configuration layer** is therefore added above the parser. Each cell of the matrix is
described by a configuration file that names the three mechanism flags and any overrides; the
layer resolves the file against the parser's defaults and writes the resolved values before
the model's parameter objects are constructed. The three mechanism flags are:

- **`m1_dense_init`** — enable the correspondence-based initialization and disable adaptive
  density control.
- **`m2_simplify`** — enable importance-weighted simplification to the primitive budget at the
  two designated iterations, and enable the medium re-identification burst that follows each.
- **`m3_quantize`** — enable quantization-aware clustering from the designated start iteration.

Three requirements attach to this layer and are not optional.

**Every run dumps its fully resolved configuration** to its output directory. Three of the four
codebases contain parameters that are set in one place and contradicted in another — a
configuration file that disables densification while the documentation claims it is enabled by
default, a batch size that is read and never used, a correspondence count that differs between
the configuration and the documented command. The only defence that scales to ninety-six runs
is for each run to record what it actually did.

**Every run asserts that each enabled mechanism fired.** Two of the three mechanisms are
silent no-ops at their upstream defaults: the dense-initialization codebase defaults its
training-epoch count to zero, so training does nothing; the quantization codebase defaults its
start iteration to the total iteration count, so clustering never begins. Neither produces an
error. The assertion is a few lines and prevents an entire class of invalid cell.

**Every run asserts a non-empty test set.** The evaluation flag defaults off in two of the four
codebases, in one case additionally hard-coded into the arguments the trainer emits.

## 3.5.4 Training schedule and iteration gating

The nominal budget is thirty thousand iterations, which is the shared convention across all
four source methods. The gating structure is dense enough to warrant a table.

| Iteration | What happens |
|---|---|
| 0 | Primitive initialization: sparse points, or dense correspondences if the initialization mechanism is enabled |
| 500 – 15 000 | Adaptive density control every hundred iterations, with periodic opacity reset — **unless** the initialization mechanism is enabled, in which case density control is off and a continuous opacity decay runs every ten steps instead |
| **10 000** | The medium model switches on. One thousand medium-only steps with primitives frozen, then two thousand colour-only steps; the learned background colour is transferred into the water colour at infinity |
| 10 000 | The grey-world prior enters the objective |
| 10 000 onward | Fifty medium-only steps every hundred geometry steps |
| 15 000 | Adaptive density control ends. **Simplification event one**: importance accumulation over all training views, intersection preservation, stochastic subsampling to the budget, followed by a medium re-identification burst |
| **20 000** | **Simplification event two**: a light deterministic prune of the lowest-importance mass, followed by a second medium re-identification burst |
| **> 20 000** | Quantization-aware clustering begins: centroids re-averaged every iteration, assignments recomputed every hundredth |
| 30 000 | Training ends |

Three notes on this schedule.

**The medium warm-up transition is left at ten thousand iterations in every configuration.**
Under dense initialization there is an argument for lowering it — the initialization places
primitives close to their final positions, so the rendered depth should stabilise far earlier
— but nothing in the available evidence measures how many steps a densely-initialised model
needs before its depth is stable. Holding the gate fixed keeps the untreated baseline and the
initialization cell differing in exactly one factor, which is the property the factorial
design depends on. The alternative is recorded as a follow-up.

**Quantization is deliberately placed after both simplification events.** Its source method
starts it earlier, but a codebook fitted before a large prune is fitted to a population about
to be discarded. This leaves a shorter quantization-aware phase than the source uses.

**The iteration count is not the optimizer-step count.** The baseline's alternating schedule
advances the loop counter only on geometry steps; the medium-only bursts are skipped past it.
At default settings a nominally thirty-thousand-iteration run performs roughly forty-three
thousand optimizer steps, each paying the cost of both rasterization passes, and the two
medium re-identification bursts add further steps that likewise do not appear in the count.
**Every timing figure in this study is reported against effective optimizer steps as well as
wall-clock**, and any comparison against a figure reported only in iterations is noted as
such.

## 3.5.5 Hyperparameters

### Inherited from the baseline, unchanged in every cell

Spherical-harmonic order zero. Photometric mixing weight of one fifth for the structural
similarity term. Position learning rate decaying exponentially across the run; separate,
constant learning rates for colour, opacity, scale and rotation. Densification gradient
threshold, density percentage, densification interval and opacity-reset interval at the
substrate's standard values. Medium optimizer learning rate of one hundredth, with fifty
medium steps per hundred geometry steps.

The six auxiliary loss weights are inherited exactly and span two orders of magnitude: unity
for the depth-weighted reconstruction and dark-channel terms, one tenth for the grey-world
prior, two for the saturation cap and the depth-smoothness term, and **one hundredth for the
opacity prior** — the smallest weight in the objective attached to the term that contributes
most to reconstruction quality.

### Initialization mechanism

Three nearest neighbours per reference view; scale factor of one thousandth of the distance to
the reference camera, halved globally; reprojection tolerance of one hundredth. Two parameters
depart from their upstream defaults and are logged per scene: the **reference-view count** is
set to the minimum of the upstream default and the number of training views, because the
default exceeds the total view count of every scene in this corpus; and the **correspondence
confidence threshold**, which has no configuration key upstream and silently inherits the
matcher's internal default, is exposed and recorded.

The two undocumented schedule behaviours — the continuous opacity decay and the clamped
position learning rate — are left enabled, because disabling them would depart further from
the mechanism as evaluated, but they are recorded as active and flagged as interacting with
the baseline's opacity prior.

### Pruning mechanism

Simplification at fifteen and twenty thousand iterations. The **primitive budget replaces the
upstream sampling ratio** and is set from the untreated baseline's converged primitive count,
so that it binds in every configuration; the realised post-simplification count is reported
per run, because the subsampling is stochastic and driven by device-computed probabilities and
therefore varies run to run even at a fixed seed. The deterministic prune at the second event
retains the top ninety-nine per cent of cumulative importance mass. The importance metric is
chosen explicitly and justified, since the upstream option has no default and neither of its
two variants was designed for a scattering medium.

### Quantization mechanism

Three codebooks — zero-order colour, scale, rotation — the higher-order harmonic codebook
being absent because the parameter block it would compress does not exist. Assignment interval
of one hundred iterations, one clustering iteration per update, and codebook sizes reported
explicitly rather than inherited, since the source method's shipped script and its publication
disagree on every one of them. Scale is clustered **before** its exponential activation and
rotation **before** normalisation, so that Euclidean distance in the clustered space is
meaningful. Position and opacity are never quantized.

Two departures from the source method are made and declared. The **opacity sparsity penalty is
disabled**, so that count reduction is attributable to the pruning mechanism alone and the two
factors remain independent. The **index bit width is derived from the codebook size** rather
than from the primitive count; the source implementation uses the latter, inflating stored
indices by roughly seventy per cent, and reproducing that inflation would misstate the
compression achieved. Both changes mean this study's quantization figures are not directly
comparable to the source method's published table.

## 3.5.6 Logging and stored artifacts

Beyond the standard checkpoints, three quantities are logged that no source method records,
and they exist to make the study's central hypotheses measurable rather than argued.

**The per-frame depth normalisation constants**, recorded before and after each simplification
event. These test directly whether primitive reduction rescales the medium model's input.

**The nine medium coefficients and the water colour**, at every checkpoint. A discontinuity at
a simplification boundary is the signature of the identifiability failure; its absorption
within the re-identification burst is the signature of the remedy working. Under quantization,
drift in these coefficients relative to an unquantized run tests whether the medium model is
absorbing codebook error — which, if it occurs, means the coefficients stop being interpretable
as a medium estimate in exactly the configurations where compression is being claimed.

**The primitive count at five points**: immediately after initialization, after the opacity
dynamics have settled, and before and after each simplification event. The first two differ
under dense initialization because failed correspondences are retained with near-zero opacity
rather than deleted, so a single post-initialization number is ambiguous.

The stored model comprises the unquantized attributes, the index streams, the codebooks and
their metadata, and the medium parameter files. **All of these count toward reported model
size.** The quantization mechanism's published size figures have no decoder network to
account for, which is a genuine advantage of that approach; this system has the nine medium
scalars instead, which are negligible in magnitude but must appear in the accounting for it to
be an accounting rather than a claim.
