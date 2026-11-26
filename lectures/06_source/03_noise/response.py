# SPDX-License-Identifier: MIT
"""White and pink noise: the spectrum (left: flat, and -3 dB per octave) and the
distribution of the voltage (right: uniform for the white noise of the module, bell
shaped for the pink one)."""
import sys
import pathlib

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "tools"))
from figures import save  # noqa: E402

f = np.logspace(1, 4, 200)
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.5, 3.2))
ax1.semilogx(f, np.zeros_like(f), lw=2, label="white: flat")
ax1.semilogx(f, -10 * np.log10(f / 10), lw=2, label="pink: -3 dB / octave")
ax1.set_xlim(10, 1e4)
ax1.set_ylim(-35, 8)
ax1.set_xlabel("Frequency [Hz]")
ax1.set_ylabel("Power per Hz [dB]")
ax1.set_title("Spectrum")
ax1.grid(True, which="both", alpha=0.4)
ax1.legend(loc="lower left", fontsize=9)

v = np.linspace(-1.2, 1.2, 481)
ax2.plot(v, np.where(np.abs(v) <= 1, 0.5, 0.0), lw=2, label="white (uniform, rms A / sqrt 3)")
s = 1 / 3
ax2.plot(v, np.exp(-v**2 / (2 * s**2)) / (s * np.sqrt(2 * np.pi)), lw=2, label="pink (bell, rms A / 3)")
ax2.set_xlim(-1.2, 1.2)
ax2.set_ylim(0, 1.6)
ax2.set_xlabel("(output - Vref) / amplitude A")
ax2.set_yticks([])
ax2.set_title("Distribution of the voltage")
ax2.legend(loc="upper right", fontsize=8)
fig.tight_layout()
save(fig, pathlib.Path(__file__).with_name("response.svg"))
