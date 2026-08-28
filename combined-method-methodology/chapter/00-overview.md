# 3.1 Research Design and Overview

This section draws on the taxonomy, pipeline, and novelty-defensibility analyses of the
technical breakdown, together with the reconnaissance and literature scan that preceded them.

## 3.1.1 Research paradigm

This study is quantitative, experimental, and comparative. It takes an existing
physically-grounded method for underwater three-dimensional reconstruction as a fixed
baseline, introduces three efficiency mechanisms drawn from the terrestrial Gaussian
splatting literature as controlled treatments, and measures the effect of each treatment and
of every combination of treatments on a common set of underwater scenes under a common
evaluation protocol. The design is a complete two-level, three-factor factorial: eight
configurations, from the untreated baseline to the fully treated system, each measured on
every scene with repeated runs.

The choice of a factorial design over the more common cumulative ablation ladder is
deliberate and is one of the study's methodological commitments. A ladder — baseline, plus
one, plus two, plus three — supports only one direction of inference: it reports what each
addition contributes *on top of what came before*, and it cannot answer what removing a
component from the complete system would cost. The distinction is not pedantic. Reviewing the
four methods this work builds upon, their ablation tables use four structurally different
designs between them, at least one of which is ambiguous even to a careful reader, and in one
case the terminal row of a supposedly complete ladder does not match the paper's own reported
full model. A factorial matrix removes the ambiguity by construction: every cell is a complete
configuration, effects are estimated as contrasts between cells, and both the
addition-from-below and the removal-from-above readings are available from the same data.
Interaction terms — the quantities this study is most interested in — are then differences of
differences within that same table, rather than something inferred across incommensurable
rows.

The paradigm is explanatory rather than merely descriptive. The study does not simply ask
whether three known efficiency techniques improve efficiency on underwater data; it asks
whether they remain *independent* when the reconstruction system they are applied to carries
a physical model of the medium, and it identifies in advance a specific mechanism by which
they might not.

## 3.1.2 The problem, and why efficiency is the right question

Reconstructing three-dimensional scenes from underwater imagery is difficult for reasons that
are optical rather than geometric. Light travelling through water is attenuated in a
wavelength-dependent way and is scattered back toward the camera by suspended particles, so
the observed image is a range-dependent mixture of the true scene radiance and a veiling
haze. A reconstruction method that ignores this will explain the haze the only way it can —
by inventing geometry in the water column — producing a model that reproduces the training
images well and represents nothing physical. Methods that model the medium explicitly avoid
this failure, and the baseline adopted here does so by rendering a medium-free radiance
field and composing it through a revised underwater image formation model before comparing
against the capture.

That solution comes at a price the literature has largely accepted without examination. The
baseline requires a second rendering pass to obtain the depth its medium model consumes,
which roughly doubles rendering cost relative to unmodified Gaussian splatting; it runs a
bursty alternating optimization schedule that adds roughly forty per cent more optimizer
steps than its nominal iteration count suggests; and it inherits from its substrate an
unbounded and unreported primitive count. Where the terrestrial Gaussian splatting community
has produced a rich body of work on making these representations smaller, faster to train,
and cheaper to store, the underwater literature has engaged with that work only sparsely, and
almost never on more than one efficiency axis at a time.

Efficiency is not an aesthetic concern in this domain. Underwater reconstruction is
disproportionately deployed on autonomous platforms with hard power, memory and thermal
budgets, and the value of a physically-grounded model is realised only if it can be
carried into the field. The gap between what the terrestrial efficiency literature has
established and what the underwater literature has adopted is therefore both real and
consequential.

## 3.1.3 Overarching research question

> **Can three efficiency mechanisms developed independently for terrestrial 3D Gaussian
> splatting — dense deterministic initialization, budget-based primitive reduction, and
> attribute vector quantization — be composed onto a physically-grounded underwater
> reconstruction baseline without degrading reconstruction fidelity; and do they remain
> mutually independent when the system they are applied to estimates a physical medium from
> rendered geometry?**

The second clause carries the study's weight. The first clause is an engineering question
with an expected answer: each of the three mechanisms is documented, in its own literature,
as orthogonal to the others, and the initialization mechanism in particular has been shown to
drop into three unmodified competing systems and improve all three without any hyperparameter
retuning. The second clause asks whether that orthogonality is a property of the mechanisms
or a property of the terrestrial systems they were demonstrated on — systems whose rendering
equations contain no depth-dependent term and no medium at all.

## 3.1.4 Hypotheses

Five hypotheses follow, stated so that each maps onto a specific contrast in the experimental
matrix. Their derivation is given in the proposed-method and experimental-design sections;
the reasoning is summarised here so that the chapter's structure is legible from the start.

**H1 — Individual efficiency gains transfer.** Each mechanism applied alone reduces its target
cost — optimization path length, primitive count, or storage — relative to the untreated
baseline, and does so in the direction its terrestrial literature reports.

**H2 — Individual gains are attenuated relative to their terrestrial magnitudes.** The
*magnitude* of each gain is smaller than published terrestrial figures. For quantization this
is predicted structurally rather than empirically: the baseline stores fourteen floating-point
numbers per primitive rather than the fifty-nine that the compression literature assumes,
because it uses zero-order spherical harmonics, and the forty-five-coefficient block that
attribute quantization compresses most aggressively simply does not exist. Any compression
ratio reported here is therefore not comparable to published figures without renormalisation,
and cannot approach them.

