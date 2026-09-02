"""Add the same densification breakdown to a vanilla SeaSplat checkout.

    python -m tools.instrument_reference /content/seasplat_ref

Three hypotheses for the 6x density gap have now been eliminated by static
comparison -- the rasterizer (identical forward and backward on identical
inputs), the densification constants, and upstream drift (`ddc6259` is HEAD).
Everything comparable agrees, and the outcomes still differ sixfold, so the
next step is to watch both implementations densify rather than to diff them
again.

This patches `densify_and_prune` in a reference checkout to print the same
per-event breakdown ours now prints: how many primitives cleared the gradient
threshold, how many were cloned, how many split, and how many were pruned for
each of the three reasons. Run both for a few thousand iterations and the
event streams line up one to one -- the intervals and start points are
identical constants on both sides.

**This is a diagnostic patch, not a baseline.** It prints and counts; it
changes no behaviour. A checkout patched this way must not be used to produce
the SS reference numbers -- clone a fresh one for that.
"""

from __future__ import annotations

import sys
from pathlib import Path

ORIGINAL = """    def densify_and_prune(self, max_grad, min_opacity, extent, max_screen_size):
        grads = self.xyz_gradient_accum / self.denom
        grads[grads.isnan()] = 0.0

        self.densify_and_clone(grads, max_grad, extent)
        self.densify_and_split(grads, max_grad, extent)

        prune_mask = (self.get_opacity < min_opacity).squeeze()
        if max_screen_size:
            big_points_vs = self.max_radii2D > max_screen_size
            big_points_ws = self.get_scaling.max(dim=1).values > 0.1 * extent
            prune_mask = torch.logical_or(torch.logical_or(prune_mask, big_points_vs), big_points_ws)
        self.prune_points(prune_mask)

        torch.cuda.empty_cache()"""

INSTRUMENTED = """    def densify_and_prune(self, max_grad, min_opacity, extent, max_screen_size):
        grads = self.xyz_gradient_accum / self.denom
        grads[grads.isnan()] = 0.0

        _n_before = self._xyz.shape[0]
        _n_over = int((torch.norm(grads, dim=-1) >= max_grad).sum().item())

        self.densify_and_clone(grads, max_grad, extent)
        _n_cloned = self._xyz.shape[0] - _n_before
        self.densify_and_split(grads, max_grad, extent)
        _n_split = self._xyz.shape[0] - _n_before - _n_cloned

        _low = (self.get_opacity < min_opacity).squeeze()
        prune_mask = _low
        _n_vs = _n_ws = 0
        if max_screen_size:
            big_points_vs = self.max_radii2D > max_screen_size
            big_points_ws = self.get_scaling.max(dim=1).values > 0.1 * extent
            _n_vs = int(big_points_vs.sum().item())
            _n_ws = int(big_points_ws.sum().item())
            prune_mask = torch.logical_or(torch.logical_or(prune_mask, big_points_vs), big_points_ws)
        _n_pruned = int(prune_mask.sum().item())
        self.prune_points(prune_mask)

        GaussianModel._densify_event = getattr(GaussianModel, "_densify_event", 0) + 1
        print(
            f"[densify] ev={GaussianModel._densify_event} before={_n_before} "
            f"over_grad={_n_over} ({100.0 * _n_over / max(1, _n_before):.1f}%) "
            f"clone=+{_n_cloned} split=+{_n_split} "
            f"prune=-{_n_pruned} (alpha={int(_low.sum().item())} "
            f"screen={_n_vs} world={_n_ws}) "
            f"after={self._xyz.shape[0]}",
            flush=True,
        )

        torch.cuda.empty_cache()"""


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2

    target = Path(sys.argv[1]) / "scene" / "gaussian_model.py"
    if not target.exists():
        print(f"FATAL: {target} not found -- is that a SeaSplat checkout?")
        return 2

    src = target.read_text(encoding="utf-8")
    if "[densify] ev=" in src:
        print(f"already instrumented: {target}")
        return 0
    if ORIGINAL not in src:
        print(f"FATAL: densify_and_prune in {target} does not match the expected\n"
              f"upstream text. The checkout is not ddc6259, or it has been edited.\n"
              f"Refusing to patch rather than silently instrumenting something else.")
        return 1

    target.write_text(src.replace(ORIGINAL, INSTRUMENTED), encoding="utf-8")
    print(f"instrumented {target}")
    print("\nOurs prints  it=<iteration>; this prints  ev=<event index>.")
    print("Both start at iteration 600 and fire every 100, so event N here is")
    print("iteration 500 + 100*N there -- they align one to one.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
