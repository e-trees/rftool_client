import copy
import struct
import rftoolclient as rftc
from .stghwparam import (
    STG_WAVE_SAMPLE_SIZE,
    STG_WORD_SIZE,
    NUM_SAMPLES_IN_STG_WORD,
    MIN_UNIT_SAMPLES_FOR_WAVE_PART)

class Stimulus(object):
    """Stimulation Generator から出力する波形情報を保持するクラス"""

    MAX_POST_BLANK_LEN = 0xFFFFFFFF    #: 最大ポストブランク長
    MAX_CHUNK_REPEATS = 0xFFFFFFFF     #: 波形チャンクの最大リピート回数
    MAX_WAIT_WORDS = 0xFFFFFFFF        #: 出力波形の先頭に付く 0 データの最大の長さ
    MAX_SEQUENCE_REPEATS = 0xFFFFFFFF  #: 波形シーケンスの最大リピート回数
    MAX_CHUNKS = 16                    #: 波形シーケンスに登録可能な最大チャンク数
    MIN_UNIT_SAMPLES_FOR_WAVE_PART = MIN_UNIT_SAMPLES_FOR_WAVE_PART #: 波形チャンクの波形パートを構成可能なサンプル数の最小単位
    NUM_SAMPLES_IN_STG_WORD = NUM_SAMPLES_IN_STG_WORD #: 1 STG ワード当たりのサンプル数

    def __init__(
        self,
        num_wait_words,
        num_seq_repeats,
        *,
        enable_lib_log = True,
        logger = rftc.get_null_logger()):
        """
        Args:
            num_wait_words (int): 
                | 出力波形の先頭に付く 0 データの長さ.
                | 1 STG ワードは 16 サンプル.
            num_seq_repeats (int): 波形シーケンスを繰り返す回数
            enable_lib_log (bool):
                | True -> ライブラリの標準のログ機能を有効にする.
                | False -> ライブラリの標準のログ機能を無効にする.
            logger (logging.Logger): ユーザ独自のログ出力に用いる Logger オブジェクト
        """
        self.__loggers = [logger]
        if enable_lib_log:
            self.__loggers.append(rftc.get_file_logger())

        try:
            if not (isinstance(num_wait_words, int) and 
                    (0 <= num_wait_words and num_wait_words <= self.MAX_WAIT_WORDS)):
                raise ValueError(
                    "The number of wait words must be an integer between {} and {} inclusive.  '{}' was set."
                    .format(0, self.MAX_WAIT_WORDS, num_seq_repeats))

            if not (isinstance(num_seq_repeats, int) and 
                    (1 <= num_seq_repeats and num_seq_repeats <= self.MAX_SEQUENCE_REPEATS)):
                raise ValueError(
                    "The number of times to repeat a wave sequence must be an integer between {} and {} inclusive.  '{}' was set."
                    .format(1, self.MAX_SEQUENCE_REPEATS, num_seq_repeats))
        except Exception as e:
            rftc.log_error(e, *self.__loggers)
            raise

        self.__chunks = []
        self.__num_wait_words = num_wait_words
        self.__num_seq_repeats = num_seq_repeats

    def del_chunk(self, index):
        """波形チャンクを削除する.

        Args:
            index (int): 削除するチャンクの番号. (登録順に 0, 1, 2, 3...)
        """
        if index < len(self.__chunks):
            del self.__chunks[index]
        
    def add_chunk(self, samples, num_blank_words, num_repeats):
        """波形チャンクを追加する

        Args:
            samples (list of int):
                | 各サンプルのリスト.
                | リストの要素数は波形パートを構成可能な最小サンプル数 (= 1024) の倍数でなければならない.
                | 各サンプルは 2bytes で表せる整数値でなければならない. (符号付, 符号なしは問わない)
            num_blank_words (int): 
                | 追加する波形チャンク内で samples に続く 0 データ (ポストブランク) の長さ.
                | 単位は STG ワード.
                | 1 STG ワードは 16 サンプル.
            num_repeats (int): 追加する波形チャンクを繰り返す回数
        """
        try:
            if not isinstance(samples, list):
                raise ValueError('Invalid sample list  ({})'.format(samples))
            
            if (len(self.__chunks) == self.MAX_CHUNKS):
                raise ValueError("No more wave chunks can be added. (max=" + str(self.MAX_CHUNKS) + ")")
            
            num_samples = len(samples)
            if num_samples == 0:
                raise ValueError('Empty sample list was set.')

            if num_samples % MIN_UNIT_SAMPLES_FOR_WAVE_PART != 0:
                raise ValueError(
                    'The number of samples in a wave chunk must be a multiple of {}.'
                    .format(MIN_UNIT_SAMPLES_FOR_WAVE_PART))

            if not (isinstance(num_blank_words, int) and 
                    (0 <= num_blank_words and num_blank_words <= self.MAX_POST_BLANK_LEN)):
                raise ValueError(
                    "Post blank length must be an integer between {} and {} inclusive.  '{}' was set."
                    .format(0, self.MAX_POST_BLANK_LEN, num_blank_words))

            if not (isinstance(num_repeats, int) and 
                    (1 <= num_repeats and num_repeats <= self.MAX_CHUNK_REPEATS)):
                raise ValueError(
                    "The number of times to repeat a wave chunk must be an integer between {} and {} inclusive.  '{}' was set."
                    .format(1, self.MAX_CHUNK_REPEATS, num_repeats))
        except Exception as e:
            rftc.log_error(e, *self.__loggers)
            raise

        self.__chunks.append(WaveChunk(samples, num_blank_words, num_repeats))
        return self

    @property
    def num_chunks(self):
        """現在登録されている波形チャンクの数
        
        Returns:
            int: 登録されているチャンク数
        """
        return len(self.__chunks)

    def chunk(self, idx):
        """引数で指定した番号の波形チャンクを返す
        
        Args:
            idx: 取得する波形チャンクの番号 (登録順に 0, 1, 2, ...)

        Returns:
            WaveChunk: 引数で指定した波形チャンク
        """
        return self.__chunks[idx]

    @property
    def chunk_list(self):
        """現在登録されている波形チャンクのリスト

        Returns:
            list of WaveChunk: 現在登録されている波形チャンクのリスト
        """
        return copy.copy(self.__chunks)

    @property
    def num_wait_samples(self):
        """出力波形の先頭に付く 0 データのサンプル数.

        Returns:
            int: 出力波形の先頭に付く 0 データのサンプル数.
        """
        return self.num_wait_words * NUM_SAMPLES_IN_STG_WORD

    @property
    def num_wait_words(self):
        """出力波形の先頭に付く 0 データの長さ.
        
        | 単位は STG ワード.
        | 1 STG ワードは 16 サンプル.

        Returns:
            int: 出力波形の先頭に付く 0 データの長さ
        """
        return self.__num_wait_words

    @property
    def num_seq_repeats(self):
        """波形シーケンスを繰り返す回数

        Returns:
            int: 波形シーケンスを繰り返す回数
        """
        return self.__num_seq_repeats

    @property
    def num_all_samples(self):
        """この出力波形の全サンプル数

        Returns:
            int: この出力波形の全サンプル数
        """
        return self.num_all_words * NUM_SAMPLES_IN_STG_WORD

    @property
    def num_all_words(self):
        """この出力波形の全 STG ワード数
        
        Returns:
            int: この出力波形の全 STG ワード数
        """
        num_chunk_words = 0
        for chunk in self.__chunks:
            num_chunk_words += chunk.num_words * chunk.num_repeats
        return num_chunk_words * self.__num_seq_repeats + self.__num_wait_words

    def all_samples_lazy(self, include_wait_words = True):
        """この出力波形に含まれる全波形サンプルを返す

        | all_samples の遅延評価版

        Args:
            include_wait_words (bool)
                | True  -> 戻り値の中にシーケンスの先頭の 0 データを含む
                | False -> 戻り値の中にシーケンスの先頭の 0 データを含まない
        
        Returns:
            list of int: 波形サンプルデータのリスト.
        """
        return self.__WaveSampleList(self, include_wait_words, *self.__loggers)

    def all_samples(self, include_wait_words = True):
        """この出力波形に含まれる全波形サンプルを返す

        Args:
            include_wait_words (bool)
                | True  -> 戻り値の中に出力波形の先頭の 0 データを含む
                | False -> 戻り値の中に出力波形の先頭の 0 データを含まない
        
        Returns:
            list of int: 波形サンプルデータのリスト.
        """
        samples = []
        for chunk in self.__chunks:
            chunk_samples = []
            chunk_samples.extend(chunk.wave_data.samples)
            chunk_samples.extend([0] * chunk.num_blank_samples)
            samples.extend(chunk_samples * chunk.num_repeats)
        samples = samples * self.__num_seq_repeats
        
        if include_wait_words:
            return  [0] * self.num_wait_samples + samples
                
        return samples

    def save_as_text(self, filepath, to_hex = False):
        """この出力波形をテキストデータとして保存する

        Args:
            filepath (string): 保存するファイルのパス
            to_hex (bool):
                | True -> 16進数として保存
                | False -> 10進数として保存
        """
        try:
            with open(filepath, 'w') as txt_file:
                sample_mask = (1 << (STG_WAVE_SAMPLE_SIZE * 8)) - 1
                first_zeros = '0\n' * (self.__num_wait_words * NUM_SAMPLES_IN_STG_WORD)
                txt_file.write(first_zeros)
                for _ in range(self.__num_seq_repeats):
                    for chunk in self.__chunks:
                        for _ in range(chunk.num_repeats):
                            for sample in chunk.wave_data.samples:
                                if to_hex:
                                    sample = sample & sample_mask
                                    txt_file.write('{:04x}\n'.format(sample))
                                else:
                                    txt_file.write('{:7d}\n'.format(sample))
                            if to_hex:
                                post_chunk_zeros = \
                                    '{:04x}\n'.format(0) * (chunk.num_blank_words * NUM_SAMPLES_IN_STG_WORD)
                            else:
                                post_chunk_zeros = \
                                    '{:7d}\n'.format(0) * (chunk.num_blank_words * NUM_SAMPLES_IN_STG_WORD)
                            txt_file.write(post_chunk_zeros)
        except Exception as e:
            rftc.log_error(e, *self.__loggers)
            raise

    def __str__(self):
        ret = ('num wait words : {}\n'.format(self.__num_wait_words) +
               'num sequence repeats : {}\n'.format(self.__num_seq_repeats) +
               'num chunks : {}\n'.format(self.num_chunks) +
               'num all samples : {}\n\n'.format(self.num_all_samples))
        
        for i in range(self.num_chunks):
            tmp = ('chunk {}\n'.format(i) +
                   '    num wave samples : {}\n'.format(self.chunk(i).wave_data.num_samples) +
                   '    num blank words : {}\n'.format(self.chunk(i).num_blank_words) +
                   '    num repeats : {}\n'.format(self.chunk(i).num_repeats))
            ret += tmp
        return ret + "\n"


    class __WaveSampleList(object):

        def __init__(self, stimulus, include_wait_words, *loggers):
            self.__chunks = stimulus.chunk_list
            if include_wait_words:
                self.__num_wait_samples = stimulus.num_wait_words * NUM_SAMPLES_IN_STG_WORD
                self.__len = stimulus.num_all_samples
            else:
                self.__num_wait_samples = 0
                self.__len = stimulus.num_all_samples - stimulus.num_wait_samples

            self.__chunk_range_list = self.__gen_chunk_range_list(self.__chunks)

            # 1 波形シーケンス当たりのサンプル数
            self.__num_samples_in_seq = \
                (self.__len - self.__num_wait_samples) // stimulus.num_seq_repeats
            self.__loggers = loggers
        
        def __gen_chunk_range_list(self, chunks):
            chunk_range_list = []
            start_idx = 0
            for chunk in chunks:
                end_idx = start_idx + chunk.num_repeats * chunk.num_samples - 1
                chunk_range_list.append((start_idx, end_idx))
                start_idx = end_idx + 1
            return chunk_range_list

        def __repr__(self):
            return self.__str__()

        def __str__(self):
            len = min(self.__len, 12)
            items = []
            for i in range(len):
                items.append(str(self[i]))
            if self.__len > 12:
                items.append('...')
            return '[' + ', '.join(items) + ']'

        def __iter__(self):
            return self.WaveIter(self)

        def __getitem__(self, key):
            if isinstance(key, int):
                if key < 0:
                    key += self.__len
                if (key < 0) or (self.__len <= key):
                    msg = 'The index [{}] is out of range.'.format(key)
                    rftc.log_error(msg, *self.__loggers)
                    raise IndexError(msg)
                if key < self.__num_wait_samples:
                    return 0

                key = (key - self.__num_wait_samples) % self.__num_samples_in_seq
                chunk, start_idx, _ = self.__find_chunk(key)
                key = (key - start_idx) % chunk.num_samples
                if key < chunk.wave_data.num_samples:
                    return chunk.wave_data.sample(key)
                else:
                    return 0

            elif isinstance(key, slice):
                return [self[i] for i in range(*key.indices(self.__len))]
            else:
                msg = 'Invalid argument type.'
                rftc.log_error(msg, *self.__loggers)
                raise TypeError(msg)

        def __find_chunk(self, idx):
            first = 0
            last = len(self.__chunk_range_list) - 1
            while first <= last:
                target = (first + last) // 2
                start, end = self.__chunk_range_list[target]
                if (start <= idx) and (idx <= end):
                    return (self.__chunks[target], start, end)
                if end < idx:
                    first = target + 1
                else:
                    last = target - 1

        def __len__(self):
            return self.__len

        class WaveIter(object):

            def __init__(self, outer):
                self._i = 0
                self.__outer = outer

            def __next__(self):
                if self._i == len(self.__outer):
                    raise StopIteration()
                val = self.__outer[self._i]
                self._i += 1
                return val


