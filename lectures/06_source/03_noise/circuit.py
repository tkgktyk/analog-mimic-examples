# SPDX-License-Identifier: MIT
"""Noise source: a Zener diode in breakdown, fed through R, is the noise; C passes only
the fluctuation to a non-inverting amplifier (Rf, Rg)."""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "tools"))
from drawing import setup_drawing  # noqa: E402
import schemdraw.elements as elm  # noqa: E402

with setup_drawing(show=False) as d:
    d.add(elm.Vdd().label("+V"))
    d.add(elm.Resistor().down().label("R"))
    z = d.here
    d.add(elm.Dot())
    d.add(elm.Zener().down().reverse().label("Zener", loc="bottom"))
    d.add(elm.Ground())
    d.add(elm.Capacitor().at(z).right().label("C"))
    d.add(elm.Line().right(0.5))
    op = d.add(elm.Opamp(leads=True).anchor("in2").right().flip())
    d.add(elm.Line().at(op.out).right(0.75))
    out = d.here
    d.add(elm.Dot(open=True).label("Vout", loc="right"))
    xj = out[0] - 0.375
    d.add(elm.Dot().at((xj, op.out[1])))
    d.add(elm.Line().at(op.in1).left(0.5))
    d.add(elm.Line().down(1.0))
    g = d.here
    d.add(elm.Dot())
    d.add(elm.Resistor().down().label("Rg", loc="bottom"))
    d.add(elm.Ground())
    rf = d.add(elm.Resistor().at(g).tox(xj))
    d.add(elm.Label().at((rf.center[0], g[1] - 0.6)).label("Rf"))
    d.add(elm.Line().toy(op.out))
    d.save(str(pathlib.Path(__file__).with_name("circuit.svg")))
print("wrote circuit.svg")
