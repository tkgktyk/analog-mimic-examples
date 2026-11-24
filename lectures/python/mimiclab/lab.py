# SPDX-License-Identifier: MIT
"""Serial protocol of the MimicLab sketch (proto 1).

Every command gets one line, "ok ..." or "err <reason>"; lines starting with "#" are
for people and skipped. "scope capture" answers "ok bin <bytes> <channels> <points> <fs>",
then the binary data (uint16 little endian, channels interleaved), then a line "end".
"""

from __future__ import annotations

import time

import numpy as np
import serial
from serial.tools import list_ports

PROTOCOL = 1
ARDUINO_VID = 0x2341


class MimicLabError(RuntimeError):
    """An error answered by the instrument, or a broken reply."""


def find_port() -> str:
    """Returns the serial port of the Arduino, if exactly one is connected."""
    ports = [p for p in list_ports.comports() if p.vid == ARDUINO_VID]
    if len(ports) == 1:
        return ports[0].device
    names = ", ".join(f"{p.device} ({p.description})" for p in list_ports.comports()) or "none"
    if not ports:
        raise MimicLabError(f"No Arduino found. Serial ports: {names}")
    raise MimicLabError(f"Several Arduinos found; give the port, e.g. MimicLab('COM5'). Ports: {names}")


def _arg(x) -> str:
    if isinstance(x, bool):
        return "on" if x else "off"
    if isinstance(x, (int, float, np.number)):
        return f"{float(x):.9g}"
    return str(x)


def _keys(text: str) -> dict:
    """Parses "word key=value key=value" into {"key": value}; the first word is "_"."""
    out = {}
    for i, tok in enumerate(text.split()):
        if "=" in tok:
            k, v = tok.split("=", 1)
            try:
                out[k] = float(v) if any(c in v for c in ".e") else int(v)
            except ValueError:
                out[k] = v
        elif i == 0:
            out["_"] = tok
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
        self._ser = serial.Serial(self.port, baud, timeout=timeout)
        self.info = self._connect()
        self.vref = float(self.info["vref"])
        self.fs = float(self.info["fs"])
        self.adc_bits = int(self.info["adc"])
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
                    raise MimicLabError(f"No answer from MimicLab on {self.port}. "
                                        "Is the MimicLab sketch written to the Arduino?")
                time.sleep(0.3)
        info = _keys(reply)
        if info.get("_") != "MimicLab":
            raise MimicLabError(f"Not a MimicLab: {reply}")
        if info.get("proto") != PROTOCOL:
            raise MimicLabError(f"Protocol {info.get('proto')} of the sketch, {PROTOCOL} of this "
                                "library: update the sketch or the library")
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
        self._ser.write((line + "\n").encode("ascii"))
        reply = self._readline()
        if reply == "ok":
            return ""
        if reply.startswith("ok "):
            return reply[3:]
        if reply.startswith("err"):
            raise MimicLabError(f"{line!r}: {reply[3:].strip()}")
        raise MimicLabError(f"{line!r}: unexpected reply {reply!r}")

    def close(self):
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
        return _keys(self._lab.command("fg " + " ".join(_arg(a) for a in args)))

    def sine(self, freq: float, amp: float, offset: float | None = None) -> dict:
        return self._set("sine", freq, amp, *([] if offset is None else [offset]))

    def square(self, freq: float, amp: float, offset: float | None = None) -> dict:
        return self._set("square", freq, amp, *([] if offset is None else [offset]))

    def triangle(self, freq: float, amp: float, offset: float | None = None) -> dict:
        return self._set("triangle", freq, amp, *([] if offset is None else [offset]))

    def dc(self, volts: float) -> dict:
        return self._set("dc", volts)

    def status(self) -> dict:
        return _keys(self._lab.command("fg"))


class Scope:
    """2-channel scope: CH1 = A1 (module input), CH2 = A2 (module output)."""

    def __init__(self, lab: MimicLab):
        self._lab = lab

    def capture(self, points: int = 2000, fs: float | None = None, sync: bool | None = None):
        """Captures both channels.

        Args:
            points: Points per channel (1 - 4000).
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
        """Amplifier: output = gain x (input - Vref) + Vref."""
        self.call("setPGA", gain)

    def filter1st_lpf(self, fc: float):
        """First-order low-pass filter (RC), cutoff fc in Hz."""
        self.call("setFilter1stLPF", fc)

    def filter1st_hpf(self, fc: float):
        """First-order high-pass filter (CR), cutoff fc in Hz."""
        self.call("setFilter1stHPF", fc)

    def filter1st_apf(self, fc: float):
        """First-order all-pass filter: gain 1, phase -180 to 0 degrees (-90 at fc)."""
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

    def vref(self, volts: float):
        """Reference voltage (signal ground) of the module, 2.5 V by default."""
        self.call("setVref", volts)
