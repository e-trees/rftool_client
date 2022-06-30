#!/usr/bin/env python3
# coding: utf-8

AWG_CLK_FREQ = 300 #MHz
WAVE_SAMPLE_SIZE = 2 #bytes
PL_DDR4_RAM_SIZE = 0x100000000
MAX_BINARIZATION_RESULTS = 256 # 保持可能な二値化結果の最大個数

class WaveChunkParamsLayout(object):
    """
    波形 RAM に格納された波形チャンクパラメータのレイアウト
    """
    WAVE_CHUNK_PARAMS_SEGMENT_OFFSET = 4096
    WAVE_CHUNK_PARAMS_WORD_SIZE = 64
    MAX_CHUNKS_IN_STEP = 4
    
    START_ADDR_OFFSET = 0
    NUM_SAMPLES_OFFSET = 4
    NUM_CYCLES_OFFSET = 8
    FLAG_LIST_OFFSET = 12
    WAVE_CHUNK_PARAM_SIZE = 16

    BIT_ENABLED = 0
    BIT_INFINITE_CYCLES = 1
