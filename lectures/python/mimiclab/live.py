# SPDX-License-Identifier: MIT
"""Live scope: one plot captured and drawn again and again, with buttons (JupyterLab).

The captures run in a background thread, so the buttons work and other cells can still
use the instrument (each command is sent under the lock of MimicLab).
"""

from __future__ import annotations

import io
import os
import threading
import time

import numpy as np
from matplotlib.figure import Figure

# Set (to a number of frames) by the tests: capture that many frames, without a thread
FRAMES_ENV = "MIMICLAB_LIVE_FRAMES"

MODES = {"free": "Free run", "single": "Single"}
SCALES = {"fixed": "0 - 5 V", "auto": "Auto"}


def measure(t, v, min_pp: float = 0.02):
    """Mean (V) and frequency (Hz) of one channel.

    The frequency is found from the rising crossings of the mean, counted like a Schmitt
    trigger (the signal must go below mean - h and then above mean + h, h = 25 % of the
    peak to peak, so that noise does not count). None when the peak to peak is below
    `min_pp` (DC) or when fewer than two crossings are captured (a slow signal).
    """
    v = np.asarray(v, dtype=float)
    mean = float(v.mean())
    pp = float(v.max() - v.min())
    if pp < min_pp:
        return mean, None
    h = 0.25 * pp
    crossings = []
    low = False
    cross = None  # time of the last rising crossing of the mean while low
    for i in range(1, len(v)):
        if v[i] < mean - h:
            low, cross = True, None
        elif low:
            if v[i - 1] < mean <= v[i]:
                frac = (mean - v[i - 1]) / (v[i] - v[i - 1])
                cross = t[i - 1] + frac * (t[i] - t[i - 1])
            if v[i] > mean + h and cross is not None:
                crossings.append(cross)
                low = False
    if len(crossings) < 2:
        return mean, None
    return mean, (len(crossings) - 1) / (crossings[-1] - crossings[0])


def _label(name, t, v):
    mean, freq = measure(t, v)
    f = "-" if freq is None else f"{freq:.4g} Hz"
    return f"{name}\nmean {mean:.3f} V\n{f}"


