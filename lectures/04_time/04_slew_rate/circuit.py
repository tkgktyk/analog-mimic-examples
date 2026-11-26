# SPDX-License-Identifier: MIT
"""Slew rate: a voltage follower; inside the op-amp, a limited current I charges the
compensation capacitor Cc, so the output cannot change faster than SR = I / Cc."""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "tools"))
from drawing import setup_drawing  # noqa: E402
import schemdraw.elements as elm  # noqa: E402

with setup_drawing(show=False) as d:
    d.add(elm.Dot(open=True).label("Vin", loc="left"))
    d.add(elm.Line().right(1.0))
    op = d.add(elm.Opamp(leads=True).anchor("in2").right().label("SR = I / Cc", loc="bottom", ofst=0.6))
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
