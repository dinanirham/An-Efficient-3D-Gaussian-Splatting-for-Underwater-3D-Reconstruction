"""Acceptance test for the vanilla-SeaSplat collector (CD-31).

    python -m tools.verify_measure_reference

Pure stdlib and numpy. No GPU, no dataset, no rasterizer.

**What the collector is for.** Every number this study reports is a difference
against A0, so A0's standing rests on being the method it claims to
reimplement. That currently rests on `replicate_baseline.py`: converged
primitive count only, at 16 000 iterations, on one scene, with no fidelity
metric involved -- and at n=3 per side the 95% interval on the ratio is
+/-23.5% on that scene, so the data are consistent with a quarter's
difference.

**The constraint it works under.** Vanilla SeaSplat must not be modified.
It does not need to be: `render_uw.py`'s `render_set` is the upstream render
path, inherited unchanged in this fork, and `train.py`'s own evaluation calls
exactly that function and then reads the images back from disk. So a vanilla
run can be measured by pointing the same sequence at its output directory --
their model, their render code, our metric harness, one convention.

**T5 is the decisive check.** A margin verdict that silently passes when a
metric is absent would certify equivalence from missing data, which is worse
than reporting nothing: it produces the exact claim the thesis needs, from
no evidence at all.
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from tools.measure_reference import (  # noqa: E402
    EVAL_SCHEMA_KEYS,
    aggregate_by_scene,
    find_iteration,
    find_written_model,
    vanilla_command,
    load_margins,
    margin_verdict,
)

_results: list[tuple[str, bool, str]] = []


def check(name: str, fn) -> None:
    try:
        ok, detail = fn()
    except Exception as exc:  # noqa: BLE001
        ok, detail = False, f"raised {type(exc).__name__}: {exc}"
    _results.append((name, ok, detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")


def make_ref(root: Path, iters: list[int], *, medium_for: list[int] | None = None) -> Path:
    """A vanilla SeaSplat output directory, as an unpatched run leaves it."""
    medium_for = iters if medium_for is None else medium_for
    for it in iters:
        d = root / "point_cloud" / f"iteration_{it}"
        d.mkdir(parents=True, exist_ok=True)
        (d / "point_cloud.ply").write_bytes(b"ply\n")
        if it in medium_for:
            (root / f"attenuate_{it}.pth").write_bytes(b"\x00")
            (root / f"backscatter_{it}.pth").write_bytes(b"\x00")
    return root


# --------------------------------------------------------------------------


def t1_iteration_is_the_largest_complete_one():
    with tempfile.TemporaryDirectory() as tmp:
        r = make_ref(Path(tmp), [7000, 15000, 30000])
        got = find_iteration(r)
    return got == 30000, f"picked {got} from 7000/15000/30000"


def t2_incomplete_iteration_is_skipped():
    """A PLY without its medium nets cannot be composed, so it is not a candidate.

    Taking it anyway would silently evaluate the newest geometry against an
    older medium model, which is a different experiment that looks like this
    one.
    """
    with tempfile.TemporaryDirectory() as tmp:
        r = make_ref(Path(tmp), [15000, 30000], medium_for=[15000])
        got = find_iteration(r)
    return got == 15000, f"30000 has no medium nets; picked {got}"


def t3_no_usable_iteration_is_reported_not_guessed():
    with tempfile.TemporaryDirectory() as tmp:
        r = make_ref(Path(tmp), [30000], medium_for=[])
        got = find_iteration(r)
    return got is None, f"no complete iteration -> {got}"


def t4_margins_come_from_the_pre_registration():
    """The margin must be read from cells.json, never defaulted in code.

    A margin invented at analysis time is not a pre-specified margin, which is
    the only kind that licenses the word 'equivalent'.
    """
    m = load_margins()
    ok = (
        m is not None
        and m["psnr_pooled_db"] == 1.0
        and m["lpips"] == 0.02
        and m["n_primitives_fraction"] == 0.30
    )
    return ok, f"read from configs/cells.json: {m}"


def t5_absent_metric_fails_rather_than_passes():
    """DECISIVE. Missing data must never certify equivalence.

    A verdict that treats an absent metric as within-margin manufactures the
    study's foundational claim out of nothing, and it would read as a clean
    result.
    """
    margins = {"psnr_pooled_db": 1.0, "lpips": 0.02, "n_primitives_fraction": 0.30}
    v = margin_verdict(
        ss={"psnr_pooled": 30.1},                 # lpips and count absent
        a0={"psnr_pooled": 30.3, "lpips": 0.18, "n_primitives_final": 3_000_000},
        margins=margins,
    )
    ok = (
        v["psnr_pooled"]["within"] is True
        and v["lpips"]["within"] is None
        and v["n_primitives_final"]["within"] is None
        and v["verdict"] == "INCOMPLETE"
    )
    return ok, f"absent metrics -> within=None, overall {v['verdict']!r}"


def t6_within_margin_passes_and_outside_fails():
    margins = {"psnr_pooled_db": 1.0, "lpips": 0.02, "n_primitives_fraction": 0.30}
    a0 = {"psnr_pooled": 30.0, "lpips": 0.180, "n_primitives_final": 3_000_000}

    near = margin_verdict({"psnr_pooled": 30.4, "lpips": 0.185,
                           "n_primitives_final": 3_300_000}, a0, margins)
    far = margin_verdict({"psnr_pooled": 32.5, "lpips": 0.185,
                          "n_primitives_final": 3_300_000}, a0, margins)
    ok = near["verdict"] == "WITHIN MARGIN" and far["verdict"] == "OUTSIDE MARGIN"
    return ok, f"near={near['verdict']!r}, far(+2.5 dB)={far['verdict']!r}"


def t7_count_margin_is_relative_not_absolute():
    """+/-30% of the baseline, not 30 primitives."""
    margins = {"psnr_pooled_db": 1.0, "lpips": 0.02, "n_primitives_fraction": 0.30}
    a0 = {"n_primitives_final": 1_000_000}
    inside = margin_verdict({"n_primitives_final": 1_250_000}, a0, margins)
    outside = margin_verdict({"n_primitives_final": 1_400_000}, a0, margins)
    ok = (inside["n_primitives_final"]["within"] is True
          and outside["n_primitives_final"]["within"] is False)
    return ok, "+25% within, +40% outside"


def t8_emitted_schema_matches_what_the_collectors_read():
    """collect_results and analyse read eval_metrics.json by key.

    A collector emitting a different shape would make SS invisible to the
    analysis while appearing to have run.
    """
    missing = [k for k in ("quality", "cost") if k not in EVAL_SCHEMA_KEYS]
    ok = not missing and "n_primitives_final" in EVAL_SCHEMA_KEYS["cost"]
    return ok, f"top-level {sorted(EVAL_SCHEMA_KEYS)}, cost carries n_primitives_final"


def t9_verdict_is_reported_per_metric_not_only_overall():
    """An aggregate pass can hide one metric failing badly."""
    margins = {"psnr_pooled_db": 1.0, "lpips": 0.02, "n_primitives_fraction": 0.30}
    v = margin_verdict(
        {"psnr_pooled": 30.1, "lpips": 0.25, "n_primitives_final": 3_000_000},
        {"psnr_pooled": 30.0, "lpips": 0.18, "n_primitives_final": 3_000_000},
        margins,
    )
    ok = (v["psnr_pooled"]["within"] is True
          and v["lpips"]["within"] is False
          and v["verdict"] == "OUTSIDE MARGIN")
    return ok, "PSNR within, LPIPS outside, overall OUTSIDE -- both visible"


def t10_runs_are_aggregated_per_scene_not_per_seed():
    """DECISIVE. SS and A0 are not seed-matched, so they must not be paired.

    Vanilla accepts --seed but seeds only the CPU generator, so its GPU draws
    vary regardless; this implementation seeds both and still measures 49%
    spread. Pairing s0 against s0 would look like a paired comparison and be an
    unpaired one with the pairing noise retained -- inflating the apparent
    difference, and able to push a genuinely equivalent pair outside the
    margin.
    """
    evals = [
        {"_scene": "Curasao", "quality": {"psnr_pooled": 30.0}, "cost": {}},
        {"_scene": "Curasao", "quality": {"psnr_pooled": 31.0}, "cost": {}},
        {"_scene": "Curasao", "quality": {"psnr_pooled": 32.0}, "cost": {}},
        {"_scene": "Panama", "quality": {"psnr_pooled": 28.0}, "cost": {}},
    ]
    agg = aggregate_by_scene(evals)
    ok = (
        set(agg) == {"Curasao", "Panama"}
        and abs(agg["Curasao"]["psnr_pooled"] - 31.0) < 1e-9
        and abs(agg["Panama"]["psnr_pooled"] - 28.0) < 1e-9
    )
    return ok, f"Curasao mean of 3 = {agg['Curasao']['psnr_pooled']:.2f}, Panama n=1 = {agg['Panama']['psnr_pooled']:.2f}"


def t11_unlabelled_runs_are_dropped_not_misfiled():
    """A run without a scene cannot be aggregated and must not land anywhere."""
    agg = aggregate_by_scene([{"quality": {"psnr_pooled": 99.0}, "cost": {}}])
    return agg == {}, "run with no _scene is dropped, not bucketed arbitrarily"


def t12_written_model_is_found_where_upstream_put_it():
    """Upstream ignores --model_path, so the output must be located afterwards.

    Observed: the flag is accepted and then overwritten with
    `<source>/experiments/<MMDDYYYY>/test`. Nothing can be passed that would
    place the model where we asked, so it is found and moved instead.
    """
    import time
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "data" / "Curasao"
        actual = src / "experiments" / "09142026" / "test"
        t0 = time.time() - 5
        make_ref(actual, [30000])
        got = find_written_model([Path(tmp) / "asked_for", src], t0)
    ok = got is not None and got.resolve() == actual.resolve()
    return ok, f"found {got.name if got else None} under experiments/<date>/"


def t13_a_previous_seeds_model_is_not_adopted():
    """DECISIVE. The upstream path is date-scoped, so seeds collide.

    Two seeds of one scene on one day write to the same directory. If a run
    fails and the search accepts whatever is lying there, it measures the
    previous seed's model and files it as its own -- three identical rows that
    look like three repeats and are one run counted thrice, which would make
    the dispersion of the reference control appear to be zero.
    """
    import time
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "data" / "Curasao"
        stale = src / "experiments" / "09142026" / "test"
        make_ref(stale, [30000])
        for f in stale.rglob("*"):
            if f.is_file():
                import os
                os.utime(f, (1, 1))          # long before this run started
        got = find_written_model([src], time.time() - 5)
    return got is None, "a model predating the run is refused, not adopted"


def t14_vanilla_command_enables_the_medium_model():
    """DECISIVE. Upstream's defaults disable the thing that makes it SeaSplat.

    `configs/cells.json` names three flags that are silent no-ops upstream, and
    each produces a different experiment rather than an error:

      --do_seathru        default False -- the medium model never activates and
                          the reference is plain 3DGS on underwater images
      --seathru_from_iter default 9_000_000, past the end of training
      --eval              default False -- empty test set, inflated metrics

    The first was omitted when this was first built. The reference trained to
    completion, reported plausible numbers, and scored 19.34 dB against roughly
    30 for SeaSplat on the same scene -- a control that was not the method it
    was controlling for, and which would have made A0 look like a large
    improvement over its own baseline.
    """
    cmd = vanilla_command(Path("/data/Curasao"), Path("/out"), seed=1)
    joined = " ".join(cmd)
    missing = [f for f in ("--do_seathru", "--seathru_from_iter", "--eval")
               if f not in joined]
    return not missing, (f"all three no-op defaults overridden "
                         f"(missing: {missing or 'none'})")


def main() -> int:
    print("=" * 68)
    print("CD-31  vanilla SeaSplat collector")
    print("=" * 68)

    check("T1  iteration is the largest complete one", t1_iteration_is_the_largest_complete_one)
    check("T2  incomplete iteration is skipped", t2_incomplete_iteration_is_skipped)
    check("T3  no usable iteration is reported, not guessed",
          t3_no_usable_iteration_is_reported_not_guessed)
    check("T4  margins come from the pre-registration", t4_margins_come_from_the_pre_registration)
    check("T5  an absent metric fails rather than passes  <-- decisive",
          t5_absent_metric_fails_rather_than_passes)
    check("T6  within margin passes, outside fails", t6_within_margin_passes_and_outside_fails)
    check("T7  count margin is relative, not absolute", t7_count_margin_is_relative_not_absolute)
    check("T8  emitted schema matches what the collectors read",
          t8_emitted_schema_matches_what_the_collectors_read)
    check("T9  verdict is per metric, not only overall",
          t9_verdict_is_reported_per_metric_not_only_overall)
    check("T10 runs aggregate per scene, not per seed  <-- decisive",
          t10_runs_are_aggregated_per_scene_not_per_seed)
    check("T11 unlabelled runs are dropped, not misfiled",
          t11_unlabelled_runs_are_dropped_not_misfiled)
    check("T12 written model is found where upstream put it",
          t12_written_model_is_found_where_upstream_put_it)
    check("T13 a previous seed's model is not adopted  <-- decisive",
          t13_a_previous_seeds_model_is_not_adopted)
    check("T14 vanilla command enables the medium model  <-- decisive",
          t14_vanilla_command_enables_the_medium_model)

    failed = [n for n, ok, _ in _results if not ok]
    print("\n" + "=" * 68)
    if failed:
        print(f"MEASURE REFERENCE: FAILED ({len(failed)}/{len(_results)})")
        for n in failed:
            print(f"  - {n}")
        return 1
    print(f"MEASURE REFERENCE: PASSED ({len(_results)}/{len(_results)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
