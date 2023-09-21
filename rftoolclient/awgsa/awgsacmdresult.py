#!/usr/bin/env python3
# coding: utf-8

from enum import Enum

class AwgSaCmdResult(Enum):
    WAVE_SEQUENCE_NOT_COMPLETE = 0
    WAVE_SEQUENCE_COMPLETE = 1
    WAVE_SEQUENCE_ERROR = 2

    DSP_NOT_COMPLETE = 0
    DSP_COMPLETE = 1
    DSP_ERROR = 2

    @classmethod
    def includes(cls, value):
        return value in [item.value for item in AwgSaCmdResult]
