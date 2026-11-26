# SPDX-License-Identifier: MIT
"""Log and antilog of the module: the log output is a straight line against the input on a
logarithmic axis (slope per decade); the antilog output is a straight line on a
logarithmic output axis (the inverse)."""
import sys
import pathlib

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "tools"))
from figures import save  # noqa: E402

SLOPE, UNIT = 1.0, 0.5
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.5, 3.4))
d = np.logspace(-2, np.log10(2.4), 100)
ax1.semilogx(d, 2.5 + SLOPE * np.log10(d / UNIT), lw=2)
ax1.plot([UNIT], [2.5], "o", color="C1")
ax1.annotate("unit: output = Vref", (UNIT, 2.5), (0.06, 3.0), arrowprops=dict(arrowstyle="->"))
ax1.set_xticks([0.01, 0.1, 1])
ax1.set_xticklabels(["0.01", "0.1", "1"])
ax1.set_xlabel("Input - Vref [V] (log scale)")
ax1.set_ylabel("Output [V]")
ax1.set_title("Log: +1 V per decade")
ax1.grid(True, which="both", alpha=0.4)

x = np.linspace(-0.6, 0.95, 100)
ax2.semilogy(x, UNIT * 10 ** (x / SLOPE), lw=2)
ax2.plot([0], [UNIT], "o", color="C1")
ax2.annotate("Vref: output = unit", (0, UNIT), (-0.55, 1.5), arrowprops=dict(arrowstyle="->"))
ax2.set_yticks([0.2, 0.5, 1, 2, 5])
ax2.set_yticklabels(["0.2", "0.5", "1", "2", "5"])
ax2.minorticks_off()
ax2.set_xlabel("Input - Vref [V]")
ax2.set_ylabel("Output [V] (log scale)")
ax2.set_title("Antilog: x 10 per 1 V")
ax2.grid(True, which="both", alpha=0.4)
fig.tight_layout()
save(fig, pathlib.Path(__file__).with_name("response.svg"))
