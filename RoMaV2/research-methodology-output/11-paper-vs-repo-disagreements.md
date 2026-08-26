# Paper-vs-repo disagreements — RoMa v2

**Paper:** `../../RoMaV2.pdf` = arXiv:2511.15706**v3** (6 Jul 2026).
**Repo:** `Parskatt/RoMaV2` @ **`95c9968`**, `git describe` → **`v2.0.1-2-g95c9968`**
(2026-04-20) — ~2.5 months **older** than the paper revision.

## The framing fact

**The released package is inference-only** `[repo: src/romav2/romav2.py:172]`:
```python
assert not self.training, "Currently only inference mode released"
```
So roughly half the paper (§3.2's losses, §3.3's refinement objective and EMA, §3.4's data
mixture, §3.5's training procedure — Eqs. 1, 2, 4, 5) has **no code to disagree with**.
This is a disclosure boundary, not an error, and the README claims nothing more.

| # | Topic | Paper says | Repo does | Tags | Severity |
|---|---|---|---|---|---|
| D-0 | **Training code** | full training recipe: two stages, 300k steps each, batch 128/64, lr 4e-4, four losses, EMA, 10-dataset mixture | **not released**. No losses, no dataloaders, no optimizer loop, no EMA. Only vestigial type definitions survive (`Batch`, `GTSource`, `OptimizerName="adamw"`) `[repo: types.py]` | `[paper §3.2-3.5]` vs `[repo: romav2.py:172]` | **high** (scope) |
| D-1 | **Similarity temperature** | not mentioned anywhere | `temp: float = 0.1` with the repo's own comment `# NOTE: 0.2 in RoMa` — **halved from v1**, directly sharpening the `Softmax(S)` that both `L_NLL` and the position-embedding aggregation consume | — vs `[repo: matcher.py:75-76]` | **medium** |
| D-2 | **Default inference setting** | §4.1: "coarse resolution of **800 × 800** and a fine resolution of **1024 × 1024**" | library default is `setting="precise"` = **800 → 1280**, `threshold=None`. The 800→1024 + `threshold=0.05` config is the separate `mega1500`/`scannet1500`/`wxbs`/`satast` branch. Tables 6–7 use **640²** (`base`). **Three configs, three tables, and the default matches none** | `[paper §4.1, Tab. 6-7]` vs `[repo: romav2.py:78, 119-160]` | **medium**, high trap value |
| D-3 | **Thresholded sampling** | Eq. 6 presents `p̂ = max(𝟙_{p>0.05}, p)` as *the* sampling procedure | `threshold = 0.05` only in the four benchmark settings; `base`/`fast`/`turbo`/`precise` set `threshold = None`, and `_map_confidence` then skips it | `[paper Eq. 6]` vs `[repo: romav2.py:61-66, 126-158]` | low–medium |
| D-4 | **Runtime preconditions** | not mentioned | `RuntimeError` unless `torch.get_float32_matmul_precision() == "highest"` — a **hard failure**, and it disables TF32 for the entire process | — vs `[repo: romav2.py:169-170]` | **medium** for integration |
| D-5 | **Fine-feature backbone** | Fig. 4 labels it "VGG19" | `vgg19bn` (batch-norm variant) with **`pretrained = False`** — trained from scratch | `[paper Fig. 4]` vs `[repo: features.py:179-182]` | low–medium |
| D-6 | **CUDA kernel availability** | §3.3 presents it as a contribution | optional, imported in `try/except`, dependency gated `sys_platform == 'linux'`. Non-Linux users silently get the 5.6 GB fallback. (Tab. 8 does report both rows, so the paper is not misleading) | `[paper §3.3]` vs `[repo: local_correlation.py:4-7; pyproject.toml]` | low |
| D-7 | **Two-stage refinement asymmetry** | not mentioned | between the low-res and high-res refinement passes, the **precision channels are zeroed** — `confidence[..., 1:] = 0.0` — with the comment *"delta at 4 is absolute, and … for the second pass we therefore can't use first pred. overlap is fine since it's relative to matcher pred."* | — vs `[repo: romav2.py:44-49]` | low–medium |
| D-8 | **§3.5 training resolutions** | a "Training:" sentence listing coarse-matcher resolutions and aspect ratios | **unrecoverable** — mangled in both `pdftotext -layout` and `-raw`. Only "refiners are trained exclusively with size 640 × 640" survives | `[paper §3.5]` — `[unverified]` | low (PDF artifact) |
| D-9 | **Dependency pinning** | — | lower bounds only (`torch` unpinned); **no `uv.lock` in this checkout**, unlike `../RoMa/` which ships one | — vs `[repo: pyproject.toml]` | low |

## ✅ Verified-correct (recorded because §6 is not only for disagreements)

| Paper claim | Code | |
|---|---|---|
| Frozen DINOv3 ViT-L/16 backbone `[§3.2]` | `name="dinov3_vitl16"`, `frozen=True` `[features.py:83-85]` | ✅ |
| `scale`: RoMa's learned 8 → **fixed 1** `[§3.5]` | `scale: float = 1` with `# NOTE: 8 in RoMa` `[matcher.py:77-78]` | ✅ |
| ViT-B multi-view Transformer, alternating attention (VGGT-style) `[§3.2]` | `mv_vit="vit_base"`, `mv_vit_attention_mode="alternating"` `[matcher.py:70-73]` | ✅ |
| DPT head `[§3.2]` | `head="dpt-no-pos"`; `dpt.py` `[matcher.py:74]` | ✅ |
| Three refiners at strides {4, 2, 1} `[§3.3]` | `refiner_type="roma-4-pow2"`, keys `4/2/1` `[refiner.py:228, 239-265]` | ✅ |
| Power-of-two channel widths `[§3.3]` | inline comments compute `512 / 128 / 32` `[refiner.py:239-265]` | ✅ |
| Cholesky precision: `Softplus(z)+1e-6`, `Σ⁻¹ = LLᵀ` `[§3.3]` | `chol_eps = 1e-6`; `F.softplus(...) + chol_eps` `[refiner.py:201-204]`; `prec_mat_from_prec_params` `[geometry.py:168-174]` | ✅ exact |
| `confidence_dim` = 1 overlap + 3 precision `[§3.3]` | `1` at matcher, `4` at refiners `[matcher.py:81; refiner.py:77]` | ✅ |
| Bidirectional warps and confidences `[§1]` | `warp_AB/BA`, `confidence_AB/BA` `[romav2.py:186-196]` | ✅ |
| Normalized-grid RoPE `[§3.5]` | `mv_vit_use_rope=True`; `vit/rope.py` `[matcher.py:71]` | ✅ |
| Balanced KDE sampling `[§4.1]` | `balanced_sampling=True` in all settings `[romav2.py:119-160]` | ✅ |

## Claims that need a caveat when cited

| Claim | Caveat |
|---|---|
| "RoMa v2 **consistently outperforms all prior matchers** on both benchmarks" `[paper §4.1]` | On **MegaDepth-1500 the margin over RoMa v1 is 0.2–0.3 AUC** (62.8 vs 62.6) — a tie, with no error bars. The real margins are in Tables 6/7 (**37–85% EPE reduction**, wins on all 6 datasets). |
| "sets a new state-of-the-art" `[paper Abstract]` | ⚠️ **Except WxBS**, where RoMa v1 wins **60.8 vs 55.4** mAA. Conceded in §5 and traced to the **IR↔RGB** subset in §4.5. Table 10 shows the same sign at the backbone level (DINOv2 35.6 vs DINOv3 34.2). **For cross-modal matching, v1 remains the better model.** |
| DINOv3 is more robust than DINOv2 `[paper Tab. 1]` | Tab. 1 is a **linear probe on MegaDepth** and says DINOv3 wins decisively (EPE 27.1→19.0). Tab. 10, end-to-end, says DINOv3 **loses on WxBS**. The two tables measure different things; quote both. |
| `L_NLL` is worth 2.7× PCK@1px `[paper Tab. 2]` | ⚠️ **Table 2 compares two architectures (UFM vs RoMa v2), not `L_NLL` on/off.** There is **no `L_NLL` ablation anywhere in the paper.** Do not attribute the gap to the loss alone. |
| 1.7× faster than RoMa `[paper §4.4]` | Measured at `base` (640², unidirectional, batch 8, H200). Tables 4/11 use a config ~5× more expensive. Also: the **CUDA kernel contributes ~2% of that speedup** — it is a memory optimisation (−14%), not a speed one. |
| Predictive covariance gives +20 AUC@1 `[paper Tab. 12]` | Hypersim only, and it is a **downstream-usage** ablation (post-hoc refinement), **not** an ablation of `L_prec` during training. |
| VKITTI2 enables textureless matching `[paper §3.4]` | A **5-scene dataset at 0.01 sampling weight** credited with a qualitative capability (Fig. 6b). Plausible, **not ablated**. |

## Unverifiable in this pass

| Claim | Why |
|---|---|
| **All four training losses** (Eqs. 1, 2, 4, 5), λ values, EMA decay, two-stage schedule | `[unverified]` — no training code (D-0) |
| Data mixture and weights (Tab. 3) | `[unverified]` — no dataloaders |
| Coarse-matcher training resolutions | `[unverified]` — PDF extraction failure (D-8) |
| Whether RoPE is genuinely restricted to frame-wise attention `[§3.2]` | `[unverified]` — `vit/attention.py`, `vit/rope*.py` not traced line-by-line |
| DPT head internals vs. ref [32] | `[unverified]` — `dpt.py` (516 lines) read structurally only |
| `fused-local-corr` kernel source | `[unverified]` — external package, not vendored |
| Whether `v2.0.1` weights produced the paper's tables | `[unverified]` — commit predates arXiv v3 by ~2.5 months; the shipped benchmark harnesses would settle it |
| Supplementary material (matcher/refiner details, GT warp & overlap construction, SatAst benchmark, covariance experiment setup) | `[unverified]` — repeatedly deferred to a supplement `[paper §3.2, §3.3, §3.4, §4.6, §4.8]` not present in the local PDF |
| Harnesses for Tables 6, 7, 8, 12, 13 | `[unverified]` — only `mega1500`, `scannet1500`, `wxbs`, `satast` ship `[repo: src/romav2/benchmarks/]` |
