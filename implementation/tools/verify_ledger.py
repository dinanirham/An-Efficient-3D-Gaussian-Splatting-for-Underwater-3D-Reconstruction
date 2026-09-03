"""Acceptance test for the campaign ledger. Pure stdlib -- no torch, no GPU.

    python -m tools.verify_ledger

The ledger is the only thing standing between a preemptible session and a
corrupted campaign, and its failure modes are all quiet ones: a stage claimed
out of order, a cell run without its prerequisite, a dead session holding a row
forever, a half-written file after a kill.  None of those raise; they just
produce a results table that means something other than it appears to.
"""

from __future__ import annotations

import json
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from tools.run_ledger import Ledger  # noqa: E402

SCENES = ["Curasao", "IUI3-RedSea", "JapaneseGradens-RedSea", "Panama"]
SEEDS = [0, 1, 2]

_results: list[tuple[str, bool, str]] = []


def check(name: str, fn) -> None:
    try:
        ok, detail = fn()
    except Exception as exc:  # noqa: BLE001
        ok, detail = False, f"raised {type(exc).__name__}: {exc}"
    _results.append((name, ok, detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")


def fresh(tmp: str) -> Ledger:
    led = Ledger(tmp)
    led.init(SCENES, SEEDS)
    return led


def finish_stage(led: Ledger, cells: set[str]) -> int:
    """Mark every run of the given cells done, as if they had succeeded."""
    n = 0
    for r in led.runs:
        if r["cell"] in cells:
            r["status"] = "done"
            n += 1
    led.save()
    return n


# ---------------------------------------------------------------------------


def t1_init_shape():
    with tempfile.TemporaryDirectory() as tmp:
        led = fresh(tmp)
        from tools.run_ledger import STAGES
        expect_cells = {c for cs in STAGES.values() for c in cs}
        cells = {r["cell"] for r in led.runs}
        n = len(expect_cells) * len(SCENES) * len(SEEDS)
        ok = len(led.runs) == n and cells == expect_cells
        return ok, (f"{len(led.runs)} runs across {len(cells)} cells "
                    f"(expect {n}/{len(expect_cells)})")


def t2_stage_order_enforced():
    """S2 must not start while S1 has outstanding work."""
    with tempfile.TemporaryDirectory() as tmp:
        led = fresh(tmp)
        led.set_budget(800_000)
        first = led.claim()
        stage_first = first["stage"]

        # Claim everything S1 will give us.
        claimed = [first]
        while (r := led.claim()) is not None:
            claimed.append(r)
        stages = {r["stage"] for r in claimed}

        ok = stage_first == "S1" and stages == {"S1"}
        return ok, (
            f"first claim stage={stage_first}; stages claimable before S1 "
            f"completes={sorted(stages)} (must be S1 only)"
        )


def t3_stage_advances_when_complete():
    with tempfile.TemporaryDirectory() as tmp:
        led = fresh(tmp)
        led.set_budget(800_000)
        finish_stage(led, {"A0"})
        nxt = led.claim()
        ok = nxt is not None and nxt["stage"] == "S2" and nxt["cell"] == "A2"
        return ok, f"after S1 completes, next claim = {nxt['id'] if nxt else None}"


def t4_m2_blocked_without_budget():
    """An m2 cell without a budget is a different experiment, not a run.

    A fully-blocked stage is skipped rather than stalling the queue, but the
    skip must be recorded -- an unannounced reorder is the failure mode here,
    not the reorder itself.
    """
    with tempfile.TemporaryDirectory() as tmp:
        led = fresh(tmp)
        # `init` now takes the budget from configs/cells.json, so the
        # no-budget state has to be constructed rather than assumed. The
        # mechanism it guards is unchanged and still worth testing: an m2 cell
        # without a budget is a different experiment, not a run.
        led.data["n_bud"] = None
        finish_stage(led, {"A0"})
        nxt = led.claim()          # S2 needs a budget it does not have
        blocked = {r["cell"] for r in led.runs if r["status"] == "blocked"}
        skipped = getattr(led, "last_skipped", [])

        ok = (
            "A2" in blocked
            and any("S2" in s and "budget" in s for s in skipped)
            # A3 needs neither a budget nor a cloud, so it is the correct
            # thing to fall through to.
            and nxt is not None and nxt["cell"] == "A3"
        )
        return ok, (
            f"blocked cells={sorted(blocked)}; skipped={skipped[:1]}; "
            f"fell through to {nxt['id'] if nxt else None}"
        )


def t4b_runnable_stage_holds_the_queue():
    """A stage that CAN run must not be skipped -- this is the real guarantee."""
    with tempfile.TemporaryDirectory() as tmp:
        led = fresh(tmp)
        led.set_budget(800_000)
        # S1 is runnable and untouched; nothing later may be claimed.
        claimed = []
        while (r := led.claim()) is not None:
            claimed.append(r["stage"])
        ok = set(claimed) == {"S1"}
        return ok, f"stages claimable while S1 is runnable: {sorted(set(claimed))}"


def t5_set_budget_releases_blocked():
    with tempfile.TemporaryDirectory() as tmp:
        led = fresh(tmp)
        led.data["n_bud"] = None          # see T4
        finish_stage(led, {"A0"})
        led.claim()                       # blocks the A2 rows
        assert any(r["status"] == "blocked" for r in led.runs)
        led.set_budget(812_345)
        nxt = led.claim()
        ok = nxt is not None and nxt["cell"] == "A2" and led.data["n_bud"] == 812_345
        return ok, f"budget set -> claimed {nxt['id'] if nxt else None}"


def t6_m1_blocked_without_dense_cloud():
    with tempfile.TemporaryDirectory() as tmp:
        led = fresh(tmp)
        led.set_budget(800_000)
        finish_stage(led, {"A0", "A2"})
        led.claim()                       # S3 = A1 (needs a cloud) and A3
        blocked = [r for r in led.runs if r["status"] == "blocked"]
        a1_blocked = [r for r in blocked if r["cell"] == "A1"]
        ok = len(a1_blocked) > 0 and "dense cloud" in a1_blocked[0]["error"]
        return ok, (
            f"{len(a1_blocked)} A1 runs blocked; reason: "
            f"{a1_blocked[0]['error'][:55] if a1_blocked else 'none'}"
        )


def t7_dense_cloud_unblocks_m1():
    with tempfile.TemporaryDirectory() as tmp:
        led = fresh(tmp)
        led.set_budget(800_000)
        finish_stage(led, {"A0", "A2"})
        for scene in SCENES:
            p = led.dense_pcd_path(scene)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(b"ply\n")
        # Release the rows blocked by the earlier probe.
        for r in led.runs:
            if r["status"] == "blocked":
                r["status"] = "pending"
        led.save()
        nxt = led.claim()
        ok = nxt is not None and nxt["stage"] == "S3"
        return ok, f"with clouds present, claimed {nxt['id'] if nxt else None}"


def t8_stale_reclaimed():
    """A session killed mid-run must not hold its row forever."""
    with tempfile.TemporaryDirectory() as tmp:
        led = fresh(tmp)
        led.set_budget(800_000)
        run = led.claim()
        stale_ts = (datetime.now(timezone.utc) - timedelta(hours=3)).isoformat()
        led.by_id(run["id"])["heartbeat"] = stale_ts
        led.save()

        n = led.reap_stale(stale_minutes=45)
        again = led.claim()
        ok = n == 1 and again is not None and again["id"] == run["id"]
        return ok, f"reclaimed={n}, re-claimed same run={again['id'] == run['id']}"


def t9_attempt_cap():
    """A configuration that always fails must not loop forever."""
    with tempfile.TemporaryDirectory() as tmp:
        led = fresh(tmp)
        led.set_budget(800_000)
        run = led.claim()
        rid = run["id"]
        for _ in range(5):
            led.finish(rid, ok=False, error="boom")
            nxt = led.claim(max_attempts=3)
            if nxt is None or nxt["id"] != rid:
                break
        attempts = led.by_id(rid)["attempts"]
        ok = attempts <= 3
        return ok, f"attempts capped at {attempts} (limit 3)"


def t10_save_is_atomic_and_reloadable():
    with tempfile.TemporaryDirectory() as tmp:
        led = fresh(tmp)
        led.set_budget(999)
        led.claim()
        reopened = Ledger(tmp)
        parsed = json.loads(led.path.read_text(encoding="utf-8"))
        leftovers = list(Path(tmp).glob("*.tmp"))
        ok = (
            reopened.data["n_bud"] == 999
            and len(parsed["runs"]) == len(led.runs)
            and not leftovers
        )
        return ok, (
            f"reloaded budget={reopened.data['n_bud']}, runs={len(parsed['runs'])}, "
            f"temp files left={len(leftovers)}"
        )


def t11_images_dir_resolution():
    """The queue must find the undistorted layout, not only the original.

    Training reads the undistorted scene, where COLMAP writes `images`. A
    resolver that accepts only `images_wb` blocks every run against a
    correctly preprocessed dataset -- and does it as a per-run "cannot build
    command" note, which looks like a data problem rather than a harness bug.
    """
    from tools.run_queue import find_images_dir

    cases = [
        ("images", "images", "undistorted layout"),
        ("images_wb", "images_wb", "original layout"),
        ("Images_wb", "Images_wb", "original, capital I"),
    ]
    with tempfile.TemporaryDirectory() as tmp:
        for made, expected, label in cases:
            scene = Path(tmp) / label.replace(" ", "_")
            (scene / made).mkdir(parents=True)
            (scene / "sparse" / "0").mkdir(parents=True)
            got = find_images_dir(scene)
            if got != expected:
                return False, f"{label}: expected {expected!r}, got {got!r}"

        # Both present: the undistorted copy must win, or a scene staged over
        # an earlier one would silently train on distorted images.
        both = Path(tmp) / "both"
        (both / "images").mkdir(parents=True)
        (both / "images_wb").mkdir(parents=True)
        if find_images_dir(both) != "images":
            return False, f"both present: got {find_images_dir(both)!r}, want 'images'"

        empty = Path(tmp) / "empty"
        (empty / "sparse").mkdir(parents=True)
        try:
            find_images_dir(empty)
            return False, "a scene with no image directory did not raise"
        except FileNotFoundError:
            pass

    return True, "images / images_wb / Images_wb resolved; images wins; empty raises"


def t12_exhausted_runs_are_visible_and_resettable():
    """A run at the attempt cap must be distinguishable from a queued one.

    It still carries status "pending", so the counts read pending=N while the
    queue reports nothing eligible to claim -- a stuck campaign that looks
    like an idle one. And once the environmental cause is fixed, there has to
    be a way back into the queue that does not discard completed runs.
    """
    with tempfile.TemporaryDirectory() as tmp:
        led = fresh(tmp)

        # Burn A0/Curasao/s0's attempts the way a broken harness would.
        row = led.by_id("A0/Curasao/s0")
        row["attempts"] = 3
        row["error"] = "cannot build command: no images_wb directory"
        led.save()

        if not any(r["id"] == row["id"] for r in led.exhausted()):
            return False, "exhausted() did not report a run at the cap"
        if "OUT OF ATTEMPTS" not in led.summary():
            return False, "summary() does not flag exhausted runs"

        # It must not be claimable while spent...
        for _ in range(12):
            got = led.claim()
            if got is None:
                break
            if got["id"] == row["id"]:
                return False, "claimed a run that was out of attempts"
            got["status"] = "done"

        n = led.reset()
        if n < 1:
            return False, f"reset returned {n}, expected at least 1"
        again = led.by_id("A0/Curasao/s0")
        if again["attempts"] != 0 or again["status"] != "pending":
            return False, f"after reset: attempts={again['attempts']} status={again['status']}"

    # Blocked runs must survive reset untouched: their problem is a missing
    # prerequisite, not a spent attempt, and claiming one would run a cell
    # whose budget or dense cloud still does not exist.
    with tempfile.TemporaryDirectory() as tmp2:
        led = fresh(tmp2)
        blocked = led.by_id("A2/Curasao/s0")
        blocked["status"] = "blocked"
        blocked["error"] = "no primitive budget recorded"
        blocked["attempts"] = 3
        led.save()
        led.reset(all_failed=True)
        if led.by_id("A2/Curasao/s0")["status"] != "blocked":
            return False, "reset flipped a blocked run to pending"

    return True, "cap is visible in summary, reset restores it, blocked untouched"


def t13_init_takes_the_budget_from_config():
    """`init` must pick n_bud up from cells.json, and say where it came from.

    The budget used to be derived from A0 and therefore lived only here. It is
    now fixed ahead of the campaign by the binding rule, so it exists in
    configs/cells.json too -- and two homes for one number is a way for them to
    disagree. Forgetting `set-budget` after an init would silently block all 48
    m2 runs.
    """
    from tools.run_ledger import config_n_bud

    expected = config_n_bud()
    if expected is None:
        return False, "configs/cells.json has no defaults.n_bud to read"

    with tempfile.TemporaryDirectory() as tmp:
        led = fresh(tmp)
        got = led.data.get("n_bud")
        src = led.data.get("n_bud_source")
        if got != expected:
            return False, f"init recorded n_bud={got}, config says {expected}"
        if not src:
            return False, "n_bud_source not recorded, so provenance is lost"

        # ...and with a budget in hand, no m2 cell may be blocked on it.
        blocked = [r["id"] for r in led.runs
                   if any("budget" in b for b in led.blockers(r))]
        if blocked:
            return False, f"{len(blocked)} runs still blocked on the budget"

    return True, f"n_bud={expected:,} read from {src}; no m2 cell blocked on it"


def main() -> int:
    check("T1 init creates the full 8x4x3 matrix", t1_init_shape)
    check("T2 stage order is enforced  <-- decisive", t2_stage_order_enforced)
    check("T3 stage advances once complete", t3_stage_advances_when_complete)
    check("T4 blocked stage is skipped, loudly", t4_m2_blocked_without_budget)
    check("T4b a runnable stage holds the queue  <-- decisive", t4b_runnable_stage_holds_the_queue)
    check("T5 setting the budget releases them", t5_set_budget_releases_blocked)
    check("T6 m1 cells blocked without a dense cloud", t6_m1_blocked_without_dense_cloud)
    check("T7 dense cloud unblocks m1", t7_dense_cloud_unblocks_m1)
    check("T8 dead sessions are reclaimed", t8_stale_reclaimed)
    check("T9 repeated failure is capped", t9_attempt_cap)
    check("T10 ledger writes atomically and reloads", t10_save_is_atomic_and_reloadable)
    check("T11 image dir resolves for undistorted scenes  <-- decisive",
          t11_images_dir_resolution)
    check("T12 exhausted runs are visible and resettable  <-- decisive",
          t12_exhausted_runs_are_visible_and_resettable)
    check("T13 init takes the budget from cells.json",
          t13_init_takes_the_budget_from_config)

    failed = [n for n, ok, _ in _results if not ok]
    print("\n" + "=" * 68)
    if failed:
        print(f"RUN LEDGER: FAILED ({len(failed)}/{len(_results)})")
        for n in failed:
            print(f"  - {n}")
        return 1
    print(f"RUN LEDGER: PASSED ({len(_results)}/{len(_results)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
