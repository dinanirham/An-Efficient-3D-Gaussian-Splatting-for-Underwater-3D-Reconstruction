"""Per-run diagnostic logging (CD-12).

Three quantities that no source method records, logged because they are what
turn this study's central claims from assertions into measurements. Together
they cost one CSV row every `diag_interval` iterations.

**Depth normalisation constants.** SeaSplat renormalises the rendered depth map
to [0,1] by its own per-frame min and max, and the medium coefficients enter
the image formation model only through their product with that depth. Removing
a large fraction of the primitives therefore rescales the medium model's only
spatial input, mid-training, by a factor nothing measures -- which is formally
indistinguishable from a change in the coefficients themselves. Logging
`z_min`/`z_max` across a simplification event is the direct test.

**Medium coefficients.** A discontinuity in beta at a simplification boundary is
the signature of that failure; its absorption inside the re-identification
burst is the signature of the fix. Under quantization, drift relative to an
unquantized run tests whether the medium model is absorbing codebook error --
which, if it happens, means beta stops being interpretable as a medium estimate
in exactly the configurations where compression is being claimed.

**Primitive count, at five points.** Logged unconditionally. Upstream printed a
count only when something was actually pruned, which makes silence ambiguous
between "under budget" and "never ran" -- and that ambiguity is what loses the
answer to whether the budget ever bound.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Optional

import torch


class DiagnosticLogger:
    """Append-only CSV logger. Flushes every row: Colab sessions get killed."""

    FIELDS = [
        "iteration",
        "event",          # periodic | pre_simp | post_simp | rewarm_end | init | settled
        "n_primitives",
        "z_min",
        "z_max",
        "z_range",
        "alpha_mean",
        "beta_att_r", "beta_att_g", "beta_att_b",
        "beta_bs_r", "beta_bs_g", "beta_bs_b",
        "binf_r", "binf_g", "binf_b",
        "loss",
        "note",
    ]

    def __init__(self, model_path: str | Path, interval: int = 500) -> None:
        self.path = Path(model_path) / "diagnostics.csv"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.interval = max(1, int(interval))
        fresh = not self.path.exists()
        self._fh = open(self.path, "a", newline="", encoding="utf-8")
        self._w = csv.DictWriter(self._fh, fieldnames=self.FIELDS)
        if fresh:
            self._w.writeheader()
            self._fh.flush()
        print(f"[diagnostics] {self.path}")

    # -- helpers -----------------------------------------------------------

    @staticmethod
    def _triple(t: Optional[torch.Tensor]) -> tuple:
        """Flatten a 3-vector-ish medium parameter to three floats."""
        if t is None:
            return ("", "", "")
        v = t.detach().flatten().float().cpu()
        if v.numel() < 3:
            return ("", "", "")
        return (round(v[0].item(), 8), round(v[1].item(), 8), round(v[2].item(), 8))

    def due(self, iteration: int) -> bool:
        return iteration % self.interval == 0

    # -- the one entry point -----------------------------------------------

    def log(
        self,
        iteration: int,
        event: str,
        n_primitives: int,
        depth_image: Optional[torch.Tensor] = None,
        alpha_image: Optional[torch.Tensor] = None,
        bs_model: Any = None,
        at_model: Any = None,
        loss: Optional[float] = None,
        note: str = "",
        z_min: Optional[float] = None,
        z_max: Optional[float] = None,
    ) -> None:
        """Write one row.

        `z_min`/`z_max` may be passed explicitly -- they must be captured
        BEFORE the per-frame min-max renormalisation, since afterwards they are
        0 and 1 by construction and carry no information.
        """
        row: dict[str, Any] = {f: "" for f in self.FIELDS}
        row["iteration"] = iteration
        row["event"] = event
        row["n_primitives"] = n_primitives
        row["note"] = note

        if z_min is not None:
            row["z_min"] = round(float(z_min), 8)
        if z_max is not None:
            row["z_max"] = round(float(z_max), 8)
        if z_min is not None and z_max is not None:
            row["z_range"] = round(float(z_max) - float(z_min), 8)

        if alpha_image is not None:
            row["alpha_mean"] = round(alpha_image.detach().mean().item(), 8)

        if bs_model is not None:
            row["beta_bs_r"], row["beta_bs_g"], row["beta_bs_b"] = self._triple(
                getattr(bs_model, "backscatter_conv_params", None)
            )
            binf = getattr(bs_model, "B_inf", None)
            if binf is not None:
                binf = torch.sigmoid(binf)
            row["binf_r"], row["binf_g"], row["binf_b"] = self._triple(binf)

        if at_model is not None:
            row["beta_att_r"], row["beta_att_g"], row["beta_att_b"] = self._triple(
                getattr(at_model, "attenuation_conv_params", None)
            )

        if loss is not None:
            row["loss"] = round(float(loss), 8)

        self._w.writerow(row)
        self._fh.flush()  # a killed Colab session must not lose the last rows

    def close(self) -> None:
        try:
            self._fh.close()
        except Exception:  # noqa: BLE001
            pass
