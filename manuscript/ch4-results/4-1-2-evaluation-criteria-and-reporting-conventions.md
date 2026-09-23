---
section: "4.1.2"
title: "Evaluation Criteria and Reporting Conventions"
chapter: 4
action: Add
evidence: ["FINDINGS §0", "research-questions-revised.md"]
figures: []
tables: []
citations: ["Wang et al., 2004", "Zhang et al., 2018"]
status: refined
word_count: 831
---

# 4.1.2 Evaluation Criteria and Reporting Conventions

Five conventions are applied throughout this chapter. They are consequences of
the experimental design rather than presentational preferences, and stating
them once here avoids repeating the justification at every result.

**Evaluation is anchored on the unmodified reference implementation.** Every
statement of the form "configuration X costs or gains Y" is a comparison
against SS, the published method, on the same scene. This is a deliberate
change from reporting against A0, the configuration with all three mechanisms
disabled. A0 remains the internal control from which the factorial contrasts
are constructed, and it is the corner of the design at which no mechanism is
active, but it is not what a reader wants a result measured against. The change
costs nothing in the analysis: because the reference cancels from any
difference of differences, (A1 − SS) − (A0 − SS) is identically A1 − A0, and
every main effect and interaction reported in Sections 4.3 to 4.6 is numerically
unchanged by the choice of anchor. One exception is unavoidable and is restated
wherever it applies: the reference implementation does not record stored size,
so results on that axis alone are reported against A0.

**Results are reported per scene and are never averaged across scenes.**
Reference fidelity spans approximately 7 dB between the easiest and hardest
scene in the corpus, and repeat dispersion differs by a factor of approximately
four across scenes (Section 4.1.3). A fidelity figure averaged over the four
scenes would therefore describe none of them, and would conceal the
scene-specific behaviour that Sections 4.3 to 4.5 identify as material. Where a
summary across scenes is unavoidable, the number of scenes on which an effect
resolves is reported rather than a pooled magnitude.

**An effect is reported as resolved only when its magnitude is at least twice
its standard error**, computed against the repeat dispersion of the scene on
which it was measured. Effects below this threshold are reported as
`UNRESOLVED`. This label is a statement about the resolving power of three
repeats and must not be read as a statement that the effect is absent. An
unresolved effect and a zero effect are not distinguishable in this design, and
no argument in this chapter treats them as though they were.

**Interactions are adjudicated on perceptual similarity and primitive count,
and PSNR interactions are reported as `UNDETERMINED` by construction.** The
standard error of a two-way contrast is approximately twice, and of a
three-way contrast approximately 2√2 times, the standard error of a single cell
mean. Applying the resolution rule to the observed dispersion gives a smallest
resolvable PSNR interaction of 0.51 to 1.61 dB depending on scene, against a
largest measured PSNR main effect of 0.80 dB. No PSNR interaction can therefore
be resolved by this design, whatever its true magnitude. The terms are
tabulated in Section 4.6 for completeness and marked accordingly; no claim in
this thesis rests on them.

**Every quantitative statement is labelled as pre-registered or post-hoc.** The
analysis plan, including its hypotheses, its equivalence margin and the
condition under which its central explanation would be considered falsified,
was written and committed before the campaign's results were examined.
Statements arising from that plan are identified as pre-registered; statements
arising from inspection of the data afterwards are identified as post-hoc and
are not presented as explanations. The distinction is carried in the body text
rather than relegated to notes, because the strength of a claim in this chapter
depends on which of the two it is. Section 4.7.3 reports a pre-registered
explanation that the data refuted, and does so in the body for exactly this
reason.

Two properties of the measurements themselves constrain what the conventions
above can be applied to. The fidelity metrics — peak signal-to-noise ratio,
structural similarity (Wang et al., 2004) and learned perceptual similarity
(Zhang et al., 2018) — are computed on the composed image. They are not
computed on the restored image or on the medium parameters, and no held-out
ground truth exists for either of those quantities. Every fidelity number in
this chapter is therefore a statement about the composed image alone, and
Section 4.8 shows that this is a materially weaker statement than it appears.
Separately, the learned attenuation and backscatter coefficients are
dimensionless with respect to a depth that is renormalised per frame. The
ordering of the three colour channels within a scene is meaningful and is
interpreted; the magnitudes are not physical quantities, are not comparable
across scenes, and are never reported as though they were.

---

## Review log

**Domain Researcher** — Draft carried four conventions and did not state the
anchor at all, which is the convention most likely to be questioned since it
changed after the analysis was complete. → *applied*: added as the first
convention, with the cancellation identity shown so a reader can verify that no
contrast moved. Second finding: the draft asserted the metrics "measure Î"
without saying that no ground truth exists for Ĵ or for the medium parameters,
which is what actually limits the claim. → *applied*, in the closing paragraph.
Third: the dimensionless-depth qualification was absent and would have been
raised at review of Section 4.2.4. → *applied*.

**Supervisor** — The anchor paragraph originally justified the change at length
before saying what it was. Lead with the rule, then the justification.
→ *applied*. Second finding: "no claim in this thesis rests on them" was
asserted for the PSNR interactions but the same discipline was not visibly
applied to `UNRESOLVED`. → *applied*: added the sentence stating that no
argument treats unresolved as zero — which is a promise the later sections must
keep, and the Supervisor should check it at chapter level.

**Journal Reviewer** — The 0.51–1.61 dB resolution figure appeared without the
main-effect magnitude it should be compared against, leaving the reader unable
to see why the conclusion follows. → *applied*: 0.80 dB largest main effect
stated inline. Second: SSIM and LPIPS were named without citation at first use
in the chapter. → *applied*, both from the controlled register. Third: "2√2"
should be typeset consistently with the rest of the chapter rather than as
inline LaTeX. → *applied*.
