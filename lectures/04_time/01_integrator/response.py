# SPDX-License-Identifier: MIT
"""Sketch of the integrator: ideal 1 / (j f/fi) and with a leak L / (1 + j L f/fi),
L = leak time / integration time = 10; fi = 1 / (2 pi tau_i)."""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "tools"))
from figures import frequencies, gain_family_sketch, save  # noqa: E402

x = frequencies()
leak = 10
curves = [("ideal", 1 / (1j * x)), (f"with leak (leak = {leak} x tau_i)", leak / (1 + 1j * leak * x))]
fig = gain_family_sketch(x, curves, ylim=(-45, 45), title="Integrator", mark=(0, "fi (0 dB)"),
                         xlabel="Frequency  f / fi    (fi = 1 / (2 pi tau_i))", legend_loc="upper right")
fig.axes[0].text(4, -8, "-20 dB / decade", color="gray")
save(fig, pathlib.Path(__file__).with_name("response.svg"))
