"""Acceptance test for the restored-image self-consistency metric (CD-28).

    python -m tools.verify_j_consistency

Pure numpy and stdlib. No GPU, no dataset, no rasterizer.

**What the metric is.** Quantization error enters the restored image `J-hat`
directly, since `J-hat` is built from the quantized colour coefficients. But
before that error reaches the measured in-medium image it is multiplied by the
attenuation map, which is at most one and approaches zero at range -- so the
fidelity metrics attenuate the evidence of quantization damage in exactly the
far-field regions where restoration matters most. `J-hat` has no ground truth
and never can, since obtaining it would require removing the water. Comparing a
model's restored output against *its own* unquantized restored output is the
only quantitative proxy available.

**Why it is computed from one model rather than from an A0/A3 pair.** The
methodology specifies "the otherwise-identical unquantized model", which reads
naturally as the matched-seed unquantized cell. That reading is confounded:
same-seed runs diverge by a median 21% in primitive count (E.22), so the
difference between A0 and A3 restored images mixes quantization damage with
trajectory divergence, and the confound is the same order as the effect.

The clean measurement is available because `save_ply` writes the *continuous*
parameters while the codebooks and index streams are stored beside them. One
model therefore carries both states, and swapping between them changes nothing
else -- same positions, same opacities, same view.

**T7 is the decisive check.** If the quantized reconstruction silently equals
the continuous parameters -- a wrong reshape, an unset override, indices read
from the wrong group -- then both renders are identical, the PSNR is infinite,
and the tool reports that quantization does no damage. That is a catastrophic
silent null of the same class as the CD-27 cache trap, and it would look like a
clean result rather than a bug.
"""

from __future__ import annotations

import json
import math
import sys
import tempfile
from pathlib import Path

import numpy as np

sys.path.append(str(Path(__file__).resolve().parent.parent))

from source.storage import index_bits, pack_indices, unpack_indices  # noqa: E402
from tools.j_consistency import (  # noqa: E402
    DRIFT_MARGIN_DB,
    GROUP_TO_ATTR,
    STORE_GLOB,
    compose_in_medium,
    continuous_state_verdict,
    discover_quantized_runs,
    psnr_pooled,
    reconstruct_quantized,
)

_results: list[tuple[str, bool, str]] = []


