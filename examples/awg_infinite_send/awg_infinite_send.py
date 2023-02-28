#!/usr/bin/env python3
# coding: utf-8

"""
AWG x8 サンプルプログラム
各 AWG から特定の周波数の正弦波を出力してキャプチャする.
"""

import os
import re
import sys
import time
import logging
import numpy as np
import pathlib
from scipy import fftpack
try:
    import matplotlib
    matplotlib.use("Agg")
    matplotlib.rcParams["agg.path.chunksize"] = 20000
finally:
    import matplotlib.pyplot as plt

lib_path = str(pathlib.Path(__file__).resolve().parents[2])
sys.path.append(lib_path)
from RftoolClient import client, rfterr, wavegen, ndarrayutil
import AwgSa as awgsa

# FPGA design
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

# Parameters
ZCU111_IP_ADDR = os.environ.get('ZCU111_IP_ADDR', "192.168.1.3")
# Log level
LOG_LEVEL = logging.INFO

# Constants
if fpga_design == SHARED_CAPTURE_RAM:
    BITSTREAM = 7  # AWG SA DRAM CAPTURE
    PLOT_DIR = "plot_awg_infinite_send/"
    DAC_FREQ = 6554.0
    ADC_FREQ = 1843.2
    CAPTURE_DELAY = 270
    POST_BLANK = 1000
elif fpga_design == PRIVATE_CAPTURE_RAM:
    BITSTREAM = 9  # AWG SA BRAM CAPTURE
    PLOT_DIR = "plot_awg_infinite_send_prv_cap_ram/"
    DAC_FREQ = 6554.0
    ADC_FREQ = 4096.0
    CAPTURE_DELAY = 200
    POST_BLANK = 100
else:
    BITSTREAM = 8  # MTS AWG SA
    PLOT_DIR = "plot_mts_awg_infinite_send/"
    DAC_FREQ = 3932.16
    ADC_FREQ = 3932.16
    CAPTURE_DELAY = 290
    POST_BLANK = 100

BITSTREAM_LOAD_TIMEOUT = 10
TRIG_BUSY_TIMEOUT = 60
DUC_DDC_FACTOR = 1
INFINITE = -1

# ADC or DAC
ADC = 0
DAC = 1

awg_list = [awgsa.AwgId.AWG_0, awgsa.AwgId.AWG_1]

def plot_graph(freq, sample, color, title, filename):
    
    time = np.linspace(0, len(sample) / freq, len(sample), endpoint=False)
    plt.figure(figsize=(8, 6), dpi=300)
    plt.xlabel("Time [us]")
    plt.title(title)
    plt.plot(time, sample[0:len(sample)], linewidth=0.8, color=color)
    plt.savefig(filename)
    plt.close()
    return

def config_bitstream(rftcmd, num_design):
    if rftcmd.GetBitstream() != num_design:
        rftcmd.SetBitstream(num_design)
        for i in range(BITSTREAM_LOAD_TIMEOUT):
            time.sleep(2.)
            if rftcmd.GetBitstreamStatus() == 1:
                break
            if i > BITSTREAM_LOAD_TIMEOUT:
                raise Exception(
                    "Failed to configure bitstream, please reboot ZCU111.")


def check_intr_flags(rftcmd, type, ch):
    if type == ADC:
        tile = int(ch / 2)
        block = ch % 2
    elif type == DAC:
        tile = int(ch / 4)
        block = ch % 4
    flags = rftcmd.GetIntrStatus(type, tile, block)[3]
    if flags == 0:
        return
    else:
        print("# WARNING: An interrupt flag was asserted in {} Ch.{} (Tile:{} Block:{}).".format(
            "ADC" if type == ADC else "DAC", ch, tile, block))
    details = []
    if (flags & 0x40000000):
        details.append("Datapath interrupt asserted.")
    if (flags & 0x000003F0):
        details.append("Overflow detected in {} stage datapath.".format(
            "ADC Decimation" if type == ADC else "DAC Interpolation"))
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
        for block in [0, 1, 2, 3]:
            rftcmd.SetMixerSettings(DAC, tile, block, 0.0, 0.0, 2, 1, 16, 4, 0)
            rftcmd.ResetNCOPhase(DAC, tile, block)
            rftcmd.UpdateEvent(DAC, tile, block, 1)
        rftcmd.SetupFIFO(DAC, tile, 0)
        for block in [0, 1, 2, 3]:
            rftcmd.SetInterpolationFactor(tile, block, DUC_DDC_FACTOR)
        rftcmd.SetFabClkOutDiv(DAC, tile, 2 + int(np.log2(DUC_DDC_FACTOR)))
        for block in [0, 1, 2, 3]:
            rftcmd.IntrClr(DAC, tile, block, 0xFFFFFFFF)
        rftcmd.SetupFIFO(DAC, tile, 1)


