#!/usr/bin/env python3
# coding: utf-8

"""
AWG と スペクトラムアナライザのサンプルプログラム.
特定の周波数の正弦波を AWG が送信し, それに ADC でミキサをかけた波形をキャプチャモジュールでキャプチャする.
キャプチャした波形をスペクトラムアナライザで処理し, スペクトルデータを読み取る.
AWG から出力される波形の周波数を f0 [Hz], ミキサの周波数を f1 [Hz] としたとき, 
ミキシング後の波形の周波数は, I, Q 共に (f0 + f1) と (f0 - f1) を含むので、ここにスペクトルのピークが出ているか確認する.
"""

import os
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
PLOT_DIR = "plot_mts_low_awg_send_iq_recv/"

# Log level
LOG_LEVEL = logging.INFO

# Constants
BITSTREAM = rftc.FpgaDesign.MTS_AWG_SA_LOW_SAMPLING_RATE  # MTS AWG SA LOW SAMPLING RATE
BITSTREAM_LOAD_TIMEOUT = 10
DAC_FREQ = 614.4
ADC_FREQ = 1105.92
ADC_MIXER_FREQ_0 = 50.0 #MHz
TRIG_BUSY_TIMEOUT = 60
DUC_DDC_FACTOR = 1
CAPTURE_DELAY = 2270

awg_list = [awgsa.AwgId.AWG_0, awgsa.AwgId.AWG_1, awgsa.AwgId.AWG_4,
            awgsa.AwgId.AWG_5, awgsa.AwgId.AWG_6, awgsa.AwgId.AWG_7]

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

    for awg_id in awg_list:
        awg_sa_cmd.set_wave_sequence(awg_id, calib_wave_sequence, num_repeats = 1)
    awg_sa_cmd.start_wave_sequence()
    wait_for_sequence_to_finish(awg_sa_cmd, awg_list)


def setup_dac(rftcmd):
    print("Setup DAC.")
    for tile in [0, 1]:
        rftcmd.SetupFIFO(rftc.DAC, tile, 0)
        for block in [0, 1, 2, 3]:
            rftcmd.SetMixerSettings(rftc.DAC, tile, block, 0.0, 0.0, 2, 1, 16, 4, 0)
            rftcmd.ResetNCOPhase(rftc.DAC, tile, block)
            rftcmd.UpdateEvent(rftc.DAC, tile, block, 1)
            rftcmd.SetInterpolationFactor(tile, block, DUC_DDC_FACTOR)
        rftcmd.SetupFIFO(rftc.DAC, tile, 1)


def setup_adc(rftcmd):
    print("Setup ADC.")
    for tile in [0, 1, 2, 3]:
        rftcmd.SetupFIFO(rftc.ADC, tile, 0)
        for block in [0, 1]:
            ADC_MIXER_FREQ = ADC_MIXER_FREQ_0
            rftcmd.SetMixerSettings(rftc.ADC, tile, block, ADC_MIXER_FREQ, 0.0, 2, 2, 16, 3, 0)
            rftcmd.ResetNCOPhase(rftc.ADC, tile, block)
            rftcmd.UpdateEvent(rftc.ADC, tile, block, 1)
            rftcmd.SetDither(tile, block, 1 if ADC_FREQ > 3000. else 0)
            rftcmd.SetDecimationFactor(tile, block, DUC_DDC_FACTOR)
            rftcmd.IntrClr(rftc.ADC, tile, block, 0xFFFFFFFF)
        rftcmd.SetupFIFO(rftc.ADC, tile, 1)


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
        iq = id_and_data[7]
        for j in range(num_frames):
            out_dir = PLOT_DIR + "AWG_{}_step_{}_frame_{}/".format(awg_id, step_id, j)
            os.makedirs(out_dir, exist_ok = True)
            begin = offset + stride * j
            end = max(begin + length - 1, begin)
            plot_graph(
                ADC_FREQ,
                samples[begin : end + 1],
                "C{}".format(color), 
                "AWG_{} step_{} {} capture data,  sample {} - {},  {} Msps".format(awg_id, step_id, iq, begin, end, ADC_FREQ),
                out_dir + "AWG_{}_step_{}_frame_{}_{}_captured.png".format(awg_id, step_id, j, iq))
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
        iq = id_and_data[6]
        for j in range(num_frames):
            out_dir = PLOT_DIR + "AWG_{}_step_{}_frame_{}/".format(awg_id, step_id, j)
            os.makedirs(out_dir, exist_ok = True)
            plot_graph_fft(
                real[j * fft_size : (j + 1) * fft_size],
                imaginary[j * fft_size : (j + 1) * fft_size],
                ADC_FREQ,
                (0.0, 0.5),
                "C{}".format(color),
                "AWG_{} step_{} frame_{} {} FFT".format(awg_id, step_id, j, iq),
                out_dir + "AWG_{}_step_{}_frame_{}_{}_FFT.png".format(awg_id, step_id, j, iq))

            plot_graph_fft_abs(
                absolute[j * fft_size : (j + 1) * fft_size],
                ADC_FREQ,
                (0.0, 0.5),
                "C{}".format(color),
                "AWG_{} step_{} frame_{} {} FFT".format(awg_id, step_id, j, iq),
                out_dir + "AWG_{}_step_{}_frame_{}_{}_FFT_abs.png".format(awg_id, step_id, j, iq))
        color += 1
    

