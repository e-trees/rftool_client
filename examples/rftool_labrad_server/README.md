# LabRAD サーバを起動する

[rftool_labrad_server.py](./rftool_labrad_server.py) は，LabRAD サーバーを起動するスクリプトです．
LabRAD サーバは，LabRAD を使ったサンプルスクリプトの実行前に起動しておく必要があります．

## 実行手順

### OpenJDK 8 のインストール

以下のコマンドを実行して，OpenJDK 8 をインストールします．
既にインストール済みの場合，このステップは省略します．

```
sudo apt-get update
sudo apt-get install openjdk-8-jdk
```

### Scalabrad の起動
以下のコマンドを実行して，Scalabrad をダウンロードおよび展開します．
既に展開まで完了している場合は，このステップは省略します．

```
wget -O scalabrad-0.8.3.tar.gz https://bintray.com/labrad/generic/download_file?file_path=scalabrad-0.8.3.tar.gz
tar xvf scalabrad-0.8.3.tar.gz
```

新しいターミナルで以下のコマンドを実行して，Scalabrad を起動します．

```
./scalabrad-0.8.3/bin/labrad
```

### LabRAD サーバの起動
新しいターミナルで以下のコマンドを実行して，LabRAD サーバを起動します．

```
cd <path to rftool_client>
pipenv shell
python ./examples/rftool_labrad_server/rftool_labrad_server.py
```

起動完了までに 2 回 Enter を押す必要があります．

```
python ./examples/rftool_labrad_server/rftool_labrad_server.py
2021-02-12 12:26:49+0900 [-] Log opened.    <- ここで Enter を押す
12:26:50.026 [LabradManagerLogin-0-1] INFO  org.labrad.manager.LoginHandler - remote=/127.0.0.1:53480, local=/127.0.0.1:7682, isLocalConnection=true

Enter LabRAD password (localhost:7682): <- 何も入力せずに Enter を押す
2021-02-12 12:26:53+0900 [LabradProtocol,client] LABRAD Server wrapped RFTOOL Client starting...
中略
2021-02-12 12:26:54+0900 [LabradProtocol,client] LABRAD Server wrapped RFTOOL Client now serving <- 終了時は Ctrl-C
```
