"""Align the two densification event streams and find where they diverge.

    python -m tools.compare_densification diag_ours.txt diag_ref.txt

Both trees print one line per densification event:

    [densify] it=600 before=25837 over_grad=812 (3.1%) clone=+509 split=+180
              prune=-96 (alpha=91 screen=4 world=1) after=26430

Ours labels events by iteration, the reference by event index; both fire every
`densification_interval` from `densify_from_iter`, so event N there is
iteration 500 + 100N here and the streams align one to one.

The point is to find the *first* event where the two disagree, and on which
quantity, because that names the mechanism:

    over_grad differs   -> the densification signal differs, even though the
                           rasterizer is byte-identical on identical inputs;
                           so what is fed to it differs
    clone/split differ
    at equal over_grad  -> the clone-vs-split decision differs: `extent`,
                           `percent_dense`, or the scaling distribution
    prune differs       -> and the alpha/screen/world split says which of the
                           three reasons

Endpoint comparison cannot do this. Vanilla grows 6.7x between iterations 5000
and 15000, which over 100 events is ~1.9% growth apiece -- a difference far too
small to see on a trajectory, and silent about which mechanism produced it.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Optional

LINE = re.compile(
    r"\[densify\]\s+(?:it|ev)=(?P<key>\d+)\s+"
    r"before=(?P<before>\d+)\s+"
    r"over_grad=(?P<over>\d+)\s+\([\d.]+%\)\s+"
    r"clone=\+(?P<clone>\d+)\s+split=\+(?P<split>\d+)\s+"
    r"prune=-(?P<prune>\d+)\s+"
    r"\(alpha=(?P<alpha>\d+)\s+screen=(?P<screen>\d+)\s+world=(?P<world>\d+)\)\s+"
    r"after=(?P<after>\d+)"
)

FIELDS = ("before", "over", "clone", "split", "prune", "alpha", "screen", "world", "after")
DENSIFY_FROM_ITER = 500
DENSIFICATION_INTERVAL = 100


def parse(path: Path) -> dict[int, dict[str, int]]:
    """Return {iteration: counts}. Event indices are mapped to iterations."""
    out: dict[int, dict[str, int]] = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        m = LINE.search(line)          # search, not match: tqdm prepends its bar
        if not m:
            continue
        d = {k: int(m.group(k)) for k in FIELDS}
        key = int(m.group("key"))
        # An event index is small and monotonic from 1; an iteration is >= 600.
        it = key if key >= DENSIFY_FROM_ITER else DENSIFY_FROM_ITER + DENSIFICATION_INTERVAL * key
        out[it] = d
    return out


def pct(a: int, b: int) -> str:
    return "-" if b == 0 else f"{100.0 * a / b:5.1f}%"


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    ours, ref = parse(Path(sys.argv[1])), parse(Path(sys.argv[2]))
    if not ours or not ref:
        print(f"FATAL: parsed {len(ours)} events from ours, {len(ref)} from ref.\n"
              "Check the logs actually contain [densify] lines -- if the grep used\n"
              "a '^' anchor it discarded them, because tqdm's progress bar leaves\n"
              "the line without a leading newline.")
        return 2

    common = sorted(set(ours) & set(ref))
    print(f"ours: {len(ours)} events   ref: {len(ref)} events   aligned: {len(common)}\n")

    # 1. First divergence, per quantity. This is the whole answer.
    print("first divergence by quantity")
    print(f"  {'quantity':<10} {'iter':>7} {'ours':>10} {'ref':>10}  ratio")
    verdicts: list[str] = []
    for f in ("over", "clone", "split", "prune", "alpha", "screen", "world"):
        first: Optional[int] = next(
            (it for it in common if ours[it][f] != ref[it][f]), None
        )
        if first is None:
            print(f"  {f:<10} {'-':>7} {'identical throughout':>22}")
            continue
        a, b = ours[first][f], ref[first][f]
        r = "inf" if b == 0 else f"{a / b:.3f}"
        print(f"  {f:<10} {first:>7} {a:>10,} {b:>10,}  {r}")
        verdicts.append(f)

    # 2. Cumulative totals -- where the primitives actually went.
    print("\ncumulative over aligned events")
    print(f"  {'quantity':<10} {'ours':>14} {'ref':>14}  ours/ref")
    for f in ("over", "clone", "split", "prune", "alpha", "screen", "world"):
        a = sum(ours[it][f] for it in common)
        b = sum(ref[it][f] for it in common)
        r = "-" if b == 0 else f"{a / b:.3f}"
        print(f"  {f:<10} {a:>14,} {b:>14,}  {r:>8}")

    # 3. The trajectory itself, sampled.
    print("\ntrajectory (after each event, sampled)")
    print(f"  {'iter':>7} {'ours':>12} {'ref':>12}  {'ratio':>7}   "
          f"{'ours +/-':>16}  {'ref +/-':>16}")
    for it in common:
        if it % 1000 not in (0, 600 % 1000) and it != common[-1]:
            continue
        o, r = ours[it], ref[it]
        net_o = o["clone"] + o["split"] - o["prune"]
        net_r = r["clone"] + r["split"] - r["prune"]
        print(f"  {it:>7} {o['after']:>12,} {r['after']:>12,}  "
              f"{o['after'] / max(1, r['after']):>7.3f}   "
              f"{net_o:>+8,} ({pct(o['over'], o['before'])}) "
              f"{net_r:>+8,} ({pct(r['over'], r['before'])})")

    print("\n" + "=" * 70)
    if not verdicts:
        print("VERDICT: the two densify identically at every aligned event.")
        print("  Whatever separates the final counts is NOT in densify_and_prune.")
        print("  Next suspect: reset_opacity, or the optimiser state it acts on.")
    else:
        print(f"VERDICT: first quantities to diverge -> {', '.join(verdicts)}")
        if "over" in verdicts:
            print("  The gradient signal differs. The rasterizer is identical on")
            print("  identical inputs, so the inputs differ -- look at what reaches")
            print("  add_densification_stats, and at the loss that produced it.")
        elif {"clone", "split"} & set(verdicts):
            print("  Equal over_grad but different clone/split: the decision")
            print("  boundary differs -- cameras_extent or percent_dense.")
        elif {"prune", "alpha", "screen", "world"} & set(verdicts):
            print("  Pruning differs; the alpha/screen/world split names which.")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
