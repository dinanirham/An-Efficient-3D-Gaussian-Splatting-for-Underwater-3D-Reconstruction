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
import matplotlib.pyplot as plt  # noqa: E402
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

    fig.suptitle(title, y=1.005, fontsize=10.5)
    fig.text(0.5, -0.012, note, ha="center", fontsize=7.5, color=NEUTRAL, wrap=True)
    fig.tight_layout(h_pad=0.4, w_pad=0.25)

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
    print(f"  {name}.pdf / .png" + (f"   [{len(missing)} panel(s) missing]" if missing else ""))


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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
