"""Measure whether A0 and vanilla SeaSplat are distinguishable.

    python -m tools.replicate_baseline --data_root /content/data \
        --ref_root /content/seasplat_ref --out /content/replication --repeats 3

Why this exists.  The 6x density gap between A0 and vanilla was chased through
four hypotheses using one run per side.  Two of them were closed (CD-22, CD-23)
and the count moved 636k -> 3.0M -> 4.5M.  Then a second reference run came
back at 4.09M against the first one's 4.79M, and a second run of *our*
unchanged code came back at 4.51M against 3.03M.

    reference   {4,788,960, 4,085,219}   17% spread, GPU draws unseeded
    ours        {3,025,374, 4,510,298}   49% spread, despite seeding both

So `n_primitives` is a high-variance outcome and the residual ratio we were
still chasing sat inside its noise.  The rasterizer backward accumulates
atomically, which is non-deterministic whatever the seed; densification then
amplifies it, because a primitive that lands either side of
`densify_grad_threshold` changes the population that feeds the next event, 144
times over.  That is the same compounding that turned a 2% per-event rate
difference into 6x.

This runs both implementations `--repeats` times on one scene and reports the
two distributions, so the question "are A0 and SeaSplat distinguishable" is
answered against the spread rather than against a single pair of numbers.

Deliberately NOT routed through the ledger: these are replication runs on one
scene, not campaign cells, and recording them as cells would put a truncated,
single-scene measurement into the results table.
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

IMPL = Path(__file__).resolve().parent.parent
DENSIFY = re.compile(r"\[densify\].*?after=(\d+)")


def final_count(log: str) -> Optional[int]:
    """Last `after=` from the densification breakdown.

    Read from the log rather than from the .ply, because seed != 0 runs no
    longer write one, and rather than from diagnostics.csv, because the
    reference does not produce one.
    """
    hits = DENSIFY.findall(log)
    return int(hits[-1]) if hits else None


def run(cmd: list[str], cwd: Path, log_path: Path) -> tuple[int, str]:
    t0 = time.time()
    proc = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True)
    out = proc.stdout + proc.stderr
    log_path.write_text(out, encoding="utf-8", errors="replace")
    print(f"      exit={proc.returncode}  {(time.time() - t0) / 60:.1f} min  -> {log_path.name}")
    return proc.returncode, out


def ours_cmd(scene: Path, iters: int, seed: int, out: Path) -> list[str]:
    return [
        sys.executable, str(IMPL / "train.py"),
        "-s", str(scene), "--images", "images",
        "--model_path", str(out), "--cell", "A0", "--seed", str(seed),
        "--iterations", str(iters),
        "--test_iterations", str(iters),
        "--save_iterations", str(iters),
        "--checkpoint_iterations", str(iters),
    ]


def ref_cmd(ref_root: Path, scene: Path, iters: int, seed: int, tag: str) -> list[str]:
    return [
        sys.executable, str(ref_root / "train.py"),
        "-s", str(scene), "--images", "images", "--exp", tag,
        "--iterations", str(iters), "--do_seathru",
        "--seathru_from_iter", "10000", "--eval", "--seed", str(seed),
        "--test_iterations", str(iters),
        "--save_iterations", str(iters),
        "--checkpoint_iterations", str(iters),
    ]


def summarise(name: str, xs: list[int]) -> dict:
    if not xs:
        return {"name": name, "n": 0}
    d = {
        "name": name, "n": len(xs), "runs": xs,
        "mean": statistics.mean(xs), "median": statistics.median(xs),
        "min": min(xs), "max": max(xs),
        "sd": statistics.stdev(xs) if len(xs) > 1 else None,
    }
    d["spread_pct"] = 100.0 * (d["max"] - d["min"]) / d["mean"]
    return d


def main() -> int:
    ap = argparse.ArgumentParser(description="replicate A0 and vanilla SeaSplat")
    ap.add_argument("--data_root", required=True, help="staged undistorted scenes")
    ap.add_argument("--ref_root", required=True, help="vanilla SeaSplat checkout")
    ap.add_argument("--out", required=True, help="where logs and the summary go")
    ap.add_argument("--scene", default="Curasao")
    ap.add_argument("--repeats", type=int, default=3)
    ap.add_argument("--iterations", type=int, default=16000,
                    help="past densify_until_iter, so the count is converged")
    ap.add_argument("--seeds", nargs="+", type=int, default=None,
                    help="one per repeat; default is 0..repeats-1. Vanilla "
                         "accepts --seed but seeds only the CPU generator, so "
                         "its GPU draws vary regardless -- which is the point.")
    ap.add_argument("--skip_ours", action="store_true")
    ap.add_argument("--skip_ref", action="store_true")
    args = ap.parse_args()

    scene = Path(args.data_root) / args.scene
    if not (scene / "sparse" / "0" / "cameras.bin").exists():
        raise SystemExit(f"no COLMAP reconstruction under {scene} -- stage the data first")
    ref_root = Path(args.ref_root)
    if not (ref_root / "train.py").exists():
        raise SystemExit(f"no train.py under {ref_root}")

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    seeds = args.seeds or list(range(args.repeats))
    if len(seeds) < args.repeats:
        raise SystemExit(f"need {args.repeats} seeds, got {len(seeds)}")

    results: dict[str, list[int]] = {"ours": [], "ref": []}
    failures: list[str] = []

    for i in range(args.repeats):
        seed = seeds[i]
        if not args.skip_ours:
            print(f"\n[{i + 1}/{args.repeats}] ours   seed={seed}")
            code, log = run(ours_cmd(scene, args.iterations, seed, out / f"ours_s{seed}"),
                            IMPL, out / f"ours_s{seed}.log")
            n = final_count(log)
            if code == 0 and n:
                results["ours"].append(n)
                print(f"      final n_primitives = {n:,}")
            else:
                failures.append(f"ours seed={seed} exit={code} n={n}")

        if not args.skip_ref:
            print(f"\n[{i + 1}/{args.repeats}] ref    seed={seed}")
            code, log = run(ref_cmd(ref_root, scene, args.iterations, seed, f"rep_s{seed}"),
                            ref_root, out / f"ref_s{seed}.log")
            n = final_count(log)
            if code == 0 and n:
                results["ref"].append(n)
                print(f"      final n_primitives = {n:,}")
            else:
                failures.append(f"ref seed={seed} exit={code} n={n}")

    a = summarise("ours (A0)", results["ours"])
    b = summarise("vanilla SeaSplat", results["ref"])

    print("\n" + "=" * 70)
    print(f"{args.scene}, {args.iterations} iterations, {args.repeats} repeats")
    print("=" * 70)
    for d in (a, b):
        if not d["n"]:
            print(f"  {d['name']:<20} no successful runs")
            continue
        sd = f"{d['sd']:>12,.0f}" if d["sd"] is not None else f"{'-':>12}"
        print(f"  {d['name']:<20} n={d['n']}  mean={d['mean']:>12,.0f}  sd={sd}"
              f"  range=[{d['min']:,} .. {d['max']:,}]  spread={d['spread_pct']:.1f}%")
        print(f"  {'':<20} runs: {', '.join(f'{x:,}' for x in d['runs'])}")

    verdict = "UNDETERMINED"
    if a["n"] and b["n"]:
        overlap = a["min"] <= b["max"] and b["min"] <= a["max"]
        ratio = a["mean"] / b["mean"]
        print(f"\n  mean ratio ours/ref = {ratio:.3f}")
        print(f"  ranges overlap      = {overlap}")
        if a["n"] < 2 or b["n"] < 2:
            print("\n  Fewer than two runs on a side: no dispersion, so no verdict.")
        elif overlap:
            verdict = "INDISTINGUISHABLE"
            print("\n  VERDICT: the ranges overlap. On this evidence A0 and vanilla")
            print("  SeaSplat are not distinguishable by primitive count, and the")
            print("  residual ratio chased earlier was inside the noise.")
        else:
            verdict = "DISTINGUISHABLE"
            print("\n  VERDICT: the ranges are disjoint. A real difference remains;")
            print("  the per-event breakdown is where to look for it next.")
        print("\n  Note: n=3 per side gives a very rough spread. Treat this as")
        print("  'are they in the same regime', not as a significance test.")

    (out / "replication.json").write_text(
        json.dumps({"scene": args.scene, "iterations": args.iterations,
                    "seeds": seeds[:args.repeats], "ours": a, "ref": b,
                    "verdict": verdict, "failures": failures}, indent=2),
        encoding="utf-8")
    print(f"\n  written: {out / 'replication.json'}")
    if failures:
        print("\n  FAILURES:")
        for f in failures:
            print(f"    {f}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
