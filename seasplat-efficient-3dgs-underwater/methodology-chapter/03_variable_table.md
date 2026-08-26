# §3 — Formal variable table

Merged across SeaSplat and the three efficiency mechanisms. Origin tags:
`[SeaSplat]` `[A1]` `[A2]` `[A3]`.

---

## 3.1 Scene representation (inherited)

| Symbol | Meaning | Shape / type | Origin | Notes |
|---|---|---|---|---|
| `N` | Number of Gaussian primitives | integer | `[SeaSplat]` | ⚠️ **contested** — see §3.5 |
| `μ_i` | Primitive centre (`_xyz`) | `(N,3)` f32 | `[SeaSplat]` | seeded by `[A1]`; **protected** from `[A3]` |
| `Σ_i` | Covariance, factored `Σ = R S Sᵀ Rᵀ` | — | `[SeaSplat]` | never stored directly |
| `s_i` | Scale, stored pre-`exp` (`_scaling`) | `(N,3)` f32 | `[SeaSplat]` | read by `[A2]`, quantized by `[A3]` |
| `q_i` | Rotation quaternion, pre-normalization (`_rotation`) | `(N,4)` f32 | `[SeaSplat]` | quantized by `[A3]` |
| `α_i` | Opacity, stored as logit (`_opacity`); `α = σ(·)` | `(N,1)` f32 | `[SeaSplat]` | ⚠️ **three mechanisms touch it** — §3.5 |
| `c_i` | DC colour (`_features_dc`); `sh_degree = 0` ⇒ no `f_rest` | `(N,3)` f32 | `[SeaSplat]` | shaped by `L_gw`/`L_sat`, quantized by `[A3]` |
| `n_i` | Normals — written to PLY as zeros, unused in rendering | `(N,3)` f32 | `[SeaSplat]` | 3 of the 17 stored floats; see §3.4 |

## 3.2 Underwater image formation (inherited, fixed)

Revised Akkaynak–Treibitz model: `I = J · e^(−β^D · Z) + B^∞ · (1 − e^(−β^B · Z))`

| Symbol | Meaning | Shape | Origin | Notes |
|---|---|---|---|---|
| `I` | Observed underwater image (the GT) | `(3,H,W)` | `[SeaSplat]` | |
| `Ĵ` | Restored / medium-free image | `(3,H,W)` | `[SeaSplat]` | target of `L_gw`, `L_sat` |
| `Î` | Re-rendered underwater image | `(3,H,W)` | `[SeaSplat]` | compared against `I` by `L_GS` |
| `Ẑ` | Rendered depth / range | `(1,H,W)` | `[SeaSplat]` | detached in `L_Z-recon` |
| **`β^D`** | Wavelength-dependent **attenuation** coefficient | **`(3,)`** | `[SeaSplat]` | ⚠️ collision — §9 |
| **`β^B`** | Wavelength-dependent **backscatter** coefficient | **`(3,)`** | `[SeaSplat]` | ⚠️ collision — §9 |
| **`B^∞`** | Veiling light / backscatter at infinite range | **`(3,)`** | `[SeaSplat]` | |

> **Nine scalars total.** `β^D`, `β^B`, `B^∞` are *global per scene*, held in
> `BackscatterNet` / `AttenuateNet` `nn.Module`s with their own optimizers — **not**
> per-primitive attributes. This is the structural reason no efficiency mechanism can corrupt
> them (§5), and it is the property that would **not** hold under a per-ray medium field.

## 3.3 Optimization schedule (inherited)

| Symbol | Value | Origin | Notes |
|---|---|---|---|
| `T` | `iterations = 30 000` | `[SeaSplat]` | identical on all 20 completed runs `[measured]` |
| `T_seathru` | `seathru_from_iter = 10 000` | `[SeaSplat]` | ⚠️ **defaults to `9 000 000`** — must be passed explicitly; confirmed present on all runs `[measured]` |
| `T_dens` | `densify_until_iter = 15 000` | `[SeaSplat]` | gates the block `[A1]` disables; sets `[A2]`'s start |
| `T_reset` | `opacity_reset_interval = 3 000` | `[SeaSplat]` | disabled as a side-effect by `[A1]` |
| `λ_GS, λ_bs, λ_gw, λ_sat, λ_op, λ_Zsmooth, λ_Zrec` | 7 loss weights (§4) | `[SeaSplat]` | **unchanged by all three mechanisms** |

---

## 3.4 Variables introduced by the efficiency mechanisms

### `[A1]` Deterministic initialization

| Symbol | Meaning | Value(s) actually used | Notes |
|---|---|---|---|
| `use_dense_init` | flag (`--no_densify`) | `True` for A1/A1v2 | ⚠️ default `False` — a bare run silently densifies |
| `P_dense` | External seed cloud path (`--pcd_path`) | `dense_<scene>.ply` | ⚠️ unversioned, unhashed |
| `N_init` | Seed primitive count = final `N` | **A1: 222 860 – 368 742**<br/>**A1v2: 888 706 – 1 460 514** `[measured]` | design target was 20 k–80 k `[recommended]` — see §6 |
| `R` | Reference views (`num_refs`) | `−1` = all train views (15–25) | EDGS uses 180 k-means-selected `[paper]` |
| `k_nn` | Neighbours per reference (`nns`) | `3` | matches EDGS `[paper]` |
| `M` | Sampled matches per pair (`matches`) | **A1: 5 000 · A1v2: 20 000** | EDGS: 20 000 `[paper]` |
| `τ_cert` | RoMa certainty threshold | **A1: 0.05 · A1v2: 0.02** | repo default `0.02` |
| `τ_reproj` | Reprojection-error filter | `2.0` px | |
| `v` | Voxel dedup grid | **A1: 0.005 · A1v2: 0.002** | repo default `0.001` |

