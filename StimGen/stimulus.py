
class Stimulus(object):
    """Stimulation Generator から出力する波形情報を保持するクラス"""

    MIN_UNIT_OF_SAMPLES = 1024      #: 波形サイクルからポストブランクを除いた部分の最小単位 (サンプル)
    MAX_REPEATS = 0xFFFFFFFF        #: 波形サイクルの最大リピート回数
    MAX_POST_BLANK_LEN = 0xFFFFFFFF #: 最大ポストブランク長 (単位 = STG ワード)
    MAX_WAIT_WORDS = 0xFFFFFFFF     #: wait wordの長さ (単位 = STG ワード)
    __SAMPLE_SIZE = 2 # bytes

    def __init__(self, samples, num_blank_words, num_wait_words, num_repeats):
        """
        Args:
            samples (list of int):
                | 出力波形のサンプルのリスト.
                | リストの要素数は 1024 でなければならない.
                | リストの各要素は 2Bytes で表せる整数値でなければならない. (符号付, 符号なしは問わない)

            num_blank_words (int): 
                | samples に続いて出力される 0 データ (ポストブランク) の長さ.
                | 単位は STG ワードで 1 STG ワードは 16 サンプル.
                | つまり, (num_blank_words * 16) 個の 0 データが samples に続いて出力される.
            
            num_wait_words (int):
                | 波形サイクルの繰り返しの前に 1 回だけ出力される 0 データ (= wait word) の長さ.
                | 単位は STG ワードで 1 STG ワードは 16 サンプル.
                | つまり, (num_wait_words * 16) 個の 0 データが波形サイクルの繰り返しの前に出力される.

            num_repeats (int): 波形サイクル (= samples + ポストブランク) を繰り返す回数
        """
        if not isinstance(samples, list) or (len(samples) == 0):
            raise ValueError('Invalid sample list  ({})'.format(samples))

        if len(samples) % self.MIN_UNIT_OF_SAMPLES != 0:
            raise ValueError(
                "The length of 'samples' must be a multiple of {}."
                .format(self.MIN_UNIT_OF_SAMPLES))
    
        if not (isinstance(num_repeats, int) and
                self.__is_in_range(1, self.MAX_REPEATS, num_repeats)):
            raise ValueError(
                "'num_repeats' must be an integer between {} and {} inclusive.  '{}' was set."
                .format(1, self.MAX_REPEATS, num_repeats))

        if not (isinstance(num_blank_words, int) and
                self.__is_in_range(0, self.MAX_POST_BLANK_LEN, num_blank_words)):
            raise ValueError(
                "'num_blank_words' must be an integer between {} and {} inclusive.  '{}' was set."
                .format(0, self.MAX_POST_BLANK_LEN, num_blank_words))
        
        if not (isinstance(num_wait_words, int) and
                self.__is_in_range(0, self.MAX_WAIT_WORDS, num_wait_words)):
            raise ValueError(
                "'num_wait_words' must be an integer between {} and {} inclusive.  '{}' was set."
                .format(0, self.MAX_WAIT_WORDS, num_wait_words))

        self.__samples = samples # メモリを消費するのでディープコピーしない
        self.__num_blank_words = num_blank_words
        self.__num_wait_words = num_wait_words
        self.__num_repeats = num_repeats


    def __is_in_range(self, min, max, val):
        return (min <= val) and (val <= max)


    @property
    def samples(self):
        return self.__samples
    

    @property
    def num_blank_words(self):
        return self.__num_blank_words


    @property
    def num_repeats(self):
        return self.__num_repeats
    

    @property
    def num_wait_words(self):
        return self.__num_wait_words


    @property
    def serialized_samples(self):
        payload = bytearray()
        mask = ((1 << (self.__SAMPLE_SIZE * 8)) - 1)
        for sample in self.__samples:
            payload += (sample & mask).to_bytes(self.__SAMPLE_SIZE, 'little')

        return payload
