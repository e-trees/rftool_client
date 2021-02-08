# 任意のサンプル値を持つ波形を出力する

[awg_any_wave_send_recv.py](../awg_any_wave_send_recv.py) は，Python スクリプト内でサンプル値を定義した波形を
AWG 0 と AWG 1 から出力し，キャプチャするスクリプトです．
AWG 0 は, 周波数と振幅が異なる 4 つの正弦波を 1 周期ずつ繰り返し出力します．
AWG 1 は，60 [MHz] の正弦波 である I データと，固定値の Q データに 50 [MHz] の IQ ミキサをかけて出力します．

AWG 0 の Real データ
![AWG 0 の出力波形](images/actual_seq_0_waveform.png)

AWG 1 の IQ データ
![AWG 1 の出力波形](images/actual_seq_1_waveform.png)

## セットアップ

次のように ADC と DAC を接続します．

![セットアップ](../../docs/images/awg-x2-setup.png)

## 実行手順と結果

以下のコマンドを実行します．

```
python awg_any_wave_send_recv.py
```

キャプチャモジュール 0 がキャプチャした波形のグラフと，キャプチャモジュール 1 がキャプチャした波形とそのスペクトルのグラフが，カレントディレクトリの下の `plot_awg_any_wave_send_recv` ディレクトリ以下に作成されます．
スペクトルのピークが現れる位置は，同スクリプトのファイルコメントを参照してください．

キャプチャモジュール 0 がキャプチャした波形 (先頭 3992 サンプル)
![キャプチャモジュール 0 がキャプチャした波形](images/AWG_0_step_0_frame_0_captured.png)

キャプチャモジュール 1 がキャプチャした波形 (先頭 212 サンプル)
![キャプチャモジュール 1 がキャプチャした波形](images/AWG_1_step_0_frame_0_captured.png)

キャプチャモジュール 1 がキャプチャした波形のスペクトル
![キャプチャモジュール 1 がキャプチャした波形のスペクトル](images/AWG_1_step_0_frame_0_FFT_abs.png)
