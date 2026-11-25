# SPDX-License-Identifier: MIT
"""Input-output characteristic of the window comparator (lower 2 V, upper 3 V): HIGH
outside the window, LOW inside."""
import sys
import pathlib

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "tools"))
from figures import arrow, save, transfer_axes  # noqa: E402,F401

fig, (a,) = transfer_axes(["Window comparator"])
a.plot([0, 2, 2, 3, 3, 5], [5, 5, 0, 0, 5, 5], lw=2)
a.axvspan(2, 3, color="C2", alpha=0.15)
a.text(2.5, 2.5, "window", ha="center", va="center", rotation=90, color="C2")
a.text(1.9, 2.5, "lower", ha="right", color="gray")
a.text(3.1, 2.5, "upper", color="gray")
fig.tight_layout()
save(fig, pathlib.Path(__file__).with_name("response.svg"))
