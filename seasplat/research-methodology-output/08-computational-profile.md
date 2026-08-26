# §8 — Computational profile

## 8.1 As reported

`[paper Tab. II]`, "averaged across training and evaluation on the SeaThru-NeRF datasets"
`[paper §V.B]`:

| Method | Train time | Render time | VRAM |
|---|---|---|---|
| **SeaSplat (ours)** | **1 h 25 m** | **0.012 s** (≈ 83 FPS) | **4.0 GB** |
| SeaThru-NeRF (Levy et al. [28]) | 21 h | 10.184 s (≈ 0.098 FPS) | 33.2 GB |
| 3DGS (Kerbl et al. [11]) | 40 m | 0.006 s (≈ 167 FPS) | 3.8 GB |

Derived overheads vs. the 3DGS base:

| Quantity | Ratio | Note |
|---|---|---|
| Train time | **2.13×** | 40 m → 1 h 25 m |
| Render time | **2.00×** | 0.006 s → 0.012 s |
| VRAM | **1.05×** | 3.8 → 4.0 GB |
| vs. SeaThru-NeRF train | **14.8× faster** | |
| vs. SeaThru-NeRF render | **849× faster** | |
| vs. SeaThru-NeRF VRAM | **8.3× smaller** | |

The paper attributes the 2× render cost correctly: "The increase in rendering time can
largely be attributed to a second rendering pass required to obtain depth" `[paper §V.B]`
— confirmed at `[repo: train.py:220; gaussian_renderer/__init__.py:109-137]`, where
`render_depth` is a full second rasterization with `override_color = z_cam`.

## 8.2 Hardware — **not comparable to an H100 96 GB, and not stated**

**The paper never names a GPU.** The only statement is "a consistent set of hardware"
`[paper §V.A.c]`. That is the whole of it. Every number in §8.1 is therefore
`[unverified]` with respect to device.

Circumstantial evidence from the repo:

| Evidence | Reading |
|---|---|
| `ARG CUDA_ARCHITECTURES=89;86` `[repo: Dockerfile:15]` | Builds only for **SM 8.6 (Ampere, RTX 30xx / A10 / A40)** and **SM 8.9 (Ada, RTX 40xx / L40)** |
| `ARG TORCH_CUDA_ARCH_LIST="8.6;8.9+PTX"` `[repo: Dockerfile:16]` | same |
| The line including `9.0` is **commented out** `[repo: Dockerfile:13-14]` | **SM 9.0 = Hopper = H100 was explicitly excluded** from the build |
| `CUDA_VERSION=11.8.0`, `torch==2.1.0+cu121` `[repo: Dockerfile:1; README.md]` | 2023-era stack |

**Conclusion for your cluster:** the container as shipped **will not run on an H100**
without adding `90` to `CUDA_ARCHITECTURES` and rebuilding the two CUDA submodules
(`diff-gaussian-rasterization`, `simple-knn`). More importantly, the 4.0 GB VRAM and
1 h 25 m figures were almost certainly measured on a consumer Ampere/Ada card, so:

- **VRAM (4.0 GB) transfers directly** — it is an absolute footprint, and an H100 96 GB
  has ~24× headroom. Not a constraint for you.
- **Train time (1 h 25 m) does not transfer.** Expect it to shrink on H100, but 3DGS
  rasterization is memory-bandwidth- and atomics-bound rather than tensor-core-bound, so
  the speedup will be well short of the raw FLOP ratio. `[unverified — not measured here]`
- **Render time (0.012 s) does not transfer** for the same reason.

**Any comparison you publish should either re-measure all three methods on the H100 or
state that Table II is reproduced as-published on unspecified hardware.** Mixing the two
is the single most likely source of an unfair comparison in this project.

## 8.3 What the reported wall-clock omits

Per delta D-8 ([`06-implementation-deltas.md`](06-implementation-deltas.md)), the
`continue` statements at `[repo: train.py:453, 463]` bypass `iteration += 1` at
`[repo: train.py:567]`. At defaults (`seathru_from_iter=10 000`, `iterations=30 000`,
`update_bs_at_interval=100`, `update_bs_at_count=50`) the run performs:

