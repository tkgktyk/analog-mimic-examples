# SPDX-License-Identifier: MIT
"""Delay line as a bucket-brigade device (BBD): switches closed by two alternating
clocks pass the charge from one capacitor to the next; a voltage follower buffers the
last one. Mimic: 4096 stages (one per 5 us sample)."""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "tools"))
from drawing import setup_drawing  # noqa: E402
import schemdraw.elements as elm  # noqa: E402

with setup_drawing(show=False) as d:
    d.add(elm.Dot(open=True).label("Vin", loc="left"))
    for k, clock in enumerate(("φ1", "φ2", "φ1")):
        d.add(elm.Switch().right().label(clock))
        p = d.here
        d.add(elm.Dot())
        d.add(elm.Capacitor().at(p).down().label(f"C{k + 1}", loc="bottom"))
        d.add(elm.Ground())
        d.add(elm.Line().at(p).right(0.5))
    d.add(elm.Gap().right(1.0).label("· · ·"))
    d.add(elm.Line().right(0.5))
    op = d.add(elm.Opamp(leads=True).anchor("in2").right())
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
