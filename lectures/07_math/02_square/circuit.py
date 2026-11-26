# SPDX-License-Identifier: MIT
"""Squarer (a multiplier with both inputs tied) and square rooter (a multiplier in the
feedback of an inverting amplifier), as block diagrams."""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "tools"))
from drawing import setup_drawing  # noqa: E402
import schemdraw.dsp as dsp  # noqa: E402
import schemdraw.elements as elm  # noqa: E402

here = pathlib.Path(__file__).parent

# Squarer
with setup_drawing(show=False) as d:
    d.add(dsp.Dot(open=True).label("Vin", loc="left"))
    d.add(dsp.Line().right(1.0))
    j = d.here
    d.add(dsp.Dot())
    d.add(dsp.Arrow().right(1.5))
    m = d.add(dsp.Mixer().anchor("W"))
    d.add(dsp.Line().at(j).down(1.6))
    d.add(dsp.Line().tox(m.S))
    d.add(dsp.Arrow().toy(m.S))
    d.add(dsp.Arrow().at(m.E).right(1.5))
    d.add(dsp.Dot(open=True).label("Vout", loc="right"))
    d.save(str(here / "circuit_squarer.svg"))

# Square rooter: the op-amp makes the squared output equal to the input current
with setup_drawing(show=False) as d:
    op = d.add(elm.Opamp(leads=True))
    d.add(elm.Line().at(op.in2).down(0.75))
    d.add(elm.Ground())
    d.add(elm.Line().at(op.in1).left(0.5))
    n = d.here
    d.add(elm.Dot())
    d.add(elm.Resistor().left().label("R"))
    d.add(elm.Dot(open=True).label("Vin", loc="left"))
    d.add(elm.Line().at(op.out).right(1.0))
    out = d.here
    d.add(elm.Dot(open=True).label("Vout", loc="right"))
    xo = out[0] - 0.5
    d.add(elm.Dot().at((xo, op.out[1])))
    y1 = op.out[1] + 2.4
    m = d.add(dsp.Mixer().at((op.center[0] + 0.6, y1)).anchor("center"))
    d.add(elm.Line().at((xo, op.out[1])).toy(y1))
    d.add(elm.Dot())
    d.add(dsp.Arrow().tox(m.E))
    d.add(elm.Line().at((xo, y1)).up(1.4))
    d.add(elm.Line().tox(m.N))
    d.add(dsp.Arrow().toy(m.N))
    d.add(elm.Resistor().at(m.W).tox(n[0]).label("R"))
    d.add(elm.Line().toy(n))
    d.save(str(here / "circuit_rooter.svg"))
print("wrote circuit_squarer.svg, circuit_rooter.svg")
