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
    def has_value(cls, value):
        return value in [item.value for item in AwgId]
