#!/usr/bin/env python3
# coding: utf-8

"""
rftoolクライアント サンプルプログラム:
    BRAM フィードバック 1Kサンプル ADC/DAC セルフテスト 2.048 GSPS

<使用ライブラリ>
    numpy
    matplotlib

<使用DACアナログ出力>
    DAC229_T1_CH2 (Tile 1 Block 2)
    DAC229_T1_CH3 (Tile 1 Block 3)

<使用ADCアナログ入力>
    ADC224_T0_CH0 (Tile 0 Block 0)
    ADC224_T0_CH1 (Tile 0 Block 1)
"""


from RftoolClient import client, rfterr, wavegen, ndarrayutil
import os
import sys
import time
import logging
import numpy as np
try:
    import matplotlib
    matplotlib.use("Agg")
    matplotlib.rcParams["agg.path.chunksize"] = 20000
finally:
    import matplotlib.pyplot as plt


class SelfTestFault(Exception):
    pass

# Parameters
ZCU111_IP_ADDR = "192.168.1.3"
PLOT_DIR = "plot_feedback_test_2/"

# Test channels
CH_TEST_MAC = 0  # channel test for ADC MAC / DAC Waveform pattern selector
CH_AWG_CAP = 1  # channel use for DAC AWG / ADC capture

# Constants
BITSTREAM = 4  # BRAM Feedback design
BITSTREAM_LOAD_TIMEOUT = 10
DAC_FREQ = 2048.0
ADC_FREQ = 2048.0
TRIG_BUSY_TIMEOUT = 5
ADC_SAMPLES = 1024
DAC_SAMPLES = 768
LOG_LEVEL = logging.WARN
ERR_THRESHOLD = 200000.


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


def check_adc_overvoltage(adc_intr_flags, channel):
    if ((adc_intr_flags >> 26) & 0x3) != 0x0:
        print("\r\nWARNING: ADC Ch:{} input overvoltage detected.\r\n".format(channel))


def check_low_input_signal(sample_array, num_channel, threshold=100.):
    if (np.max(sample_array) < threshold) & (np.min(sample_array) > -threshold):
        print("\r\nWARNING: ADC Ch:{} low input signal.\r\n".format(num_channel))


def check_mac_overrange(ovr_range, channel):
    if (ovr_range >> channel) & 0x1 == 0x1:
        print("\r\nWARNING: ADC Ch:{} MAC overrange detected.\r\n".format(channel))


