# Revisited Thesis — Audit and Revision Plan

**Status: audit complete, prose not started.** `THESIS.md` requires the diagnostic package
before any rewriting: *"Do not begin full prose rewriting during the initial audit."*

This folder holds that package. Chapter drafts will be added here after Gate 2 approval.

---

## Read in this order

| | File | Answers |
|---|---|---|
| 0 | [`00-phase0-manifest.md`](00-phase0-manifest.md) | What is authoritative, what could not be reached — **Gate 1** |
| 1 | [`01-discrepancy-ledger.md`](01-discrepancy-ledger.md) | Where the manuscript, the two codebases, the source methods and the runs disagree |
| 2 | [`02-reviewer-traceability.md`](02-reviewer-traceability.md) | All 19 reviewer concerns, classified, with what the new work does and does not answer |
| 3 | [`03-claim-validity-ledger.md`](03-claim-validity-ledger.md) | Every manuscript claim classified against evidence |
| 4 | [`04-repositioning.md`](04-repositioning.md) | Two candidate framings, a recommendation, revised RQs and contributions — **Gate 2, needs approval** |
| 5 | [`05-surgical-plan.md`](05-surgical-plan.md) | Section-by-section actions — **Gate 3** |
| 6 | [`06-experiment-and-literature-plan.md`](06-experiment-and-literature-plan.md) | Minimum additional work, costed |

---

## The four things that matter most

**1. The manuscript's headline result does not survive audit.**
"Mini-Splatting importance-based budget pruning gives the best overall balance — 72% reduction
for 0.05 dB" describes `opacity × scale` with deterministic top-k, fired once. Mini-Splatting
uses accumulator-based importance with *stochastic* sampling at two iterations — and its own
paper rejects top-k as destroying local geometry. The prior code says *"Inspired by
Mini-Splatting"*; the thesis says it *is* Mini-Splatting. **(D-1)**

The same result was reported without dispersion, which is now measured at 6–29% per scene.
A 0.05 dB difference from single runs sits far inside that. **(D-5)**

**2. The current implementation already fixes most of what was wrong.**
Seven of ten discrepancies are resolved: faithful M2 and M3, a baseline verified
indistinguishable from unmodified SeaSplat at n=3, a defined timing protocol, per-scene
results, three seeds, recorded hardware. Reviewer 3's four reproducibility demands are met in
full.

**3. The rejection was mostly not about the experiments.**
Of 19 concerns, six remain unresolved. **Five are writing and positioning**; exactly one —
the missing rate–distortion sweep — needs compute.

**4. Chapter 4 must be rebuilt, and about 60% of the thesis can be written now.**
Chapters 2, 1, 3 and §§4.1–4.3 are unblocked by the running campaign. Chapter 4's existing
tables come from a different codebase with documented fidelity gaps and cannot be retained.

---

## Recommended positioning

**Framing A — a controlled factorial study of whether terrestrial 3DGS efficiency mechanisms
transfer to physics-aware underwater reconstruction, and of the integration boundaries that
determine whether they do.**

Supportable with runs already scheduled. Framing B adds a budget sweep and answers the last
compute-bound reviewer concern; the two are nested, so writing A first costs nothing.

Full argument, revised research questions, hypotheses and contributions:
[`04-repositioning.md`](04-repositioning.md).

---

## What is needed to proceed

1. **Approve or amend the positioning** (Gate 2). Everything downstream depends on it.
2. **Decide on the additional experiments** — the CD-6 ablation is 12 runs and converts this
   thesis's own proposed remedy from designed to demonstrated; the budget sweep is 18–36 runs
   and answers the last reviewer objection.
3. **Confirm the literature work** — six method breakdowns, no compute, blocking Chapter 2.

Once positioning is approved, drafting begins with Chapter 2, per the brief's Gate 4 order.

---

## Evidence base

| | |
|---|---|
| Implementation | `implementation/` @ `3c165ae`, 60 files, 81 acceptance checks |
| Methodology | `combined-method-methodology/`, 13 technical files + 10-file chapter set |
| Source methods | 9 × `research-methodology-output/`, 12 files each |
| Prior manuscript | 153 pp., 2026-05-22 |
| Reviews | SIGGRAPH Asia 2026 `tcom_126`, 4 reviews + meta-review, −0.5 average |
| Prior implementation | separate fork, 8 feature branches, tips 2026-05-11/12 |
| Campaign | 12 of 112 runs complete (S1) |
