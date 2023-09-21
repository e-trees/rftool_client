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

        if 1.4e+10 < float(delay):
            raise ValueError("The {}[ns] capture delay is too long. (max={}[ns])".format(delay, 1.4e+10))

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
        data += struct.pack("<i", self.__do_accumulation)
        data += struct.pack("<i", 1) # キャプチャ繰り返し回数
        data += struct.pack("<i", 0) # 無限キャプチャ繰り返しフラグ
        return data


class AwgWindowedCapture(object):

    def __init__(
        self,
        time,
        num_windows,
        *,
        delay = 0.0):
        """
        ADC データのキャプチャ情報を持つオブジェクトを作成する.
        このクラスでキャプチャを定義すると, キャプチャした ADC データを複数のウィンドウに分けて, 
        ウィンドウ同士をサンプルごとに足し合わせて保存する.
        Parameters
        ----------
        time : float
            ウィンドウ一つ当たりのキャプチャ時間 (単位:ns)
        num_windows : int
            ウィンドウの個数 (= 積算回数).
            負の値を指定すると, キャプチャモジュールを強制停止させるまで, ウィンドウ単位での積算を続ける.
        delay : float
            このキャプチャに対応する波形ステップの開始から, キャプチャを開始するまでの遅延時間 (単位:ns)
        """
        if (not isinstance(time, (int, float)) or time <= 0.0):
            raise ValueError("invalid capture time  " + str(time))
        
        if (not isinstance(num_windows, int) or (num_windows == 0 or 0xFFFFFFFE < num_windows)):
            raise ValueError("invalid number of windows " + str(num_windows))

        if (not isinstance(delay, (int, float)) or delay < 0.0):
            raise ValueError("invalid delay  " + str(delay))

        if 1.4e+10 < float(delay):
            raise ValueError("The {}[ns] capture delay is too long. (max={}[ns])".format(delay, 1.4e+10))

        self.__time = float(time)
        self.__num_windows = 0 if num_windows < 0 else num_windows
        self.__is_infinite_windows = 1 if num_windows < 0 else 0
        self.__delay = float(delay)


    def serialize(self):
        data = bytearray()
        data += struct.pack("<d", self.__time)
        data += struct.pack("<d", self.__delay)
        data += struct.pack("<i", 1) # 積算有効フラグ
        data += struct.pack("<i", self.__num_windows)
        data += struct.pack("<i", self.__is_infinite_windows)
        return data
