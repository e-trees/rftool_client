#!/usr/bin/env python3
# coding: utf-8

"""
AWG サンプルプログラム:
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
import AwgSa as awgsa

LOG_LEVEL = logging.INFO
ZCU111_IP_ADDR = os.environ.get('ZCU111_IP_ADDR', "192.168.1.3")
DAC_FREQ = 4096.0
BITSTREAM = 7 # AWG SA DRAM CAPTURE
BITSTREAM_LOAD_TIMEOUT = 10
PLOT_DIR = "plot_awg_waveseq_visualize/"

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


def output_samples(filename, step_id_to_samples):
    """
    サンプル値をテキスト形式で出力する
    """
    with open(filename, mode = 'w') as f:
        for step_id, samples in sorted(step_id_to_samples.items()):
            f.write("step_" + str(step_id) + "\n")
            for sample_val in samples:
                f.write("\t" + str(sample_val) + "\n")
            f.write("\n")


def set_wave_sequence(awg_sa_cmd):
    """
    波形シーケンスを AWG にセットする
    """
    wave_0 = awgsa.AwgWave(
        wave_type = awgsa.AwgWave.SINE,
        frequency = 10.0,
        phase = 0,
        amplitude = 20000,
        num_cycles = 3)

    wave_1 = awgsa.AwgWave(
        wave_type = awgsa.AwgWave.SAWTOOTH,
        frequency = 15.0,
        phase = 0.0,
        amplitude = 10000,
        offset = 0,
        crest_pos = 0.5,
        num_cycles = 3)

    wave_2 = awgsa.AwgWave(
        wave_type = awgsa.AwgWave.SQUARE,
        frequency = 10.0,
        phase = 0.0,
        amplitude = 10000,
        offset = 0,
        duty_cycle = 50.0,
        num_cycles = 3)

    wave_3 = awgsa.AwgWave(
        wave_type = awgsa.AwgWave.GAUSSIAN,
        frequency = 10.0,
        phase = 0.0,
        amplitude = 8000,
        offset = 0,
        domain_begin = -4.0,
        domain_end = 4.0,
        variance = 0.2,
        num_cycles = 2)
    
    wave_4 = awgsa.AwgIQWave(wave_0, wave_1)
    wave_5 = awgsa.AwgIQWave(wave_1, wave_2)
    wave_6 = awgsa.AwgIQWave(wave_2, wave_0)

    wave_sequence_0 = (awgsa.WaveSequence(DAC_FREQ)
        .add_step(step_id = 0, wave = wave_0, post_blank = 2000)
        .add_step(step_id = 1, wave = wave_1, post_blank = 1500)
        .add_step(step_id = 2, wave = wave_2, post_blank = 0)
        .add_step(step_id = 3, wave = wave_3, post_blank = 3000))
        
    wave_sequence_1 = (awgsa.WaveSequence(DAC_FREQ, is_iq_data = True)
        .add_step(step_id = 0, wave = wave_4, post_blank = 1000)
        .add_step(step_id = 1, wave = wave_5, post_blank = 2000)
        .add_step(step_id = 2, wave = wave_6, post_blank = 1500))

    awg_sa_cmd.set_wave_sequence(awgsa.AwgId.AWG_0, wave_sequence_0, num_repeats = 1)
    awg_sa_cmd.set_wave_sequence(awgsa.AwgId.AWG_1, wave_sequence_1, num_repeats = 1)
    return (wave_sequence_0, wave_sequence_1)


def main():   

    with client.RftoolClient(logger=logger) as rft:
        print("Connect to RFTOOL Server.")
        rft.connect(ZCU111_IP_ADDR)
        rft.command.TermMode(0)

        print("Configure Bitstream.")
        config_bitstream(rft.command, BITSTREAM)

        # 初期化    
        rft.awg_sa_cmd.initialize_awg_sa()
        (wave_seq_0, wave_seq_1) = set_wave_sequence(rft.awg_sa_cmd)

        # Real 波形出力
        # Python スクリプト内で計算したサンプル値を保持するオブジェクトを取得
        waveform_0 = wave_seq_0.get_waveform_sequence()
        waveform_0.save_as_img(PLOT_DIR + "user_def_seq_0_waveform.png")
        step_id_to_samples = waveform_0.get_samples_by_step_id()
        output_samples(PLOT_DIR + "user_def_seq_0_waveform.txt", step_id_to_samples)
        
        # ハードウェア内部の RAM に格納されたサンプル値を保持するオブジェクトを取得
        waveform_0 = rft.awg_sa_cmd.get_waveform_sequence(awgsa.AwgId.AWG_0)
        waveform_0.save_as_img(PLOT_DIR + "actual_seq_0_waveform.png")
        step_id_to_samples = waveform_0.get_samples_by_step_id()
        output_samples(PLOT_DIR + "actual_seq_0_waveform.txt", step_id_to_samples)

        # I/Q 波形出力
        # Python スクリプト内で計算したサンプル値を保持するオブジェクトを取得
        waveform_1 = wave_seq_1.get_waveform_sequence()
        waveform_1.save_as_img(PLOT_DIR + "user_def_seq_1_waveform.png")
        waveform_1.save_as_img(PLOT_DIR + "user_def_seq_1_waveform_merged.png", iq_separation = False)
        step_id_to_i_samples = waveform_1.get_i_samples_by_step_id()
        step_id_to_q_samples = waveform_1.get_q_samples_by_step_id()
        output_samples(PLOT_DIR + "user_def_seq_1_i_waveform.txt", step_id_to_i_samples)
        output_samples(PLOT_DIR + "user_def_seq_1_q_waveform.txt", step_id_to_q_samples)

        # ハードウェア内部の RAM に格納されたサンプル値を保持するオブジェクトを取得
        waveform_1 = rft.awg_sa_cmd.get_waveform_sequence(awgsa.AwgId.AWG_1)
        waveform_1.save_as_img(PLOT_DIR + "actual_seq_1_waveform.png")
        waveform_1.save_as_img(PLOT_DIR + "actual_seq_1_waveform_merged.png", iq_separation = False)
        step_id_to_i_samples = waveform_1.get_i_samples_by_step_id()
        step_id_to_q_samples = waveform_1.get_q_samples_by_step_id()
        output_samples(PLOT_DIR + "actual_seq_1_i_waveform.txt", step_id_to_i_samples)
        output_samples(PLOT_DIR + "actual_seq_1_q_waveform.txt", step_id_to_q_samples)

    print("Done.")
    return


if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    handler = logging.StreamHandler()
    handler.setLevel(LOG_LEVEL)
    logger.setLevel(LOG_LEVEL)
    logger.addHandler(handler)

    main()
