#!/usr/bin/env python3
# coding: utf-8

"""
rftoolクライアントサンプルプログラム:
    BRAM 16Kサンプル DAC出力 / ADC積算 動作テスト 4.096 GSPS

<使用ライブラリ>
    numpy
    scipy
    matplotlib

<使用DACアナログ出力>
    DAC229_T1_CH2 (Tile 1 Block 2)
    DAC229_T1_CH3 (Tile 1 Block 3)

<使用ADCアナログ入力>
    ADC224_T0_CH0 (Tile 0 Block 0)
    ADC224_T0_CH1 (Tile 0 Block 1)
"""

import sys
import os
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

## Variables
ZCU111_IP_ADDR = "192.168.1.3"
DAC_SAMPLES = 16384  # DAC num of samples
ADC_SAMPLES = 16384  # ADC num of samples
CROP_PLOT = [0, 1024]  # crop samples for plot
FFT_SIZE = 1024
PLOT_DIR = "plot_bram_iq_send_recv/"

# Log level
LOG_LEVEL = logging.INFO

# Constants
BITSTREAM = 5  # BRAM ACCUM MAX SAMPLING RATE
BITSTREAM_LOAD_TIMEOUT = 10
DAC_FREQ = 4096.0
ADC_FREQ = 4096.0
DUC_DDC_FACTOR = 1
TRIG_BUSY_TIMEOUT = 5

# I/Q or Real
USE_REAL = 0
USE_IQ = 1

#ADC or DAC
ADC = 0
DAC = 1

USE_INTERNAL_PLL = 1
PLL_A = 0x8
PLL_B = 0x4
PLL_C = 0x1

def calculate_min_max(sample, chunks):
    sample_rs = np.reshape(sample, (-1, chunks))
    sample_min = np.amin(sample_rs, axis=1)
    sample_max = np.amax(sample_rs, axis=1)
    return sample_min, sample_max


def plot_graph_entire_iq(freq, sample, chunk_plot, color, title, filename):
    time = np.linspace(
        0., len(sample) / freq, len(sample), endpoint=False)
    sample_min_i, sample_max_i = calculate_min_max(sample.real, chunk_plot)
    sample_min_q, sample_max_q = calculate_min_max(sample.imag, chunk_plot)
    fig = plt.figure(figsize=(8, 6), dpi=300)
    ax1 = fig.add_subplot(2, 1, 1)
    plt.title(title)
    ax1.set_ylabel("Real part")
    ax1.plot(time, sample.real, linewidth=0.8, color=color)
    ax2 = fig.add_subplot(2, 1, 2)
    ax2.set_xlabel("Time [us]")
    ax2.set_ylabel("Imaginary part")
    ax2.plot(time, sample.imag, linewidth=0.8, color=color)
    plt.savefig(PLOT_DIR + filename)
    plt.close()
    return


def plot_graph_crop_iq(freq, sample, color, title, filename):
    len_crop = CROP_PLOT[1] - CROP_PLOT[0]
    time = np.linspace(CROP_PLOT[0] / freq, CROP_PLOT[1] / freq, len_crop, endpoint=False) * 1000
    fig = plt.figure(figsize=(8, 6), dpi=300)
    ax1 = fig.add_subplot(2, 1, 1)
    plt.title(title)
    ax1.set_ylabel("Real part")
    ax1.plot(time, sample[CROP_PLOT[0]:CROP_PLOT[1]].real,
        linewidth=0.8, color=color)
    ax2 = fig.add_subplot(2, 1, 2)
    ax2.set_xlabel("Time [ns]")
    ax2.set_ylabel("Imaginary part")
    ax2.plot(time, sample[CROP_PLOT[0]:CROP_PLOT[1]].imag,
        linewidth=0.8, color=color)
    plt.savefig(PLOT_DIR + filename)
    plt.close()
    return