def setup_adc(rftcmd):
    print("Setup ADC.")
    for tile in [0, 1, 2, 3]:
        for block in [0, 1]:
            rftcmd.SetMixerSettings(ADC, tile, block, 0.0, 0.0, 2, 1, 16, 4, 0)
            rftcmd.ResetNCOPhase(ADC, tile, block)
            rftcmd.UpdateEvent(ADC, tile, block, 1)
        rftcmd.SetupFIFO(ADC, tile, 0)
        for block in [0, 1]:
            rftcmd.SetDither(tile, block, 1 if ADC_FREQ > 3000. else 0)
            rftcmd.SetDecimationFactor(tile, block, DUC_DDC_FACTOR)
        rftcmd.SetFabClkOutDiv(ADC, tile, 2 + int(np.log2(DUC_DDC_FACTOR)))
        for block in [0, 1]:
            rftcmd.IntrClr(ADC, tile, block, 0xFFFFFFFF)
        rftcmd.SetupFIFO(ADC, tile, 1)


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
        rftcmd.DynamicPLLConfig(ADC, tile, USE_INTERNAL_PLL, ref_clock_freq, adc_sampling_rate)
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
        rftcmd.DynamicPLLConfig(DAC, tile, USE_INTERNAL_PLL, ref_clock_freq, dac_sampling_rate)
    return


def shutdown_all_tiles(rftcmd):
    """
    DAC と ADC の全タイルをシャットダウンする
    """
    rftcmd.Shutdown(DAC, -1)
    rftcmd.Shutdown(ADC, -1)


def startup_all_tiles(rftcmd):
    """
    DAC と ADC の全タイルを起動する
    """
    rftcmd.StartUp(DAC, -1)
    rftcmd.StartUp(ADC, -1)


def stop_awgs(awg_sa_cmd):
    """
    ユーザが選択した AWG を停止する
    """
    while True:
        print("Select AWG to stop.")
        for awg_id in awg_list:
            print("    {} -> AWG {}".format(int(awg_id), int(awg_id)))
        print("    a -> all AWGs")

        selected = input()
        pattern = r'^[0-7a]$'
        result = re.match(pattern, selected)
        if result is None:
            print("'{}' is invaid awg id.\n".format(selected))
        elif selected == 'a':
            awg_sa_cmd.terminate_all_awgs()
            print("stopped all awgs\n")
        else:
            awg_sa_cmd.terminate_awgs(awgsa.AwgId.to_awg_id(selected))
            print("stopped awg {}\n".format(selected))
        
        if all_sequences_are_complete(awg_sa_cmd, *awg_list):
            return


def all_sequences_are_complete(awg_sa_cmd, *awg_id_list):
    """
    波形シーケンスの出力とキャプチャが終了するまで待つ
    """
    for awg_id in awg_id_list:
        awg_stat = awg_sa_cmd.is_wave_sequence_complete(awg_id)
        if awg_stat != awgsa.AwgSaCmdResult.WAVE_SEQUENCE_COMPLETE:
            return False

    return True


def check_skipped_step(awg_sa_cmd):
    """
    スキップされたキャプチャステップが無いかチェックする.
    キャプチャディレイや先行するキャプチャのキャプチャ時間などにより,
    キャプチャが出来なかった場合, そのキャプチャはスキップされる.
    """
    for awg_id in awg_list:
        for step_id in range(1):
            if awg_sa_cmd.is_capture_step_skipped(awg_id, step_id = step_id):
                print("The Step id {} in AWG {} has been skipped!!".format(step_id, awg_id))


