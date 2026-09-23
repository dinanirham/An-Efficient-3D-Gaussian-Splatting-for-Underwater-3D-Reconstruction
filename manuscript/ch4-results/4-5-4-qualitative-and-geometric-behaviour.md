---
section: "4.5.4"
title: "Qualitative and Geometric Behaviour"
chapter: 4
action: Refine
evidence: ["renders", "FINDINGS §9"]
figures: ["figure-4-08-quantisation", "figure-q1-a3-quantisation"]
tables: []
citations: []
status: refined
word_count: 704
---

# 4.5.4 Qualitative and Geometric Behaviour

Section 4.5.1 reports that this mechanism is fidelity-neutral on three scenes
of four. This subsection asks what it does that the composed-image metrics do
not register, and it is the first place in the chapter where the answer
requires looking at something other than the composed image.

> **[FIGURE 4.8]** `figures/chapter4/figure-4-08-quantisation.pdf`
> *Attribute quantisation in the far field: composed against restored.* The
> reference and the mechanism, each shown as composed image and as restored
> image, on a far-field crop, one row per scene.
> **Status:** built · **Anchored on:** SS

The far field is the right place to look, for the reason given in Section
4.2.3: it is where the attenuation term has decayed and the backscatter term
saturated, so the composed image is dominated by the medium and the geometry
behind it contributes least. Any change to per-primitive attributes that the
medium term suppresses will be least visible there in the composed image and
most visible there in the restoration.

That is what the figure shows. The composed images of the two configurations
are closely comparable at range on all four scenes, consistent with the
unresolved pixel-metric effects of Section 4.5.1. The restored images are not:
the mechanism's restoration is visibly different in colour balance and in the
texture it recovers from the far field, most clearly on Panama and Curaçao.
The pair of rows makes the mechanism's character legible in a way no number in
Section 4.5.1 does — it changes the decomposition more than it changes the
image the decomposition composes to.

**Figure 4.8 illustrates this rather than measuring it, and the distinction is
load-bearing.** The two configurations shown are separately trained models with
different random seeds and different optimisation histories. Some of the
difference between their restorations is quantisation and some is trajectory
divergence between two runs, and this figure cannot separate them. The
comparison that can — one model rendered from its continuous parameters and
from its codebook, with nothing else differing — is Figure 4.14, and it is the
subject of Section 4.5.7. The reader should take from Figure 4.8 that the
restoration is where this mechanism acts, and take the magnitude from Section
4.5.7 rather than from here.

> **[FIGURE Q1-A3]** `figures/chapter4/figure-q1-a3-quantisation.pdf`
> *Attribute-level quantisation against the reference and the baseline.*
> Far-field crop of one held-out view per scene with ground truth, the
> reference, the unmodified configuration and the mechanism.
> **Status:** built · **Anchored on:** SS

At near field, and in the composed image generally, the mechanism produces no
characteristic artefact. There is no counterpart here to deterministic
initialisation's softened fine structure or spatial reorganisation's uniform
texture loss: quantising three attribute vectors to learned codebooks leaves
the rendered image looking like the reference's, which is what the codebooks
are trained to achieve and what the unresolved metrics in Section 4.5.1
independently report.

Geometrically the mechanism changes nothing by construction. Primitive
positions, counts and visibility fractions are those of the configuration it
modifies, because it acts on attribute storage after the population is
determined. One observation from Section 4.2.6 attaches to this mechanism and
is repeated here only to decline it: the campaign's largest bounding-box
inflation, 1 301-fold, occurs on a quantisation run on Curaçao. Because full
point clouds were retained for one repeat per configuration, that value rests
on a single run, the reference implementation produces a 313-fold inflation on
one of its own three repeats, and no rate can be attributed to any mechanism.
It is recorded and not interpreted.

As with every qualitative subsection in this chapter, the material here covers
one repeat per configuration and scene (Section 4.1.4). The resolved fidelity
result on IUI3 Red Sea comes from the three-repeat metrics of Section 4.5.1,
not from these panels.

---

## Review log

**Domain Researcher** — The draft treated Figure 4.8 as evidence for the size
of the quantisation effect on the restoration. It cannot be: the two
configurations are separately trained and the comparison confounds quantisation
with trajectory divergence. → *applied*: bolded paragraph naming the confound
and directing the magnitude claim to Section 4.5.7. Second finding: the draft
did not justify using the far field, leaving the crop choice arbitrary.
→ *applied*, from the image formation model.

**Supervisor** — The draft reported "no characteristic artefact" as though it
were a weak finding. Set against the other two mechanisms, each of which has a
signature loss, its absence here is informative and should be stated as a
contrast. → *applied*. Devil's advocate: if nothing is visible in the composed
image, does this subsection earn its place? Yes, because the point of it is
that the mechanism's effect is real and is somewhere the composed image does
not show — which is the chapter's argument in miniature.

**Journal Reviewer** — The 1 301-fold inflation was reported in Section 4.2.6
and again here; repeating it beside a mechanism section risks implying an
attribution the single-repeat design cannot support. → *applied*: recorded
explicitly to decline it, with the reference's own 313-fold given for
comparison. Second: the single-repeat basis needed restating at point of use.
→ *applied*.
