#!/usr/bin/env python3
# coding: utf-8

"""
AWG サンプルプログラム:
"""

import os
import sys
import time
import logging
import numpy as np
import rftoolclient as rftc
import rftoolclient.awgsa as awgsa

try:
    import matplotlib
    matplotlib.use("Agg")
    matplotlib.rcParams["agg.path.chunksize"] = 20000
finally:
    import matplotlib.pyplot as plt

# Parameters
ZCU111_IP_ADDR = os.environ.get('ZCU111_IP_ADDR', "192.168.1.3")
PLOT_DIR = "plot_awg_digital_output/"

# Log level
LOG_LEVEL = logging.INFO

SHARED_CAPTURE_RAM = 0
PRIVATE_CAPTURE_RAM = 1
MTS = 2
fpga_design = SHARED_CAPTURE_RAM
try:
    if sys.argv[1] == "prv_cap_ram":
        fpga_design = PRIVATE_CAPTURE_RAM
    elif sys.argv[1] == "mts":
        fpga_design = MTS
except Exception:
    pass

# Constants
if fpga_design == SHARED_CAPTURE_RAM:
    BITSTREAM = rftc.FpgaDesign.AWG_SA  # AWG SA DRAM CAPTURE
    PLOT_DIR = "plot_awg_digital_output/"
    DAC_FREQ = 6554.0
    ADC_FREQ = 1105.92
    CAPTURE_DELAY = 335
elif fpga_design == PRIVATE_CAPTURE_RAM:
    BITSTREAM = rftc.FpgaDesign.AWG_SA_BRAM_CAPTURE  # AWG SA BRAM CAPTURE
    PLOT_DIR = "plot_awg_digital_output_prv_cap_ram/"
    DAC_FREQ = 6554.0
    ADC_FREQ = 4096.0
    CAPTURE_DELAY = 200
else:
    BITSTREAM = rftc.FpgaDesign.MTS_AWG_SA  # MTS AWG SA
    PLOT_DIR = "plot_mts_awg_digital_output/"
    DAC_FREQ = 3932.16
    ADC_FREQ = 3932.16
    CAPTURE_DELAY = 345

BITSTREAM_LOAD_TIMEOUT = 10
TRIG_BUSY_TIMEOUT = 60
DUC_DDC_FACTOR = 1
POST_BLANK = 2000


def plot_graph(freq, sample, color, title, filename):
    
    time = np.linspace(0, len(sample) / freq, len(sample), endpoint=False)
    plt.figure(figsize=(8, 6), dpi=300)
    plt.xlabel("Time [us]")
    plt.title(title)
    plt.plot(time, sample[0:len(sample)], linewidth=0.8, color=color)
    plt.savefig(filename)
    plt.close()
    return


def check_intr_flags(rftcmd, type, ch):
    if type == rftc.ADC:
        tile = int(ch / 2)
        block = ch % 2
    elif type == rftc.DAC:
        tile = int(ch / 4)
        block = ch % 4
    flags = rftcmd.GetIntrStatus(type, tile, block)[3]
    if flags == 0:
        return
    else:
        print("# WARNING: An interrupt flag was asserted in {} Ch.{} (Tile:{} Block:{}).".format(
            "ADC" if type == rftc.ADC else "DAC", ch, tile, block))
    details = []
    if (flags & 0x40000000):
        details.append("Datapath interrupt asserted.")
    if (flags & 0x000003F0):
        details.append("Overflow detected in {} stage datapath.".format(
            "ADC Decimation" if type == rftc.ADC else "DAC Interpolation"))
    if (flags & 0x00000400):
        details.append("Overflow detected in QMC Gain/Phase.")
    if (flags & 0x00000800):
        details.append("Overflow detected in QMC Offset.")
    if (flags & 0x00001000):
        details.append("Overflow detected in DAC Inverse Sinc Filter.")
    if (flags & 0x00FF0000):
        details.append("Sub RF-ADC Over/Under range detected.")
    if (flags & 0x08000000):
        details.append("RF-ADC over range detected.")
    if (flags & 0x04000000):
        details.append("RF-ADC over voltage detected.")
    if (flags & 0x00000001):
        details.append("RFDC FIFO overflow detected.")
    if (flags & 0x00000002):
        details.append("RFDC FIFO underflow detected.")
    if (flags & 0x00000004):
        details.append("RFDC FIFO marginal overflow detected.")
    if (flags & 0x00000008):
        details.append("RFDC FIFO marginal underflow detected.")
    for d in details:
        print(" - " + d)
    return


