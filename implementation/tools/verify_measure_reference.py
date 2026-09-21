"""Acceptance test for the vanilla-SeaSplat collector (CD-31).

    python -m tools.verify_measure_reference

Pure stdlib and numpy. No GPU, no dataset, no rasterizer.

**What the collector is for.** Every number this study reports is a difference
against A0, so A0's standing rests on being the method it claims to
reimplement. That currently rests on `replicate_baseline.py`: converged
primitive count only, at 16 000 iterations, on one scene, with no fidelity
metric involved -- and at n=3 per side the 95% interval on the ratio is
+/-23.5% on that scene, so the data are consistent with a quarter's
difference.

**The constraint it works under.** Vanilla SeaSplat must not be modified.
It does not need to be: `render_uw.py`'s `render_set` is the upstream render
path, inherited unchanged in this fork, and `train.py`'s own evaluation calls
exactly that function and then reads the images back from disk. So a vanilla
run can be measured by pointing the same sequence at its output directory --
their model, their render code, our metric harness, one convention.

**T5 is the decisive check.** A margin verdict that silently passes when a
metric is absent would certify equivalence from missing data, which is worse
than reporting nothing: it produces the exact claim the thesis needs, from
no evidence at all.
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from tools.measure_reference import (  # noqa: E402
    A0_COST_KEYS,
    A0_SPLIT_KEYS,
    A0_TOP_KEYS,
    Deps,
    EVAL_SCHEMA_KEYS,
    measure,
    aggregate_by_scene,
    find_iteration,
    find_written_model,
    prune_intermediates,
    vanilla_command,
    load_margins,
    margin_verdict,
)

_results: list[tuple[str, bool, str]] = []


def check(name: str, fn) -> None:
    try:
        ok, detail = fn()
    except Exception as exc:  # noqa: BLE001
        ok, detail = False, f"raised {type(exc).__name__}: {exc}"
    _results.append((name, ok, detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")


def make_ref(root: Path, iters: list[int], *, medium_for: list[int] | None = None) -> Path:
    """A vanilla SeaSplat output directory, as an unpatched run leaves it."""
    medium_for = iters if medium_for is None else medium_for
    for it in iters:
        d = root / "point_cloud" / f"iteration_{it}"
        d.mkdir(parents=True, exist_ok=True)
        (d / "point_cloud.ply").write_bytes(b"ply\n")
        if it in medium_for:
            (root / f"attenuate_{it}.pth").write_bytes(b"\x00")
            (root / f"backscatter_{it}.pth").write_bytes(b"\x00")
    return root


# --------------------------------------------------------------------------


def t1_iteration_is_the_largest_complete_one():
    with tempfile.TemporaryDirectory() as tmp:
        r = make_ref(Path(tmp), [7000, 15000, 30000])
        got = find_iteration(r)
    return got == 30000, f"picked {got} from 7000/15000/30000"


def t2_incomplete_iteration_is_skipped():
    """A PLY without its medium nets cannot be composed, so it is not a candidate.

    Taking it anyway would silently evaluate the newest geometry against an
    older medium model, which is a different experiment that looks like this
    one.
    """
    with tempfile.TemporaryDirectory() as tmp:
        r = make_ref(Path(tmp), [15000, 30000], medium_for=[15000])
        got = find_iteration(r)
    return got == 15000, f"30000 has no medium nets; picked {got}"


def t3_no_usable_iteration_is_reported_not_guessed():
    with tempfile.TemporaryDirectory() as tmp:
        r = make_ref(Path(tmp), [30000], medium_for=[])
        got = find_iteration(r)
    return got is None, f"no complete iteration -> {got}"


def t4_margins_come_from_the_pre_registration():
    """The margin must be read from cells.json, never defaulted in code.

    A margin invented at analysis time is not a pre-specified margin, which is
    the only kind that licenses the word 'equivalent'.
    """
    m = load_margins()
    ok = (
        m is not None
        and m["psnr_pooled_db"] == 1.0
        and m["lpips"] == 0.02
        and m["n_primitives_fraction"] == 0.30
    )
    return ok, f"read from configs/cells.json: {m}"


def t5_absent_metric_fails_rather_than_passes():
    """DECISIVE. Missing data must never certify equivalence.

    A verdict that treats an absent metric as within-margin manufactures the
    study's foundational claim out of nothing, and it would read as a clean
    result.
    """
    margins = {"psnr_pooled_db": 1.0, "lpips": 0.02, "n_primitives_fraction": 0.30}
    v = margin_verdict(
        ss={"psnr_pooled": 30.1},                 # lpips and count absent
        a0={"psnr_pooled": 30.3, "lpips": 0.18, "n_primitives_final": 3_000_000},
        margins=margins,
    )
    ok = (
        v["psnr_pooled"]["within"] is True
        and v["lpips"]["within"] is None
        and v["n_primitives_final"]["within"] is None
        and v["verdict"] == "INCOMPLETE"
    )
    return ok, f"absent metrics -> within=None, overall {v['verdict']!r}"


def t6_within_margin_passes_and_outside_fails():
    margins = {"psnr_pooled_db": 1.0, "lpips": 0.02, "n_primitives_fraction": 0.30}
    a0 = {"psnr_pooled": 30.0, "lpips": 0.180, "n_primitives_final": 3_000_000}

    near = margin_verdict({"psnr_pooled": 30.4, "lpips": 0.185,
                           "n_primitives_final": 3_300_000}, a0, margins)
    far = margin_verdict({"psnr_pooled": 32.5, "lpips": 0.185,
                          "n_primitives_final": 3_300_000}, a0, margins)
    ok = near["verdict"] == "WITHIN MARGIN" and far["verdict"] == "OUTSIDE MARGIN"
    return ok, f"near={near['verdict']!r}, far(+2.5 dB)={far['verdict']!r}"


def t7_count_margin_is_relative_not_absolute():
    """+/-30% of the baseline, not 30 primitives."""
    margins = {"psnr_pooled_db": 1.0, "lpips": 0.02, "n_primitives_fraction": 0.30}
    a0 = {"n_primitives_final": 1_000_000}
    inside = margin_verdict({"n_primitives_final": 1_250_000}, a0, margins)
    outside = margin_verdict({"n_primitives_final": 1_400_000}, a0, margins)
    ok = (inside["n_primitives_final"]["within"] is True
          and outside["n_primitives_final"]["within"] is False)
    return ok, "+25% within, +40% outside"


def t8_emitted_schema_matches_what_the_collectors_read():
    """DECISIVE. The schema is whatever the consumers read -- not a guess.

    collect_results takes fidelity from ev["Test"] and ev["Train"] and marks a
    run INCOMPLETE if the split key is missing; analyse does ev[split] and
    skips on absence. The first version of this tool wrote the right numbers
    under a key named "quality", and its test asserted that invented key.
    Every consumer would have dropped the cell while it looked measured.

    So the expected shape is imported from the consumer and checked against
    what train.py writes for A0, block by block.
    """
    from tools.collect_results import COST, FIDELITY

    # What collect_results / analyse need present.
    need_split = set(FIDELITY) | {"n_images"}
    ok_splits = all(
        split in EVAL_SCHEMA_KEYS and need_split <= set(EVAL_SCHEMA_KEYS[split])
        for split in ("Train", "Test")
    )
    ok_cost = "cost" in EVAL_SCHEMA_KEYS and set(COST) <= set(EVAL_SCHEMA_KEYS["cost"])
    ok_no_invented = "quality" not in EVAL_SCHEMA_KEYS
    ok = ok_splits and ok_cost and ok_no_invented
    return ok, (f"Train/Test carry {sorted(need_split)}; cost carries the "
                f"{len(COST)} consumer keys; no invented 'quality' block")


def t9_verdict_is_reported_per_metric_not_only_overall():
    """An aggregate pass can hide one metric failing badly."""
    margins = {"psnr_pooled_db": 1.0, "lpips": 0.02, "n_primitives_fraction": 0.30}
    v = margin_verdict(
        {"psnr_pooled": 30.1, "lpips": 0.25, "n_primitives_final": 3_000_000},
        {"psnr_pooled": 30.0, "lpips": 0.18, "n_primitives_final": 3_000_000},
        margins,
    )
    ok = (v["psnr_pooled"]["within"] is True
          and v["lpips"]["within"] is False
          and v["verdict"] == "OUTSIDE MARGIN")
    return ok, "PSNR within, LPIPS outside, overall OUTSIDE -- both visible"


def t9b_check_margin_finds_runs_under_the_campaign_root():
    """DECISIVE. check_margin is given $DRIVE_ROOT and must look in runs/.

    It globbed from the root itself and so could never find a run, reporting
    "no SS runs found. S0 has not produced results yet" on a campaign whose
    S0 was complete. A message that is true of the search and false of the
    campaign is the worst kind, because nothing about it looks like a bug.
    """
    import io, contextlib
    from tools.measure_reference import check_margin
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for cell, psnr in (("SS", 30.1), ("A0", 30.4)):
            d = root / "runs" / cell / "Curasao" / "s0"
            d.mkdir(parents=True)
            (d / "eval_metrics.json").write_text(json.dumps({
                "Test": {"psnr_pooled": psnr, "lpips": 0.18},
                "cost": {"n_primitives_final": 4_000_000},
            }), encoding="utf-8")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            check_margin(root)
        out = buf.getvalue()
        # Finding the runs is necessary; reading their fidelity is the point.
        # The first version of this test passed while every PSNR came back
        # None and the verdict said INCOMPLETE, because it only checked that
        # the scene name appeared. A verdict that is not WITHIN or OUTSIDE is
        # a failure here.
        ok = ("Curasao" in out and "no SS runs found" not in out
              and "INCOMPLETE" not in out and "n/a" not in out
              and "WITHIN MARGIN" in out)
        return ok, ("found SS and A0 under runs/, read Test.psnr_pooled and "
                    "lpips, and reached a verdict"
                    if ok else out.strip().split(chr(10))[-6])


def t10_runs_are_aggregated_per_scene_not_per_seed():
    """DECISIVE. SS and A0 are not seed-matched, so they must not be paired.

    Vanilla accepts --seed but seeds only the CPU generator, so its GPU draws
    vary regardless; this implementation seeds both and still measures 49%
    spread. Pairing s0 against s0 would look like a paired comparison and be an
    unpaired one with the pairing noise retained -- inflating the apparent
    difference, and able to push a genuinely equivalent pair outside the
    margin.
    """
    evals = [
        {"_scene": "Curasao", "Test": {"psnr_pooled": 30.0}, "cost": {}},
        {"_scene": "Curasao", "Test": {"psnr_pooled": 31.0}, "cost": {}},
        {"_scene": "Curasao", "Test": {"psnr_pooled": 32.0}, "cost": {}},
        {"_scene": "Panama", "Test": {"psnr_pooled": 28.0}, "cost": {}},
    ]
    agg = aggregate_by_scene(evals)
    ok = (
        set(agg) == {"Curasao", "Panama"}
        and abs(agg["Curasao"]["psnr_pooled"] - 31.0) < 1e-9
        and abs(agg["Panama"]["psnr_pooled"] - 28.0) < 1e-9
    )
    return ok, f"Curasao mean of 3 = {agg['Curasao']['psnr_pooled']:.2f}, Panama n=1 = {agg['Panama']['psnr_pooled']:.2f}"


def t11_unlabelled_runs_are_dropped_not_misfiled():
    """A run without a scene cannot be aggregated and must not land anywhere."""
    agg = aggregate_by_scene([{"Test": {"psnr_pooled": 99.0}, "cost": {}}])
    return agg == {}, "run with no _scene is dropped, not bucketed arbitrarily"


def t12_written_model_is_found_where_upstream_put_it():
    """Upstream ignores --model_path, so the output must be located afterwards.

    Observed: the flag is accepted and then overwritten with
    `<source>/experiments/<MMDDYYYY>/test`. Nothing can be passed that would
    place the model where we asked, so it is found and moved instead.
    """
    import time
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "data" / "Curasao"
        actual = src / "experiments" / "09142026" / "test"
        t0 = time.time() - 5
        make_ref(actual, [30000])
        got = find_written_model([Path(tmp) / "asked_for", src], t0)
    ok = got is not None and got.resolve() == actual.resolve()
    return ok, f"found {got.name if got else None} under experiments/<date>/"


def t13_a_previous_seeds_model_is_not_adopted():
    """DECISIVE. The upstream path is date-scoped, so seeds collide.

    Two seeds of one scene on one day write to the same directory. If a run
    fails and the search accepts whatever is lying there, it measures the
    previous seed's model and files it as its own -- three identical rows that
    look like three repeats and are one run counted thrice, which would make
    the dispersion of the reference control appear to be zero.
    """
    import time
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "data" / "Curasao"
        stale = src / "experiments" / "09142026" / "test"
        make_ref(stale, [30000])
        for f in stale.rglob("*"):
            if f.is_file():
                import os
                os.utime(f, (1, 1))          # long before this run started
        got = find_written_model([src], time.time() - 5)
    return got is None, "a model predating the run is refused, not adopted"


def t14_vanilla_command_enables_the_medium_model():
    """DECISIVE. Upstream's defaults disable the thing that makes it SeaSplat.

    `configs/cells.json` names three flags that are silent no-ops upstream, and
    each produces a different experiment rather than an error:

      --do_seathru        default False -- the medium model never activates and
                          the reference is plain 3DGS on underwater images
      --seathru_from_iter default 9_000_000, past the end of training
      --eval              default False -- empty test set, inflated metrics

    The first was omitted when this was first built. The reference trained to
    completion, reported plausible numbers, and scored 19.34 dB against roughly
    30 for SeaSplat on the same scene -- a control that was not the method it
    was controlling for, and which would have made A0 look like a large
    improvement over its own baseline.
    """
    cmd = vanilla_command(Path("/data/Curasao"), Path("/out"), seed=1)
    joined = " ".join(cmd)
    missing = [f for f in ("--do_seathru", "--seathru_from_iter", "--eval")
               if f not in joined]
    return not missing, (f"all three no-op defaults overridden "
                         f"(missing: {missing or 'none'})")


def t15_prune_keeps_only_the_final_model():
    """DECISIVE. Pruning deletes files; it must never touch the target.

    Upstream saves at 1k/7k/15k/30k with medium nets and a background at each,
    plus a full-optimiser checkpoint it appends unconditionally. Only the
    30000 model is measured. Everything else is Drive for nothing -- but a
    prune that overreached by one name would delete the model it exists to
    keep, and the run would report success with nothing measurable behind it.
    """
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        for it in (1000, 7000, 15000, 30000):
            (d / "point_cloud" / f"iteration_{it}").mkdir(parents=True)
            (d / "point_cloud" / f"iteration_{it}" / "point_cloud.ply").write_bytes(b"ply")
            for pre in ("attenuate_", "backscatter_", "bg_"):
                (d / f"{pre}{it}.pth").write_bytes(b"\x00")
        for it in (1000, 7000, 15000, 30000):
            (d / f"chkpnt{it}.pth").write_bytes(b"\x00")
        (d / "cameras.json").write_text("{}", encoding="utf-8")
        (d / "cfg_args").write_text("", encoding="utf-8")
        (d / "input.ply").write_bytes(b"ply")

        removed = prune_intermediates(d, 30000)

        kept = sorted(p.name for p in d.iterdir())
        pcs = sorted(p.name for p in (d / "point_cloud").iterdir())
        ok = (
            pcs == ["iteration_30000"]
            and "attenuate_30000.pth" in kept
            and "backscatter_30000.pth" in kept
            and "bg_30000.pth" in kept
            and "cameras.json" in kept and "cfg_args" in kept and "input.ply" in kept
            and not any(n.startswith("chkpnt") for n in kept)
            and not any(n.endswith(("_1000.pth", "_7000.pth", "_15000.pth")) for n in kept)
            and len(removed) == 3 + 9 + 4      # 3 clouds, 9 medium/bg, 4 checkpoints
        )
        return ok, (f"kept iteration_30000 + its nets + cameras/cfg/input; "
                    f"removed {len(removed)}")


def t16_vanilla_command_trims_the_save_schedule():
    """The intermediates are stopped at the source where the CLI allows it."""
    cmd = vanilla_command(Path("/data/Curasao"), Path("/out"), seed=0)
    j = " ".join(cmd)
    ok = "--save_iterations 30000" in j and "--checkpoint_iterations 30000" in j
    return ok, "save and checkpoint schedules pinned to the final iteration"


def t17_contract_matches_what_train_py_writes():
    """DECISIVE. The A0 key constants must track train.py, or SS drifts alone.

    Read train.py's results block from source and compare, so the next field
    added to A0's file fails here rather than quietly leaving SS one key short
    -- or one key over, which is worse, since extras are what future consumers
    get written against.
    """
    import re
    src = (Path(__file__).resolve().parent.parent / "train.py").read_text(
        encoding="utf-8")
    blk = src[src.index('    results = {\n        "container"'):
              src.index("    results_file = Path")]
    top = tuple(re.findall(r'^\s{8}"(\w+)":', blk, re.M)) + ("Train", "Test")
    cost_blk = blk[blk.index('"cost": {'):]
    cost_blk = cost_blk[:cost_blk.index("\n        },")]
    cost_static = set(re.findall(r'^\s{12}"(\w+)":', cost_blk, re.M))

    prof_src = (Path(__file__).resolve().parent.parent / "utils"
                / "render_profile.py").read_text(encoding="utf-8")
    # profile_rendering seeds its dict with a literal ("render_x": ...) and
    # then assigns into it (out["render_x"] = ...); both spellings count.
    cost_prof = (set(re.findall(r'out\["(render_\w+)"\]', prof_src))
                 | set(re.findall(r'^\s+"(render_\w+)":', prof_src, re.M)))

    ok_top = top == A0_TOP_KEYS
    ok_cost = (cost_static | cost_prof) == set(A0_COST_KEYS)
    ok = ok_top and ok_cost
    drift = []
    if not ok_top:
        drift.append(f"top {top} != {A0_TOP_KEYS}")
    if not ok_cost:
        drift.append(f"cost diff {sorted((cost_static | cost_prof) ^ set(A0_COST_KEYS))}")
    return ok, "constants match train.py + profile_rendering" if ok else "; ".join(drift)


def t18_split_block_recipe_matches_train_py():
    """The per-split block is built with train.py's recipe, aliases included."""
    # aggregate_images returns these five; the module imports torch, so the
    # shape is stated here rather than imported -- this suite stays CPU-only.
    agg = {"n_images": 1, "psnr_pooled": 30.0, "psnr_per_channel": 30.2,
           "ssim": 0.9, "lpips": 0.18}
    block = {**agg, "SSIM": agg["ssim"], "PSNR": agg["psnr_pooled"],
             "LPIPS": agg["lpips"], "per_image": []}
    ok = set(block) == set(A0_SPLIT_KEYS) and block["PSNR"] == block["psnr_pooled"]
    return ok, f"{sorted(block)} and PSNR aliases the pooled figure"


