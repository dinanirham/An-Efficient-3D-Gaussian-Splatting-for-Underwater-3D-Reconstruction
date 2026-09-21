"""Restored-image (J-hat) self-consistency for quantized cells (CD-28).

    python -m tools.j_consistency --output_root "$DRIVE_ROOT" [--json out.json]

**The measurement gap this closes.** A physically-grounded underwater method
produces two images: the in-medium reconstruction, which has ground truth, and
the restored medium-free image `J-hat`, which is the scientific point of the
exercise and can never have any -- obtaining it would require removing the
water. Every fidelity number in this study therefore scores the composed image.

That is not merely incomplete, it is biased in a specific direction.
Quantization error enters `J-hat` directly, since `J-hat` is built from the
quantized colour coefficients, but before it reaches the measured in-medium
image it is multiplied by the attenuation map, which is at most one and
approaches zero at range. **The fidelity metrics attenuate the evidence of
quantization damage in exactly the far-field, red-starved regions where
restoration matters most.** This tool is the only available quantitative proxy
for what is being hidden there.

**One model, two states.** The methodology specifies comparison against "the
otherwise-identical unquantized model", which reads naturally as the
matched-seed unquantized cell. That reading is confounded: same-seed runs
diverge by a median 21% in primitive count (E.22), so an A0-vs-A3 difference
mixes quantization damage with trajectory divergence at the same order of
magnitude.

The clean comparison needs no second run. `save_ply` writes the *continuous*
parameters -- it reads `_features_dc`, `_scaling` and `_rotation` directly,
bypassing the quantization override -- while `codebooks.npz` and `indices.bin`
sit beside it. A single stored run therefore carries both states, and swapping
between them holds everything else fixed: same positions, same opacities, same
view, same medium. What differs is only whether three attributes take their
continuous or their codebook values.

**What it is and is not.** A consistency measure, not an accuracy measure. It
can show that quantization *changed* the restoration; it can never show the
change was toward or away from truth. Reported as secondary, never aggregated
into a headline.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import numpy as np

sys.path.append(str(Path(__file__).resolve().parent.parent))

from source.storage import unpack_indices  # noqa: E402

# The quantizer's group names, and the raw model attribute each overrides.
# Overrides are installed on the RAW parameters, so the model's own activation
# (exp for scale, normalise for rotation) applies afterwards -- which is what
# "quantize before activation" means in practice.
GROUP_TO_ATTR: dict[str, str] = {
    "dc": "features_dc",
    "scale": "scaling",
    "rotation": "rotation",
}

PSNR_CAP = 100.0   # identical images; reported rather than inf

# The compressed store's directory, as train.py names it: compressed_<iter>.
# The first version of this tool globbed for "compact/", which nothing has
# ever written, so it found no runs and reported that as "unquantized cells
# are skipped by design" -- a message that was true and a search that was
# looking in the wrong place. verify_j_consistency T11 reads train.py's
# source and fails if this pattern drifts from what it actually writes.
STORE_GLOB = "compressed_*"


def psnr_pooled(a: np.ndarray, b: np.ndarray) -> float:
    """Pooled convention: one MSE over all pixels and channels, converted once.

    Pinned rather than inherited. The per-channel convention averages three
    separate ratios and is always larger by Jensen's inequality, and the gap is
    widest exactly in underwater imagery, where the channels' errors diverge
    most -- nearly 12 dB on a synthetic underwater-like profile. A self
    consistency figure computed under the other convention would not be
    comparable with anything else this study reports.
    """
    mse = float(((a.astype(np.float64) - b.astype(np.float64)) ** 2).mean())
    if mse <= 0.0:
        return PSNR_CAP
    return min(PSNR_CAP, 10.0 * float(np.log10(1.0 / mse)))


def reconstruct_quantized(
    centers: np.ndarray, indices: np.ndarray, vec_dim: int
) -> np.ndarray:
    """The codebook lookup: one centroid per primitive, shaped (N, vec_dim)."""
    out = centers[indices]
    return out.reshape(indices.shape[0], vec_dim)


@dataclass
class StoredRun:
    cell: str
    scene: str
    seed: int
    store: Path
    meta: dict[str, Any]
    complete: bool = True
    why: str = ""
    groups: dict[str, np.ndarray] = field(default_factory=dict)


def discover_quantized_runs(output_root: Path) -> list[StoredRun]:
    """Find stored runs whose meta declares quantization, and load codebooks.

    Unquantized cells are skipped rather than paired with anything: without M3
    there is no quantization to measure, and inventing a comparison would be
    reporting trajectory divergence under this metric's name.
    """
    # output_root is the campaign root -- $DRIVE_ROOT -- and the runs live
    # one level down, exactly as collect_results, medium_collapse and
    # spatial_extent resolve it. The first two versions of this tool globbed
    # from output_root directly and so could not reach a single run; the
    # message they printed, "no quantized runs found", was true of the
    # search and false of the campaign.
    runs: list[StoredRun] = []
    runs_dir = output_root / "runs"
    for meta_path in sorted(runs_dir.glob(f"*/*/s*/{STORE_GLOB}/meta.json")):
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not meta.get("quantized"):
            continue

        store = meta_path.parent
        seed_dir = store.parent
        run = StoredRun(
            cell=seed_dir.parent.parent.name,
            scene=seed_dir.parent.name,
            seed=int(seed_dir.name.lstrip("s") or 0),
            store=store,
            meta=meta,
        )

        cb_path = store / "codebooks.npz"
        idx_path = store / "indices.bin"
        if not cb_path.exists() or not idx_path.exists():
            run.complete = False
            run.why = "codebooks.npz or indices.bin missing"
            runs.append(run)
            continue

        n = int(meta["num_primitives"])
        try:
            cb = np.load(cb_path)
            blob = idx_path.read_bytes()
            offset = 0
            # Written in sorted group order; read back the same way.
            for name in sorted(meta["groups"]):
                g = meta["groups"][name]
                nbytes = int(g["packed_bytes"])
                idx = unpack_indices(blob[offset:offset + nbytes], n,
                                    int(g["bits_per_index"]))[:n]
                offset += nbytes
                run.groups[name] = reconstruct_quantized(
                    cb[name], idx.astype(np.int64), int(g["vec_dim"])
                )
        except (OSError, KeyError, ValueError) as exc:
            run.complete = False
            run.why = f"{type(exc).__name__}: {exc}"

        runs.append(run)
    return runs


# ---------------------------------------------------------------------------
# Rendering. Imported lazily so the pure parts stay testable without CUDA.
# ---------------------------------------------------------------------------


def measure_run(run: StoredRun, source_path: str, resolution: int = -1) -> Optional[dict]:
    """Render every held-out view twice and return the per-view PSNR.

    Requires the rasterizer, so this runs on the campaign hardware. The two
    renders differ only in whether the three quantized attributes carry their
    continuous or their codebook values; positions, opacities, camera and
    medium are untouched between them.
    """
    import torch
    from argparse import ArgumentParser

    from gaussian_renderer import render
    from scene import GaussianModel, Scene

    ply = run.store.parent / "point_cloud" / "iteration_30000" / "point_cloud.ply"
    if not ply.exists():
        cands = sorted((run.store.parent).glob("point_cloud/iteration_*/point_cloud.ply"))
        if not cands:
            return None
        ply = cands[-1]

    gaussians = GaussianModel(int(run.meta.get("sh_degree", 0)))
    gaussians.load_ply(str(ply))

    # Through the real parsers, never a hand-built Namespace. Scene reads
    # subsample, start_cam, end_cam, rescale_units, scene_bounds_xxyyzz and
    # skip_first_n_images; a Namespace listing only the obvious fields raised
    # on the first of those in measure_reference, after the model had loaded
    # and rendered. The set of fields is whatever Scene reads today and after
    # the next change to it.
    from arguments import ModelParams, PipelineParams
    _mp = ArgumentParser()
    _lp = ModelParams(_mp)
    mp = _lp.extract(_mp.parse_args([
        "-s", str(source_path), "--model_path", str(run.store.parent),
        "--images", "images", "--resolution", str(resolution), "--eval",
    ]))
    scene = Scene(mp, gaussians, load_iteration=-1, shuffle=False)
    cams = scene.getTestCameras() or scene.getTrainCameras()

    _pp = ArgumentParser()
    pipe = PipelineParams(_pp).extract(_pp.parse_args([]))
    bg = torch.zeros(3, device="cuda")

    # Codebook values as raw-parameter overrides, matching AttributeQuantizer.apply.
    overrides = {}
    for name, arr in run.groups.items():
        t = torch.from_numpy(np.ascontiguousarray(arr)).float().cuda()
        if name == "dc":
            t = t.reshape(t.shape[0], 1, 3)   # features_dc is (N, 1, 3)
        overrides[GROUP_TO_ATTR[name]] = t

    per_view: list[float] = []
    with torch.no_grad():
        for cam in cams:
            gaussians.clear_quant_override()
            j_cont = render(cam, gaussians, pipe, bg)["render"].clamp(0, 1)

            for attr, t in overrides.items():
                gaussians.set_quant_override(attr, t)
            j_quant = render(cam, gaussians, pipe, bg)["render"].clamp(0, 1)
            gaussians.clear_quant_override()

            per_view.append(psnr_pooled(j_cont.cpu().numpy(), j_quant.cpu().numpy()))

    if not per_view:
        return None
    return {
        "n_views": len(per_view),
        "psnr_mean": round(float(np.mean(per_view)), 4),
        "psnr_min": round(float(np.min(per_view)), 4),
        "psnr_max": round(float(np.max(per_view)), 4),
        "psnr_sd": round(float(np.std(per_view)), 4),
        "per_view": [round(v, 4) for v in per_view],
    }


def main() -> int:
    if len(sys.argv) > 3 and sys.argv[1] == "--write_ply":
        return _cli_write_ply(sys.argv[2:4])

    ap = argparse.ArgumentParser(
        description="restored-image (J-hat) self-consistency, quantized vs continuous")
    ap.add_argument("--output_root", required=True)
    ap.add_argument("--source_root", default=None,
                    help="dataset root holding <scene>/; defaults to "
                         "<output_root>/dataset/undistorted, where 00_setup "
                         "writes it")
    ap.add_argument("--json", default=None)
    args = ap.parse_args()

    root = Path(args.output_root)
    src_root = Path(args.source_root) if args.source_root else \
        root / "dataset" / "undistorted"   # inside the campaign root, not beside it

    runs = discover_quantized_runs(root)
    if not runs:
        print("no quantized runs found -- A3/A5/A6/A7 store codebooks.npz; "
              "unquantized cells are skipped by design")
        return 0

    with_ply = sum(1 for r in runs if r.complete and
                   list((r.store.parent / "point_cloud").glob("iteration_*/point_cloud.ply")))
    print(f"{len(runs)} quantized run(s) found; {with_ply} carry a full-precision PLY.")
    print("Only those are measurable: the PLY holds the continuous parameters this")
    print("metric compares against, and train.py keeps it for seed 0 alone.\n")
    print(f"{'run':<30} {'views':>6} {'J-hat PSNR':>11} {'min':>8} {'max':>8}")
    print("-" * 68)

    report: dict[str, Any] = {}
    for r in runs:
        rid = f"{r.cell}/{r.scene}/s{r.seed}"
        if not r.complete:
            print(f"{rid:<30} {'-':>6} {'SKIPPED':>11}   {r.why}")
            report[rid] = {"skipped": r.why}
            continue
        try:
            m = measure_run(r, str(src_root / r.scene))
        except Exception as exc:  # noqa: BLE001
            print(f"{rid:<30} {'-':>6} {'ERROR':>11}   {type(exc).__name__}: {exc}")
            report[rid] = {"error": f"{type(exc).__name__}: {exc}"}
            continue
        if m is None:
            # Not missing data: train.py keeps the ~300 MB full-precision PLY
            # for seed 0 only (--save_ply_all_seeds to keep them all), and the
            # compressed store holds the QUANTIZED attributes alone. This
            # metric needs the continuous ones too, so it is computable for
            # one seed per quantized cell per scene -- 16 runs, not 48 -- and
            # is reported at n=1 per scene, never as if three seeds existed.
            print(f"{rid:<30} {'-':>6} {'NO PLY':>11}   seed>0: PLY not kept "
                  f"under the storage policy; continuous params unavailable")
            report[rid] = {"skipped": "no PLY -- seed>0 keeps only the compressed "
                                      "store; needs continuous parameters"}
            continue
        print(f"{rid:<30} {m['n_views']:>6} {m['psnr_mean']:>11.2f} "
              f"{m['psnr_min']:>8.2f} {m['psnr_max']:>8.2f}")
        report[rid] = m

    print()
    print("A consistency measure, not an accuracy measure: it shows that")
    print("quantization CHANGED the restored image, never that the change was")
    print("toward or away from truth. Report as secondary.")
    print()
    print(f"A value at the {PSNR_CAP:.0f} dB cap means the two renders were identical,")
    print("which is a BUG signal, not a result -- the override did not take.")

    if args.json:
        Path(args.json).write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"\nwritten: {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


def _cli_write_ply(argv: list[str]) -> int:
    """`python -m tools.j_consistency --write_ply <compressed_dir> <out.ply>`.

    Emits a viewable PLY from the decoded store, so the artifact a viewer opens
    for a quantized run is the model that run reported. `save_ply` writes the
    CONTINUOUS parameters, so the `point_cloud.ply` currently sitting in an A3
    run is the pre-quantization model -- not A3.
    """
    from source.storage import write_decoded_ply

    src, dst = argv[0], argv[1]
    info = write_decoded_ply(src, dst)
    mb = info["bytes"] / 1024 / 1024
    print(f"wrote {info['path']}")
    print(f"  {info['num_primitives']:,} primitives, "
          f"{info['floats_per_primitive']} floats each -> {mb:.2f} MB")
    print()
    print("This is the quantized model, viewable. It is NOT the compressed size")
    print("and cannot be: a PLY stores one fixed-width float per property, so")
    print("14 attributes at float32 is 56 bytes/primitive however the values")
    print("were obtained. The compression lives in replacing 10 of those floats")
    print("with 12-bit indices, which no renderer reads. The compressed store")
    print("and a renderable PLY are different objects.")
    return 0