def setup_dac(rftcmd):
    print("Setup DAC.")
    for tile in [0, 1]:
        rftcmd.SetupFIFO(rftc.DAC, tile, 0)
        rftcmd.SetFabClkOutDiv(rftc.DAC, tile, 2 + int(np.log2(DUC_DDC_FACTOR)))
        for block in [0, 1, 2, 3]:
            rftcmd.SetMixerSettings(rftc.DAC, tile, block, 0.0, 0.0, 2, 1, 16, 4, 0)
            rftcmd.ResetNCOPhase(rftc.DAC, tile, block)
            rftcmd.UpdateEvent(rftc.DAC, tile, block, 1)
            rftcmd.SetInterpolationFactor(tile, block, DUC_DDC_FACTOR)
            rftcmd.IntrClr(rftc.DAC, tile, block, 0xFFFFFFFF)
        rftcmd.SetupFIFO(rftc.DAC, tile, 1)


def setup_adc(rftcmd):
    print("Setup ADC.")
    for tile in [0, 1, 2, 3]:
        rftcmd.SetupFIFO(rftc.ADC, tile, 0)
        rftcmd.SetFabClkOutDiv(rftc.ADC, tile, 2 + int(np.log2(DUC_DDC_FACTOR)))
        for block in [0, 1]:
            rftcmd.SetMixerSettings(rftc.ADC, tile, block, 0.0, 0.0, 2, 1, 16, 4, 0)
            rftcmd.ResetNCOPhase(rftc.ADC, tile, block)
            rftcmd.UpdateEvent(rftc.ADC, tile, block, 1)
            rftcmd.SetDither(tile, block, 1 if ADC_FREQ > 3000. else 0)
            rftcmd.SetDecimationFactor(tile, block, DUC_DDC_FACTOR)
            rftcmd.IntrClr(rftc.ADC, tile, block, 0xFFFFFFFF)
        rftcmd.SetupFIFO(rftc.ADC, tile, 1)


USE_INTERNAL_PLL = 1
PLL_A = 0x8
PLL_B = 0x4
PLL_C = 0x1

def set_adc_sampling_rate(rftcmd, adc_sampling_rate):
    """
    Set ADC sampling rates

    Parameters
    ----------
    type : RftoolCommand
        RftoolCommand object for sending rftool commands
    adc_sampling_rate : float
        ADC sampling rate (Msps)
    """
    
    # lmx2594 の設定パターン.  2 を指定すると lmx2594 の出力するクロックの周波数が 245.76 MHz になる.
    lmx2594_config = 2 
    # RF Data Converter に設定する ref clock の周波数 (MHz).
    ref_clock_freq = 245.76
    # ADC タイル0 と タイル1 の ref clock を出力する lmx2594 は PLL_A
    rftcmd.SetExtPllClkRate(0, PLL_A, lmx2594_config)
    # ADC タイル2 と タイル3 の ref clock を出力する lmx2594 は PLL_B
    rftcmd.SetExtPllClkRate(0, PLL_B, lmx2594_config)
    # サンプリングレート設定 (Msps)
    for tile in [0, 1, 2, 3]:
        rftcmd.DynamicPLLConfig(rftc.ADC, tile, USE_INTERNAL_PLL, ref_clock_freq, adc_sampling_rate)
    return


def set_dac_sampling_rate(rftcmd, dac_sampling_rate):
    """
    Set DAC sampling rates

    Parameters
    ----------
    type : RftoolCommand
        RftoolCommand object for sending rftool commands
    dac_sampling_rate : float
        DAC sampling rate (Msps)
    """

    # lmx2594 の設定パターン.  3 を指定すると lmx2594 の出力するクロックの周波数が 409.6 MHz になる.
    lmx2594_config = 3
    # RF Data Converter に設定する ref clock の周波数 (MHz).
    ref_clock_freq = 409.6
    # DAC タイル0 と タイル1 の ref clock を出力する lmx2594 は PLL_C
    rftcmd.SetExtPllClkRate(0, PLL_C, lmx2594_config)
    # サンプリングレート設定 (Msps)
    for tile in [0, 1]:
        rftcmd.DynamicPLLConfig(rftc.DAC, tile, USE_INTERNAL_PLL, ref_clock_freq, dac_sampling_rate)
    return


