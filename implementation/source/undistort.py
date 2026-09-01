"""Mandatory preprocessing: COLMAP undistortion of the SeaThru-NeRF scenes.

    python -m source.undistort --source <orig>/Curasao --output <undist>/Curasao

**This is not optional.** All four scenes ship with the COLMAP **OPENCV**
camera model and real distortion coefficients (k1 ~ -0.085, k2 ~ 0.15), while
the scene reader accepts only PINHOLE and SIMPLE_PINHOLE:

    assert False, "Colmap camera model not handled: only undistorted datasets
                   (PINHOLE or SIMPLE_PINHOLE cameras) supported!"

Without this step every run -- and every `roma_init` invocation, which uses the
same reader -- fails at scene load. The failure is at least loud, but it is
also total.

Two traps this handles:

**Layout.** `colmap image_undistorter` writes its reconstruction to
`<output>/sparse/` *flat*, while the reader hard-codes `sparse/0` with no
fallback. The files are moved into place.

**Idempotence.** Undistorting an already-undistorted scene would resample the
images a second time. The camera model is checked first and the work skipped if
it is already PINHOLE, so re-running the preprocessing notebook is harmless.
"""

from __future__ import annotations

import argparse
import json
import shutil
import struct
import subprocess
import sys
from pathlib import Path
from typing import Any

# COLMAP camera model ids -> (name, number of parameters)
CAMERA_MODELS: dict[int, tuple[str, int]] = {
    0: ("SIMPLE_PINHOLE", 3), 1: ("PINHOLE", 4), 2: ("SIMPLE_RADIAL", 4),
    3: ("RADIAL", 5), 4: ("OPENCV", 8), 5: ("OPENCV_FISHEYE", 8),
    6: ("FULL_OPENCV", 12), 7: ("FOV", 5), 8: ("SIMPLE_RADIAL_FISHEYE", 4),
    9: ("RADIAL_FISHEYE", 5), 10: ("THIN_PRISM_FISHEYE", 12),
}
ACCEPTED = {"PINHOLE", "SIMPLE_PINHOLE"}


def read_camera_model(cameras_bin: str | Path) -> dict[str, Any]:
    """Read the first camera from a COLMAP `cameras.bin`.

    Deliberately self-contained rather than importing `scene.colmap_loader`:
    that would pull in `scene/__init__.py`, and hence GaussianModel and the
    compiled `simple_knn` extension, making this unusable on a machine that has
    not built the CUDA modules yet -- which is exactly when preprocessing runs.
    """
    with open(cameras_bin, "rb") as fh:
        num_cameras = struct.unpack("<Q", fh.read(8))[0]
        camera_id, model_id, width, height = struct.unpack("<iiQQ", fh.read(24))
        name, n_params = CAMERA_MODELS[model_id]
        params = struct.unpack("<" + "d" * n_params, fh.read(8 * n_params))
    return {
        "num_cameras": num_cameras,
        "camera_id": camera_id,
        "model": name,
        "width": width,
        "height": height,
        "params": list(params),
        "needs_undistortion": name not in ACCEPTED,
    }


def find_sparse_dir(scene: str | Path) -> Path:
    """Locate the reconstruction, accepting either `sparse/0` or flat `sparse`."""
    scene = Path(scene)
    for candidate in (scene / "sparse" / "0", scene / "sparse"):
        if (candidate / "cameras.bin").exists():
            return candidate
    raise FileNotFoundError(f"no cameras.bin under {scene}/sparse[/0]")


def normalise_sparse_layout(scene: str | Path) -> bool:
    """Ensure the reconstruction sits at `sparse/0/`. Returns True if it moved.

    The reader hard-codes `sparse/0` and has no flat fallback, so a scene left
    in COLMAP's undistorter layout loads nothing.
    """
    scene = Path(scene)
    flat, nested = scene / "sparse", scene / "sparse" / "0"
    if (nested / "cameras.bin").exists():
        return False
    if not (flat / "cameras.bin").exists():
        raise FileNotFoundError(f"no reconstruction found under {flat}")

    nested.mkdir(parents=True, exist_ok=True)
    for item in list(flat.iterdir()):
        if item.name == "0":
            continue
        shutil.move(str(item), str(nested / item.name))
    return True


