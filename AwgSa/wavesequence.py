#!/usr/bin/env python3
# coding: utf-8

from . import AwgWave, AwgIQWave
import struct

class WaveSequence(object):
    """波形ステップのシーケンスを保持する"""
    _MIN_SAMPLING_RATE = 1000.0
    _MAX_SAMPLING_RATE = 6554.0
    _MAX_WAVE_STEPS = 32

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
           (sampling_rate < WaveSequence._MIN_SAMPLING_RATE or WaveSequence._MAX_SAMPLING_RATE < sampling_rate)):
           raise ValueError("invalid sampling rate  " + str(sampling_rate))

        if not isinstance(is_iq_data, bool):
            raise ValueError("invalid is_iq_data  " + str(is_iq_data))

        self.sampling_rate = sampling_rate
        self.is_iq_data = 1 if is_iq_data else 0
        self.wave_step_list = {}
        return


    def add_step(self, step_id, wave, *, interval = 0):
        """
        波形ステップを追加する
        
        Parameters
        ----------
        step_id : int
            波形ステップID.  波形シーケンスの波形は, 波形ステップID が小さい順に出力される.
        wave : AwgWave
            AwgWave オブジェクト
        interval : float
            このステップの波形出力開始から次のステップの波形出力開始までの間隔. (単位:ns)
        """
        if (not isinstance(step_id, int) or (step_id < 0 or 0x7FFFFFFF < step_id)):
            raise ValueError("invalid step_id " + str(step_id))

        if (step_id in self.wave_step_list):
            raise ValueError("The step id (" + str(step_id) + ") is already registered.")

        if (len(self.wave_step_list) == self._MAX_WAVE_STEPS):
            raise ValueError("No more steps can be added. (max=" + str(self._MAX_WAVE_STEPS) + ")")

        if (not isinstance(wave, AwgWave) and
            not isinstance(wave, AwgIQWave)):
            raise ValueError("invalid wave " + str(wave))

        if (not isinstance(interval, (float, int)) or 1.0e+10 < interval):
            raise ValueError("invalid interval " + str(interval))

        self.wave_step_list[step_id] = (wave, float(interval))
        return self


    def serialize(self):
        
        data = bytearray()
        data += "WSEQ".encode('utf-8')
        data += struct.pack("<d", self.sampling_rate)
        data += self.is_iq_data.to_bytes(4, 'little')
        data += self.num_wave_steps().to_bytes(4, 'little')

        wave_step_list = sorted(self.wave_step_list.items())
        overhead = 10 * 1 / 3 # FPGA の AWG スタートにかかるオーバーヘッド (ns) 300MHz x 1clk
        for elem in wave_step_list:
            step_id = elem[0]
            wave = elem[1][0]
            interval = elem[1][1]
            interval = max(interval - overhead, wave.get_duration() - overhead, 0.0)
            data += step_id.to_bytes(4, 'little')
            data += struct.pack("<d", interval)
            data += wave.serialize()

        return data
    

    def num_wave_steps(self):
        return len(self.wave_step_list)


    def get_step_duration(self, step_id):
        """
        引数で指定したステップの開始から次のステップの開始までの時間 (単位:ns) を返す.
        ステップの波形の出力時間より interval が長い場合, interval が返る.
        そうでない場合, 波形の出力時間が返る.

        Parameters
        ----------
        step_id : int
            時間を調べたいステップ の ID

        Returns
        ----------
        duration : float
            引数で指定したステップの開始から次のステップの開始までの時間 (単位:ns)
        """

        if not step_id in self.wave_step_list:
            raise ValueError("invalid step_id " + str(step_id))
        
        return max(self.wave_step_list[step_id][0].get_duration(), self.wave_step_list[step_id][1])


    def get_whole_duration(self):
        """
        この波形シーケンスが持つ全ステップの時間の合計 (単位:ns) を返す.
        Returns
        ----------
        duration : float
            この波形シーケンスが持つ全ステップの時間の合計 (単位:ns)
        """    
        duration = 0.0
        for key in self.wave_step_list.keys():
            duration += self.get_step_duration(key)

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
        if not step_id in self.wave_step_list:
            raise ValueError("invalid step_id " + str(step_id))
        
        return self.wave_step_list[step_id][0]
