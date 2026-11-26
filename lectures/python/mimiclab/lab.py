# SPDX-License-Identifier: MIT
"""Serial protocol of the MimicLab sketch (proto 1).

Every command gets one line, "ok ..." or "err <reason>"; lines starting with "#" are
for people and skipped. "scope capture" answers "ok bin <bytes> <channels> <points> <fs>",
then the binary data (uint16 little endian, channels interleaved), then a line "end".
"""

from __future__ import annotations

import math
import threading
import time
from typing import NamedTuple

import numpy as np
import serial
from serial.tools import list_ports

from .analysis import fit_sine
from .plot import Monitor

PROTOCOL = 1
ARDUINO_VID = 0x2341


class Response(NamedTuple):
    """Frequency response: frequencies [Hz], gain (output / input), phase [deg] and the
    captured waveforms, a list of (t, ch1, ch2) for each frequency."""
    freq: np.ndarray
    gain: np.ndarray
    phase: np.ndarray
    waves: list | None = None

    @property
    def gain_db(self):
        return 20 * np.log10(self.gain)


class MimicLabError(RuntimeError):
    """An error answered by the instrument, or a broken reply."""


def find_port() -> str:
    """Returns the serial port of the Arduino, if exactly one is connected."""
    ports = [p for p in list_ports.comports() if p.vid == ARDUINO_VID]
    if len(ports) == 1:
        return ports[0].device
    names = ", ".join(f"{p.device} ({p.description})" for p in list_ports.comports()) or "なし"
    if not ports:
        raise MimicLabError(f"Arduino が見つかりません。USB ケーブルを確かめてください。"
                            f"シリアルポート: {names}")
    raise MimicLabError(f"Arduino が複数つながっています。MimicLab('COM5') のようにポートを"
                        f"指定してください。シリアルポート: {names}")


def _arg(x) -> str:
    if isinstance(x, bool):
        return "on" if x else "off"
    if isinstance(x, (int, float, np.number)):
        return f"{float(x):.9g}"
    return str(x)


def _keys(text: str, first: str = "name") -> dict:
    """Parses "word key=value key=value" into {first: "word", "key": value, ...}."""
    out = {}
    for i, tok in enumerate(text.split()):
        if "=" in tok:
            k, v = tok.split("=", 1)
            try:
                out[k] = float(v) if any(c in v for c in ".e") else int(v)
            except ValueError:
                out[k] = v
        elif i == 0:
            out[first] = tok
    return out


