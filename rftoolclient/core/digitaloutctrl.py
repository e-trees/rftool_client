import time
import rftoolclient.stimgen as sg
import rftoolclient as rftc
from rftoolclient.stimgen.memorymap import (
    DigitalOutMasterCtrlRegs, DigitalOutCtrlRegs, DigitalOutputDataListRegs)

class DigitalOutCtrl:
    """ディジタル出力モジュールを制御するためのクラス"""

    def __init__(self, common_cmd, logger=None):
        self.__logger = logger or rftc.get_null_logger()
        self.__reg_access = common_cmd.stim_reg_access


    def initialize(self, *dout_id_list):
        """引数で指定したディジタル出力モジュールを初期化する.

        Args:
            *dout_id_list (list of DigitalOut): 初期化するディジタル出力モジュールの ID
        """
        try:
            self.__validate_dout_id(*dout_id_list)
        except Exception as e:
            rftc.log_error(e, self.__logger)
            raise
        
        self.disable_start_trigger(*dout_id_list)
        self.disable_restart_trigger(*dout_id_list)
        self.__deselect_ctrl_target(*dout_id_list)
        for dout_id in dout_id_list:
            addr = DigitalOutCtrlRegs.Addr.dout(dout_id) + DigitalOutCtrlRegs.Offset.CTRL
            self.__reg_access.write(addr, 0)

        self.__reset_douts(*dout_id_list)
        dout_data_list = sg.DigitalOutputDataList().add(0, 2)
        self.set_output_data(dout_data_list, *dout_id_list)


    def set_output_data(self, data_list, *dout_id_list):
        """引数で指定したディジタル出力モジュールに出力データ設定する.

        Args:
            data_list (DigitalOutputDataList): 出力パターンを格納した DigitalOutputDataList オブジェクト
            dout_id_list (DigitalOut): 出力パターンを設定するディジタル出力モジュールの ID の リスト
        """
        try:
            self.__validate_dout_id(*dout_id_list)
        except Exception as e:
            rftc.log_error(e, self.__logger)
            raise
        
        regs = []
        for i in range(len(data_list)):
            bits, time = data_list[i]
            regs.append(bits)
            regs.append(time - 1)
        
        for dout_id in dout_id_list:
            base_addr = DigitalOutputDataListRegs.Addr.dout(dout_id)
            addr = base_addr + DigitalOutputDataListRegs.Offset.pattern(0)
            self.__reg_access.write_multi(addr, *regs)

            base_addr = DigitalOutCtrlRegs.Addr.dout(dout_id)
            addr = base_addr + DigitalOutCtrlRegs.Offset.NUM_PATTERNS
            self.__reg_access.write(addr, len(data_list))
            addr = base_addr + DigitalOutCtrlRegs.Offset.START_IDX
            self.__reg_access.write(addr, 0)


    def set_default_output_data(self, bits, *dout_id_list):
        """引数で指定したディジタル出力モジュールにデフォルトの出力データ設定する.

        | このメソッドで指定した出力値は, ディジタル出力モジュールが動作していないときに常に出力される.
        | initialize メソッドでディジタルモジュールを初期化してもこの値は変わらない.
        | このメソッドを複数回呼び出すと, ディジタル出力モジュールは最後の呼び出しで設定した値を出力する.

        Args:
            bits (int) : デフォルトで出力されるビットデータ.  0 ~ 7 ビット目がデジタル出力ポートの電圧値に対応する.  0 が Lo で 1 が Hi.
            dout_id_list (DigitalOut): 出力パターンを設定するディジタル出力モジュールの ID の リスト
        """
        try:
            self.__validate_dout_id(*dout_id_list)
            if not isinstance(bits, int):
                raise ValueError("'bits' must be an integer.")
        except Exception as e:
            rftc.log_error(e, self.__logger)
            raise

        for dout_id in dout_id_list:
            base_addr = DigitalOutputDataListRegs.Addr.dout(dout_id)
            addr = base_addr + DigitalOutputDataListRegs.Offset.DEFAULT_BIT_PATTERN
            self.__reg_access.write(addr, bits)


    def enable_start_trigger(self, *dout_id_list):
        """引数で指定したディジタル出力モジュールのスタートトリガを有効化する.

        | スタートトリガを有効化したディジタル出力モジュールは Stimulus Generator の波形出力開始と同時に動作を開始する.
        
        Args:
            *dout_id_list (list of DigitalOut): スタートトリガを有効にするディジタル出力モジュールの ID
        """
        try:
            self.__validate_dout_id(*dout_id_list)
        except Exception as e:
            rftc.log_error(e, self.__logger)
            raise

        self.__set_mask_bits(
            DigitalOutMasterCtrlRegs.ADDR + DigitalOutMasterCtrlRegs.Offset.START_TRIG_MASK_0,
            *dout_id_list)


    def disable_start_trigger(self, *dout_id_list):
        """引数で指定したディジタル出力モジュールのスタートトリガを無効化する.
        
        Args:
            *dout_id_list (list of DigitalOut): スタートトリガを無効にするディジタル出力モジュールの ID
        """
        try:
            self.__validate_dout_id(*dout_id_list)
        except Exception as e:
            rftc.log_error(e, self.__logger)
            raise

        self.__clear_mask_bits(
            DigitalOutMasterCtrlRegs.ADDR + DigitalOutMasterCtrlRegs.Offset.START_TRIG_MASK_0,
            *dout_id_list)


    def enable_restart_trigger(self, *dout_id_list):
        """引数で指定したディジタル出力モジュールのリスタートトリガを有効化する.

        | リスタートトリガを有効化したディジタル出力モジュールが Pause 状態のときに
        | Stimulus Generator が波形出力を開始すると, 現在の設定に基づいてディジタル値の出力を再スタートする.
        
        Args:
            *dout_id_list (list of DigitalOut): リスタートトリガを有効にするディジタル出力モジュールの ID
        """
        try:
            self.__validate_dout_id(*dout_id_list)
        except Exception as e:
            rftc.log_error(e, self.__logger)
            raise

        self.__set_mask_bits(
            DigitalOutMasterCtrlRegs.ADDR + DigitalOutMasterCtrlRegs.Offset.RESTART_TRIG_MASK_0,
            *dout_id_list)


    def disable_restart_trigger(self, *dout_id_list):
        """引数で指定したディジタル出力モジュールのリスタートトリガを無効化する.
        
        Args:
            *dout_id_list (list of DigitalOut): リスタートトリガを無効にするディジタル出力モジュールの ID
        """
        try:
            self.__validate_dout_id(*dout_id_list)
        except Exception as e:
            rftc.log_error(e, self.__logger)
            raise

        self.__clear_mask_bits(
            DigitalOutMasterCtrlRegs.ADDR + DigitalOutMasterCtrlRegs.Offset.RESTART_TRIG_MASK_0,
            *dout_id_list)


    def enable_pause_trigger(self, *dout_id_list):
        """引数で指定したディジタル出力モジュールの一時停止トリガを有効化する.

        | 一時停止トリガを有効化したディジタル出力モジュールが Active 状態のときに
        | Stimulus Generator が一時停止すると，それらも一時停止する.
        
        Args:
            *dout_id_list (list of DigitalOut): 一時停止トリガを有効にするディジタル出力モジュールの ID
        """
        try:
            self.__validate_dout_id(*dout_id_list)
        except Exception as e:
            rftc.log_error(e, self.__logger)
            raise

        self.__set_mask_bits(
            DigitalOutMasterCtrlRegs.ADDR + DigitalOutMasterCtrlRegs.Offset.PAUSE_TRIG_MASK_0,
            *dout_id_list)


    def disable_pause_trigger(self, *dout_id_list):
        """引数で指定したディジタル出力モジュールの一時停止トリガを無効化する.
        
        Args:
            *dout_id_list (list of DigitalOut): 一時停止トリガを無効にするディジタル出力モジュールの ID
        """
        try:
            self.__validate_dout_id(*dout_id_list)
        except Exception as e:
            rftc.log_error(e, self.__logger)
            raise

        self.__clear_mask_bits(
            DigitalOutMasterCtrlRegs.ADDR + DigitalOutMasterCtrlRegs.Offset.PAUSE_TRIG_MASK_0,
            *dout_id_list)


    def enable_resume_trigger(self, *dout_id_list):
        """引数で指定したディジタル出力モジュールの再開トリガを有効化する.

        | 再開トリガ有効化したディジタル出力モジュールが Pause 状態のときに
        | Stimulus Generator が動作を再開すると，それらも動作を再開する.
        
        Args:
            *dout_id_list (list of DigitalOut): 一時停止トリガを有効にするディジタル出力モジュールの ID
        """
        try:
            self.__validate_dout_id(*dout_id_list)
        except Exception as e:
            rftc.log_error(e, self.__logger)
            raise

        self.__set_mask_bits(
            DigitalOutMasterCtrlRegs.ADDR + DigitalOutMasterCtrlRegs.Offset.RESUME_TRIG_MASK_0,
            *dout_id_list)


    def disable_resume_trigger(self, *dout_id_list):
        """引数で指定したディジタル出力モジュールの再開トリガを無効化する.
        
        Args:
            *dout_id_list (list of DigitalOut): 再開トリガを無効にするディジタル出力モジュールの ID
        """
        try:
            self.__validate_dout_id(*dout_id_list)
        except Exception as e:
            rftc.log_error(e, self.__logger)
            raise

        self.__clear_mask_bits(
            DigitalOutMasterCtrlRegs.ADDR + DigitalOutMasterCtrlRegs.Offset.RESUME_TRIG_MASK_0,
            *dout_id_list)


    def start_douts(self, *dout_id_list):
        """引数で指定したディジタル出力モジュールの動作を開始する.

        | スタートトリガの有効/無効は影響しない.

        Args:
            *dout_id_list (list of DigitalOut): 動作を開始するデジタル出力モジュールの ID
        """
        try:
            self.__validate_dout_id(*dout_id_list)
        except Exception as e:
            rftc.log_error(e, self.__logger)
            raise
        
        self.__select_ctrl_target(*dout_id_list)
        addr = DigitalOutMasterCtrlRegs.ADDR + DigitalOutMasterCtrlRegs.Offset.CTRL
        self.__reg_access.write_bits(addr, DigitalOutMasterCtrlRegs.Bit.CTRL_START, 1, 0)
        self.__reg_access.write_bits(addr, DigitalOutMasterCtrlRegs.Bit.CTRL_START, 1, 1)
        time.sleep(10e-6)
        self.__reg_access.write_bits(addr, DigitalOutMasterCtrlRegs.Bit.CTRL_START, 1, 0)   
        self.__deselect_ctrl_target(*dout_id_list)


    def pause_douts(self, *dout_id_list):
        """引数で指定したディジタル出力モジュールを一時停止させる.

        Args:
            *dout_id_list (list of DigitalOut): 一時停止するデジタル出力モジュールの ID
        """
        try:
            self.__validate_dout_id(*dout_id_list)
        except Exception as e:
            rftc.log_error(e, self.__logger)
            raise

        self.__select_ctrl_target(*dout_id_list)
        addr = DigitalOutMasterCtrlRegs.ADDR + DigitalOutMasterCtrlRegs.Offset.CTRL
        self.__reg_access.write_bits(addr, DigitalOutMasterCtrlRegs.Bit.CTRL_PAUSE, 1, 0)
        self.__reg_access.write_bits(addr, DigitalOutMasterCtrlRegs.Bit.CTRL_PAUSE, 1, 1)
        time.sleep(10e-6)
        self.__reg_access.write_bits(addr, DigitalOutMasterCtrlRegs.Bit.CTRL_PAUSE, 1, 0)   
        self.__deselect_ctrl_target(*dout_id_list)


    def resume_douts(self, *dout_id_list):
        """引数で指定したディジタル出力モジュールが一時停止中であった場合, 動作を再開させる.

        Args:
            *dout_id_list (list of DigitalOut): 動作を再開するデジタル出力モジュールの ID
        """
        try:
            self.__validate_dout_id(*dout_id_list)
        except Exception as e:
            rftc.log_error(e, self.__logger)
            raise

        self.__select_ctrl_target(*dout_id_list)
        addr = DigitalOutMasterCtrlRegs.ADDR + DigitalOutMasterCtrlRegs.Offset.CTRL
        self.__reg_access.write_bits(addr, DigitalOutMasterCtrlRegs.Bit.CTRL_RESUME, 1, 0)
        self.__reg_access.write_bits(addr, DigitalOutMasterCtrlRegs.Bit.CTRL_RESUME, 1, 1)
        time.sleep(10e-6)
        self.__reg_access.write_bits(addr, DigitalOutMasterCtrlRegs.Bit.CTRL_RESUME, 1, 0)
        self.__deselect_ctrl_target(*dout_id_list)


    def restart_douts(self, *dout_id_list):
        """引数で指定したディジタル出力モジュールが一時停止中であった場合, 再スタートさせる.

        | 再スタートしたディジタル出力モジュールは, 現在のディジタル値リストの先頭から出力を始める.

        Args:
            *dout_id_list (list of DigitalOut): 再スタートするデジタル出力モジュールの ID
        """
        try:
            self.__validate_dout_id(*dout_id_list)
        except Exception as e:
            rftc.log_error(e, self.__logger)
            raise

        self.__select_ctrl_target(*dout_id_list)
        addr = DigitalOutMasterCtrlRegs.ADDR + DigitalOutMasterCtrlRegs.Offset.CTRL
        self.__reg_access.write_bits(addr, DigitalOutMasterCtrlRegs.Bit.CTRL_RESTART, 1, 0)
        self.__reg_access.write_bits(addr, DigitalOutMasterCtrlRegs.Bit.CTRL_RESTART, 1, 1)
        time.sleep(10e-6)
        self.__reg_access.write_bits(addr, DigitalOutMasterCtrlRegs.Bit.CTRL_RESTART, 1, 0)
        self.__deselect_ctrl_target(*dout_id_list)


    def terminate_douts(self, *dout_id_list):
        """引数で指定したディジタル出力モジュールを強制停止させる.

        Args:
            *dout_id_list (list of DigitalOut): 強制停止させるデジタル出力モジュールの ID
        """
        try:
            self.__validate_dout_id(*dout_id_list)
        except Exception as e:
            rftc.log_error(e, self.__logger)
            raise

        for dout_id in dout_id_list:
            addr = DigitalOutCtrlRegs.Addr.dout(dout_id) + DigitalOutCtrlRegs.Offset.CTRL
            self.__reg_access.write_bits(addr, DigitalOutCtrlRegs.Bit.CTRL_TERMINATE, 1, 1)
            self.__wait_for_douts_idle(5, dout_id)
            self.__reg_access.write_bits(addr, DigitalOutCtrlRegs.Bit.CTRL_TERMINATE, 1, 0)


    def clear_dout_stop_flags(self, *dout_id_list):
        """引数で指定した全てのディジタル出力モジュールの動作完了フラグを下げる

        Args:
            *dout_id_list (list of DigitalOut): 動作完了フラグを下げるデジタル出力モジュールの ID
        """
        try:
            self.__validate_dout_id(*dout_id_list)
        except Exception as e:
            rftc.log_error(e, self.__logger)
            raise
    
        self.__select_ctrl_target(*dout_id_list)
        addr = DigitalOutMasterCtrlRegs.ADDR + DigitalOutMasterCtrlRegs.Offset.CTRL
        self.__reg_access.write_bits(addr, DigitalOutMasterCtrlRegs.Bit.CTRL_DONE_CLR, 1, 0)
        self.__reg_access.write_bits(addr, DigitalOutMasterCtrlRegs.Bit.CTRL_DONE_CLR, 1, 1)
        self.__reg_access.write_bits(addr, DigitalOutMasterCtrlRegs.Bit.CTRL_DONE_CLR, 1, 0)
        self.__deselect_ctrl_target(*dout_id_list)


    def wait_for_douts_to_stop(self, timeout, *dout_id_list):
        """引数で指定した全てのディジタル出力モジュールの波形の送信が終了するのを待つ

        Args:
            timeout (int or float): タイムアウト値 (単位: 秒). タイムアウトした場合, 例外を発生させる.
            *stg_id_list (list of STG): 波形の送信が終了するのを待つ STG の ID
        
        Raises:
            DigitalOutTimeoutError: タイムアウトした場合
        """
        try:
            self.__validate_timeout(timeout)
            self.__validate_dout_id(*dout_id_list)
        except Exception as e:
            rftc.log_error(e, self.__logger)
            raise
                
        start = time.time()
        while True:
            all_stopped = True
            for dout_id in dout_id_list:
                addr = DigitalOutCtrlRegs.Addr.dout(dout_id) + DigitalOutCtrlRegs.Offset.STATUS
                val = self.__reg_access.read_bits(addr, DigitalOutCtrlRegs.Bit.STATUS_DONE, 1)
                if val == 0:
                    all_stopped = False
                    break
            if all_stopped:
                return

            elapsed_time = time.time() - start
            if elapsed_time > timeout:
                err = sg.DigitalOutTimeoutError('Digital output module stop timeout')
                rftc.log_error(err, self.__logger)
                raise err
            time.sleep(0.01)


    def version(self):
        """ディジタル出力モジュールのバージョンを取得する

        Returns:
            string: バージョンを表す文字列
        """
        data = self.__reg_access.read(DigitalOutMasterCtrlRegs.ADDR + DigitalOutMasterCtrlRegs.Offset.VERSION)
        ver_char = chr(0xFF & (data >> 24))
        ver_year = 0xFF & (data >> 16)
        ver_month = 0xF & (data >> 12)
        ver_day = 0xFF & (data >> 4)
        ver_id = 0xF & data
        return '{}:20{:02}/{:02}/{:02}-{}'.format(ver_char, ver_year, ver_month, ver_day, ver_id)


    def __validate_dout_id(self, *dout_id_list):
        if not sg.DigitalOut.includes(*dout_id_list):
            raise ValueError('DigitalOut ID {}'.format(dout_id_list))
    
    
    def __validate_timeout(self, timeout):
        if (not isinstance(timeout, (int, float))) or (timeout < 0):
            raise ValueError('Invalid timeout {}'.format(timeout))


    def __select_ctrl_target(self, *dout_id_list):
        """一括制御を有効にするディジタル出力モジュールを選択する"""
        self.__set_mask_bits(
            DigitalOutMasterCtrlRegs.ADDR + DigitalOutMasterCtrlRegs.Offset.CTRL_TARGET_SEL_0,
            *dout_id_list)


    def __deselect_ctrl_target(self, *dout_id_list):
        """一括制御を無効にするディジタル出力モジュールを選択する"""
        self.__clear_mask_bits(
            DigitalOutMasterCtrlRegs.ADDR + DigitalOutMasterCtrlRegs.Offset.CTRL_TARGET_SEL_0,
            *dout_id_list)


    def __set_mask_bits(self, mask_reg_addr, *dout_id_list):
        """ビットマスクレジスタの特定のビットを 1 にする
        
        Args:
            mask_reg_addr (int): 値を変更するビットマスクレジスタのアドレス
            *dout_id_list (list of STG): このリストのディジタル出力モジュールに対応するビットを全て 1 にする
        """
        reg_0, reg_1 = self.__reg_access.read_multi(mask_reg_addr, 2)

        for dout_id in dout_id_list:
            bit_pos = DigitalOutMasterCtrlRegs.Bit.dout(dout_id)
            if dout_id <= sg.DigitalOut.U31:
                reg_0 |= 1 << bit_pos
            else:
                reg_1 |= 1 << bit_pos

        self.__reg_access.write_multi(mask_reg_addr, reg_0, reg_1)


    def __clear_mask_bits(self, mask_reg_addr, *dout_id_list):
        """ビットマスクレジスタの特定のビットを 0 にする
        
        Args:
            mask_reg_addr (int): 値を変更するビットマスクレジスタのアドレス
            *dout_id_list (list of STG): このリストのディジタル出力モジュールに対応するビットを全て 0 にする
        """
        reg_0, reg_1 = self.__reg_access.read_multi(mask_reg_addr, 2)

        for dout_id in dout_id_list:
            bit_pos = DigitalOutMasterCtrlRegs.Bit.dout(dout_id)
            if dout_id <= sg.DigitalOut.U31:
                reg_0 &= 0xFFFFFFFF & (~(1 << bit_pos))
            else:
                reg_1 &= 0xFFFFFFFF & (~(1 << bit_pos))

        self.__reg_access.write_multi(mask_reg_addr, reg_0, reg_1)


    def __reset_douts(self, *dout_id_list):
        self.__select_ctrl_target(*dout_id_list)
        addr = DigitalOutMasterCtrlRegs.ADDR + DigitalOutMasterCtrlRegs.Offset.CTRL
        self.__reg_access.write_bits(addr, DigitalOutMasterCtrlRegs.Bit.CTRL_RESET, 1, 1)
        time.sleep(10e-6)
        self.__reg_access.write_bits(addr, DigitalOutMasterCtrlRegs.Bit.CTRL_RESET, 1, 0)
        time.sleep(10e-6)
        self.__deselect_ctrl_target(*dout_id_list)


    def __wait_for_douts_idle(self, timeout, *dout_id_list):
        start = time.time()
        while True:
            all_idle = True
            for dout_id in dout_id_list:
                addr = DigitalOutCtrlRegs.Addr.dout(dout_id) + DigitalOutCtrlRegs.Offset.STATUS
                val = self.__reg_access.read_bits(addr, DigitalOutCtrlRegs.Bit.STATUS_BUSY, 1)
                if val == 1:
                    all_idle = False
                    break
            if all_idle:
                return

            elapsed_time = time.time() - start
            if elapsed_time > timeout:
                err = sg.DigitalOutTimeoutError('Digital output module idle timed out')
                rftc.log_error(err, self.__logger)
                raise err
            time.sleep(0.01)
