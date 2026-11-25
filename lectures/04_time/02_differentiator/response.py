# SPDX-License-Identifier: MIT
"""Sketch of the differentiator: ideal j f/fd and with a limit (j f/fd) / (1 + j r f/fd),
r = limit time / differentiation time = 0.1; fd = 1 / (2 pi tau_d)."""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "tools"))
from figures import frequencies, gain_family_sketch, save  # noqa: E402

x = frequencies()
r = 0.1
curves = [("ideal", 1j * x), (f"with limit (limit = {r} x tau_d)", 1j * x / (1 + 1j * r * x))]
fig = gain_family_sketch(x, curves, ylim=(-45, 45), title="Differentiator", mark=(0, "fd (0 dB)"),
                         xlabel="Frequency  f / fd    (fd = 1 / (2 pi tau_d))", legend_loc="upper left")
fig.axes[0].text(0.02, -20, "+20 dB / decade", color="gray")
save(fig, pathlib.Path(__file__).with_name("response.svg"))
