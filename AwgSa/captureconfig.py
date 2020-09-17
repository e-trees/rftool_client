#!/usr/bin/env python3
# coding: utf-8

from . import CaptureSequence
from . import AwgId
import struct

class CaptureConfig(object):
    """ キャプチャシーケンスのリストを保持する """

    _MAX_CAPTURE_SEQUENCES = 8

    def __init__(self):
        self.capture_sequence_list = {}
        return

    def add_capture_sequence(self, awg_id, capture_sequence):
        """
        キャプチャシーケンスを追加する
        
        Parameters
        ----------
        awg_id : int
            capture_sequence をセットする AWG の ID.
        capture_sequence : CaptureSequence
            追加するキャプチャシーケンス
        """
        if (not AwgId.has_value(awg_id)):
            raise ValueError("invalid awg_id  " + str(awg_id))

        if (len(self.capture_sequence_list) == self._MAX_CAPTURE_SEQUENCES):
            raise ValueError("No more capture sequences can be added. (max=" + str(self._MAX_CAPTURE_SEQUENCES) + ")")

        if (not isinstance(capture_sequence, CaptureSequence)):
            raise ValueError("invalid capture sequence" + str(capture_sequence))

        self.capture_sequence_list[int(awg_id)] = capture_sequence
        return self


    def serialize(self):
        data = bytearray()
        data += "CPCF".encode('utf-8')

        capture_sequence_list = sorted(self.capture_sequence_list.items())
        for elem in capture_sequence_list:
            awg_id = elem[0]
            capture_sequence = elem[1]
            data += awg_id.to_bytes(4, 'little')
            sequence_data = capture_sequence.serialize()
            data += len(sequence_data).to_bytes(4, 'little')
            data += sequence_data

        return data


    def num_sequences(self):
        return len(self.capture_sequence_list)
