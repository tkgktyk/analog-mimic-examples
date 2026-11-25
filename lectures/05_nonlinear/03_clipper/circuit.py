# SPDX-License-Identifier: MIT
"""Diode clipper: series R, a diode to the upper bias voltage VH and a reversed diode to the lower bias voltage VL."""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "tools"))
from drawing import setup_drawing  # noqa: E402
import schemdraw.elements as elm  # noqa: E402

with setup_drawing(show=False) as d:
    d.add(elm.Dot(open=True).label("Vin", loc="left"))
    d.add(elm.Resistor().right().label("R"))
    n1 = d.here
    d.add(elm.Dot())
    d.add(elm.Line().right(2.0))
    n2 = d.here
    d.add(elm.Dot())
    d.add(elm.Line().right(1.25))
    d.add(elm.Dot(open=True).label("Vout", loc="right"))
    d.add(elm.Diode().at(n1).down().label("D1", loc="bottom"))
    d.add(elm.Battery().down().reverse().label("VH", loc="bottom"))
    d.add(elm.Ground())
    d.add(elm.Diode().at(n2).down().reverse().label("D2", loc="bottom"))
    d.add(elm.Battery().down().reverse().label("VL", loc="bottom"))
    d.add(elm.Ground())
    d.save(str(pathlib.Path(__file__).with_name("circuit.svg")))
print("wrote circuit.svg")
