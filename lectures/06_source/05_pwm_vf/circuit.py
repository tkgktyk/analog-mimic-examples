# SPDX-License-Identifier: MIT
"""PWM modulator: a comparator between the input (+) and a triangle carrier (-)."""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "tools"))
from drawing import setup_drawing  # noqa: E402
import schemdraw.elements as elm  # noqa: E402

with setup_drawing(show=False) as d:
    d.add(elm.Dot(open=True).label("Vin", loc="left"))
    d.add(elm.Line().right(1.5))
    op = d.add(elm.Opamp(leads=True).anchor("in2").right().flip())
    d.add(elm.Line().at(op.out).right(0.75))
    d.add(elm.Dot(open=True).label("PWM out", loc="right"))
    d.add(elm.Line().at(op.in1).left(0.75))
    d.add(elm.SourceTriangle().down().label("carrier", loc="bottom"))
    d.add(elm.Ground())
    d.save(str(pathlib.Path(__file__).with_name("circuit.svg")))
print("wrote circuit.svg")
