# SPDX-License-Identifier: MIT
"""Precision half-wave rectifier (super diode): the op-amp drives the diode, the feedback from the cathode cancels the diode drop; load R to Vref."""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "tools"))
from drawing import setup_drawing  # noqa: E402
import schemdraw.elements as elm  # noqa: E402

with setup_drawing(show=False) as d:
    d.add(elm.Dot(open=True).label("Vin", loc="left"))
    d.add(elm.Line().right(1.0))
    op = d.add(elm.Opamp(leads=True).anchor("in2").right())
    d.add(elm.Diode().at(op.out).right().label("D"))
    p = d.here
    d.add(elm.Dot())
    d.add(elm.Line().right(1.5))
    d.add(elm.Dot(open=True).label("Vout", loc="right"))
    d.add(elm.Line().at(op.in1).left(0.5))
    d.add(elm.Line().up(1.25))
    d.add(elm.Line().tox(p))
    d.add(elm.Line().toy(p))
    d.add(elm.Resistor().at((p[0] + 0.9, p[1])).down().label("R", loc="bottom"))
    d.add(elm.Ground())
    d.add(elm.Dot().at((p[0] + 0.9, p[1])))
    d.save(str(pathlib.Path(__file__).with_name("circuit.svg")))
print("wrote circuit.svg")
