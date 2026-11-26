# SPDX-License-Identifier: MIT
"""VCO as a block diagram: the input times the sign of the square wave (+1 / -1) is
integrated into a triangle whose slope follows the input; the Schmitt trigger turns it
at its thresholds, so the frequency is proportional to the input."""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "tools"))
from drawing import setup_drawing  # noqa: E402
import schemdraw.dsp as dsp  # noqa: E402

with setup_drawing(show=False) as d:
    d.add(dsp.Dot(open=True).label("Vin", loc="left"))
    d.add(dsp.Arrow().right(1.5))
    m = d.add(dsp.Mixer().anchor("W").label("x (+1 / -1)", loc="top", ofst=0.2))
    d.add(dsp.Arrow().at(m.E).right(1.0))
    b1 = d.add(dsp.Box(w=2.4, h=1.2).anchor("W").label("integrator"))
    d.add(dsp.Line().at(b1.E).right(0.75))
    t = d.here
    d.add(dsp.Dot().label("triangle", loc="top"))
    d.add(dsp.Arrow().right(1.0))
    b2 = d.add(dsp.Box(w=2.4, h=1.2).anchor("W").label("Schmitt"))
    d.add(dsp.Line().at(b2.E).right(0.75))
    s = d.here
    d.add(dsp.Dot())
    d.add(dsp.Arrow().right(1.0))
    d.add(dsp.Dot(open=True).label("square", loc="right"))
    d.add(dsp.Line().at(s).down(1.6))
    d.add(dsp.Line().tox(m.S))
    d.add(dsp.Arrow().to(m.S))
    d.save(str(pathlib.Path(__file__).with_name("circuit.svg")))
print("wrote circuit.svg")
