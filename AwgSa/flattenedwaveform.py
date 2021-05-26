#!/usr/bin/env python3
# coding: utf-8

import numpy as np
from .wavesamplegen import WaveObjToSampleConverter, WaveRamToSampleConverter
from decimal import Decimal, ROUND_HALF_UP, ROUND_HALF_EVEN

class FlattenedWaveform(object):
    """
    Real データの波形のサンプルデータとインターバルを保持する
    """
    @classmethod
    def build_from_wave_ram(cls, wave_ram_data, num_prime_wave_samples, step_idx):
        """
        波形 RAM の情報から FlattenedWaveform オブジェクトを作成する
        
        Parameters
        ----------
        wave_ram_data : bytes
            波形 RAM のバイトデータ
        num_prime_wave_samples : int
            波形ステップの有波形部のサンプル数
        step_idx : int
            波形データを作成する波形ステップの番号 (0, 1, 2, ...)
            ステップID ではない.

        Returns
        -------
        instance : FlattenedWaveform
            FlattenedWaveform オブジェクト
        """
        samples = WaveRamToSampleConverter.gen_samples(wave_ram_data, num_prime_wave_samples, step_idx)
        return FlattenedWaveform(samples)


    @classmethod
    def build_from_wave_obj(cls, wave, sampling_rate):
        """
        波形ステップの情報から FlattenedWaveform オブジェクトを作成する
        
        Parameters
        ----------
        wave : AwgWave, AwgAnyWave
            このオブジェクトの波形データを作成する
        sampling_rate : float
            wave を出力する際のサンプリングレート

        Returns
        -------
        instance : FlattenedWaveform
            FlattenedWaveform オブジェクト
        """
        samples = WaveObjToSampleConverter.gen_samples(wave, sampling_rate)
        return FlattenedWaveform(samples)


    def __init__(self, samples): 
        self.__samples = samples
        return


    def get_samples(self):
        return self.__samples.tolist()


    def get_num_samples(self):
        return len(self.__samples)


class FlattenedIQWaveform(object):
    """
    I/Q データの波形のサンプルデータとインターバルを保持する
    """
    @classmethod
    def build_from_wave_ram(cls, wave_ram_data, num_prime_wave_samples, step_idx):
        """
        波形 RAM の情報から FlattenedIQWaveform オブジェクトを作成する
        
        Parameters
        ----------
        wave_ram_data : bytes
            波形 RAM のバイトデータ
        num_prime_wave_samples : int
            波形ステップの有波形部のサンプル数
        step_idx : int
            波形データを作成する波形ステップの番号 (0, 1, 2, ...)
            ステップID ではない.

        Returns
        -------
        instance : FlattenedIQWaveform
            FlattenedIQWaveform オブジェクト
        """
        (i_samples, q_samples) = WaveRamToSampleConverter.gen_iq_samples(wave_ram_data, num_prime_wave_samples, step_idx)
        return FlattenedIQWaveform(i_samples, q_samples)


    @classmethod
    def build_from_wave_obj(cls, iq_wave, sampling_rate):
        """
        波形ステップの情報から FlattenedIQWaveform オブジェクトを作成する
        
        Parameters
        ----------
        wave : AwgIQWave
            このオブジェクトの波形データを作成する
        sampling_rate : float
            wave を出力する際のサンプリングレート

        Returns
        -------
        instance : FlattenedIQWaveform
            FlattenedIQWaveform オブジェクト
        """
        (i_samples, q_samples) = WaveObjToSampleConverter.gen_iq_samples(iq_wave, sampling_rate)
        return FlattenedIQWaveform(i_samples, q_samples)


    def __init__(self, i_samples, q_samples):
        self.__i_samples = i_samples
        self.__q_samples = q_samples
        assert len(self.__i_samples) == len(self.__q_samples), "I data and Q data have the different numbers of the samples."
        return


    def get_i_samples(self):
        return self.__i_samples.tolist()


    def get_q_samples(self):
        return self.__q_samples.tolist()


    def get_num_samples(self):
        return len(self.__i_samples)
