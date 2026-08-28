"""M2: importance-weighted simplification to a primitive budget.

Scope (CD-4): this is Mini-Splatting's **simplification stage only**.  Its
densification half -- blur split and depth reinitialization -- is deliberately
not implemented, because both fail exactly where this domain needs them most:
the reinit is driven by rendered depth and does nothing in regions without a
reliable one, and its pixel sampling is biased toward *low*-opacity pixels.
In an underwater scene that region is the water column, twice over.  Anything
that cites this as "Mini-Splatting" is overclaiming; it is Mini-Splatting's
simplification stage.

Two properties of the mechanism are load-bearing and easy to lose in a
reimplementation:

**Intersection preserving.**  A primitive that is never the dominant
contributor to any pixel in any training view is, by definition, always
occluded or always subordinate -- pure redundancy.  It is removed by zeroing
its sampling probability rather than by a separate pass.

**Stochastic sampling, not top-k.**  Importance is *spatially autocorrelated*:
neighbouring primitives score similarly, so a deterministic threshold removes
whole regions rather than thinning uniformly.  Randomising survival within a
uniform-importance patch thins the patch instead of deleting it.  This matters
more here than upstream, because with densification disabled in the A4/A7 cells
there is nothing left to regrow what a threshold would strip.
"""

from __future__ import annotations

from typing import Any, Callable

import torch


def accumulate_importance(
    gaussians: Any,
    cameras: list,
    render_fn: Callable,
    pipe: Any,
    bg: torch.Tensor,
    metric: str = "outdoor",
) -> tuple[torch.Tensor, torch.Tensor]:
    """Accumulate per-primitive importance over every training view.

    Returns `(importance, area_max_total)`.

    `indoor`  -> I^1: plain accumulated blending weight.
    `outdoor` -> I^2: blending weight normalised by projected area, counted
                 only in views where the primitive is the argmax contributor.

    Neither metric was designed for a scattering medium, and the `outdoor`
    variant's area normalisation exists specifically to suppress *sky*.  An
    underwater far field is systematically low-contrast but is scene, not sky,
    so the choice is a real modelling decision rather than a default -- it is
    recorded in the manifest and stated in the write-up.
    """
    if metric not in ("indoor", "outdoor"):
        raise ValueError(f"imp_metric must be 'indoor' or 'outdoor', got {metric!r}")

    n = gaussians.get_xyz.shape[0]
    device = gaussians.get_xyz.device
    importance = torch.zeros(n, dtype=torch.float32, device=device)
    area_max_total = torch.zeros(n, dtype=torch.float32, device=device)

    for cam in cameras:
        with torch.no_grad():
            pkg = render_fn(cam, gaussians, pipe, bg)
        weights = pkg["accum_weights"].float().reshape(-1)
        area_proj = pkg["area_proj"].float().reshape(-1)
        area_max = pkg["area_max"].float().reshape(-1)

        area_max_total += area_max
        if metric == "outdoor":
            seen = area_max > 0
            safe_area = area_proj.clamp(min=1.0)
            importance[seen] += (weights / safe_area)[seen]
        else:
            importance += weights

    # Intersection preserving: never the argmax anywhere -> probability zero.
    importance[area_max_total == 0] = 0.0
    return importance, area_max_total


def sample_to_budget(
    importance: torch.Tensor,
    budget: int,
    generator: torch.Generator | None = None,
) -> torch.Tensor:
    """Importance-weighted sampling WITHOUT replacement. Returns a keep mask.

    Deliberately not top-k; see the module docstring.
    """
    eligible = int((importance > 0).sum().item())
    if eligible == 0:
        raise RuntimeError(
            "no primitive is the dominant contributor to any pixel in any "
            "training view; importance is identically zero. This usually means "
            "the rasterizer's area_max accumulator is not being populated."
        )

    target = min(int(budget), eligible)
    idx = torch.multinomial(
        importance, num_samples=target, replacement=False, generator=generator
    )
    keep = torch.zeros_like(importance, dtype=torch.bool)
    keep[idx] = True
    return keep


def cdf_keep_mask(importance: torch.Tensor, thres: float = 0.99) -> torch.Tensor:
    """Drop the primitives making up the bottom `1 - thres` of importance mass.

    Deterministic, and that is not a contradiction of the argument above: the
    objection to thresholding concerns *large* pruning ratios, where it removes
    whole regions.  At a 1% mass ratio it removes only primitives that
    contribute essentially nothing.  The asymmetry between the two
    simplification events is intentional and worth stating rather than leaving
    implicit.
    """
    order = torch.argsort(importance)             # ascending
    cumulative = torch.cumsum(importance[order], dim=0)
    total = cumulative[-1]
    if total <= 0:
        return torch.ones_like(importance, dtype=torch.bool)

    drop = cumulative < (1.0 - thres) * total
    keep = torch.ones_like(importance, dtype=torch.bool)
    keep[order[drop]] = False
    return keep
