# §1 — Taxonomic placement and modification

## Base method extended

**3D Gaussian Splatting**, Kerbl, Kopanas, Leimkühler & Drettakis, *ACM TOG 42(4), 2023*
(ref **[31]**) — the INRIA reference implementation, vendored as a **git submodule**:

`[repo: source/trainer.py:9 — sys.path.append('./submodules/gaussian-splatting/')]`
`[repo: install.sh — pip install -e submodules/gaussian-splatting/submodules/diff-gaussian-rasterization]`

The rasterizer is **unmodified** (note `antialiasing: False` and the presence of
`exposure_lr_*` keys `[repo: configs/gs/base.yaml]`, indicating a *recent* 3DGS release, not
the 2023 original). The optimizer, the loss, the Gaussian parameterisation and the SH
machinery are all stock. What is deleted is **Adaptive Density Control**.

The second, equally essential dependency:

| Lineage | What is inherited | Evidence |
|---|---|---|
| **RoMa: Robust Dense Feature Matching**, Edstedt et al., CVPR 2024 (ref **[13]**) | The dense correspondence network `M` — the source of *all* geometry in the initialization | `[paper §3.2, §4.5]` `[repo: source/corr_init.py:4, 17 — sys.path.append('../submodules/RoMa'); from romatch import roma_outdoor, roma_indoor]` `[repo: install.sh — pip install -e submodules/RoMa]` |

> **This is the direct structural link to your `../RoMa/` folder.** EDGS's default is
> `roma_model: "outdoors"` `[repo: configs/train.yaml]`, and it *reconfigures* RoMa on load:
> `roma_model.upsample_preds = False` and `roma_model.symmetric = False`
> `[repo: source/corr_init.py:538-539]` — disabling two of RoMa's own features for speed.
> Any change you make in `../RoMa/` or `../RoMaV2/` propagates directly into EDGS's geometry.

Other named ingredients: the DLT-style triangulation of §3.3 is classical multi-view
geometry (Hartley & Zisserman), solved by `torch.linalg.lstsq`
`[repo: source/corr_init.py:471-472]`; COLMAP (ref [60]) supplies camera poses.

## The modification, in one sentence

EDGS replaces 3DGS's iterative gradient-triggered densification with a **single dense
initialization**: triangulate hundreds of thousands of dense 2D correspondences from a
pretrained matcher, filter them by matcher confidence and reprojection error, seed one
Gaussian per surviving correspondence with position/colour/scale read directly off the
images, discard the SfM points, and then run stock 3DGS optimization with densification
switched off.

## Design family, in one sentence

EDGS is an **explicit radiance field** (rasterized 3D Gaussians), **per-scene optimized**,
with **no medium/degradation model** — and its axis of contribution is **initialization**,
which makes it the only method in your comparison set that changes *neither the objective
nor the optimizer nor the representation*, only the starting point.

### The axis, and why it is genuinely different

| | **EDGS** | `mini-splatting/` | `CompGS/`, `compact3d/`, `OMG/` | `seasplat/`, `seathru_NeRF/` |
|---|---|---|---|---|
| Changes the loss? | ❌ | ❌ | ✅ | ✅ |
| Changes the optimizer/schedule? | ⚠️ yes, but undocumented (see D-3, D-4) | ✅ (reinit, LR rewind) | ✅ | ✅ |
| Changes the representation? | ❌ | ❌ | ✅ | ❌ / ✅ |
| Changes the rasterizer? | ❌ | ✅ (forked kernel) | ❌ | ✅ (depth pass) |
| **Changes initialization?** | ✅ **this is the whole method** | ⚠️ repeatedly, mid-training | ❌ | ❌ |
| Needs an external pretrained network? | ✅ **RoMa** | ❌ | ❌ (but CompGS needs G-PCC) | ❌ |
| Composable with the others? | ✅ **by construction** | partially | — | — |

**Composability is the paper's strongest structural claim, and it is well supported.**
Table 3 drops EDGS in as the initializer for three *unmodified* competing densification
methods and improves all three:

| Method | without EDGS init | with EDGS init | Δ |
|---|---|---|---|
| AbsGS-0004 [85] | 0.818 / 27.41 / 0.198 | **0.822 / 27.53 / 0.187** | +0.12 dB, −6% LPIPS |
| 3DGS-MCMC [32] | 0.842 / 28.15 / 0.176 | **0.847 / 28.29 / 0.159** | +0.14 dB, −10% LPIPS |
| Taming 3DGS [46] | 0.820 / 27.71 / 0.207 | **0.842 / 28.07 / 0.179** | +0.36 dB, −14% LPIPS |

"without increasing final Gaussian count or increasing training time" `[paper Tab. 3]`, and
crucially **"without fine-tuning hyperparameters"** — no per-method retuning. This is the
result to cite when arguing EDGS is orthogonal to the rest of your comparison set.

### Three further consequences

1. **The `#G` column moves in the *opposite* direction from most efficiency work.** EDGS
   *reduces* the final Gaussian count while *improving* quality: on Mip-NeRF 360, **1.9 M**
   vs 3DGS\*'s 2.8 M and 3DGS's 3.5 M `[paper Tab. 1]`. It gets there by starting dense and
   only pruning, rather than starting sparse and growing. Contrast `mini-splatting/`, whose
   D-variant *increases* the count.
2. **It inherits the matcher's failure modes.** Everything geometric comes from RoMa.
   Table 5 shows the method is fairly robust to the choice (LoFTR 27.49, DKM 27.79, RoMa
   28.02) **except** RAFT (26.90), which the paper explains: RAFT "struggles due to its
   primary design for optical flow between consecutive video frames, where viewpoint
   differences are minimal" `[paper §4.5]`. Textureless or non-Lambertian regions — water
   column, sky, specular surfaces — are where dense matchers are weakest, which bears
   directly on any underwater application.
3. **Densification is not merely unnecessary — it is nearly useless here.** Table 4:
   3DGS drops from 27.49 to **25.60** dB without densification (−1.89 dB), whereas EDGS
   gains only **+0.06 dB** *with* it (28.02 → 28.08). "EDGS does not require densification
   and only marginally improves when densification is applied" `[paper Tab. 4 caption]`.

## Position relative to the sibling folders

| Folder | Relationship |
|---|---|
| `gaussian-splatting/` | the base method and a vendored submodule; `3DGS*` in Table 1 is a retrained baseline |
| **`RoMa/`** | **a hard dependency** — the default matcher `M`, reconfigured at `corr_init.py:538-539`. Ablated in Table 5 |
| **`RoMaV2/`** | the successor to that dependency; not evaluated by the paper, and an obvious upgrade path for you |
| `mini-splatting/` | cited as ref **[15]** ("MiniSplatting") and compared against in Tables 1–2. **The closest methodological neighbour**: both attack the spatial distribution of Gaussians, one by re-initializing repeatedly during training, the other by initializing once, well |
| `colmap/` | upstream poses (ref [60]); EDGS still needs COLMAP, it only stops needing COLMAP's *points* |
| `CompGS/`, `compact3d/`, `OMG/` | orthogonal (compression); EDGS composes with them in principle |
| `seasplat/`, `seathru_NeRF/`, `nerf/` | orthogonal, but see the note above on dense matching in scattering media |
