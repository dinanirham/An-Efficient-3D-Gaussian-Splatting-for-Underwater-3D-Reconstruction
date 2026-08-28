# 3.6 Experimental Design

This section draws on the pipeline, constraint, computational-profile and reproducibility
analyses of the technical breakdown, and connects each experiment to a hypothesis stated in
§3.1.

## 3.6.1 The design, and why it is factorial

The experiment is a complete two-level, three-factor factorial. The factors are the three
efficiency mechanisms; each is either present or absent; the eight resulting configurations
are run on all four scenes with repeated seeds.

| ID | Dense init | Budget prune | Quantization |
|---|---|---|---|
| **A0** | — | — | — |
| **A1** | ✅ | — | — |
| **A2** | — | ✅ | — |
| **A3** | — | — | ✅ |
| **A4** | ✅ | ✅ | — |
| **A5** | ✅ | — | ✅ |
| **A6** | — | ✅ | ✅ |
| **A7** | ✅ | ✅ | ✅ |

The alternative — a cumulative ladder, adding one mechanism at a time — is what all four
source methods use, and it is the wrong instrument for the question this study asks.

A ladder supports one direction of inference only. From rows reading *baseline*, *baseline plus
A*, *baseline plus A plus B*, one can say what B contributed **on top of A**, and nothing else.
One cannot say what removing B from the complete system would cost, because no row of the
table removes it. This distinction is routinely elided in the literature this work builds on:
of the four source methods, one publishes a cumulative ladder whose terminal row does not
match its own reported complete model, one publishes three structurally different tables all
labelled "ablation", one publishes four, and one publishes a table whose direction cannot be
determined even by careful reading because the marks distinguishing its rows do not survive
text extraction from the document.

A factorial matrix removes the ambiguity by construction. Every cell is a complete
configuration. A mechanism's effect is a **contrast between cells**, and both directions are
available from the same eight measurements:

- **Effect from below** — the mechanism added to the bare baseline: A1−A0, A2−A0, A3−A0.
- **Effect from above** — the mechanism removed from the complete system: A7−A6 removes dense
  initialization, A7−A5 removes pruning, A7−A4 removes quantization.
- **Interaction** — the difference between the two readings, which is the quantity of primary
  interest.

If the two readings agree, the mechanisms are independent and the ladder would have been
adequate. If they disagree, the mechanisms interact, and the disagreement is itself the
result. **The design has no uninformative outcome on that comparison**, which is why it was
chosen.

## 3.6.2 What each cell isolates

**A0 — the untreated baseline.** The reference point for every contrast, and a *prerequisite*
rather than merely a comparison: the primitive budget for the pruning mechanism is set from
A0's converged count, and A0's count is not reported in any publication of the baseline, only
logged internally. The matrix therefore cannot be configured until A0 has been run and
measured. A0 also serves as an internal validity check — if it does not reproduce the
baseline's published quality on these scenes within run-to-run variation, the environment is
wrong and no other cell is interpretable.

**A1 — dense initialization alone.** Isolates the effect of replacing gradient-triggered
densification with a one-shot correspondence-based initialization. The mechanism does not
touch the objective, so any change in quality is attributable to the geometry the optimizer
starts from and to the two undocumented schedule behaviours the mechanism brings with it.
This cell also carries the study's first domain-specific risk: the correspondence network's
documented weak cases include water, and with densification disabled there is no mechanism
to add primitives later.

**A2 — budget pruning alone.** Isolates the effect of reducing the primitive population to a
fixed count by importance-weighted stochastic sampling. This is the **most important single
cell in the design**, because it is where the study's central hypothesis is tested: it is the
only single-mechanism cell in which the primitive population changes discontinuously
mid-training, and therefore the only one in which the medium model's input can be rescaled.

**A3 — quantization alone.** Isolates the effect of replacing per-primitive attributes with
codebook indices. Because position and opacity are never quantized, this cell cannot perturb
either of the quantities the baseline's well-posedness argument depends on most, and it is
predicted to be the best-behaved of the three single-mechanism cells.

