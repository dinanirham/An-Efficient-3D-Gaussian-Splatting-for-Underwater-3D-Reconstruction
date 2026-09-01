"""Fatal startup checks and the per-run manifest (CD-1, M2).

Every failure mode this module guards against is **silent** in the upstream
code: nothing raises, nothing warns, and the run produces plausible-looking
numbers that answer a different question from the one asked.  Concretely:

  * `--eval` defaults to False, so the test set is empty and training silently
    uses every frame, inflating the reported metrics.
  * `seathru_from_iter` defaults to 9_000_000 -- past the end of a 30k run --
    so the medium model never activates and the run is plain 3DGS with an
    underwater dataset.
  * A mechanism flag can be set while the code path it enables never fires.
  * Colab does not guarantee which GPU is allocated.  Cells that land on
    different devices cannot be compared, which is fatal to a factorial design
    whose conclusions are all between-cell contrasts.

Checks are fatal by construction: a run that cannot answer its question should
not consume an hour of A100 time first.
"""

from __future__ import annotations

import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import torch


class PreflightError(SystemExit):
    """Raised (as SystemExit) when a run must not proceed."""

    def __init__(self, checks: list[str]) -> None:
        body = "\n".join(f"  - {c}" for c in checks)
        super().__init__(
            "\n"
            "================ PREFLIGHT FAILED ================\n"
            f"{body}\n"
            "==================================================\n"
            "Refusing to start: this run could not answer the question it was\n"
            "configured to ask. Fix the above and re-launch.\n"
        )


# ---------------------------------------------------------------------------
# environment probes
# ---------------------------------------------------------------------------


def git_sha(repo_root: Path) -> str:
    try:
        out = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        sha = out.stdout.strip()
        dirty = subprocess.run(
            ["git", "-C", str(repo_root), "status", "--porcelain"],
            capture_output=True,
            text=True,
            timeout=10,
        ).stdout.strip()
        return f"{sha}{'-dirty' if dirty else ''}" if sha else "unknown"
    except Exception:  # noqa: BLE001 - a manifest must never break a run
        return "unknown"


def gpu_info() -> dict[str, Any]:
    if not torch.cuda.is_available():
        return {"available": False}
    cap = torch.cuda.get_device_capability()
    info: dict[str, Any] = {
        "available": True,
        "name": torch.cuda.get_device_name(),
        "capability": f"sm_{cap[0]}{cap[1]}",
        "count": torch.cuda.device_count(),
        "total_memory_gb": round(
            torch.cuda.get_device_properties(0).total_memory / 1024**3, 2
        ),
    }
    try:
        info["nvidia_smi"] = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,driver_version,memory.total",
             "--format=csv,noheader"],
            capture_output=True, text=True, timeout=10,
        ).stdout.strip()
    except Exception:  # noqa: BLE001
        info["nvidia_smi"] = "unavailable"
    return info


# ---------------------------------------------------------------------------
# phase 1: before the scene is loaded
# ---------------------------------------------------------------------------


