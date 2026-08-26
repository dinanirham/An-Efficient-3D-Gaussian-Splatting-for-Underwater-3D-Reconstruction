# RoMa v2 — research methodology breakdown

Generated per `../../research-methodology.md`.

## Sources of evidence

| Source | Identifier |
|---|---|
| Paper | `../../RoMaV2.pdf` — *RoMa v2: Harder Better Faster Denser Feature Matching*, Johan Edstedt, David Nordström, Yushan Zhang, Georg Bökman, Jonathan Astermark, Anders Heyden, Viktor Larsson, Mårten Wadenbäck, Michael Felsberg, Fredrik Kahl (Linköping / Chalmers / Amsterdam / Lund). **arXiv:2511.15706v3**, 6 Jul 2026. |
| Repo | `github.com/Parskatt/RoMaV2`, commit **`95c9968145c8906b7b59383258e9f73b02853d89`**, `git describe` → **`v2.0.1-2-g95c9968`**, branch `main`, 2026-04-20. Package version `2.0.1` `[repo: pyproject.toml]`. |

**This is the only folder in the comparison set with a semver release tag** (`v2.0.1`), and
the pretrained checkpoint is pinned to it:
`https://github.com/Parskatt/RoMaV2/releases/download/v2.0.1/romav2.0.1.pt`
`[repo: src/romav2/romav2.py:95-98]`.

## ⚠️ Training code is not released — this is an inference-only package

`[repo: src/romav2/romav2.py:172]`:
```python
assert not self.training, "Currently only inference mode released"
```

Consequences for this breakdown, which are structural rather than incidental:

- **§4 (losses)** — `L_NLL`, `L_warp`, `L_overlap`, `L_prec` (paper Eqs. 1–5) have **no code
  counterpart**. They are documented from the paper alone and tagged accordingly.
- **§3 (independent variables)** — there are no optimized variables in the released
  artifact. The section instead documents the **frozen architecture** and its checkpointed
  parameters, plus what the paper says was trained.
- **§10 (reproducibility)** — no seeds, no data pipeline, no training schedule. What *is*
  reproducible is inference, and that is unusually well pinned (see
  [`10-reproducibility.md`](10-reproducibility.md)).
- The `src/romav2/benchmarks/` directory **does** ship, so the evaluation numbers of
  Tables 4, 6, 7 and 11 are re-runnable `[repo: src/romav2/benchmarks/{mega1500,scannet1500,wxbs,satast}.py]`.

## A note on this folder's role in your comparison set

RoMa v2 is **not a radiance field**. It is a two-view dense correspondence model, and it sits
in your set for one concrete reason: **`../EDGS/` depends on RoMa v1 as its geometry source**
(`from romatch import roma_outdoor`, `[EDGS repo: source/corr_init.py:17]`), and EDGS's
Table 5 ablates the matcher. RoMa v2 is the untested drop-in upgrade for that slot. Sections
1, 8 and 9 here are written with that link in the foreground.

## Evidence tags

`[paper §X / Eq. Y]` · `[repo: path:line]` · `[unverified]` · `[inferred]` ·
**`[paper-only]`** = described in the paper with no released implementation (training).

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

RoMa v2 estimates, for an image pair, a **bidirectional dense warp** `W = {W^{A↦B}, W^{B↦A}}`,
a **confidence/overlap** map `p`, and — new in v2 — a per-pixel **2×2 precision matrix**
`Σ⁻¹`. The architecture is two-stage. A **coarse matcher** runs frozen **DINOv3 ViT-L/16**
features from both images through a **ViT-B multi-view Transformer with alternating
frame-wise and global attention**, then a DPT head emits a stride-4 warp and confidence.
Three **convolutional refiners** at strides {4, 2, 1} then sharpen it to full resolution,
each conditioned on the previous warp and confidence via a local correlation volume. The
principal changes from RoMa v1 are: DINOv2 → DINOv3; the **Gaussian Process replaced by
single-headed attention** plus a new patch-level NLL loss `L_NLL`; a **decoupled two-stage
training schedule** (matcher first, then frozen while refiners train); a **custom CUDA kernel**
for local correlation; a **much broader training mixture** (10 datasets vs RoMa's
MegaDepth-only); predictive covariance; and an **EMA** on the refiners to remove a measured
sub-pixel bias.

> **Headline caveat:** the released package is **inference-only**, so every claim in §3.2–3.5
> of the paper (architecture-internal losses, data mixture, training schedule, EMA) is
> unverifiable against code. What *is* verifiable — architecture shapes, the frozen DINOv3
> backbone, the `scale = 1` position-embedding fix, the Cholesky precision
> parameterisation, the inference resolutions — checks out.
