"""Generate the Chapter IV plot figures from the committed campaign bundle.

    python figures/make_chapter4_figures.py

Produces the six figures marked PLOT or DERIVE+PLOT in
`new-revisited-writing/chapter-04-assets.md`. Everything here reads from
`analysis/campaign-2026-09/`, which is the unpacked campaign bundle; nothing
needs Colab or the Drive checkpoints. The seven figures marked RENDER do need
those and are not produced here.

Each figure is written twice: PDF for the thesis document, where it stays
vector and its text stays selectable, and PNG at 300 dpi for drafts and
slides.

Figures produced
  4.1   resolvable effect size against observed effect size
  4.3   learned attenuation spectra per scene
  4.9   operating points per scene
  4.10  attenuation trajectory through the simplification events
  4.11  dispersion ratio by outcome stratum
  4.12  fraction removed against attenuation loss

Conventions, fixed here so every figure agrees: scenes always appear in the
same order and the same colour; the physical channel colours red, green and
blue are used only for the three medium channels and never for anything else;
collapsed runs are marked with the accent colour used nowhere else.
"""

from __future__ import annotations

import csv
import json
import math
import statistics as st
import time
from pathlib import Path
from typing import Any, Optional

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

ROOT: Path = Path(__file__).resolve().parent.parent
DATA: Path = ROOT / "analysis" / "campaign-2026-09"
OUT: Path = ROOT / "figures" / "chapter4"

# Directory names as the data carries them, and the names the thesis prints.
SCENES: dict[str, str] = {
    "Curasao": "Curaçao",
    "IUI3-RedSea": "IUI3 Red Sea",
    "JapaneseGradens-RedSea": "Japanese Gardens",
    "Panama": "Panama",
}
SCENE_COLOR: dict[str, str] = {
    "Curasao": "#1F6FB4",
    "IUI3-RedSea": "#C8462E",
    "JapaneseGradens-RedSea": "#1F7A66",
    "Panama": "#7A5CA8",
}
CHANNEL_COLOR: dict[str, str] = {"r": "#C0392B", "g": "#1E8449", "b": "#2471A3"}
ACCENT: str = "#C8462E"       # collapsed / refuted / attention
NEUTRAL: str = "#4A5C5B"
GRID: str = "#D8E0DF"

CELLS: list[str] = ["SS", "A0", "A0D", "A1", "A2", "A3", "A4", "A5", "A6", "A7"]

# The unmodified reference is drawn hollow wherever it appears, so a reader
# never mistakes it for a configuration under test. It has no per-iteration
# diagnostics -- one final row per run -- and no stored-size accounting, so
# it is absent from the three figures that need those and marked as a final
# state where only its endpoint exists.
REF_STYLE: dict[str, Any] = {"facecolors": "none", "linewidths": 1.4}


def style() -> None:
    plt.rcParams.update({
        "figure.dpi": 120,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "DejaVu Sans"],
        "font.size": 9,
        "axes.titlesize": 10,
        "axes.labelsize": 9,
        "axes.edgecolor": NEUTRAL,
        "axes.linewidth": 0.8,
        "axes.grid": True,
        "grid.color": GRID,
        "grid.linewidth": 0.6,
        "legend.frameon": False,
        "legend.fontsize": 8,
        "xtick.color": NEUTRAL,
        "ytick.color": NEUTRAL,
        "text.color": "#10201F",
        "axes.labelcolor": "#10201F",
    })


def save(fig: plt.Figure, name: str) -> None:
    """Write both formats, retrying briefly.

    On Windows a just-written file is occasionally still held when the next
    write lands on it, and the save fails with EINVAL. Retrying clears it; the
    alternative is a run that dies two figures from the end.
    """
    OUT.mkdir(parents=True, exist_ok=True)
    for ext in ("pdf", "png"):
        target = OUT / f"{name}.{ext}"
        for attempt in range(5):
            try:
                fig.savefig(target)
                break
            except OSError:
                if attempt == 4:
                    raise
                time.sleep(0.4)
    plt.close(fig)
    print(f"  {name}.pdf / .png")


# ── data access ──────────────────────────────────────────────────────────

def runs() -> list[dict[str, str]]:
    return list(csv.DictReader(open(DATA / "results_runs.csv", encoding="utf-8")))


def by_scene() -> list[dict[str, str]]:
    return list(csv.DictReader(open(DATA / "results_by_scene.csv", encoding="utf-8")))


def collapse() -> dict[str, Any]:
    return json.loads((DATA / "medium_collapse.json").read_text(encoding="utf-8"))


def noise_floor() -> dict[str, Any]:
    return json.loads((DATA / "_noise_floor.json").read_text(encoding="utf-8"))


def mean_of(rows: list[dict[str, str]], cell: str, scene: str, metric: str) -> float | None:
    hit = [r for r in rows if r["cell"] == cell and r["scene"] == scene
           and r["metric"] == metric]
    return float(hit[0]["mean"]) if hit else None


def sd_of(rows: list[dict[str, str]], cell: str, scene: str, metric: str) -> float | None:
    hit = [r for r in rows if r["cell"] == cell and r["scene"] == scene
           and r["metric"] == metric]
    return float(hit[0]["sd"]) if hit else None


def diagnostics(cell: str, scene: str, seed: int) -> list[dict[str, str]]:
    path = DATA / "diagnostics" / f"{cell}_{scene}_s{seed}.csv"
    if not path.is_file():
        return []
    return list(csv.DictReader(open(path, encoding="utf-8")))


