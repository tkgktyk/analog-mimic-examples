# SPDX-License-Identifier: MIT
"""First-order low-pass filter: RC and a voltage follower (gain 1)."""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "tools"))
from drawing import setup_drawing  # noqa: E402
import schemdraw.elements as elm  # noqa: E402

with setup_drawing(show=False) as d:
    d.add(elm.Dot(open=True).label("Vin", loc="left"))
    d.add(elm.Resistor().right().label("R"))
    d.add(elm.Dot())
    node = d.here
    d.add(elm.Line().right(0.75))
    op = d.add(elm.Opamp(leads=True).anchor("in2").right())
    # Voltage follower: output back to the inverting input
    d.add(elm.Line().at(op.out).right(0.75))
    out = d.here
    d.add(elm.Dot(open=True).label("Vout", loc="right"))
    d.add(elm.Line().at(op.in1).up(1.0))
    d.add(elm.Line().tox(out[0] - 0.375))
    d.add(elm.Line().toy(op.out))
    d.add(elm.Dot().at((out[0] - 0.375, op.out[1])))
    d.add(elm.Capacitor().at(node).down().label("C", loc="bottom"))
    d.add(elm.Ground())
    d.save(str(pathlib.Path(__file__).with_name("circuit.svg")))
print("wrote circuit.svg")
