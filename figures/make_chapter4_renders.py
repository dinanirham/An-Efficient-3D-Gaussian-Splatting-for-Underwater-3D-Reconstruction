"""Assemble the Chapter IV render figures from the collected images.

    python figures/make_chapter4_renders.py

Reads `analysis/campaign-2026-09/ch4_assets/renders/`, produced on Colab by
`03_figures.ipynb`, and lays the images out into the figures the chapter needs.
No GPU, no checkpoints: this is composition only.

Every panel of a figure shows the same held-out view and, where cropped, the
same crop box, so that differences between panels are differences between
configurations and nothing else. Crops are fractions of the image, not pixel
boxes, because the four scenes were captured at different resolutions
(1599x1059, 1383x917, 1384x918, 1600x1058) and a fixed pixel box would cover a
different share of each.

Two regions, chosen from the corpus rather than by convention:

  far    the water column where the reef recedes -- strongest attenuation,
         and where quantisation damage is argued to hide behind it
  near   the textured reef in the foreground -- where simplification's loss
         of high-frequency detail shows

Figures produced
  4.2   ground truth, reference, baseline -- the equivalence claim, visually
  4.4   the medium decomposition of one view per scene
  4.6   initialisation, near-field
  4.7   simplification, near-field
  4.8   quantisation, far-field, composed against restored
"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Optional

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.figure import Figure  # noqa: E402
from PIL import Image  # noqa: E402

ROOT: Path = Path(__file__).resolve().parent.parent
RENDERS: Path = ROOT / "analysis" / "campaign-2026-09" / "ch4_assets" / "renders"
OUT: Path = ROOT / "figures" / "chapter4"

SCENES: dict[str, str] = {
    "Curasao": "Curaçao",
    "IUI3-RedSea": "IUI3 Red Sea",
    "JapaneseGradens-RedSea": "Japanese Gardens",
    "Panama": "Panama",
}

# (centre_x, centre_y, width) as fractions of the image; height follows at 4:3.
REGIONS: dict[str, tuple[float, float, float]] = {
    "far": (0.52, 0.20, 0.30),
    "near": (0.25, 0.72, 0.30),
}

NEUTRAL: str = "#4A5C5B"
INK: str = "#10201F"


def style() -> None:
    plt.rcParams.update({
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "DejaVu Sans"],
        "font.size": 9,
        "text.color": INK,
    })


def load(scene: str, cell: str, kind: str) -> Optional[Image.Image]:
    path = RENDERS / f"{scene}_{cell}_{kind}.png"
    if not path.is_file():
        return None
    return Image.open(path).convert("RGB")


def crop(im: Image.Image, region: Optional[str]) -> Image.Image:
    if region is None:
        return im
    cx, cy, fw = REGIONS[region]
    w = int(round(fw * im.width))
    h = int(round(w * 0.75))
    x = int(round(cx * im.width - w / 2))
    y = int(round(cy * im.height - h / 2))
    x = max(0, min(x, im.width - w))
    y = max(0, min(y, im.height - h))
    return im.crop((x, y, x + w, y + h))


def _caption_band(fig: Figure, note: str) -> float:
    """Figure fraction to reserve below the axes for a wrapped caption.

    Placing it just below zero and trusting a tight bounding box does not work:
    tight_layout has already extended the axes to the figure edge, so the text
    lands on the last row of images.
    """
    lines = max(1, round(len(note) / 110))
    return min(0.22, (0.28 + 0.16 * lines) / fig.get_figheight())


def grid(name: str, columns: list[tuple[str, str, str]], region: Optional[str],
         title: str, note: str) -> None:
    """One row per scene, one column per (cell, kind, label)."""
    rows = list(SCENES)
    fig, axes = plt.subplots(len(rows), len(columns),
                             figsize=(2.35 * len(columns), 1.85 * len(rows)))
    if len(rows) == 1:
        axes = [axes]

    missing: list[str] = []
    for r, scene in enumerate(rows):
        for c, (cell, kind, label) in enumerate(columns):
            ax = axes[r][c]
            ax.set_xticks([])
            ax.set_yticks([])
            for spine in ax.spines.values():
                spine.set_edgecolor("#C9D4D3")
                spine.set_linewidth(0.6)
            im = load(scene, cell, kind)
            if im is None:
                missing.append(f"{scene}/{cell}/{kind}")
                ax.text(0.5, 0.5, "not collected", transform=ax.transAxes,
                        ha="center", va="center", fontsize=7, color=NEUTRAL)
                continue
            ax.imshow(crop(im, region))
            if r == 0:
                ax.set_title(label, fontsize=8.5, pad=4)
            if c == 0:
                ax.set_ylabel(SCENES[scene], fontsize=8.5)

    band = _caption_band(fig, note)
    fig.suptitle(title, y=1.005, fontsize=10.5)
    fig.tight_layout(rect=(0, band, 1, 1), h_pad=0.4, w_pad=0.25)
    fig.text(0.5, band * 0.42, note, ha="center", va="center",
             fontsize=7.5, color=NEUTRAL, wrap=True)

    _save(fig, name, missing)


def _save(fig: "plt.Figure", name: str, missing: Optional[list] = None) -> None:
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
    tail = f"   [{len(missing)} panel(s) missing]" if missing else ""
    print(f"  {name}.pdf / .png{tail}")



# ── the comparison rule, and what every panel carries ────────────────────

import csv  # noqa: E402
import json  # noqa: E402

DATA: Path = ROOT / "analysis" / "campaign-2026-09"
ACCENT: str = "#C8462E"

MECHANISMS: list[tuple[str, str, str]] = [
    ("A0D", "gradient detachment", "near"),
    ("A1", "initialisation", "near"),
    ("A2", "simplification", "near"),
    ("A3", "quantisation", "far"),
    ("A4", "initialisation + simplification", "near"),
    ("A5", "initialisation + quantisation", "far"),
    ("A6", "simplification + quantisation", "far"),
    ("A7", "all three", "near"),
]


def per_view() -> dict[tuple[str, str], dict[str, float]]:
    """The metrics of the one view each figure shows, per configuration."""
    path = DATA / "ch4_assets" / "per_view_metrics.csv"
    if not path.is_file():
        return {}
    rows = list(csv.DictReader(open(path, encoding="utf-8")))
    # The figure's view is the one the collector also rendered; identify it by
    # matching the render's own view rather than re-deriving the index here.
    out: dict[tuple[str, str], dict[str, float]] = {}
    by_scene: dict[str, list[dict]] = {}
    for r in rows:
        by_scene.setdefault(r["scene"], []).append(r)
    for scene, group in by_scene.items():
        images = sorted({r["image"] for r in group})
        if not images:
            continue
        chosen = images[min(len(images) - 1, max(0, round(VIEW_FRACTION.get(scene, 0.5)
                                                          * (len(images) - 1))))]
        for r in group:
            if r["image"] == chosen:
                out[(r["cell"], scene)] = {"psnr": float(r["psnr_pooled"]),
                                           "lpips": float(r["lpips"])}
    return out


VIEW_FRACTION: dict[str, float] = {
    "Curasao": 0.5, "IUI3-RedSea": 0.5,
    "JapaneseGradens-RedSea": 0.34, "Panama": 0.5,
}


def collapsed_runs() -> set[tuple[str, str]]:
    """Configurations that lost a channel at seed 0 — the only highlight the
    analysis supports on a per-panel basis."""
    path = DATA / "medium_collapse.json"
    if not path.is_file():
        return set()
    mc = json.loads(path.read_text(encoding="utf-8"))
    out = set()
    for key, rec in mc.items():
        cell, scene, seed = key.split("/")
        if seed == "s0" and rec.get("collapsed"):
            out.add((cell, scene))
    return out


def comparison(cell: str, label: str, region: str) -> None:
    """F1 — ground truth, reference, baseline, mechanism. One row per scene.

    The four columns are the comparison rule: a mechanism is only interesting
    against a baseline the reader can see is faithful, so the reference travels
    with every figure rather than living once in section 4.2.
    """
    metrics = per_view()
    collapsed = collapsed_runs()
    columns = [("__gt__", "ground truth"), ("SS", "reference (SS)"),
               ("A0", "baseline (A0)"), (cell, f"{cell} — {label}")]
    scenes = list(SCENES)

    fig, axes = plt.subplots(len(scenes), len(columns),
                             figsize=(2.5 * len(columns), 2.05 * len(scenes)))
    missing: list[str] = []
    for r, scene in enumerate(scenes):
        for c, (who, head) in enumerate(columns):
            ax = axes[r][c]
            ax.set_xticks([]); ax.set_yticks([])
            src_cell = "A0" if who == "__gt__" else who
            kind = "gt" if who == "__gt__" else "composed"
            im = load(scene, src_cell, kind)
            if im is None:
                missing.append(f"{scene}/{who}")
                ax.text(0.5, 0.5, "not collected", transform=ax.transAxes,
                        ha="center", va="center", fontsize=7, color=NEUTRAL)
                for sp in ax.spines.values():
                    sp.set_edgecolor("#C9D4D3"); sp.set_linewidth(0.6)
                continue
            ax.imshow(crop(im, region))

            lost = who != "__gt__" and (who, scene) in collapsed
            for sp in ax.spines.values():
                sp.set_edgecolor(ACCENT if lost else "#C9D4D3")
                sp.set_linewidth(1.8 if lost else 0.6)
            if lost:
                ax.text(0.03, 0.95, "channel lost", transform=ax.transAxes,
                        fontsize=7, color="white", va="top",
                        bbox={"facecolor": ACCENT, "edgecolor": "none", "pad": 1.6})

            m = metrics.get((src_cell, scene)) if who != "__gt__" else None
            if m:
                ax.text(0.97, 0.05, f"{m['psnr']:.1f} dB   {m['lpips']:.3f}",
                        transform=ax.transAxes, ha="right", va="bottom",
                        fontsize=6.8, color="white",
                        bbox={"facecolor": "#10201F", "alpha": 0.55,
                              "edgecolor": "none", "pad": 1.6})
            if r == 0:
                ax.set_title(head, fontsize=8.5, pad=4)
            if c == 0:
                ax.set_ylabel(SCENES[scene], fontsize=8.5)

    band = _caption_band(fig, "x" * 260)
    fig.suptitle(f"{label.capitalize()} against the reference and the baseline",
                 y=1.004, fontsize=10.5)
    fig.tight_layout(rect=(0, band, 1, 1), h_pad=0.4, w_pad=0.25)
    fig.text(0.5, band * 0.42,
             f"{region.capitalize()}-field crop of one held-out view per scene, seed 0. "
             "Each panel carries the PSNR and LPIPS of that view in that configuration, "
             "not the scene mean. An accent border marks a run that lost an attenuation "
             "channel.",
             ha="center", va="center", fontsize=7.5, color=NEUTRAL, wrap=True)
    _save(fig, f"figure-q1-{cell.lower()}-{label.split()[0]}", missing)


def overview(scene: str = "Curasao") -> None:
    """F2 — the whole design at one glance, two rows of five."""
    metrics = per_view()
    collapsed = collapsed_runs()
    order = ["__gt__", "SS", "A0", "A0D", "A1", "A2", "A3", "A4", "A5", "A6", "A7"]
    fig, axes = plt.subplots(2, 6, figsize=(13.2, 4.6))
    flat = [ax for row in axes for ax in row]
    for ax, who in zip(flat, order + [None]):
        ax.set_xticks([]); ax.set_yticks([])
        if who is None:
            ax.axis("off")
            continue
        src = "A0" if who == "__gt__" else who
        im = load(scene, src, "gt" if who == "__gt__" else "composed")
        if im is None:
            ax.text(0.5, 0.5, "not collected", transform=ax.transAxes,
                    ha="center", va="center", fontsize=7, color=NEUTRAL)
            continue
        ax.imshow(crop(im, "near"))
        lost = who != "__gt__" and (who, scene) in collapsed
        for sp in ax.spines.values():
            sp.set_edgecolor(ACCENT if lost else "#C9D4D3")
            sp.set_linewidth(1.8 if lost else 0.6)
        ax.set_title("ground truth" if who == "__gt__" else who, fontsize=8.5, pad=3)
        m = metrics.get((src, scene)) if who != "__gt__" else None
        if m:
            ax.text(0.97, 0.05, f"{m['psnr']:.1f}  {m['lpips']:.3f}",
                    transform=ax.transAxes, ha="right", va="bottom", fontsize=6.4,
                    color="white", bbox={"facecolor": "#10201F", "alpha": 0.55,
                                         "edgecolor": "none", "pad": 1.4})
    fig.suptitle(f"All ten configurations — {SCENES[scene]}, near-field", y=1.01)
    band = _caption_band(fig, "x" * 140)
    fig.tight_layout(rect=(0, band, 1, 1), h_pad=0.5, w_pad=0.25)
    fig.text(0.5, band * 0.42,
             "One held-out view, one crop, seed 0. PSNR and LPIPS are for this view. "
             "An accent border marks a lost attenuation channel.",
             ha="center", va="center", fontsize=7.5, color=NEUTRAL)
    _save(fig, "figure-q2-all-configurations")


def error_maps(scene: str = "IUI3-RedSea") -> None:
    """F3 — where the error sits, which no table shows."""
    from PIL import ImageChops
    gt = load(scene, "A0", "gt")
    if gt is None:
        print("  error maps: ground truth not collected")
        return
    cells = ["SS", "A0", "A1", "A2", "A3"]
    fig, axes = plt.subplots(1, len(cells), figsize=(2.3 * len(cells), 2.1))
    for ax, cell in zip(axes, cells):
        ax.set_xticks([]); ax.set_yticks([])
        for sp in ax.spines.values():
            sp.set_edgecolor("#C9D4D3"); sp.set_linewidth(0.6)
        im = load(scene, cell, "composed")
        if im is None:
            ax.text(0.5, 0.5, "not collected", transform=ax.transAxes,
                    ha="center", va="center", fontsize=7, color=NEUTRAL)
            continue
        diff = ImageChops.difference(im.convert("RGB"), gt.convert("RGB"))
        ax.imshow(crop(diff, "near"), vmin=0, vmax=64)
        ax.set_title(cell, fontsize=8.5, pad=3)
    fig.suptitle(f"Absolute error against ground truth — {SCENES[scene]}", y=1.02)
    band = _caption_band(fig, "x" * 210)
    fig.tight_layout(rect=(0, band, 1, 1), w_pad=0.25)
    fig.text(0.5, band * 0.42,
             "Near-field crop, identically scaled across panels and clipped at 64 of "
             "255 so differences remain visible. Error concentrates on texture, which "
             "is what the perceptual metric reacts to and the pixel metric does not.",
             ha="center", va="center", fontsize=7.5, color=NEUTRAL, wrap=True)
    _save(fig, "figure-q3-error-maps")


def main() -> int:
    if not RENDERS.is_dir():
        print(f"no renders at {RENDERS.relative_to(ROOT)} — run 03_figures.ipynb first")
        return 1
    style()
    print(f"writing to {OUT.relative_to(ROOT)}")

    grid("figure-4-02-baseline-vs-reference",
         [("SS", "gt", "ground truth"),
          ("SS", "composed", "reference (SS)"),
          ("A0", "composed", "baseline (A0)")],
         None,
         "Reference and baseline against ground truth",
         "Full held-out frame, one per scene. The two implementations are "
         "equivalent within the pre-registered margin; this is what that looks like.")

    grid("figure-4-04-medium-decomposition",
         [("A0", "composed", "composed  Î"),
          ("A0", "restored", "restored  Ĵ"),
          ("A0", "attenuation", "attenuation"),
          ("A0", "backscatter", "backscatter")],
         None,
         "What the baseline claims the water is doing",
         "The decomposition the method exists to produce. Only the composed image "
         "has ground truth; the other three are the model's own account and are not "
         "validated against a measurement.")

    grid("figure-4-06-initialisation",
         [("A0", "gt", "ground truth"),
          ("A0", "composed", "baseline (A0)"),
          ("A1", "composed", "initialisation (A1)")],
         "near",
         "Deterministic initialisation, near-field detail",
         "Same crop of the same held-out view. A1 reaches this with 10–16× fewer "
         "primitives; perceptual similarity is unchanged on three scenes and worse "
         "on IUI3 Red Sea.")

    grid("figure-4-07-simplification",
         [("A0", "gt", "ground truth"),
          ("A0", "composed", "baseline (A0)"),
          ("A2", "composed", "simplification (A2)")],
         "near",
         "Spatial reorganisation, near-field detail",
         "Simplification costs perceptual similarity on all four scenes at "
         "7–45 standard errors, while PSNR improves on two. This crop is where "
         "that disagreement lives.")

    grid("figure-4-08-quantisation",
         [("A0", "composed", "baseline, composed"),
          ("A3", "composed", "quantised, composed"),
          ("A0", "restored", "baseline, restored"),
          ("A3", "restored", "quantised, restored")],
         "far",
         "Attribute quantisation in the far field: composed against restored",
         "Two separately trained models. Their composed images are nearly "
         "indistinguishable and their restorations are not — but this comparison "
         "confounds quantisation with trajectory divergence between runs, so it "
         "illustrates rather than measures. The within-model comparison, one model "
         "in both attribute states, is Figure 4.14 and is not yet rendered.")
    # 4.13 needs no new collection: the collapsed run and an intact one on the
    # same scene are both already rendered.
    collapsed_pair()
    extras()

    # The qualitative family: every mechanism against ground truth, the
    # reference and the baseline.
    for cell, label, region in MECHANISMS:
        comparison(cell, label, region)
    overview()
    error_maps()
    return 0


def collapsed_pair() -> None:
    """Figure 4.13 — what a lost channel looks like.

    The honest pairing available. Full point clouds are kept for seed 0 only,
    and no cell has both a collapsed and an intact repeat at that seed, so the
    collapsed run is shown against the baseline on the same scene and view
    rather than against another repeat of its own cell. The two therefore
    differ in configuration as well as in outcome, and the caption says so.
    """
    scene = "JapaneseGradens-RedSea"
    panels = [("A0", "attenuation", "baseline — attenuation"),
              ("A2", "attenuation", "collapsed — attenuation"),
              ("A0", "restored", "baseline — restored  Ĵ"),
              ("A2", "restored", "collapsed — restored  Ĵ")]
    fig, axes = plt.subplots(1, 4, figsize=(9.4, 2.1))
    for ax, (cell, kind, label) in zip(axes, panels):
        ax.set_xticks([]); ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_edgecolor("#C9D4D3"); spine.set_linewidth(0.6)
        im = load(scene, cell, kind)
        if im is None:
            ax.text(0.5, 0.5, "not collected", transform=ax.transAxes,
                    ha="center", va="center", fontsize=7, color=NEUTRAL)
            continue
        ax.imshow(im)
        ax.set_title(label, fontsize=8.5, pad=4)
    fig.suptitle("A lost attenuation channel — " + SCENES[scene], y=1.04, fontsize=10.5)
    band = _caption_band(fig, "x" * 330)
    fig.tight_layout(rect=(0, band, 1, 1), w_pad=0.25)
    fig.text(0.5, band * 0.42,
             "The simplification run lost its blue channel; the baseline did not. "
             "Their composed images score within 0.8 of a baseline standard deviation "
             "of each other. No cell has both a collapsed and an intact repeat at the "
             "one seed whose point cloud is retained, so these differ in configuration "
             "as well as in outcome.",
             ha="center", va="center", fontsize=7.5, color=NEUTRAL, wrap=True)
    _save(fig, "figure-4-13-collapsed-medium")


def extras() -> None:
    """Figures 4.5 and 4.14, once the extra render pass has been collected."""
    have = lambda scene, cell, kind: (RENDERS / f"{scene}_{cell}_{kind}.png").is_file()
    if have("Curasao", "A0", "composed_visibleonly"):
        grid("figure-4-05-invisible-population",
             [("A0", "composed", "all primitives"),
              ("A0", "composed_visibleonly", "visible primitives only"),
              ("A0", "composed_visiblediff", "difference, ×4")],
             None,
             "The population that never reaches a render",
             "Between 59 and 73 per cent of the baseline's primitives fall below the "
             "visibility threshold. Silencing them changes the image by almost "
             "nothing, which is why a count reduction should be read against the "
             "visible population rather than the total.")
    else:
        print("  figure 4.5: run the collector with --only extras first")

    if have("Curasao", "A3", "restored_continuous"):
        grid("figure-4-14-attribute-states",
             [("A3", "restored_continuous", "continuous state"),
              ("A3", "restored_codebook", "codebook state")],
             "far",
             "One model, both attribute states, restored image",
             "The comparison Figure 4.8 cannot make: the same trained model rendered "
             "from its continuous parameters and from its codebook. Nothing else "
             "differs, so the difference is quantisation and not trajectory "
             "divergence. Consistency, not accuracy.")
    else:
        print("  figure 4.14: run the collector with --only extras first")


if __name__ == "__main__":
    raise SystemExit(main())
