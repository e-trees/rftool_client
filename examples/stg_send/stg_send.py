import sys
import os
import logging
import math
import rftoolclient as rftc
import rftoolclient.stimgen as sg
from collections import namedtuple

try:
    is_all_sync_design = (sys.argv[1] == "sync_all")
except Exception:
    is_all_sync_design = False

ZCU111_IP_ADDR = os.environ.get('ZCU111_IP_ADDR', "192.168.1.3")
DAC_FREQ = 614.4 # Msps
WAVE_FREQ = DAC_FREQ / sg.Stimulus.MIN_UNIT_SAMPLES_FOR_WAVE_PART #MHz

if is_all_sync_design:
    BITSTREAM = rftc.FpgaDesign.STIM_GEN_ALL_SYNC
else:
    BITSTREAM = rftc.FpgaDesign.STIM_GEN

stg_list = sg.STG.all()
dout_list = [sg.DigitalOut.U0, sg.DigitalOut.U1]

StimParams = namedtuple(
    'StimParams',
    ('num_wait_words', 'num_seq_repeats', 'num_chunk_repeats', 'num_blank_words', 'chunk_waves'))

stg_to_params = {
    # sin  (出力パターン)
    sg.STG.U0 : StimParams(
        num_wait_words = 0,
        num_seq_repeats = 1,
        num_chunk_repeats = 1,
        num_blank_words = 0,
        chunk_waves = ['sin']),

    # sin  _  sin  _  sin  _  sin  _
    sg.STG.U1 : StimParams(
        num_wait_words = 0,
        num_seq_repeats = 4,
        num_chunk_repeats = 1,
        num_blank_words = 64,
        chunk_waves = ['sin']),

    # sin
    sg.STG.U2 : StimParams(
        num_wait_words = 0,
        num_seq_repeats = 1,
        num_chunk_repeats = 1,
        num_blank_words = 0,
        chunk_waves = ['sin']),

    # sin
    sg.STG.U3 : StimParams(
        num_wait_words = 0,
        num_seq_repeats = 1,
        num_chunk_repeats = 1,
        num_blank_words = 0,
        chunk_waves = ['sin']),

    # sin  sin  saw  saw  squ  squ  sin  sin  saw  saw  squ  squ
    sg.STG.U4 : StimParams(
        num_wait_words = 0,
        num_seq_repeats = 2,
        num_chunk_repeats = 2,
        num_blank_words = 0,
        chunk_waves = ['sin', 'saw', 'squ']),

    # sin  saw  squ  sin  sin  saw  saw  squ  squ  sin  saw  squ  sin  saw  sin  squ
    sg.STG.U5 : StimParams(
        num_wait_words = 0,
        num_seq_repeats = 1,
        num_chunk_repeats = 1,
        num_blank_words = 0,
        chunk_waves = [
            'sin', 'saw', 'squ',
            'sin', 'sin', 'saw', 'saw', 'squ', 'squ',
            'sin', 'saw', 'squ',
            'sin', 'saw', 'sin', 'squ']),

    # squ  squ  squ  saw  saw  saw  squ  squ  squ  saw  saw  saw
    sg.STG.U6 : StimParams(
        num_wait_words = 0,
        num_seq_repeats = 2,
        num_chunk_repeats = 3,
        num_blank_words = 0,
        chunk_waves = ['squ', 'saw']),

    # _  squ  squ  saw  saw  squ  squ  saw  saw  squ  squ  saw  saw
    sg.STG.U7 : StimParams(
        num_wait_words = 64,
        num_seq_repeats = 3,
        num_chunk_repeats = 2,
        num_blank_words = 0,
        chunk_waves = ['squ', 'saw']),
}


def output_rfdc_interrupt_details(stg_ctrl, stg_to_interrupts):
    """RF Data Converter の割り込みを出力する"""
    for stg, interrupts in stg_to_interrupts.items():
        tile, block = stg_ctrl.stg_to_dac_tile_block(stg)
        print('Interrupts on DAC tile {}, block {}  (Stimulus Generator {})'.format(tile, block, stg))
        for interrupt in interrupts:
            print('  ', rftc.RfdcInterrupt.to_msg(interrupt))
        print()


