"""Collect the Chapter IV assets that need the campaign's checkpoints.

    python -m tools.chapter_assets --output_root "$DRIVE_ROOT" --out ch4_assets
    python -m tools.chapter_assets --output_root "$DRIVE_ROOT" --out ch4_assets \\
        --only renders,C1

Everything here needs either a GPU or files that live on Drive, which is why
it runs on Colab and not beside the figure script. It emits two kinds of thing:

  * **data** — CSV and JSON, which the local `figures/make_chapter4_figures.py`
    turns into figures. Numbers are produced once, here, and plotted there.
  * **images** — renders at a view and crop fixed per scene, which are figures
    in themselves.

The fixed view and crops are the point. A figure that compares configurations
must hold the camera and the crop constant or it is not a comparison, so both
are chosen deterministically from the scene name and reused by every cell.

What it produces, keyed to `new-revisited-writing/chapter-04-assets.md`:

  renders  figures 4.2, 4.4, 4.5, 4.6, 4.7, 4.8, 4.13, 4.14
  C1       per_view_metrics.csv       per-image fidelity, seed 0
  C2       depth renders              depth map per configuration
  C3       restoration renders        J-hat per configuration
  C4       depth_range_sweeps.csv     per-frame depth-range distributions
  C5       medium_trajectories.csv    beta_att over training, all 120 runs
  C6       radius_histograms.csv      primitive distance from the camera

**C1 is bounded by the storage policy.** Full point clouds are kept for seed 0
only, so per-image metrics can be recovered for one repeat per cell and scene.
That is enough to show whether a scene mean rests on one bad view; it cannot
show how per-view fidelity varies between repeats. Reported as such.

**The quantised cells need their codebooks installed.** `save_ply` writes the
*continuous* parameters — it reads the raw tensors and bypasses the
quantisation override — so loading a quantised run's point cloud and rendering
it measures a latent the campaign never evaluated. The first version of this
tool did exactly that, and reported quantisation as costing up to 6 dB where
the campaign measured a fraction of one. Every run with a `compressed_*` store
now has its codebook state installed before anything is rendered, and every
run is checked against its own `eval_metrics.json` before the numbers are
written.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any, Iterable, Optional, Sequence

import numpy as np

sys.path.append(str(Path(__file__).resolve().parent.parent))

SCENES: tuple[str, ...] = (
    "Curasao", "IUI3-RedSea", "JapaneseGradens-RedSea", "Panama",
)
CELLS: tuple[str, ...] = (
    "SS", "A0", "A0D", "A1", "A2", "A3", "A4", "A5", "A6", "A7",
)

# The held-out view each scene is shown at, as a fraction of the test set. A
# fraction rather than an index so a scene with three test views and one with
# four both land mid-sequence, away from the endpoints where camera coverage
# is weakest.
FIXED_VIEW: dict[str, float] = {
    "Curasao": 0.5,
    "IUI3-RedSea": 0.5,
    "JapaneseGradens-RedSea": 0.34,
    "Panama": 0.5,
}

# (x, y, w, h) in pixels: a far-field crop and a near-field crop per scene.
# Far-field is where attenuation is strongest and where quantisation damage is
# argued to hide; near-field is where the veiling-haze geometry sits.
CROPS: dict[str, tuple[tuple[int, int, int, int], tuple[int, int, int, int]]] = {
    "Curasao": ((520, 180, 360, 270), (120, 520, 360, 270)),
    "IUI3-RedSea": ((560, 200, 360, 270), (150, 540, 360, 270)),
    "JapaneseGradens-RedSea": ((500, 160, 360, 270), (140, 500, 360, 270)),
    "Panama": ((540, 190, 360, 270), (130, 520, 360, 270)),
}

RENDER_CELLS: tuple[str, ...] = ("A0", "A1", "A2", "A3", "A4")

# The backbone the campaign evaluated with; recorded so the per-view table
# and the aggregates it explains are the same measurement.
LPIPS_NET: str = "vgg"


# ── pure helpers, covered by verify_chapter_assets ───────────────────────

def pick_view_index(scene: str, n_views: int) -> int:
    """The held-out view this scene is always shown at."""
    if n_views <= 0:
        raise ValueError(f"{scene}: no views to choose from")
    frac = FIXED_VIEW.get(scene, 0.5)
    return min(n_views - 1, max(0, int(round(frac * (n_views - 1)))))


def clamp_crop(image_hw: tuple[int, int],
               box: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    """Move a crop inside the image, keeping its size.

    Resizing instead of moving would make two cells' crops different boxes,
    which is the one thing these figures may not do.
    """
    h, w = image_hw
    x, y, bw, bh = box
    bw, bh = min(bw, w), min(bh, h)
    x = max(0, min(x, w - bw))
    y = max(0, min(y, h - bh))
    return x, y, bw, bh


def per_view_rows(cell: str, scene: str, seed: int,
                  records: Iterable[dict]) -> list[dict[str, Any]]:
    """One row per held-out image, with its identity columns."""
    rows: list[dict[str, Any]] = []
    for rec in records:
        row: dict[str, Any] = {"cell": cell, "scene": scene, "seed": seed}
        row.update(rec)
        rows.append(row)
    return rows


def radius_histogram(xyz: np.ndarray, centre: np.ndarray,
                     bins: int = 40) -> tuple[list[float], list[float]]:
    """Normalised distribution of primitive distance from a point."""
    d = np.linalg.norm(np.asarray(xyz, dtype=float) - np.asarray(centre, dtype=float), axis=1)
    counts, edges = np.histogram(d, bins=bins)
    total = counts.sum()
    frac = (counts / total) if total else counts.astype(float)
    return [float(e) for e in edges], [float(v) for v in frac]


def write_manifest(out: Path, expected: dict[str, str]) -> None:
    """Record what actually landed, so a partial run is visible as partial."""
    written = {name: tag for name, tag in expected.items() if (out / name).exists()}
    absent = {name: tag for name, tag in expected.items() if name not in written}
    (out / "assets_manifest.json").write_text(
        json.dumps({"written": written, "absent": absent}, indent=2),
        encoding="utf-8")


def _write_csv(path: Path, rows: Sequence[dict[str, Any]]) -> None:
    if not rows:
        return
    keys: list[str] = []
    for row in rows:
        for k in row:
            if k not in keys:
                keys.append(k)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)


def _runs(root: Path,
          only_cells: Optional[Sequence[str]] = None) -> list[tuple[str, str, int, Path]]:
    found: list[tuple[str, str, int, Path]] = []
    runs_dir = root / "runs"
    for cell in (only_cells or CELLS):
        for scene in SCENES:
            for seed in (0, 1, 2):
                d = runs_dir / cell / scene / f"s{seed}"
                if d.is_dir():
                    found.append((cell, scene, seed, d))
    return found


# ── C5: medium trajectories, all runs ────────────────────────────────────

def collect_medium_trajectories(root: Path, out: Path) -> int:
    """beta_att, beta_bs and B_inf against iteration, for every run.

    The analysis bundle carried diagnostics for the 48 simplification runs
    only; Drive has all 120. This is what lets Chapter IV show the baseline's
    own medium converging and staying put, rather than asserting it from a
    collapse count.
    """
    rows: list[dict[str, Any]] = []
    for cell, scene, seed, d in _runs(root):
        path = d / "diagnostics.csv"
        if not path.is_file():
            continue
        for rec in csv.DictReader(open(path, encoding="utf-8")):
            if not rec.get("beta_att_r"):
                continue
            it = int(rec["iteration"])
            if it % 500 and rec.get("event") == "periodic":
                continue
            row: dict[str, Any] = {
                "cell": cell, "scene": scene, "seed": seed,
                "iteration": it, "event": rec.get("event", ""),
            }
            for key in ("beta_att_r", "beta_att_g", "beta_att_b",
                        "beta_bs_r", "beta_bs_g", "beta_bs_b",
                        "binf_r", "binf_g", "binf_b", "n_primitives"):
                if rec.get(key):
                    row[key] = float(rec[key])
            rows.append(row)
    _write_csv(out / "medium_trajectories.csv", rows)
    return len(rows)


# ── C4: per-frame depth-range distributions ──────────────────────────────

def collect_depth_range_sweeps(root: Path, out: Path) -> int:
    """The cross-frame depth-range statistics at every sweep.

    These are the quantity the registered explanation was about. Reporting the
    distribution, not only the ratio the analysis tested, lets the chapter show
    that the distribution does move across a cut while the outcome does not
    follow it.
    """
    rows: list[dict[str, Any]] = []
    for cell, scene, seed, d in _runs(root):
        path = d / "diagnostics.csv"
        if not path.is_file():
            continue
        for rec in csv.DictReader(open(path, encoding="utf-8")):
            if not rec.get("zr_mean"):
                continue
            row: dict[str, Any] = {
                "cell": cell, "scene": scene, "seed": seed,
                "iteration": int(rec["iteration"]), "event": rec.get("event", ""),
            }
            for key in ("zr_n_views", "zr_mean", "zr_sd", "zr_cv",
                        "zr_min", "zr_max", "n_primitives"):
                if rec.get(key):
                    row[key] = float(rec[key])
            rows.append(row)
    _write_csv(out / "depth_range_sweeps.csv", rows)
    return len(rows)


# ── C6: primitive distance from the camera ───────────────────────────────

def collect_radius_histograms(root: Path, out: Path, bins: int = 40) -> int:
    """Where each configuration puts its primitives, relative to the cameras.

    Direct evidence for the account of the invisible population: before the
    medium model activates, veiling haze must be paid for by geometry, and the
    optimiser is argued to recruit low-opacity primitives near the camera.
    """
    from plyfile import PlyData

    rows: list[dict[str, Any]] = []
    for cell, scene, seed, d in _runs(root):
        if seed != 0:
            continue
        plys = sorted(d.glob("point_cloud/iteration_*/point_cloud.ply"))
        if not plys:
            continue
        data = PlyData.read(str(plys[-1]))["vertex"]
        xyz = np.stack([data["x"], data["y"], data["z"]], axis=1)
        centre = xyz.mean(axis=0)
        edges, frac = radius_histogram(xyz, centre, bins=bins)
        for i, share in enumerate(frac):
            rows.append({
                "cell": cell, "scene": scene, "seed": seed,
                "bin_lo": edges[i], "bin_hi": edges[i + 1],
                "fraction": share, "n_points": int(xyz.shape[0]),
            })
    _write_csv(out / "radius_histograms.csv", rows)
    return len(rows)


# ── C1 + renders: everything that needs the GPU ──────────────────────────

SELFCHECK_TOL_DB: float = 0.5


def selfcheck_verdict(mine: float, expected: Optional[float],
                      tol: float = SELFCHECK_TOL_DB) -> tuple[Optional[float], str]:
    """Compare a recomputed mean against the run's own recorded evaluation.

    Same run, same views, same conventions, so the two should agree to within
    the render path's tolerance. A disagreement means the model was rendered in
    a state the campaign never evaluated -- precisely the defect that made the
    first version of this tool report quantisation as costing six decibels.
    """
    if expected is None:
        return None, "no eval_metrics"
    delta = round(mine - expected, 4)
    return delta, "ok" if abs(delta) <= tol else "MISMATCH"


def _selfcheck(d: Path, mine: float) -> tuple[Optional[float], Optional[float], str]:
    path = d / "eval_metrics.json"
    expected: Optional[float] = None
    if path.is_file():
        try:
            block = json.loads(path.read_text(encoding="utf-8")).get("Test") or {}
            value = block.get("psnr_pooled")
            expected = round(float(value), 4) if value is not None else None
        except (ValueError, TypeError):
            expected = None
    delta, verdict = selfcheck_verdict(mine, expected)
    return expected, delta, verdict


def _quant_overrides(d: Path):
    """The codebook state for a run, or None if it was not quantised.

    Mirrors what the training loop installs, and what `j_consistency` compares
    against: the override lands on the RAW parameters, so the model's own
    activation applies afterwards.
    """
    import torch
    from source.storage import unpack_indices
    from tools.j_consistency import GROUP_TO_ATTR, STORE_GLOB, reconstruct_quantized

    stores = sorted(d.glob(f"{STORE_GLOB}/meta.json"))
    if not stores:
        return None
    store = stores[-1].parent
    meta = json.loads(stores[-1].read_text(encoding="utf-8"))
    cb = np.load(store / "codebooks.npz")
    packed = (store / "indices.bin").read_bytes()

    overrides: dict[str, Any] = {}
    n = int(meta["num_primitives"])
    offset = 0
    for name in sorted(meta["groups"]):
        g = meta["groups"][name]
        bits = int(g["index_bits"])
        size = (n * bits + 7) // 8
        idx = unpack_indices(packed[offset:offset + size], n, bits)
        offset += size
        arr = reconstruct_quantized(cb[name], idx, int(g["vec_dim"]))
        t = torch.from_numpy(np.ascontiguousarray(arr)).float().cuda()
        if name == "dc":
            t = t.reshape(t.shape[0], 1, 3)
        overrides[GROUP_TO_ATTR[name]] = t
    return overrides


def _load_run(d: Path, source: Path, sh_degree: int = 0):
    """Model, scene and medium for one run, through the real parsers."""
    import torch
    from argparse import ArgumentParser
    from arguments import ModelParams, PipelineParams
    from deepseecolor.models import AttenuateNetV3, BackscatterNetV2
    from scene import GaussianModel, Scene

    plys = sorted(d.glob("point_cloud/iteration_*/point_cloud.ply"))
    if not plys:
        return None
    iteration = int(plys[-1].parent.name.split("_")[-1])

    gaussians = GaussianModel(sh_degree)
    gaussians.load_ply(str(plys[-1]))

    parser = ArgumentParser()
    lp = ModelParams(parser)
    mp = lp.extract(parser.parse_args([
        "-s", str(source), "--model_path", str(d),
        "--images", "images", "--resolution", "-1", "--eval",
    ]))
    scene = Scene(mp, gaussians, load_iteration=-1, shuffle=False)

    pp = ArgumentParser()
    pipe = PipelineParams(pp).extract(pp.parse_args([]))

    at = bs = None
    at_path = d / f"attenuate_{iteration}.pth"
    bs_path = d / f"backscatter_{iteration}.pth"
    if at_path.is_file() and bs_path.is_file():
        at = AttenuateNetV3(scale=5.0).cuda()
        bs = BackscatterNetV2(use_residual=False, scale=5.0).cuda()
        at.load_state_dict(torch.load(at_path))
        bs.load_state_dict(torch.load(bs_path))
        at.eval()
        bs.eval()
    return gaussians, scene, pipe, at, bs, iteration


def collect_per_view_and_renders(root: Path, out: Path, source_root: Path,
                                 do_renders: bool = True,
                                 only_cells: Optional[Sequence[str]] = None
                                 ) -> tuple[int, int]:
    """C1, C2, C3 and the render figures, in one pass over seed-0 checkpoints."""
    import torch
    import torchvision
    from gaussian_renderer import render, render_depth
    from lpipsPyTorch import lpips
    from utils.loss_utils import ssim
    from utils.depth_stats import normalise_depth
    # The campaign's own conventions, not a second implementation of them:
    # pooled PSNR, full-frame and unmasked, one LPIPS backbone. Recomputing
    # these by hand is how a per-view table ends up incomparable with the
    # aggregates it is supposed to explain.
    from utils.metrics_conventions import evaluate_pair

    img_dir = out / "renders"
    img_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    checks: list[dict[str, Any]] = []
    n_images = 0

    for cell, scene, seed, d in _runs(root, only_cells):
        if seed != 0:
            continue
        loaded = _load_run(d, source_root / scene)
        if loaded is None:
            print(f"  {cell}/{scene}: no point cloud, skipped")
            continue
        gaussians, sc, pipe, at, bs, iteration = loaded
        views = sc.getTestCameras() or sc.getTrainCameras()
        if not views:
            continue

        # A quantised run must be rendered in its codebook state. The stored
        # point cloud holds the continuous parameters, which the campaign never
        # evaluated and which score several dB lower.
        overrides = _quant_overrides(d)
        state = "continuous"
        if overrides:
            for attr, tensor in overrides.items():
                gaussians.set_quant_override(attr, tensor)
            state = "codebook"
        keep = pick_view_index(scene, len(views))
        bg = torch.zeros(3, device="cuda")

        with torch.no_grad():
            records: list[dict[str, Any]] = []
            for idx, cam in enumerate(views):
                gt = cam.original_image.cuda().clamp(0, 1)
                j = render(cam, gaussians, pipe, bg)["render"].clamp(0, 1)

                probe = render_depth(cam, gaussians, pipe, bg)
                depth, _, _ = normalise_depth(probe["depth"], probe["alpha"],
                                              1.0, True, True, nan_label=None)
                if at is not None:
                    dd = depth.unsqueeze(0)
                    att = at(dd)
                    back = bs(dd)
                    img = (j.unsqueeze(0) * att + back).clamp(0, 1).squeeze(0)
                else:
                    att = back = None
                    img = j

                rec = evaluate_pair(img, gt, ssim, lpips, lpips_net=LPIPS_NET)
                rec["image"] = getattr(cam, "image_name", f"view_{idx}")
                rec["state"] = state
                records.append(rec)
                n_images += 1

                if do_renders and idx == keep and cell in RENDER_CELLS:
                    stem = f"{scene}_{cell}"
                    save = torchvision.utils.save_image
                    save(gt, img_dir / f"{stem}_gt.png")
                    save(img, img_dir / f"{stem}_composed.png")
                    save(j, img_dir / f"{stem}_restored.png")       # C3
                    save(depth, img_dir / f"{stem}_depth.png")      # C2
                    if att is not None:
                        save(att.squeeze(0), img_dir / f"{stem}_attenuation.png")
                        save(back.squeeze(0), img_dir / f"{stem}_backscatter.png")

            rows.extend(per_view_rows(cell, scene, seed, records))

        mine = sum(r["psnr_pooled"] for r in records) / len(records)
        expected, delta, verdict = _selfcheck(d, mine)
        checks.append({"cell": cell, "scene": scene, "seed": seed, "state": state,
                       "per_view_mean": round(mine, 4),
                       "eval_metrics": expected, "delta": delta, "verdict": verdict})
        print(f"  {cell}/{scene}: {len(records)} views, {state} state, "
              f"mean {mine:.2f} vs eval_metrics {expected} -> {verdict}")
        gaussians.clear_quant_override()
        del gaussians, sc
        torch.cuda.empty_cache()

    _write_csv(out / "per_view_metrics.csv", rows)
    _write_csv(out / "per_view_selfcheck.csv", checks)
    bad = [c for c in checks if c["verdict"] != "ok"]
    if bad:
        print(f"\n  {len(bad)} run(s) disagree with their own eval_metrics.json:")
        for c in bad:
            print(f"    {c['cell']}/{c['scene']} {c['state']}: "
                  f"{c['per_view_mean']} vs {c['eval_metrics']} ({c['verdict']})")
        print("  Do not use per_view_metrics.csv for those rows until it is understood.")
    (out / "renders" / "README.txt").write_text(
        "One held-out view per scene, chosen deterministically by scene name and\n"
        "reused by every configuration, so the panels of a figure are comparable.\n"
        "Crop rectangles are in tools/chapter_assets.py (CROPS) and are applied\n"
        "when the figure is assembled, not here, so the full frame stays available.\n",
        encoding="utf-8")
    return len(rows), n_images


EXPECTED: dict[str, str] = {
    "per_view_metrics.csv": "C1 per-image fidelity, seed 0 only",
    "depth_range_sweeps.csv": "C4 per-frame depth-range distributions",
    "medium_trajectories.csv": "C5 medium parameters over training, all runs",
    "radius_histograms.csv": "C6 primitive distance from the cloud centre",
}


def main() -> int:
    ap = argparse.ArgumentParser(description="collect Chapter IV assets from the campaign")
    ap.add_argument("--output_root", required=True, help="campaign root holding runs/")
    ap.add_argument("--out", required=True, help="directory to write assets into")
    ap.add_argument("--source_root", default=None,
                    help="dataset root holding <scene>/; defaults to "
                         "<output_root>/dataset/undistorted")
    ap.add_argument("--only", default="all",
                    help="comma-separated subset of: renders,C1,C4,C5,C6")
    ap.add_argument("--cells", default=None,
                    help="comma-separated cells to process, e.g. A3,A5,A6,A7. "
                         "Applies to C1 and the renders; used to redo part of a "
                         "collection without repeating the whole pass.")
    args = ap.parse_args()

    root = Path(args.output_root)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    source_root = Path(args.source_root) if args.source_root else \
        root / "dataset" / "undistorted"

    want = {w.strip() for w in args.only.split(",")} if args.only != "all" else \
        {"renders", "C1", "C4", "C5", "C6"}

    if "C5" in want:
        print("C5 medium trajectories, all runs")
        print(f"  {collect_medium_trajectories(root, out)} rows")
    if "C4" in want:
        print("C4 depth-range sweeps")
        print(f"  {collect_depth_range_sweeps(root, out)} rows")
    if "C6" in want:
        print("C6 radius histograms, seed 0")
        print(f"  {collect_radius_histograms(root, out)} rows")
    if want & {"C1", "renders"}:
        print("C1 per-view metrics and the render figures, seed 0")
        cells = [c.strip() for c in args.cells.split(",")] if args.cells else None
        if cells:
            print(f"  restricted to {cells}")
        rows, imgs = collect_per_view_and_renders(
            root, out, source_root, do_renders="renders" in want, only_cells=cells)
        print(f"  {rows} rows over {imgs} images")

    write_manifest(out, EXPECTED)
    if args.cells:
        note = (
            "Partial collection: cells " + str(args.cells)
            + ", products " + str(sorted(want)) + "." + chr(10)
            + "Merge into the full bundle rather than replacing it." + chr(10)
        )
        (out / "PARTIAL.txt").write_text(note, encoding="utf-8")
    print(f"\nwritten to {out}")
    print("Bundle this directory and unpack it beside analysis/campaign-2026-09/,")
    print("then rerun figures/make_chapter4_figures.py locally.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
