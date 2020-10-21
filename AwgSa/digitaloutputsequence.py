#!/usr/bin/env python3
# coding: utf-8

from . import DigitalOutputVector
import struct

class DigitalOutputSequence(object):
    """ デジタル出力ステップのシーケンスを保持する """

    __MAX_DOUT_STEPS = 32

    def __init__(self):
        self.__dout_list = {}
        return

    def add_step(self, step_id, dout_vec):
        """
        デジタル出力ステップを追加する.
        
        parameters
        ----------
        step_id : int
            デジタル出力開始の基準となる波形ステップID.
        dout_vec : DigitalOutputVector
            DigitalOutputVector オブジェクト
        """
        if (not isinstance(step_id, int) or (step_id < 0 or 0x7FFFFFFF < step_id)):
            raise ValueError("invalid step_id " + str(step_id))

        if (step_id in self.__dout_list):
            raise ValueError("The step id (" + str(step_id) + ") is already registered.")

        if (len(self.__dout_list) == self.__MAX_DOUT_STEPS):
            raise ValueError("No more digital output vectors can be added. (max=" + str(self.__MAX_DOUT_STEPS) + ")")
        
        if (not isinstance(dout_vec, DigitalOutputVector)):
            raise ValueError("invalid digital output vector " + str(dout_vec))

        self.__dout_list[step_id] = dout_vec
        return self


    def num_steps(self):
        return len(self.__dout_list)


    def serialize(self):

        data = bytearray()
        data += "DSEQ".encode('utf-8')
        data += self.num_steps().to_bytes(4, 'little')
        dout_list = sorted(self.__dout_list.items())
        for elem in dout_list:
            step_id = elem[0]
            dout_vec = elem[1]
            data += step_id.to_bytes(4, 'little')
            data += dout_vec.serialize()

        return data
