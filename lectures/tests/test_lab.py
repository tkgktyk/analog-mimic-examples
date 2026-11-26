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
    assert lab.max_points == 2000
    with pytest.raises(MimicLabError, match="out of range"):
        lab.scope.capture(2001)


def test_protocol_mismatch(fake, monkeypatch):
    def old_id(self, t):
        return b"ok MimicLab proto=99 ver=9 fs=20000 dac=12 adc=14 mimic=none vref=5.000\n"
    monkeypatch.setattr(fake_device.FakeSerial, "answer", old_id)
    with pytest.raises(MimicLabError, match="proto"):
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


def test_pga_and_vref(fake):
    lab = MimicLab()
    lab.fg.sine(100, 0.5)
    lab.mimic.pga(-2)
    t, ch1, ch2 = lab.scope.capture(400)
    assert ch2.max() == pytest.approx(3.5, abs=0.01)
    assert np.corrcoef(ch1, ch2)[0, 1] < -0.99  # inverted
    lab.mimic.vref(2.0)
    assert fake[0].sent[-1] == "mimic setVref 2"


def test_frequency_response(fake):
    lab = MimicLab()
    lab.mimic.filter1st_lpf(100)
    r = lab.frequency_response([10, 100, 1000], settle=0)
    assert r.gain[1] == pytest.approx(0.707, abs=0.02)
    assert r.phase[1] == pytest.approx(-45, abs=3)
    assert r.gain_db[2] == pytest.approx(-20, abs=1)


def test_biquad(fake):
    lab = MimicLab()
    lab.mimic.biquad_lpf(100, 2)
    r = lab.frequency_response([100, 1000], settle=0)
    assert r.gain[0] == pytest.approx(2, rel=0.03)       # Q at fc
    assert r.phase[0] == pytest.approx(-90, abs=3)
    assert r.gain_db[1] == pytest.approx(-40, abs=1.5)   # 40 dB / decade
    lab.mimic.biquad_bpf(100, 5)
    r = lab.frequency_response([100], settle=0)
    assert r.gain[0] == pytest.approx(1, rel=0.03)


def test_nonlinear(fake):
    lab = MimicLab()
    lab.fg.sine(50, 1.0)
    lab.mimic.comparator_schmitt(3.0, 2.0)
    assert fake[0].sent[-1] == "mimic setComparatorSchmitt 3 2"
    t, ch1, ch2 = lab.scope.capture(400)          # one period
    assert set(np.round(ch2, 1)) <= {0.0, 5.0}    # digital output
    assert ch2[ch1 > 3.05].min() > 4.9 and ch2[ch1 < 1.95].max() < 0.1
    lab.mimic.comparator_window(3.0, 2.0)
    t, ch1, ch2 = lab.scope.capture(400)
    assert ch2[(ch1 > 2.1) & (ch1 < 2.9)].max() < 0.1
    lab.mimic.clipper(3.0, 2.0)
    t, ch1, ch2 = lab.scope.capture(400)
    assert ch2.max() == pytest.approx(3.0, abs=0.01) and ch2.min() == pytest.approx(2.0, abs=0.01)
    lab.mimic.rectifier_full("neg")
    assert fake[0].sent[-1] == "mimic setRectifierFull neg"
    t, ch1, ch2 = lab.scope.capture(400)
    assert ch2.max() == pytest.approx(2.5, abs=0.01) and ch2.min() == pytest.approx(1.5, abs=0.01)
    lab.mimic.peak_hold()
    t, ch1, ch2 = lab.scope.capture(400)
    assert ch2.min() == pytest.approx(3.5, abs=0.01)  # held at the peak


def test_port_busy(monkeypatch):
    import serial
    import mimiclab.lab

    def busy(*args, **kwargs):
        raise serial.SerialException("could not open port 'COM4': PermissionError")
    monkeypatch.setattr(mimiclab.lab.serial, "Serial", busy)
    with pytest.raises(MimicLabError, match="lab.close"):
        MimicLab("COM4")


def test_waveforms_and_phase(fake):
    from mimiclab import match_phase, plot_waveforms
    lab = MimicLab()
    lab.mimic.biquad_hpf(100, 2)
    r = lab.frequency_response([10, 100, 1000], settle=0, monitor=True)
    assert len(r.waves) == 3 and len(r.waves[0]) == 3
    fig = plot_waveforms(r)
    assert len(fig.axes) == 4
    theory = np.array([178.8, 90.0, 1.2])
    assert np.allclose(match_phase(r.phase - 360, theory), r.phase)


def test_shared_monitor_and_folded(fake, capsys):
    from mimiclab import Monitor, plot_waveforms
    lab = MimicLab()
    mon = Monitor()
    for q in (0.5, 2):
        lab.mimic.biquad_lpf(100, q)
        r = lab.frequency_response([50, 100], settle=0, monitor=mon, label=f"Q = {q}: ")
    assert mon.label == "Q = 2: "
    mon.close()
    assert plot_waveforms(r, collapsed=True) is None


