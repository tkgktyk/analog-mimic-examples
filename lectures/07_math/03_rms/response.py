# SPDX-License-Identifier: MIT
"""Sine, triangle and square of the same amplitude: the true RMS (solid) and the reading
of an average-responding meter, mean |d| x 1.111 (dashed), which is right only for a sine."""
import sys
import pathlib

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "tools"))
from figures import save  # noqa: E402

FORM = np.pi / (2 * np.sqrt(2))   # rms / mean |d| of a sine, 1.111
ph = np.linspace(0, 2, 801, endpoint=False) % 1.0
waves = {
    "sine": np.sin(2 * np.pi * ph),
    "triangle": np.where((ph + 0.25) % 1.0 < 0.5, 4 * ((ph + 0.25) % 1.0) - 1, 3 - 4 * ((ph + 0.25) % 1.0)),
    "square": np.where(ph < 0.5, 1.0, -1.0),
}
fig, axes = plt.subplots(1, 3, figsize=(10, 3), sharey=True)
x = np.linspace(0, 2, 801, endpoint=False)
for ax, (name, w) in zip(axes, waves.items()):
    rms = np.sqrt(np.mean(w**2))
    avg = np.mean(np.abs(w)) * FORM
    ax.plot(x, w, color="0.6", lw=1.5)
    ax.axhline(rms, color="C0", lw=2, label=f"true RMS {rms:.3f}")
    ax.axhline(avg, color="C1", lw=2, ls="--", label=f"average x 1.111: {avg:.3f}")
    ax.set_title(f"{name} ({round((avg / rms - 1) * 100, 1) + 0.0:+.1f} %)")
    ax.set_xlabel("Time [periods]")
    ax.set_ylim(-1.2, 1.9)
    ax.grid(True)
    ax.legend(loc="upper center", fontsize=7.5)
axes[0].set_ylabel("d / amplitude")
fig.tight_layout()
save(fig, pathlib.Path(__file__).with_name("response.svg"))
