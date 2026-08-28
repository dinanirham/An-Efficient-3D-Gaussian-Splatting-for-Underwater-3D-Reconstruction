# §4 — The objective

## 4.1 Headline: the combined method's loss is the baseline's loss, unchanged

This is the shortest section in the technical set, and the brevity is itself a finding.

- **M1 (EDGS) adds nothing.** "THE ENTIRE OBJECTIVE. No regulariser, no correspondence loss.
  (`tv_loss` exists in `losses.py:78` but is never called)"
  `[../EDGS/07-pseudocode.md line 33]`. Its whole contribution is upstream of optimization.
- **M2 (Mini-Splatting) adds nothing.** "There is **no** `.detach()` and no auxiliary loss in
  the entire method" `[../mini-splatting/07-pseudocode.md pt.1]`. Its contribution is
  non-differentiable bookkeeping around an untouched objective.
- **M3 (CompGS-VQ) adds exactly one term** — an ℓ1 opacity regulariser — **and the combined
  method disables it** (§4.3).

Consequently the objective of every cell A0–A7 is **SeaSplat's seven terms with SeaSplat's
six λ**. What changes across cells is not the loss but *what the loss is evaluated on*: under
M3 the forward pass renders **quantized** attributes, so `L_GS` measures quantized-model
quality while gradients update the unquantized parameters (§4.4).

---

## 4.2 The baseline's full objective, carried forward verbatim

The paper writes it as an unweighted sum of seven terms `[seasplat paper Eq. 10]`; the
repository implements six distinct λ spanning **200×**. Both forms matter — the unweighted
form is what a reader of the paper will expect, the weighted form is what runs.

### As implemented `[../seasplat/04-loss.md §4.3]`

```
L_total = 0.8·L₁(Î, I) + 0.2·(1 − SSIM(Î, I))     # L_GS       — λ implicit
        + 1.00 · L_Z-recon                        # dwr_lambda
        + 1.00 · L_bs                             # dcp_loss_lambda
        + 0.10 · L_gw           [i > 10 000]      # gw_loss_lambda
        + 2.00 · L_sat          [i > seathru]     # sat_loss_lambda
        + 0.01 · L_op                             # bg_lambda
        + 2.00 · L_Zsmooth                        # depth_smooth_lambda
```

### Term-by-term, with what each prevents and which mechanism perturbs it

| # | Term | Closed form (repo) | Prevents | Perturbed by |
|---|---|---|---|---|
| 1 | **`L_GS`** | `0.8·‖Î−I‖₁ + 0.2·(1−SSIM(Î,I))` | nothing is constrained without it | **M3** — `Î` is built from quantized `f_dc`, `s`, `q` |
| 2 | **`L_bs`** | `1000·SmoothL₁(relu(−D̃),0;β=0.2) + ‖relu(D̃)‖₁`, `D̃ = I⊘ − B̂⊘` | **D-1, the "no medium" solution** `Â=1, B̂=0, Ĵ=I` — a *global optimum* of `L_GS` | **none** — both operands are detached from geometry, so no mechanism can reach it |
| 3 | **`L_gw`** | `mean_c(mean_{H,W}(Ĵ_c) − 0.5)²`, gated `i > 10 000` | **D-3, the per-channel colour gauge** `Ĵ_c ← γ_c Ĵ_c` absorbed by `β_att` | **M3** — quantized `f_dc` shifts `Ĵ`'s channel means |
| 4 | **`L_sat`** | `mean(relu(−Ĵ) + relu(Ĵ−0.7))²` | `Ĵ` blowing out where `1/Â` amplification is unbounded | **M3** — same path |
| 5 | **`L_op`** | `‖α[‖Î⊘ − σ(B^∞)⊘‖₂ < 0.2√3]‖₁` | **D-4, water-column floaters** — the +2.42 dB term | **M1, M2** — both rewrite opacity dynamics (`03-variables.md` IC-1) |
| 6 | **`L_Zsmooth`** | `mean\|∂ₓẐ·e^{−∂ₓI}\| + mean\|∂_yẐ·e^{−∂_yI}\|` | depth noise being used as free capacity by the medium model | **M1, M2** — both change what produces `Ẑ` |
| 7 | **`L_Z-recon`** | `mean\|Ẑ⊘ ⊙ (Î − I)\|` | far-field colour restoration collapsing; the detached weight forbids the `Ẑ → 0` shortcut | **M2** — the prune rescales `Ẑ` (`03-variables.md` IC-2) |

