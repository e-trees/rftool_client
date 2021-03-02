#!/usr/bin/env python3
# coding: utf-8

import struct
import copy
import numpy as np
from . import awgsaerror

class WaveParamSerializer(object):
    
    def _serialize_params(
        self,
        wave_type,
        frequency,
        phase,
        amplitude,
        offset,
        num_cycles,
        duty_cycle,
        crest_pos,
        variance,
        domain_begin,
        domain_end,
        num_any_wave_samples):

        data = bytearray()
        data += wave_type.to_bytes(4, 'little')
        data += struct.pack("<d", frequency)
        data += struct.pack("<d", phase)
        data += struct.pack("<d", amplitude)
        data += struct.pack("<d", offset)
        data += num_cycles.to_bytes(4, 'little')
        data += struct.pack("<d", duty_cycle)
        data += struct.pack("<d", crest_pos)
        data += struct.pack("<d", variance)
        data += struct.pack("<d", domain_begin)
        data += struct.pack("<d", domain_end)
        data += num_any_wave_samples.to_bytes(4, 'little')
        return data


class AwgWave(WaveParamSerializer):
    """
    波形情報を持つオブジェクトを作成する.

    Parameters
    ----------
    wave_type : int
        波の種類. (SINE, SQUARE, SAWTOOTH, GAUSSIAN)
    frequency : float
        周波数. (MHz)
    phase : float
        位相. (degree)
    amplitude : float
        振幅.
    offset : float
        DCオフセット.
    num_cycles : int
        波の個数.
    dudy_cycle : float
        デユーティー比[%]. SQUARE でのみ有効.  (0 ~ 100)
    crest_pos : float
        変位が最大になる時間軸の位置. SAWTOOTH でのみ有効.  (0.0 ~ 1.0)
    variance : float
        分散. (GAUSSIAN でのみ有効)
    domain_begin : float
        定義域の始点. (GAUSSIAN でのみ有効)
    domain_end : float
        定義域の終点. (GAUSSIAN でのみ有効)
    """
    SINE = 0
    SQUARE = 1
    SAWTOOTH = 2
    GAUSSIAN = 3
    __WAVE_MAX = 4

    def __init__(
        self,
        wave_type,
        frequency, 
        *,
        phase = 0.0,
        amplitude = 32760,
        offset = 0.0,
        num_cycles = 1,
        duty_cycle = 50.0,
        crest_pos = 1.0,
        variance = 1.0,
        domain_begin = -2.0,
        domain_end = 2.0):

        if (not isinstance(wave_type, int)) or\
           (wave_type < AwgWave.SINE or AwgWave.__WAVE_MAX <= wave_type):
            raise ValueError("invalid wave type  " + str(wave_type))
        
        if (not isinstance(frequency, (int, float)) or\
           (frequency <= 0)):
            raise ValueError("invalid frequency  " + str(frequency))
        
        if not isinstance(phase, (int, float)):
            raise ValueError("invalid phase  " + str(phase))
        
        if not isinstance(amplitude, (int, float)):
            raise ValueError("invalid amplitude  " + str(amplitude))
        
        if not isinstance(offset, (int, float)):
            raise ValueError("invalid offset  " + str(offset))

        if (not isinstance(num_cycles, int) or (num_cycles <= 0 or 0xFFFFFFFE < num_cycles)):
            raise ValueError("invalid number of cycles " + str(num_cycles))
        
        if (not isinstance(duty_cycle, (int, float)) or\
           (duty_cycle < 0.0 or 100.0 < duty_cycle)):
           raise ValueError("invalid duty cycle  " + str(duty_cycle))

        if (not isinstance(crest_pos, (int, float)) or\
           (crest_pos < 0.0 or 1.0 < crest_pos)):
           raise ValueError("invalid sawtooth max pos  " + str(duty_cycle))

        if (not isinstance(variance, (int, float)) or (variance <= 0.0)):
           raise ValueError("invalid variance  " + str(variance))

        if (not isinstance(domain_begin, (int, float))):
           raise ValueError("invalid beginning of the domain of the definition  " + str(domain_begin))
        
        if (not isinstance(domain_end, (int, float))):
           raise ValueError("invalid end of the domain of the definition  " + str(domain_end))


        self.__wave_type = wave_type
        self.__frequency = float(frequency)
        if float(phase) < 0.0:
            self.__phase = float(phase) % -360.0 + 360.0
        else:
            self.__phase = float(phase) % 360.0
        
        self.__amplitude = float(amplitude)
        self.__offset = float(offset)
        self.__num_cycles = num_cycles
        self.__duty_cycle = float(duty_cycle)
        self.__crest_pos = float(crest_pos)
        self.__variance = float(variance)
        self.__domain_begin = float(domain_begin)
        self.__domain_end = float(domain_end)
        return


    def serialize(self):
        data = self._serialize_params(
            self.__wave_type, self.__frequency, self.__phase,
            self.__amplitude, self.__offset, self.__num_cycles,
            self.__duty_cycle, self.__crest_pos, self.__variance,
            self.__domain_begin, self.__domain_end, 0)
        return data


    def get_duration(self):
        """
        この波形が出力される時間 (単位:ns) を取得する
        """
        return 1000.0 * self.__num_cycles / self.__frequency


    def get_wave_type(self):
        return self.__wave_type


    def get_frequency(self):
        """
        この波形の周波数を返す. (単位:MHz)
        """
        return self.__frequency


    def get_phase(self):
        return self.__phase


    def get_amplitude(self):
        return self.__amplitude


    def get_offset(self):
        return self.__offset


    def get_num_cycles(self):
        return self.__num_cycles


    def get_duty_cycle(self):
        return self.__duty_cycle


    def get_crest_pos(self):
        return self.__crest_pos


    def get_variance(self):
        return self.__variance


    def get_domain_begin(self):
        return self.__domain_begin


    def get_domain_end(self):
        return self.__domain_end


