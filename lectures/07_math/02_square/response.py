# SPDX-License-Identifier: MIT
"""Squarer and square rooter of the module (unit 1.25 V): the transfer curves (left) and a
sine through the squarer (right: twice the frequency, all above 0 V)."""
import sys
import pathlib

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "tools"))
from figures import save  # noqa: E402

UNIT = 1.25
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.5, 3.4))
d = np.linspace(-2, 2, 401)
ax1.plot(d, d**2 / UNIT, lw=2, label="squarer d² / unit")
ax1.plot(d, np.sqrt(np.maximum(d, 0) * UNIT), lw=2, label="square rooter sqrt(d unit)")
ax1.plot(d, np.abs(d), "k:", lw=1, label="|d|")
ax1.set_xlabel("d = input - Vref [V]")
ax1.set_ylabel("Output [V] (from 0 V)")
ax1.set_ylim(-0.1, 3.3)
ax1.grid(True)
ax1.legend(loc="upper center", fontsize=8)

t = np.linspace(0, 2, 400)
ax2.plot(t, 2.5 + np.sin(2 * np.pi * t), lw=2, label="input: Vref + sin")
ax2.plot(t, np.sin(2 * np.pi * t)**2 / UNIT, lw=2, label="squarer: sin² / unit")
ax2.axhline(0.5 / UNIT, color="C1", ls="--", lw=1, label="mean A² / (2 unit)")
ax2.set_xlabel("Time [periods of the input]")
ax2.set_ylabel("Voltage [V]")
ax2.set_ylim(-0.1, 4.6)
ax2.grid(True)
ax2.legend(loc="upper right", fontsize=8)
fig.tight_layout()
save(fig, pathlib.Path(__file__).with_name("response.svg"))
