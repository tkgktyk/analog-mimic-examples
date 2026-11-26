# SPDX-License-Identifier: MIT
"""Slew rate limiting in time: a square wave becomes a trapezoid (left); a sine whose
largest slope 2 pi f A is below SR passes, above SR it becomes a smaller triangle
(right)."""
import sys
import pathlib

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "tools"))
from figures import save  # noqa: E402


def slew(x, rate, dt):
    y = np.empty_like(x)
    out = x[0]
    for n, v in enumerate(x):
        out += np.clip(v - out, -rate * dt, rate * dt)
        y[n] = out
    return y


t = np.linspace(0, 2, 8001)            # time in input periods
dt = t[1] - t[0]
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.5, 3.2))

sq = np.where((t % 1) < 0.5, 1.0, -1.0)
ax1.plot(t, sq, color="gray", lw=1, label="input")
ax1.plot(t, slew(sq, 10, dt), lw=2, label="output")
ax1.annotate("slope = SR", (0.6, 0.0), (0.68, 0.55), fontsize=9, arrowprops=dict(arrowstyle="->", color="gray"))
ax1.set_title("Square wave")
ax1.set_xlabel("Time [periods]")
ax1.set_ylabel("Input / output - Vref")

x = np.sin(2 * np.pi * t)
ax2.plot(t, x, color="gray", lw=1, label="input")
for k, style in ((1.5, "-"), (0.5, "--")):
    y = slew(x, k * 2 * np.pi, dt)
    ax2.plot(t, y, lw=2, ls=style, label=f"SR = {k} x 2 pi f A" + (" (= input)" if k > 1 else ""))
ax2.set_title("Sine wave (amplitude A)")
ax2.set_xlabel("Time [periods]")
for ax, ncol in ((ax1, 3), (ax2, 2)):
    ax.set_xlim(0, 2)
    ax.set_ylim(-1.2, 1.9)
    ax.legend(loc="upper right", fontsize=8, ncol=ncol)
fig.tight_layout()
save(fig, pathlib.Path(__file__).with_name("response.svg"))
