# SPDX-License-Identifier: MIT
"""Input-output characteristics: comparator (threshold 2.5 V) and Schmitt trigger
(upper 3 V, lower 2 V; the output depends on the way the input came)."""
import sys
import pathlib

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "tools"))
from figures import arrow, save, transfer_axes  # noqa: E402,F401

fig, (a, b) = transfer_axes(["Comparator", "Schmitt trigger"])
a.plot([0, 2.5, 2.5, 5], [0, 0, 5, 5], lw=2)
a.axvline(2.5, color="gray", ls="--", lw=1)
a.text(2.6, 2.3, "threshold", color="gray")
b.plot([0, 3, 3, 5], [0, 0, 5, 5], lw=2, color="C0")
b.plot([5, 2, 2, 0], [5, 5, 0, 0], lw=2, color="C1")
arrow(b, (1.0, 0), (1.8, 0), "C0")
arrow(b, (3, 1.5), (3, 3.2), "C0")
arrow(b, (4.6, 5), (3.8, 5), "C1")
arrow(b, (2, 3.5), (2, 1.8), "C1")
for x, t in ((3, "upper"), (2, "lower")):
    b.axvline(x, color="gray", ls="--", lw=1)
b.text(3.1, 0.3, "upper", color="gray")
b.text(1.9, 0.3, "lower", ha="right", color="gray")
fig.tight_layout()
save(fig, pathlib.Path(__file__).with_name("response.svg"))