**H3 — Quality cost concentrates in the water column.** Where quality degrades, it degrades
disproportionately in low-texture, depth-ambiguous regions. This prediction is unusually well
supported before any measurement, because three of the four methods being composed
independently name that same region as their weak point: the baseline reports that
unmodified Gaussian splatting fills the water column with spurious primitives and devotes a
dedicated loss term to suppressing them; the initialization mechanism depends on a dense
correspondence network whose documented failure cases are textureless and non-Lambertian
surfaces, water among them explicitly; and the pruning mechanism's depth-driven machinery
fails wherever no reliable depth exists, a condition its authors illustrate with sky and
which the water column reproduces exactly.

**H4 — Primitive reduction perturbs medium estimation.** This is the study's central and most
specific hypothesis. The baseline's medium model consumes a rendered depth map that is
renormalised to the unit interval independently for every frame, and the medium coefficients
enter the image formation model only through their product with that depth. Removing a large
fraction of the primitives changes the nearest and farthest surfaces contributing to each
frame, hence changes the normalisation, hence rescales the medium model's only spatial input
mid-training — which is formally indistinguishable from a change in the medium coefficients
themselves. The baseline's well-posedness machinery is designed to prevent the optimizer from
*exploiting* that ambiguity; none of it prevents the ambiguity from being *injected* by an
external event. H4 predicts a measurable discontinuity in the estimated medium parameters at
the pruning event, and predicts that a medium-only re-identification step immediately
afterwards removes it.

**H5 — Pruning and quantization interact sub-additively; initialization and quantization do
not.** The most recent method in the pruning lineage was motivated by precisely the claim that
count reduction and attribute compression do not compose, because a sparser set of primitives
becomes more sensitive to lossy compression of the attributes that remain. If that claim
holds in this domain, the paired configuration should lose more quality than the sum of its
parts. Conversely, initialization and quantization share no pipeline stage, and quantization
by construction never touches primitive position or opacity, so this pair is predicted to
behave additively.

## 3.1.5 Position within the literature

The underwater Gaussian splatting field has moved quickly and has begun to address
efficiency, but along different axes from those studied here. One line of work achieves
compactness by changing the primitive type itself, replacing standard anisotropic Gaussians
with tensorized higher-order primitives and reporting substantial parameter reductions.
Another couples a learnable underwater formation model with an uncertainty-driven pruning
branch that removes floating primitives, and compresses the *medium field* by tensor
decomposition. A third reduces redundancy in a simultaneous-localisation setting by merging
primitives within voxels. Several recent methods reduce spherical-harmonic order to degree
zero for compactness — a choice the baseline adopted for a different reason, namely that
underwater object colour is treated as view-independent.

None of these combines dense correspondence-based initialization, budget-based primitive
reduction, and attribute vector quantization; and the reconnaissance found no underwater
Gaussian splatting method at all that applies clustering-based attribute quantization. The
composition idea is not itself novel — terrestrial work has produced joint structured pruning
and quantization frameworks, and multi-stage pipelines that chain pruning, spherical-harmonic
adjustment and entropy-constrained quantization — but those systems are medium-free, and the
question this study asks does not arise in them.

The contribution is therefore positioned as methodological rather than as a new architecture.
It is not "a better underwater reconstruction system"; it is an account of what has to change
when efficiency mechanisms designed for a medium-free representation are applied to one that
estimates a medium from its own rendered geometry, together with the experimental design that
would establish whether those changes are sufficient. The honest scope of that contribution,
including what the present evidence does and does not establish, is set out in the
scope-and-limitations section.

## 3.1.6 How the chapter is organised

The chapter answers the research question in the order the question decomposes.

The **dataset** section establishes the empirical ground: which underwater scenes are used,
what optical and geometric diversity they span, and why a corpus of this size and character
can support efficiency claims more confidently than fidelity claims. The **preprocessing**
section gives the data-preparation procedure in enough detail for a replication attempt to
follow it, including the pose estimation, the radiometric handling, and the initialization
inputs, with the rationale for each step.

The **proposed method** section is the chapter's core and is given the most space. It
develops the baseline's formulation, introduces each of the three mechanisms at its insertion
point in the training loop, and then treats at length the integration logic that constitutes
this work's own technical content — the decisions that are neither in the baseline nor in any
of the three mechanisms, and that exist because the composition creates conditions none of
them was designed for. The **implementation details** section supplies the hardware, software,
hyperparameters, schedule, and feature-flag scheme a replication would need.

The **experimental design** section lays out the eight-cell matrix, states what each cell
isolates, connects each contrast to one of the five hypotheses, and makes explicit the
inferential structure that distinguishes this design from the ablation tables of the methods
it builds upon. The **evaluation metrics** section defines each instrument precisely —
including the several places where superficially standard metrics are computed in
incompatible ways across the source literature — and distinguishes primary from secondary
measures. The **validity and reproducibility** section addresses seeding, repetition,
dispersion, and the specific threats to internal and external validity this design carries.

The **scope and limitations** section states plainly what the methodology does not claim,
and the **summary** closes by restating the method, the experimental logic, and what the
results chapter must establish.
