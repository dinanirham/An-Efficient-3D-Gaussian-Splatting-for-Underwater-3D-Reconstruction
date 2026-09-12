"""Cross-frame depth-range statistics (CD-27).

**What this measures and why it is not what was already measured.**

The medium coefficients enter the image formation model only through the
product `beta * Z_hat`, and `Z_hat` is the rendered depth renormalised by
*each frame's own* extrema.  Imposing the physical attenuation law on frame
`f` therefore requires

    beta = beta_phys * (M_f - m_f)

whose right-hand side depends on the frame.  A single scene-global `beta`
cannot satisfy that across frames unless the depth range is constant across
the training set, and nothing in the design makes it so.  The fitted `beta` is
consequently a *compromise over the distribution* of per-frame depth ranges --
a function of the primitive population, not of the medium alone.  When a
simplification event moves that distribution, `beta` moves with it, and the
pre-event value has no claim to be the target a re-identification burst should
return to.  This is why CD-6 could not have worked.

CD-12 already logs `z_min` and `z_max`, but from the **single view sampled at
that iteration**.  That is one draw from the distribution the argument is
about, not a statistic of it, so the logged `z_range` varies frame to frame
independently of anything the mechanisms do.  The prediction that collapse
tracks the *change in cross-frame dispersion* cannot be tested from a single
draw, and the quantity has not been measured in any run of the campaign.

**Cost.** One forward render per training view per sweep, under `no_grad`, at
whatever interval the caller chooses plus unconditionally at the simplification
boundaries.  On this corpus that is 15-25 renders, well under a second against
a run of roughly fifty minutes.

**Two invariants this module exists to hold**, both covered by
`tools/verify_depth_stats.py`:

1.  The sweep and the training loop compute the constants through *one*
    implementation.  A second implementation that drifted would measure a
    depth range that `beta` is not actually fitted against -- the same class of
    error as CD-22/CD-23, where every forward value was right and only the
    destination was wrong.
2.  The sweep consumes no randomness.  A sweep that advanced the RNG stream
    would make an instrumented run non-comparable with the runs already
    completed, which is a silent way to invalidate a campaign.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Callable, Optional, Sequence

import torch


def normalise_depth(
    depth: torch.Tensor,
    alpha: torch.Tensor,
    normalize_depth: float,
    filter_depth: bool,
    norm_depth_max: bool,
    nan_label: Optional[str] = "training",
) -> tuple[torch.Tensor, Optional[float], Optional[float]]:
    """Apply the baseline's per-frame depth normalisation.

    Returns `(normalised_depth, z_min, z_max)`, where the two constants are
    captured **before** the rescale -- afterwards they are 0 and 1 by
    construction and carry no information.  They are `None` when no
    renormalisation was applied, which is the honest report: the quantity the
    medium model is fitted against does not exist in that configuration.

    `nan_label` names the caller in the all-NaN warning; pass `None` to stay
    silent, which the sweep does so that one bad frame does not print once per
    view per checkpoint.

    This is the single implementation of the path.  `train.py` delegates to it
    so that the instrument and the optimiser cannot diverge.
    """
    if not filter_depth:
        return depth, None, None

    depth = depth / alpha

    bad = torch.logical_or(torch.isnan(depth), torch.isinf(depth))
    if torch.any(bad):
        valid = depth[torch.logical_not(bad)]
        if len(valid) == 0:
            if nan_label is not None:
                print(f"[{nan_label}] everything is nan")
            not_nan_max = 100.0
        else:
            not_nan_max = torch.max(valid).item()
        depth = torch.nan_to_num(depth, not_nan_max, not_nan_max)

    depth = depth / normalize_depth

    if not norm_depth_max:
        return depth, None, None

    z_min = depth.min().item()
    z_max = depth.max().item()
    if z_min != z_max:
        depth = (depth - depth.min()) / (depth.max() - depth.min())
    else:
        # Degenerate frame.  Preserved exactly as upstream wrote it, including
        # the division-by-zero it carries when the frame is uniformly zero:
        # changing it here would alter the trajectory of runs already
        # completed and break comparability, which is a worse defect than the
        # hazard.  Recorded rather than fixed.
        depth = depth / depth.max()

    return depth, z_min, z_max


@dataclass
class DepthRangeStats:
    """The distribution of `(M_f - m_f)` over the training views."""

    FIELDS = (
        "zr_n_views",
        "zr_mean",
        "zr_sd",
        "zr_cv",
        "zr_min",
        "zr_max",
        "zm_mean",
        "zM_mean",
    )

    n_views: int = 0
    range_mean: float = 0.0
    range_sd: float = 0.0
    range_cv: float = 0.0
    range_min: float = 0.0
    range_max: float = 0.0
    min_mean: float = 0.0
    max_mean: float = 0.0
    ranges: list[float] = field(default_factory=list)

    @classmethod
    def empty(cls) -> "DepthRangeStats":
        return cls()

    def as_row(self) -> dict[str, Any]:
        """CSV fields. Unmeasured entries are blank, never zero.

        A zero dispersion is a claim about the scene; an absent measurement is
        not, and writing 0.0 for the second would let an analysis average the
        two together.
        """
        if self.n_views == 0:
            row: dict[str, Any] = {f: "" for f in self.FIELDS}
            row["zr_n_views"] = 0
            return row
        return {
            "zr_n_views": self.n_views,
            "zr_mean": round(self.range_mean, 8),
            "zr_sd": round(self.range_sd, 8),
            "zr_cv": round(self.range_cv, 8),
            "zr_min": round(self.range_min, 8),
            "zr_max": round(self.range_max, 8),
            "zm_mean": round(self.min_mean, 8),
            "zM_mean": round(self.max_mean, 8),
        }


def _stats_from(mins: list[float], maxs: list[float]) -> DepthRangeStats:
    n = len(mins)
    if n == 0:
        return DepthRangeStats.empty()

    ranges = [hi - lo for lo, hi in zip(mins, maxs)]
    mean = sum(ranges) / n
    # Population sd: these are the whole training set, not a sample from it.
    var = sum((r - mean) ** 2 for r in ranges) / n
    sd = math.sqrt(var)
    # The coefficient of variation is the quantity the prediction is about:
    # dimensionless, so it is comparable across scenes whose units differ, and
    # it is the dispersion that matters rather than the level -- a distribution
    # that merely translates leaves beta's compromise attainable, one that
    # broadens does not.
    cv = sd / mean if mean != 0.0 else 0.0

    return DepthRangeStats(
        n_views=n,
        range_mean=mean,
        range_sd=sd,
        range_cv=cv,
        range_min=min(ranges),
        range_max=max(ranges),
        min_mean=sum(mins) / n,
        max_mean=sum(maxs) / n,
        ranges=ranges,
    )


def sweep_depth_ranges(
    cameras: Sequence[Any],
    gaussians: Any,
    render_depth_fn: Callable[..., dict],
    pipe: Any,
    bg: Any,
    normalize_depth: float,
    filter_depth: bool,
    norm_depth_max: bool,
) -> DepthRangeStats:
    """Render every view once and return the depth-range distribution.

    Iterates the camera list in order rather than drawing from the shuffled
    viewpoint stack, so the training RNG stream is untouched and an
    instrumented run stays comparable with the runs already completed.
    """
    if not filter_depth or not norm_depth_max or len(cameras) == 0:
        # No per-frame renormalisation is in force, so the distribution the
        # medium model is fitted against does not exist.  Report nothing
        # rather than reporting the raw depth under a name that implies it.
        return DepthRangeStats.empty()

    mins: list[float] = []
    maxs: list[float] = []

    for cam in cameras:
        with torch.no_grad():
            pkg = render_depth_fn(cam, gaussians, pipe, bg)
            _, lo, hi = normalise_depth(
                pkg["depth"],
                pkg["alpha"],
                normalize_depth,
                filter_depth,
                norm_depth_max,
                nan_label=None,
            )
        if lo is None or hi is None:
            continue
        mins.append(lo)
        maxs.append(hi)

    return _stats_from(mins, maxs)
