# §4 — Cross-branch comparison

Eight rows: the baseline plus the seven implemented arms of the 2³ factorial.

---

## Master table

| Branch | Commit | Mechanism | Canonical source | Fidelity to source | Timing vs `seathru_from_iter` | Gradient path | Medium model safe? | 🔴 | 🟡 |
|---|---|---|---|---|---|---|---|---|---|
| **A0** `baseline/seasplat` | `ddc6259` | — | SeaSplat | reference | reference | ✅ | ✅ | — | — |
| **A1** `feature/a1-deterministic-init` | `ce9c21e` | dense init + `--no_densify` | **EDGS** | ⚠️ **partial** — dense init ✅; but EDGS's `α<0.005` prune, `reduce_opacity` decay and `max_lr` clamp all absent | 🟢 no in-loop schedule; gate straddles activation | ✅ clean | ✅ | 3 | 4 |
| **A2** `feature/a2-spatial-reorganization` | `bcd6eee` | budget prune every 500 iters | **Mini-Splatting** | ❌ **low** — none of blur split / depth reinit / intersection preserving; importance is `opacity×scale`, not accumulated blending weight; deterministic, not stochastic | ✅ **compliant** — first fire 15 500 > 10 000 | ✅ clean, optimizer correctly rebuilt | ✅ **verified** | 3 | 3 |
| **A3** `feature/a3-attribute-quantization` | `980e915` | offline K-means VQ over PLY | **compact3d** | ⚠️ **partial** — `xyz` protected ✅, pre-`exp`/pre-normalize spaces ✅; but post-hoc not QAT, `opacity` quantized, `k=256` vs 4096–32768 | n/a — runs after training | n/a — no gradients | ✅ **explicitly** | 4 | 3 |
| **A4** `feature/a4-init-reorg` | `788b325` | A1 + A2 | EDGS + Mini-Splatting | inherits both | 🟢 A2 compliant; A1 has none | ✅ | ✅ | 1 | 2 |
| **A5** `feature/a5-init-quant` | `fd56225` | A1 + A3 | EDGS + compact3d | inherits both | ✅ no conflict possible | ✅ | ✅ | 2 | 2 |
| **A6** `feature/a6-reorg-quant` | `26ea058` | A2 + A3 | Mini-Splatting + compact3d | inherits both | ✅ A2 compliant | ✅ | ✅ | 1 | 1 |
| **A7** `feature/a7-full-integration` | `b4802fb` | A1 + A2 + A3 | all three | inherits all | 🟢 A2 compliant | ✅ | ✅ | 2 | 1 |

`🔴` / `🟡` = high / medium-severity findings originating in that row (combination rows count
only *new* interaction findings, not inherited ones).

---

## Where each branch stands against its source method

| | A1 vs EDGS | A2 vs Mini-Splatting | A3 vs compact3d |
|---|---|---|---|
| **Core idea implemented?** | ✅ yes — dense RoMa init, densification off | ❌ **no** — only the count-budget shell | ⚠️ partially — VQ, but not quantization-*aware* |
| **Counterweights implemented?** | ❌ **no** — the three EDGS mechanisms that make a densification-free regime survivable are all missing | n/a | ❌ no — no ℓ1 opacity reg, no count reduction |
| **Attribution risk in the write-up** | 🟡 moderate — the headline mechanism is there | 🔴 **high — cite as "magnitude-based pruning," not Mini-Splatting** | 🟡 moderate — cite as "post-hoc VQ," not compact3d |
| **Hyperparameters vs source** | `certainty` 0.02 vs 0.05; refs all vs 180; matches 5 000 vs 15–20 k | budget 800 k (source has no fixed budget) | `k` 256 vs 4096–32768 |

---

## The three questions that gate interpretation

Every ambiguous cell in the table above traces to one of three unrecorded numbers. All three
are recorded nowhere because `docs/ablation_design.md`, `docs/experiment_plan.md` and
`docs/reproducibility_notes.md` are **all 0 bytes**.

| # | Unknown | Blocks | Cost to resolve |
|---|---|---|---|
| **U-1** | `N_init` — the point count `roma_init.py` produces | **A4 and A7.** With densification off, `N` can never grow, so if `N_init ≤ 800 000` then A4 ≡ A1 and A7 ≡ A5, and two factorial cells do not exist. | one unconditional log line; **no retrain** |
| **U-2** | The `seathru_from_iter` value actually passed | **All timing claims.** It defaults to `9_000_000` `[repo: arguments/__init__.py:179]`, i.e. the medium model is **off unless explicitly enabled**. If the runs omitted the flag, every branch was compared against plain 3DGS, not SeaSplat. | read the run command; **no retrain** |
| **U-3** | Whether `max_gaussians = 800 000` ever binds on ordinary densified runs | **A2 and A6** as well. If it never binds, A2 is baseline-with-logging. | same log line as U-1 |

**U-2 is the most serious.** It is binary, it is cheap to check, and if it resolves the wrong
way then no result in the study is about underwater rendering at all.

---

## Severity concentration

| Branch family | Correctness risk | Efficiency-gain risk | Note |
|---|---|---|---|
| A1-derived (A1, A4, A5, A7) | **highest** | moderate | All inherit A1-1: no Gaussian is ever removed, so `L_op` has no executor |
| A3-derived (A3, A5, A6, A7) | high | **highest** | All inherit A3-7: ≈2.8× compression ceiling, `xyz` = 60% of residual |
| **A5** (A1+A3) | 🔴 **peak** | 🔴 **peak** | The only combination with **no compensating mechanism** — see `combination_audit/a1_a3.md` |
| A2-derived (A2, A4, A6, A7) | moderate | conditional on U-1/U-3 | A2 is the only mechanism verified to be both correctly timed and gradient-safe |

---

## Finding tally

| Class | Count |
|---|---|
| **Correctness-risk** (result may be wrong, invalid, or unsupported by the code) | **25** |
| **Efficiency-gain-risk** (claimed gain may be smaller, unattributable, or absent) | **8** |
| **Verified-correct / positive** | **4** |
| Total | 37 |

The four positives are worth naming, because they are the load-bearing things that *do* work:

| | Finding |
|---|---|
| A2-3 | `opacity × scale` ranks `L_op`-suppressed Gaussians lowest — A2 prunes exactly what SeaSplat's opacity prior suppresses |
| A3-8 | `quantize.py` explicitly protects the medium `.pth` and emits a reconstructed PLY for evaluation through the full underwater path |
| C6-2 | A2's pruning truncates the opacity tail before A3's codebook is fit, reducing A3-3's exposure |
| C7-2 | In the binding case, A7's ordering (dense init → count reduction → quantization) is the sequencing compact3d argues for |

Additionally verified correct across the board: **the evaluation path is byte-identical on
all eight branches** (`metrics.py`, `render_uw.py`, `utils/image_utils.py` unchanged), and
**the medium model is provably isolated from every mechanism** — a property of SeaSplat's
global 9-scalar parameterization that would *not* hold under a per-ray medium field such as
SeaThru-NeRF's. See `validation_alignment.md` and `my-research/comparison-glossary.md`.