def is_collapsed(mc: dict[str, Any], cell: str, scene: str, seed: int) -> bool:
    return bool(mc[f"{cell}/{scene}/s{seed}"]["collapsed"])


# ── 4.1  resolvable effect size against observed effect size ─────────────

def figure_4_1() -> None:
    """Why PSNR interactions are undetermined, shown rather than asserted."""
    nf = noise_floor()
    rows = by_scene()
    fig, ax = plt.subplots(figsize=(6.6, 3.4))
    xs = range(len(SCENES))

    for i, (key, label) in enumerate(SCENES.items()):
        sd = nf[key]["psnr"]
        # Resolution thresholds: 2 SE, with SE scaled by the contrast's width.
        main = 2 * sd * math.sqrt(2 / 3)
        two = 2 * sd * 2 / math.sqrt(3)
        three = 2 * sd * 2 * math.sqrt(2) / math.sqrt(3)
        ax.plot([i - 0.28, i + 0.28], [main, main], color=NEUTRAL, lw=2)
        ax.plot([i - 0.28, i + 0.28], [two, two], color=NEUTRAL, lw=2, ls="--")
        ax.plot([i - 0.28, i + 0.28], [three, three], color=NEUTRAL, lw=2, ls=":")
        # Observed absolute main effects of the three mechanisms.
        base = mean_of(rows, "A0", key, "psnr_pooled")
        for cell in ("A1", "A2", "A3"):
            val = mean_of(rows, cell, key, "psnr_pooled")
            if base is not None and val is not None:
                ax.scatter([i], [abs(val - base)], s=26, color=SCENE_COLOR[key],
                           zorder=3, alpha=0.85)
        # The reference against the same thresholds: its disagreement with the
        # baseline is smaller than any effect the design can resolve.
        ref = mean_of(rows, "SS", key, "psnr_pooled")
        if base is not None and ref is not None:
            ax.scatter([i], [abs(ref - base)], s=44, marker="o", zorder=4,
                       edgecolors=SCENE_COLOR[key], **REF_STYLE)

    ax.set_xticks(list(xs))
    ax.set_xticklabels(SCENES.values())
    ax.set_ylabel("PSNR effect magnitude (dB)")
    ax.set_title("Smallest resolvable effect, by contrast width, against observed main effects")
    handles = [
        Line2D([], [], color=NEUTRAL, lw=2, label="resolvable main effect (2 SE)"),
        Line2D([], [], color=NEUTRAL, lw=2, ls="--", label="resolvable two-way interaction"),
        Line2D([], [], color=NEUTRAL, lw=2, ls=":", label="resolvable three-way interaction"),
        Line2D([], [], marker="o", ls="", color=NEUTRAL, label="observed |main effect|, M1/M2/M3"),
        Line2D([], [], marker="o", ls="", markerfacecolor="none",
               markeredgecolor=NEUTRAL, label="|reference - baseline|"),
    ]
    ax.legend(handles=handles, loc="upper left", ncol=2)
    ax.set_ylim(bottom=0)
    save(fig, "figure-4-01-resolution")


# ── 4.3  learned attenuation spectra ─────────────────────────────────────

def figure_4_3() -> None:
    """The ordering check: red should attenuate fastest."""
    rs = runs()
    fig, axes = plt.subplots(1, 4, figsize=(8.4, 2.9), sharey=True)
    width = 0.36

    for ax, (key, label) in zip(axes, SCENES.items()):
        for off, cell in ((-width / 2, "A0"), (width / 2, "SS")):
            sub = [r for r in rs if r["cell"] == cell and r["scene"] == key]
            for j, ch in enumerate("rgb"):
                vals = [float(r[f"beta_att_{ch}"]) for r in sub]
                m = st.mean(vals)
                sd = st.stdev(vals) if len(vals) > 1 else 0.0
                ax.bar(j + off, m, width, yerr=sd, capsize=2,
                       color=CHANNEL_COLOR[ch],
                       alpha=1.0 if cell == "A0" else 0.45,
                       edgecolor=CHANNEL_COLOR[ch], linewidth=0.8,
                       error_kw={"elinewidth": 0.8, "ecolor": NEUTRAL})
        ax.set_xticks([0, 1, 2])
        ax.set_xticklabels(["R", "G", "B"])
        ax.set_title(label)
        ax.grid(axis="x", visible=False)
        # Mark the scene whose ordering is not the physical one.
        a0 = [r for r in rs if r["cell"] == "A0" and r["scene"] == key]
        red = st.mean(float(r["beta_att_r"]) for r in a0)
        blue = st.mean(float(r["beta_att_b"]) for r in a0)
        if red < blue:
            ax.set_facecolor("#FBEFEC")
            ax.text(0.5, 0.94, "ordering not physical", transform=ax.transAxes,
                    ha="center", va="top", fontsize=7.5, color=ACCENT)

    axes[0].set_ylabel(r"$\beta_{att}$  (per normalised depth)")
    handles = [
        Line2D([], [], marker="s", ls="", color=NEUTRAL, alpha=1.0, label="baseline (A0)"),
        Line2D([], [], marker="s", ls="", color=NEUTRAL, alpha=0.45, label="reference (SS)"),
    ]
    axes[-1].legend(handles=handles, loc="upper right")
    fig.suptitle("Fitted attenuation per channel; physical water gives R > G > B",
                 y=1.04, fontsize=10)
    save(fig, "figure-4-03-attenuation-spectra")


# ── 4.9  operating points ────────────────────────────────────────────────

