# §11 — Specification-vs-implementation gaps for the combined method

## 11.0 Why this file cannot be a paper-vs-repo table, and what it is instead

For each of the nine reference methods, `11-paper-vs-repo-disagreements.md` compares a
**published paper** against a **released repository** at a named commit. The combined method
has neither in scope:

- **There is no paper.** The method is unpublished.
- **The implementation is out of scope.** The two folders that would contain it —
  `seasplat-efficiency-adaptation/` and `seasplat-efficient-3dgs-underwater/` — were excluded
  from this pass by the task brief and are neither read nor cited anywhere in this folder.
  Whatever they contain, this document is not entitled to speak about it.

So the honest form of this section is a **specification-vs-implementation risk table**: for a
method whose specification is `01`–`10` of this folder, which claims are most likely to
diverge from any implementation of it, and which inherited disagreements become *this
method's own* the moment it is written up as a paper.

**This is the section to revisit first** once the implementation is in scope. Every row below
is a checkable question, not an assertion.

---

## 11.1 Inherited disagreements that become **this method's** disagreements on publication

A disagreement in a source becomes a disagreement in the derived work whenever the derived
work's *paper* would restate the source's *paper* while its *code* inherits the source's
*code*. These are the ones where that applies.

| # | If the write-up says… | …the implementation will actually do | Because | Severity |
|---|---|---|---|---|
| **P-1** | "the objective is the sum of seven terms" (SeaSplat Eq. 10) | apply **six distinct λ spanning 200×** (0.01 → 2.0) | inherited SeaSplat D-1 | **high** — a reader reproducing from the equation gets a different objective |
| **P-2** | "we use SeaSplat's medium model with `β^D`, `β^B`, `B^∞`" | additionally train a **fourth parameter, `learned_bg`**, with its own Adam optimizer, and **copy it into `B^∞`** at the SeaThru transition | inherited SeaSplat D-7; `learned_bg` appears **nowhere** in SeaSplat's paper | **high** — and it is load-bearing against degeneracy D-1 |
| **P-3** | "trained for 30 000 iterations" | perform **≈43 000** optimizer steps, plus CD-6's re-warm-up bursts | inherited SeaSplat D-8 | **high** — invalidates any wall-clock or step-count comparison |
| **P-4** | "we apply EDGS's initialization" | run **EDGS v1** — §3.5's SH initialization does not exist | inherited EDGS D-1. ⚠️ **but see §11.2 G-1: it is inert here** | **low here, high in general** |
| **P-5** | "EDGS improves quality without modifying the optimization algorithm" | additionally apply a **×0.99 opacity decay every 10 steps** (Σ logit ≈ −15), a **halved `opacity_lr`**, and a **clamped LR schedule** | inherited EDGS D-3, D-4 — all undocumented and all default-on | **high** — the claim is false as stated, for the *schedule* |
| **P-6** | "we apply Mini-Splatting's simplification" | inherit `sampling_factor = 0.5` and a CDF threshold of `0.99`, **neither of which is in Mini-Splatting's paper** | inherited Mini-Splatting D-4 | **medium** — mitigated here by CD-5's explicit budget |
| **P-7** | "Mini-Splatting's density control" | **not call `reset_opacity()` at all** — 3DGS's core anti-floater mechanism is silently removed | inherited Mini-Splatting D-1. ⚠️ **overridden here by CD-3** | **high if CD-3 is not implemented** |
| **P-8** | "we apply CompGS-VQ's quantization, storing a codebook and one index per Gaussian" | store indices with **no sorting and no run-length encoding** — one of the two storage mechanisms described in CompGS-VQ's abstract and §3 | inherited CompGS-VQ D-1 | **medium** — the achievable compression is below the published figure before any baseline difference |
| **P-9** | "K-means with `t = 100` and 1 iteration, codebook size 16384/32768 from iteration 20 000" | whatever `run.sh` does: `st_iter = 15 000`, `kmeans_iters = 10`, `ncls = 4096`, plus an undocumented **two-stage `--start_checkpoint` workflow** | inherited CompGS-VQ D-2 | **high for reproduction** — the shipped script is not the paper's configuration |
| **P-10** | "metrics are PSNR, SSIM, LPIPS on held-out frames" | compute PSNR as the **mean of per-channel PSNRs**, on **8-bit files re-read from disk**, with **VGG**-LPIPS, on a test set that is **empty** unless `--eval` was passed | inherited SeaSplat D-13, D-14, D-17 | **high** — three independent comparability defects in one sentence |
| **P-11** | "we ablate each mechanism" | be unable to disable ~12 boolean flags from the CLI, because they default `True` and are registered `action="store_true"` | inherited SeaSplat D-12. ⚠️ **addressed by CD-1** | **high if CD-1 is not implemented** |
| **P-12** | "edge-aware depth smoothness following Godard et al." | use the **signed** image gradient `e^{−∂I}`, not `e^{−\|∂I\|}` — inverting the intended behaviour on half of all edges | inherited SeaSplat S-1, a deviation **paper and repo share** | **medium** — deliberately unfixed (CD-14 rationale); must be stated, not cited to Godard |

