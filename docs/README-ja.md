# e-treesカスタマイズバージョンrftool-client向けPython API利用ガイド

ZCU111を利用して任意の波形出力とその応答波形のキャプチャを柔軟かつ簡便に行えることを目的としてしたファームウェアを
制御するPython API利用ガイドです．

ファームウェアの持つ，

- 複数の波形を任意のインターバルでDACから出力
- DAC出力に対する応答をADCからDRAMまたはBRAMにキャプチャ(保存)
- AWGの出力と連動したディジタル出力

の各機能の出力波形のパラメータやキャプチャのタイミングなどを設定することができます．

システム構成は以下の図の通りです．

![システムオーバービュー](images/zcu111_system_overview.png)

## 環境構築
- [サンプルプログラムの動作環境](operating_environment.md)
- [ZCU111 の設定](zcu111_setting.md)

## 機能別設定手順

- [出力波形設定手順](awg-ja.md) 
- [キャプチャ設定手順](capture-ja.md) 
- [ディジタル出力設定手順](digital-ja.md) 
- [波形シーケンス可視化機能](wave-sequence-vis-ja.md) 
- [外部トリガ機能](external-trigger-ja.md)

## ユーザによるデザインの拡張

- [DSP デザイン](dsp-design.md)

## サンプルプログラム

- [ホスト PC と ZCU 111 の接続を確認する](../examples/setup_verify/README.md)
- [2 つの AWG から波形を出力しキャプチャする](../examples/awg_send_recv/README.md)
- [AWG から出力した波形を積算しながらキャプチャする (Non-MTS 版)](../examples/awg_accum_send_recv/README.md)
- [AWG から出力した波形を積算しながらキャプチャする (MTS 版)](../examples/mts_awg_accum_send_recv/README.md)
- [AWG から IQ ミキシングした波形を出力する](../examples/awg_iq_send_recv/README.md)
- [キャプチャモジュールで IQ ミキシングした波形をキャプチャする](../examples/awg_send_iq_recv/README.md)
- [8つのAWGから10サイクルの正弦波を出力しキャプチャする(Non-MTS 版)](../examples/awg_x8_send_recv/README.md)
- [8つのAWGから10サイクルの正弦波を出力しキャプチャする (MTS 版)](../examples/mts_awg_x8_send_recv/README.md)
- [6つのAWGから15サイクルの正弦波を出力しキャプチャする (低サンプリングレート MTS)](../examples/mts_awg_x8_low_sampling_rate/README.md)
- [8つのAWGからI/Q変調した波形を出力しADCでI/Qミキサをかけてキャプチャ(DRAM/BRAM利用)](../examples/awg_x8_iq_send_iq_recv/README.md)
- [任意のサンプル値を持つ波形を出力する](../examples/awg_any_wave_send_recv/README.md)
- [AWG から送信する波形データの可視化](../examples/awg_waveseq_visualize/README.md)
- [ディジタル出力の利用](../examples/awg_digital_output/README.md)
- [キャプチャを連続で行う](../examples/awg_x8_continuous_send_recv/README.md)
- [ウィンドウ単位でキャプチャデータを積算する](../examples/awg_windowed_capture/README.md)
- [外部トリガで AWG を起動する](../examples/awg_x8_external_trigger/README.md)
- [外部トリガで AWG を連続して起動する](../examples/awg_continual_external_trigger/README.md)
- [AWG から波形を出力し続ける](../examples/awg_infinite_send/README.md)
- [DRAM からデータを読み出す](../examples/awg_dram_read/README.md)
- [波形ステップの空白期間を計測する](../examples/awg_measure_wave_gap/README.md)
- [信号処理を適用したデータをキャプチャする](../examples/awg_dsp_send_recv/README.md)
- [キャプチャデータに対し信号処理を適用する](../examples/awg_dsp_binarization/README.md)
- [他の波形ステップを参照する波形ステップを定義する](../examples/awg_ref_step/README.md)
- [2つの ZCU111 の DAC を同期させる](../examples/mts_external_clock/README.md)

## LabRAD を使ったサンプルプログラム

- [LabRAD サーバを起動する](../examples/rftool_labrad_server/README.md)
- [ホスト PC と ZCU 111 の接続を確認する](../examples/setup_verify_labrad/README.md)

### サンプルプログラムの実行に必要な環境

- ZCU111およびe-trees.Japan製ZCU111ファームウェア
- Python 3.9.16
- NumPy, matplotlib，など
