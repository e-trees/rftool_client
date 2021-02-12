# Feedback システムのテスト 2

[feedback_test_2_labrad.py](./feedback_test_2_labrad.py) は，ADC がキャプチャした波形に応じて，DAC が出力する波形が変わるシステム (Feedback システム) のテストを行うスクリプトです．

## セットアップ

次のようにADCとDACを接続します．  

![セットアップ](../../docs/images/dac_adc_setup-3.png)

## 実行手順と結果

LabRAD サーバの起動後，以下のコマンドを実行します．実行後，`username` と `LabRAD password` の入力を求められますが，どち
らも何も入力せずに Enter を押します．
LabRAD サーバの起動方法は，[LabRAD サーバを起動する](../rftool_labrad_server/README.md) を参照してください．


```
python feedback_test_2_labrad.py
```
カレントディレクトリの下の `plot_feedback_test_2` ディレクトリの中に，以下のファイルが保存されます．
\* には，0 ～ 3 の数字が入ります．
adc_cap_dacsel_pattern_*.png の Expected と Actual の波形が一致していればテストは成功です．
- adc_cap_awg_pattern_*.png
- adc_cap_dacsel_pattern_*.png

adc_cap_awg_pattern_0.png  
![adc_cap_awg_pattern_0](images/adc_cap_awg_pattern_0.png)

adc_cap_awg_pattern_1.png  
![adc_cap_awg_pattern_1](images/adc_cap_awg_pattern_1.png)

adc_cap_awg_pattern_2.png  
![adc_cap_awg_pattern_2](images/adc_cap_awg_pattern_2.png)

adc_cap_awg_pattern_3.png  
![adc_cap_awg_pattern_3](images/adc_cap_awg_pattern_3.png)

adc_cap_dacsel_pattern_0.png  
![adc_cap_dacsel_pattern_0](images/adc_cap_dacsel_pattern_0.png)

adc_cap_dacsel_pattern_1.png  
![adc_cap_dacsel_pattern_1](images/adc_cap_dacsel_pattern_1.png)

adc_cap_dacsel_pattern_2.png  
![adc_cap_dacsel_pattern_2](images/adc_cap_dacsel_pattern_2.png)

adc_cap_dacsel_pattern3.png  
![adc_cap_dacsel_pattern_3](images/adc_cap_dacsel_pattern_3.png)
