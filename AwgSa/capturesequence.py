#!/usr/bin/env python3
# coding: utf-8

from . import AwgCapture
import struct

class CaptureSequence(object):
    """ キャプチャステップからなるシーケンスを保持する """
    _MIN_SAMPLING_RATE = 1000.0
    _MAX_SAMPLING_RATE = 4096.0
    _MAX_CAPTURE_STEPS = 32

    def __init__(
        self,
        sampling_rate,
        *,
        enable_iq_mixer = False):
        """
        キャプチャシーケンスオブジェクトを作成する.

        Parameters
        ----------
        sampling_rate : float
            ADC サンプリングレート [Msps]
        enable_iq_mixer : bool
            IQ Mixer を有効にするかどうか (True:有効, False:無効)
        """

        if (not isinstance(sampling_rate, (int, float)) or\
           (sampling_rate < CaptureSequence._MIN_SAMPLING_RATE or CaptureSequence._MAX_SAMPLING_RATE < sampling_rate)):
           raise ValueError("invalid sampling rate  " + str(sampling_rate))
        
        if not isinstance(enable_iq_mixer, bool):
            raise ValueError("invalid enable_iq_mixer  " + str(enable_iq_mixer))
        
        self.sampling_rate = float(sampling_rate)
        self.enable_iq_mixer = 1 if enable_iq_mixer else 0
        self.capture_list = {}
        return


    def add_step(self, step_id, capture):
        """
        キャプチャステップを追加する
        
        Parameters
        ----------
        step_id : int
            キャプチャ開始の基準となる波形ステップID.
        capture : AwgCapture
            AwgCapture オブジェクト
        """
        if (not isinstance(step_id, int) or (step_id < 0 or 0x7FFFFFFF < step_id)):
            raise ValueError("invalid step_id " + str(step_id))
        
        if (step_id in self.capture_list):
            raise ValueError("The step id (" + str(step_id) + ") is already registered.")

        if (len(self.capture_list) == self._MAX_CAPTURE_STEPS):
            raise ValueError("No more captures can be added. (max=" + str(self._MAX_CAPTURE_STEPS) + ")")

        if (not isinstance(capture, AwgCapture)):
            raise ValueError("invalid capture " + str(capture))

        self.capture_list[step_id] = capture
        return self


    def serialize(self):

        data = bytearray()
        data += struct.pack("<d", self.sampling_rate)
        data += self.enable_iq_mixer.to_bytes(4, 'little')
        data += self.num_capture_steps().to_bytes(4, 'little')

        capture_list = sorted(self.capture_list.items())
        for elem in capture_list:
            step_id = elem[0]
            capture = elem[1]
            data += step_id.to_bytes(4, 'little')
            data += capture.serialize()

        return data


    def num_capture_steps(self):
        return len(self.capture_list)
