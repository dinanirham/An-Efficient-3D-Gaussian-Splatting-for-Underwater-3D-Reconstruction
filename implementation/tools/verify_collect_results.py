"""Verification for collect_results' provenance columns.

    python tools/verify_collect_results.py

Both campaigns' results tables carried an empty `git_commit` in every row
while every run directory held a `run_config.json` with the sha in it. The
collector read `cfg["git"]["commit"]`; the manifest writer in
`utils/preflight.py` writes `cfg["git_sha"]`. The reader encoded a guess about
the writer, and the guess was silent because a missing key is an empty string.

The rule these tests enforce: the fixture is built from what the writer
writes, never from what the reader expects. T1 reads the writer's source for
its key names; T2 collects a run directory whose manifest carries exactly
those keys.
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from tools.collect_results import collect_runs, provenance  # noqa: E402

_results: list[tuple[str, bool, str]] = []


def check(name: str, fn) -> None:
    try:
        ok, msg = fn()
    except Exception as exc:  # noqa: BLE001
        ok, msg = False, f"{type(exc).__name__}: {exc}"
    _results.append((name, ok, msg))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {msg}")


# What preflight.write_manifest writes, key for key. T1 checks this against
# the writer's source so that the fixture cannot drift from it unnoticed.
WRITER_KEYS = ("git_sha", "gpu", "resolved_args")


def _manifest(sha: str) -> dict:
    return {
        "written_at": "2026-09-15T13:54:53+00:00",
        "cell": "A3",
        "cell_values": {"m3_quantize": True},
        "git_sha": sha,
        "gpu": {"available": True, "name": "NVIDIA A100-SXM4-40GB"},
        "python": "3.13.15",
        "platform": "Linux",
        "torch": "2.11.0+cu128",
        "torch_cuda": "12.8",
        "argv": ["train.py"],
        "resolved_args": {"m1_dense_init": False, "m2_simplify": False,
                          "m3_quantize": True, "n_bud": 200000,
                          "kmeans_k": 4096, "seathru_from_iter": 10000},
    }


def t1_fixture_keys_are_the_writers_keys():
    """DECISIVE. The manifest fixture uses the keys write_manifest writes."""
    src = (Path(__file__).resolve().parent.parent / "utils" / "preflight.py"
           ).read_text(encoding="utf-8")
    missing = [k for k in WRITER_KEYS if f'"{k}":' not in src]
    return not missing, ("write_manifest writes " + ", ".join(WRITER_KEYS)
                         if not missing else f"writer no longer writes {missing}")


def t2_provenance_reads_sha_gpu_and_args():
    p = provenance(_manifest("3c165ae1ccad7f6c08dd875677de56e048055dfd"))
    ok = (p["git_commit"] == "3c165ae1c" and p["gpu"] == "NVIDIA A100-SXM4-40GB"
          and p["args"]["n_bud"] == 200000)
    return ok, f"git_commit={p['git_commit']!r} gpu={p['gpu']!r}"


def t3_dirty_tree_is_recorded_not_dropped():
    """A '-dirty' sha is the most important provenance fact a run can carry."""
    p = provenance(_manifest("3c165ae1ccad7f6c08dd875677de56e048055dfd-dirty"))
    return p["git_commit"] == "3c165ae1c-dirty", f"git_commit={p['git_commit']!r}"


def t4_collected_row_carries_the_commit():
    """DECISIVE. End to end: a run directory in the campaign layout yields a
    populated git_commit column, which neither campaign's table had."""
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp) / "runs" / "A3" / "Curasao" / "s0"
        d.mkdir(parents=True)
        (d / "run_config.json").write_text(json.dumps(_manifest("abcdef0123456789")),
                                           encoding="utf-8")
        (d / "eval_metrics.json").write_text(json.dumps({
            "Test": {"psnr_pooled": 30.0, "lpips": 0.18, "n_images": 3},
            "cost": {"n_primitives_final": 100},
        }), encoding="utf-8")
        rows = collect_runs(Path(tmp))   # the campaign root; runs/ is inside
        ok = len(rows) == 1 and rows[0].get("git_commit") == "abcdef012" \
            and rows[0].get("gpu") == "NVIDIA A100-SXM4-40GB" \
            and rows[0].get("n_bud") == 200000
        return ok, (f"row: git_commit={rows[0].get('git_commit')!r} "
                    f"n_bud={rows[0].get('n_bud')!r}" if rows else "no rows")


def main() -> int:
    print("=" * 68)
    print("collect_results  provenance columns")
    print("=" * 68)
    check("T1 fixture keys are the writer's keys  <-- decisive",
          t1_fixture_keys_are_the_writers_keys)
    check("T2 provenance reads sha, gpu and resolved args",
          t2_provenance_reads_sha_gpu_and_args)
    check("T3 a dirty tree is recorded, not dropped",
          t3_dirty_tree_is_recorded_not_dropped)
    check("T4 collected row carries the commit  <-- decisive",
          t4_collected_row_carries_the_commit)
    failed = [n for n, ok, _ in _results if not ok]
    print("\n" + "=" * 68)
    if failed:
        print(f"COLLECT RESULTS: FAILED ({len(failed)}/{len(_results)})")
        return 1
    print(f"COLLECT RESULTS: PASSED ({len(_results)}/{len(_results)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
