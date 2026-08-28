"""Campaign driver: claim a run, execute it, record the outcome, repeat.

    python -m tools.run_queue \
        --output_root /content/drive/MyDrive/e3dgsuw \
        --data_root  /content/drive/MyDrive/SeathruNeRF_dataset \
        --max_minutes 200

Designed to be re-launched, not babysat.  A Colab session terminates long
before 145 GPU-hours of work is done, so the loop is written to make an
abrupt death harmless: state lives in the ledger on Drive, the process
heartbeats while a run is in flight, and a fresh session picks up wherever the
last one stopped.

**On resume: this driver restarts an interrupted run rather than resuming it,
and that is deliberate.**  `train.py` checkpoints the Gaussians and can restore
them, but the checkpoint does NOT contain the medium model, the learned
background, the codebooks, or the loop's own schedule flags.  Resuming from it
would silently reinitialise beta and B_inf -- producing a run that looks
complete, reports plausible numbers, and is not the experiment it claims to be.
Losing up to ~1.5 h of compute is much cheaper than one invisibly invalid cell.
Making resume correct is a real improvement, but it has to come with those
tensors in the checkpoint, not before.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

sys.path.append(str(Path(__file__).resolve().parent.parent))

from tools.run_ledger import M1_CELLS, M2_CELLS, Ledger  # noqa: E402

HEARTBEAT_SECONDS = 60


def gpu_name() -> str:
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
            capture_output=True, text=True, timeout=15,
        )
        return out.stdout.strip().splitlines()[0]
    except Exception:  # noqa: BLE001
        return "unknown"


def find_images_dir(scene_dir: Path) -> str:
    """Resolve the image directory, case-insensitively.

    Three scenes ship `images_wb`; IUI3-RedSea ships `Images_wb` with a capital
    I.  On a case-sensitive filesystem a hard-coded name silently fails for
    that one scene -- and a scene that fails to load is a scene missing from
    the results, not an error anyone sees.
    """
    for child in sorted(scene_dir.iterdir()):
        if child.is_dir() and child.name.lower() == "images_wb":
            return child.name
    raise FileNotFoundError(f"no images_wb directory under {scene_dir}")


def build_command(
    run: dict, ledger: Ledger, data_root: Path, impl_root: Path, extra: list[str]
) -> tuple[list[str], Path]:
    scene_dir = data_root / run["scene"]
    if not scene_dir.exists():
        raise FileNotFoundError(f"scene not found: {scene_dir}")

    out_dir = ledger.root / "runs" / run["cell"] / run["scene"] / f"s{run['seed']}"
    cmd = [
        sys.executable, str(impl_root / "train.py"),
        "-s", str(scene_dir),
        "--images", find_images_dir(scene_dir),
        "--model_path", str(out_dir),
        "--cell", run["cell"],
        "--seed", str(run["seed"]),
    ]
    if run["cell"] in M1_CELLS:
        cmd += ["--pcd_path", str(ledger.dense_pcd_path(run["scene"]))]
    if run["cell"] in M2_CELLS:
        cmd += ["--n_bud", str(ledger.data["n_bud"])]
    cmd += extra
    return cmd, out_dir


def execute(cmd: list[str], log_path: Path, ledger: Ledger, run_id: str) -> int:
    """Run to completion, heartbeating so a death is detectable as stale."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as log:
        log.write(f"\n{'=' * 70}\n{datetime.now(timezone.utc).isoformat()}\n")
        log.write(" ".join(cmd) + "\n" + "=" * 70 + "\n")
        log.flush()

        proc = subprocess.Popen(
            cmd, stdout=log, stderr=subprocess.STDOUT, text=True
        )
        last = time.time()
        while proc.poll() is None:
            time.sleep(5)
            if time.time() - last >= HEARTBEAT_SECONDS:
                try:
                    ledger.heartbeat(run_id)
                except Exception:  # noqa: BLE001 - never kill a run over a heartbeat
                    pass
                last = time.time()
        return proc.returncode


def tail(path: Path, n: int = 25) -> str:
    try:
        return "".join(path.read_text(encoding="utf-8", errors="replace")
                       .splitlines(keepends=True)[-n:])
    except Exception:  # noqa: BLE001
        return "(no log)"