class LiveScope:
    """Use lab.scope.live(); see Scope.live for the arguments."""

    def __init__(self, lab, points=2000, fs=None, mode="free", scale="fixed", frames=None):
        if mode not in MODES:
            raise ValueError(f"mode must be one of {list(MODES)}")
        if scale not in SCALES:
            raise ValueError(f"scale must be one of {list(SCALES)}")
        self._lab = lab
        self.points, self.fs = int(points), fs
        self.mode, self.scale = mode, scale
        self.data = None
        self.rate = None
        self._last = None
        self._stop = threading.Event()
        self._again = threading.Event()
        self._draw_lock = threading.Lock()
        self._thread = None
        self.fig = Figure(figsize=(9, 3.5), layout="constrained")
        self.ax = self.fig.add_subplot()

        # One live scope at a time on an instrument
        for old in list(lab._lives):
            old.stop()
        lab._lives.append(self)

        if frames is None and os.environ.get(FRAMES_ENV):
            frames = int(os.environ[FRAMES_ENV])
        if frames is not None:
            self._run_frames(frames)
        else:
            self._start()

    # ---- capture and drawing ----

    def _capture(self):
        self.data = self._lab.scope.capture(self.points, fs=self.fs, sync=False)
        now = time.perf_counter()  # fine steps (time.monotonic() is about 16 ms on Windows)
        if self._last is not None and now > self._last:
            r = 1 / (now - self._last)
            self.rate = r if self.rate is None else 0.7 * self.rate + 0.3 * r
        self._last = now

    def _png(self) -> bytes:
        with self._draw_lock:
            ax = self.ax
            ax.clear()
            t, ch1, ch2 = self.data
            ax.plot(t * 1e3, ch1, label=_label("CH1 (A1)", t, ch1))
            ax.plot(t * 1e3, ch2, label=_label("CH2 (A2)", t, ch2))
            if self.scale == "fixed":
                ax.set_ylim(-0.2, self._lab.vref + 0.2)
            else:
                lo = min(ch1.min(), ch2.min())
                hi = max(ch1.max(), ch2.max())
                mid, half = (lo + hi) / 2, max(hi - lo, 0.01) / 2 * 1.1
                ax.set_ylim(mid - half, mid + half)
            ax.set_xlim(0, t[-1] * 1e3)
            ax.set_xlabel("Time [ms]")
            ax.set_ylabel("Voltage [V]")
            ax.grid(True)
            ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1.0), fontsize=9)
            fs = len(t) / (t[-1] + t[1]) if len(t) > 1 else 0
            title = f"{MODES[self.mode]}, {SCALES[self.scale]}: {len(t)} points at {fs / 1e3:g} kHz"
            if self.mode == "free" and self.rate:
                title += f", {self.rate:.1f} frames/s"
            ax.set_title(title, fontsize=10)
            buf = io.BytesIO()
            self.fig.savefig(buf, format="png", dpi=90)
        return buf.getvalue()

    # ---- without a thread (tests, or frames=N) ----

    def _run_frames(self, frames):
        for _ in range(max(1, frames)):
            self._capture()
        try:
            from IPython.display import Image, display
            display(Image(self._png()))
        except ImportError:
            pass
        self._lab._lives.remove(self)

    # ---- with buttons ----

    def _start(self):
        import ipywidgets as w
        from IPython.display import display

        self._capture()  # the first frame before showing anything
        self._image = w.Image(value=self._png(), format="png")
        self._mode_w = w.ToggleButtons(options=[(v, k) for k, v in MODES.items()], value=self.mode)
        self._scale_w = w.ToggleButtons(options=[(v, k) for k, v in SCALES.items()], value=self.scale)
        self._again_w = w.Button(description="Capture", icon="camera",
                                 disabled=self.mode == "free",
                                 tooltip="Capture once more (Single)")
        self._stop_w = w.Button(description="Stop", icon="stop", tooltip="End the live scope")
        self._status = w.Label("")
        for b in (self._mode_w, self._scale_w):
            b.style.button_width = "80px"
        self._mode_w.observe(self._on_mode, names="value")
        self._scale_w.observe(self._on_scale, names="value")
        self._again_w.on_click(lambda _: self._again.set())
        self._stop_w.on_click(lambda _: self.stop())
        bar = w.HBox([self._mode_w, self._again_w, self._scale_w, self._stop_w, self._status])
        display(w.VBox([bar, self._image]))
        self._thread = threading.Thread(target=self._loop, name="mimiclab-live", daemon=True)
        self._thread.start()

    def _on_mode(self, change):
        self.mode = change["new"]
        self._again_w.disabled = self.mode == "free"
        if self.mode == "single":
            self._again.set()  # Single takes one capture at once
        else:
            self._last = None
            self.rate = None

    def _on_scale(self, change):
        self.scale = change["new"]
        if self.data is not None:
            self._image.value = self._png()

    def _loop(self):
        try:
            while not self._stop.is_set():
                if self.mode == "free" or self._again.is_set():
                    self._again.clear()
                    self._capture()
                    if self._stop.is_set():
                        break
                    self._image.value = self._png()
                else:
                    self._again.wait(0.1)
            self._status.value = "Stopped"
        except Exception as e:  # e.g. the port was closed
            self._status.value = f"Stopped: {e}"
        finally:
            for b in (self._mode_w, self._scale_w, self._again_w, self._stop_w):
                b.disabled = True
            if self in self._lab._lives:
                self._lab._lives.remove(self)

    def stop(self):
        """Ends the live scope (the last picture stays)."""
        self._stop.set()
        self._again.set()
        if self._thread is not None and self._thread is not threading.current_thread():
            self._thread.join(timeout=5)
        if self in self._lab._lives:
            self._lab._lives.remove(self)

    def __repr__(self):
        state = "running" if self._thread is not None and self._thread.is_alive() else "stopped"
        return f"LiveScope({MODES[self.mode]}, {SCALES[self.scale]}, {state})"
