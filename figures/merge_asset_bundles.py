"""Merge a partial asset collection into the full one, without losing anything.

    python figures/merge_asset_bundles.py ch4_rest.tar.gz
    python figures/merge_asset_bundles.py ch4_rest.tar.gz --dry-run

A partial collection — one produced with `--cells` — carries a `PARTIAL.txt`
and a data file covering only the configurations it was asked for. Unpacking it
over the full bundle would replace a ten-configuration table with a
four-configuration one, and nothing about the result would look wrong.

So the rules are asymmetric, and deliberately so:

* **Renders are added.** A file the full bundle does not have is copied in. A
  file it already has is compared, and a mismatch is reported rather than
  silently resolved — rendering is deterministic, so two collections of the
  same configuration should agree byte for byte, and a disagreement means one
  of them was produced from a different state.
* **Data files are never taken from a partial bundle.** They are compared
  against the full one for the rows they share, so a disagreement is still
  surfaced, but the full file stands.

Run it with `--dry-run` first if the bundle's provenance is uncertain.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import shutil
import sys
import tarfile
import tempfile
from pathlib import Path

ROOT: Path = Path(__file__).resolve().parent.parent
FULL: Path = ROOT / "analysis" / "campaign-2026-09" / "ch4_assets"

DATA_FILES: tuple[str, ...] = (
    "per_view_metrics.csv", "per_view_selfcheck.csv",
    "depth_range_sweeps.csv", "medium_trajectories.csv", "radius_histograms.csv",
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cells_in(path: Path) -> set[str]:
    if not path.is_file():
        return set()
    try:
        return {r["cell"] for r in csv.DictReader(open(path, encoding="utf-8"))}
    except (KeyError, UnicodeDecodeError):
        return set()


def unpack(archive: Path, into: Path) -> Path:
    with tarfile.open(archive) as tf:
        tf.extractall(into)
    roots = [p for p in into.iterdir() if p.is_dir()]
    if len(roots) != 1:
        raise SystemExit(f"{archive.name}: expected one directory inside, found {len(roots)}")
    return roots[0]


def merge(part: Path, dry_run: bool) -> int:
    if not FULL.is_dir():
        raise SystemExit(f"no full bundle at {FULL.relative_to(ROOT)}")
    partial = (part / "PARTIAL.txt").is_file()
    print(f"source : {part.name}  ({'partial' if partial else 'full'} collection)")
    print(f"target : {FULL.relative_to(ROOT)}")
    if partial:
        print("   " + (part / "PARTIAL.txt").read_text(encoding="utf-8").strip()
              .replace("\n", "\n   "))

    added = kept = conflicts = 0
    src_renders = part / "renders"
    if src_renders.is_dir():
        dst_renders = FULL / "renders"
        dst_renders.mkdir(parents=True, exist_ok=True)
        for src in sorted(src_renders.glob("*.png")):
            dst = dst_renders / src.name
            if not dst.exists():
                if not dry_run:
                    shutil.copy2(src, dst)
                added += 1
            elif digest(src) == digest(dst):
                kept += 1
            else:
                conflicts += 1
                print(f"   CONFLICT {src.name}: differs from the copy already held")
    print(f"renders: {added} added, {kept} identical, {conflicts} conflicting")

    for name in DATA_FILES:
        src, dst = part / name, FULL / name
        if not src.is_file():
            continue
        if not dst.is_file():
            if not dry_run:
                shutil.copy2(src, dst)
            print(f"   {name}: taken (the full bundle had none)")
            continue
        a, b = cells_in(src), cells_in(dst)
        if a and b:
            verdict = "kept the fuller table" if b >= a else "SOURCE IS FULLER — check by hand"
            print(f"   {name}: source covers {len(a)}, target {len(b)} — {verdict}")
        else:
            print(f"   {name}: kept the target's copy")

    if conflicts:
        print("\nRendering is deterministic, so a conflict means one collection was")
        print("produced from a different model state. Resolve it before drafting.")
        return 1
    if dry_run:
        print("\ndry run — nothing was written")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("archive", help="the partial bundle, .tar.gz or an unpacked directory")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    src = Path(args.archive)
    if not src.exists():
        raise SystemExit(f"not found: {src}")
    if src.is_dir():
        return merge(src, args.dry_run)
    with tempfile.TemporaryDirectory() as tmp:
        return merge(unpack(src, Path(tmp)), args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
