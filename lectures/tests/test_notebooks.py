# SPDX-License-Identifier: MIT
"""Every code cell of every lecture notebook runs against the fake instrument
(the notebooks keep working when mimiclab changes)."""
import json
import pathlib

import matplotlib.pyplot as plt
import pytest

LECTURES = pathlib.Path(__file__).resolve().parents[1]
NOTEBOOKS = sorted(p for p in LECTURES.glob("*/*.ipynb") if ".ipynb_checkpoints" not in p.parts)


def test_notebooks_found():
    assert NOTEBOOKS


@pytest.mark.parametrize("path", NOTEBOOKS, ids=lambda p: p.name)
def test_notebook_runs(fake, path, monkeypatch):
    monkeypatch.chdir(path.parent)
    nb = json.loads(path.read_text(encoding="utf-8"))
    scope = {"__name__": "__main__"}
    for i, cell in enumerate(nb["cells"]):
        if cell["cell_type"] != "code":
            continue
        source = "".join(cell["source"])
        try:
            exec(compile(source, f"{path.name}[{i}]", "exec"), scope)
        except Exception as e:
            raise AssertionError(f"{path.name}, cell {i}:\n{source}") from e
    plt.close("all")
