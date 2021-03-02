#!/usr/bin/env python3
# coding: utf-8

from enum import IntEnum

class ExternalTriggerId(IntEnum):
    EXT_TRIG_0 = 0
    EXT_TRIG_4 = 4
    @classmethod
    def has_value(cls, value):
        return value in [item.value for item in ExternalTriggerId]
