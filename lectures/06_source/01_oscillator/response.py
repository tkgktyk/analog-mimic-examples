# SPDX-License-Identifier: MIT
"""The four waveforms of the oscillator over two periods: every one starts at Vref and rises."""
import sys
import pathlib

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "tools"))
from figures import save  # noqa: E402

ph = np.linspace(0, 2, 4001)
p = ph % 1
waves = {
    "sine": np.sin(2 * np.pi * p),
    "triangle": np.where((p + 0.25) % 1 < 0.5, 4 * ((p + 0.25) % 1) - 1, 3 - 4 * ((p + 0.25) % 1)),
    "square": np.where(p < 0.5, 1.0, -1.0),
    "sawtooth": 2 * ((p + 0.5) % 1) - 1,
}
fig, axes = plt.subplots(1, 4, figsize=(10, 2.6), sharey=True)
for ax, (name, w) in zip(axes, waves.items()):
    w = w.copy()
    w[1:][np.abs(np.diff(w)) > 0.5] = np.nan   # no vertical lines at the jumps
    ax.plot(ph, w, lw=2)
    ax.axhline(0, color="gray", ls=":", lw=1)
    ax.set_title(name)
    ax.set_xlim(0, 2)
    ax.set_xticks([0, 1, 2])
    ax.set_ylim(-1.3, 1.3)
    ax.set_xlabel("Time [periods]")
axes[0].set_ylabel("(output - Vref) / amplitude")
fig.tight_layout()
save(fig, pathlib.Path(__file__).with_name("response.svg"))
