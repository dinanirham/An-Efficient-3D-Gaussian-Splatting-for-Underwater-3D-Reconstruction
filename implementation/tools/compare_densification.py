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
    # Opacity distribution, added after the CD-23 run localised the residual to
    # the first densification following an opacity reset. Optional, so logs
    # written before the instrumentation still parse instead of silently
    # yielding zero events.
    r"(?:\s+op_p05=(?P<op_p05>[\d.]+)\s+op_p25=(?P<op_p25>[\d.]+)"
    r"\s+op_med=(?P<op_med>[\d.]+)\s+op_lt01=(?P<op_lt01>[\d.]+)%)?"
)

FIELDS = ("before", "over", "clone", "split", "prune", "alpha", "screen", "world", "after")
OPACITY = ("op_p05", "op_p25", "op_med", "op_lt01")

# The noise floor, measured. tools/replicate_baseline puts the run-to-run
# spread of the converged count at ~21% for both implementations, so a per-event
# difference below this says nothing, and one that does not persist says little
# more. Without these two, this tool reported 1.001 as a divergence.
TOLERANCE = 0.20
RUN_LENGTH = 3
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
        for k in OPACITY:
            if m.group(k) is not None:
                d[k] = float(m.group(k))
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

    # 1. First MATERIAL divergence, per quantity.
    #
    # Exact inequality is useless here. Replication puts the run-to-run spread
    # of the final count at ~21% on both implementations, so two runs differing
    # by 3,357 against 3,353 at iteration 600 -- a ratio of 1.001 -- is noise
    # being reported as a finding. That is how a single paired run showed 0.68x
    # for two implementations the replication then called indistinguishable.
    #
    # A divergence is only interesting if it is large enough to survive that
    # floor, and only if it persists: one loud event proves nothing, three
    # consecutive ones are a trend.
    print(f"first material divergence  (>{TOLERANCE:.0%}, sustained "
          f"{RUN_LENGTH} consecutive events)")
    print(f"  {'quantity':<10} {'iter':>7} {'ours':>10} {'ref':>10}  ratio")
    verdicts: list[str] = []
    for f in ("over", "clone", "split", "prune", "alpha", "screen", "world"):
        run_start: Optional[int] = None
        run_len = 0
        first: Optional[int] = None
        for it in common:
            a, b = ours[it][f], ref[it][f]
            big = max(a, b)
            diverged = big > 0 and abs(a - b) / big > TOLERANCE
            if diverged:
                run_start = it if run_len == 0 else run_start
                run_len += 1
                if run_len >= RUN_LENGTH:
                    first = run_start
                    break
            else:
                run_len = 0
        if first is None:
            print(f"  {f:<10} {'-':>7} {'within tolerance throughout':>22}")
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

    # 4. Opacity distribution. After CD-23 the residual traced to the first
    #    densification following an opacity reset -- upstream pruned 214,311
    #    there against our 135,915 -- and reset_opacity is byte-identical on
    #    both sides. So the question is not the reset but the distribution it
    #    acts on, and how far it drifts in the 100 steps before the prune.
    if all("op_med" in ours[it] and "op_med" in ref[it] for it in common):
        print("\nopacity distribution  (reset fires every 3000 iterations)")
        print(f"  {'iter':>7} {'ours med':>9} {'ref med':>9} "
              f"{'ours <0.01':>11} {'ref <0.01':>10}")
        for it in common:
            if it % 1000 and it not in (3100, 6100, 9100, 12100, common[-1]):
                continue
            o, r = ours[it], ref[it]
            mark = "  <-- first prune after reset" if it in (3100, 6100, 9100, 12100) else ""
            print(f"  {it:>7} {o['op_med']:>9.5f} {r['op_med']:>9.5f} "
                  f"{o['op_lt01']:>10.2f}% {r['op_lt01']:>9.2f}%{mark}")
    else:
        print("\n(no opacity fields -- logs predate that instrumentation)")

    print("\n" + "=" * 70)
    if not verdicts:
        print("VERDICT: no material divergence at any aligned event.")
        print("  The two densify the same way to within the measured noise")
        print("  floor. If their final counts still differ, that difference is")
        print("  not evidence on its own -- run tools/replicate_baseline and")
        print("  compare distributions, not a single pair.")
    else:
        print(f"VERDICT: sustained divergence in -> {', '.join(verdicts)}")
        print("  This is a single pair of runs. It says WHERE they differ, not")
        print("  WHETHER they do; replicate_baseline answers whether.")
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
