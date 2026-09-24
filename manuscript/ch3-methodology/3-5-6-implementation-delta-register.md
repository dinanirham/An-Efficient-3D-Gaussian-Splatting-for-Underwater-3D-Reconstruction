---
section: "3.5.6"
title: "Implementation-Delta Register"
chapter: 3
action: Add
evidence: ["CD register", "FINDINGS §1", "FINDINGS §5"]
figures: []
tables: ["Table 3.7"]
citations: []
status: refined
word_count: 889
---

# 3.5.6 Implementation-Delta Register

This study measures implementations, not published descriptions, and the two
differ. This subsection registers every difference in one place, so that a
result reported in Chapter IV can be traced to what actually ran. Chapter IV
refers to this register wherever a finding might otherwise be read as a
replication of a published claim.

> **[TABLE 3.7]** *Differences between the source methods as published and as
> executed here.* "Adaptation" is a change this study made; "carried" is
> behaviour present in a source implementation but absent from its paper;
> "scoped out" is a component deliberately not used.

| Mechanism | Difference | Kind | Reason |
|---|---|---|---|
| M1 | Correspondences from training views only | Adaptation | Prevents evaluation-set leakage through geometry (3.4.5) |
| M1 | Cheirality check added to the reprojection filter | Adaptation | Near-parallel rays admit points behind the camera; nothing downstream removes them (3.5.2) |
| M1 | Reference-view count collapses to the training-view count | Corpus constraint | The source default exceeds every scene's view count (3.5.2) |
| M1 | Continuous opacity decay; clamped position learning rate | Carried | Present in the released implementation, absent from its paper |
| M2 | Densification half not used | Scoped out | Collides with M1 where density control is disabled; the factor here is reduction |
| M2 | Rasteriser substituted | Adaptation | The baseline's rasteriser does not emit the per-primitive accumulators the importance score requires |
| M3 | k-means++ seeding with empty-cluster reseeding | Adaptation | Uniform seeding gives higher quantisation error at identical storage (3.5.4) |
| M3 | Opacity regulariser disabled | Scoped out | It reduces primitive count, which would make M3 and M2 non-independent factors |
| M3 | Three attribute groups, not four | Configuration | No higher-order harmonics at spherical-harmonic degree zero |
| Baseline | Medium-only interval after each M2 event | Addition | An intervention of this study's own; see below |

Three of these deltas produced findings about composition rather than merely
recording a setting, and they are the study's own technical content.

## The rasteriser substitution, and a class of failure it exposed

Adaptive density control decides what to clone or split from the accumulated
norm of the loss gradient with respect to screen-space positions. Each
rasterisation call owns one such buffer, so whichever losses backpropagate
through a given pass, their gradients land in that pass's buffer and nowhere
else.

Substituting the rasteriser preserved every forward value — alpha in range,
compositing correct, depth recovered to seven decimal places — and silently
removed alpha-derived gradients from the densification signal. The configuration
with no mechanism active then converged to approximately one sixth of the
expected primitive count. **No check on a returned value could have observed
this**, and every acceptance check in the study was, at that point, a check on
a returned value.

The invariant now asserted, in both directions, is that density control must
see the image and the alpha channel, and must not see depth. Both halves are
load-bearing: omitting alpha gives one population, admitting depth as well
gives another, and satisfying both reproduces the expected behaviour within
run-to-run spread. The generalisable observation is that **an integration
boundary can preserve every value and still change which gradients flow**, and
that a test suite checking outputs cannot detect it.

## Coupled parameters must be controlled at the switch

The source of M1 disables the periodic opacity reset by setting its interval
past the end of training. That single parameter gates *two* mechanisms: the
reset itself, and a size-based prune that removes primitives by screen radius
or world scale. Under dense initialisation densification never runs and
primitive scales derive from correspondence distance rather than from
optimisation, so arming that prune removes most of the cloud with nothing to
replace it.

Reimplementing the source's intent site by site re-armed each mechanism in turn,
across three successive corrections. The decision recorded here is to control
the behaviour at the parameter the source method itself uses, and the
generalisable observation is that **a composed method inherits its components'
coupling as well as their behaviour**.

## The medium-only interval is this study's own addition

The interval following each reduction event (Section 3.5.3) is not part of any
source method. It was added on a reasoning registered before the campaign,
which Section 3.6.4 states as a hypothesis and Section 4.7.3 reports as
refuted by its own test. The interval itself remained in the executed design
regardless of the fate of the reasoning that motivated it, because removing it
mid-campaign would have made the stages incomparable.

Two consequences are recorded rather than argued. Every configuration
containing spatial reorganisation also contains the interval, so its effects
cannot be separated from the reduction's (Section 4.7.5). And a remedy that
this study proposed is reported in Chapter IV as not achieving what it was
intended to achieve, which is a negative result about the study's own
contribution and is stated as one.

---

## Review log

**Domain Researcher** — The draft presented the medium-model argument — that
depth renormalisation makes β rescale after a population change — as an
established account justifying the interval. Section 4.7.3 refutes exactly that
account. A methodology chapter asserting it as mechanism would put the thesis
in contradiction with itself. → *applied*: the interval is recorded as an
addition whose motivating reasoning is a registered hypothesis, located in
Section 3.6.4, with its fate in Section 4.7.3. Second finding: the draft quoted
"six of twelve runs" for the collapse from the archived campaign; the executed
campaign gives 5 of 12 for that configuration and 9 of 24 pooled.
→ *applied*: the counts are removed from this subsection entirely, since
incidence is a result and belongs in Chapter IV.

**Supervisor** — The draft's title was "Integration decisions" and it read as a
narrative of debugging. Chapter IV points here for the implementation deltas,
so the register has to be a register — enumerable, checkable, one row per
difference. → *applied*: table first, then the three deltas that produced
findings. Devil's advocate: does tabulating the deltas make the study look
heavily modified? It makes it look honestly reported; the alternative is a
reader discovering the same list by reading the code.

**Journal Reviewer** — Measured quantities were quoted with bracketed sample
annotations carried over from an internal register, which will not survive
typesetting and are not a citation format. → *applied*: removed, with
quantities either given plainly or deferred to Chapter IV where they are
results. Second: the subsection did not say what it is for, though another
chapter depends on it. → *applied*: opening paragraph.
