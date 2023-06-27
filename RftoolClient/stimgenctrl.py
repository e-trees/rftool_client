import sys
import pathlib
import time
from RftoolClient import cmdutil

lib_path = str(pathlib.Path(__file__).resolve().parents[2])
sys.path.append(lib_path)
import StimGen as sg
import common as cmn
from StimGen.memorymap import StgMasterCtrlRegs, StgCtrlRegs, WaveParamRegs

class StimGenCtrl(object):
    """Stimulus Generator を制御するクラス"""

    __NUM_SAMPLES_IN_STG_WORD = 16
    MAX_WAVE_PART_SAMPLES = 0x80000000 # 各 STG の波形パート 1 つ当たりに含まれるサンプル数を STG の数足した値の最大値

    def __init__(self, common_cmd, rft_cmd, logger=None):
        self.__logger = logger or cmn.get_null_logger()
        self.__common_cmd = common_cmd
        self.__reg_access = common_cmd.stim_reg_access
        self.__rft_cmd = rft_cmd


    def initialize(self, *stg_id_list):
        """引数で指定した Stimulus Generator を初期化する.

        Args:
            *stg_id_list (list of STG): 初期化する STG の ID
        """
        try:
            self.__validate_stg_id(*stg_id_list)
        except Exception as e:
            cmn.log_error(e, self.__logger)
            raise

        self.__deselect_ctrl_target(*stg_id_list)
        for stg_id in stg_id_list:
            addr = StgCtrlRegs.Addr.stg(stg_id) + StgCtrlRegs.Offset.CTRL
            self.__reg_access.write(addr, 0)

        self.__reset_stgs(*stg_id_list)        
        samples = [30000] * sg.Stimulus.MIN_UNIT_OF_SAMPLES
        stimulus = sg.Stimulus(samples, 0, 0, 1)
        stg_to_stim = {stg_id : stimulus for stg_id in stg_id_list}
        self.set_stimulus(stg_to_stim)


    def set_stimulus(self, stg_to_stim):
        """Stimulus Generator に波形データを登録する.

        | このメソッドを呼び出すと以前登録した波形情報は失われるので, 
        | 同時に使用する全ての Stimulus Generator の波形を登録すること.

        Args:
            stg_to_stim ({STG -> Stimulus}): 
                | key = 波形を設定する Stimulus Generator の ID
                | value = 波形情報を保持する Stimulus オブジェクト
        """
        try:
            if not isinstance(stg_to_stim, dict):
                raise('Invalid stg_to_stim')
            self.__validate_stg_id(*stg_to_stim.keys())
            addr = 0

            num_all_samples = sum([len(stimulus.samples) for stimulus in stg_to_stim.values()])
            if num_all_samples > self.MAX_WAVE_PART_SAMPLES:
                raise ValueError('The total number of samples in the wave parts is too large ({} samples). (MAX = {} samples)'
                                 .format(num_all_samples, self.MAX_WAVE_PART_SAMPLES))

            for stg_id, stimulus in stg_to_stim.items():
                if len(stimulus.samples) == 0:
                    raise ValueError(
                        "The length of 'samples' must be greater than 0.   (STG = {})"
                        .format(stg_id))
                if len(stimulus.samples) % sg.Stimulus.MIN_UNIT_OF_SAMPLES != 0:
                    raise ValueError(
                        "The length of 'samples' must be a multiple of {}.   (STG = {})"
                        .format(sg.Stimulus.MIN_UNIT_OF_SAMPLES, stg_id))

                self.__set_wave_seq_params(stg_id, stimulus.num_wait_words)
                sample_data = stimulus.serialized_samples
                num_sample_words = len(stimulus.samples) // self.__NUM_SAMPLES_IN_STG_WORD
                self.__common_cmd.write_dram(addr, sample_data, show_progress = True)
                self.__set_chunk_params(
                    stg_id,
                    addr,
                    num_sample_words,
                    stimulus.num_blank_words,
                    stimulus.num_repeats)
                addr += len(sample_data)

        except Exception as e:
            cmn.log_error(e, self.__logger)
            raise


    def start_stgs(self, *stg_id_list):
        """引数で指定した Stimulus Generator の波形送信を開始する.

        Args:
            *stg_id_list (list of STG): 波形送信を開始する STG の ID
        """
        try:
            self.__validate_stg_id(*stg_id_list)
        except Exception as e:
            cmn.log_error(e, self.__logger)
            raise

        self.__select_ctrl_target(*stg_id_list)
        addr = StgMasterCtrlRegs.ADDR + StgMasterCtrlRegs.Offset.CTRL
        self.__reg_access.write_bits(addr, StgMasterCtrlRegs.Bit.CTRL_PREPARE, 1, 0)
        self.__reg_access.write_bits(addr, StgMasterCtrlRegs.Bit.CTRL_PREPARE, 1, 1)
        self.__wait_for_stgs_ready(5, *stg_id_list)
        self.__reg_access.write_bits(addr, StgMasterCtrlRegs.Bit.CTRL_PREPARE, 1, 0)

        self.__reg_access.write_bits(addr, StgMasterCtrlRegs.Bit.CTRL_START, 1, 0)
        self.__reg_access.write_bits(addr, StgMasterCtrlRegs.Bit.CTRL_START, 1, 1)
        self.__reg_access.write_bits(addr, StgMasterCtrlRegs.Bit.CTRL_START, 1, 0)        
        self.__deselect_ctrl_target(*stg_id_list)


    def terminate_stgs(self, *stg_id_list):
        """引数で指定した Stimulus Generator を強制停止させる.

        Args:
            *stg_id_list (list of STG): 強制停止させる STG の ID
        """
        try:
            self.__validate_stg_id(*stg_id_list)
        except Exception as e:
            cmn.log_error(e, self.__logger)
            raise

        for stg_id in stg_id_list:
            addr = StgCtrlRegs.Addr.stg(stg_id) + StgCtrlRegs.Offset.CTRL
            self.__reg_access.write_bits(addr, StgCtrlRegs.Bit.CTRL_TERMINATE, 1, 1)
            self.__wait_for_stgs_idle(5, stg_id)
            self.__reg_access.write_bits(addr, StgCtrlRegs.Bit.CTRL_TERMINATE, 1, 0)


    def clear_stg_stop_flags(self, *stg_id_list):
        """引数で指定した全ての Stimulus Generator の波形出力終了フラグを下げる

        Args:
            *stg_id_list (list of STG): 波形出力終了フラグを下げる STG の ID
        """
        try:
            self.__validate_stg_id(*stg_id_list)
        except Exception as e:
            cmn.log_error(e, self.__logger)
            raise
    
        self.__select_ctrl_target(*stg_id_list)
        addr = StgMasterCtrlRegs.ADDR + StgMasterCtrlRegs.Offset.CTRL
        self.__reg_access.write_bits(addr, StgMasterCtrlRegs.Bit.CTRL_DONE_CLR, 1, 0)
        self.__reg_access.write_bits(addr, StgMasterCtrlRegs.Bit.CTRL_DONE_CLR, 1, 1)
        self.__reg_access.write_bits(addr, StgMasterCtrlRegs.Bit.CTRL_DONE_CLR, 1, 0)
        self.__deselect_ctrl_target(*stg_id_list)


    def wait_for_stgs_to_stop(self, timeout, *stg_id_list):
        """引数で指定した全ての Stimulus Generator の波形の送信が終了するのを待つ

        Args:
            timeout (int or float): タイムアウト値 (単位: 秒). タイムアウトした場合, 例外を発生させる.
            *stg_id_list (list of STG): 波形の送信が終了するのを待つ STG の ID
        
        Raises:
            StgTimeoutError: タイムアウトした場合
        """
        try:
            self.__validate_timeout(timeout)
            self.__validate_stg_id(*stg_id_list)
        except Exception as e:
            cmn.log_error(e, self.__logger)
            raise
                
        start = time.time()
        while True:
            all_stopped = True
            for stg_id in stg_id_list:
                addr = StgCtrlRegs.Addr.stg(stg_id) + StgCtrlRegs.Offset.STATUS
                val = self.__reg_access.read_bits(addr, StgCtrlRegs.Bit.STATUS_DONE, 1)
                if val == 0:
                    all_stopped = False
                    break
            if all_stopped:
                return

            elapsed_time = time.time() - start
            if elapsed_time > timeout:
                err = sg.StgTimeoutError('STG stop timeout')
                cmn.log_error(err, self.__logger)
                raise err
            time.sleep(0.01)


    def check_stg_err(self, *stg_id_list):
        """引数で指定した Stimulus Generator のエラーをチェックする.

        エラーのあった Stimulus Generator ごとにエラーの種類を返す.

        Args:
            *stg_id_list (STG): エラーを調べる STG の ID

        Returns:
            {STG -> list of StgErr}:
            | key = Stimulus Generator の ID
            | value = 発生したエラーのリスト
            | エラーが無かった場合は空の Dict.
        """
        try:
            self.__validate_stg_id(*stg_id_list)
        except Exception as e:
            cmn.log_error(e, self.__logger)
            raise

        stg_to_errs = {}
        for stg_id in stg_id_list:
            err_list = []
            addr = StgCtrlRegs.Addr.stg(stg_id) + StgCtrlRegs.Offset.ERR
            err = self.__reg_access.read_bits(addr, StgCtrlRegs.Bit.ERR_READ, 1)
            if err == 1:
                err_list.append(sg.StgErr.MEM_RD)
            err = self.__reg_access.read_bits(addr, StgCtrlRegs.Bit.ERR_SAMPLE_SHORTAGE, 1)
            if err == 1:
                err_list.append(sg.StgErr.SAMPLE_SHORTAGE)

            if err_list:
                stg_to_errs[stg_id] = err_list

        return stg_to_errs


    def check_dac_interrupt(self, *stg_id_list):
        """引数で指定した Stimulus Generator に対応する DAC の割り込みをチェックする.

        Stimulus Generator ごとに対応する DAC の割り込みを返す

        Args:
            *stg_id_list (STG): 割り込みを調べる DAC にデータを送る Stimulus Generator の ID

        Returns:
            {STG -> list of RfdcInterrupt}:
            | key = Stimulus Generator の ID
            | value = 発生した割り込みのリスト
            | 割り込みが無かった場合は空の Dict.
        """
        try:
            self.__validate_stg_id(*stg_id_list)
        except Exception as e:
            cmn.log_error(e, self.__logger)
            raise
        
        stg_to_interrupts = {}
        for stg_id in stg_id_list:
            interrupts = []
            tile, block = self.stg_to_dac_tile_block(stg_id)
            flags = self.__rft_cmd.GetIntrStatus(cmn.DAC, tile, block)[3]
            if (flags & cmn.RfdcIntrpMask.DAC_I_INTP_STG0_OVF or
                flags & cmn.RfdcIntrpMask.DAC_I_INTP_STG1_OVF or
                flags & cmn.RfdcIntrpMask.DAC_I_INTP_STG2_OVF or
                flags & cmn.RfdcIntrpMask.DAC_Q_INTP_STG0_OVF or
                flags & cmn.RfdcIntrpMask.DAC_Q_INTP_STG1_OVF or
                flags & cmn.RfdcIntrpMask.DAC_Q_INTP_STG2_OVF):
                interrupts.append(cmn.RfdcInterrupt.DAC_INTERPOLATION_OVERFLOW)
            if (flags & cmn.RfdcIntrpMask.DAC_QMC_GAIN_PHASE_OVF):
                interrupts.append(cmn.RfdcInterrupt.DAC_QMC_GAIN_PHASE_OVERFLOW)
            if (flags & cmn.RfdcIntrpMask.DAC_QMC_OFFSET_OVF):
                interrupts.append(cmn.RfdcInterrupt.DAC_QMC_OFFSET_OVERFLOW)
            if (flags & cmn.RfdcIntrpMask.DAC_INV_SINC_OVF):
                interrupts.append(cmn.RfdcInterrupt.DAC_INV_SINC_OVERFLOW)
            if (flags & cmn.RfdcIntrpMask.DAC_FIFO_OVF):
                interrupts.append(cmn.RfdcInterrupt.DAC_FIFO_OVERFLOW)
            if (flags & cmn.RfdcIntrpMask.DAC_FIFO_UDF):
                interrupts.append(cmn.RfdcInterrupt.DAC_FIFO_UNDERFLOW)
            if (flags & cmn.RfdcIntrpMask.DAC_FIFO_MARGIANL_OVF):
                interrupts.append(cmn.RfdcInterrupt.DAC_FIFO_MARGINAL_OVERFLOW)
            if (flags & cmn.RfdcIntrpMask.DAC_FIFO_MARGIANL_UDF):
                interrupts.append(cmn.RfdcInterrupt.DAC_FIFO_MARGINAL_UNDERFLOW)
            
            if interrupts:
                stg_to_interrupts[stg_id] = interrupts

        return stg_to_interrupts


    def setup_dacs(self):
        """
        全ての DAC を Stimulus Generator 用にセットアップする
        """
        for tile in [0, 1]:
            self.__rft_cmd.SetupFIFO(cmn.DAC, tile, 0)
            for block in [0, 1, 2, 3]:
                self.__rft_cmd.SetMixerSettings(cmn.DAC, tile, block, 0.0, 0.0, 2, 1, 16, 4, 0)
                self.__rft_cmd.UpdateEvent(cmn.DAC, tile, block, 1)
                self.__rft_cmd.SetInterpolationFactor(tile, block, 1)
                self.__rft_cmd.IntrClr(cmn.DAC, tile, block, 0xFFFFFFFF)
            self.__rft_cmd.SetupFIFO(cmn.DAC, tile, 1)


    def sync_dac_tiles(self):
        """
        全ての DAC タイルを同期させる.
        このメソッドを呼ぶ前に, DAC データパスの設定 (I/Q ミキサ, 補間など) の設定を完了させておくこと.
        """
        self.__common_cmd.sync_dac_tiles()


    def stg_to_dac_tile_block(self, stg_id):
        """引数で指定した Stimlus Generator に対応する DAC のタイル ID とブロック ID を取得する

        Parameters
        ----------
        stg_id : STG
            この STG ID に対応する DAC のタイル ID とブロック ID を取得する
        
        Returns
        -------
        id_list : (int, int)
            (タイル ID, ブロック ID)
        """
        if (not sg.STG.includes(stg_id)):
           raise ValueError("invalid stg_id  " + str(stg_id))

        if stg_id == sg.STG.U0:
            return (1, 2)
        if stg_id == sg.STG.U1:
            return (1, 3)
        if stg_id == sg.STG.U2:
            return (1, 1)
        if stg_id == sg.STG.U3:
            return (1, 2)
        if stg_id == sg.STG.U4:
            return (0, 0)
        if stg_id == sg.STG.U5:
            return (0, 1)
        if stg_id == sg.STG.U6:
            return (0, 2)
        if stg_id == sg.STG.U7:
            return (0, 3)


    def version(self):
        """Stimlus Generator のバージョンを取得する

        Returns:
            string: バージョンを表す文字列
        """
        data = self.__reg_access.read(StgMasterCtrlRegs.ADDR + StgMasterCtrlRegs.Offset.VERSION)
        ver_char = chr(0xFF & (data >> 24))
        ver_year = 0xFF & (data >> 16)
        ver_month = 0xF & (data >> 12)
        ver_day = 0xFF & (data >> 4)
        ver_id = 0xF & data
        return '{}:20{:02}/{:02}/{:02}-{}'.format(ver_char, ver_year, ver_month, ver_day, ver_id)


    def __validate_stg_id(self, *stg_id_list):
        if not sg.STG.includes(*stg_id_list):
            raise ValueError('Invalid STG ID {}'.format(stg_id_list))


    def __validate_timeout(self, timeout):
        if (not isinstance(timeout, (int, float))) or (timeout < 0):
            raise ValueError('Invalid timeout {}'.format(timeout))


    def __select_ctrl_target(self, *stg_id_list):
        """一括制御を有効にする Stimulus Generator を選択する"""
        addr = StgMasterCtrlRegs.ADDR + StgMasterCtrlRegs.Offset.CTRL_TARGET_SEL
        for stg_id in stg_id_list:
            self.__reg_access.write_bits(addr, StgMasterCtrlRegs.Bit.stg(stg_id), 1, 1)


    def __deselect_ctrl_target(self, *stg_id_list):
        """一括制御を無効にする Stimulus Generator を選択する"""
        addr = StgMasterCtrlRegs.ADDR + StgMasterCtrlRegs.Offset.CTRL_TARGET_SEL
        for stg_id in stg_id_list:
            self.__reg_access.write_bits(addr, StgMasterCtrlRegs.Bit.stg(stg_id), 1, 0)


    def __reset_stgs(self, *stg_id_list):
        self.__select_ctrl_target(*stg_id_list)
        addr = StgMasterCtrlRegs.ADDR + StgMasterCtrlRegs.Offset.CTRL
        self.__reg_access.write_bits(addr, StgMasterCtrlRegs.Bit.CTRL_RESET, 1, 1)
        time.sleep(10e-6)
        self.__reg_access.write_bits(addr, StgMasterCtrlRegs.Bit.CTRL_RESET, 1, 0)
        time.sleep(10e-6)
        self.__deselect_ctrl_target(*stg_id_list)


    def __wait_for_stgs_ready(self, timeout, *stg_id_list):
        start = time.time()
        while True:
            all_ready = True
            for stg_id in stg_id_list:
                addr = StgCtrlRegs.Addr.stg(stg_id) + StgCtrlRegs.Offset.STATUS
                val = self.__reg_access.read_bits(addr, StgCtrlRegs.Bit.STATUS_READY, 1)
                if val == 0:
                    all_ready = False
                    break
            if all_ready:
                return

            elapsed_time = time.time() - start
            if elapsed_time > timeout:
                err = sg.StgTimeoutError('STG ready timed out')
                cmn.log_error(err, self.__logger)
                raise err
            time.sleep(0.01)


    def __wait_for_stgs_idle(self, timeout, *stg_id_list):
        start = time.time()
        while True:
            all_idle = True
            for stg_id in stg_id_list:
                addr = StgCtrlRegs.Addr.stg(stg_id) + StgCtrlRegs.Offset.STATUS
                val = self.__reg_access.read_bits(addr, StgCtrlRegs.Bit.STATUS_BUSY, 1)
                if val == 1:
                    all_idle = False
                    break
            if all_idle:
                return

            elapsed_time = time.time() - start
            if elapsed_time > timeout:
                err = sg.StgTimeoutError('STG idle timed out')
                cmn.log_error(err, self.__logger)
                raise err
            time.sleep(0.01)


    def __set_wave_seq_params(self, stg_id, num_wait_words):
        base = WaveParamRegs.Addr.stg(stg_id)
        addr = base + WaveParamRegs.Offset.NUM_WAIT_WORDS
        self.__reg_access.write(addr, num_wait_words)
        addr = base + WaveParamRegs.Offset.NUM_REPEATS
        self.__reg_access.write(addr, 1)
        addr = base + WaveParamRegs.Offset.NUM_CHUNKS
        self.__reg_access.write(addr, 1)


    def __set_chunk_params(
        self,
        stg_id,
        sample_data_addr,
        num_wave_part_words,
        num_blank_words,
        num_repeats):
        base_addr = WaveParamRegs.Addr.stg(stg_id) + WaveParamRegs.Offset.CHUNK_0
        addr = base_addr + WaveParamRegs.Offset.CHUNK_START_ADDR
        self.__reg_access.write(addr, sample_data_addr // 16) # レジスタにセットするのは 16 で割った値
        addr = base_addr + WaveParamRegs.Offset.NUM_WAVE_PART_WORDS
        self.__reg_access.write(addr, num_wave_part_words)
        addr = base_addr + WaveParamRegs.Offset.NUM_BLANK_WORDS
        self.__reg_access.write(addr, num_blank_words)
        addr = base_addr + WaveParamRegs.Offset.NUM_CHUNK_REPEATS
        self.__reg_access.write(addr, num_repeats)
