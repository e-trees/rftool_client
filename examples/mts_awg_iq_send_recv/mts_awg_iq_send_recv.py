#!/usr/bin/env python3
# coding: utf-8

"""
AWG と スペクトラムアナライザのサンプルプログラム.
I/Q データを DAC でミキシングし, ADC で Real データとしてキャプチャする.
キャプチャしたデータに FFT をかけ, 結果をグラフとして出力する.

[AWG 4, 5 の説明] 
    AWG 4, 5 は, I データとして正弦波 (f0 [Hz]) を入力し, Q データとしてデューティ比 100% の方形波を入力する.
    DAC から出力される波形は, (I データ x ミキサ正弦波) + (Q データ x ミキサ余弦波) である.
    ミキサの周波数を f1 [Hz] としたとき, 
    (I データ x ミキサ正弦波) の波形の周波数成分は, (f0 + f1) と (f0 - f1) となり, 
    (Q データ x ミキサ余弦波) の波形の周波数成分は, f1 となる.
    よって, DAC から出力される波形の周波数成分は, (f0 + f1) , (f0 - f1), f1 となり, 
    この 3 箇所にキャプチャデータのスペクトルのピークが表れる.

[AWG 6, 7 の説明]
    AWG 6, 7 は, I データとして余弦波 (f2 [Hz]) を入力し, Q データとして正弦波 (f2 [Hz]) を入力する.
    DAC から出力される波形は, (I データ x ミキサ正弦波) + (Q データ x ミキサ余弦波) である.
    ミキサの周波数を f3 [Hz] としたとき, 
    (I データ x ミキサ正弦波) の波形の周波数成分は, (f2 + f3) と (f2 - f3) となり,
    (Q データ x ミキサ余弦波) の波形の周波数成分は, (f2 + f3) と (f2 - f3) となる.
    ただし, この 2つの波形の f2 - f3 成分は, 大きさが正負逆なので, 足したときに打ち消しあう.
    よって, DAC から出力される波形の周波数は, f2 + f3 となり, ここにキャプチャデータのスペクトルのピークが表れる.
"""

import os
import sys
import time
import logging
import numpy as np
import pathlib

try:
    import matplotlib
    matplotlib.use("Agg")
    matplotlib.rcParams["agg.path.chunksize"] = 20000
finally:
    import matplotlib.pyplot as plt

lib_path = str(pathlib.Path(__file__).resolve().parents[2])
sys.path.append(lib_path)
from RftoolClient import client, ndarrayutil
import AwgSa as awgsa

# FPGA design
MTS = 0
MTS_LOW = 1
fpga_design = MTS
try:
    if sys.argv[1] == "low":
        fpga_design = MTS_LOW
except Exception:
    pass

# Parameters
ZCU111_IP_ADDR = os.environ.get('ZCU111_IP_ADDR', "192.168.1.3")

# Log level
LOG_LEVEL = logging.INFO

# Constants
if fpga_design == MTS:
    BITSTREAM = 8  # MTS AWG SA
    PLOT_DIR = "plot_mts_awg_iq_send_recv/"
    DAC_FREQ = 3932.16
    ADC_FREQ = 3932.16
    CAPTURE_DELAY = 365
    DAC_MIXER_FREQ_0 = 107 #MHz
    DAC_MIXER_FREQ_1 = 44 #MHz
else:
    BITSTREAM = 12  # MTS AWG SA LOW SAMPLING RATE
    PLOT_DIR = "plot_mts_low_awg_iq_send_recv/"
    DAC_FREQ = 614.4
    ADC_FREQ = 1105.92
    CAPTURE_DELAY = 2365
    DAC_MIXER_FREQ_0 = 15.0 #MHz
    DAC_MIXER_FREQ_1 = 10.0 #MHz

BITSTREAM_LOAD_TIMEOUT = 10
TRIG_BUSY_TIMEOUT = 60
DUC_DDC_FACTOR = 1

# ADC or DAC
ADC = 0
DAC = 1

awg_list = [awgsa.AwgId.AWG_4, awgsa.AwgId.AWG_6,
            awgsa.AwgId.AWG_5, awgsa.AwgId.AWG_7]

