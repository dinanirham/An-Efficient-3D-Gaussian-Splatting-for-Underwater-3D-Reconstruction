"""Explicit PSNR conventions, and the aggregation that goes with them.

Peak signal-to-noise ratio is computed two incompatible ways across the
methods this study compares against, and the difference is largest in exactly
this domain:

  per-channel  mean over channels of PSNR(MSE_c)   -- SeaSplat's in-training path
  pooled       PSNR(mean over channels of MSE_c)   -- the standard definition

By Jensen's inequality the per-channel figure is always the larger of the two,
and the gap grows as the channels' errors diverge.  **Underwater is the regime
of maximum channel divergence** -- red is attenuated to near-nothing over range
while blue is barely affected -- so the convention inflates results more here
than anywhere else.

Worse, the choice is usually made by accident rather than by decision.  The
inherited `utils.image_utils.psnr` reduces with `.view(img.shape[0], -1)`,
which yields per-channel PSNR for a `(3,H,W)` tensor and pooled PSNR for a
`(1,3,H,W)` one.  This repository calls it both ways: the in-training report
passes `(3,H,W)` (per-channel), while the disk-based evaluation that writes
`eval_metrics.json` passes `(1,3,H,W)` via `readImages` (pooled).  The same
codebase therefore reports both conventions under one name, and the same flip
is documented in two other methods in the comparison set.

The functions here take the shape ambiguity away: each states its convention in
its name and normalises the input first, so a call site cannot silently change
which quantity is produced.
"""

from __future__ import annotations

import math
from typing import Any, Iterable

import torch


def _as_chw(img: torch.Tensor) -> torch.Tensor:
    """Normalise to (C,H,W), rejecting anything ambiguous.

    Accepting a batch here would reintroduce exactly the ambiguity this module
    exists to remove, so a batch of more than one is refused rather than
    silently averaged.
    """
    if img.dim() == 4:
        if img.shape[0] != 1:
            raise ValueError(
                f"expected a single image, got a batch of {img.shape[0]}. "
                f"Averaging a batch here would hide which convention is in use."
            )
        img = img[0]
    if img.dim() != 3:
        raise ValueError(f"expected (C,H,W) or (1,C,H,W), got {tuple(img.shape)}")
    return img


def _mse_per_channel(a: torch.Tensor, b: torch.Tensor) -> torch.Tensor:
    a, b = _as_chw(a).float(), _as_chw(b).float()
    return ((a - b) ** 2).reshape(a.shape[0], -1).mean(dim=1)


def psnr_per_channel(a: torch.Tensor, b: torch.Tensor, data_range: float = 1.0) -> float:
    """Mean over channels of the per-channel PSNR.

    SeaSplat's in-training convention.  Reported so that A0 stays comparable
    with SeaSplat's own published table.
    """
    mse = _mse_per_channel(a, b).clamp_min(1e-20)
    return float((20.0 * torch.log10(data_range / mse.sqrt())).mean().item())


def psnr_pooled(a: torch.Tensor, b: torch.Tensor, data_range: float = 1.0) -> float:
    """PSNR of the mean squared error pooled over all pixels and channels.

    The standard definition, and the one SeaThru-NeRF, UW-3DGS and TUGS use --
    so this is the figure that may be placed beside theirs.
    """
    mse = _mse_per_channel(a, b).mean().clamp_min(1e-20)
    return float((20.0 * torch.log10(data_range / mse.sqrt())).item())


def evaluate_pair(
    render: torch.Tensor,
    gt: torch.Tensor,
    ssim_fn: Any,
    lpips_fn: Any,
    lpips_net: str = "vgg",
) -> dict[str, float]:
    """Every metric for one image pair, each under a named convention.

    Full-frame and unmasked, matching every method compared against: no sky
    mask, no water-column mask, no alpha or valid-depth mask.
    """
    return {
        "psnr_per_channel": psnr_per_channel(render, gt),
        "psnr_pooled": psnr_pooled(render, gt),
        "ssim": float(ssim_fn(render, gt).mean().item()),
        "lpips": float(lpips_fn(render, gt, net_type=lpips_net).mean().item()),
    }


METRIC_KEYS = ("psnr_per_channel", "psnr_pooled", "ssim", "lpips")


def aggregate_images(records: Iterable[dict]) -> dict[str, Any]:
    """Mean of each metric over a set of images, plus the count.

    The count is not decoration: scene image counts here are unequal
    (21/29/20/18), so an unweighted mean over scenes and an image-weighted mean
    over the campaign are different numbers.  Recording `n_images` per scene is
    what lets the analysis compute both instead of silently picking one.
    """
    records = list(records)
    out: dict[str, Any] = {"n_images": len(records)}
    if not records:
        return out
    for key in METRIC_KEYS:
        vals = [r[key] for r in records if key in r and math.isfinite(r[key])]
        out[key] = sum(vals) / len(vals) if vals else float("nan")
    return out


def aggregate_scenes(per_scene: dict[str, dict]) -> dict[str, Any]:
    """Both weightings, side by side, never one silently.

    `unweighted` treats every scene equally -- SeaSplat's published convention.
    `image_weighted` weights by image count.  They differ here, and stating
    which is used removes an easy source of disagreement.
    """
    scenes = {k: v for k, v in per_scene.items() if v.get("n_images")}
    out: dict[str, Any] = {
        "scenes": sorted(scenes),
        "n_scenes": len(scenes),
        "n_images_total": sum(v["n_images"] for v in scenes.values()),
        "unweighted": {},
        "image_weighted": {},
    }
    if not scenes:
        return out

    for key in METRIC_KEYS:
        vals = [(v[key], v["n_images"]) for v in scenes.values()
                if key in v and math.isfinite(v[key])]
        if not vals:
            out["unweighted"][key] = float("nan")
            out["image_weighted"][key] = float("nan")
            continue
        out["unweighted"][key] = sum(x for x, _ in vals) / len(vals)
        total = sum(n for _, n in vals)
        out["image_weighted"][key] = sum(x * n for x, n in vals) / total
    return out


def convention_note(lpips_net: str, container: str) -> dict[str, str]:
    """The provenance every reported number needs attached to it."""
    return {
        "psnr_per_channel": "mean over channels of PSNR(MSE_c); SeaSplat's "
                            "in-training convention; higher by Jensen",
        "psnr_pooled": "PSNR of MSE pooled over pixels and channels; the "
                       "standard definition; comparable with SeaThru-NeRF, "
                       "UW-3DGS, TUGS",
        "ssim": "11x11 Gaussian window, sigma 1.5, standard 3DGS implementation",
        "lpips": f"backbone={lpips_net}; VGG and AlexNet give systematically "
                 f"different values and no source paper states which it used",
        "masking": "none; full-frame, matching every method compared against",
        "container": f"metrics computed on 8-bit images re-read from disk as "
                     f"{container}; not comparable with methods that score "
                     f"linear pre-photofinished data",
    }
