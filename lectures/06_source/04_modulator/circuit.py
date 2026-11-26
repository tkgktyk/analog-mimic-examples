# SPDX-License-Identifier: MIT
"""AM / ring modulator as a block diagram: the input plus a bias A, times the carrier of
an oscillator. A = 0 gives the ring (balanced, DSB) modulator."""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "tools"))
from drawing import setup_drawing  # noqa: E402
import schemdraw.dsp as dsp  # noqa: E402
import schemdraw.elements as elm  # noqa: E402

with setup_drawing(show=False) as d:
    d.add(dsp.Dot(open=True).label("Vin (signal)", loc="left"))
    d.add(dsp.Arrow().right(1.5))
    s = d.add(dsp.Sum().anchor("W"))
    d.add(dsp.Line().at(s.N).up(1.0))
    d.add(dsp.Dot(open=True).label("A (0: ring)", loc="top"))
    d.add(dsp.Arrow().at(s.E).right(1.5))
    m = d.add(dsp.Mixer().anchor("W"))
    d.add(dsp.Arrow().at(m.E).right(1.5))
    d.add(dsp.Dot(open=True).label("Vout", loc="right"))
    o = d.add(dsp.Oscillator().at((m.S[0], m.S[1] - 1.6)).anchor("center"))
    d.add(dsp.Line().at(m.S).to(o.N))
    d.add(elm.Label().at((o.E[0] + 1.2, o.E[1])).label("carrier fc"))
    d.save(str(pathlib.Path(__file__).with_name("circuit.svg")))
print("wrote circuit.svg")
