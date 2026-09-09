"""Campaign analysis: main effects, interactions, and dispersion.

    python -m tools.analyse --output_root <root>
    python -m tools.analyse --output_root <root> --metric psnr_pooled --json out.json

Reads what the runs emit -- `eval_metrics.json`, `model_size.json`,
`run_config.json` -- and produces the contrasts the design is built around.

Three properties this implements that the design insists on:

**Main effects are estimated in BOTH directions.** From below (`A1−A0`) and
from above (`A7−A6`). Where they agree within pooled dispersion the mechanism
is independent and either may be quoted; where they disagree, *neither may be
quoted alone* and the disagreement is the interaction. A tool that reported
only one direction would make that rule unenforceable.

**Interactions are deviations from an explicit null.** For quality metrics the
null is additive; for ratio measures (storage, primitive count, frame rate) it
is multiplicative, computed in log space. Mixing the two silently is an easy
and invisible error.

**Nothing is reported without its dispersion.** Every contrast carries a pooled
standard error, and interactions -- being differences of differences -- carry
roughly twice the variance of a main effect. The literature this builds on
reports sub-decibel ablation differences from single runs; this refuses to.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Optional

CELLS = ["A0", "A1", "A2", "A3", "A4", "A5", "A6", "A7"]

# Which mechanisms each cell has: (M1, M2, M3)
CELL_FLAGS: dict[str, tuple[bool, bool, bool]] = {
    "A0": (False, False, False), "A1": (True, False, False),
    "A2": (False, True, False), "A3": (False, False, True),
    "A4": (True, True, False), "A5": (True, False, True),
    "A6": (False, True, True), "A7": (True, True, True),
}

# Metrics where combination is multiplicative rather than additive.
MULTIPLICATIVE = {
    "ratio_vs_this_baseline", "total_bytes", "bytes_per_primitive",
    "n_primitives_final", "train_wall_seconds", "effective_optimizer_steps",
    # Frame rate combines multiplicatively -- a speedup is a ratio, and the
    # design's prediction about it ("sub-linear in primitive reduction") is a
    # statement about ratios. Peak memory is deliberately NOT here: it carries
    # a large device-constant floor, so a ratio of two peaks is dominated by
    # the constant and an additive difference in MB is the honest form.
    "render_fps",
}

DEFAULT_METRICS = [
    "psnr_pooled", "psnr_per_channel", "ssim", "lpips",
    "n_primitives_final", "total_bytes", "bytes_per_primitive",
    "effective_optimizer_steps", "train_wall_seconds",
    # Frame rate is the one efficiency measure all three mechanisms affect, and
    # two of the design's predictions are stated against it. Omitting it from
    # the defaults would leave both untested by the analysis that runs.
    "render_fps", "render_ms_per_frame", "render_peak_mem_mb",
]


# ---------------------------------------------------------------------------
# loading
# ---------------------------------------------------------------------------


@dataclass
class Run:
    cell: str
    scene: str
    seed: int
    metrics: dict[str, float] = field(default_factory=dict)
    n_images: int = 0
    gpu: str = ""


def _read_json(path: Path) -> Optional[dict]:
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:  # noqa: BLE001 - a missing or partial run is not fatal
        return None


def load_campaign(output_root: str | Path, split: str = "Test") -> list[Run]:
    """Collect every completed run under `runs/<cell>/<scene>/s<seed>/`."""
    root = Path(output_root) / "runs"
    runs: list[Run] = []
    if not root.exists():
        return runs

    for cell_dir in sorted(root.iterdir()):
        if not cell_dir.is_dir() or cell_dir.name not in CELL_FLAGS:
            continue
        for scene_dir in sorted(cell_dir.iterdir()):
            if not scene_dir.is_dir():
                continue
            for seed_dir in sorted(scene_dir.iterdir()):
                if not seed_dir.is_dir() or not seed_dir.name.startswith("s"):
                    continue
                try:
                    seed = int(seed_dir.name[1:])
                except ValueError:
                    continue

                ev = _read_json(seed_dir / "eval_metrics.json")
                if ev is None or split not in ev:
                    continue  # incomplete run

                run = Run(cell_dir.name, scene_dir.name, seed)
                block = ev[split]
                for key in ("psnr_pooled", "psnr_per_channel", "ssim", "lpips"):
                    if key in block:
                        run.metrics[key] = float(block[key])
                run.n_images = int(block.get("n_images", 0))

                for key, val in (ev.get("cost") or {}).items():
                    if isinstance(val, (int, float)):
                        run.metrics[key] = float(val)

                # Newest compressed artifact, if any.
                sizes = sorted(seed_dir.glob("compressed_*/model_size.json"))
                if sizes:
                    ms = _read_json(sizes[-1]) or {}
                    for key in ("total_bytes", "bytes_per_primitive",
                                "ratio_vs_this_baseline"):
                        if key in ms:
                            run.metrics[key] = float(ms[key])

                cfg = _read_json(seed_dir / "run_config.json") or {}
                run.gpu = (cfg.get("gpu") or {}).get("name", "")
                runs.append(run)
    return runs


# ---------------------------------------------------------------------------
# aggregation
# ---------------------------------------------------------------------------


@dataclass
class Estimate:
    """A value with its uncertainty and where it came from."""
    mean: float
    sem: float       # standard error of the mean
    n: int

    def __repr__(self) -> str:  # pragma: no cover - display only
        return f"{self.mean:.4f}±{self.sem:.4f}(n={self.n})"


def _mean_sem(values: list[float]) -> Optional[Estimate]:
    vals = [v for v in values if v is not None and math.isfinite(v)]
    if not vals:
        return None
    n = len(vals)
    mean = sum(vals) / n
    if n < 2:
        # A single run has no measurable dispersion. Reporting sem=0 would
        # imply certainty that does not exist, so it is flagged as unknown.
        return Estimate(mean, float("nan"), n)
    var = sum((v - mean) ** 2 for v in vals) / (n - 1)
    return Estimate(mean, math.sqrt(var / n), n)


def per_cell(
    runs: Iterable[Run], metric: str, weighting: str = "unweighted"
) -> dict[str, Estimate]:
    """Aggregate to one estimate per cell, over scenes and seeds.

    Seeds are pooled within a scene first, then scenes are combined -- so the
    dispersion reported is across seeds, which is the quantity that says
    whether a contrast is real.
    """
    by_cell_scene: dict[tuple[str, str], list[float]] = {}
    images: dict[tuple[str, str], int] = {}
    for r in runs:
        if metric not in r.metrics:
            continue
        key = (r.cell, r.scene)
        by_cell_scene.setdefault(key, []).append(r.metrics[metric])
        images[key] = max(images.get(key, 0), r.n_images)

    out: dict[str, Estimate] = {}
    for cell in CELLS:
        scene_keys = [k for k in by_cell_scene if k[0] == cell]
        if not scene_keys:
            continue

        scene_means: list[float] = []
        scene_vars: list[float] = []
        weights: list[float] = []
        n_total = 0
        dispersion_unknown = False
        for k in scene_keys:
            est = _mean_sem(by_cell_scene[k])
            if est is None:
                continue
            scene_means.append(est.mean)
            if math.isnan(est.sem):
                # A single seed has no measurable dispersion. Substituting zero
                # here would turn "unknown" into "certain" and would propagate
                # into every contrast as a spuriously tight error bar, so the
                # unknown is carried through instead.
                dispersion_unknown = True
                scene_vars.append(0.0)
            else:
                scene_vars.append(est.sem ** 2)
            weights.append(images.get(k, 1) if weighting == "image_weighted" else 1.0)
            n_total += est.n

        if not scene_means:
            continue
        wsum = sum(weights)
        mean = sum(m * w for m, w in zip(scene_means, weights)) / wsum
        # Variance of a weighted mean of independent scene means.
        var = sum(v * (w / wsum) ** 2 for v, w in zip(scene_vars, weights))
        sem = float("nan") if dispersion_unknown else math.sqrt(var)
        out[cell] = Estimate(mean, sem, n_total)
    return out


# ---------------------------------------------------------------------------
# contrasts
# ---------------------------------------------------------------------------


def _combine(est: dict[str, Estimate], terms: dict[str, int],
             multiplicative: bool) -> Optional[Estimate]:
    """Evaluate a signed linear combination of cells, propagating error.

    For multiplicative metrics the combination is done in log space, so a
    contrast is a ratio rather than a difference, and the result is
    exponentiated back.
    """
    if any(c not in est for c in terms):
        return None
    total = 0.0
    var = 0.0
    n = min(est[c].n for c in terms)
    for cell, sign in terms.items():
        e = est[cell]
        if multiplicative:
            if e.mean <= 0:
                return None
            value = math.log(e.mean)
            # delta method: Var(log X) ~ Var(X) / X^2
            v = (e.sem / e.mean) ** 2 if math.isfinite(e.sem) else float("nan")
        else:
            value = e.mean
            v = e.sem ** 2 if math.isfinite(e.sem) else float("nan")
        total += sign * value
        var = float("nan") if math.isnan(v) or math.isnan(var) else var + v
    sem = math.sqrt(var) if not math.isnan(var) else float("nan")
    if multiplicative:
        # Report the ratio itself; the error bar is asymmetric in linear space,
        # so the log-space sem is carried through as a relative figure.
        return Estimate(math.exp(total), sem, n)
    return Estimate(total, sem, n)


MAIN_FROM_BELOW = {"M1": {"A1": 1, "A0": -1},
                   "M2": {"A2": 1, "A0": -1},
                   "M3": {"A3": 1, "A0": -1}}

MAIN_FROM_ABOVE = {"M1": {"A7": 1, "A6": -1},
                   "M2": {"A7": 1, "A5": -1},
                   "M3": {"A7": 1, "A4": -1}}

# Two-way interactions, with the third factor held OFF -- this is the form the
# design specifies:  (A4−A0) − [(A1−A0) + (A2−A0)]  =  A4 − A1 − A2 + A0
TWO_WAY = {
    "M1xM2": {"A4": 1, "A1": -1, "A2": -1, "A0": 1},
    "M1xM3": {"A5": 1, "A1": -1, "A3": -1, "A0": 1},
    "M2xM3": {"A6": 1, "A2": -1, "A3": -1, "A0": 1},
}

# Standard 2^3 three-factor contrast: sign = product of factor signs.
THREE_WAY = {"A7": 1, "A4": -1, "A5": -1, "A6": -1,
             "A1": 1, "A2": 1, "A3": 1, "A0": -1}


def analyse_metric(
    runs: list[Run], metric: str, weighting: str = "unweighted"
) -> dict[str, Any]:
    est = per_cell(runs, metric, weighting)
    mult = metric in MULTIPLICATIVE

    out: dict[str, Any] = {
        "metric": metric,
        "combination": "multiplicative" if mult else "additive",
        "weighting": weighting,
        "cells": {c: {"mean": e.mean, "sem": e.sem, "n": e.n}
                  for c, e in est.items()},
        "missing_cells": [c for c in CELLS if c not in est],
        "main_effects": {},
        "interactions": {},
    }

    for mech in ("M1", "M2", "M3"):
        below = _combine(est, MAIN_FROM_BELOW[mech], mult)
        above = _combine(est, MAIN_FROM_ABOVE[mech], mult)
        entry: dict[str, Any] = {
            "from_below": None if below is None else vars(below),
            "from_above": None if above is None else vars(above),
        }
        if below and above:
            if mult:
                diff = abs(math.log(below.mean) - math.log(above.mean))
            else:
                diff = abs(below.mean - above.mean)
            known = math.isfinite(below.sem) and math.isfinite(above.sem)
            pooled = math.sqrt(below.sem ** 2 + above.sem ** 2) if known else float("nan")
            entry["disagreement"] = diff
            entry["pooled_sem"] = pooled
            if not known or pooled == 0:
                # Without dispersion, agreement cannot be established either
                # way. Reporting None rather than False keeps "we could not
                # tell" distinct from "they disagree".
                entry["directions_agree"] = None
                entry["quotable_alone"] = False
                entry["reason"] = "dispersion unknown (need >= 2 seeds)"
            else:
                agree = diff <= 2 * pooled
                entry["directions_agree"] = bool(agree)
                entry["quotable_alone"] = bool(agree)
        out["main_effects"][mech] = entry

    for name, terms in TWO_WAY.items():
        res = _combine(est, terms, mult)
        if res is None:
            out["interactions"][name] = None
            continue
        null = 1.0 if mult else 0.0
        dev = abs(math.log(res.mean) if mult else res.mean)
        out["interactions"][name] = {
            **vars(res),
            "null": null,
            "exceeds_2sem": bool(
                math.isfinite(res.sem) and res.sem > 0 and dev > 2 * res.sem
            ),
        }

    res = _combine(est, THREE_WAY, mult)
    out["interactions"]["M1xM2xM3"] = None if res is None else {
        **vars(res),
        "null": 1.0 if mult else 0.0,
        "exceeds_2sem": bool(
            math.isfinite(res.sem) and res.sem > 0
            and abs(math.log(res.mean) if mult else res.mean) > 2 * res.sem
        ),
    }
    return out


# ---------------------------------------------------------------------------
# reporting
# ---------------------------------------------------------------------------


def format_report(result: dict[str, Any]) -> str:
    lines: list[str] = []
    m, comb = result["metric"], result["combination"]
    lines.append(f"\n=== {m}  ({comb}, {result['weighting']}) " + "=" * 24)

    if result["missing_cells"]:
        lines.append(f"  MISSING CELLS: {', '.join(result['missing_cells'])} "
                     f"-- contrasts needing them are omitted")

    lines.append("  cells:")
    for cell in CELLS:
        c = result["cells"].get(cell)
        if c:
            sem = "  ±nan (single run)" if math.isnan(c["sem"]) else f"±{c['sem']:.4f}"
            lines.append(f"    {cell}  {c['mean']:12.4f} {sem}  n={c['n']}")

    lines.append("  main effects (from below / from above):")
    for mech, e in result["main_effects"].items():
        b, a = e.get("from_below"), e.get("from_above")
        if not b or not a:
            lines.append(f"    {mech}: incomplete")
            continue
        if e.get("directions_agree") is None:
            verdict = f"UNDETERMINED -- {e.get('reason', 'dispersion unknown')}"
        elif e["directions_agree"]:
            verdict = "agree -- either may be quoted"
        else:
            verdict = "DISAGREE -- neither may be quoted alone; report the interaction"
        lines.append(
            f"    {mech}: {b['mean']:+.4f} / {a['mean']:+.4f}   "
            f"|diff|={e['disagreement']:.4f} vs 2·sem={2 * e['pooled_sem']:.4f}  -> {verdict}"
        )

    lines.append("  interactions (deviation from the "
                 f"{'multiplicative' if comb == 'multiplicative' else 'additive'} null):")
    for name, i in result["interactions"].items():
        if i is None:
            lines.append(f"    {name}: incomplete")
            continue
        flag = "EXCEEDS 2·sem" if i["exceeds_2sem"] else "within noise"
        lines.append(
            f"    {name:10s} {i['mean']:+.4f}  (null {i['null']:.1f}, "
            f"sem {i['sem']:.4f})  -> {flag}"
        )
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="analyse the campaign")
    ap.add_argument("--output_root", required=True)
    ap.add_argument("--split", default="Test", choices=["Test", "Train"])
    ap.add_argument("--metric", action="append", default=None)
    ap.add_argument("--weighting", default="unweighted",
                    choices=["unweighted", "image_weighted"])
    ap.add_argument("--json", default=None, help="write full results here")
    args = ap.parse_args()

    runs = load_campaign(args.output_root, args.split)
    if not runs:
        print(f"no completed runs under {args.output_root}/runs")
        return 1

    cells = sorted({r.cell for r in runs})
    scenes = sorted({r.scene for r in runs})
    gpus = sorted({r.gpu for r in runs if r.gpu})
    print(f"loaded {len(runs)} runs: {len(cells)} cells, {len(scenes)} scenes")
    if len(gpus) > 1:
        print(f"  *** WARNING: runs span {len(gpus)} GPUs: {gpus}. "
              f"Between-cell contrasts across different devices are not "
              f"comparable, and every conclusion here is such a contrast. ***")

    metrics = args.metric or DEFAULT_METRICS
    results = {}
    for metric in metrics:
        if not any(metric in r.metrics for r in runs):
            continue
        res = analyse_metric(runs, metric, args.weighting)
        results[metric] = res
        print(format_report(res))

    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(results, fh, indent=2)
        print(f"\nwrote {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
