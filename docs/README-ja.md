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

## 機能別設定手順

- [出力波形設定手順](awg-ja.md) 
- [キャプチャ設定手順](capture-ja.md) 
- [ディジタル出力設定手順](digital-ja.md) 
- [波形シーケンス可視化機能](wave-sequence-vis-ja.md) 

## サンプルプログラム

- [ホスト PC と ZCU 111 の接続を確認する](../examples/setup_verify/README.md)
- [2 つの AWG から波形を出力しキャプチャする](../examples/awg_send_recv/README.md)
- [AWG から出力した波形を積算しながらキャプチャする (Non-MTS 版)](../examples/awg_accum_send_recv/README.md)
- [AWG から出力した波形を積算しながらキャプチャする (MTS 版)](../examples/mts_awg_accum_send_recv/README.md)
- [AWG から IQ ミキシングした波形を出力する](../examples/awg_iq_send_recv/README.md)
- [キャプチャモジュールで IQ ミキシングした波形をキャプチャする](../examples/awg_send_iq_recv/README.md)
- [8つのAWGから10サイクルの正弦波を出力しキャプチャする(Non-MTS 版)](../examples/awg_x8_send_recv/README.md)
- [8つのAWGから10サイクルの正弦波を出力しキャプチャする (MTS 版)](../examples/mts_awg_x8_send_recv/README.md)
- [8つのAWGからI/Q変調した波形を出力しADCでI/Qミキサをかけてキャプチャ(DRAM/BRAM利用)](../examples/awg_x8_iq_send_iq_recv/README.md)
- [任意のサンプル値を持つ波形を出力する](../examples/awg_any_wave_send_recv/README.md)
- [AWG から送信する波形データの可視化](../examples/awg_waveseq_visualize/README.md)
- [ディジタル出力の利用](../examples/awg_digital_output/README.md)
- [キャプチャを連続で行う](../examples/continuous_send_recv/README.md)
- [DRAM を使った波形データの送信](../examples/dram_send_2ch_250ms/README.md)
- [DAC の最大サンプリングレートでの波形データの送信](../examples/bram_send_max_sampling_rate/README.md)
- [BRAM を使った波形データの送受信](../examples/bram_send_recv/README.md)
- [BRAM を使った IQ データの受信](../examples/bram_iq_send_recv/README.md)
- [BRAM を使った波形データの積算 (振幅が変化する正弦波)](../examples/bram_accum_send_recv/README.md)
- [BRAM を使った波形データの積算 (正弦波)](../examples/bram_accum_send_recv_sine/README.md)
- [BRAM を使った波形データの積算 (単発パルス)](../examples/bram_accum_send_recv_pulse/README.md)
- [DRAM を使った波形データの送受信](../examples/dram_send_recv_2ch_250ms/README.md)
- [DRAM を使った IQ データの送受信](../examples/dram_iq_send_recv/README.md)
- [DRAM を使った波形データの積算](../examples/dram_accum_send_recv/README.md)
- [Feedback システムのテスト 1](../examples/feedback_test_1/README.md)
- [Feedback システムのテスト 2](../examples/feedback_test_2/README.md)

## LabRAD を使ったサンプルプログラム

- [【LabRAD】LabRAD サーバを起動する](../examples/rftool_labrad_server/README.md)
- [【LabRAD】ホスト PC と ZCU 111 の接続を確認する](../examples/setup_verify_labrad/README.md)
- [【LabRAD】BRAM を使った波形データの積算 (振幅が変化する正弦波)](../examples/bram_accum_send_recv_labrad/README.md)
- [【LabRAD】Feedback システムのテスト 1](../examples/feedback_test_1_labrad/README.md)
- [【LabRAD】Feedback システムのテスト 2](../examples/feedback_test_2_labrad/README.md)

### サンプルプログラムの実行に必要な環境

- ZCU111およびe-trees.Japan製ZCU111ファームウェア
- Python 3.7.5
- NumPy, matplotlib，など
