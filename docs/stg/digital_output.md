# ディジタル出力モジュールユーザマニュアル

本資料は，ZCU111 を利用したディジタル出力モジュールの利用者向けマニュアルです．

## 1. システム構成

ディジタル出力モジュールは ZCU111 の FPGA 上に実装されており，そのシステム構成は以下のようになります．
ディジタル出力モジュールの制御には専用の Python API を用います．
この API には Python で作成したディジタル出力値を FPGA に送信する機能や，ディジタル出力モジュールの動作完了を待つ機能などが含まれています．

ディジタル出力モジュールは本デザインに含まれる [Stimulus Generator](stimgen.md) (以下 STG) と連動して動作させることが可能です．

![システムオーバービュー](images/stg_system_overview.png)

## 2. STG デザインの種類

STG およびディジタル出力モジュールを搭載したデザインには，STG とディジタル出力モジュールの動作クロックが異なるバージョンと同じバージョンの 2 種類があります．本資料では前者を **独立クロックバージョン**、後者を **同一クロックバージョン** と呼びます．
独立クロックバージョンでは，上図の「ディジタル出力スタートトリガ」がクロックドメインをまたぐため，波形の出力開始とディジタル値の出力開始の間の時間がスタートトリガ入力のたびに変わる可能性があります．
一方，同一クロックバージョンではこの時間は常に一定です．

## 3. ディジタル出力モジュールの状態

ディジタル出力モジュールは下図の状態を持ち，次の 3 つのイベントで状態遷移します．
 - STG の波形出力が開始される
 - 全ディジタル出力値の出力が完了する
 - 特定の Python API (図中の青字) が呼ばれる

![ディジタル出力モジュールの状態](images/state.png)

**状態の説明**

| 状態名 | 説明 |
| --- | --- |
| Idle | 初期状態. |
| Prepare | 現在設定されているディジタル出力値リストの値を最初から出力するための準備を行います． |
| Active | ディジタル出力値リストから値を順に出力します．|
| Pause | ディジタル出力モジュールの動作を一時停止します．|

<br>

**状態と出力値の関係**

| 状態名 | 出力値 |
| --- | --- |
| Idle | Idle 状態専用の出力値. （詳細は 5.3 を参照）|
| Prepare | この状態に遷移する直前の出力値. |
| Active | ディジタル出力値リストの値. |
| Pause | この状態に遷移する直前の出力値. |


## 4. 出力ポート

ディジタル出力モジュール 0, 1 の出力値は ZCU111 の PMOD 0, 1 の電圧値として出力されます．
PMOD の各ポートには P0 ~ P7 の番号が以下の図のように割り当てられ，出力値の 0 ~ 7 ビット目の 0/1 が P0 ~ P7 の Lo/Hi に対応します．

![システムオーバービュー](images/pmod_ports.png)

## 5. ディジタル出力モジュール制御用 API の詳細

本章ではディジタル出力モジュールの操作に必要な Python API を手順ごとに説明します．

### 5.1. 初期化

ディジタル出力モジュールは，次節以降で述べる操作を行う前に必ず初期化しなければなりません．
初期化には DigitalOutCtrl クラスの initialize メソッドを使用します．

初期化のコード例を以下に示します．

```
from RftoolClient import client
import StimGen as sg
import common as cmn

# RftoolClient オブジェクトを作成する
with client.RftoolClient(logger) as rft:
    # ZCU111 に接続
    rft.connect(ZCU111_IP_ADDR)

    # FPGA コンフィギュレーション
    rft.command.ConfigFpga(cmn.FpgaDesign.STIM_GEN, 10)
    
    # RftoolClient オブジェクトから DigitalOutCtrl オブジェクトを取得
    dout_ctrl = rft.digital_out_ctrl

    # ディジタル出力モジュールの初期化
    dout_ctrl.initialize(sg.DigitalOut.U0, sg.DigitalOut.U1)
```

### 5.2. Active 状態の出力データの設定

