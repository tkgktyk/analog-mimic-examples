# Analog Mimic Examples

[Analog Mimic](https://github.com/tkgktyk/analog-mimic) のモジュールを使った講義と作例です。
Lectures and projects with the Analog Mimic module.

| | 内容 / Contents | 言葉 / Language |
|---|---|---|
| [`lectures/`](lectures/) | 講義:アナログ信号処理と回路ブロックを、Arduino と Python のノートブックで学ぶ。回路がわからない人はここから | 日本語 |
| [`projects/`](projects/) | Projects: things to build with sensors and the module | English |

モジュールの API の例(デモ)は Arduino ライブラリ [analog-mimic-arduino](https://github.com/tkgktyk/analog-mimic-arduino) の `examples/` にあります。
API examples (demos) are in the `examples/` of the Arduino library [analog-mimic-arduino](https://github.com/tkgktyk/analog-mimic-arduino).

## 必要なもの / Requirements

- Arduino **UNO R4 Minima**(推奨 / recommended)。UNO R4 WiFi は対応を想定していますが未確認です(not tested yet)。**UNO R3 では動きません**(DAC がない / no DAC)。
- Analog Mimic(MIMIC01、ファーム / firmware fw-20261123 以降 / or later)
- Arduino IDE と、Library Manager の **AnalogMimic 0.2.0 以降** / or later

## 開発者向け / For developers

ルートの `platformio.ini` は開発用です(講義を受ける人は Arduino IDE で書き込みます)。
VS Code でルートを開き、スケッチの .ino を開いて Ctrl+Shift+B。ライブラリは隣の作業コピー(`../analog-mimic-arduino`)を使います。
The `platformio.ini` at the root is for development. Open the root in VS Code, open the .ino of a sketch and press Ctrl+Shift+B.
The library is the working copy next to this repository (`../analog-mimic-arduino`).
Sketch names (folder names) must be unique in the whole repository.

結線図(`schematic.py` → `schematic.svg`)は schemdraw で描き、ライブラリの `extras/schematics/mimic_parts.py`(隣の作業コピー)を使います。スクリプトを変えたら `python <フォルダ>/schematic.py` で作り直してコミットします。
The wiring diagrams (`schematic.py` → `schematic.svg`) are drawn with schemdraw and the `extras/schematics/mimic_parts.py` of the library (the working copy next to this repository). Regenerate and commit the SVG when the script changes.

Python のテスト(偽の測定器で `mimiclab` と全部のノートブックを動かす):`cd lectures` → `uv run pytest`。GitHub Actions(`.github/workflows/ci.yml`)は、全部のスケッチのコンパイル(UNO R4 Minima / WiFi、Library Manager の AnalogMimic)、Python のテスト(Ubuntu / Windows)、結線図が最新かを確かめます。
Python tests (mimiclab and every notebook against a fake instrument): `cd lectures`, then `uv run pytest`. GitHub Actions compiles every sketch (UNO R4 Minima / WiFi, AnalogMimic from the Library Manager), runs the Python tests (Ubuntu / Windows) and checks that the wiring diagrams are up to date.

## ライセンス / License

| 対象 / Files | ライセンス / License |
|---|---|
| スケッチ(.ino)、Python(.py、`schematic.py` を含む)、ノートブックのコードのセル / Sketches, Python code (including `schematic.py`), code cells of the notebooks | MIT([`LICENSE`](LICENSE)) |
| README などの本文、ノートブックの説明文、図(SVG)、写真 / Text (README etc.), text cells of the notebooks, figures (SVG), photos | CC BY 4.0([`LICENSE-CC-BY-4.0`](LICENSE-CC-BY-4.0)) |

Copyright (c) 2026 TAKAGI Katsuyuki
