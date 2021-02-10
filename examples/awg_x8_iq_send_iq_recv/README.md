# 8つのAWGからI/Q変調した波形を出力しADCでI/Qミキサをかけてキャプチャ

[awg_x8_iq_send_iq_recv.py](../awg_x8_iq_send_iq_recv.py) は，8つの AWG からI/Q変調した波形を出力し，それをADCでI/Qミキサをかけてキャプチャするものです．結果はキャプチャした波形のスペクトルをIとQに分けて出力します．

![AWG0の被変調波](images/awg-x8-iq-send-iq-recv-example.png)

## セットアップ

ADCとDACを以下のように接続します．

![セットアップ](images/awg-x8-iq-send-iq-recv-setup.png)

差動入出力を接続する際は，付属の BPF を取り付けた SMA ケーブルで接続します．

## DRAM利用

```
python awg_x8_iq_send_iq_recv.py
```

として実行します．

カレントディレクトリの下の `plot_awg_x8_iq_send_iq_recv` ディレクトリの中に各 AWG ごとに I データと Q データのスペクトルのグラフが作成されます．スペクトルのピークが現れる位置は，同スクリプトのファイルコメントを参照してください．

キャプチャモジュール1のIデータスペクトル  
![キャプチャモジュール1のIデータスペクトル](images/awg-x8-iq-send-iq-recv-spectrum-i.png)

キャプチャモジュール1のQデータスペクトル  
![キャプチャモジュール1のQデータスペクトル](images/awg-x8-iq-send-iq-recv-spectrum-q.png)

## BRAM利用

```
python awg_x8_iq_send_iq_recv.py prv_cap_ram
```

として実行します．

カレントディレクトリの下の `plot_awg_x8_iq_send_iq_recv_prv_cap_ram` ディレクトリの中に各 AWG ごとに I データと Q データのスペクトルのグラフが作成されます．スペクトルのピークが現れる位置は，同スクリプトのファイルコメントを参照してください．

キャプチャモジュール1のIデータスペクトル  
![キャプチャモジュール1のIデータスペクトル](images/awg-x8-iq-send-iq-recv-bram-spectrum-i.png)

キャプチャモジュール1のQデータスペクトル  
![キャプチャモジュール1のQデータスペクトル](images/awg-x8-iq-send-iq-recv-bram-spectrum-q.png)

