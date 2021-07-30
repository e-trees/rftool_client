#!/usr/bin/env python3
# coding: utf-8

from enum import IntEnum

class ClockSrc(IntEnum):
    INTERNAL = 0
    EXTERNAL = 1
    @classmethod
    def has_value(cls, value):
        return value in [item.value for item in ClockSrc]

    @classmethod
    def of(cls, value):
        if value == 0:
            return ClockSrc.INTERNAL
        elif value == 1:
            return ClockSrc.EXTERNAL
        raise ValueError("invalid value for converting to ClockSrc " + str(value))
