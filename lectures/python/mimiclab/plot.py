# SPDX-License-Identifier: MIT
"""Plots of measurements."""
import base64
import io
import math

import matplotlib.pyplot as plt


def plot_waveforms(r, cols=4, title=None, collapsed=False):
    """Draws the waveforms captured by frequency_response(), one small plot per
    frequency, with the gain and phase found there (left out when r.gain is None).

    collapsed: show the picture folded (click to open) in a notebook, instead of
        returning the figure. Returns None then.
    """
    n = len(r.freq)
    rows = math.ceil(n / cols)
    fig, axes = plt.subplots(rows, cols, figsize=(3 * cols, 2.2 * rows), squeeze=False)
    n_none = [None] * n
    gains = n_none if r.gain is None else r.gain
    phases = n_none if r.phase is None else r.phase
    for ax, f, (t, ch1, ch2), g, p in zip(axes.flat, r.freq, r.waves, gains, phases):
        ax.plot(t * 1e3, ch1, lw=1, label="CH1: input")
        ax.plot(t * 1e3, ch2, lw=1, label="CH2: output")
        ax.set_title(f"{f:.4g} Hz", fontsize=10)
        if g is not None:
            ax.text(0.02, 0.04, f"gain {g:.3f}\nphase {p:.0f} deg", transform=ax.transAxes,
                    fontsize=8, va="bottom", bbox=dict(fc="white", alpha=0.7, lw=0))
        ax.tick_params(labelsize=8)
        ax.grid(True, alpha=0.4)
    for ax in list(axes.flat)[n:]:
        ax.axis("off")
    axes[0][0].legend(fontsize=7, loc="upper right")
    fig.supxlabel("Time [ms]")
    fig.supylabel("Voltage [V]")
    if title:
        fig.suptitle(title)
    fig.tight_layout()
    if collapsed:
        show_folded(fig, "各周波数の波形(クリックで開く)" + (f": {title}" if title else ""))
        return None
    return fig


def show_folded(fig, summary):
    """Shows a figure folded in a notebook (an HTML <details> with the picture), and
    closes it. Unlike folding a cell's output, this stays folded after running."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=90)
    plt.close(fig)
    img = base64.b64encode(buf.getvalue()).decode("ascii")
    html = (f"<details><summary>{summary}</summary>"
            f'<img src="data:image/png;base64,{img}"></details>')
    try:
        from IPython.display import HTML, display
        display(HTML(html))
    except ImportError:
        print(summary)


class Monitor:
    """A plot updated in place while measuring (in a notebook)."""

    def __init__(self, label=""):
        self.label = label
        self.fig, self.ax = plt.subplots(figsize=(8, 3))
        try:
            from IPython.display import display
            self.handle = display(self.fig, display_id=True)
        except ImportError:
            self.handle = None

    def update(self, f, t, ch1, ch2, gain=None, phase=None):
        ax = self.ax
        ax.clear()
        ax.plot(t * 1e3, ch1, label="CH1: input")
        ax.plot(t * 1e3, ch2, label="CH2: output")
        values = "" if gain is None else f": gain {gain:.3f}, phase {phase:.0f} deg"
        ax.set_title(f"{self.label}{f:.4g} Hz{values}")
        ax.set_xlabel("Time [ms]")
        ax.set_ylabel("Voltage [V]")
        ax.grid(True)
        ax.legend(loc="upper right")
        self.fig.tight_layout()
        if self.handle is not None:
            self.handle.update(self.fig)

    def close(self):
        plt.close(self.fig)  # the display keeps the last picture
