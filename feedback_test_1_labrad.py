#!/usr/bin/env python3
# coding: utf-8

"""
rftoolクライアント サンプルプログラム:
    BRAM フィードバック 1Kサンプル ADC/DAC 動作テスト 2.048 GSPS (LabRADサーバ接続)

<使用ライブラリ>
    numpy
    matplotlib
    pylabrad

<使用DACアナログ出力>
    DAC229_T1_CH2 (Tile 1 Block 2)
    DAC229_T1_CH3 (Tile 1 Block 3)

<使用ADCアナログ入力>
    ADC224_T0_CH0 (Tile 0 Block 0)
    ADC224_T0_CH1 (Tile 0 Block 1)
"""


from RftoolClient import client, rfterr, wavegen, ndarrayutil
import os
import time
import logging
import labrad
import numpy as np
try:
    import matplotlib
    matplotlib.use("Agg")
    matplotlib.rcParams["agg.path.chunksize"] = 20000
finally:
    import matplotlib.pyplot as plt

# Parameters
LABRAD_HOST = "localhost"
DAC_SAMPLES = 1024
ADC_SAMPLES = 1024
PLOT_DIR = "plot_feedback_test_1/"

# Constants
BITSTREAM = 4  # BRAM Feedback design
BITSTREAM_LOAD_TIMEOUT = 10
DAC_FREQ = 2048.0
ADC_FREQ = 2048.0
TRIG_BUSY_TIMEOUT = 5
LOG_LEVEL = logging.INFO
BLOCK_SIZE = 2048


def plot_graph(freq, sample, color, title, filename):
    time = np.linspace(0., len(sample) / freq, len(sample), endpoint=False)
    fig = plt.figure(figsize=(8, 6), dpi=300)
    plt.xlabel("Time [us]")
    plt.title(title)
    plt.plot(time, sample, linewidth=0.8, color=color)
    plt.savefig(PLOT_DIR + filename)
    plt.close()
    return


def wait_trig_done(rft):
    for i in range(TRIG_BUSY_TIMEOUT):
        if rft.gettriggerstatus() == 0:
            break
        time.sleep(1.)
    else:
        raise("Trigger busy timed out.")
    return


def config_bitstream(rft, num_design):
    if rft.getbitstream() != num_design:
        rft.setbitstream(num_design)
        for i in range(BITSTREAM_LOAD_TIMEOUT):
            time.sleep(2.)
            if rft.getbitstreamstatus() == 1:
                break
            if i > BITSTREAM_LOAD_TIMEOUT:
                raise Exception(
                    "Failed to configure bitstream, please reboot ZCU111.")
    return


def check_intr_flags(rft, type, ch):
    if type == 0:  # ADC
        tile = int(ch / 2)
        block = ch % 2
    elif type == 1:  # DAC
        tile = int(ch / 4)
        block = ch % 4
    flags = rft.getintrstatus(type, tile, block)[3]
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


def writedatatomemory_w(rft, type, ch, size, data):
    pos = 0
    rft.writedatatomemory_setsize(size)
    while pos < size:
        rft.writedatatomemory_setdata(data[pos:pos+BLOCK_SIZE])
        pos += BLOCK_SIZE
        if pos % (BLOCK_SIZE*512) == 0:
            print("... sent {}bytes".format(pos))
    print("total sent {}bytes".format(pos))
    rft.writedatatomemory_exec(type, ch)
    return


def readdatafrommemory_w(rft, type, ch, size):
    pos = 0
    data = bytearray(size)
    rft.readdatafrommemory_setsize(size)
    rft.readdatafrommemory_exec(type, ch)
    while pos < size:
        data[pos:pos+BLOCK_SIZE] = rft.readdatafrommemory_getdata(BLOCK_SIZE)
        pos += BLOCK_SIZE
        if pos % (BLOCK_SIZE*512) == 0:
            print("... received {}bytes".format(pos))
    print("total received {}bytes".format(pos))
    return bytes(data)