def main() -> int:
    ap = argparse.ArgumentParser(description="run the campaign queue")
    ap.add_argument("--output_root", required=True)
    ap.add_argument("--data_root", required=True)
    ap.add_argument("--max_minutes", type=int, default=0,
                    help="stop claiming new runs after this long (0 = no limit). "
                         "Set it below the session limit so the loop exits "
                         "cleanly instead of being killed mid-run.")
    ap.add_argument("--max_runs", type=int, default=0)
    ap.add_argument("--stale_minutes", type=int, default=45)
    ap.add_argument("--max_attempts", type=int, default=3)
    ap.add_argument("--allow_any_gpu", action="store_true")
    ap.add_argument("--dry_run", action="store_true",
                    help="print the commands that would run, claim nothing")
    ap.add_argument("extra", nargs="*",
                    help="extra args forwarded verbatim to train.py")
    args = ap.parse_args()

    impl_root = Path(__file__).resolve().parent.parent
    data_root = Path(args.data_root)
    ledger = Ledger(args.output_root)
    if not ledger.path.exists():
        raise SystemExit(
            f"no ledger at {ledger.path}. Create one first:\n"
            f"  python -m tools.run_ledger init --output_root {args.output_root}"
        )

    gpu = gpu_name()
    print(f"[queue] gpu: {gpu}")
    if "A100" not in gpu and not args.allow_any_gpu and not args.dry_run:
        raise SystemExit(
            f"\nRefusing to start: GPU is {gpu!r}, not an A100.\n"
            f"Every cell must run on the same device or the between-cell\n"
            f"contrasts -- which is what every conclusion rests on -- are not\n"
            f"comparable. Restart the session for an A100, or pass\n"
            f"--allow_any_gpu and record that these runs are not comparable\n"
            f"with the rest of the campaign.\n"
        )

    reclaimed = ledger.reap_stale(args.stale_minutes)
    if reclaimed:
        print(f"[queue] reclaimed {reclaimed} stale run(s) from a dead session")

    if args.dry_run:
        # Side-effect free: previewing must not consume attempts or flip
        # statuses on runs that never actually ran.
        upcoming = ledger.preview(limit=args.max_runs or 10,
                                  max_attempts=args.max_attempts)
        if not upcoming:
            print("[dry-run] nothing eligible; check the ledger status below")
        for run in upcoming:
            try:
                cmd, _ = build_command(run, ledger, data_root, impl_root, args.extra)
                print(f"\n[dry-run] {run['id']}\n  " + " ".join(cmd))
            except Exception as exc:  # noqa: BLE001
                print(f"\n[dry-run] {run['id']}: cannot build command: {exc}")
        print("\n" + ledger.summary())
        return 0

    deadline = time.time() + args.max_minutes * 60 if args.max_minutes else None
    completed = 0

    while True:
        if deadline and time.time() > deadline:
            print("[queue] time budget reached; stopping cleanly")
            break
        if args.max_runs and completed >= args.max_runs:
            print("[queue] run budget reached")
            break

        run = ledger.claim(max_attempts=args.max_attempts)
        for skip in getattr(ledger, "last_skipped", []):
            # Reordering the campaign is acceptable; doing it quietly is not.
            print(f"[queue] NOTE: {skip}")
        if run is None:
            print("[queue] nothing eligible to claim")
            break

        try:
            cmd, out_dir = build_command(run, ledger, data_root, impl_root, args.extra)
        except Exception as exc:  # noqa: BLE001
            print(f"[queue] {run['id']}: cannot build command: {exc}")
            ledger.finish(run["id"], ok=False, error=str(exc))
            continue

        print(f"\n[queue] === {run['id']} (attempt {run['attempts']}) ===")
        print("  " + " ".join(cmd))
        started = time.time()
        log_path = out_dir / "train.log"
        code = execute(cmd, log_path, ledger, run["id"])
        elapsed = time.time() - started

        if code == 0:
            ledger.finish(run["id"], ok=True, gpu=gpu, output_dir=str(out_dir),
                          wall_seconds=round(elapsed, 1))
            completed += 1
            print(f"[queue] done in {elapsed / 60:.1f} min -> {out_dir}")
        else:
            err = f"exit {code}"
            ledger.finish(run["id"], ok=False, gpu=gpu, output_dir=str(out_dir),
                          wall_seconds=round(elapsed, 1), error=err)
            print(f"[queue] FAILED ({err}) after {elapsed / 60:.1f} min")
            print(tail(log_path))

    print("\n" + ledger.summary())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
