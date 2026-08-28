"""Acceptance test for the PSNR conventions and aggregation. Needs torch, not a GPU.

    python -m tools.verify_metrics

T4 is the one that earns its place.  The inherited `utils.image_utils.psnr`
reduces with `.view(img.shape[0], -1)`, so it computes per-channel PSNR for a
(3,H,W) tensor and pooled PSNR for a (1,3,H,W) one -- and this repository calls
it both ways.  T4 pins that behaviour down as an executable fact rather than a
claim someone has to re-derive from the shapes at each call site.

T1 and T6 measure why it matters: the gap between the conventions is a function
of how much the channels' errors diverge, and underwater imagery is the regime
where they diverge most.
"""

from __future__ import annotations

import sys
from pathlib import Path

import torch

sys.path.append(str(Path(__file__).resolve().parent.parent))

from utils.image_utils import psnr as inherited_psnr  # noqa: E402
from utils.metrics_conventions import (  # noqa: E402
    aggregate_images,
    aggregate_scenes,
    psnr_per_channel,
    psnr_pooled,
)

_results: list[tuple[str, bool, str]] = []


def check(name: str, fn) -> None:
    try:
        ok, detail = fn()
    except Exception as exc:  # noqa: BLE001
        ok, detail = False, f"raised {type(exc).__name__}: {exc}"
    _results.append((name, ok, detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")


def divergent_pair(h: int = 32, w: int = 32):
    """An underwater-like error profile: red badly wrong, blue nearly right."""
    torch.manual_seed(0)
    gt = torch.rand(3, h, w)
    err = torch.zeros(3, h, w)
    err[0] = 0.30      # red   -- attenuated to near-nothing over range
    err[1] = 0.05      # green
    err[2] = 0.005     # blue  -- barely affected
    return (gt + err).clamp(0, 1), gt


def uniform_pair(h: int = 32, w: int = 32):
    torch.manual_seed(0)
    gt = torch.rand(3, h, w)
    return (gt + 0.1).clamp(0, 1), gt


# ---------------------------------------------------------------------------


def t1_jensen_ordering():
    """Per-channel >= pooled always, with equality only when channels agree."""
    r, g = divergent_pair()
    per, pool = psnr_per_channel(r, g), psnr_pooled(r, g)

    ru, gu = uniform_pair()
    per_u, pool_u = psnr_per_channel(ru, gu), psnr_pooled(ru, gu)

    ok = per > pool and abs(per_u - pool_u) < 0.05
    return ok, (
        f"divergent: per-channel={per:.3f} > pooled={pool:.3f} "
        f"(gap {per - pool:.3f} dB); uniform gap={abs(per_u - pool_u):.4f} dB"
    )


def t2_shape_agnostic():
    """(C,H,W) and (1,C,H,W) must give identical numbers."""
    r, g = divergent_pair()
    a = psnr_per_channel(r, g), psnr_pooled(r, g)
    b = psnr_per_channel(r[None], g[None]), psnr_pooled(r[None], g[None])
    ok = abs(a[0] - b[0]) < 1e-6 and abs(a[1] - b[1]) < 1e-6
    return ok, f"chw={a[0]:.6f}/{a[1]:.6f}  bchw={b[0]:.6f}/{b[1]:.6f}"


def t3_batch_refused():
    """A real batch must be refused, not silently averaged."""
    r, g = divergent_pair()
    try:
        psnr_pooled(r[None].repeat(2, 1, 1, 1), g[None].repeat(2, 1, 1, 1))
    except ValueError as exc:
        return "batch" in str(exc), f"refused: {str(exc)[:60]}..."
    return False, "a batch of 2 was silently accepted"


def t4_inherited_function_is_shape_dependent():
    """Pin down what the inherited psnr() actually does at each call shape."""
    r, g = divergent_pair()

    chw = float(inherited_psnr(r, g).mean().item())          # in-training path
    bchw = float(inherited_psnr(r[None], g[None]).mean().item())  # disk path

    matches_per_channel = abs(chw - psnr_per_channel(r, g)) < 1e-4
    matches_pooled = abs(bchw - psnr_pooled(r, g)) < 1e-4
    differ = abs(chw - bchw) > 0.1

    ok = matches_per_channel and matches_pooled and differ
    return ok, (
        f"(3,H,W)->{chw:.3f} == per-channel:{matches_per_channel}; "
        f"(1,3,H,W)->{bchw:.3f} == pooled:{matches_pooled}; "
        f"same function, {abs(chw - bchw):.3f} dB apart"
    )


def t5_aggregation_weightings_differ():
    """Unequal scene sizes must make the two weightings disagree."""
    per_scene = {
        # Roughly the real corpus: 21 / 29 / 20 / 18 images.
        "Curasao": {"n_images": 21, "psnr_pooled": 26.0, "psnr_per_channel": 27.0,
                    "ssim": 0.85, "lpips": 0.20},
        "IUI3-RedSea": {"n_images": 29, "psnr_pooled": 22.0, "psnr_per_channel": 23.0,
                        "ssim": 0.80, "lpips": 0.25},
        "JapaneseGradens-RedSea": {"n_images": 20, "psnr_pooled": 28.0,
                                   "psnr_per_channel": 29.0, "ssim": 0.88, "lpips": 0.18},
        "Panama": {"n_images": 18, "psnr_pooled": 24.0, "psnr_per_channel": 25.0,
                   "ssim": 0.82, "lpips": 0.22},
    }
    agg = aggregate_scenes(per_scene)
    unw = agg["unweighted"]["psnr_pooled"]
    iw = agg["image_weighted"]["psnr_pooled"]
    ok = (
        agg["n_scenes"] == 4
        and agg["n_images_total"] == 88
        and abs(unw - iw) > 0.05
    )
    return ok, (
        f"unweighted={unw:.4f}  image_weighted={iw:.4f}  "
        f"differ by {abs(unw - iw):.4f} dB over {agg['n_images_total']} images"
    )


def t6_gap_grows_with_divergence():
    """The convention gap must scale with channel divergence, not be a constant."""
    torch.manual_seed(0)
    gt = torch.rand(3, 32, 32)
    gaps = []
    for spread in (0.0, 0.1, 0.3):
        err = torch.zeros(3, 32, 32)
        err[0], err[1], err[2] = 0.05 + spread, 0.05, max(0.001, 0.05 - spread / 2)
        r = (gt + err).clamp(0, 1)
        gaps.append(psnr_per_channel(r, gt) - psnr_pooled(r, gt))
    ok = gaps[0] < gaps[1] < gaps[2]
    return ok, "gap by divergence: " + ", ".join(f"{g:.3f}" for g in gaps) + " dB"


def t7_image_aggregation_counts():
    recs = [
        {"psnr_pooled": 20.0, "psnr_per_channel": 21.0, "ssim": 0.8, "lpips": 0.2},
        {"psnr_pooled": 30.0, "psnr_per_channel": 31.0, "ssim": 0.9, "lpips": 0.1},
    ]
    agg = aggregate_images(recs)
    ok = agg["n_images"] == 2 and abs(agg["psnr_pooled"] - 25.0) < 1e-9
    return ok, f"n={agg['n_images']} mean pooled={agg['psnr_pooled']}"


def main() -> int:
    check("T1 per-channel exceeds pooled, and only when channels diverge", t1_jensen_ordering)
    check("T2 conventions are shape-agnostic", t2_shape_agnostic)
    check("T3 a real batch is refused", t3_batch_refused)
    check("T4 inherited psnr() is shape-dependent  <-- documents the flip", t4_inherited_function_is_shape_dependent)
    check("T5 the two aggregations disagree on unequal scenes", t5_aggregation_weightings_differ)
    check("T6 the gap scales with channel divergence", t6_gap_grows_with_divergence)
    check("T7 per-image aggregation records counts", t7_image_aggregation_counts)

    failed = [n for n, ok, _ in _results if not ok]
    print("\n" + "=" * 68)
    if failed:
        print(f"METRIC CONVENTIONS: FAILED ({len(failed)}/{len(_results)})")
        for n in failed:
            print(f"  - {n}")
        return 1
    print(f"METRIC CONVENTIONS: PASSED ({len(_results)}/{len(_results)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