def figure_4_9() -> None:
    """Nine cells per scene; a description, not a rate-distortion curve."""
    rows = by_scene()
    fig, axes = plt.subplots(2, 4, figsize=(9.2, 5.0))
    trained = [c for c in CELLS if c != "SS"]

    for col, (key, label) in enumerate(SCENES.items()):
        for row, (xmetric, xlabel) in enumerate(
            (("n_primitives_final", "primitives"), ("total_mb", "stored size (MB)"))
        ):
            ax = axes[row][col]
            for cell in trained:
                x = mean_of(rows, cell, key, xmetric)
                y = mean_of(rows, cell, key, "lpips")
                if x is None or y is None:
                    continue
                ax.scatter([x], [y], s=30, color=SCENE_COLOR[key], zorder=3,
                           alpha=0.9 if cell in ("A0", "A1", "A4", "A7") else 0.55)
                ax.annotate(cell, (x, y), textcoords="offset points",
                            xytext=(4, 3), fontsize=7, color=NEUTRAL)
            # The reference, where it can be placed. It has no stored-size
            # accounting, so it appears on the count axis only, and it is not
            # part of the front: it is what the front is measured against.
            xs = mean_of(rows, "SS", key, xmetric)
            ys = mean_of(rows, "SS", key, "lpips")
            if xs is not None and ys is not None:
                ax.scatter([xs], [ys], s=52, marker="o", zorder=4,
                           edgecolors=SCENE_COLOR[key], **REF_STYLE)
                ax.annotate("SS", (xs, ys), textcoords="offset points",
                            xytext=(5, -9), fontsize=7, color=NEUTRAL)
            ax.set_xscale("log")
            ax.grid(which="both", axis="x")
            if row == 0:
                ax.set_title(label)
            if col == 0:
                ax.set_ylabel("LPIPS  (lower is better)")
            ax.set_xlabel(xlabel)

    fig.suptitle("Operating points per scene — nine configurations, one point each", y=1.0)
    fig.tight_layout()
    save(fig, "figure-4-09-operating-points")


# ── 4.10  attenuation trajectory through the events ──────────────────────

def figure_4_10(cell: str = "A2", scene: str = "Curasao") -> None:
    """One collapsed and one intact repeat of the same cell and scene."""
    mc = collapse()
    seeds = [s for s in (0, 1, 2) if diagnostics(cell, scene, s)]
    collapsed = [s for s in seeds if is_collapsed(mc, cell, scene, s)]
    intact = [s for s in seeds if not is_collapsed(mc, cell, scene, s)]
    if not collapsed or not intact:
        print(f"  skipped 4.10: {cell}/{scene} lacks both strata")
        return

    pick = [(intact[0], "medium intact"), (collapsed[0], "channel lost")]
    fig, axes = plt.subplots(1, 2, figsize=(8.4, 3.2), sharey=True)

    for ax, (seed, title) in zip(axes, pick):
        rows = [r for r in diagnostics(cell, scene, seed) if r.get("beta_att_r")]
        it = [int(r["iteration"]) for r in rows]
        for ch in "rgb":
            ax.plot(it, [float(r[f"beta_att_{ch}"]) for r in rows],
                    color=CHANNEL_COLOR[ch], lw=1.3, label=ch.upper())
        for boundary in (15000, 20000):
            ax.axvline(boundary, color=NEUTRAL, lw=0.9, ls="--")
        ax.axhline(0.0, color=ACCENT, lw=0.9, ls=":")
        ax.set_xlabel("iteration")
        ax.set_title(f"{SCENES[scene]} · {cell} · repeat {seed} — {title}")
    axes[0].set_ylabel(r"$\beta_{att}$")
    axes[0].legend(title="channel", loc="upper left")
    axes[1].annotate("simplification events", xy=(15000, axes[1].get_ylim()[1]),
                     xytext=(16200, axes[1].get_ylim()[1] * 0.92),
                     fontsize=7.5, color=NEUTRAL)
    fig.suptitle("Attenuation through the two simplification events, all three channels", y=1.02)
    save(fig, "figure-4-10-attenuation-trajectory")


# ── 4.11  dispersion ratio by outcome ────────────────────────────────────

def figure_4_11() -> None:
    """The refutation, shown as the overlap it is."""
    mc = collapse()
    no_m1_c: list[float] = []
    no_m1_i: list[float] = []
    m1_all: list[tuple[float, bool]] = []

    for key, rec in mc.items():
        cell, scene, seed = key.split("/")
        ratios = rec.get("zr_cv_ratio") or []
        if not ratios:
            continue
        first = ratios[0]["ratio"]
        collapsed = bool(rec["collapsed"])
        if cell in ("A2", "A6"):
            (no_m1_c if collapsed else no_m1_i).append(first)
        elif cell in ("A4", "A7"):
            m1_all.append((max(r["ratio"] for r in ratios), collapsed))

    fig, ax = plt.subplots(figsize=(6.6, 3.2))
    rng = [0.12, -0.12]
    for vals, y, color, label in (
        (no_m1_i, 1.0, NEUTRAL, f"intact (n={len(no_m1_i)})"),
        (no_m1_c, 0.6, ACCENT, f"channel lost (n={len(no_m1_c)})"),
    ):
        for i, v in enumerate(vals):
            ax.scatter([v], [y + rng[i % 2] * 0.35], s=34, color=color,
                       alpha=0.85, zorder=3)
        if vals:
            ax.plot([st.median(vals)] * 2, [y - 0.16, y + 0.16], color=color, lw=2.4)
    for v, collapsed in m1_all:
        ax.scatter([v], [0.15], s=26, color="#1F7A66", alpha=0.7, zorder=3)

    ax.axvline(1.0, color=NEUTRAL, lw=0.8, ls="--")
    ax.set_yticks([1.0, 0.6, 0.15])
    ax.set_yticklabels(["intact", "channel lost", "with M1\n(largest ratio)"])
    ax.set_xlabel("cross-frame depth-range dispersion ratio at the first event")
    ax.set_title("The registered predictor does not separate the two outcomes")
    ax.text(0.99, 0.06, "U = 79 of 135 · AUC 0.585 · exact one-sided p = 0.26",
            transform=ax.transAxes, ha="right", fontsize=8, color=ACCENT)
    ax.set_ylim(-0.1, 1.35)
    ax.grid(axis="y", visible=False)
    save(fig, "figure-4-11-dispersion-strata")