# --------------------------------------------------------------------------
# measure(), end to end. Every collaborator that touches torch, CUDA or the
# rasterizer is stubbed -- and each stub enforces the same contract the real
# one does, so a wrong TYPE at the boundary fails here rather than on Colab.
# --------------------------------------------------------------------------


class _Cam:
    def __init__(self, name: str) -> None:
        self.image_name = name


class _Gaussians:
    class _XYZ:
        shape = (4_234_010, 3)
    get_xyz = _XYZ()


class _Scene:
    def __init__(self, train: list, test: list) -> None:
        self._train, self._test = train, test

    def getTrainCameras(self):
        return self._train

    def getTestCameras(self):
        return self._test


class _Net:
    """What DiagnosticLogger reads off the medium models."""

    def __init__(self, att, bs, binf) -> None:
        self.attenuation_conv_params = att
        self.backscatter_conv_params = bs
        self.B_inf = binf


class _T:
    """A minimal tensor stand-in for DiagnosticLogger._triple."""

    def __init__(self, vals) -> None:
        self._v = list(vals)

    def detach(self):
        return self

    def flatten(self):
        return self

    def float(self):
        return self

    def cpu(self):
        return self

    def numel(self):
        return len(self._v)

    def __getitem__(self, i):
        class _S:
            def __init__(s, x): s.x = x
            def item(s): return s.x
        return _S(self._v[i])