def output_stim_gen_err_details(stg_to_errs):
    """Stimulus Generator のエラーを出力する"""
    for stg, errs in stg_to_errs.items():
        print('Errors on Stimulus Generator {}'.format(stg))
        for err in errs:
            print('  ', sg.StgErr.to_msg(err))
        print()


def gen_wave_samples(type):
    """引数に応じて「正弦波」「ノコギリ波」「矩形波」のいずれかを作る"""
    if type == 'sin':
        wave = rftc.SinWave(1, WAVE_FREQ * 1e6, 30000)
    elif type == 'saw':
        wave = rftc.SawtoothWave(1, WAVE_FREQ * 1e6, 30000, phase = math.pi, crest_pos = 0.0)
    elif type == 'squ':
        wave = rftc.SquareWave(1, WAVE_FREQ * 1e6, 30000)
    
    # サンプル数を 1024 の倍数に調整する
    samples = wave.gen_samples(DAC_FREQ * 1e6) # samples は 16-bit 符号付整数のリスト
    rem = len(samples) % sg.Stimulus.MIN_UNIT_SAMPLES_FOR_WAVE_PART
    if rem != 0:
        samples.extend([0] * (sg.Stimulus.MIN_UNIT_SAMPLES_FOR_WAVE_PART - rem))
    return samples


def set_stimulus(stg_ctrl):
    wave_samples_cache = {
        'sin' : gen_wave_samples('sin'),
        'saw' : gen_wave_samples('saw'),
        'squ' : gen_wave_samples('squ')
    }
    stg_to_stimulus = {}
    for stg_id, params in stg_to_params.items():
        stimulus = sg.Stimulus(params.num_wait_words, params.num_seq_repeats)
        for wave in params.chunk_waves:
            stimulus.add_chunk(
                wave_samples_cache[wave],
                params.num_blank_words,
                params.num_chunk_repeats)
        stg_to_stimulus[stg_id] = stimulus

    # 波形情報を Stimulus Generator に送信する.
    stg_ctrl.set_stimulus(stg_to_stimulus)


def setup_stim_gens(stg_ctrl):
    """Stimulus Generator の波形出力に必要な設定を行う"""
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
        .add(0x01, 100)
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
    # デフォルトのディジタル出力データの設定
    digital_out_ctrl.set_default_output_data(0x36, *dout_list)
    # ディジタル出力データの設定
    set_digital_out_data(digital_out_ctrl)
    # Stimulus Generator からのスタートトリガを受け付けるように設定.
    # このスタートトリガは, 何れかの Stimulus Generator の波形出力開始と同時にアサートされる.
    # なお, StimGenCtrl.start_stgs で複数の STG をスタートしてもスタートトリガは一度しかアサートされない.
    digital_out_ctrl.enable_trigger(sg.DigitalOutTrigger.START, *dout_list)


def main(logger):
    with rftc.RftoolClient(logger) as client:
        print('Connect to RFTOOL Server.')
        client.connect(ZCU111_IP_ADDR)
        client.command.TermMode(0)
        # FPGA コンフィギュレーション
        client.command.ConfigFpga(BITSTREAM, 10)
        # Stimulus Generator のセットアップ
        setup_stim_gens(client.stg_ctrl)
        # ディジタル出力モジュールのセットアップ
        setup_digital_output_modules(client.digital_out_ctrl)
        # 波形出力スタート
        client.stg_ctrl.start_stgs(*stg_list)
        # 波形出力完了待ち
        client.stg_ctrl.wait_for_stgs_to_stop(5, *stg_list)
        # ディジタル出力モジュール動作完了待ち
        client.digital_out_ctrl.wait_for_douts_to_stop(5, *dout_list)
        # 波形出力完了フラグクリア
        client.stg_ctrl.clear_stg_stop_flags(*stg_list)
        # ディジタル出力モジュール動作完了フラグクリア
        client.digital_out_ctrl.clear_dout_stop_flags(*dout_list)
        # DAC 割り込みチェック
        stg_to_interrupts = client.stg_ctrl.check_dac_interrupt(*stg_list)
        output_rfdc_interrupt_details(client.stg_ctrl, stg_to_interrupts)
        # Stimulus Generator エラーチェック
        stg_to_errs = client.stg_ctrl.check_stg_err(*stg_list)
        output_stim_gen_err_details(stg_to_errs)


if __name__ == "__main__":
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    main(logger)
