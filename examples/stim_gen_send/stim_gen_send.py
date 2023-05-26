import sys
import pathlib
import os
import logging

lib_path = str(pathlib.Path(__file__).resolve().parents[2])
sys.path.append(lib_path)
from RftoolClient import client
import StimGen as sg
import common as cmn

ZCU111_IP_ADDR = os.environ.get('ZCU111_IP_ADDR', "192.168.1.3")
DAC_FREQ = 614.4 # Msps

stg_list = sg.STG.all()
dout_list = sg.DigitalOut.all()
stg_to_freq = {
    sg.STG.U0 : 1.0,
    sg.STG.U1 : 1.5,
    sg.STG.U2 : 2.0,
    sg.STG.U3 : 2.5,
    sg.STG.U4 : 3.0,
    sg.STG.U5 : 3.5,
    sg.STG.U6 : 4.0,
    sg.STG.U7 : 4.5
} # MHz


def output_rfdc_interrupt_details(stg_ctrl, stg_to_interrupts):
    """RF Data Converter の割り込みを出力する"""
    for stg, interrupts in stg_to_interrupts.items():
        tile, block = stg_ctrl.stg_to_dac_tile_block(stg)
        print('Interrupts on DAC tile {}, block {}  (Stimulus Generator {})'.format(tile, block, stg))
        for interrupt in interrupts:
            if interrupt == cmn.RfdcInterrupt.DAC_INTERPOLATION_OVERFLOW:
                print('  Overflow detected in DAC Interpolation stage datapath.')
            if interrupt == cmn.RfdcInterrupt.ADC_DECIMATION_OVERFLOW:
                print('  Overflow detected in ADC decimation stage datapath.')
            if interrupt == cmn.RfdcInterrupt.DAC_QMC_GAIN_PHASE_OVERFLOW:
                print('  Overflow detected in DAC QMC Gain/Phase.')
            if interrupt == cmn.RfdcInterrupt.DAC_QMC_OFFSET_OVERFLOW:
                print('  Overflow detected in DAC QMC offset.')
            if interrupt == cmn.RfdcInterrupt.ADC_QMC_GAIN_PHASE_OVERFLOW:
                print('  Overflow detected in ADC QMC Gain/Phase.')
            if interrupt == cmn.RfdcInterrupt.ADC_QMC_OFFSET_OVERFLOW:
                print('  Overflow detected in ADC QMC offset.')
            if interrupt == cmn.RfdcInterrupt.DAC_INV_SINC_OVERFLOW:
                print('  Overflow detected in DAC Inverse Sinc Filter.')
            if interrupt == cmn.RfdcInterrupt.SUB_ADC_OVER_RANGE:
                print('  Sub ADC over/under range detected.')
            if interrupt == cmn.RfdcInterrupt.ADC_OVER_VOLTAGE:
                print('  ADC over voltage detected.')
            if interrupt == cmn.RfdcInterrupt.ADC_OVER_RANGE:
                print('  ADC over range detected.')
            if interrupt == cmn.RfdcInterrupt.DAC_FIFO_OVERFLOW:
                print('  DAC FIFO overflow detected.')
            if interrupt == cmn.RfdcInterrupt.DAC_FIFO_UNDERFLOW:
                print('  DAC FIFO underflow detected.')
            if interrupt == cmn.RfdcInterrupt.DAC_FIFO_MARGINAL_OVERFLOW:
                print('  DAC FIFO marginal overflow detected.')
            if interrupt == cmn.RfdcInterrupt.DAC_FIFO_MARGINAL_UNDERFLOW:
                print('  DAC FIFO marginal underflow detected.')
            if interrupt == cmn.RfdcInterrupt.ADC_FIFO_OVERFLOW:
                print('  ADC FIFO overflow detected.')
            if interrupt == cmn.RfdcInterrupt.ADC_FIFO_UNDERFLOW:
                print('  ADC FIFO underflow detected.')
            if interrupt == cmn.RfdcInterrupt.ADC_FIFO_MARGINAL_OVERFLOW:
                print('  ADC FIFO marginal overflow detected.')
            if interrupt == cmn.RfdcInterrupt.ADC_FIFO_MARGINAL_UNDERFLOW:
                print('  ADC FIFO marginal underflow detected.')
        print()


def output_stim_gen_err_details(stg_to_errs):
    """Stimulus Generator のエラーを出力する"""
    for stg, errs in stg_to_errs.items():
        print('Errors on Stimulus Generator {}'.format(stg))
        for err in errs:
            if err == sg.StgErr.MEM_RD:
                print('  Failed to read waveform')
            if err == sg.StgErr.SAMPLE_SHORTAGE:
                print('  Wave samples were not sent to a DAC in time')
        print()


