#!/usr/bin/env python3
# coding: utf-8

AWG_CLK_FREQ = 300 #MHz
WAVE_SAMPLE_SIZE = 2 #bytes
PL_DDR4_RAM_SIZE = 0x100000000

class WaveStepParamsLayout(object):
    """
    ハードウェアの波形 RAM の各種パラメータのレイアウト
    """
    WAVE_STEP_PARAMS_WORD_SIZE = 64
    
    START_ADDR_OFFSET = 0
    NUM_SAMPLES_OFFSET = 4
    LAST_CYCLE_START_ADDR_OFFSET = 8
    LAST_CYCLE_NUM_SAMPLES_OFFSET = 12
    NUM_CYCLES_OFFSET = 16
    INTERVAL_OFFSET = 20

    START_ADDR_SIZE = 4
    NUM_SAMPLES_SIZE = 4
    LAST_CYCLE_START_ADDR_SIZE = 4
    LAST_CYCLE_NUM_SAMPLES_SIZE = 4
    NUM_CYCLES_SIZE = 4
    INTERVAL_SIZE = 4

