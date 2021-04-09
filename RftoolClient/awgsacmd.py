#!/usr/bin/env python3
# coding: utf-8

from RftoolClient import cmdutil, rfterr
import logging, struct
from AwgSa import WaveSequence
from AwgSa import AwgId
from AwgSa import AwgSaCmdResult
from AwgSa import CaptureConfig
from AwgSa import DigitalOutputSequence
from AwgSa import WaveSequenceParams
from AwgSa import FlattenedWaveformSequence
from AwgSa import FlattenedIQWaveformSequence
from AwgSa import ExternalTriggerId
from AwgSa import TriggerMode
from AwgSa import PL_DDR4_RAM_SIZE

class AwgSaCommand(object):
    """AWG SA 制御用のコマンドを定義するクラス"""

    def __init__(self, ctrl_interface, data_interface, logger=None):
        self.__logger = logging.getLogger(__name__)
        self.__logger.addHandler(logging.NullHandler())
        self.__logger = logger or self.__logger

        self.__rft_ctrl_if = ctrl_interface
        self.__rft_data_if = data_interface
        self.__joinargs = cmdutil.CmdUtil.joinargs
        self.__splitargs = cmdutil.CmdUtil.splitargs
        self.__split_response = cmdutil.CmdUtil.split_response
        self.__logger.debug("RftoolCommand __init__")
        self.__awg_to_adc_tile = {
            AwgId.AWG_0 : 0,
            AwgId.AWG_1 : 0,
            AwgId.AWG_2 : 1,
            AwgId.AWG_3 : 1,
            AwgId.AWG_4 : 2,
            AwgId.AWG_5 : 2,
            AwgId.AWG_6 : 3,
            AwgId.AWG_7 : 3 }
        self.__awg_to_dac_tile = {
            AwgId.AWG_0 : 1,
            AwgId.AWG_1 : 1,
            AwgId.AWG_2 : 1,
            AwgId.AWG_3 : 1,
            AwgId.AWG_4 : 0,
            AwgId.AWG_5 : 0,
            AwgId.AWG_6 : 0,
            AwgId.AWG_7 : 0 }
        return


    def get_fpga_design_version(self):
        """
        現在 FPGA にコンフィギュレーションされているデザインのバージョンを調べる

        Returns
        -------
        version : string
            バージョン情報を示す文字列.  ('デザイナID':作成年月日-'デザインID')
        """
        return self.__rft_ctrl_if.put("GetFpgaDesignVersion")


    def set_wave_sequence(self, awg_id, wave_sequence, *, num_repeats = 1):
        """
        波形シーケンスをAWGにセットする.

        Parameters
        ----------
        awg_id : AwgId
            wave_sequence をセットする AWG の ID
        wave_sequence : WaveSequence
            設定する波形シーケンス
        num_repeats : int
            波形シーケンスを繰り返す回数
            負の数を指定すると AWG を強制停止させるまでシーケンスを繰り返し続ける
        """
        if (not isinstance(wave_sequence, WaveSequence)):
            raise ValueError("invalid wave_sequence " + str(wave_sequence))

        if (not AwgId.has_value(awg_id)):
           raise ValueError("invalid awg_id  " + str(awg_id))
        
        if (not isinstance(num_repeats, int)) or\
           (num_repeats == 0 or 0xFFFFFFFE < num_repeats):
           raise ValueError("invalid num_repeats  " + str(num_repeats))

        infinite_repeat = 1 if num_repeats < 0 else 0
        data = wave_sequence.serialize()
        command = self.__joinargs("SetWaveSequence", [int(awg_id), num_repeats, infinite_repeat, len(data)])
        self.__rft_data_if.PutCmdWithData(command, data)


    def enable_awg(self, *awg_id_list):
        """
        引数で指定した AWG を有効にする

        Parameters
        ----------
        *awg_id_list : AwgId
            有効にする AWG の ID
        """
        enable_list = [0, 0, 0, 0, 0, 0, 0, 0]
        for awg_id in awg_id_list:
            if (not AwgId.has_value(awg_id)):
                raise ValueError("invalid awg_id  " + str(awg_id))
            enable_list[int(awg_id)] = 1

        command = self.__joinargs("EnableAwg", enable_list)
        self.__rft_ctrl_if.put(command)


    def disable_awg(self, *awg_id_list):
        """
        引数で指定した AWG を無効にする

        Parameters
        ----------
        *awg_id_list : AwgId
            無効にする AWG の ID
        """
        disable_list = [0, 0, 0, 0, 0, 0, 0, 0]
        for awg_id in awg_id_list:
            if (not AwgId.has_value(awg_id)):
                raise ValueError("invalid awg_id  " + str(awg_id))
            disable_list[int(awg_id)] = 1

        command = self.__joinargs("DisableAwg", disable_list)
        self.__rft_ctrl_if.put(command)


    def start_wave_sequence(self):
        """
        波形出力およびキャプチャ処理を開始する
        """
        command = "StartWaveSequence"
        self.__rft_ctrl_if.put(command)


    def is_wave_sequence_complete(self, awg_id):
        """
        波形シーケンスの出力が完了しているかどうかを取得する

        Parameters
        ----------
        awg_id : AwgId
            波形シーケンスの出力完了を調べる AWG の ID

        Returns
        -------
        status : int
            WAVE_SEQUENCE_NOT_COMPLETE -> 出力未完了
            WAVE_SEQUENCE_COMPLETE -> 出力完了 or 停止命令により停止した
            WAVE_SEQUENCE_ERROR -> 出力中にエラーが発生
        """ 
        if (not AwgId.has_value(awg_id)):
            raise ValueError("invalid awg_id  " + str(awg_id))
        command = self.__joinargs("IsWaveSequenceComplete", [int(awg_id)])
        res = self.__rft_ctrl_if.put(command)
        res = int(res)
        if res == 0:
            return AwgSaCmdResult.WAVE_SEQUENCE_NOT_COMPLETE
        elif res == 1:
            return AwgSaCmdResult.WAVE_SEQUENCE_COMPLETE
        elif res == 2:
            return AwgSaCmdResult.WAVE_SEQUENCE_ERROR
        
        return AwgSaCmdResult.UNKNOWN


    def is_awg_working(self, awg_id):
        """
        AWG が動作中かどうかを調べる

        Parameters
        ----------
        awg_id : AwgId
            動作中かどうかを調べる AWG の ID

        Returns
        -------
        status : bool
            True -> 動作中
            False -> 非動作中
        """ 
        if (not AwgId.has_value(awg_id)):
            raise ValueError("invalid awg_id  " + str(awg_id))
        command = self.__joinargs("IsAwgWorking", [int(awg_id)])
        res = self.__rft_ctrl_if.put(command)
        res = int(res)
        if res == 0:
            return False
        elif res == 1:
            return True
        
        return AwgSaCmdResult.UNKNOWN


    def set_capture_config(self, capture_config):
        """
        キャプチャシーケンスをAWGにセットする.

        Parameters
        ----------
        wave_sequence : WaveSequence
            設定するキャプチャシーケンス
        """
        if (not isinstance(capture_config, CaptureConfig)):
            raise ValueError("invalid capture_config " + str(capture_config))
        
        data = capture_config.serialize()
        command = self.__joinargs("SetCaptureConfig", [len(data)])
        self.__rft_data_if.PutCmdWithData(command, data)
        

    def read_capture_data(self, awg_id, step_id):
        """
        キャプチャデータを読み取る
        
        Parameters
        ----------
        awg_id : AwgId
            読み取るキャプチャステップを含むキャプチャシーケンスをセットしたキャプチャモジュールの ID
        step_id : int
            読み取るキャプチャステップのID
        
        Returns
        -------
        data : bytes
            キャプチャデータ
        """
        if (not AwgId.has_value(awg_id)):
            raise ValueError("invalid awg_id  " + str(awg_id))
        
        if (not isinstance(step_id, int) or (step_id < 0 or 0x7FFFFFFF < step_id)):
            raise ValueError("invalid step_id " + str(step_id))

        command = self.__joinargs("ReadCaptureData", [int(awg_id), step_id])
        self.__rft_data_if.send_command(command)
        res = self.__rft_data_if.recv_response() # キャプチャデータの前のコマンド成否レスポンス  [SA_SUCCESS/SA_FAILURE, data size]
        [result, data_size] = self.__split_response(res, ",")
        if (result == "AWG_SUCCESS"):
            data = self.__rft_data_if.recv_data(data_size)
            self.__rft_data_if.recv_response() # end of capture data

        res = self.__rft_data_if.recv_response() # end of 'ReadCaptureData' command
        if res[:5] == "ERROR":
            raise rfterr.RftoolExecuteCommandError(res)
        self.__logger.debug(res)
        return data


    def get_capture_data_size(self, awg_id, step_id):
        
        if (not AwgId.has_value(awg_id)):
            raise ValueError("invalid awg_id  " + str(awg_id))
        
        if (not isinstance(step_id, int) or (step_id < 0 or 0x7FFFFFFF < step_id)):
            raise ValueError("invalid step_id " + str(step_id))

        command = self.__joinargs("GetCaptureDataSize ", [int(awg_id), step_id])
        res = self.__rft_ctrl_if.put(command)
        return int(res)  # byte
        

    def initialize_awg_sa(self):
        """
        AWG および AWG 制御用ライブラリの初期化を行う
        """
        command = "InitializeAwgSa"
        self.__rft_ctrl_if.put(command)


    def is_capture_step_skipped(self, awg_id, step_id):
        """
        引数で指定したキャプチャステップがスキップされていたかどうかを調べる
        
        Parameters
        ----------
        awg_id : AwgId
            調べたいキャプチャステップを含むキャプチャシーケンスをセットした AWG の ID
        step_id : int
            調べたいキャプチャステップのID
        
        Returns
        -------
        flag : bool
            True -> スキップされた
            False -> スキップされていない (正常)
        """
        if (not AwgId.has_value(awg_id)):
            raise ValueError("invalid awg_id  " + str(awg_id))
        
        if (not isinstance(step_id, int) or (step_id < 0 or 0x7FFFFFFF < step_id)):
            raise ValueError("invalid step_id " + str(step_id))

        command = self.__joinargs("IsCaptureStepSkipped ", [int(awg_id), step_id])
        res = self.__rft_ctrl_if.put(command)
        return False if int(res) == 0 else True


    def is_accumulated_value_overranged(self, awg_id, step_id):
        """
        引数で指定したキャプチャステップで積算値の範囲オーバーが発生したかどうかを調べる
        
        Parameters
        ----------
        awg_id : AwgId
            調べたいキャプチャステップを含むキャプチャシーケンスをセットした AWG の ID
        step_id : int
            調べたいキャプチャステップのID
        
        Returns
        -------
        flag : bool
            True -> 範囲オーバーした
            False -> 範囲オーバーしていない (正常)
        """
        if (not AwgId.has_value(awg_id)):
            raise ValueError("invalid awg_id  " + str(awg_id))
        
        if (not isinstance(step_id, int) or (step_id < 0 or 0x7FFFFFFF < step_id)):
            raise ValueError("invalid step_id " + str(step_id))

        command = self.__joinargs("IsAccumulatedValueOverranged", [int(awg_id), step_id])
        res = self.__rft_ctrl_if.put(command)
        return False if int(res) == 0 else True


    def is_capture_data_fifo_overflowed(self, awg_id, step_id):
        """
        引数で指定したキャプチャステップで, ADC から送られる波形データを
        格納する FIFO のオーバーフローが発生したかどうかを調べる.        
        Parameters
        ----------
        awg_id : AwgId
            調べたいキャプチャステップを含むキャプチャシーケンスをセットした AWG の ID
        step_id : int
            調べたいキャプチャステップのID
        
        Returns
        -------
        flag : int
            True -> オーバーフローした
            False -> オーバーフローしていない (正常)
        """
        if (not AwgId.has_value(awg_id)):
            raise ValueError("invalid awg_id  " + str(awg_id))
        
        if (not isinstance(step_id, int) or (step_id < 0 or 0x7FFFFFFF < step_id)):
            raise ValueError("invalid step_id " + str(step_id))

        command = self.__joinargs("IsCaptureDataFifoOverflowed", [int(awg_id), step_id])
        res = self.__rft_ctrl_if.put(command)
        return False if int(res) == 0 else True


    def get_spectrum(self, awg_id, step_id, start_sample_idx, num_frames, *, is_iq_data = False):
        """
        キャプチャしたデータの FFT スペクトラムを取得する
        
        Parameters
        ----------
        awg_id : AwgId
            スペクトラムを取得したいデータをキャプチャした AWG の ID
        step_id : int
            スペクトラムを取得したいキャプチャステップのID
        start_sample_idx : int
            キャプチャデータ中のスペクトラムを得たい部分の先頭サンプルのインデックス. (0 始まり)
            I/Q データの場合は, まとめて 1 サンプルと数える.
        num_frames : int
            取得する FFT のフレーム数
        is_iq_data : bool
            キャプチャデータが I/Q データの場合 True. Real データの場合 False.
        
        Returns
        -------
        spectrum : bytes
            スペクトラムデータ
        """

        if (not AwgId.has_value(awg_id)):
            raise ValueError("invalid awg_id  " + str(awg_id))
        
        if (not isinstance(step_id, int) or (step_id < 0 or 0x7FFFFFFF < step_id)):
            raise ValueError("invalid step_id " + str(step_id))
        
        if (not isinstance(start_sample_idx, int) or start_sample_idx < 0):
            raise ValueError("invalid start_sample_idx " + str(start_sample_idx))

        if (not isinstance(num_frames, int) or num_frames < 0):
            raise ValueError("invalid num_frames " + str(num_frames))

        if (not isinstance(is_iq_data, bool)):
            raise ValueError("invalid is_iq_data " + str(is_iq_data))

        if (is_iq_data and start_sample_idx % 8 != 0):
           raise ValueError("'start_sample_idx' must be a multiple of 8 for I/Q data.  " + str(start_sample_idx))

        if ((not is_iq_data) and start_sample_idx % 16 != 0):
            raise ValueError("'start_sample_idx' must be a multiple of 16 for Real data.  " + str(start_sample_idx))

        is_iq_data = 1 if is_iq_data else 0
        command = self.__joinargs(
            "GetSpectrum", [int(awg_id), step_id, start_sample_idx, num_frames, is_iq_data])
        self.__rft_data_if.send_command(command)
        res = self.__rft_data_if.recv_response() # スペクトルデータの前のコマンド成否レスポンス  [SA_SUCCESS/SA_FAILURE, data size]
        [result, data_size] = self.__split_response(res, ",")

        if (result == "SA_SUCCESS"):
            spectrum = self.__rft_data_if.recv_data(data_size)
            self.__rft_data_if.recv_response() # end of spectrum data

        res = self.__rft_data_if.recv_response() # end of 'GetSpectrum' command
        if res[:5] == "ERROR":
            raise rfterr.RftoolExecuteCommandError(res)
        self.__logger.debug(res)
        return spectrum


    def get_fft_size(self):
        """
        スペクトラムアナライザの FFT サイズを返す
        """
        return 8192


    def set_digital_output_sequence(self, awg_id, dout_sequence):
        """
        デジタル出力シーケンスをハードウェアにセットする.

        Parameters
        ----------
        awg_id : AwgId
            このシーケンスのデジタル出力の基準となる波形を生成する AWG の ID
        dout_sequence : DigitalOutputSequence
            設定するデジタル出力シーケンス
        """
        if (not isinstance(dout_sequence, DigitalOutputSequence)):
            raise ValueError("invalid dout_sequence  " + str(dout_sequence))

        if (not AwgId.has_value(awg_id)):
           raise ValueError("invalid awg_id  " + str(awg_id))
        
        data = dout_sequence.serialize()
        command = self.__joinargs("SetDoutSequence", [int(awg_id), len(data)])
        self.__rft_data_if.PutCmdWithData(command, data)


    def is_digital_output_step_skipped(self, awg_id, step_id):
        """
        引数で指定したデジタル出力ステップがスキップされていたかどうかを調べる
        
        Parameters
        ----------
        awg_id : AwgId
            調べたいデジタル出力ステップを含むデジタル出力シーケンスをセットした AWG の ID
        step_id : int
            調べたいデジタル出力ステップのID
        
        Returns
        -------
        flag : int
            True -> スキップされた
            False -> スキップされていない (正常)
        """
        if (not AwgId.has_value(awg_id)):
            raise ValueError("invalid awg_id  " + str(awg_id))
        
        if (not isinstance(step_id, int) or (step_id < 0 or 0x7FFFFFFF < step_id)):
            raise ValueError("invalid step_id " + str(step_id))

        command = self.__joinargs("IsDoutStepSkipped", [int(awg_id), step_id])
        res = self.__rft_ctrl_if.put(command)
        return False if int(res) == 0 else True


    def get_waveform_sequence(self, awg_id):
        """
        awg_id で指定した AWG が出力する波形のサンプル値を保持するオブジェクトを取得する.

        Returns
        -------
        waveform_seq : FlattenedWaveformSequence, FlattenedIQWaveformSequence
            波形のサンプル値を保持するオブジェクト.
            awg_id で指定した AWG に Real データの波形シーケンスを設定した場合は, FlattenedWaveformSequence が返る.
            I/Q データの波形シーケンスを設定した場合は, FlattenedIQWaveformSequence が返る.
            [補足]
            戻り値のオブジェクトから参照できるサンプルデータは, WaveSequence.get_waveform_sequence(...) の場合と異なり, 
            実際に DAC に入力される値である.
        """
        if (not AwgId.has_value(awg_id)):
           raise ValueError("invalid awg_id  " + str(awg_id))

        wave_seq_params = self.__get_wave_seq_params(awg_id)

        command = self.__joinargs("GetWaveRAM", [int(awg_id)])
        self.__rft_data_if.send_command(command)
        res = self.__rft_data_if.recv_response() # 波形 RAM データの前のコマンド成否レスポンス  [SA_SUCCESS/SA_FAILURE, wave ram data size]
        [result, wave_ram_data_size] = self.__split_response(res, ",")
        
        if (result == "AWG_SUCCESS"):
            wave_ram_data = self.__rft_data_if.recv_data(wave_ram_data_size)
            self.__rft_data_if.recv_response() # end of wave ram data

        res = self.__rft_data_if.recv_response() # end of 'GetWaveRAM' command
        if res[:5] == "ERROR":
            raise rfterr.RftoolExecuteCommandError(res)
        self.__logger.debug(res)
        
        if wave_seq_params.is_iq_data:
            return FlattenedIQWaveformSequence.build_from_wave_ram(wave_seq_params, wave_ram_data)
        else:
            return FlattenedWaveformSequence.build_from_wave_ram(wave_seq_params, wave_ram_data)


    def __get_wave_seq_params(self, awg_id):
        """
        awg_id で指定した AWG に設定されている波形シーケンスのパラメータをバイトデータとして取得する
        """
        if (not AwgId.has_value(awg_id)):
           raise ValueError("invalid awg_id  " + str(awg_id))

        command = self.__joinargs("GetWaveSequenceParams", [int(awg_id)])
        self.__rft_data_if.send_command(command)
        res = self.__rft_data_if.recv_response() # パラメータの前のコマンド成否レスポンス  [SA_SUCCESS/SA_FAILURE, wave sequence param size]
        [result, seq_param_size] = self.__split_response(res, ",")

        if (result == "AWG_SUCCESS"):
            seq_params_bytes = self.__rft_data_if.recv_data(seq_param_size)
            self.__rft_data_if.recv_response() # end of wave seq param data

        res = self.__rft_data_if.recv_response() # end of 'GetWaveSequenceParams' command
        if res[:5] == "ERROR":
            raise rfterr.RftoolExecuteCommandError(res)
        self.__logger.debug(res)
        return WaveSequenceParams.build_from_bytes(seq_params_bytes)


    def get_adc_tile_id_by_awg_id(self, awg_id):
        """
        AWG に対応する ADC のタイル ID を取得する
        """
        if (not AwgId.has_value(awg_id)):
           raise ValueError("invalid awg_id  " + str(awg_id))
        return self.__awg_to_adc_tile[awg_id]


    def get_dac_tile_id_by_awg_id(self, awg_id):
        """
        AWG に対応する DAC のタイル ID を取得する
        """
        if (not AwgId.has_value(awg_id)):
           raise ValueError("invalid awg_id  " + str(awg_id))
        return self.__awg_to_dac_tile[awg_id]


    def sync_dac_tiles(self):
        """
        全ての DAC タイルを同期させる.
        """
        command = self.__joinargs("SyncMultiTiles", [1])
        self.__rft_ctrl_if.put(command)


    def sync_adc_tiles(self):
        """
        全ての ADC タイルを同期させる.
        """
        command = self.__joinargs("SyncMultiTiles", [0])
        self.__rft_ctrl_if.put(command)


    def external_trigger_on(self, *ext_trig_id_list):
        """
        引数で指定した外部トリガモジュールを起動する.
        起動したトリガモジュールは, トリガ条件を満たし次第トリガを発行する.

        Parameters
        ----------
        *ext_trig_id_list : ExternalTriggerId
            起動する 外部トリガモジュール の ID
        """
        enable_list = [0, 0, 0, 0, 0, 0, 0, 0]
        for ext_trig_id in ext_trig_id_list:
            if (not ExternalTriggerId.has_value(ext_trig_id)):
                raise ValueError("invalid external trigger id  " + str(ext_trig_id))
            enable_list[int(ext_trig_id)] = 1

        command = self.__joinargs("ExternalTriggerOn", enable_list)
        self.__rft_ctrl_if.put(command)


    def external_trigger_off(self, *ext_trig_id_list):
        """
        引数で指定した外部トリガモジュールを停止する.
        停止したトリガモジュールは, トリガを発行しない.

        Parameters
        ----------
        *ext_trig_id_list : ExternalTriggerId
            停止する 外部トリガモジュール の ID
        """
        enable_list = [0, 0, 0, 0, 0, 0, 0, 0]
        for ext_trig_id in ext_trig_id_list:
            if (not ExternalTriggerId.has_value(ext_trig_id)):
                raise ValueError("invalid external trigger id  " + str(ext_trig_id))
            enable_list[int(ext_trig_id)] = 1

        command = self.__joinargs("ExternalTriggerOff", enable_list)
        self.__rft_ctrl_if.put(command)


    def set_trigger_mode(self, awg_id, trig_mode):
        """
        引数で指定した AWG のトリガモードを設定する.

        Parameters
        ----------
        awg_id : AwgId
            トリガモードを設定する AWG の ID
        trig_mode : TriggerMode
            MANUAL -> AwgSaCommand.start_wave_sequence を呼ぶと AWG の処理が始まる
            EXTERNAL -> AwgSaCommand.external_trigger_on で起動した外部トリガモジュールがトリガを発行すると AWG の処理が始まる
        """
        if (not AwgId.has_value(awg_id)):
            raise ValueError("invalid awg_id  " + str(awg_id))
        
        if (not TriggerMode.has_value(trig_mode)):
            raise ValueError("invalid trig_mode  " + str(trig_mode))
        
        command = self.__joinargs("SetTriggerMode", [int(awg_id), int(trig_mode)])
        self.__rft_ctrl_if.put(command)


    def get_trigger_mode(self, awg_id):
        """
        引数で指定した AWG のトリガモードを取得する.

        Parameters
        ----------
        awg_id : AwgId
            トリガモードを取得する AWG の ID
        
        Returns
        -------
        trigger_mode : TriggerMode
            引数で指定した AWG のトリガモード
        """
        if (not AwgId.has_value(awg_id)):
            raise ValueError("invalid awg_id  " + str(awg_id))
        
        command = self.__joinargs("GetTriggerMode", [int(awg_id)])
        res = self.__rft_ctrl_if.put(command)        
        return TriggerMode.of(int(res))


    def set_external_trigger_param(self, ext_trig_id, param_id, param):
        """
        引数で指定した外部トリガモジュールにトリガパラメータを設定する

        Parameters
        ----------
        ext_trig_id : ExternalTriggerId
            パラメータを設定する外部トリガモジュールの ID
        param_id : int
            値を設定するパラメータの番号
        param : signed int (4 bytes) or unsigned int (4 bytes)
            設定するパラメータ
        """
        if (not ExternalTriggerId.has_value(ext_trig_id)):
            raise ValueError("invalid external trigger id  " + str(ext_trig_id))

        if (not isinstance(param_id, int) or (param_id < 0)):
            raise ValueError("invalid param_id " + str(param_id))

        if (not isinstance(param_id, int) or (param < -2147483648) or (4294967295 < param)):
            raise ValueError("invalid param " + str(param))

        if (param < 0):
            param = param + (1 << 32) # to unsigned

        command = self.__joinargs("SetExternalTriggerParam", [int(ext_trig_id), param_id, param])
        self.__rft_ctrl_if.put(command)


    def get_external_trigger_param(self, ext_trig_id, param_id, to_signed):
        """
        引数で指定した外部トリガモジュールのトリガパラメータを取得する

        Parameters
        ----------
        ext_trig_id : ExternalTriggerId
            パラメータを取得する外部トリガモジュールの ID
        param_id : int
            値を取得するパラメータの番号
        to_signed : bool
            取得したパラメータ (4 bytes) を符号付き整数で返す場合 true, 符号無し整数で返す場合 false
        
        Returns
        -------
        trigger_param : int
            引数で指定したトリガモジュールに設定されているトリガパラメータ
        """
        if (not ExternalTriggerId.has_value(ext_trig_id)):
            raise ValueError("invalid external trigger id  " + str(ext_trig_id))

        if (not isinstance(param_id, int) or (param_id < 0)):
            raise ValueError("invalid param_id " + str(param_id))

        command = self.__joinargs("GetExternalTriggerParam", [int(ext_trig_id), param_id])
        res = self.__rft_ctrl_if.put(command)
        trigger_param = int(res) # コマンドの戻り値は unsigned
        if to_signed and (trigger_param & 0x80000000):
            trigger_param = trigger_param - 0x100000000
        
        return trigger_param


    def is_external_trigger_active(self, ext_trig_id):
        """
        引数で指定した外部トリガモジュールが動作中かどうか調べる

        Parameters
        ----------
        ext_trig_id : ExternalTriggerId
            動作中かどうかを調べる外部トリガモジュールの ID

        Returns
        -------
        flag : bool
            true -> 外部トリガモジュールが動作中
            false -> 外部トリガモジュールが停止中
        """
        if (not ExternalTriggerId.has_value(ext_trig_id)):
            raise ValueError("invalid external trigger id  " + str(ext_trig_id))

        command = self.__joinargs("IsExternalTriggerActive", [int(ext_trig_id)])
        res = self.__rft_ctrl_if.put(command)
        return False if int(res) == 0 else True


    def is_external_trigger_signal_sent(self, ext_trig_id):
        """
        引数で指定した外部トリガモジュールが, トリガを発行したかどうかを調べる

        Parameters
        ----------
        ext_trig_id : ExternalTriggerId
            トリガを発行したかどうかを調べる外部トリガモジュールの ID

        Returns
        -------
        flag : bool
            true -> トリガを発行した
            false -> トリガを発行していない
        """
        if (not ExternalTriggerId.has_value(ext_trig_id)):
            raise ValueError("invalid external trigger id  " + str(ext_trig_id))

        command = self.__joinargs("IsExternalTriggerSignalSent", [int(ext_trig_id)])
        res = self.__rft_ctrl_if.put(command)
        return False if int(res) == 0 else True


    def terminate_awgs(self, *awg_list):
        """
        引数で指定した AWG に停止命令を発行する.
        AWG が停止命令を受け取ったときに実行中のキャプチャは最後まで実行される.
        AWG の停止までブロックするわけではないので, 停止の確認は is_wave_sequence_complete メソッドの戻り値が
        AwgSaCmdResult.WAVE_SEQUENCE_COMPLETE かどうかで判断すること.

        Parameters
        ----------
        *awg_list : AwgId
            停止させる AWG の ID
        """
        termination_flag_list = [0, 0, 0, 0, 0, 0, 0, 0]
        for awg_id in awg_list:
            if (not AwgId.has_value(awg_id)):
                raise ValueError("invalid awg id  " + str(awg_id))
            termination_flag_list[int(awg_id)] = 1

        command = self.__joinargs("TerminateAwgs", termination_flag_list)
        self.__rft_ctrl_if.put(command)


    def terminate_all_awgs(self):
        """
        全ての AWG に停止命令を発行する.
        AWG が停止命令を受け取ったときに実行中のキャプチャは最後まで実行される.
        AWG が停止するまでブロックするわけではないので, 停止の確認は is_wave_sequence_complete メソッドの戻り値が
        AwgSaCmdResult.WAVE_SEQUENCE_COMPLETE かどうかで判断すること.
        """
        self.__rft_ctrl_if.put("TerminateAllAwgs")


    def read_dram(self, offset, size):
        """
        PL に接続された外部 DRAM の任意のアドレスからデータを読み取る.
        
        Parameters
        ----------
        offset : int
            データを取得するアドレス
        size : int
            読み取るサイズ (Bytes)
        
        Returns
        -------
        data : bytes
            DRAM のデータ
        """
        if (not isinstance(offset, int) or (offset < 0 or 0xFFFFFFFF < offset)):
            raise ValueError("invalid offset " + str(offset))

        if (not isinstance(size, int) or (size <= 0 or PL_DDR4_RAM_SIZE < (size + offset))):
            raise ValueError(
                "invalid read addr range  ({} - {})\n".format(offset, size + offset - 1) + 
                "The valid one is 0 to {}.".format(PL_DDR4_RAM_SIZE - 1))

        command = self.__joinargs("ReadDram", [offset, size])
        self.__rft_data_if.send_command(command)
        res = self.__rft_data_if.recv_response().rstrip('\r\n') # キャプチャデータの前のコマンド成否レスポンス  AWG_SUCCESS/AWG_FAILURE
        if (res == "AWG_SUCCESS"):
            data = self.__rft_data_if.recv_data(size)
            res = self.__rft_data_if.recv_response() # end of capture data

        res = self.__rft_data_if.recv_response() # end of 'ReadDram' command
        if res[:5] == "ERROR":
            raise rfterr.RftoolExecuteCommandError(res)
        self.__logger.debug(res)
        return data


    def get_capture_section_info(self, awg_id, step_id):
        """
        キャプチャモジュールの ID とキャプチャステップから, 
        対応するキャプチャデータの格納先の RAM のアドレスとデータサイズ (Bytes) を取得する.
        set_capture_config でキャプチャシーケンスをキャプチャモジュールにセットしてから呼ぶこと.

        Parameters
        ----------
        awg_id : AwgId
            引数で指定したキャプチャデータを取得するキャプチャモジュールの ID
        step_id : int
            引数で指定したキャプチャデータを取得するステップの ID
        
        Returns
        -------
        (addr, data_size) : (int, int)
            引数で指定したキャプチャデータの格納先である RAM のアドレスとデータサイズ
        """
        if (not AwgId.has_value(awg_id)):
            raise ValueError("invalid awg_id  " + str(awg_id))
        
        if (not isinstance(step_id, int) or (step_id < 0 or 0x7FFFFFFF < step_id)):
            raise ValueError("invalid step_id " + str(step_id))

        command = self.__joinargs("GetCaptureSectionInfo", [int(awg_id), step_id])
        res = self.__rft_ctrl_if.put(command)
        [addr, data_size] = self.__split_response(res, ",")
        return (int(addr), int(data_size))
