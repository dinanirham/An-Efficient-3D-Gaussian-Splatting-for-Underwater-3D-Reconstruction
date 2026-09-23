---
section: "4.1.3"
title: "Repeat Dispersion as the Measurement Baseline"
chapter: 4
action: Add
evidence: ["FINDINGS §0", "results_by_scene.csv"]
figures: ["figure-4-01-resolution"]
tables: ["Table 4.2"]
citations: []
status: refined
word_count: 796
---

# 4.1.3 Repeat Dispersion as the Measurement Baseline

Every comparison in this chapter is referred to the dispersion produced by
repetition alone. Three repeats of each configuration were run on each scene,
differing only in seed, and their standard deviation establishes the scale
against which an effect is judged. Two such scales are needed, and
distinguishing them matters: the configuration a contrast is *anchored on*
supplies the dispersion that sets the contrast's resolution, and this chapter
uses two different anchors for two different purposes.

> **[TABLE 4.2]** *Repeat dispersion over three repeats, per scene, for the
> unmodified configuration (A0) and the reference implementation (SS).*
> Primitive count is given as a coefficient of variation because its magnitude
> differs by an order of magnitude across configurations. Source: FINDINGS §0
> and `results_by_scene.csv`.

| Scene | PSNR sd (dB) A0 | PSNR sd (dB) SS | LPIPS sd A0 | LPIPS sd SS | Count CV A0 | Count CV SS |
|---|---:|---:|---:|---:|---:|---:|
| Curaçao | 0.395 | 0.733 | 0.0025 | 0.0072 | 8.6 % | 17.2 % |
| IUI3 Red Sea | 0.245 | 0.434 | 0.0013 | 0.0026 | 12.5 % | 19.5 % |
| Japanese Gardens | 0.126 | 0.455 | 0.0050 | 0.0019 | 34.3 % | 7.4 % |
| Panama | 0.481 | 0.539 | 0.0091 | 0.0052 | 36.6 % | 27.9 % |

Three features of this table govern the interpretation of every later result.

First, fidelity dispersion is small in absolute terms on both configurations,
which is what makes effects of a few tenths of a decibel resolvable at all. A
campaign with a single run per cell could not have reported any of the fidelity
results in this chapter, because it would have had no scale against which to
judge them.

Second, the dispersion of primitive count differs by a factor of four across
scenes and is substantial on two of them. Under identical configuration, the
unmodified configuration's final population varies by approximately one third
from one repeat to the next on Japanese Gardens and Panama. Independent
measurement of same-seed non-determinism in the underlying implementation found
a median variation of 21 % with a tail reaching 59 %, so dispersion of this
order is within what the training process itself produces rather than evidence
of a defect. Its consequence is nonetheless direct: on those two scenes a
difference in primitive count must be large before it can be resolved, and
several count contrasts in Section 4.6 are unresolved there for this reason
alone.

Third — and this is a cost of the anchoring decision stated in Section 4.1.2 —
**the reference implementation is the more variable of the two on peak
signal-to-noise ratio, on all four scenes.** Its dispersion is 1.1 to 3.6 times
that of the unmodified configuration, the largest ratio falling on Japanese
Gardens, the scene whose unmodified dispersion is smallest. Because the
standard error of a contrast combines the dispersion of both configurations
entering it, every evaluative comparison against the reference is resolved at a
coarser threshold than the corresponding factorial contrast against the
unmodified configuration. Anchoring on the published method is the right choice
for a thesis whose claims concern that method, but it is not a free one, and
results in Sections 4.3 to 4.5 that are reported as unresolved against the
reference are not thereby shown to be small.

The pattern does not carry to the other two metrics. On learned perceptual
similarity the reference is more variable on two scenes and less variable on
two; on primitive count it is markedly less variable on Japanese Gardens, where
the unmodified configuration's 34.3 % is the campaign's widest. No single
configuration is uniformly the quieter measurement, which is why the dispersion
of both configurations entering a contrast is carried through rather than a
pooled figure being assumed.

> **[FIGURE 4.1]** `figures/chapter4/figure-4-01-resolution.pdf`
> *Resolvable effect size against observed effect size, per scene.* The
> two-standard-error threshold for main, two-way and three-way contrasts, with
> the observed main effects overlaid. The separation between the PSNR threshold
> and the largest observed PSNR main effect is the graphical form of the
> `UNDETERMINED` finding of Section 4.6.
> **Status:** built

Figure 4.1 places these thresholds beside the effects the campaign actually
measured. Its purpose is to make the resolution argument visible rather than
arithmetical: for perceptual similarity and primitive count the observed main
effects stand clear of the threshold on most scenes, while for peak
signal-to-noise ratio the largest main effect the campaign measured, 0.80 dB,
falls below the smallest resolvable two-way interaction on every scene. That
relationship, and not any property of the mechanisms, is what makes the PSNR
interaction terms undeterminable in this design.

---

## Review log

**Domain Researcher** — The draft tabulated only the unmodified
configuration's dispersion, which was correct when contrasts were anchored
there but is now incomplete: every evaluative contrast in Sections 4.3 to 4.5
combines the reference's dispersion as well. Checking the data showed the
reference is the *more* variable on PSNR on all four scenes, by up to 3.6×.
This is a real cost of the anchoring decision and had not been stated anywhere.
→ *applied*: both configurations tabulated, the third feature written, and the
consequence spelled out — an unresolved result against the reference is not
thereby shown to be small. Second finding: the draft implied a single noise
floor. → *applied*: two scales, named and distinguished in the opening.

**Supervisor** — The new third feature is the most consequential sentence in
the subsection and was buried mid-paragraph in the first attempt. → *applied*:
promoted, bolded, and followed immediately by what it costs the reader. Second
finding: having made the point, the draft overstated it — the reference is not
uniformly noisier, and a reader who checks the LPIPS and count columns would
notice. → *applied*: fourth paragraph added conceding the pattern does not
carry, which is why per-contrast dispersion is used rather than a pooled
figure. Devil's advocate position raised and not sustained: if the reference is
noisier, is it fit to anchor on? Yes — dispersion affects resolution, not
validity, and Section 4.2.1 tests fitness on equivalence, not on variance.

**Journal Reviewer** — Count dispersion reported as a coefficient of variation
in a table whose other columns are absolute, without saying why. → *applied*:
stated in the caption. Second: Figure 4.1 was referenced in the prose but had
no placeholder or caption. → *applied*. Third: "1.1 to 3.6 times" needed the
scene carrying the extreme named for verifiability. → *applied*.