def check(name: str, fn) -> None:
    try:
        ok, detail = fn()
    except Exception as exc:  # noqa: BLE001
        ok, detail = False, f"raised {type(exc).__name__}: {exc}"
    _results.append((name, ok, detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")


def write_run(root: Path, cell: str, scene: str, seed: int, *, quantized: bool,
              n: int = 64, k: int = 16) -> Path:
    """Materialise a minimal stored run, quantized or not."""
    # The real layout: <campaign root>/runs/<cell>/<scene>/s<seed>/<store>.
    # Two earlier versions of this fixture omitted runs/, and the tool's glob
    # omitted it too, so the test passed while the tool found nothing on
    # Drive. The fixture now builds exactly what the worker builds, and the
    # discovery call receives the campaign root, exactly as 02_analysis
    # passes $DRIVE_ROOT.
    d = root / "runs" / cell / scene / f"s{seed}" / "compressed_30000"
    d.mkdir(parents=True, exist_ok=True)

    meta = {"num_primitives": n, "sh_degree": 0, "quantized": quantized,
            "groups": {}}

    if quantized:
        rng = np.random.default_rng(0)
        codebooks = {}
        packed = {}
        for name, dim in (("dc", 3), ("scale", 3), ("rotation", 4)):
            bits = index_bits(k)
            idx = rng.integers(0, k, size=n).astype(np.int64)
            codebooks[name] = rng.normal(size=(k, dim)).astype(np.float32)
            packed[name] = pack_indices(idx, bits)
            meta["groups"][name] = {"num_clusters": k, "bits_per_index": bits,
                                    "vec_dim": dim,
                                    "packed_bytes": len(packed[name])}
        with open(d / "indices.bin", "wb") as fh:
            for name in sorted(packed):
                fh.write(packed[name])
        np.savez(d / "codebooks.npz", **codebooks)

    (d / "meta.json").write_text(json.dumps(meta), encoding="utf-8")
    return d


# --------------------------------------------------------------------------


def t1_index_round_trip_is_lossless():
    rng = np.random.default_rng(1)
    bad = []
    for k in (2, 4, 16, 256, 4096):
        bits = index_bits(k)
        idx = rng.integers(0, k, size=257).astype(np.int64)
        back = unpack_indices(pack_indices(idx, bits), len(idx), bits)
        if not np.array_equal(idx, back[:len(idx)]):
            bad.append(k)
    return not bad, f"lossless at k in 2..4096 (failed: {bad or 'none'})"


def t2_reconstruction_is_a_codebook_lookup():
    k, n, dim = 8, 32, 3
    centers = np.arange(k * dim, dtype=np.float32).reshape(k, dim)
    idx = np.array([i % k for i in range(n)], dtype=np.int64)
    out = reconstruct_quantized(centers, idx, vec_dim=dim)
    ok = out.shape == (n, dim) and np.array_equal(out, centers[idx])
    return ok, f"shape {out.shape}, equals centers[indices]"


def t3_vec_dim_shapes_match_each_attribute():
    shapes = {}
    for name, dim in (("dc", 3), ("scale", 3), ("rotation", 4)):
        centers = np.zeros((4, dim), dtype=np.float32)
        idx = np.zeros(10, dtype=np.int64)
        shapes[name] = reconstruct_quantized(centers, idx, vec_dim=dim).shape
    ok = shapes == {"dc": (10, 3), "scale": (10, 3), "rotation": (10, 4)}
    return ok, f"{shapes}"


def t4_unquantized_runs_are_skipped():
    """No spurious pairing: a cell without M3 has nothing to compare."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_run(root, "A0", "Curasao", 0, quantized=False)
        write_run(root, "A3", "Curasao", 0, quantized=True)
        write_run(root, "A6", "Panama", 1, quantized=True)
        found = sorted(r.cell for r in discover_quantized_runs(root))
    ok = found == ["A3", "A6"]
    return ok, f"discovered {found}, A0 correctly skipped"


def t5_identical_images_report_a_capped_psnr():
    a = np.random.default_rng(2).random((3, 8, 8)).astype(np.float32)
    v = psnr_pooled(a, a.copy())
    ok = math.isfinite(v) and v >= 99.0
    return ok, f"identical -> {v:.1f} dB, finite and capped"


def t6_psnr_falls_as_error_grows():
    rng = np.random.default_rng(3)
    a = rng.random((3, 16, 16)).astype(np.float32)
    vals = [psnr_pooled(a, np.clip(a + s * rng.normal(size=a.shape), 0, 1).astype(np.float32))
            for s in (0.001, 0.01, 0.1)]
    ok = vals[0] > vals[1] > vals[2]
    return ok, "monotone: " + " > ".join(f"{v:.1f}" for v in vals)


def t7_reconstruction_actually_differs_from_continuous():
    """DECISIVE. A silent equality here reports 'quantization is free'.

    If the reconstruction ever returns the continuous values -- wrong reshape,
    override not installed, indices read from the wrong group -- both renders
    coincide, the PSNR is infinite, and the tool reports a clean null that
    looks like a result.
    """
    rng = np.random.default_rng(4)
    n, k, dim = 512, 16, 3
    continuous = rng.normal(size=(n, dim)).astype(np.float32)
    # A realistic codebook: k centres fitted loosely to the same distribution.
    centers = rng.normal(size=(k, dim)).astype(np.float32)
    idx = np.argmin(
        ((continuous[:, None, :] - centers[None, :, :]) ** 2).sum(-1), axis=1
    ).astype(np.int64)
    q = reconstruct_quantized(centers, idx, vec_dim=dim)

    identical = np.array_equal(q, continuous)
    rel = float(np.abs(q - continuous).mean() / (np.abs(continuous).mean() + 1e-12))
    ok = (not identical) and rel > 1e-3
    return ok, f"differs from continuous, mean relative change {rel:.3f}"


def t8_missing_codebooks_is_skipped_not_fatal():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        d = write_run(root, "A3", "Curasao", 0, quantized=True)
        (d / "codebooks.npz").unlink()
        runs = discover_quantized_runs(root)
        ok = runs == [] or all(not r.complete for r in runs)
    return ok, "incomplete store reported, not raised"


def t9_psnr_uses_the_pooled_convention():
    """One MSE over all pixels and channels, not a mean of per-channel PSNRs.

    The two differ by up to 12 dB on underwater-like error profiles, so the
    convention has to be pinned rather than inherited.
    """
    a = np.zeros((3, 4, 4), dtype=np.float32)
    b = np.zeros((3, 4, 4), dtype=np.float32)
    b[0] = 0.5                      # error confined to one channel
    mse = float(((a - b) ** 2).mean())      # pooled: divided by 3 channels
    want = 10.0 * math.log10(1.0 / mse)
    got = psnr_pooled(a, b)
    ok = math.isclose(got, want, rel_tol=1e-6)
    return ok, f"{got:.4f} dB == pooled {want:.4f} dB"


def t10_group_mapping_covers_every_quantized_attribute():
    ok = set(GROUP_TO_ATTR) == {"dc", "scale", "rotation"}
    return ok, f"groups {sorted(GROUP_TO_ATTR)} -> {sorted(GROUP_TO_ATTR.values())}"


def t11_store_glob_matches_what_train_py_writes():
    """DECISIVE. The search pattern is anchored to the writer, not to a guess.

    The tool once globbed "compact/", a directory nothing writes, and found no
    runs. Its own test passed because the fixture wrote "compact/" too -- the
    test encoded the same wrong assumption as the code. The fixture now writes
    what train.py writes, and this check reads train.py to confirm the pattern
    would match it.
    """
    import fnmatch
    src = (Path(__file__).resolve().parent.parent / "train.py").read_text(encoding="utf-8")
    # train.py:  Path(model_params.model_path) / f"compressed_{iteration}"
    written = "compressed_30000"
    ok = ('f"compressed_{iteration}"' in src) and fnmatch.fnmatch(written, STORE_GLOB)
    return ok, f"train.py writes compressed_<iter>; glob {STORE_GLOB!r} matches it"


def t12_verdict_separates_drift_from_a_real_model():
    """DECISIVE. The check that decides whether section 10 stands or falls.

    The continuous parameters under a straight-through quantizer with no
    commitment term are a latent, not a model: nothing keeps them near their
    centroid. If rendering the in-medium image from them scores far below the
    codebook state against ground truth, the J-hat gap measures drift and the
    instrument's premise fails. If they score alike, the continuous state is a
    real model and the gap is quantization damage, as the tool assumed.
    """
    cases = [
        ((10.0, 29.0), "DRIFT"),
        ((29.0 - DRIFT_MARGIN_DB + 0.1, 29.0), "MODEL"),
        ((29.0, 29.0), "MODEL"),
        ((29.0 - DRIFT_MARGIN_DB - 0.1, 29.0), "DRIFT"),
        ((33.0, 29.0), "INVERTED"),
    ]
    bad = [(a, want, continuous_state_verdict(*a)) for a, want in cases
           if continuous_state_verdict(*a) != want]
    return not bad, ("all five boundaries classified" if not bad else f"wrong: {bad}")


def t13_compose_is_the_baseline_image_formation():
    """I = clamp(J * attenuation + backscatter, 0, 1), exactly as render_uw.py."""
    j = np.array([[[0.5, 1.0], [0.2, 0.0]]] * 3)
    att = np.full_like(j, 0.5)
    bs = np.full_like(j, 0.3)
    got = compose_in_medium(j, att, bs)
    want = np.clip(j * 0.5 + 0.3, 0.0, 1.0)
    ok = got.shape == j.shape and np.allclose(got, want) and got.max() <= 1.0
    return ok, "J*att + bs, clamped to [0, 1]"


def main() -> int:
    print("=" * 68)
    print("CD-28  restored-image (J-hat) self-consistency")
    print("=" * 68)

    check("T1  index round trip is lossless", t1_index_round_trip_is_lossless)
    check("T2  reconstruction is a codebook lookup", t2_reconstruction_is_a_codebook_lookup)
    check("T3  vec_dim shapes match each attribute", t3_vec_dim_shapes_match_each_attribute)
    check("T4  unquantized runs are skipped", t4_unquantized_runs_are_skipped)
    check("T5  identical images report a capped PSNR",
          t5_identical_images_report_a_capped_psnr)
    check("T6  PSNR falls as error grows", t6_psnr_falls_as_error_grows)
    check("T7  reconstruction differs from continuous  <-- decisive",
          t7_reconstruction_actually_differs_from_continuous)
    check("T8  missing codebooks is skipped, not fatal",
          t8_missing_codebooks_is_skipped_not_fatal)
    check("T9  PSNR uses the pooled convention", t9_psnr_uses_the_pooled_convention)
    check("T10 group mapping covers every quantized attribute",
          t10_group_mapping_covers_every_quantized_attribute)
    check("T11 store glob matches what train.py writes  <-- decisive",
          t11_store_glob_matches_what_train_py_writes)
    check("T12 verdict separates drift from a real model  <-- decisive",
          t12_verdict_separates_drift_from_a_real_model)
    check("T13 compose is the baseline image formation",
          t13_compose_is_the_baseline_image_formation)

    failed = [n for n, ok, _ in _results if not ok]
    print("\n" + "=" * 68)
    if failed:
        print(f"J CONSISTENCY: FAILED ({len(failed)}/{len(_results)})")
        for n in failed:
            print(f"  - {n}")
        return 1
    print(f"J CONSISTENCY: PASSED ({len(_results)}/{len(_results)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
