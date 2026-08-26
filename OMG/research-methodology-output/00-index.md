# OMG — research methodology breakdown

Generated per `../../research-methodology.md`.

## Sources of evidence

| Source | Identifier |
|---|---|
| Paper | `../../OMG.pdf` — *Optimized Minimal 3D Gaussian Splatting*, Joo Chan Lee (SKKU), Jong Hwan Ko (SKKU), Eunbyung Park (Yonsei). **NeurIPS 2025**; local PDF is **arXiv:2503.16924v2**, 6 Nov 2025. |
| Repo | `github.com/maincold2/OMG`, commit **`6edeb72d4dbaf34ffe724deb0c1dc0ca3bece0bb`** (`6edeb72`), branch `main`, 2025-03-24. No tags. |

⚠️ The commit is **~7 months older** than the arXiv v2 revision. Deltas that could plausibly
be v1→v2 drift are marked 🔶.

## Built directly on `../mini-splatting/`

> "Our model is implemented upon **Mini-Splatting [14]**, one of the methods achieving high
> performance with a small number of Gaussians." `[paper §4.1]`
> "Our code is based on [Mini-Splatting](https://github.com/fatPeter/mini-splatting)."
> `[repo: README.md]`

The inheritance is verbatim, not nominal — `arguments/__init__.py` carries Mini-Splatting's
entire parameter set unchanged (`simp_iteration1 = 15000`, `simp_iteration2 = 20000`,
`num_depth = 3_500_000`, `num_max = 4_500_000`, `sampling_factor = 0.5`), and
`intersection_preserving()` `[repo: scene/gaussian_model.py:627-650]` is Mini-Splatting's
importance routine line-for-line. **Read
`../mini-splatting/research-methodology-output/` first** — everything documented there about
blur split, depth reinitialization, the removed opacity reset and the LR-schedule rewind
applies here too.

OMG replaces exactly **one** step of that pipeline (the second simplification prune) and adds
**two** new stages (a neural field for appearance, and sub-vector quantization).

## Evidence tags

`[paper §X / Eq. Y]` · `[repo: path:line]` · `[unverified]` · `[inferred]` · 🔶 = possible
v1/v2 drift.

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

OMG attacks a gap the compression literature had left open: methods that **reduce the number
of Gaussians** and methods that **compress attributes** do not compose, because "a smaller set
of Gaussians becomes increasingly sensitive to lossy attribute compression" `[paper Abstract]`.
OMG does both at once, with three components. **(1) Local distinctiveness (LD) scoring** —
importance is the usual blending-weight score *multiplied by* a measure of how different a
Gaussian's appearance feature is from its Morton-order neighbours, so that redundant
near-duplicates are pruned in preference to locally-unique ones. **(2) A hybrid appearance
representation** — each Gaussian keeps a tiny 3-D static feature `T` and 3-D view-dependent
feature `V`, concatenated with a 13-D **space feature** `F` decoded from the Gaussian's
position by a *tiny* frequency-encoded MLP; four small MLPs then produce DC colour, opacity
and the 45 higher-order SH coefficients. Geometry (scale, rotation) stays per-Gaussian,
because "as Gaussians become sparser … each Gaussian covers a larger spatial region, requiring
a more specific scale and rotation" `[paper §3.1]`. **(3) Sub-vector quantization (SVQ)** —
attribute vectors are partitioned and each partition gets its own small codebook (Product
Quantization), avoiding both VQ's huge codebooks and R-VQ's multiple indices per attribute.

> **Result:** **4.06 MB** at 27.06 PSNR on Mip-NeRF 360 — ~200× smaller than 3DGS and ~50%
> smaller than the previous SotA — at **350 FPS (612 on a 4090)** `[paper Tab. 1]`.

> **Headline deltas found:** the paper's `N_i^K` "K-nearest neighbors" is **exactly 2**
> neighbours in code; the codebook "fine-tuning" runs at **lr = 1e-8** (effectively frozen);
> `D`, `λ`, all four SVQ configurations and the entire MLP architecture appear only in code.
