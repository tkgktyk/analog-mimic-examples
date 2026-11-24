# SPDX-License-Identifier: MIT
"""Wiring of the lectures (the same for every lecture): Arduino UNO R4 with the
MimicLab sketch and one Analog Mimic (Mimic0x: Mimic00, Mimic01, ...).

A0 (function generator) drives the module input AIN and is read back on A1 (CH1);
the module output AOUT is read on A2 (CH2).

Uses mimic_parts.py of the Arduino library (analog-mimic-arduino/extras/schematics),
from the working copy next to this repository:
    uv run --project lectures python lectures/schematic.py
"""
import sys
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
PARTS = HERE.parents[1] / "analog-mimic-arduino" / "extras" / "schematics"
sys.path.insert(0, str(PARTS))
from mimic_parts import setup_drawing, mimic0x, PIN_SPACING  # noqa: E402
import schemdraw.elements as elm  # noqa: E402


def uno_r4_lab(label="Arduino UNO R4 (MimicLab)"):
    """UNO R4 with the pins of the lectures. From the bottom: A0, A1, A2, SCL, SDA,
    GND, 5V; A2 and above are level with AOUT, SCL, SDA, GND, VCC of mimic0x()."""
    names = [("A0", "A0 (FG)"), ("A1", "A1 (CH1)"), ("A2", "A2 (CH2)"),
             ("SCL", "SCL"), ("SDA", "SDA"), ("GND", "GND"), ("5V", "5V")]
    pins = [elm.IcPin(name=text, side="right", anchorname=a) for a, text in names]
    return elm.Ic(pins=pins, pinspacing=PIN_SPACING, edgepadW=1.0, edgepadH=0.5,
                  leadlen=0.5).label(label, loc="top", fontsize=13)


with setup_drawing(show=False) as d:
    uno = d.add(uno_r4_lab())
    m = d.add(mimic0x().anchor("SCL").at((uno.SCL[0] + 6, uno.SCL[1])))
    for a, b in [("SCL", "SCL"), ("SDA", "SDA"), ("GND", "GND"), ("5V", "VCC"), ("A2", "AOUT")]:
        d.add(elm.Wire("-").at(getattr(uno, a)).to(getattr(m, b)))

    # Function generator: A0 to AIN under the module, and back to A1 (CH1)
    x1 = uno.A0[0] + 1.0
    y = uno.A0[1] - 1.5
    xr = m.AIN[0] + 1.5
    d.add(elm.Line().at(uno.A1).to((x1, uno.A1[1])))
    d.add(elm.Line().at(uno.A0).to((x1, uno.A0[1])))
    # The branch of A0 is made on a breadboard
    d.add(elm.Dot().at((x1, uno.A0[1])).label("breadboard", loc="right", fontsize=11, color="gray"))
    d.add(elm.Line().at((x1, uno.A1[1])).to((x1, y)))
    d.add(elm.Line().to((xr, y)))
    d.add(elm.Line().to((xr, m.AIN[1])))
    d.add(elm.Line().to(m.AIN))

    out = pathlib.Path(__file__).with_suffix(".svg")
    d.save(str(out))
print("wrote", out)
