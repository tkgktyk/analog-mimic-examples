# SPDX-License-Identifier: MIT
"""Delay (dead time) tau: the output is the input shifted by tau (left); the gain is 1
at every frequency and the phase falls in proportion to the frequency, -360 f tau
degrees (right, linear frequency axis)."""
import sys
import pathlib

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "tools"))
from figures import save  # noqa: E402

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.5, 3.2))

t = np.linspace(0, 2, 4001)            # time in periods of the input
tau = 0.3
sq = lambda x: np.where((x % 1) < 0.5, 1.0, -1.0)  # noqa: E731
ax1.plot(t, sq(t), color="gray", lw=1, label="input")
ax1.plot(t, sq(t - tau), lw=2, label="output (delay tau)")
ax1.annotate("", (0.5 + tau, 1.25), (0.5, 1.25), arrowprops=dict(arrowstyle="<->", color="C3"))
ax1.text(0.5 + tau / 2, 1.32, "tau", color="C3", ha="center")
ax1.set_xlim(0, 2)
ax1.set_ylim(-1.3, 1.75)
ax1.set_xlabel("Time [periods]")
ax1.set_ylabel("Input / output - Vref")
ax1.set_title("In time")
ax1.legend(loc="upper right", fontsize=8, ncol=2)

f = np.linspace(0, 3, 301)             # frequency x tau
ax2.plot(f, -360 * f, lw=2)
ax2.set_xlim(0, 3)
ax2.set_ylim(-1080, 0)
ax2.set_yticks(np.arange(-1080, 1, 180))
ax2.set_xlabel("Frequency  f x tau")
ax2.set_ylabel("Phase [deg]")
ax2.set_title("Phase (the gain is 1 at every frequency)")
ax2.grid(True, alpha=0.4)
ax2.text(1.6, -300, "-360 f tau", color="C0")
fig.tight_layout()
save(fig, pathlib.Path(__file__).with_name("response.svg"))
