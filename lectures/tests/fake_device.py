# SPDX-License-Identifier: MIT
"""A fake MimicLab instrument for the tests: answers the commands of the sketch
(proto 1) like the hardware, without an Arduino.

The generator state is kept; a capture returns the generator wave on CH1 and, on CH2,
the same wave through a first-order LPF / HPF (a simple digital filter, settled) when
one is set, otherwise the input. Good enough to run the notebooks, not a model of the
module.
"""
import numpy as np

FS = 20000.0
VREF = 5.0
ADC_FULL = 1 << 14


class FakeSerial:
    """Stands in for serial.Serial(port, baud, timeout=...)."""

    def __init__(self, *args, timeout=None, **kwargs):
        self.timeout = timeout
        self.buf = b"# MimicLab ready\n"
        self.sent = []  # command lines received, for the tests
        self.wave, self.freq, self.amp, self.offset = "dc", 0.0, 0.0, VREF / 2
        self.filter = None  # ("lpf" | "hpf", fc)

    # ---- serial.Serial interface ----

    def reset_input_buffer(self):
        self.buf = b""

    def readline(self):
        i = self.buf.find(b"\n")
        if i < 0:
            out, self.buf = self.buf, b""
        else:
            out, self.buf = self.buf[: i + 1], self.buf[i + 1:]
        return out

    def read(self, n):
        out, self.buf = self.buf[:n], self.buf[n:]
        return out

    def close(self):
        pass

    def write(self, data):
        for line in data.decode("ascii").splitlines():
            if line.strip():
                self.sent.append(line.strip())
                self.buf += self.answer(line.split())

    # ---- the sketch ----

    def fg_line(self):
        return (f"ok {self.wave} freq={self.freq:.6f} amp={self.amp:.4f} "
                f"offset={self.offset:.4f}\n").encode()

    def answer(self, t):
        cmd = t[0].lower()
        if cmd == "id":
            return b"ok MimicLab proto=1 ver=0.1.0 fs=20000 dac=12 adc=14 mimic=20261123 vref=5.000\n"
        if cmd == "fg":
            if len(t) == 1:
                return self.fg_line()
            w = t[1].lower()
            if w == "dc":
                self.wave, self.freq, self.amp, self.offset = "dc", 0.0, 0.0, float(t[2])
            elif w in ("sine", "square", "triangle"):
                self.wave, self.freq, self.amp = w, float(t[2]), float(t[3])
                self.offset = float(t[4]) if len(t) > 4 else VREF / 2
            else:
                return b"err unknown wave\n"
            return self.fg_line()
        if cmd == "scope":
            return self.capture(int(t[2]), int(t[3]) if len(t) > 3 else 1)
        if cmd == "mimic":
            m = t[1].lower()
            if m == "list":
                return b"# setFilter1stLPF (1 args)\n# getStatus getInputVolts\nok\n"
            if m == "setfilter1stlpf":
                self.filter = ("lpf", float(t[2]))
            elif m == "setfilter1sthpf":
                self.filter = ("hpf", float(t[2]))
            elif m.startswith("set"):
                self.filter = None
            elif m == "getinputvolts":
                return f"ok {self.offset:.5f}\n".encode()
            elif m == "getbuilddate":
                return b"ok 20261123\n"
            elif m == "getstatus":
                return b"ok 0\n"
            elif m != "begin":
                return b"err unknown method (mimic list)\n"
            return b"ok\n"
        return b"err unknown command (help)\n"

    def wave_at(self, t):
        """The generator output (V) at times t (s); phase 0 at t = 0."""
        ph = (self.freq * t) % 1.0
        if self.wave == "sine":
            s = np.sin(2 * np.pi * ph)
        elif self.wave == "square":
            s = np.where(ph < 0.5, 1.0, -1.0)
        elif self.wave == "triangle":
            q = (ph + 0.25) % 1.0
            s = np.where(q < 0.5, 4 * q - 1, 3 - 4 * q)
        else:
            s = np.zeros_like(t)
        return self.offset + self.amp * s

    def capture(self, points, divider):
        fs = FS / divider
        # Start a whole number of periods early, so that the filter is settled at t = 0
        warm = 0
        if self.filter and self.freq > 0:
            periods = int(np.ceil(10 / (2 * np.pi * self.filter[1]) * self.freq)) + 1
            warm = int(round(periods / self.freq * fs))
        t = (np.arange(warm + points) - warm) / fs
        x = self.wave_at(t)
        y = x.copy()
        if self.filter:
            kind, fc = self.filter
            a = 1 - np.exp(-2 * np.pi * fc / fs)  # first-order low-pass, around the offset
            lp = np.empty_like(x)
            acc = x[0]
            for n, v in enumerate(x):
                acc += a * (v - acc)
                lp[n] = acc
            y = lp if kind == "lpf" else x - lp + self.offset
        x, y = x[warm:], y[warm:]
        codes = [np.clip(np.round(v / VREF * ADC_FULL), 0, ADC_FULL - 1) for v in (x, y)]
        data = np.column_stack(codes).astype("<u2").tobytes()
        return f"ok bin {len(data)} 2 {points} {fs:.3f}\n".encode() + data + b"end\n"
