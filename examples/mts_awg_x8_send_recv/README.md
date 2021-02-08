# 8つのAWGから10サイクルの正弦波を出力しキャプチャする (MTS 版)

[mts_awg_x8_send_recv.py](../mts_awg_x8_send_recv.py) は，8つの AWG から特定の周波数の波形を出力し，8 つのキャプチャモジュールでキャプチャするスクリプトです．
出力される波形は、10サイクルの正弦波と出力期間 2.5[us] の正弦波で，どちらも周波数は同じです．
キャプチャデータのうち，10サイクルの正弦波はそのままグラフとして出力され，2.5[us] の正弦波は FFT スペクトルの計算に使用されます．

AWG 0 から出力される波形
![AWG 0 から出力される波形](images/awg_0_waveform.png)

## セットアップ

次のように ADC と DAC を接続します．

![セットアップ](../../docs/images/awg-x8-setup.png)

差動入出力を接続する際は，付属の BPF を取り付けた SMA ケーブルで接続します．

## 実行手順と結果

以下のコマンドを実行します．

```
python mts_awg_x8_send_recv.py
```

8つの AWG に対応するキャプチャ波形とスペクトルのグラフが，カレントディレクトリの下の `plot_mts_awg_x8_send_recv_prv_cap_ram` ディレクトリ以下に8枚ずつ作成されます．

LPF 内蔵ポート (AWG 0 と AWG 1 の DAC ポート) の波形をキャプチャした例
![LPF 内蔵ポートのキャプチャの波形例](images/AWG_0_step_0_captured.png)

HPF 内蔵ポート (AWG 2 と AWG 3 の DAC ポート) の波形をキャプチャした例
![HPF 内蔵ポートのキャプチャの波形例](images/AWG_2_step_0_captured.png)

差動入出力ポート (AWG 4 〜 AWG 7 の DAC ポート) の波形をキャプチャした例
![差動入出力ポートのキャプチャの波形例](images/AWG_5_step_0_captured.png)

LPF 内蔵ポート (AWG 0 と AWG 1 の DAC ポート) のキャプチャ波形のスペクトル例
![LPF 内蔵ポートのキャプチャ波形のスペクトル例](images/AWG_0_step_1_frame_0_FFT_abs.png)

HPF 内蔵ポート (AWG 2 と AWG 3 の DAC ポート) のキャプチャ波形のスペクトル例
![HPF 内蔵ポートのキャプチャ波形のスペクトル例](images/AWG_2_step_1_frame_0_FFT_abs.png)

差動入出力ポート (AWG 4 〜 AWG 7 の DAC ポート) のキャプチャ波形のスペクトル例
![差動入出力ポートのキャプチャ波形のスペクトル例](images/AWG_5_step_1_frame_0_FFT_abs.png)