Full derivations, failure modes and paper-vs-repo forms for every term are in
`../seasplat/04-loss.md` §4.2 and are not restated here.

> **Inherited shared deviation, not a disagreement.** Both the paper and the repo write
> `L_Zsmooth` with the **signed** image gradient `e^{−∂I}`, where the cited source (Godard et
> al.) uses `e^{−|∂I|}`. The consequence is that depth smoothness is enforced *more* strongly
> across dark→bright edges than in flat regions — inverted on half of all edges — and the
> repo's own commented-out block contains the correct version
> `[../seasplat/04-loss.md term 6; ../seasplat/11-paper-vs-repo-disagreements.md S-1]`.
> The combined method inherits this unchanged. `[PI]` It is a candidate one-line fix, but
> changing it would make A0 no longer SeaSplat-as-published, so it is **left as-is** and
> declared.

---

## 4.3 The one mechanism-required term, and why it is disabled

**Term:** `λ_reg · Σ_i α_i`, ℓ1 on opacity, `λ_reg = 1e-7`, active only for
`15 000 < i ≤ 20 000`, with `prune(0.005)` every 1 000 iterations inside that window
`[../compact3d/04-loss.md §4.2]`.

**Status in the combined method, per the tagging the brief asks for:**

| Question | Answer |
|---|---|
| **Needed?** | ❌ **No.** CompGS-VQ needs it because *its* count reduction has no other source, and because it identified that after quantization the unquantized position and opacity are >80% of the residual budget `[compact3d paper §3]`. In the combined method, **M2 is the count-reduction mechanism**, and it reduces count directly to a budget rather than indirectly through an opacity prior. |
| **Implemented?** | ⚠️ **Present in the source, deliberately disabled.** `--opacity_reg` defaults to `False` in CompGS-VQ's own CLI anyway `[../compact3d/11-paper-vs-repo-disagreements.md D-6]`, so disabling it is the *default* behaviour, not a patch. |
| **Validated?** | ❌ **No.** The decision to disable is an argument (below), not a measurement. |

**The argument for disabling.** Three reasons, in decreasing order of force:

1. **It confounds the factorial design.** CompGS-VQ's own numbers attribute the compression
   to quantization and the **2–3× rendering speedup to the pruning, not the quantization**
   `[../compact3d/08-computational-profile.md §8.2]`. Leaving it on would make the "M3"
   factor a *quantization-plus-pruning* factor, so the M2 and M3 columns of the 2³ matrix
   would not be independent and the A6/A7 cells would double-prune. The matrix would stop
   measuring what it claims to measure.
2. **It adds a fifth writer to the opacity variable.** `03-variables.md` IC-1 already
   records four forces on `_opacity` under A4/A7, three of them calibrated in codebases where
   `L_op` does not exist. Adding a fifth with no compensating benefit worsens the least
   tractable interaction in the design.
3. **Its schedule collides with M2's.** The regulariser window is `15 000–20 000` with the
   lower bound **hard-coded** `[../compact3d/11-paper-vs-repo-disagreements.md D-5]`, which
   is exactly the window bracketed by `simp_iteration1` and `simp_iteration2`
   `[../mini-splatting/03-variables.md]`. Two count-reduction mechanisms would run
   simultaneously on overlapping schedules.

**The cost of disabling, stated honestly.** CompGS-VQ's published compression figures
(41× / 65×) and its FPS figures were obtained **with** the regulariser. Disabling it means
the M3 cell of this study is **not a reproduction of CompGS-VQ** and its numbers must not be
compared to CompGS-VQ's published table. `[PI]` This is recorded again in
`06-implementation-deltas.md` and `11-paper-vs-repo-disagreements.md`.

