"""Acceptance test for the compressed artifact and its size accounting.

    python -m tools.verify_storage

Needs torch, not a GPU.

T2 is the reason this module exists.  Before it, the codebooks were persisted
with `torch.save`, which stores the assignment vector as int64 -- eight bytes
per index where twelve bits suffice.  A compression figure measured from that
file would have been roughly 5x too large, and it would have looked entirely
reasonable: the file exists, the numbers are real, and nothing errors.  The
only way to catch it is to compare what is written against what a correct
encoder would spend.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import numpy as np
import torch

sys.path.append(str(Path(__file__).resolve().parent.parent))

from source.quantize import AttributeQuantizer  # noqa: E402
from source.storage import (  # noqa: E402
    BASELINE_FLOATS_PER_PRIMITIVE,
    index_bits,
    measure_model_size,
    pack_indices,
    unpack_indices,
    write_compressed_model,
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
    def __init__(self, n: int = 5000) -> None:
        torch.manual_seed(0)
        self._xyz = torch.randn(n, 3)
        self._opacity = torch.randn(n, 1)
        self._features_dc = torch.randn(n, 1, 3)
        self._scaling = torch.randn(n, 3)
        self._rotation = torch.randn(n, 4)
        self.max_sh_degree = 0
        self._quant_override: dict = {}

    @property
    def get_xyz(self) -> torch.Tensor:
        return self._xyz

    # AttributeQuantizer.apply installs overrides through these.
    def set_quant_override(self, name: str, tensor) -> None:
        self._quant_override[name] = tensor

    def clear_quant_override(self) -> None:
        self._quant_override = {}


def fitted_quantizer(g: FakeGaussians, k: int = 4096) -> AttributeQuantizer:
    q = AttributeQuantizer(num_clusters=k, num_iters=1)
    q.apply(g, assign=True)
    return q


# ---------------------------------------------------------------------------


def t1_pack_roundtrip():
    """Packing must be exactly invertible at every width used."""
    rng = np.random.default_rng(0)
    details = []
    ok_all = True
    for k in (2, 256, 4096, 32768):
        bits = index_bits(k)
        idx = rng.integers(0, k, size=1000)
        back = unpack_indices(pack_indices(idx, bits), len(idx), bits)
        exact = bool((back == idx).all())
        ok_all &= exact
        details.append(f"k={k}({bits}b):{'ok' if exact else 'MISMATCH'}")
    return ok_all, " ".join(details)


def t2_packing_beats_naive_storage():
    """THE decisive check: packed indices must approach the analytical size."""
    n, k = 100_000, 4096
    bits = index_bits(k)
    idx = np.random.default_rng(0).integers(0, k, size=n)

    packed = len(pack_indices(idx, bits))
    analytical = n * bits / 8
    int64_naive = n * 8            # what torch.save would have written

    ok = packed <= analytical * 1.001 and packed < int64_naive / 5
    return ok, (
        f"packed={packed}B  analytical={analytical:.0f}B  "
        f"int64={int64_naive}B  ({int64_naive / packed:.1f}x saved)"
    )


def t3_overflow_refused():
    """An index that does not fit must raise, not silently truncate."""
    try:
        pack_indices(np.array([0, 5000]), bits=12)   # 5000 >= 4096
    except ValueError as exc:
        return "does not fit" in str(exc), f"refused: {str(exc)[:55]}"
    return False, "an out-of-range index was silently packed"


def t4_quantized_artifact_components():
    with tempfile.TemporaryDirectory() as tmp:
        g = FakeGaussians(5000)
        q = fitted_quantizer(g, k=4096)
        d = write_compressed_model(Path(tmp) / "art", g, q)
        rep = measure_model_size(d)

        names = set(rep["components_bytes"])
        must_have = {"xyz.npy", "opacity.npy", "indices.bin", "codebooks.npz",
                     "meta.json"}
        # The attributes the codebooks encode must NOT be written again.
        must_not = {"features_dc.npy", "scaling.npy", "rotation.npy"}
        ok = must_have <= names and not (must_not & names)
        return ok, (
            f"{sorted(names)}; total={rep['total_mb']:.4f} MB, "
            f"{rep['bytes_per_primitive']:.2f} B/primitive"
        )


def t5_ratio_normalised_and_labelled():
    with tempfile.TemporaryDirectory() as tmp:
        g = FakeGaussians(20_000)
        q = fitted_quantizer(g, k=4096)
        d = write_compressed_model(Path(tmp) / "art", g, q)
        rep = measure_model_size(d)

        expected_baseline = 20_000 * BASELINE_FLOATS_PER_PRIMITIVE * 4
        ok = (
            rep["baseline"]["total_bytes"] == expected_baseline
            and rep["ratio_vs_this_baseline"] > 1.0
            and "14 floats" in rep["note"]
            and "59" in rep["note"]
        )
        return ok, (
            f"ratio={rep['ratio_vs_this_baseline']:.2f}x vs 14-float baseline; "
            f"note flags the 59-float mismatch"
        )


def t6_unquantized_cell_also_measured():
    """Unquantized cells need an artifact too, or sizes are not comparable."""
    with tempfile.TemporaryDirectory() as tmp:
        g = FakeGaussians(5000)
        d = write_compressed_model(Path(tmp) / "art", g, None)
        rep = measure_model_size(d)
        names = set(rep["components_bytes"])
        # Without a codebook, the attributes must be stored directly.
        ok = {"features_dc.npy", "scaling.npy", "rotation.npy"} <= names
        return ok, (
            f"unquantized artifact = {rep['total_mb']:.4f} MB, "
            f"{rep['bytes_per_primitive']:.2f} B/primitive "
            f"(baseline is {BASELINE_FLOATS_PER_PRIMITIVE * 4} B/primitive)"
        )


def t7_measured_reconciles_with_analytical():
    """Measured size must be close to the analytical count, and the gap named."""
    with tempfile.TemporaryDirectory() as tmp:
        g = FakeGaussians(50_000)
        q = fitted_quantizer(g, k=4096)
        d = write_compressed_model(Path(tmp) / "art", g, q)
        rep = measure_model_size(d)
        over = rep["measured_over_analytical"]
        ok = 0.95 <= over <= 1.25
        return ok, (
            f"measured/analytical = {over:.4f} "
            f"({rep['total_bytes']}B vs {rep['analytical_bytes']}B); "
            f"the excess is container overhead, and is reported"
        )


def t8_medium_parameters_counted():
    """Nine scalars, but they must appear or it is not an accounting."""
    class FakeBs:
        backscatter_conv_params = torch.randn(3, 1, 1, 1)
        B_inf = torch.randn(3, 1, 1)

    class FakeAt:
        attenuation_conv_params = torch.randn(3, 1, 1, 1)

    with tempfile.TemporaryDirectory() as tmp:
        g = FakeGaussians(1000)
        d = write_compressed_model(
            Path(tmp) / "art", g, None, bs_model=FakeBs(), at_model=FakeAt()
        )
        rep = measure_model_size(d)
        ok = "medium.npz" in rep["components_bytes"]
        return ok, (
            f"medium.npz present, {rep['components_bytes'].get('medium.npz')} B "
            f"of {rep['total_bytes']} B total"
        )


def main() -> int:
    check("T1 index packing round-trips exactly", t1_pack_roundtrip)
    check("T2 packed indices approach the analytical size  <-- decisive", t2_packing_beats_naive_storage)
    check("T3 an out-of-range index is refused", t3_overflow_refused)
    check("T4 quantized artifact has the right components, and no duplicates", t4_quantized_artifact_components)
    check("T5 ratio is normalised to 14 floats and labelled", t5_ratio_normalised_and_labelled)
    check("T6 unquantized cells produce a comparable artifact", t6_unquantized_cell_also_measured)
    check("T7 measured size reconciles with the analytical count", t7_measured_reconciles_with_analytical)
    check("T8 medium parameters are counted", t8_medium_parameters_counted)

    failed = [n for n, ok, _ in _results if not ok]
    print("\n" + "=" * 68)
    if failed:
        print(f"MODEL SIZE ACCOUNTING: FAILED ({len(failed)}/{len(_results)})")
        for n in failed:
            print(f"  - {n}")
        return 1
    print(f"MODEL SIZE ACCOUNTING: PASSED ({len(_results)}/{len(_results)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
