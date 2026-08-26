# RoMa — research methodology breakdown

Generated per `../../research-methodology.md`.

## Sources of evidence

| Source | Identifier |
|---|---|
| Paper | `../../RoMa.pdf` — *RoMa: Robust Dense Feature Matching*, Johan Edstedt, Qiyu Sun, Georg Bökman, Mårten Wadenbäck, Michael Felsberg (Linköping / ECUST / Chalmers). **CVPR 2024**; local PDF is **arXiv:2305.15404v2**, 11 Dec 2023. |
| Repo | `github.com/Parskatt/RoMa`, commit **`77f8d68803526dcddfd9b7a46bc76125bdc25f15`**, `git describe --tags` → **`v0.1.2-4-g77f8d68`**, branch `main`, 2026-01-23. |

## ✅ Training code **is** released — unlike `../RoMaV2/`

This is the sharpest practical difference between the two matcher folders and it shapes this
whole breakdown:

| | **RoMa (this folder)** | `../RoMaV2/` |
|---|---|---|
| Loss functions | ✅ `romatch/losses/robust_loss.py` | ❌ |
| Training loop | ✅ `romatch/train/train.py`, `experiments/train_roma_outdoor.py` | ❌ |
| Datasets | ✅ `romatch/datasets/{megadepth,scannet}.py` | ❌ |
| Benchmarks | ✅ 5 harnesses `romatch/benchmarks/` | ✅ 4 harnesses |
| Tag | `v0.1.2` | `v2.0.1` |
| Lockfile | ✅ `uv.lock` present | ❌ absent |

So §4 (losses), §5 (well-posedness) and §10 (reproducibility) here are **verified against
code**, where the v2 folder could only cite the paper. Where the two papers describe the same
mechanism, I cross-reference.

The repo also ships a **`TinyRoMa`** variant (`romatch/models/tiny.py`,
`experiments/train_tiny_roma_v1_outdoor.py`, `romatch/losses/robust_loss_tiny_roma.py`) that
appears **nowhere in the paper** — a repo-only addition, flagged in
[`06-implementation-deltas.md`](06-implementation-deltas.md).

## Evidence tags

`[paper §X / Eq. Y]` · `[repo: path:line]` · `[unverified]` · `[inferred]`

## Section files

| § | File |
|---|---|
| 1 | [`01-taxonomy.md`](01-taxonomy.md) |
| 2 | [`02-pipeline.md`](02-pipeline.md) |
| 3 | [`03-variables.md`](03-variables.md) |
| 4 | [`04-loss.md`](04-loss.md) |
| 5 | [`05-constraints.md`](05-constraints.md) |
| 6 | [`06-implementation-deltas.md`](06-implementation-deltas.md) |
| 7 | [`07-pseudocode.md`](07-pseudocode.md) |
| 8 | [`08-computational-profile.md`](08-computational-profile.md) |
| 9 | [`09-glossary.md`](09-glossary.md) |
| 10 | [`10-reproducibility.md`](10-reproducibility.md) |
| — | [`11-paper-vs-repo-disagreements.md`](11-paper-vs-repo-disagreements.md) |

## One-paragraph summary

RoMa takes **DKM** (Edstedt et al., CVPR 2023) as its baseline and changes three things.
**(a) Features:** the coarse encoder becomes a **frozen DINOv2 ViT-L/14**, and — because
DINOv2 has no fine features and only exists at stride 14 — the feature extractor is
**decoupled** into `F_coarse = DINOv2` plus a *separate*, specialised **VGG19** fine encoder.
The paper's striking finding is that coarse robustness and fine localizability are in
**tension**: VGG19 is *worse* than ResNet50 as a coarse encoder yet *better* as a fine one.
**(b) Decoder:** DKM's ConvNet match decoder is replaced by a **position-encoding-free
Transformer** that predicts **anchor probabilities** over a 64×64 grid rather than regressing
coordinates. **(c) Losses:** motivated by a diffusion model of match localizability, the
coarse stage uses **regression-by-classification** (because motion boundaries make the coarse
conditional multimodal) while the refinement stage uses a **robust generalized-Charbonnier
regression** (because the conditional is locally unimodal). The result set a new SotA, most
dramatically **+36% mAA on WxBS**.

> **Headline deltas found:** the Charbonnier scale `c` is **1e-4 in code vs 0.03 in the
> paper** — a 300× discrepancy; an undocumented **local-window gating** restricts refinement
> supervision at each scale; and all losses are masked to `prob > 0.99`. See
> [`06-implementation-deltas.md`](06-implementation-deltas.md).

## Role in your comparison set

RoMa is **not a radiance field** — it is a two-view dense matcher. It is here because
**`../EDGS/` depends on it directly**: `from romatch import roma_outdoor, roma_indoor`
`[EDGS repo: source/corr_init.py:17]`, and every 3D point EDGS triangulates comes from a RoMa
warp. EDGS's Table 5 ablates the matcher and RoMa wins. Sections 1, 8 and 9 here are written
with that dependency in the foreground.
