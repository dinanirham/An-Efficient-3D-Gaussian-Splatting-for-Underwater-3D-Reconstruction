"""M3 acceptance test for the dense-initialization geometry. Needs torch, not a GPU.

    python -m tools.verify_dense_init

The offline stage's triangulation is the highest-risk code in M1: it is pure
geometry with several conventions that are easy to get subtly wrong (the scene
reader stores `R` already transposed; projection matrices are world->pixel;
cheirality has to be checked separately), and a sign error would not crash --
it would quietly produce a cloud of plausible-looking floaters behind the
cameras, which with densification disabled nothing downstream would remove.

So the checks below build synthetic cameras, project known 3D points through
them, and require the pipeline to recover those points.
"""

from __future__ import annotations

import math
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import torch

sys.path.append(str(Path(__file__).resolve().parent.parent))

from source.roma_init import (  # noqa: E402
    intrinsics,
    projection,
    reprojection_error,
    triangulate,
    world_to_camera,
)

_results: list[tuple[str, bool, str]] = []


def check(name: str, fn) -> None:
    try:
        ok, detail = fn()
    except Exception as exc:  # noqa: BLE001
        ok, detail = False, f"raised {type(exc).__name__}: {exc}"
    _results.append((name, ok, detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")


@dataclass
class SynthCam:
    """Mimics the scene reader's CameraInfo, including its transposed R."""
    R: np.ndarray
    T: np.ndarray
    FovX: float
    FovY: float
    width: int
    height: int


def make_cam(position: np.ndarray, width=640, height=480, fov_deg=60.0) -> SynthCam:
    """Camera at `position`, axis-aligned, looking down +z."""
    R_w2c = np.eye(3)                      # world->camera rotation
    t = -R_w2c @ position                  # world->camera translation
    # The reader stores R already transposed, so hand it R_w2c.T.
    return SynthCam(
        R=R_w2c.T, T=t,
        FovX=math.radians(fov_deg), FovY=math.radians(fov_deg),
        width=width, height=height,
    )


def project_points(cam: SynthCam, pts: np.ndarray) -> np.ndarray:
    P = projection(cam)
    homo = np.concatenate([pts, np.ones((pts.shape[0], 1))], axis=1)
    proj = homo @ P.T
    return proj[:, :2] / proj[:, 2:3]


# ---------------------------------------------------------------------------


def t1_convention_matches_repo():
    """world_to_camera must agree with the repo's own getWorld2View2."""
    from utils.graphics_utils import getWorld2View2

    cam = make_cam(np.array([0.3, -0.2, 0.0]))
    mine = world_to_camera(cam)
    theirs = getWorld2View2(cam.R, cam.T)
    err = np.abs(mine - theirs).max()
    return err < 1e-6, f"max|ours - getWorld2View2| = {err:.2e}"


def t2_intrinsics_sane():
    cam = make_cam(np.zeros(3), width=640, height=480, fov_deg=60.0)
    K = intrinsics(cam)
    fx_expected = 640 / (2 * math.tan(math.radians(30.0)))
    ok = (
        abs(K[0, 0] - fx_expected) < 1e-6
        and abs(K[0, 2] - 320.0) < 1e-9
        and abs(K[1, 2] - 240.0) < 1e-9
    )
    return ok, f"fx={K[0,0]:.3f} (expected {fx_expected:.3f}) cx={K[0,2]} cy={K[1,2]}"


def t3_triangulation_recovers_points():
    """THE decisive test: project known points, triangulate, recover them."""
    rng = np.random.default_rng(0)
    pts = np.stack([
        rng.uniform(-1.0, 1.0, 40),
        rng.uniform(-1.0, 1.0, 40),
        rng.uniform(3.0, 8.0, 40),
    ], axis=1)

    cam_a = make_cam(np.array([0.0, 0.0, 0.0]))
    cam_b = make_cam(np.array([0.6, 0.0, 0.0]))   # 60 cm baseline

    uv_a = torch.tensor(project_points(cam_a, pts), dtype=torch.float32)
    uv_b = torch.tensor(project_points(cam_b, pts), dtype=torch.float32)

    got = triangulate(projection(cam_a), projection(cam_b), uv_a, uv_b)
    err = (got.numpy() - pts).max()
    worst = np.abs(got.numpy() - pts).max()
    return worst < 1e-2, f"max|recovered - truth| = {worst:.2e} (signed max {err:.2e})"


def t4_reprojection_error_discriminates():
    """Exact points reproject to ~0; perturbed ones do not."""
    pts = np.array([[0.0, 0.0, 5.0], [0.5, -0.3, 4.0]])
    cam = make_cam(np.zeros(3))
    uv = torch.tensor(project_points(cam, pts), dtype=torch.float32)
    P = projection(cam)

    good = torch.tensor(pts, dtype=torch.float32)
    err_good, z_good = reprojection_error(P, good, uv)

    bad = good.clone()
    bad[:, 0] += 0.5
    err_bad, _ = reprojection_error(P, bad, uv)

    ok = err_good.max() < 1e-2 and err_bad.min() > 10.0 and (z_good > 0).all()
    return ok, (
        f"exact max={err_good.max():.2e}px  perturbed min={err_bad.min():.1f}px  "
        f"z>0={bool((z_good > 0).all())}"
    )


def t5_cheirality_detects_points_behind():
    """A point behind the camera must report negative depth, not just big error."""
    cam = make_cam(np.zeros(3))
    P = projection(cam)
    behind = torch.tensor([[0.0, 0.0, -5.0]], dtype=torch.float32)
    uv = torch.zeros((1, 2), dtype=torch.float32)
    _, z = reprojection_error(P, behind, uv)
    return bool(z.item() < 0), f"z = {z.item():.3f} (must be < 0)"


def t6_ply_roundtrip_and_hash():
    """Cloud + sidecar round-trip, and a tampered cloud is rejected."""
    from utils.dense_init_io import load_dense_pcd, sidecar_path, write_dense_pcd

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "cloud.ply"
        pts = np.array([[0.0, 0.0, 5.0], [1.0, 2.0, 3.0]], dtype=np.float32)
        rgb = np.array([[255, 0, 0], [0, 128, 255]], dtype=np.uint8)
        write_dense_pcd(path, pts, rgb, meta={"produced_by": "test"})

        pcd = load_dense_pcd(path)
        pos_ok = np.abs(pcd.points - pts).max() < 1e-6
        col_ok = np.abs(pcd.colors - rgb / 255.0).max() < 1e-6
        side_ok = sidecar_path(path).exists()

        # Tamper with the cloud and confirm the hash check fires.
        write_dense_pcd(
            Path(tmp) / "other.ply", pts * 2, rgb, meta={"produced_by": "test"}
        )
        (Path(tmp) / "other.ply").replace(path)   # sidecar now stale
        tamper_caught = False
        try:
            load_dense_pcd(path)
        except ValueError:
            tamper_caught = True

    ok = pos_ok and col_ok and side_ok and tamper_caught
    return ok, (
        f"positions={pos_ok} colors={col_ok} sidecar={side_ok} "
        f"tamper_detected={tamper_caught}"
    )


def _opacity_schedule(
    n_iterations: int = 15_000,
    reset_interval: int | None = 3_000,
    decay_until: int = 10_000,
    decay_interval: int = 10,
    start_opacity: float = 0.1,
    prune_floor: float = 0.005,
) -> int:
    """Iterations an *undefended* primitive survives under M1's opacity schedule.

    Pure logit arithmetic, no torch: the question is a schedule question. A
    primitive the photometric loss never pushes upward is the worst case, and
    under M1 the worst case decides the population, because `prune_only`
    removes it and no densification puts it back.

    `reset_interval=None` models EDGS, which sets `opacity_reset_interval` to
    the iteration count so `reset_opacity()` never fires.
    """
    logit = math.log(start_opacity / (1.0 - start_opacity))
    floor = math.log(prune_floor / (1.0 - prune_floor))
    cap = math.log(0.01 / 0.99)          # reset_opacity caps at 0.01
    step = math.log(0.99)

    for it in range(1, n_iterations + 1):
        if reset_interval and it % reset_interval == 0:
            logit = min(logit, cap)      # reset is a CAP, not a raise
        if it % decay_interval == 0 and it < decay_until:
            logit += step
        if logit < floor:
            return it
    return n_iterations


def _undefended_lifetime(
    reset_interval: int,
    decay_interval: int,
    decay_factor: float,
    decay_from: int,
    decay_until: int,
    n_iterations: int,
    start_opacity: float = 0.1,
    prune_floor: float = 0.005,
) -> int:
    """Iteration at which a primitive the loss never defends crosses the floor.

    Pure logit arithmetic; the question is a schedule question. Under M1 the
    worst case decides the population, because `prune_only` removes it and no
    densification puts it back. `reset_opacity()` is `min(opacity, 0.01)` -- a
    cap, not a raise -- so it is modelled as such.
    """
    logit = math.log(start_opacity / (1.0 - start_opacity))
    floor = math.log(prune_floor / (1.0 - prune_floor))
    cap = math.log(0.01 / 0.99)
    step = math.log(decay_factor)
    for it in range(1, n_iterations + 1):
        if reset_interval and it % reset_interval == 0:
            logit = min(logit, cap)
        if decay_interval and it % decay_interval == 0 and decay_from <= it < decay_until:
            logit += step
        if logit < floor:
            return it
    return n_iterations


def t7_cull_must_not_precede_the_medium_model():
    """Under M1, an undefended primitive must survive until the medium model is on.

    EDGS's decay-and-cull removes "Gaussians the photometric loss does not
    defend" `[../EDGS/02-pipeline.md]`. That is sound when the loss is a
    complete statement of the objective. Under SeaSplat it is not: before
    `seathru_from_iter` there is no medium term, so veiling haze must be
    explained by geometry, and the photometric optimum is a handful of large
    blobs -- SeaSplat's own degeneracy D-4. A cull run in that window decides
    what is "needed" against an objective missing the medium model, and with
    densification disabled nothing restores what it removes.

    Measured: A1/IUI3-RedSea/s0 fell 471,531 -> 6,291 before iteration 10,000
    with the medium off, then 6,291 -> 74 once L_op joined. Every frame
    rendered empty and the run still reported success.

    The invariant is a scheduling one and holds whichever remedy is chosen:
    **an undefended primitive must not reach the prune floor before
    `seathru_from_iter`.**
    """
    from argparse import ArgumentParser  # noqa: PLC0415

    from arguments import OptimizationParams  # noqa: PLC0415

    opt = OptimizationParams(ArgumentParser())
    opt.m1_dense_init = True          # T7 is a statement about the M1 schedule
    if getattr(opt, "m1_decay_after_seathru", None) is None:
        return False, "m1_decay_after_seathru missing"

    seathru_at = int(opt.seathru_from_iter)
    if seathru_at > 100_000:            # upstream sentinel: seathru disabled
        return True, "seathru disabled at defaults; scheduling invariant vacuous"

    # The reset does not fire under M1 -- EDGS disables it because the
    # continuous decay replaces it -- so the model must not apply one.
    # This is the half that was missed first time round: the reset was
    # dormant under the old schedule and became lethal under the new one.
    reset_fires = not (opt.m1_dense_init and opt.m1_reduce_opacity)
    dies_at = _undefended_lifetime(
        reset_interval=int(opt.opacity_reset_interval) if reset_fires else 0,
        decay_interval=int(opt.m1_reduce_opacity_interval),
        decay_factor=float(opt.m1_reduce_opacity_factor),
        decay_from=seathru_at if opt.m1_decay_after_seathru else 0,
        decay_until=int(opt.densify_until_iter),
        n_iterations=int(opt.densify_until_iter),
    )
    if dies_at < seathru_at:
        return False, (
            f"an undefended primitive is culled at iteration {dies_at}, before "
            f"the medium model activates at {seathru_at} -- the cull runs "
            f"against an objective with no medium term, and M1 has no "
            f"densification to restore what it removes"
        )
    return True, f"undefended primitive survives to {dies_at} >= seathru {seathru_at}"


def main() -> int:
    check("T1 world_to_camera matches the repo's getWorld2View2", t1_convention_matches_repo)
    check("T2 intrinsics from FoV are correct", t2_intrinsics_sane)
    check("T3 triangulation recovers known points  <-- decisive", t3_triangulation_recovers_points)
    check("T4 reprojection error discriminates good from bad", t4_reprojection_error_discriminates)
    check("T5 cheirality detects points behind the camera", t5_cheirality_detects_points_behind)
    check("T6 ply round-trips and tampering is detected", t6_ply_roundtrip_and_hash)
    check("T7 cull must not precede the medium model  <-- decisive",
          t7_cull_must_not_precede_the_medium_model)

    failed = [n for n, ok, _ in _results if not ok]
    print("\n" + "=" * 68)
    if failed:
        print(f"M3 DENSE INIT GEOMETRY: FAILED ({len(failed)}/{len(_results)})")
        for n in failed:
            print(f"  - {n}")
        return 1
    print(f"M3 DENSE INIT GEOMETRY: PASSED ({len(_results)}/{len(_results)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
