#!/usr/bin/env python3
# coding: utf-8

import rftoolclient.awgsa as ag

class CaptureConfig(object):
    """ キャプチャシーケンスのリストを保持する """

    __MAX_CAPTURE_SEQUENCES = 8

    def __init__(self):
        self.__capture_sequence_list = {}
        return

    def add_capture_sequence(self, awg_id, capture_sequence):
        """
        キャプチャシーケンスを追加する
        
        Parameters
        ----------
        awg_id : AwgId
            capture_sequence をセットする AWG の ID.
        capture_sequence : CaptureSequence
            追加するキャプチャシーケンス
        """
        if (not ag.AwgId.includes(awg_id)):
            raise ValueError("invalid awg_id  " + str(awg_id))

        if (len(self.__capture_sequence_list) == self.__MAX_CAPTURE_SEQUENCES):
            raise ValueError("No more capture sequences can be added. (max=" + str(self.__MAX_CAPTURE_SEQUENCES) + ")")

        if (not isinstance(capture_sequence, ag.CaptureSequence)):
            raise ValueError("invalid capture sequence" + str(capture_sequence))

        self.__capture_sequence_list[int(awg_id)] = capture_sequence
        return self


    def serialize(self):
        data = bytearray()
        data += "CPCF".encode('utf-8')
        data += self.num_sequences().to_bytes(4, 'little')

        capture_sequence_list = sorted(self.__capture_sequence_list.items())
        for elem in capture_sequence_list:
            awg_id = elem[0]
            capture_sequence = elem[1]
            data += awg_id.to_bytes(4, 'little')
            sequence_data = capture_sequence.serialize()
            data += len(sequence_data).to_bytes(4, 'little')
            data += sequence_data

        return data


    def num_sequences(self):
        return len(self.__capture_sequence_list)


    def get_capture_sequence(self, awg_id):
        """
        Parameters
        ----------
        キャプチャシーケンスを取得する
        awg_id : AwgId
            取得したいキャプチャシーケンスをセットした AWG の ID
        
        Returns
        ----------
        capture_sequence : CaptureSequence
            awg_id の AWG にセットされたキャプチャシーケンス
        """
        return self.__capture_sequence_list[int(awg_id)]
