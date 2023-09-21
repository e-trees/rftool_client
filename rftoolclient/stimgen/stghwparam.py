
# STG から出力するサンプルのサイズ (単位 : bytes)
STG_WAVE_SAMPLE_SIZE = 2
# STG から 1 サイクルで出力されるデータのサイズ (bytes)
STG_WORD_SIZE = 32
# STG から 1 サイクルで出力されるデータのサンプル数
NUM_SAMPLES_IN_STG_WORD = STG_WORD_SIZE // STG_WAVE_SAMPLE_SIZE
# 波形チャンクの波形パートを構成可能なサンプル数の最小単位
MIN_UNIT_SAMPLES_FOR_WAVE_PART = 1024

# 波形データを格納する RAM の 1 ワード当たりのバイト数
WAVE_RAM_WORD_SIZE = 64
# 波形データを格納する RAM のバイト数
WAVE_RAM_SIZE = 0x1_0000_0000
