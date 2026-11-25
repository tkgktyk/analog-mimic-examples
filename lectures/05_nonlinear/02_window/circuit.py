# SPDX-License-Identifier: MIT
"""Window comparator: two comparators (Vin > VH, Vin < VL) joined by diodes (OR) with a pull-down resistor."""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "tools"))
from drawing import setup_drawing  # noqa: E402
import schemdraw.elements as elm  # noqa: E402

with setup_drawing(show=False) as d:
    a = d.add(elm.Opamp(leads=True).anchor("center").at((0, 1.6)))
    b = d.add(elm.Opamp(leads=True).anchor("center").at((0, -1.6)))
    xl = a.in2[0] - 1.25
    d.add(elm.Line().at(a.in2).tox(xl))
    d.add(elm.Line().toy(b.in1))
    d.add(elm.Line().tox(b.in1))
    d.add(elm.Dot().at((xl, 0)))
    d.add(elm.Line().at((xl, 0)).left(1.0))
    d.add(elm.Dot(open=True).label("Vin", loc="left"))
    d.add(elm.Line().at(a.in1).left(1.0))
    d.add(elm.Dot(open=True).label("VH", loc="left"))
    d.add(elm.Line().at(b.in2).left(1.0))
    d.add(elm.Dot(open=True).label("VL", loc="left"))
    d.add(elm.Diode().at(a.out).right())
    xn = d.here[0]
    d.add(elm.Line().toy(0))
    d.add(elm.Diode().at(b.out).right())
    d.add(elm.Line().toy(0))
    d.add(elm.Dot().at((xn, 0)))
    d.add(elm.Line().at((xn, 0)).right(1.25))
    m = d.here
    d.add(elm.Dot())
    d.add(elm.Line().right(1.0))
    d.add(elm.Dot(open=True).label("Vout", loc="right"))
    d.add(elm.Resistor().at(m).down().label("R", loc="bottom"))
    d.add(elm.Ground())
    d.save(str(pathlib.Path(__file__).with_name("circuit.svg")))
print("wrote circuit.svg")