def check_capture_data_fifo_oevrflow(awg_sa_cmd):
    """
    ADC から送られる波形データを格納する FIFO で, オーバーフローが発生していないかチェックする.
    PL 上の DRAM の帯域の制限などにより, ADC から送信されるデータの処理が間に合わない場合, 
    波形データを格納する FIFO のオーバーフローが発生する.
    """
    for awg_id in awg_list:
        for step_id in range(1):
            if awg_sa_cmd.is_capture_data_fifo_overflowed(awg_id, step_id):
                print("The ADC data FIFO in AWG {} has overflowed at step id {}!!".format(awg_id, step_id))
            if awg_sa_cmd.is_accumulated_value_overranged(awg_id, step_id):
                print("The ADC data is overranged at step id {} in AWG {}!!".format(step_id, awg_id))


def output_graphs(*id_and_data_list):

    color = 0
    for id_and_data in id_and_data_list:
        awg_id = id_and_data[0]
        step_id = id_and_data[1]
        samples = id_and_data[2]
        out_dir = PLOT_DIR + "AWG_{}/".format(awg_id)
        os.makedirs(out_dir, exist_ok = True)
        plot_graph(
            ADC_FREQ, 
            samples, 
            "C{}".format(color), 
            "AWG_{} step_{} captured waveform {} samples, {} Msps".format(awg_id, step_id, len(samples), ADC_FREQ),
            out_dir + "AWG_{}_step_{}_captured.png".format(awg_id, step_id))
        color += 1


def calibrate_adc(awg_sa_cmd):
    """
    ADC をキャリブレーションする
    """
    # AWG に波形シーケンスをセットする
    for awg_id in awg_list:
        calib_wave = awgsa.AwgWave(
            wave_type = awgsa.AwgWave.SINE,
            frequency = 10,
            phase = 0,
            amplitude = 30000,
            num_cycles = int(1e5)) #10ms
        calib_wave_sequence = (awgsa.WaveSequence(DAC_FREQ)
            .add_step(step_id = 0, wave = calib_wave, post_blank = 0))
        awg_sa_cmd.set_wave_sequence(awg_id, calib_wave_sequence, num_repeats = 1)

    awg_sa_cmd.start_wave_sequence()
    all_sequences_are_complete(awg_sa_cmd, *awg_list)


def set_wave_sequence(awg_sa_cmd):
    """
    波形シーケンスを AWG にセットする
    """
    # 波形の定義
    wave_0 = awgsa.AwgWave(
        wave_type = awgsa.AwgWave.SINE,
        frequency = 10,
        phase = 0,
        amplitude = 30000,
        num_cycles = INFINITE)

    wave_1 = awgsa.AwgWave(
        wave_type = awgsa.AwgWave.SQUARE,
        frequency = 10,
        phase = 0,
        amplitude = 30000,
        num_cycles = 3)

    wave_2 = awgsa.AwgWave(
        wave_type = awgsa.AwgWave.SAWTOOTH,
        frequency = 10,
        phase = 0,
        amplitude = 30000,
        num_cycles = 4)

    # 波形シーケンスの定義
    wave_sequence_0 = (awgsa.WaveSequence(DAC_FREQ)
        .add_step(step_id = 0, wave = wave_0, post_blank = 0))
    wave_sequence_1 = (awgsa.WaveSequence(DAC_FREQ)
        .add_step(step_id = 0, wave = wave_1, post_blank = 0)
        .add_step(step_id = 1, wave = wave_2, post_blank = POST_BLANK))
    # AWG に波形シーケンスをセットする
    awg_sa_cmd.set_wave_sequence(awg_id = awg_list[0], wave_sequence = wave_sequence_0, num_repeats = 1)
    awg_sa_cmd.set_wave_sequence(awg_id = awg_list[1], wave_sequence = wave_sequence_1, num_repeats = INFINITE)
    return { awg_list[0] : wave_sequence_0, 
             awg_list[1] : wave_sequence_1 }


