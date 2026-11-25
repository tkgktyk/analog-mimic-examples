# SPDX-License-Identifier: MIT
"""Input-output characteristics of the rectifiers folding at Vref = 2.5 V: half-wave
max(x, Vref) and full-wave Vref + |x - Vref|, with output = input dashed."""
import sys
import pathlib

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "tools"))
from figures import arrow, save, transfer_axes  # noqa: E402,F401

x = np.linspace(0, 5, 501)
fig, (a, b) = transfer_axes(["Half-wave", "Full-wave"])
for ax, y in ((a, np.maximum(x, 2.5)), (b, 2.5 + np.abs(x - 2.5))):
    ax.plot(x, x, "--", color="gray", lw=1)
    ax.plot(x, y, lw=2)
    ax.axvline(2.5, color="gray", ls=":", lw=1)
    ax.text(2.6, 0.3, "Vref", color="gray")
fig.tight_layout()
save(fig, pathlib.Path(__file__).with_name("response.svg"))
