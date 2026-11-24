# SPDX-License-Identifier: MIT
"""The protocol of mimiclab against the fake instrument."""
import numpy as np
import pytest

from mimiclab import MimicLab, MimicLabError
import fake_device


def test_connect(fake):
    lab = MimicLab()
    assert lab.info["name"] == "MimicLab"
    assert lab.info["mimic"] == 20261123
    assert lab.vref == 5.0 and lab.fs == 20000.0 and lab.adc_bits == 14


def test_protocol_mismatch(fake, monkeypatch):
    def old_id(self, t):
        return b"ok MimicLab proto=99 ver=9 fs=20000 dac=12 adc=14 mimic=none vref=5.000\n"
    monkeypatch.setattr(fake_device.FakeSerial, "answer", old_id)
    with pytest.raises(MimicLabError, match="Protocol"):
        MimicLab()


def test_fg(fake):
    lab = MimicLab()
    assert lab.fg.sine(100, 1.0) == {"wave": "sine", "freq": 100.0, "amp": 1.0, "offset": 2.5}
    assert lab.fg.square(50, 0.5, 2.0)["offset"] == 2.0
    assert lab.fg.dc(1.25)["wave"] == "dc"
    assert fake[0].sent[-1] == "fg dc 1.25"


def test_mimic_commands(fake):
    lab = MimicLab()
    lab.mimic.filter1st_lpf(100)
    lab.mimic.setFilterBiquadLPF(1000, 0.7071)
    lab.mimic.setOutputOpen(False)
    lab.mimic.setEnvelopeFollower(1000, "neg")
    assert fake[0].sent[-4:] == [
        "mimic setFilter1stLPF 100",
        "mimic setFilterBiquadLPF 1000 0.7071",
        "mimic setOutputOpen off",
        "mimic setEnvelopeFollower 1000 neg",
    ]
    assert lab.mimic.list() == ["setFilter1stLPF", "getStatus", "getInputVolts"]
    assert lab.mimic.build_date() == "20261123"
    with pytest.raises(MimicLabError, match="unknown method"):
        lab.mimic.call("noSuchMethod")


def test_capture(fake):
    lab = MimicLab()
    lab.fg.sine(100, 1.0)
    lab.mimic.filter1st_lpf(100)
    t, ch1, ch2 = lab.scope.capture(2000, fs=10000)
    assert len(t) == len(ch1) == len(ch2) == 2000
    assert t[1] == pytest.approx(1e-4)
    assert ch1.max() == pytest.approx(3.5, abs=1e-3)
    assert ch1.min() == pytest.approx(1.5, abs=1e-3)
    assert (ch2.max() - ch2.min()) / 2 == pytest.approx(1 / np.sqrt(2), abs=0.01)
    assert fake[0].sent[-1] == "scope capture 2000 2"


def test_capture_fs_must_divide(fake):
    lab = MimicLab()
    with pytest.raises(ValueError):
        lab.scope.capture(100, fs=3000)


def test_unknown_command(fake):
    lab = MimicLab()
    with pytest.raises(MimicLabError, match="unknown command"):
        lab.command("nothing")
