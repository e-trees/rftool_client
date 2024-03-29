#!/usr/bin/env python3
# coding: utf-8

"""
外部トリガサンプルプログラム
AWG 0 がトリガ条件を満たす波形を連続して出力する.
それを受信した外部トリガモジュール 0 は, AWG 1, AWG 4 ～ AWG 7 に連続してトリガをかける.
外部トリガで起動した AWG の波形は, 対応するキャプチャモジュールによって積算されて保存される.
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

try:
    num_trigger_wave_repeats = int(sys.argv[1])
except Exception:
    num_trigger_wave_repeats = 10

# Parameters
ZCU111_IP_ADDR = os.environ.get('ZCU111_IP_ADDR', "192.168.1.3")
# Log level
LOG_LEVEL = logging.INFO

# Constants
BITSTREAM = rftc.FpgaDesign.AWG_SA_BRAM_CAPTURE  # AWG SA BRAM CAPTURE
PLOT_DIR = 'plot_awg_continual_external_trigger/' + str(num_trigger_wave_repeats) + '/'
DAC_FREQ = 6554.0
ADC_FREQ = 4096.0
CAPTURE_DELAY = 205
CAPTURE_POST_PROC_TIME = 830 # キャプチャの後処理にかかる時間 (単位 : ns)
TIME_TO_PREPARE = 3600  # 波形シーケンスの処理終了から, AWG が次のトリガーを受付可能になるまでの時間 (単位 : ns)
WAVE_LEN = 2100  # 外部トリガで駆動される AWG の出力波形の長さ (単位 : ns)

BITSTREAM_LOAD_TIMEOUT = 10
TRIG_BUSY_TIMEOUT = 60
DUC_DDC_FACTOR = 1

awg_list = [awgsa.AwgId.AWG_0, awgsa.AwgId.AWG_1, awgsa.AwgId.AWG_4, 
            awgsa.AwgId.AWG_5, awgsa.AwgId.AWG_6, awgsa.AwgId.AWG_7]

awg_to_freq = { awgsa.AwgId.AWG_0 : 2, # AWG 0 generates trigger wave
                awgsa.AwgId.AWG_1 : 2,
                awgsa.AwgId.AWG_4 : 15,
                awgsa.AwgId.AWG_5 : 20,
                awgsa.AwgId.AWG_6 : 25,
                awgsa.AwgId.AWG_7 : 30
            } #MHz

awg_to_cycles = {
    awgsa.AwgId.AWG_0 : [1],
    awgsa.AwgId.AWG_1 : [int(0.001 * WAVE_LEN * awg_to_freq[awgsa.AwgId.AWG_1])],
    awgsa.AwgId.AWG_4 : [int(0.001 * WAVE_LEN * awg_to_freq[awgsa.AwgId.AWG_4])],
    awgsa.AwgId.AWG_5 : [int(0.001 * WAVE_LEN * awg_to_freq[awgsa.AwgId.AWG_5])],
    awgsa.AwgId.AWG_6 : [int(0.001 * WAVE_LEN * awg_to_freq[awgsa.AwgId.AWG_6])],
    awgsa.AwgId.AWG_7 : [int(0.001 * WAVE_LEN * awg_to_freq[awgsa.AwgId.AWG_7])] 
}

awg_to_post_blank = {
    # トリガ波形の出力間隔 = 外部トリガで駆動される AWG の出力波形の長さ + キャプチャディレイ + キャプチャ後処理時間 + 次のトリガの受け入れ準備時間
    awgsa.AwgId.AWG_0 : WAVE_LEN + CAPTURE_DELAY + CAPTURE_POST_PROC_TIME + TIME_TO_PREPARE,
    awgsa.AwgId.AWG_1 : 0,
    awgsa.AwgId.AWG_4 : 0,
    awgsa.AwgId.AWG_5 : 0,
    awgsa.AwgId.AWG_6 : 0,
    awgsa.AwgId.AWG_7 : 0
} # ns

awg_to_trigger_mode = {
    awgsa.AwgId.AWG_0 : awgsa.TriggerMode.MANUAL, # AWG 0 はトリガとなる波形を出力するので SW から起動する
    awgsa.AwgId.AWG_1 : awgsa.TriggerMode.EXTERNAL,
    awgsa.AwgId.AWG_4 : awgsa.TriggerMode.EXTERNAL,
    awgsa.AwgId.AWG_5 : awgsa.TriggerMode.EXTERNAL,
    awgsa.AwgId.AWG_6 : awgsa.TriggerMode.EXTERNAL,
    awgsa.AwgId.AWG_7 : awgsa.TriggerMode.EXTERNAL
}

def plot_graph(freq, sample, color, title, filename):
    
    time = np.linspace(0, len(sample) / freq, len(sample), endpoint=False)
    plt.figure(figsize=(8, 6), dpi=300)
    plt.xlabel("Time [us]")
    plt.title(title)
    plt.plot(time, sample[0:len(sample)], linewidth=0.8, color=color)
    plt.savefig(filename)
    plt.close()
    return


def add_fft_annotate(plot, freq_res, threshold, bin_offset, spectrum):
    
    num_annotations = 0
    for i in range(len(spectrum)):
        if abs(spectrum[i]) >= threshold:
            freq = "f=" + "{:.2f}".format((i + bin_offset) * freq_res)
            bin_no = "bin=" + str(i + bin_offset)
            plot.annotate(freq + "\n" + bin_no, (i * freq_res, spectrum[i]), size=6)
            num_annotations += 1
        if num_annotations > 50:
            break

# sampling_rate Msps
def plot_graph_fft(real, imaginary, sampling_rate, plot_range, color, title, filename):
    
    freq_res = sampling_rate / len(real)
    begin = int(plot_range[0] * len(real))
    end = int(plot_range[1] * len(real))
    bin_no = [i * freq_res for i in range(begin, end)]
    fig = plt.figure(figsize=(8, 6), dpi=300)
    
    ax1 = fig.add_subplot(2, 1, 1)
    plt.title(title)
    plt.suptitle(
        "sampling rate: {} [Msps],  bin: {}-{},  FFT size: {}"
        .format(sampling_rate, begin, max(begin, end - 1), len(real)),
        fontsize=10)
    ax1.grid(which="both")
    ax1.grid(which="major", alpha=0.5)
    ax1.grid(which="minor", alpha=0.2)
    ax1.set_ylabel("Real part")
    part_of_real = real[begin : end]
    label_threshold = max(abs(part_of_real)) / 3.0
    add_fft_annotate(ax1, freq_res, label_threshold, begin, part_of_real)
    ax1.plot(bin_no, part_of_real, linewidth=0.8, color=color)

    ax2 = fig.add_subplot(2, 1, 2)
    ax2.grid(which="both")
    ax2.grid(which="major", alpha=0.5)
    ax2.grid(which="minor", alpha=0.2)
    ax2.set_xlabel("Frequency [MHz]")
    ax2.set_ylabel("Imaginary part")
    part_of_imaginary = imaginary[begin : end]
    label_threshold = max(abs(part_of_imaginary)) / 3.0
    add_fft_annotate(ax2, freq_res, label_threshold, begin, part_of_imaginary)
    ax2.plot(bin_no, part_of_imaginary, linewidth=0.8, color=color)
    plt.savefig(filename)
    plt.close()
    return


def plot_graph_fft_abs(spectrum, sampling_rate, plot_range, color, title, filename):
    """
    spectrum : list of int
        プロットするスペクトラム
    sampling_rate : float
        FFT をかけた波形データのサンプリングレート
    plot_range : (float, float)
        プロットする範囲 (各要素は 0~1.0)
    color : str
        グラフの色 (matplot の CN 記法)
    title : str
        グラフのタイトル
    filename : str
        出力ファイル名
    """
    freq_res = sampling_rate / len(spectrum)
    begin = int(plot_range[0] * len(spectrum))
    end = int(plot_range[1] * len(spectrum))

    part_of_spectrum = spectrum[begin : end]
    bin_no = [i * freq_res for i in range(begin, end)]
    plt.title(title)
    plt.suptitle(
        "sampling rate: {} [Msps],  bin: {}-{},  FFT size: {}"
        .format(sampling_rate, begin, end - 1, len(spectrum), freq_res),
        fontsize=10)
    ax = plt.gca()
    ax.grid(which="both")
    ax.grid(which="major", alpha=0.5)
    ax.grid(which="minor", alpha=0.2)
    ax.set_ylabel("Power")
    ax.set_xlabel("Frequency [MHz]")
    label_threshold = max(abs(part_of_spectrum)) / 3.0
    add_fft_annotate(ax, freq_res, label_threshold, begin, part_of_spectrum)
    ax.plot(bin_no, part_of_spectrum, linewidth=0.8, color=color)
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
        out_dir = PLOT_DIR + "AWG_{}/".format(awg_id)
        os.makedirs(out_dir, exist_ok = True)
        plot_graph(
            ADC_FREQ, 
            samples, 
            "C{}".format(color), 
            "AWG_{} step_{} captured waveform {} samples, {} Msps".format(awg_id, step_id, len(samples), ADC_FREQ),
            out_dir + "AWG_{}_step_{}_captured.png".format(awg_id, step_id))
        color += 1


def output_fft_graphs(fft_size, *id_and_data_list):

    os.makedirs(PLOT_DIR, exist_ok = True)
    color = 0
    for id_and_data in id_and_data_list:
        awg_id = id_and_data[0]
        step_id = id_and_data[1]
        num_frames = id_and_data[2]
        real = id_and_data[3]
        imaginary = id_and_data[4]
        absolute = id_and_data[5]
        for j in range(num_frames):
            out_dir = PLOT_DIR + "AWG_{}/".format(awg_id)
            os.makedirs(out_dir, exist_ok = True)
            plot_graph_fft(
                real[j * fft_size : (j + 1) * fft_size],
                imaginary[j * fft_size : (j + 1) * fft_size],
                ADC_FREQ,
                (0.0, 0.5),
                "C{}".format(color),
                "AWG_{} step_{} frame_{} FFT".format(awg_id, step_id, j),
                out_dir + "AWG_{}_step_{}_frame_{}_FFT.png".format(awg_id, step_id, j))

            plot_graph_fft_abs(
                absolute[j * fft_size : (j + 1) * fft_size],
                ADC_FREQ,
                (0.0, 0.5),
                "C{}".format(color),
                "AWG_{} step_{} frame_{} FFT".format(awg_id, step_id, j),
                out_dir + "AWG_{}_step_{}_frame_{}_FFT_abs.png".format(awg_id, step_id, j))
        color += 1
    

def output_spectrum_data(awg_id_to_spectrum, num_frames, step_id, fft_size):
    """
    スペクトラムデータ出力
    """
    for awg_id in awg_id_to_spectrum:
        spectrum  = rftc.NdarrayUtil.bytes_to_real_64(awg_id_to_spectrum[awg_id])
        real      = spectrum[0 : len(spectrum) : 2]
        imaginary = spectrum[1 : len(spectrum) : 2]
        absolute  = np.sqrt(real * real + imaginary * imaginary)
        output_fft_graphs(
            fft_size,
            (awg_id, step_id, num_frames, real, imaginary, absolute))


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
        wave_sequence = awgsa.WaveSequence(DAC_FREQ)
        for step_id, cycles in enumerate(awg_to_cycles[awg_id]):
            # 波形の定義
            wave = awgsa.AwgWave(
                wave_type = awgsa.AwgWave.SINE,
                frequency = freq,
                phase = 0,
                amplitude = 30000,
                num_cycles = cycles)
            # 波形シーケンスの定義
            wave_sequence.add_step(step_id, wave, post_blank = awg_to_post_blank[awg_id])
        num_repeats = num_trigger_wave_repeats if (awg_id == awgsa.AwgId.AWG_0) else 1
        # AWG に波形シーケンスをセットする
        awg_sa_cmd.set_wave_sequence(awg_id, wave_sequence, num_repeats = num_repeats)
        awg_id_to_wave_sequence[awg_id] = wave_sequence

    return awg_id_to_wave_sequence


def set_capture_sequence(awg_sa_cmd, awg_id_to_wave_sequence):
    """
    キャプチャシーケンスをキャプチャモジュールにセットする
    """
    capture_config = awgsa.CaptureConfig()
    for awg_id, wave_sequence in awg_id_to_wave_sequence.items():
        capture_sequence = awgsa.CaptureSequence(ADC_FREQ)
        for step_id in wave_sequence.get_step_id_list():
            # delay が波形ステップの開始から終了までの時間を超えないように注意.
            capture = awgsa.AwgCapture(
                time = wave_sequence.get_wave(step_id).get_duration(),
                delay = CAPTURE_DELAY,
                do_accumulation = True)
            # キャプチャシーケンスへのキャプチャステップの追加
            capture_sequence.add_step(step_id, capture)
        # キャプチャシーケンスとキャプチャモジュールを対応付ける
        capture_config.add_capture_sequence(awg_id, capture_sequence)
    # キャプチャモジュールにキャプチャシーケンスを設定する
    awg_sa_cmd.set_capture_config(capture_config)


def start_awg_and_capture(awg_sa_cmd):
    """
    波形の出力とキャプチャを開始する
    """
    print("start AWG 0")
    awg_sa_cmd.start_wave_sequence()
    wait_for_sequence_to_finish(awg_sa_cmd, *awg_list)


def set_external_trigger_condition(awg_sa_cmd, external_trig_id):
    """
    外部トリガのトリガ条件を設定する
    """
    LEVEL_LESS_THAN_EQ    = 0 # 閾値以下になったとき
    LEVEL_GREATER_THAN_EQ = 1 # 閾値以上になったとき
    EDGE_LESS_THAN_EQ     = 2 # 閾値を上から下に跨いだ時
    EDGE_GREATER_THAN_EQ  = 3 # 閾値を下から上に跨いだ時

    awg_sa_cmd.set_external_trigger_param(external_trig_id, 0, EDGE_GREATER_THAN_EQ)
    THRESHOLD = 1000 # トリガ条件の閾値
    awg_sa_cmd.set_external_trigger_param(external_trig_id, 1, THRESHOLD)

    #awg_sa_cmd.set_external_trigger_param(external_trig_id, 0, EDGE_LESS_THAN_EQ)
    #THRESHOLD = -200 # トリガ条件の閾値
    #awg_sa_cmd.set_external_trigger_param(external_trig_id, 1, THRESHOLD)


def setup_external_trigger(awg_sa_cmd):
    """
    外部トリガの発行に必要な設定を行う
    """
    # 各 AWG のトリガモードを設定
    for awg_id, trigger_mode in awg_to_trigger_mode.items():
        awg_sa_cmd.set_trigger_mode(awg_id, trigger_mode)
    # 外部トリガモジュール 0 にトリガ条件を設定
    set_external_trigger_condition(awg_sa_cmd, awgsa.ExternalTriggerId.EXT_TRIG_0)
    # 外部トリガモジュール 0 を起動
    awg_sa_cmd.external_trigger_on(awgsa.ExternalTriggerId.EXT_TRIG_0, oneshot = False)


def main():

    with rftc.RftoolClient(logger) as client:
        print("Connect to RFTOOL Server.")
        client.connect(ZCU111_IP_ADDR)
        client.command.TermMode(0)

        print("Configure Bitstream.")
        client.command.ConfigFpga(BITSTREAM, BITSTREAM_LOAD_TIMEOUT)
        shutdown_all_tiles(client.command)
        set_adc_sampling_rate(client.command, ADC_FREQ)
        set_dac_sampling_rate(client.command, DAC_FREQ)
        startup_all_tiles(client.command)
        setup_dac(client.command)
        setup_adc(client.command)
        
        # 初期化
        client.awg_sa_cmd.initialize_awg_sa()
        # AWG 有効化
        client.awg_sa_cmd.enable_awg(*awg_list)
        # ADC キャリブレーション
        calibrate_adc(client.awg_sa_cmd)
        # AWG の波形シーケンス設定
        awg_id_to_wave_sequence = set_wave_sequence(client.awg_sa_cmd)
        # キャプチャシーケンス設定
        set_capture_sequence(client.awg_sa_cmd, awg_id_to_wave_sequence)
        # 外部トリガ設定 & 起動
        setup_external_trigger(client.awg_sa_cmd)
        # AWG 0 にマニュアルトリガを発行.
        # AWG 0 が波形生成を開始して, それを外部トリガモジュール 0 が受け取り, 外部トリガを発行する.
        # その結果, AWG 1, 4 ～ 7 が起動して波形の出力とキャプチャが始まる.
        start_awg_and_capture(client.awg_sa_cmd)

        # エラーチェック
        check_skipped_step(client.awg_sa_cmd, awg_id_to_wave_sequence)
        check_capture_data_fifo_oevrflow(client.awg_sa_cmd, awg_id_to_wave_sequence)
        for ch in range(8):
            check_intr_flags(client.command, rftc.ADC, ch)
        for ch in range(8):
            check_intr_flags(client.command, rftc.DAC, ch)

        # キャプチャデータ取得
        print("Get capture data.")
        awg_id_to_wave_samples = {}
        for awg_id, wave_sequence in awg_id_to_wave_sequence.items():
            step_id_list = wave_sequence.get_step_id_list()
            wave_data = client.awg_sa_cmd.read_capture_data(awg_id, step_id = step_id_list[0])
            awg_id_to_wave_samples[awg_id] = rftc.NdarrayUtil.bytes_to_real_32(wave_data)

        # キャプチャデータ出力
        print("Output capture data.")
        for awg_id, wave_samples in awg_id_to_wave_samples.items():
            num_samples = min(len(wave_samples), int(2 * ADC_FREQ / awg_to_freq[awg_id]))
            output_graphs((awg_id, 0, wave_samples[0:num_samples]))

        # スペクトラム取得
        print("Get spectrums.")
        num_frames = 1
        fft_size = client.awg_sa_cmd.get_fft_size()
        awg_id_to_spectrum = {}
        for awg_id, wave_sequence in awg_id_to_wave_sequence.items():
            if awg_id != awgsa.AwgId.AWG_0:
                step_id_list = wave_sequence.get_step_id_list()
                awg_id_to_spectrum[awg_id] = client.awg_sa_cmd.get_spectrum(
                    awg_id, step_id = step_id_list[0],
                    start_sample_idx = 0, num_frames = num_frames, is_iq_data = False)

        # スペクトラム出力
        print("Output spectrums.")
        output_spectrum_data(awg_id_to_spectrum, num_frames, 1, fft_size)

        # 送信波形をグラフ化
        for awg_id in awg_list:
           client.awg_sa_cmd.get_waveform_sequence(awg_id).save_as_img(
               PLOT_DIR + "waveform/awg_{}_waveform.png".format(awg_id))
        
        # AWG へのトリガ入力回数を表示する
        print()
        for awg_id in awg_list:
            print('AWG {} : The number of {} trigger inputs   {}'.format(
                awg_id, 
                'manual' if awg_to_trigger_mode[awg_id] == awgsa.TriggerMode.MANUAL else 'external',
                client.awg_sa_cmd.get_num_wave_sequence_completed(awg_id) - 1)) # - 1 -> ADC キャリブレーションの分
    print("Done.")
    return


if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    handler = logging.StreamHandler()
    handler.setLevel(LOG_LEVEL)
    logger.setLevel(LOG_LEVEL)
    logger.addHandler(handler)
    main()
