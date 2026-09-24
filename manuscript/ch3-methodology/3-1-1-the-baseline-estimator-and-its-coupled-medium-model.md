---
section: "3.1.1"
title: "The Baseline Estimator and Its Coupled Medium Model"
chapter: 3
action: Refine
evidence: ["CD register", "implementation"]
figures: ["figure-0-optimisation-loop"]
tables: []
citations: ["Kerbl et al., 2023", "Akkaynak & Treibitz, 2018", "Yang et al., 2024", "Levy et al., 2023"]
status: refined
word_count: 796
---

# 3.1.1 The Baseline Estimator and Its Coupled Medium Model

The estimator this study modifies represents a scene as an explicit set of
anisotropic Gaussian primitives rendered by differentiable rasterisation
(Kerbl et al., 2023), and fits a physical image formation model jointly with
the geometry (Yang et al., 2024). Both halves matter for what follows: the
first is what the efficiency mechanisms act on, and the second is what they
turn out to disturb.

The rendered quantity is not compared directly against the captured image. The
rasteriser produces a medium-free radiance Ĵ and a depth map Ẑ, and these are
composed through the medium model before any comparison is made:

> Î  =  Ĵ ⊙ exp(−β_att · Ẑ)  +  σ(B∞) ⊙ (1 − exp(−β_bs · Ẑ))

The first term attenuates the medium-free radiance with distance; the second
adds backscattered veiling light that saturates with distance. Following the
revised formulation of Akkaynak and Treibitz (2018), and as adopted by
SeaThru-NeRF (Levy et al., 2023) and by this estimator, **attenuation and
backscatter are governed by distinct coefficients** rather than by a single
extinction term. The medium is described by nine scalars — an attenuation
coefficient, a backscatter saturation rate and a veiling-light value for each
of three colour channels — optimised jointly with the primitives against the
photometric loss on Î.

Three properties of this arrangement are consequential for the experiment and
are stated here because later sections depend on them.

**The loss constrains the composition, not its factors.** Only Î is compared
against a captured image. Ĵ, the two medium maps and the nine scalars have no
independent supervision; any assignment of radiance between the scene and the
water that reproduces the observation is equally consistent with the training
signal. The decomposition is exact by construction and is therefore not
evidence that the decomposition is correct. Section 4.8 reports what this costs
in practice.

**The medium model reads a per-frame renormalised depth.** Ẑ is rescaled to the
unit interval within each frame before it reaches the attenuation and
backscatter terms. The fitted coefficients are consequently dimensionless with
respect to a normalised depth rather than attenuation in inverse metres. They
cannot be compared with published measurements of natural water, and they
cannot be compared across scenes of differing depth range; only the ordering of
the three channels within one scene is interpretable. Every claim this thesis
makes about the fitted medium is a claim about ordering, and Section 3.7.3
states how that constrains the diagnostics.

**The medium is global and the geometry is not.** The nine scalars describe the
whole scene, while the primitives are local. A change to the primitive
population therefore changes what the nine scalars are fitted against, without
changing their number or their parameterisation. This is the coupling the study
exists to measure: the efficiency mechanisms act on the geometry, and the
medium model is downstream of the geometry through the rendered depth.

> **[FIGURE 3.1]** `figures/figure-0-optimisation-loop.svg`
> *The optimisation loop.* The rasteriser produces a medium-free radiance and a
> depth map; the medium model composes them into the image against which the
> photometric loss is taken. The medium parameters and the primitives are
> updated from the same loss.
> **Status:** built

The baseline as executed differs in specified ways from the published
description of the method it implements, and those differences are registered
in Section 3.5.6 rather than being described as faithful implementation. The
configuration with all three mechanisms disabled is not assumed to reproduce
the published method; it is tested against an unmodified reference
implementation under a pre-registered equivalence margin, which Section 3.6.2
sets out and Section 4.2.1 reports.

One configuration choice affects several later quantities and is recorded here.
Spherical-harmonic degree is set to zero, so each primitive carries fourteen
floating-point values rather than the fifty-nine of the full-degree
representation. This makes the storage figures in Chapter IV specific to this
configuration — the compression ratio of Section 4.5.2 follows arithmetically
from that layout — and it means the attribute-quantisation mechanism has less
to compress here than it would at full degree. The choice follows the reference
implementation's own configuration for this corpus and is not a departure.

---

## Review log

**Domain Researcher** — The draft described the medium model without saying
that attenuation and backscatter carry distinct coefficients, which is the
substantive content of the revised formulation and the reason the two
coefficient sets can disagree in Section 4.2.4. → *applied*, with the citation.
Second finding: the draft stated the formation model and moved on. The three
properties that make the experiment interpretable — the loss constrains only
the composition, the depth is renormalised, the medium is global while the
geometry is local — had to be assembled by the reader from later chapters.
→ *applied*: each stated here with its downstream consequence named.

**Supervisor** — The draft asserted that the baseline "implements SeaSplat",
which the thesis spends Section 4.2.1 declining to claim. → *applied*: differs
in registered ways, tested against a reference under a margin, not assumed
faithful. Devil's advocate: does stating the loss-constrains-the-composition
point here pre-empt Chapter IV's finding? No — it is a property of the
objective, visible from the equation, and stating it in the methodology is what
makes Chapter IV's result a measurement rather than a surprise.

**Journal Reviewer** — The spherical-harmonic degree was not recorded anywhere
in the methodology, yet Chapter IV's compression ratio depends on it.
→ *applied*: closing paragraph, with the fourteen-value layout and the
consequence for Section 4.5.2. Second: the formation model was given without
naming which terms are learned. → *applied*: nine scalars, enumerated.
