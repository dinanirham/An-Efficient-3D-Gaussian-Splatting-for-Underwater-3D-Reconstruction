"""Detect medium-model collapse across the campaign.

    python -m tools.medium_collapse --output_root /content/drive/MyDrive/e3dgsuw

The attenuation coefficients are unconstrained parameters, but the forward pass
clamps their *product* with depth:

    beta_d_conv = torch.clamp(conv2d(depth, self.residual_conv_params), 0.0)
                                                    [deepseecolor/models.py:83]

Depth is non-negative, so once a channel's beta_att goes negative the product
clamps to zero, `d(clamp)/d(beta) = 0`, and that channel is **frozen for the
rest of training with no path back**. Its attenuation term becomes
`exp(-0) = 1`: no attenuation modelled, which is SeaSplat's own D-1 "no medium"
degeneracy reached one channel at a time.

Observed first on A2/IUI3-RedSea/s0, where blue crossed zero at the
simplification step itself and green followed 4 500 iterations later, while
beta_bs ran away to 15.8 and saturated the backscatter term into a constant.
The rendered medium-free radiance then has red restored and green and blue not,
which is visible in a splat viewer as a reddish cast -- and is invisible to
PSNR, SSIM and LPIPS, because those score the *composed* image, which the model
can still fit.

This scans every run and reports it, because a per-channel collapse is a
physics failure that the fidelity metrics are structurally unable to show.
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics as st
from collections import defaultdict
from pathlib import Path
from typing import Any, Optional

CHANNELS = ("r", "g", "b")


def read_diagnostics(path: Path) -> dict[int, list[dict]]:
    """{iteration: [rows]}. Multiple rows per iteration: one per medium burst
    step and per view, so callers must aggregate rather than assume one."""
    out: dict[int, list[dict]] = defaultdict(list)
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            for r in csv.DictReader(fh):
                if r.get("beta_att_r"):
                    out[int(r["iteration"])].append(r)
    except (OSError, ValueError, KeyError):
        return {}
    return out


def _f(row: dict, key: str) -> Optional[float]:
    v = row.get(key)
    try:
        return float(v) if v not in (None, "") else None
    except ValueError:
        return None


def analyse(path: Path) -> Optional[dict[str, Any]]:
    d = read_diagnostics(path)
    if not d:
        return None
    its = sorted(d)
    final = d[its[-1]][-1]

    res: dict[str, Any] = {
        "iterations_logged": len(its),
        "final_iteration": its[-1],
        "n_primitives_final": int(float(final["n_primitives"])) if final.get("n_primitives") else None,
        "beta_att_final": {c: _f(final, f"beta_att_{c}") for c in CHANNELS},
        "beta_bs_final": {c: _f(final, f"beta_bs_{c}") for c in CHANNELS},
        "binf_final": {c: _f(final, f"binf_{c}") for c in CHANNELS},
        "collapsed": [],
        "first_negative": {},
        "frozen": {},
    }

    for c in CHANNELS:
        key = f"beta_att_{c}"
        first = next((it for it in its if (v := _f(d[it][-1], key)) is not None and v < 0), None)
        res["first_negative"][c] = first
        if first is None:
            continue
        res["collapsed"].append(c)

        # Frozen means literally one distinct value after going negative --
        # the signature of a dead gradient rather than a slow drift.
        after = [v for it in its if it >= first
                 and (v := _f(d[it][-1], key)) is not None]
        res["frozen"][c] = len(set(after)) == 1 and len(after) > 1

    # Largest single-step drop in mean attenuation, and where. A simplification
    # event shows up here as a step, not a slope.
    means = []
    for it in its:
        vals = [v for c in CHANNELS if (v := _f(d[it][-1], f"beta_att_{c}")) is not None]
        if vals:
            means.append((it, sum(vals) / len(vals)))
    drop_at, drop_frac = None, 0.0
    for (i0, m0), (i1, m1) in zip(means, means[1:]):
        if m0 > 1e-6:
            frac = (m0 - m1) / m0
            if frac > drop_frac:
                drop_frac, drop_at = frac, (i0, i1)
    res["largest_drop"] = {"between": drop_at, "fraction": round(drop_frac, 4)}

    # Backscatter runaway: beta_bs so large that exp(-beta*Z) ~ 0 for Z in
    # [0,1], which saturates the backscatter term into a constant colour.
    bs = [v for c in CHANNELS if (v := res["beta_bs_final"][c]) is not None]
    res["bs_saturated"] = bool(bs) and min(bs) > 5.0

    # CD-27: the cross-frame depth-range dispersion across each simplification
    # boundary.  The prediction under test is that collapse tracks the CHANGE
    # in this dispersion rather than the change in primitive count -- beta is
    # fitted against a per-frame renormalisation, so it follows the spread of
    # the per-frame ranges, and a distribution that merely translates leaves
    # its compromise attainable while one that broadens does not.
    #
    # Read here rather than left in the CSV because an instrument is not
    # finished until something reads it (the CD-24 lesson).  Absent on runs
    # predating the instrument, which is reported as absent, never as zero.
    swept = [(it, r) for it in its for r in d[it]
             if _f(r, "zr_cv") is not None and r.get("event") in
             ("pre_simp", "post_simp", "rewarm_end")]
    res["zr"] = [
        {
            "iteration": it,
            "event": r.get("event"),
            "n_views": int(float(r["zr_n_views"])) if r.get("zr_n_views") else None,
            "cv": _f(r, "zr_cv"),
            "mean": _f(r, "zr_mean"),
        }
        for it, r in swept
    ]

    # Pair each pre_simp with the post_simp that follows it, and report the
    # ratio of dispersions.  > 1 means the population change broadened the
    # distribution, which is the predicted precondition for collapse.
    res["zr_cv_ratio"] = []
    for i, a in enumerate(res["zr"]):
        if a["event"] != "pre_simp":
            continue
        b = next((x for x in res["zr"][i + 1:] if x["event"] == "post_simp"), None)
        if b and a["cv"] and a["cv"] > 0:
            res["zr_cv_ratio"].append({
                "at": a["iteration"],
                "cv_before": round(a["cv"], 6),
                "cv_after": round(b["cv"], 6),
                "ratio": round(b["cv"] / a["cv"], 4),
            })

    return res


def main() -> int:
    ap = argparse.ArgumentParser(description="detect medium-model collapse")
    ap.add_argument("--output_root", required=True)
    ap.add_argument("--json", default=None, help="write the full report here")
    args = ap.parse_args()

    runs_dir = Path(args.output_root) / "runs"
    if not runs_dir.is_dir():
        raise SystemExit(f"no runs/ under {args.output_root}")

    report: dict[str, Any] = {}
    for csv_path in sorted(runs_dir.glob("*/*/*/diagnostics.csv")):
        if "_archive" in csv_path.parts:
            continue
        rid = "/".join(csv_path.parts[-4:-1])
        r = analyse(csv_path)
        if r:
            report[rid] = r

    if not report:
        print("no diagnostics found")
        return 1

    print(f"{'run':<34} {'n_prim':>10} {'att R':>8} {'att G':>8} {'att B':>8} "
          f"{'bs max':>8}  collapse")
    print("-" * 96)
    n_bad = 0
    for rid, r in report.items():
        a = r["beta_att_final"]
        bs = [v for v in r["beta_bs_final"].values() if v is not None]
        flags = []
        for c in r["collapsed"]:
            flags.append(f"{c.upper()}{'(frozen)' if r['frozen'].get(c) else ''}")
        if r["bs_saturated"]:
            flags.append("bs-saturated")
        if flags:
            n_bad += 1
        print(f"{rid:<34} {r['n_primitives_final'] or 0:>10,} "
              + " ".join(f"{a[c]:>8.4f}" if a[c] is not None else f"{'-':>8}" for c in CHANNELS)
              + f" {max(bs) if bs else 0:>8.2f}  {', '.join(flags) or 'ok'}")

    print("-" * 96)
    print(f"{n_bad} of {len(report)} runs show a collapsed channel or saturated backscatter")

    if n_bad:
        print("\nlargest single-step attenuation drop, for affected runs:")
        for rid, r in report.items():
            if not (r["collapsed"] or r["bs_saturated"]):
                continue
            d = r["largest_drop"]
            where = f"{d['between'][0]} -> {d['between'][1]}" if d["between"] else "-"
            print(f"  {rid:<34} {100 * d['fraction']:>5.1f}%  at {where}")
        print("\nA drop coincident with simp_iteration1/2 is the signature of\n"
              "simplification perturbing medium identifiability (H4), not of drift.")

    # CD-27.  The prediction: collapse tracks the change in cross-frame
    # dispersion of the depth range, not the change in primitive count.  A run
    # predating the instrument reports nothing here rather than a zero.
    swept = {rid: r for rid, r in report.items() if r.get("zr_cv_ratio")}
    if swept:
        print("\ncross-frame depth-range dispersion across each simplification event:")
        print(f"  {'run':<34} {'at':>6} {'cv before':>10} {'cv after':>10} "
              f"{'ratio':>7}  collapsed")
        print("  " + "-" * 78)
        for rid, r in swept.items():
            bad = bool(r["collapsed"] or r["bs_saturated"])
            for e in r["zr_cv_ratio"]:
                print(f"  {rid:<34} {e['at']:>6} {e['cv_before']:>10.4f} "
                      f"{e['cv_after']:>10.4f} {e['ratio']:>7.3f}  "
                      f"{'yes' if bad else 'no'}")
        print("\nThe prediction is that ratio > 1 -- a distribution that BROADENED --\n"
              "separates the collapsed runs from the intact ones. A distribution that\n"
              "merely translates leaves beta's compromise attainable. If ratio does\n"
              "not separate them, the identifiability account in\n"
              "08-supervisory-review is wrong and should be withdrawn rather than\n"
              "qualified.")
    elif report:
        print(f"\n[CD-27] no cross-frame sweep in any of {len(report)} runs -- they\n"
              "        predate the instrument. The dispersion prediction cannot be\n"
              "        tested on them, which is why it is reported as untested\n"
              "        rather than as unsupported.")

    if args.json:
        Path(args.json).write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"\nwritten: {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
