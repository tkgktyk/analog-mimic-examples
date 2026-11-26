# Analog Mimic Examples

[English](#english)

[Analog Mimic](https://github.com/tkgktyk/analog-mimic) のモジュールを使った講義と作例です。

| | 内容 |
|---|---|
| [`lectures/`](lectures/) | **講義**:アナログ信号処理と回路のブロックを、Arduino と Python のノートブックで、実機で測りながら学ぶ。増幅、フィルタ、時間の処理、非線形、信号源と変調、演算の 0〜7 章。回路がわからない人はここから |
| [`projects/`](projects/) | 作例:センサーとモジュールで作るもの(準備中、英語) |

モジュールの API の例(デモ)は、Arduino のライブラリ [analog-mimic-arduino](https://github.com/tkgktyk/analog-mimic-arduino) の `examples/` にあります。

## 必要なもの

- Arduino **UNO R4 Minima**(推奨)。UNO R4 WiFi は対応を想定していますが未確認です。**UNO R3 では動きません**(DAC がないため)。
- Analog Mimic(MIMIC01、ファーム fw-20261125 以降)
- Arduino IDE と、ライブラリマネージャの **AnalogMimic 0.2.1 以降**

講義の始め方(Python の準備、測定器のスケッチの書きこみ、結線)は [`lectures/README.md`](lectures/README.md) にあります。機材がなくても、GitHub でノートブックを開けば、説明と実機で測った結果のグラフを読めます。

---

## English

Lectures and projects with the [Analog Mimic](https://github.com/tkgktyk/analog-mimic) module.

| | Contents |
|---|---|
| [`lectures/`](lectures/) | **Lectures** (in Japanese): analog signal processing and circuit blocks, measured on hardware with an Arduino and Python notebooks. Chapters 0 - 7: amplifiers, filters, time, nonlinear circuits, sources and modulators, computation |
| [`projects/`](projects/) | Projects: things to build with sensors and the module (coming soon) |

API examples (demos) of the module are in the `examples/` of the Arduino library [analog-mimic-arduino](https://github.com/tkgktyk/analog-mimic-arduino).

### Requirements

- Arduino **UNO R4 Minima** (recommended). The UNO R4 WiFi should work but is not tested yet. **The UNO R3 does not work** (no DAC).
- Analog Mimic (MIMIC01, firmware fw-20261125 or later)
- Arduino IDE and **AnalogMimic 0.2.1 or later** from the Library Manager

How to start the lectures (Python, the instrument sketch, the wiring): [`lectures/README.md`](lectures/README.md). The notebooks can be read on GitHub without the hardware, with the graphs measured on hardware.

### License

| Files | License |
|---|---|
| Sketches (.ino), Python code (including `schematic.py`), code cells of the notebooks | MIT ([`LICENSE`](LICENSE)) |
| Text (README etc.), text cells of the notebooks, figures (SVG), photos | CC BY 4.0 ([`LICENSE-CC-BY-4.0`](LICENSE-CC-BY-4.0)) |

Copyright (c) 2026 TAKAGI Katsuyuki

## For developers

The `platformio.ini` at the root is for development (learners write the sketches with the Arduino IDE). Open the root in VS Code, open the .ino of a sketch and press Ctrl+Shift+B. The library is the working copy next to this repository (`../analog-mimic-arduino`). Sketch names (folder names) must be unique in the whole repository.

Figures are made by scripts: wiring diagrams (`schematic.py` → `schematic.svg`) and circuit diagrams (`circuit.py` → `circuit.svg`) with schemdraw and `extras/schematics/mimic_parts.py` of the library (the working copy next to this repository), response sketches (`response.py` → `response.svg`) with matplotlib (`lectures/tools/figures.py`). After changing a script, regenerate with `uv run --project lectures python <script>` and commit the SVG too.

Python tests (`mimiclab` and every notebook against a fake instrument): `cd lectures`, then `uv run pytest`. GitHub Actions (`.github/workflows/ci.yml`) compiles every sketch (UNO R4 Minima / WiFi, AnalogMimic from the Library Manager), runs the Python tests (Ubuntu / Windows) and checks that the figures are up to date.

The lecture notebooks are saved with the results measured on hardware (MimicLab and the firmware version are printed in the first output). After changing a notebook, run it on hardware with *Restart Kernel and Run All Cells* and commit it with its outputs.
