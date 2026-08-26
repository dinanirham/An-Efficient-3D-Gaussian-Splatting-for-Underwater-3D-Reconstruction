# SeaThru-NeRF — research methodology breakdown

Generated per `../../research-methodology.md`.

## Sources of evidence

| Source | Identifier |
|---|---|
| Paper | `../../seathru_NeRF.pdf` — *SeaThru-NeRF: Neural Radiance Fields in Scattering Media*, Levy, Peleg, Pearl, Rosenbaum, Akkaynak, Korman, Treibitz. **CVPR 2023**; local PDF is arXiv:2304.07743v1 (16 Apr 2023). |
| Repo | `github.com/deborahLevy130/seathru_NeRF`, inspected at commit **`3f4ebfe2c9dcb93af7916a3c7e7e196b9b956160`** (`3f4ebfe`), branch `master`, authored 2024-03-14. No release tags. |

Language: **JAX / Flax**, forked from `google-research/multinerf` (mip-NeRF 360).
Configuration is **gin**-based, so "defaults" means the values in
`configs/llff_256_uw.gin` — the config the released training script actually uses — not
the Python dataclass defaults in `internal/configs.py`. Both are cited where they differ.

## Evidence tags

- `[paper §X / Eq. Y]` — stated explicitly in the paper.
- `[repo: path:line]` — confirmed by reading source at commit `3f4ebfe`.
- `[unverified]` — plausible but not traceable to either source in this pass.
- `[inferred]` — derived by combining verified facts; the derivation is stated.

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

SeaThru-NeRF rewrites the volume-rendering integral itself. Where NeRF accumulates a single
`(σ, c)` field, SeaThru-NeRF carries **two**: an *object* field `(σ^obj, c^obj)` queried per
3D sample, and a *medium* field `(σ^bs, σ^attn, c^med)` produced **once per ray** by a small
MLP that sees **only the viewing direction**. The rendered pixel is the sum of an attenuated
object term and an accumulated backscatter term, and the derivation (§4.2) shows this
reduces exactly to the Akkaynak–Treibitz revised image formation model when the object is
opaque. The medium is therefore **a field over viewing directions**, not a set of scene
constants — the defining contrast with SeaSplat. Well-posedness comes from three structural
choices rather than a battery of priors: constancy of the medium along each ray, a
binary-transmittance prior on `T^obj` (Eq. 27), and mip-NeRF 360's proposal/interlevel
machinery.

> **⚠ Two headline paper-vs-repo gaps found:** the released `mediumMLP` is **1 layer of 128
> units**, not the "6 linear layers with 256 features" the paper states; and the released
> config makes the object colour `c^obj` **view-independent**, contradicting §4.3. Details
> in [`06-implementation-deltas.md`](06-implementation-deltas.md) D-1 and D-3.
