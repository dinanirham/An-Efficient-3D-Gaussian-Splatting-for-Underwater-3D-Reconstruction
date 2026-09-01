"""The run ledger: durable state for a 96-run campaign on preemptible sessions.

    python -m tools.run_ledger init   --output_root /content/drive/MyDrive/e3dgsuw
    python -m tools.run_ledger status --output_root ...
    python -m tools.run_ledger set-budget 812345 --output_root ...

8 cells x 4 scenes x 3 seeds is roughly 145 GPU-hours against Colab sessions
that terminate well before that, so the campaign's state cannot live in a
process.  It lives here, on Drive, and any fresh session reconstructs what to
do next by reading it.

Three properties the campaign depends on:

**Stage ordering.**  Runs are claimed from the lowest stage that still has work.
S1 (A0) must finish before anything else, because the primitive budget is
derived from A0's converged count and is not knowable before it.

**Prerequisites.**  An m2 cell without a budget, or an m1 cell without its dense
cloud, is not merely misconfigured -- it silently becomes a different
experiment.  Such runs are marked `blocked` rather than attempted.

**Stale reclamation.**  A session killed mid-run leaves its row `running`
forever.  Rows whose heartbeat has gone quiet are returned to `pending`, with
the attempt counted so a genuinely broken configuration cannot loop.
"""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

LEDGER_NAME = "run_ledger.json"

# Staging from EXECUTION-PROMPT §7. Each stage yields a usable result on its
# own, so a campaign that runs out of compute still produces something.
STAGES: dict[str, list[str]] = {
    "S1": ["A0"],                # unblocks the budget and environment validity
    "S2": ["A2"],                # the central hypothesis (H4)
    "S3": ["A1", "A3"],          # remaining main effects
    "S4": ["A4", "A5", "A6"],    # the three two-way interactions
    "S5": ["A7"],                # three-way term, effect-from-above contrasts
}
CELL_STAGE = {c: s for s, cells in STAGES.items() for c in cells}
STAGE_ORDER = list(STAGES)

M1_CELLS = {"A1", "A4", "A5", "A7"}
M2_CELLS = {"A2", "A4", "A6", "A7"}

# Attempts before a run stops being claimed, so a broken configuration cannot
# loop for a whole session. One source of truth: claim(), preview() and the
# summary all have to agree on it, or the queue silently skips runs the status
# output still calls pending.
MAX_ATTEMPTS = 3


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse(ts: Optional[str]) -> Optional[datetime]:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts)
    except ValueError:
        return None


