# SPDX-License-Identifier: MIT
"""Sketch of the frequency response of the first-order LPF: H = 1 / (1 + j f/fc)."""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "tools"))
import numpy as np  # noqa: E402
from figures import frequencies, gain_sketch, save  # noqa: E402

x = frequencies()
h = 1 / (1 + 1j * x)
fig = gain_sketch(x, h, asymptotes=[([x[0], 1], [0, 0]), ([1, x[-1]], [0, -20 * np.log10(x[-1])])],
                  title="First-order LPF")
fig.axes[0].text(9, -12, "-20 dB / decade", color="gray")
save(fig, pathlib.Path(__file__).with_name("response.svg"))
