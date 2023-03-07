#!/usr/bin/env python3
# coding: utf-8

"""
MTS 版 AWG x8 サンプルプログラム.
各 AWG から特定の周波数の正弦波を出力してキャプチャする.
本スクリプトが想定する MTS 版 AWG デザインでは, ADC および DAC のサンプリングレートは固定であり,
キャプチャ RAM は キャプチャモジュールごとに個別に存在ものとする.
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

try:
    is_async = (sys.argv[1] == "async")
except Exception:
    is_async = False

lib_path = str(pathlib.Path(__file__).resolve().parents[2])
sys.path.append(lib_path)
from RftoolClient import client, rfterr, wavegen, ndarrayutil
import AwgSa as awgsa

# Parameters
ZCU111_IP_ADDR_0 = os.environ.get('ZCU111_IP_ADDR_0', "192.168.1.3")
ZCU111_IP_ADDR_1 = os.environ.get('ZCU111_IP_ADDR_1', "192.168.2.3")

# Log level
LOG_LEVEL = logging.INFO

# Constants
BITSTREAM = 8  # MTS AWG SA
BITSTREAM_LOAD_TIMEOUT = 10
TRIG_BUSY_TIMEOUT = 60
DUC_DDC_FACTOR = 1
DAC_FREQ = 3932.16
ADC_FREQ = 3932.16
CAPTURE_DELAY = 345
INFINITE = -1

# ADC or DAC
ADC = 0
DAC = 1

awg_list = [awgsa.AwgId.AWG_0, awgsa.AwgId.AWG_1, awgsa.AwgId.AWG_2, awgsa.AwgId.AWG_3, 
            awgsa.AwgId.AWG_4, awgsa.AwgId.AWG_5, awgsa.AwgId.AWG_6, awgsa.AwgId.AWG_7]

awg_to_freq = { awgsa.AwgId.AWG_0 : 10,
                awgsa.AwgId.AWG_1 : 20,
                awgsa.AwgId.AWG_2 : 786.43,
                awgsa.AwgId.AWG_3 : 655.36,
                awgsa.AwgId.AWG_4 : 561.73,
                awgsa.AwgId.AWG_5 : 491.52,
                awgsa.AwgId.AWG_6 : 436.90,
                awgsa.AwgId.AWG_7 : 393.21,
            } #MHz


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


def setup_dac(rftcmd):
    print("Setup DAC.")
    for tile in [0, 1]:
        for block in [0, 1, 2, 3]:
            rftcmd.SetMixerSettings(DAC, tile, block, 0.0, 0.0, 2, 1, 16, 4, 0)
            rftcmd.ResetNCOPhase(DAC, tile, block)
            rftcmd.UpdateEvent(DAC, tile, block, 1)
        rftcmd.SetupFIFO(DAC, tile, 0)
        for block in [0, 1, 2, 3]:
            rftcmd.SetInterpolationFactor(tile, block, DUC_DDC_FACTOR)
        for block in [0, 1, 2, 3]:
            rftcmd.IntrClr(DAC, tile, block, 0xFFFFFFFF)
        rftcmd.SetupFIFO(DAC, tile, 1)


def setup_adc(rftcmd):
    print("Setup ADC.")
    for tile in [0, 1, 2, 3]:
        for block in [0, 1]:
            rftcmd.SetMixerSettings(ADC, tile, block, 0.0, 0.0, 2, 1, 16, 4, 0)
            rftcmd.ResetNCOPhase(ADC, tile, block)
            rftcmd.UpdateEvent(ADC, tile, block, 1)
        rftcmd.SetupFIFO(ADC, tile, 0)
        for block in [0, 1]:
            rftcmd.SetDither(tile, block, 1 if ADC_FREQ > 3000. else 0)
            rftcmd.SetDecimationFactor(tile, block, DUC_DDC_FACTOR)
        for block in [0, 1]:
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


def set_wave_sequence(awg_sa_cmd):
    """
    波形シーケンスを AWG にセットする
    """
    awg_id_to_wave_sequence = {}

    for awg_id in awg_list:
        # 波形の定義
        wave_0 = awgsa.AwgWave(
            wave_type = awgsa.AwgWave.SINE,
            frequency = awg_to_freq[awg_id],
            phase = 0,
            amplitude = 30000,
            num_cycles = INFINITE)

        # 波形シーケンスの定義
        # 波形ステップの開始から終了までの期間は, キャプチャの終了処理にかかるオーバーヘッドを考慮し, 波形出力期間 + 2000 ns を設定する.
        wave_sequence = awgsa.WaveSequence(DAC_FREQ).add_step(step_id = 0, wave = wave_0)

        # AWG に波形シーケンスをセットする
        awg_sa_cmd.set_wave_sequence(awg_id = awg_id, wave_sequence = wave_sequence, num_repeats = 1)
        awg_id_to_wave_sequence[awg_id] = wave_sequence

    return awg_id_to_wave_sequence


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


def shutdown_all_tiles(rftcmd):
    """
    DAC と ADC の全タイルをシャットダウンする
    """
    rftcmd.Shutdown(DAC, -1)
    rftcmd.Shutdown(ADC, -1)


def startup_all_tiles(rftcmd):
    """
    DAC と ADC の全タイルを起動する
    """
    rftcmd.StartUp(DAC, -1)
    rftcmd.StartUp(ADC, -1)

def main():

    rft_0 = client.RftoolClient(logger=logger)
    rft_1 = client.RftoolClient(logger=logger)
    clk_setting = awgsa.ClockSrc.INTERNAL if is_async else awgsa.ClockSrc.EXTERNAL

    for rft, ipaddr in [(rft_0, ZCU111_IP_ADDR_0), (rft_1, ZCU111_IP_ADDR_1)]:
        print("Connect to RFTOOL Server.")
        rft.connect(ipaddr)
        rft.command.TermMode(0)

        print("Configure Bitstream.")
        config_bitstream(rft.command, BITSTREAM)
        shutdown_all_tiles(rft.command)
        startup_all_tiles(rft.command)
        setup_dac(rft.command)
        setup_adc(rft.command)

        # 初期化
        rft.awg_sa_cmd.initialize_awg_sa()
        # ソースクロックの選択
        rft.awg_sa_cmd.select_src_clk(clk_setting)
        # AWG 有効化
        rft.awg_sa_cmd.enable_awg(*awg_list)
        # Multi Tile Synchronization
        rft.awg_sa_cmd.sync_dac_tiles()
        rft.awg_sa_cmd.sync_adc_tiles()
        # 波形シーケンス設定
        set_wave_sequence(rft.awg_sa_cmd)
        # 波形出力スタート
        rft.awg_sa_cmd.start_wave_sequence()
    
    print("Press enter to stop all AWGs")
    input()
    for rft in [rft_0, rft_1]:
        rft.awg_sa_cmd.terminate_all_awgs()
        wait_for_sequence_to_finish(rft.awg_sa_cmd, *awg_list)

    for rft in [rft_0, rft_1]:
        # エラーチェック
        print("Check for errors")
        for ch in range(8):
            check_intr_flags(rft.command, DAC, ch)

    rft_0.close()
    rft_1.close()
    print("Done.")
    return


if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    handler = logging.StreamHandler()
    handler.setLevel(LOG_LEVEL)
    logger.setLevel(LOG_LEVEL)
    logger.addHandler(handler)

    main()
