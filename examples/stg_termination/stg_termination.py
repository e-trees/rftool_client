import sys
import os
import logging
import rftoolclient as rftc
import rftoolclient.stimgen as sg

try:
    is_all_sync_design = (sys.argv[1] == "sync_all")
except Exception:
    is_all_sync_design = False


ZCU111_IP_ADDR = os.environ.get('ZCU111_IP_ADDR', "192.168.1.3")
DAC_FREQ = 614.4 # Msps

if is_all_sync_design:
    BITSTREAM = rftc.FpgaDesign.STIM_GEN_ALL_SYNC
else:
    BITSTREAM = rftc.FpgaDesign.STIM_GEN

stg_list = sg.STG.all()
dout_list = [sg.DigitalOut.U0, sg.DigitalOut.U1]
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
            print('  ', rftc.RfdcInterrupt.to_msg(interrupt))
        print()


def output_stim_gen_err_details(stg_to_errs):
    """Stimulus Generator のエラーを出力する"""
    for stg, errs in stg_to_errs.items():
        print('Errors on Stimulus Generator {}'.format(stg))
        for err in errs:
            print('  ', sg.StgErr.to_msg(err))
        print()


def gen_example_sample_data(stg_id):
    """出力サンプルデータの例として sin カーブを作る"""
    wave = rftc.SinWave(3, stg_to_freq[stg_id] * 1e6, 30000)
    samples = wave.gen_samples(DAC_FREQ * 1e6) # samples は 16-bit 符号付整数のリスト
    # サンプル数を 1024 の倍数に調整する
    rem = len(samples) % sg.Stimulus.MIN_UNIT_SAMPLES_FOR_WAVE_PART
    if rem != 0:
        samples.extend([0] * (sg.Stimulus.MIN_UNIT_SAMPLES_FOR_WAVE_PART - rem))
    
    return samples


def set_stimulus(stg_ctrl):
    stg_to_stimulus = {}
    for stg_id in stg_list:
        # 波形のサンプルデータを作成する
        samples = gen_example_sample_data(stg_id)
        # 波形サンプルを Stimulus オブジェクトにセットし, Stimulus オブジェクトを dict に格納する
        stimulus = sg.Stimulus(num_wait_words = 0, num_seq_repeats = 0xFFFFFFFF)
        stimulus.add_chunk(samples = samples, num_blank_words = 0, num_repeats = 0xFFFFFFFF)
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
        .add(0xFF, 0xFFFFFFFF))
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
    digital_out_ctrl.enable_trigger(sg.DigitalOutTrigger.START, *dout_list)


def main(logger):
    with rftc.RftoolClient(logger) as client:
        print("Connect to RFTOOL Server.")
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
        input('press Enter to stop STGs.')
        # 波形出力強制停止
        client.stg_ctrl.terminate_stgs(*stg_list)
        # ディジタル値出力強制停止
        client.digital_out_ctrl.terminate_douts(*dout_list)
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
