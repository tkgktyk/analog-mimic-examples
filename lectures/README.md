# 講義(Analog Mimic で学ぶアナログ信号処理)

Arduino UNO R4 を**測定器**(信号発生器と 2ch のオシロ)にして、Mimic に信号を入れ、入力と出力を Python のノートブックでグラフにしながら学びます。
機材がなくても、GitHub でノートブックを開けば説明と結果のグラフを読めます。

> 公開済みのモード(AnalogMimic 0.2)の講義はそろっています。新しいモードの講義は、モードの公開に合わせて足していきます。

## 必要なもの

- PC(Windows / macOS / Linux)
- Arduino **UNO R4 Minima**(推奨)。UNO R4 WiFi は対応を想定していますが未確認です。UNO R3 では動きません(DAC がないため)。
- Analog Mimic(MIMIC01、ファーム fw-20261125 以降)
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

章ごとのフォルダに分かれています。各講義はノートブック 1 本(例 `02_filter1st/01_lpf.ipynb`)で、回路、原理、Mimic の設定、実験をまとめています。図とそのスクリプトは、同じ名前のフォルダ(`02_filter1st/01_lpf/`)にあります。

| 章 | 講義 |
|---|---|
| [0 準備](00_intro/) | [0-0 測定器で電圧を見る(オシロスコープ)](00_intro/00_scope.ipynb)、[0-1 測定器の使い方(ボルテージフォロワ)](00_intro/01_bypass.ipynb) |
| [1 増幅](01_amplifier/) | [1-1 増幅回路(非反転増幅・反転増幅)](01_amplifier/01_pga.ipynb) |
| [2 1 次フィルタ](02_filter1st/) | [2-1 ローパスフィルタ(LPF)](02_filter1st/01_lpf.ipynb)、[2-2 ハイパスフィルタ(HPF)](02_filter1st/02_hpf.ipynb)、[2-3 周波数特性を測る(ボード線図)](02_filter1st/03_bode.ipynb)、[2-4 オールパスフィルタ(APF)](02_filter1st/04_apf.ipynb) |
| [3 2 次フィルタ](03_filter2nd/) | [3-1 ローパスフィルタ(サレン・キー)](03_filter2nd/01_sk_lpf.ipynb)、[3-2 ハイパスフィルタ(サレン・キー)](03_filter2nd/02_sk_hpf.ipynb)、[3-3 バンドパスフィルタ(多重帰還)](03_filter2nd/03_mfb_bpf.ipynb)、[3-4 ノッチフィルタ(ツイン T)](03_filter2nd/04_notch.ipynb)、[3-5 状態変数フィルタ](03_filter2nd/05_svf.ipynb) |
| [4 時間の処理](04_time/) | [4-1 積分器](04_time/01_integrator.ipynb)、[4-2 微分器](04_time/02_differentiator.ipynb)、[4-3 サンプル&ホールド](04_time/03_sample_hold.ipynb)、[4-4 スルーレート](04_time/04_slew_rate.ipynb)、[4-5 遅延(むだ時間)](04_time/05_delay.ipynb) |
| [5 非線形の回路](05_nonlinear/) | [5-1 比較器とシュミットトリガ](05_nonlinear/01_comparator.ipynb)、[5-2 ウィンドウ比較器](05_nonlinear/02_window.ipynb)、[5-3 クリッパ](05_nonlinear/03_clipper.ipynb)、[5-4 整流回路](05_nonlinear/04_rectifier.ipynb)、[5-5 ピークホールドとエンベロープ](05_nonlinear/05_peak_envelope.ipynb) |
| [6 信号源と変調](06_source/) | [6-1 発振器と定電圧](06_source/01_oscillator.ipynb)、[6-2 VCO(電圧制御発振器)](06_source/02_vco.ipynb)、[6-3 ノイズ(雑音)](06_source/03_noise.ipynb)、[6-4 AM とリング変調](06_source/04_modulator.ipynb)、[6-5 PWM と V/F 変換](06_source/05_pwm_vf.ipynb) |

最初に 0 章(0-0、0-1)をやってください。
