# SPDX-License-Identifier: MIT
"""Sketch of the notch filter for several Q: H = (s^2 + 1) / (s^2 + s/Q + 1)."""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "tools"))
import numpy as np  # noqa: E402
from figures import frequencies, biquad, gain_family_sketch, save  # noqa: E402

x = frequencies()

x = frequencies(points=2001)  # an odd count puts a point exactly at fc
curves = [(f"Q = {q}", biquad(x, "notch", q)) for q in (0.25, 1, 5)]
fig = gain_family_sketch(x, curves, ylim=(-50, 5), title="Notch filter")
save(fig, pathlib.Path(__file__).with_name("response.svg"))
