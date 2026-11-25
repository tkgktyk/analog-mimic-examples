# SPDX-License-Identifier: MIT
"""Sketch of the second-order BPF (0 dB at fc) for several Q: H = (s/Q) / (s^2 + s/Q + 1)."""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "tools"))
import numpy as np  # noqa: E402
from figures import frequencies, biquad, gain_family_sketch, save  # noqa: E402

x = frequencies()

curves = [(f"Q = {q}", biquad(x, "bpf", q)) for q in (0.5, 2, 10)]
fig = gain_family_sketch(x, curves, ylim=(-50, 10), title="Second-order BPF", mark=(0, "fc (0 dB)"))
save(fig, pathlib.Path(__file__).with_name("response.svg"))
