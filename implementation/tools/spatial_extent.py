"""Spatial extent of the primitive cloud, as a geometric test for floaters.

    python -m tools.spatial_extent --output_root /content/drive/MyDrive/e3dgsuw

Every fidelity measure in this study is photometric, and SeaSplat's degeneracy
D-4 -- opaque low-texture primitives placed near the camera to reproduce veiling
haze as geometry -- is photometrically *excellent*. It is visible in the
geometry and nowhere else, so nothing the campaign currently records would
detect it.

A raw min/max bounding box is decided by a handful of outliers, which is
precisely what makes it useful here and also what makes it fragile on its own.
This reports both, and the **ratio** between them:

    full extent      min/max over every primitive -- sensitive to floaters
    robust extent    the 1st-99th percentile box  -- the scene proper
    inflation        full volume / robust volume  -- how much a 2% tail costs

A cloud whose inflation is near 1 has no significant tail. A cloud inflated by
orders of magnitude is being stretched by a small number of distant or
near-camera primitives.

**Opacity gating matters.** A primitive at alpha = 0.001 contributes nothing to
the render and should not enlarge a reported extent, so every measure is also
computed over primitives above a visibility threshold. The gap between gated and
ungated extent is itself informative: a large gap means the tail is invisible
and cosmetic, a small gap means it is being rendered.

PLY fields are read directly. Opacity is stored as a logit and scale as a
logarithm, and both are inverted here -- comparing raw stored values across
cells would be meaningless.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import struct
from pathlib import Path
from typing import Any, Optional

import numpy as np

VISIBLE_ALPHA = 0.05     # below this a primitive is not meaningfully rendered
LO, HI = 1.0, 99.0       # robust-box percentiles


def read_ply_fields(path: Path, wanted: tuple[str, ...]) -> Optional[dict[str, np.ndarray]]:
    """Minimal binary-little-endian PLY reader for the 3DGS layout.

    Written rather than taking a dependency because this must run wherever a
    run's artifacts landed, and because the layout is fixed and small: a flat
    list of float32 (occasionally double) scalar properties on one element.
    """
    try:
        with open(path, "rb") as fh:
            header = b""
            while b"end_header" not in header:
                chunk = fh.readline()
                if not chunk:
                    return None
                header += chunk
            text = header.decode("ascii", errors="replace")

            if "binary_little_endian" not in text:
                return None
            m = re.search(r"element vertex (\d+)", text)
            if not m:
                return None
            n = int(m.group(1))

            props: list[tuple[str, str]] = []
            for line in text.splitlines():
                pm = re.match(r"property\s+(\w+)\s+(\w+)", line)
                if pm:
                    props.append((pm.group(1), pm.group(2)))
            if not props:
                return None

            sizes = {"float": 4, "float32": 4, "double": 8, "float64": 8,
                     "uchar": 1, "uint8": 1, "int": 4, "int32": 4}
            codes = {"float": "f4", "float32": "f4", "double": "f8",
                     "float64": "f8", "uchar": "u1", "uint8": "u1",
                     "int": "i4", "int32": "i4"}
            if any(t not in sizes for t, _ in props):
                return None

            dtype = np.dtype([(name, codes[t]) for t, name in props])
            buf = fh.read(n * dtype.itemsize)
            if len(buf) < n * dtype.itemsize:
                return None
            arr = np.frombuffer(buf, dtype=dtype, count=n)
    except (OSError, ValueError, struct.error):
        return None

    out = {}
    for w in wanted:
        if w in arr.dtype.names:
            out[w] = np.asarray(arr[w], dtype=np.float64)
    return out


def _box(xyz: np.ndarray) -> dict[str, Any]:
    lo, hi = xyz.min(axis=0), xyz.max(axis=0)
    ext = hi - lo
    return {
        "extent_x": ext[0], "extent_y": ext[1], "extent_z": ext[2],
        "volume": float(np.prod(ext)),
        "diagonal": float(np.linalg.norm(ext)),
    }


def _robust_box(xyz: np.ndarray, lo_p: float, hi_p: float) -> dict[str, Any]:
    lo = np.percentile(xyz, lo_p, axis=0)
    hi = np.percentile(xyz, hi_p, axis=0)
    ext = hi - lo
    inside = np.all((xyz >= lo) & (xyz <= hi), axis=1)
    return {
        "extent_x": ext[0], "extent_y": ext[1], "extent_z": ext[2],
        "volume": float(np.prod(ext)),
        "diagonal": float(np.linalg.norm(ext)),
        "frac_inside": float(inside.mean()),
    }


def analyse_ply(path: Path) -> Optional[dict[str, Any]]:
    f = read_ply_fields(path, ("x", "y", "z", "opacity", "scale_0", "scale_1", "scale_2"))
    if not f or "x" not in f:
        return None

    xyz = np.stack([f["x"], f["y"], f["z"]], axis=1)
    n = len(xyz)
    out: dict[str, Any] = {"n_points": n}

    full = _box(xyz)
    rob = _robust_box(xyz, LO, HI)
    out.update({f"full_{k}": v for k, v in full.items()})
    out.update({f"p{int(LO)}_{k}": v for k, v in rob.items()})

    # The headline: how much does the outer 2% of primitives enlarge the box?
    out["inflation_volume"] = (full["volume"] / rob["volume"]
                               if rob["volume"] > 0 else float("inf"))
    out["inflation_diagonal"] = (full["diagonal"] / rob["diagonal"]
                                 if rob["diagonal"] > 0 else float("inf"))

    # Opacity gating. Stored as a logit; a primitive below the visibility
    # threshold contributes nothing to the render and should not enlarge a
    # reported extent.
    if "opacity" in f:
        alpha = 1.0 / (1.0 + np.exp(-f["opacity"]))
        vis = alpha >= VISIBLE_ALPHA
        out["frac_visible"] = float(vis.mean())
        out["alpha_median"] = float(np.median(alpha))
        if vis.sum() >= 10:
            gated = _box(xyz[vis])
            out.update({f"visible_{k}": v for k, v in gated.items()})
            out["invisible_inflation_volume"] = (
                full["volume"] / gated["volume"] if gated["volume"] > 0 else float("inf")
            )

    # Radial spread about the median point: a floater tail shows as a long
    # upper quantile relative to the bulk.
    centre = np.median(xyz, axis=0)
    r = np.linalg.norm(xyz - centre, axis=1)
    for q in (50, 90, 99, 100):
        out[f"radius_p{q}"] = float(np.percentile(r, q))
    out["radius_p100_over_p50"] = (out["radius_p100"] / out["radius_p50"]
                                   if out["radius_p50"] > 0 else float("inf"))

    # Mean primitive size, for context: a smaller population of larger
    # primitives covers the same scene differently.
    if all(k in f for k in ("scale_0", "scale_1", "scale_2")):
        sc = np.exp(np.stack([f["scale_0"], f["scale_1"], f["scale_2"]], axis=1))
        out["scale_median"] = float(np.median(sc))
        out["scale_p99"] = float(np.percentile(sc, 99))

    return out


def find_plys(output_root: Path) -> list[tuple[str, str, int, Path]]:
    found = []
    root = output_root / "runs"
    if not root.is_dir():
        return found
    for cell_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        if cell_dir.name.startswith("_"):
            continue
        for scene_dir in sorted(p for p in cell_dir.iterdir() if p.is_dir()):
            for seed_dir in sorted(p for p in scene_dir.iterdir() if p.is_dir()):
                if not seed_dir.name.startswith("s"):
                    continue
                plys = sorted(seed_dir.glob("point_cloud/iteration_*/point_cloud.ply"))
                if plys:
                    try:
                        seed = int(seed_dir.name[1:])
                    except ValueError:
                        continue
                    found.append((cell_dir.name, scene_dir.name, seed, plys[-1]))
    return found


def main() -> int:
    ap = argparse.ArgumentParser(
        description="bounding-box extent of each stored point cloud")
    ap.add_argument("--output_root", required=True)
    ap.add_argument("--out_dir", default=None, help="default: <output_root>/analysis")
    ap.add_argument("--ply", default=None,
                    help="analyse a single file instead of walking runs/")
    args = ap.parse_args()

    if args.ply:
        r = analyse_ply(Path(args.ply))
        print(json.dumps(r, indent=2, default=float) if r
              else f"could not read {args.ply}")
        return 0 if r else 1

    root = Path(args.output_root)
    out_dir = Path(args.out_dir) if args.out_dir else root / "analysis"
    targets = find_plys(root)
    if not targets:
        print(f"no point_cloud.ply found under {root / 'runs'}")
        print("note: the PLY is written for seed 0 only unless "
              "--save_ply_all_seeds was passed")
        return 1

    rows = []
    for cell, scene, seed, path in targets:
        print(f"  reading {cell}/{scene}/s{seed} ...", flush=True)
        r = analyse_ply(path)
        if r is None:
            print("    unreadable; skipped")
            continue
        rows.append({"cell": cell, "scene": scene, "seed": seed, **r})

    if not rows:
        print("nothing readable")
        return 1

    out_dir.mkdir(parents=True, exist_ok=True)
    fields: list[str] = []
    for r in rows:
        for k in r:
            if k not in fields:
                fields.append(k)
    with open(out_dir / "spatial_extent.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow(r)

    print(f"\n{'run':<34} {'points':>10} {'full diag':>10} {'p1-99 diag':>11} "
          f"{'inflation':>10} {'vis%':>6}")
    print("-" * 86)
    for r in sorted(rows, key=lambda r: (r["scene"], r["cell"], r["seed"])):
        print(f"{r['cell'] + '/' + r['scene'] + '/s' + str(r['seed']):<34} "
              f"{r['n_points']:>10,} {r['full_diagonal']:>10.2f} "
              f"{r['p1_diagonal']:>11.2f} {r['inflation_diagonal']:>9.2f}x "
              f"{100 * r.get('frac_visible', float('nan')):>5.1f}%")

    print(f"\nfull      min/max over every primitive")
    print(f"p1-99     the 1st-99th percentile box -- the scene proper")
    print(f"inflation full diagonal / robust diagonal; near 1 means no tail")
    print(f"vis%      primitives with alpha >= {VISIBLE_ALPHA}")
    print(f"\nwritten: {out_dir / 'spatial_extent.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
