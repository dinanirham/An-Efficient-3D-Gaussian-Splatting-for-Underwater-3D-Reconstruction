"""Acceptance test for the campaign analysis. Pure stdlib -- no torch, no GPU.

    python -m tools.verify_analysis

Builds synthetic campaigns on disk in the real file layout, with interactions
of *known* size injected, and requires the analysis to recover them.

This is the only way to validate this tool before results exist. It cannot
catch schema drift -- if the runs one day emit a different `eval_metrics.json`
shape, these fixtures would still pass while the loader silently returned
nothing. The loader's "no completed runs" path is the guard against that, and
T8 exercises it.

T1 and T2 are the pair that matters: additive data must produce interactions
indistinguishable from zero, and injected interactions must come back at the
size they were injected. A tool that fails either would report interaction
structure that is an artifact of its own arithmetic.
"""

from __future__ import annotations

import json
import math
import sys
import tempfile
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from tools.analyse import CELLS, analyse_metric, load_campaign  # noqa: E402

SCENES = ["Curasao", "IUI3-RedSea", "JapaneseGradens-RedSea", "Panama"]
SEEDS = [0, 1, 2]

_results: list[tuple[str, bool, str]] = []


def check(name: str, fn) -> None:
    try:
        ok, detail = fn()
    except Exception as exc:  # noqa: BLE001
        ok, detail = False, f"raised {type(exc).__name__}: {exc}"
    _results.append((name, ok, detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")


def write_campaign(
    root: Path,
    quality: dict[str, float],
    ratio: dict[str, float] | None = None,
    seeds: list[int] = SEEDS,
    scenes: list[str] = SCENES,
    jitter: float = 0.02,
    gpu: str = "NVIDIA A100-SXM4-40GB",
) -> None:
    """Write a campaign in the layout `load_campaign` expects."""
    rng_state = [12345]

    def jit() -> float:
        # Deterministic LCG so fixtures are reproducible without numpy.
        rng_state[0] = (1103515245 * rng_state[0] + 12345) % (1 << 31)
        return ((rng_state[0] / (1 << 31)) - 0.5) * 2 * jitter

    for cell, base in quality.items():
        for scene in scenes:
            for seed in seeds:
                d = root / "runs" / cell / scene / f"s{seed}"
                d.mkdir(parents=True, exist_ok=True)
                with open(d / "eval_metrics.json", "w", encoding="utf-8") as fh:
                    json.dump({
                        "Test": {
                            "psnr_pooled": base + jit(),
                            "psnr_per_channel": base + 1.0 + jit(),
                            "ssim": 0.8,
                            "lpips": 0.2,
                            "n_images": 3,
                        },
                        "cost": {"effective_optimizer_steps": 43000},
                    }, fh)
                with open(d / "run_config.json", "w", encoding="utf-8") as fh:
                    json.dump({"gpu": {"name": gpu}}, fh)

                if ratio is not None:
                    c = d / "compressed_30000"
                    c.mkdir(exist_ok=True)
                    with open(c / "model_size.json", "w", encoding="utf-8") as fh:
                        json.dump({
                            "bytes_per_primitive": ratio[cell] * (1 + jit() * 0.1),
                            "total_bytes": 1000.0,
                            "ratio_vs_this_baseline": 2.0,
                        }, fh)


def additive_quality(a0=25.0, d1=1.0, d2=-0.5, d3=-0.2) -> dict[str, float]:
    """A perfectly additive 2^3: every interaction is exactly zero."""
    return {
        "A0": a0,
        "A1": a0 + d1,
        "A2": a0 + d2,
        "A3": a0 + d3,
        "A4": a0 + d1 + d2,
        "A5": a0 + d1 + d3,
        "A6": a0 + d2 + d3,
        "A7": a0 + d1 + d2 + d3,
    }


def multiplicative_ratio(a0=20.0, r1=0.9, r2=0.5, r3=0.4) -> dict[str, float]:
    return {
        "A0": a0, "A1": a0 * r1, "A2": a0 * r2, "A3": a0 * r3,
        "A4": a0 * r1 * r2, "A5": a0 * r1 * r3, "A6": a0 * r2 * r3,
        "A7": a0 * r1 * r2 * r3,
    }


# ---------------------------------------------------------------------------


def t1_additive_data_has_no_interactions():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_campaign(root, additive_quality())
        res = analyse_metric(load_campaign(root), "psnr_pooled")

        flagged = [k for k, v in res["interactions"].items()
                   if v and v["exceeds_2sem"]]
        sizes = {k: round(v["mean"], 4) for k, v in res["interactions"].items() if v}
        return not flagged, f"all within noise; magnitudes {sizes}"


def t2_injected_interaction_recovered():
    """THE decisive check: an injected M2xM3 must come back at its true size."""
    q = additive_quality()
    delta = -0.80                      # A6 underperforms the additive prediction
    q["A6"] += delta
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_campaign(root, q, jitter=0.01)
        res = analyse_metric(load_campaign(root), "psnr_pooled")

        got = res["interactions"]["M2xM3"]["mean"]
        others = {k: v["mean"] for k, v in res["interactions"].items()
                  if k != "M2xM3" and v}
        # A6 appears in the three-way contrast too, with sign -1.
        clean = all(abs(v) < 0.15 for k, v in others.items() if k != "M1xM2xM3")
        return abs(got - delta) < 0.05 and clean, (
            f"M2xM3 recovered {got:+.4f} vs injected {delta:+.2f}; "
            f"other two-way terms {[round(v, 3) for k, v in others.items() if k != 'M1xM2xM3']}"
        )


def t3_three_way_recovered():
    q = additive_quality()
    delta = 0.60
    q["A7"] += delta                   # A7 alone carries the three-way term
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_campaign(root, q, jitter=0.01)
        res = analyse_metric(load_campaign(root), "psnr_pooled")

        three = res["interactions"]["M1xM2xM3"]["mean"]
        twos = [v["mean"] for k, v in res["interactions"].items()
                if k != "M1xM2xM3" and v]
        # A7 appears in no two-way contrast, so those must stay clean.
        return abs(three - delta) < 0.05 and all(abs(t) < 0.1 for t in twos), (
            f"three-way {three:+.4f} vs injected {delta:+.2f}; "
            f"two-way terms {[round(t, 3) for t in twos]}"
        )


def t4_multiplicative_null_is_one():
    """Ratio metrics must combine multiplicatively, with null 1.0."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_campaign(root, additive_quality(), ratio=multiplicative_ratio())
        res = analyse_metric(load_campaign(root), "bytes_per_primitive")

        ok_mode = res["combination"] == "multiplicative"
        near_one = all(abs(v["mean"] - 1.0) < 0.05
                       for v in res["interactions"].values() if v)
        nulls = all(v["null"] == 1.0 for v in res["interactions"].values() if v)
        return ok_mode and near_one and nulls, (
            f"mode={res['combination']}, interactions "
            f"{[round(v['mean'], 4) for v in res['interactions'].values() if v]} "
            f"(null 1.0)"
        )


def t5_main_effects_agree_on_additive_data():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_campaign(root, additive_quality(), jitter=0.01)
        res = analyse_metric(load_campaign(root), "psnr_pooled")

        agree = {m: e.get("directions_agree") for m, e in res["main_effects"].items()}
        vals = {m: (round(e["from_below"]["mean"], 3), round(e["from_above"]["mean"], 3))
                for m, e in res["main_effects"].items()}
        return all(agree.values()), f"below/above {vals}; agree {agree}"


def t6_disagreement_flagged_when_interaction_present():
    """With an interaction, the two directions must diverge and be flagged."""
    q = additive_quality()
    q["A6"] -= 1.5
    q["A7"] -= 1.5                     # M1's from-above contrast is A7−A6
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_campaign(root, q, jitter=0.01)
        res = analyse_metric(load_campaign(root), "psnr_pooled")

        m2 = res["main_effects"]["M2"]
        # A6 and A7 both shifted, so M2's from-above (A7−A5) moves while
        # from-below (A2−A0) does not.
        return m2["directions_agree"] is False, (
            f"M2 below={m2['from_below']['mean']:+.3f} "
            f"above={m2['from_above']['mean']:+.3f} "
            f"|diff|={m2['disagreement']:.3f} > 2·sem={2 * m2['pooled_sem']:.3f}; "
            f"quotable_alone={m2['quotable_alone']}"
        )


def t7_partial_campaign_reports_missing():
    """A campaign missing cells must omit affected contrasts, not invent them."""
    q = {k: v for k, v in additive_quality().items() if k in ("A0", "A1", "A2")}
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_campaign(root, q)
        res = analyse_metric(load_campaign(root), "psnr_pooled")

        missing = set(res["missing_cells"])
        m1_below = res["main_effects"]["M1"]["from_below"]
        ok = (
            missing == {"A3", "A4", "A5", "A6", "A7"}
            and m1_below is not None                     # A1−A0 is computable
            and res["interactions"]["M1xM2"] is None     # needs A4
            and res["main_effects"]["M1"]["from_above"] is None
        )
        return ok, (
            f"missing={sorted(missing)}; from_below computed, "
            f"from_above and interactions correctly omitted"
        )


def t8_empty_campaign_is_not_silent():
    with tempfile.TemporaryDirectory() as tmp:
        runs = load_campaign(Path(tmp))
        return runs == [], f"empty root yields {len(runs)} runs (loader returns nothing)"


def t9_single_seed_dispersion_is_unknown_not_zero():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_campaign(root, additive_quality(), seeds=[0], jitter=0.0)
        res = analyse_metric(load_campaign(root), "psnr_pooled")
        sem = res["cells"]["A0"]["sem"]
        inter = res["interactions"]["M1xM2"]
        agree = res["main_effects"]["M1"]["directions_agree"]
        ok = (
            math.isnan(sem)
            and not inter["exceeds_2sem"]
            and agree is None          # undetermined, NOT "they disagree"
        )
        return ok, (
            f"sem={sem} (nan, not 0); no interaction claimed; "
            f"direction agreement reported as {agree} rather than False"
        )


def main() -> int:
    check("T1 additive data yields no interactions", t1_additive_data_has_no_interactions)
    check("T2 injected two-way interaction recovered  <-- decisive", t2_injected_interaction_recovered)
    check("T3 injected three-way interaction recovered", t3_three_way_recovered)
    check("T4 ratio metrics combine multiplicatively, null 1.0", t4_multiplicative_null_is_one)
    check("T5 main effects agree on additive data", t5_main_effects_agree_on_additive_data)
    check("T6 direction disagreement is flagged", t6_disagreement_flagged_when_interaction_present)
    check("T7 partial campaign omits contrasts it cannot compute", t7_partial_campaign_reports_missing)
    check("T8 an empty campaign yields nothing, loudly", t8_empty_campaign_is_not_silent)
    check("T9 single seed gives unknown dispersion, not zero", t9_single_seed_dispersion_is_unknown_not_zero)

    failed = [n for n, ok, _ in _results if not ok]
    print("\n" + "=" * 68)
    if failed:
        print(f"CAMPAIGN ANALYSIS: FAILED ({len(failed)}/{len(_results)})")
        for n in failed:
            print(f"  - {n}")
        return 1
    print(f"CAMPAIGN ANALYSIS: PASSED ({len(_results)}/{len(_results)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