def main():
    print("Connect to LabRAD manager.")
    cxn = labrad.connect(LABRAD_HOST)
    rft = cxn.zcu111_rftool_labrad_server

    wgen = wavegen.WaveGen(logger=logger)
    nu = ndarrayutil.NdarrayUtil

    print("Generate waveform data.")
    wgen.set_parameter(num_sample=DAC_SAMPLES, dac_freq=DAC_FREQ,
                       carrier_freq=20.0, amplitude=-30000.0)
    w_data = wgen.sinwave()

    w_size = len(w_data)  # for 16-bit signed integer
    r_size = ADC_SAMPLES * 2  # for 16-bit signed integer

    mac_comp_coeff = np.array([-1, 0, 1], dtype="<i4")  # MAC result comparation coefficients
    mac_comp_coeff_b = nu.real_to_bytes_32(mac_comp_coeff)

    dac_trig_params = np.array([0, DAC_SAMPLES/8] * 16, dtype="<i4")  # start of word:0, num of word:DAC_SAMPLES/8
    dac_trig_params_b = nu.real_to_bytes_32(dac_trig_params)

    rft.termmode(0)

    print("Configure Bitstream.")
    config_bitstream(rft, BITSTREAM)

    print("Setup ADC.")
    for tile in [0, 1, 2, 3]:
        for block in [0, 1]:
            rft.setmixersettings(0, tile, block, 0.0, 0.0,
                2, 2, 0, 3, 0)
            rft.resetncophase(0, tile, block)
            rft.updateevent(0, tile, block, 1)
        rft.setupfifo(0, tile, 0)
        for block in [0, 1]:
            rft.setdither(tile, block, 1 if ADC_FREQ > 3000. else 0)
            rft.setdecimationfactor(tile, block, 1)
        rft.setfabclkoutdiv(0, tile, 2)
        for block in [0, 1]:
            rft.intrclr(0, tile, block, -1)
        rft.setupfifo(0, tile, 1)

    print("Setup DAC.")
    for tile in [0, 1]:
        for block in [0, 1, 2, 3]:
            rft.setmixersettings(1, tile, block, 0.0, 0.0,
                2, 1, 16, 4, 0)
            rft.resetncophase(1, tile, block)
            rft.updateevent(1, tile, block, 1)
        rft.setupfifo(1, tile, 0)
        for block in [0, 1, 2, 3]:
            rft.setinterpolationfactor(tile, block, 1)
        rft.setfabclkoutdiv(1, tile, 1)
        for block in [0, 1, 2, 3]:
            rft.intrclr(1, tile, block, -1)
        rft.setupfifo(1, tile, 1)

    print("Clear BlockRAM.")
    rft.clearbram()

    # Write waveform data to DAC channel 0, 1 (Tile 1 Block 2, 3) BRAM region
    for ch in [0, 1]:
        print("Send waveform data to Feedback system Ch.{} DAC BlockRAM".format(ch))
        writedatatomemory_w(rft, 1, ch, w_size, w_data)

    # Write MAC result comparation coefficients for ADC channel 0 I part, 0 Q part, 1 I part, 1 Q part
    for ch in [0, 1, 2, 3]:
        print("Send waveform data to Feedback system Ch.{} MAC result comparation coefficients.".format(ch))
        writedatatomemory_w(rft,
            4, ch, len(mac_comp_coeff_b), mac_comp_coeff_b)

    print("Send waveform data to Feedback system Ch.{} DAC trigger parameters.".format(0))
    writedatatomemory_w(rft,
        5, 0, len(dac_trig_params_b), dac_trig_params_b)
    print("Send waveform data to Feedback system Ch.{} DAC trigger parameters.".format(1))
    writedatatomemory_w(rft,
        5, 1, len(dac_trig_params_b), dac_trig_params_b)

    print("Setting trigger information.")
    rft.settriggerinfo(
        0, 0x03, ADC_SAMPLES, 0)  # enable ADC channel 0(Tile 0 Block 0), channel 1(Tile 0 Block 1)
                                  # to trigger DAC channel 0(Tile 1 Block 2), channel 1(Tile 1 Block 3)
    rft.settriggerlatency(0, 66)  # ADC trigger latency (approx. 0.22us = 66/300MHz)
    rft.setmacconfig(0x00, 0xFF)  # all ADC channels is 16-bit format
                                          # force trigger all DACs regardless of MAC overrange
    rft.settriggercycle(32768, 1)  # trigger 32768 times

    print("Start trigger.")
    rft.starttrigger()

    wait_trig_done(rft)

    time.sleep(1.)

    print("Setting trigger information.")
    rft.settriggercycle(3, 1)  # trigger 3 times

    print("Start trigger.")
    rft.starttrigger()

    wait_trig_done(rft)

    # Read I(Real) data from ADC Tile 0 Block 0, 1 RAM region
    r_data = []
    for ch in [0, 2]:
        print("Receive waveform data from Feedback system Ch.{} ADC capture BlockRAM".format(ch))
        r_data.append(readdatafrommemory_w(rft, 0, ch, r_size))

    print("Check interrupt flags.")
    for ch in range(8):  # ADC
        check_intr_flags(rft, 0, ch)
    for ch in range(8):  # DAC
        check_intr_flags(rft, 1, ch)

    print("Processing sample data.")
    print("- DAC sample data")
    w_sample = nu.bytes_to_real(w_data)
    del w_data
    print("- ADC sample data")
    r_sample = [nu.bytes_to_real(r_data[ch]) for ch in [0, 1]]
    del r_data

    print("Generating graph image.")
    os.makedirs(PLOT_DIR, exist_ok=True)

    print("- DAC waveform")
    plot_graph(
        DAC_FREQ,
        w_sample,
        "C0",
        "DAC waveform {} samples, {} Msps".format(DAC_SAMPLES, DAC_FREQ),
        "bram_send.png"
    )

    for ch in range(2):
        print("- ADC waveform Ch. {}".format(ch))
        plot_graph(
            ADC_FREQ,
            r_sample[ch],
            "C{}".format(ch + 1),
            "ADC waveform {} samples, {} Msps".format(ADC_SAMPLES, ADC_FREQ),
            "bram_recv_{}.png".format(ch)
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