class AwgAnyWave(WaveParamSerializer):
    """
    任意のサンプル値を持つ波形オブジェクトを作成する

    Parameters
    ----------
    sampling_rate : float
        この波形を出力する際のサンプリングレート (単位:Msps)
        
    samples : numpy.ndarray
        サンプル値の配列.
        dtype は int16 とすること.
    """

    __ANY_WAVE = 1000

    def __init__(self, samples, num_cycles):
        
        if (not isinstance(samples, np.ndarray)):
            raise ValueError("invalid samples " + str(samples))

        if (samples.dtype != np.int16):
            raise ValueError("The type of samples must be numpy.int16.  " + str(samples.dtype))

        if (not isinstance(num_cycles, int) or (num_cycles <= 0 or 0xFFFFFFFE < num_cycles)):
            raise ValueError("invalid number of cycles " + str(num_cycles))

        if (len(samples) == 0):
            raise ValueError("samples has no data.")

        self.__sampling_rate = None
        self.__samples = copy.deepcopy(samples)
        self.__num_cycles = num_cycles
        return


    def get_duration(self):
        """
        この波形が出力される時間 (単位:ns) を取得する
        """
        return 1000.0 * self.__num_cycles / self.get_frequency()


    def get_frequency(self):
        """
        この波形の周波数を返す. (単位:MHz)
        """
        if self.__sampling_rate is None:
            raise awgsaerror.InvalidOperationError("The sampling rate has not been set.")
        return self.__sampling_rate / len(self.__samples)


    def get_samples(self):
        return copy.deepcopy(self.__samples)


    def _set_sampling_rate(self, sampling_rate):
        """
        このメソッドを AwgSa パッケージ外から呼ばないこと!!
        """
        if not isinstance(sampling_rate, (int, float)):
            raise ValueError("invalid samplin rate  " + str(sampling_rate))
        self.__sampling_rate = float(sampling_rate)


    def get_num_cycles(self):
        return self.__num_cycles


    def serialize(self):
        data = self._serialize_params(
            AwgAnyWave.__ANY_WAVE, self.get_frequency(), 0.0,
            0.0, 0.0, self.__num_cycles,
            0.0, 0.0, 0.0,
            0.0, 0.0, len(self.__samples))
        data += self.__samples.tobytes()
        return data


class AwgIQWave(object):
    """
    I 相 と Q 相の波形を持つオブジェクトを作成する.

    Parameters
    ----------
    i_wave : AwgWave
        I 相の波形
    q_wave : AwgWave
        Q 相の波形
    """
    def __init__(self, i_wave, q_wave):

        if not isinstance(i_wave, (AwgWave, AwgAnyWave)):
            raise ValueError("invalid i_wave " + str(i_wave))

        if not isinstance(q_wave, (AwgWave, AwgAnyWave)):
            raise ValueError("invalid q_wave " + str(q_wave))

        if i_wave.get_num_cycles() != q_wave.get_num_cycles():
            raise ValueError(
                "The number of cycles of I wave and Q wave must be the same.\n" + 
                "I wave cycles = " + str(i_wave.get_num_cycles()) + "    " + 
                "Q wave cycles = " + str(q_wave.get_num_cycles()))

        self.__i_wave = i_wave
        self.__q_wave = q_wave
        return


    def get_i_wave(self):
        """
        I 相の波形を取得する
        """
        return self.__i_wave


    def get_q_wave(self):
        """
        Q 相の波形を取得する
        """
        return self.__q_wave


    def get_duration(self):
        """
        この波形が出力される時間 (単位:ns) を取得する.
        I/Q データの出力時間は, I 相と Q 相の長い方の出力時間である.
        """
        return max(self.__i_wave.get_duration(), self.__q_wave.get_duration())


    def serialize(self):
        data = bytearray()
        data += self.__i_wave.serialize()
        data += self.__q_wave.serialize()
        return data
