# SPDX-License-Identifier: MIT
"""Control of the MimicLab instrument (Arduino UNO R4 + Analog Mimic) for the lectures.

    from mimiclab import MimicLab
    lab = MimicLab()                      # finds the Arduino, or MimicLab("COM5")
    lab.fg.sine(100, 1.0)                 # 100 Hz, 1 V peak around 2.5 V
    lab.mimic.filter1st_lpf(100)          # first-order LPF, fc = 100 Hz
    t, ch1, ch2 = lab.scope.capture(2000) # 2000 points at 20 kHz, in V
"""

from .lab import MimicLab, MimicLabError, find_port

__all__ = ["MimicLab", "MimicLabError", "find_port"]
__version__ = "0.1.0"
