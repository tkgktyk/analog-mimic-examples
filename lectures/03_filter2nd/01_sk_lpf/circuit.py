# SPDX-License-Identifier: MIT
"""Second-order low-pass filter: Sallen-Key, unity gain (equal R; C1 to the output, C2 to ground)."""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "tools"))
from drawing import setup_drawing  # noqa: E402
import schemdraw.elements as elm  # noqa: E402

with setup_drawing(show=False) as d:
    d.add(elm.Dot(open=True).label("Vin", loc="left"))
    d.add(elm.Resistor().right().label("R"))
    a = d.here
    d.add(elm.Dot())
    d.add(elm.Resistor().right().label("R"))
    b = d.here
    d.add(elm.Dot())
    d.add(elm.Line().right(0.75))
    op = d.add(elm.Opamp(leads=True).anchor("in2").right())
    d.add(elm.Line().at(op.out).right(0.75))
    out = d.here
    d.add(elm.Dot(open=True).label("Vout", loc="right"))
    xj = out[0] - 0.375
    d.add(elm.Line().at(op.in1).up(1.0))
    d.add(elm.Line().tox(xj))
    yf = d.here[1]
    d.add(elm.Line().toy(op.out))
    d.add(elm.Dot().at((xj, op.out[1])))
    d.add(elm.Capacitor().at(a).up().toy(yf + 1.25).label("C1"))
    d.add(elm.Line().tox(xj))
    d.add(elm.Line().toy(yf))
    d.add(elm.Dot().at((xj, yf)))
    d.add(elm.Capacitor().at(b).down().label("C2", loc="bottom"))
    d.add(elm.Ground())
    d.save(str(pathlib.Path(__file__).with_name("circuit.svg")))
print("wrote circuit.svg")
