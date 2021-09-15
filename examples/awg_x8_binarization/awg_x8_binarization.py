#!/usr/bin/env python3
# coding: utf-8

"""
外部トリガサンプルプログラム
AWG 4 が出力した波形を外部トリガモジュール 4 が受け取り, AWG 0 ～ AWG 3, AWG 5 ～ AWG 7 にトリガをかける.
"""

import os
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

# Parameters
ZCU111_IP_ADDR = os.environ.get('ZCU111_IP_ADDR', "192.168.1.3")
# Log level
LOG_LEVEL = logging.INFO

# Constants
BITSTREAM = 10 # AWG SA BINARIZATION
PLOT_DIR = "plot_awg_x8_binarization/"
DAC_FREQ = 6554.0
ADC_FREQ = 2048.0
ADC_MIXER_FREQ = 0.5 #MHz
NUM_TO_DEVIDE = 4
CAPTURE_DELAY = 250 #ns

BITSTREAM_LOAD_TIMEOUT = 10
TRIG_BUSY_TIMEOUT = 60
DUC_DDC_FACTOR = 1

# ADC or DAC
ADC = 0
DAC = 1

awg_list = [awgsa.AwgId.AWG_0, awgsa.AwgId.AWG_4, awgsa.AwgId.AWG_5, awgsa.AwgId.AWG_6, awgsa.AwgId.AWG_7]

awg_to_freq = { awgsa.AwgId.AWG_0 : 2,  # トリガ波形の周波数
                awgsa.AwgId.AWG_4 : ADC_MIXER_FREQ * NUM_TO_DEVIDE, # 1ステップ当たりの長さを I/Q ミキサの周期の 1/4 とする
                awgsa.AwgId.AWG_5 : ADC_MIXER_FREQ * NUM_TO_DEVIDE,
                awgsa.AwgId.AWG_6 : ADC_MIXER_FREQ * NUM_TO_DEVIDE,
                awgsa.AwgId.AWG_7 : ADC_MIXER_FREQ * NUM_TO_DEVIDE,
            } #MHz

awg_to_trigger_mode = {
    awgsa.AwgId.AWG_0 : awgsa.TriggerMode.MANUAL,
    awgsa.AwgId.AWG_4 : awgsa.TriggerMode.EXTERNAL,
    awgsa.AwgId.AWG_5 : awgsa.TriggerMode.EXTERNAL,
    awgsa.AwgId.AWG_6 : awgsa.TriggerMode.EXTERNAL,
    awgsa.AwgId.AWG_7 : awgsa.TriggerMode.EXTERNAL
}

awg_to_duty_cycle = {
    awgsa.AwgId.AWG_0 : 50,
    awgsa.AwgId.AWG_4 : 100,
    awgsa.AwgId.AWG_5 : 100,
    awgsa.AwgId.AWG_6 : 100,
    awgsa.AwgId.AWG_7 : 100
}

def calculate_min_max(sample, chunks):
    sample_rs = np.reshape(sample, (-1, chunks))
    sample_min = np.amin(sample_rs, axis=1)
    sample_max = np.amax(sample_rs, axis=1)
    return sample_min, sample_max


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
            # タイル 2 と3 (キャプチャモジュール 4, 5, 6, 7) のみ I/Q ミキサを有効化する
            if (tile == 2) or (tile == 3):
                rftcmd.SetMixerSettings(ADC, tile, block, ADC_MIXER_FREQ, 0.0, 2, 2, 16, 3, 0)
            else:
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


def output_graphs(*id_and_data_list):

    color = 0
    for id_and_data in id_and_data_list:
        awg_id = id_and_data[0]
        step_id = id_and_data[1]
        samples = id_and_data[2]
        i_or_q = id_and_data[3]
        out_dir = PLOT_DIR + "AWG_{}/".format(awg_id)
        os.makedirs(out_dir, exist_ok = True)
        plot_graph(
            ADC_FREQ, 
            samples, 
            "C{}".format(color), 
            "AWG_{} step_{} captured {} waveform {} samples, {} Msps".format(awg_id, step_id, i_or_q, len(samples), ADC_FREQ),
            out_dir + "AWG_{}_step_{}_captured_{}.png".format(awg_id, step_id, i_or_q))
        color += 1


def calibrate_adc(awg_sa_cmd):
    """
    ADC をキャリブレーションする
    """
    # AWG に波形シーケンスをセットする
    for awg_id in awg_list:
        calib_wave = awgsa.AwgWave(
            wave_type = awgsa.AwgWave.SINE,
            frequency = awg_to_freq[awg_id],
            phase = 0,
            amplitude = 30000,
            num_cycles = int(awg_to_freq[awg_id] * 1e4)) #10ms
        calib_wave_sequence = (awgsa.WaveSequence(DAC_FREQ)
            .add_step(step_id = 0, wave = calib_wave, post_blank = 0))
        awg_sa_cmd.set_wave_sequence(awg_id, calib_wave_sequence, num_repeats = 1)

    awg_sa_cmd.start_wave_sequence()
    wait_for_sequence_to_finish(awg_sa_cmd, *awg_list)


