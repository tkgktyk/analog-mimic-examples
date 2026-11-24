# SPDX-License-Identifier: MIT
"""Every code cell of every lecture notebook runs against the fake instrument
(the notebooks keep working when mimiclab changes)."""
import json
import os
import pathlib

import matplotlib.pyplot as plt
import pytest

LECTURES = pathlib.Path(__file__).resolve().parents[1]


def find_notebooks():
    """Notebooks under lectures/, skipping hidden folders (.venv, .ipynb_checkpoints)."""
    found = []
    for folder, dirs, files in os.walk(LECTURES):
        dirs[:] = sorted(d for d in dirs if not d.startswith("."))
        found += [pathlib.Path(folder) / f for f in files if f.endswith(".ipynb")]
    return sorted(found)


NOTEBOOKS = find_notebooks()


def test_notebooks_found():
    assert NOTEBOOKS


@pytest.mark.parametrize("path", NOTEBOOKS, ids=lambda p: p.relative_to(LECTURES).as_posix())
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
