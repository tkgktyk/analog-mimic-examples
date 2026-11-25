# SPDX-License-Identifier: MIT
"""Peak detector: a super diode charges C; R across C discharges it (envelope follower), a switch across C resets it (peak hold)."""
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
    d.add(elm.Line().at(op.in1).left(0.5))
    d.add(elm.Line().up(1.25))
    d.add(elm.Line().tox(p))
    d.add(elm.Line().toy(p))
    xs = [p[0] + 1.0, p[0] + 2.5, p[0] + 4.0]
    d.add(elm.Line().at(p).tox(xs[-1] + 1.25))
    d.add(elm.Dot(open=True).label("Vout", loc="right"))
    d.add(elm.Capacitor().at((xs[0], p[1])).down().label("C", loc="bottom"))
    d.add(elm.Ground())
    d.add(elm.Resistor().at((xs[1], p[1])).down().label("R", loc="bottom"))
    d.add(elm.Ground())
    d.add(elm.Switch().at((xs[2], p[1])).down().label("reset", loc="bottom"))
    d.add(elm.Ground())
    for x in xs:
        d.add(elm.Dot().at((x, p[1])))
    d.save(str(pathlib.Path(__file__).with_name("circuit.svg")))
print("wrote circuit.svg")