⚠️ **None of the three shipped `roma_init.py` defaults (`matches=5000`, `certainty=0.02`,
`voxel=0.001`) corresponds to either executed configuration** — the notebooks pass explicit
keyword arguments that override them. See §6.

### `[A2]` Spatial reorganization

| Symbol | Meaning | Value | Notes |
|---|---|---|---|
| `use_spatial_pruning` | flag | always on for A2 | ⚠️ guarded by `hasattr(...)`, which is always `True` — no off switch |
| `N_max` | `max_gaussians` | **`800 000`** | binds on all four scenes `[measured]`: final `N` = exactly 800 000 |
| `Φ_i` | **Importance score** = `α_i · ρ(s_i)` | scalar per primitive | ⭐ **new symbol** — the mechanism's core quantity |
| `ρ` | Scale reduction, selected by `imp_metric` | `outdoor` → `max(s_i)`<br/>`indoor` → `mean(s_i)` | ⚠️ reuses Mini-Splatting's parameter name for unrelated semantics (§9) |
| `Δ` | Reorganization interval | `500` iterations, `iter > 15 000` | 30 events per run |

### `[A3]` Attribute-level quantization

| Symbol | Meaning | Value | Notes |
|---|---|---|---|
| `use_quantization` | flag | offline invocation | ⚠️ `arguments/__init__.py` params are **dead config** (§6) |
| `k` | Codebook size | **`256`** | CompGS uses 4 096–32 768 `[paper]` |
| `g` | Sub-vector group size | **`4`** | inert at `sh_degree = 0` (every attribute is one group) |
| `A` | Quantized attribute set | `{f_dc, f_rest, opacity, scale, rotation}` | ⚠️ CompGS excludes **opacity** `[paper: compact3d §3]` |
| `C_a` | Codebook for attribute `a` | `(k, g)` f32 | |
| `z_a` | Per-primitive index vector | `(N,)` **uint16** | ⚠️ `k = 256` needs 8 bits — 2× waste |
| `quant_xyz` | Position quantization | `False` | ✅ matches CompGS `[paper]` |

---

## 3.5 ⚠️ Variables touched by more than one mechanism

These are the compounding sites — the places where a pairwise or full-stack configuration can
behave unlike the sum of its parts.

| Variable | `[SeaSplat]` | `[A1]` | `[A2]` | `[A3]` | Risk |
|---|---|---|---|---|---|
| **`α_i` (opacity)** | `L_op` (λ=0.01) drives `α → 0` for backscatter-only primitives; `α < 0.005` prune **removes** them; `reset_opacity` every 3 000 | **removes prune *and* reset** (both inside the gated block) | **reads** `α` in `Φ_i` — prunes suppressed primitives first | **quantizes** `α` to 256 centroids | 🔴 **The central compounding site.** Four different mechanisms act on one variable. §5.3 |
| **`N`** | grown by densification | **sets `N_init` and freezes** | **caps at `N_max`** | unchanged | 🔴 A1 makes `N` monotonically non-increasing ⇒ A2 inert below budget ⇒ **A4 ≡ A1, A7 ≡ A5** `[measured]` |
| **`c_i` (`f_dc`)** | shaped by `L_gw` (λ=0.1) and `L_sat` (λ=2.0) on `Ĵ` | seeded from RoMa-sampled source pixels | — | **quantized post-hoc** | 🟡 No gradient step remains to rebalance the aggregate colour statistics the two losses tuned |
| **`s_i` (scale)** | free parameter | — | **read** in `Φ_i` | **quantized** | 🟡 A2 ranks on a quantity A3 later perturbs — but ordering (prune → quantize) means A2 always sees exact values ✅ |
| **`μ_i` (position)** | free parameter | **set from triangulation** | — | **explicitly protected** | 🟢 Coherent: A1 maximizes the count of the one attribute A3 cannot compress (§8) |
| **`β^D, β^B, B^∞`** | 9 global scalars | ❌ | ❌ | ❌ **explicitly protected** | ✅ **Verified untouched by all three** (§5) |

### The opacity chain, stated once

`L_op` suppresses → the α-prune removes → A2 re-ranks on the suppressed value → A3 snaps it to
a centroid. Each link is individually sound. **Removing the second link (A1) while keeping the
fourth (A3) is the one composition with no compensating mechanism** — it is why A5 and A7 carry
the highest predicted correctness risk (§5.4), and why the `L_op` coupling makes A2 the
strongest measured result (§1.3a).

---

## 3.6 Storage layout — 17 float32 per primitive

Confirmed empirically: `model_size_mb / num_gaussians = 6.8 × 10⁻⁵ MB` = **68.0 bytes**,
identical across A0/A1/A1v2/A2 `[measured: all 16 non-A3 rows]`.

| Field | floats | bytes | Quantized by `[A3]`? |
|---|---:|---:|---|
| `μ` (xyz) | 3 | 12 | ❌ protected |
| `n` (normals, all zero) | 3 | 12 | ❌ passthrough |
| `c` (`f_dc`) | 3 | 12 | ✅ |
| `α` (opacity) | 1 | 4 | ✅ ⚠️ |
| `s` (scale) | 3 | 12 | ✅ |
| `q` (rotation) | 4 | 16 | ✅ |
| **Total** | **17** | **68** | |

`f_rest` is absent because `sh_degree = 0`; `quantize.py` correctly skips zero-width
attributes. Measured post-quantization figure is **15.9 bytes/primitive**
(`1.59 × 10⁻⁵ MB`), a **4.28×** reduction `[measured: A3 rows]` — analysed in §8.2.
