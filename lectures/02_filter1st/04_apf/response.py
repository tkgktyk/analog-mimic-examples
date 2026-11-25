# SPDX-License-Identifier: MIT
"""Sketch of the frequency response of the first-order APF: H = (1 - j f/fc) / (1 + j f/fc)."""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "tools"))
from figures import frequencies, gain_phase_sketch, save  # noqa: E402

x = frequencies()
h = (1 - 1j * x) / (1 + 1j * x)
fig = gain_phase_sketch(x, h, title="First-order APF")
save(fig, pathlib.Path(__file__).with_name("response.svg"))