def plot_graph_fft_iq(freq, sample, color, title, filename):
    fft_freq = np.fft.fftfreq(FFT_SIZE, d=1./(freq*1.e6))[0:int(FFT_SIZE/2)]
    fft_data_i = np.zeros(int(FFT_SIZE/2))
    for i in range(int(len(sample)/FFT_SIZE)):
        fft_cur = abs(
            fftpack.fft(sample[FFT_SIZE*i:FFT_SIZE*(i+1)].real))[0:int(FFT_SIZE/2)]
        fft_data_i = np.max([fft_data_i, fft_cur], axis=0)
    fft_data_q = np.zeros(int(FFT_SIZE/2))
    for i in range(int(len(sample)/FFT_SIZE)):
        fft_cur = abs(
            fftpack.fft(sample[FFT_SIZE*i:FFT_SIZE*(i+1)].real))[0:int(FFT_SIZE/2)]
        fft_data_q = np.max([fft_data_q, fft_cur], axis=0)

    fig = plt.figure(figsize=(8, 6), dpi=300)
    ax1 = fig.add_subplot(2, 1, 1)
    plt.title(title)
    #ax1.set_yscale("log")
    ax1.set_xscale("log")
    ax1.grid(which="both")
    ax1.grid(which="major", alpha=0.5)
    ax1.grid(which="minor", alpha=0.2)
    ax1.set_ylabel("Real part")
    ax1.plot(fft_freq, fft_data_i, linewidth=0.8, color=color)
    ax2 = fig.add_subplot(2, 1, 2)
    #ax2.set_yscale("log")
    ax2.set_xscale("log")
    ax2.grid(which="both")
    ax2.grid(which="major", alpha=0.5)
    ax2.grid(which="minor", alpha=0.2)
    ax2.set_xlabel("Frequency [Hz]")
    ax2.set_ylabel("Imaginary part")
    ax2.plot(fft_freq, fft_data_q, linewidth=0.8, color=color)
    plt.savefig(PLOT_DIR + filename)
    plt.close()
    return

def plot_graph_entire(freq, sample, chunk_plot, color, title, filename):
    time = np.linspace(0., len(sample) / freq, len(sample), endpoint=False)
    fig = plt.figure(figsize=(8, 6), dpi=300)
    plt.xlabel("Time [us]")
    plt.title(title)
    plt.plot(time, sample, linewidth=0.8, color=color)
    plt.savefig(PLOT_DIR + filename)
    plt.close()
    return

def plot_graph_crop(freq, sample, color, title, filename):
    len_crop = CROP_PLOT[1] - CROP_PLOT[0]
    time = np.linspace(
        CROP_PLOT[0] / freq, CROP_PLOT[1] / freq, len_crop, endpoint=False) * 1000.
    fig = plt.figure(figsize=(8, 6), dpi=300)
    plt.xlabel("Time [ns]")
    plt.title(title)
    plt.plot(time, sample[CROP_PLOT[0]:CROP_PLOT[1]],
        linewidth=0.8, color=color)
    plt.savefig(PLOT_DIR + filename)
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
    #ax.set_yscale("log")
    ax.set_xscale("log")
    ax.grid(which="major", alpha=0.5)
    ax.grid(which="minor", alpha=0.2)
    plt.xlabel("Frequency [Hz]")
    plt.title(title)
    plt.plot(fft_freq, fft_data, linewidth=0.8, color=color)
    plt.savefig(PLOT_DIR + filename)
    plt.close()
    return


def wait_trig_done(rftcmd):
    for i in range(TRIG_BUSY_TIMEOUT):
        if rftcmd.GetTriggerStatus() == 0:
            break
        time.sleep(1.)
    else:
        raise("Trigger busy timed out.")
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


