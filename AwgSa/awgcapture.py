#!/usr/bin/env python3
# coding: utf-8

import struct

class AwgCapture(object):

    def __init__(
        self,
        time,
        *,
        delay = 0.0,
        do_accumulation = True):
        """
        ADCデータのキャプチャ情報を持つオブジェクトを作成する.

        Parameters
        ----------
        time : float
            キャプチャ時間. (単位:ns)
        delay : float
            このキャプチャに対応する波形ステップの開始から, キャプチャを開始するまでの遅延時間 (単位:ns)
        do_accumulation : bool
            波形シーケンスを繰り返した際に, キャプチャデータを累積するかどうか. (True:累積する, False:累積しない)
        """


        if (not isinstance(time, (int, float)) or time <= 0.0):
            raise ValueError("invalid capture time  " + str(time))
        
        if (not isinstance(delay, (int, float)) or delay < 0.0):
            raise ValueError("invalid delay  " + str(delay))
        
        if not isinstance(do_accumulation, bool):
            raise ValueError("invalid do_accumulation  " + str(do_accumulation))
        
        self.__time = float(time)
        self.__delay = float(delay)
        self.__do_accumulation = 1 if do_accumulation else 0
        return


    def serialize(self):
        data = bytearray()
        data += struct.pack("<d", self.__time)
        data += struct.pack("<d", self.__delay)
        data += self.__do_accumulation.to_bytes(4, 'little')
        return data
