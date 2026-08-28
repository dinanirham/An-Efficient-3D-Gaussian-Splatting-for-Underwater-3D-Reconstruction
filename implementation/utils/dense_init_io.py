"""I/O and provenance for the M1 dense initialization cloud.

The dense point cloud **is** the experimental condition for the A1-derived
cells (A1, A4, A5, A7): with densification disabled the primitive count can
never grow, so the cloud alone decides the starting -- and largely the final --
geometry, and with it whether the A2 budget ever binds.

An unversioned cloud produced by an unseeded GPU matcher therefore makes those
four cells unattributable: two runs of the initializer give different clouds,
different counts, and different "efficiency" numbers with no way to tell that
apart from a real effect.  Every cloud is written with a sidecar recording its
point count, SHA-256 and the exact parameters that produced it, and the trainer
records that hash in its run manifest.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
from plyfile import PlyData, PlyElement

from utils.graphics_utils import BasicPointCloud


def sha256_file(path: str | Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            block = fh.read(chunk)
            if not block:
                break
            h.update(block)
    return h.hexdigest()


def sidecar_path(ply_path: str | Path) -> Path:
    return Path(ply_path).with_suffix(".json")


def write_dense_pcd(
    ply_path: str | Path,
    points: np.ndarray,
    colors_uint8: np.ndarray,
    meta: dict[str, Any],
) -> Path:
    """Write the cloud plus its provenance sidecar.

    `colors_uint8` is stored as 0-255 `red`/`green`/`blue`, matching what
    COLMAP's `points3D` reader produces, so the downstream loader does not need
    to know which source a cloud came from.
    """
    ply_path = Path(ply_path)
    ply_path.parent.mkdir(parents=True, exist_ok=True)

    n = points.shape[0]
    if n == 0:
        raise ValueError("refusing to write an empty dense cloud")
    if colors_uint8.shape[0] != n:
        raise ValueError(
            f"points/colors length mismatch: {n} vs {colors_uint8.shape[0]}"
        )

    dtype = [
        ("x", "f4"), ("y", "f4"), ("z", "f4"),
        ("nx", "f4"), ("ny", "f4"), ("nz", "f4"),
        ("red", "u1"), ("green", "u1"), ("blue", "u1"),
    ]
    arr = np.empty(n, dtype=dtype)
    arr["x"], arr["y"], arr["z"] = points[:, 0], points[:, 1], points[:, 2]
    arr["nx"] = arr["ny"] = arr["nz"] = 0.0
    arr["red"] = colors_uint8[:, 0]
    arr["green"] = colors_uint8[:, 1]
    arr["blue"] = colors_uint8[:, 2]

    PlyData([PlyElement.describe(arr, "vertex")]).write(str(ply_path))

    meta = dict(meta)
    meta["num_points"] = int(n)
    meta["sha256"] = sha256_file(ply_path)
    with open(sidecar_path(ply_path), "w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=2)

    print(f"[dense-init] wrote {n} points -> {ply_path}")
    print(f"[dense-init] sha256 {meta['sha256']}")
    return ply_path


def load_dense_pcd(ply_path: str | Path) -> BasicPointCloud:
    """Load a dense cloud, verifying its sidecar hash if one is present."""
    ply_path = Path(ply_path)
    if not ply_path.exists():
        raise FileNotFoundError(
            f"dense init cloud not found: {ply_path}\n"
            f"Produce it first with:  python -m source.roma_init "
            f"--source_path <scene> --output {ply_path}"
        )

    side = sidecar_path(ply_path)
    if side.exists():
        with open(side, encoding="utf-8") as fh:
            meta = json.load(fh)
        actual = sha256_file(ply_path)
        if meta.get("sha256") and meta["sha256"] != actual:
            raise ValueError(
                f"dense cloud {ply_path} does not match its sidecar hash.\n"
                f"  sidecar: {meta['sha256']}\n"
                f"  actual : {actual}\n"
                f"The cloud has changed since it was recorded, so any run using "
                f"it cannot be attributed. Regenerate both, or delete the "
                f"sidecar deliberately."
            )
        print(f"[dense-init] sidecar verified ({meta.get('num_points')} points)")
    else:
        print(f"[dense-init] WARNING: no sidecar at {side}; provenance unrecorded")

    ply = PlyData.read(str(ply_path))["vertex"]
    points = np.vstack([ply["x"], ply["y"], ply["z"]]).T.astype(np.float32)

    if "red" in ply.data.dtype.names:
        colors = (
            np.vstack([ply["red"], ply["green"], ply["blue"]]).T.astype(np.float32)
            / 255.0
        )
    else:
        colors = np.full_like(points, 0.5, dtype=np.float32)

    if "nx" in ply.data.dtype.names:
        normals = np.vstack([ply["nx"], ply["ny"], ply["nz"]]).T.astype(np.float32)
    else:
        normals = np.zeros_like(points, dtype=np.float32)

    return BasicPointCloud(points=points, colors=colors, normals=normals)


def read_sidecar(ply_path: str | Path) -> dict[str, Any]:
    """Return the sidecar dict, or an empty dict. Never raises."""
    try:
        with open(sidecar_path(ply_path), encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:  # noqa: BLE001 - provenance must not break a run
        return {}
