#!/usr/bin/env python3
# coding: utf-8

"""
AWG x8 サンプルプログラム
各 AWG から特定の周波数の正弦波を出力してキャプチャする.
"""

from RftoolClient import client, rfterr, wavegen, ndarrayutil
import AwgSa as awgsa
import os
import sys
import time
import logging
import numpy as np
from scipy import fftpack
try:
    import matplotlib
    matplotlib.use("Agg")
    matplotlib.rcParams["agg.path.chunksize"] = 20000
finally:
    import matplotlib.pyplot as plt

# Parameters
ZCU111_IP_ADDR = "192.168.1.3"
PLOT_DIR = "plot_awg_x8_send_recv/"

# Log level
LOG_LEVEL = logging.INFO

# Constants
BITSTREAM = 7  # AWG SA
BITSTREAM_LOAD_TIMEOUT = 10
DAC_FREQ = 6553.6
ADC_FREQ = 3747.84
TRIG_BUSY_TIMEOUT = 60
DUC_DDC_FACTOR = 1

# ADC or DAC
ADC = 0
DAC = 1

awg_list = [awgsa.AwgId.AWG_0, awgsa.AwgId.AWG_1, awgsa.AwgId.AWG_2, awgsa.AwgId.AWG_3, 
            awgsa.AwgId.AWG_4, awgsa.AwgId.AWG_5, awgsa.AwgId.AWG_6, awgsa.AwgId.AWG_7]


awg_to_freq = { awgsa.AwgId.AWG_0 : 700,
                awgsa.AwgId.AWG_1 : 700,
                awgsa.AwgId.AWG_2 : 700,
                awgsa.AwgId.AWG_3 : 700,
                awgsa.AwgId.AWG_4 : 700,
                awgsa.AwgId.AWG_5 : 700,
                awgsa.AwgId.AWG_6 : 700,
                awgsa.AwgId.AWG_7 : 700} #MHz


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


def add_fft_annotate(plot, freq_res, threshold, bin_offset, spectrum):
    for i in range(len(spectrum)):
        if abs(spectrum[i]) >= threshold:
            freq = "f=" + "{:.2f}".format((i + bin_offset) * freq_res)
            bin_no = "bin=" + str(i + bin_offset)
            plot.annotate(freq + "\n" + bin_no, (i * freq_res, spectrum[i]), size=6)


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
    fig = plt.figure(figsize=(8, 6), dpi=300)
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


def wait_for_sequence_to_finish(awg_sa_cmd, awg_id):
    """
    波形シーケンスの出力とキャプチャが終了するまで待つ
    """
    for i in range(TRIG_BUSY_TIMEOUT):
        awg_stat = awg_sa_cmd.is_wave_sequence_complete(awg_id)
        if (awg_stat == awgsa.AwgSaCmdResult.WAVE_SEQUENCE_COMPLETE):
            return
        time.sleep(1.)
        
    raise("AWG busy timed out.")


def check_skipped_step(awg_sa_cmd):
    """
    スキップされたキャプチャステップが無いかチェックする.
    キャプチャディレイや先行するキャプチャのキャプチャ時間などにより,
    キャプチャが出来なかった場合, そのキャプチャはスキップされる.
    """
    for awg_id in awg_list:
        if awg_sa_cmd.is_capture_step_skipped(awg_id, step_id=0):
            print("The Step id 0 in AWG {} has been skipped!!".format(awg_id))


def check_capture_data_fifo_oevrflow(awg_sa_cmd):
    """
    ADC から送られる波形データを格納する FIFO で, オーバーフローが発生していないかチェックする.
    PL 上の DRAM の帯域の制限などにより, ADC から送信されるデータの処理が間に合わない場合, 
    波形データを格納する FIFO のオーバーフローが発生する.
    """
    for awg_id in awg_list:
        if awg_sa_cmd.is_capture_data_fifo_overflowed(awg_id, step_id=0):
            print("The ADC data FIFO in AWG {} has overflowed at step id 0!!".format(awg_id))


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
            out_dir = PLOT_DIR + "AWG_{}_step_{}_frame_{}/".format(awg_id, step_id, j)
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
    

def output_spectrum_data(awg_id_to_spectrum, num_frames, fft_size):
    """
    スペクトラムデータ出力
    """
    for awg_id in awg_id_to_spectrum:
        spectrum  = ndarrayutil.NdarrayUtil.bytes_to_real_64(awg_id_to_spectrum[awg_id])
        real      = spectrum[0 : len(spectrum) : 2]
        imaginary = spectrum[1 : len(spectrum) : 2]
        absolute  = np.sqrt(real * real + imaginary * imaginary)
        output_fft_graphs(
            fft_size,
            (awg_id, 0, num_frames, real, imaginary, absolute))


