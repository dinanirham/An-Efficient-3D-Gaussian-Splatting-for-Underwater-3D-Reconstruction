"""M1 acceptance test for the merged rasterizer binding.

Run on the target GPU (an A100 for this study):

    python -m tools.verify_rasterizer

The merged binding (see `gaussian_renderer/__init__.py`) drops SeaSplat's
`dxyang/diff-gaussian-rasterization` fork in favour of Mini-Splatting's
`diff_gaussian_rasterization_ms`, and recovers the alpha channel that the
`_ms` fork does not return by rendering a three-channel probe colour

    channel 0 = z   ->  blended depth  (Z_raw)
    channel 1 = 1   ->  accumulated alpha
    channel 2 = 0

against a zero background.  Every claim that design rests on is checked here,
because none of it is testable without a GPU and all of it is load-bearing:
SeaSplat divides depth by alpha, and `L_op` -- the single highest-value term
in its objective -- routes gradient to opacity through alpha alone.

The decisive test is T3.  For a single Gaussian at camera-frame depth z, the
probe gives Z_raw = alpha * z exactly, so Z_raw / alpha must recover z for
every pixel the Gaussian covers, independently of its opacity.  If the probe
were wrong -- wrong channel, background leaking in, alpha not actually being
accumulated alpha -- that identity would not hold.
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from typing import Callable

import torch


# --------------------------------------------------------------------------
# Minimal duck-typed stand-ins for GaussianModel / Camera / PipelineParams.
# Using real objects here would couple the test to scene loading and to
# GaussianModel's optimiser setup, neither of which is under test.
# --------------------------------------------------------------------------


@dataclass
class FakePipe:
    debug: bool = False
    compute_cov3D_python: bool = False
    convert_SHs_python: bool = False


class FakeGaussians:
    """Exposes exactly the properties `render()` reads."""

    def __init__(
        self,
        xyz: torch.Tensor,
        opacity: torch.Tensor,
        scale: float = 0.05,
    ) -> None:
        n = xyz.shape[0]
        dev = "cuda"
        self._xyz = xyz.to(dev).float().requires_grad_(True)
        # `get_opacity` applies a sigmoid upstream; store the logit so the
        # gradient path matches the real model.
        self._opacity_logit = (
            torch.log(opacity / (1.0 - opacity)).to(dev).float().requires_grad_(True)
        )
        self._scaling_log = torch.full(
            (n, 3), math.log(scale), device=dev, dtype=torch.float32
        ).requires_grad_(True)
        rot = torch.zeros((n, 4), device=dev, dtype=torch.float32)
        rot[:, 0] = 1.0
        self._rotation = rot.requires_grad_(True)
        self._features = torch.zeros((n, 1, 3), device=dev, dtype=torch.float32)
        self.active_sh_degree = 0
        self.max_sh_degree = 0

    @property
    def get_xyz(self) -> torch.Tensor:
        return self._xyz

    @property
    def get_opacity(self) -> torch.Tensor:
        return torch.sigmoid(self._opacity_logit)

    @property
    def get_scaling(self) -> torch.Tensor:
        return torch.exp(self._scaling_log)

    @property
    def get_rotation(self) -> torch.Tensor:
        return torch.nn.functional.normalize(self._rotation, dim=-1)

    @property
    def get_features(self) -> torch.Tensor:
        return self._features


def make_camera(width: int = 64, height: int = 64, fov_deg: float = 60.0):
    """Camera at the world origin looking down +z, 3DGS conventions."""
    from utils.graphics_utils import getProjectionMatrix

    fov = math.radians(fov_deg)
    znear, zfar = 0.01, 100.0

    world_view = torch.eye(4, dtype=torch.float32, device="cuda")
    proj = (
        getProjectionMatrix(znear=znear, zfar=zfar, fovX=fov, fovY=fov)
        .transpose(0, 1)
        .cuda()
    )
    full_proj = (world_view.unsqueeze(0).bmm(proj.unsqueeze(0))).squeeze(0)

    @dataclass
    class Cam:
        FoVx: float = fov
        FoVy: float = fov
        image_width: int = width
        image_height: int = height
        world_view_transform: torch.Tensor = world_view
        full_proj_transform: torch.Tensor = full_proj
        camera_center: torch.Tensor = torch.zeros(3, device="cuda")

    return Cam()


# --------------------------------------------------------------------------
# Checks
# --------------------------------------------------------------------------

Result = tuple[bool, str]
_results: list[tuple[str, bool, str]] = []


def check(name: str, fn: Callable[[], Result]) -> None:
    try:
        ok, detail = fn()
    except Exception as exc:  # noqa: BLE001 - report, do not mask
        ok, detail = False, f"raised {type(exc).__name__}: {exc}"
    _results.append((name, ok, detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")


def t0_extension() -> Result:
    import diff_gaussian_rasterization_ms as m

    caps = torch.cuda.get_device_capability()
    name = torch.cuda.get_device_name()
    arch_ok = caps >= (8, 0)
    return arch_ok, f"{name} sm_{caps[0]}{caps[1]}, module at {m.__file__}"


def t1_alpha_range() -> Result:
    """Alpha must lie in [0, 1] and vanish as opacity vanishes."""
    from gaussian_renderer import render_depth_alpha

    cam, pipe = make_camera(), FakePipe()
    xyz = torch.tensor([[0.0, 0.0, 2.0]])

    hi = FakeGaussians(xyz, torch.tensor([[0.99]]))
    lo = FakeGaussians(xyz, torch.tensor([[1e-4]]))

    a_hi = render_depth_alpha(cam, hi, pipe)["alpha"]
    a_lo = render_depth_alpha(cam, lo, pipe)["alpha"]

    in_range = bool((a_hi >= -1e-5).all() and (a_hi <= 1.0 + 1e-5).all())
    ordered = bool(a_hi.max() > 0.5 and a_lo.max() < 1e-2)
    return (
        in_range and ordered,
        f"alpha_hi_max={a_hi.max():.4f} alpha_lo_max={a_lo.max():.6f}",
    )


def t2_alpha_composition() -> Result:
    """Two stacked Gaussians must composite as 1-(1-a1)(1-a2).

    Both sit at the SAME depth, so their projected footprints -- and hence
    their per-pixel alphas -- are identical.  At different depths the screen
    sizes differ, the two per-pixel alphas are no longer equal, and
    1-(1-a)^2 stops being the right closed form to compare against.
    """
    from gaussian_renderer import render_depth_alpha

    cam, pipe = make_camera(), FakePipe()
    a = 0.5
    one = FakeGaussians(torch.tensor([[0.0, 0.0, 2.0]]), torch.tensor([[a]]))
    two = FakeGaussians(
        torch.tensor([[0.0, 0.0, 2.0], [0.0, 0.0, 2.0]]),
        torch.tensor([[a], [a]]),
    )

    a1 = render_depth_alpha(cam, one, pipe)["alpha"]
    a2 = render_depth_alpha(cam, two, pipe)["alpha"]

    # Compare at the pixel where both are most opaque (image centre).
    c = (a1.shape[-2] // 2, a1.shape[-1] // 2)
    got = a2[0, c[0], c[1]].item()
    base = a1[0, c[0], c[1]].item()
    expect = 1.0 - (1.0 - base) ** 2
    ok = abs(got - expect) < 5e-3
    return ok, f"centre: one={base:.4f} two={got:.4f} expected={expect:.4f}"


def t3_depth_over_alpha() -> Result:
    """THE decisive test: Z_raw / alpha must recover z for a single Gaussian."""
    from gaussian_renderer import render_depth_alpha

    cam, pipe = make_camera(), FakePipe()
    z = 2.5
    passes: list[str] = []
    ok_all = True

    for opacity in (0.3, 0.7, 0.95):
        g = FakeGaussians(
            torch.tensor([[0.0, 0.0, z]]), torch.tensor([[opacity]])
        )
        pkg = render_depth_alpha(cam, g, pipe)
        depth, alpha = pkg["depth"], pkg["alpha"]

        covered = alpha > 1e-3
        if covered.sum() == 0:
            return False, f"Gaussian not visible at opacity={opacity}"
        recovered = (depth[covered] / alpha[covered])
        err = (recovered - z).abs().max().item()
        ok_all &= err < 1e-2
        passes.append(f"o={opacity}: max|Z/a - z|={err:.2e}")

    return ok_all, "; ".join(passes)


def t4_alpha_gradient() -> Result:
    """L_op needs gradient from alpha to opacity; it must be non-zero."""
    from gaussian_renderer import render_depth_alpha

    cam, pipe = make_camera(), FakePipe()
    g = FakeGaussians(torch.tensor([[0.0, 0.0, 2.0]]), torch.tensor([[0.5]]))

    alpha = render_depth_alpha(cam, g, pipe)["alpha"]
    alpha.sum().backward()

    grad = g._opacity_logit.grad
    ok = grad is not None and torch.isfinite(grad).all() and grad.abs().sum() > 0
    return ok, f"d(sum alpha)/d(opacity_logit) = {None if grad is None else grad.flatten().tolist()}"


def t7_alpha_gradient_reaches_densification() -> Result:
    """CD-22.  Alpha's gradient must land in the buffer density control reads.

    This is the check that would have caught the defect T0-T6 could not see:
    every one of them inspects a *returned tensor*, and alpha's value was
    correct throughout.  What was wrong was the gradient's destination.

    Upstream SeaSplat takes alpha from the colour pass, so alpha-loss gradients
    accumulate into the same `means2D` that `add_densification_stats` reads.
    Our probe pass allocates its own buffer unless one is supplied -- which
    reproduces alpha exactly and silently removes it from the densification
    signal.  Measured consequence: 743k primitives against vanilla's 4.46M.

    Both directions are asserted, because a test that only confirms the fix
    would still pass if the sharing were quietly dropped again.
    """
    from gaussian_renderer import render, render_depth_alpha

    cam, pipe = make_camera(), FakePipe()
    bg = torch.zeros(3, device="cuda")
    xyz = torch.tensor([[0.0, 0.0, 2.0], [0.3, 0.1, 2.4]])

    # Shared buffer: alpha's gradient must arrive.
    g = FakeGaussians(xyz.clone(), torch.tensor([[0.5], [0.5]]))
    shared = render(cam, g, pipe, bg)["viewspace_points"]
    render_depth_alpha(cam, g, pipe, screenspace_points=shared)["alpha"].sum().backward()
    shared_grad = 0.0 if shared.grad is None else shared.grad.abs().sum().item()

    # Own buffer (the pre-fix path): the caller's tensor must stay untouched,
    # confirming the defect is real rather than the sharing being a no-op.
    g2 = FakeGaussians(xyz.clone(), torch.tensor([[0.5], [0.5]]))
    separate = render(cam, g2, pipe, bg)["viewspace_points"]
    render_depth_alpha(cam, g2, pipe)["alpha"].sum().backward()
    separate_grad = 0.0 if separate.grad is None else separate.grad.abs().sum().item()

    ok = shared_grad > 0.0 and separate_grad == 0.0
    return ok, (
        f"shared buffer: sum|d(alpha)/d(means2D)| = {shared_grad:.4e} (must be > 0); "
        f"unshared: {separate_grad:.4e} (must be 0)"
    )


def t5_importance_accumulators() -> Result:
    """A2 needs accum_weights / area_proj / area_max from the colour pass."""
    from gaussian_renderer import render

    cam, pipe = make_camera(), FakePipe()
    g = FakeGaussians(
        torch.tensor([[0.0, 0.0, 2.0], [0.3, 0.0, 2.5]]),
        torch.tensor([[0.8], [0.8]]),
    )
    bg = torch.zeros(3, device="cuda")
    pkg = render(cam, g, pipe, bg)

    need = ("accum_weights", "area_proj", "area_max")
    missing = [k for k in need if k not in pkg]
    if missing:
        return False, f"missing keys: {missing}"

    shapes = {k: tuple(pkg[k].shape) for k in need}
    n = g.get_xyz.shape[0]
    right_shape = all(pkg[k].shape[0] == n for k in need)
    nonzero = pkg["area_max"].sum().item() > 0
    return right_shape and nonzero, f"{shapes}, area_max_sum={pkg['area_max'].sum().item()}"


def t6_background_isolation() -> Result:
    """The probe must not pick up a background contribution."""
    from gaussian_renderer import render_depth_alpha

    cam, pipe = make_camera(), FakePipe()
    # No geometry in front of most pixels -> those pixels must read alpha 0,
    # even though the scene background elsewhere may be non-zero.
    g = FakeGaussians(torch.tensor([[0.0, 0.0, 2.0]]), torch.tensor([[0.9]]))
    pkg = render_depth_alpha(cam, g, pipe)
    alpha, depth = pkg["alpha"], pkg["depth"]

    corner_a = alpha[0, 0, 0].item()
    corner_d = depth[0, 0, 0].item()
    ok = abs(corner_a) < 1e-4 and abs(corner_d) < 1e-4
    return ok, f"corner alpha={corner_a:.2e} depth={corner_d:.2e} (both must be ~0)"


def main() -> int:
    if not torch.cuda.is_available():
        print("FATAL: no CUDA device. This test must run on the target GPU.")
        return 2

    check("T0 extension builds and targets sm_80+", t0_extension)
    check("T1 alpha in [0,1] and monotone in opacity", t1_alpha_range)
    check("T2 alpha composites as 1-(1-a1)(1-a2)", t2_alpha_composition)
    check("T3 Z_raw/alpha recovers true depth  <-- decisive", t3_depth_over_alpha)
    check("T4 alpha is differentiable w.r.t. opacity", t4_alpha_gradient)
    check("T5 importance accumulators present and sane", t5_importance_accumulators)
    check("T6 zero background does not leak into probe", t6_background_isolation)
    check("T7 alpha gradient reaches density control  <-- decisive",
          t7_alpha_gradient_reaches_densification)

    failed = [n for n, ok, _ in _results if not ok]
    print("\n" + "=" * 68)
    if failed:
        print(f"M1 ACCEPTANCE: FAILED ({len(failed)}/{len(_results)})")
        for n in failed:
            print(f"  - {n}")
        return 1
    print(f"M1 ACCEPTANCE: PASSED ({len(_results)}/{len(_results)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