class WaveChunk(object):
    """波形チャンクの情報を保持するクラス"""

    def __init__(self, samples, num_blank_words, num_repeats):
        self.__wave_data = WaveData(samples, STG_WAVE_SAMPLE_SIZE)
        self.__num_blank_words = num_blank_words
        self.__num_repeats = num_repeats

    @property
    def wave_data(self):
        """この波形チャンクのポストブランクを除く波形データ

        Returns:
            WaveData: この波形チャンクのポストブランクを除く波形データ
        """
        return self.__wave_data

    @property
    def num_blank_words(self):
        """この波形チャンクのポストブランクの長さ
        
        Returns:
            int: 
                | この波形チャンクのポストブランクの長さ.
                | 単位は STG ワード.
                | 1 STG ワードは 16 サンプル.
        """
        return self.__num_blank_words

    @property
    def num_blank_samples(self):
        """この波形チャンクのポストブランクのサンプル数
        
        Returns:
            int: この波形チャンクのポストブランクのサンプル数
        """
        return self.num_blank_words * NUM_SAMPLES_IN_STG_WORD

    @property
    def num_wave_words(self):
        """この波形チャンクの波形パートの長さ
        
        Returns:
            int: 
                | この波形チャンクの波形パートの長さ
                | 単位は STG ワード.
                | 1 STG ワードは 16 サンプル.
        """
        return self.__wave_data.num_bytes // STG_WORD_SIZE

    @property
    def num_wave_samples(self):
        """この波形チャンクの波形パートのサンプル数
        
        Returns:
            int: この波形チャンクの波形パートのサンプル数
        """
        return self.num_wave_words * NUM_SAMPLES_IN_STG_WORD

    @property
    def num_repeats(self):
        """この波形チャンクを繰り返す回数
        
        Returns:
            int: この波形チャンクを繰り返す回数
        """
        return self.__num_repeats

    @property
    def num_words(self):
        """この波形チャンクのワード数.

        1 STG ワードは 16 サンプル.
        
        Returns:
            int: この波形チャンクのワード数
        """
        return self.num_wave_words + self.num_blank_words

    @property
    def num_samples(self):
        """この波形チャンクのサンプル数.

        Returns:
            int: この波形チャンクのサンプル数
        """
        return self.num_words * NUM_SAMPLES_IN_STG_WORD


