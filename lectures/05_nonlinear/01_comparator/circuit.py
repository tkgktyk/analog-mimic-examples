# SPDX-License-Identifier: MIT
"""Schmitt trigger: non-inverting comparator with positive feedback (R1 from the input, R2 from the output to the + input; - input at Vref)."""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "tools"))
from drawing import setup_drawing  # noqa: E402
import schemdraw.elements as elm  # noqa: E402

with setup_drawing(show=False) as d:
    d.add(elm.Dot(open=True).label("Vin", loc="left"))
    d.add(elm.Resistor().right().label("R1"))
    a = d.here
    d.add(elm.Dot())
    d.add(elm.Line().right(0.75))
    op = d.add(elm.Opamp(leads=True).anchor("in2").right())
    d.add(elm.Line().at(op.in1).left(0.75))
    d.add(elm.Dot(open=True).label("Vref", loc="left"))
    d.add(elm.Line().at(op.out).right(0.75))
    out = d.here
    d.add(elm.Dot(open=True).label("Vout", loc="right"))
    xj = out[0] - 0.375
    d.add(elm.Dot().at((xj, op.out[1])))
    d.add(elm.Line().at(a).down(1.75))
    d.add(elm.Resistor().tox(xj).label("R2"))
    d.add(elm.Line().toy(op.out))
    d.save(str(pathlib.Path(__file__).with_name("circuit.svg")))
print("wrote circuit.svg")
