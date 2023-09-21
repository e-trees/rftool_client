#!/usr/bin/env python3
# coding: utf-8

from enum import IntEnum

class AwgId(IntEnum):
    AWG_0 = 0
    AWG_1 = 1
    AWG_2 = 2
    AWG_3 = 3
    AWG_4 = 4
    AWG_5 = 5
    AWG_6 = 6
    AWG_7 = 7
    
    @classmethod
    def includes(cls, value):
        return value in [item.value for item in AwgId]
    
    @classmethod
    def to_awg_id(cls, value):
        if value == 0 or value == '0':
            return AwgId.AWG_0
        if value == 1 or value == '1':
            return AwgId.AWG_1
        if value == 2 or value == '2':
            return AwgId.AWG_2
        if value == 3 or value == '3':
            return AwgId.AWG_3
        if value == 4 or value == '4':
            return AwgId.AWG_4
        if value == 5 or value == '5':
            return AwgId.AWG_5
        if value == 6 or value == '6':
            return AwgId.AWG_6
        if value == 7 or value == '7':
            return AwgId.AWG_7
        raise ValueError("cannot convert {} to AWG ID".format(value))
