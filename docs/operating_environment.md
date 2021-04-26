# サンプルプログラムの動作環境

動作環境は次の通りです 
- Python 3.7.5
- Pipenv
- Pyenv

こちらでは、Windows 10 + WSL1 (Ubuntu 18.04.4) で動作確認をしました。
セットアップ方法は次の通りです。

1. サンプルプログラム一式の圧縮ファイル (rftool_client_yyyymmdd.tar.gz) を Cドライブ直下に展開します
1. WSL を起動します (「」内のコマンドは、WSL のターミナルに入力するものとします)
1. 「cd /mnt/c/rftool_client_yyyymmdd」で rftool_client_yyyymmdd に移動します
1. 「pyenv install 3.7.5」 で Python 3.7.5 をインストールします
1. 「pipenv install --python=/home/<WSLのユーザー名>/.pyenv/versions/3.7.5/bin/python」 で仮想環境を作成します
1. 「pipenv shell」で仮想環境に入ります
1. 以降は各サンプルを実行してください

