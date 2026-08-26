# §6 — Implementation deltas from the paper

**Repo state inspected:** `github.com/UCDvision/compact3d`, commit
`dccc07e3ab05f65246be25f0ee416aa9a127b54e`, branch `main`, 2024-09-25. No tags.

**Paper inspected:** `../../compact3d.pdf` = arXiv:2311.18159**v3**, 26 Sep 2024 (ECCV 2024)
— **one day after the commit**, i.e. paper and code are essentially contemporaneous. Version
drift is therefore an unlikely explanation for anything below.

**Files read directly:** `train_kmeans.py`, `kmeans_quantize.py`, `run.sh`, `README.md`,
`decompress_to_ply.py` (partial). `gaussian_model.py` not read in depth.

> ⚠️ **Important context:** the repo README documents **post-paper updates**, notably
> "**[31 July 2024]: Added code for opacity regularization**". So `run.sh` reflects a
> *later* recipe than the one behind Table 1. Several deltas below follow from that.

---

## D-1 — ⭐ **Run-length encoding of sorted indices is not implemented**

`[paper §3]` describes it as one of two storage mechanisms:

> "3DGS models the scene as a set of **order-less** Gaussians. Hence, we **sort the Gaussians
> based on one of the indices**, e.g., rotation, so that Gaussians using the same code appear
> together in the list. Then, for that index, instead of storing `n` integers, we store **how
> many times each code appears** in the list, reducing the storage from `n` integers to `k`
> integers. This is **similar to run-length-encoding** for data compression."

It is also in the abstract: "We compress the indices further by **sorting them and using a
method similar to run-length encoding**."

`[repo: train_kmeans.py:254-279]` — `save_kmeans()` does **plain bit-packing**:
```python
bitarray_all = bitarray([])
for kmeans in kmeans_list:
    n_bits = int(np.ceil(np.log2(len(kmeans.cls_ids))))
    assignments = dec2binary(kmeans.cls_ids, n_bits)
    bitarr = bitarray(list(assignments.cpu().numpy().flatten()))
    bitarray_all.extend(bitarr)
```

**No sorting, no run-length counting.** `grep -rn "rle\|RLE\|run_length\|argsort"` over the
repo returns nothing relevant.

**Severity: high.** An abstract-level claim with no implementation. Note the paper's own
Table 6 framing (position/opacity dominate >80% of memory) means RLE's contribution to the
headline ratio would have been modest — but it is claimed, and it is absent.

---

## D-2 — ⭐ `run.sh` is **not** the paper's configuration

| Setting | `[paper §4]` | `[repo: run.sh]` | `[repo: CLI default]` |
|---|---|---|---|
| Quantization start | **20 000** | **15 000** | 30 000 (⇒ off) |
| K-means iterations | **1** | **10** | 1 ✅ |
| Covariance codebook | **16384** (16K) / 32768 (32K) | **4096** | 4096 |
| SH codebook | **4096** | **512** | 4096 |
| DC codebook | 4096 | 4096 ✅ | 4096 ✅ |
| Assignment frequency | 100 | 100 ✅ | 100 ✅ |
| `λ_reg` | 1e-7 | 1e-7 ✅ | 0. |
| Prune window | 15K→20K | 15K→20K ✅ | 15K→20K ✅ |
| Workflow | single run | **two-stage**: requires `--start_checkpoint` from a separate *unquantized* run to 15 000 | — |

Four of the six method-defining constants differ, and the shipped script additionally requires
a **two-stage workflow the paper never mentions** (`ckpt=output/exp_001_noquant/.../chkpnt15000.pth`
`[repo: run.sh]`).

**Severity: high for reproduction.** `bash run.sh` does not reproduce CompGS-16K or 32K.

---

## D-3 — The described **assignment freeze at 25K does not exist**

`[paper §4]`: "We use just 1 such K-means iteration in our experiments **once every 100
iterations till iteration 25K** and **keep the assignments constant thereafter till the last
iteration, 30K**."

`[repo: train_kmeans.py:127-130]`:
```python
if iteration % freq_cls_assn == 1:
    assign = True
else:
    assign = False
```
No upper bound. Reassignment continues every 100 iterations through iteration 30 000.

**Severity: medium.** The final 5 000 iterations were supposed to let the parameters settle
against a *fixed* partition — a stabilisation step that is absent.

---

## D-4 — Index bit-width is derived from the **number of Gaussians**, not the codebook size

`[repo: train_kmeans.py:263]`:
```python
n_bits = int(np.ceil(np.log2(len(kmeans.cls_ids))))
```
and `[repo: kmeans_quantize.py:118]`: `self.cls_ids = self.nn_index` — the **per-Gaussian
assignment vector, length `N`**.

So `n_bits = ceil(log2(N))`. For `N ≈ 1–2 M` that is **20–21 bits per index**, where
`ceil(log2(4096)) = 12` (or 15 for 32K) is what the values actually require.

**Implication:** `kmeans_inds.bin` is roughly **1.7× larger than necessary** for a 4096-entry
codebook. `[inferred — arithmetic from the two lines above; I did not measure a produced file]`

Two mitigating notes: (a) `n_bits` is identical across all four codebooks (it depends only on
`N`), so decoding is at least *self-consistent*; (b) the paper's reported sizes may have been
computed analytically rather than from this file. `[unverified]`

**Severity: medium** — flag it, verify against a produced artifact before quoting file sizes.

