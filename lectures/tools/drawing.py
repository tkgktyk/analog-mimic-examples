# SPDX-License-Identifier: MIT
"""Common setup of the circuit diagrams of the lectures (schemdraw).

The style comes from mimic_parts.py of the Arduino library (the working copy next to
this repository, analog-mimic-arduino/extras/schematics), so the circuit diagrams look
like the wiring diagrams.
"""
import sys
import pathlib

PARTS = pathlib.Path(__file__).resolve().parents[2].parent / "analog-mimic-arduino" / "extras" / "schematics"
sys.path.insert(0, str(PARTS))

from mimic_parts import setup_drawing  # noqa: E402,F401
