#!/usr/bin/env python3
# coding: utf-8

from . import AwgWave, AwgAnyWave, AwgIQWave
from .flattenedwaveformsequence import FlattenedWaveformSequence, FlattenedIQWaveformSequence
import struct
import copy

class WaveSequence(object):
    """波形ステップのシーケンスを保持する"""
    __MIN_SAMPLING_RATE = 1000.0
    __MAX_SAMPLING_RATE = 6554.0
    __MAX_WAVE_STEPS = 64

    def __init__(self, sampling_rate, *, is_iq_data = False):
        """
        波形シーケンスオブジェクトを作成する.
        
        Parameters
        ----------
        sampling_rate : float
            DAC サンプリングレート [Msps]
        is_iq_data : bool
            I/Q データを取得するかどうか (True: I/Q データを取得する, False: Real データを取得する)
        """

        if (not isinstance(sampling_rate, (int, float)) or\
           (sampling_rate < WaveSequence.__MIN_SAMPLING_RATE or WaveSequence.__MAX_SAMPLING_RATE < sampling_rate)):
           raise ValueError("invalid sampling rate  " + str(sampling_rate))

        if not isinstance(is_iq_data, bool):
            raise ValueError("invalid is_iq_data  " + str(is_iq_data))

        self.__sampling_rate = sampling_rate
        self.__is_iq_data = 1 if is_iq_data else 0
        self.__step_id_to_wave = {}
        self.__step_id_to_post_blank = {}
        return


    def add_step(self, step_id, wave, *, post_blank = 0):
        """
        波形ステップを追加する.

        Parameters
        ----------
        step_id : int
            波形ステップID.  波形シーケンスの波形は, 波形ステップID が小さい順に出力される.
        wave : AwgWave, AwgIQWave, AwgAnyWave
            波形ステップで出力する波形の波形オブジェクト
        post_blank : float
            このステップの波形の出力終了から次のステップの波形の出力開始までの間隔. (単位:ns)
            波形ステップの終了から開始までの間隔は, post_blank の値に関わらず最大 60 ns ほど空く場合がある.
        """
        if (not isinstance(step_id, int) or (step_id < 0 or 0x7FFFFFFF < step_id)):
            raise ValueError("invalid step_id " + str(step_id))

        if (step_id in self.__step_id_to_wave):
            raise ValueError("The step id (" + str(step_id) + ") is already registered.")

        if (len(self.__step_id_to_wave) == self.__MAX_WAVE_STEPS):
            raise ValueError("No more steps can be added. (max=" + str(self.__MAX_WAVE_STEPS) + ")")

        if (not isinstance(post_blank, (float, int))):
            raise ValueError("invalid post_blank " + str(post_blank))

        self.__check_wave_type(wave)
        wave = copy.deepcopy(wave)
        self.__set_sampling_rate_to_wave(wave)
        self.__step_id_to_wave[step_id] = wave

        if wave.get_duration() != float('inf'):
            interval = float(wave.get_duration() + post_blank)
            if 1.4e+10 < interval:
                raise ValueError("The time from the start to the end of the step {} is too long.".format(step_id))
        else:
            post_blank = 0

        self.__step_id_to_post_blank[step_id] = post_blank
        return self


    def __check_wave_type(self, wave):
        
        if self.__is_iq_data == 0 and (isinstance(wave, (AwgWave, AwgAnyWave))):
            return

        if self.__is_iq_data == 1 and isinstance(wave, AwgIQWave):
            return
        
        if self.__is_iq_data == 1 and not isinstance(wave, AwgIQWave):
            raise ValueError("The type of the wave added to an I/Q wave sequence must be AwgIQWave.  " + str(type(wave)))

        raise ValueError("invalid wave " + str(wave))


    def __set_sampling_rate_to_wave(self, wave):
        """
        wave から辿れる AwgAnyWave にサンプリングレートを設定する
        """
        if isinstance(wave, AwgAnyWave):
            wave._set_sampling_rate(self.__sampling_rate)

        if isinstance(wave, AwgIQWave):
            if isinstance(wave.get_i_wave(), AwgAnyWave):
                wave.get_i_wave()._set_sampling_rate(self.__sampling_rate)
            if isinstance(wave.get_q_wave(), AwgAnyWave):
                wave.get_q_wave()._set_sampling_rate(self.__sampling_rate)


    def serialize(self):
        
        data = bytearray()
        data += "WSEQ".encode('utf-8')
        data += struct.pack("<d", self.__sampling_rate)
        data += self.__is_iq_data.to_bytes(4, 'little')
        data += self.num_wave_steps().to_bytes(4, 'little')
        wave_list = sorted(self.__step_id_to_wave.items())
        for step_id, wave in wave_list:
            post_blank = self.__step_id_to_post_blank[step_id]
            data += step_id.to_bytes(4, 'little')
            data += struct.pack("<d", post_blank)
            data += wave.serialize()

        return data
    

    def num_wave_steps(self):
        return len(self.__step_id_to_wave)


    def get_step_interval(self, step_id):
        """
        引数で指定したステップの開始から次のステップの開始までの時間 (単位:ns) を返す.

        Parameters
        ----------
        step_id : int
            時間を調べたいステップ の ID

        Returns
        ----------
        duration : float
            引数で指定したステップの開始から次のステップの開始までの時間 (単位:ns)
            float 型の
        """
        if not step_id in self.__step_id_to_wave:
            raise ValueError("invalid step_id " + str(step_id))
            
        return self.__step_id_to_wave[step_id].get_duration() + self.__step_id_to_post_blank[step_id]


    def get_whole_duration(self):
        """
        この波形シーケンスが持つ全ステップの時間の合計 (単位:ns) を返す.
        Returns
        ----------
        duration : float
            この波形シーケンスが持つ全ステップの時間の合計 (単位:ns)
        """    
        duration = 0.0
        for key in self.__step_id_to_wave.keys():
            duration += self.get_step_interval(key)

        return duration


    def get_wave(self, step_id):
        """
        引数の ステップID に対応する AwgWave オブジェクトを取得する
        
        Parameters
        ----------
        step_id : int
            波形をオブジェクトを取得したいステップ の ID

        Returns
        ----------
        duration : AwgWave
            引数の ステップID に対応する AwgWave オブジェクト (単位:ns)
        """        
        if not step_id in self.__step_id_to_wave:
            raise ValueError("invalid step_id " + str(step_id))
        
        return self.__step_id_to_wave[step_id]


    def get_waveform_sequence(self):
        """
        この波形シーケンスに登録された波形のサンプルデータを参照するためのオブジェクトを取得する.
        [補足]
        戻り値のオブジェクトから参照できるサンプルデータは, python ライブラリ内部で計算される.
        実際に DAC に入力されるサンプルデータは, AWG のファームウェア内部で計算されるため, 
        戻り値のオブジェクトから参照できるサンプルデータと完全に一致する保証はない
        
        Returns
        -------
        FlattenedWaveformSequence
        """
        if self.__is_iq_data == 1:
            return FlattenedIQWaveformSequence.build_from_wave_obj(
                self.__step_id_to_wave, self.__step_id_to_post_blank, self.__sampling_rate)
        else:
            return FlattenedWaveformSequence.build_from_wave_obj(
                self.__step_id_to_wave, self.__step_id_to_post_blank, self.__sampling_rate)


    def get_step_id_list(self):
        """
        この波形シーケンスに登録されたステップの ID を出力順に並べてリストにして返す.
        """
        return sorted(self.__step_id_to_wave.keys())