---

## D-5 — The opacity-regularization lower bound is **hard-coded**

`[repo: train_kmeans.py:160-161]`:
```python
if iteration > args.max_prune_iter or iteration < 15000:
    lambda_reg = 0.
```
and again at `[repo: train_kmeans.py:221]`: `if args.opacity_reg and iteration > 15000:`.

The **upper** bound is `--max_prune_iter`; the **lower** bound is the literal `15000`. Matches
`[paper §4]` ✅, but cannot be changed without editing the source.

**Severity: low**, relevant if you want to sweep the window.

---

## D-6 — `--kmeans_st_iter` defaults to 30 000, i.e. quantization is **off by default**

`[repo: train_kmeans.py:367-368]`: `default=30000`. Since `--total_iterations` is also 30 000,
the condition `iteration > kmeans_st_iter` never fires. A bare `python train_kmeans.py` trains
plain 3DGS.

Similarly `--lambda_reg` defaults to `0.` and `--opacity_reg` to `False`
`[repo: train_kmeans.py:386-388]`.

**Severity: low**, high trap value — the defaults produce the *baseline*, not the method.

---

## D-7 — No entropy coding of indices

`[repo: train_kmeans.py:261-268]` bit-packs indices uniformly. K-means assignment
distributions are typically far from uniform, so Huffman or arithmetic coding would reduce the
index stream further. The paper does not claim entropy coding — but both successor methods add
it (`../OMG/`: Huffman + LZMA; `../CompGS/` (Liu): a learned entropy model), so it is worth
recording as the state of the art at this point in the lineage. `[inferred]`

**Severity: low** (informational).

---

## D-8 — Naming: paper "CompGS", repo "compact3d", overview text "Compact3D"

`[repo: README.md]` uses all three. Combined with the **distinct** ACM-MM work also called
CompGS (`../CompGS/`), and with `../../CompGS.pdf` being a **byte-identical duplicate** of this
folder's PDF, the naming is a genuine hazard for a literature table.

**Severity: cosmetic**, high confusion value. See
`../CompGS/research-methodology-output/00-index.md`.

---

## ✅ Verified-correct

| Paper claim | Code |
|---|---|
| Quantized forward, non-quantized backward, STE `[§3]` | `forward_*` render on `centers[nn_index]`; gradients update the stored parameters `[kmeans_quantize.py:194, 204]` ✅ |
| Centroids every iteration, assignments every `t` `[§3]` | cheap `update_centers()` vs gated `cdist`+`argmin` `[kmeans_quantize.py:46-61 vs 138-172]`; `iteration % freq == 1` `[train_kmeans.py:127-130]` ✅ |
| `t = 100` `[§4]` | `--kmeans_freq` default 100 ✅ |
| 1 K-means iteration `[§4]` | `--kmeans_iters` default **1** ✅ (though `run.sh` uses 10 — D-2) |
| Four separate codebooks: dc, sh, scale, rot `[§3, §4]` | `--quant_params` default `['sh','dc','scale','rot']` `[train_kmeans.py:381]` ✅ |
| Position and opacity **not** quantized `[§3]` | excluded from the default `quant_params`; `pos` supported only for the Table 9 ablation `[train_kmeans.py:131-132]` ✅ |
| Scale quantized **before `exp`**, rotation **before normalization** `[§4]` | `forward_scale` / `forward_rot` operate on `_scaling` / `_rotation` ✅ |
| DC codebook 4096 `[§4]` | `--kmeans_ncls_dc` default 4096 ✅ |
| ℓ1 opacity regulariser `L = L_3DGS + λ_reg Σα` `[§3]` | `L_reg_op = gaussians.get_opacity.sum()`; `get_opacity = sigmoid(_opacity) ≥ 0` so `.sum()` **is** the ℓ1 norm ✅ |
| `λ_reg = 1e-7`, iterations 15K→20K, prune every 1000 `[§4]` | `[train_kmeans.py:158-166, 220-226]` ✅ exact |
| "no changes in the hyperparameters … compared to 3DGS" `[§4]` | file overlay; `reset_opacity()` still called `[train_kmeans.py:217-218]` ✅ |
| Joint `scale_rot` / `sh_dc` variants (Table 9) | implemented `[train_kmeans.py:141-144]` ✅ |
| BitQ: position 16-bit, opacity 8-bit `[Tab. 1 caption]` | `[unverified]` — not located in this pass |

---

## Items I could *not* verify in this pass

| Claim | Status |
|---|---|
| Table 6's memory breakdown (>80% position+opacity) | `[unverified]` — cells did not survive text extraction; the prose is quoted verbatim |
| Tables 2, 9 numeric values | `[unverified]` — extraction failure |
| Whether reported sizes were computed from `kmeans_inds.bin` or analytically | `[unverified]` — bears directly on D-4 |
| The BitQ post-processing implementation | `[unverified]` — not located |
| `gaussian_model.py` modifications vs upstream 3DGS | `[unverified]` — not diffed |
| K-means initialisation (random? k-means++?) and whether it is seeded | `[unverified]` — see [`10-reproducibility.md`](10-reproducibility.md) |
| DL3DV-10K / ARKit-200 protocols | `[unverified]` — "Details … presented in the Appendix" `[paper §4]` |
| `t = 500` claim | `[unverified]` — asserted in `[paper §3]`, no supporting table |
