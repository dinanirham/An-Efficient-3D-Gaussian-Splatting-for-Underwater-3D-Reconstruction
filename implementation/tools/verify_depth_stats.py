"""Acceptance test for the cross-frame depth-range instrument (CD-27).

    python -m tools.verify_depth_stats

Runs on CPU with synthetic tensors and a stub renderer.  No GPU, no dataset.

**Why this instrument exists.** The medium coefficients enter the image
formation model only through the product `beta * Z_hat`, and `Z_hat` is the
rendered depth renormalised by *each frame's own* extrema.  Matching the
physical law on frame f therefore requires `beta = beta_phys * (M_f - m_f)`,
whose right-hand side depends on the frame.  A single scene-global `beta`
cannot satisfy that across frames unless the depth range is constant, so the
fitted value is a compromise over the training set's *distribution* of depth
ranges -- and it moves when the distribution moves.

The existing diagnostics record `z_min`/`z_max` from the single view sampled
at that iteration, which is one draw from that distribution rather than a
statistic of it.  The prediction under test -- that collapse tracks the change
in cross-frame *dispersion* -- cannot be evaluated from a single draw.  Hence
this sweep.

**The two decisive checks are T6 and T7.**  T6 fails if the sweep and the
training loop ever compute the normalisation constants by different paths,
which would make the measured range not the one beta is actually fitted
against -- the exact class of error that produced CD-22/CD-23, where every
forward value was correct and only the destination was wrong.  T7 fails if the
sweep perturbs the RNG stream, which would silently make an instrumented run
non-comparable with the runs already completed.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import Any

import torch

sys.path.append(str(Path(__file__).resolve().parent.parent))

from utils.depth_stats import (  # noqa: E402
    DepthRangeStats,
    normalise_depth,
    sweep_depth_ranges,
)

_results: list[tuple[str, bool, str]] = []


def check(name: str, fn) -> None:
    try:
        ok, detail = fn()
    except Exception as exc:  # noqa: BLE001
        ok, detail = False, f"raised {type(exc).__name__}: {exc}"
    _results.append((name, ok, detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")


class StubCam:
    """Carries only an index, so the stub renderer can vary depth per view."""

    def __init__(self, idx: int) -> None:
        self.idx = idx


def make_renderer(ranges: list[tuple[float, float]]):
    """A renderer whose frame `i` has depth spanning exactly ranges[i].

    Alpha is all ones so that the `depth / alpha` step is an identity and the
    test controls the constants exactly.
    """

    def render_depth_fn(cam: StubCam, gaussians: Any, pipe: Any, bg: Any) -> dict:
        lo, hi = ranges[cam.idx]
        depth = torch.linspace(lo, hi, steps=16).reshape(1, 4, 4)
        return {"depth": depth, "alpha": torch.ones_like(depth)}

    return render_depth_fn


# --------------------------------------------------------------------------
# normalise_depth
# --------------------------------------------------------------------------


def t1_filter_off_is_a_passthrough():
    d = torch.tensor([[1.0, 5.0], [3.0, 9.0]])
    a = torch.ones_like(d)
    out, lo, hi = normalise_depth(d, a, normalize_depth=1.0,
                                  filter_depth=False, norm_depth_max=True)
    ok = torch.equal(out, d) and lo is None and hi is None
    return ok, f"depth unchanged, constants None (got {lo}, {hi})"


def t2_constants_are_captured_before_the_rescale():
    # Constants must be the PRE-normalisation extrema.  Afterwards they are
    # 0 and 1 by construction and carry no information at all.
    d = torch.tensor([[2.0, 4.0], [6.0, 10.0]])
    a = torch.ones_like(d)
    out, lo, hi = normalise_depth(d, a, normalize_depth=1.0,
                                  filter_depth=True, norm_depth_max=True)
    ok = (
        math.isclose(lo, 2.0) and math.isclose(hi, 10.0)
        and math.isclose(out.min().item(), 0.0, abs_tol=1e-6)
        and math.isclose(out.max().item(), 1.0, abs_tol=1e-6)
    )
    return ok, f"captured ({lo}, {hi}), output spans [{out.min():.3f}, {out.max():.3f}]"


def t3_normalize_depth_divisor_is_applied_before_capture():
    d = torch.tensor([[4.0, 20.0]])
    a = torch.ones_like(d)
    _, lo, hi = normalise_depth(d, a, normalize_depth=4.0,
                                filter_depth=True, norm_depth_max=True)
    ok = math.isclose(lo, 1.0) and math.isclose(hi, 5.0)
    return ok, f"divisor 4 applied first: ({lo}, {hi}) expected (1.0, 5.0)"


def t4_nan_and_inf_are_replaced_by_the_valid_max():
    d = torch.tensor([[1.0, float("nan")], [3.0, float("inf")]])
    a = torch.ones_like(d)
    out, lo, hi = normalise_depth(d, a, normalize_depth=1.0,
                                  filter_depth=True, norm_depth_max=True)
    finite = bool(torch.isfinite(out).all())
    ok = finite and math.isclose(hi, 3.0) and math.isclose(lo, 1.0)
    return ok, f"all finite={finite}, constants ({lo}, {hi}) expected (1.0, 3.0)"


def t5_all_nan_falls_back_without_raising():
    d = torch.full((2, 2), float("nan"))
    a = torch.ones_like(d)
    out, lo, hi = normalise_depth(d, a, normalize_depth=1.0,
                                  filter_depth=True, norm_depth_max=True)
    ok = bool(torch.isfinite(out).all()) and lo is not None and hi is not None
    return ok, f"fallback applied, constants ({lo}, {hi}), no exception"


def t6_degenerate_frame_does_not_divide_by_zero():
    d = torch.full((2, 2), 7.0)
    a = torch.ones_like(d)
    out, lo, hi = normalise_depth(d, a, normalize_depth=1.0,
                                  filter_depth=True, norm_depth_max=True)
    # Upstream divides by max in this branch rather than leaving the frame
    # alone, so 7 -> 1.  Pinned to the value, not merely to finiteness: a
    # refactor that returned the input unchanged would pass a finiteness check
    # and silently change every degenerate frame in the campaign.
    ok = (
        bool(torch.isfinite(out).all())
        and math.isclose(lo, hi)
        and math.isclose(float(out.reshape(-1)[0].item()), 1.0, rel_tol=1e-6)
    )
    return ok, f"min==max -> depth/max, first element {out.reshape(-1)[0].item():.4f} (want 1.0)"


# --------------------------------------------------------------------------
# the sweep
# --------------------------------------------------------------------------


def t7_sweep_matches_the_training_path_exactly():
    """DECISIVE. One implementation, or the measurement is of the wrong thing."""
    ranges = [(0.0, 4.0), (1.0, 9.0), (2.0, 3.0)]
    cams = [StubCam(i) for i in range(3)]
    rf = make_renderer(ranges)

    stats = sweep_depth_ranges(cams, None, rf, None, None,
                               normalize_depth=1.0, filter_depth=True,
                               norm_depth_max=True)

    # Recompute frame by frame through the same entry point the training loop
    # uses, and require agreement to float equality rather than a tolerance.
    expected: list[float] = []
    for cam in cams:
        pkg = rf(cam, None, None, None)
        _, lo, hi = normalise_depth(pkg["depth"], pkg["alpha"], 1.0, True, True)
        expected.append(hi - lo)

    got = stats.ranges
    ok = len(got) == len(expected) and all(g == e for g, e in zip(got, expected))
    return ok, f"per-frame ranges {[round(x, 4) for x in got]} == training path"


def t8_sweep_leaves_the_rng_stream_untouched():
    """DECISIVE. A sweep that consumes randomness changes the experiment."""
    torch.manual_seed(1234)
    before = torch.random.get_rng_state().clone()

    cams = [StubCam(i) for i in range(4)]
    rf = make_renderer([(0.0, 1.0), (0.0, 2.0), (0.0, 3.0), (0.0, 4.0)])
    sweep_depth_ranges(cams, None, rf, None, None,
                       normalize_depth=1.0, filter_depth=True, norm_depth_max=True)

    after = torch.random.get_rng_state()
    ok = bool(torch.equal(before, after))
    return ok, "RNG state identical before and after the sweep"


def t9_dispersion_statistics_are_correct():
    # Ranges 1, 2, 3, 4 -> mean 2.5, population sd sqrt(1.25) ~ 1.118034
    cams = [StubCam(i) for i in range(4)]
    rf = make_renderer([(0.0, 1.0), (0.0, 2.0), (0.0, 3.0), (0.0, 4.0)])
    st = sweep_depth_ranges(cams, None, rf, None, None,
                            normalize_depth=1.0, filter_depth=True,
                            norm_depth_max=True)
    want_sd = math.sqrt(1.25)
    ok = (
        st.n_views == 4
        and math.isclose(st.range_mean, 2.5, rel_tol=1e-6)
        and math.isclose(st.range_sd, want_sd, rel_tol=1e-6)
        and math.isclose(st.range_min, 1.0, rel_tol=1e-6)
        and math.isclose(st.range_max, 4.0, rel_tol=1e-6)
    )
    return ok, f"mean {st.range_mean:.4f}, sd {st.range_sd:.6f} (want {want_sd:.6f})"


def t10_cv_is_dimensionless_and_scale_invariant():
    """The predicted driver of collapse must not depend on scene units."""
    cams = [StubCam(i) for i in range(4)]
    base = [(0.0, 1.0), (0.0, 2.0), (0.0, 3.0), (0.0, 4.0)]
    scaled = [(lo, hi * 1000.0) for lo, hi in base]

    a = sweep_depth_ranges(cams, None, make_renderer(base), None, None,
                           1.0, True, True)
    b = sweep_depth_ranges(cams, None, make_renderer(scaled), None, None,
                           1.0, True, True)
    ok = math.isclose(a.range_cv, b.range_cv, rel_tol=1e-6) and a.range_cv > 0
    return ok, f"cv {a.range_cv:.6f} == {b.range_cv:.6f} under 1000x rescale"


def t11_no_views_is_empty_not_an_exception():
    st = sweep_depth_ranges([], None, make_renderer([]), None, None,
                            1.0, True, True)
    row = st.as_row()
    ok = st.n_views == 0 and all(v == "" for k, v in row.items() if k != "zr_n_views")
    return ok, "empty sweep yields blank fields rather than zeros"


def t12_row_keys_are_stable_and_blank_when_unmeasured():
    """Blank, never 0.0 -- a zero dispersion is a claim, absence is not."""
    st = DepthRangeStats.empty()
    row = st.as_row()
    ok = set(row) == set(DepthRangeStats.FIELDS) and row["zr_cv"] == ""
    return ok, f"{len(row)} stable fields, unmeasured entries blank"


def t13_gating_off_reports_nothing_rather_than_raw_depth():
    """With norm_depth_max off there is no per-frame renormalisation, so the
    quantity the hypothesis is about does not exist and must not be invented."""
    cams = [StubCam(i) for i in range(3)]
    rf = make_renderer([(0.0, 1.0), (0.0, 2.0), (0.0, 3.0)])
    st = sweep_depth_ranges(cams, None, rf, None, None,
                            normalize_depth=1.0, filter_depth=True,
                            norm_depth_max=False)
    ok = st.n_views == 0
    return ok, "no renormalisation in force -> nothing reported"


def main() -> int:
    print("=" * 68)
    print("CD-27  cross-frame depth-range instrument")
    print("=" * 68)

    check("T1  filter_depth off is a passthrough", t1_filter_off_is_a_passthrough)
    check("T2  constants captured before the rescale",
          t2_constants_are_captured_before_the_rescale)
    check("T3  normalize_depth divisor applied before capture",
          t3_normalize_depth_divisor_is_applied_before_capture)
    check("T4  NaN/Inf replaced by the valid max", t4_nan_and_inf_are_replaced_by_the_valid_max)
    check("T5  all-NaN frame falls back without raising",
          t5_all_nan_falls_back_without_raising)
    check("T6  degenerate frame does not divide by zero",
          t6_degenerate_frame_does_not_divide_by_zero)
    check("T7  sweep matches the training path exactly  <-- decisive",
          t7_sweep_matches_the_training_path_exactly)
    check("T8  sweep leaves the RNG stream untouched  <-- decisive",
          t8_sweep_leaves_the_rng_stream_untouched)
    check("T9  dispersion statistics are correct", t9_dispersion_statistics_are_correct)
    check("T10 cv is dimensionless and scale invariant",
          t10_cv_is_dimensionless_and_scale_invariant)
    check("T11 no views is empty, not an exception", t11_no_views_is_empty_not_an_exception)
    check("T12 row keys stable, unmeasured blank", t12_row_keys_are_stable_and_blank_when_unmeasured)
    check("T13 no renormalisation -> nothing reported",
          t13_gating_off_reports_nothing_rather_than_raw_depth)

    failed = [n for n, ok, _ in _results if not ok]
    print("\n" + "=" * 68)
    if failed:
        print(f"DEPTH STATS: FAILED ({len(failed)}/{len(_results)})")
        for n in failed:
            print(f"  - {n}")
        return 1
    print(f"DEPTH STATS: PASSED ({len(_results)}/{len(_results)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