def main():
    wgen = wavegen.WaveGen(logger=logger)
    nu = ndarrayutil.NdarrayUtil

    print("Generate waveform data.")
    wgen.set_parameter(num_sample=DAC_SAMPLES, dac_freq=DAC_FREQ,
                       carrier_freq=10.67, amplitude=-30000.)
    sin_data = wgen.sinwave()
    pulse_data = wgen.pulsewave()
    tri_data = wgen.triwave()
    saw_data = wgen.sawwave()
    awg_data = sin_data
    mac_wav_data = sin_data + pulse_data + tri_data + saw_data
    adc_cap_len = ADC_SAMPLES * 2  # 16-bit signed integer
    dac_words = int(DAC_SAMPLES / 8)

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
                rft.command.SetDecimationFactor(tile, block, 1)
            rft.command.SetFabClkOutDiv(0, tile, 2)
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
                rft.command.SetInterpolationFactor(tile, block, 1)
            rft.command.SetFabClkOutDiv(1, tile, 1)
            for block in [0, 1, 2, 3]:
                rft.command.IntrClr(1, tile, block, 0xFFFFFFFF)
            rft.command.SetupFIFO(1, tile, 1)

        print("Clear BlockRAM.")
        rft.command.ClearBRAM()

        print("Send DAC AWG waveform data / parameters.")
        ## Write waveform data / trigger parameters for DAC AWG
        rft.if_data.WriteDataToMemory(1, CH_AWG_CAP, len(awg_data), awg_data)
        dac_awg_params = np.array([0, dac_words] * 16, dtype="<i4")
        dac_awg_params_b = nu.real_to_bytes_32(dac_awg_params)
        rft.if_data.WriteDataToMemory(
            5, CH_AWG_CAP, len(dac_awg_params_b), dac_awg_params_b)

        print("Send waveform data for DAC Waveform selector.")
        ## Write waveform data / trigger parameters for DAC Waveform selector
        # 4 patterns output
        rft.if_data.WriteDataToMemory(1, CH_TEST_MAC, len(mac_wav_data), mac_wav_data)

        print("Set trigger parameters.")
        # Set parameters for ADC/DAC-BRAM Bridge controller
        rft.command.SetTriggerInfo(
            0, ((0x1 << CH_TEST_MAC) | (0x1 << CH_AWG_CAP)), ADC_SAMPLES, 0)
        rft.command.SetTriggerLatency(0, 48)
        rft.command.SetTriggerCycle(32768*32, 1)
        rft.command.SetMACConfig(0xFF, 0x00)  # all ADC channels is 12-bit format
                                              # do not trigger all DACs when MAC is overrange

        print("Start Trigger.")
        rft.command.StartTrigger()

        wait_trig_done(rft.command)

        # Get RFDC ADC interrupt flags / overvoltage detection
        adc_test_ch_flags = rft.command.GetIntrStatus(
            0, (CH_TEST_MAC >> 1) & 0x3, CH_TEST_MAC & 0x1)[3]
        adc_cap_ch_flags = rft.command.GetIntrStatus(
            0, (CH_AWG_CAP >> 1) & 0x3, CH_AWG_CAP & 0x1)[3]
        check_adc_overvoltage(adc_test_ch_flags, CH_TEST_MAC)
        check_adc_overvoltage(adc_cap_ch_flags, CH_AWG_CAP)

        print("Receive ADC MAC channel capture data.")
        # Get ADC capture data of test channel
        adc_mac_capdata = rft.if_data.ReadDataFromMemory(
            0, CH_TEST_MAC*2, adc_cap_len)

        adc_awg_force_captures = []
        for sel_pattern in [0, 1, 2, 3]:
            print("Set force DAC Waveform selector output pattern {}".format(sel_pattern))
            dac_sel_params = np.array(
                [sel_pattern * dac_words, dac_words] * 16, dtype="<i4")
            dac_sel_params_b = nu.real_to_bytes_32(dac_sel_params)
            rft.if_data.WriteDataToMemory(
                5, CH_TEST_MAC, len(dac_sel_params_b), dac_sel_params_b)

            print("Start Trigger.")
            rft.command.StartTrigger()

            wait_trig_done(rft.command)

            # Get RFDC ADC interrupt flags / overvoltage detection
            adc_test_ch_flags = rft.command.GetIntrStatus(
                0, (CH_TEST_MAC >> 1) & 0x3, CH_TEST_MAC & 0x1)[3]
            check_adc_overvoltage(adc_test_ch_flags, CH_TEST_MAC)
            adc_cap_ch_flags = rft.command.GetIntrStatus(
                0, (CH_AWG_CAP >> 1) & 0x3, CH_AWG_CAP & 0x1)[3]
            check_adc_overvoltage(adc_cap_ch_flags, CH_AWG_CAP)

            print("Receive ADC capture data for DAC Waveform selector output.")
            adc_awg_capdata_force = rft.if_data.ReadDataFromMemory(
                0, CH_AWG_CAP*2, adc_cap_len)
            adc_awg_capsample_force = np.array(
                nu.bytes_to_real(adc_awg_capdata_force)) / 16
            check_low_input_signal(adc_awg_capsample_force, CH_AWG_CAP)
            adc_awg_force_captures.append(adc_awg_capsample_force)

    print("Disconnect from server.")

    adc_mac_capsample = np.array(
        nu.bytes_to_real(adc_mac_capdata)) / 16  # conv. 12-bit integer
    check_low_input_signal(adc_mac_capsample, CH_TEST_MAC)

    print("Prepare MAC multiplied coefficients for self-test.")

    require_mac_val = [-25165824, -8388608, 8388608, 25165824]
    mac_cap_sq_sum = np.dot(1. * adc_mac_capsample, adc_mac_capsample)
    multiplied_samples = [
        np.round((rq / mac_cap_sq_sum) * adc_mac_capsample).astype("<i4")
        for rq in require_mac_val]

    # print("mac_cap_sq_sum: {}".format(mac_cap_sq_sum))
    # print("require_mac_val / mac_cap_sq_sum = {}".format(np.array(require_mac_val) / mac_cap_sq_sum))
    print("MAC multiplied coefficients .max={0}, min={1}".format(np.max(multiplied_samples), np.min(multiplied_samples)))

    multiplied_data = [nu.real_to_bytes_32(smp) for smp in multiplied_samples]
    mac_comp_coeff = np.array([-16777216, 0, 16777216], dtype="<i4")
    mac_comp_coeff_b = nu.real_to_bytes_32(mac_comp_coeff)

    with client.RftoolClient(logger=logger) as rft:
        print("Re-connect to ZCU111 RFTOOL server.")
        rft.connect(ZCU111_IP_ADDR)
        rft.command.TermMode(0)

        # Clear all ADC interrupt flags
        for tile in [0, 1, 2, 3]:
            for block in [0, 1]:
                rft.command.IntrClr(0, tile, block, 0xFFFFFFFF)

        print("Send ADC MAC result comparation coefficient data.")
        ## Write comparation coefficients for ADC MAC
        rft.if_data.WriteDataToMemory(4, CH_TEST_MAC*2,
            len(mac_comp_coeff_b), mac_comp_coeff_b)

        print("Set DAC Waveform selector parameters.")
        dac_sel_params = np.array([
            0 * dac_words, dac_words,  # sine
            1 * dac_words, dac_words,  # pulse
            2 * dac_words, dac_words,  # triangle
            3 * dac_words, dac_words,  # sawtooth
        ] * 4, dtype="<i4")
        dac_sel_params_b = nu.real_to_bytes_32(dac_sel_params)
        rft.if_data.WriteDataToMemory(
            5, CH_TEST_MAC, len(dac_sel_params_b), dac_sel_params_b)

        rft.command.SetTriggerCycle(3, 1)

        adc_awg_result_captures = []
        adc_mac_actual_captures = []
        for sel_pattern in [0, 1, 2, 3]:
            print("Send ADC MAC multiplied coefficient data where DAC Waveform selector output to be pattern {}.".format(sel_pattern))
            ## Write Multiplied coefficients for ADC MAC
            rft.if_data.WriteDataToMemory(3, CH_TEST_MAC*2,
                len(multiplied_data[sel_pattern]), multiplied_data[sel_pattern])

            print("Start trigger BRAM Bridge controller.")
            rft.command.StartTrigger()

            wait_trig_done(rft.command)

            mac_ovrrange = rft.command.GetAccumulateOverrange()
            check_mac_overrange(mac_ovrrange, CH_TEST_MAC)

            # Get RFDC ADC interrupt flags / overvoltage detection
            adc_test_ch_flags = rft.command.GetIntrStatus(
                0, (CH_TEST_MAC >> 1) & 0x3, CH_TEST_MAC & 0x1)[3]
            check_adc_overvoltage(adc_test_ch_flags, CH_TEST_MAC)
            adc_cap_ch_flags = rft.command.GetIntrStatus(
                0, (CH_AWG_CAP >> 1) & 0x3, CH_AWG_CAP & 0x1)[3]
            check_adc_overvoltage(adc_cap_ch_flags, CH_AWG_CAP)

            print("Receive ADC capture data for DAC Waveform selector output validation.")
            # Get ADC capture data of test channel
            adc_awg_result_capdata = rft.if_data.ReadDataFromMemory(0, CH_AWG_CAP*2, adc_cap_len)
            adc_awg_result_capsample = np.array(
                nu.bytes_to_real(adc_awg_result_capdata)) / 16
            check_low_input_signal(adc_awg_result_capsample, CH_AWG_CAP)
            adc_awg_result_captures.append(adc_awg_result_capsample)

            print("Receive ADC MAC channel actual capture data.")
            # Get ADC capture data of test channel
            adc_mac_actual_capdata = rft.if_data.ReadDataFromMemory(
                0, CH_TEST_MAC*2, adc_cap_len)
            adc_mac_actual_capsample = np.array(
                nu.bytes_to_real(adc_mac_actual_capdata)) / 16
            check_low_input_signal(adc_mac_actual_capsample, CH_TEST_MAC)
            adc_mac_actual_captures.append(adc_mac_actual_capsample)

    print("Disconnect from server.")

    time_dac = np.linspace(0., DAC_SAMPLES / DAC_FREQ, DAC_SAMPLES, endpoint=False)  # us
    time_adc = np.linspace(0., ADC_SAMPLES / DAC_FREQ, ADC_SAMPLES, endpoint=False)  # us

    validation_res = False
    os.makedirs(PLOT_DIR, exist_ok=True)

    for sel_pattern in [0, 1, 2, 3]:
        print("Validation DAC Waveform selector output pattern {}".format(sel_pattern))
        expected_mac_result = np.dot(adc_mac_capsample, multiplied_samples[sel_pattern])
        print("    Expected MAC Result = {}".format(expected_mac_result))
        actual_mac_result = np.dot(adc_mac_actual_captures[sel_pattern], multiplied_samples[sel_pattern])
        print(" Actual last MAC Result = {}".format(actual_mac_result))
        adc_awg_error = np.abs(adc_awg_result_captures[sel_pattern] - adc_awg_force_captures[sel_pattern])
        adc_awg_error_sum = np.sum(adc_awg_error)
        print(" DAC Waveform selector output error sum. = {}".format(adc_awg_error_sum))
        if adc_awg_error_sum < ERR_THRESHOLD:
            print("Validate DAC Waveform selector output pattern {} successful.".format(sel_pattern))
        else:
            print("Validate DAC Waveform selector output pattern {} failed.".format(sel_pattern))
            validation_res = True

        print("Generate graph image.")
        fig = plt.figure(figsize=(8, 6), dpi=300)
        plt.xlabel("Time [us]")
        plt.title(
            "ADC capture DAC Sel. output Pattern {2} ({0} samples, {1} Msps)".format(
            ADC_SAMPLES, ADC_FREQ, sel_pattern))
        plt.plot(time_adc, adc_awg_force_captures[sel_pattern], linewidth=0.8, label="Expected")
        plt.plot(time_adc, adc_awg_result_captures[sel_pattern], linewidth=0.8, label="Actual")
        plt.legend()
        plt.savefig(PLOT_DIR + "adc_cap_dacsel_pattern_{}.png".format(sel_pattern))

        fig = plt.figure(figsize=(8, 6), dpi=300)
        plt.xlabel("Time [us]")
        plt.title(
            "ADC capture DAC AWG output Pattern {2} ({0} samples, {1} Msps)".format(
            ADC_SAMPLES, ADC_FREQ, sel_pattern))
        plt.plot(time_adc, adc_mac_capsample, linewidth=0.8, label="Expected")
        plt.plot(time_adc, adc_mac_actual_captures[sel_pattern], linewidth=0.8, label="Actual")
        plt.legend()
        plt.savefig(PLOT_DIR + "adc_cap_awg_pattern_{}.png".format(sel_pattern))

    print("Done.")
    return validation_res


if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    handler = logging.StreamHandler()
    handler.setLevel(LOG_LEVEL)
    logger.setLevel(LOG_LEVEL)
    logger.addHandler(handler)

    ret = main()
    sys.exit(ret)
