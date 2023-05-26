import sys
import pathlib
import time

from RftoolClient import cmdutil, rfterr

lib_path = str(pathlib.Path(__file__).resolve().parents[2])
sys.path.append(lib_path)
import StimGen as sg
import common as cmn
from StimGen.memorymap import DigitalOutMasterCtrlRegs, DigitalOutCtrlRegs, DigitalOutputDataListRegs

class DigitalOutCtrl:
    """ディジタル出力モジュールを制御するためのクラス"""

    def __init__(self, common_cmd, logger=None):
        self.__logger = logger or cmn.get_null_logger()
        self.__reg_access = common_cmd.stim_reg_access


    def initialize(self, *dout_id_list):
        """引数で指定したディジタル出力モジュールを初期化する.

        Args:
            *dout_id_list (list of DigitalOut): 初期化するディジタル出力モジュールの ID
        """
        try:
            self.__validate_dout_id(*dout_id_list)
        except Exception as e:
            cmn.log_error(e, self.__logger)
            raise

        self.disable_start_trigger(*dout_id_list)
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
            cmn.log_error(e, self.__logger)
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


    def enable_start_trigger(self, *dout_id_list):
        """引数で指定したディジタル出力モジュールのスタートトリガを有効化する.

        | スタートトリガを有効化したディジタル出力モジュールは Stimulus Generator の波形出力開始と同時に動作を開始する.
        
        Args:
            *dout_id_list (list of DigitalOut): スタートトリガを有効にするディジタル出力モジュールの ID
        """
        try:
            self.__validate_dout_id(*dout_id_list)
        except Exception as e:
            cmn.log_error(e, self.__logger)
            raise

        addr = DigitalOutMasterCtrlRegs.ADDR + DigitalOutMasterCtrlRegs.Offset.EXT_TRIG_MASK
        for dout_id in dout_id_list:
            self.__reg_access.write_bits(addr, DigitalOutMasterCtrlRegs.Bit.dout(dout_id), 1, 1)


    def disable_start_trigger(self, *dout_id_list):
        """引数で指定したディジタル出力モジュールのスタートトリガを無効化する.
        
        Args:
            *dout_id_list (list of DigitalOut): スタートトリガを無効にするディジタル出力モジュールの ID
        """
        try:
            self.__validate_dout_id(*dout_id_list)
        except Exception as e:
            cmn.log_error(e, self.__logger)
            raise

        addr = DigitalOutMasterCtrlRegs.ADDR + DigitalOutMasterCtrlRegs.Offset.EXT_TRIG_MASK
        for dout_id in dout_id_list:
            self.__reg_access.write_bits(addr, DigitalOutMasterCtrlRegs.Bit.dout(dout_id), 1, 0)


    def start_douts(self, *dout_id_list):
        """引数で指定したディジタル出力モジュールの動作を開始する.

        | スタートトリガの有効/無効は影響しない.

        Args:
            *dout_id_list (list of DigitalOut): 動作を開始するデジタル出力モジュールの ID
        """
        try:
            self.__validate_dout_id(*dout_id_list)
        except Exception as e:
            cmn.log_error(e, self.__logger)
            raise

        self.__select_ctrl_target(*dout_id_list)
        addr = DigitalOutMasterCtrlRegs.ADDR + DigitalOutMasterCtrlRegs.Offset.CTRL
        self.__reg_access.write_bits(addr, DigitalOutMasterCtrlRegs.Bit.CTRL_START, 1, 0)
        self.__reg_access.write_bits(addr, DigitalOutMasterCtrlRegs.Bit.CTRL_START, 1, 1)
        time.sleep(10e-6)
        self.__reg_access.write_bits(addr, DigitalOutMasterCtrlRegs.Bit.CTRL_START, 1, 0)   
        self.__deselect_ctrl_target(*dout_id_list)


    def terminate_douts(self, *dout_id_list):
        """引数で指定したディジタル出力モジュールを強制停止させる.

        Args:
            *dout_id_list (list of DigitalOut): 強制停止させるデジタル出力モジュールの ID
        """
        try:
            self.__validate_dout_id(*dout_id_list)
        except Exception as e:
            cmn.log_error(e, self.__logger)
            raise

        for dout_id in dout_id_list:
            addr = DigitalOutCtrlRegs.Addr.dout(dout_id) + DigitalOutCtrlRegs.Offset.CTRL
            self.__reg_access.write_bits(addr, DigitalOutCtrlRegs.Bit.CTRL_TERMINATE, 1, 1)
            self.__wait_for_douts_idle(3, dout_id)
            self.__reg_access.write_bits(addr, DigitalOutCtrlRegs.Bit.CTRL_TERMINATE, 1, 0)


    def clear_dout_stop_flags(self, *dout_id_list):
        """引数で指定した全てのディジタル出力モジュールの動作完了フラグを下げる

        Args:
            *dout_id_list (list of DigitalOut): 動作完了フラグを下げるデジタル出力モジュールの ID
        """
        try:
            self.__validate_dout_id(*dout_id_list)
        except Exception as e:
            cmn.log_error(e, self.__logger)
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
            cmn.log_error(e, self.__logger)
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
                cmn.log_error(err, self.__logger)
                raise err
            time.sleep(0.01)


    def version(self):
        """ディジタル出力モジュールのバージョンを取得する

        Returns:
            string: バージョンを表す文字列
        """
        data = self.__reg_access.read(DigitalOutCtrlRegs.ADDR + DigitalOutCtrlRegs.Offset.VERSION)
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
        addr = DigitalOutMasterCtrlRegs.ADDR + DigitalOutMasterCtrlRegs.Offset.CTRL_TARGET_SEL
        for dout_id in dout_id_list:
            self.__reg_access.write_bits(addr, DigitalOutMasterCtrlRegs.Bit.dout(dout_id), 1, 1)


    def __deselect_ctrl_target(self, *dout_id_list):
        """一括制御を無効にするディジタル出力モジュールを選択する"""
        addr = DigitalOutMasterCtrlRegs.ADDR + DigitalOutMasterCtrlRegs.Offset.CTRL_TARGET_SEL
        for dout_id in dout_id_list:
            self.__reg_access.write_bits(addr, DigitalOutMasterCtrlRegs.Bit.dout(dout_id), 1, 0)


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
                cmn.log_error(err, self.__logger)
                raise err
            time.sleep(0.01)