> **P-2, P-5 and P-7 are the three that a reviewer could catch by reading the source
> repositories.** All three are cases where a source *paper* omits a mechanism its *code*
> depends on. A derived work that cites the paper inherits the omission and, unlike the
> original, has no excuse — the deltas are documented in this evidence base.

---

## 11.2 Gaps that the composition **closes**

Worth stating, because a table of only problems misrepresents the situation.

| # | Gap in a source | Status here |
|---|---|---|
| **G-1** | EDGS's highest-severity delta — §3.5's SH initialization (Eqs. 12–13) is unimplemented, `f_rest ← 0`, and "Table 6's `SH Init.` row is not reproducible" `[../EDGS/11-…​ D-1]` | ✅ **INERT.** `sh_degree = 0` means `f_rest` has shape `(N,0,3)` and does not exist `[../seasplat/03-variables.md]`. The code path that is missing has nothing to act on. `[inferred]` |
| **G-2** | CompGS-VQ's `--opacity_reg` defaults `False`, so its count-reduction machinery is off unless requested `[../compact3d/11-…​ D-6]` | ✅ **Convenient.** CD-8 wants it off; the default already is. What must be asserted is that nobody turns it on. |
| **G-3** | Mini-Splatting's `ms_c` compression pipeline hides an undocumented voxel dedup that drops colliding Gaussians, folding primitive removal into the reported file size `[../mini-splatting/11-…​ D-10]` | ✅ **Not used.** M3 is CompGS-VQ, not RAHT. Stated explicitly so nobody cites `ms_c`'s rate figures as this work's. |
| **G-4** | EDGS's `psnr()` is written for `(3,H,W)` but called with `(1,3,H,W)`, silently switching convention `[../EDGS/11-…​ D-13]` | ✅ **Not used.** SeaSplat's harness is used throughout — which has its own convention problem (P-10), but only one. |
| **G-5** | Mini-Splatting's `ms_d/` sampling uses `replace=True` + `np.unique`, yielding fewer points than requested `[../mini-splatting/11-…​ D-9]` | ✅ **Not used.** `ms/` is the variant. |
| **G-6** | CompGS-VQ's index bit-width bug, `ceil(log2(N))` instead of `ceil(log2(K_cb))`, inflating storage ~1.7× `[../compact3d/11-…​ D-4]` | ✅ **Fixed** by CD-11 — at the cost that the reported size is no longer directly comparable to CompGS-VQ's published `Mem` column. |

---

## 11.3 Where the specification is most likely to diverge from any implementation

These are the `[proposed integration]` decisions of `06-implementation-deltas.md` §6.5,
ranked by how easy each is to get wrong or to skip silently. **They are the specification's
own risk register.**

