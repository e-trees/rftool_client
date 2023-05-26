# 8つの STG から正弦波を出力する

[stim_gen_send.py](./stim_gen_send.py) は，8 つの STG (Stimulus Generator) からそれぞれ周波数の異なる正弦波を出力するスクリプトです.

## セットアップ

DAC, PMOD とオシロスコープを接続します．

![セットアップ](../../docs/stg/images/stg_x8_send_setup.png)

## 実行手順と結果

以下のコマンドを実行します．

```
python stim_gen_send.py
```

DAC と PMOD からの出力がオシロスコープで観察できます．


STG 0, STG 1, STG 4 の波形  (上から順に STG 0, STG 1, STG 4)

![STG 0, STG 1, STG 4 の波形](images/stg_0_1_4.jpg)

<br>

STG 5, STG 6, STG 7 の波形  (上から順に STG 5, STG 6, STG 7)

![STG 5, STG 6, STG 7 の波形](images/stg_5_6_7.jpg)

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