def preflight_args(args: Any, opt: Any, dataset: Any) -> None:
    """Checks that depend only on the resolved configuration."""
    fail: list[str] = []
    warn: list[str] = []

    # -- GPU identity -------------------------------------------------------
    gpu = gpu_info()
    if not gpu["available"]:
        fail.append("no CUDA device visible")
    elif "A100" not in gpu["name"] and not getattr(opt, "allow_any_gpu", False):
        fail.append(
            f"GPU is {gpu['name']!r}, not an A100. Every cell of the matrix must "
            f"run on the same device or the between-cell contrasts are not "
            f"comparable. Pass --allow_any_gpu to override, and record that the "
            f"run is not comparable with the rest."
        )

    # -- the medium model must actually activate ----------------------------
    if not getattr(opt, "do_seathru", False):
        fail.append(
            "do_seathru is False: the medium model never activates, so this "
            "would be a study of plain 3DGS on underwater images, not of "
            "SeaSplat. Use --cell, or pass --do_seathru."
        )
    if opt.seathru_from_iter >= opt.iterations:
        fail.append(
            f"seathru_from_iter={opt.seathru_from_iter} >= iterations="
            f"{opt.iterations}: the medium model would never switch on. "
            f"(The upstream default is 9_000_000 -- this is that trap.)"
        )

    # -- ordering the medium-aware pruning property depends on --------------
    if opt.densify_until_iter <= opt.seathru_from_iter:
        fail.append(
            f"densify_until_iter={opt.densify_until_iter} <= seathru_from_iter="
            f"{opt.seathru_from_iter}. Opacity-driven pruning would then finish "
            f"before L_op ever runs, removing the coupling between the opacity "
            f"prior and primitive removal. Upstream satisfies this ordering only "
            f"incidentally; here it is required."
        )

    # -- evaluation ---------------------------------------------------------
    if not getattr(dataset, "eval", False):
        fail.append(
            "eval is False: the test set will be empty and training will use "
            "every frame, silently inflating the reported metrics. Pass --eval."
        )

    # -- mechanism flags must correspond to a real cell ---------------------
    flags = (
        bool(getattr(opt, "m1_dense_init", False)),
        bool(getattr(opt, "m2_simplify", False)),
        bool(getattr(opt, "m3_quantize", False)),
    )
    known = {
        (False, False, False): "A0", (True, False, False): "A1",
        (False, True, False): "A2", (False, False, True): "A3",
        (True, True, False): "A4", (True, False, True): "A5",
        (False, True, True): "A6", (True, True, True): "A7",
    }
    cell = known[flags]
    declared = getattr(args, "cell", None)
    if declared is not None and declared.upper() != cell:
        fail.append(
            f"--cell {declared} was requested but the resolved mechanism flags "
            f"describe {cell} (m1={flags[0]}, m2={flags[1]}, m3={flags[2]}). "
            f"A command-line flag has overridden the cell file; that is allowed, "
            f"but it means the run is not the cell it claims to be."
        )

    # -- the scene must already be undistorted -------------------------------
    # All four SeaThru-NeRF scenes ship as COLMAP OPENCV with real distortion,
    # and the scene reader accepts only PINHOLE/SIMPLE_PINHOLE.  Caught here so
    # the message names the fix, rather than surfacing as a bare assert several
    # frames deep in the loader after the manifest has already been written.
    source_path = getattr(dataset, "source_path", "") or ""
    if source_path:
        try:
            from source.undistort import find_sparse_dir, read_camera_model
            info = read_camera_model(find_sparse_dir(source_path) / "cameras.bin")
            if info["needs_undistortion"]:
                fail.append(
                    f"scene uses the {info['model']} camera model; the reader "
                    f"supports only PINHOLE/SIMPLE_PINHOLE, so this run would "
                    f"fail at scene load. Preprocess it first:\n"
                    f"      python -m source.undistort --source {source_path} "
                    f"--output <undistorted>/<scene>"
                )
        except FileNotFoundError as exc:
            fail.append(f"no COLMAP reconstruction found: {exc}")
        except Exception as exc:  # noqa: BLE001
            warn.append(f"could not verify the camera model ({exc})")

    # -- M1 cannot run without its cloud ------------------------------------
    if flags[0]:
        pcd = getattr(dataset, "pcd_path", "") or ""
        if not pcd:
            fail.append(
                "m1_dense_init is set but pcd_path is empty. The run would fall "
                "back to COLMAP's sparse points *with densification disabled* -- "
                "a configuration that is neither A0 nor A1, and which no metric "
                "would flag. Produce the cloud with source/roma_init.py and pass "
                "--pcd_path."
            )
        elif not Path(pcd).exists():
            fail.append(f"m1_dense_init cloud does not exist: {pcd}")

    # -- M2 needs a budget that can actually bind ---------------------------
    if flags[1]:
        n_bud = getattr(opt, "n_bud", -1)
        if n_bud is None or n_bud <= 0:
            fail.append(
                "m2_simplify is set but n_bud is unset. The budget is an "
                "explicit primitive count, and it must be derived from A0's "
                "converged count so that it binds in every cell -- a budget "
                "that does not bind makes A4 equivalent to A1 and A7 to A5, "
                "and a null interaction measured in that state is a "
                "configuration artifact rather than a finding. Run A0 first "
                "and read its final count from diagnostics.csv."
            )
        if getattr(opt, "imp_metric", None) not in ("indoor", "outdoor"):
            fail.append(
                f"imp_metric must be 'indoor' or 'outdoor', got "
                f"{getattr(opt, 'imp_metric', None)!r}. Neither was designed "
                f"for a scattering medium; the choice must be deliberate."
            )
        if not (opt.simp_iteration1 < opt.simp_iteration2 <= opt.iterations):
            fail.append(
                f"simplification schedule out of order: simp_iteration1="
                f"{opt.simp_iteration1}, simp_iteration2={opt.simp_iteration2}, "
                f"iterations={opt.iterations}"
            )
        if opt.simp_iteration1 <= opt.seathru_from_iter:
            fail.append(
                f"simp_iteration1={opt.simp_iteration1} <= seathru_from_iter="
                f"{opt.seathru_from_iter}: the medium model would not yet be "
                f"active at the first simplification event, so the CD-6 "
                f"re-identification burst could not run and the depth rescale "
                f"it exists to absorb would go uncorrected."
            )
        if getattr(opt, "m2_rewarm_steps", 0) <= 0:
            # Not fatal: running without the burst is exactly the ablation that
            # tests whether CD-6 is necessary.  But it must be visible in the
            # log, because the resulting damage shows up as "pruning cost
            # quality" -- indistinguishable, without the diagnostics, from the
            # effect being measured.
            warn.append(
                "m2_rewarm_steps=0: the medium model will NOT be re-identified "
                "after the primitive population changes. Valid as a deliberate "
                "ablation of CD-6; invalid as a default. Confirm this is "
                "intended, and read diagnostics.csv's beta columns across the "
                "simplification boundary when interpreting the result."
            )

    # -- M3 schedule and codebook -------------------------------------------
    if flags[2]:
        if opt.kmeans_st_iter >= opt.iterations:
            fail.append(
                f"kmeans_st_iter={opt.kmeans_st_iter} >= iterations="
                f"{opt.iterations}: quantization would never start. (This is "
                f"the reference implementation's own CLI default, which "
                f"silently disables the method.)"
            )
        if flags[1] and opt.kmeans_st_iter <= opt.simp_iteration2:
            fail.append(
                f"kmeans_st_iter={opt.kmeans_st_iter} <= simp_iteration2="
                f"{opt.simp_iteration2}. The codebook would be fitted to a "
                f"population that is about to be pruned, and quantization-aware "
                f"training would spend its gradient budget adapting parameters "
                f"that are then discarded (CD-10)."
            )
        if opt.kmeans_k < 2:
            fail.append(f"kmeans_k must be >= 2, got {opt.kmeans_k}")
        elif opt.kmeans_k < 4096:
            warn.append(
                f"kmeans_k={opt.kmeans_k} is below 4096. At sh_degree=0 the "
                f"grouping machinery is inert, so k is the only quality dial "
                f"quantization has; small values here were a known defect in a "
                f"previous attempt."
            )

    # -- seeding ------------------------------------------------------------
    seed = getattr(args, "seed", -1)
    if seed is None or seed < 0:
        fail.append(
            "seed is unset (default -1 draws from OS entropy). Every cell needs "
            "an explicit seed so that dispersion across seeds is measurable "
            "rather than incidental. Pass --seed."
        )

    if fail:
        raise PreflightError(fail)

    for w in warn:
        print(f"[preflight] WARNING: {w}")
    print(f"[preflight] ok  cell={cell}  gpu={gpu.get('name')}  seed={seed}")