def set_capture_sequence(awg_sa_cmd, awg_id_to_wave_sequence):
    """
    キャプチャシーケンスを AWG にセットする
    """
    capture_0 = awgsa.AwgCapture(
        time = 500,
        delay = CAPTURE_DELAY,
        do_accumulation = False)
    capture_1 = awgsa.AwgCapture(
        time = awg_id_to_wave_sequence[awg_list[1]].get_whole_duration() - POST_BLANK + 100,
        delay = CAPTURE_DELAY,
        do_accumulation = False)

    # キャプチャシーケンスの定義
    capture_sequence_0 = awgsa.CaptureSequence(ADC_FREQ).add_step(step_id = 0, capture = capture_0)
    capture_sequence_1 = awgsa.CaptureSequence(ADC_FREQ).add_step(step_id = 0, capture = capture_1)
    # キャプチャシーケンスとキャプチャモジュールを対応付ける
    capture_config = awgsa.CaptureConfig()
    capture_config.add_capture_sequence(awg_list[0], capture_sequence_0)
    capture_config.add_capture_sequence(awg_list[1], capture_sequence_1)
    # キャプチャモジュールにキャプチャシーケンスを設定する
    awg_sa_cmd.set_capture_config(capture_config)


def start_awg_and_capture(awg_sa_cmd):
    """
    波形の出力とキャプチャを開始する
    """
    # 全チャネル同時に波形出力とキャプチャを行う
    print("start all AWGs")
    awg_sa_cmd.start_wave_sequence()


def main():

    with client.RftoolClient(logger=logger) as rft:
        print("Connect to RFTOOL Server.")
        rft.connect(ZCU111_IP_ADDR)
        rft.command.TermMode(0)

        print("Configure Bitstream.")
        config_bitstream(rft.command, BITSTREAM)
        if fpga_design != MTS:
            shutdown_all_tiles(rft.command)
            set_adc_sampling_rate(rft.command, ADC_FREQ)
            set_dac_sampling_rate(rft.command, DAC_FREQ)
            startup_all_tiles(rft.command)

        setup_dac(rft.command)
        setup_adc(rft.command)
        # 初期化    
        rft.awg_sa_cmd.initialize_awg_sa()
        # AWG 有効化
        rft.awg_sa_cmd.enable_awg(*awg_list)        
        # Multi Tile Synchronization
        if fpga_design == MTS:
            rft.awg_sa_cmd.sync_dac_tiles()
            rft.awg_sa_cmd.sync_adc_tiles()
        # ADC キャリブレーション
        calibrate_adc(rft.awg_sa_cmd)
        # 波形シーケンス設定
        awg_id_to_wave_sequence = set_wave_sequence(rft.awg_sa_cmd)
        # キャプチャシーケンス設定
        set_capture_sequence(rft.awg_sa_cmd, awg_id_to_wave_sequence)        
        # 波形出力 & キャプチャスタート
        start_awg_and_capture(rft.awg_sa_cmd)
        # AWG 停止
        stop_awgs(rft.awg_sa_cmd)       
        # エラーチェック
        check_skipped_step(rft.awg_sa_cmd)
        check_capture_data_fifo_oevrflow(rft.awg_sa_cmd)
        for ch in range(8):
            check_intr_flags(rft.command, ADC, ch)
        for ch in range(8):
            check_intr_flags(rft.command, DAC, ch)
        
        # キャプチャデータ取得
        print("Get capture data.")
        nu = ndarrayutil.NdarrayUtil
        awg_id_to_wave_samples = {}
        for awg_id in awg_list:
            wave_data = rft.awg_sa_cmd.read_capture_data(awg_id, step_id = 0)
            awg_id_to_wave_samples[awg_id] = nu.bytes_to_real_32(wave_data)

        # キャプチャデータ出力
        print("Output capture data.")
        for awg_id, wave_samples in awg_id_to_wave_samples.items():
            output_graphs((awg_id, 0, wave_samples))

        # 送信波形をグラフ化
        for awg_id in awg_list:
           rft.awg_sa_cmd.get_waveform_sequence(awg_id).save_as_img(PLOT_DIR + "waveform/awg_{}_waveform.png".format(awg_id))

    print("Done.")
    return


if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    handler = logging.StreamHandler()
    handler.setLevel(LOG_LEVEL)
    logger.setLevel(LOG_LEVEL)
    logger.addHandler(handler)
    main()