# ── 4.12  what actually separates the outcomes ───────────────────────────

def figure_4_12() -> None:
    """Two panels. The cut drives the loss; the level reached drives the outcome.

    Pooling the two simplification events in one panel misleads: the first
    removes 86-95% of the population and the second 16-36%, and four runs with
    dense initialisation lose 52-73% of their attenuation at the second event
    without losing a channel. Fractional loss is therefore not what decides the
    outcome, and panel (b) shows what does.
    """
    mc = collapse()
    per_event: list[dict[str, Any]] = []
    per_run: list[tuple[float, bool]] = []

    for cell in ("A2", "A6", "A4", "A7"):
        for scene in SCENES:
            for seed in (0, 1, 2):
                rows = diagnostics(cell, scene, seed)
                if not rows:
                    continue
                idx = {(int(r["iteration"]), r["event"]): r for r in rows}
                collapsed = is_collapsed(mc, cell, scene, seed)
                floors: list[float] = []
                for it0, it1 in ((15000, 15001), (20000, 20001)):
                    pre = idx.get((it0, "pre_simp"))
                    post = idx.get((it0, "post_simp"))
                    rw = idx.get((it1, "rewarm_end"))
                    if not (pre and post and rw and pre.get("beta_att_r")):
                        continue
                    beta = lambda r: [float(r[f"beta_att_{c}"]) for c in "rgb"]
                    b_pre, b_rw = st.mean(beta(pre)), st.mean(beta(rw))
                    if b_pre <= 0:
                        continue
                    per_event.append({
                        "removed": 1 - int(post["n_primitives"]) / int(pre["n_primitives"]),
                        "loss": 1 - b_rw / b_pre,
                        "event": it0,
                        "collapsed": collapsed,
                        "m1": cell in ("A4", "A7"),
                    })
                    floors.append(min(beta(rw)))
                if floors:
                    per_run.append((min(floors), collapsed))

    fig, (ax, bx) = plt.subplots(1, 2, figsize=(9.0, 3.6),
                                 gridspec_kw={"width_ratios": [1.35, 1]})

    for p in per_event:
        ax.scatter([100 * p["removed"]], [100 * p["loss"]], zorder=3, s=30,
                   color=ACCENT if p["collapsed"] else ("#1F7A66" if p["m1"] else NEUTRAL),
                   marker="^" if p["event"] == 20000 else "o",
                   alpha=0.85 if p["collapsed"] else 0.6)
    ax.set_xlabel("primitives removed at the event (%)")
    ax.set_ylabel("attenuation lost in the following"
                  " medium-only steps (%)")
    ax.set_title("(a) the cut and the loss")
    ax.legend(handles=[
        Line2D([], [], marker="o", ls="", color=NEUTRAL, label="first event"),
        Line2D([], [], marker="^", ls="", color=NEUTRAL, label="second event"),
        Line2D([], [], marker="o", ls="", color=ACCENT, label="run lost a channel"),
        Line2D([], [], marker="^", ls="", color="#1F7A66", label="with dense initialisation"),
    ], loc="upper left", fontsize=7.5)

    for i, (floor, collapsed) in enumerate(per_run):
        bx.scatter([floor], [(0.72 if collapsed else 1.0) + (i % 3 - 1) * 0.045],
                   s=32, zorder=3, color=ACCENT if collapsed else NEUTRAL, alpha=0.8)
    bx.axvline(0.0, color=ACCENT, lw=1.0, ls=":")
    bx.set_yticks([1.0, 0.72])
    bx.set_yticklabels(["intact", "channel lost"])
    bx.set_ylim(0.5, 1.25)
    bx.set_xlabel("lowest channel $" + '\\beta_{att}' + "$ reached after a burst")
    bx.set_title("(b) the level reached")
    bx.grid(axis="y", visible=False)

    fig.suptitle("Fractional loss does not decide the outcome; the level reached does", y=1.06)
    fig.tight_layout()
    save(fig, "figure-4-12-removal-vs-loss")



# ── 4.15  main effects, with the resolution threshold ────────────────────

# What each anchor means, and what it therefore cannot be used for.
#
#   A0  the factorial contrast. A1 differs from A0 by exactly M1, so the
#       difference *is* the mechanism effect. This is the pre-registered
#       comparison and the one the main-effects tables report.
#   SS  the published reference. A1 - SS is not a mechanism effect: it
#       confounds M1 with everything separating the two implementations,
#       and A0 - SS is itself non-zero. It answers the other question a
#       reader has — where does each configuration stand against SeaSplat.
ANCHORS: dict[str, tuple[str, list[tuple[str, str]], str]] = {
    "A0": ("figure-4-15-main-effects-forest",
           [("A1", "M1 initialisation"), ("A2", "M2 simplification"),
            ("A3", "M3 quantisation"), ("SS", "reference (SS)")],
           "Main effects against the baseline, with two-standard-error intervals"),
    "SS": ("figure-4-15b-configurations-vs-reference",
           [("A0", "A0 no mechanism"), ("A1", "A1  M1"), ("A2", "A2  M2"),
            ("A3", "A3  M3"), ("A7", "A7  all three")],
           "Each configuration against the published reference (SS)"),
}


