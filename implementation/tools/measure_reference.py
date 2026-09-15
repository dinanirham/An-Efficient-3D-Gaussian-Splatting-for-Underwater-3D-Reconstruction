"""Measure a vanilla SeaSplat run with the campaign's own harness (CD-31).

    python -m tools.measure_reference \
        --ref_root   /content/seasplat_ref/output/Curasao \
        --source_path /content/drive/.../dataset/undistorted/Curasao \
        --out        "$DRIVE_ROOT/runs/SS/Curasao/s0"

    python -m tools.measure_reference --check_margin --output_root "$DRIVE_ROOT"

**Why.** Every number this study reports is a difference against A0, so A0's
standing rests entirely on being the method it claims to reimplement. That
currently rests on `tools/replicate_baseline.py`, which compares **converged
primitive count only**, at **16 000 iterations**, on **one scene** -- and at
n=3 per side the 95% interval on the ratio is +/-23.5% there, so the data are
consistent with A0 differing from vanilla SeaSplat by a quarter. Absence of a
detected difference is not evidence of equivalence, least of all on an outcome
with 6.0-29.3% dispersion.

**The constraint.** Vanilla SeaSplat is not modified, and does not need to be.
`render_uw.py`'s `render_set` is the upstream render path, inherited unchanged
in this fork, and `train.py`'s own evaluation calls exactly that function and
then reads the images back from disk. Pointing the same sequence at a vanilla
output directory gives: their trained model, their render code, our metric
harness, one convention on both sides.

Note that `tools/instrument_reference.py` *patches* a checkout and says in its
own docstring that a patched checkout must not produce SS numbers. That tool
is for diagnosis. This one touches nothing.

**Matching the harness matters more than it looks.** Metrics are computed from
8-bit files written to disk and read back, not from in-memory tensors -- an
inherited quirk of the evaluation path (`chapter/06` section 3.7.5). Rendering
to disk and reading back reproduces it on both sides. Computing SS metrics
from in-memory tensors would be *more* accurate and *less* comparable, which
is the wrong trade for a control.

**The margin.** `--check_margin` compares SS against A0 using the equivalence
margin fixed in `configs/cells.json` before S0 ran. A margin chosen after
seeing the data is not a pre-specified margin, and only a pre-specified one
licenses the word *equivalent*.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Optional

sys.path.append(str(Path(__file__).resolve().parent.parent))

CELLS = Path(__file__).resolve().parent.parent / "configs" / "cells.json"

# The shape collect_results.py and analyse.py read. Both take the split block
# from ev["Test"] / ev["Train"] -- collect_results marks a run INCOMPLETE if the
# split key is absent, and analyse skips it -- so a file that carried the right
# numbers under any other key would be dropped by every consumer while looking
# like a measured control. The first version of this tool did exactly that,
# under a key named "quality", and its own test asserted the invented key
# rather than the real one. The key lists are now imported from the consumer.
from tools.collect_results import COST as CONSUMER_COST  # noqa: E402
from tools.collect_results import FIDELITY as CONSUMER_FIDELITY  # noqa: E402

SPLITS: tuple[str, ...] = ("Train", "Test")
EVAL_SCHEMA_KEYS: dict[str, tuple[str, ...]] = {
    **{split: (*CONSUMER_FIDELITY, "n_images") for split in SPLITS},
    "cost": tuple(CONSUMER_COST),
}

# The EXACT key set train.py writes for every other cell, so SS's file is
# schema-identical rather than merely a superset. Extra keys are a slow
# poison: a consumer written against A0 ignores them today and someone
# writes one against SS tomorrow. Anything SS-specific goes to a sidecar,
# never into this file. verify_measure_reference T17 reads train.py's source
# and fails if this drifts from what it actually writes.
A0_TOP_KEYS: tuple[str, ...] = (
    "container", "lpips_backbone", "masking", "conventions", "cost", "Train", "Test",
)
A0_COST_KEYS: tuple[str, ...] = (
    "iterations", "effective_optimizer_steps", "train_wall_seconds",
    "n_primitives_final", "population_collapsed",
    # from utils.render_profile.profile_rendering
    "render_fps", "render_ms_per_frame", "render_ms_per_frame_sd",
    "render_ms_per_frame_cv", "render_frames_timed", "render_warmup_frames",
    "render_repeats", "render_note", "render_peak_mem_mb",
)
A0_SPLIT_KEYS: tuple[str, ...] = (
    "n_images", "psnr_pooled", "psnr_per_channel", "ssim", "lpips",
    "SSIM", "PSNR", "LPIPS", "per_image",
)

MARGIN_TO_METRIC = {
    "psnr_pooled_db": ("psnr_pooled", "absolute"),
    "lpips": ("lpips", "absolute"),
    "n_primitives_fraction": ("n_primitives_final", "relative"),
}


def find_iteration(ref_root: Path) -> Optional[int]:
    """The largest iteration with a point cloud *and* both medium nets.

    Completeness matters: a PLY without its medium nets cannot be composed, and
    silently falling back to an older medium model would evaluate new geometry
    against a stale medium -- a different experiment that looks like this one.
    """
    best: Optional[int] = None
    for d in (ref_root / "point_cloud").glob("iteration_*"):
        if not (d / "point_cloud.ply").exists():
            continue
        try:
            it = int(d.name.split("_")[1])
        except (IndexError, ValueError):
            continue
        if not (ref_root / f"attenuate_{it}.pth").exists():
            continue
        if not (ref_root / f"backscatter_{it}.pth").exists():
            continue
        if best is None or it > best:
            best = it
    return best


def load_margins(path: Path = CELLS) -> Optional[dict]:
    """The equivalence margin, read from the pre-registration and never defaulted.

    Returning None rather than a built-in default is deliberate. A margin
    invented at analysis time is not pre-specified, and a tool that supplies
    one quietly would let an equivalence claim rest on a number chosen after
    seeing the data.
    """
    try:
        cfg = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    m = cfg.get("cells", {}).get("SS", {}).get("equivalence_margin")
    if not m:
        return None
    return {k: v for k, v in m.items() if not k.startswith("_")}


def aggregate_by_scene(evals: list[dict]) -> dict[str, dict[str, float]]:
    """Mean of each metric per scene, over however many repeats exist.

    **Not per seed**, and the distinction is load-bearing. Vanilla SeaSplat
    accepts `--seed` but seeds only the CPU generator, so its GPU draws vary
    regardless `[tools/replicate_baseline.py]` -- 17% spread across two
    reference runs at a fixed seed. This implementation seeds both and still
    measures 49%, because the rasterizer backward accumulates atomically and
    densification amplifies the difference.

    So `s0`, `s1`, `s2` are **repeat indices on both sides, not matched
    seeds**. Pairing `SS/scene/s0` against `A0/scene/s0` would look like a
    paired comparison and be an unpaired one with the pairing noise left in:
    it would inflate the apparent difference and could push a genuinely
    equivalent pair outside the margin. The comparison that the data supports
    is distribution against distribution, which at three repeats means scene
    mean against scene mean.
    """
    out: dict[str, dict[str, list[float]]] = {}
    for e in evals:
        scene = e.get("_scene")
        if scene is None:
            continue
        flat = {**e.get("quality", {}), **e.get("cost", {})}
        bucket = out.setdefault(scene, {})
        for k, v in flat.items():
            if isinstance(v, (int, float)):
                bucket.setdefault(k, []).append(float(v))
    return {
        scene: {k: sum(vs) / len(vs) for k, vs in metrics.items() if vs}
        for scene, metrics in out.items()
    }


def margin_verdict(ss: dict, a0: dict, margins: dict) -> dict[str, Any]:
    """Per-metric comparison against the pre-specified margin.

    An absent metric yields `within=None`, never `True`. Treating missing data
    as within-margin would manufacture this study's foundational claim out of
    nothing, and it would read as a clean result rather than as an error.
    """
    out: dict[str, Any] = {}
    any_missing = False
    any_outside = False

    for mkey, (metric, kind) in MARGIN_TO_METRIC.items():
        limit = margins.get(mkey)
        a, b = a0.get(metric), ss.get(metric)
        if limit is None or a is None or b is None:
            out[metric] = {"within": None, "ss": b, "a0": a, "limit": limit,
                           "why": "metric or margin absent"}
            any_missing = True
            continue
        diff = float(b) - float(a)
        allowed = float(limit) * abs(float(a)) if kind == "relative" else float(limit)
        within = abs(diff) <= allowed
        out[metric] = {"within": bool(within), "ss": b, "a0": a,
                       "diff": round(diff, 6), "allowed": round(allowed, 6),
                       "kind": kind}
        if not within:
            any_outside = True

    if any_outside:
        out["verdict"] = "OUTSIDE MARGIN"
    elif any_missing:
        out["verdict"] = "INCOMPLETE"
    else:
        out["verdict"] = "WITHIN MARGIN"
    return out


# ---------------------------------------------------------------------------
# Measurement. Torch is imported lazily so the pure parts stay CPU-testable.
# ---------------------------------------------------------------------------


def _model_params(source_path: str, model_path: str, resolution: int = -1):
    """Every field Scene reads, from the real parser rather than a hand list.

    A hand-built Namespace was the first version of this, and it was missing
    subsample, start_cam, end_cam, rescale_units, scene_bounds_xxyyzz and
    skip_first_n_images. Scene raised on the first one, measure() died before
    writing anything, and the run directory was left holding upstream's own
    eval_metrics.json in a different schema -- which looked like a measured
    control and was not one. Going through ModelParams means the field set is
    whatever Scene actually reads, today and after the next change to it.
    """
    from argparse import ArgumentParser

    from arguments import ModelParams

    parser = ArgumentParser()
    lp = ModelParams(parser)
    args = parser.parse_args([
        "-s", str(source_path),
        "--model_path", str(model_path),
        "--images", "images",
        "--resolution", str(resolution),
        "--eval",
    ])
    return lp.extract(args)


def measure(ref_root: Path, source_path: Path, out_dir: Path,
            iteration: Optional[int] = None,
            train_wall_seconds: Optional[float] = None) -> dict:
    """Render a vanilla run through the campaign harness and emit our schema."""
    import torch
    from argparse import ArgumentParser

    from gaussian_renderer import render
    from metrics import readImages
    from render_uw import render_set
    from scene import GaussianModel, Scene
    from utils.metrics_conventions import aggregate_images, evaluate_pair
    from utils.render_profile import profile_rendering
    from deepseecolor.models import AttenuateNetV3, BackscatterNetV2
    from lpipsPyTorch import lpips
    from utils.loss_utils import ssim

    it = iteration or find_iteration(ref_root)
    if it is None:
        raise SystemExit(
            f"no iteration in {ref_root} has a point cloud AND both medium nets. "
            f"A vanilla run writes attenuate_<it>.pth and backscatter_<it>.pth "
            f"beside point_cloud/iteration_<it>/; without them the image "
            f"formation model cannot be applied and only geometry is measurable."
        )
    print(f"[SS] {ref_root.name}: iteration {it}")

    out_dir.mkdir(parents=True, exist_ok=True)

    gaussians = GaussianModel(0)
    scene = Scene(_model_params(str(source_path), str(ref_root), -1),
                  gaussians, load_iteration=it, shuffle=False)

    # Their medium model, loaded into the classes it was trained with. Both
    # are inherited from the upstream fork, so this is their model in their
    # code -- only the harness around it is ours.
    at_model = AttenuateNetV3(scale=5.0).cuda()
    bs_model = BackscatterNetV2(use_residual=False, scale=5.0).cuda()
    at_model.load_state_dict(torch.load(ref_root / f"attenuate_{it}.pth"))
    bs_model.load_state_dict(torch.load(ref_root / f"backscatter_{it}.pth"))
    at_model.eval()
    bs_model.eval()

    # Same reasoning as _model_params: whatever render() reads, from the real
    # parser, rather than a hand list that goes stale the next time a field
    # is added.
    from arguments import PipelineParams
    _pp = ArgumentParser()
    pipe = PipelineParams(_pp).extract(_pp.parse_args([]))
    bg = torch.zeros(3, device="cuda")

    from utils.metrics_conventions import convention_note

    gt_dir = source_path / "images"
    use_jpeg = not list(gt_dir.glob("*.png"))
    container = "jpeg" if use_jpeg else "png"
    lpips_net = "vgg"

    # Both splits, the same way train.py does it for every other cell: render
    # to disk through the inherited render_set, read the 8-bit files back, and
    # score them. Train is kept because A0 reports it and a control that
    # reports less than the thing it controls for is harder to compare.
    split_blocks: dict[str, dict] = {}
    for split_name, cams_for in (("train", scene.getTrainCameras()),
                                 ("test", scene.getTestCameras())):
        with torch.no_grad():
            render_set(out_dir, split_name, it, cams_for, gaussians, pipe, bg,
                       True, False, False, None, bs_model, at_model,
                       save_as_jpeg=use_jpeg)
        image_dir = out_dir / split_name / "with_water"
        records = []
        fnames = [f.name for f in sorted(image_dir.iterdir()) if f.is_file()]
        renders, gts, names = readImages(str(image_dir), str(gt_dir), fnames)
        for i in range(len(renders)):
            rec = evaluate_pair(renders[i], gts[i], ssim, lpips, lpips_net=lpips_net)
            rec["image"] = names[i]
            records.append(rec)
        agg = aggregate_images(records)
        # Identical to train.py's block, aliases included: "PSNR" maps to the
        # POOLED figure because that is what upstream's code computed here.
        split_blocks[split_name.capitalize()] = {
            **agg,
            "SSIM": agg["ssim"],
            "PSNR": agg["psnr_pooled"],
            "LPIPS": agg["lpips"],
            "per_image": records,
        }
    agg = split_blocks["Test"]

    with torch.no_grad():
        prof = profile_rendering(render, scene.getTestCameras(), gaussians, pipe, bg)

    n = int(gaussians.get_xyz.shape[0])

    # SS has no diagnostics.csv: that instrument is this repository's (CD-12)
    # and upstream does not carry it, so there is no trajectory to record.
    # But the FINAL medium state is fully recoverable from the .pth files, and
    # writing it as one row in the same schema lets medium_collapse read the
    # reference's beta beside A0's rather than skipping the cell. One row,
    # labelled as such -- an absent trajectory is reported as absent, not
    # faked from a single point.
    from utils.diagnostics import DiagnosticLogger
    diag = DiagnosticLogger(out_dir, interval=1)
    diag.log(iteration=it, event="final", n_primitives=n,
             bs_model=bs_model, at_model=at_model,
             note="SS reference: final state only; upstream carries no "
                  "per-iteration diagnostics")
    diag.close()

    ply = ref_root / "point_cloud" / f"iteration_{it}" / "point_cloud.ply"
    artifact_bytes = ply.stat().st_size
    for extra in (f"attenuate_{it}.pth", f"backscatter_{it}.pth", f"bg_{it}.pth"):
        p = ref_root / extra
        if p.exists():
            artifact_bytes += p.stat().st_size

    results = {
        # Exactly train.py's key set -- see A0_TOP_KEYS / A0_COST_KEYS. Nothing
        # SS-specific lives here; it goes to reference.json beside this file.
        "container": container,
        "lpips_backbone": lpips_net,
        "masking": "none",
        "conventions": convention_note(lpips_net, container),
        "cost": {
            "iterations": int(it),
            # Upstream's loop has the same `continue` past the counter that
            # gives A0 ~43 000 optimizer steps for 30 000 iterations (D-8); the
            # exact figure is not recoverable from its artifacts, so absent
            # rather than assumed equal.
            "effective_optimizer_steps": None,
            # Subprocess clock when training preceded this measurement in the
            # same invocation; None when re-measuring an existing model. Its
            # span differs from A0's and is described in reference.json.
            "train_wall_seconds": train_wall_seconds,
            "n_primitives_final": n,
            "population_collapsed": False,
            **prof,
        },
        **split_blocks,
    }
    assert tuple(results) == A0_TOP_KEYS, tuple(results)
    assert set(results["cost"]) == set(A0_COST_KEYS), sorted(results["cost"])
    (out_dir / "eval_metrics.json").write_text(json.dumps(results, indent=2),
                                               encoding="utf-8")

    # Everything SS-specific, in a sidecar, so the metrics file's schema is
    # identical to A0's and the provenance is still on disk beside it.
    provenance = {
        "cell": "SS",
        "source": str(ref_root),
        "iteration": int(it),
        "what": (
            "Vanilla SeaSplat, unmodified. Rendered with the upstream render_set "
            "and scored with this campaign's metric harness, so the convention "
            "matches A0 on both sides. Metrics come from 8-bit files written and "
            "read back, reproducing the inherited evaluation quirk rather than "
            "correcting it on one side only."
        ),
        "train_wall_span": (
            "whole upstream train.py process: dataset load + training + final "
            "renders + upstream's own metric scoring. A0's figure excludes the "
            "first and last, so this is a superset by roughly 35 s (~2%)."
            if train_wall_seconds is not None else
            "not measured: this model was re-measured, not trained, in this "
            "invocation"
        ),
        "effective_optimizer_steps": (
            "not recoverable from upstream's artifacts; its loop bypasses the "
            "counter the same way (D-8) but the count is not logged"
        ),
        "diagnostics": (
            "final state only, one row; upstream carries no per-iteration "
            "diagnostics (CD-12 is this repository's instrument)"
        ),
    }
    (out_dir / "reference.json").write_text(json.dumps(provenance, indent=2),
                                            encoding="utf-8")

    size = {
        "artifact_dir": str(ref_root),
        "num_primitives": n,
        "total_bytes": artifact_bytes,
        "total_mb": round(artifact_bytes / 1024 / 1024, 4),
        "bytes_per_primitive": round(artifact_bytes / max(n, 1), 4),
        "_note": ("Vanilla stores a full-precision PLY plus the medium nets; it "
                  "writes no compact artifact, so this is not comparable with "
                  "A0's compressed_* figure without saying so."),
    }
    (out_dir / "model_size.json").write_text(json.dumps(size, indent=2), encoding="utf-8")

    print(f"[SS] PSNR {agg['psnr_pooled']:.4f} pooled / "
          f"{agg['psnr_per_channel']:.4f} per-channel, LPIPS {agg['lpips']:.4f}, "
          f"{n:,} primitives")
    print(f"[SS] wrote {out_dir/'eval_metrics.json'}")
    return results


def check_margin(output_root: Path) -> int:
    """Compare SS against A0 per scene, against the pre-specified margin."""
    margins = load_margins()
    if not margins:
        print("no equivalence_margin in configs/cells.json under cells.SS.")
        print("Set it BEFORE S0 runs -- a margin chosen afterwards is not a")
        print("pre-specified margin and cannot license the word 'equivalent'.")
        return 1

    print(f"equivalence margin (pre-registered): {margins}")
    print("Compared as scene means over repeats, NOT seed by seed: vanilla's")
    print("seed does not reach its GPU draws, so s0/s1/s2 are repeat indices")
    print("on both sides and a paired comparison would be false precision.\n")

    def collect(cell: str) -> list[dict]:
        out = []
        for p in sorted(output_root.glob(f"{cell}/*/s*/eval_metrics.json")):
            try:
                e = json.loads(p.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            e["_scene"] = p.parent.parent.name
            out.append(e)
        return out

    ss_by_scene = aggregate_by_scene(collect("SS"))
    a0_by_scene = aggregate_by_scene(collect("A0"))
    ss_n = {s: 0 for s in ss_by_scene}
    for p in output_root.glob("SS/*/s*/eval_metrics.json"):
        ss_n[p.parent.parent.name] = ss_n.get(p.parent.parent.name, 0) + 1

    if not ss_by_scene:
        print("no SS runs found. S0 has not produced results yet.")
        return 0

    for scene in sorted(ss_by_scene):
        if scene not in a0_by_scene:
            print(f"{scene}: no A0 runs to compare against\n")
            continue
        v = margin_verdict(ss_by_scene[scene], a0_by_scene[scene], margins)
        print(f"{scene}  (SS n={ss_n.get(scene, 0)}): {v['verdict']}")
        for metric in ("psnr_pooled", "lpips", "n_primitives_final"):
            e = v.get(metric, {})
            mark = {True: "within", False: "OUTSIDE", None: "n/a"}[e.get("within")]
            print(f"    {metric:<20} {mark:>8}  diff={e.get('diff')}  "
                  f"allowed=±{e.get('allowed')}")
        print()
    print("A verdict of WITHIN MARGIN supports 'A0 is equivalent to SeaSplat to")
    print("within the stated margin'. It does not support 'A0 reproduces")
    print("SeaSplat', which is a stronger claim than any finite sample licenses.")
    return 0


def find_written_model(search_roots: list[Path], after: float) -> Optional[Path]:
    """Locate the model a vanilla run actually wrote.

    Upstream **ignores `--model_path`** and derives its own from the source
    path and the date -- observed as `<source>/experiments/<MMDDYYYY>/test`.
    The flag is accepted and then overwritten, so there is nothing to pass that
    would place the output where we asked.

    That also means the destination is scoped by *day*, not by run: two seeds
    of the same scene on the same date write to the same directory, and the
    second silently overwrites the first. So a candidate is only accepted if
    its point cloud was written after this run started -- otherwise a failed
    run would happily measure its predecessor's model and report it as its own.
    """
    best: Optional[tuple[float, Path]] = None
    for root in search_roots:
        if not root.exists():
            continue
        for ply in root.rglob("point_cloud/iteration_*/point_cloud.ply"):
            model_dir = ply.parent.parent.parent
            it = ply.parent.name.split("_")[-1]
            if not (model_dir / f"attenuate_{it}.pth").exists():
                continue
            if not (model_dir / f"backscatter_{it}.pth").exists():
                continue
            mtime = ply.stat().st_mtime
            if mtime < after:
                continue
            if best is None or mtime > best[0]:
                best = (mtime, model_dir)
    return best[1] if best else None


def vanilla_command(scene_dir: Path, out: Path, seed: int,
                    iterations: int = 30000,
                    seathru_from_iter: int = 10000) -> list[str]:
    """The upstream command line, built in one place so it can be asserted on."""
    return [
        "python", "train.py",
        "-s", str(scene_dir),
        "--model_path", str(out),
        "--iterations", str(iterations),
        "--do_seathru",
        "--seathru_from_iter", str(seathru_from_iter),
        "--eval", "--seed", str(seed),
        # Upstream saves at 1k/7k/15k/30k and checkpoints at four more. Only
        # the final model is measured, and the intermediates are ~900 MB per
        # run of Drive for nothing (configs/cells.json _storage_note). These
        # are ordinary 3DGS flags upstream accepts, so no code is touched.
        # Upstream appends --iterations to both lists regardless, so 30000
        # appears twice; harmless. The 30000 checkpoint itself cannot be
        # suppressed from the CLI and is pruned after relocation.
        "--save_iterations", str(iterations),
        "--checkpoint_iterations", str(iterations),
    ]


def prune_intermediates(model_dir: Path, keep_iteration: int) -> list[str]:
    """Drop everything but the final model.

    --save_iterations and --checkpoint_iterations remove the intermediate
    saves, but upstream appends --iterations to the checkpoint list
    unconditionally, so chkpnt30000.pth -- the full optimiser state, ~300 MB
    at 4M primitives -- is written regardless. Interrupted runs are restarted
    rather than resumed (CD-18), so it has no use. Any intermediate that
    slipped through a different upstream default is removed on the same
    grounds. Returned so the caller can log what went.
    """
    import shutil

    removed: list[str] = []
    pc = model_dir / "point_cloud"
    if pc.is_dir():
        for d in pc.iterdir():
            if d.is_dir() and d.name != f"iteration_{keep_iteration}":
                shutil.rmtree(d, ignore_errors=True)
                removed.append(f"point_cloud/{d.name}")
    for p in model_dir.iterdir():
        if not p.is_file():
            continue
        if p.name.startswith("chkpnt"):
            p.unlink()
            removed.append(p.name)
            continue
        for prefix in ("attenuate_", "backscatter_", "bg_"):
            if p.name.startswith(prefix) and p.name != f"{prefix}{keep_iteration}.pth":
                p.unlink()
                removed.append(p.name)
    if removed:
        shown = ", ".join(removed[:8]) + (" ..." if len(removed) > 8 else "")
        print(f"[SS] pruned {len(removed)} intermediate artifact(s): {shown}")
    return removed


def train_vanilla(ref_repo: Path, scene_dir: Path, out: Path, seed: int,
                  iterations: int = 30000,
                  seathru_from_iter: int = 10000) -> tuple[int, float]:
    """Run the upstream trainer, in the upstream checkout, unmodified.

    Invoked as a subprocess in `ref_repo` rather than imported, because that is
    the only way to be sure the code executing is theirs: an import would run
    their module inside this process, against whatever this repository has
    already put on `sys.path`, and the first name collision would silently
    substitute our implementation for theirs.

    `--model_path` is passed and ignored -- see `find_written_model`. The output
    is located afterwards and moved to `out`, so the model lands on Drive with
    the run that produced it instead of in ephemeral storage under a
    date-scoped name that the next seed would overwrite.
    """
    import shutil
    import subprocess
    import time

    started = time.time()
    # The three flags `configs/cells.json` names as silent no-ops upstream, and
    # they are named there because each one quietly produces a different
    # experiment rather than an error:
    #
    #   --do_seathru        default False. Without it the medium model never
    #                       activates and the reference is plain 3DGS on
    #                       underwater images -- which is not SeaSplat, and
    #                       which cost about 11 dB when this was first run.
    #   --seathru_from_iter default 9_000_000, i.e. past the end of training,
    #                       so the model is nominally enabled and never runs.
    #   --eval              default False. The test set is empty, training uses
    #                       every frame, and the reported metrics are inflated.
    #
    # The configuration layer exists to stop exactly this, and hand-building a
    # command here walked around it once already.
    cmd = vanilla_command(scene_dir, out, seed, iterations, seathru_from_iter)
    print(f"[SS] training vanilla in {ref_repo}\n     {' '.join(cmd)}", flush=True)
    rc = subprocess.run(cmd, cwd=str(ref_repo)).returncode
    # The subprocess clock. A0's train_wall_seconds is read inside train.py,
    # from just before the loop to just after the final renders -- so it
    # excludes dataset loading and metric scoring. This figure is the whole
    # process and therefore a superset by those two, roughly 35 s on a
    # 1700 s run. Reported with its span named, never silently as if equal.
    elapsed = round(time.time() - started, 1)
    if rc != 0:
        return rc, elapsed

    written = find_written_model([out, scene_dir, ref_repo], started)
    if written is None:
        print(f"[SS] training reported success but no complete model was written "
              f"after {started:.0f}. Searched {out}, {scene_dir}, {ref_repo}.")
        return 1, elapsed

    if written.resolve() == out.resolve():
        return 0, elapsed

    print(f"[SS] upstream wrote to {written} (it overrides --model_path);"
          f"\n     relocating to {out}", flush=True)
    out.parent.mkdir(parents=True, exist_ok=True)
    for item in written.iterdir():
        dest = out / item.name
        if dest.exists():
            shutil.rmtree(dest) if dest.is_dir() else dest.unlink()
        shutil.move(str(item), str(dest))
    shutil.rmtree(written, ignore_errors=True)
    prune_intermediates(out, iterations)
    return 0, elapsed


def main() -> int:
    ap = argparse.ArgumentParser(
        description="measure vanilla SeaSplat with the campaign harness")
    ap.add_argument("--ref_root", help="a vanilla SeaSplat output directory")
    ap.add_argument("--source_path", help="the scene's data directory")
    ap.add_argument("--out", help="campaign run dir, e.g. .../runs/SS/Curasao/s0")
    ap.add_argument("--iteration", type=int, default=None)
    ap.add_argument("--check_margin", action="store_true")
    ap.add_argument("--output_root", help="campaign root, for --check_margin")
    ap.add_argument("--ref_repo", default=None,
                    help="unpatched upstream checkout; train there first, then "
                         "measure. This is what the worker passes for S0.")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--iterations", type=int, default=30000)
    args = ap.parse_args()

    if args.check_margin:
        if not args.output_root:
            raise SystemExit("--check_margin needs --output_root")
        return check_margin(Path(args.output_root))

    missing = [f for f in ("ref_root", "source_path", "out") if not getattr(args, f)]
    if missing:
        raise SystemExit(f"missing required argument(s): {', '.join(missing)}")

    if args.ref_repo:
        repo = Path(args.ref_repo)
        if not (repo / "train.py").exists():
            raise SystemExit(
                f"no train.py in {repo}. S0 needs the UNPATCHED upstream "
                f"checkout that 00_setup stages at /content/seasplat_vanilla. "
                f"Do not point this at /content/seasplat_ref: that tree is "
                f"patched by tools.instrument_reference and is disqualified "
                f"from producing SS numbers by its own docstring."
            )
        rc, wall = train_vanilla(repo, Path(args.source_path), Path(args.ref_root),
                                 args.seed, args.iterations)
        if rc != 0:
            raise SystemExit(f"vanilla training failed (exit {rc})")
    else:
        wall = None

    measure(Path(args.ref_root), Path(args.source_path), Path(args.out),
            args.iteration, train_wall_seconds=wall)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
