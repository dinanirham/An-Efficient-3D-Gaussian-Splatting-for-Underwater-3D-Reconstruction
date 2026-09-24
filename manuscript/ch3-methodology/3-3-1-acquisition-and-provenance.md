---
section: "3.3.1"
title: "Acquisition and Provenance"
chapter: 3
action: Retain
evidence: ["dataset", "LIT"]
figures: []
tables: ["Table 3.3"]
citations:
  - "Levy et al., 2023"
  - "Schönberger & Frahm, 2016"
status: refined
word_count: 562
---

# 3.3.1 Acquisition and Provenance

The corpus is the SeaThru-NeRF dataset (Levy et al., 2023): four underwater
scenes captured with a housed digital camera by a diver, with camera poses
recovered by structure from motion (Schönberger & Frahm, 2016). It is the
public corpus for this task, and the four scenes are its entirety.

> **[TABLE 3.3]** *Corpus composition.* Image counts are the dataset's own;
> the held-out counts follow from the partitioning rule of Section 3.4.4 and
> are confirmed against the evaluation records of the executed campaign.

| Scene | Images | Training | Held out | Water body | Character |
|---|---:|---:|---:|---|---|
| Curaçao | 21 | 18 | 3 | Caribbean | Reef structure, moderate visibility |
| IUI3 Red Sea | 29 | 25 | 4 | Red Sea | Reef wall, higher visibility |
| Japanese Gardens | 20 | 17 | 3 | Red Sea | Coral garden, mixed range |
| Panama | 18 | 15 | 3 | Pacific | Turbid, strong backscatter |
| **Total** | **88** | **75** | **13** | | |

**The corpus was chosen for comparability rather than for size.** The
convention throughout this lineage is to hold out every eighth image by index
order, so the held-out frames used here are the same frames that the underwater
methods this study builds on and compares against also hold out. A fidelity
number produced here is measured on the same pixels as a published one, which
is a stronger form of comparability than most cross-paper comparison in this
literature affords.

The four scenes also span a usefully wide range of water conditions, which
matters more for this study than for a purely geometric one: the medium model's
identifiability depends on how much the water actually does to the image, and a
corpus of uniformly clear water would not exercise it. In practice the range
proved wider than water type alone would suggest — the four scenes differ by
approximately 7 dB in reconstruction difficulty (Section 4.2.2), and one of
them behaves anomalously in six respects that Section 4.12.4 collects.

Two properties of the acquisition bear on results reported later and are
recorded here rather than discovered there. The scenes differ substantially in
view count, from 18 images to 29. And the views of IUI3 Red Sea — the scene
with the most images — were taken consecutively along a reef wall, which gives
the narrowest range of camera baselines in the corpus and therefore the
weakest triangulation constraints. That scene is the one on which every
mechanism's perceptual cost is largest and on which the fitted medium model is
least internally coherent. The association is recorded in Section 4.12.4 and is
not explained by this campaign, which varied neither view count nor baseline.

Provenance of the data itself is straightforward and worth stating for
reproducibility: the dataset is used as published, with no images added,
removed or re-annotated, and the preprocessing of Section 3.4 is the only
transformation applied between the published files and the training loop.

---

## Review log

**Domain Researcher** — The draft gave image counts without the training and
held-out split, which a reader needs in order to judge the evaluation. Adding
it also surfaced that IUI3's 25 training views, quoted repeatedly in Chapter
IV, are derivable here. → *applied*: both columns, confirmed against the
campaign's own evaluation records rather than asserted. Second finding: the
"why this corpus" argument rested on water variety alone; the observed 7 dB
difficulty span is the stronger version of the same point. → *applied*.

**Supervisor** — The draft's acquisition detail sat in a limitations subsection
where a reader meets it after forming a view of the corpus. The consecutive
reef-wall acquisition on IUI3 is load-bearing for Chapter IV's anomalous scene
and belongs with the description of the data. → *applied*, with the association
flagged as unexplained. Devil's advocate: does foregrounding one scene's
weakness undermine the corpus? It is the entire public corpus for the task;
naming its properties is the only honest option available.

**Journal Reviewer** — Held-out counts were asserted without a source, in a
table a reader would use to check the evaluation. → *applied*: the caption
names the rule and the verification. Second: dataset provenance — whether
images were modified — was not stated at all. → *applied*: closing paragraph.
