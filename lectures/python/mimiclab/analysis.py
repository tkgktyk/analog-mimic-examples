# SPDX-License-Identifier: MIT
"""Small helpers to read measurements."""
import numpy as np


def fit_sine(t, v, freq):
    """Fits a sine of a known frequency, v = A sin(2 pi f t + phase) + offset.

    Returns:
        (amplitude [V], phase [deg], offset [V])
    """
    w = 2 * np.pi * freq
    a_mat = np.column_stack([np.sin(w * t), np.cos(w * t), np.ones_like(t)])
    a, b, c = np.linalg.lstsq(a_mat, v, rcond=None)[0]
    return float(np.hypot(a, b)), float(np.degrees(np.arctan2(b, a))), float(c)


def match_phase(phase, reference):
    """Shifts measured phases [deg] by a whole number of turns (360 deg) so that they
    lie on the reference (e.g. the theory at the same frequencies). A phase is only
    known modulo 360 deg; this picks the turn that matches."""
    phase = np.asarray(phase, dtype=float)
    turns = np.round(np.mean(np.asarray(reference) - phase) / 360)
    return phase + 360 * turns
