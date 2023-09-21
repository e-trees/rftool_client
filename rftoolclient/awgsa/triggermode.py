#!/usr/bin/env python3
# coding: utf-8

from enum import IntEnum

class TriggerMode(IntEnum):
    MANUAL = 0
    EXTERNAL = 1
    @classmethod
    def includes(cls, value):
        return value in [item.value for item in TriggerMode]

    @classmethod
    def of(cls, value):
        if value == 0:
            return TriggerMode.MANUAL
        elif value == 1:
            return TriggerMode.EXTERNAL

        raise ValueError("Failed to convert {} to TriggerMode " + str(value))
