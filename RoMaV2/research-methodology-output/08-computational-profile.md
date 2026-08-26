# §8 — Computational profile

## 8.1 As reported

`[paper Tab. 8]` — **"Benchmarking on 640 × 640 images with a batch size of 8 on an H200."**

| Method | Throughput (pairs/s) | Memory (GB) |
|---|---|---|
| UFM | **43.0** | 16.2 |
| RoMa | 18.5 | **4.7** |
| RoMa v2 (w/o CUDA kernel) | 30.3 | 5.6 |
| **RoMa v2 (w/ kernel)** | **30.9** | **4.8** |

† "We use 644 × 644 for RoMa and UFM due to patch size 14" `[paper Tab. 8]` — an honest
adjustment, since RoMa v2's DINOv3 uses patch size 16.

Derived:

| Comparison | Throughput | Memory |
|---|---|---|
| RoMa v2 vs **RoMa** | **1.67× faster** | 1.02× (parity) |
| RoMa v2 vs **UFM** | 0.72× (**1.39× slower**) | **3.4× less** |
| Effect of the CUDA kernel alone | 1.02× | **1.17× less** |

**The CUDA kernel is a memory optimisation, not a speed one** (+2% throughput, −14% memory).
The 1.67× speedup over RoMa comes from elsewhere — principally the stride-4 DPT head, which
cuts the refiner count from RoMa's 5 (stride 14) to **3** (strides 4/2/1) `[paper §3.3]`.
`[inferred]`

The paper's framing is accurate on both sides: "we improve the throughput significantly
compared to RoMa, running 1.7× faster. Compared to UFM our model is **slightly slower**,
however with a **much smaller memory footprint**" `[paper §4.4]`.

## 8.2 Hardware — **NVIDIA H200**, and this is the most transferable number in your set

| Aspect | Assessment |
|---|---|
| **Device** | **H200** — named explicitly `[paper Tab. 8]`. Hopper, same architecture as your H100, with more/faster HBM. |
| **vs your H100 96 GB** | ✅ **The closest hardware match anywhere in this comparison set.** Same SM 9.0 generation. Expect throughput within ~10–20% and memory figures to transfer essentially unchanged. Contrast `../seasplat/` (unnamed, consumer-class), `../CompGS/` (unnamed), `../mini-splatting/` (RTX 3090), `../seathru_NeRF/` and `../EDGS/` (A100). |
| **Memory headroom** | 4.8 GB at batch 8 / 640² ⇒ you can raise batch size or resolution substantially on 96 GB. |
| **Software stack** | Python ≥ 3.10 (tested 3.12), current torch/torchvision `[repo: pyproject.toml; README.md]`. Installed with `uv`. **The most modern stack in the set**, alongside `../CompGS/` and `../EDGS/`. |
| ⚠️ **`fused-local-corr` is Linux-only** | `"fused-local-corr ; sys_platform == 'linux'"` `[repo: pyproject.toml]`, imported in a `try/except` `[repo: local_correlation.py:4-7]`. On your Windows workstation you silently get the **5.6 GB / 30.3 pairs-per-second** path; on a Linux cluster you get 4.8 GB / 30.9. Same results either way — only the memory differs. |
| ⚠️ **`float32_matmul_precision` must be `"highest"`** | a hard `RuntimeError` `[repo: romav2.py:169-170]`. This disables TF32 for the whole process, which will slow down anything else running alongside it — relevant if you embed the matcher in a 3DGS training run. |

## 8.3 Resolution is the real cost knob

`[repo: src/romav2/romav2.py:119-160]` — the same checkpoint spans a wide cost range:

| Setting | Coarse | Fine | Bidirectional | Relative cost `[inferred]` |
|---|---|---|---|---|
| `turbo` | 320² | — | ❌ | **~1×** (baseline) |
| `fast` | 512² | — | ❌ | ~2.5× |
| `base` | 640² | — | ❌ | ~4× ← Tables 6, 7 |
| `mega1500` etc. | 800² | 1024² | ✅ | ~20× ← Table 4 |
| `precise` (default) | 800² | 1280² | ✅ | ~28× |

`[inferred: scaling as H·W for the coarse stage, plus a second refinement pass at the fine
resolution, doubled for bidirectional; not measured]`

**Table 8's throughput figure is for `base` (640², unidirectional).** The benchmark results
of Table 4 use a configuration roughly **5× more expensive**. Do not pair the two numbers.

## 8.4 Accuracy, for the record

`[paper Tab. 4]` — relative pose, AUC@5/10/20:

| Method | MegaDepth-1500 | ScanNet-1500 |
|---|---|---|
| MASt3R | 42.4 / 61.5 / 76.9 | 33.6 / 56.8 / 74.1 |
| VGGT | 33.5 / 52.9 / 70.0 | 33.9 / 55.2 / 73.4 |
| LoFTR | 52.8 / 69.2 / 81.2 | 22.1 / 40.8 / 57.6 |
| DKM | 60.4 / 74.9 / 85.1 | 29.4 / 50.7 / 68.3 |
| **RoMa** | 62.6 / 76.7 / 86.3 | 31.8 / 53.4 / 70.9 |
| UFM | 41.5 / 57.9 / 72.4 | 31.3 / 54.1 / 72.0 |
| **RoMa v2** | **62.8 / 77.0 / 86.6** | **33.6 / 56.2 / 73.8** |

