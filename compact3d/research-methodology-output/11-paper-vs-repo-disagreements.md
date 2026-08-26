# Paper-vs-repo disagreements — CompGS / Compact3D

**Paper:** `../../compact3d.pdf` = arXiv:2311.18159**v3** (26 Sep 2024), ECCV 2024.
**Repo:** `UCDvision/compact3d` @ **`dccc07e`** (25 Sep 2024) — **one day before** the arXiv
revision, so version drift is an unlikely explanation for anything below.

> **Context:** the README documents post-paper updates, notably *"[31 July 2024]: Added code
> for opacity regularization"*. `run.sh` reflects that later recipe, not the Table 1
> configuration — which accounts for D-2.

| # | Topic | Paper says | Repo does | Tags | Severity |
|---|---|---|---|---|---|
| D-1 | ⭐ **Run-length encoding** | Abstract: "We compress the indices further by **sorting them and using a method similar to run-length encoding**." §3: sort by one index, then store code counts, "reducing the storage from `n` integers to `k` integers" | **`save_kmeans()` does plain bit-packing.** No sorting, no run counts. `grep -rn "rle\|RLE\|run_length\|argsort"` finds nothing relevant | `[paper Abstract, §3]` vs `[repo: train_kmeans.py:254-279]` | **high** |
| D-2 | ⭐ **`run.sh` ≠ the paper's configuration** | §4: quantization starts at **20 000**; **1** K-means iteration; covariance codebook **16384** (16K) / **32768** (32K); SH codebook **4096** | `run.sh`: `st_iter=**15000**`, `kmeans_iters=**10**`, `ncls=**4096**`, `ncls_sh=**512**`; and it requires a **two-stage workflow** (`--start_checkpoint` from a prior unquantized run) that the paper never mentions | `[paper §4]` vs `[repo: run.sh]` | **high** for reproduction |
| D-3 | **Assignment freeze** | §4: assignments updated every 100 iterations "**till iteration 25K**" and then "**keep the assignments constant thereafter till the last iteration, 30K**" | `if iteration % freq_cls_assn == 1: assign = True` — **no upper bound**; reassignment continues to 30 000 | `[paper §4]` vs `[repo: train_kmeans.py:127-130]` | **medium** |
| D-4 | **Index bit-width** | implied `ceil(log2(K))` | `n_bits = ceil(log2(len(kmeans.cls_ids)))`, and `cls_ids = nn_index` — the **per-Gaussian assignment vector of length `N`**. So `n_bits = ceil(log2(N)) ≈ 20` for `N ≈ 10⁶`, where 12 suffices for `K = 4096`. `kmeans_inds.bin` is ~**1.7× larger than necessary** `[inferred]` | `[paper §3]` vs `[repo: train_kmeans.py:263; kmeans_quantize.py:118]` | **medium** |
| D-5 | **Opacity-reg window** | §4: "λ_reg = 10⁻⁷ **from iterations 15K to 20K**" ✅ | matches — but the **lower bound 15000 is hard-coded** in two places; only `--max_prune_iter` is configurable | `[paper §4]` vs `[repo: train_kmeans.py:160-161, 221]` | low |
| D-6 | **CLI defaults disable the method** | — | `--kmeans_st_iter` defaults to **30000** = `--total_iterations`, so `iteration > kmeans_st_iter` never fires; `--lambda_reg` defaults to `0.`; `--opacity_reg` defaults to `False`. A bare run trains **plain 3DGS** | — vs `[repo: train_kmeans.py:367, 386-388]` | low, high trap value |
| D-7 | **No entropy coding of indices** | not claimed | indices are bit-packed uniformly despite a typically non-uniform assignment distribution. Both successors add it (`../OMG/`: Huffman+LZMA; `../CompGS/`: learned entropy model) | — vs `[repo: train_kmeans.py:261-268]` | low (informational) |
| D-8 | **Naming** | paper title: **CompGS** | repo: **compact3d**; overview text: **Compact3D**. And a *different* ACM-MM 2024 work is also called **CompGS** (`../CompGS/`), whose folder held a **byte-identical duplicate** of this PDF until 2026-08-25 | `[paper title]` vs `[repo: README.md]` | cosmetic, high confusion value |

## ✅ Verified-correct — a high hit rate on the method itself

