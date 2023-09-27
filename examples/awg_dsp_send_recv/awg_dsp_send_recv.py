#!/usr/bin/env python3
# coding: utf-8

"""
AWG から出力した波形に信号処理を施してキャプチャする.
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
# Log level
LOG_LEVEL = logging.INFO

try:
    no_dsp = (sys.argv[1] == "no_dsp")
except Exception:
    no_dsp = False

# Constants
if no_dsp:
    BITSTREAM = rftc.FpgaDesign.AWG_SA  # AWG SA DRAM CAPTURE
    PLOT_DIR = "plot_awg_no_dsp_send_recv/"
else:
    BITSTREAM = rftc.FpgaDesign.AWG_DSP  # AWG DSP SHARED RAM
    PLOT_DIR = "plot_awg_dsp_send_recv/"

DAC_FREQ = 4096.0
ADC_FREQ = 2048.0
CAPTURE_DELAY = 200

BITSTREAM_LOAD_TIMEOUT = 10
TRIG_BUSY_TIMEOUT = 60
DUC_DDC_FACTOR = 1

awg_list = [awgsa.AwgId.AWG_4, awgsa.AwgId.AWG_5, awgsa.AwgId.AWG_6, awgsa.AwgId.AWG_7]
freq_list = [1, 100, 200, 300, 400, 500, 600] # MHz

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
            if awg_sa_cmd.is_capture_data_fifo_overflowed(awg_id, step_id = step_id):
                print("The ADC data FIFO in AWG {} has overflowed at step id {}!!".format(awg_id, step_id))


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
    for awg_id, spectrum in awg_id_to_spectrum.items():
        output_fft_graphs(
            fft_size,
            (awg_id, step_id, num_frames, spectrum.real, spectrum.imag, abs(spectrum)))


def calibrate_adc(awg_sa_cmd):
    """
    ADC をキャリブレーションする
    """
    # AWG に波形シーケンスをセットする
    for awg_id in awg_list:
        calib_wave = awgsa.AwgWave(
            wave_type = awgsa.AwgWave.SINE,
            frequency = freq_list[0],
            phase = 0,
            amplitude = 30000,
            num_cycles = int(freq_list[0] * 1e4))
        calib_wave_sequence = (awgsa.WaveSequence(DAC_FREQ)
            .add_step(step_id = 0, wave = calib_wave, post_blank = 0))
        awg_sa_cmd.set_wave_sequence(awg_id, calib_wave_sequence, num_repeats = 1)

    awg_sa_cmd.start_wave_sequence()
    wait_for_sequence_to_finish(awg_sa_cmd, *awg_list)


def gen_wave():
    """
    cos を複数重ね合わせた波を作る
    """
    num_samples = 32 * 1024
    samples = np.zeros(num_samples)
    for freq in freq_list:
        radians = [2 * np.pi * i * freq / DAC_FREQ for i in range(num_samples)]
        samples += 32000 * np.cos(radians) / len(freq_list)
    return awgsa.AwgAnyWave(np.array(samples, dtype='int16'), 1)


def set_wave_sequence(awg_sa_cmd):
    """
    波形シーケンスを AWG にセットする
    """
    wave = gen_wave()
    awg_id_to_wave_sequence = {}
    for awg_id in awg_list:
        # 波形シーケンスの定義
        wave_sequence = awgsa.WaveSequence(DAC_FREQ).add_step(step_id = 0, wave = wave, post_blank = 0)
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
            time = wave_sequence.get_wave(step_id = 0).get_duration() + 35,
            delay = CAPTURE_DELAY,
            do_accumulation = False)

        # キャプチャシーケンスの定義
        capture_sequence = awgsa.CaptureSequence(ADC_FREQ).add_step(step_id = 0, capture = capture_0)
        # キャプチャシーケンスとキャプチャモジュールを対応付ける
        capture_config.add_capture_sequence(awg_id, capture_sequence)

    # キャプチャモジュールにキャプチャシーケンスを設定する
    awg_sa_cmd.set_capture_config(capture_config)


def start_awg_and_capture(awg_sa_cmd):
    """
    波形の出力とキャプチャを開始する
    """
    # 1 チャネルずつ波形出力とキャプチャを行う
    for awg_id in awg_list:
        print("start AWG {}".format(awg_id))
        awg_sa_cmd.disable_awg(*awg_list)
        awg_sa_cmd.enable_awg(awg_id)
        awg_sa_cmd.start_wave_sequence()
        wait_for_sequence_to_finish(awg_sa_cmd, awg_id)


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
        # 波形シーケンス設定
        awg_id_to_wave_sequence = set_wave_sequence(client.awg_sa_cmd)
        # キャプチャシーケンス設定
        set_capture_sequence(client.awg_sa_cmd, awg_id_to_wave_sequence)        
        # 波形出力 & キャプチャスタート
        start_awg_and_capture(client.awg_sa_cmd)
        # エラーチェック
        check_skipped_step(client.awg_sa_cmd)
        check_capture_data_fifo_oevrflow(client.awg_sa_cmd)
        for ch in range(8):
            check_intr_flags(client.command, rftc.ADC, ch)
        for ch in range(8):
            check_intr_flags(client.command, rftc.DAC, ch)

        # スペクトラム計算
        print("Get capture data.")
        fft_size = 8192
        awg_id_to_spectrum = {}
        dc_gain = 1473  # FIR フィルタの直流成分の増幅率.
        for awg_id in awg_list:
            wave_data = client.awg_sa_cmd.read_capture_data(awg_id, step_id = 0)
            if no_dsp:
                wave_sample = rftc.NdarrayUtil.bytes_to_real_32(wave_data)
            else:
                # FIR フィルタを通さない場合と比較しやすいようにスケーリングする
                wave_sample = rftc.NdarrayUtil.bytes_to_real_32(wave_data) / dc_gain
            awg_id_to_spectrum[awg_id] = np.fft.fft(wave_sample[0:fft_size])

        # スペクトラム出力
        print("Output spectrums.")
        output_spectrum_data(awg_id_to_spectrum, 1, 0, fft_size)

    print("Done.")
    return


if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    handler = logging.StreamHandler()
    handler.setLevel(LOG_LEVEL)
    logger.setLevel(LOG_LEVEL)
    logger.addHandler(handler)
    main()
