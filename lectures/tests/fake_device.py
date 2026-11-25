# SPDX-License-Identifier: MIT
"""A fake MimicLab instrument for the tests: answers the commands of the sketch
(proto 1) like the hardware, without an Arduino.

The generator state is kept; a capture returns the generator wave on CH1 and, on CH2,
the same wave through the mode that is set (PGA, filters, integrator, differentiator,
comparators with the digital output 0 V / VDD, clippers, rectifiers, envelope follower;
filters and states settled from a few periods before t = 0), limited to 0.1 - 4.9 V.
Good enough to run the notebooks, not a model of the module.
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
        # ("bypass",), ("pga", gain), ("lpf" | "hpf" | "apf", fc), ("biquad", kind, fc, q)
        self.mode = ("bypass",)
        self.vref = VREF / 2
        # The smaller buffer of the UNO R4 WiFi, so that every notebook fits both boards
        self.max_points = 2000

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
            return (b"ok MimicLab proto=1 ver=0.1.1 fs=20000 dac=12 adc=14 maxpts=%d mimic=20261123 vref=5.000\n"
                    % self.max_points)
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
            filters = {"setfilter1stlpf": "lpf", "setfilter1sthpf": "hpf", "setfilter1stapf": "apf"}
            if m in filters:
                self.mode = (filters[m], float(t[2]))
            elif m.startswith("setfilterbiquad") and m[15:] in ("lpf", "hpf", "bpf", "notch"):
                kind = m[15:]
                q = float(t[3]) if len(t) > 3 else (0.7071 if kind in ("lpf", "hpf") else 1.0)
                self.mode = ("biquad", kind, float(t[2]), q)
            elif m == "setintegrator":
                self.mode = ("integ", float(t[2]), float(t[3]) if len(t) > 3 else 0.0)
            elif m == "setdifferentiator":
                self.mode = ("diff", float(t[2]), float(t[3]) if len(t) > 3 else 10.0)
            elif m in ("setcomparatorschmitt", "setcomparatorwindow", "setclipper", "setsoftclipper"):
                self.mode = (m[3:], float(t[2]), float(t[3]))
            elif m in ("setrectifierhalf", "setrectifierfull"):
                self.mode = (m[3:], len(t) > 2 and t[2].lower().startswith("neg"))
            elif m == "setenvelopefollower":
                self.mode = ("envelope", float(t[2]), len(t) > 3 and t[3].lower().startswith("neg"))
            elif m == "setpeakhold":
                self.mode = ("envelope", 0.0, len(t) > 2 and t[2].lower().startswith("neg"))
            elif m == "setpga":
                self.mode = ("pga", float(t[2]))
            elif m == "setvref":
                self.vref = float(t[2])
            elif m.startswith("set"):
                self.mode = ("bypass",)
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
        if not 1 <= points <= self.max_points:
            return b"err points out of range (1 - %d)\n" % self.max_points
        fs = FS / divider
        kind = self.mode[0]
        # Start a whole number of periods early, so that a filter is settled at t = 0
        warm = 0
        if kind in ("lpf", "hpf", "apf", "biquad", "integ", "diff", "envelope", "comparatorschmitt") and self.freq > 0:
            if kind == "biquad":
                tau = max(1.0, 2 * self.mode[3]) / (2 * np.pi * self.mode[2])
            elif kind == "integ":
                tau = self.mode[2] * 1e-6 if self.mode[2] > 0 else 0.0
            elif kind == "diff":
                tau = self.mode[2] * 1e-6
            elif kind == "envelope":
                tau = self.mode[1] * 1e-6
            elif kind == "comparatorschmitt":
                tau = 0.0
            else:
                tau = 1 / (2 * np.pi * self.mode[1])
            periods = int(np.ceil(10 * tau * self.freq)) + 1
            warm = int(round(periods / self.freq * fs))
        t = (np.arange(warm + points) - warm) / fs
        x = np.clip(self.wave_at(t), 0, VREF)  # the DAC
        u = x - self.vref  # the module works on the input relative to Vref
        if kind == "pga":
            y = self.mode[1] * u
        elif kind in ("lpf", "hpf", "apf"):
            a = 1 - np.exp(-2 * np.pi * self.mode[1] / fs)  # first-order low-pass
            lp = np.empty_like(u)
            acc = u[0]
            for n, v in enumerate(u):
                acc += a * (v - acc)
                lp[n] = acc
            y = {"lpf": lp, "hpf": u - lp, "apf": 2 * lp - u}[kind]
        elif kind == "biquad":
            y = biquad(u, *self.mode[1:], fs)
        elif kind == "integ":
            y = integrate(u, self.mode[1] * 1e-6, self.mode[2] * 1e-6, fs)
        elif kind == "diff":
            y = differentiate(u, self.mode[1] * 1e-6, self.mode[2] * 1e-6, fs)
        elif kind in ("clipper", "softclipper"):
            y = clip(x, *self.mode[1:], soft=kind == "softclipper") - self.vref
        elif kind == "rectifierhalf":
            y = np.minimum(u, 0) if self.mode[1] else np.maximum(u, 0)
        elif kind == "rectifierfull":
            y = -np.abs(u) if self.mode[1] else np.abs(u)
        elif kind == "envelope":
            y = -envelope(-u, self.mode[1] * 1e-6, fs) if self.mode[2] else envelope(u, self.mode[1] * 1e-6, fs)
        else:
            y = u
        if kind.startswith("comparator"):  # digital output: 0 V / VDD
            y = comparator(x, kind[10:], *self.mode[1:])
        else:
            y = np.clip(self.vref + y, 0.1, VREF - 0.1)  # headroom of the module output
        x, y = x[warm:], y[warm:]
        codes = [np.clip(np.round(v / VREF * ADC_FULL), 0, ADC_FULL - 1) for v in (x, y)]
        data = np.column_stack(codes).astype("<u2").tobytes()
        return f"ok bin {len(data)} 2 {points} {fs:.3f}\n".encode() + data + b"end\n"


def biquad(u, kind, fc, q, fs):
    """Second-order filter of the module (bilinear transform of the analog prototype
    (b2 s^2 + b1 s + b0) / (s^2 + s/Q + 1), s normalized by 2 pi fc, prewarped at fc)."""
    b2, b1, b0 = {"lpf": (0, 0, 1), "hpf": (1, 0, 0), "bpf": (0, 1 / q, 0), "notch": (1, 0, 1)}[kind]
    k = np.tan(np.pi * fc / fs)
    zm, zpm, zp = np.array([1, -2, 1]), np.array([1, 0, -1]), np.array([1, 2, 1])
    b = b2 * zm + b1 * k * zpm + b0 * k * k * zp
    a = zm + (k / q) * zpm + k * k * zp
    b, a = b / a[0], a / a[0]
    y = np.zeros_like(u)
    x1 = x2 = y1 = y2 = 0.0
    for n, x0 in enumerate(u):
        y0 = b[0] * x0 + b[1] * x1 + b[2] * x2 - a[1] * y1 - a[2] * y2
        x2, x1, y2, y1 = x1, x0, y1, y0
        y[n] = y0
    return y


def comparator(x, kind, upper, lower):
    """Comparator of the module (absolute volts in and out): window HIGH outside
    lower - upper; Schmitt HIGH above upper, LOW below lower, otherwise unchanged."""
    if kind == "window":
        return np.where((x > upper) | (x < lower), VREF, 0.0)
    y = np.empty_like(x)
    state = 0.0
    for n, v in enumerate(x):
        if v > upper:
            state = VREF
        elif v < lower:
            state = 0.0
        y[n] = state
    return y


def clip(x, upper, lower, soft=False):
    """Clipper of the module: hard, or the cubic soft clip (gain 1 at the centre)."""
    if not soft:
        return np.clip(x, lower, upper)
    c, h = (upper + lower) / 2, (upper - lower) / 2
    d = x - c
    y = c + d - 4 * d ** 3 / (27 * h * h)
    return np.where(d >= 1.5 * h, upper, np.where(d <= -1.5 * h, lower, y))


def envelope(mag, tau, fs):
    """Envelope follower of the module: follows the peak of mag (>= 0), decays with tau
    (0: holds the peak)."""
    d = np.exp(-1 / (fs * tau)) if tau > 0 else 1.0
    y = np.empty_like(mag)
    e = 0.0
    for n, v in enumerate(np.maximum(mag, 0)):
        e = v if v > e else e * d
        y[n] = e
    return y


def integrate(u, tau_i, tau_leak, fs):
    """Integrator of the module: m += c (K u - m) with a leak, m += u Ts / tau_i without."""
    ts = 1 / fs
    y = np.empty_like(u)
    m = 0.0
    if tau_leak > 0:
        c = 1 - np.exp(-ts / tau_leak)
        k = tau_leak / tau_i
        for n, v in enumerate(u):
            m += c * (k * v - m)
            m = min(max(m, -2.5), 2.5)
            y[n] = m
    else:
        for n, v in enumerate(u):
            m += v * ts / tau_i
            m = min(max(m, -2.5), 2.5)
            y[n] = m
    return y


def differentiate(u, tau_d, tau_lim, fs):
    """Differentiator of the module: m += c (K (u[n] - u[n-1]) - m), K = tau_d fs."""
    k = tau_d * fs
    c = 1 - np.exp(-1 / (fs * tau_lim)) if tau_lim > 0 else 1.0
    y = np.empty_like(u)
    m = 0.0
    last = u[0]
    for n, v in enumerate(u):
        m += c * (k * (v - last) - m)
        last = v
        y[n] = m
    return y
