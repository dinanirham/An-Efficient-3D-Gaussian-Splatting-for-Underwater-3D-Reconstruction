---
section: "4.7.6"
title: "Physical Consequence"
chapter: 4
action: Add
evidence: ["FINDINGS §5a", "FINDINGS §8", "renders"]
figures: ["figure-4-13-collapsed-medium"]
tables: []
citations: ["Akkaynak & Treibitz, 2018"]
status: refined
word_count: 651
---

# 4.7.6 Physical Consequence

The preceding subsections report the collapse as a number: a coefficient
crossing zero in nine of 24 runs. This subsection states what that means for
the reconstruction, because a reader who has followed the incidence and the
diagnostics may still not have been told what is actually wrong with the
affected models.

The estimator composes the observed image as a medium-free radiance attenuated
with depth, plus a backscatter term that saturates with depth. The attenuation
coefficient governs how fast radiance is lost along a ray, and in water it is
necessarily positive: light is removed with distance, at a rate that differs by
wavelength (Akkaynak & Treibitz, 2018). **A negative attenuation coefficient
describes water that amplifies light with distance.** There is no physical
medium this corresponds to.

The consequence for the decomposition is specific. In the affected channel the
water becomes effectively transparent, then worse than transparent, so the
medium term stops removing radiance and the composed image can only match the
observation if the medium-free image absorbs the difference. The restored image
takes on the appearance the water should have accounted for. The estimator
continues to produce a decomposition; it is simply no longer a decomposition
into a scene and a water column, but into two quantities whose product matches
the data.

> **[FIGURE 4.13]** `figures/chapter4/figure-4-13-collapsed-medium.pdf`
> *A lost attenuation channel — Japanese Gardens.* One scene and view across
> three configurations — the reference, the unmodified configuration and a
> collapsed simplification run — as attenuation map and restored image. The
> collapsed attenuation map is immediately distinguishable from the other two;
> the restored image carries a colour cast the others do not; and the composed
> images that the fidelity metrics score are not distinguishable at all.
> **Status:** built · **Anchored on:** SS

Figure 4.13 is the section's evidence and its argument in one panel. The
attenuation map of the collapsed run is unmistakable beside the reference and
the unmodified configuration, and its restoration carries a colour cast that
neither of the others shows. What is not visible is any difference in the
composed image, which is the only one of the four quantities that has ground
truth and the only one any metric in this chapter evaluates.

**The failure is therefore invisible to the evaluation protocol this literature
uses.** Section 4.8 establishes that at scale — twelve within-configuration
comparisons, a median difference of 0.8 of a baseline standard deviation, with
inconsistent sign — and this subsection establishes what is being missed. The
two halves belong together: a failure that were merely undetected would be a
gap in reporting, while a failure that is undetectable by the standard
instruments is a problem with the instruments.

One consequence for practice follows directly and is stated without hedging. A
configuration selected on fidelity and size, by the procedure that Section
4.6.6 describes and that this literature conventionally applies, will select
configurations that lose an attenuation channel in a substantial minority of
runs without any indication that it has done so. The affected run's images look
right. Only the physical model is wrong, and the physical model is the reason a
physically grounded estimator was chosen over a general one.

The limitation stated in Figure 4.13's caption applies to the visual evidence
and not to the finding. No configuration has both a collapsed and an intact
repeat at the one seed whose point cloud was retained (Section 4.1.4), so the
panels compare configurations that differ in outcome and in mechanism. The
incidence of Section 4.7.1 and the strata comparison of Section 4.8.1 both rest
on all three repeats and do not share that limitation.

---

## Review log

**Domain Researcher** — The draft described the collapse as "physically
implausible", which is too weak: a negative attenuation coefficient is not
implausible, it is impossible for a medium that absorbs. → *applied*, with the
citation and the explicit statement of what it would describe. Second finding:
the draft did not explain where the radiance goes, which is the question a
reader in this area asks immediately. → *applied*: the restored image absorbs
it, and the decomposition becomes two quantities whose product matches the data.

**Supervisor** — The draft ended on the figure. The subsection's purpose is to
make the failure matter, and that requires saying what a practitioner would
experience. → *applied*: the selection consequence, stated without hedging, and
the distinction between an undetected failure and an undetectable one. Devil's
advocate: is "only the physical model is wrong" dismissive of how much that
matters? It is phrased to land the opposite way — the physical model is the
reason the method was chosen.

**Journal Reviewer** — The figure's single-repeat limitation was in its caption
but could be read as limiting the finding rather than the illustration.
→ *applied*: closing paragraph separates the two, naming which results rest on
all three repeats.