class WaveData(object):
    """波形のサンプルデータを保持するクラス"""

    def __init__(self, samples, wave_sample_size):
        self.__samples = copy.copy(samples)
        self.__wave_sample_size = wave_sample_size

    @property
    def samples(self):
        """波形データのサンプルリスト

        Returns:
            list of int: 波形データのサンプルリスト
        """
        return copy.copy(self.__samples)

    def sample(self, idx):
        """引数で指定したサンプルを返す
        
        Rturns:
            int: サンプル値
        """
        return self.__samples[idx]

    @property
    def num_samples(self):
        """波形データのサンプル数
        
        Returns:
            int: 波形データのサンプル数
        """
        return len(self.__samples)

    @property
    def num_bytes(self):
        """波形データのバイト数
        
        Returns:
            int: 波形データのバイト数
        """
        return len(self.__samples) * self.__wave_sample_size

    def serialize(self):
        sample_mask = (1 << (self.__wave_sample_size * 8)) - 1
        payload = bytearray()
        for sample in self.__samples:
            sample = sample & sample_mask
            payload += struct.pack('<H', sample)
        return payload

    @classmethod
    def deserialize(cls, data, wave_sample_size):
        sample_mask = ((1 << (wave_sample_size * 8)) - 1)
        minval = 1 << (wave_sample_size * 8 - 1)
        samples = []
        num_samples = len(data) // wave_sample_size
        for i in range(num_samples):
            sample = int.from_bytes(data[i * wave_sample_size : (i + 1) * wave_sample_size], 'little')
            sample = sample & sample_mask
            sample = (sample ^ minval) - minval
            samples.append(sample)

        return WaveData(samples, wave_sample_size)
