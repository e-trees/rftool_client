#!/usr/bin/env python3
# coding: utf-8

from enum import Enum, auto

class DspParamId(Enum):
    SRC_ADDR = auto()
    DEST_ADDR = auto()
    NUM_SAMPLES = auto()
    IQ_FLAG = auto()
    GENERAL_0 = auto()
    GENERAL_1 = auto()
    GENERAL_2 = auto()
    GENERAL_3 = auto()
