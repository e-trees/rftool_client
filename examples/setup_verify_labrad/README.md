# ホスト PC と ZCU 111 の接続を確認する

[setup_verify_labrad.py](./setup_verify_labrad.py) は，ホスト PC と ZCU 111 の接続を確認するスクリプトです．

## セットアップ

以下の図のようにホスト PC と ZCU 111 をイーサネットケーブルで接続し IP アドレスを設定します．
ZCU 111 の IP アドレスの初期設定は，192.168.1.3 となっています．  

![ホスト PC と ZCU 111 の接続](../../docs/images/setup_verify-1.png)

## 実行手順と結果

LabRAD サーバの起動後，以下のコマンドを実行します．実行後，`username` と `LabRAD password` の入力を求められますが，どち
らも何も入力せずに Enter を押します．
LabRAD サーバの起動方法は，[LabRAD サーバを起動する](../rftool_labrad_server/README.md) を参照してください．


```
python setup_verify_labrad.py
```

接続に成功した場合，ターミナルに以下のメッセージが表示されます．
```
connection test succeeded
```

接続に失敗した場合，ターミナルに以下のメッセージが表示されます．
```
exception: (0) [LABRAD Server wrapped RFTOOL Client] Remote Traceback (most recent call last):
中略
Connection test failed
```
