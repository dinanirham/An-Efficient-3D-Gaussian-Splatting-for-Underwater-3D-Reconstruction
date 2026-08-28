"""M5 acceptance test for quantization-aware VQ. Needs torch, not a GPU.

    python -m tools.verify_quantize

T5 is the one that matters most.  Quantization-aware training only works
because the forward pass renders the *quantized* values while gradients reach
the *unquantized* parameters -- that is what lets the optimizer move them
somewhere that quantizes well, and it is exactly what post-hoc clustering
cannot do.  A straight-through estimator that silently detached would still
train, still converge, and still produce plausible numbers; it would just be
post-hoc quantization wearing the wrong name.

T6 covers the conflict this milestone creates rather than fixes: the
assignment vector is per-primitive, so pruning desynchronises it from the
model.  That conflict does not exist for post-hoc quantization.
"""

from __future__ import annotations

import sys
from pathlib import Path

import torch

sys.path.append(str(Path(__file__).resolve().parent.parent))

from source.quantize import AttributeQuantizer, VectorQuantizer  # noqa: E402

_results: list[tuple[str, bool, str]] = []


def check(name: str, fn) -> None:
    try:
        ok, detail = fn()
    except Exception as exc:  # noqa: BLE001
        ok, detail = False, f"raised {type(exc).__name__}: {exc}"
    _results.append((name, ok, detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")


def clustered_data(n_per: int = 200, dim: int = 3) -> torch.Tensor:
    """Four well-separated blobs -- k=4 should recover them exactly."""
    torch.manual_seed(0)
    centres = torch.tensor(
        [[0.0, 0.0, 0.0], [10.0, 0.0, 0.0], [0.0, 10.0, 0.0], [0.0, 0.0, 10.0]]
    )[:, :dim]
    return torch.cat([c + 0.05 * torch.randn(n_per, dim) for c in centres])


# ---------------------------------------------------------------------------


def t1_recovers_known_clusters():
    torch.manual_seed(0)
    data = clustered_data()
    q = VectorQuantizer("test", num_clusters=4, num_iters=10)
    out = q.quantize(data, assign=True)

    err = (out - data).abs().max().item()
    # Each blob has radius ~0.05*3 sigma; centroids should sit inside them.
    return err < 0.5, f"max|quantized - original| = {err:.4f} (blob sigma 0.05)"


def t2_forward_returns_centroids():
    """The forward value must BE a codebook entry, not the original."""
    torch.manual_seed(0)
    data = clustered_data()
    q = VectorQuantizer("test", num_clusters=4, num_iters=10)
    out = q.quantize(data, assign=True)

    distinct = torch.unique(out.round(decimals=3), dim=0).shape[0]
    return distinct <= 4, f"{distinct} distinct output vectors (must be <= k=4)"


def t3_cheap_path_preserves_partition():
    """Between reassignments the partition must be reused, not recomputed."""
    torch.manual_seed(0)
    data = clustered_data()
    q = VectorQuantizer("test", num_clusters=4, num_iters=1)
    q.quantize(data, assign=True)
    before = q.nn_index.clone()

    # Perturb slightly and run the cheap path.
    q.quantize(data + 0.001, assign=False)
    same = torch.equal(before, q.nn_index)
    return same, f"assignments unchanged on the cheap path: {same}"


def t4_empty_clusters_survive_pruning():
    """Clusters emptied by pruning must not produce NaN centres."""
    torch.manual_seed(0)
    data = clustered_data()
    q = VectorQuantizer("test", num_clusters=4, num_iters=10)
    q.quantize(data, assign=True)

    # Drop three of the four blobs entirely.
    keep = torch.zeros(data.shape[0], dtype=torch.bool)
    keep[:200] = True
    q.prune(keep)
    out = q.quantize(data[keep], assign=False)

    finite = bool(torch.isfinite(q.centers).all() and torch.isfinite(out).all())
    return finite, f"all centres finite after emptying 3/4 clusters: {finite}"


def t5_straight_through_gradient():
    """THE decisive test: forward is quantized, gradient reaches the raw param."""
    torch.manual_seed(0)
    data = clustered_data().requires_grad_(True)
    q = VectorQuantizer("test", num_clusters=4, num_iters=10)
    out = q.quantize(data, assign=True)

    # Forward must differ from the input (it is a centroid)...
    forward_differs = (out - data).abs().max().item() > 1e-4
    # ...but the gradient must pass through as identity.
    out.sum().backward()
    grad = data.grad
    grad_ok = (
        grad is not None
        and torch.isfinite(grad).all()
        and torch.allclose(grad, torch.ones_like(grad))
    )
    return forward_differs and grad_ok, (
        f"forward quantized={forward_differs}, "
        f"d(sum q)/d(param) == 1 everywhere={grad_ok}"
    )


def t6_prune_keeps_indices_aligned():
    """Pruning must index-select nn_index, or the codebook desynchronises."""
    torch.manual_seed(0)
    data = clustered_data()
    q = VectorQuantizer("test", num_clusters=4, num_iters=10)
    q.quantize(data, assign=True)
    original = q.nn_index.clone()

    keep = torch.zeros(data.shape[0], dtype=torch.bool)
    keep[::2] = True                    # keep every other primitive
    q.prune(keep)

    aligned = (
        q.nn_index.shape[0] == int(keep.sum())
        and torch.equal(q.nn_index, original[keep])
    )
    # And after pruning, quantize must still work on the smaller model.
    out = q.quantize(data[keep], assign=False)
    return aligned and out.shape[0] == int(keep.sum()), (
        f"nn_index {original.shape[0]} -> {q.nn_index.shape[0]} "
        f"(expected {int(keep.sum())}), aligned={aligned}"
    )


def t7_stale_length_forces_reassignment():
    """If nn_index length ever mismatches, reassign rather than crash or corrupt."""
    torch.manual_seed(0)
    data = clustered_data()
    q = VectorQuantizer("test", num_clusters=4, num_iters=10)
    q.quantize(data, assign=True)

    # Simulate a prune that forgot to notify the quantizer.
    smaller = data[:300]
    out = q.quantize(smaller, assign=False)
    ok = out.shape[0] == 300 and q.nn_index.shape[0] == 300
    return ok, f"recovered from a desynchronised index: out={tuple(out.shape)}"


def t8_storage_report_uses_codebook_width():
    """Index width must be ceil(log2 k), not ceil(log2 N)."""
    q = VectorQuantizer("test", num_clusters=4096, num_iters=1)
    q.vec_dim = 3
    rep = q.storage_bits(num_primitives=1_000_000)
    # log2(4096) = 12, whereas log2(1e6) ~ 20 -- the defect being avoided.
    ok = rep["bits_per_index"] == 12
    return ok, f"bits_per_index={rep['bits_per_index']} (must be 12, not ~20)"


def t9_ratio_normalised_to_this_baseline():
    """The reported ratio must be against 14 floats/primitive, not 59."""
    aq = AttributeQuantizer(num_clusters=4096, num_iters=1)
    for name, dim in (("dc", 3), ("scale", 3), ("rotation", 4)):
        aq.quantizers[name].vec_dim = dim
    rep = aq.storage_report(num_primitives=1_000_000)
    ok = (
        rep["baseline_bits_14f"] == 1_000_000 * 14 * 32
        and rep["ratio_vs_this_baseline"] > 1.0
        and "14 floats" in rep["note"]
    )
    return ok, (
        f"ratio={rep['ratio_vs_this_baseline']:.2f}x against a 14-float "
        f"baseline; unquantized remainder="
        f"{rep['unquantized_bits'] / 8 / 1024 / 1024:.1f} MB"
    )


def main() -> int:
    check("T1 recovers known clusters", t1_recovers_known_clusters)
    check("T2 forward returns codebook entries", t2_forward_returns_centroids)
    check("T3 cheap path reuses the partition", t3_cheap_path_preserves_partition)
    check("T4 emptied clusters stay finite", t4_empty_clusters_survive_pruning)
    check("T5 straight-through gradient reaches raw params  <-- decisive", t5_straight_through_gradient)
    check("T6 prune keeps nn_index aligned", t6_prune_keeps_indices_aligned)
    check("T7 stale index length forces reassignment", t7_stale_length_forces_reassignment)
    check("T8 index width is ceil(log2 k), not log2 N", t8_storage_report_uses_codebook_width)
    check("T9 ratio is normalised to this baseline's 14 floats", t9_ratio_normalised_to_this_baseline)

    failed = [n for n, ok, _ in _results if not ok]
    print("\n" + "=" * 68)
    if failed:
        print(f"M5 QUANTIZATION: FAILED ({len(failed)}/{len(_results)})")
        for n in failed:
            print(f"  - {n}")
        return 1
    print(f"M5 QUANTIZATION: PASSED ({len(_results)}/{len(_results)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