Active 状態の出力データは，StimGen パッケージの DigitalOutputDataList クラスを用いて作成します．
同クラスの add メソッドに出力値と出力時間を設定します．
出力時間の単位は，独立クロックバージョンの場合 10 [ns] で，同一クロックバージョンの場合 26.0417 [ns] となります．
出力データをディジタル出力モジュールに設定するには DigitalOutCtrl クラスの set_output_data メソッドを使用します．

ディジタル出力データを設定するコード例を以下に示します．

```
# RftoolClient オブジェクトを作成する
with client.RftoolClient(logger) as rft:

    ### ディジタル出力モジュールの初期化 (省略) ###

    # ディジタル出力データの作成
    dout_data_list = sg.DigitalOutputDataList()
    (dout_data_list
        .add(0x01, 100)
        .add(0x02, 150)
        .add(0x04, 200))

    # 出力データをディジタル出力モジュールに設定
    dout_ctrl.set_output_data(dout_data_list, sg.DigitalOut.U0, sg.DigitalOut.U1)
```

このコードで定義される出力データは以下のようになります．

![ディジタル出力例](images/dout_result.png)

### 5.3. Idle 状態の出力データの設定

Idle 状態の出力データ (以下デフォルト出力値と呼ぶ) は，DigitalOutCtrl クラスの set_default_output_data メソッドで設定します．
このメソッドを呼び出すとすぐに，引数で指定したディジタル出力モジュールのデフォルト出力値が変わります．
STG デザインをコンフィギュレーションした直後のデフォルト出力値は 0 です．
一度変更したデフォルト出力値は，初期化などの操作では変わらず，再度このメソッドで変更するまで保持されます．

デフォルト出力値を設定するコード例を以下に示します．

```
from RftoolClient import client
import StimGen as sg
import common as cmn

# RftoolClient オブジェクトを作成する
with client.RftoolClient(logger) as rft:
    
    ### ディジタル出力モジュールの初期化 (省略) ###

    # ディジタル出力モジュール 0, 1 のデフォルト出力値を 0x36 に変更する
    dout_ctrl.set_default_output_data(0x36, sg.DigitalOut.U0, sg.DigitalOut.U1)
```

### 5.4. スタートトリガの有効化

ディジタル出力モジュールは，STG の波形出力開始に合わせて動作を開始する場合，スタートトリガを有効にしなければなりません．
スタートトリガの有効化には DigitalOutCtrl クラスの enable_start_trigger メソッドを使用します．

スタートトリガを有効化するコード例を以下に示します．

```
from RftoolClient import client
import StimGen as sg

# RftoolClient オブジェクトを作成する
with client.RftoolClient(logger) as rft:
    
    ### ディジタル出力モジュールの初期化 (省略) ###
    ### ディジタル出力データの設定 (省略) ###

    # スタートトリガの有効化
    # 以降 STG の波形出力開始に合わせてディジタル出力モジュール 0 と 1 が動作を開始する
    dout_ctrl.enable_start_trigger(sg.DigitalOut.U0, sg.DigitalOut.U1)
```

このスタートトリガは，何れかの STG の波形出力開始と同時にアサートされます．
StimGenCtrl クラスの start_stgs メソッドで複数の STG をスタートしてもスタートトリガは 1 度しかアサートされません．
STG に連動させずディジタル出力モジュールだけを動作させたい場合，**DigitalOutCtrl クラスの start_douts メソッド**を使用してください．このメソッドの引数に指定したディジタル出力モジュールは，スタートトリガの有効/無効に関係なく動作を開始します．

### 5.5. ディジタル値出力の一時停止

ディジタル出力モジュールは，Active 状態のときに DigitalOutCtrl クラスの pause_douts メソッドを呼ぶと一時停止します．
一時停止中は Active 状態のときに最後に出力していた値を出力し続けます．
また，一時停止中は 5.2, 5.3 の手順でデフォルト出力値やディジタル出力データを更新することが可能です．
一時停止中にディジタル出力データを更新した場合は，5.7, 5.8 の手順で **再スタート** をしてください．

ディジタル値出力を一時停止するコード例を以下に示します．

