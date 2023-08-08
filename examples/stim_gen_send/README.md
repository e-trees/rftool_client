# 8つの STG から正弦波を出力する

[stim_gen_send.py](./stim_gen_send.py) は，8 つの STG (Stimulus Generator) から異なるパターンの波形を出力するスクリプトです．
本スクリプトでは，STG デザインの **独立クロックバージョン** と **同一クロックバージョン** の動作を確認できます．
2 つのバージョンの詳細は，[ディジタル出力モジュールユーザマニュアル](../../docs/stg/digital_output.md) を参照してください．

## セットアップ

DAC, PMOD とオシロスコープを接続します．

![セットアップ](../../docs/stg/images/stg_x8_send_setup.png)

## 独立クロックバージョンの実行手順と結果

以下のコマンドを実行します．

```
python stim_gen_send.py
```

DAC と PMOD からの出力がオシロスコープで観察できます．


STG 0, STG 1 の波形  (上 STG 0, 下 STG 1)

![STG 0, STG 1 の波形](images/stg_0_1_whole.jpg)

<br>

STG 0, STG 1 の波形の先頭部分 (上 STG 0, 下 STG 1)

![STG 0, STG 1 の波形](images/stg_0_1_part.jpg)

<br>

STG 4, STG 5 の波形  (上 STG 4, 下 STG 5)

![STG 4, STG 4 の波形](images/stg_4_5_whole.jpg)

<br>

STG 4, STG 5 の波形の先頭部分 (上 STG 4, 下 STG 5)

![STG 4, STG 5 の波形](images/stg_4_5_part.jpg)

<br>

STG 6, STG 7 の波形  (上 STG 6, 下 STG 7)

![STG 6, STG 7 の波形](images/stg_6_7_whole.jpg)

<br>

STG 6, STG 7 の波形の先頭部分 (上 STG 6, 下 STG 7)

![STG 6, STG 7 の波形](images/stg_6_7_part.jpg)

<br>

STG 0, PMOD 0 (P0, P1) の波形   (上から順に STG 0, PMOD 0 P0, P1)

![STG 0, PMOD 0 (P0, P1) の波形](images/stg_0_pmod_0_p0_p1.jpg)

<br>

STG 0, PMOD 0 (P2, P3) の波形   (上から順に STG 0, PMOD 0 P2, P3)

![STG 0, PMOD 0 (P2, P3) の波形](images/stg_0_pmod_0_p2_p3.jpg)

<br>

STG 0, PMOD 0 (P4, P5) の波形   (上から順に STG 0, PMOD 0 P4, P5)

![STG 0, PMOD 0 (P4, P5) の波形](images/stg_0_pmod_0_p4_p5.jpg)

<br>

STG 0, PMOD 0 (P6, P7) の波形   (上から順に STG 0, PMOD 0 P6, P7)

![STG 0, PMOD 0 (P6, P7) の波形](images/stg_0_pmod_0_p6_p7.jpg)

<br>

## 同一クロックバージョンの実行手順と結果

以下のコマンドを実行します．

```
python stim_gen_send.py sync_all
```

DAC と PMOD からの出力がオシロスコープで観察できます．
STG 0 ~ 7 の波形は独立クロックバージョンと同じです．


<br>

STG 0, PMOD 0 (P0, P1) の波形   (上から順に STG 0, PMOD 0 P0, P1)

![STG 0, PMOD 0 (P0, P1) の波形](images/stg_0_pmod_0_p0_p1_sync.jpg)

<br>

STG 0, PMOD 0 (P2, P3) の波形   (上から順に STG 0, PMOD 0 P2, P3)

![STG 0, PMOD 0 (P2, P3) の波形](images/stg_0_pmod_0_p2_p3_sync.jpg)

<br>

STG 0, PMOD 0 (P4, P5) の波形   (上から順に STG 0, PMOD 0 P4, P5)

![STG 0, PMOD 0 (P4, P5) の波形](images/stg_0_pmod_0_p4_p5_sync.jpg)

<br>

STG 0, PMOD 0 (P6, P7) の波形   (上から順に STG 0, PMOD 0 P6, P7)

![STG 0, PMOD 0 (P6, P7) の波形](images/stg_0_pmod_0_p6_p7_sync.jpg)
