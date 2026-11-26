# SPDX-License-Identifier: MIT
"""Frequency of the VCO against the input: f = f0 + k (Vin - Vref), not below 0."""
import sys
import pathlib

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "tools"))
from figures import save  # noqa: E402

v = np.linspace(-2, 2, 401)            # input - Vref [V]
f0, k = 1.0, 0.8
f = np.clip(f0 + k * v, 0, None)
fig, ax = plt.subplots(figsize=(5.2, 3.2))
ax.plot(v, f, lw=2)
ax.plot(0, f0, "o", color="C0")
ax.annotate("f0 (at Vref)", (0, f0), (0.3, 0.45), arrowprops=dict(arrowstyle="->", color="gray"))
ax.annotate("slope k [Hz/V]", (1.0, f0 + k), (-0.2, 2.3), arrowprops=dict(arrowstyle="->", color="gray"))
ax.text(-1.95, 0.1, "stops at 0 Hz", color="gray")
ax.set_xlim(-2, 2)
ax.set_ylim(0, 2.8)
ax.set_xticks([-2, -1, 0, 1, 2])
ax.set_yticks([])
ax.set_xlabel("Input - Vref [V]")
ax.set_ylabel("Frequency")
ax.set_title("VCO: f = f0 + k (Vin - Vref)")
fig.tight_layout()
save(fig, pathlib.Path(__file__).with_name("response.svg"))
