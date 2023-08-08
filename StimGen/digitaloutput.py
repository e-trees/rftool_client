import copy

class DigitalOutputDataList:
    """デジタル出力モジュールが出力するビットパターンを保持するクラス"""

    MAX_PATTERNS = 512 #: デジタル出力モジュールに設定可能な最大パターン数
    MIN_TIME = 2
    MAX_TIME = 0xFFFFFFFF

    def __init__(self):
        self.__patterns = []


    def add(self, bits, time):
        """出力データを追加する

        Args:
            bits (int): 出力されるビットデータ.  0 ~ 7 ビット目がデジタル出力ポートの電圧値に対応する.  0 が Lo で 1 が Hi.
            time (int):
                | bits の出力時間.  2 以上を指定すること.
                | 出力時間の単位は，独立クロックバージョンの場合 10 [ns] で，同一クロックバージョンの場合 26.0417 [ns].
                | バージョンの違いについては https://github.com/e-trees/rftool_client/blob/master/docs/stg/digital_output.md を参照.
        """
        if (len(self.__patterns) == self.MAX_PATTERNS):
            raise ValueError("No more output patterns can be added. (max=" + str(self.MAX_PATTERNS) + ")")
        
        if not (isinstance(time, int) and self.__is_in_range(self.MIN_TIME, self.MAX_TIME, time)):
            raise ValueError(
                "Output time must be an integer between {} and {} inclusive.  '{}' was set."
                .format(self.MIN_TIME, self.MAX_TIME, time))

        if not isinstance(bits, int):
            raise ValueError("'bits' must be an integer.")

        self.__patterns.append((bits, time))
        return self


    def __getitem__(self, idx):
        return self.__patterns[idx]
    

    def __len__(self):
        return len(self.__patterns)


    def __is_in_range(self, min, max, val):
        return (min <= val) and (val <= max)