⚠️ **On MegaDepth-1500 the margin over RoMa v1 is 0.2–0.3 AUC** — essentially a tie. RoMa v2's
gains are elsewhere:

`[paper Tab. 6, 7]` — dense matching at 640², EPE (lower better) and PCK@1px:

| Dataset | RoMa | UFM | **RoMa v2** | v2 vs v1 |
|---|---|---|---|---|
| TA-WB | 60.61 / 35.1 | 15.85 / 31.3 | **13.82 / 67.7** | **−77% EPE** |
| MegaDepth | 2.34 / 74.8 | 3.15 / 55.3 | **1.47 / 79.6** | −37% EPE |
| ScanNet++ v2 | 27.52 / 20.2 | 6.93 / 31.4 | **4.00 / 45.5** | **−85% EPE** |
| FlyingThings3D | 5.68 / 78.0 | 1.33 / 83.4 | **0.93 / 89.4** | **−84% EPE** |
| AerialMegaDepth | 25.05 / 39.0 | 17.44 / 29.3 | **4.12 / 55.9** | **−84% EPE** |
| MapFree | 8.55 / 45.8 | 3.59 / 31.6 | **2.03 / 55.4** | −76% EPE |

**RoMa v2 wins every one of the 6 dense-matching datasets on every metric** — a much stronger
result than the pose tables. And `[paper Tab. 11]`:

| Benchmark | RoMa | UFM | RoMa v2 |
|---|---|---|---|
| WxBS (mAA@10px) | **60.8** | 42.3 | 55.4 ⚠️ |
| SatAst (AUC@10px) | 23.5 | 1.8 | **37.0** |
| RUBIK (Success %) | 47.3 | 53.1 | **57.3** |

⚠️ **WxBS is the one loss**, conceded in §5 and traced to the IR-to-RGB subset in §4.5.
**For cross-modal matching, `../RoMa/` v1 is still the better model.**

## 8.5 ⭐ What this means for `../EDGS/`

This is the actionable part of this section. EDGS uses **RoMa v1** for all of its geometry
`[EDGS repo: source/corr_init.py:17, 533-537]` and ablates the matcher in its Table 5:

| Matcher in EDGS | PSNR | SSIM | LPIPS |
|---|---|---|---|
| RAFT | 26.90 | 0.803 | 0.201 |
| LoFTR | 27.79 | 0.818 | 0.179 |
| DKM | 27.81 | 0.831 | 0.192 |
| **RoMa (v1)** | **28.02** | **0.839** | **0.141** |

Reasons to expect RoMa v2 to improve on this, and reasons for caution:

**For:**
- **1.67× faster** at matched settings, and EDGS runs `num_refs × nns_per_ref = 540` pairs
  per scene `[EDGS repo: configs/train.yaml]` — initialization time drops materially.
- **EPE improvements of 37–85%** across all six dense benchmarks (§8.4). EDGS's triangulation
  quality is bounded by warp accuracy, and its `p^proj` filter discards high-reprojection-error
  matches `[EDGS paper Eq. 10]` — better warps mean fewer discards, i.e. **denser usable
  initialization**.
- EDGS explicitly disables two RoMa v1 features for speed —
  `upsample_preds = False`, `symmetric = False` `[EDGS repo: source/corr_init.py:538-539]`.
  RoMa v2's **stride-4 native output** (vs v1's stride 14) means less is lost by skipping
  upsampling.
- v2's **bidirectional** mode is native, which is closer to what EDGS approximates by matching
  each reference against `J = 3` neighbours.

**Against / to watch:**
- **API is not drop-in.** `from romav2 import RoMaV2` with a `Setting` enum, versus v1's
  `roma_outdoor()` / `roma_indoor()`. EDGS calls `roma_model.match()`, `.sample()`,
  `.to_pixel_coordinates()`, and reaches into `roma_model.sample_thresh`,
  `.w_resized/.h_resized`, `.upsample_preds`, `.symmetric`, `.attenuate_cert`
  `[EDGS repo: source/corr_init.py:137-177, 541]`. **Several of those attributes do not exist
  in v2** — this is a real porting job, not a one-line swap. `[inferred from comparing the two APIs]`
- **`τ_corr` changes meaning.** EDGS sets `upper_thresh = roma_model.sample_thresh`
  `[EDGS repo: source/corr_init.py:541]` — v2's confidence calibration differs, so the
  operating point shifts silently.
- **`float32_matmul_precision = "highest"`** is enforced process-wide
  `[repo: romav2.py:169-170]`, which would disable TF32 for the 3DGS training that follows in
  the same process.
- **No indoor/outdoor variants** in v2 — a single checkpoint replaces v1's two.
- If any of your scenes are **cross-modal**, v1's WxBS advantage applies.

**Suggested experiment:** re-run EDGS's Table 5 protocol with RoMa v2 as a fifth row, holding
`init_wC` fixed. That is a small, self-contained, publishable delta and it uses two folders of
your set together.
