# SPDX-License-Identifier: MIT
"""Sample & hold and track & hold in time (left: 8 clock periods per input period,
tracking half of each period), and aliasing (right: an input at 0.9 x the sampling
frequency looks like 0.1 x the sampling frequency)."""
import sys
import pathlib

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "tools"))
from figures import save  # noqa: E402

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.5, 3.2))

# Left: time in input periods; 8 samples per period
t = np.linspace(0, 2, 4001)
x = np.sin(2 * np.pi * t)
n = 8
k = np.floor(t * n) / n
sh = np.sin(2 * np.pi * k)
th = np.where(t * n - np.floor(t * n) < 0.5, x, np.sin(2 * np.pi * (k + 0.5 / n)))
ax1.plot(t, x, color="gray", lw=1, label="input")
ax1.plot(t, sh, lw=2, label="sample & hold")
ax1.plot(t, th, lw=1.5, ls="--", label="track & hold (track 50 %)")
ax1.set_xlim(0, 2)
ax1.set_ylim(-1.2, 1.55)
ax1.set_xlabel("Time [input periods]")
ax1.set_ylabel("Input / output - Vref")
ax1.set_title("8 samples per period")
ax1.legend(loc="upper right", fontsize=8, ncol=3)

# Right: time in sampling periods; input at 0.9 fs
ts = np.linspace(0, 20, 8001)
xs = np.sin(2 * np.pi * 0.9 * ts)
ks = np.floor(ts)
ax2.plot(ts, xs, color="gray", lw=0.7, label="input (0.9 fs)")
ax2.plot(ts, np.sin(2 * np.pi * 0.9 * ks), lw=2, label="sample & hold")
ax2.plot(ts, np.sin(2 * np.pi * -0.1 * ts), color="C3", lw=1, ls=":", label="looks like 0.1 fs")
ax2.plot(np.arange(21), np.sin(2 * np.pi * 0.9 * np.arange(21)), "o", color="C0", ms=3)
ax2.set_xlim(0, 20)
ax2.set_ylim(-1.2, 1.55)
ax2.set_xlabel("Time [sampling periods]")
ax2.set_title("Aliasing")
ax2.legend(loc="upper right", fontsize=8, ncol=3)
fig.tight_layout()
save(fig, pathlib.Path(__file__).with_name("response.svg"))
