# SeaSplat — research methodology breakdown

Generated per `../../research-methodology.md`.

## Sources of evidence

| Source | Identifier |
|---|---|
| Paper | `../../seasplat.pdf` — *SeaSplat: Representing Underwater Scenes with 3D Gaussian Splatting and a Physically Grounded Image Formation Model*, Yang, Leonard, Girdhar. arXiv:2409.17345v2 [cs.CV], 2 Jun 2025. |
| Repo | `github.com/dxyang/seasplat`, inspected at commit **`ddc6259db238a5cc72fcc9e0e99a6589fd20d48f`** (`ddc6259`), branch `master`, authored 2024-11-27. `git describe --always` → `ddc6259`; no release tags exist in this repository. |

> Note: the local PDF is the **v2** (June 2025) arXiv revision, while the repo HEAD is from **November 2024**. Some paper-vs-repo deltas below may be revision drift rather than genuine disagreement; this is flagged where it matters.

## Evidence tags used throughout

- `[paper §X / Eq. Y]` — stated explicitly in the paper.
- `[repo: path:line]` — confirmed by reading source at commit `ddc6259`.
- `[unverified]` — plausible/commonly-assumed but not traceable to either source in this pass.
- `[inferred]` — derived by me from combining two verified facts; the derivation is stated.

## Section files

| § | File | Contents |
|---|---|---|
| 1 | [`01-taxonomy.md`](01-taxonomy.md) | Base method, modification, design family |
| 2 | [`02-pipeline.md`](02-pipeline.md) | Pipeline flowcharts + loss-composition diagram (Mermaid) |
| 3 | [`03-variables.md`](03-variables.md) | Independent / dependent / fixed variables with shapes + init |
| 4 | [`04-loss.md`](04-loss.md) | Every loss term, purpose, failure mode, ablation-table reading |
| 5 | [`05-constraints.md`](05-constraints.md) | Degeneracies of the naive objective and the resolving mechanisms |
| 6 | [`06-implementation-deltas.md`](06-implementation-deltas.md) | Paper-vs-repo deltas, source-tagged |
| 7 | [`07-pseudocode.md`](07-pseudocode.md) | Full train step, per-line source tags, schedule gates, detach points |
| 8 | [`08-computational-profile.md`](08-computational-profile.md) | Time / FPS / VRAM / parameter count, complexity claims |
| 9 | [`09-glossary.md`](09-glossary.md) | Symbol → meaning → first definition |
| 10 | [`10-reproducibility.md`](10-reproducibility.md) | Seeds, splits, exact metric computation, non-determinism |
| — | [`11-paper-vs-repo-disagreements.md`](11-paper-vs-repo-disagreements.md) | Condensed disagreement table (required output) |

## One-paragraph summary

SeaSplat takes vanilla 3D Gaussian Splatting and reinterprets the rasterized radiance
field as the **medium-free** image `Ĵ`, then pushes `Ĵ` through the Akkaynak–Treibitz
revised underwater image formation model — `Î = Ĵ ⊙ Â + B̂`, with `Â = e^{-β^D Ẑ}` and
`B̂ = B^∞(1 - e^{-β^B Ẑ})` — before comparing against the captured image. The medium is
described by **six global scalars** (`β^D ∈ ℝ³`, `β^B ∈ ℝ³`) plus a global water color
`B^∞ ∈ ℝ³`, all shared across the entire scene, in deliberate contrast to SeaThru-NeRF's
per-viewing-direction MLP-predicted medium. Because `Ĵ ⊙ Â + B̂ = I` is massively
underdetermined, the method adds five auxiliary losses and, critically, a
**gradient-detachment + alternating-optimization** scheme so the medium parameters
never back-propagate into the Gaussian geometry.
