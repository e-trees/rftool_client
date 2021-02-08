#!/usr/bin/env python3
# coding: utf-8

"""
rftoolクライアント サンプルプログラム:
    DRAM 682Mサンプル 1ch DAC/1ch ADC 動作テスト 1.536 GSPS

<使用ライブラリ>
    numpy
    scipy
    matplotlib

<使用DACアナログ出力>
    DAC229_T1_CH2 (Tile 1 Block 2)

<使用ADCアナログ入力>
    ADC224_T0_CH0 (Tile 0 Block 0)
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

# Parameters
ZCU111_IP_ADDR = "192.168.1.3"
DAC_SAMPLES = 682 * 1024 * 1024
ADC_SAMPLES = 682 * 1024 * 1024
DATA_DEVIDES = 2 * 1024
PLOT_DIVIDES = 2 * 1024
CROP_PLOT = [0, 512]
FFT_SIZE = 32768
PLOT_DIR = "plot_dram_accum_send_recv/"

# Log level
LOG_LEVEL = logging.INFO

# Constants
BITSTREAM = 6  # DRAM ACCUM
BITSTREAM_LOAD_TIMEOUT = 10
DAC_FREQ = 1536.0
ADC_FREQ = 1536.0
TRIG_BUSY_TIMEOUT = 60 # sec
DUC_DDC_FACTOR = 1
CHUNK_SAMPLES = int(DAC_SAMPLES / DATA_DEVIDES)
CHUNK_DAC_PLOT = int(DAC_SAMPLES / PLOT_DIVIDES)
CHUNK_ADC_PLOT = int(ADC_SAMPLES / PLOT_DIVIDES)

# I/Q or Real
USE_REAL = 0
USE_IQ = 1

# ADC or DAC
ADC = 0
DAC = 1

# trigger parameters
TRIGGER_INTERVAL = 500.0 # ms
DAC_TRIGGER_LATENCY = 1.0 # ms
ADC_TRIGGER_LATENCY = DAC_TRIGGER_LATENCY + 0.0003 # ms

# Active Channel
DAC_CH = 6
ADC_CH = 0

def calculate_min_max(sample, chunks):
    sample_rs = np.reshape(sample, (-1, chunks))
    sample_min = np.amin(sample_rs, axis=1)
    sample_max = np.amax(sample_rs, axis=1)
    return sample_min, sample_max


def plot_graph_entire(freq, sample, color, title, filename):
    time = np.linspace(
        0., len(sample) / freq, PLOT_DIVIDES, endpoint=False) / 1000.
    sample_min, sample_max = calculate_min_max(sample, CHUNK_DAC_PLOT)
    fig = plt.figure(figsize=(8, 6), dpi=300)
    plt.xlabel("Time [ms]")
    plt.title(title)
    plt.plot(time, sample_min, linewidth=0.8, color=color)
    plt.plot(time, sample_max, linewidth=0.8, color=color)
    plt.fill_between(time, sample_min, sample_max, alpha=0.5, color=color)
    plt.savefig(filename)
    plt.close()
    return


def plot_graph_crop(freq, sample, color, title, filename):
    len_crop = CROP_PLOT[1] - CROP_PLOT[0]
    time = np.linspace(
        CROP_PLOT[0] / freq, CROP_PLOT[1] / freq, len_crop, endpoint=False)
    fig = plt.figure(figsize=(8, 6), dpi=300)
    plt.xlabel("Time [us]")
    plt.title(title)
    plt.plot(time, sample[CROP_PLOT[0]:CROP_PLOT[1]],
        linewidth=0.8, color=color)
    plt.savefig(filename)
    plt.close()
    return


def plot_graph_fft(freq, sample, color, title, filename):
    fft_freq = np.fft.fftfreq(FFT_SIZE, d=1./(freq*1.e6))[0:int(FFT_SIZE/2)]
    fft_data = np.zeros(int(FFT_SIZE/2))
    for i in range(int(len(sample)/FFT_SIZE)):
        fft_cur = abs(
            fftpack.fft(sample[FFT_SIZE*i:FFT_SIZE*(i+1)]))[0:int(FFT_SIZE/2)]
        fft_data = np.max([fft_data, fft_cur], axis=0)

    fig = plt.figure(figsize=(8, 6), dpi=300)
    ax = plt.gca()
    plt.grid(which="both")
    ax.set_yscale("log")
    ax.set_xscale("log")
    ax.grid(which="major", alpha=0.5)
    ax.grid(which="minor", alpha=0.2)
    plt.xlabel("Frequency [Hz]")
    plt.title(title)
    plt.plot(fft_freq, fft_data, linewidth=0.8, color=color)
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
    return


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


def wait_trig_done(rftcmd):

    BIT_DRAM_ACCUM_STATUS_COMPLETE = 0
    for i in range(TRIG_BUSY_TIMEOUT):
        status = rftcmd.GetTriggerStatus()
        complete = status & (1 << BIT_DRAM_ACCUM_STATUS_COMPLETE)
        if complete == 0:
            break
        time.sleep(1.)
    else:
        raise("Trigger busy timed out.")
    return


def calc_trigger_wait_count(millisec):
    """引数に指定した時間をトリガーのタイミングを指定するカウント値に変換する
        Parameters
        ----------
        millisec : float
            カウント値に直したい時間 (ミリ秒)

        Returns
        -------
        type : int
            カウント値
    """
    COUNTER_FREQUENCY = 300 * 1000 * 1000
    return int((millisec * COUNTER_FREQUENCY) / 1000)

def main(num_trig):

    nu = ndarrayutil.NdarrayUtil
    print("Generating waveform data.")
    r_cycles = np.round(CHUNK_SAMPLES * 20 / DAC_FREQ)  # aprox. 20 MHz
    sin_wave = np.array([np.sin(2. * np.pi * np.linspace(0., r_cycles, CHUNK_SAMPLES, endpoint=False))])
    amplitude_0 = np.linspace(-30000, 30000, DATA_DEVIDES, endpoint=False, dtype="int16")
    amplitude_1 = np.linspace(-3000, 3000, DATA_DEVIDES, endpoint=False, dtype="int16")
    w_data_0 = np.multiply(sin_wave, np.array([amplitude_0]).T).reshape(1, -1)[0].astype("<i2").tobytes()
    del r_cycles, sin_wave, amplitude_0, amplitude_1

    w_size = len(w_data_0)
    r_size = ADC_SAMPLES * 4

    with client.RftoolClient(logger=logger) as rft:
        print("Connect to RFTOOL Server.")
        rft.connect(ZCU111_IP_ADDR)
        rft.command.TermMode(0)

        print("Configure Bitstream.")
        config_bitstream(rft.command, BITSTREAM)

        set_adc_sampling_rate(rft.command, ADC_FREQ)
        set_dac_sampling_rate(rft.command, DAC_FREQ)
        
        print("Setup ADC.")
        for tile in [0, 1, 2, 3]:
            for block in [0, 1]:
                rft.command.SetMixerSettings(ADC, tile, block, 0.0, 0.0, 2, 2, 0, 3, 0)
                rft.command.ResetNCOPhase(ADC, tile, block)
                rft.command.UpdateEvent(ADC, tile, block, 1)
            rft.command.SetupFIFO(ADC, tile, 0)
            for block in [0, 1]:
                rft.command.SetDither(tile, block, 1 if ADC_FREQ > 3000. else 0)
                rft.command.SetDecimationFactor(tile, block, DUC_DDC_FACTOR)
            rft.command.SetFabClkOutDiv(ADC, tile, 2 + int(np.log2(DUC_DDC_FACTOR)))
            for block in [0, 1]:
                rft.command.IntrClr(ADC, tile, block, 0xFFFFFFFF)
            rft.command.SetupFIFO(ADC, tile, 1)

        print("Setup DAC.")
        for tile in [0, 1]:
            for block in [0, 1, 2, 3]:
                rft.command.SetMixerSettings(DAC, tile, block, 0.0, 0.0, 2, 1, 16, 4, 0)
                rft.command.ResetNCOPhase(DAC, tile, block)
                rft.command.UpdateEvent(DAC, tile, block, 1)
            rft.command.SetupFIFO(DAC, tile, 0)
            for block in [0, 1, 2, 3]:
                rft.command.SetInterpolationFactor(tile, block, DUC_DDC_FACTOR)
            rft.command.SetFabClkOutDiv(DAC, tile, 2 + int(np.log2(DUC_DDC_FACTOR)))
            for block in [0, 1, 2, 3]:
                rft.command.IntrClr(DAC, tile, block, 0xFFFFFFFF)
            rft.command.SetupFIFO(DAC, tile, 1)

        print("Send waveform data to DAC Ch.{} DynamicRAM".format(DAC_CH))
        rft.if_data.WriteDataToMemory(DAC, DAC_CH, w_size, w_data_0)

        rft.command.SetAccumulateMode(0)  # disable accumulation
        print("Setting trigger information.")
        active_dac_ch_list = 1 << DAC_CH
        active_adc_ch_list = 1 << ADC_CH
        rft.command.SetTriggerInfo(DAC, active_dac_ch_list, DAC_SAMPLES, USE_REAL)
        rft.command.SetTriggerInfo(ADC, active_adc_ch_list, ADC_SAMPLES, USE_REAL)
        rft.command.SetTriggerLatency(DAC, calc_trigger_wait_count(DAC_TRIGGER_LATENCY))
        rft.command.SetTriggerLatency(ADC, calc_trigger_wait_count(ADC_TRIGGER_LATENCY))
        rft.command.SetTriggerCycle(2, calc_trigger_wait_count(TRIGGER_INTERVAL))
        
        print("Start trigger.")
        rft.command.StartTrigger() # for ADC calibration
        wait_trig_done(rft.command)

        rft.command.SetAccumulateMode(1)  # enable accumulation
        rft.command.ClearDRAM(ADC)
        rft.command.SetTriggerCycle(num_trig, calc_trigger_wait_count(TRIGGER_INTERVAL))
        rft.command.StartTrigger()
        wait_trig_done(rft.command)

        print("Receive waveform data from ADC Ch.{} DynamicRAM".format(ADC_CH))
        r_data_0 = rft.if_data.ReadDataFromMemory(ADC, ADC_CH, r_size)

        print("Check interrupt flags.")
        for ch in range(8):
            check_intr_flags(rft.command, ADC, ch)
        for ch in range(8):
            check_intr_flags(rft.command, DAC, ch)

    
    print("Processing sample data.")
    print("- DAC sample data")
    w_sample = nu.bytes_to_real(w_data_0)
    del w_data_0
    print("- ADC sample data")
    r_sample = nu.bytes_to_real_32(r_data_0)
    del r_data_0
    
    print("Generating graph image.")
    outputdir = PLOT_DIR + str(num_trig) + "/"
    os.makedirs(outputdir, exist_ok=True)
    
    print("- entire DAC Ch.{}".format(DAC_CH))
    plot_graph_entire(
        DAC_FREQ,
        w_sample,
        "C{}".format(DAC_CH),
        "DAC waveform {} samples, {} Msps".format(DAC_SAMPLES, DAC_FREQ),
        outputdir + "dram_send_{}.png".format(DAC_CH)
    )

    print("- crop DAC Ch.{}".format(DAC_CH))
    plot_graph_crop(
        DAC_FREQ,
        w_sample,
        "C{}".format(DAC_CH),
        "DAC waveform {} samples{}, {} Msps".format(
            DAC_SAMPLES,
            " (crop {}-{})".format(CROP_PLOT[0], CROP_PLOT[1]),
            DAC_FREQ),
        outputdir + "dram_send_{}_crop.png".format(DAC_CH)
    )
    
    print("- FFT DAC Ch.{}".format(DAC_CH))
    plot_graph_fft(
        DAC_FREQ,
        w_sample,
        "C{}".format(DAC_CH),
        "DAC FFT (size:{} peak-holded), {} samples, {} Msps".format(
            FFT_SIZE, DAC_SAMPLES, DAC_FREQ),
        outputdir + "dram_send_{}_fft.png".format(DAC_CH)
    )
    
    print("- entire ADC Ch.{}".format(ADC_CH))
    plot_graph_entire(
        ADC_FREQ,
        r_sample,
        "C{}".format(ADC_CH),
        "ADC waveform {} samples, {} Msps({} times accum.)".format(ADC_SAMPLES, ADC_FREQ, str(num_trig)),
        outputdir + "dram_recv_{}.png".format(ADC_CH)
    )

    print("- crop ADC Ch.{}".format(ADC_CH))
    plot_graph_crop(
        ADC_FREQ,
        r_sample,
        "C{}".format(ADC_CH),
        "ADC waveform {} samples{}, {} Msps({} times accum.)".format(
            ADC_SAMPLES,
            " (crop {}-{})".format(CROP_PLOT[0], CROP_PLOT[1]),
            ADC_FREQ,
            str(num_trig)),
        outputdir + "dram_recv_{}_crop.png".format(ADC_CH)
    )
    
    print("- FFT ADC Ch.{}".format(ADC_CH))
    plot_graph_fft(
        ADC_FREQ,
        r_sample,
        "C{}".format(ADC_CH),
        "ADC FFT (size:{} peak-holded), {} samples, {} Msps({} times accum.)".format(
            FFT_SIZE, ADC_SAMPLES, ADC_FREQ, str(num_trig)),
        outputdir + "dram_recv_{}_fft.png".format(ADC_CH)
    )
    
    print("Done.")
    return


if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    handler = logging.StreamHandler()
    handler.setLevel(LOG_LEVEL)
    logger.setLevel(LOG_LEVEL)
    logger.addHandler(handler)

    try:
        num_trig = int(sys.argv[1])
    except Exception:
        num_trig = 10

    main(num_trig)
