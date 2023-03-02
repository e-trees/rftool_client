#!/usr/bin/env python3
# coding: utf-8

"""
キャプチャモジュールの後処理に必要な時間を計測するプログラム.
2 or 3 つの AWG から波形を出力し, 対応するキャプチャモジュールで同時にキャプチャを行う.
キャプチャの後処理は順番に行い, 後処理を行っていない残り 2 つのモジュールはキャプチャ処理を続ける.
これにより, DDR4 への書き込みパスがビジーであるときにどのくらい後処理が遅れるかを測定する.
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
PLOT_DIR = "plot_awg_measure_capture_end_proc/"

# Log level
LOG_LEVEL = logging.INFO

# Constants
BITSTREAM = 7  # AWG SA DRAM CAPTURE
BITSTREAM_LOAD_TIMEOUT = 10
DAC_FREQ = 6554.0
TRIG_BUSY_TIMEOUT = 480
DUC_DDC_FACTOR = 1
POST_BLANK = 850 #ns

# ADC or DAC
ADC = 0
DAC = 1

awg_list = None
tile_to_sampling_rate = None  # Msps
awg_to_freq = None
awg_to_num_cycles = None
do_accumulation = None


def set_awg_capture_params(param_sel):
    
    global awg_list
    global tile_to_sampling_rate
    global awg_to_freq
    global awg_to_num_cycles
    global do_accumulation
    global POST_BLANK

    if param_sel == 0:
        POST_BLANK = 0
        awg_list = [awgsa.AwgId.AWG_0, awgsa.AwgId.AWG_2]
        do_accumulation = False
        tile_to_sampling_rate = {
            0 : 1228.8,  # awg 0, awg 1
            1 : 2211.84, # awg 2, awg 3
            2 : 1228.8,  # awg 4, awg 5
            3 : 1228.8   # awg 6, awg 7
        }
    elif param_sel == 1:
        POST_BLANK = 0
        awg_list = [awgsa.AwgId.AWG_1, awgsa.AwgId.AWG_4]
        do_accumulation = False
        tile_to_sampling_rate = {
            0 : 1228.8,  # awg 0, awg 1
            1 : 1228.8,  # awg 2, awg 3
            2 : 2211.84, # awg 4, awg 5
            3 : 1228.8   # awg 6, awg 7
        }
    elif param_sel == 2:
        POST_BLANK = 0
        awg_list = [awgsa.AwgId.AWG_0, awgsa.AwgId.AWG_1, awgsa.AwgId.AWG_2]
        do_accumulation = False
        tile_to_sampling_rate = {
            0 : 1044.48, # awg 0, awg 1
            1 : 1228.8,  # awg 2, awg 3
            2 : 1044.48, # awg 4, awg 5
            3 : 1044.48  # awg 6, awg 7
        }
    elif param_sel == 3:
        POST_BLANK = 0
        awg_list = [awgsa.AwgId.AWG_3, awgsa.AwgId.AWG_4, awgsa.AwgId.AWG_7]
        do_accumulation = False
        tile_to_sampling_rate = {
            0 : 1044.48, # awg 0, awg 1
            1 : 1044.48, # awg 2, awg 3
            2 : 1044.48, # awg 4, awg 5
            3 : 1228.8   # awg 6, awg 7
        }
    elif param_sel == 4:
        POST_BLANK = 0
        awg_list = [awgsa.AwgId.AWG_2, awgsa.AwgId.AWG_4]
        do_accumulation = False
        tile_to_sampling_rate = {
            0 : 1597.44, # awg 0, awg 1
            1 : 1597.44, # awg 2, awg 3
            2 : 1597.44, # awg 4, awg 5
            3 : 1597.44  # awg 6, awg 7
        }
    elif param_sel == 5:
        POST_BLANK = 0
        awg_list = [awgsa.AwgId.AWG_2]
        do_accumulation = False
        tile_to_sampling_rate = {
            0 : 1228.8,  # awg 0, awg 1
            1 : 3563.52, # awg 2, awg 3   3686.4 はダメ 2021/04/09
            2 : 1228.8,  # awg 4, awg 5
            3 : 1228.8   # awg 6, awg 7
        }
    elif param_sel == 6:
        POST_BLANK = 0
        awg_list = [awgsa.AwgId.AWG_2, awgsa.AwgId.AWG_4]
        do_accumulation = False
        tile_to_sampling_rate = {
            0 : 2457.6,  # awg 0, awg 1
            1 : 1044.48, # awg 2, awg 3
            2 : 1044.48, # awg 4, awg 5
            3 : 1044.48  # awg 6, awg 7
        }
    elif param_sel == 7:
        POST_BLANK = 0
        awg_list = [awgsa.AwgId.AWG_2, awgsa.AwgId.AWG_4, awgsa.AwgId.AWG_6]
        do_accumulation = False
        tile_to_sampling_rate = {
            0 : 1105.92,  # awg 0, awg 1
            1 : 1105.92, # awg 2, awg 3
            2 : 1105.92, # awg 4, awg 5
            3 : 1105.92  # awg 6, awg 7
        }
    elif param_sel == 8:
        POST_BLANK = 0
        awg_list = [awgsa.AwgId.AWG_2]
        do_accumulation = True
        tile_to_sampling_rate = {
            0 : 1000.00, # awg 0, awg 1
            1 : 2088.96, # awg 2, awg 3
            2 : 1000.00, # awg 4, awg 5
            3 : 1000.00  # awg 6, awg 7
        }

    base_cycle = 256000
    freq = 6.4 #MHz
    awg_to_freq = {}
    awg_to_num_cycles = {}
    for i in range(len(awg_list)):
        awg_id = awg_list[i]
        awg_to_freq[awg_id] = freq
        awg_to_num_cycles[awg_id] = (base_cycle * (i + 1), base_cycle * (3 - i))
    

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
            rftcmd.SetDither(tile, block, 1 if tile_to_sampling_rate[tile] > 3000. else 0)
            rftcmd.SetDecimationFactor(tile, block, DUC_DDC_FACTOR)
        rftcmd.SetFabClkOutDiv(ADC, tile, 2 + int(np.log2(DUC_DDC_FACTOR)))
        for block in [0, 1]:
            rftcmd.IntrClr(ADC, tile, block, 0xFFFFFFFF)
        rftcmd.SetupFIFO(ADC, tile, 1)


USE_INTERNAL_PLL = 1
PLL_A = 0x8
PLL_B = 0x4
PLL_C = 0x1

def set_adc_sampling_rate(rftcmd):
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
        rftcmd.DynamicPLLConfig(ADC, tile, USE_INTERNAL_PLL, ref_clock_freq, tile_to_sampling_rate[tile])
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


def wait_for_sequence_to_finish(awg_sa_cmd, awg_id):
    """
    波形シーケンスの出力とキャプチャが終了するまで待つ
    """
    for i in range(TRIG_BUSY_TIMEOUT):
        awg_stat = awg_sa_cmd.is_wave_sequence_complete(awg_id)
        if (awg_stat == awgsa.AwgSaCmdResult.WAVE_SEQUENCE_COMPLETE):
            return
        time.sleep(1.)
        
    raise("AWG {} busy timed out.".format(awg_id))


def check_skipped_step(awg_sa_cmd):
    """
    スキップされたキャプチャステップが無いかチェックする.
    キャプチャディレイや先行するキャプチャのキャプチャ時間などにより,
    キャプチャが出来なかった場合, そのキャプチャはスキップされる.
    """
    for awg_id in awg_list:
        if awg_sa_cmd.is_capture_step_skipped(awg_id, step_id = 0):
            print("The Step id 0 in AWG {} has been skipped!!".format(awg_id))            
        if awg_sa_cmd.is_capture_step_skipped(awg_id, step_id = 1):
            print("The Step id 1 in AWG {} has been skipped!!".format(awg_id))


def check_capture_data_fifo_oevrflow(awg_sa_cmd):
    """
    ADC から送られる波形データを格納する FIFO で, オーバーフローが発生していないかチェックする.
    PL 上の DRAM の帯域の制限などにより, ADC から送信されるデータの処理が間に合わない場合, 
    波形データを格納する FIFO のオーバーフローが発生する.
    """
    for awg_id in awg_list:
        if awg_sa_cmd.is_capture_data_fifo_overflowed(awg_id, step_id = 0):
            print("The ADC data FIFO in AWG {} has overflowed at step id 0!!".format(awg_id))
        if awg_sa_cmd.is_capture_data_fifo_overflowed(awg_id, step_id = 1):
            print("The ADC data FIFO in AWG {} has overflowed at step id 1!!".format(awg_id))


def output_graphs(awg_sa_cmd, *id_and_data_list):

    os.makedirs(PLOT_DIR, exist_ok = True)
    color = 0
    for id_and_data in id_and_data_list:
        awg_id = id_and_data[0]
        step_id = id_and_data[1]
        samples = id_and_data[2]
        tile = awg_sa_cmd.get_adc_tile_id_by_awg_id(awg_id)
        sampling_rate = tile_to_sampling_rate[tile]
        plot_graph(
            sampling_rate,
            samples, 
            "C{}".format(color), 
            "AWG_{} step_{} captured waveform {} samples, {} Msps".format(awg_id, step_id, len(samples), sampling_rate),
            PLOT_DIR + "AWG_{}_step_{}_captured.png".format(awg_id, step_id))
        color += 1


def calibrate_adc(awg_sa_cmd):
    """
    ADC をキャリブレーションする
    """
    calib_wave = awgsa.AwgWave(
        wave_type = awgsa.AwgWave.SINE,
        frequency = 300.0,
        phase = 0,
        amplitude = 30000,
        num_cycles = 3000000)

    calib_wave_sequence = (awgsa.WaveSequence(DAC_FREQ)
        .add_step(step_id = 0, wave = calib_wave, post_blank = 0))

    # AWG に波形シーケンスをセットする
    for awg_id in awg_list:
        awg_sa_cmd.set_wave_sequence(awg_id, calib_wave_sequence, num_repeats = 1)

    awg_sa_cmd.start_wave_sequence()
    for awg_id in awg_list:
        wait_for_sequence_to_finish(awg_sa_cmd, awg_id)


def set_wave_sequence(awg_sa_cmd):
    """
    波形シーケンスを AWG にセットする
    """
    awg_to_wave_sequence = {}
    for awg_id in awg_list:
        # 波形の定義
        freq = awg_to_freq[awg_id]
        num_cycles_0 = awg_to_num_cycles[awg_id][0]
        num_cycles_1 = awg_to_num_cycles[awg_id][1]
        wave_0 = awgsa.AwgWave(wave_type = awgsa.AwgWave.SINE, frequency = freq, num_cycles = num_cycles_0)
        wave_1 = awgsa.AwgWave(wave_type = awgsa.AwgWave.SINE, frequency = freq, num_cycles = num_cycles_1)
        # 波形シーケンスの定義
        # post_blank は, キャプチャの終了処理にかかるオーバーヘッドを考慮して設定する.
        wave_sequence = (awgsa.WaveSequence(DAC_FREQ)
            .add_step(step_id = 0, wave = wave_0, post_blank = POST_BLANK)
            .add_step(step_id = 1, wave = wave_1, post_blank = POST_BLANK))
        # AWG に波形シーケンスをセットする
        awg_sa_cmd.set_wave_sequence(awg_id = awg_id, wave_sequence = wave_sequence, num_repeats = 10)
        awg_to_wave_sequence[awg_id] = wave_sequence
    return awg_to_wave_sequence


def set_capture_sequence(awg_sa_cmd, awg_to_wave_sequence):
    """
    キャプチャシーケンスを AWG にセットする
    """
    capture_config = awgsa.CaptureConfig()
    for awg_id, wave_sequence in awg_to_wave_sequence.items():
        capture_0 = awgsa.AwgCapture(
            time = wave_sequence.get_wave(step_id = 0).get_duration(),
            delay = 0,
            do_accumulation = do_accumulation)
        capture_1 = awgsa.AwgCapture(
            time = wave_sequence.get_wave(step_id = 1).get_duration(),
            delay = 0,
            do_accumulation = do_accumulation)
        # キャプチャシーケンスの定義
        tile = awg_sa_cmd.get_adc_tile_id_by_awg_id(awg_id)
        sampling_rate = tile_to_sampling_rate[tile]
        capture_sequence = (awgsa.CaptureSequence(sampling_rate)
            .add_step(step_id = 0, capture = capture_0)
            .add_step(step_id = 1, capture = capture_1))
     
        # キャプチャシーケンスとキャプチャモジュールを対応付ける
        capture_config.add_capture_sequence(awg_id, capture_sequence)
    # キャプチャモジュールにキャプチャシーケンスを設定する
    awg_sa_cmd.set_capture_config(capture_config)


def main():   

    with client.RftoolClient(logger=logger) as rft:

        print("Connect to RFTOOL Server.")
        rft.connect(ZCU111_IP_ADDR)
        rft.command.TermMode(0)

        print("Configure Bitstream.")
        config_bitstream(rft.command, BITSTREAM)
        shutdown_all_tiles(rft.command)
        set_adc_sampling_rate(rft.command)
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
        # 波形シーケンス設定
        awg_to_wave_sequence = set_wave_sequence(rft.awg_sa_cmd)
        # キャプチャシーケンス設定
        set_capture_sequence(rft.awg_sa_cmd, awg_to_wave_sequence)
        # 波形出力 & キャプチャスタート
        rft.awg_sa_cmd.start_wave_sequence()
        # 終了待ち
        for awg_id in awg_list:
            wait_for_sequence_to_finish(rft.awg_sa_cmd, awg_id)
            print("awg {} end.".format(awg_id))

        # エラーチェック
        check_skipped_step(rft.awg_sa_cmd)
        check_capture_data_fifo_oevrflow(rft.awg_sa_cmd)
        for ch in range(8):
            check_intr_flags(rft.command, ADC, ch)
        for ch in range(8):
            check_intr_flags(rft.command, DAC, ch)

        """
        # キャプチャデータ取得
        nu = ndarrayutil.NdarrayUtil
        for awg_id in awg_list:
            r_data_0 = rft.awg_sa_cmd.read_capture_data(awg_id, step_id = 0)
            
            r_data_1 = rft.awg_sa_cmd.read_capture_data(awg_id, step_id = 1)
            r_sample_0 = nu.bytes_to_real_32(r_data_0)
            r_sample_1 = nu.bytes_to_real_32(r_data_1)
            output_graphs(
                rft.awg_sa_cmd,
                (awg_id, 0, r_sample_0),
                (awg_id, 1, r_sample_1))
            print("r_sample_0  "  + str(len(r_sample_0)))
            print("r_sample_1  "  + str(len(r_sample_1)))
        """

        # 送信波形をグラフ化
        #for awg_id in awg_list:
        #   rft.awg_sa_cmd.get_waveform_sequence(awg_id).save_as_img(PLOT_DIR + "waveform/awg_{}_waveform.png".format(awg_id))

    print("Done..")
    return


if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    handler = logging.StreamHandler()
    handler.setLevel(LOG_LEVEL)
    logger.setLevel(LOG_LEVEL)
    logger.addHandler(handler)

    try:
        param_sel = int(sys.argv[1])
    except Exception:
        param_sel = 0

    set_awg_capture_params(param_sel)
    main()