NULL_NOTE: dict[str, str] = {
    "A0": "Zero is A0 on that same row's scene, never a pooled or absolute zero: "
          "each scene is compared with A0 of that scene. The count panel is a "
          "ratio on a log axis, so its null is 1. The SS group is SS - A0, which "
          "is the equivalence claim of 4.2.1 drawn rather than tabulated.",
    "SS": "Zero is SS on that same row's scene. These are not mechanism effects: "
          "A0 already differs from SS, so a row here carries that difference plus "
          "whatever the mechanism does. For the effect of a mechanism alone, read "
          "Figure 4.15, where the null is A0. The count panel is a ratio, null 1.",
}


def figure_4_15(null_cell: str = "A0") -> None:
    """R1. Which effects clear two standard errors, at a glance.

    `null_cell` chooses what the zero line means — see ANCHORS above. It
    changes the question the figure answers, not merely its presentation.
    """
    name, mechs, title = ANCHORS[null_cell]
    rows = by_scene()
    metrics = [("psnr_pooled", "PSNR (dB)", False),
               ("lpips", "LPIPS", False),
               ("n_primitives_final", "primitive count (ratio)", True)]

    # One group of four scenes per row-block: the panel has to be tall enough
    # for the rotated group labels to sit beside their own rows without
    # colliding.
    fig, axes = plt.subplots(1, 3, figsize=(9.6, 1.25 * len(mechs) + 0.4))
    for ax, (metric, label, as_ratio) in zip(axes, metrics):
        y = 0.0
        ticks: list[float] = []
        names: list[str] = []
        for cell, mech in mechs:
            for key, scene in SCENES.items():
                base = mean_of(rows, null_cell, key, metric)
                val = mean_of(rows, cell, key, metric)
                sd_b = sd_of(rows, null_cell, key, metric)
                sd_v = sd_of(rows, cell, key, metric)
                if None in (base, val, sd_b, sd_v) or not base:
                    y -= 1.0
                    continue
                se = math.sqrt((sd_b ** 2 + sd_v ** 2) / 3)
                if as_ratio:
                    # A ratio's interval belongs in log space; an additive one
                    # can reach zero and disappears off a logarithmic axis.
                    eff = val / base
                    se_log = math.sqrt((sd_b / base) ** 2
                                       + (sd_v / val) ** 2) / math.sqrt(3)
                    lo, hi = eff * math.exp(-2 * se_log), eff * math.exp(2 * se_log)
                    null = 1.0
                else:
                    eff = val - base
                    lo, hi = eff - 2 * se, eff + 2 * se
                    null = 0.0
                resolved = (lo > null) or (hi < null)
                ax.plot([lo, hi], [y, y], color=SCENE_COLOR[key],
                        lw=1.6, alpha=0.9 if resolved else 0.35,
                        solid_capstyle="butt")
                ax.scatter([eff], [y], s=26, zorder=3, color=SCENE_COLOR[key],
                           alpha=1.0 if resolved else 0.4,
                           marker="o" if resolved else "x")
                ticks.append(y)
                names.append(scene)
                y -= 1.0
            y -= 0.7
        ax.axvline(1.0 if as_ratio else 0.0, color=NEUTRAL, lw=0.9, ls="--")
        if as_ratio:
            ax.set_xscale("log")
        ax.set_yticks(ticks)
        ax.set_yticklabels(names, fontsize=7.5)
        ax.set_xlabel(label)
        ax.grid(axis="y", visible=False)

    # Group labels in data coordinates, so they track the rows they name.
    n_scenes = len(SCENES)
    for i, (_, mech) in enumerate(mechs):
        centre = -(i * (n_scenes + 0.7) + (n_scenes - 1) / 2)
        axes[0].annotate(mech, xy=(-0.70, centre),
                         xycoords=("axes fraction", "data"),
                         rotation=90, ha="center", va="center",
                         fontsize=8.5, fontweight="bold", color="#10201F")
    fig.legend(handles=[
        Line2D([], [], marker="o", ls="-", color=NEUTRAL, label="resolved (2 SE excludes the null)"),
        Line2D([], [], marker="x", ls="-", color=NEUTRAL, alpha=0.4, label="unresolved at three repeats"),
    ], loc="lower center", ncol=2, bbox_to_anchor=(0.5, -0.06), fontsize=8)
    fig.suptitle(title, y=1.02)
    fig.text(0.5, -0.085, NULL_NOTE[null_cell], ha="center", va="center",
             fontsize=7.5, color=NEUTRAL, wrap=True)
    fig.tight_layout()
    fig.subplots_adjust(left=0.18)
    save(fig, name)


# ── 4.16  interaction plots ──────────────────────────────────────────────