def main():
    
    wgen = wavegen.WaveGen(logger=logger)
    nu = ndarrayutil.NdarrayUtil

    print("Generate waveform data.")
    wgen.set_parameter(num_sample=DAC_SAMPLES, dac_freq=DAC_FREQ,
                       carrier_freq=30.0, amplitude=30000.0)
    w_data = wgen.sinwave()
    w_size = len(w_data)  # for 16bit signed integer
    r_size = ADC_SAMPLES * 4 * 2  # for two 32bit signed integer values (I Data and Q Data)
    
    with client.RftoolClient(logger=logger) as rft:
        print("Connect to RFTOOL Server.")
        rft.connect(ZCU111_IP_ADDR)
        rft.command.TermMode(0)

        print("Configure Bitstream.")
        config_bitstream(rft.command, BITSTREAM)

        print("set sampling rate.")
        set_adc_sampling_rate(rft.command, ADC_FREQ)
        set_dac_sampling_rate(rft.command, DAC_FREQ)

        print("Setup ADC.")
        for tile in [0, 1, 2, 3]:
            for block in [0, 1]:
                rft.command.SetMixerSettings(ADC, tile, block, 10, 45.0,
                    2, 2, 16, 3, 0)
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
                rft.command.SetMixerSettings(DAC, tile, block, 0.0, 0.0,
                    2, 1, 16, 4, 0)
                rft.command.ResetNCOPhase(DAC, tile, block)
                rft.command.UpdateEvent(DAC, tile, block, 1)
            rft.command.SetupFIFO(DAC, tile, 0)
            for block in [0, 1, 2, 3]:
                rft.command.SetInterpolationFactor(tile, block, DUC_DDC_FACTOR)
            rft.command.SetFabClkOutDiv(DAC, tile, 2 + int(np.log2(DUC_DDC_FACTOR)))
            for block in [0, 1, 2, 3]:
                rft.command.IntrClr(DAC, tile, block, 0xFFFFFFFF)
            rft.command.SetupFIFO(DAC, tile, 1)

        print("Clear BlockRAM.")
        rft.command.ClearBRAM()

        for ch in [6, 7]:
            print("Send waveform data to DAC Ch.{} BlockRAM".format(ch))
            rft.if_data.WriteDataToMemory(DAC, ch, w_size, w_data)

        print("Setting trigger information.")
        rft.command.SetTriggerInfo(ADC, 0xFF, ADC_SAMPLES, USE_IQ)
        rft.command.SetTriggerInfo(DAC, 0xFF, DAC_SAMPLES, USE_REAL)
        rft.command.SetTriggerLatency(ADC, 45)
        rft.command.SetTriggerLatency(DAC, 0)
        rft.command.SetTriggerCycle(1, 1)
        rft.command.SetAccumulateMode(0)  # disable accumulation

        print("Start trigger.")
        rft.command.StartTrigger()
        wait_trig_done(rft.command)

        r_data = []
        for ch in [0, 1]:
            print("Receive waveform data from ADC Ch.{} BlockRAM".format(ch))
            r_data.append(rft.if_data.ReadDataFromMemory(ADC, ch, r_size))

        print("Check interrupt flags.")
        for ch in range(8):
            check_intr_flags(rft.command, ADC, ch)
        for ch in range(8):
            check_intr_flags(rft.command, DAC, ch)
    
    print("Processing sample data.")
    print("- DAC sample data")
    w_sample = nu.bytes_to_real(w_data)
    del w_data
    print("- ADC sample data")
    r_sample = np.array([nu.bytes_to_complex_32(rd) for rd in r_data])
    del r_data

    print("Generating graph image.")
    os.makedirs(PLOT_DIR, exist_ok=True)

    print("- entire DAC")
    plot_graph_entire(
        DAC_FREQ,
        w_sample,
        1,
        "C0",
        "DAC waveform {} samples, {} Msps".format(DAC_SAMPLES, DAC_FREQ),
        "bram_send.png"
    )

    print("- crop DAC")
    plot_graph_crop(
        DAC_FREQ,
        w_sample,
        "C0",
        "DAC waveform {} samples{}, {} Msps".format(
            DAC_SAMPLES,
            " (crop {}-{})".format(CROP_PLOT[0], CROP_PLOT[1]),
            DAC_FREQ),
        "bram_send_crop.png"
    )

    print("- FFT DAC")
    plot_graph_fft(
        DAC_FREQ,
        w_sample,
        "C0",
        "DAC FFT, {} samples, {} Msps".format(DAC_SAMPLES, DAC_FREQ),
        "bram_send_fft.png"
    )    

    for ch in range(2):
        print("- entire ADC Ch.{}".format(ch))
        plot_graph_entire_iq(
            ADC_FREQ,
            r_sample[ch],
            1,
            "C{}".format(ch + 1),
            "ADC waveform {} samples, {} Msps".format(ADC_SAMPLES, ADC_FREQ),
            "bram_recv_{}.png".format(ch)
        )

        print("- crop ADC Ch.{}".format(ch))
        plot_graph_crop_iq(
            ADC_FREQ,
            r_sample[ch],
            "C{}".format(ch + 1),
            "ADC waveform {} samples{}, {} Msps".format(
                ADC_SAMPLES,
                " (crop {}-{})".format(CROP_PLOT[0], CROP_PLOT[1]),
                ADC_FREQ),
            "bram_recv_{}_crop.png".format(ch)
        )

        print("- FFT ADC Ch.{}".format(ch))
        plot_graph_fft_iq(
            ADC_FREQ,
            r_sample[ch],
            "C{}".format(ch + 1),
            "ADC FFT {} samples, {} Msps".format(ADC_SAMPLES, ADC_FREQ),
            "bram_recv_{}_fft.png".format(ch)
        )
    print("Done.")
    return


if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    handler = logging.StreamHandler()
    handler.setLevel(LOG_LEVEL)
    logger.setLevel(LOG_LEVEL)
    logger.addHandler(handler)

    main()
