# SPDX-License-Identifier: MIT
"""Sample and hold: a switch (closed by the clock) charges C to the input; a voltage
follower buffers the voltage of C."""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "tools"))
from drawing import setup_drawing  # noqa: E402
import schemdraw.elements as elm  # noqa: E402

with setup_drawing(show=False) as d:
    d.add(elm.Dot(open=True).label("Vin", loc="left"))
    d.add(elm.Switch().right().label("SW (clock)"))
    p = d.here
    d.add(elm.Dot())
    d.add(elm.Line().right(1.0))
    op = d.add(elm.Opamp(leads=True).anchor("in2").right())
    d.add(elm.Capacitor().at(p).down().label("C", loc="bottom"))
    d.add(elm.Ground())
    d.add(elm.Line().at(op.out).right(0.75))
    out = d.here
    d.add(elm.Dot(open=True).label("Vout", loc="right"))
    xj = out[0] - 0.375
    d.add(elm.Dot().at((xj, op.out[1])))
    d.add(elm.Line().at(op.in1).left(0.5))
    d.add(elm.Line().up(1.25))
    d.add(elm.Line().tox(xj))
    d.add(elm.Line().toy(op.out))
    d.save(str(pathlib.Path(__file__).with_name("circuit.svg")))
print("wrote circuit.svg")
