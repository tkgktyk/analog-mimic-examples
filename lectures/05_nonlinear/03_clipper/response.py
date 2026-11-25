# SPDX-License-Identifier: MIT
"""Input-output characteristics of the clippers (limits 1.5 and 3.5 V): hard (ideal
diodes) and soft (cubic, like real diodes), with output = input dashed."""
import sys
import pathlib

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "tools"))
from figures import arrow, save, transfer_axes  # noqa: E402,F401

x = np.linspace(0, 5, 501)
c, h = 2.5, 1.0
d = x - c
soft = np.where(d >= 1.5 * h, c + h, np.where(d <= -1.5 * h, c - h, c + d - 4 * d ** 3 / (27 * h * h)))
fig, (a,) = transfer_axes(["Clipper"])
a.plot(x, x, "--", color="gray", lw=1, label="output = input")
a.plot(x, np.clip(x, 1.5, 3.5), lw=2, label="hard")
a.plot(x, soft, lw=2, label="soft")
for y in (1.5, 3.5):
    a.axhline(y, color="gray", ls=":", lw=1)
a.legend(loc="upper left", fontsize=9)
fig.tight_layout()
save(fig, pathlib.Path(__file__).with_name("response.svg"))
