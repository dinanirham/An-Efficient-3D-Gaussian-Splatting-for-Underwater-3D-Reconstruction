"""Verification for the Chapter IV asset collector.

    python tools/verify_chapter_assets.py

Tests the pure parts only — view selection, crop arithmetic, output shapes and
the manifest contract. Rendering and metric computation need a GPU and the
campaign checkpoints, and are exercised by running the tool itself on Colab.

The rule these tests enforce is the one this campaign learned the hard way: a
figure that compares configurations must hold the view and the crop fixed, or
it is not a comparison. Every selection here is deterministic given the scene,
so two cells rendered in different sessions still line up.
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from tools.chapter_assets import (  # noqa: E402
    CROPS,
    FIXED_VIEW,
    clamp_crop,
    per_view_rows,
    pick_view_index,
    invisible_mask,
    selfcheck_verdict,
    radius_histogram,
    write_manifest,
)

_results: list[tuple[str, bool, str]] = []


def check(name: str, fn) -> None:
    try:
        ok, msg = fn()
    except Exception as exc:  # noqa: BLE001
        ok, msg = False, f"{type(exc).__name__}: {exc}"
    _results.append((name, ok, msg))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {msg}")


def t1_view_choice_is_deterministic_per_scene():
    """DECISIVE. The same scene yields the same view every time, in any session."""
    a = [pick_view_index("Curasao", 3) for _ in range(5)]
    b = [pick_view_index("Curasao", 3) for _ in range(5)]
    ok = len(set(a)) == 1 and a == b
    return ok, f"Curasao with 3 views -> index {a[0]} on every call"


def t2_view_choice_stays_in_range():
    bad = [(scene, n, pick_view_index(scene, n))
           for scene in FIXED_VIEW for n in (1, 2, 3, 4, 13)
           if not 0 <= pick_view_index(scene, n) < n]
    return not bad, "index within [0, n) for every scene and view count" if not bad else str(bad)


def t3_no_views_is_refused_not_guessed():
    try:
        pick_view_index("Curasao", 0)
    except ValueError:
        return True, "raises rather than returning a bogus index"
    return False, "returned an index for a scene with no views"


def t4_crop_is_clamped_into_the_image():
    """A crop wider than the image would silently shrink and break comparability."""
    box = clamp_crop((900, 1200), (0, 0, 400, 300))
    inside = clamp_crop((900, 1200), (1100, 800, 400, 300))
    ok = box == (0, 0, 400, 300) and inside[0] + inside[2] <= 1200 and inside[1] + inside[3] <= 900
    return ok, f"in-bounds kept {box}; out-of-bounds clamped to {inside}"


def t5_crop_keeps_its_size_when_clamped():
    """Clamping must move the box, never resize it, or two cells differ."""
    w, h = 400, 300
    out = clamp_crop((900, 1200), (1190, 890, w, h))
    return out[2] == w and out[3] == h, f"size preserved: {out[2]}x{out[3]}"


def t6_every_scene_has_a_named_crop_pair():
    missing = [s for s in FIXED_VIEW if s not in CROPS or len(CROPS[s]) != 2]
    return not missing, ("every scene has a far-field and a near-field crop"
                         if not missing else f"missing: {missing}")


def t7_per_view_rows_carry_one_row_per_image():
    recs = [{"image": "a.png", "psnr_pooled": 30.0, "ssim": 0.9, "lpips": 0.18},
            {"image": "b.png", "psnr_pooled": 24.5, "ssim": 0.8, "lpips": 0.29}]
    rows = per_view_rows("A0", "Curasao", 0, recs)
    ok = (len(rows) == 2 and rows[0]["cell"] == "A0" and rows[0]["seed"] == 0
          and rows[1]["psnr_pooled"] == 24.5 and rows[0]["image"] == "a.png")
    return ok, f"{len(rows)} rows, identity columns present"


def t8_radius_histogram_is_normalised_and_binned():
    import numpy as np
    xyz = np.zeros((100, 3), dtype=float)
    xyz[:, 0] = np.linspace(0.0, 10.0, 100)
    edges, frac = radius_histogram(xyz, centre=np.zeros(3), bins=10)
    ok = len(frac) == 10 and abs(sum(frac) - 1.0) < 1e-9 and len(edges) == 11
    return ok, f"{len(frac)} bins summing to {sum(frac):.6f}"


def t9_manifest_records_what_was_written():
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        (out / "per_view_metrics.csv").write_text("x", encoding="utf-8")
        write_manifest(out, {"per_view_metrics.csv": "C1", "missing.csv": "C9"})
        got = json.loads((out / "assets_manifest.json").read_text(encoding="utf-8"))
        ok = (got["written"]["per_view_metrics.csv"] == "C1"
              and "missing.csv" in got["absent"])
        return ok, f"written {list(got['written'])}, absent {list(got['absent'])}"


def t10_selfcheck_catches_the_wrong_model_state():
    """DECISIVE. The guard that would have caught the quantised-cell defect.

    The first version of this tool rendered quantised runs from their stored
    point cloud, which holds the CONTINUOUS parameters, and so measured a model
    the campaign never evaluated: A3 on Panama came out 6 dB below its own
    recorded result and nothing objected. Every run is now compared with its
    own eval_metrics.json before the numbers are written.
    """
    cases = [
        (30.00, 30.20, "ok"),          # render-path tolerance
        (30.00, 30.50, "ok"),          # exactly at the bound
        (30.00, 30.51, "MISMATCH"),    # just past it
        (21.87, 28.71, "MISMATCH"),    # the real A3/Panama defect
        (30.00, None, "no eval_metrics"),
    ]
    bad = [(m, e, want, selfcheck_verdict(m, e)[1]) for m, e, want in cases
           if selfcheck_verdict(m, e)[1] != want]
    return not bad, ("boundaries and the real defect classified"
                     if not bad else f"wrong: {bad}")


def t11_store_schema_is_read_in_one_place_only():
    """DECISIVE. chapter_assets must not parse the compressed store itself.

    It did once: a hand-rolled reader guessed `index_bits` where the writer
    writes `bits_per_index`, and died on the first quantised run. A guess that
    had been plausible rather than wrong would have produced numbers instead of
    an exception. The store has one reader, in j_consistency, and this test
    fails if a second one reappears here.
    """
    src = (Path(__file__).resolve().parent / "chapter_assets.py").read_text(encoding="utf-8")
    leaked = [k for k in ("bits_per_index", "packed_bytes", "index_bits",
                          "indices.bin", "codebooks.npz", "num_primitives")
              if k in src]
    return not leaked, ("no store-schema knowledge in chapter_assets"
                        if not leaked else f"schema leaked back in: {leaked}")


def t12_invisible_mask_uses_the_geometry_threshold():
    """The figure and the geometry table must mean the same thing by 'invisible'."""
    import numpy as np
    from tools.chapter_assets import VISIBLE_ALPHA
    opacity = np.array([[0.0], [0.049], [0.05], [0.9]])
    mask = invisible_mask(opacity)
    ok = list(mask) == [True, True, False, False] and VISIBLE_ALPHA == 0.05
    return ok, f"threshold {VISIBLE_ALPHA}; boundary value counts as visible"


def main() -> int:
    print("=" * 68)
    print("Chapter IV asset collector")
    print("=" * 68)
    check("T1 view choice is deterministic per scene  <-- decisive",
          t1_view_choice_is_deterministic_per_scene)
    check("T2 view index stays in range", t2_view_choice_stays_in_range)
    check("T3 a scene with no views is refused", t3_no_views_is_refused_not_guessed)
    check("T4 crop is clamped into the image", t4_crop_is_clamped_into_the_image)
    check("T5 clamping moves the crop, never resizes it  <-- decisive",
          t5_crop_keeps_its_size_when_clamped)
    check("T6 every scene has both crops", t6_every_scene_has_a_named_crop_pair)
    check("T7 per-view rows carry one row per image", t7_per_view_rows_carry_one_row_per_image)
    check("T8 radius histogram is normalised", t8_radius_histogram_is_normalised_and_binned)
    check("T9 manifest records written and absent", t9_manifest_records_what_was_written)
    check("T10 self-check catches the wrong model state  <-- decisive",
          t10_selfcheck_catches_the_wrong_model_state)
    check("T11 the store has one reader  <-- decisive",
          t11_store_schema_is_read_in_one_place_only)
    check("T12 invisible mask uses the geometry threshold",
          t12_invisible_mask_uses_the_geometry_threshold)

    failed = [n for n, ok, _ in _results if not ok]
    print("\n" + "=" * 68)
    if failed:
        print(f"CHAPTER ASSETS: FAILED ({len(failed)}/{len(_results)})")
        for n in failed:
            print(f"  - {n}")
        return 1
    print(f"CHAPTER ASSETS: PASSED ({len(_results)}/{len(_results)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