def verify_undistorted(scene: str | Path) -> dict[str, Any]:
    """Confirm a scene will load. Raises with the actionable message if not."""
    scene = Path(scene)
    info = read_camera_model(find_sparse_dir(scene) / "cameras.bin")
    if info["needs_undistortion"]:
        raise RuntimeError(
            f"{scene} still uses the {info['model']} camera model. The scene "
            f"reader accepts only {' or '.join(sorted(ACCEPTED))}, so every run "
            f"on this scene would fail at load. Run source/undistort.py first."
        )
    if not (scene / "sparse" / "0" / "cameras.bin").exists():
        raise RuntimeError(
            f"{scene}: reconstruction is not at sparse/0/. The reader hard-codes "
            f"that path; call normalise_sparse_layout()."
        )
    return info


def undistort_scene(
    source: str | Path,
    output: str | Path,
    images: str = "images_wb",
    colmap: str = "colmap",
    force: bool = False,
) -> dict[str, Any]:
    """Undistort one scene. Idempotent unless `force`."""
    source, output = Path(source), Path(output)
    before = read_camera_model(find_sparse_dir(source) / "cameras.bin")

    if not before["needs_undistortion"] and not force:
        print(f"[undistort] {source.name}: already {before['model']}; skipping")
        return {"skipped": True, "model": before["model"]}

    if output.exists() and (output / "sparse" / "0" / "cameras.bin").exists() and not force:
        info = read_camera_model(output / "sparse" / "0" / "cameras.bin")
        if not info["needs_undistortion"]:
            print(f"[undistort] {source.name}: output already present; skipping")
            return {"skipped": True, "model": info["model"]}

    image_dir = None
    for child in sorted(source.iterdir()):
        if child.is_dir() and child.name.lower() == images.lower():
            image_dir = child
            break
    if image_dir is None:
        raise FileNotFoundError(
            f"no image directory matching {images!r} under {source} "
            f"(note IUI3-RedSea ships 'Images_wb' with a capital I)"
        )

    output.mkdir(parents=True, exist_ok=True)
    cmd = [
        colmap, "image_undistorter",
        "--image_path", str(image_dir),
        "--input_path", str(find_sparse_dir(source)),
        "--output_path", str(output),
        "--output_type", "COLMAP",
    ]
    print("[undistort] " + " ".join(cmd))
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(
            f"colmap image_undistorter failed ({proc.returncode}):\n"
            f"{proc.stdout[-2000:]}\n{proc.stderr[-2000:]}"
        )

    moved = normalise_sparse_layout(output)
    after = verify_undistorted(output)

    n_in = len([p for p in image_dir.iterdir() if p.is_file()])
    n_out = len([p for p in (output / "images").iterdir() if p.is_file()])
    if n_in != n_out:
        # Not fatal -- but a scene that quietly lost frames changes its split.
        print(f"[undistort] WARNING: {n_in} images in, {n_out} out")

    meta = {
        "source": str(source.resolve()),
        "images_dir": image_dir.name,
        "before": before,
        "after": after,
        "sparse_relocated": moved,
        "images_in": n_in,
        "images_out": n_out,
    }
    with open(output / "undistort.json", "w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=2)

    print(f"[undistort] {source.name}: {before['model']} "
          f"{before['width']}x{before['height']} -> {after['model']} "
          f"{after['width']}x{after['height']}, {n_out} images")
    return meta


def main() -> int:
    ap = argparse.ArgumentParser(description="COLMAP undistortion (required)")
    ap.add_argument("--source", required=True, help="original scene directory")
    ap.add_argument("--output", required=True, help="destination scene directory")
    ap.add_argument("--images", default="images_wb")
    ap.add_argument("--colmap", default="colmap", help="colmap executable")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--check_only", action="store_true",
                    help="report the camera model and exit")
    args = ap.parse_args()

    if args.check_only:
        info = read_camera_model(find_sparse_dir(args.source) / "cameras.bin")
        print(json.dumps(info, indent=2))
        return 1 if info["needs_undistortion"] else 0

    undistort_scene(args.source, args.output, args.images,
                    colmap=args.colmap, force=args.force)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