def set_stimulus(stg_ctrl):
    stg_to_stimulus = {}
    for stg_id in stg_list:
        # 波形のサンプルデータを作成する
        wave = cmn.SinWave(3, stg_to_freq[stg_id] * 1e6, 30000)
        samples = wave.gen_samples(DAC_FREQ * 1e6) # samples は 16-bit 符号付整数のリスト
        # サンプル数を 1024 の倍数に調整する
        rem = len(samples) % sg.Stimulus.MIN_UNIT_OF_SAMPLES
        if rem != 0:
            samples.extend([0] * (sg.Stimulus.MIN_UNIT_OF_SAMPLES - rem))
        # 波形サンプルを Stimulus オブジェクトにセットし, Stimulus オブジェクトを dict に格納する
        stg_to_stimulus[stg_id] = sg.Stimulus(
            samples,
            num_blank_words = 0,
            num_wait_words = 0,
            num_repeats = 2)

    # 波形情報を Stimulus Generator に送信する.
    stg_ctrl.set_stimulus(stg_to_stimulus)


def setup_stim_gens(stg_ctrl):
    """Stimulue Generator の波形出力に必要な設定を行う"""
    # STG デザイン用に DAC を設定
    stg_ctrl.setup_dacs()
    # DAC タイル同期
    stg_ctrl.sync_dac_tiles()
    # Stimulus Generator 初期化
    stg_ctrl.initialize(*stg_list)
    # 波形データを Stimulus Generator に設定
    set_stimulus(stg_ctrl)


def set_digital_out_data(digital_out_ctrl):
    # ディジタル出力データの作成
    dout_data_list = sg.DigitalOutputDataList()
    (dout_data_list
        .add(0x01, 0xFFFFFFFF)
        .add(0x02, 100)
        .add(0x04, 100)
        .add(0x08, 100)
        .add(0x10, 100)
        .add(0x20, 100)
        .add(0x40, 100)
        .add(0x80, 100))
    # 出力データをディジタル出力モジュールに設定
    digital_out_ctrl.set_output_data(dout_data_list, *dout_list)


def setup_digital_output_modules(digital_out_ctrl):
    """ディジタル出力に必要な設定を行う"""
    # ディジタル出力モジュール初期化
    digital_out_ctrl.initialize(*dout_list)
    # ディジタル出力データの設定
    set_digital_out_data(digital_out_ctrl)
    # Stimulus Generator からのスタートトリガを受け付けるように設定.
    # このスタートトリガは, 何れかの Stimulus Generator の波形出力開始と同時にアサートされる.
    # なお, StimGenCtrl.start_stgs で複数の STG をスタートしてもスタートトリガは一度しかアサートされない.
    digital_out_ctrl.enable_start_trigger(*dout_list)


def main(logger):    
    with client.RftoolClient(logger) as rft:
        print("Connect to RFTOOL Server.")
        rft.connect(ZCU111_IP_ADDR)
        rft.command.TermMode(0)
        # FPGA コンフィギュレーション
        rft.command.ConfigFpga(cmn.FpgaDesign.STIM_GEN, 10)
        # Stimulus Generator のセットアップ
        setup_stim_gens(rft.stg_ctrl)
        # ディジタル出力モジュールのセットアップ
        setup_digital_output_modules(rft.digital_out_ctrl)
        # 波形出力スタート
        rft.stg_ctrl.start_stgs(*stg_list)
        # 波形出力完了待ち
        rft.stg_ctrl.wait_for_stgs_to_stop(5, *stg_list)
        # ディジタル出力モジュール動作完了待ち
        rft.digital_out_ctrl.wait_for_douts_to_stop(5, *dout_list)
        # 波形出力完了フラグクリア
        rft.stg_ctrl.clear_stg_stop_flags(*stg_list)
        # ディジタル出力モジュール動作完了フラグクリア
        rft.digital_out_ctrl.clear_dout_stop_flags(*dout_list)
        # DAC 割り込みチェック
        stg_to_interrupts = rft.stg_ctrl.check_dac_interrupt(*stg_list)
        output_rfdc_interrupt_details(rft.stg_ctrl, stg_to_interrupts)
        # Stimulus Generator エラーチェック
        stg_to_errs = rft.stg_ctrl.check_stg_err(*stg_list)
        output_stim_gen_err_details(stg_to_errs)


if __name__ == "__main__":
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    main(logger)
