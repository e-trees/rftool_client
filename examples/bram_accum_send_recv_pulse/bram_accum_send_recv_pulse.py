#!/usr/bin/env python3
# coding: utf-8

"""
ADC積算のCDCの影響をテストするためのプログラム

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

import os
import sys
import time
import logging
import numpy as np
import pathlib
from scipy import fftpack
from scipy.signal import find_peaks
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
ZCU111_IP_ADDR = os.environ.get('ZCU111_IP_ADDR', "192.168.1.3")
DAC_SAMPLES = 32768  # DAC num of samples
ADC_SAMPLES = 32768  # ADC num of samples
DUC_DDC_FACTOR = 1  # ADC decimation / DAC interpolation factor (1, 2, 4, 8)
PLOT_DIVIDES = 128
CROP_PLOT = [0, 128]  # crop samples for plot
FFT_SIZE = 8192
PLOT_DIR = "plot_bram_accum_send_recv_pulse/"

# Log level
LOG_LEVEL = logging.INFO

# Constants
BITSTREAM = 3  # BRAM 8ch ADC / 8ch DAC 32K samples with accumualtion
BITSTREAM_LOAD_TIMEOUT = 10
DAC_FREQ = 2048.0
ADC_FREQ = 2048.0
TRIG_BUSY_TIMEOUT = 100
CHUNK_DAC_PLOT = int(DAC_SAMPLES / PLOT_DIVIDES)
CHUNK_ADC_PLOT = int(ADC_SAMPLES / PLOT_DIVIDES)


def calculate_min_max(sample, chunks):
    sample_rs = np.reshape(sample, (-1, chunks))
    sample_min = np.amin(sample_rs, axis=1)
    sample_max = np.amax(sample_rs, axis=1)
    return sample_min, sample_max


def plot_graph_entire(freq, sample, color, title, filename):
    time = np.linspace(
        0., len(sample) / freq, PLOT_DIVIDES, endpoint=False)
    sample_min, sample_max = calculate_min_max(sample, CHUNK_DAC_PLOT)
    fig = plt.figure(figsize=(8, 6), dpi=300)
    plt.xlabel("Time [us]")
    plt.title(title)
    plt.plot(time, sample_min, linewidth=0.8, color=color)
    plt.plot(time, sample_max, linewidth=0.8, color=color)
    plt.fill_between(time, sample_min, sample_max, alpha=0.5, color=color)
    plt.savefig(filename)
    plt.close()
    return


def plot_graph_crop(freq, sample, color, title, filename):
    sample_crop = sample[CROP_PLOT[0]:CROP_PLOT[1]]
    peaks, _ = find_peaks(sample_crop, width=7)
    sum_peaks = np.sum([sample_crop[peaks]])
    perc = 100. * np.array([sample_crop[peaks]]) / sum_peaks

    len_crop = CROP_PLOT[1] - CROP_PLOT[0]
    time = np.linspace(
        CROP_PLOT[0] / freq, CROP_PLOT[1] / freq, len_crop, endpoint=False) * 1000.
    fig = plt.figure(figsize=(8, 6), dpi=300)
    plt.xlabel("Time [ns]")
    plt.title(title)
    plt.plot(time, sample_crop,
        linewidth=0.8, color=color)

    i = 0
    for p in peaks:
        plt.text(time[p], sample_crop[p], "{}\n{:.1f}%".format(sample_crop[p], perc[0][i]), horizontalalignment='center', verticalalignment='center', fontsize=10)
        i = i + 1
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
        details.append("RFDC FIFO marginal overflow detected.")
    if (flags & 0x00000008):
        details.append("RFDC FIFO marginal underflow detected.")
    for d in details:
        print(" - " + d)
    return


def main(num_trig):
    wgen = wavegen.WaveGen(logger=logger)
    nu = ndarrayutil.NdarrayUtil

    print("Generate waveform data.")
    wgen.set_parameter(num_sample=DAC_SAMPLES, dac_freq=DAC_FREQ,
                       carrier_freq=20., amplitude=30000.0)
    # sin_wave = nu.bytes_to_real(wgen.sinwave())
    #
    # amplitude = np.linspace(-1., 1., DAC_SAMPLES, endpoint=False)
    #
    # w_data = (sin_wave * amplitude).reshape(1, -1)[0].astype("<i2").tobytes()

    # del sin_wave, amplitude

    # w_data = wgen.pulsewave()
    w_sample = np.zeros(DAC_SAMPLES).astype('<i2')
    w_sample[8:16] = -0x7FFF
    w_data = nu.real_to_bytes(w_sample)

    w_size = len(w_data)  # for 16bit signed integer
    r_size = ADC_SAMPLES * 4  # for 32bit signed integer

    with client.RftoolClient(logger=logger) as rft:
        print("Connect to RFTOOL Server.")
        rft.connect(ZCU111_IP_ADDR)
        rft.command.TermMode(0)

        print("Configure Bitstream.")
        config_bitstream(rft.command, BITSTREAM)

        print("Setup ADC.")
        for tile in [0, 1, 2, 3]:
            for block in [0, 1]:
                rft.command.SetMixerSettings(0, tile, block, 0.0, 0.0,
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
                rft.command.SetMixerSettings(1, tile, block, 0.0, 0.0,
                    2, 1, 16, 4, 0)
                rft.command.ResetNCOPhase(1, tile, block)
                rft.command.UpdateEvent(1, tile, block, 1)
            rft.command.SetupFIFO(1, tile, 0)
            for block in [0, 1, 2, 3]:
                rft.command.SetInterpolationFactor(tile, block, DUC_DDC_FACTOR)
            rft.command.SetFabClkOutDiv(1, tile, 2 + int(np.log2(DUC_DDC_FACTOR)))
            for block in [0, 1, 2, 3]:
                rft.command.IntrClr(1, tile, block, 0xFFFFFFFF)
            rft.command.SetupFIFO(1, tile, 1)

        print("Clear BlockRAM.")
        rft.command.ClearBRAM()

        for ch in [6, 7]:
            print("Send waveform data to DAC Ch.{} BlockRAM".format(ch))
            rft.if_data.WriteDataToMemory(1, ch, w_size, w_data)

        print("Setting trigger information.")
        rft.command.SetTriggerInfo(0, 0xFF, ADC_SAMPLES, 0)
        rft.command.SetTriggerInfo(1, 0xFF, DAC_SAMPLES, 0)
        rft.command.SetTriggerLatency(0, 90)
        rft.command.SetTriggerLatency(1, 0)
        rft.command.SetTriggerCycle(32768, 1)  # trigger 32768 times
        rft.command.SetAccumulateMode(0)  # disable accumulation

        print("Start trigger.")
        rft.command.StartTrigger()  # for ADC calibration

        wait_trig_done(rft.command)

        print("Setting trigger information.")
        rft.command.SetTriggerCycle(num_trig, 100000)
        rft.command.SetAccumulateMode(1)  # enable accumulation

        print("Clear BlockRAM.")
        rft.command.ClearBRAM()

        for ch in [6, 7]:
            print("Send waveform data to DAC Ch.{} BlockRAM".format(ch))
            rft.if_data.WriteDataToMemory(1, ch, w_size, w_data)

        print("Start trigger.")
        rft.command.StartTrigger()  # for ADC accumualtion

        wait_trig_done(rft.command)

        r_data = []
        for ch in [0, 1]:
            print("Receive waveform data from ADC Ch.{} BlockRAM".format(ch))
            r_data.append(rft.if_data.ReadDataFromMemory(0, ch, r_size))

        print("Check interrupt flags.")
        for ch in range(8):  # ADC
            check_intr_flags(rft.command, 0, ch)
        for ch in range(8):  # DAC
            check_intr_flags(rft.command, 1, ch)

    print("Processing sample data.")
    print("- DAC sample data")
    w_sample = nu.bytes_to_real(w_data)
    del w_data
    print("- ADC sample data")
    r_sample = np.array([nu.bytes_to_real_32(rd) for rd in r_data])
    del r_data

    print("Generating graph image.")
    os.makedirs(PLOT_DIR + str(num_trig) + "/", exist_ok=True)

    # print("- entire DAC")
    # plot_graph_entire(
    #     DAC_FREQ,
    #     w_sample,
    #     "C0",
    #     "DAC waveform {} samples, {} Msps".format(DAC_SAMPLES, DAC_FREQ),
    #     PLOT_DIR + str(num_trig) + "/bram_send.png"
    # )
    #
    print("- crop DAC")
    plot_graph_crop(
        DAC_FREQ,
        w_sample,
        "C0",
        "DAC waveform {} samples{}, {} Msps".format(
            DAC_SAMPLES,
            " (crop {}-{})".format(CROP_PLOT[0], CROP_PLOT[1]),
            DAC_FREQ),
        PLOT_DIR + str(num_trig) + "/bram_send_crop.png"
    )
    #
    # print("- FFT DAC")
    # plot_graph_fft(
    #     DAC_FREQ,
    #     w_sample,
    #     "C0",
    #     "DAC FFT, {} samples, {} Msps".format(DAC_SAMPLES, DAC_FREQ),
    #     PLOT_DIR + str(num_trig) + "/bram_send_fft.png"
    # )

    for ch in [0, 1]:
        # print("- entire ADC Ch.{}".format(ch))
        # plot_graph_entire(
        #     ADC_FREQ,
        #     r_sample[ch],
        #     "C{}".format(ch + 1),
        #     "ADC waveform {} samples, {} Msps({} times accum.)".format(ADC_SAMPLES, ADC_FREQ, str(num_trig)),
        #     PLOT_DIR + str(num_trig) + "/bram_recv_{}.png".format(ch)
        # )

        print("- crop ADC Ch.{}".format(ch))
        plot_graph_crop(
            ADC_FREQ,
            r_sample[ch],
            "C{}".format(ch + 1),
            "ADC waveform {} samples{}, {} Msps({} times accum.)".format(
                ADC_SAMPLES,
                " (crop {}-{})".format(CROP_PLOT[0], CROP_PLOT[1]),
                ADC_FREQ, str(num_trig)),
            PLOT_DIR + str(num_trig) + "/bram_recv_{}_crop.png".format(ch)
        )

        # print("- FFT ADC Ch.{}".format(ch))
        # plot_graph_fft(
        #     ADC_FREQ,
        #     r_sample[ch],
        #     "C{}".format(ch + 1),
        #     "ADC FFT {} samples, {} Msps({} times accum.)".format(ADC_SAMPLES, ADC_FREQ, str(num_trig)),
        #     PLOT_DIR + str(num_trig) + "/bram_recv_{}_fft.png".format(ch)
        # )

    print("Done.")
    return


if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    handler = logging.StreamHandler()
    handler.setLevel(LOG_LEVEL)
    logger.setLevel(LOG_LEVEL)
    logger.addHandler(handler)

    try:
        num_trig = sys.argv[1]
    except Exception:
        num_trig = 32

    main(num_trig)
