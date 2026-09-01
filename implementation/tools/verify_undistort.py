"""Acceptance test for the undistortion preprocessing. Pure stdlib, no COLMAP.

    python -m tools.verify_undistort

COLMAP itself is not exercised -- it is an external binary and its correctness
is not ours to test. What is tested is everything around it, which is where the
failures actually live: detecting that undistortion is needed, repairing the
layout COLMAP produces, and refusing to let an un-undistorted scene through.

T1 runs against the **real dataset**, so it is the check that would have caught
this gap in the first place: all four scenes are OPENCV, and the scene reader
accepts only PINHOLE.
"""

from __future__ import annotations

import os
import struct
import sys
import tempfile
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from source.undistort import (  # noqa: E402
    ACCEPTED,
    find_sparse_dir,
    normalise_sparse_layout,
    read_camera_model,
    undistort_scene,
    verify_undistorted,
)

REPO = Path(__file__).resolve().parent.parent.parent

# T1 needs the *original*, still-distorted dataset. Its location is not fixed:
# beside the repo on a workstation, on Drive under Colab, and the distributed
# folder name varies in case (SeaThruNeRF_dataset / SeathruNeRF_dataset). Take
# an override, then try the plausible spellings, so the one check that would
# catch the undistortion gap does not silently go missing on the machine the
# campaign actually runs on.
_DATASET_ENV = os.environ.get("E3DGSUW_DATASET")
if _DATASET_ENV:
    DATASET = Path(_DATASET_ENV)
else:
    _candidates = [
        REPO / "dataset" / name
        for name in ("SeathruNeRF_dataset", "SeaThruNeRF_dataset")
    ]
    DATASET = next((p for p in _candidates if p.exists()), _candidates[0])
SCENES = ["Curasao", "IUI3-RedSea", "JapaneseGradens-RedSea", "Panama"]

_results: list[tuple[str, bool, str]] = []