**A4 — initialization and pruning.** Tests whether two mechanisms that both reduce primitive
count compose. It carries a design hazard requiring explicit control: if dense initialization
already converges below the budget, the pruning step removes nothing and this cell silently
becomes a re-run of A1. The budget is therefore set from A0 rather than as a ratio, and
**whether the budget bound is reported per run** — a null interaction from a non-binding
budget is an artifact, not a finding.

**A5 — initialization and quantization.** The least-coupled pair: the two mechanisms occupy
non-adjacent pipeline stages and share no variable, since quantization touches neither
position nor opacity. Predicted to be approximately additive; a large interaction here would
be the most surprising result in the matrix and would indicate something unmodelled.

**A6 — pruning and quantization.** Tests the one interaction for which external theory exists.
The most recent method in the pruning lineage was motivated by the claim that count reduction
and attribute compression do not compose — a sparser population being more sensitive to lossy
compression of what remains — and answered it by co-designing the two. This cell tests the
un-co-designed composition in a new domain. Both outcomes are publishable: a sub-additive
result confirms the claim underwater; a clean null refutes it in this regime.

**A7 — fully stacked.** The system as a deployable artifact, and the source of the
effect-from-above contrasts. It inherits every integration decision and both design hazards
simultaneously.

## 3.6.3 Mapping experiments to hypotheses

| Hypothesis | Contrast that tests it | Decision rule |
|---|---|---|
| **H1** — individual gains transfer | A1−A0, A2−A0, A3−A0 on the efficiency measures | Each mechanism moves its own target cost in the reported direction, beyond seed dispersion |
| **H2** — gains are attenuated relative to terrestrial magnitudes | The same contrasts, compared against each source's published figures **after renormalisation** | For quantization the prediction is structural: the compression ratio must be far below published figures because the baseline stores fourteen numbers per primitive rather than fifty-nine |
| **H3** — quality cost concentrates in the water column | A1−A0 and A2−A0 on quality, together with the primitive-count trajectory and a floater diagnostic | Quality loss exceeding the terrestrial analogue, accompanied by a change in near-camera low-opacity primitive population |
| **H4** — pruning perturbs medium estimation | **A2, via the depth-normalisation and medium-coefficient logs across the simplification boundary** | A discontinuity in the coefficients at the boundary confirms; its absence refutes. The re-identification burst is expected to absorb it |
| **H5** — pruning×quantization interacts, initialization×quantization does not | A6 − [A2 + A3 − A0] and A5 − [A1 + A3 − A0] | The first differs from zero beyond pooled dispersion; the second does not |

H4 deserves emphasis because it is the only hypothesis in the set that is **not** tested by a
between-cell quality comparison. It is tested by a within-run diagnostic: two logged
quantities, observed across a single scheduled event, in a single configuration. This makes it
by far the cheapest hypothesis to evaluate and the only one that could be answered by a
two-cell experiment. It is also the one whose failure mode is invisible in the quality
numbers, since a mis-identified medium model manifests as slightly worse reconstruction in
the pruned configurations — indistinguishable, without the diagnostic, from pruning simply
costing quality.

## 3.6.4 Comparison baselines

Three tiers of comparison, kept distinct because they carry different evidential weight.

**Internal — the primary comparison.** All eight cells, same device, same software build, same
data, same evaluation harness. Every claim about mechanism effects and interactions rests on
this tier alone. It is internally valid by construction.

**Against the baseline as published.** The untreated cell is compared against the baseline's
published figures on these same four scenes, as an environment check. This comparison is
**quality-only**, not timing: the baseline names no hardware, so its wall-clock and frame-rate
figures cannot be placed beside measurements from an identified device without labelling the
mismatch. Even the quality comparison requires care, because the baseline's published numbers
were produced by an evaluation harness with three separable idiosyncrasies documented in the
next section.

