# §8 — Computational profile

## 8.1 As reported *by this paper*

> "The network is trained for **250,000 iterations** with a **batch size of 16384 rays**,
> taking around **10 hours on an Nvidia A100 GPU**." `[paper §4.5]`

| Quantity | Value | Source |
|---|---|---|
| Training time | **≈ 10 h** | `[paper §4.5]` |
| Hardware | **1 × NVIDIA A100** — *named*, unlike SeaSplat | `[paper §4.5]` |
| Iterations | 250 000 | `[paper §4.5]` = `[repo: configs/llff_256_uw.gin Config.max_steps]` |
| Batch size | 16 384 rays | `[paper §4.5]` = `[repo: configs/llff_256_uw.gin]` |
| Samples/ray | 128 proposal + 32 NeRF (2 levels) | `[repo: configs/llff_256_uw.gin]` |
| Render time / FPS | **not reported** | `[unverified]` |
| VRAM | **not reported** | `[unverified]` |
| Parameter count | **not reported** | `[unverified]` |

Derived: `250 000 × 16 384 ≈ 4.1 × 10⁹` ray-samples-batches; at 160 samples/ray that is
`≈ 6.6 × 10¹¹` MLP sample evaluations for the object branch, plus `4.1 × 10⁹` mediumMLP
evaluations (one per ray, not per sample). `[inferred: arithmetic from the config above]`
The **per-ray** (rather than per-sample) medium evaluation is a real efficiency property of
the design and is worth stating explicitly — see §8.4.

## 8.2 ⚠ SeaSplat reports *different* numbers for this method

`[seasplat paper Tab. II]` attributes to "Levy et al. [28]" (this method):

| Quantity | SeaThru-NeRF's own claim | SeaSplat's measurement of it |
|---|---|---|
| Train time | **≈ 10 h** (A100) | **21 h** (hardware unnamed) |
| Render time | not reported | **10.184 s/frame** |
| VRAM | not reported | **33.2 GB** |

**The train-time figures differ by 2.1×.** Neither is wrong: SeaThru-NeRF measured on an
A100; SeaSplat re-ran the released code on its own, unnamed hardware whose `Dockerfile`
targets SM 8.6/8.9 (consumer Ampere/Ada) `[seasplat repo: Dockerfile:15]`. A consumer card
being ~2× slower than an A100 on a JAX workload is entirely plausible.

**Practical consequence for your comparison:** the 14.8×-faster-training and
849×-faster-rendering claims in SeaSplat's Table II are **SeaSplat-hardware numbers for
both methods**, which is internally consistent and the right way to do it — but they must
not be mixed with the 10 h A100 figure from this paper. Pick one measurement regime and
state it. `[inferred: comparing paper §4.5 with seasplat paper Tab. II]`

## 8.3 Hardware comparability with your H100 96 GB

| Aspect | Assessment |
|---|---|
| **Device class** | A100 (SM 8.0, 40/80 GB) vs H100 (SM 9.0, 96 GB). **The closest match in this whole comparison set** — same datacentre class, one generation apart. Far more transferable than SeaSplat's unnamed consumer card. |
| **A100 variant** | `[unverified]` — the paper does not say 40 GB or 80 GB. Matters, because batch 16 384 at full ≈900×1400 resolution is memory-hungry and the README explicitly warns about OOM (*"You may need to reduce the batch size (Config.batch_size) to avoid out of memory errors"* `[repo: README.md]`). |
| **Software stack** | ⚠️ **This is the real obstacle.** `install.sh` pins `jaxlib-0.4.1+cuda11.cudnn82` `[repo: install.sh]`, i.e. **JAX 0.4.1 on CUDA 11**. H100 requires CUDA 12 for anything beyond basic compatibility mode; `flax==0.6.1`, `chex==0.1.5` and Python 3.9 `[repo: requirements.txt; README.md]` are a late-2022 stack. Expect a non-trivial dependency upgrade before this runs well on H100, and note that upgrading JAX across 0.4.x has historically broken Flax `nn.compact` and `random_split` call sites. |
| **Time estimate on H100** | `[unverified]` — not measured here. The workload is MLP-dominated (dense matmuls), so it should transfer *better* to H100 than 3DGS rasterization does; but the gain will be gated by whether you can get a modern JAX + XLA on it. |

**Recommendation:** if you intend a fair three-way comparison
(SeaThru-NeRF / SeaSplat / 3DGS) on the H100, budget the JAX upgrade as a real work item,
and re-measure all three rather than quoting any published table. The two papers'
published numbers for *this same method* already differ by 2.1×, which is itself the
argument for re-measuring.

## 8.4 Complexity claims — asymptotic vs. empirical

| Claim | Type | Verdict |
|---|---|---|
| The mediumMLP is evaluated **once per ray**, not once per sample | **Asymptotic, and true.** `O(B)` medium evaluations vs `O(B·N)` object evaluations. | ✅ Verified in code: `c_med`, `σ^bs`, `σ^attn` are computed from `dir_enc_for_water_1` (shape `[..., feat]`, no sample axis) and only then broadcast `[repo: models.py:865-890; render.py:184]`. A genuine, structural saving. |
| The medium adds negligible cost vs. mip-NeRF 360 | **Empirical**, and unquantified. | ⚠️ The paper gives no baseline timing to compare against, so the overhead is unmeasured. Given a 1×128 medium trunk against an 8×256 object trunk evaluated 32× more often, the overhead is plausibly a few percent — but that is `[inferred]`, not reported. |
| SeaSplat's "849× faster rendering" | **Empirical**, SeaSplat's hardware, one method's released code vs another's. | ✅ The *magnitude* is robust — implicit MLP ray-marching at 160 samples/ray versus rasterization is an architectural gap of orders of magnitude, not a tuning artifact. The exact factor is not. |
| "Estimation of wideband medium parameters, which are informative properties of the captured environment" `[paper §1]` | **Qualitative capability claim.** | ⚠️ `σ^attn`, `σ^bs` are learned in **inverse-NDC units** (`near = 0, far = 1` `[repo: gin]`), so they are not in inverse metres and no calibration to physical units is described. Treat the recovered coefficients as relative, not absolute. `[inferred; see 05-constraints §5.3]` |

## 8.5 Cost asymmetry against the rest of the comparison set

Order-of-magnitude context for your write-up, all as-published, **different hardware
each** — do not build a table from this without re-measuring:

| Method | Training | Rendering |
|---|---|---|
| SeaThru-NeRF | ≈10 h (A100, own claim) / 21 h (SeaSplat's measurement) | ≈10.2 s/frame (SeaSplat's measurement) |
| SeaSplat | 1 h 25 m (unnamed) | 0.012 s/frame |
| 3DGS | 40 m (unnamed) | 0.006 s/frame |

The ~50–850× rendering gap is the whole reason the underwater-restoration literature moved
from NeRF to 3DGS between 2023 and 2024, and it is the axis along which the rest of your
comparison set (`mini-splatting/`, `CompGS/`, `compact3d/`, `OMG/`, `EDGS/`) pushes further.
