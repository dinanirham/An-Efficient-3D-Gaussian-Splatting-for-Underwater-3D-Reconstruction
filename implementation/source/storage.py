"""The compressed artifact, and an honest measurement of its size.

Two separate things, deliberately kept apart:

**Writing an artifact that could actually be shipped.**  M5's analytical
`storage_report` counts the bits a correct encoder *would* spend.  That is the
right number to reason with, but it is not evidence: the codebooks were being
persisted with `torch.save`, which stores the assignment vector as int64 --
eight bytes per index where twelve bits suffice, roughly 5x the analytical
figure.  A compression claim backed by a file that large is not a claim about
compression.  So indices are bit-packed at `ceil(log2 k)` bits, and the
attributes the codebooks already encode are not written a second time.

**Measuring what is on disk.**  Reported size is every component of the
artifact: the unquantized remainder (position and opacity, which are never
quantized), the packed index streams, the codebooks, the metadata, and the
medium parameters.  The medium is nine scalars -- negligible in magnitude, but
it must appear, or the figure is a claim rather than an accounting.

Every ratio is stated against **this baseline's 14 floats per primitive**
(`sh_degree = 0`), never the 59 the compression literature assumes.  The two
are different quantities and placing them in one table is a category error.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import torch

# Per-primitive float count for this baseline: xyz(3) + f_dc(3) + opacity(1)
# + scale(3) + rotation(4).  f_rest is empty because sh_degree = 0.
BASELINE_FLOATS_PER_PRIMITIVE = 14
LITERATURE_FLOATS_PER_PRIMITIVE = 59  # 3DGS at sh_degree = 3, for contrast only


# Quantizer group names, and the raw model attribute each one carries.
# Overrides are installed on the RAW parameters, so the model's own activation
# (exp for scale, normalise for rotation) applies afterwards.
_GROUP_TO_ATTR: dict[str, str] = {
    "dc": "features_dc",
    "scale": "scaling",
    "rotation": "rotation",
}


def index_bits(num_clusters: int) -> int:
    return max(1, math.ceil(math.log2(max(2, num_clusters))))


def pack_indices(idx: np.ndarray, bits: int) -> bytes:
    """Bit-pack unsigned indices at `bits` bits each, most-significant first."""
    idx = np.asarray(idx, dtype=np.uint64)
    if idx.size and int(idx.max()) >= (1 << bits):
        raise ValueError(f"index {int(idx.max())} does not fit in {bits} bits")
    shifts = np.arange(bits - 1, -1, -1, dtype=np.uint64)
    bit_array = ((idx[:, None] >> shifts) & np.uint64(1)).astype(np.uint8)
    return np.packbits(bit_array.reshape(-1)).tobytes()


def unpack_indices(data: bytes, count: int, bits: int) -> np.ndarray:
    """Inverse of `pack_indices`. Exists so the packing can be proven correct."""
    raw = np.unpackbits(np.frombuffer(data, dtype=np.uint8))[: count * bits]
    weights = (1 << np.arange(bits - 1, -1, -1)).astype(np.uint64)
    return (raw.reshape(count, bits).astype(np.uint64) * weights).sum(axis=1)


def write_compressed_model(
    out_dir: str | Path,
    gaussians: Any,
    quantizer: Any | None,
    bs_model: Any | None = None,
    at_model: Any | None = None,
    learned_bg: Any | None = None,
) -> Path:
    """Write the shippable artifact. Returns its directory."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    n = int(gaussians.get_xyz.shape[0])

    # Never quantized, so stored directly.
    np.save(out_dir / "xyz.npy",
            gaussians._xyz.detach().cpu().numpy().astype(np.float32))
    np.save(out_dir / "opacity.npy",
            gaussians._opacity.detach().cpu().numpy().astype(np.float32))

    meta: dict[str, Any] = {
        "num_primitives": n,
        "sh_degree": int(getattr(gaussians, "max_sh_degree", 0)),
        "baseline_floats_per_primitive": BASELINE_FLOATS_PER_PRIMITIVE,
        "quantized": quantizer is not None,
        "groups": {},
    }

    if quantizer is not None:
        codebooks: dict[str, np.ndarray] = {}
        packed: dict[str, bytes] = {}
        for name, q in quantizer.quantizers.items():
            bits = index_bits(q.num_clusters)
            idx = q.nn_index.detach().cpu().numpy()
            packed[name] = pack_indices(idx, bits)
            codebooks[name] = q.centers.detach().cpu().numpy().astype(np.float32)
            meta["groups"][name] = {
                "num_clusters": int(q.num_clusters),
                "bits_per_index": bits,
                "vec_dim": int(q.vec_dim),
                "packed_bytes": len(packed[name]),
            }
        with open(out_dir / "indices.bin", "wb") as fh:
            for name in sorted(packed):
                fh.write(packed[name])
        np.savez(out_dir / "codebooks.npz", **codebooks)
    else:
        # Unquantized cells still need their attributes stored somewhere, or
        # the comparison against a quantized cell is not like-for-like.
        np.save(out_dir / "features_dc.npy",
                gaussians._features_dc.detach().cpu().numpy().astype(np.float32))
        np.save(out_dir / "scaling.npy",
                gaussians._scaling.detach().cpu().numpy().astype(np.float32))
        np.save(out_dir / "rotation.npy",
                gaussians._rotation.detach().cpu().numpy().astype(np.float32))

    # The medium: nine scalars plus the learned background.  Tiny, and included
    # precisely because leaving it out would make the total a claim rather than
    # an accounting.
    medium: dict[str, np.ndarray] = {}
    if at_model is not None:
        p = getattr(at_model, "attenuation_conv_params", None)
        if p is not None:
            medium["beta_att"] = p.detach().cpu().numpy().astype(np.float32)
    if bs_model is not None:
        p = getattr(bs_model, "backscatter_conv_params", None)
        if p is not None:
            medium["beta_bs"] = p.detach().cpu().numpy().astype(np.float32)
        b = getattr(bs_model, "B_inf", None)
        if b is not None:
            medium["B_inf"] = b.detach().cpu().numpy().astype(np.float32)
    if learned_bg is not None:
        medium["learned_bg"] = learned_bg.detach().cpu().numpy().astype(np.float32)
    if medium:
        np.savez(out_dir / "medium.npz", **medium)

    with open(out_dir / "meta.json", "w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=2)

    return out_dir


def load_compressed_model(artifact_dir: str | Path) -> dict[str, np.ndarray]:
    """Reconstruct every primitive attribute from a `compressed_*/` store.

    Returns raw (pre-activation) arrays under the model's own attribute names,
    so the caller can install them directly: `xyz`, `opacity`, `features_dc`,
    `scaling`, `rotation`, plus whatever medium tensors were saved.

    **Why this exists.** The store was write-only from the day it was written.
    `measure_model_size` sums file sizes and the collectors read the JSON, but
    nothing ever decoded the bytes back into a model -- which means the
    reported size was a correct accounting of a representation nobody had
    demonstrated was sufficient.  That is a weaker claim than it looks: "model
    size on disk" invites the question of whether the model can be recovered
    from those bytes, and until now the answer was untested.

    It also settles what the full-precision PLY beside it is for.  If this
    function reproduces the model, the PLY is a viewer convenience and not part
    of the claimed artifact; if it does not, the size figure is wrong.
    """
    d = Path(artifact_dir)
    meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
    n = int(meta["num_primitives"])

    out: dict[str, np.ndarray] = {
        "xyz": np.load(d / "xyz.npy"),
        "opacity": np.load(d / "opacity.npy"),
    }

    if meta.get("quantized"):
        cb = np.load(d / "codebooks.npz")
        blob = (d / "indices.bin").read_bytes()
        offset = 0
        # Written in sorted group order; read back the same way or the streams
        # silently swap and every attribute takes another attribute's values.
        for name in sorted(meta["groups"]):
            g = meta["groups"][name]
            nbytes = int(g["packed_bytes"])
            idx = unpack_indices(blob[offset:offset + nbytes], n,
                                 int(g["bits_per_index"]))[:n]
            offset += nbytes
            centers = cb[name]
            out[_GROUP_TO_ATTR[name]] = centers[idx.astype(np.int64)].reshape(
                n, int(g["vec_dim"]))
        if offset != len(blob):
            raise ValueError(
                f"indices.bin has {len(blob)} bytes, groups account for {offset}")
    else:
        for attr, fname in (("features_dc", "features_dc.npy"),
                            ("scaling", "scaling.npy"),
                            ("rotation", "rotation.npy")):
            out[attr] = np.load(d / fname)

    med = d / "medium.npz"
    if med.exists():
        z = np.load(med)
        for k in z.files:
            out[f"medium_{k}"] = z[k]

    return out


def write_decoded_ply(artifact_dir: str | Path, out_path: str | Path) -> dict[str, Any]:
    """Write a viewable PLY from the decoded store, with no normals field.

    **This is not the compressed size and cannot be.** A PLY stores one fixed
    width float per property per primitive, so fourteen attributes at float32
    is 56 bytes per primitive however the values were obtained -- the
    compression lives in replacing ten of those floats with twelve-bit indices,
    which no renderer reads.  The 79 MB store and a renderable PLY are
    different objects, and asking the PLY to be 79 MB is asking it to stop
    being a PLY.

    What this does fix is a real inconsistency: `save_ply` writes the
    *continuous* parameters, so the `point_cloud.ply` sitting in a quantized
    run is **not the model that run reported**.  Opening it in a viewer shows
    the pre-quantization model.  This writer emits the decoded, actually
    quantized values, so the artifact matches the measurement.

    It also drops the three zero-valued normals that `save_ply` inherits from
    vanilla 3DGS -- 3 of 17 floats, about 46 MB per run at 4M primitives, all
    zeros.
    """
    from plyfile import PlyData, PlyElement

    m = load_compressed_model(artifact_dir)
    n = m["xyz"].shape[0]

    cols = [("x", m["xyz"][:, 0]), ("y", m["xyz"][:, 1]), ("z", m["xyz"][:, 2])]
    dc = m["features_dc"].reshape(n, -1)
    for i in range(dc.shape[1]):
        cols.append((f"f_dc_{i}", dc[:, i]))
    cols.append(("opacity", m["opacity"].reshape(-1)))
    sc = m["scaling"].reshape(n, -1)
    for i in range(sc.shape[1]):
        cols.append((f"scale_{i}", sc[:, i]))
    rot = m["rotation"].reshape(n, -1)
    for i in range(rot.shape[1]):
        cols.append((f"rot_{i}", rot[:, i]))

    arr = np.empty(n, dtype=[(name, "f4") for name, _ in cols])
    for name, v in cols:
        arr[name] = v.astype(np.float32)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    PlyData([PlyElement.describe(arr, "vertex")]).write(str(out_path))

    return {"path": str(out_path), "num_primitives": n,
            "floats_per_primitive": len(cols),
            "bytes": out_path.stat().st_size}


def measure_model_size(artifact_dir: str | Path) -> dict[str, Any]:
    """Measure the artifact on disk, component by component.

    Deliberately measures files rather than trusting the analytical count, so
    that the two can be reconciled -- a gap between them means the encoder is
    spending bits the analysis does not know about.
    """
    artifact_dir = Path(artifact_dir)
    with open(artifact_dir / "meta.json", encoding="utf-8") as fh:
        meta = json.load(fh)

    components: dict[str, int] = {}
    for path in sorted(artifact_dir.iterdir()):
        if path.is_file():
            components[path.name] = path.stat().st_size
    total = sum(components.values())

    n = meta["num_primitives"]
    baseline_bytes = n * BASELINE_FLOATS_PER_PRIMITIVE * 4

    report: dict[str, Any] = {
        "artifact_dir": str(artifact_dir),
        "num_primitives": n,
        "components_bytes": components,
        "total_bytes": total,
        "total_mb": round(total / 1024 / 1024, 4),
        "bytes_per_primitive": round(total / max(1, n), 4),
        "baseline": {
            "floats_per_primitive": BASELINE_FLOATS_PER_PRIMITIVE,
            "total_bytes": baseline_bytes,
            "total_mb": round(baseline_bytes / 1024 / 1024, 4),
        },
        "ratio_vs_this_baseline": round(baseline_bytes / max(1, total), 4),
        "note": (
            f"Ratio is against this baseline's {BASELINE_FLOATS_PER_PRIMITIVE} "
            f"floats/primitive (sh_degree=0). The compression literature assumes "
            f"{LITERATURE_FLOATS_PER_PRIMITIVE}; ratios against that are a "
            f"different quantity and must not be tabulated together."
        ),
    }

    if meta.get("quantized"):
        analytical = 0
        for g in meta["groups"].values():
            analytical += g["packed_bytes"]
            analytical += g["num_clusters"] * g["vec_dim"] * 4
        analytical += n * 4 * 4          # xyz(3) + opacity(1), float32
        report["analytical_bytes"] = analytical
        report["measured_over_analytical"] = round(total / max(1, analytical), 4)

    return report
