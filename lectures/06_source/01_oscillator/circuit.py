# SPDX-License-Identifier: MIT
"""Function generator: an integrator (R, C) and a Schmitt trigger (R1, R2) in a loop.
The square wave of the Schmitt trigger is integrated into a triangle; the triangle
flips the Schmitt trigger at its thresholds."""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "tools"))
from drawing import setup_drawing  # noqa: E402
import schemdraw.elements as elm  # noqa: E402

with setup_drawing(show=False) as d:
    op1 = d.add(elm.Opamp(leads=True))
    d.add(elm.Line().at(op1.in2).down(0.75))
    d.add(elm.Ground())
    d.add(elm.Line().at(op1.in1).left(0.5))
    n = d.here
    d.add(elm.Dot())
    d.add(elm.Resistor().left().label("R"))
    a = d.here
    d.add(elm.Line().at(op1.out).right(0.75))
    tri = d.here
    d.add(elm.Dot())
    d.add(elm.Label().at((tri[0], tri[1] - 0.5)).label("triangle"))
    d.add(elm.Line().at(n).up(1.5))
    d.add(elm.Capacitor().tox(tri).label("C"))
    d.add(elm.Line().toy(tri))
    d.add(elm.Resistor().at(tri).right().label("R1"))
    op2 = d.add(elm.Opamp(leads=True).anchor("in2").right().flip())
    d.add(elm.Line().at(op2.in1).down(0.75))
    d.add(elm.Ground())
    d.add(elm.Line().at(op2.out).right(0.75))
    sq = d.here
    d.add(elm.Dot())
    d.add(elm.Line().right(1.0))
    loop = d.here
    d.add(elm.Dot())
    d.add(elm.Line().right(0.5))
    d.add(elm.Dot(open=True).label("Vout (square)", loc="right"))
    d.add(elm.Line().at(op2.in2).left(0.4))
    p = d.here
    d.add(elm.Dot())
    d.add(elm.Line().up(1.25))
    d.add(elm.Resistor().tox(sq).label("R2"))
    d.add(elm.Line().toy(sq))
    d.add(elm.Line().at(loop).down(2.75))
    d.add(elm.Line().tox(a))
    d.add(elm.Line().toy(a))
    d.save(str(pathlib.Path(__file__).with_name("circuit.svg")))
print("wrote circuit.svg")
