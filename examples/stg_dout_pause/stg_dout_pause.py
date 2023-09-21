import sys
import os
import logging
import time
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

stg_list = [sg.STG.U4]
dout_list = sg.DigitalOut.all()
stg_to_freq = { sg.STG.U4 : 1 } # MHz


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
        stimulus = sg.Stimulus(num_wait_words = 0, num_seq_repeats = 1)
        stimulus.add_chunk(samples = samples, num_blank_words = 0, num_repeats = 1)
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


def set_digital_out_data(digital_out_ctrl, bit_patterns):
    # ディジタル出力データの作成
    dout_time = 153599803 if is_all_sync_design else 400000000 # 4 [sec]
    for dout_id in dout_list:
        dout_data_list = sg.DigitalOutputDataList()
        for bit_pattern in bit_patterns:
            dout_data_list.add(bit_pattern, dout_time)

        # 出力データをディジタル出力モジュールに設定
        digital_out_ctrl.set_output_data(dout_data_list, dout_id)


def set_default_digital_out_data(digital_out_ctrl):
    # デフォルトのディジタル出力データの設定
    for dout_id in dout_list:
        digital_out_ctrl.set_default_output_data(0, dout_id)


def setup_digital_output_modules(digital_out_ctrl):
    """ディジタル出力に必要な設定を行う"""
    # ディジタル出力モジュール初期化
    digital_out_ctrl.initialize(*dout_list)
    # デフォルトのディジタル出力データの設定
    set_default_digital_out_data(digital_out_ctrl)
    # ディジタル出力データの設定
    bit_patterns = [1, 2]
    set_digital_out_data(digital_out_ctrl, bit_patterns)
    # Stimulus Generator からのリスタートトリガを受け付けるように設定.
    # このリスタートトリガは, 何れかの Stimulus Generator の波形出力開始と同時にアサートされる.
    digital_out_ctrl.enable_restart_trigger(*dout_list)


def restart_douts(mode, stg_ctrl, digital_out_ctrl):
    """ディジタル出力モジュールを再スタートする"""
    if mode == 1:
        # 再スタート
        digital_out_ctrl.restart_douts(*dout_list)
    else:
        # STG の波形出力スタート.
        # STG の波形出力開始に合わせてディジタル出力モジュールが再スタートする.
        stg_ctrl.start_stgs(*stg_list)
        # 波形出力完了待ち
        stg_ctrl.wait_for_stgs_to_stop(5, *stg_list)


def main(logger):
    with rftc.RftoolClient(logger) as rft:
        print("Connect to RFTOOL Server.")
        rft.connect(ZCU111_IP_ADDR)
        rft.command.TermMode(0)
        # FPGA コンフィギュレーション
        rft.command.ConfigFpga(BITSTREAM, 10)
        # Stimulus Generator のセットアップ
        setup_stim_gens(rft.stg_ctrl)
        # ディジタル出力モジュールのセットアップ
        setup_digital_output_modules(rft.digital_out_ctrl)
        # ディジタル出力スタート
        rft.digital_out_ctrl.start_douts(*dout_list)
        time.sleep(2)
        # ディジタル出力一時停止
        rft.digital_out_ctrl.pause_douts(*dout_list)
        ctrl_sel = input('input\n    0: resume\n    1: restart from software\n    2: restart from STG\n')
        
        if int(ctrl_sel) == 0:
            # 再開
            rft.digital_out_ctrl.resume_douts(*dout_list)
        else:
            # ディジタル出力データを変更
            bit_patterns = [3, 2, 1]
            set_digital_out_data(rft.digital_out_ctrl, bit_patterns)
            # 再スタート
            restart_douts(int(ctrl_sel), rft.stg_ctrl, rft.digital_out_ctrl)

        # ディジタル出力モジュール動作完了待ち
        rft.digital_out_ctrl.wait_for_douts_to_stop(15, *dout_list)
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