def test_measure():
    from mimiclab.live import measure
    t = np.arange(2000) / 20000
    mean, f = measure(t, 2.5 + np.sin(2 * np.pi * 50 * t))
    assert abs(mean - 2.5) < 1e-3 and abs(f - 50) < 0.1
    noisy = 2.5 + 0.01 * np.sin(2 * np.pi * 60 * t) + 0.001 * np.random.default_rng(1).standard_normal(2000)
    assert abs(measure(t, noisy)[1] - 60) < 1           # 20 mV peak to peak
    assert measure(t, 3.3 + 0.001 * np.sin(2 * np.pi * 50 * t))[1] is None  # DC
    assert measure(t, 2.5 + np.sin(2 * np.pi * 5 * t))[1] is None          # half a period


def test_live_frames(fake):
    lab = MimicLab()
    live = lab.scope.live(frames=2)
    assert len(live.data[1]) == 2000 and not lab._lives
    assert fake[0].sent.count("scope capture 2000 1 free") == 2
    with pytest.raises(ValueError):
        lab.scope.live(mode="run", frames=1)


def test_live_thread(fake):
    import threading
    import time
    lab = MimicLab()
    lab.fg.sine(100, 1.0)
    live = lab.scope.live()           # thread and buttons (no kernel: the widgets do nothing)
    pause = threading.Event()         # time.sleep does nothing in the tests (conftest)
    deadline = time.monotonic() + 10
    while fake[0].sent.count("scope capture 2000 1 free") < 3 and time.monotonic() < deadline:
        lab.fg.sine(100, 1.0)         # other commands while it runs (the lock)
        pause.wait(0.01)              # the lock is not fair: let the thread take it (Windows)
    assert not live._status.value.startswith("Stopped"), live._status.value  # error in the thread
    assert fake[0].sent.count("scope capture 2000 1 free") >= 3
    live._scale_w.value = "auto"      # redraw with the last data
    live._mode_w.value = "single"
    live.stop()
    assert not live._thread.is_alive() and not lab._lives
    live2 = lab.scope.live(scale="auto")
    lab.close()                       # stops the live scope
    assert not live2._thread.is_alive()


def test_time_modes(fake):
    lab = MimicLab()
    lab.fg.sine(50, 1.0)
    lab.mimic.sample_hold(500)
    assert fake[0].sent[-1] == "mimic setSampleAndHold 500"
    t, ch1, ch2 = lab.scope.capture(2000)
    steps = np.flatnonzero(np.abs(np.diff(ch2)) > 0.02)
    assert abs(np.median(np.diff(t[steps])) - 0.002) < 1e-4       # one step every 2 ms
    lab.mimic.track_hold(200, 0.5)
    assert fake[0].sent[-1] == "mimic setTrackAndHold 200 0.5"
    lab.fg.square(50, 1.0)
    lab.mimic.slew_rate(0.001)                                      # 1 V/ms
    t, ch1, ch2 = lab.scope.capture(2000)
    assert 0.9e3 < np.max(np.abs(np.diff(ch2))) * 20000 < 1.1e3   # V/s
    lab.mimic.delay(1000)                                           # 5 ms
    assert fake[0].sent[-1] == "mimic setDigitalDelay 1000"
    t, ch1, ch2 = lab.scope.capture(2000)
    assert np.mean(np.abs(ch2[100:] - ch1[:-100]) < 0.01) > 0.99   # 100 points later (but the edges)


def test_sources(fake):
    lab = MimicLab()
    lab.mimic.oscillator(100, 1.0, "triangle")
    assert fake[0].sent[-1] == "mimic setOscillator 100 1 triangle"
    t, ch1, ch2 = lab.scope.capture(2000)
    assert abs(ch2.max() - 3.5) < 0.01 and abs(ch2.min() - 1.5) < 0.01
    lab.mimic.constant_voltage(1.2)
    assert abs(lab.scope.capture(100)[2].mean() - 1.2) < 0.01
    lab.fg.dc(3.0)                                    # 0.5 V above Vref
    lab.mimic.vco(1000, 200, 1.0, "square")           # 1100 Hz
    t, ch1, ch2 = lab.scope.capture(2000)
    rising = np.flatnonzero(np.diff(np.sign(ch2 - 2.5)) > 0)
    assert abs((len(rising) - 1) / (t[rising[-1]] - t[rising[0]]) - 1100) < 15
    lab.mimic.pwm(100, 1.0)                           # duty 75 % at Vref + 0.5 V
    assert abs((lab.scope.capture(2000)[2] > 2.5).mean() - 0.75) < 0.02
    lab.mimic.vf(1000)                                # 500 Hz
    t, ch1, ch2 = lab.scope.capture(2000)
    assert abs(np.count_nonzero(np.diff((ch2 > 2.5).astype(int)) > 0) - 50) <= 1
    lab.fg.sine(50, 1.0)
    lab.mimic.am(1000, 1.0, 0.5)
    lab.mimic.ring(1000)
    t, ch1, ch2 = lab.scope.capture(2000)
    assert ch2.max() < 3.51 and ch2.min() > 1.49
    lab.mimic.noise(1.0)
    v = lab.scope.capture(2000)[2]
    assert abs(v.std() - 1 / np.sqrt(3)) < 0.03
    lab.mimic.noise(1.0, "pink")
    assert fake[0].sent[-1] == "mimic setNoise 1 pink"
    assert abs(lab.scope.capture(2000)[2].std() - 1 / 3) < 0.03
