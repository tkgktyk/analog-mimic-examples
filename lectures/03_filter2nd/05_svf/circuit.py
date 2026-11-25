# SPDX-License-Identifier: MIT
"""State-variable filter as a block diagram: a summer and two integrators.

HP = Vin - BP / Q - LP,  BP = (w0 / s) HP,  LP = (w0 / s) BP.
"""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "tools"))
from drawing import setup_drawing  # noqa: E402
import schemdraw.dsp as dsp  # noqa: E402

with setup_drawing(show=False) as d:
    d.add(dsp.Dot(open=True).label("Vin", loc="left"))
    d.add(dsp.Arrow().right(1.5).label("+", loc="bottom", ofst=(0.5, 0)))
    s = d.add(dsp.SumSigma().anchor("W"))
    d.add(dsp.Line().at(s.E).right(1.0))
    hp = d.here
    d.add(dsp.Dot().label("HP", loc="top"))
    d.add(dsp.Arrow().right(1.0))
    i1 = d.add(dsp.Box(w=2, h=1.2).anchor("W").label("$\\omega_0 / s$"))
    d.add(dsp.Line().at(i1.E).right(1.0))
    bp = d.here
    d.add(dsp.Dot().label("BP", loc="top", ofst=(-0.5, 0.1)))
    d.add(dsp.Arrow().right(1.0))
    i2 = d.add(dsp.Box(w=2, h=1.2).anchor("W").label("$\\omega_0 / s$"))
    d.add(dsp.Line().at(i2.E).right(1.0))
    lp = d.here
    d.add(dsp.Dot())
    d.add(dsp.Arrow().right(1.0))
    d.add(dsp.Dot(open=True).label("LP", loc="right"))
    # Feedback of BP through 1 / Q (above) and of LP (below), both subtracted
    d.add(dsp.Line().at(bp).up(2.0))
    d.add(dsp.Arrow().left(1.0))
    g = d.add(dsp.Box(w=1.6, h=1.0).anchor("E").label("$1 / Q$"))
    d.add(dsp.Line().at(g.W).tox(s.N))
    d.add(dsp.Arrow().to(s.N).label("-", loc="left", ofst=(0, 0.3)))
    d.add(dsp.Line().at(lp).down(2.0))
    d.add(dsp.Line().tox(s.S))
    d.add(dsp.Arrow().to(s.S).label("-", loc="left", ofst=(0, 0.3)))
    d.save(str(pathlib.Path(__file__).with_name("circuit.svg")))
print("wrote circuit.svg")