```
30 000  outer Gaussian steps
+ 1 000  medium warm-up steps          (one-off, at the SeaThru transition)
+ 2 000  colour-adjustment steps       (one-off)
+ 50 × (20 000 / 100) = 10 000  medium burst steps
= ≈ 43 000 optimizer steps for a "30 000 iteration" run
```
`[inferred: arithmetic over repo train.py:434-463 with arguments/__init__.py:88,180-181 and README seathru_from_iter=10000]`

Each medium step is cheap relative to a Gaussian step (no densification bookkeeping, but it
*does* re-run both rasterization passes, because the `continue` happens *after* the forward
pass — `[repo: train.py:201-220]` executes on every pass through the loop). So the extra
13 000 passes each pay the **full two-rasterization forward cost**. That is a plausible
mechanical explanation for the 2.13× train-time ratio over 3DGS despite only ~9 extra
learned scalars — and it is a straightforward efficiency target if you were to modify the
method. `[inferred]`

## 8.4 Gaussian / parameter count

| Quantity | Value | Source |
|---|---|---|
| Medium parameters | **9 scalars** (`β^D∈ℝ³`, `β^B∈ℝ³`, `B^∞∈ℝ³`) | `[repo: models.py:54,61,216 with use_bs_residual=False, use_at_v3=True]` |
| Background parameter | 3 scalars (`bg`), folded into `B^∞` at the transition | `[repo: train.py:130,209-212]` |
| Per-Gaussian parameters | **14 floats** (`μ`:3, `f_dc`:3, `o`:1, `s`:3, `q`:4) — because `sh_degree = 0` | `[repo: arguments/__init__.py:49]` |
| Number of Gaussians `N` | **not reported** in the paper; logged to TensorBoard only | `[unverified]` `[repo: train.py:1007]` |
| Model size on disk | **not reported** | `[unverified]` |

> Contrast: upstream 3DGS at `sh_degree=3` stores **59 floats/Gaussian**. SeaSplat's
> zero-order SH already gives a **4.2× per-Gaussian storage reduction** before any of the
> compression methods in your comparison set (`compact3d/`, `CompGS/`, `OMG/`,
> `mini-splatting/`) are applied. When you tabulate compression ratios across folders,
> normalising against a 59-float baseline for those methods and a 14-float baseline for
> SeaSplat is a category error waiting to happen.

## 8.5 Complexity claims — asymptotic vs. empirical

The paper's efficiency claim is:

> "our method does not require densely querying or sampling medium parameters at every
> pixel, instead having a set of global medium parameters." `[paper §V.B]`

Reading this precisely:

| Claim | Type | Verdict |
|---|---|---|
| "adds `O(1)` medium parameters vs. base 3DGS" | **Asymptotic, and true.** 9 scalars independent of `N`, of image resolution, and of the number of views. | ✅ Genuinely asymptotic. The paper does not use the `O(1)` phrasing itself, but the claim is exactly that and it holds by construction. |
| "does not require dense per-pixel medium querying, unlike SeaThru-NeRF" | **Asymptotic in the medium model**: `O(1)` parameter *lookups* vs. `O(H·W·S)` MLP evaluations. | ✅ True as stated — but note the *application* of those 9 parameters is still `O(H·W)` (an elementwise exp over the depth map, `[repo: models.py:232]`). The saving is in model evaluation, not in map construction. |
| "SeaSplat preserves the computational efficiency of 3DGS" `[paper Tab. II caption]` | **Empirical, on unspecified hardware, on 4 scenes.** | ⚠️ 2.13× training and 2.00× rendering are *not* "negligible" — the paper's own phrasing ("not to negligibly affect performance" `[paper §V.B]`) is a double negative that reads as the opposite of what Table II shows. The 2× render cost has an identified structural cause (second rasterization pass), not a hardware-specific one, so it will persist on any device. |
| "significantly lower train time and memory … than other underwater restoration methods" `[paper Tab. II caption]` | **Empirical**, but the 8–850× gaps over SeaThru-NeRF are large enough to be robust to hardware. | ✅ Safe to cite, with the hardware caveat. |

**Bottom line for citation:** the `O(1)`-parameters claim is asymptotic and safe. The
"preserves 3DGS efficiency" claim is empirical, is a 2× regression on both train and
render, and rests on unnamed hardware — cite it with the numbers, not the adjective.
