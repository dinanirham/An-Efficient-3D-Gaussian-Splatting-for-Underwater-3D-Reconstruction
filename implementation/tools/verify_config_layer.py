"""M2 acceptance test for the configuration layer (CD-1). CPU-only.

    python -m tools.verify_config_layer

Checks the two things the 2^3 matrix cannot run without:

  1. Boolean options that default to True can actually be turned off.
     Upstream registered every bool with action="store_true", so roughly a
     dozen True-defaulting flags were unclearable from the command line and
     the matrix could not be configured without editing source between cells.

  2. Resolution order is  code defaults < cell file < command line.
     If the cell file were to win over an explicit argument, a run could
     silently disagree with what the operator asked for.

Deliberately imports nothing that needs a GPU, so it runs anywhere.
"""

from __future__ import annotations

import sys
from argparse import ArgumentParser

from arguments import (
    ModelParams,
    OptimizationParams,
    PipelineParams,
    add_cell_argument,
    apply_cell_config,
    load_cells,
)

_results: list[tuple[str, bool, str]] = []


def check(name: str, fn) -> None:
    try:
        ok, detail = fn()
    except Exception as exc:  # noqa: BLE001
        ok, detail = False, f"raised {type(exc).__name__}: {exc}"
    _results.append((name, ok, detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")


def build(argv: list[str]):
    """Parse `argv` exactly as train.py does."""
    parser = ArgumentParser()
    lp = ModelParams(parser)
    op = OptimizationParams(parser)
    PipelineParams(parser)
    parser.add_argument("--seed", type=int, default=-1)
    add_cell_argument(parser)

    saved, sys.argv = sys.argv, ["train.py", *argv]
    try:
        cell_name, cell_values = apply_cell_config(parser)
        args = parser.parse_args(argv)
    finally:
        sys.argv = saved
    return args, cell_name, cell_values, lp, op


def t1_cells_complete():
    cells = load_cells()["cells"]
    want = {f"A{i}" for i in range(8)}
    got = set(cells)
    missing = want - got
    flags = {
        n: (c["set"]["m1_dense_init"], c["set"]["m2_simplify"], c["set"]["m3_quantize"])
        for n, c in cells.items()
    }
    distinct = len(set(flags.values())) == 8
    return (not missing and distinct), f"{len(got)} cells, all flag triples distinct={distinct}"


def t2_cell_applies():
    args, name, _, _, _ = build(["--cell", "A4"])
    ok = (
        name == "A4"
        and args.m1_dense_init is True
        and args.m2_simplify is True
        and args.m3_quantize is False
        and args.eval is True
        and args.do_seathru is True
        and args.seathru_from_iter == 10000
    )
    return ok, (
        f"m1={args.m1_dense_init} m2={args.m2_simplify} m3={args.m3_quantize} "
        f"eval={args.eval} do_seathru={args.do_seathru} "
        f"seathru_from_iter={args.seathru_from_iter}"
    )


def t3_cli_beats_cell():
    args, _, _, _, _ = build(["--cell", "A4", "--no-m2_simplify"])
    ok = args.m1_dense_init is True and args.m2_simplify is False
    return ok, f"A4 with --no-m2_simplify -> m1={args.m1_dense_init} m2={args.m2_simplify}"


def t4_true_bools_clearable():
    """The store_true fix: every True-defaulting bool must be clearable."""
    parser = ArgumentParser()
    op = OptimizationParams(parser)
    defaults_true = [
        k for k, v in vars(op).items()
        if isinstance(v, bool) and v is True and not k.startswith("_")
    ]
    if not defaults_true:
        return False, "no True-defaulting bools found; test would be vacuous"

    argv = [f"--no-{k}" for k in defaults_true]
    args = parser.parse_args(argv)
    still_true = [k for k in defaults_true if getattr(args, k) is not False]
    return not still_true, (
        f"{len(defaults_true)} True-defaulting bools, all cleared"
        if not still_true else f"could not clear: {still_true}"
    )


def t5_bool_default_preserved():
    """Not passing a flag must leave its default intact, in both directions."""
    args, _, _, _, _ = build([])
    ok = args.learn_background is True and args.do_seathru is False
    return ok, f"learn_background={args.learn_background} do_seathru={args.do_seathru}"


def t6_unknown_cell_rejected():
    try:
        build(["--cell", "A9"])
    except SystemExit as exc:
        return "unknown cell" in str(exc), f"rejected: {str(exc).splitlines()[0][:70]}"
    return False, "an unknown cell was accepted"


def main() -> int:
    check("T1 all eight cells present and distinct", t1_cells_complete)
    check("T2 --cell applies flags and shared defaults", t2_cell_applies)
    check("T3 command line overrides the cell file", t3_cli_beats_cell)
    check("T4 True-defaulting bools are clearable  <-- the CD-1 fix", t4_true_bools_clearable)
    check("T5 unpassed bools keep their defaults", t5_bool_default_preserved)
    check("T6 unknown cell is rejected", t6_unknown_cell_rejected)

    failed = [n for n, ok, _ in _results if not ok]
    print("\n" + "=" * 68)
    if failed:
        print(f"M2 CONFIG LAYER: FAILED ({len(failed)}/{len(_results)})")
        for n in failed:
            print(f"  - {n}")
        return 1
    print(f"M2 CONFIG LAYER: PASSED ({len(_results)}/{len(_results)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