def shutdown_all_tiles(rftcmd):
    """
    DAC と ADC の全タイルをシャットダウンする
    """
    rftcmd.Shutdown(rftc.DAC, -1)
    rftcmd.Shutdown(rftc.ADC, -1)


def startup_all_tiles(rftcmd):
    """
    DAC と ADC の全タイルを起動する
    """
    rftcmd.StartUp(rftc.DAC, -1)
    rftcmd.StartUp(rftc.ADC, -1)


def wait_for_sequence_to_finish(awg_sa_cmd):
    """
    波形シーケンスの出力とキャプチャが終了するまで待つ
    """
    for i in range(TRIG_BUSY_TIMEOUT):
        awg_0_stat = awg_sa_cmd.is_wave_sequence_complete(awgsa.AwgId.AWG_0)
        awg_1_stat = awg_sa_cmd.is_wave_sequence_complete(awgsa.AwgId.AWG_1)
        if (awg_0_stat == awgsa.AwgSaCmdResult.WAVE_SEQUENCE_COMPLETE and
            awg_1_stat == awgsa.AwgSaCmdResult.WAVE_SEQUENCE_COMPLETE):
            return
        time.sleep(1.)
        
    raise("AWG busy timed out.")


def check_skipped_step(awg_sa_cmd):
    """
    スキップされたキャプチャステップが無いかチェックする.
    キャプチャディレイや先行するキャプチャのキャプチャ時間などにより,
    キャプチャが出来なかった場合, そのキャプチャはスキップされる.
    """
    if awg_sa_cmd.is_capture_step_skipped(awgsa.AwgId.AWG_0, step_id=0):
        print("The capture step id 0 in AWG 0 has been skipped!!")

    if awg_sa_cmd.is_capture_step_skipped(awgsa.AwgId.AWG_0, step_id=1):
        print("The capture step id 1 in AWG 0 has been skipped!!")

    if awg_sa_cmd.is_capture_step_skipped(awgsa.AwgId.AWG_1, step_id=0):
        print("The capture step id 0 in AWG 1 has been skipped!!")


def check_capture_data_fifo_oevrflow(awg_sa_cmd):
    """
    ADC から送られる波形データを格納する FIFO で, オーバーフローが発生していないかチェックする.
    PL 上の DRAM の帯域の制限などにより, ADC から送信されるデータの処理が間に合わない場合, 
    波形データを格納する FIFO のオーバーフローが発生する.
    """
    if awg_sa_cmd.is_capture_data_fifo_overflowed(awgsa.AwgId.AWG_0, step_id=0):
        print("The ADC data FIFO in AWG 0 has overflowed at step id 0!!")
    
    if awg_sa_cmd.is_capture_data_fifo_overflowed(awgsa.AwgId.AWG_0, step_id=1):
        print("The ADC data FIFO in AWG 0 has overflowed at step id 1!!")

    if awg_sa_cmd.is_capture_data_fifo_overflowed(awgsa.AwgId.AWG_1, step_id=0):
        print("The ADC data FIFO in AWG 1 has overflowed at step id 0!!")


def check_skipped_digital_output(awg_sa_cmd):
    """
    スキップされたデジタル出力ステップが無いかチェックする.
    """
    if awg_sa_cmd.is_digital_output_step_skipped(awgsa.AwgId.AWG_0, step_id=1):
        print("The digital output step id 1 in AWG 0 has been skipped!!")

    if awg_sa_cmd.is_digital_output_step_skipped(awgsa.AwgId.AWG_1, step_id=0):
        print("The digital output step id 0 in AWG 1 has been skipped!!")


def output_graphs(*id_and_data_list):

    os.makedirs(PLOT_DIR, exist_ok = True)
    color = 0
    for id_and_data in id_and_data_list:
        awg_id = id_and_data[0]
        step_id = id_and_data[1]
        samples = id_and_data[2]
        plot_graph(
            ADC_FREQ, 
            samples, 
            "C{}".format(color), 
            "AWG_{} step_{} captured waveform {} samples, {} Msps".format(awg_id, step_id, len(samples), ADC_FREQ),
            PLOT_DIR + "AWG_{}_step_{}_captured.png".format(awg_id, step_id))
        color += 1


