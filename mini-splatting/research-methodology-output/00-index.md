# Mini-Splatting — research methodology breakdown

Generated per `../../research-methodology.md`.

## Sources of evidence

| Source | Identifier |
|---|---|
| Paper | `../../mini-splatting.pdf` — *Mini-Splatting: Representing Scenes with a Constrained Number of Gaussians*, Guangchi Fang & Bing Wang (HK PolyU). **ECCV 2024**; local PDF is arXiv:2403.14166**v3** (16 Oct 2024). Includes appendices A–H. |
| Repo | `github.com/fatPeter/mini-splatting`, inspected at commit **`c0d55811930dec3bfd3d61cad927093d166aaf82`** (`c0d5581`), branch `main`, authored 2024-10-12. No release tags. |

The repo contains **four** pipelines, each with its own `train.py`/`run.py`:

| Dir | Variant | Role |
|---|---|---|
| `gs/` | vanilla 3DGS | baseline (`3DGS*` rows in Table 1) |
| `ms_d/` | **Mini-Splatting-D** | densification only — quality-prioritized |
| `ms/` | **Mini-Splatting** | densification **+** simplification — resource-efficient |
| `ms_c/` | **Mini-Splatting-C** | post-hoc compression of a trained `ms/` model |

Unless stated otherwise, "the code" below means `ms/train.py` (the headline method).
Differences in `ms_d/` and `ms_c/` are called out explicitly.

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

Mini-Splatting changes **nothing about the 3DGS loss or the rendering equation**. Its entire
contribution is a rewritten *adaptive density control* schedule, argued from a point-cloud
perspective: 3DGS's Gaussian centers cluster ("overlapping") and miss detail
("under-reconstruction"), so rather than pruning the bad distribution the method
**reorganises** it. Densification adds **blur split** (split any Gaussian that is the
maximum contributor over more than `θ_blur·H·W` pixels) and **depth reinitialization**
(rasterize a per-pixel ray/ellipsoid mid-point depth, backproject, resample ≈3.5 M points,
and hard-reset the whole Gaussian set to those points, every 5 K iterations).
Simplification then applies **intersection preserving** (keep only Gaussians that are the
argmax contributor somewhere) and **importance-weighted stochastic sampling**
(`P_i ∝ I_i`, not top-`k` pruning) at 15 K, plus a light CDF prune at 20 K.

> Because the loss is untouched, this folder's §4 is short and its §5 is unusual: the
> "objective" being made well-posed is not a loss at all but the *spatial distribution* of
> primitives — see [`05-constraints.md`](05-constraints.md).

> **Two significant undocumented deltas:** opacity reset — 3DGS's core anti-floater
> mechanism — is **entirely removed**; and depth-reinit point sampling is **importance-
> weighted by `1 − α_accum`**, not "randomly select" as §4.1 states. See
> [`06-implementation-deltas.md`](06-implementation-deltas.md) D-1 and D-2.