| Rank | `[PI]` decision | Failure mode if skipped or mis-implemented | How to detect it |
|---|---|---|---|
| **1** | **CD-6** — medium-only re-warm-up after each simplification event | The medium parameters remain fitted to a depth field that has been rescaled; `β` silently absorbs the scale change (SeaSplat degeneracy D-2, injected). Quality drops in A2/A4/A6/A7 for a reason that looks like "pruning hurts" but is actually an identifiability failure | Table 8.3c column 1: `Ẑ_min`/`Ẑ_max` before → after; column 2: `β` at 15 K vs 20 K vs 30 K. **A large `β` jump at the simplification boundary is the signature** |
| **2** | ~~**CD-5** — explicit primitive budget from A0's converged count~~ **REVISED by CD-25: fixed pre-campaign by the binding rule.** The original source would have realised the risk rather than avoided it — A0's median is 2 482 200 and every M1 cloud is under 500 000 | The budget does not bind under M1, so **A4 ≡ A1 and A7 ≡ A5**. A "no interaction detected" result would be an artifact of configuration, not a finding | Checklist item 15 of `10-reproducibility.md`: report whether the budget bound. A realised `N_rend` equal to the pre-prune count is the tell |
| **3** | **CD-8** — disable CompGS-VQ's ℓ1 opacity regulariser | M2 and M3 stop being independent factors; A6 and A7 double-prune; the M3 main effect is contaminated with a count reduction | Compare `N_rend` in A3 against A0. If they differ, the regulariser fired |
| **4** | **CD-1** — a config layer above SeaSplat's argument parser | The matrix cannot be run without editing source between cells, which is unreproducible and untraceable | The per-run resolved-config dump is the artifact. If it is absent, so is the guarantee |
| **5** | **CD-3** — retain `reset_opacity()` under M2 | Water-column floaters lose one of their two suppressors while `L_op` is simultaneously being perturbed by M1's decay. Interacts with the highest-risk shared variable (IC-1) | A floater-ratio diagnostic on the water column, in the style UW-3DGS reports `[unverified — Phase 0 web fetch]` |
| **6** | **CD-9 / CD-11** — three codebooks; corrected index bit-width | Compression figures become non-comparable in two directions at once, and the 4.2× per-Gaussian baseline difference is easy to forget | Report per-Gaussian float count alongside every compression ratio (`08-…​` §8.2) |
| **7** | **CD-2** — `K_ref = min(num_refs, V)` | Pose k-means asked for 180 clusters from 18–29 points. Behaviour is undefined-ish rather than wrong, but the operating point is far off EDGS's measured saturation curve | Log `K_ref` and `V` per scene |
| **8** | **CD-7** — LR precedence between M1's clamp and M2's rewind | Under A4/A7 one schedule silently wins; which one is an implementation accident rather than a decision | Log the effective LR per iteration for a single run per cell |
| **9** | **CD-13** — one CUDA extension serving both depth-override and importance outputs | The build succeeds but one of the two tensor sets is wrong, and nothing crashes | Unit-check `out_pts`/`Z_raw` agreement on a synthetic scene before the matrix is run |
| **10** | **CD-4** — scope M2 to simplification only | The write-up says "Mini-Splatting" and the reader assumes the full method including depth reinitialization | Naming discipline: call it *Mini-Splatting's simplification stage* throughout |

---

## 11.4 Unverifiable in this pass

| Claim | Why it is unverifiable here |
|---|---|
| Anything about an existing implementation of the combined method | the two candidate folders are **excluded by the task brief**; see `open-questions.md` OQ-1 |
| Whether any combined-method run has ever been executed, and with what result | **no results were found** anywhere in scope (Phase 0, `08-computational-profile.md` §8.0) |
| SeaSplat's GPU for its Table II | the paper says only "a consistent set of hardware" `[../seasplat/11-…​, "Unverifiable"]` `[unverified]` |
| SeaSplat's Gaussian count and model size | never reported; only logged to TensorBoard `[../seasplat/08-…​ §8.4]` `[unverified]` |
| CompGS-VQ's K-means initialisation scheme and whether it is seeded | `[../compact3d/11-…​, "Unverifiable"]` `[unverified]` — bears directly on run-to-run variance of the reported model size |
| EDGS Table 6's checkmark pattern and hence its ablation direction | glyphs survive neither `pdftotext -layout` nor `-raw` `[../EDGS/11-…​ D-14]` `[unverified]` |
| Whether SeaThru-NeRF's published numbers used the same PSNR convention as SeaSplat's Table I | ⚠️ **resolved in the negative** by `../seathru_NeRF/10-…​ §10.3a` — they did **not**; the comparison favours SeaSplat. Recorded here because SeaSplat's own folder left it open |
| UW-3DGS's and TUGS's reported figures | from Phase 0 web fetches of arXiv HTML, **not** from local PDFs `[unverified]` — see `open-questions.md` OQ-6 |
