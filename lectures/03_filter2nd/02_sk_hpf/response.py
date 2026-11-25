# SPDX-License-Identifier: MIT
"""Sketch of the second-order HPF for several Q: H = s^2 / (s^2 + s/Q + 1)."""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "tools"))
import numpy as np  # noqa: E402
from figures import frequencies, biquad, gain_family_sketch, save  # noqa: E402

x = frequencies()

curves = [(f"Q = {q}", biquad(x, "hpf", q)) for q in (0.5, 0.707, 2)]
fig = gain_family_sketch(x, curves, asymptotes=[([x[0], 1], [40 * np.log10(x[0]), 0]), ([1, x[-1]], [0, 0])],
                         title="Second-order HPF")
fig.axes[0].legend(loc="lower right", fontsize=9)
fig.axes[0].text(0.012, -30, "+40 dB / decade", color="gray")
save(fig, pathlib.Path(__file__).with_name("response.svg"))
