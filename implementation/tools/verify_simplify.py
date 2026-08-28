"""M4 acceptance test for the simplification stage. Needs torch, not a GPU.

    python -m tools.verify_simplify

The decisive check is T3.  Mini-Splatting's argument for stochastic sampling
over deterministic top-k is that importance is *spatially autocorrelated*:
neighbouring primitives score similarly, so a threshold removes whole regions
rather than thinning uniformly.  That is a claim about coverage, not about
average importance, and it is invisible to any test that only checks "did we
keep the right number".  T3 builds an importance field with exactly that
structure and measures regional survival under both rules.
"""

from __future__ import annotations

import sys
from pathlib import Path

import torch

sys.path.append(str(Path(__file__).resolve().parent.parent))

from source.simplify import (  # noqa: E402
    accumulate_importance,
    cdf_keep_mask,
    sample_to_budget,
)

_results: list[tuple[str, bool, str]] = []


def check(name: str, fn) -> None:
    try:
        ok, detail = fn()
    except Exception as exc:  # noqa: BLE001
        ok, detail = False, f"raised {type(exc).__name__}: {exc}"
    _results.append((name, ok, detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")


class FakeGaussians:
    def __init__(self, n: int) -> None:
        self._n = n

    @property
    def get_xyz(self) -> torch.Tensor:
        return torch.zeros((self._n, 3))


def make_render_fn(per_view: list[dict]):
    """Replay canned rasterizer outputs, one dict per view."""
    calls = {"i": 0}

    def render_fn(cam, gaussians, pipe, bg):
        out = per_view[calls["i"]]
        calls["i"] += 1
        return out

    return render_fn


# ---------------------------------------------------------------------------


def t1_intersection_preserving():
    """A primitive that is never the argmax anywhere must end at probability 0."""
    n = 5
    views = [
        {  # primitive 4 projects but is never dominant
            "accum_weights": torch.tensor([1.0, 2.0, 3.0, 4.0, 5.0]),
            "area_proj": torch.tensor([10.0, 10.0, 10.0, 10.0, 10.0]),
            "area_max": torch.tensor([1.0, 1.0, 1.0, 1.0, 0.0]),
        },
        {
            "accum_weights": torch.tensor([1.0, 1.0, 1.0, 1.0, 9.0]),
            "area_proj": torch.tensor([10.0, 10.0, 10.0, 10.0, 10.0]),
            "area_max": torch.tensor([1.0, 1.0, 1.0, 1.0, 0.0]),
        },
    ]
    imp, area = accumulate_importance(
        FakeGaussians(n), [None, None], make_render_fn(views), None, None,
        metric="outdoor",
    )
    ok = imp[4].item() == 0.0 and (imp[:4] > 0).all().item()
    return ok, f"importance={imp.tolist()} (index 4 must be 0 despite weight 9)"


def t2_indoor_vs_outdoor():
    """indoor = raw weight; outdoor = weight / projected area, argmax-gated."""
    views = [{
        "accum_weights": torch.tensor([4.0, 4.0]),
        "area_proj": torch.tensor([2.0, 8.0]),
        "area_max": torch.tensor([1.0, 1.0]),
    }]
    ind, _ = accumulate_importance(
        FakeGaussians(2), [None], make_render_fn(views), None, None, metric="indoor")
    out, _ = accumulate_importance(
        FakeGaussians(2), [None], make_render_fn(views), None, None, metric="outdoor")
    ok = (
        torch.allclose(ind, torch.tensor([4.0, 4.0]))
        and torch.allclose(out, torch.tensor([2.0, 0.5]))
    )
    return ok, f"indoor={ind.tolist()} outdoor={out.tolist()} (expect [2.0, 0.5])"


def t3_sampling_thins_rather_than_deletes():
    """THE decisive test: stochastic sampling must preserve regional coverage."""
    torch.manual_seed(0)
    n_blocks, per_block, budget = 10, 100, 300
    importance = torch.cat([
        torch.full((per_block,), float(b + 1)) for b in range(n_blocks)
    ])

    keep = sample_to_budget(importance, budget)
    blocks_alive = sum(
        1 for b in range(n_blocks)
        if keep[b * per_block:(b + 1) * per_block].any()
    )

    # What a deterministic top-k would have done with the same budget.
    topk = torch.zeros_like(importance, dtype=torch.bool)
    topk[torch.topk(importance, budget).indices] = True
    topk_blocks_alive = sum(
        1 for b in range(n_blocks)
        if topk[b * per_block:(b + 1) * per_block].any()
    )

    ok = keep.sum().item() == budget and blocks_alive > topk_blocks_alive
    return ok, (
        f"kept={keep.sum().item()}  regions surviving: sampling={blocks_alive}/10 "
        f"vs top-k={topk_blocks_alive}/10"
    )


def t4_sampling_respects_budget_and_zeros():
    """Never exceed the budget; never resurrect a zero-importance primitive."""
    imp = torch.tensor([0.0, 0.0, 5.0, 3.0, 2.0])
    keep = sample_to_budget(imp, budget=10)     # budget exceeds eligibility
    ok = keep.sum().item() == 3 and not keep[0] and not keep[1]
    return ok, f"kept={keep.tolist()} (only the 3 non-zero are eligible)"


def t5_cdf_drops_bottom_mass():
    """The CDF prune must drop the bottom 1% of total importance mass."""
    imp = torch.cat([torch.full((100,), 0.001), torch.full((100,), 1.0)])
    keep = cdf_keep_mask(imp, thres=0.99)
    dropped_mass = imp[~keep].sum().item()
    total = imp.sum().item()
    ok = dropped_mass <= 0.01 * total and keep[100:].all().item()
    return ok, (
        f"dropped {(~keep).sum().item()} primitives = "
        f"{100 * dropped_mass / total:.3f}% of mass; all high-mass kept="
        f"{keep[100:].all().item()}"
    )


def t6_all_zero_importance_is_loud():
    """Identically-zero importance means a broken accumulator; fail loudly."""
    try:
        sample_to_budget(torch.zeros(10), budget=5)
    except RuntimeError as exc:
        return "area_max" in str(exc), f"raised: {str(exc)[:70]}..."
    return False, "silently accepted an all-zero importance vector"


def main() -> int:
    check("T1 intersection preserving zeroes never-argmax primitives", t1_intersection_preserving)
    check("T2 indoor and outdoor metrics differ as specified", t2_indoor_vs_outdoor)
    check("T3 sampling thins regions, top-k deletes them  <-- decisive", t3_sampling_thins_rather_than_deletes)
    check("T4 sampling respects budget and zero-importance", t4_sampling_respects_budget_and_zeros)
    check("T5 cdf prune drops the bottom 1% of mass", t5_cdf_drops_bottom_mass)
    check("T6 all-zero importance fails loudly", t6_all_zero_importance_is_loud)

    failed = [n for n, ok, _ in _results if not ok]
    print("\n" + "=" * 68)
    if failed:
        print(f"M4 SIMPLIFICATION: FAILED ({len(failed)}/{len(_results)})")
        for n in failed:
            print(f"  - {n}")
        return 1
    print(f"M4 SIMPLIFICATION: PASSED ({len(_results)}/{len(_results)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
