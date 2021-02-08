# AWG から出力した波形を積算しながらキャプチャする (Non-MTS 版)

[awg_accum_send_recv.py](../awg_accum_send_recv.py) は，AWG 0 から同じ波形を 1000 回繰り返し出力し，キャプチャモジュール 0 で波形同士を積算しながらキャプチャするスクリプトです．AWG 0 に設定する出力波形を以下の図に示します．実際には，ZCU111 付属のバラン内部の回路の構成により変位が反転した波形が出力されます．

AWG 0 の出力波形       
![AWG 0 の出力波形](images/awg_0_waveform.png)

## セットアップ

次のように ADC と DAC を接続します．

![セットアップ](../../docs/images/awg_x1_setup.png)

## 実行手順と結果

### DRAM をキャプチャ RAM として 使う場合

以下のコマンドを実行します．

```
python awg_accum_send_recv.py
```

キャプチャモジュール 0 がキャプチャした 2 つの波形のグラフが，カレントディレクトリの下の `plot_awg_accum_send_recv` ディレクトリ以下に作成されます．

キャプチャモジュール 0 がキャプチャした波形 1
![AWG 0 がキャプチャした波形 1](images/AWG_0_step_0_dram_captured.png)

キャプチャモジュール 0 がキャプチャした波形 2
![AWG 0 がキャプチャした波形 2](images/AWG_0_step_1_dram_captured.png)

### BRAM をキャプチャ RAM として 使う場合

以下のコマンドを実行します．

```
python awg_accum_send_recv.py prv_cap_ram
```

キャプチャモジュール 0 がキャプチャした 2 つの波形のグラフが，カレントディレクトリの下の `plot_awg_accum_send_recv_prv_cap_ram` ディレクトリ以下に作成されます．

キャプチャモジュール 0 がキャプチャした波形 1
![AWG 0 がキャプチャした波形 1](images/AWG_0_step_0_bram_captured.png)

キャプチャモジュール 0 がキャプチャした波形 2
![AWG 0 がキャプチャした波形 2](images/AWG_0_step_1_bram_captured.png)
