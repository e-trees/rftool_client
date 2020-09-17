#!/usr/bin/env python3
# coding: utf-8

import struct

class AwgWave(object):
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
    _WAVE_MAX = 4

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
           (wave_type < AwgWave.SINE or AwgWave._WAVE_MAX <= wave_type):
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


        self.wave_type = wave_type
        self.frequency = float(frequency)
        if float(phase) < 0.0:
            self.phase = float(phase) % -360.0 + 360.0
        else:
            self.phase = float(phase) % 360.0
        
        self.amplitude = float(amplitude)
        self.offset = float(offset)
        self.num_cycles = num_cycles
        self.duty_cycle = float(duty_cycle)
        self.crest_pos = float(crest_pos)
        self.variance = float(variance)
        self.domain_begin = float(domain_begin)
        self.domain_end = float(domain_end)
        return

    def serialize(self):
        data = bytearray()
        data += self.wave_type.to_bytes(4, 'little')
        data += struct.pack("<d", self.frequency)
        data += struct.pack("<d", self.phase)
        data += struct.pack("<d", self.amplitude)
        data += struct.pack("<d", self.offset)
        data += self.num_cycles.to_bytes(4, 'little')
        data += struct.pack("<d", self.duty_cycle)
        data += struct.pack("<d", self.crest_pos)
        data += struct.pack("<d", self.variance)
        data += struct.pack("<d", self.domain_begin)
        data += struct.pack("<d", self.domain_end)
        return data

    def get_duration(self):
        """
        この波形が出力される時間 (単位:ns) を取得する
        """
        return 1000.0 * self.num_cycles / self.frequency

