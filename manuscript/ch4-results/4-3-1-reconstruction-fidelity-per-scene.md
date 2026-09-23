---
section: "4.3.1"
title: "Reconstruction Fidelity per Scene"
chapter: 4
action: Rewrite
evidence: ["FINDINGS §2", "results_by_scene.csv"]
figures: ["figure-4-15b-configurations-vs-reference", "figure-q1-a1-initialisation"]
tables: ["Table 4.8"]
citations: ["Kotovenko et al., 2026"]
status: refined
word_count: 823
---

# 4.3.1 Reconstruction Fidelity per Scene

Deterministic initialisation replaces the adaptive densification procedure of
the underlying splatting method with a dense correspondence-derived point cloud
fixed at the start of optimisation (Kotovenko et al., 2026). Primitives are
neither cloned nor split during training, so the population is determined
before the first gradient step. This subsection reports what that costs in
reconstruction fidelity; Section 4.3.2 reports what it saves.

> **[TABLE 4.8]** *Deterministic initialisation against the reference, per
> scene.* Effect with z against repeat dispersion at three repeats; |z| below 2
> is reported `UNRESOLVED`. Source: `results_by_scene.csv`.

| Scene | ΔPSNR (dB) | z | ΔLPIPS | z | Verdict |
|---|---:|---:|---:|---:|---|
| Curaçao | +0.56 | +1.1 | +0.003 | +0.6 | both `UNRESOLVED` |
| IUI3 Red Sea | +0.35 | +1.4 | **+0.059** | **+32.5** | LPIPS resolved worse |
| Japanese Gardens | **+0.55** | **+2.0** | +0.007 | +1.8 | PSNR resolved better |
| Panama | +0.60 | +1.8 | **+0.010** | **+3.1** | LPIPS resolved worse |

**The pixel metric moves in the mechanism's favour on every scene.** The effect
is between +0.35 and +0.60 dB against the reference, positive on all four, and
resolves on one. A mechanism that removes the representation's ability to grow
where the optimiser judges growth necessary might have been expected to cost
fidelity; it does not, on this corpus, on this metric.

**The perceptual metric disagrees, and on one scene it disagrees sharply.** On
IUI3 Red Sea deterministic initialisation is worse by 0.059 in learned
perceptual similarity at 32 standard errors — the largest single-scene fidelity
cost any mechanism incurs in this campaign. On Panama it is worse by 0.010 at
3.1 standard errors, which is resolved but an order of magnitude smaller. On
the remaining two scenes it is indistinguishable from the reference. This is
the disagreement Section 4.2.2 committed to reporting rather than resolving:
the mechanism improves radiometric agreement while degrading perceptual
similarity, and the two statements are both true because the metrics measure
different properties.

The IUI3 Red Sea result is the mechanism's principal fidelity cost and is the
first appearance of that scene's anomalous behaviour in the mechanism sections.
Section 4.2.4 established that it is also the scene whose fitted medium
spectrum is inverted and whose two coefficient sets disagree, and Section 4.12.4
collects the five observations that attach to it. No causal claim links them
here. What can be said is that the scene on which a fixed initial population is
least adequate is also the scene with the fewest and worst-conditioned training
views — 25 frames acquired consecutively along a reef wall — which is the
condition under which a correspondence-derived cloud would be expected to be
sparsest where the geometry is least constrained.

> **[FIGURE Q1-A1]** `figures/chapter4/figure-q1-a1-initialisation.pdf`
> *Deterministic initialisation against the reference and the baseline.*
> Near-field crop of one held-out view per scene, seed 0, with ground truth,
> the reference, the unmodified configuration and the mechanism in that order.
> Each panel carries the peak signal-to-noise ratio and learned perceptual
> similarity of the view shown, not the scene mean.
> **Status:** built · **Anchored on:** SS

A comparison with the factorial contrast is instructive and is the first
concrete instance of a limitation stated in Section 4.1.3. Measured against the
unmodified configuration rather than the reference, the same mechanism resolves
positive on PSNR on **two** scenes, Japanese Gardens at +0.80 dB and Panama at
+0.72 dB, and its perceptual cost resolves on **one**, IUI3 Red Sea alone.
Measured against the reference it resolves on one scene and two respectively.
The underlying effects are the same; the reference is simply the noisier
comparator on the pixel metric, so the same effect clears the threshold less
often. Neither set of numbers is more correct. The factorial contrast is the
mechanism's effect and is what Section 4.6 composes; the comparison against the
reference is the mechanism's standing relative to the published method and is
what a reader adopting it would experience. Both are reported, and where they
differ in resolution rather than in magnitude, this chapter says so.

> **[FIGURE 4.15b]** `figures/chapter4/figure-4-15b-configurations-vs-reference.pdf`
> *Each configuration against the published reference.* The second group is
> deterministic initialisation. Its peak signal-to-noise interval crosses zero
> on three scenes while sitting wholly above it on Japanese Gardens, and its
> perceptual interval sits clear of zero on IUI3 Red Sea.
> **Status:** built · **Anchored on:** SS

The fidelity result is therefore mixed rather than favourable, and the mixture
is structured. On three of four scenes the mechanism is fidelity-neutral or
better on both metrics. On one scene it is perceptually much worse while
remaining radiometrically neutral. Any recommendation drawn from this section
must carry that conditional, and Section 4.3.5 states it in the form a
practitioner would need.

---

## Review log

**Domain Researcher** — The draft described the mechanism as "a better
initialisation", which is a claim about mechanism quality that the data does
not support and which the source method does not make either. → *applied*:
described by what it does — a fixed correspondence-derived cloud with cloning
and splitting disabled — with the citation. Second finding: the draft offered
no account of why IUI3 Red Sea should be the scene where a fixed population
fails, leaving the largest result in the subsection unexplained.
→ *applied*: the view-count and camera-pairing observation, stated as a
condition under which sparsity would be expected, explicitly not as a cause.

**Supervisor** — The draft reported PSNR and LPIPS in sequence and let the
reader notice they disagree. The disagreement is the subsection's finding and
should be its structure. → *applied*: two bolded paragraphs, one per metric,
with the disagreement named as the thing §4.2.2 committed to. Second finding:
the comparison against the factorial contrast originally read as hedging — two
sets of numbers with no guidance. → *applied*: neither is more correct, each
answers a different question, and the sentence naming which is which. Devil's
advocate: does reporting both invite a reader to pick the flattering one? It
would if only the favourable comparison were given; giving both with the reason
for the difference is the defence.

**Journal Reviewer** — Effects reported without the n or the dispersion the z
is computed against. → *applied*, in the table caption. Second: "48 SE" from
the source analysis was quoted in the draft while the table showed 32.5; the
former is the factorial contrast and the latter the anchored one, and mixing
them is an error. → *applied*: the anchored value in the table, the factorial
value quoted only in the paragraph that names it as such. Third: the source
method needed citation at first mention. → *applied*, from the register.