class MimicLab:
    """The instrument: function generator (fg), 2-channel scope (scope) and the module (mimic).

    Args:
        port: Serial port (e.g. "COM5" or "/dev/ttyACM0"). None finds the Arduino.
        baud: Baud rate; must match the sketch (used by the UNO R4 WiFi, ignored by the Minima).
        timeout: Seconds to wait for a reply.
    """

    def __init__(self, port: str | None = None, baud: int = 1_000_000, timeout: float = 2.0):
        self.port = port or find_port()
        self.timeout = timeout
        # One command (or capture) at a time: the live scope sends from a thread
        self._lock = threading.RLock()
        self._lives = []
        try:
            self._ser = serial.Serial(self.port, baud, timeout=timeout)
        except serial.SerialException as e:
            raise MimicLabError(
                f"{self.port} を開けません。ほかのプログラムが使っている可能性があります。"
                "前のノートブックで lab.close() を実行するか、JupyterLab の左の"
                "「実行中のカーネルとターミナル」から前のノートブックのカーネルを止めてください。"
                "PlatformIO や Arduino IDE のシリアルモニタも閉じてください。") from e
        self.info = self._connect()
        self.vref = float(self.info["vref"])
        self.fs = float(self.info["fs"])
        self.adc_bits = int(self.info["adc"])
        # Points per channel of one capture (2000; sketch 0.1.0 had 4000)
        self.max_points = int(self.info.get("maxpts", 4000))
        self.fg = FunctionGenerator(self)
        self.scope = Scope(self)
        self.mimic = Mimic(self)

    def _connect(self) -> dict:
        # The board may restart when the port opens (UNO R4 WiFi): try "id" for a few seconds
        deadline = time.monotonic() + 5.0
        while True:
            self._ser.reset_input_buffer()
            try:
                reply = self.command("id")
                break
            except MimicLabError:
                if time.monotonic() > deadline:
                    self._ser.close()
                    raise MimicLabError(f"{self.port} の Arduino が答えません。MimicLab の"
                                        "スケッチを書き込んであるか確かめてください。")
                time.sleep(0.3)
        info = _keys(reply)
        if info.get("name") != "MimicLab":
            self._ser.close()
            raise MimicLabError(f"MimicLab ではありません: {reply}")
        if info.get("proto") != PROTOCOL:
            self._ser.close()
            raise MimicLabError(f"スケッチの命令の版(proto {info.get('proto')})と mimiclab の版"
                                f"(proto {PROTOCOL})が合いません。スケッチか mimiclab を新しくしてください。")
        return info

    # ---- Low level ----

    def _readline(self) -> str:
        """Reads the next line that is not a comment ("#")."""
        while True:
            raw = self._ser.readline()
            if not raw.endswith(b"\n"):
                raise MimicLabError("No reply (timeout)")
            line = raw.decode("ascii", "replace").strip()
            if line and not line.startswith("#"):
                return line

    def command(self, line: str) -> str:
        """Sends one command and returns the text after "ok" (raises MimicLabError on "err")."""
        with self._lock:
            self._ser.write((line + "\n").encode("ascii"))
            reply = self._readline()
        if reply == "ok":
            return ""
        if reply.startswith("ok "):
            return reply[3:]
        if reply.startswith("err"):
            raise MimicLabError(f"{line!r}: {reply[3:].strip()}")
        raise MimicLabError(f"{line!r}: unexpected reply {reply!r}")

    def frequency_response(self, freqs, amp: float = 1.0, offset: float | None = None,
                           periods: int = 5, settle: float = 0.3,
                           monitor=False, label: str = "") -> Response:
        """Measures the response of the module with sine waves (a Bode plot).

        For each frequency, the generator sends a sine, waits `settle` seconds, captures
        at least `periods` periods of CH1 (input) and CH2 (output) and fits a sine of
        that frequency to both. The generator is left at the last frequency.

        Args:
            freqs: Frequencies [Hz]; up to about 2 kHz is meaningful (20 kHz sampling).
            amp: Amplitude (peak) of the sine [V].
            offset: Centre of the sine [V]; None for 2.5 V.
            periods: Periods captured at each frequency (more for less noise).
            settle: Seconds to wait after changing the frequency.
            monitor: True shows the waveforms while measuring (in a notebook), like
                watching an oscilloscope; the last one stays. A Monitor() can be given
                instead, to use one plot for several measurements (close it after).
            label: Text put before the frequency in the title of the monitor.

        Returns:
            Response(freq, gain, phase, waves): phase of the output from the input, in
            degrees, continuous over the frequencies (it can go below -180); waves: the
            captured (t, ch1, ch2) at each frequency (plot_waveforms() draws them).
        """
        freqs = np.asarray(freqs, dtype=float)
        gains, phases, waves = [], [], []
        own = monitor is True
        mon = Monitor() if own else (monitor or None)
        if mon is not None:
            mon.label = label
        for f in freqs:
            if offset is None:
                self.fg.sine(f, amp)
            else:
                self.fg.sine(f, amp, offset)
            time.sleep(settle)
            span = periods / f
            limit = min(2000, self.max_points)
            divider = max(1, math.ceil(span * self.fs / limit))
            fs = self.fs / divider
            points = min(limit, max(100, math.ceil(span * fs)))
            t, ch1, ch2 = self.scope.capture(points, fs=fs)
            a1, p1, _ = fit_sine(t, ch1, f)
            a2, p2, _ = fit_sine(t, ch2, f)
            gains.append(a2 / a1)
            phases.append((p2 - p1 + 180) % 360 - 180)
            waves.append((t, ch1, ch2))
            if mon is not None:
                mon.update(f, t, ch1, ch2, gains[-1], phases[-1])
        if own:
            mon.close()
        phase = np.degrees(np.unwrap(np.radians(phases)))
        return Response(freqs, np.array(gains), phase, waves)

    def close(self):
        for live in list(self._lives):
            live.stop()
        self._ser.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def __repr__(self):
        return (f"MimicLab(port={self.port!r}, ver={self.info.get('ver')}, "
                f"mimic={self.info.get('mimic')})")