if fpga_design == MTS:
    freq_list = [393.2, 196.6]
else:
    freq_list = [61.4, 30.7]

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
        details.append("RFDC FIFO marginal overflow detected.")
    if (flags & 0x00000008):
        details.append("RFDC FIFO marginal underflow detected.")
    for d in details:
        print(" - " + d)
    return

def calibrate_adc(awg_sa_cmd):
    """
    ADC をキャリブレーションする
    """
    i_wave = awgsa.AwgWave(
        wave_type = awgsa.AwgWave.SINE,
        frequency = 10.0,
        phase = 0,
        amplitude = 15000,
        num_cycles = int(1e5))
    q_wave = awgsa.AwgWave(
        wave_type = awgsa.AwgWave.SINE,
        frequency = 10.0,
        phase = 0,
        amplitude = 15000,
        num_cycles = int(1e5))
    iq_wave = awgsa.AwgIQWave(i_wave, q_wave)

    calib_wave_sequence = (awgsa.WaveSequence(DAC_FREQ, is_iq_data = True)
        .add_step(step_id = 0, wave = iq_wave, post_blank = 2000))
    
    for awg_id in awg_list:
        awg_sa_cmd.set_wave_sequence(awg_id, calib_wave_sequence, num_repeats = 1)
    awg_sa_cmd.start_wave_sequence()
    wait_for_sequence_to_finish(awg_sa_cmd, awg_list)


def setup_dac(rftcmd, awg_sa_cmd):
    print("Setup DAC.")
    for tile in [0, 1]:
        rftcmd.SetupFIFO(DAC, tile, 0)
        for block in [0, 1, 2, 3]:
            if (awg_sa_cmd.awg_to_dac_tile_block(awg_list[0]) == (tile, block) or
                awg_sa_cmd.awg_to_dac_tile_block(awg_list[1]) == (tile, block)):
                mixer_freq = DAC_MIXER_FREQ_0
            else:
                mixer_freq = DAC_MIXER_FREQ_1
            rftcmd.SetMixerSettings(DAC, tile, block, mixer_freq, 0.0, 2, 2, 16, 2, 0)
            rftcmd.UpdateEvent(DAC, tile, block, 1)
            rftcmd.SetInterpolationFactor(tile, block, DUC_DDC_FACTOR + 1) #I/Q データの場合 x2 以上で補間される
            rftcmd.IntrClr(DAC, tile, block, 0xFFFFFFFF)
        rftcmd.SetupFIFO(DAC, tile, 1)


def setup_adc(rftcmd):
    print("Setup ADC.")
    for tile in [0, 1, 2, 3]:
        rftcmd.SetupFIFO(ADC, tile, 0)
        for block in [0, 1]:
            rftcmd.SetMixerSettings(ADC, tile, block, 0.0, 0.0, 2, 1, 16, 4, 0)
            rftcmd.UpdateEvent(ADC, tile, block, 1)
            rftcmd.SetDither(tile, block, 1 if ADC_FREQ > 3000. else 0)
            rftcmd.SetDecimationFactor(tile, block, DUC_DDC_FACTOR)
            rftcmd.IntrClr(ADC, tile, block, 0xFFFFFFFF)
        rftcmd.SetupFIFO(ADC, tile, 1)


def wait_for_sequence_to_finish(awg_sa_cmd, awg_id_list):
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


def check_skipped_step(awg_sa_cmd):
    """
    スキップされたキャプチャステップが無いかチェックする.
    キャプチャディレイや先行するキャプチャのキャプチャ時間などにより,
    キャプチャが出来なかった場合, そのキャプチャはスキップされる.
    """
    for awg_id in awg_list:
        for step_id in range(1):
            if awg_sa_cmd.is_capture_step_skipped(awg_id, step_id):
                print("The Step id {} in AWG {} has been skipped!!".format(step_id, awg_id))


