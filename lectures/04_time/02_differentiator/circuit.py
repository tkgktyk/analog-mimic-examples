# SPDX-License-Identifier: MIT
"""Differentiator: inverting op-amp differentiator (input C, feedback Rf) with a series
resistor Rs that limits the gain at high frequencies."""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "tools"))
from drawing import setup_drawing  # noqa: E402
import schemdraw.elements as elm  # noqa: E402

with setup_drawing(show=False) as d:
    op = d.add(elm.Opamp(leads=True))
    d.add(elm.Line().at(op.in2).down(0.75))
    d.add(elm.Ground())
    d.add(elm.Line().at(op.in1).left(0.5))
    n = d.here
    d.add(elm.Dot())
    d.add(elm.Capacitor().left().label("C"))
    d.add(elm.Resistor().left().label("Rs"))
    d.add(elm.Dot(open=True).label("Vin", loc="left"))
    d.add(elm.Line().at(op.out).right(0.75))
    out = d.here
    d.add(elm.Dot(open=True).label("Vout", loc="right"))
    xj = out[0] - 0.375
    d.add(elm.Line().at(n).up(1.5))
    d.add(elm.Resistor().tox(xj).label("Rf"))
    d.add(elm.Line().toy(op.out))
    d.add(elm.Dot().at((xj, op.out[1])))
    d.save(str(pathlib.Path(__file__).with_name("circuit.svg")))
print("wrote circuit.svg")