def calibrate_adc(awg_sa_cmd):
    """
    ADC をキャリブレーションする
    """
    calib_wave = awgsa.AwgWave(
        wave_type = awgsa.AwgWave.SINE,
        frequency = 10.0,
        phase = 0,
        amplitude = 30000,
        num_cycles = 100000)

    calib_wave_sequence = (awgsa.WaveSequence(DAC_FREQ)
        .add_step(step_id = 0, wave = calib_wave, post_blank = 0))

    # AWG に波形シーケンスをセットする
    awg_sa_cmd.set_wave_sequence(awgsa.AwgId.AWG_0, calib_wave_sequence, num_repeats = 1)
    awg_sa_cmd.set_wave_sequence(awgsa.AwgId.AWG_1, calib_wave_sequence, num_repeats = 1)
    awg_sa_cmd.start_wave_sequence()
    wait_for_sequence_to_finish(awg_sa_cmd)


def set_wave_sequence(awg_sa_cmd):
    """
    波形シーケンスを AWG にセットする
    """
    # 波形の定義
    wave_0 = awgsa.AwgWave(
        wave_type = awgsa.AwgWave.GAUSSIAN,
        frequency = 1.0,
        phase = 0,
        amplitude = 30000,
        num_cycles = 2,
        variance = 0.2,
        domain_begin = -1.5,
        domain_end = 1.5)

    wave_1 = awgsa.AwgWave(
        wave_type = awgsa.AwgWave.SINE,
        frequency = 1.0,
        phase = 0,
        amplitude = 30000,
        num_cycles = 4)

    wave_2 = awgsa.AwgWave(
        wave_type = awgsa.AwgWave.SAWTOOTH,
        frequency = 1.0,
        phase = 0,
        amplitude = 30000,
        num_cycles = 8,
        crest_pos = 1.0)

    # 波形シーケンスの定義
    # 波形ステップの開始から終了までの期間は, キャプチャの終了処理にかかるオーバーヘッドを考慮し, 波形出力期間 + POST_BLANK を設定する.
    wave_sequence_0 = (awgsa.WaveSequence(DAC_FREQ)
        .add_step(step_id = 0, wave = wave_0, post_blank = POST_BLANK)
        .add_step(step_id = 1, wave = wave_1, post_blank = POST_BLANK))

    wave_sequence_1 = (awgsa.WaveSequence(DAC_FREQ)
        .add_step(step_id = 0, wave = wave_2, post_blank = POST_BLANK))

    # AWG に波形シーケンスをセットする
    awg_sa_cmd.set_wave_sequence(awgsa.AwgId.AWG_0, wave_sequence_0, num_repeats = 1)
    awg_sa_cmd.set_wave_sequence(awgsa.AwgId.AWG_1, wave_sequence_1, num_repeats = 1)
    return (wave_sequence_0, wave_sequence_1)


def set_capture_sequence(awg_sa_cmd, seq_0, seq_1):
    """
    キャプチャシーケンスを AWG にセットする
    """
    # キャプチャ時間は, キャプチャする波形の長さ + 20 ns とする.
    # delay が波形ステップの開始から終了までの時間を超えないように注意.
    capture_0 = awgsa.AwgCapture(
        time = seq_0.get_wave(step_id = 0).get_duration() + 20,
        delay = CAPTURE_DELAY,
        do_accumulation = False)

    capture_1 = awgsa.AwgCapture(
        time = seq_0.get_wave(step_id = 1).get_duration() + 20,
        delay = CAPTURE_DELAY,
        do_accumulation = False)

    # 波形シーケンス 1 全体をキャプチャするため, キャプチャ時間は,
    # シーケンス 1 全体の長さ - 余分にとった時間 (POST_BLANK) + 20 ns とする.
    capture_2 = awgsa.AwgCapture(
       time = seq_1.get_whole_duration() - POST_BLANK + 20,
       delay = CAPTURE_DELAY,
       do_accumulation = False)

    # キャプチャシーケンスの定義
    capture_sequence_0 = (awgsa.CaptureSequence(ADC_FREQ, is_iq_data = False)
        .add_step(step_id = 0, capture = capture_0)
        .add_step(step_id = 1, capture = capture_1))

    capture_sequence_1 = (awgsa.CaptureSequence(ADC_FREQ, is_iq_data = False)
        .add_step(step_id = 0, capture = capture_2))

    # キャプチャシーケンスとキャプチャモジュールを対応付ける
    capture_config = (awgsa.CaptureConfig()
        .add_capture_sequence(awgsa.AwgId.AWG_0, capture_sequence_0)
        .add_capture_sequence(awgsa.AwgId.AWG_1, capture_sequence_1))

    # キャプチャモジュールにキャプチャシーケンスを設定する
    awg_sa_cmd.set_capture_config(capture_config)


