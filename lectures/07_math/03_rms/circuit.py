# SPDX-License-Identifier: MIT
"""True RMS-to-DC converter as a block diagram: square, average (the averaging capacitor),
square root."""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "tools"))
from drawing import setup_drawing  # noqa: E402
import schemdraw.dsp as dsp  # noqa: E402

with setup_drawing(show=False) as d:
    d.add(dsp.Dot(open=True).label("Vin", loc="left"))
    d.add(dsp.Arrow().right(1.2))
    b = d.add(dsp.Box(w=2.0, h=1.2).anchor("W").label("square"))
    d.add(dsp.Arrow().at(b.E).right(1.2))
    b = d.add(dsp.Box(w=2.0, h=1.2).anchor("W").label("average"))
    d.add(dsp.Arrow().at(b.E).right(1.2))
    b = d.add(dsp.Box(w=2.0, h=1.2).anchor("W").label("square root"))
    d.add(dsp.Arrow().at(b.E).right(1.2))
    d.add(dsp.Dot(open=True).label("Vout (DC)", loc="right"))
    d.save(str(pathlib.Path(__file__).with_name("circuit.svg")))
print("wrote circuit.svg")