def figure_4_16() -> None:
    """R2. The canonical factorial figure: parallel means additive."""
    rows = by_scene()
    pairs = [(("A0", "A1", "A2", "A4"), "M1", "M2"),
             (("A0", "A2", "A3", "A6"), "M2", "M3"),
             (("A0", "A1", "A3", "A5"), "M1", "M3")]
    fig, axes = plt.subplots(1, 3, figsize=(9.6, 3.4), sharey=False)

    for ax, (cells, fa, fb) in zip(axes, pairs):
        off, a_on, b_on, both = cells
        for key, scene in SCENES.items():
            pts = {c: mean_of(rows, c, key, "lpips") for c in cells}
            if any(v is None for v in pts.values()):
                continue
            # x = factor A off/on; one line per level of factor B
            ax.plot([0, 1], [pts[off], pts[a_on]], color=SCENE_COLOR[key],
                    lw=1.4, marker="o", ms=4, ls="-", alpha=0.9)
            ax.plot([0, 1], [pts[b_on], pts[both]], color=SCENE_COLOR[key],
                    lw=1.4, marker="s", ms=4, ls="--", alpha=0.9)
        ax.set_xticks([0, 1])
        ax.set_xticklabels([f"{fa} off", f"{fa} on"])
        ax.set_title(f"{fa} x {fb}")
        ax.set_xlim(-0.25, 1.25)
    axes[0].set_ylabel("LPIPS  (lower is better)")
    fig.legend(handles=[
        Line2D([], [], color=NEUTRAL, marker="o", ls="-", label="second factor off"),
        Line2D([], [], color=NEUTRAL, marker="s", ls="--", label="second factor on"),
    ] + [Line2D([], [], color=c, lw=2, label=SCENES[k])
         for k, c in SCENE_COLOR.items()],
        loc="lower center", ncol=6, bbox_to_anchor=(0.5, -0.10), fontsize=8)
    fig.suptitle("Interaction plots — parallel lines would mean the mechanisms add", y=1.03)
    fig.tight_layout()
    save(fig, "figure-4-16-interaction-plots")


# ── 4.17  population through training ────────────────────────────────────

def figure_4_17() -> None:
    """R3. When each mechanism acts, and the budget that binds."""
    rs = runs()
    anchors = [("n_prim_init", 0), ("n_prim_at_10000", 10000),
               ("n_prim_at_15000", 15000), ("n_primitives_final", 30000)]
    # SS carries no per-iteration diagnostics, so only its first and last
    # anchors exist; the gap is left visible rather than interpolated.
    show = [("SS", "-", "reference"), ("A0", "-", "baseline"), ("A1", "-", "M1"),
            ("A2", "-", "M2"), ("A3", "-", "M3"), ("A4", "--", "M1+M2"),
            ("A7", ":", "M1+M2+M3")]
    cmap = {"SS": "#94A9A8", "A0": NEUTRAL, "A1": "#1F6FB4", "A2": ACCENT,
            "A3": "#7A5CA8", "A4": "#1F7A66", "A7": "#9C6A1E"}

    fig, axes = plt.subplots(1, 4, figsize=(10.2, 3.1), sharey=True)
    for ax, (key, scene) in zip(axes, SCENES.items()):
        for cell, ls, label in show:
            sub = [r for r in rs if r["cell"] == cell and r["scene"] == key]
            if not sub:
                continue
            ys = []
            for col, _ in anchors:
                vals = [float(r[col]) for r in sub if r.get(col)]
                ys.append(st.mean(vals) if vals else float("nan"))
            ax.plot([it for _, it in anchors], ys, ls, color=cmap[cell],
                    lw=1.5, marker="o", ms=3.2, label=label)
        ax.axhline(200000, color=ACCENT, lw=0.9, ls=":")
        for boundary in (15000, 20000):
            ax.axvline(boundary, color=GRID, lw=1.0)
        ax.set_yscale("log")
        ax.set_title(scene)
        ax.set_xlabel("iteration")
        ax.set_xticks([0, 10000, 20000, 30000])
        ax.set_xticklabels(["0", "10k", "20k", "30k"], fontsize=8)
    axes[0].set_ylabel("primitives (log scale)")
    axes[-1].text(30500, 205000, "budget", fontsize=7, color=ACCENT,
                  va="bottom", ha="right")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=6,
               bbox_to_anchor=(0.5, -0.09), fontsize=8)
    fig.suptitle("Primitive population through training; anchors at the schedule's inflection points", y=1.04)
    fig.tight_layout()
    save(fig, "figure-4-17-population-trajectory")


# ── 4.18  frame rate against population ──────────────────────────────────

def figure_4_18() -> None:
    """R4. Sub-linear, with a scene-dependent exponent."""
    rows = by_scene()
    fig, ax = plt.subplots(figsize=(6.4, 4.0))
    for key, scene in SCENES.items():
        xs, ys = [], []
        for cell in CELLS:
            n = mean_of(rows, cell, key, "n_primitives_final")
            f = mean_of(rows, cell, key, "render_fps")
            if n and f:
                xs.append(n)
                ys.append(f)
        ax.scatter(xs, ys, s=30, color=SCENE_COLOR[key], alpha=0.85,
                   zorder=3, label=scene)
        lx = [math.log10(v) for v in xs]
        ly = [math.log10(v) for v in ys]
        n_pts = len(lx)
        mx, my = st.mean(lx), st.mean(ly)
        denom = sum((v - mx) ** 2 for v in lx)
        slope = sum((lx[i] - mx) * (ly[i] - my) for i in range(n_pts)) / denom
        lo, hi = min(lx), max(lx)
        ax.plot([10 ** lo, 10 ** hi],
                [10 ** (my + slope * (lo - mx)), 10 ** (my + slope * (hi - mx))],
                color=SCENE_COLOR[key], lw=1.1, ls="--", alpha=0.7)
        ax.annotate(f"{scene}: slope {slope:.2f}",
                    (10 ** lo, 10 ** (my + slope * (lo - mx))),
                    textcoords="offset points", xytext=(-6, 4),
                    ha="right", fontsize=7, color=SCENE_COLOR[key])
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("primitives")
    ax.set_ylabel("render rate (fps)")
    ax.set_title("Frame rate against population, all ten configurations")
    ax.legend(fontsize=8, loc="lower left")
    ax.text(0.99, 0.97, "inverse proportionality would give slope " + chr(8722) + "1",
            transform=ax.transAxes, ha="right", va="top",
            fontsize=7.5, color=NEUTRAL)
    ax.set_xlim(left=9e4)
    save(fig, "figure-4-18-fps-vs-count")


