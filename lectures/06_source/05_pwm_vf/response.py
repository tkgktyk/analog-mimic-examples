# SPDX-License-Identifier: MIT
"""PWM (top: HIGH while the input is above the triangle carrier) and V/F conversion
(bottom: a square wave whose frequency follows the input)."""
import sys
import pathlib

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "tools"))
from figures import save  # noqa: E402

t = np.linspace(0, 1, 20001)
x = 0.7 * np.sin(2 * np.pi * t)
q = (12 * t + 0.25) % 1
car = np.where(q < 0.5, 4 * q - 1, 3 - 4 * q)
pwm = np.where(x > car, 1.0, 0.0)
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 4.6), sharex=True)
ax1.plot(t, car, color="gray", lw=0.8, label="carrier")
ax1.plot(t, x, color="C3", lw=2, label="input")
ax1.plot(t, 1.4 + 0.5 * pwm, color="C0", lw=1.2, label="PWM output")
ax1.set_ylim(-1.9, 2.1)
ax1.set_yticks([])
ax1.set_title("PWM: the width of the pulses follows the input")
ax1.legend(loc="lower right", fontsize=8, ncol=3)

v = 0.5 + 0.45 * np.sin(2 * np.pi * t)
phase = np.cumsum(30 * v) * (t[1] - t[0])
sq = np.where(phase % 1 < 0.5, 1.0, 0.0)
ax2.plot(t, v, color="C3", lw=2, label="input")
ax2.plot(t, 1.2 + 0.5 * sq, color="C0", lw=1.2, label="V/F output")
ax2.set_ylim(-0.6, 2.0)
ax2.set_yticks([])
ax2.set_xlim(0, 1)
ax2.set_xlabel("Time")
ax2.set_title("V/F: the frequency follows the input")
ax2.legend(loc="lower right", fontsize=8, ncol=2)
fig.tight_layout()
save(fig, pathlib.Path(__file__).with_name("response.svg"))