def set_wave_sequence(awg_sa_cmd):
    """
    波形シーケンスを AWG にセットする
    """
    awg_id_to_wave_sequence = {}
    for awg_id, freq in awg_to_freq.items():
        duty_cycle = awg_to_duty_cycle[awg_id]
        wave_sequence = awgsa.WaveSequence(DAC_FREQ)
        # 波形の定義
        wave = awgsa.AwgWave(
            wave_type = awgsa.AwgWave.SQUARE,
            frequency = freq,
            phase = 0.0,
            amplitude = 30000,
            duty_cycle = duty_cycle,
            num_cycles = 1)
        # 波形シーケンスの定義
        wave_sequence.add_step(0, wave, post_blank = 0)
        
        # AWG に波形シーケンスをセットする
        awg_sa_cmd.set_wave_sequence(awg_id, wave_sequence, num_repeats = 20)
        awg_id_to_wave_sequence[awg_id] = wave_sequence

    return awg_id_to_wave_sequence


def set_capture_sequence(awg_sa_cmd, awg_id_to_wave_sequence):
    """
    キャプチャシーケンスをキャプチャモジュールにセットする
    """
    capture_module_to_capture_sequence = {}
    capture_config = awgsa.CaptureConfig()
    for awg_id, wave_sequence in awg_id_to_wave_sequence.items():
        # トリガ波形は2値化対象としない
        if awg_id == awgsa.AwgId.AWG_0:
            continue
        capture_sequence = awgsa.CaptureSequence(ADC_FREQ, is_iq_data = True) # ADC の出力を I/Q データとして取得
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
        capture_config.add_capture_sequence(awg_id, capture_sequence)
        capture_module_to_capture_sequence[awg_id] = capture_sequence
    # キャプチャモジュールにキャプチャシーケンスを設定する
    awg_sa_cmd.set_capture_config(capture_config)
    return capture_module_to_capture_sequence


def start_awg_and_capture(awg_sa_cmd):
    """
    波形の出力とキャプチャを開始する
    """
    print("start AWG 0")
    awg_sa_cmd.start_wave_sequence()


def set_external_trigger_condition(awg_sa_cmd, external_trig_id):
    """
    外部トリガのトリガ条件を設定する
    """
    LEVEL_LESS_THAN_EQ    = 0 # 閾値以下になったとき
    LEVEL_GREATER_THAN_EQ = 1 # 閾値以上になったとき
    EDGE_LESS_THAN_EQ     = 2 # 閾値を上から下に跨いだ時
    EDGE_GREATER_THAN_EQ  = 3 # 閾値を下から上に跨いだ時
    
    awg_sa_cmd.set_external_trigger_param(external_trig_id, 0, EDGE_GREATER_THAN_EQ)
    THRESHOLD = 5000 # トリガ条件の閾値
    awg_sa_cmd.set_external_trigger_param(external_trig_id, 1, THRESHOLD)


def setup_external_trigger(awg_sa_cmd):
    """
    外部トリガの発行に必要な設定を行う
    """
    for awg_id, trigger_mode in awg_to_trigger_mode.items():
        awg_sa_cmd.set_trigger_mode(awg_id, trigger_mode)
    # 外部トリガモジュール 0 にトリガ条件を設定
    set_external_trigger_condition(awg_sa_cmd, awgsa.ExternalTriggerId.EXT_TRIG_0)
    # 外部トリガモジュール 0 を単発トリガで起動
    awg_sa_cmd.external_trigger_on(awgsa.ExternalTriggerId.EXT_TRIG_0)


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
        rft.awg_sa_cmd.enable_awg(*awg_list)
        # ADC キャリブレーション
        calibrate_adc(rft.awg_sa_cmd)
        # AWG の波形シーケンス設定
        awg_id_to_wave_sequence = set_wave_sequence(rft.awg_sa_cmd)
        # キャプチャシーケンス設定        
        capture_module_to_capture_sequence = set_capture_sequence(rft.awg_sa_cmd, awg_id_to_wave_sequence)
        # トリガ設定
        setup_external_trigger(rft.awg_sa_cmd)
        # AWG 0 にマニュアルトリガを発行して, 波形の出力を開始する.
        start_awg_and_capture(rft.awg_sa_cmd)
        # 波形キャプチャ終了待ち
        wait_for_sequence_to_finish(rft.awg_sa_cmd, *awg_list)
        # エラーチェック
        check_skipped_step(rft.awg_sa_cmd, capture_module_to_capture_sequence)
        check_capture_data_fifo_oevrflow(rft.awg_sa_cmd, capture_module_to_capture_sequence)
        for ch in range(8):
            check_intr_flags(rft.command, ADC, ch)
        for ch in range(8):
            check_intr_flags(rft.command, DAC, ch)
        
        for awg_id, _ in capture_module_to_capture_sequence.items():
            print("\nBinarization {} Result".format(awg_id))
            (i_result, q_result) = rft.awg_sa_cmd.get_binarization_result(awg_id)
            for idx in range(len(i_result)):
                print('I[{:3d}] = {},   Q[{:3d}] = {}'.format(idx, i_result[idx], idx, q_result[idx]))
            print()

        # 送信波形をグラフ化
        for awg_id in awg_list:
            if awg_to_trigger_mode[awg_id] == awgsa.TriggerMode.MANUAL:
                continue
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
