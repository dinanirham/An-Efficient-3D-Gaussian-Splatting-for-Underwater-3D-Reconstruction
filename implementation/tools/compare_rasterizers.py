"""Compare the two rasterizer forks on identical inputs.

    python -m tools.compare_rasterizers

Why this exists.  Restoring the alpha gradient (CD-22) did not close the
density gap: A0 converges to ~635k primitives where vanilla SeaSplat reaches
4,462,668 on the same scene.  Vanilla grows 6.7x between iterations 5000 and
15000, which across 100 densification events is only ~1.9% growth per event --
so the cause is a *small* per-event difference that compounds, not a gross
structural one.

Two quantities decide each event, and both come straight out of the rasterizer
backward, where no forward-output test can see them:

    means2D.grad  ->  add_densification_stats accumulates its norm, and
                      densify_and_prune clones/splits whatever exceeds
                      densify_grad_threshold = 0.0002
    radii         ->  max_radii2D, which size_threshold=20 prunes against
                      once iteration > opacity_reset_interval

Mini-Splatting exists specifically to replace 3DGS densification, so its fork
having a modified densification signal is entirely plausible.  This script
feeds both forks byte-identical Gaussians, camera and loss, and reports the
ratios directly.

Requires BOTH extensions importable:

    diff_gaussian_rasterization_ms   ours (mini-splatting/submodules)
    diff_gaussian_rasterization      SeaSplat's, from dxyang's fork

The reference fork is not vendored here; SeaSplat's submodule is empty in this
checkout.  Build it once:

    git clone --recursive https://github.com/dxyang/seasplat.git /content/seasplat_ref
    pip install /content/seasplat_ref/submodules/diff-gaussian-rasterization
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import torch

sys.path.append(str(Path(__file__).resolve().parent.parent))

from utils.graphics_utils import getProjectionMatrix  # noqa: E402

SEED = 0
N_GAUSSIANS = 4000
WIDTH = HEIGHT = 256
DENSIFY_GRAD_THRESHOLD = 0.0002   # the constant the ratio has to be read against
SIZE_THRESHOLD = 20               # max_radii2D prune threshold, post opacity reset


@dataclass
class Scene:
    means3D: torch.Tensor
    scales: torch.Tensor
    rotations: torch.Tensor
    opacity: torch.Tensor
    colors: torch.Tensor
    weight: torch.Tensor      # fixed random loss weighting, identical per fork


def build_scene(device: str = "cuda") -> Scene:
    """A fixed pseudo-random cloud in front of the camera.

    Deliberately not a toy two-Gaussian case: the quantities under test are
    population statistics over thousands of primitives at many depths and
    screen sizes, and a scale difference could easily be invisible at n=2.
    """
    g = torch.Generator(device="cpu").manual_seed(SEED)

    xy = (torch.rand((N_GAUSSIANS, 2), generator=g) - 0.5) * 2.0
    z = 1.5 + torch.rand((N_GAUSSIANS, 1), generator=g) * 6.0
    means3D = torch.cat([xy, z], dim=1).to(device).float()

    # Spread over two orders of magnitude so both the clone branch (small) and
    # the split branch (large) of densify_and_prune are represented.
    log_s = -4.5 + torch.rand((N_GAUSSIANS, 3), generator=g) * 2.5
    scales = log_s.exp().to(device).float()

    rot = torch.zeros((N_GAUSSIANS, 4))
    rot[:, 0] = 1.0
    rotations = rot.to(device).float()

    opacity = (0.05 + torch.rand((N_GAUSSIANS, 1), generator=g) * 0.9).to(device).float()
    colors = torch.rand((N_GAUSSIANS, 3), generator=g).to(device).float()
    weight = torch.rand((3, HEIGHT, WIDTH), generator=g).to(device).float()

    return Scene(means3D, scales, rotations, opacity, colors, weight)


def make_camera(device: str = "cuda"):
    fov = math.radians(60.0)
    world_view = torch.eye(4, dtype=torch.float32, device=device)
    proj = (
        getProjectionMatrix(znear=0.01, zfar=100.0, fovX=fov, fovY=fov)
        .transpose(0, 1)
        .to(device)
    )
    full_proj = world_view.unsqueeze(0).bmm(proj.unsqueeze(0)).squeeze(0)

    @dataclass
    class Cam:
        FoVx: float = fov
        FoVy: float = fov
        image_width: int = WIDTH
        image_height: int = HEIGHT
        world_view_transform: torch.Tensor = world_view
        full_proj_transform: torch.Tensor = full_proj
        camera_center: torch.Tensor = torch.zeros(3, device=device)

    return Cam()


def rasterize(module: Any, name: str, scene: Scene, cam: Any) -> dict[str, torch.Tensor]:
    """Run one fork and return its image, radii and means2D gradient.

    The loss is a fixed weighted sum of the image, identical across forks, so
    dL/dmeans2D is the same mathematical quantity on both sides and any
    difference is the implementation's.
    """
    means3D = scene.means3D.clone().requires_grad_(True)
    scales = scene.scales.clone().requires_grad_(True)
    rotations = scene.rotations.clone().requires_grad_(True)
    opacity = scene.opacity.clone().requires_grad_(True)
    colors = scene.colors.clone().requires_grad_(True)

    means2D = torch.zeros_like(means3D, requires_grad=True)
    means2D.retain_grad()

    settings = module.GaussianRasterizationSettings(
        image_height=int(cam.image_height),
        image_width=int(cam.image_width),
        tanfovx=math.tan(cam.FoVx * 0.5),
        tanfovy=math.tan(cam.FoVy * 0.5),
        bg=torch.zeros(3, device="cuda"),
        scale_modifier=1.0,
        viewmatrix=cam.world_view_transform,
        projmatrix=cam.full_proj_transform,
        sh_degree=0,
        campos=cam.camera_center,
        prefiltered=False,
        debug=False,
    )
    out = module.GaussianRasterizer(raster_settings=settings)(
        means3D=means3D,
        means2D=means2D,
        shs=None,
        colors_precomp=colors,
        opacities=opacity,
        scales=scales,
        rotations=rotations,
        cov3D_precomp=None,
    )

    # The two forks return different tuples:
    #   _ms     -> image, radii, accum_weights, area_proj, area_max
    #   dxyang  -> image, alpha, radii
    if len(out) == 5:
        image, radii = out[0], out[1]
    elif len(out) == 3:
        image, radii = out[0], out[2]
    else:
        raise RuntimeError(f"{name}: unexpected return arity {len(out)}")

    (image * scene.weight).sum().backward()

    return {"image": image.detach(), "radii": radii.detach(),
            "grad": means2D.grad.detach().clone()}


def summarise(tag: str, ours: torch.Tensor, ref: torch.Tensor) -> None:
    print(f"\n  {tag}")
    for label, t in (("_ms (ours)", ours), ("dxyang (ref)", ref)):
        f = t.float()
        print(f"    {label:<14} mean={f.mean():.6e}  max={f.max():.6e}  "
              f"nonzero={(f != 0).float().mean() * 100:.1f}%")
    denom = ref.float().mean()
    if denom.abs() > 0:
        print(f"    ratio ours/ref (mean) = {ours.float().mean() / denom:.4f}")


def main() -> int:
    if not torch.cuda.is_available():
        print("FATAL: needs a GPU")
        return 2

    try:
        import diff_gaussian_rasterization_ms as ms
    except ImportError as exc:
        print(f"FATAL: our rasterizer is missing ({exc})")
        return 2
    try:
        import diff_gaussian_rasterization as ref
    except ImportError:
        print("FATAL: SeaSplat's reference rasterizer is not installed.\n"
              "  git clone --recursive https://github.com/dxyang/seasplat.git "
              "/content/seasplat_ref\n"
              "  pip install /content/seasplat_ref/submodules/"
              "diff-gaussian-rasterization")
        return 2

    scene, cam = build_scene(), make_camera()
    a = rasterize(ms, "_ms", scene, cam)
    b = rasterize(ref, "dxyang", scene, cam)

    print("=" * 70)
    print(f"{N_GAUSSIANS} Gaussians, {WIDTH}x{HEIGHT}, identical inputs and loss")
    print("=" * 70)

    # 1. Forward agreement. If images differ the comparison below is moot.
    d = (a["image"] - b["image"]).abs()
    print(f"\n  forward image: max|diff|={d.max():.3e}  mean|diff|={d.mean():.3e}")

    # 2. The densification signal itself.
    gn_a = a["grad"][:, :2].norm(dim=-1)
    gn_b = b["grad"][:, :2].norm(dim=-1)
    summarise("||dL/dmeans2D||  <- add_densification_stats accumulates this", gn_a, gn_b)

    # What actually decides an event is how many clear the threshold. A ratio
    # near 1 on the mean can still hide a large difference in the tail.
    over_a = (gn_a > DENSIFY_GRAD_THRESHOLD).float().mean() * 100
    over_b = (gn_b > DENSIFY_GRAD_THRESHOLD).float().mean() * 100
    print(f"    over densify_grad_threshold={DENSIFY_GRAD_THRESHOLD}: "
          f"ours {over_a:.2f}%  ref {over_b:.2f}%")

    # 3. radii, which size_threshold prunes against.
    summarise("radii  <- max_radii2D, pruned when > size_threshold",
              a["radii"], b["radii"])
    big_a = (a["radii"] > SIZE_THRESHOLD).float().mean() * 100
    big_b = (b["radii"] > SIZE_THRESHOLD).float().mean() * 100
    print(f"    over size_threshold={SIZE_THRESHOLD}: "
          f"ours {big_a:.2f}%  ref {big_b:.2f}%")

    print("\n" + "=" * 70)
    print("READ THIS AS:")
    print("  forward diff ~0 and both ratios ~1  -> rasterizer exonerated;")
    print("                                         look elsewhere for the 6x")
    print("  grad ratio < 1 / fewer over threshold -> ours densifies less, and")
    print("                                         by roughly that factor")
    print("  radii ratio > 1 / more over threshold -> ours over-prunes large")
    print("                                         primitives")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