def output_capture_data(awg_id_to_iq_data, awg_id_to_wave_seq, num_frames, sample_offset, fft_size):
    """
    波形データ出力
    """
    for awg_id in awg_id_to_iq_data:
        step_id = 0
        length = int(8 * ADC_FREQ / awg_id_to_wave_seq[awg_id].get_wave(step_id).get_frequency())
        iq_samples = rftc.NdarrayUtil.bytes_to_real_32(awg_id_to_iq_data[awg_id])
        i_samples = iq_samples[0 : len(iq_samples) : 2]
        q_samples = iq_samples[1 : len(iq_samples) : 2]
        output_wave_graphs(
            (awg_id, step_id, num_frames, i_samples, sample_offset, length, fft_size, "I"),
            (awg_id, step_id, num_frames, q_samples, sample_offset, length, fft_size, "Q"))


def output_spectrum_data(awg_id_to_spectrum, num_frames, fft_size):
    """
    スペクトラムデータ出力
    """
    for awg_id in awg_id_to_spectrum:
        iq_spectrum = rftc.NdarrayUtil.bytes_to_real_64(awg_id_to_spectrum[awg_id])
        i_real      = iq_spectrum[0 : len(iq_spectrum) : 4]
        i_imaginary = iq_spectrum[1 : len(iq_spectrum) : 4]
        i_abs       = np.sqrt(i_real * i_real + i_imaginary * i_imaginary)
        q_real      = iq_spectrum[2 : len(iq_spectrum) : 4]
        q_imaginary = iq_spectrum[3 : len(iq_spectrum) : 4]
        q_abs       = np.sqrt(q_real * q_real + q_imaginary * q_imaginary)
        output_fft_graphs(
            fft_size,
            (awg_id, 0, num_frames, i_real, i_imaginary, i_abs, "I"),
            (awg_id, 0, num_frames, q_real, q_imaginary, q_abs, "Q"))


def set_wave_sequence(awg_sa_cmd):
    """
    波形シーケンスを AWG にセットする
    """
    awg_id_to_wave_sequence = {}

    for awg_id in awg_list:
        # 波形の定義
        wave_0 = awgsa.AwgWave(
            wave_type = awgsa.AwgWave.SINE,
            frequency = 61.4,
            phase = 0,
            amplitude = -30000,
            num_cycles = 1200)

        # 波形シーケンスの定義
        # 波形ステップの開始から終了までの期間は, キャプチャの終了処理にかかるオーバーヘッドを考慮し, 波形出力期間 + 2000 ns を設定する.
        wave_sequence = (awgsa.WaveSequence(DAC_FREQ)
            .add_step(step_id = 0, wave = wave_0, post_blank = 2000))

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
        capture_0 = awgsa.AwgCapture(
            time = wave_sequence.get_wave(step_id = 0).get_duration() + 20,
            delay = CAPTURE_DELAY,
            do_accumulation = False)

        # キャプチャシーケンスの定義
        capture_sequence = (awgsa.CaptureSequence(ADC_FREQ, is_iq_data = True)
            .add_step(step_id = 0, capture = capture_0))
        
        # キャプチャシーケンスとキャプチャモジュールを対応付ける
        capture_config.add_capture_sequence(awg_id, capture_sequence)

    # キャプチャモジュールにキャプチャシーケンスを設定する
    awg_sa_cmd.set_capture_config(capture_config)


def main():

    with rftc.RftoolClient(logger) as client:
        print("Connect to RFTOOL Server.")
        client.connect(ZCU111_IP_ADDR)
        client.command.TermMode(0)

        print("Configure Bitstream.")
        client.command.ConfigFpga(BITSTREAM, BITSTREAM_LOAD_TIMEOUT)
        setup_dac(client.command)
        setup_adc(client.command)
        client.awg_sa_cmd.sync_dac_tiles()
        client.awg_sa_cmd.sync_adc_tiles()
        
        # 初期化    
        client.awg_sa_cmd.initialize_awg_sa()
        # AWG 有効化
        client.awg_sa_cmd.enable_awg(*awg_list)
        # ADC キャリブレーション
        calibrate_adc(client.awg_sa_cmd)
        # 波形シーケンス設定
        awg_id_to_wave_seq = set_wave_sequence(client.awg_sa_cmd)
        # キャプチャシーケンス設定
        set_capture_sequence(client.awg_sa_cmd, awg_id_to_wave_seq)
        # 波形出力 & キャプチャスタート
        client.awg_sa_cmd.start_wave_sequence()
        # 終了待ち
        wait_for_sequence_to_finish(client.awg_sa_cmd, awg_list)
        # エラーチェック
        check_skipped_step(client.awg_sa_cmd)
        check_capture_data_fifo_oevrflow(client.awg_sa_cmd)
        for ch in range(8):
            check_intr_flags(client.command, rftc.ADC, ch)
        for ch in range(8):
            check_intr_flags(client.command, rftc.DAC, ch)
        
        # キャプチャデータ取得
        rd_samples_list = [
            client.awg_sa_cmd.read_capture_data(awg_id, step_id = 0) for awg_id in awg_list]

        # キャプチャデータ出力
        num_frames = 2
        start_sample_idx = 0 # FFT 開始サンプルのインデックス
        fft_size = client.awg_sa_cmd.get_fft_size()
        awg_id_to_iq_data = dict(zip(awg_list, rd_samples_list))
        output_capture_data(awg_id_to_iq_data, awg_id_to_wave_seq, num_frames, start_sample_idx, fft_size)

        # スペクトラム取得
        print("Get spectrums.")
        awg_id_to_spectrum = {}
        for awg_id in awg_list:
            awg_id_to_spectrum[awg_id] = client.awg_sa_cmd.get_spectrum(
                awg_id, step_id = 0,
                start_sample_idx = start_sample_idx, num_frames = num_frames, is_iq_data = True)

        # スペクトラム出力
        print("Output spectrums.")
        output_spectrum_data(awg_id_to_spectrum, num_frames, fft_size)

        # 送信波形をグラフ化
        for awg_id in awg_list:
            client.awg_sa_cmd.get_waveform_sequence(awg_id).save_as_img(
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