def check(name: str, fn) -> None:
    try:
        ok, detail = fn()
    except Exception as exc:  # noqa: BLE001
        ok, detail = False, f"raised {type(exc).__name__}: {exc}"
    _results.append((name, ok, detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")


def write_cameras_bin(path: Path, model_id: int, params: list[float],
                      width: int = 640, height: int = 480) -> None:
    """Minimal COLMAP cameras.bin with one camera."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as fh:
        fh.write(struct.pack("<Q", 1))
        fh.write(struct.pack("<iiQQ", 1, model_id, width, height))
        fh.write(struct.pack("<" + "d" * len(params), *params))


def make_scene(root: Path, model_id: int, params: list[float],
               nested: bool = True) -> Path:
    scene = root / "scene"
    sparse = scene / "sparse" / "0" if nested else scene / "sparse"
    write_cameras_bin(sparse / "cameras.bin", model_id, params)
    (sparse / "images.bin").write_bytes(b"\x00" * 8)
    (sparse / "points3D.bin").write_bytes(b"\x00" * 8)
    return scene


# ---------------------------------------------------------------------------


def t1_real_dataset_needs_undistortion():
    """THE check that would have caught the gap: real scenes are OPENCV."""
    if not DATASET.exists():
        return False, f"dataset not found at {DATASET}"
    rows = []
    all_need = True
    for scene in SCENES:
        info = read_camera_model(find_sparse_dir(DATASET / scene) / "cameras.bin")
        all_need &= info["needs_undistortion"]
        rows.append(f"{scene.split('-')[0]}={info['model']}")
    return all_need, (
        f"{', '.join(rows)}; reader accepts only {sorted(ACCEPTED)} -> "
        f"undistortion is mandatory"
    )


def t2_find_sparse_handles_both_layouts():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        nested = make_scene(root / "a", 1, [500.0, 500.0, 320.0, 240.0], nested=True)
        flat = make_scene(root / "b", 1, [500.0, 500.0, 320.0, 240.0], nested=False)
        ok = (
            find_sparse_dir(nested).name == "0"
            and find_sparse_dir(flat).name == "sparse"
        )
        return ok, f"nested -> {find_sparse_dir(nested).name}, flat -> {find_sparse_dir(flat).name}"


def t3_layout_repaired_and_idempotent():
    """COLMAP writes sparse/ flat; the reader hard-codes sparse/0."""
    with tempfile.TemporaryDirectory() as tmp:
        scene = make_scene(Path(tmp), 1, [500.0, 500.0, 320.0, 240.0], nested=False)
        moved_first = normalise_sparse_layout(scene)
        at_nested = (scene / "sparse" / "0" / "cameras.bin").exists()
        others = {"images.bin", "points3D.bin"} <= {
            p.name for p in (scene / "sparse" / "0").iterdir()
        }
        moved_again = normalise_sparse_layout(scene)      # must be a no-op
        ok = moved_first and at_nested and others and not moved_again
        return ok, (
            f"moved={moved_first}, files at sparse/0={at_nested}, "
            f"siblings moved={others}, second call no-op={not moved_again}"
        )


def t4_opencv_scene_refused_with_actionable_message():
    with tempfile.TemporaryDirectory() as tmp:
        scene = make_scene(Path(tmp), 4,  # OPENCV
                           [1960.0, 1961.0, 894.0, 580.0, -0.085, 0.147, 0.0, 0.0])
        try:
            verify_undistorted(scene)
        except RuntimeError as exc:
            msg = str(exc)
            ok = "OPENCV" in msg and "undistort" in msg.lower()
            return ok, f"refused: ...{msg[-95:]}"
        return False, "an OPENCV scene was accepted"


def t5_pinhole_scene_accepted():
    with tempfile.TemporaryDirectory() as tmp:
        scene = make_scene(Path(tmp), 1, [500.0, 500.0, 320.0, 240.0])
        info = verify_undistorted(scene)
        return info["model"] == "PINHOLE", f"accepted model={info['model']}"


def t6_already_undistorted_is_skipped():
    """Re-running preprocessing must not resample the images a second time."""
    with tempfile.TemporaryDirectory() as tmp:
        scene = make_scene(Path(tmp), 1, [500.0, 500.0, 320.0, 240.0])
        # colmap="false" would fail immediately if it were ever invoked.
        res = undistort_scene(scene, Path(tmp) / "out", colmap="false")
        return res.get("skipped") is True, (
            f"skipped={res.get('skipped')} model={res.get('model')} "
            f"(colmap binary never invoked)"
        )


def t7_missing_reconstruction_is_loud():
    with tempfile.TemporaryDirectory() as tmp:
        try:
            find_sparse_dir(Path(tmp))
        except FileNotFoundError as exc:
            return "cameras.bin" in str(exc), f"raised: {str(exc)[:60]}"
        return False, "a scene with no reconstruction was accepted"


def main() -> int:
    check("T1 real dataset is OPENCV, undistortion required  <-- decisive",
          t1_real_dataset_needs_undistortion)
    check("T2 sparse dir found in both layouts", t2_find_sparse_handles_both_layouts)
    check("T3 flat layout repaired to sparse/0, idempotently",
          t3_layout_repaired_and_idempotent)
    check("T4 an OPENCV scene is refused, actionably",
          t4_opencv_scene_refused_with_actionable_message)
    check("T5 a PINHOLE scene is accepted", t5_pinhole_scene_accepted)
    check("T6 an already-undistorted scene is skipped", t6_already_undistorted_is_skipped)
    check("T7 a missing reconstruction fails loudly", t7_missing_reconstruction_is_loud)

    failed = [n for n, ok, _ in _results if not ok]
    print("\n" + "=" * 68)
    if failed:
        # Report passes, matching the PASSED branch and every other suite.
        # "FAILED (1/7)" read as one check passing when it meant one failing.
        print(f"UNDISTORTION: FAILED ({len(_results) - len(failed)}/"
              f"{len(_results)} passed, {len(failed)} failed)")
        for n in failed:
            print(f"  - {n}")
        return 1
    print(f"UNDISTORTION: PASSED ({len(_results)}/{len(_results)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
