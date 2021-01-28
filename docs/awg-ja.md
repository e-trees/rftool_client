# 出力波形設定手順

AWGから波形を出力するには，以下の3つの手順を実行します．

1. 波形の定義
1. 波形の出力順と出力タイミングの決定(= 波形シーケンスの定義)
1. 波形シーケンスのAWGへの登録

![波形出力設定手順概要](images/awg-setup-overview.png)

## 波形の定義 - 組み込み波形の利用

波形の定義には `awgsa` パッケージの `AwgWave`クラスを利用します．
このクラスのコンストラクタで，各波形のパラメタ(周波数，位相，出力サイクル数など)を設定し出力波形を定義します．

```API使用例

wave_0 = awgsa.AwgWave(
    wave_type = awgsa.AwgWave.SINE,
	frequency = 10.0,
	phase = 0,
	amplitude = 30000,
	num_cyles = 4)

```