# ── 4.19  restoration gap against in-medium loss ─────────────────────────

def figure_4_19() -> None:
    """R5. The two are uncorrelated, which is what refutes drift."""
    j = json.loads((DATA / "j_consistency.json").read_text(encoding="utf-8"))
    xs, ys, labels = [], [], []
    for key, rec in j.items():
        if "verdict" not in rec:
            continue
        cell, scene, _ = key.split("/")
        xs.append(rec["truth_psnr_codebook"] - rec["truth_psnr_continuous"])
        ys.append(rec["psnr_mean"])
        labels.append((cell, scene))

    fig, ax = plt.subplots(figsize=(6.2, 3.8))
    for x, y, (cell, scene) in zip(xs, ys, labels):
        ax.scatter([x], [y], s=34, zorder=3, color=SCENE_COLOR[scene], alpha=0.85)
        ax.annotate(cell, (x, y), textcoords="offset points", xytext=(4, 3),
                    fontsize=7, color=NEUTRAL)
    rk = lambda v: [sorted(v).index(e) + 1 for e in v]
    rx, ry = rk(xs), rk(ys)
    n = len(xs)
    rho = 1 - 6 * sum((a - b) ** 2 for a, b in zip(rx, ry)) / (n * (n * n - 1))
    ax.set_xlabel("in-medium loss of the continuous state (dB)")
    ax.set_ylabel("restored-image gap between\nthe two attribute states (dB)")
    ax.set_title("If drift explained the gap, these would rise together")
    ax.text(0.98, 0.94, f"Spearman rho = {rho:.2f}  (n = {n})", transform=ax.transAxes,
            ha="right", fontsize=8.5, color=ACCENT)
    ax.legend(handles=[Line2D([], [], marker="o", ls="", color=c, label=SCENES[k])
                       for k, c in SCENE_COLOR.items()], fontsize=7.5, loc="lower right")
    save(fig, "figure-4-19-restoration-vs-drift")


# ── 4.20  collapse onset ─────────────────────────────────────────────────

def figure_4_20() -> None:
    """R6. Boundary alignment, shown rather than asserted."""
    mc = collapse()
    onsets: list[tuple[int, str, str]] = []
    for key, rec in mc.items():
        cell, scene, seed = key.split("/")
        firsts = [v for v in rec["first_negative"].values() if v is not None]
        if firsts:
            onsets.append((min(firsts), cell, scene))

    fig, ax = plt.subplots(figsize=(7.0, 2.6))
    for boundary, name in ((15000, "first simplification"), (20000, "second simplification")):
        ax.axvspan(boundary, boundary + 200, color=ACCENT, alpha=0.12)
        ax.axvline(boundary, color=NEUTRAL, lw=1.0, ls="--")
        ax.text(boundary, 1.28, name, fontsize=7.5, color=NEUTRAL,
                ha="center", va="bottom")
    seen: dict[int, int] = {}
    for it, cell, scene in sorted(onsets):
        k = seen.get(it, 0)
        seen[it] = k + 1
        ax.scatter([it], [1.0 - k * 0.11], s=40, zorder=3,
                   color=SCENE_COLOR[scene], alpha=0.9)
        ax.annotate(cell, (it, 1.0 - k * 0.11), textcoords="offset points",
                    xytext=(6, -2), fontsize=7, color=NEUTRAL)
    ax.set_xlim(9000, 31000)
    ax.set_ylim(0.18, 1.45)
    ax.set_yticks([])
    ax.set_xlabel("iteration at which a channel first goes negative")
    ax.set_title("Onset of medium collapse, nine runs")
    ax.text(9400, 0.26, "medium model active from iteration 10 000",
            fontsize=7.5, color=NEUTRAL, ha="left", va="center")
    ax.grid(axis="y", visible=False)
    save(fig, "figure-4-20-collapse-onset")



# ── figures over the Colab-collected assets ──────────────────────────────
#
# These need `ch4_assets/` unpacked beside the campaign bundle, produced by
# 03_figures.ipynb. Each skips with a note rather than failing, so the script
# stays runnable before that pass has been made.

def _asset(name: str) -> Optional[list[dict[str, str]]]:
    path = DATA / "ch4_assets" / name
    if not path.is_file():
        print(f"  skipped: {name} not collected yet (run 03_figures.ipynb)")
        return None
    return list(csv.DictReader(open(path, encoding="utf-8")))


def figure_c1_per_view() -> None:
    """C1. Does any scene mean rest on a single bad view?"""
    rows = _asset("per_view_metrics.csv")
    if rows is None:
        return
    fig, axes = plt.subplots(1, 4, figsize=(10.0, 3.4), sharey=False)
    order = list(CELLS)
    for ax, (key, scene) in zip(axes, SCENES.items()):
        for i, cell in enumerate(order):
            vals = [float(r["psnr_pooled"]) for r in rows
                    if r["cell"] == cell and r["scene"] == key]
            if not vals:
                continue
            for j, v in enumerate(vals):
                ax.scatter([i + (j % 3 - 1) * 0.12], [v], s=18, zorder=3,
                           color=SCENE_COLOR[key], alpha=0.75)
            ax.plot([i - 0.28, i + 0.28], [st.mean(vals)] * 2,
                    color=NEUTRAL, lw=1.8)
        ax.set_xticks(range(len(order)))
        ax.set_xticklabels(order, fontsize=7, rotation=90)
        ax.set_title(scene)
        ax.grid(axis="x", visible=False)
    axes[0].set_ylabel("PSNR per held-out view (dB)")
    fig.suptitle("Per-view fidelity; the bar is the scene mean the tables report", y=1.03)
    fig.tight_layout()
    save(fig, "figure-4-c1-per-view")


