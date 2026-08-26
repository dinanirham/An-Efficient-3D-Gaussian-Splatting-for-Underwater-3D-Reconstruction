# §6 — Implementation deltas from the paper

**Repo state inspected:** `github.com/maincold2/OMG`, commit
`6edeb72d4dbaf34ffe724deb0c1dc0ca3bece0bb`, branch `main`, 2025-03-24. No tags.

**Paper inspected:** `../../OMG.pdf` = arXiv:2503.16924**v2**, 6 Nov 2025 (NeurIPS 2025) —
**~7 months newer** than the commit. 🔶 marks deltas plausibly explained by that gap.

**Files read directly:** `train.py`, `scene/gaussian_model.py`, `arguments/__init__.py`,
`README.md`, plus `git log`.

> **Framing:** OMG's paper is *architecturally* accurate — every equation I could check maps
> onto real code. Its weakness is **under-specification**: the value of essentially every
> constant lives only in the repository. The deltas below are mostly of that kind, plus two
> genuine behavioural surprises (D-1, D-2).

---

## D-1 — ⭐ "K-nearest neighbors" is **exactly two** Morton neighbours

`[paper Eq. 8]`: `I_i = Ī_i · ( (1/D) Σ_{j ∈ N_i^K} ‖T_i − T_j‖₁ )^λ`, "where `N_i^K` denotes
the set of **K-nearest neighbors** of Gaussian `i`".

`[paper §3.3]` discloses the approximation: "As computing exact K-nearest neighbors for every
Gaussian is computationally expensive, we approximate neighbor selection by sorting Gaussians
in **Morton order** and selecting Gaussians with **adjacent indices** as their local neighbors."

`[repo: scene/gaussian_model.py:652-665]`:
```python
order   = self.sort_morton()
order_l = torch.clamp_min(order - 1, 0)
order_r = torch.clamp_max(order + 1, torch.amax(order))
...
res_color = torch.mean(torch.abs(ordered_color[order_l] - ori_color)
                     + torch.abs(ordered_color[order_r] - ori_color), dim=-1)
imp_score = imp_score * res_color ** lambda_ld
```

**`K = 2`** — the immediate predecessor and successor in Morton order. It is not a
hyperparameter, not exposed, and not swept. The paper's `N_i^K` notation implies a tunable
neighbourhood that does not exist.

**Severity: medium.** The approximation *is* disclosed; the cardinality is not, and `K`
appears in the paper's central equation as if it were a free parameter.

---

## D-2 — ⭐ Codebook "fine-tuning" runs at **`lr = 1e-8`** — effectively frozen

`[paper §3.2]`: "we adopt a fine-tuning strategy in the final 1K iterations: after initializing
with K-means, we freeze the indices and **finetune only the codebook using the rendering
loss**."

`[repo: scene/gaussian_model.py:818]`:
```python
self.optimizer_code = torch.optim.Adam(code_params, lr=1e-8, eps=1e-15)
```
stepped for the final 1000 iterations `[repo: train.py:191-192]`.

Adam's step magnitude is ≈ `lr`, so each codeword moves ~**1e-5** in total. Against attribute
values of order 1e-1–1e0, that is **no meaningful optimization** — the codebook is essentially
frozen at its K-means initialisation.