# ---------------------------------------------------------------------------
# phase 2: after the scene is loaded
# ---------------------------------------------------------------------------


def preflight_scene(scene: Any) -> dict[str, int]:
    """Checks that need the loaded dataset. Returns the split sizes."""
    n_train = len(scene.getTrainCameras())
    n_test = len(scene.getTestCameras())

    if n_test == 0:
        raise PreflightError([
            "the test set is empty after loading the scene. --eval was set, so "
            "this is a dataset or split problem rather than a flag problem: "
            "check that the scene has more than `llffhold` (8) frames and that "
            "the image directory resolved correctly (note IUI3-RedSea ships as "
            "'Images_wb', capital I, which fails on a case-sensitive filesystem)."
        ])

    print(f"[preflight] split ok  train={n_train}  test={n_test}")
    return {"train_cameras": n_train, "test_cameras": n_test}


# ---------------------------------------------------------------------------
# manifest
# ---------------------------------------------------------------------------


def write_manifest(
    model_path: str | Path,
    args: Any,
    cell_name: str | None,
    cell_values: dict,
    repo_root: Path,
    extra: dict[str, Any] | None = None,
) -> Path:
    """Write `run_config.json`: everything needed to reproduce or attribute a run.

    Written at startup rather than at the end so that a run killed mid-flight
    (routine on Colab) still records what it was.
    """
    model_path = Path(model_path)
    model_path.mkdir(parents=True, exist_ok=True)
    target = model_path / "run_config.json"

    manifest: dict[str, Any] = {
        "written_at": datetime.now(timezone.utc).isoformat(),
        "cell": cell_name,
        "cell_values": cell_values,
        "git_sha": git_sha(repo_root),
        "gpu": gpu_info(),
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "torch": torch.__version__,
        "torch_cuda": torch.version.cuda,
        "argv": sys.argv,
        "resolved_args": {
            k: (str(v) if not isinstance(v, (int, float, bool, str, type(None))) else v)
            for k, v in sorted(vars(args).items())
        },
    }
    if extra:
        manifest.update(extra)

    with open(target, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2, sort_keys=False)
    print(f"[manifest] {target}")
    return target
