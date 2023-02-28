# 8つのAWGから10サイクルの正弦波を出力しキャプチャする

[awg_x8_send_recv.py](./awg_x8_send_recv.py) は，8つの AWG から特定の周波数の波形を出力し，それをキャプチャするものです．
出力される波形は，10サイクルの正弦波と出力期間 2.5[us] の正弦波で，どちらも周波数は同じです．
キャプチャデータのうち，10サイクルの正弦波はそのままグラフとして出力され，2.5[us] の正弦波は FFT スペクトルの計算に使用されます．

![AWG0から出力される波形](images/awg-x8-send-recv-example.png)

## セットアップ

次のようにADCとDACを接続します．

![セットアップ](../../docs/images/awg-x8-send-recv-setup.png)

差動入出力を接続する際は，付属の BPF を取り付けた SMA ケーブルで接続します．

## DRAMを利用する場合

以下のコマンドを実行します．

```
python awg_x8_send_recv.py
```

8つの AWG に対応するキャプチャ波形とスペクトルのグラフが，カレントディレクトリの下の `plot_awg_x8_send_recv` ディレクトリ以下に作成されます．

<br>

AWG 1 (LPF 内蔵ポート) の波形のキャプチャデータ  
![AWG 1 の波形のキャプチャデータ](images/awg-x8-send-recv-result-1.png)

AWG 2 (HPF 内蔵ポート) の波形のキャプチャデータ  
![AWG 2 の波形のキャプチャデータ](images/awg-x8-send-recv-result-2.png)

AWG 4 (差動入出力ポート) の波形のキャプチャデータ  
![AWG 4 の波形のキャプチャデータ](images/awg-x8-send-recv-result-3.png)

AWG 1 (LPF 内蔵ポート) の波形のスペクトル  
![AWG 1 の波形のスペクトル](images/awg-x8-send-recv-spectrum-1.png)

AWG 2 (HPF 内蔵ポート) の波形のスペクトル  
![AWG 2 の波形のスペクトル](images/awg-x8-send-recv-spectrum-2.png)

AWG 4 (差動入出力ポート) の波形のスペクトル  
![AWG 4 の波形のスペクトル](images/awg-x8-send-recv-spectrum-3.png)


## BRAMを利用する場合

以下のコマンドを実行します．

```
python awg_x8_send_recv.py prv_cap_ram
```

8つの AWG に対応するキャプチャ波形とスペクトルのグラフが，カレントディレクトリの下の `plot_awg_x8_send_recv_prv_cap_ram` ディレクトリ以下に作成されます．

AWG 0 (LPF 内蔵ポート) の波形のキャプチャデータ  
![AWG 0 の波形のキャプチャデータ](images/awg-x8-send-recv-bram-result-1.png)

AWG 2 (HPF 内蔵ポート) の波形のキャプチャデータ  
![AWG 2 の波形のキャプチャデータ](images/awg-x8-send-recv-bram-result-2.png)

AWG 7 (差動入出力ポート) の波形のキャプチャデータ  
![AWG 7 の波形のキャプチャデータ](images/awg-x8-send-recv-bram-result-3.png)

AWG 0 (LPF 内蔵ポート) の波形のスペクトル  
![AWG 0 の波形のスペクトル](images/awg-x8-send-recv-bram-spectrum-1.png)

AWG 2 (LPF 内蔵ポート) の波形のスペクトル  
![AWG 2 の波形のスペクトル](images/awg-x8-send-recv-bram-spectrum-2.png)

AWG 7 (LPF 内蔵ポート) の波形のスペクトル  
![AWG 7 の波形のスペクトル](images/awg-x8-send-recv-bram-spectrum-3.png)
