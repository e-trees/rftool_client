#!/usr/bin/env python3
# coding: utf-8

import struct

class DigitalOutputVector(object):
    """ 一連のデジタル出力データを保持するクラス """

    _MAX_NUM_OUTPUT_DATA = 32

    def __init__(self, *, delay = 0.0):
        """        
        parameters
        ----------
        delay : float
            このデジタル出力に対応する波形ステップの開始から, 最初のデジタルデータを出力するまでの遅延時間 (単位:ns)
        """
        self.delay = delay
        self.output_list = []
        return

    def append_data(self, val, duration):
        """
        出力データを追加する.
        
        parameters
        ----------
        val : int
            出力する値. (0x0 ~ 0xFF)
        duration : float
            出力期間 (単位:ns)
        """
        if (len(self.output_list) == DigitalOutputVector._MAX_NUM_OUTPUT_DATA):
            raise ValueError("No more output data can be appended. (max=" + str(DigitalOutputVector._MAX_NUM_OUTPUT_DATA) + ")")

        if (not isinstance(val, int) or (val < 0 or 255 < val)):
            raise ValueError("invalid output value " + hex(val))

        if (not isinstance(duration, (float, int)) or 1.0e+10 < duration):
            raise ValueError("invalid duration " + str(duration))

        self.output_list.append((val, float(duration)))
        return self


    def get_duration(self):
        """
        全出力データの出力期間 (単位:ns) の合計を取得する.
        """
        duration = 0.0
        for output in self.output_list:
            duration += output[1]
        return duration


    def num_output_data(self):
        return len(self.output_list)


    def serialize(self):

        data = bytearray()
        data += struct.pack("<d", self.delay)
        data += len(self.output_list).to_bytes(4, 'little')

        for output in self.output_list:
            output_data = output[0]
            duration = output[1]
            data += output_data.to_bytes(4, 'little')
            data += struct.pack("<d", duration)
        
        return data
