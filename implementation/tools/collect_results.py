"""Collect every per-run number the campaign produces into one place.

    python -m tools.collect_results --output_root /content/drive/MyDrive/e3dgsuw

Writes four files into `<output_root>/analysis/`:

    results_runs.csv          one row per run, every extracted field
    results_by_scene.csv      mean / sd / cv per cell x scene
    results_by_cell.csv       scene-aggregated, both aggregation rules
    results_summary.md        a single readable view of all of the above

Four sources are merged per run -- `eval_metrics.json` (fidelity and cost),
`model_size.json` (storage, with its container), `run_config.json` (provenance)
and `diagnostics.csv` (the medium-model trajectory). A run missing any of them
still appears, with the absent fields blank, because a partially-written run is
information and silently dropping it would make the completion count wrong.

Three conventions this tool enforces, each because getting them wrong has
already cost this project a result:

**Dispersion is never pooled across scenes.** The measured coefficient of
variation on primitive count ranges from 6.0% to 29.3% depending on scene, so a
single pooled figure understates the stable scenes and overstates the noisy
ones. Every dispersion here is within a cell x scene group.

**Both aggregation rules are reported.** Scene frame counts are unequal
(3/4/3/3 held-out frames), so an unweighted mean of scene means and an
image-weighted mean are different numbers. The methodology requires stating
which is used; this emits both so the choice is visible rather than implicit.

**Medium-model collapse travels with every row.** The collapse is bistable and
seed-conditioned, so a cell x scene group can hold both collapsed and intact
models. Averaging over that mixture measures neither, and no fidelity metric can
detect it -- they score the composed image, which a saturated backscatter term
still fits. Groups that mix are flagged, not silently averaged.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import statistics as st
from collections import defaultdict
from pathlib import Path
from typing import Any, Optional

CHANNELS = ("r", "g", "b")

# Written per run. Order is the report order.
FIDELITY = ("psnr_pooled", "psnr_per_channel", "ssim", "lpips")
COST = (
    "n_primitives_final",
    "train_wall_seconds",
    "effective_optimizer_steps",
    "render_fps",
    "render_ms_per_frame",
    "render_ms_per_frame_cv",
    "render_peak_mem_mb",
    "render_frames_timed",
)
SIZE = ("total_bytes", "total_mb", "bytes_per_primitive", "ratio_vs_this_baseline")

# Metrics whose group summary should be reported as a ratio rather than a
# difference. Frame rate and storage combine multiplicatively; fidelity in dB
# and structural indices do not.
MULTIPLICATIVE = {
    "n_primitives_final", "total_bytes", "total_mb", "bytes_per_primitive",
    "ratio_vs_this_baseline", "render_fps", "train_wall_seconds",
    "effective_optimizer_steps",
}


def _read_json(path: Path) -> Optional[dict]:
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError):
        return None


def _f(value: Any) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


# --- diagnostics -----------------------------------------------------------


def read_diagnostics(path: Path) -> dict[str, Any]:
    """Final medium state, collapse, and the trajectory's shape.

    Returns blanks rather than raising: a run whose diagnostics are missing is
    reported as unmeasured, which is different from reported as intact.
    """
    out: dict[str, Any] = {
        "collapsed_channels": "", "n_collapsed": "",
        "medium_measured": 0,
        "largest_att_drop_pct": "", "largest_att_drop_at": "",
        "n_prim_init": "", "n_prim_at_10000": "", "n_prim_at_15000": "",
        "z_min_final": "", "z_max_final": "",
    }
    for c in CHANNELS:
        out[f"beta_att_{c}"] = ""
        out[f"beta_bs_{c}"] = ""
        out[f"binf_{c}"] = ""

    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            rows = list(csv.DictReader(fh))
    except OSError:
        return out
    if not rows:
        return out

    med = [r for r in rows if r.get("beta_att_r")]
    if med:
        out["medium_measured"] = 1
        last = med[-1]
        collapsed = []
        for c in CHANNELS:
            v = _f(last.get(f"beta_att_{c}"))
            if v is not None:
                out[f"beta_att_{c}"] = round(v, 6)
                # beta_att is unconstrained but its product with depth is
                # clamped at zero, so a negative channel has no gradient and
                # never returns. The final row is therefore sufficient.
                if v < 0:
                    collapsed.append(c.upper())
            for key in (f"beta_bs_{c}", f"binf_{c}"):
                w = _f(last.get(key))
                if w is not None:
                    out[key] = round(w, 6)
        out["collapsed_channels"] = ",".join(collapsed)
        out["n_collapsed"] = len(collapsed)

        # Largest single-step change in mean attenuation, and where. A drop
        # coincident with an intervention is the signature of that
        # intervention; a drop elsewhere is drift.
        by_it: dict[int, dict] = {}
        for r in med:
            by_it[int(r["iteration"])] = r          # last row wins per iteration
        means = []
        for it in sorted(by_it):
            vals = [v for c in CHANNELS
                    if (v := _f(by_it[it].get(f"beta_att_{c}"))) is not None]
            if vals:
                means.append((it, sum(vals) / len(vals)))
        best, where = 0.0, None
        for (i0, m0), (i1, m1) in zip(means, means[1:]):
            if m0 > 1e-6:
                frac = (m0 - m1) / m0
                if frac > best:
                    best, where = frac, f"{i0}->{i1}"
        if where:
            out["largest_att_drop_pct"] = round(100 * best, 2)
            out["largest_att_drop_at"] = where

        zs = [(_f(r.get("z_min")), _f(r.get("z_max"))) for r in med[-40:]]
        zs = [(a, b) for a, b in zs if a is not None and b is not None]
        if zs:
            out["z_min_final"] = round(st.median(a for a, _ in zs), 4)
            out["z_max_final"] = round(st.median(b for _, b in zs), 4)

    counts = {int(r["iteration"]): _f(r.get("n_primitives"))
              for r in rows if r.get("n_primitives")}
    if counts:
        out["n_prim_init"] = int(counts[min(counts)])
        for it in (10_000, 15_000):
            near = [k for k in counts if k <= it]
            if near:
                out[f"n_prim_at_{it}"] = int(counts[max(near)])
    return out


# --- per-run collection ----------------------------------------------------


def collect_runs(output_root: Path, split: str = "Test") -> list[dict[str, Any]]:
    runs: list[dict[str, Any]] = []
    root = output_root / "runs"
    if not root.is_dir():
        return runs

    for cell_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        if cell_dir.name.startswith("_"):          # _archive and friends
            continue
        for scene_dir in sorted(p for p in cell_dir.iterdir() if p.is_dir()):
            for seed_dir in sorted(p for p in scene_dir.iterdir() if p.is_dir()):
                if not seed_dir.name.startswith("s"):
                    continue
                try:
                    seed = int(seed_dir.name[1:])
                except ValueError:
                    continue

                row: dict[str, Any] = {
                    "cell": cell_dir.name, "scene": scene_dir.name, "seed": seed,
                    "complete": 0,
                }

                ev = _read_json(seed_dir / "eval_metrics.json")
                if ev:
                    row["complete"] = 1 if split in ev else 0
                    row["container"] = ev.get("container", "")
                    row["lpips_backbone"] = ev.get("lpips_backbone", "")
                    for which in ("Test", "Train"):
                        block = ev.get(which) or {}
                        prefix = "" if which == split else f"{which.lower()}_"
                        for k in FIDELITY:
                            v = _f(block.get(k))
                            if v is not None:
                                row[f"{prefix}{k}"] = v
                        if which == split:
                            row["n_images"] = block.get("n_images", "")
                    for k in COST:
                        v = _f((ev.get("cost") or {}).get(k))
                        if v is not None:
                            row[k] = v
                    row["population_collapsed_flag"] = int(
                        bool((ev.get("cost") or {}).get("population_collapsed"))
                    )

                sizes = sorted(seed_dir.glob("compressed_*/model_size.json"))
                if sizes:
                    ms = _read_json(sizes[-1]) or {}
                    for k in SIZE:
                        v = _f(ms.get(k))
                        if v is not None:
                            row[k] = v
                    row["size_container"] = "compressed_npy"
                    base = ms.get("baseline") or {}
                    row["baseline_floats_per_primitive"] = base.get(
                        "floats_per_primitive", ""
                    )

                cfg = _read_json(seed_dir / "run_config.json") or {}
                row["gpu"] = (cfg.get("gpu") or {}).get("name", "")
                row["git_commit"] = (cfg.get("git") or {}).get("commit", "")[:9]
                args = cfg.get("args") or cfg
                for k in ("m1_dense_init", "m2_simplify", "m3_quantize",
                          "n_bud", "kmeans_k", "seathru_from_iter"):
                    if k in args:
                        row[k] = args[k]

                row.update(read_diagnostics(seed_dir / "diagnostics.csv"))
                runs.append(row)
    return runs


# --- aggregation -----------------------------------------------------------


def _summarise(values: list[float]) -> dict[str, Any]:
    vals = [v for v in values if v is not None and not math.isnan(v)]
    if not vals:
        return {"n": 0, "mean": "", "sd": "", "cv_pct": "", "min": "", "max": ""}
    mean = st.mean(vals)
    # The standard deviation of one sample is undefined, not zero. Printing 0.0
    # would read as perfect reproducibility, which is the opposite of what a
    # single run tells you -- and this campaign has already been misled once by
    # treating a single-run figure as though it carried no uncertainty.
    sd = st.stdev(vals) if len(vals) > 1 else None
    return {
        "n": len(vals),
        "mean": round(mean, 6),
        "sd": round(sd, 6) if sd is not None else "n/a (n=1)",
        "cv_pct": (round(100 * sd / mean, 3) if sd is not None and mean
                   else ("n/a (n=1)" if sd is None else "")),
        "min": round(min(vals), 6),
        "max": round(max(vals), 6),
    }


def by_scene(runs: list[dict], metrics: list[str]) -> list[dict]:
    """One row per cell x scene x metric. Dispersion lives here and nowhere
    above it, because it is heterogeneous across scenes by a factor of five."""
    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for r in runs:
        if r.get("complete"):
            groups[(r["cell"], r["scene"])].append(r)

    out = []
    for (cell, scene), rs in sorted(groups.items()):
        collapsed = [r for r in rs if r.get("n_collapsed")]
        for m in metrics:
            s = _summarise([r.get(m) for r in rs])
            if not s["n"]:
                continue
            out.append({
                "cell": cell, "scene": scene, "metric": m, **s,
                "n_collapsed": len(collapsed),
                "mixed_collapse": int(0 < len(collapsed) < len(rs)),
            })
    return out


def by_cell(runs: list[dict], metrics: list[str]) -> list[dict]:
    """Scene-aggregated, under BOTH rules.

    `mean_of_scene_means` weights every scene equally; `image_weighted` weights
    by held-out frame count, which is unequal across scenes. They are different
    numbers and the methodology requires the rule to be stated, so both are
    emitted rather than one being chosen silently here.
    """
    per: dict[tuple[str, str], dict[str, list[float]]] = defaultdict(
        lambda: defaultdict(list)
    )
    images: dict[tuple[str, str], float] = {}
    for r in runs:
        if not r.get("complete"):
            continue
        key = (r["cell"], r["scene"])
        images[key] = _f(r.get("n_images")) or 0.0
        for m in metrics:
            v = r.get(m)
            if v is not None:
                per[key][m].append(v)

    cells = sorted({c for c, _ in per})
    out = []
    for cell in cells:
        scenes = [(c, s) for c, s in per if c == cell]
        for m in metrics:
            means = [(k, st.mean(per[k][m])) for k in scenes if per[k].get(m)]
            if not means:
                continue
            unweighted = st.mean(v for _, v in means)
            wsum = sum(images.get(k, 0) for k, _ in means)
            weighted = (
                sum(v * images.get(k, 0) for k, v in means) / wsum if wsum else ""
            )
            n_runs = sum(len(per[k][m]) for k, _ in means)
            out.append({
                "cell": cell, "metric": m,
                "n_scenes": len(means), "n_runs": n_runs,
                "mean_of_scene_means": round(unweighted, 6),
                "image_weighted": round(weighted, 6) if weighted != "" else "",
                "scene_min": round(min(v for _, v in means), 6),
                "scene_max": round(max(v for _, v in means), 6),
                "multiplicative": int(m in MULTIPLICATIVE),
            })
    return out


# --- output ----------------------------------------------------------------


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    fields: list[str] = []
    for r in rows:
        for k in r:
            if k not in fields:
                fields.append(k)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def write_summary(path: Path, runs: list[dict], scene_rows: list[dict],
                  cell_rows: list[dict], metrics: list[str]) -> None:
    done = [r for r in runs if r.get("complete")]
    cells = sorted({r["cell"] for r in runs})
    scenes = sorted({r["scene"] for r in runs})
    gpus = sorted({r.get("gpu", "") for r in done if r.get("gpu")})
    commits = sorted({r.get("git_commit", "") for r in done if r.get("git_commit")})

    L: list[str] = ["# Campaign results — single view", ""]
    L += [f"Runs found: **{len(runs)}**, complete: **{len(done)}**, "
          f"cells: {len(cells)}, scenes: {len(scenes)}", ""]

    if len(gpus) > 1:
        L += [f"> ⚠️ **Runs span {len(gpus)} GPUs**: {', '.join(gpus)}. Every conclusion "
              f"here is a between-cell contrast, and cells on different devices are not "
              f"comparable.", ""]
    if len(commits) > 1:
        L += [f"> ⚠️ **Runs span {len(commits)} implementation commits**: "
              f"{', '.join(commits)}. Check that no change between them alters what a "
              f"cell measures.", ""]

    # -- completion matrix
    L += ["## Completion", "", "| cell | " + " | ".join(scenes) + " |",
          "|---|" + "---|" * len(scenes)]
    for cell in cells:
        cs = []
        for sc in scenes:
            rs = [r for r in runs if r["cell"] == cell and r["scene"] == sc]
            n = sum(1 for r in rs if r.get("complete"))
            cs.append(f"{n}/3" if n < 3 else "**3/3**")
        L.append(f"| {cell} | " + " | ".join(cs) + " |")
    L.append("")

    # -- medium-model collapse
    collapsed = [r for r in done if r.get("n_collapsed")]
    L += ["## Medium-model collapse", ""]
    if not collapsed:
        L += ["No run lost an attenuation channel.", ""]
    else:
        L += [f"**{len(collapsed)} of {len(done)} runs lost an attenuation channel "
              f"permanently.** `beta_att` is unconstrained but its product with depth is "
              f"clamped at zero, so a negative channel has no gradient and never returns; "
              f"its attenuation term is fixed at 1 for the rest of training.", "",
              "| run | channels | largest att. drop | at |", "|---|---|---:|---|"]
        for r in sorted(collapsed, key=lambda r: (r["cell"], r["scene"], r["seed"])):
            L.append(f"| {r['cell']}/{r['scene']}/s{r['seed']} | "
                     f"{r['collapsed_channels']} | {r['largest_att_drop_pct']}% | "
                     f"{r['largest_att_drop_at']} |")
        L.append("")
        mixed = sorted({(x["cell"], x["scene"]) for x in scene_rows
                        if x.get("mixed_collapse")})
        if mixed:
            L += [f"**{len(mixed)} group(s) mix collapsed and intact seeds.** A mean over "
                  f"these averages two physically different models, and no fidelity metric "
                  f"can separate them — they score the composed image, which a saturated "
                  f"backscatter term still fits.", ""]
            for cell, scene in mixed:
                L.append(f"- `{cell}/{scene}`")
            L.append("")

    # -- per scene
    L += ["## Per scene", "",
          "Dispersion is reported here and not above it: the coefficient of variation on "
          "primitive count is heterogeneous across scenes by roughly a factor of five, so a "
          "pooled figure would understate the stable scenes and overstate the noisy ones.",
          ""]
    for m in metrics:
        rows = [r for r in scene_rows if r["metric"] == m]
        if not rows:
            continue
        L += [f"### {m}", "", "| cell | scene | n | mean | sd | cv% | min | max | mixed |",
              "|---|---|---:|---:|---:|---:|---:|---:|:--:|"]
        for r in rows:
            L.append(f"| {r['cell']} | {r['scene']} | {r['n']} | {r['mean']} | "
                     f"{r['sd']} | {r['cv_pct']} | {r['min']} | {r['max']} | "
                     f"{'⚠️' if r['mixed_collapse'] else ''} |")
        L.append("")

    # -- scene-aggregated
    L += ["## Scene-aggregated", "",
          "Both aggregation rules are given. Held-out frame counts are unequal across "
          "scenes, so an unweighted mean of scene means and an image-weighted mean are "
          "different numbers; the rule in use must be stated wherever a figure is quoted.",
          "", "| cell | metric | scenes | runs | mean of scene means | image-weighted | "
          "scene min | scene max |", "|---|---|---:|---:|---:|---:|---:|---:|"]
    for r in cell_rows:
        L.append(f"| {r['cell']} | {r['metric']} | {r['n_scenes']} | {r['n_runs']} | "
                 f"{r['mean_of_scene_means']} | {r['image_weighted']} | "
                 f"{r['scene_min']} | {r['scene_max']} |")
    L += ["", "---", "",
          "Generated by `tools/collect_results.py`. Per-run rows are in "
          "`results_runs.csv`; this file is a view of them, not a separate source."]

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(L), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="collect all campaign results into one view")
    ap.add_argument("--output_root", required=True)
    ap.add_argument("--split", default="Test", choices=("Test", "Train"))
    ap.add_argument("--out_dir", default=None,
                    help="default: <output_root>/analysis")
    ap.add_argument("--metric", action="append", default=None,
                    help="restrict to these metrics; repeatable")
    args = ap.parse_args()

    root = Path(args.output_root)
    out_dir = Path(args.out_dir) if args.out_dir else root / "analysis"

    runs = collect_runs(root, args.split)
    if not runs:
        print(f"no runs found under {root / 'runs'}")
        return 1

    metrics = args.metric or [
        m for m in (*FIDELITY, *COST, *SIZE)
        if any(m in r for r in runs)
    ]

    scene_rows = by_scene(runs, metrics)
    cell_rows = by_cell(runs, metrics)

    write_csv(out_dir / "results_runs.csv", runs)
    write_csv(out_dir / "results_by_scene.csv", scene_rows)
    write_csv(out_dir / "results_by_cell.csv", cell_rows)
    write_summary(out_dir / "results_summary.md", runs, scene_rows, cell_rows, metrics)

    done = sum(1 for r in runs if r.get("complete"))
    collapsed = sum(1 for r in runs if r.get("n_collapsed"))
    print(f"{len(runs)} runs ({done} complete), {len(metrics)} metrics")
    if collapsed:
        print(f"  {collapsed} run(s) with a collapsed attenuation channel "
              f"-- see results_summary.md")
    for name in ("results_runs.csv", "results_by_scene.csv",
                 "results_by_cell.csv", "results_summary.md"):
        print(f"  {out_dir / name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