```
from RftoolClient import client
import StimGen as sg

# RftoolClient オブジェクトを作成する
with client.RftoolClient(logger) as rft:
    
    ### ディジタル出力モジュールの初期化 (省略) ###
    ### ディジタル出力データの設定 (省略) ###

    # ディジタル出力モジュール 0, 1 の動作開始
    dout_ctrl.start_douts(sg.DigitalOut.U0, sg.DigitalOut.U1)

    # ディジタル出力モジュール 0, 1 の一時停止
    dout_ctrl.pause_douts(sg.DigitalOut.U0, sg.DigitalOut.U1)
```

### 5.6. ディジタル値出力の再開

ディジタル出力モジュールは，Pause 状態のときに DigitalOutCtrl クラスの resume_douts メソッドを呼ぶと動作を再開します．

ディジタル値出力を再開するコード例を以下に示します．

```
from RftoolClient import client
import StimGen as sg

# RftoolClient オブジェクトを作成する
with client.RftoolClient(logger) as rft:
    
    ### ディジタル出力モジュールの初期化 (省略) ###
    ### ディジタル出力データの設定 (省略) ###
    ### ディジタル出力モジュールの動作開始 (省略) ###
    ### ディジタル出力モジュールの一時停止 (省略) ###

    # ディジタル出力モジュール 0, 1 の動作再開
    dout_ctrl.resume_douts(sg.DigitalOut.U0, sg.DigitalOut.U1)
```

### 5.7. 再スタート

ディジタル出力モジュールは，Pause 状態のときに DigitalOutCtrl クラスの restart_douts メソッドを呼ぶと，ディジタル値の出力を最初からやり直します (再スタート)．その際 Pause 状態でディジタル出力データを更新していると，更新したデータが出力されます．

ディジタル出力モジュールを再スタートするコード例を以下に示します．

```
from RftoolClient import client
import StimGen as sg

# RftoolClient オブジェクトを作成する
with client.RftoolClient(logger) as rft:
    
    ### ディジタル出力モジュールの初期化 (省略) ###
    ### ディジタル出力データの設定 (省略) ###
    ### ディジタル出力モジュールの動作開始 (省略) ###
    ### ディジタル出力モジュールの一時停止 (省略) ###

    # ディジタル出力データの作成
    dout_data_list = sg.DigitalOutputDataList()
    (dout_data_list
        .add(0x0A, 100)
        .add(0x06, 150))

    # 出力データをディジタル出力モジュールに設定
    dout_ctrl.set_output_data(dout_data_list, sg.DigitalOut.U0, sg.DigitalOut.U1)

    # ディジタル出力モジュール 0, 1 の再スタート
    dout_ctrl.restart_douts(sg.DigitalOut.U0, sg.DigitalOut.U1)
```

### 5.8. 再スタートトリガの有効化

ディジタル出力モジュールの再スタートは，Python API (DigitalOutCtrl.restart_douts) を使わずに STG の波形出力開始に合わせて行うことが可能です．
STG の波形出力開始に合わせて再スタートする場合，再スタートトリガを有効にしなければなりません． 再スタートトリガの有効化には DigitalOutCtrl クラスの enable_restart_trigger メソッドを使用します．

再スタートトリガを有効化するコード例を以下に示します．

```
from RftoolClient import client
import StimGen as sg

# RftoolClient オブジェクトを作成する
with client.RftoolClient(logger) as rft:
    
    ### ディジタル出力モジュールの初期化 (省略) ###
    ### ディジタル出力データの設定 (省略) ###
    ### ディジタル出力モジュールの動作開始 (省略) ###
    ### ディジタル出力モジュールの一時停止 (省略) ###

    # ディジタル出力データの作成
    dout_data_list = sg.DigitalOutputDataList()
    (dout_data_list
        .add(0x0A, 100)
        .add(0x06, 150))

    # 出力データをディジタル出力モジュールに設定
    dout_ctrl.set_output_data(dout_data_list, sg.DigitalOut.U0, sg.DigitalOut.U1)

    # 再スタートトリガの有効化
    # 以降 STG の波形出力開始に合わせてディジタル出力モジュール 0 と 1 が再スタートする
    dout_ctrl.enable_restart_trigger(sg.DigitalOut.U0, sg.DigitalOut.U1)
```