def figure_c4_depth_ranges() -> None:
    """C4. The distribution the registered explanation was about."""
    rows = _asset("depth_range_sweeps.csv")
    if rows is None:
        return
    cell, scene = "A2", "Curasao"
    sel = [r for r in rows if r["cell"] == cell and r["scene"] == scene]
    if not sel:
        print("  skipped: no sweeps for the chosen cell and scene")
        return
    fig, ax = plt.subplots(figsize=(6.6, 3.4))
    for seed in sorted({r["seed"] for r in sel}):
        pts = sorted((int(r["iteration"]), float(r["zr_mean"]), float(r["zr_sd"]))
                     for r in sel if r["seed"] == seed)
        its = [p[0] for p in pts]
        ax.errorbar(its, [p[1] for p in pts], yerr=[p[2] for p in pts],
                    lw=1.3, capsize=2, alpha=0.85, label=f"repeat {seed}")
    for boundary in (15000, 20000):
        ax.axvline(boundary, color=NEUTRAL, lw=0.9, ls="--")
    ax.set_xlabel("iteration")
    ax.set_ylabel("per-frame depth range\n(mean over views, bars are sd)")
    ax.set_title(f"Cross-frame depth-range distribution — {SCENES[scene]}, {cell}")
    ax.legend(fontsize=8)
    save(fig, "figure-4-c4-depth-ranges")


def figure_c5_medium_convergence() -> None:
    """C5. The baseline's medium settles; the simplification cells' does not."""
    rows = _asset("medium_trajectories.csv")
    if rows is None:
        return
    fig, axes = plt.subplots(1, 4, figsize=(10.2, 3.0), sharey=True)
    for ax, (key, scene) in zip(axes, SCENES.items()):
        for cell, color in (("A0", NEUTRAL), ("A2", ACCENT), ("A4", "#1F7A66")):
            for seed in ("0", "1", "2"):
                pts = sorted((int(r["iteration"]),
                              st.mean([float(r[f"beta_att_{c}"]) for c in "rgb"]))
                             for r in rows if r["cell"] == cell
                             and r["scene"] == key and r["seed"] == seed
                             and r.get("beta_att_r"))
                if not pts:
                    continue
                ax.plot([p[0] for p in pts], [p[1] for p in pts],
                        color=color, lw=1.0, alpha=0.7,
                        label=cell if seed == "0" else None)
        # The reference's final medium, the only point it records.
        ref = [st.mean([float(r[f"beta_att_{c}"]) for c in "rgb"])
               for r in rows if r["cell"] == "SS" and r["scene"] == key
               and r.get("beta_att_r")]
        if ref:
            ax.scatter([30000] * len(ref), ref, s=40, marker="o", zorder=4,
                       edgecolors="#94A9A8", label="reference, final", **REF_STYLE)
        for boundary in (10000, 15000, 20000):
            ax.axvline(boundary, color=GRID, lw=1.0)
        ax.set_title(scene)
        ax.set_xlabel("iteration")
    axes[0].set_ylabel("mean attenuation")
    axes[0].legend(fontsize=7.5)
    fig.suptitle("Medium convergence from activation at iteration 10 000", y=1.04)
    fig.tight_layout()
    save(fig, "figure-4-c5-medium-convergence")


def figure_c6_radius() -> None:
    """C6. Where each configuration puts its primitives."""
    rows = _asset("radius_histograms.csv")
    if rows is None:
        return
    fig, axes = plt.subplots(1, 4, figsize=(10.2, 2.9), sharey=True)
    for ax, (key, scene) in zip(axes, SCENES.items()):
        for cell, color in (("SS", "#94A9A8"), ("A0", NEUTRAL),
                            ("A1", "#1F6FB4"), ("A2", ACCENT)):
            sel = sorted((float(r["bin_lo"]), float(r["fraction"]))
                         for r in rows if r["cell"] == cell and r["scene"] == key)
            if not sel:
                continue
            ax.plot([p[0] for p in sel], [100 * p[1] for p in sel],
                    color=color, lw=1.4, label=cell)
        ax.set_title(scene)
        ax.set_xlabel("distance from cloud centre")
    axes[0].set_ylabel("share of primitives (%)")
    axes[0].legend(fontsize=7.5)
    fig.suptitle("Spatial distribution of the representation", y=1.04)
    fig.tight_layout()
    save(fig, "figure-4-c6-radius")


def main() -> None:
    style()
    print(f"writing to {OUT.relative_to(ROOT)}")
    figure_4_1()
    figure_4_3()
    figure_4_9()
    figure_4_10()
    figure_4_11()
    figure_4_12()
    figure_4_15("A0")
    figure_4_15("SS")
    figure_4_16()
    figure_4_17()
    figure_4_18()
    figure_4_19()
    figure_4_20()
    figure_c1_per_view()
    figure_c4_depth_ranges()
    figure_c5_medium_convergence()
    figure_c6_radius()


if __name__ == "__main__":
    main()
