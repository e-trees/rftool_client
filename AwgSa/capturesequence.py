#!/usr/bin/env python3
# coding: utf-8

from . import AwgCapture, AwgWindowedCapture
import struct

class CaptureSequence(object):
    """ キャプチャステップのシーケンスを保持する """
    __MIN_SAMPLING_RATE = 1000.0
    __MAX_SAMPLING_RATE = 4096.0
    __MAX_CAPTURE_STEPS = 32

    def __init__(self, sampling_rate, *, is_iq_data = False):
        """
        キャプチャシーケンスオブジェクトを作成する.

        Parameters
        ----------
        sampling_rate : float
            ADC サンプリングレート [Msps]
        is_iq_data : bool
            I/Q データをキャプチャするかどうか (True: I/Q データをキャプチャする, False: Real データをキャプチャする)
        """

        if (not isinstance(sampling_rate, (int, float)) or\
           (sampling_rate < CaptureSequence.__MIN_SAMPLING_RATE or CaptureSequence.__MAX_SAMPLING_RATE < sampling_rate)):
           raise ValueError("invalid sampling rate  " + str(sampling_rate))
        
        if not isinstance(is_iq_data, bool):
            raise ValueError("invalid is_iq_data  " + str(is_iq_data))
        
        self.__sampling_rate = float(sampling_rate)
        self.__is_iq_data = 1 if is_iq_data else 0
        self.__capture_list = {}
        return


    def add_step(self, step_id, capture):
        """
        キャプチャステップを追加する
        
        Parameters
        ----------
        step_id : int
            キャプチャ開始の基準となる波形ステップID.
        capture : AwgCapture, AwgWindowedCapture
            AwgCapture or AwgWindowedCapture オブジェクト
        """
        if (not isinstance(step_id, int) or (step_id < 0 or 0x7FFFFFFF < step_id)):
            raise ValueError("invalid step_id " + str(step_id))
        
        if (step_id in self.__capture_list):
            raise ValueError("The step id (" + str(step_id) + ") is already registered.")

        if (len(self.__capture_list) == self.__MAX_CAPTURE_STEPS):
            raise ValueError("No more captures can be added. (max=" + str(self.__MAX_CAPTURE_STEPS) + ")")

        if (not isinstance(capture, (AwgCapture, AwgWindowedCapture))):
            raise ValueError("invalid capture " + str(capture))

        self.__capture_list[step_id] = capture
        return self


    def serialize(self):

        data = bytearray()
        data += struct.pack("<d", self.__sampling_rate)
        data += self.__is_iq_data.to_bytes(4, 'little')
        data += self.num_capture_steps().to_bytes(4, 'little')

        capture_list = sorted(self.__capture_list.items())
        for elem in capture_list:
            step_id = elem[0]
            capture = elem[1]
            data += step_id.to_bytes(4, 'little')
            data += capture.serialize()

        return data


    def num_capture_steps(self):
        return len(self.__capture_list)
