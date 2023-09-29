# サンプルプログラムの動作環境

動作環境は次の通りです 
- Python 3.9.16
- Pipenv
- Pyenv

こちらでは、Windows 10 + WSL1 (Ubuntu 18.04.4) で動作確認をしました。
セットアップ方法は次の通りです。

1. `cd /D C:\` で C ドライブに移動します.
1. `git clone https://github.com/e-trees/rftool_client.git` で rftool_client リポジトリを C ドライブ直下にコピーします.
1. WSL を起動します (「」内のコマンドは、WSL のターミナルに入力するものとします)
1. 「`cd /mnt/c/rftool_client`」で `rftool_client` に移動します
1. https://github.com/pyenv/pyenv#installation を参考に pyenv をインストールします
1. 「`pyenv install 3.9.16`」 で Python 3.9.16 をインストールします
1. 「`pyenv global 3.9.16`」 で WSL のデフォルトの python のバージョンを変更します
1. 「`pip install --upgrade pip`」 で pip を最新バージョンにします
1. 「`pip install pipenv`」 で pipenv をインストールします
1. 「`pipenv sync`」 で仮想環境を作成します
1. 「`pipenv shell`」で仮想環境に入ります
1. 以降は各サンプルを実行してください
