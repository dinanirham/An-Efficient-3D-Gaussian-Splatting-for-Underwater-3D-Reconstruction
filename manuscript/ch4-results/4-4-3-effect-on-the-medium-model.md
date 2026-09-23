---
section: "4.4.3"
title: "Effect on the Medium Model"
chapter: 4
action: Add
evidence: ["FINDINGS §5a", "FINDINGS §8", "medium_collapse.json"]
figures: ["figure-4-13-collapsed-medium"]
tables: ["Table 4.12"]
citations: []
status: refined
word_count: 668
---

# 4.4.3 Effect on the Medium Model

This is the subsection at which the third evaluation axis begins to separate
configurations that the first two report as equivalent. Sections 4.4.1 and
4.4.2 establish that spatial reorganisation is radiometrically indistinguishable
from the published reference, perceptually worse everywhere, and fourteen to
twenty-nine times smaller. On the medium model it does something neither of the
preceding sections could have detected.

> **[TABLE 4.12]** *Attenuation-channel collapse under spatial reorganisation,
> per scene.* A run is counted as collapsed when one attenuation coefficient is
> driven to or below zero and does not recover before training ends. Three
> repeats per scene. Source: `medium_collapse.json`.

| Scene | Collapsed / runs |
|---|---:|
| Curaçao | 1 / 3 |
| IUI3 Red Sea | 0 / 3 |
| Japanese Gardens | 2 / 3 |
| Panama | 2 / 3 |
| **Total** | **5 / 12** |

**Five of twelve runs lost an attenuation channel.** The reference and the
unmodified configuration lost none in twenty-four (Section 4.2.7), and
deterministic initialisation lost none in twelve (Section 4.3.3). This is the
first configuration in the chapter for which the medium model fails, and the
failure is not marginal: the affected coefficient is driven to approximately
−0.05 against roughly +1.2 in an intact run of the same configuration on the
same scene, which describes water that amplifies light with distance.

Three properties of the incidence are recorded here because they constrain what
Section 4.7 may conclude. The failure is **seed-conditioned rather than
deterministic**: three of four scenes produce both collapsed and intact repeats
under identical configuration, so the mechanism does not cause collapse but
makes it possible. It is **scene-dependent**: IUI3 Red Sea produces no collapsed
run in twelve across this mechanism and its quantisation pairing, which is the
same scene that Section 4.2.4 identified as having the least coherent medium
fit — an association Section 4.12.4 records and does not explain. **Blue is the
channel lost in every affected run**, and in two of the nine collapsed runs
across this mechanism and its quantisation pairing the green channel crosses
zero at the same iteration. The failure therefore has a
consistent spectral direction: it is always the short-wavelength end of the
attenuation spectrum that is driven negative, never the long.

> **[FIGURE 4.13]** `figures/chapter4/figure-4-13-collapsed-medium.pdf`
> *A lost attenuation channel — Japanese Gardens.* One scene and view across
> three configurations — the reference, the unmodified configuration, and a
> collapsed run of this mechanism — as attenuation map and restored image. The
> collapsed attenuation map is immediately distinguishable; the composed images
> the fidelity metrics score are not.
> **Status:** built · **Anchored on:** SS

**This subsection reports the rate and defers the analysis.** Four questions
follow immediately from the table and none is answered here. Whether the
collapse is caused by the magnitude of the cut or by its discontinuity is
Section 4.7.2. Whether the explanation registered before the campaign accounts
for it is Section 4.7.3, and that explanation was refuted. What the
per-iteration diagnostics show instead is Section 4.7.4. Whether the
medium-only intervals that follow each pruning event cause or merely host the
failure is Section 4.7.5, and the campaign cannot separate the two because
every configuration containing this mechanism contains them. Answering any of
these here would require evidence drawn from configurations this section does
not cover.

One thing must nonetheless be said at this point, because Sections 4.4.1 and
4.4.2 have just reported this mechanism favourably on size and neutrally on
peak signal-to-noise ratio. **A collapsed run is not detectable from the
fidelity numbers reported in those subsections.** Within this cell and scene,
collapsed and intact repeats differ by a median 0.8 of a baseline standard
deviation on the composed image, with the sign inconsistent (Section 4.8.1). A
practitioner who adopted this mechanism and evaluated it as this literature
conventionally does would obtain the size and speed results of Section 4.4.2,
would see nothing wrong in the fidelity results of Section 4.4.1, and would
have a physically meaningless water column in roughly two runs in five.

---

## Review log

**Domain Researcher** — The draft gave only the pooled 5 of 12. The per-scene
breakdown is what shows the failure to be seed-conditioned rather than
deterministic, which is the property that makes Section 4.7's analysis possible
at all. → *applied*: table per scene, with the three properties named. Second
finding: "lost a channel" was used without stating the magnitude, leaving a
reader unable to judge whether it is a rounding artefact. → *applied*: −0.05
against +1.2, with the physical reading.

**Supervisor** — The draft deferred everything to Section 4.7 and therefore said
nothing, which reads as evasion in the subsection where the chapter's most
important failure first appears. → *applied*: the deferral is now explicit
about which four questions go where and why, and the closing paragraph states
the consequence that can be drawn now. Devil's advocate: is it fair to describe
a practitioner as obtaining a meaningless water column when the composed images
are fine? Yes, and it is the point — the decomposition is the reason to choose
a physically grounded method, and it is the part that failed.

**Journal Reviewer** — The draft stated, following the chapter specification,
that "the same channel is lost in every case". Checking `medium_collapse.json`
shows blue lost in all nine collapsed runs but green lost simultaneously in
two, so the claim as written is not exact. → *applied*: blue in every case,
green additionally in two, and the spectral direction stated as the invariant.
`chapter-04-specification.md` is corrected to match. Second: the collapse
criterion was not restated in a subsection a reader may consult directly.
→ *applied*, in the table caption. Third: "two runs in five" in the closing
paragraph does not match "5 of 12" exactly. → *retained deliberately*: the rate
is exact in the table and marked "roughly" in the prose.
