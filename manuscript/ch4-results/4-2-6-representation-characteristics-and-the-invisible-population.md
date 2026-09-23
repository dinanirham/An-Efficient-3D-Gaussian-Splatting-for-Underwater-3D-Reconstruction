---
section: "4.2.6"
title: "Representation Characteristics and the Invisible Population"
chapter: 4
action: Rewrite
evidence: ["FINDINGS §9"]
figures: ["figure-4-05-invisible-population", "figure-4-c6-radius"]
tables: ["Table 4.7"]
citations: ["Kerbl et al., 2023"]
status: refined
word_count: 795
---

# 4.2.6 Representation Characteristics and the Invisible Population

The primitive counts of Section 4.2.2 are the quantity the efficiency
mechanisms are designed to reduce, and they are reported throughout this
chapter as ratios against the reference. This subsection establishes something
about those counts that changes how every such ratio should be read: most of
the primitives the baseline optimiser produces are never rendered.

A primitive contributes to an image only if its opacity survives the alpha
compositing that produces the pixel. Counting the primitives whose opacity
exceeds the visibility threshold used by the renderer gives the following
fractions.

> **[TABLE 4.7]** *Fraction of primitives above the visibility threshold, per
> scene and configuration.* Seed 0, except the reference, for which all three
> repeats were measured. Source: FINDINGS §9.

| Scene | A0 | SS (3 repeats) | A0D | A1 | A2 | A4 |
|---|---:|---:|---:|---:|---:|---:|
| Curaçao | 27 % | 23–26 % | 68 % | 87 % | 96 % | 98 % |
| IUI3 Red Sea | 40 % | 29–43 % | 76 % | 94 % | 88 % | 100 % |
| Japanese Gardens | 41 % | 36–37 % | 74 % | 87 % | 93 % | 99 % |
| Panama | 36 % | 26–37 % | 65 % | 78 % | 94 % | 95 % |

**Between 59 and 73 per cent of the baseline's primitives fall below the
visibility threshold, and the published reference carries the same fraction.**
This is not a defect introduced by the reimplementation and it is not a
property of underwater scenes; it is a property of the adaptive densification
procedure that the underlying splatting method uses to grow a representation
(Kerbl et al., 2023), which clones and splits primitives on a gradient
criterion and has no corresponding procedure for removing those that end up
contributing nothing.

> **[FIGURE 4.5]** `figures/chapter4/figure-4-05-invisible-population.pdf`
> *The population that never reaches a render.* The baseline rendered as it
> stands, the same model with every sub-threshold primitive silenced rather
> than deleted, and the difference at four times amplification. Silencing 59 to
> 73 per cent of the representation changes the image by almost nothing.
> **Status:** built

Figure 4.5 makes the claim falsifiable rather than merely arithmetical.
Silencing the sub-threshold population is not the same operation as deleting
it: the model is otherwise identical, the same rays are traced, and the
difference image is therefore attributable to that population alone. It is
almost black at four times amplification.

The consequence is a reporting one and it applies to every count ratio in this
chapter. A mechanism that removes primitives is not, in general, removing
reconstruction. **A reduction should be read against the visible population
rather than against the total**, and the two differ by roughly a factor of
three at the baseline. Spatial reorganisation's 25-fold count reduction on
Curaçao, reported in Section 4.4.2, is approximately a sevenfold reduction of
the population that actually renders. Both numbers are true; the first is the
one that determines storage and the second is the one that determines how much
representational capacity was given up. This chapter reports the first, because
it is the quantity the mechanisms target and the quantity the source methods
report, and states the second wherever a claim about reconstruction quality
depends on it.

The table also shows that the mechanisms differ sharply in how much of their
output is live. Deterministic initialisation produces a representation that is
78 to 94 per cent visible, and the initialisation-plus-simplification
combination 95 to 100 per cent. These configurations are not merely smaller;
they are composed almost entirely of primitives that contribute. Gradient
detachment, measured separately in Section 4.9, reaches 65 to 76 per cent
without targeting count at all, which is consistent with its acting on the
density-control signal rather than on the population directly.

One further representational property is recorded here because it belongs to
the baseline rather than to any mechanism. Bounding-box inflation — the full
extent of the point cloud divided by its central 98 per cent extent — is
between 2 and 25 times on most runs, and pathological on a few. The reference
implementation produces a 313-fold inflation on one of its three repeats, and
the largest value in the campaign, 1 301-fold, occurs on a quantisation run.
Detached outlying primitives are therefore a property of the baseline optimiser
and its seed, not of any mechanism under test. Because full point clouds were
retained for one repeat per configuration (Section 4.1.4), the mechanism cells
cannot be given a rate for this, and the observation is reported without
attribution.

> **[FIGURE C6]** `figures/chapter4/figure-4-c6-radius.pdf`
> *Distribution of primitive distance from the cloud centre.* The compact core
> and the detached tail, per configuration.
> **Status:** built

---

## Review log

**Domain Researcher** — The draft attributed the invisible population to the
underwater setting. It is a property of adaptive densification and would appear
in a terrestrial scene too; the reference carrying the same fraction is the
evidence. → *applied*, with the citation and the reason — cloning and splitting
have no counterpart that removes non-contributing primitives. Second finding:
the silence-versus-delete distinction is what makes Figure 4.5 evidence rather
than illustration, and the draft did not state it. → *applied*.

**Supervisor** — The subsection reported a striking fact and left the reader to
work out its consequence. The consequence is a reporting rule that governs the
rest of the chapter, and it should be stated as a rule. → *applied*: bolded,
with the Curaçao example carried through in both forms and an explicit
statement of which number this chapter reports and why. Devil's advocate: if
the visible-population figure is the more meaningful one, why not report it
throughout? Because it exists for one repeat per cell only, so it cannot carry
dispersion — stated where the claim is made.

**Journal Reviewer** — Table mixed a single-repeat column with a three-repeat
range without saying so. → *applied*, in the caption. Second: the 1 301-fold
inflation was reported beside mechanism results in a way that implied
attribution the single-repeat design cannot support. → *applied*: the paragraph
now states the limit and declines the attribution. Third: Figure C6 was
referenced nowhere despite being built. → *applied*.
