# Qualitative figure production — specification

**Purpose.** Chapter IV's quantitative tables answer *how much*. The qualitative
figures answer *what it looks like and where*, and they are the part an examiner
reads first. This document fixes how they are produced so that every one of them
supports a claim rather than decorating one.

**Standard.** Q1 journal conventions for novel view synthesis: fixed view, fixed
crop, ground truth present, per-panel metrics, error visible, and a caption that
says what to look at and what the figure does not show.

---

## 1. The comparison rule

**Every qualitative comparison shows ground truth, the reference, the baseline,
and the configuration under test — in that order, always.**

```
ground truth │ SS reference │ A0 baseline │ configuration
```

Three reasons this is not negotiable:

1. **Ground truth** is what both are approximating. Without it a reader is
   comparing two renders to each other and cannot tell which is closer.
2. **SS** is the published method. A mechanism's effect is only interesting
   relative to a baseline that is itself faithful, and the reader should be able
   to confirm that faithfulness in the same glance rather than trusting §4.2.1.
3. **A0** is the contrast every number in the chapter is measured against. If it
   is absent, the figure and the table are measuring different things.

A figure comparing two mechanisms to each other still carries all four columns;
the mechanisms are added, not substituted.

## 2. What every panel carries

| Element | Rule |
|---|---|
| View | One held-out view per scene, chosen deterministically, identical across every panel of every figure |
| Crop | Identical box across panels, expressed as a fraction of the image because the scenes differ in resolution |
| Metric | The per-view PSNR and LPIPS **of that view in that configuration**, from `per_view_metrics.csv` — not the scene mean |
| Label | Configuration name and what it is (`A2 — simplification`), never the bare cell code alone |
| Provenance | Seed 0, stated once in the caption, because that is the only repeat with a stored point cloud |

Per-panel metrics are the single most useful enrichment: they let a reader
connect what they see to the number in the table, and they expose the cases
where the eye and the metric disagree — which this campaign has several of.

## 3. Highlighting — only where something is established

Highlight marks are claims. Each is permitted only when the analysis supports it,
and each is drawn in the accent colour used for nothing else.

| Mark | Use when | Source |
|---|---|---|
| Accent border on a panel | That run lost an attenuation channel | §5a |
| Accent border on a panel | That configuration × scene carries the largest resolved cost in the figure's metric | §2 |
| Inset box on the full frame | Showing where a crop was taken | — |
| Arrow or ring | A specific, nameable artefact the caption then discusses | — |

**Never highlight** a difference that is unresolved, a difference the reader
cannot see, or a panel merely because it is the thesis's own mechanism.
An unhighlighted figure is preferable to a highlight that overstates.

## 4. The figure family

**F1 — Per-mechanism comparison, one per mechanism (A0D, A1–A7): 7–8 figures.**
Rows are scenes, columns are the four of the comparison rule. Cropped to the
region where the mechanism's effect is argued to appear: near-field for
initialisation and simplification, far-field for quantisation, near-field for
the combinations. Per-panel PSNR and LPIPS. Collapse and largest-cost marks
where they apply.

**F2 — Full-set overview, one scene, all ten configurations.** Two rows of five.
The figure a reader uses to see the whole design at once. Curaçao, which carries
the largest population and the widest span of outcomes.

**F3 — Error maps, baseline against each mechanism.** Absolute difference from
ground truth, identically scaled across panels, for one scene. Shows *where*
error sits rather than how much, which no table does.

**F4 — Medium decomposition** (already built as 4.4). Extend from the baseline
alone to baseline, one collapsed run and one quantised run, so the decomposition
is shown succeeding and failing.

**F5 — The three special figures** already specified: the invisible population
(4.5), the collapsed medium (4.13), both attribute states (4.14).

## 5. What the figures must show, from the analysis

Each of these is established and currently has no qualitative counterpart. A
figure that shows one of them earns its page.

1. **The reference and the baseline are indistinguishable** — F1, every row.
2. **Initialisation reaches baseline quality with 10–16× fewer primitives** —
   F1 for A1, with the count in the panel label.
3. **Simplification softens near-field texture** while improving PSNR on two
   scenes — F1 for A2, the case where the eye and PSNR disagree.
4. **Quantisation is invisible in the composed image** — F1 for A3 at the far
   field, which is the argument for why the composed metrics cannot see it.
5. **IUI3 Red Sea costs perceptual quality under every mechanism** — visible as
   a row that degrades across all of F1.
6. **A collapsed medium leaves the composed image intact** — 4.13.

## 6. Production rules

* Figures are produced by a committed script, never by hand, so that a
  re-collection reproduces them exactly. Rendering is deterministic.
* Both PDF (vector text) and 300 dpi PNG.
* No panel is upscaled; crops come from the full-resolution render.
* Error maps state their scaling factor in the caption.
* A missing panel renders as an explicit "not collected" box, never as a gap
  that a reader might mistake for a result.
* Every caption states what to look at **and** what the figure does not show.

## 7. Collection requirement

F1 needs renders for all ten configurations. The collector currently renders
six: `SS, A0, A1, A2, A3, A4`. It must render `A0D, A5, A6, A7` as well —
four more configurations × four scenes × six image kinds.