class Ledger:
    def __init__(self, output_root: str | Path) -> None:
        self.root = Path(output_root)
        self.path = self.root / LEDGER_NAME
        self.data: dict[str, Any] = {}
        if self.path.exists():
            self.load()

    # -- persistence -------------------------------------------------------

    def load(self) -> None:
        with open(self.path, encoding="utf-8") as fh:
            self.data = json.load(fh)

    def save(self) -> None:
        """Atomic replace: a session killed mid-write must not corrupt state."""
        self.root.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=str(self.root), suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(self.data, fh, indent=2)
            os.replace(tmp, self.path)
        except Exception:
            Path(tmp).unlink(missing_ok=True)
            raise

    # -- construction ------------------------------------------------------

    def init(
        self,
        scenes: list[str],
        seeds: list[int],
        cells: Optional[list[str]] = None,
        force: bool = False,
    ) -> None:
        if self.path.exists() and not force:
            raise SystemExit(
                f"{self.path} already exists. Refusing to overwrite a campaign "
                f"in progress -- pass --force if that is really what you want."
            )
        cells = cells or [c for s in STAGE_ORDER for c in STAGES[s]]
        runs = []
        for cell in cells:
            for scene in scenes:
                for seed in seeds:
                    runs.append({
                        "id": f"{cell}/{scene}/s{seed}",
                        "cell": cell,
                        "scene": scene,
                        "seed": seed,
                        "stage": CELL_STAGE[cell],
                        "status": "pending",
                        "attempts": 0,
                        "started_at": None,
                        "heartbeat": None,
                        "finished_at": None,
                        "wall_seconds": None,
                        "gpu": None,
                        "output_dir": None,
                        "error": None,
                    })
        self.data = {
            "created": _utc(),
            "scenes": scenes,
            "seeds": seeds,
            "n_bud": None,
            "runs": runs,
        }
        self.save()

    # -- queries -----------------------------------------------------------

    @property
    def runs(self) -> list[dict]:
        return self.data.get("runs", [])

    def by_id(self, run_id: str) -> dict:
        for r in self.runs:
            if r["id"] == run_id:
                return r
        raise KeyError(run_id)

    def dense_pcd_path(self, scene: str) -> Path:
        return self.root / "dense" / f"{scene}.ply"

    def blockers(self, run: dict) -> list[str]:
        """Why this run must not start yet. Empty means it is ready."""
        reasons = []
        if run["cell"] in M2_CELLS and not self.data.get("n_bud"):
            reasons.append(
                "no primitive budget recorded; run S1 (A0) first, then "
                "`run_ledger set-budget <count>`"
            )
        if run["cell"] in M1_CELLS and not self.dense_pcd_path(run["scene"]).exists():
            reasons.append(
                f"dense cloud missing: {self.dense_pcd_path(run['scene'])} "
                f"(produce it with source/roma_init.py)"
            )
        return reasons

    def reap_stale(self, stale_minutes: int = 45) -> int:
        """Return runs whose session died back to the queue."""
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=stale_minutes)
        n = 0
        for r in self.runs:
            if r["status"] != "running":
                continue
            hb = _parse(r.get("heartbeat"))
            if hb is None or hb < cutoff:
                r["status"] = "pending"
                r["error"] = (
                    f"reclaimed: no heartbeat since {r.get('heartbeat')} "
                    f"(session presumably terminated)"
                )
                n += 1
        if n:
            self.save()
        return n

    def exhausted(self, max_attempts: int = MAX_ATTEMPTS) -> list[dict]:
        """Runs that are out of attempts and will never be claimed again."""
        return [
            r for r in self.runs
            if r["status"] == "pending" and r["attempts"] >= max_attempts
        ]

    def reset(
        self,
        cells: Optional[list[str]] = None,
        all_failed: bool = False,
        max_attempts: int = MAX_ATTEMPTS,
    ) -> int:
        """Return exhausted runs to the queue by clearing their attempts.

        A run that hits the cap for an *environmental* reason -- a wrong path,
        a missing package, a harness bug -- stays unclaimable forever once the
        cause is fixed, because nothing clears `attempts`. The queue then
        reports "nothing eligible to claim" while the status output still
        calls those runs pending, which reads as a campaign that is idle
        rather than one that is stuck.

        Without this the only remedies are re-initialising the ledger, which
        discards completed runs, or editing the JSON by hand.
        """
        targets = self.runs if all_failed else self.exhausted(max_attempts)
        n = 0
        for r in targets:
            # Never touch finished or in-flight work, and leave `blocked`
            # alone: that state is about an unmet prerequisite, not a failed
            # attempt, and flipping it to pending would claim a run whose
            # budget or dense cloud still does not exist.
            if r["status"] not in ("pending", "failed"):
                continue
            if cells and r["cell"] not in cells:
                continue
            if r["attempts"] == 0 and not r["error"]:
                continue
            r["attempts"] = 0
            r["error"] = ""
            r["status"] = "pending"
            n += 1
        if n:
            self.save()
        return n

    def claim(self, max_attempts: int = MAX_ATTEMPTS) -> Optional[dict]:
        """Take the next eligible run, honouring stage order. None if nothing.

        Ordering policy, which is deliberately not "never descend":

        * A stage with work that *could* run holds the queue.  This is the
          property that matters -- S1 must complete before anything else,
          because the primitive budget comes from it.
        * A stage whose remaining work is entirely **blocked** on a missing
          prerequisite is skipped, so a fully-blocked S2 does not idle an A100
          that could be running S3's A3 cells.  Skips are recorded in
          `last_skipped` and reported by the driver, because a silent reorder
          is exactly the kind of surprise that makes a results table mean
          something other than it appears to.

        `blocked` is transient: it is recomputed on every claim, so generating
        a missing dense cloud or setting the budget releases those runs without
        any further bookkeeping.
        """
        self.last_skipped: list[str] = []

        # Prerequisites may have been satisfied since the last pass.
        for r in self.runs:
            if r["status"] == "blocked":
                r["status"] = "pending"
                r["error"] = None

        for stage in STAGE_ORDER:
            in_stage = [r for r in self.runs if r["stage"] == stage]
            if not in_stage:
                continue

            runnable: list[dict] = []
            blocked: list[dict] = []
            for r in in_stage:
                if r["status"] != "pending" or r["attempts"] >= max_attempts:
                    continue
                reasons = self.blockers(r)
                if reasons:
                    r["status"] = "blocked"
                    r["error"] = "; ".join(reasons)
                    blocked.append(r)
                else:
                    runnable.append(r)

            if runnable:
                run = runnable[0]
                run["status"] = "running"
                run["attempts"] += 1
                run["started_at"] = _utc()
                run["heartbeat"] = _utc()
                run["error"] = None
                self.save()
                return run

            # Something is already in flight for this stage: wait for it rather
            # than descending, or the ordering guarantee is worthless.
            if any(r["status"] == "running" for r in in_stage):
                self.save()
                return None

            if blocked:
                self.last_skipped.append(
                    f"{stage} skipped: {len(blocked)} run(s) blocked -- "
                    f"{blocked[0]['error']}"
                )
            # otherwise the stage is complete; fall through.

        self.save()
        return None

    def preview(self, limit: int = 10,
                max_attempts: int = MAX_ATTEMPTS) -> list[dict]:
        """What `claim` would hand out next, WITHOUT mutating anything.

        A dry run that consumed attempts or flipped statuses would be worse
        than useless -- it would quietly burn the retry budget of runs that
        never actually ran.
        """
        out: list[dict] = []
        taken: set[str] = set()
        for stage in STAGE_ORDER:
            in_stage = [r for r in self.runs if r["stage"] == stage]
            if not in_stage:
                continue
            for r in in_stage:
                if r["status"] not in ("pending", "blocked"):
                    continue
                if r["attempts"] >= max_attempts or r["id"] in taken:
                    continue
                if self.blockers(r):
                    continue
                out.append(r)
                taken.add(r["id"])
                if len(out) >= limit:
                    return out
            if any(r["status"] == "running" for r in in_stage):
                return out
        return out

    def heartbeat(self, run_id: str) -> None:
        self.load()
        self.by_id(run_id)["heartbeat"] = _utc()
        self.save()

    def finish(
        self,
        run_id: str,
        ok: bool,
        gpu: Optional[str] = None,
        output_dir: Optional[str] = None,
        wall_seconds: Optional[float] = None,
        error: Optional[str] = None,
    ) -> None:
        self.load()
        run = self.by_id(run_id)
        run["status"] = "done" if ok else "failed"
        run["finished_at"] = _utc()
        run["heartbeat"] = _utc()
        run["gpu"] = gpu
        run["output_dir"] = output_dir
        run["wall_seconds"] = wall_seconds
        run["error"] = error
        # A failure goes back in the queue unless it has exhausted its attempts;
        # `claim` enforces the cap.
        if not ok:
            run["status"] = "pending"
        self.save()

    def set_budget(self, n_bud: int) -> None:
        self.load()
        self.data["n_bud"] = int(n_bud)
        # Anything blocked purely on the budget becomes eligible again.
        for r in self.runs:
            if r["status"] == "blocked":
                r["status"] = "pending"
                r["error"] = None
        self.save()

    def summary(self) -> str:
        counts: dict[str, int] = {}
        per_stage: dict[str, dict[str, int]] = {}
        for r in self.runs:
            counts[r["status"]] = counts.get(r["status"], 0) + 1
            st = per_stage.setdefault(r["stage"], {})
            st[r["status"]] = st.get(r["status"], 0) + 1

        lines = [
            f"ledger : {self.path}",
            f"budget : {self.data.get('n_bud') or 'NOT SET (blocks all m2 cells)'}",
            f"total  : {len(self.runs)} runs  " + "  ".join(
                f"{k}={v}" for k, v in sorted(counts.items())
            ),
            "",
        ]
        for stage in STAGE_ORDER:
            st = per_stage.get(stage)
            if not st:
                continue
            cells = ",".join(STAGES[stage])
            lines.append(
                f"  {stage} ({cells:<12}) " + "  ".join(
                    f"{k}={v}" for k, v in sorted(st.items())
                )
            )
        # An exhausted run still reads as "pending" in the counts above, which
        # is how a stuck campaign comes to look like an idle one: the queue
        # says "nothing eligible to claim" while the stage line says pending=12.
        spent = self.exhausted()
        if spent:
            lines += [
                "",
                f"  !! {len(spent)} run(s) OUT OF ATTEMPTS -- counted as pending "
                f"above, but the queue will not claim them.",
                "     Fix the cause, then: run_ledger reset --output_root <root>",
            ]

        problems = [r for r in self.runs if r["status"] == "blocked" or r["error"]]
        if problems:
            lines += ["", "  attention:"]
            spent_ids = {r["id"] for r in spent}
            for r in problems[:10]:
                mark = "spent" if r["id"] in spent_ids else r["status"]
                lines.append(f"    {r['id']:<24} {mark:<8} {r['error']}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------


def main() -> int:
    ap = argparse.ArgumentParser(description="campaign run ledger")
    ap.add_argument("command",
                    choices=["init", "status", "set-budget", "reap", "reset"])
    ap.add_argument("value", nargs="?", help="budget count for set-budget")
    ap.add_argument("--output_root", required=True)
    ap.add_argument("--scenes", nargs="+",
                    default=["Curasao", "IUI3-RedSea", "JapaneseGradens-RedSea", "Panama"])
    ap.add_argument("--seeds", nargs="+", type=int, default=[0, 1, 2])
    ap.add_argument("--cells", nargs="+", default=None)
    ap.add_argument("--stale_minutes", type=int, default=45)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--all", action="store_true",
                    help="reset: include runs that failed but still have "
                         "attempts left, not only exhausted ones")
    args = ap.parse_args()

    ledger = Ledger(args.output_root)

    if args.command == "init":
        ledger.init(args.scenes, args.seeds, args.cells, force=args.force)
        print(f"initialised {len(ledger.runs)} runs")
        print(ledger.summary())
    elif args.command == "status":
        print(ledger.summary())
    elif args.command == "set-budget":
        if not args.value:
            raise SystemExit("set-budget needs a count")
        ledger.set_budget(int(args.value))
        print(f"budget set to {args.value}; blocked runs released")
    elif args.command == "reap":
        n = ledger.reap_stale(args.stale_minutes)
        print(f"reclaimed {n} stale run(s)")
    elif args.command == "reset":
        n = ledger.reset(cells=args.cells, all_failed=args.all)
        print(f"reset {n} run(s) -- attempts cleared, back in the queue")
        print(ledger.summary())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
