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


def gain_sketch(x, h, asymptotes=(), ylim=(-45, 5), title=None, label_offset=(8, 8)):
    """Gain in dB of h (complex response at x = f / fc), with dashed asymptotes and the
    position of fc. asymptotes: list of (x, y_dB) arrays; label_offset: position of the
    fc label from the point, in points."""
    fig, ax = plt.subplots(figsize=(6, 3.2))
    for xa, ya in asymptotes:
        ax.plot(xa, ya, "--", color="gray", lw=1)
    ax.plot(x, 20 * np.log10(np.abs(h)), lw=2, color="C0")
    ax.axvline(1, color="C3", lw=1)
    ax.plot([1], [-3.01], "o", color="C3")
    ax.annotate("fc (-3 dB)", (1, -3.01), xytext=label_offset, textcoords="offset points", color="C3")
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


def gain_phase_sketch(x, h, title=None, gain_ylim=(-10, 5), phase_ticks=(-180, -90, 0)):
    """Gain [dB] and phase [deg] of h (complex response at x = f / fc), with the
    position of fc and the phase there."""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(6, 4.6), sharex=True)
    ax1.plot(x, 20 * np.log10(np.abs(h)), lw=2, color="C0")
    ax1.set_ylim(*gain_ylim)
    ax1.set_ylabel("Gain [dB]")
    phase = np.degrees(np.unwrap(np.angle(h)))
    ax2.plot(x, phase, lw=2, color="C1")
    ph_fc = float(np.interp(0.0, np.log10(x), phase))
    ax2.plot([1], [ph_fc], "o", color="C3")
    ax2.annotate(f"fc ({ph_fc:.0f} deg)", (1, ph_fc), xytext=(8, 8), textcoords="offset points",
                 color="C3")
    ax2.set_yticks(phase_ticks)
    ax2.set_ylabel("Phase [deg]")
    for ax in (ax1, ax2):
        ax.axvline(1, color="C3", lw=1)
        ax.set_xscale("log")
        ax.set_xlim(x[0], x[-1])
    ax2.set_xlabel("Frequency  f / fc")
    if title:
        ax1.set_title(title)
    fig.tight_layout()
    return fig


def biquad(x, kind, q):
    """Second-order response at x = f / fc (the same forms as the module):
    lpf 1/D, hpf s^2/D, bpf (s/Q)/D, notch (s^2 + 1)/D, with D = s^2 + s/Q + 1."""
    s = 1j * x
    d = s * s + s / q + 1
    num = {"lpf": 1, "hpf": s * s, "bpf": s / q, "notch": s * s + 1}[kind]
    return num / d


def gain_family_sketch(x, curves, asymptotes=(), ylim=(-60, 15), title=None, mark=None,
                       xlabel="Frequency  f / fc", legend_loc="lower left"):
    """Gains [dB] of several responses (curves: list of (label, h)) with dashed
    asymptotes and a vertical line at fc. mark: (y_dB, text) to put a point at fc."""
    fig, ax = plt.subplots(figsize=(6, 3.4))
    for xa, ya in asymptotes:
        ax.plot(xa, ya, "--", color="gray", lw=1)
    for i, (label, h) in enumerate(curves):
        ax.plot(x, 20 * np.log10(np.maximum(np.abs(h), 1e-6)), lw=2, color=f"C{i}", label=label)
    ax.axvline(1, color="C3", lw=1)
    if mark:
        ax.plot([1], [mark[0]], "o", color="C3")
        ax.annotate(mark[1], (1, mark[0]), xytext=(8, 8), textcoords="offset points", color="C3")
    ax.set_xscale("log")
    ax.set_xlim(x[0], x[-1])
    ax.set_ylim(*ylim)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("Gain [dB]")
    ax.legend(loc=legend_loc, fontsize=9)
    if title:
        ax.set_title(title)
    fig.tight_layout()
    return fig


def transfer_axes(titles, lim=(0.0, 5.0)):
    """Axes for input-output characteristics (input voltage across, output up), one per
    title, square, from lim[0] to lim[1] V."""
    fig, axes = plt.subplots(1, len(titles), figsize=(3.3 * len(titles) + 0.4, 3.6))
    axes = np.atleast_1d(axes)
    for ax, title in zip(axes, titles):
        ax.set_xlim(*lim)
        ax.set_ylim(lim[0] - 0.25, lim[1] + 0.25)
        ax.set_aspect("equal")
        ax.set_xlabel("Input [V]")
        ax.set_title(title)
    axes[0].set_ylabel("Output [V]")
    return fig, axes


def arrow(ax, start, end, color="C0"):
    """An arrow head along a line, to show the direction of travel."""
    ax.annotate("", end, start, arrowprops=dict(arrowstyle="-|>", color=color, lw=2))
