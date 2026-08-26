# CompGS (Liu et al.) — research methodology breakdown

Generated per `../../research-methodology.md`.

## ⚠️ Note on the acronym collision

**Two unrelated works share the name "CompGS."** This folder is a checkout of
`github.com/LiuXiangrui/CompGS` (confirmed by `git remote -v`) — *Efficient 3D Scene
Representation via Compressed Gaussian Splatting* (ACM MM 2024). The other is
**arXiv:2311.18159, "CompGS: Smaller and Faster Gaussian Splatting with Vector
Quantization"** (Navaneet et al., UC Davis, ECCV 2024) = the **`../../compact3d/`** folder.
That other work is a **baseline this paper compares against** — "Navaneet et al. [33]" in
Tables 1–3 and Fig. 6.

> **Resolved 2026-08-25:** `../../CompGS.pdf` previously held a byte-identical copy of
> `../../compact3d.pdf` (the wrong paper). It has been replaced with the correct paper,
> verified byte-identical (`md5 = 89f5638d43128cc7017ef796280341f6`) to
> `arxiv.org/pdf/2404.09458v1`. **All `[paper …]` citations in this folder resolve against
> the current local PDF.**

## Sources of evidence

| Source | Identifier |
|---|---|
| Paper | `../../CompGS.pdf` — *CompGS: Efficient 3D Scene Representation via Compressed Gaussian Splatting*, Xiangrui Liu, Xinju Wu, Pingping Zhang, Shiqi Wang, Zhu Li, Sam Kwong (CityU HK / UMKC / Lingnan). **arXiv:2404.09458v1**, 15 Apr 2024. |
| Repo | `github.com/LiuXiangrui/CompGS`, commit **`d501617323606b769246eafc1fb8472a61859e1d`** (`d501617`), branch `main`, 2024-11-07. No tags. |
| ⚠️ Version caveat | The repo's own BibTeX cites the **ACM MM 2024** version (`booktitle={Proceedings of the 32nd ACM International Conference on Multimedia}`), while the local PDF is the CVPR-format **arXiv v1** (April 2024), ~7 months older than the commit. **Some deltas below may be revision drift between arXiv v1 and the MM camera-ready, which I could not obtain.** Every such case is flagged. |

Evidence tags in this folder carry an extra distinction:

- `[paper §X / Eq. Y]` — arXiv:2404.09458**v1** = the current `../../CompGS.pdf`.
- `[repo: path:line]` — confirmed at commit `d501617`.
- `[unverified]` / `[inferred]` — as elsewhere.
- 🔶 — marks a claim where the arXiv-v1-vs-MM version gap is a plausible explanation.

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

CompGS (Liu et al.) imports the **hybrid video-coding paradigm** — predictive coding plus
rate-distortion optimization — into Gaussian splatting. The scene is represented by a small
set of **anchor primitives** `ω` (frozen voxelized SfM positions, a learned 6-D scaling
vector, a rotation quaternion, and a 32-D reference embedding `f_ω`), each of which
*predicts* `K = 10` **coupled primitives** `γ_k` that carry only an 8-D **residual
embedding** `g_k`. Small MLPs decode `{f_ω, g_k}` into per-coupled-primitive position
offsets, scales, rotations, opacities and view-dependent colours; only the coupled
primitives are ever rasterized. Every learned embedding is then passed through a
**CompressAI-style conditional Gaussian entropy model with hyperpriors**, whose estimated
bitrate enters the loss as `λR`, so the representation is trained directly against a
rate-distortion cost and afterwards entropy-coded with arithmetic coding (embeddings) and
**G-PCC** (anchor positions).

> The structural backbone — anchors, `K` derived primitives, view-dependent MLP decoding,
> and the anchor growing/pruning rules — is **Scaffold-GS** (Lu et al., ref [27]),
> acknowledged in the README. CompGS's own contributions are the *residual embeddings* and
> the *rate-constrained optimization*, which are exactly what Table 4 and Table 5 ablate.

> **Headline deltas found:** the implemented loss has a **third term the paper never
> mentions** (a Scaffold-GS scale-volume regulariser); the "affine transform" of Eqs. 2–4
> is implemented as Scaffold-GS offset prediction with **two** MLPs, not three; and the
> reported `num_gaussians` counts **anchors only**, not the `10×` larger set actually
> rendered. See [`06-implementation-deltas.md`](06-implementation-deltas.md).