def set_digital_output_sequence(awg_sa_cmd):

    dout_0 = (awgsa.DigitalOutputVector()
        .append_data(0xA9, 1000)
        .append_data(0x76, 1500)
        .append_data(0xBF, 1500)
        .append_data(0x00, 1))

    dout_1 = (awgsa.DigitalOutputVector(delay=1000.0)
        .append_data(0x5E, 2000)
        .append_data(0x43, 1000)
        .append_data(0x21, 3000)
        .append_data(0xD6, 1000)
        .append_data(0x00, 1))

    dout_sequence_0 = (awgsa.DigitalOutputSequence()
        .add_step(step_id = 1, dout_vec = dout_0))

    dout_sequence_1 = (awgsa.DigitalOutputSequence()
        .add_step(step_id = 0, dout_vec = dout_1))

    # HW にデジタル出力シーケンスをセットする
    awg_sa_cmd.set_digital_output_sequence(awg_id = awgsa.AwgId.AWG_0, dout_sequence = dout_sequence_0)
    awg_sa_cmd.set_digital_output_sequence(awgsa.AwgId.AWG_1, dout_sequence_1)


def main():   

    with rftc.RftoolClient(logger) as client:
        print("Connect to RFTOOL Server.")
        client.connect(ZCU111_IP_ADDR)
        client.command.TermMode(0)

        print("Configure Bitstream.")
        client.command.ConfigFpga(BITSTREAM, BITSTREAM_LOAD_TIMEOUT)
        if fpga_design != MTS:
            shutdown_all_tiles(client.command)
            set_adc_sampling_rate(client.command, ADC_FREQ)
            set_dac_sampling_rate(client.command, DAC_FREQ)
            startup_all_tiles(client.command)

        setup_dac(client.command)
        setup_adc(client.command)
        if fpga_design == MTS:
            client.awg_sa_cmd.sync_dac_tiles()
            client.awg_sa_cmd.sync_adc_tiles()

        # 初期化    
        client.awg_sa_cmd.initialize_awg_sa()
        # AWG 有効化
        client.awg_sa_cmd.enable_awg(awgsa.AwgId.AWG_0, awgsa.AwgId.AWG_1)
        # ADC キャリブレーション
        calibrate_adc(client.awg_sa_cmd)
        # 波形シーケンス設定
        (wave_seq_0, wave_seq_1) = set_wave_sequence(client.awg_sa_cmd)
        # キャプチャシーケンス設定
        set_capture_sequence(client.awg_sa_cmd, wave_seq_0, wave_seq_1)
        # デジタル出力シーケンス設定
        set_digital_output_sequence(client.awg_sa_cmd)
        # 波形出力 & キャプチャスタート
        client.awg_sa_cmd.start_wave_sequence()
        # 終了待ち
        wait_for_sequence_to_finish(client.awg_sa_cmd)
        # エラーチェック
        check_skipped_step(client.awg_sa_cmd)
        check_capture_data_fifo_oevrflow(client.awg_sa_cmd)
        check_skipped_digital_output(client.awg_sa_cmd)
        for ch in range(8):
            check_intr_flags(client.command, rftc.ADC, ch)
        for ch in range(8):
            check_intr_flags(client.command, rftc.DAC, ch)
        
        # キャプチャデータ取得
        r_data_0 = client.awg_sa_cmd.read_capture_data(awgsa.AwgId.AWG_0, step_id = 0)
        r_data_1 = client.awg_sa_cmd.read_capture_data(awgsa.AwgId.AWG_0, step_id = 1)
        r_data_2 = client.awg_sa_cmd.read_capture_data(awgsa.AwgId.AWG_1, step_id = 0)
        r_sample_0 = rftc.NdarrayUtil.bytes_to_real_32(r_data_0)
        r_sample_1 = rftc.NdarrayUtil.bytes_to_real_32(r_data_1)
        r_sample_2 = rftc.NdarrayUtil.bytes_to_real_32(r_data_2)

        output_graphs(
            (awgsa.AwgId.AWG_0, 0, r_sample_0),
            (awgsa.AwgId.AWG_0, 1, r_sample_1),
            (awgsa.AwgId.AWG_1, 0, r_sample_2))

    print("Done.")
    return


if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    handler = logging.StreamHandler()
    handler.setLevel(LOG_LEVEL)
    logger.setLevel(LOG_LEVEL)
    logger.addHandler(handler)

    main()