The result is not *wrong* (SVQ costs ≤0.05 dB `[paper Tab. 4]`, so K-means alone suffices, and
this is consistent with the paper's own remark that "as training converges, the selected
codebook indices remain largely unchanged"), but the described mechanism is not the operative
one.

**Severity: medium** 🔶 — possibly a leftover from a tuning sweep.

---

## D-3 — `slice_scale = 1`: the scale attribute is **not** sub-vector quantized

`[paper §3.2]`: "We apply SVQ to **geometric attributes `s_n`, `r_n`**, resulting in quantized
vectors `ŝ_n`, `r̂_n`."

`[repo: arguments/__init__.py:100-105]`:
```python
self.slice_scale   = 1        # → 1 sub-vector of length 3  ⇒ plain VQ
self.cluster_scale = 2**6     # 64 codewords
self.slice_rot     = 2        # → 2 sub-vectors of length 2
self.cluster_rot   = 2**9     # 512 each
self.slice_app     = 2        # → 2 sub-vectors of length 3
self.cluster_app   = 2**10    # 1024 each
```

With `M = 1` there is no partitioning — scale gets one 64-entry codebook over the whole
3-vector, i.e. **ordinary vector quantization**. Only rotation and appearance are genuinely
sub-vector quantized.

**Severity: low–medium**, and worth stating precisely if you cite SVQ as applied uniformly.

---

## D-4 — Essentially every constant is repo-only

| Quantity | Paper | Repo |
|---|---|---|
| `λ` (LD exponent) | ❌ symbol only, no value | **`2.0`** `[arguments/__init__.py:99]` |
| `D` (feature dim) | ❌ "where `D` is the dimensionality" | **`3`** `[gaussian_model.py:724-725]` |
| Space-feature dim | ❌ | **`13`** `[gaussian_model.py:674]` |
| Positional-encoding frequencies | ❌ "positional encoding" | **`16`** `[gaussian_model.py:677]` |
| MLP width / hidden layers | ❌ "tiny MLP" | **`64` / `1`**, all four MLPs `[gaussian_model.py:672-720]` |
| MLP activations | ❌ | ReLU (`mlp_cont`), LeakyReLU (other three) |
| MLP optimizer | ❌ | Adam `lr = 0.01` + `LinearLR(100)` ⊕ `MultiStepLR([1000,3500,6000], γ=0.33)` `[gaussian_model.py:737-751]` |
| `net_itr` (when the field is created) | ❌ | **`15 000`** `[arguments/__init__.py:97]` |
| SVQ `M`, `B` per attribute | ❌ | see D-3 |
| Codebook optimizer | ❌ | Adam `lr = 1e-8` (D-2) |
| K-means settings | ❌ | cuML, `max_iter=1000`, `n_init=1` `[gaussian_model.py:846]` |

`[paper §4.1]` says "Further implementation details are provided in the supplementary
materials", which is not in the local PDF `[unverified]` — so some of these may be documented
there.

**Severity: high for reproduction from the paper alone**, low for correctness.

---

## D-5 — The Mini-Splatting inheritance is total, and its undocumented mechanisms come along

`[repo: arguments/__init__.py:89-95]` reproduces Mini-Splatting's parameter block verbatim, and
`[repo: scene/gaussian_model.py:627-650]` is its `intersection_preserving` line-for-line.

That means OMG silently inherits every delta documented in
`../mini-splatting/research-methodology-output/11-paper-vs-repo-disagreements.md`, notably:

- **`reset_opacity()` is never called** — 3DGS's opacity reset remains removed.
- **Depth-reinit pixel sampling is `(1 − α_accum)`-weighted**, not uniform.
- **The LR schedule is rewound** at `simp_iteration1`:
  `update_learning_rate(iteration − simp_iteration1 + 5000)` `[repo: train.py:73-77]`.
- `num_max = 4.5 M` cap; `sampling_factor = 0.5`.

The OMG paper mentions none of these, and cites Mini-Splatting only for the "blur split
technique" `[paper §4.2]`.

**Severity: medium** — a reader benchmarking OMG against 3DGS is benchmarking against
Mini-Splatting-plus-OMG, with two layers of undocumented behaviour.

---

## D-6 — `res_color` compares a **learned latent**, not colour

`[repo: gaussian_model.py:657-663]`:
```python
if not self.net_enabled:
    ori_color, ordered_color = self._features_dc[:,0], self._features_dc[order,0]
else:
    ori_color, ordered_color = self._features_static, self._features_static[order]
```

Since `net_itr = 15 000 < simp_iteration2 = 20 000`, the **`T` branch is always the one that
runs** at pruning time. `T` is initialised from DC colour but then trained
`[repo: gaussian_model.py:724]`, so by iteration 20 000 it is a learned 3-D latent whose
relation to perceived colour is indirect.

The paper is consistent — Eq. 8 does say `T` — but the variable name (`res_color`) and the
phrase "similarity of the static appearance feature" `[paper §3.3]` invite reading it as
colour. Worth stating precisely.

**Severity: low** (clarifying).

---

## D-7 — `λ` is an exponent

`[repo: gaussian_model.py:665]`: `imp_score = imp_score * res_color ** lambda_ld`.

`[paper Eq. 8]` renders in the extracted text as
`I_i = Ī_i ( (1/D) Σ_j ‖T_i − T_j‖_1 )` with `λ` positioned ambiguously — plausibly a
superscript that the PDF text layer dropped. **I did not resolve this from the text layer**;
the code is unambiguous that `λ` is an **exponent**, not a multiplier, and the paper's own
wording ("a scaling factor that adjusts the **sensitivity** to appearance variation"
`[paper §3.3]`) fits an exponent better than a multiplier — a pure multiplier would cancel out
of a CDF threshold entirely.

⚠️ Check Eq. 8 visually in `../../OMG.pdf` before quoting its form.

**Severity: low** (probably a rendering artifact, but flag it).

---

## D-8 — Only the XS threshold ships as the default

`[repo: arguments/__init__.py:98]`: `self.importance_thresh = 0.96` — i.e. **OMG-XS**. The
README documents the full ladder ("0.96, 0.98, 0.99, 0.999, 0.9999 for XS to XL. 0.96 (XS) by
default") `[repo: README.md]`, so this is disclosed — but a bare `python train.py` reproduces
only the smallest variant.

**Severity: low**, high trap value. (Same pattern as `../CompGS/`, which ships only λ = 0.001.)

---

## D-9 — Hard external dependencies, one with a hard-coded path

`[repo: README.md]`:
- **tiny-cuda-nn** — all four MLPs `[repo: gaussian_model.py:672-720]`.
- **cuML / RAPIDS** — K-means for SVQ; the README links the RAPIDS install guide and
  acknowledges "If you have trouble in installing cuml…".
- **TMC13 / G-PCC** — must be compiled separately, and "add tmc3 to your environment variable
  or **manually specify its location in the code (lines 243 and 258)**"
  `[repo: utils/gpcc_utils.py]`. The wrapper is itself borrowed: "this script is sourced from
  **HAC++**".

Without G-PCC, positions cannot be encoded and the reported sizes cannot be reproduced.

**Severity: medium** for reproduction.

---

## D-10 — `Ī_i`'s `imp_metric` branch is required and unmentioned

`[repo: gaussian_model.py:641-646]` — `outdoor` uses `accum_weights / area_proj`, `indoor` uses
`accum_weights`. `--imp_metric` is a **required** CLI argument `[repo: README.md]`.

`[paper Eq. 7]` presents a single formula, `Ī_i = Σ_ρ w_{i,ρ}`, with no scene-type branch.
This is inherited from Mini-Splatting, whose own paper calls the metric "case-dependent and
hand-crafted … an experimental trick" `[mini-splatting paper App. E]`.

**Severity: medium** — a hand-picked, scene-type-dependent choice sitting inside the paper's
Eq. 7.

---

## ✅ Verified-correct

| Paper claim | Code |
|---|---|
| Built on Mini-Splatting `[§4.1]` | parameter block + `intersection_preserving` verbatim `[arguments/__init__.py:89-95; gaussian_model.py:627-650]` ✅ |
| `Ī_i` = blending weight gated by argmax-contribution `[Eq. 7]` | `imp_score[accum_area_max == 0] = 0` `[gaussian_model.py:648]` ✅ |
| Morton-order neighbour approximation `[§3.3]` | `sort_morton()`, 21-bit quantization `[gaussian_model.py:752-760]` ✅ |
| CDF-based thresholding with τ `[§3.3, §4.1]` | `init_cdf_mask(importance, thres=τ)` `[gaussian_model.py:666]` ✅ |
| τ = 0.96/0.98/0.99/0.999/0.9999 for XS–XL `[§4.1]` | `importance_thresh` `[arguments/__init__.py:98; README.md]` ✅ |
| Hybrid appearance: `cat(T_n, F_n)` → colour/opacity, `cat(V_n, F_n)` → SH `[Eqs. 3-4]` | `n_input_dims = 16 = 3 + 13` for `mlp_dc`, `mlp_opacity`, `mlp_view` `[gaussian_model.py:687-720]` ✅ |
| `F_n = MLP_s(γ(p_n))` `[Eq. 4]` | `tcnn.NetworkWithInputEncoding`, Frequency encoding `[gaussian_model.py:672-686]` ✅ |
| Geometry stays per-Gaussian `[§3.1]` | `_scaling`, `_rotation` are ordinary parameters ✅ |
| SVQ = partition + independent codebooks `[Eqs. 5-6]` | `kmeans(..., svq_len, n_clusters)` per partition `[gaussian_model.py:842-855]` ✅ |
| SVQ applied to `s`, `r`, and `cat(T, V)` `[§3.2]` | `[gaussian_model.py:814-816]` ✅ |
| K-means init, indices frozen, final 1K iterations `[§3.2]` | `svq_itr = 29 000` of 30 000; indices never updated `[arguments/__init__.py:96; train.py:88-89]` ✅ |
| Post-processing: 16-bit + G-PCC, Huffman, LZMA `[§4.1]` | `[train.py:116-124; gaussian_model.py:857-864]` ✅ |
| MLPs counted in the reported size `[implied]` | `byte = {..., 'MLPs': 0}`; size = `getsize("comp.xz")` `[train.py:119-123]` ✅ **honest** |
| Loss unchanged `[§3.2 implied]` | `0.8·L₁ + 0.2·(1−SSIM)` `[train.py:100-102]` ✅ |

---

## Items I could *not* verify in this pass

| Claim | Status |
|---|---|
| Supplementary "further implementation details" `[paper §4.1]` | `[unverified]` — not in the local PDF |
| Table 5 numeric values (SVQ vs VQ vs R-VQ) | `[unverified]` — cells did not survive text extraction; the directional claims are quoted verbatim |
| Figure 5 values (LD scoring without attribute compression) | `[unverified]` — published as a plot |
| Whether "CompGS [44]" in Tables 1–2 is `../compact3d/` | `[inferred]` — ref [44] is also cited for opacity regularization and VQ `[paper §2.2]`, which matches Navaneet et al.; not confirmed against the bibliography |
| `init_cdf_mask` internals | `[unverified]` — inherited from Mini-Splatting; not re-read here |
| `utils/compress_utils.py`, `utils/gpcc_utils.py` | `[unverified]` — not read in depth |
| Whether the commit reproduces the arXiv-v2 numbers | `[unverified]` — commit is ~7 months older 🔶 |