def calibrate_adc(awg_sa_cmd):
    """
    ADC をキャリブレーションする
    """
    calib_wave = awgsa.AwgWave(
        wave_type = awgsa.AwgWave.SINE,
        frequency = 800.0,
        phase = 0,
        amplitude = 30000,
        num_cycles = 1000000)

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
    awg_id_to_wave_sequence = {}

    for awg_id in awg_list:
        # 波形の定義
        wave = awgsa.AwgWave(
            wave_type = awgsa.AwgWave.SINE,
            frequency = awg_to_freq[awg_id],
            phase = 0,
            amplitude = 30000,
            num_cycles = 5)

        # 波形シーケンスの定義
        # 波形ステップの開始から終了までの期間は, キャプチャの終了処理にかかるオーバーヘッドを考慮し, 波形出力期間 + 2000 ns を設定する.
        wave_sequence = (awgsa.WaveSequence(DAC_FREQ)
            .add_step(step_id = 0, wave = wave, post_blank = 2000))

        # AWG に波形シーケンスをセットする
        awg_sa_cmd.set_wave_sequence(awg_id = awg_id, wave_sequence = wave_sequence, num_repeats = 1)
        awg_id_to_wave_sequence[awg_id] = wave_sequence

    return awg_id_to_wave_sequence


def set_capture_sequence(awg_sa_cmd, awg_id_to_wave_sequence):
    """
    キャプチャシーケンスを AWG にセットする
    """
    capture_config = awgsa.CaptureConfig()

    for awg_id, wave_sequence in awg_id_to_wave_sequence.items():
        # キャプチャ時間は, キャプチャする波形の長さ + 35 ns とする.
        # delay が波形ステップの開始から終了までの時間を超えないように注意.
        capture = awgsa.AwgCapture(
            time = wave_sequence.get_wave(step_id = 0).get_duration() + 35,
            delay = 148,
            do_accumulation = False)

        # キャプチャシーケンスの定義
        capture_sequence = (awgsa.CaptureSequence(ADC_FREQ)
            .add_step(step_id = 0, capture = capture))
        
        # キャプチャシーケンスと AWG を対応付ける
        capture_config.add_capture_sequence(awg_id, capture_sequence)

    # AWG に キャプチャシーケンスを設定する
    awg_sa_cmd.set_capture_config(capture_config)


def main():

    with client.RftoolClient(logger=logger) as rft:
        print("Connect to RFTOOL Server.")
        rft.connect(ZCU111_IP_ADDR)
        rft.command.TermMode(0)

        print("Configure Bitstream.")
        config_bitstream(rft.command, BITSTREAM)
        set_adc_sampling_rate(rft.command, ADC_FREQ)
        set_dac_sampling_rate(rft.command, DAC_FREQ)
        setup_dac(rft.command)
        setup_adc(rft.command)

        # 初期化    
        rft.awg_sa_cmd.initialize_awg_sa()
        # AWG 有効化
        rft.awg_sa_cmd.enable_awg(*awg_list)
        # ADC キャリブレーション
        calibrate_adc(rft.awg_sa_cmd)
        # 波形シーケンス設定
        awg_id_to_wave_sequence = set_wave_sequence(rft.awg_sa_cmd)
        # キャプチャシーケンス設定
        set_capture_sequence(rft.awg_sa_cmd, awg_id_to_wave_sequence)
        
        # 波形出力 & キャプチャスタート
        # 1 チャネルずつ波形出力とキャプチャを行う
        for awg_id in awg_list:
            print("awg {} start".format(awg_id))
            rft.awg_sa_cmd.disable_awg(*awg_list)
            rft.awg_sa_cmd.enable_awg(awg_id)
            rft.awg_sa_cmd.start_wave_sequence()
            # 終了待ち
            wait_for_sequence_to_finish(rft.awg_sa_cmd, awg_id)

        # エラーチェック
        check_skipped_step(rft.awg_sa_cmd)
        check_capture_data_fifo_oevrflow(rft.awg_sa_cmd)
        for ch in range(8):
            check_intr_flags(rft.command, ADC, ch)
        for ch in range(8):
            check_intr_flags(rft.command, DAC, ch)
        
        # キャプチャデータ取得
        nu = ndarrayutil.NdarrayUtil
        awg_id_to_wave_samples = {}
        for awg_id in awg_list:
            wave_data = rft.awg_sa_cmd.read_capture_data(awg_id, step_id = 0)
            awg_id_to_wave_samples[awg_id] = nu.bytes_to_real_32(wave_data)

        # キャプチャデータ出力
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
