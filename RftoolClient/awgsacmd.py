#!/usr/bin/env python3
# coding: utf-8

from RftoolClient import cmdutil, rfterr
import logging
from AwgSa import WaveSequence
from AwgSa import AwgId
from AwgSa import AwgSaCmdResult
from AwgSa import CaptureConfig
from AwgSa import DigitalOutputSequence
from AwgSa import WaveSequenceParams
from AwgSa import FlattenedWaveformSequence
from AwgSa import FlattenedIQWaveformSequence

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
        return


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
        """
        if (not isinstance(wave_sequence, WaveSequence)):
            raise ValueError("invalid wave_sequence " + str(wave_sequence))

        if (not AwgId.has_value(awg_id)):
           raise ValueError("invalid awg_id  " + str(awg_id))
        
        if (not isinstance(num_repeats, int)) or\
           (num_repeats <= 0 or 0xFFFFFFFE <= num_repeats):
           raise ValueError("invalid num_repeats  " + str(num_repeats))
        
        data = wave_sequence.serialize()
        command = self.__joinargs("SetWaveSequence", [int(awg_id), num_repeats, len(data)])
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
            WAVE_SEQUENCE_COMPLETE -> 出力完了
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
            読み取るキャプチャステップを含むキャプチャシーケンスをセットした AWG の ID
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
        flag : int
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
        flag : int
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
