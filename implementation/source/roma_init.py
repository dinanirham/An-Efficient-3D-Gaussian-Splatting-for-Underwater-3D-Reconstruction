"""M1 offline stage: dense correspondence initialization.

    python -m source.roma_init --source_path <scene> --output <scene>/dense/a1.ply --seed 0

Replaces COLMAP's sparse points with a dense cloud triangulated from
pretrained dense correspondences, so that training can proceed with
densification switched off.  Runs once per scene per density preset; the
resulting cloud is the experimental condition for cells A1, A4, A5 and A7.

Four decisions that differ from a naive port, each because this domain or this
dataset differs from the one the source method was tuned on:

* **Train cameras only.**  Correspondences are drawn exclusively from training
  views.  Using held-out frames to build the initial geometry would leak the
  test set into the model through the initialization -- a leak no metric would
  reveal, since the leaked information arrives as geometry rather than as
  supervision.

* **`K_ref = min(num_refs, V)`.**  The upstream default of 180 reference views
  exceeds the *total* view count of every scene in this corpus (18-29), which
  would ask k-means for more clusters than it has points.  The realised value
  is recorded, because it puts the configuration off the saturation curve the
  source method published.

* **Batched triangulation.**  One `torch.linalg.svd` over all correspondences
  rather than a per-pair Python loop.

* **Seeded and hashed.**  The matcher's sampling is stochastic; an unseeded,
  unversioned cloud makes four cells of the matrix unattributable, because
  two runs would give different point counts and hence different "efficiency"
  numbers with no way to separate that from a real effect.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import random
import sys
import time
from pathlib import Path

import numpy as np
import torch

sys.path.append(str(Path(__file__).resolve().parent.parent))

# `scene` and the matcher are imported inside main(): importing `scene` pulls in
# GaussianModel, which needs the compiled simple_knn CUDA extension.  Keeping
# it out of module scope lets the geometry functions below be imported -- and
# unit-tested -- on a machine with no GPU and no built extensions.
from utils.dense_init_io import write_dense_pcd  # noqa: E402

# Density presets.  `matches_per_ref` is the dial that decides whether the A2
# budget can bind on the A1-derived cells: with densification disabled the
# primitive count can never grow, so if the cloud comes in below the budget
# then A4 collapses onto A1 and A7 onto A5.  See G-2 in the execution prompt.
PRESETS: dict[str, dict] = {
    "sparse": {"matches_per_ref": 5000, "certainty_thresh": 0.05, "nns_per_ref": 3},
    "dense": {"matches_per_ref": 20000, "certainty_thresh": 0.02, "nns_per_ref": 3},
}


def seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


# ---------------------------------------------------------------------------
# camera geometry
# ---------------------------------------------------------------------------


def intrinsics(cam) -> np.ndarray:
    """K from the field-of-view stored by the 3DGS scene reader."""
    fx = cam.width / (2.0 * math.tan(cam.FovX * 0.5))
    fy = cam.height / (2.0 * math.tan(cam.FovY * 0.5))
    return np.array(
        [[fx, 0.0, cam.width / 2.0],
         [0.0, fy, cam.height / 2.0],
         [0.0, 0.0, 1.0]],
        dtype=np.float64,
    )


def world_to_camera(cam) -> np.ndarray:
    """4x4 world->camera.

    The scene reader stores `R` already transposed (it builds world-to-view as
    `R.transpose()`), so the world-to-camera rotation is `R.T`.
    """
    m = np.eye(4, dtype=np.float64)
    m[:3, :3] = cam.R.T
    m[:3, 3] = cam.T
    return m


def projection(cam) -> np.ndarray:
    """3x4 world->pixel projection matrix."""
    return intrinsics(cam) @ world_to_camera(cam)[:3, :]


def select_references(cams: list, k: int, seed: int) -> list[int]:
    """K-means over flattened world-to-camera matrices; keep the nearest member."""
    from sklearn.cluster import KMeans

    feats = np.stack([world_to_camera(c).flatten() for c in cams])
    k = max(1, min(k, len(cams)))
    if k == len(cams):
        return list(range(len(cams)))

    km = KMeans(n_clusters=k, n_init=10, random_state=seed).fit(feats)
    picks: list[int] = []
    for c in range(k):
        d = np.linalg.norm(feats - km.cluster_centers_[c], axis=1)
        picks.append(int(np.argmin(d)))
    return sorted(set(picks))


def nearest_neighbours(cams: list, i: int, j: int) -> list[int]:
    """`j` closest views to `i` by Frobenius distance between camera matrices."""
    feats = np.stack([world_to_camera(c).flatten() for c in cams])
    d = np.linalg.norm(feats - feats[i], axis=1)
    d[i] = np.inf
    return np.argsort(d)[:j].tolist()


# ---------------------------------------------------------------------------
# triangulation
# ---------------------------------------------------------------------------


def triangulate(
    P_a: np.ndarray, P_b: np.ndarray, uv_a: torch.Tensor, uv_b: torch.Tensor
) -> torch.Tensor:
    """Batched two-view DLT. Returns world points, shape (N, 3).

    For each view, a pixel (u, v) contributes two rows:
        u * P[2] - P[0] = 0
        v * P[2] - P[1] = 0
    Stacking both views gives a 4x4 homogeneous system per correspondence,
    solved as the right singular vector of least singular value -- all of them
    in one batched SVD.
    """
    dev = uv_a.device
    Pa = torch.as_tensor(P_a, dtype=torch.float32, device=dev)
    Pb = torch.as_tensor(P_b, dtype=torch.float32, device=dev)

    n = uv_a.shape[0]
    A = torch.empty((n, 4, 4), dtype=torch.float32, device=dev)
    A[:, 0] = uv_a[:, 0:1] * Pa[2] - Pa[0]
    A[:, 1] = uv_a[:, 1:2] * Pa[2] - Pa[1]
    A[:, 2] = uv_b[:, 0:1] * Pb[2] - Pb[0]
    A[:, 3] = uv_b[:, 1:2] * Pb[2] - Pb[1]

    _, _, Vh = torch.linalg.svd(A)
    X = Vh[:, -1, :]
    w = X[:, 3:4]
    w = torch.where(w.abs() < 1e-12, torch.full_like(w, 1e-12), w)
    return X[:, :3] / w


def reprojection_error(
    P: np.ndarray, pts: torch.Tensor, uv: torch.Tensor
) -> tuple[torch.Tensor, torch.Tensor]:
    """Pixel error and camera-frame depth for `pts` seen at `uv`."""
    dev = pts.device
    Pm = torch.as_tensor(P, dtype=torch.float32, device=dev)
    homo = torch.cat([pts, torch.ones_like(pts[:, :1])], dim=1)
    proj = homo @ Pm.T
    z = proj[:, 2]
    safe = torch.where(z.abs() < 1e-9, torch.full_like(z, 1e-9), z)
    uv_hat = proj[:, :2] / safe[:, None]
    return (uv_hat - uv).norm(dim=1), z


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


def main() -> int:
    ap = argparse.ArgumentParser(description="M1 dense correspondence initialization")
    ap.add_argument("--source_path", "-s", required=True)
    ap.add_argument("--output", "-o", required=True, help="destination .ply")
    ap.add_argument("--images", default="images")
    ap.add_argument("--preset", choices=sorted(PRESETS), default="sparse")
    ap.add_argument("--num_refs", type=int, default=180)
    ap.add_argument("--matches_per_ref", type=int, default=None)
    ap.add_argument("--nns_per_ref", type=int, default=None)
    ap.add_argument(
        "--certainty_thresh", type=float, default=None,
        help="tau_corr. Upstream has NO config key for this and silently "
             "inherits the matcher's internal sample_thresh (0.05), so it "
             "changes if the matcher is swapped. Exposed and recorded here.",
    )
    ap.add_argument("--proj_err_tolerance", type=float, default=8.0,
                    help="max reprojection error in pixels")
    ap.add_argument("--roma_model", choices=["outdoor", "indoor"], default="outdoor",
                    help="Neither describes a scattering medium; the choice is "
                         "recorded so it can be justified or ablated.")
    ap.add_argument("--upsample_preds", action=argparse.BooleanOptionalAction,
                    default=False, help="EDGS disables this for speed (delta D-9)")
    ap.add_argument("--symmetric", action=argparse.BooleanOptionalAction,
                    default=False, help="EDGS disables this for speed (delta D-9)")
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--device", default="cuda")
    args = ap.parse_args()

    preset = PRESETS[args.preset]
    matches_per_ref = args.matches_per_ref or preset["matches_per_ref"]
    nns_per_ref = args.nns_per_ref or preset["nns_per_ref"]
    certainty_thresh = (
        args.certainty_thresh if args.certainty_thresh is not None
        else preset["certainty_thresh"]
    )

    seed_everything(args.seed)
    started = time.time()

    from PIL import Image
    from scene.dataset_readers import sceneLoadTypeCallbacks

    # -- cameras: TRAIN ONLY ------------------------------------------------
    info = sceneLoadTypeCallbacks["Colmap"](args.source_path, args.images, True)
    cams = list(info.train_cameras)
    if len(cams) < 2:
        print(f"FATAL: need >= 2 training views, found {len(cams)}", file=sys.stderr)
        return 2
    print(f"[roma-init] {len(cams)} training views "
          f"({len(info.test_cameras)} held out and NOT used)")

    k_ref = min(args.num_refs, len(cams))
    if k_ref < args.num_refs:
        print(f"[roma-init] num_refs {args.num_refs} exceeds the view count; "
              f"using K_ref={k_ref}")
    refs = select_references(cams, k_ref, args.seed)
    print(f"[roma-init] {len(refs)} reference views")

    # -- matcher ------------------------------------------------------------
    from romatch import roma_indoor, roma_outdoor

    device = torch.device(args.device)
    build = roma_outdoor if args.roma_model == "outdoor" else roma_indoor
    matcher = build(device=device)
    matcher.upsample_preds = args.upsample_preds
    matcher.symmetric = args.symmetric
    matcher.sample_thresh = certainty_thresh

    # `local_corr` is RoMa's optional fused CUDA kernel (the `fused-local-corr`
    # extra). Its refiner blocks reach for it whenever use_custom_corr is set,
    # and the import failure surfaces mid-forward rather than at construction.
    # Fall back to the pure-torch correlation, which is the reference path the
    # kernel optimises rather than a different computation.
    custom_corr = importlib.util.find_spec("local_corr") is not None
    if not custom_corr:
        n_disabled = 0
        for module in matcher.modules():
            if getattr(module, "use_custom_corr", False):
                module.use_custom_corr = False
                n_disabled += 1
        print(f"[roma-init] local_corr unavailable; using the pure-torch "
              f"correlation on {n_disabled} refiner blocks (slower, same result)")

    print(f"[roma-init] matcher={args.roma_model} tau_corr={certainty_thresh} "
          f"upsample_preds={args.upsample_preds} symmetric={args.symmetric} "
          f"fused_local_corr={custom_corr}")

    all_pts: list[np.ndarray] = []
    all_rgb: list[np.ndarray] = []
    n_raw = n_kept = 0

    for step, i in enumerate(refs, 1):
        ref = cams[i]
        neighbours = nearest_neighbours(cams, i, nns_per_ref)

        warps, certs = [], []
        for j in neighbours:
            with torch.no_grad():
                warp, cert = matcher.match(
                    ref.image_path, cams[j].image_path, device=device
                )
            warps.append(warp[0] if warp.dim() == 4 else warp)
            certs.append(cert[0] if cert.dim() == 3 else cert)

        # Per-pixel argmax of certainty across the J neighbours, so each pixel
        # is triangulated against whichever view saw it best.
        cert_stack = torch.stack(certs)                       # (J, H, W)
        best = cert_stack.argmax(dim=0)                       # (H, W)
        warp_stack = torch.stack(warps)                       # (J, H, W, 4)
        idx = best[None, ..., None].expand(1, *best.shape, 4)
        warp_best = torch.gather(warp_stack, 0, idx)[0]       # (H, W, 4)
        cert_best = cert_stack.gather(0, best[None])[0]       # (H, W)

        try:
            sampled, _ = matcher.sample(warp_best, cert_best, num=matches_per_ref)
        except RuntimeError as exc:  # too few confident matches
            print(f"[roma-init] ref {i}: sampling failed ({exc}); skipping")
            continue

        # The gathered warp mixes neighbours per pixel, so resolve which
        # neighbour each sample came from before triangulating.
        H, W = cert_best.shape
        px = ((sampled[:, 0] + 1) * 0.5 * (W - 1)).round().long().clamp(0, W - 1)
        py = ((sampled[:, 1] + 1) * 0.5 * (H - 1)).round().long().clamp(0, H - 1)
        which = best[py, px]

        P_a = projection(ref)
        img = np.asarray(Image.open(ref.image_path).convert("RGB"))

        for slot, j in enumerate(neighbours):
            sel = which == slot
            if sel.sum() == 0:
                continue
            m = sampled[sel]
            uv_a, uv_b = matcher.to_pixel_coordinates(
                m, ref.height, ref.width, cams[j].height, cams[j].width
            )
            uv_a, uv_b = uv_a.float(), uv_b.float()

            P_b = projection(cams[j])
            pts = triangulate(P_a, P_b, uv_a, uv_b)

            err_a, z_a = reprojection_error(P_a, pts, uv_a)
            err_b, z_b = reprojection_error(P_b, pts, uv_b)
            err = torch.maximum(err_a, err_b)

            # Cheirality: the point must be in front of both cameras.  Without
            # this, near-parallel rays produce confident matches that
            # triangulate behind a camera and become floaters that nothing
            # removes, since densification is off.
            keep = (err < args.proj_err_tolerance) & (z_a > 0) & (z_b > 0)
            n_raw += int(sel.sum())
            n_kept += int(keep.sum())
            if keep.sum() == 0:
                continue

            good = pts[keep].cpu().numpy()
            cu = uv_a[keep, 0].round().long().clamp(0, ref.width - 1).cpu().numpy()
            cv = uv_a[keep, 1].round().long().clamp(0, ref.height - 1).cpu().numpy()
            all_pts.append(good)
            all_rgb.append(img[cv, cu])

        if step % 5 == 0 or step == len(refs):
            kept = sum(p.shape[0] for p in all_pts)
            print(f"[roma-init] ref {step}/{len(refs)}  points so far: {kept}")

    if not all_pts:
        print("FATAL: no correspondences survived filtering.", file=sys.stderr)
        return 3

    points = np.concatenate(all_pts).astype(np.float32)
    colors = np.concatenate(all_rgb).astype(np.uint8)
    elapsed = time.time() - started

    print(f"[roma-init] triangulated {n_raw}, kept {n_kept} "
          f"({100.0 * n_kept / max(1, n_raw):.1f}%)")
    print(f"[roma-init] wall clock {elapsed / 60:.1f} min")

    write_dense_pcd(
        args.output,
        points,
        colors,
        meta={
            "produced_by": "source/roma_init.py",
            "source_path": str(Path(args.source_path).resolve()),
            "seed": args.seed,
            "preset": args.preset,
            "num_refs_requested": args.num_refs,
            "num_refs_used": len(refs),
            "train_views": len(cams),
            "test_views_excluded": len(info.test_cameras),
            "matches_per_ref": matches_per_ref,
            "nns_per_ref": nns_per_ref,
            "certainty_thresh": certainty_thresh,
            "proj_err_tolerance": args.proj_err_tolerance,
            "roma_model": args.roma_model,
            "upsample_preds": args.upsample_preds,
            "symmetric": args.symmetric,
            # Records which correlation path ran. Not a correctness flag --
            # both compute the same thing -- but it moves preprocessing
            # wall-clock, which is reported alongside A1's training cost.
            "fused_local_corr": custom_corr,
            "triangulated": n_raw,
            "kept": n_kept,
            "preprocessing_seconds": round(elapsed, 1),
        },
    )
    print(
        "\n[roma-init] NOTE: this preprocessing time is NOT included in the "
        "training wall-clock. Report it alongside, or A1's cost is understated "
        "relative to A0's."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