class FunctionGenerator:
    """Function generator on A0 (DAC). Voltages in V, frequencies in Hz.

    The offset defaults to 2.5 V, the default Vref (signal ground) of the module.
    Each method returns the setting, with the actual frequency of the generator.
    """

    def __init__(self, lab: MimicLab):
        self._lab = lab

    def _set(self, *args) -> dict:
        return _keys(self._lab.command("fg " + " ".join(_arg(a) for a in args)), "wave")

    def sine(self, freq: float, amp: float, offset: float | None = None) -> dict:
        return self._set("sine", freq, amp, *([] if offset is None else [offset]))

    def square(self, freq: float, amp: float, offset: float | None = None) -> dict:
        return self._set("square", freq, amp, *([] if offset is None else [offset]))

    def triangle(self, freq: float, amp: float, offset: float | None = None) -> dict:
        return self._set("triangle", freq, amp, *([] if offset is None else [offset]))

    def dc(self, volts: float) -> dict:
        return self._set("dc", volts)

    def status(self) -> dict:
        return _keys(self._lab.command("fg"), "wave")


class Scope:
    """2-channel scope: CH1 = A1 (module input), CH2 = A2 (module output)."""

    def __init__(self, lab: MimicLab):
        self._lab = lab

    def capture(self, points: int = 2000, fs: float | None = None, sync: bool | None = None):
        """Captures both channels.

        Args:
            points: Points per channel (1 - lab.max_points, 2000).
            fs: Sampling frequency in Hz: 20000 divided by an integer (20000, 10000, 5000, ...).
                None for 20000.
            sync: True starts at phase 0 of the generator (the same waveform every time),
                False starts at once. None: True unless the generator is at DC.

        Returns:
            (t, ch1, ch2): time in s and the two channels in V (numpy arrays).
        """
        base = self._lab.fs
        divider = 1 if fs is None else round(base / fs)
        if divider < 1 or abs(base / divider - (fs or base)) > 1e-6 * base:
            raise ValueError(f"fs must be {base:g} Hz divided by an integer")
        cmd = f"scope capture {int(points)} {divider}"
        if sync is not None:
            cmd += " sync" if sync else " free"

        ser = self._lab._ser
        with self._lab._lock:
            old = ser.timeout
            # Capture time, one generator period (waiting for phase 0) and the transfer
            ser.timeout = self._lab.timeout + points * divider / base + 1.5
            try:
                header = self._lab.command(cmd).split()
                if len(header) != 5 or header[0] != "bin":
                    raise MimicLabError(f"unexpected reply: {' '.join(header)}")
                nbytes, nch, npts, fs_actual = int(header[1]), int(header[2]), int(header[3]), float(header[4])
                data = ser.read(nbytes)
                if len(data) != nbytes:
                    raise MimicLabError(f"capture: {len(data)} of {nbytes} bytes received")
                if self._lab._readline() != "end":
                    raise MimicLabError("capture: no 'end' after the data")
            finally:
                ser.timeout = old

        codes = np.frombuffer(data, dtype="<u2").reshape(npts, nch)
        volts = codes * (self._lab.vref / (1 << self._lab.adc_bits))
        t = np.arange(npts) / fs_actual
        return t, volts[:, 0], volts[:, 1]

    def live(self, points: int = 2000, fs: float | None = None, mode: str = "free",
             scale: str = "fixed", frames: int | None = None):
        """Shows both channels again and again in one plot, like an oscilloscope (JupyterLab).

        Buttons: Free run (capture again and again) / Single (one capture; "Capture" takes
        another), 0 - 5 V / Auto (vertical scale), Stop. The legend shows the mean and the
        frequency of each channel. The captures start at once (no trigger). Other cells
        can still use the instrument while it runs; lab.close() stops it.

        Args:
            points, fs: As capture() (2000 points at 20 kHz: 0.1 s).
            mode: "free" or "single" at the start.
            scale: "fixed" (0 - 5 V) or "auto" at the start.
            frames: Capture this many frames, show the last one and return (no buttons).

        Returns:
            The LiveScope; .stop() ends it, .data is the last (t, ch1, ch2).
        """
        from .live import LiveScope
        return LiveScope(self._lab, points, fs, mode, scale, frames)


