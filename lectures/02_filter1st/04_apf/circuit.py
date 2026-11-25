# SPDX-License-Identifier: MIT
"""First-order all-pass filter: H = (1 - sRC) / (1 + sRC) (two equal resistors R1)."""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "tools"))
from drawing import setup_drawing  # noqa: E402
import schemdraw.elements as elm  # noqa: E402

with setup_drawing(show=False) as d:
    op = d.add(elm.Opamp(leads=True))
    d.add(elm.Line().at(op.in1).left(0.5))
    n = d.here
    d.add(elm.Dot())
    d.add(elm.Resistor().left().label("R1"))
    vin = d.here
    d.add(elm.Dot())
    d.add(elm.Line().left(0.75))
    d.add(elm.Dot(open=True).label("Vin", loc="left"))
    d.add(elm.Line().at(op.out).right(0.75))
    out = d.here
    d.add(elm.Dot(open=True).label("Vout", loc="right"))
    d.add(elm.Line().at(n).up(1.5))
    d.add(elm.Resistor().tox(out[0] - 0.375).label("R1"))
    d.add(elm.Line().toy(op.out))
    d.add(elm.Dot().at((out[0] - 0.375, op.out[1])))
    # Non-inverting input: R from Vin, C to ground
    d.add(elm.Line().at(op.in2).left(0.5))
    p = d.here
    d.add(elm.Dot())
    d.add(elm.Line().at(vin).toy(p))
    d.add(elm.Resistor().right().tox(p[0]).label("R"))
    d.add(elm.Capacitor().at(p).down().label("C", loc="bottom"))
    d.add(elm.Ground())
    d.save(str(pathlib.Path(__file__).with_name("circuit.svg")))
print("wrote circuit.svg")
