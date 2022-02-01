#!/usr/bin/env python3
# coding: utf-8

AWG_CLK_FREQ = 300 # MHz
AWG_WAVE_SAMPLE_SIZE = 2 # Bytes
CAPTURE_WAVE_SAMPLE_SIZE = 4 # Bytes
PL_DDR4_RAM_SIZE = 0x100000000
NUM_REAL_SAMPLES_IN_CAPTURE_WORD = 16 # キャプチャワード内に含まれる Real データのサンプル数
NUM_IQ_SAMPLES_IN_CAPTURE_WORD = 8 # キャプチャワード内に含まれる I/Q データのサンプル数

class WaveChunkParamsLayout(object):
    """
    波形 RAM に格納された波形チャンクパラメータのレイアウト
    """
    WAVE_CHUNK_PARAMS_SEGMENT_OFFSET = 2048
    WAVE_CHUNK_PARAMS_WORD_SIZE = 64
    MAX_CHUNKS_IN_STEP = 4
    
    START_ADDR_OFFSET = 0
    NUM_SAMPLES_OFFSET = 4
    NUM_CYCLES_OFFSET = 8
    FLAG_LIST_OFFSET = 12
    WAVE_CHUNK_PARAM_SIZE = 16

    BIT_ENABLED = 0
    BIT_INFINITE_CYCLES = 1