class Mimic:
    """The Analog Mimic module, through the AnalogMimic library of the Arduino.

    Any method of the library can be called by its name, e.g.
    lab.mimic.setFilter1stLPF(100) sends "mimic setFilter1stLPF 100" (lab.mimic.list()
    shows them). The short names below are the ones used in the lectures.
    Polarity: "pos" or "neg".
    """

    def __init__(self, lab: MimicLab):
        self._lab = lab

    def call(self, method: str, *args) -> str:
        """Calls a library method by name and returns its reply ("" for setters)."""
        return self._lab.command(" ".join(["mimic", method, *(_arg(a) for a in args)]))

    def __getattr__(self, name: str):
        if name.startswith(("set", "get")):
            return lambda *args: self.call(name, *args)
        raise AttributeError(name)

    def list(self) -> list[str]:
        """Names of the library methods the sketch knows."""
        ser = self._lab._ser
        ser.write(b"mimic list\n")
        names = []
        while True:
            raw = ser.readline()
            if not raw.endswith(b"\n"):
                raise MimicLabError("mimic list: no reply (timeout)")
            line = raw.decode("ascii", "replace").strip()
            if line.startswith("#"):
                body = line[1:].strip()
                names += [body.split()[0]] if "(" in body else body.split()
            elif line == "ok":
                return names
            elif line.startswith("err"):
                raise MimicLabError(f"mimic list: {line[3:].strip()}")

    def begin(self) -> None:
        """Connects to the module again (e.g. after plugging it in)."""
        self.call("begin")

    # ---- Reading ----

    def build_date(self) -> str:
        """Firmware build date of the module (YYYYMMDD)."""
        return self.call("getBuildDate")

    def input_volts(self) -> float:
        """Input voltage measured by the module, in V."""
        return float(self.call("getInputVolts"))

    def status(self) -> int:
        return int(self.call("getStatus"))

    # ---- Short names used in the lectures ----

    def bypass(self):
        """Output = input (voltage follower)."""
        self.call("setBypassDSP")

    def pga(self, gain: float):
        """Amplifier: output = Vref + gain x (input - Vref); a negative gain inverts."""
        self.call("setPGA", gain)

    def filter1st_lpf(self, fc: float):
        """First-order low-pass filter (RC), cutoff fc in Hz."""
        self.call("setFilter1stLPF", fc)

    def filter1st_hpf(self, fc: float):
        """First-order high-pass filter (CR), cutoff fc in Hz."""
        self.call("setFilter1stHPF", fc)

    def filter1st_apf(self, fc: float):
        """First-order all-pass filter: gain 1, phase 0 to -180 degrees (-90 at fc)."""
        self.call("setFilter1stAPF", fc)

    def biquad_lpf(self, fc: float, q: float | None = None):
        """Second-order low-pass filter (Butterworth unless q is given)."""
        self.call("setFilterBiquadLPF", fc, *([] if q is None else [q]))

    def biquad_hpf(self, fc: float, q: float | None = None):
        """Second-order high-pass filter (Butterworth unless q is given)."""
        self.call("setFilterBiquadHPF", fc, *([] if q is None else [q]))

    def biquad_bpf(self, fc: float, q: float = 1.0):
        """Second-order band-pass filter, centre fc in Hz."""
        self.call("setFilterBiquadBPF", fc, q)

    def biquad_notch(self, fc: float, q: float = 1.0):
        """Second-order notch (band-stop) filter, centre fc in Hz."""
        self.call("setFilterBiquadNotch", fc, q)

    def integrator(self, integration_time_us: float, leak_time_us: float = 0.0):
        """Integrator: output = Vref + (1 / tau_i) x integral of (input - Vref) dt.
        A leak (resistor across the capacitor) makes it a low-pass with a DC gain of
        leak / integration time. Times in microseconds. The output is kept when the
        settings change; switch to another mode (e.g. bypass()) to reset it."""
        self.call("setIntegrator", integration_time_us, leak_time_us)

    def differentiator(self, differentiation_time_us: float, limit_time_us: float = 10.0):
        """Differentiator: output = Vref + tau_d x d(input)/dt, with the gain limited to
        tau_d / limit above 1 / (2 pi limit). Times in microseconds."""
        self.call("setDifferentiator", differentiation_time_us, limit_time_us)

    def comparator(self, threshold: float):
        """Comparator (digital output, 0 / VDD): HIGH when the input is above the
        threshold (V). The same as comparator_schmitt(threshold, threshold)."""
        self.call("setComparatorSchmitt", threshold, threshold)

    def comparator_schmitt(self, upper: float, lower: float):
        """Schmitt trigger (digital output): HIGH above upper, LOW below lower (V),
        otherwise unchanged (hysteresis)."""
        self.call("setComparatorSchmitt", upper, lower)

    def comparator_window(self, upper: float, lower: float):
        """Window comparator (digital output): HIGH when the input is above upper or
        below lower (V), LOW inside the window."""
        self.call("setComparatorWindow", upper, lower)

    def clipper(self, upper: float, lower: float):
        """Hard clipper: passes the input between lower and upper (V), clips outside."""
        self.call("setClipper", upper, lower)

    def soft_clipper(self, upper: float, lower: float):
        """Soft clipper: smooth saturation toward lower and upper (V), like diodes."""
        self.call("setSoftClipper", upper, lower)

    def rectifier_half(self, polarity: str = "pos"):
        """Half-wave rectifier at Vref: max(input, Vref) ("pos") or min ("neg")."""
        self.call("setRectifierHalf", polarity)

    def rectifier_full(self, polarity: str = "pos"):
        """Full-wave rectifier: Vref + |input - Vref| ("pos") or Vref - |...| ("neg")."""
        self.call("setRectifierFull", polarity)

    def envelope(self, decay_time_us: float, polarity: str = "pos"):
        """Envelope follower: follows the peak of the input above Vref ("pos") or below
        ("neg") and decays toward Vref with the time constant (us, the RC). The output is
        on the side of the peak: Vref + peak ("pos"), Vref - peak ("neg")."""
        self.call("setEnvelopeFollower", decay_time_us, polarity)

    def peak_hold(self, polarity: str = "pos"):
        """Peak hold (envelope follower without decay). The peak is kept when the
        settings change; switch to another mode (e.g. bypass()) to reset it."""
        self.call("setPeakHold", polarity)

    # Time: sample & hold, slew rate, delay (experimental modes of the library 0.2:
    # the sketch MimicLab 0.1.3 or later)

    def sample_hold(self, freq: float):
        """Sample and hold: takes the input once every 1 / freq s and holds it (a step
        output). The period is a whole number of module samples (5 us). The held value
        starts at mid-scale when the mode is selected."""
        self.call("setSampleAndHold", freq)

    def track_hold(self, freq: float, track_ratio: float = 0.5):
        """Track and hold: follows the input for track_ratio of every period (1 / freq)
        and holds the last value for the rest."""
        self.call("setTrackAndHold", freq, track_ratio)

    def slew_rate(self, slew_v_per_us: float):
        """Slew rate limiter, like the slew rate of an op-amp: the output changes by at
        most slew_v_per_us V/us (the step is VDD / 32768 per 5 us sample, about 0.03 V/ms
        at 5 V). The output starts at mid-scale when the mode is selected."""
        self.call("setSlewRateLimiter", slew_v_per_us)

    def delay(self, samples: int):
        """Delay line (dead time): output = input delayed by samples x 5 us
        (0 - 4095 samples, up to 20.475 ms)."""
        self.call("setDigitalDelay", int(round(samples)))

    # Signal sources and modulators (experimental modes of the library 0.2: the sketch
    # MimicLab 0.1.4 or later). Waveforms: "sine", "triangle", "square", "sawtooth".

    def constant_voltage(self, volts: float):
        """Constant voltage source: the output stays at volts (V) whatever the input."""
        self.call("setConstantVoltage", volts)

    def oscillator(self, freq: float, amplitude: float, waveform: str = "sine"):
        """Oscillator (function generator): Vref + amplitude x wave(2 pi freq t). Every
        waveform starts at Vref and rises; the phase continues when the settings change."""
        self.call("setOscillator", freq, amplitude, waveform)

    def vco(self, center_freq: float, hz_per_volt: float, amplitude: float, waveform: str = "sine"):
        """Voltage-controlled oscillator: frequency = center_freq + hz_per_volt x
        (input - Vref), limited to 0 - 100 kHz."""
        self.call("setVco", center_freq, hz_per_volt, amplitude, waveform)

    def am(self, carrier_freq: float, carrier_amplitude: float, depth_per_volt: float,
           waveform: str = "sine"):
        """AM modulator: Vref + carrier_amplitude x (1 + depth_per_volt x (input - Vref))
        x carrier. depth_per_volt = 1 gives 100 % modulation at 1 V."""
        self.call("setAmModulator", carrier_freq, carrier_amplitude, depth_per_volt, waveform)

    def ring(self, carrier_freq: float, gain: float = 1.0, waveform: str = "sine"):
        """Ring (balanced, DSB) modulator: Vref + gain x (input - Vref) x carrier."""
        self.call("setRingModulator", carrier_freq, gain, waveform)

    def pwm(self, carrier_freq: float, full_scale: float, waveform: str = "triangle"):
        """PWM modulator (digital output): HIGH while the input is above the carrier;
        duty 0 % at Vref - full_scale, 50 % at Vref, 100 % at Vref + full_scale.
        waveform: "triangle" (both edges move) or "sawtooth" (one edge fixed)."""
        self.call("setPwmModulator", carrier_freq, full_scale, waveform)

    def vf(self, hz_per_volt: float, zero_freq: float = 0.0):
        """V/F converter (digital output, 50 % square): frequency = zero_freq +
        hz_per_volt x (input - Vref), limited to 0 - 100 kHz (HIGH at 0 Hz)."""
        self.call("setVfConverter", hz_per_volt, zero_freq)

    def noise(self, amplitude: float, color: str = "white"):
        """Noise generator (input not used): "white" is uniform within +/-amplitude (rms
        amplitude / sqrt 3); "pink" falls by 3 dB per octave, rms amplitude / 3."""
        self.call("setNoise", amplitude, color)

    # Nonlinear: logarithm, multiplier, true RMS, dead zone (experimental modes of the
    # library 0.2: the sketch MimicLab 0.1.5 or later). The outputs of antilog, squarer,
    # square rooter and true RMS are magnitudes from 0 V: lift them with output_offset().

    def log(self, slope: float = 1.0, unit: float = 0.5):
        """Logarithmic amplifier: Vref + slope x log10((input - Vref) / unit); slope in V
        per decade (negative inverts). Inputs near or below Vref saturate low."""
        self.call("setLog", slope, unit)

    def antilog(self, slope: float = 1.0, unit: float = 0.5):
        """Antilogarithmic (exponential) amplifier: unit x 10^((input - Vref) / slope),
        from 0 V. slope = 1 / log10(2) = 3.32 V per decade doubles the output per volt."""
        self.call("setAntilog", slope, unit)

    def squarer(self, unit: float = 0.0):
        """Squarer: (input - Vref)^2 / unit, from 0 V; unit 0 uses VDD / 4 (1.25 V)."""
        self.call("setSquarer", unit)

    def square_rooter(self, unit: float = 0.0):
        """Square rooter: sqrt((input - Vref) x unit), from 0 V, 0 below Vref; unit 0
        uses VDD / 4 (1.25 V)."""
        self.call("setSquareRooter", unit)

    def true_rms(self, averaging_time_us: float):
        """True RMS-to-DC converter: sqrt(mean((input - Vref)^2)), from 0 V, averaged
        with the time constant in us (10 us - 10 s)."""
        self.call("setTrueRms", averaging_time_us)

    def dead_zone(self, upper: float, lower: float):
        """Dead zone: Vref while the input is between lower and upper (V), and
        Vref + (input - limit) beyond a limit (slope 1, no step)."""
        self.call("setDeadZone", upper, lower)

    def output_offset(self, volts: float):
        """Adds volts to the output of every mode (0 by default)."""
        self.call("setOutputOffset", volts)

    def vref(self, volts: float):
        """Reference voltage (signal ground) of the module, 2.5 V by default."""
        self.call("setVref", volts)