---

## 4.4 What changes without the loss changing: quantization-aware evaluation

Under M3 (A3, A5, A6, A7), the forward pass renders from centroids while the optimizer holds
the unquantized parameters, with a straight-through estimator supplying the missing gradient
`[../compact3d/05-constraints.md M-1/M-2]`. Formally the objective is unchanged; operationally
three things follow, and the third is specific to this baseline.

1. **`L_GS` now measures quantized-model quality.** This is the point of
   quantization-aware training: "parameters drift toward configurations that quantize well"
   `[../compact3d/05-constraints.md M-1]`.
2. **Gradients still route to the parameter groups the baseline's optimizer expects**, so
   SeaSplat's three-optimizer separation and its detach map survive intact
   (`02-pipeline.md` §2.4). The composition is type-correct.
3. ⚠️ **The medium parameters absorb part of the quantization error.** `[inferred]` This
   follows from combining two verified facts: `Î = Ĵ ⊙ Â + B̂` with `Ĵ` built from quantized
   `f_dc` `[../seasplat/02-pipeline.md Stage C]`, and the medium optimizers being stepped
   against the same `L_GS` in 50-step bursts `[../seasplat/05-constraints.md M-2]`. Nothing
   prevents `β_att` and `B^∞` from shifting to compensate for a systematic colour bias
   introduced by the DC codebook. In vanilla 3DGS there is no such absorber; here there is,
   and it is *global*, so a local quantization error gets explained by a scene-wide medium
   change.

   **Why this matters and is not merely academic:** the entire scientific interest of
   SeaSplat is that `β_att`, `β_bs`, `B^∞` are supposed to describe *the water*. If they also
   absorb codebook error, they stop being interpretable as a medium estimate at exactly the
   configurations (A3, A5, A6, A7) where compression is being claimed. `[PI]` The mitigation
   is to **log the medium parameters at every save iteration and report their drift between
   quantized and unquantized runs** — a cheap, direct check that costs nothing and would
   convert this from a hypothesis into a measurement. It is not performed in this evidence
   base.

---

## 4.5 Reading the baseline's ablation table — the trap that must not be repeated

SeaSplat's Table III is **cumulative-additive, not leave-one-out**
`[../seasplat/04-loss.md §4.4]`. Every row is *vanilla 3DGS plus the listed subset*; no row
removes a component from the full model. The consequences were recorded there and bind any
citation in this work:

- ✅ "adding BS on top of DS+BG+C costs 0.49 dB in-medium (27.13 → 26.64)"
- ❌ "removing BS costs 0.47 dB"
- **Row 9 ≠ row 8**: "Ours (all losses)" = 27.11 is *not* the same configuration as
  "+DS+BG+C+BS" = 26.64, so the ladder does **not** enumerate the full objective —
  `L_Z-recon` is unaccounted for.
- The legend defines "SD"; every row is labelled "DS". Same term.

**And the honest headline:** only `L_op` ("BG", λ = 0.01, the *smallest* weight) moves
in-medium PSNR materially — **+2.42 dB alone**. `L_bs` and `L_Zsmooth` *individually hurt*
the in-medium metric. The paper's own explanation is a measurement mismatch: those terms
exist to make the **restored** image `Ĵ` meaningful, and "there is no ground truth for `Ĵ`"
`[../seasplat/04-loss.md §4.4, paper §V.C]`.

> **This is the direct reason `01-taxonomy.md` A3-b flags quantization damage to `Ĵ` as
> unmeasurable by construction, and the reason `06-evaluation-metrics` in the narrative
> chapter separates reconstruction fidelity from restoration quality as different
> instruments.** The same blind spot that makes SeaSplat's own ablation
> under-informative makes the compression ablations under-informative in the same
> direction — and unlike SeaSplat, this work is in a position to say so up front.

`[PI]` **The combined method's own ablation matrix is deliberately factorial, not
cumulative**, precisely so that this reading trap does not recur. See
`10-reproducibility.md` §10.5 and `chapter/05-experimental-design.md`.