| Paper claim | Code |
|---|---|
| Quantized forward, non-quantized backward, STE `[§3]` | render on `centers[nn_index]`; optimizer holds the unquantized parameters `[kmeans_quantize.py:194, 204]` ✅ |
| Centroids every iteration, assignments every `t` — "crucial in limiting the training time" `[§3]` | cheap `update_centers()` (cached indices) vs the gated `cdist`+`argmin` path `[kmeans_quantize.py:46-61 vs 138-172]` ✅ |
| `t = 100` `[§4]` | `--kmeans_freq` default 100 ✅ |
| **1** K-means iteration `[§4]` | `--kmeans_iters` default **1** ✅ (though `run.sh` overrides to 10 — D-2) |
| Four separate codebooks: dc, sh, scale, rot `[§3, §4]` | `--quant_params` default `['sh','dc','scale','rot']` `[train_kmeans.py:381]` ✅ |
| Position and opacity **not** quantized `[§3]` | excluded from the default; `pos` supported only for the Table 9 ablation `[train_kmeans.py:131-132]` ✅ |
| Scale quantized **before `exp`**, rotation **before normalization** `[§4]` | `forward_scale` / `forward_rot` operate on `_scaling` / `_rotation` ✅ |
| DC codebook 4096 `[§4]` | default 4096 ✅ |
| `L = L_3DGS + λ_reg Σ_i α_i` `[§3]` | `L_reg_op = gaussians.get_opacity.sum()`; `get_opacity = sigmoid(·) ≥ 0`, so `.sum()` **is** the ℓ1 norm ✅ |
| `λ_reg = 1e-7`, prune every 1000 in 15K–20K `[§4]` | `[train_kmeans.py:158-166, 220-226]` ✅ exact |
| "**no changes in the hyperparameters** … compared to 3DGS" `[§4]` | file overlay; `reset_opacity()` still called `[train_kmeans.py:217-218]` — **unlike `../mini-splatting/` and `../OMG/`, which remove it** ✅ |
| Joint `scale_rot` / `sh_dc` variants (Table 9) | implemented `[train_kmeans.py:141-144]` ✅ |
| Training overhead 1.4–1.7× for 32K `[§4]` | consistent with Tab. 1 (1.36× M360, 1.69× T&T) ✅ |

## Claims that need a caveat when cited

| Claim | Caveat |
|---|---|
| "40× to 50× smaller and 2× to 3× faster" `[§1]` | ✅ Accurate for the 32K rows against the **reproduced** 3DGS (778 MB). The **65×** figure is the **BitQ** variant. |
| The 2–3× speedup | ⚠️ Comes from the **opacity regulariser + pruning**, *not* the quantization. The paper says so ("this reduction comes with a bi-product that is increase in inference speed" `[§3]`) but a one-line citation can easily attribute it to VQ. |
| Training cost | ✅ **The paper discloses it plainly** `[§4]`: 1.4–1.7× for 32K. Corroborated externally — `../CompGS/` (Liu) measures this method's **encode time at 68.29 s vs 0.54–2.23 s** for four other compression methods `[CompGS-Liu Tab. 7]`. |
| "works well even for values of `t` as high as 500" `[§3]` | ⚠️ **No supporting table.** Both the paper's experiments and `run.sh` use `t = 100`. `[unverified]` |
| Table 6's ">80% of memory" | ⚠️ §4 separately says "**more than two-thirds**". The two figures differ and neither table's cells survived text extraction `[unverified]`. **The qualitative point — position/opacity dominate after quantization — is the paper's most influential result** and is what drove G-PCC position coding in both successors. |
| Compression ratios | ⚠️ "we **normalize all methods by dividing them by the size of our method**" `[§4]` — ratios are relative to CompGS. Read the `Mem` column directly. |
| `Mem` figures | ⚠️ Verify against a produced `kmeans_inds.bin` — the bit-width bug (D-4) means the on-disk artifact may exceed the reported number. `[unverified]` |
| Table 1 rows | **Variants, not an ablation ladder.** 16K vs 32K differ only in covariance codebook size; BitQ is post-training on top of 32K. |

## ⭐ A methodological contribution worth citing beyond this folder

`[paper §4]` introduces **PSNR-AM** and, uniquely in your nine folders, states *why* averaging
PSNR is problematic:

> "this metric may be **dominated by very accurate reconstructions (smaller errors)** since it
> is based on the **geometric average of the errors due to the log operation** … Hence … we also
> report PSNR-AM, for which we **average the error across all images and scenes before
> calculating the PSNR**."

This is the same Jensen-inequality issue that makes per-channel-mean PSNR differ from
pooled-MSE PSNR across your set. **Cite this passage when justifying whichever convention you
standardise on.**

## Unverifiable in this pass

| Claim | Why |
|---|---|
| Tables 2, 6, 9 numeric values | `[unverified]` — cells did not survive PDF text extraction |
| Whether reported `Mem` came from `kmeans_inds.bin` or an analytic count | `[unverified]` — bears directly on D-4 |
| BitQ implementation (position 16-bit, opacity 8-bit) | `[unverified]` — not located in the repo |
| K-means initialisation scheme, and whether it is seeded | `[unverified]` — bears on run-to-run variance of `Mem` |
| `gaussian_model.py` diff vs upstream 3DGS | `[unverified]` — not diffed |
| The metric harness (`metrics.py`) | `[unverified]` — comes from 3DGS via the overlay, not present in this folder |
| DL3DV-10K / ARKit-200 protocols | `[unverified]` — "Details … presented in the Appendix" `[§4]` |
| Which RTX 6000 (Quadro Turing vs Ada) | `[unverified]` — `[§4]` says only "a single RTX-6000 GPU" |
