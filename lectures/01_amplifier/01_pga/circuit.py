# SPDX-License-Identifier: MIT
"""Non-inverting amplifier (G = 1 + Rf / Rg) and inverting amplifier (G = -Rf / Rin)."""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "tools"))
from drawing import setup_drawing  # noqa: E402
import schemdraw.elements as elm  # noqa: E402

here = pathlib.Path(__file__).parent

# Non-inverting: (+) on top
with setup_drawing(show=False) as d:
    op = d.add(elm.Opamp(leads=True).flip())
    d.add(elm.Line().at(op.in2).left(1.0))
    d.add(elm.Dot(open=True).label("Vin", loc="left"))
    d.add(elm.Line().at(op.out).right(0.75))
    out = d.here
    d.add(elm.Dot(open=True).label("Vout", loc="right"))
    d.add(elm.Line().at(op.in1).left(0.5))
    d.add(elm.Line().down(1.25))
    m = d.here
    d.add(elm.Dot())
    d.add(elm.Resistor().right().tox(out[0] - 0.375).label("Rf"))
    d.add(elm.Line().toy(op.out))
    d.add(elm.Dot().at((out[0] - 0.375, op.out[1])))
    d.add(elm.Resistor().at(m).down().label("Rg", loc="bottom"))
    d.add(elm.Ground())
    d.save(str(here / "circuit_noninverting.svg"))

# Inverting
with setup_drawing(show=False) as d:
    op = d.add(elm.Opamp(leads=True))
    d.add(elm.Line().at(op.in2).down(0.75))
    d.add(elm.Ground())
    d.add(elm.Line().at(op.in1).left(0.5))
    n = d.here
    d.add(elm.Dot())
    d.add(elm.Resistor().left().label("Rin"))
    d.add(elm.Dot(open=True).label("Vin", loc="left"))
    d.add(elm.Line().at(op.out).right(0.75))
    out = d.here
    d.add(elm.Dot(open=True).label("Vout", loc="right"))
    d.add(elm.Line().at(n).up(1.5))
    d.add(elm.Resistor().tox(out[0] - 0.375).label("Rf"))
    d.add(elm.Line().toy(op.out))
    d.add(elm.Dot().at((out[0] - 0.375, op.out[1])))
    d.save(str(here / "circuit_inverting.svg"))
print("wrote circuit_noninverting.svg, circuit_inverting.svg")
