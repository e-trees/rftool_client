#!/usr/bin/env python3
# coding: utf-8

import os
import sys
import time
import logging
import numpy as np
import pathlib
import random
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

# Parameters
ZCU111_IP_ADDR = os.environ.get('ZCU111_IP_ADDR', "192.168.1.3")
# Log level
LOG_LEVEL = logging.INFO

# Constants
BITSTREAM = 10 # AWG SA BINARIZATION
PLOT_DIR = "plot_binarization_test/"
DAC_FREQ = 6000.0
ADC_FREQ = 1000.0
CAPTURE_DELAY = 400 #ns
TEST_AWG = awgsa.AwgId.AWG_4

BITSTREAM_LOAD_TIMEOUT = 10
TRIG_BUSY_TIMEOUT = 60
DUC_DDC_FACTOR = 1

# ADC or DAC
ADC = 0
DAC = 1


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
        details.append("RFDC FIFO merginal overflow detected.")
    if (flags & 0x00000008):
        details.append("RFDC FIFO merginal underflow detected.")
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


def wait_for_sequence_to_finish(awg_sa_cmd, *awg_id_list):
    """
    波形シーケンスの出力とキャプチャが終了するまで待つ
    """
    for i in range(TRIG_BUSY_TIMEOUT):
        all_finished = True
        for awg_id in awg_id_list:
            awg_stat = awg_sa_cmd.is_wave_sequence_complete(awg_id)
            if awg_stat != awgsa.AwgSaCmdResult.WAVE_SEQUENCE_COMPLETE:
                all_finished = False
                break

        if all_finished:
            return
        time.sleep(1.)
        
    raise("AWG busy timed out.")


def check_skipped_step(awg_sa_cmd, awg_id_to_wave_sequence):
    """
    スキップされたキャプチャステップが無いかチェックする.
    キャプチャディレイや先行するキャプチャのキャプチャ時間などにより,
    キャプチャが出来なかった場合, そのキャプチャはスキップされる.
    """
    for awg_id, wave_sequence in awg_id_to_wave_sequence.items():
        for step_id in wave_sequence.get_step_id_list():
            if awg_sa_cmd.is_capture_step_skipped(awg_id, step_id):
                print("The Step id {} in AWG {} has been skipped!!".format(step_id, awg_id))


def check_capture_data_fifo_oevrflow(awg_sa_cmd, awg_id_to_wave_sequence):
    """
    ADC から送られる波形データを格納する FIFO で, オーバーフローが発生していないかチェックする.
    PL 上の DRAM の帯域の制限などにより, ADC から送信されるデータの処理が間に合わない場合, 
    波形データを格納する FIFO のオーバーフローが発生する.
    """
    for awg_id, wave_sequence in awg_id_to_wave_sequence.items():
        for step_id in wave_sequence.get_step_id_list():
            if awg_sa_cmd.is_capture_data_fifo_overflowed(awg_id, step_id):
                print("The ADC data FIFO in AWG {} has overflowed at step id {}!!".format(awg_id, step_id))


def calibrate_adc(awg_sa_cmd):
    """
    ADC をキャリブレーションする
    """
    # AWG に波形シーケンスをセットする
    calib_wave = awgsa.AwgWave(
        wave_type = awgsa.AwgWave.SINE,
        frequency = 10.0,
        phase = 0,
        amplitude = 30000,
        num_cycles = 100000)
    calib_wave_sequence = (awgsa.WaveSequence(DAC_FREQ)
        .add_step(step_id = 0, wave = calib_wave, post_blank = 0))
    awg_sa_cmd.set_wave_sequence(TEST_AWG, calib_wave_sequence, num_repeats = 1)

    awg_sa_cmd.start_wave_sequence()
    wait_for_sequence_to_finish(awg_sa_cmd, TEST_AWG)


def set_wave_sequence(awg_sa_cmd, wave_pattern):
    """
    波形シーケンスを AWG にセットする
    """
    step_id = 0
    wave_sequence = awgsa.WaveSequence(DAC_FREQ)
    for type in wave_pattern:
        amplitude = 0 if type == 0 else 32760
        # 波形の定義
        wave = awgsa.AwgWave(
            wave_type = awgsa.AwgWave.SQUARE,
            frequency = 4,
            phase = 0.0,
            amplitude = amplitude,
            duty_cycle = 100,
            num_cycles = 1)
        # 波形シーケンスの定義
        wave_sequence.add_step(step_id, wave, post_blank = 500)
        step_id += 1
        
    # AWG に波形シーケンスをセットする
    awg_sa_cmd.set_wave_sequence(TEST_AWG, wave_sequence, num_repeats = 1)
    return wave_sequence


