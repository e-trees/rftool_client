# DRAM を使った波形データの送信

[dram_send_2ch_250ms_labrad.py](./dram_send_2ch_250ms_labrad.py) は，2 つの DAC チャネルから振幅が変化する 20[MHz] の正弦波信号を約 1 秒間隔で繰り返し出力するスクリプトです．出力する波形のデータは，DRAM に格納されます．

## セットアップ

次のように DAC とオシロスコープを接続します．  

![セットアップ](./../../docs/images/dac-oscilloscope-connection.png)

## 実行手順と結果

LabRAD サーバの起動後，以下のコマンドを実行します．実行後，`username` と `LabRAD password` の入力を求められますが，どち
らも何も入力せずに Enter を押します．
LabRAD サーバの起動方法は，[LabRAD サーバを起動する](../rftool_labrad_server/README.md) を参照してください．

```
python dram_send_2ch_250ms_labrad.py
```

カレントディレクトリの下の `plot_dram_send_2ch_250ms` ディレクトリの中に，送信波形のグラフおよびスペクトルが以下のファイル名で保存されます．
- dram_send_0.png (DAC チャネル 6 の送信波形全体)
- dram_send_0_crop.png (DAC チャネル 6 の送信波形の先頭 512 サンプル)
- dram_send_0_fft.png (DAC チャネル 6 の送信波形の周波数スペクトル)
- dram_send_1.png (DAC チャネル 7 の送信波形全体)
- dram_send_1_crop.png (DAC チャネル 7 の送信波形の先頭 512 サンプル)
- dram_send_1_fft.png (DAC チャネル 7 の送信波形の周波数スペクトル)

DAC チャネル 6 の送信波形全体  
![送信波形全体](images/dram_send_0.png)

DAC チャネル 6 の送信波形の先頭 512 サンプル  
![送信波形の先頭 512 サンプル](images/dram_send_0_crop.png)

DAC チャネル 6 の送信波形の周波数スペクトル  
![送信波形の周波数スペクトル](images/dram_send_0_fft.png)

オシロスコープで観測される波形を以下に示します．
黄色のグラフが DAC チャネル 6 に対応しており，水色のグラフが DAC チャネル 7 に対応しています．
上の送信波形と比べ，変位が反転していますが，これは ZCU111 付属のバラン内部の回路の構成によるものです．

オシロスコープ観測波形 (全体)  
![オシロスコープ観測波形 (全体)](images/dram_send_2ch_250ms-1.jpg)

オシロスコープ観測波形 (先頭)  
![オシロスコープ観測波形 (先頭)](images/dram_send_2ch_250ms-2.jpg)
