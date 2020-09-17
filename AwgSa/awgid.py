#!/usr/bin/env python3
# coding: utf-8

from enum import IntEnum

class AwgId(IntEnum):
    AWG_0 = 0
    AWG_1 = 1
    @classmethod
    def has_value(cls, value):
        return value in [item.value for item in AwgId]