def set_capture_sequence(awg_sa_cmd, wave_sequence):
    """
    キャプチャシーケンスをキャプチャモジュールにセットする
    """
    capture_config = awgsa.CaptureConfig()
    # I/Q ミキサは無効にするが, キャプチャシーケンスの設定では, I/Q データをキャプチャする設定にしておく.
    # これにより, I データ用の 2 値化モジュールが Real データを処理するようになる.
    capture_sequence = awgsa.CaptureSequence(ADC_FREQ, is_iq_data = True)
    for step_id in wave_sequence.get_step_id_list():
        # delay が波形ステップの開始から終了までの時間を超えないように注意.
        # 2値化処理のオーバーヘッド 約 40ns を2値化処理の時間から引いておく
        capture_time = wave_sequence.get_wave(step_id).get_duration() - 40
        capture = awgsa.AwgCapture(
            time = capture_time,
            delay = CAPTURE_DELAY,
            do_accumulation = False)
        # キャプチャシーケンスへのキャプチャステップの追加
        capture_sequence.add_step(step_id, capture)
        # キャプチャシーケンスとキャプチャモジュールを対応付ける
        capture_config.add_capture_sequence(TEST_AWG, capture_sequence)

    # キャプチャモジュールにキャプチャシーケンスを設定する
    awg_sa_cmd.set_capture_config(capture_config)
    return capture_sequence


def main():

    with client.RftoolClient(logger=logger) as rft:
        print("Connect to RFTOOL Server.")
        rft.connect(ZCU111_IP_ADDR)
        rft.command.TermMode(0)

        print("Configure Bitstream.")
        config_bitstream(rft.command, BITSTREAM)
        
        print("\nPlease configure the binarization modules with VIO.")
        input()

        shutdown_all_tiles(rft.command)
        set_adc_sampling_rate(rft.command, ADC_FREQ)
        set_dac_sampling_rate(rft.command, DAC_FREQ)
        startup_all_tiles(rft.command)
        setup_dac(rft.command)
        setup_adc(rft.command)

        # 初期化
        rft.awg_sa_cmd.initialize_awg_sa()
        # AWG 有効化
        rft.awg_sa_cmd.enable_awg(TEST_AWG)
        # ADC キャリブレーション
        calibrate_adc(rft.awg_sa_cmd)

        MAX_SHIFT_REG_BITS = 256 # 2 値化結果を格納するシフトレジスタのビット数
        MAX_WAVE_STEPS = 64 # 波形シーケンスに登録可能な最大波形ステップ数
        num_repeats = MAX_SHIFT_REG_BITS // MAX_WAVE_STEPS
        expected_bin_result = [random.randint(0, 1) for _ in range(MAX_SHIFT_REG_BITS)] # 2値化結果の期待値

        for i in range(num_repeats):
            # AWG の波形シーケンス設定
            wave_pattern = expected_bin_result[i * MAX_WAVE_STEPS : (i + 1) * MAX_WAVE_STEPS]
            wave_sequence = set_wave_sequence(rft.awg_sa_cmd, wave_pattern)
            # キャプチャシーケンス設定        
            cap_sequence = set_capture_sequence(rft.awg_sa_cmd, wave_sequence)
            # 波形出力 & 2 値化スタート
            rft.awg_sa_cmd.start_wave_sequence()
            # 波形キャプチャ終了待ち
            wait_for_sequence_to_finish(rft.awg_sa_cmd, TEST_AWG)
            # エラーチェック
            check_skipped_step(rft.awg_sa_cmd, { TEST_AWG : wave_sequence })
            check_capture_data_fifo_oevrflow(rft.awg_sa_cmd, { TEST_AWG : wave_sequence })
            for ch in range(8):
                check_intr_flags(rft.command, ADC, ch)
            for ch in range(8):
                check_intr_flags(rft.command, DAC, ch)

            # 送信波形をグラフ化
            # rft.awg_sa_cmd.get_waveform_sequence(TEST_AWG).save_as_img(
            #     PLOT_DIR + "waveform/awg_{}_waveform_{}.png".format(TEST_AWG, i))
        
        (i_result, q_result) = rft.awg_sa_cmd.get_binarization_result(TEST_AWG)
        i_result.reverse() # 古い結果から順に格納されるように反転する
        if i_result != expected_bin_result:
            print('test failed')
            for i in range(len(expected_bin_result)):
                if i_result[i] != expected_bin_result[i]:
                    print("The result of idx {} doesn't match the expected value.".format(i))
                    print("result ", i_result[i])
                    print("expected ", expected_bin_result[i], '\n')
        else:
            print('\ntest succeeded\n')
            print('[RESULT]')
            print('old  ---------------------- new')
            for i in range(0, len(i_result), 16):
                for j in range(16):
                    print(i_result[i + j], end=',')
                print()
            

    print("Done.")
    return


if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    handler = logging.StreamHandler()
    handler.setLevel(LOG_LEVEL)
    logger.setLevel(LOG_LEVEL)
    logger.addHandler(handler)
    main()
