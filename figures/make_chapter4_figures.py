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
from pathlib import Path
from typing import Any

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
    OUT.mkdir(parents=True, exist_ok=True)
    for ext in ("pdf", "png"):
        fig.savefig(OUT / f"{name}.{ext}")
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

    ax.set_xticks(list(xs))
    ax.set_xticklabels(SCENES.values())
    ax.set_ylabel("PSNR effect magnitude (dB)")
    ax.set_title("Smallest resolvable effect, by contrast width, against observed main effects")
    handles = [
        Line2D([], [], color=NEUTRAL, lw=2, label="resolvable main effect (2 SE)"),
        Line2D([], [], color=NEUTRAL, lw=2, ls="--", label="resolvable two-way interaction"),
        Line2D([], [], color=NEUTRAL, lw=2, ls=":", label="resolvable three-way interaction"),
        Line2D([], [], marker="o", ls="", color=NEUTRAL, label="observed |main effect|, M1/M2/M3"),
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


def main() -> None:
    style()
    print(f"writing to {OUT.relative_to(ROOT)}")
    figure_4_1()
    figure_4_3()
    figure_4_9()
    figure_4_10()
    figure_4_11()
    figure_4_12()


if __name__ == "__main__":
    main()
