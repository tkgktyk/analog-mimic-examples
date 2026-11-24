# SPDX-License-Identifier: MIT
import sys
import pathlib

import matplotlib
import pytest

matplotlib.use("Agg")  # no windows in the tests
sys.path.insert(0, str(pathlib.Path(__file__).parent))

import fake_device  # noqa: E402
import mimiclab.lab  # noqa: E402


@pytest.fixture
def fake(monkeypatch):
    """Replaces the serial port with the fake instrument; returns the list of the fakes made."""
    made = []

    def make(*args, **kwargs):
        dev = fake_device.FakeSerial(*args, **kwargs)
        made.append(dev)
        return dev

    monkeypatch.setattr(mimiclab.lab.serial, "Serial", make)
    monkeypatch.setattr(mimiclab.lab, "find_port", lambda: "FAKE")
    return made