**Against competing underwater methods.** Reported for context, not as controlled comparison.
The closest published system couples a physical formation model with uncertainty-driven
pruning and a compressed medium representation on these same four scenes; another achieves
compactness by changing the primitive type. Neither is re-run here. These comparisons are
presented with explicit statements of what differs — evaluation convention, hardware, and in
one case colour space — rather than tabulated as if commensurable.

**Not compared against terrestrial figures directly.** The three efficiency mechanisms'
published numbers come from terrestrial benchmarks, three different devices, and a
fifty-nine-number-per-primitive representation. They inform the hypotheses; they do not appear
in the same table as this study's results.

## 3.6.5 Protocol

**Split.** Every eighth frame by index order held out; three test frames per scene. The rule
is inherited unchanged and coincides with the held-out frames of every published method on
these scenes. The evaluation flag is passed explicitly and a non-empty test set asserted,
because it defaults off in two of the four codebases.

**Repetition.** Three seeds per cell per scene: eight cells × four scenes × three seeds =
**ninety-six training runs**. This is the dominant cost of the study and is budgeted, not
discovered. It is also not negotiable. Interaction terms are differences of differences and
carry roughly twice the variance of a main effect, so an interaction claimed from single runs
would repeat exactly the error every source method makes — the baseline's own published
ablation reports differences below half a decibel from single runs with a randomly seeded
default and no error bars.

**Reporting.** Mean and standard deviation across seeds, per scene and aggregated. Both the
unweighted scene mean and the image-weighted mean are given, since scene frame counts are
unequal. Efficiency measures are reported per run, with the realised primitive count rather
than the target budget, because the subsampling is stochastic.

**Sequencing.** A0 runs first on all scenes and seeds; its converged primitive count sets the
budget; the remaining seven cells then run. This dependency is a consequence of the baseline
never reporting its own primitive count.

## 3.6.6 The inferential structure, stated explicitly

The study reports three families of quantity.

**Main effects** are estimated in both directions and both are reported. Where the
from-below and from-above estimates of the same mechanism agree, the mechanism is independent
of the others and either number may be quoted. Where they disagree, **neither may be quoted
alone**, and the disagreement is reported as the interaction.

**Interactions** are computed as the deviation of a compound cell from the additive prediction
built from its components, using additive combination for quality measures expressed in
decibels or as similarity indices, and multiplicative combination for ratio measures such as
storage, count and frame rate. Deviations are assessed against the pooled dispersion of the
cells entering the calculation, not against a single run's difference.

**Diagnostics** — the depth normalisation constants, the medium coefficients, the primitive
count trajectory, and the restored-image self-consistency measure — are reported per run and
are not aggregated into a headline. Their function is to *localise* an effect once the
contrasts have detected it, and in the case of H4 to test a hypothesis that the contrasts
cannot reach.

## 3.6.7 Design hazards controlled in advance

Two failure modes would produce a spurious null result, and both are controlled by design
rather than checked after the fact.

**A non-binding budget.** If dense initialization converges below the pruning budget, the
pruning step becomes a no-op and two cells collapse onto two others. The budget is set from
the untreated baseline's count so that it binds everywhere, and whether it bound is reported
per run.

**A confounded factor.** The quantization mechanism ships its own count-reduction machinery,
which its own authors identify as the source of its published rendering speedup. Left enabled,
the pruning and quantization factors would not be independent and the compound cells would
prune twice. It is disabled, and the primitive count of the quantization-only cell is compared
against the baseline's as a check that it stayed disabled.

A third hazard is acknowledged and **not** fully controlled. Three of the four codebases
contain undocumented schedule behaviours — a continuous opacity decay, a clamped learning-rate
schedule, a rewound learning-rate schedule, a removed periodic opacity reset — that arrive
attached to their mechanisms and cannot be separated from them without departing further from
the methods as evaluated. Where two of these conflict, a precedence rule is stated and
recorded. The residual risk is that a measured mechanism effect is partly an effect of its
attached schedule behaviour rather than of the mechanism proper. This is stated in the
limitations section rather than hidden, and it is a limitation the source publications share,
since none of them separates the two either.
