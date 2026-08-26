# EDGS — research methodology breakdown

Generated per `../../research-methodology.md`.

## Sources of evidence

| Source | Identifier |
|---|---|
| Paper | `../../EDGS.pdf` — *EDGS: Eliminating Densification for Efficient Convergence of 3DGS*, Dmytro Kotovenko\*, Olga Grebenkova\*, Björn Ommer (CompVis @ LMU Munich / MCML). **CVPR 2026**; local PDF is **arXiv:2504.13204v2**, 12 Feb 2026. |
| Repo | `github.com/CompVis/EDGS`, HEAD **`f90b022445fc88368f75e66e8fb34aea88372cac`** (`f90b022`), branch `main`, 2026-07-04. No tags. |

## ⚠️ The released code predates the paper by ~10 months

`git log` shows **exactly one code-bearing commit**:

| Commit | Date | Subject |
|---|---|---|
| `f90b022` | 2026-07-04 | Revise citation for EDGS paper to CVPR format |
| `9a89764` | 2026-03-25 | Update README with CVPR 2026 details and news |
| `eb21ad5` | 2025-05-12 | Update links to demo |
| `b0db2e6` | 2025-04-23 | Delete unnecessary files |
| `e419fd2` | 2025-04-23 | Update demo link |
| `606542b` | 2025-04-21 | Added citation |
| `2872045` | 2025-04-21 | Create LICENSE.txt |
| **`668e280`** | **2025-04-21** | **Init public code** |

`git diff --stat 668e280 HEAD` touches only `LICENSE.txt`, `README.md`, and the removal of
a `submodules/vggt` pointer. **No `.py` file has changed since 2025-04-21**, i.e. since
arXiv **v1**. The repo's own README says so:

> "**2026-03-25: Updated training code will be released soon.**" `[repo: README.md]`

It has not been. Consequently:

- The code implements the **v1** method. The local PDF is **v2**.
- **§3.5 (spherical-harmonics initialization, Eqs. 12–13) is not implemented at all** — see
  [`06-implementation-deltas.md`](06-implementation-deltas.md) D-1. Table 6's `SH Init.`
  column cannot be reproduced from this checkout.
- Deltas below marked 🔶 are plausibly explained by this v1/v2 gap rather than by an
  implementation error.

## Evidence tags

`[paper §X / Eq. Y]` (= arXiv:2504.13204**v2**) · `[repo: path:line]` (= commit `668e280`
content, HEAD `f90b022`) · `[unverified]` · `[inferred]` · 🔶 = plausible v1/v2 drift.

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

EDGS deletes 3DGS's adaptive density control and replaces it with a **one-shot dense
initialization**. Reference views are chosen by K-means over camera poses; for each, the
`nns_per_ref` nearest neighbours are matched with a pretrained **dense correspondence
network** — **RoMa** by default, which is the `../RoMa/` folder in this comparison set —
yielding a per-pixel warp field `W_ij` and a confidence map `c_ij`. Matched pixel pairs are
**triangulated** by a least-squares solve into 3D points; a sampling distribution combining
matcher confidence (`p^corr`) and reprojection error (`p^proj`) selects which to keep; and
each surviving point becomes a Gaussian with position from triangulation, colour from the
reference image pixel, and scale proportional to its distance from the reference camera.
The original SfM points are then **deleted**, and training proceeds with the stock 3DGS
photometric loss and **no densification at all**.

> **The loss is completely unmodified** — like `mini-splatting/`, EDGS's entire contribution
> is upstream of the objective. Unlike `mini-splatting/`, it is upstream of *optimization
> itself*: the contribution happens once, before step 1.

> **Headline deltas found:** §3.5's SH initialization is absent from the code (`f_rest ← 0`);
> `p^proj` is implemented as an **opacity mask**, not a sampling distribution; and the
> trainer applies two undocumented mechanisms — a **continuous ×0.99 opacity decay every 10
> steps** and a **learning-rate schedule clamped to step ≥ 8000**.
