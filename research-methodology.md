# Research Methodology Breakdown Request

Produce a research-methodology diagram and structured breakdown of **[FOLDER NAME]**,
grounded in the paper at `./[FOLDER NAME].pdf` and the reference implementation
in `./[FOLDER NAME]/`.

## Scope

1. **Taxonomic placement and modification**
   - Base method this work extends (if any) — name the specific paper/architecture,
     not just "3DGS" or "NeRF" generically.
   - One sentence: what constraint or modification is added.
   - One sentence: which design family it belongs to (e.g. explicit radiance field vs.
     implicit MLP field; per-scene optimization vs. feed-forward/generalizable;
     physically-grounded medium model vs. learned/black-box degradation model).
     This matters for underwater/scattering-medium methods specifically, since the
     field splits sharply along that axis (SeaThru-NeRF/WaterNeRF-style implicit MLP
     medium estimation vs. SeaSplat-style explicit global medium parameters).

2. **Pipeline flowchart** — data → preprocessing → model init → forward pass →
   loss computation → optimization → outputs.
   One diagram per stage if the full pipeline exceeds ~6 nodes.

3. **Formal variable table**
   - Independent variables (what is directly optimized/parameterized) — include
     tensor shape/dimensionality and initialization scheme, tagged per the
     verifiability rule in §6.
   - Dependent variables (quantities derived each forward pass)
   - Fixed/given inputs (data, camera params, hyperparameters, their stated or
     default values)

4. **Full loss function**
   - Each term's name, closed-form expression, and purpose.
   - What failure mode it prevents if removed.
   - If citing an ablation table: state precisely what each row represents
     (cumulative addition to a baseline vs. leave-one-out from the full model —
     these are not interchangeable, and misreading one as the other is a common
     and citable error). Do not infer a leave-one-out claim from an
     additive-ablation table.

5. **Constraints and well-posedness**
   - What makes the naive objective underdetermined (name the specific degenerate
     solution the naive loss admits).
   - What mechanism resolves it (gradient detachment, auxiliary priors,
     staged/interleaved optimization, homogeneity/regularity assumptions).

6. **Implementation deltas from the paper**
   - Read source files in `./[FOLDER NAME]/` directly — training script, config/
     argument defaults, model definition — rather than relying on the README alone.
   - Tag every non-trivial claim:
     - `[paper §X / Eq. Y]` — stated explicitly in the paper
     - `[repo: path/to/file:line or flag]` — confirmed directly from source
     - `[unverified]` — plausible or commonly-assumed, but not traceable to either
       source in this pass; state this rather than asserting it as fact.
   - Note the repo commit/tag inspected, since defaults can change across commits.

7. **Pseudocode**
   - One algorithm block (language-agnostic pseudocode, not a code dump) covering
     the full train step: input batch → forward render → medium composition →
     loss terms → backward → parameter-group-specific update → densification/
     pruning schedule if applicable.
   - Use the paper's own symbol notation (μ, Σ, β^D, β^B, etc.), not generic
     variable names, so it reads as a formal complement to §3's variable table.
   - Mark which lines are gated by schedule flags (e.g. "if iter ≥ seathru_from_iter")
     and which tensors are gradient-detached, per §5 — the pseudocode should make
     the well-posedness mechanism visually traceable in the control flow, not just
     asserted in prose.
   - Tag each line's source the same way as §6 (`[paper]` / `[repo: file:line]` /
     `[inferred]`) since pseudocode is where paper-repo gaps are easiest to paper
     over accidentally.

8. **Computational profile**
   - Training time, inference/render FPS, GPU memory, and Gaussian/parameter
     count, as reported — and whether these were measured on hardware comparable
     to yours (H100 96GB, per your cluster).
   - Any complexity claim relative to the base method (e.g. "adds O(1) global
     parameters vs. base 3DGS" — call out if a claimed complexity advantage is
     asymptotic vs. just empirically-observed-in-this-setting).

9. **Notation glossary**
   - One table: symbol → meaning → first-defined location (paper eq. number or
     repo file). Build this once per method and it becomes reusable across your
     comparison set (`seasplat/`, `seathru_nerf/`, `mini-splatting/`, `CompGS/`,
     `EDGS/`, `RoMaV2/`) without re-deriving notation collisions each time.

10. **Reproducibility checklist**
    - Seed handling, train/test split definition, exact metric computation
      (e.g. masked vs. full-frame PSNR — this varies across underwater papers
      and silently changes reported numbers), and any stated non-determinism.

## Output

- SVG/diagram for the pipeline and loss composition.
- Pseudocode block per §7, source-tagged per line.
- Prose covering points 1, 3, 5, 6, 8, 9, 10 (skip restating what's already
  visually encoded in the diagram or pseudocode).
- A short table of paper-vs-repo disagreements, each tagged per §6.