def check_capture_data_fifo_oevrflow(awg_sa_cmd):
    """
    ADC から送られる波形データを格納する FIFO で, オーバーフローが発生していないかチェックする.
    PL 上の BRAM の帯域の制限などにより, ADC から送信されるデータの処理が間に合わない場合, 
    波形データを格納する FIFO のオーバーフローが発生する.
    """
    for awg_id in awg_list:
        for step_id in range(1):
            if awg_sa_cmd.is_capture_data_fifo_overflowed(awg_id, step_id):
                print("The ADC data FIFO in AWG {} has overflowed at step id {}!!".format(awg_id, step_id))


def output_wave_graphs(*id_and_data_list):

    color = 0
    for id_and_data in id_and_data_list:        
        awg_id = id_and_data[0]
        step_id = id_and_data[1]
        num_frames = id_and_data[2]
        samples = id_and_data[3]
        offset = id_and_data[4]
        length = id_and_data[5]
        stride = id_and_data[6]
        for j in range(num_frames):
            out_dir = PLOT_DIR + "AWG_{}_step_{}_frame_{}/".format(awg_id, step_id, j)
            os.makedirs(out_dir, exist_ok = True)
            begin = offset + stride * j
            end = max(begin + length - 1, begin)
            plot_graph(
                ADC_FREQ,
                samples[begin : end + 1],
                "C{}".format(color), 
                "AWG_{} step_{} capture data,  sample {} - {},  {} Msps".format(awg_id, step_id, begin, end, ADC_FREQ),
                out_dir + "AWG_{}_step_{}_frame_{}_captured.png".format(awg_id, step_id, j))
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
    

def output_capture_data(awg_id_to_wave_data, awg_id_to_wave_seq, num_frames, sample_offset, fft_size):
    """
    波形データ出力
    """
    for awg_id in awg_id_to_wave_data:
        step_id = 0
        freq = min(awg_id_to_wave_seq[awg_id].get_wave(step_id).get_i_wave().get_frequency(),
                   awg_id_to_wave_seq[awg_id].get_wave(step_id).get_q_wave().get_frequency())
        length = int(25 * ADC_FREQ / freq)
        wave_data = ndarrayutil.NdarrayUtil.bytes_to_real_32(awg_id_to_wave_data[awg_id])
        output_wave_graphs((awg_id, step_id, num_frames, wave_data, sample_offset, length, fft_size))


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


def set_wave_sequence(awg_sa_cmd):
    """
    波形シーケンスを AWG にセットする
    """
    # 波形の定義
    i_wave_0 = awgsa.AwgWave(
        wave_type = awgsa.AwgWave.SINE,
        frequency = freq_list[0],
        phase = 0,
        amplitude = 15000,
        num_cycles = 2500)

    q_wave_0 = awgsa.AwgWave(
        wave_type = awgsa.AwgWave.SQUARE,
        frequency = freq_list[0],
        phase = 0,
        amplitude = 15000,
        duty_cycle = 100.0,
        num_cycles = 2500)

    iq_wave_0 = awgsa.AwgIQWave(i_wave_0, q_wave_0)

    i_wave_1 = awgsa.AwgWave(
        wave_type = awgsa.AwgWave.SINE,
        frequency = freq_list[1],
        phase = 90.0, # cos
        amplitude = 15000,
        duty_cycle = 100.0,
        num_cycles = 1200)

    q_wave_1 = awgsa.AwgWave(
        wave_type = awgsa.AwgWave.SINE,
        frequency = freq_list[1],
        phase = 0,
        amplitude = 15000,
        num_cycles = 1200)

    iq_wave_1 = awgsa.AwgIQWave(i_wave_1, q_wave_1)

    # 波形シーケンスの作成
    wave_sequence_0 = (awgsa.WaveSequence(DAC_FREQ, is_iq_data = True)
        .add_step(step_id = 0, wave = iq_wave_0, post_blank = 2000))
    wave_sequence_1 = (awgsa.WaveSequence(DAC_FREQ, is_iq_data = True)
        .add_step(step_id = 0, wave = iq_wave_1, post_blank = 2000))

    # AWG に波形シーケンスをセットする
    awg_sa_cmd.set_wave_sequence(awg_list[0], wave_sequence_0)
    awg_sa_cmd.set_wave_sequence(awg_list[1], wave_sequence_0)
    awg_sa_cmd.set_wave_sequence(awg_list[2], wave_sequence_1)
    awg_sa_cmd.set_wave_sequence(awg_list[3], wave_sequence_1)
    return {
        awg_list[0] : wave_sequence_0,
        awg_list[1] : wave_sequence_0,
        awg_list[2] : wave_sequence_1,
        awg_list[3] : wave_sequence_1}