class _Diag:
    """Writes the same one-row CSV DiagnosticLogger would, without torch."""

    def __init__(self, out_dir: Path) -> None:
        self.path = out_dir / "diagnostics.csv"
        self.rows: list[dict] = []

    def log(self, **kw) -> None:
        self.rows.append(kw)

    def close(self) -> None:
        import csv
        with open(self.path, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=["iteration", "event", "n_primitives", "note"])
            w.writeheader()
            for r in self.rows:
                w.writerow({k: r.get(k, "") for k in w.fieldnames})


def _stub_deps(calls: dict) -> Deps:
    """Stubs that record what they were given and enforce the real contracts."""
    import contextlib

    def render_set(out_dir, split, it, cams, gaussians, pipe, bg,
                   do_seathru, add_water, add_fog, learned_bg, bs, at,
                   save_as_jpeg=False):
        # The real one writes files here; measure() lists this directory.
        d = Path(out_dir) / split / "with_water"
        d.mkdir(parents=True, exist_ok=True)
        for c in cams:
            (d / f"{c.image_name}.png").write_bytes(b"png")
        calls.setdefault("render_set", []).append((split, len(cams), do_seathru))

    def read_images(renders_dir, gt_dir, fnames):
        # The EXACT operation that crashed on Colab: metrics.readImages joins
        # its directories with `/`. A str here raises TypeError, as it did.
        import os
        for f in fnames:
            os.path.exists(gt_dir / (f.split(".")[0] + ".png"))
            os.path.exists(renders_dir / f)
        calls["read_images_types"] = (type(renders_dir).__name__, type(gt_dir).__name__)
        return [object()] * len(fnames), [object()] * len(fnames), [f.split(".")[0] for f in fnames]

    def evaluate_pair(r, g, net):
        return {"psnr_pooled": 30.0, "psnr_per_channel": 30.2, "ssim": 0.9, "lpips": 0.18}

    def aggregate_images(records):
        n = len(records)
        return {"n_images": n, "psnr_pooled": 30.0, "psnr_per_channel": 30.2,
                "ssim": 0.9, "lpips": 0.18}

    def profile_rendering(cams, g, pipe, bg):
        return {"render_fps": 70.0, "render_ms_per_frame": 14.2,
                "render_ms_per_frame_sd": 0.3, "render_ms_per_frame_cv": 2.1,
                "render_frames_timed": len(cams), "render_warmup_frames": 5,
                "render_repeats": 3, "render_note": "stub", "render_peak_mem_mb": 3500.0}

    return Deps(
        no_grad=contextlib.nullcontext,
        model_params=lambda s, m, r: {"source": s, "model_path": m, "resolution": r},
        pipe_params=lambda: object(),
        load_gaussians=lambda ply, sh: _Gaussians(),
        make_scene=lambda mp, g, it: _Scene(
            [_Cam(f"tr{i:02d}") for i in range(18)], [_Cam(f"te{i:02d}") for i in range(3)]),
        load_medium=lambda root, it: (
            _Net(None, _T([6.9, 4.6, 3.5]), _T([0.2, 0.3, 0.4])),
            _Net(_T([1.4, 1.3, 1.2]), None, None)),
        background=lambda: object(),
        render_set=render_set,
        read_images=read_images,
        evaluate_pair=evaluate_pair,
        aggregate_images=aggregate_images,
        convention_note=lambda net, c: {"psnr_pooled": "pooled", "container": c},
        profile_rendering=profile_rendering,
        diag_logger=_Diag,
    )


