"""Rendering throughput and peak memory, measured on the trained model.

Frame rate is the efficiency measure all three mechanisms affect — the others
each move one axis — and the design rests two falsifiable predictions on it:

* the quantization cell should show **approximately no** frame-rate gain, since
  the published two-to-three-fold speedup of that method is credited by its own
  authors to an opacity sparsity penalty this study disables;
* gains from primitive reduction should be **sub-linear**, because rasterization
  cost is dominated by covered pixels rather than primitive count.

Neither is testable without this measurement.

Two details decide whether the number means anything.

**Synchronisation.** CUDA kernel launches are asynchronous, so timing them
without `torch.cuda.synchronize()` measures how fast Python can enqueue work.
That reliably produces impressive and meaningless figures.

**Warm-up.** The first render of a session pays autotuning, allocator growth
and lazy module initialisation. Discarding a few frames costs milliseconds and
removes a bias that is large at these frame counts.

What is timed is the **colour pass alone** — the rasterization that produces
the medium-free radiance a viewer displays. The depth and alpha probes exist to
serve the training objective and are not part of rendering; including them
would measure this study's training arrangement rather than the model's
rendering cost, and would not be comparable with any published figure.
"""

from __future__ import annotations

import time
from typing import Any

import torch


def profile_rendering(
    render_fn: Any,
    cameras: list,
    gaussians: Any,
    pipe: Any,
    background: torch.Tensor,
    warmup: int = 5,
    repeats: int = 20,
) -> dict[str, Any]:
    """Time the colour pass over `cameras`, and report peak memory.

    Returns a dict for the run's `cost` block. Never raises: a profiling
    failure must not lose a finished training run, so it is reported in the
    payload instead.
    """
    out: dict[str, Any] = {
        "render_fps": None,
        "render_ms_per_frame": None,
        "render_frames_timed": 0,
        "render_warmup_frames": warmup,
        "render_repeats": repeats,
        "render_ms_per_frame_sd": None,
        "render_ms_per_frame_cv": None,
        "render_note": None,
    }
    if not cameras:
        out["render_note"] = "no cameras supplied"
        return out

    try:
        with torch.no_grad():
            for i in range(warmup):
                render_fn(cameras[i % len(cameras)], gaussians, pipe, background)
            if torch.cuda.is_available():
                torch.cuda.synchronize()
                # Reset here, not earlier: peak memory should describe
                # rendering, not whatever training left behind.
                torch.cuda.reset_peak_memory_stats()

            # Time each full pass over the cameras separately, rather than one
            # block. The scenes hold only three or four held-out views, so a
            # single block is under a fifth of a second and gives no way to
            # tell a stable figure from a noisy one. Per-pass samples cost one
            # extra synchronise each and yield a dispersion.
            per_pass: list[float] = []
            for _ in range(repeats):
                t0 = time.perf_counter()
                for cam in cameras:
                    render_fn(cam, gaussians, pipe, background)
                if torch.cuda.is_available():
                    torch.cuda.synchronize()
                per_pass.append(time.perf_counter() - t0)

            elapsed = sum(per_pass)

        n = len(cameras) * repeats
        out["render_frames_timed"] = n
        out["render_ms_per_frame"] = round(1000.0 * elapsed / max(1, n), 4)
        out["render_fps"] = round(n / elapsed, 2) if elapsed > 0 else None

        # Dispersion of per-frame time across passes. A frame rate quoted
        # without it cannot be compared against another cell's: the design's
        # sub-linearity prediction is a claim about ratios, and a ratio of two
        # unstable numbers says nothing.
        if len(per_pass) > 1:
            ms = [1000.0 * t / len(cameras) for t in per_pass]
            mean = sum(ms) / len(ms)
            var = sum((x - mean) ** 2 for x in ms) / (len(ms) - 1)
            out["render_ms_per_frame_sd"] = round(var ** 0.5, 4)
            out["render_ms_per_frame_cv"] = (
                round(100.0 * (var ** 0.5) / mean, 2) if mean > 0 else None
            )
        if torch.cuda.is_available():
            out["render_peak_mem_mb"] = round(
                torch.cuda.max_memory_allocated() / 1024 / 1024, 1
            )
        out["render_note"] = (
            "colour pass only, cuda-synchronised, over the held-out views; "
            "probe passes excluded as they serve training rather than rendering"
        )
    except Exception as exc:  # noqa: BLE001 -- never lose a finished run
        out["render_note"] = f"profiling failed: {type(exc).__name__}: {exc}"

    return out
