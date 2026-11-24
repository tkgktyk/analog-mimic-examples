# SPDX-License-Identifier: MIT
"""A fake MimicLab instrument for the tests: answers the commands of the sketch
(proto 1) like the hardware, without an Arduino.

The generator state is kept; a capture returns the generator wave on CH1 and, on CH2,
the same wave through the first-order LPF / HPF when one is set (steady state of a
sine), otherwise the input. Good enough to run the notebooks, not a model of the module.
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

    def capture(self, points, divider):
        fs = FS / divider
        t = np.arange(points) / fs
        w = 2 * np.pi * self.freq
        if self.wave == "dc":
            x = np.zeros(points)
        else:
            x = np.sin(w * t)
        gain, phase = 1.0, 0.0
        if self.filter and self.freq > 0:
            kind, fc = self.filter
            r = self.freq / fc
            h = 1 / (1 + 1j * r) if kind == "lpf" else 1j * r / (1 + 1j * r)
            gain, phase = abs(h), np.angle(h)
        y = gain * np.sin(w * t + phase) if self.wave != "dc" else x
        codes = [np.clip(np.round((self.offset + self.amp * s) / VREF * ADC_FULL), 0, ADC_FULL - 1)
                 for s in (x, y)]
        data = np.column_stack(codes).astype("<u2").tobytes()
        return f"ok bin {len(data)} 2 {points} {fs:.3f}\n".encode() + data + b"end\n"
