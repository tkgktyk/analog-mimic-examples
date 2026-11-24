# SPDX-License-Identifier: MIT
"""Sketches of frequency responses for the lectures (matplotlib).

The horizontal axis is the frequency normalized by the cutoff (f / fc), so a sketch
holds for every fc. The SVG files are reproducible (no date, fixed ids, text as paths),
so CI can check that they are up to date.
"""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

plt.rcParams.update({
    "svg.hashsalt": "analog-mimic",
    "svg.fonttype": "path",
    "font.size": 11,
    "axes.grid": True,
    "grid.alpha": 0.4,
})


def frequencies(decades=2, points=400):
    """f / fc from 10^-decades to 10^decades."""
    return np.logspace(-decades, decades, points)


def gain_sketch(x, h, asymptotes=(), ylim=(-45, 5), title=None):
    """Gain in dB of h (complex response at x = f / fc), with dashed asymptotes and the
    position of fc. asymptotes: list of (x, y_dB) arrays."""
    fig, ax = plt.subplots(figsize=(6, 3.2))
    for xa, ya in asymptotes:
        ax.plot(xa, ya, "--", color="gray", lw=1)
    ax.plot(x, 20 * np.log10(np.abs(h)), lw=2, color="C0")
    ax.axvline(1, color="C3", lw=1)
    ax.plot([1], [-3.01], "o", color="C3")
    ax.annotate("fc (-3 dB)", (1, -3.01), xytext=(8, 8), textcoords="offset points", color="C3")
    ax.set_xscale("log")
    ax.set_xlim(x[0], x[-1])
    ax.set_ylim(*ylim)
    ax.set_xlabel("Frequency  f / fc")
    ax.set_ylabel("Gain [dB]")
    if title:
        ax.set_title(title)
    fig.tight_layout()
    return fig


def save(fig, path):
    fig.savefig(path, format="svg", metadata={"Date": None, "Creator": None})
    plt.close(fig)
    print("wrote", path)
