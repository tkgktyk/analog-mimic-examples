# SPDX-License-Identifier: MIT
"""Logarithmic amplifier (diode in the feedback of an inverting amplifier) and
antilogarithmic amplifier (diode at the input, resistor in the feedback)."""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "tools"))
from drawing import setup_drawing  # noqa: E402
import schemdraw.elements as elm  # noqa: E402

here = pathlib.Path(__file__).parent


def amplifier(d, input_part, feedback_part, input_label, feedback_label):
    op = d.add(elm.Opamp(leads=True))
    d.add(elm.Line().at(op.in2).down(0.75))
    d.add(elm.Ground())
    d.add(elm.Line().at(op.in1).left(0.5))
    n = d.here
    d.add(elm.Dot())
    d.add(elm.Line().left(0.75))   # keep the input part clear of the feedback
    d.add(input_part.left().label(input_label))
    d.add(elm.Dot(open=True).label("Vin", loc="left"))
    d.add(elm.Line().at(op.out).right(0.75))
    out = d.here
    d.add(elm.Dot(open=True).label("Vout", loc="right"))
    d.add(elm.Line().at(n).up(1.75))
    d.add(feedback_part.tox(out[0] - 0.375).label(feedback_label))
    d.add(elm.Line().toy(op.out))
    d.add(elm.Dot().at((out[0] - 0.375, op.out[1])))


# Log: the current Vin / R flows through the diode, whose voltage is logarithmic
with setup_drawing(show=False) as d:
    amplifier(d, elm.Resistor(), elm.Diode().right(), "R", "D")
    d.save(str(here / "circuit_log.svg"))

# Antilog: the diode current is exponential in Vin and flows through Rf
with setup_drawing(show=False) as d:
    amplifier(d, elm.Diode().reverse(), elm.Resistor().right(), "D", "Rf")
    d.save(str(here / "circuit_antilog.svg"))
print("wrote circuit_log.svg, circuit_antilog.svg")
