# 講義(Analog Mimic で学ぶアナログ信号処理)

Arduino UNO R4 を**測定器**(信号発生器と 2ch のオシロ)にして、Mimic に信号を入れ、入力と出力を Python のノートブックでグラフにしながら学びます。
機材がなくても、GitHub でノートブックを開けば説明と結果のグラフを読めます。

> 作成中です。

## 必要なもの

- PC(Windows / macOS / Linux)
- Arduino **UNO R4 Minima**(推奨)。UNO R4 WiFi は対応を想定していますが未確認です。UNO R3 では動きません(DAC がないため)。
- Analog Mimic(MIMIC01、ファーム fw-20261123 以降)
- ジャンパーワイヤー、ブレッドボード

## 結線(全講義で同じ)

![結線図](schematic.svg)

A0 は二股にして、Mimic の AIN と A1 の両方につなぎます(ブレッドボードを使います)。

| UNO R4 | Mimic | 役割 |
|---|---|---|
| 5V | VCC | 電源 |
| GND | GND | |
| SDA | SDA | I²C |
| SCL | SCL | I²C |
| A0(DAC) | AIN | 信号発生器の出力 → Mimic の入力 |
| A1 | (A0 につなぐ) | CH1:Mimic の入力を読み直す |
| A2 | AOUT | CH2:Mimic の出力 |

## 準備

### 1. 測定器のスケッチを書き込む(最初の 1 回だけ)

1. Arduino IDE の Library Manager で **AnalogMimic**(0.2.0 以降)を入れる。
2. [`firmware/MimicLab/MimicLab.ino`](firmware/MimicLab/) を開いて UNO R4 に書き込む。

### 2. Python の環境を作る

[uv](https://docs.astral.sh/uv/) を使います(Python 本体も uv が入れます)。

```
winget install --id=astral-sh.uv -e      (Windows。macOS / Linux は uv のサイトの手順で)
cd analog-mimic-examples/lectures
uv sync
uv run jupyter lab
```

VS Code で開く場合は、`uv sync` でできた `lectures/.venv` をノートブックのカーネルに選びます。

<details><summary>uv が使えない場合(venv + pip)</summary>

Python 3.10 以降(3.12 を推奨)を入れてから:

```
cd analog-mimic-examples/lectures
python -m venv .venv
.venv\Scripts\activate          (macOS / Linux は source .venv/bin/activate)
pip install -e .
jupyter lab
```
</details>

## 講義

| | 内容 |
|---|---|
| [01](01_lpf/) | 正弦波をローパスフィルタに通す(試作) |
