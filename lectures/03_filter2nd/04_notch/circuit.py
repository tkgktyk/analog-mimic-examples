# SPDX-License-Identifier: MIT
"""Notch filter: twin-T network and a voltage follower (fc = 1 / (2 pi R C), Q = 1/4)."""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "tools"))
from drawing import setup_drawing  # noqa: E402
import schemdraw.elements as elm  # noqa: E402

with setup_drawing(show=False) as d:
    d.add(elm.Dot(open=True).label("Vin", loc="left"))
    vin = d.here
    d.add(elm.Line().right(0.75))
    d.add(elm.Dot())
    top = d.here
    d.add(elm.Resistor().right().label("R"))
    m1 = d.here
    d.add(elm.Dot())
    d.add(elm.Resistor().right().label("R"))
    n = d.here
    d.add(elm.Dot())
    d.add(elm.Capacitor().at(m1).up().label("2C"))
    d.add(elm.Ground().theta(180))
    # Lower T
    d.add(elm.Line().at(top).down(3.0))
    d.add(elm.Capacitor().right().label("C"))
    m2 = d.here
    d.add(elm.Dot())
    d.add(elm.Capacitor().right().label("C"))
    d.add(elm.Line().toy(n))
    d.add(elm.Resistor().at(m2).down().label("R/2", loc="bottom"))
    d.add(elm.Ground())
    # Follower
    d.add(elm.Line().at(n).right(0.75))
    op = d.add(elm.Opamp(leads=True).anchor("in2").right())
    d.add(elm.Line().at(op.out).right(0.75))
    out = d.here
    d.add(elm.Dot(open=True).label("Vout", loc="right"))
    d.add(elm.Line().at(op.in1).up(1.0))
    d.add(elm.Line().tox(out[0] - 0.375))
    d.add(elm.Line().toy(op.out))
    d.add(elm.Dot().at((out[0] - 0.375, op.out[1])))
    d.save(str(pathlib.Path(__file__).with_name("circuit.svg")))
print("wrote circuit.svg")