def _stage_run(tmp: Path) -> tuple[Path, Path]:
    ref = tmp / "runs" / "SS" / "Curasao" / "s0"
    make_ref(ref, [30000])
    (ref / "bg_30000.pth").write_bytes(b"\x00" * 16)
    src = tmp / "data" / "Curasao"
    (src / "images").mkdir(parents=True)
    (src / "images" / "tr00.png").write_bytes(b"png")   # so container resolves to png
    return ref, src


def t19_measure_writes_a0s_schema_end_to_end():
    """DECISIVE. The real measure() body, boundary stubbed, file asserted.

    Every previous check covered the helpers around measure(); measure()
    itself had never run under test, which is why each Colab run found the
    next wrong line. This executes it and reads back what it wrote.
    """
    with tempfile.TemporaryDirectory() as tmp:
        ref, src = _stage_run(Path(tmp))
        calls: dict = {}
        measure(ref, src, ref, iteration=30000, train_wall_seconds=1712.4,
                deps=_stub_deps(calls))

        ev = json.loads((ref / "eval_metrics.json").read_text(encoding="utf-8"))
        a0 = json.load(open(Path(__file__).resolve().parent.parent.parent
                            / "eval_metrics_A0_Curasao_s0.json")) \
            if (Path(__file__).resolve().parent.parent.parent
                / "eval_metrics_A0_Curasao_s0.json").exists() else None

        problems = []
        if tuple(ev) != A0_TOP_KEYS:
            problems.append(f"top keys {tuple(ev)}")
        if set(ev["cost"]) != set(A0_COST_KEYS):
            problems.append(f"cost keys {sorted(set(ev['cost']) ^ set(A0_COST_KEYS))}")
        for split, n in (("Train", 18), ("Test", 3)):
            if set(ev[split]) != set(A0_SPLIT_KEYS):
                problems.append(f"{split} keys {sorted(set(ev[split]) ^ set(A0_SPLIT_KEYS))}")
            if ev[split]["n_images"] != n:
                problems.append(f"{split} n_images {ev[split]['n_images']} != {n}")
            if ev[split]["PSNR"] != ev[split]["psnr_pooled"]:
                problems.append(f"{split} PSNR alias not pooled")
        if ev["cost"]["train_wall_seconds"] != 1712.4:
            problems.append("wall clock not carried")
        if ev["cost"]["n_primitives_final"] != 4_234_010:
            problems.append("count not from the model")
        if ev["container"] != "png":
            problems.append(f"container {ev['container']}")
        # If the real A0 file is beside the repo, the shapes must match it too.
        if a0 is not None and set(a0["cost"]) - set(ev["cost"]):
            problems.append(f"A0 cost keys missing: {sorted(set(a0['cost']) - set(ev['cost']))}")

        for side in ("model_size.json", "reference.json", "diagnostics.csv"):
            if not (ref / side).exists():
                problems.append(f"{side} not written")
        if calls.get("render_set") != [("train", 18, True), ("test", 3, True)]:
            problems.append(f"render_set calls {calls.get('render_set')}")

        ok = not problems
        return ok, ("eval_metrics.json is A0's schema; sidecars written; "
                    "both splits rendered with the medium on"
                    if ok else "; ".join(problems))