def set_capture_sequence(awg_sa_cmd, awg_id_to_wave_sequence):
    """
    キャプチャシーケンスを AWG にセットする
    """
    capture_config = awgsa.CaptureConfig()

    for awg_id, wave_sequence in awg_id_to_wave_sequence.items():
        # キャプチャ時間は, キャプチャする波形の長さ + 35 ns とする.
        # delay が波形ステップの開始から終了までの時間を超えないように注意.
        capture_0 = awgsa.AwgCapture(
            time = wave_sequence.get_wave(step_id = 0).get_duration() + 20,
            delay = CAPTURE_DELAY,
            do_accumulation = False)

        # キャプチャシーケンスの定義
        capture_sequence = (awgsa.CaptureSequence(ADC_FREQ)
            .add_step(step_id = 0, capture = capture_0))
        
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
        setup_dac(rft.command, rft.awg_sa_cmd)
        setup_adc(rft.command)
        rft.awg_sa_cmd.sync_dac_tiles()
        rft.awg_sa_cmd.sync_adc_tiles()

        # 初期化    
        rft.awg_sa_cmd.initialize_awg_sa()
        # AWG 有効化
        rft.awg_sa_cmd.enable_awg(*awg_list)
        # ADC キャリブレーション
        calibrate_adc(rft.awg_sa_cmd)
        # 波形シーケンス設定
        awg_id_to_wave_seq = set_wave_sequence(rft.awg_sa_cmd)
        # キャプチャシーケンス設定
        set_capture_sequence(rft.awg_sa_cmd, awg_id_to_wave_seq)
        # 波形出力 & キャプチャスタート
        rft.awg_sa_cmd.start_wave_sequence()
        # 終了待ち
        wait_for_sequence_to_finish(rft.awg_sa_cmd, awg_list)
        # エラーチェック
        check_skipped_step(rft.awg_sa_cmd)
        check_capture_data_fifo_oevrflow(rft.awg_sa_cmd)
        for ch in range(8):
            check_intr_flags(rft.command, ADC, ch)
        for ch in range(8):
            check_intr_flags(rft.command, DAC, ch)

        # キャプチャデータ取得
        rd_samples_list = [
            rft.awg_sa_cmd.read_capture_data(awg_id, step_id = 0) for awg_id in awg_list]

        # キャプチャデータ出力
        num_frames = 2
        start_sample_idx = 16 # FFT 開始サンプルのインデックス
        fft_size = rft.awg_sa_cmd.get_fft_size()
        awg_id_to_wave_data = dict(zip(awg_list, rd_samples_list))
        output_capture_data(awg_id_to_wave_data, awg_id_to_wave_seq, num_frames, start_sample_idx, fft_size)

        # スペクトラム取得
        print("Get spectrums.")
        awg_id_to_spectrum = {}
        for awg_id in awg_list:
            awg_id_to_spectrum[awg_id] = rft.awg_sa_cmd.get_spectrum(
                awg_id, step_id = 0,
                start_sample_idx = start_sample_idx, num_frames = num_frames, is_iq_data = False)

        # スペクトラム出力
        print("Output spectrums.")
        output_spectrum_data(awg_id_to_spectrum, num_frames, fft_size)

        # 送信波形をグラフ化
        for awg_id in awg_list:
           rft.awg_sa_cmd.get_waveform_sequence(awg_id).save_as_img(
               PLOT_DIR + "waveform/awg_{}_waveform.png".format(awg_id))

    print("Done.")
    return


if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    handler = logging.StreamHandler()
    handler.setLevel(LOG_LEVEL)
    logger.setLevel(LOG_LEVEL)
    logger.addHandler(handler)

    main()
