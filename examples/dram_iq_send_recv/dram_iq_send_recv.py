#!/usr/bin/env python3
# coding: utf-8

"""
rftoolクライアント サンプルプログラム:
    DRAM 2ch DAC/2ch ADC 動作テスト 2.048 GSPS I/Q変復調モード

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

# Parameters
ZCU111_IP_ADDR = "192.168.1.3"
DAC_SAMPLES = 32 * 1024 * 1024
ADC_SAMPLES = 32 * 1024 * 1024
NCO_FREQ = 512.0  # Mixer NCO frequency [MHz]
NCO_PHASE = 0.0  # Mixer NCO phase [deg]
DATA_DEVIDES = 2 * 1024
PLOT_DIVIDES = 2 * 1024
CROP_PLOT = [0, 512]
FFT_SIZE = 32768
PLOT_DIR = "plot_dram_iq_send_recv/"

# Log level
LOG_LEVEL = logging.INFO

# Constants
BITSTREAM = 2  # DRAM 2ch ADC / 2ch DAC 512M samples
BITSTREAM_LOAD_TIMEOUT = 10
DAC_FREQ = 2048.0
ADC_FREQ = 2048.0
DUC_DDC_FACTOR = 2  # ADC decimation / DAC interpolation factor
EFF_DAC_FREQ = DAC_FREQ / DUC_DDC_FACTOR
EFF_ADC_FREQ = ADC_FREQ / DUC_DDC_FACTOR
CHUNK_SAMPLES = int(DAC_SAMPLES / DATA_DEVIDES)
CHUNK_DAC_PLOT = int(DAC_SAMPLES / PLOT_DIVIDES)
CHUNK_ADC_PLOT = int(ADC_SAMPLES / PLOT_DIVIDES)


def calculate_min_max(sample, chunks):
    sample_rs = np.reshape(sample, (-1, chunks))
    sample_min = np.amin(sample_rs, axis=1)
    sample_max = np.amax(sample_rs, axis=1)
    return sample_min, sample_max


def plot_graph_entire(freq, sample, color, title, filename):
    time = np.linspace(
        0., len(sample) / freq, PLOT_DIVIDES, endpoint=False) / 1000.
    sample_min_i, sample_max_i = calculate_min_max(sample.real, CHUNK_DAC_PLOT)
    sample_min_q, sample_max_q = calculate_min_max(sample.imag, CHUNK_DAC_PLOT)
    fig = plt.figure(figsize=(8, 6), dpi=300)
    ax1 = fig.add_subplot(2, 1, 1)
    plt.title(title)
    ax1.set_ylabel("Real part")
    ax1.plot(time, sample_min_i, linewidth=0.8, color=color)
    ax1.plot(time, sample_max_i, linewidth=0.8, color=color)
    ax1.fill_between(time, sample_min_i, sample_max_i, alpha=0.5, color=color)
    ax2 = fig.add_subplot(2, 1, 2)
    ax2.set_xlabel("Time [ms]")
    ax2.set_ylabel("Imaginary part")
    ax2.plot(time, sample_min_q, linewidth=0.8, color=color)
    ax2.plot(time, sample_max_q, linewidth=0.8, color=color)
    ax2.fill_between(time, sample_min_q, sample_max_q, alpha=0.5, color=color)
    plt.savefig(PLOT_DIR + filename)
    plt.close()
    return


def plot_graph_crop(freq, sample, color, title, filename):
    len_crop = CROP_PLOT[1] - CROP_PLOT[0]
    time = np.linspace(
        CROP_PLOT[0] / freq, CROP_PLOT[1] / freq, len_crop, endpoint=False)
    fig = plt.figure(figsize=(8, 6), dpi=300)
    ax1 = fig.add_subplot(2, 1, 1)
    plt.title(title)
    ax1.set_ylabel("Real part")
    ax1.plot(time, sample[CROP_PLOT[0]:CROP_PLOT[1]].real,
        linewidth=0.8, color=color)
    ax2 = fig.add_subplot(2, 1, 2)
    ax2.set_xlabel("Time [ms]")
    ax2.set_ylabel("Imaginary part")
    ax2.plot(time, sample[CROP_PLOT[0]:CROP_PLOT[1]].imag,
        linewidth=0.8, color=color)
    plt.savefig(PLOT_DIR + filename)
    plt.close()
    return
    return


def plot_graph_fft(freq, sample, color, title, filename):
    fft_freq = np.fft.fftfreq(FFT_SIZE, d=1./(freq*1.e6))[0:int(FFT_SIZE/2)]
    fft_data_i = np.zeros(int(FFT_SIZE/2))
    for i in range(int(len(sample)/FFT_SIZE)):
        fft_cur = abs(
            fftpack.fft(sample[FFT_SIZE*i:FFT_SIZE*(i+1)].real))[0:int(FFT_SIZE/2)]
        fft_data_i = np.max([fft_data_i, fft_cur], axis=0)
    fft_data_q = np.zeros(int(FFT_SIZE/2))
    for i in range(int(len(sample)/FFT_SIZE)):
        fft_cur = abs(
            fftpack.fft(sample[FFT_SIZE*i:FFT_SIZE*(i+1)].imag))[0:int(FFT_SIZE/2)]
        fft_data_q = np.max([fft_data_q, fft_cur], axis=0)

    fig = plt.figure(figsize=(8, 6), dpi=300)
    ax1 = fig.add_subplot(2, 1, 1)
    plt.title(title)
    ax1.set_yscale("log")
    ax1.set_xscale("log")
    ax1.grid(which="both")
    ax1.grid(which="major", alpha=0.5)
    ax1.grid(which="minor", alpha=0.2)
    ax1.set_ylabel("Real part")
    ax1.plot(fft_freq, fft_data_i, linewidth=0.8, color=color)
    ax2 = fig.add_subplot(2, 1, 2)
    ax2.set_yscale("log")
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
    if type == 0:  # ADC
        tile = int(ch / 2)
        block = ch % 2
    elif type == 1:  # DAC
        tile = int(ch / 4)
        block = ch % 4
    flags = rftcmd.GetIntrStatus(type, tile, block)[3]
    if flags == 0:
        return
    else:
        print("# WARNING: An interrupt flag was asserted in {} Ch.{} (Tile:{} Block:{}).".format(
            "ADC" if type == 0 else "DAC", ch, tile, block))
    details = []
    if (flags & 0x40000000):
        details.append("Datapath interrupt asserted.")
    if (flags & 0x000003F0):
        details.append("Overflow detected in {} stage datapath.".format(
            "ADC Decimation" if type == 0 else "DAC Interpolation"))
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


def main():
    nu = ndarrayutil.NdarrayUtil

    print("Generating waveform data.")
    r_cycles = np.round(CHUNK_SAMPLES * 20.0 / EFF_DAC_FREQ)  # aprox. 20 MHz
    omega = 2. * np.pi * np.linspace(0., r_cycles, CHUNK_SAMPLES, endpoint=False)
    amplitude = np.linspace(-20000., 20000., DATA_DEVIDES, endpoint=False)
    sin_wave = np.sin(omega)
    cos_wave = np.cos(omega)
    interleaved_wave = np.array([sin_wave, cos_wave]).T.reshape(1, -1)

    w_data = np.multiply(
        interleaved_wave, np.array([amplitude]).T).reshape(1, -1)[0].astype("<i2").tobytes()

    del r_cycles, sin_wave, cos_wave, amplitude, interleaved_wave

    w_size = len(w_data)
    r_size = ADC_SAMPLES * 4

    with client.RftoolClient(logger=logger) as rft:
        print("Connect to RFTOOL Server.")
        rft.connect(ZCU111_IP_ADDR)
        rft.command.TermMode(0)

        print("Configure Bitstream.")
        config_bitstream(rft.command, BITSTREAM)

        print("Setup ADC.")
        for tile in [0, 1, 2, 3]:
            for block in [0, 1]:
                rft.command.SetMixerSettings(0, tile, block, NCO_FREQ, NCO_PHASE,
                    2, 2, 0, 3, 0)
                rft.command.ResetNCOPhase(0, tile, block)
                rft.command.UpdateEvent(0, tile, block, 1)
            rft.command.SetupFIFO(0, tile, 0)
            for block in [0, 1]:
                rft.command.SetDither(tile, block, 1 if ADC_FREQ > 3000. else 0)
                rft.command.SetDecimationFactor(tile, block, DUC_DDC_FACTOR)
            rft.command.SetFabClkOutDiv(0, tile, 2 + int(np.log2(DUC_DDC_FACTOR)))
            for block in [0, 1]:
                rft.command.IntrClr(0, tile, block, 0xFFFFFFFF)
            rft.command.SetupFIFO(0, tile, 1)

        print("Setup DAC.")
        for tile in [0, 1]:
            for block in [0, 1, 2, 3]:
                rft.command.SetMixerSettings(1, tile, block, NCO_FREQ, NCO_PHASE,
                    2, 2, 0, 2, 0)
                rft.command.ResetNCOPhase(1, tile, block)
                rft.command.UpdateEvent(1, tile, block, 1)
            rft.command.SetupFIFO(1, tile, 0)
            for block in [0, 1, 2, 3]:
                rft.command.SetInterpolationFactor(tile, block, DUC_DDC_FACTOR)
            rft.command.SetFabClkOutDiv(1, tile, 1 + int(np.log2(DUC_DDC_FACTOR)))
            for block in [0, 1, 2, 3]:
                rft.command.IntrClr(1, tile, block, 0xFFFFFFFF)
            rft.command.SetupFIFO(1, tile, 1)

        for ch in [6, 7]:
            print("Send waveform data to DAC Ch.{} DynamicRAM".format(ch))
            rft.if_data.WriteDataToMemory(1, ch, w_size, w_data)

        print("Setting trigger information.")
        rft.command.SetTriggerInfo(1, 0xC0, DAC_SAMPLES, 1)
        rft.command.SetTriggerInfo(0, 0x03, ADC_SAMPLES, 1)
        rft.command.SetTriggerLatency(1, 0)
        rft.command.SetTriggerLatency(0, 40)

        print("Start trigger.")
        rft.command.StartTrigger()

        print("Receive waveform data from ADC Ch.{} DynamicRAM".format(0))
        r_data_0 = rft.if_data.ReadDataFromMemory(0, 0, r_size)
        print("Receive waveform data from ADC Ch.{} DynamicRAM".format(1))
        r_data_1 = rft.if_data.ReadDataFromMemory(0, 1, r_size)

        print("Check interrupt flags.")
        for ch in range(8):  # ADC
            check_intr_flags(rft.command, 0, ch)
        for ch in range(8):  # DAC
            check_intr_flags(rft.command, 1, ch)

    print("Processing sample data.")
    print("- DAC sample data")
    w_sample = nu.bytes_to_complex(w_data)
    del w_data
    print("- ADC sample data")
    r_sample = [nu.bytes_to_complex(r_data_0), nu.bytes_to_complex(r_data_1)]
    del r_data_0, r_data_1

    print("Generating graph image.")
    os.makedirs(PLOT_DIR, exist_ok=True)

    print("- entire DAC")
    plot_graph_entire(
        EFF_DAC_FREQ,
        w_sample,
        "C0",
        "DAC waveform {} samples, {} Msps".format(DAC_SAMPLES, DAC_FREQ),
        "dram_iq_send.png"
    )

    print("- crop DAC")
    plot_graph_crop(
        EFF_DAC_FREQ,
        w_sample,
        "C0",
        "DAC waveform {} samples{}, {} Msps".format(
            DAC_SAMPLES,
            " (crop {}-{})".format(CROP_PLOT[0], CROP_PLOT[1]),
            DAC_FREQ),
        "dram_iq_send_crop.png"
    )

    print("- FFT DAC")
    plot_graph_fft(
        EFF_DAC_FREQ,
        w_sample,
        "C0",
        "DAC FFT (size:{} peak-holded), {} samples, {} Msps({}x DUC)".format(
            FFT_SIZE, DAC_SAMPLES, DAC_FREQ, DUC_DDC_FACTOR),
        "dram_iq_send_fft.png"
    )

    for ch in range(2):
        print("- entire ADC Ch.{}".format(ch))
        plot_graph_entire(
            EFF_ADC_FREQ,
            r_sample[ch],
            "C{}".format(ch + 1),
            "ADC waveform {} samples, {} Msps({}x DDC)".format(ADC_SAMPLES, ADC_FREQ, DUC_DDC_FACTOR),
            "dram_iq_recv_{}.png".format(ch)
        )

        print("- crop ADC Ch.{}".format(ch))
        plot_graph_crop(
            EFF_ADC_FREQ,
            r_sample[ch],
            "C{}".format(ch + 1),
            "ADC waveform {} samples{}, {} Msps({}x DDC)".format(
                ADC_SAMPLES,
                " (crop {}-{})".format(CROP_PLOT[0], CROP_PLOT[1]),
                ADC_FREQ, DUC_DDC_FACTOR),
            "dram_iq_recv_{}_crop.png".format(ch)
        )

        print("- FFT ADC Ch.{}".format(ch))
        plot_graph_fft(
            EFF_ADC_FREQ,
            r_sample[ch],
            "C{}".format(ch + 1),
            "ADC FFT (size:{} peak-holded), {} samples, {} Msps({}x DDC)".format(
                FFT_SIZE, ADC_SAMPLES, ADC_FREQ, DUC_DDC_FACTOR),
            "dram_iq_recv_{}_fft.png".format(ch)
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