def t20_read_images_receives_paths_not_strings():
    """DECISIVE. The exact crash from Colab, reproduced by the stub's `/` join."""
    with tempfile.TemporaryDirectory() as tmp:
        ref, src = _stage_run(Path(tmp))
        calls: dict = {}
        measure(ref, src, ref, iteration=30000, deps=_stub_deps(calls))
        kinds = calls.get("read_images_types")
        ok = kinds == ("PosixPath", "PosixPath") or kinds == ("WindowsPath", "WindowsPath")
        return ok, f"readImages got {kinds}"


def main() -> int:
    print("=" * 68)
    print("CD-31  vanilla SeaSplat collector")
    print("=" * 68)

    check("T1  iteration is the largest complete one", t1_iteration_is_the_largest_complete_one)
    check("T2  incomplete iteration is skipped", t2_incomplete_iteration_is_skipped)
    check("T3  no usable iteration is reported, not guessed",
          t3_no_usable_iteration_is_reported_not_guessed)
    check("T4  margins come from the pre-registration", t4_margins_come_from_the_pre_registration)
    check("T5  an absent metric fails rather than passes  <-- decisive",
          t5_absent_metric_fails_rather_than_passes)
    check("T6  within margin passes, outside fails", t6_within_margin_passes_and_outside_fails)
    check("T7  count margin is relative, not absolute", t7_count_margin_is_relative_not_absolute)
    check("T8  emitted schema matches what the collectors read",
          t8_emitted_schema_matches_what_the_collectors_read)
    check("T9  verdict is per metric, not only overall",
          t9_verdict_is_reported_per_metric_not_only_overall)
    check("T9b check_margin finds runs under the campaign root  <-- decisive",
          t9b_check_margin_finds_runs_under_the_campaign_root)
    check("T10 runs aggregate per scene, not per seed  <-- decisive",
          t10_runs_are_aggregated_per_scene_not_per_seed)
    check("T11 unlabelled runs are dropped, not misfiled",
          t11_unlabelled_runs_are_dropped_not_misfiled)
    check("T12 written model is found where upstream put it",
          t12_written_model_is_found_where_upstream_put_it)
    check("T13 a previous seed's model is not adopted  <-- decisive",
          t13_a_previous_seeds_model_is_not_adopted)
    check("T14 vanilla command enables the medium model  <-- decisive",
          t14_vanilla_command_enables_the_medium_model)
    check("T15 prune keeps only the final model  <-- decisive",
          t15_prune_keeps_only_the_final_model)
    check("T16 vanilla command trims the save schedule",
          t16_vanilla_command_trims_the_save_schedule)
    check("T17 A0 key constants track train.py  <-- decisive",
          t17_contract_matches_what_train_py_writes)
    check("T18 split block uses train.py's recipe",
          t18_split_block_recipe_matches_train_py)
    check("T19 measure() writes A0's schema end to end  <-- decisive",
          t19_measure_writes_a0s_schema_end_to_end)
    check("T20 readImages receives Paths, not strings  <-- decisive",
          t20_read_images_receives_paths_not_strings)

    failed = [n for n, ok, _ in _results if not ok]
    print("\n" + "=" * 68)
    if failed:
        print(f"MEASURE REFERENCE: FAILED ({len(failed)}/{len(_results)})")
        for n in failed:
            print(f"  - {n}")
        return 1
    print(f"MEASURE REFERENCE: PASSED ({len(_results)}/{len(_results)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
