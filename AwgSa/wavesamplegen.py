#!/usr/bin/env python3
# coding: utf-8

import struct
import numpy as np
from .awgwave import AwgWave, AwgAnyWave
from .hardwareinfo import WaveStepParamsLayout as params
from .hardwareinfo import WAVE_SAMPLE_SIZE
from decimal import Decimal, ROUND_HALF_UP, ROUND_HALF_EVEN
from collections import namedtuple

class WaveObjToSampleConverter(object):

    __MAX_WAVE_SAMPLE_VAL = 32767.0
    __MIN_WAVE_SAMPLE_VAL = -32768.0

    @classmethod
    def gen_samples(cls, wave, sampling_rate):
        """
        AwgWave, AwgAnyWave を元に Real 波形のサンプルデータを生成する
        """
        if isinstance(wave, AwgWave):
            samples = WaveObjToSampleConverter.__gen_samples_from_awgwave(wave, sampling_rate)
        elif isinstance(wave, AwgAnyWave):
            samples = WaveObjToSampleConverter.__gen_samples_from_awganywave(wave)
        else:
            assert False, ("This should never happen.")

        return np.tile(samples, wave.get_num_cycles())


    @classmethod
    def gen_iq_samples(cls, iq_wave, sampling_rate):
        """
        AwgIQWave を元に I/Q 波形のサンプルデータを生成する
        """
        gen_samples = (lambda wave:
            cls.__gen_samples_from_awgwave(wave, sampling_rate)
            if isinstance(wave, AwgWave) else
            cls.__gen_samples_from_awganywave(wave))

        [i_samples, q_samples] = map(gen_samples, [iq_wave.get_i_wave(), iq_wave.get_q_wave()])
        if len(i_samples) < len(q_samples):
            i_samples = np.append(i_samples, np.zeros(len(q_samples) - len(i_samples)))
        else:
            q_samples = np.append(q_samples, np.zeros(len(i_samples) - len(q_samples)))

        return (np.tile(i_samples, iq_wave.get_i_wave().get_num_cycles()),
                np.tile(q_samples, iq_wave.get_q_wave().get_num_cycles()))


    @classmethod
    def __gen_samples_from_awgwave(cls, wave, sampling_rate):
        
        num_samples = cls.__calc_num_wave_samples(sampling_rate, wave.get_frequency())
        if num_samples == 0:
            return np.empty(0, dtype = np.int16)

        wave_type = wave.get_wave_type()
        if wave_type == AwgWave.SINE:
            samples = cls.__gen_sine_wave(num_samples, wave)
        elif wave_type == AwgWave.SQUARE:
            samples = cls.__gen_square_wave(num_samples, wave)
        elif wave_type == AwgWave.SAWTOOTH:
            samples = cls.__gen_sawtooth_wave(num_samples, wave)
        elif wave_type == AwgWave.GAUSSIAN:
            samples = cls.__gen_gaussian_wave(num_samples, wave)
        else:
            assert False, ("This should never happen.")
        
        return samples


    @classmethod
    def __gen_samples_from_awganywave(cls, wave):
        samples = np.clip(wave.get_samples(), cls.__MIN_WAVE_SAMPLE_VAL, cls.__MAX_WAVE_SAMPLE_VAL)
        samples = np.array(samples, dtype = np.int16)
        return samples


    @classmethod
    def __gen_sine_wave(cls, num_samples, params):

        points = np.linspace(0.0, 2.0 * np.pi, num_samples, endpoint = False)
        points = points + np.radians(params.get_phase())
        sin_wave = params.get_amplitude() * np.sin(points) + params.get_offset()
        sin_wave = np.clip(sin_wave, cls.__MIN_WAVE_SAMPLE_VAL, cls.__MAX_WAVE_SAMPLE_VAL)
        sin_wave = np.array(sin_wave, dtype = np.int16)
        return sin_wave

    
    @classmethod
    def __gen_square_wave(cls, num_samples, params):
    
        amplitude = params.get_amplitude()
        offset = params.get_offset()
        duty_cycle = np.clip(params.get_duty_cycle(), 0.0, 100.0)
        samples = np.full(
            num_samples,
            np.clip(-amplitude + offset, cls.__MIN_WAVE_SAMPLE_VAL, cls.__MAX_WAVE_SAMPLE_VAL),
            dtype = np.int16)

        if duty_cycle != 0.0:
            last_hi_pos = int((num_samples - 1) * duty_cycle / 100.0)
            for i in range(last_hi_pos + 1):
                samples[i] = np.clip(amplitude + offset, cls.__MIN_WAVE_SAMPLE_VAL, cls.__MAX_WAVE_SAMPLE_VAL)
        
        return cls.__shift_phase(samples, params.get_phase())


    @classmethod
    def __gen_sawtooth_wave(cls, num_samples, params):
        
        samples = np.empty(0, dtype = np.int16)
        crest_pos = int(np.clip(params.get_crest_pos(), 0.0, 1.0) * 0.5 * (num_samples - 1))
        valley_pos = (num_samples - 1) - crest_pos
        if valley_pos == crest_pos and num_samples > 1:
            valley_pos = crest_pos + 1
        
        amplitude = params.get_amplitude()
        offset = params.get_offset()
        #up
        slope = amplitude / max(1.0, crest_pos)
        part_of_samples = np.arange(crest_pos) * slope + offset
        part_of_samples = np.clip(part_of_samples, cls.__MIN_WAVE_SAMPLE_VAL, cls.__MAX_WAVE_SAMPLE_VAL)
        samples = np.array(part_of_samples, dtype = np.int16)

        # down
        slope = -2.0 * amplitude / max(1.0, valley_pos - crest_pos)
        part_of_samples = np.arange(valley_pos - crest_pos) * slope + offset + amplitude
        part_of_samples = np.clip(part_of_samples, cls.__MIN_WAVE_SAMPLE_VAL, cls.__MAX_WAVE_SAMPLE_VAL)
        samples = np.append(samples, np.array(part_of_samples, dtype = np.int16))

        # up
        slope = amplitude / max(1.0, num_samples - valley_pos)
        part_of_samples = np.arange(num_samples - valley_pos) * slope + offset - amplitude
        part_of_samples = np.clip(part_of_samples, cls.__MIN_WAVE_SAMPLE_VAL, cls.__MAX_WAVE_SAMPLE_VAL)
        samples = np.append(samples, np.array(part_of_samples, dtype = np.int16))
        return cls.__shift_phase(samples, params.get_phase())
        

    @classmethod
    def __gen_gaussian_wave(cls, num_samples, params):

        domain_begin = params.get_domain_begin()
        domain_end = params.get_domain_end()
        wave_domain_len = domain_end - domain_begin
        variation = wave_domain_len / num_samples
        samples = np.empty(num_samples, dtype = np.int16)
        variance = params.get_variance()
        for i in range(len(samples)):
            tmp = (domain_begin + i * variation) + (params.get_phase() * wave_domain_len / 360.0)
            tmp = cls.__fcycle(tmp, domain_begin, domain_end)
            sample_val = params.get_amplitude() * np.exp(-(tmp * tmp) / (2 * variance)) / np.sqrt(2 * np.pi * variance)
            sample_val += params.get_offset()
            samples[i] = np.clip(sample_val, cls.__MIN_WAVE_SAMPLE_VAL, cls.__MAX_WAVE_SAMPLE_VAL)
        return samples
    

    @classmethod
    def __calc_num_wave_samples(cls, sampling_rate, frequency):
        if sampling_rate < frequency:
            return 0
        return int(Decimal(sampling_rate / frequency).quantize(Decimal('0'), rounding = ROUND_HALF_UP))


    @classmethod
    def __shift_phase(cls, samples, phase):
        num_samples = len(samples)
        tmp = num_samples * phase / 360.0
        shift_amout = num_samples - int(Decimal(tmp).quantize(Decimal('0'), rounding = ROUND_HALF_UP))
        return np.roll(samples, shift_amout)


    @classmethod
    def __fcycle(cls, val, lo, hi):
        """
        val が lo 以上, hi 未満の範囲で循環した場合の値を返す.
        fcycle(-3, -2, 2) -> 1
        fcycle(16, 10, 15) -> 11
        """
        mod = np.fmod(val - lo, hi - lo)
        if mod < 0:
            mod = (hi - lo) + mod
        return mod + lo


class WaveRamToSampleConverter(object):
    
    @classmethod
    def gen_samples(cls, wave_ram_data, step_idx):
        """
        波形 RAM のデータを元に Real 波形のサンプルデータを生成する
        """
        params = cls.__get_wave_step_params(wave_ram_data, step_idx)
        samples_part = []
        for i in range(params.num_samples):
            offset = i * WAVE_SAMPLE_SIZE + params.start_addr
            tmp = wave_ram_data[offset : offset + WAVE_SAMPLE_SIZE]
            samples_part.append(struct.unpack('h', tmp)[0])

        samples = []        
        for i in range(params.num_cycles - 1):
            samples.extend(samples_part)

        for i in range(params.last_cyle_num_samples):
            offset = i * WAVE_SAMPLE_SIZE + params.last_cycle_start_addr
            tmp = wave_ram_data[offset : offset + WAVE_SAMPLE_SIZE]
            samples.append(struct.unpack('h', tmp)[0])        

        return np.array(samples, np.int16)


    @classmethod
    def gen_iq_samples(cls, wave_ram_data, step_idx):
        """
        波形 RAM のデータを元に I/Q 波形のサンプルデータを生成する
        """
        params = cls.__get_wave_step_params(wave_ram_data, step_idx)
        i_samples_part = []
        q_samples_part = []
        for i in range(int(params.num_samples / 2)):
            offset = 2 * i * WAVE_SAMPLE_SIZE + params.start_addr
            tmp = wave_ram_data[offset : offset + WAVE_SAMPLE_SIZE]
            i_samples_part.append(struct.unpack('h', tmp)[0])
            tmp = wave_ram_data[offset + WAVE_SAMPLE_SIZE : offset + WAVE_SAMPLE_SIZE * 2]
            q_samples_part.append(struct.unpack('h', tmp)[0])

        i_samples = []
        q_samples = []
        for i in range(params.num_cycles - 1):
            i_samples.extend(i_samples_part)
            q_samples.extend(q_samples_part)

        for i in range(int(params.last_cyle_num_samples / 2)):
            offset = 2 * i * WAVE_SAMPLE_SIZE + params.last_cycle_start_addr
            tmp = wave_ram_data[offset : offset + WAVE_SAMPLE_SIZE]
            i_samples.append(struct.unpack('h', tmp)[0])
            tmp = wave_ram_data[offset + WAVE_SAMPLE_SIZE : offset + WAVE_SAMPLE_SIZE * 2]
            q_samples.append(struct.unpack('h', tmp)[0])

        return (np.array(i_samples, np.int16), np.array(q_samples, np.int16))
    

    @classmethod
    def __get_wave_step_params(cls, wave_ram_data, step_idx):

        offset = step_idx * params.WAVE_STEP_PARAMS_WORD_SIZE
        param_bytes = wave_ram_data[offset:]
        
        offset = params.START_ADDR_OFFSET
        tmp = param_bytes[offset : offset + params.START_ADDR_SIZE]
        start_addr = struct.unpack('I', tmp)[0]
        
        offset = params.NUM_SAMPLES_OFFSET
        tmp = param_bytes[offset : offset + params.NUM_SAMPLES_SIZE]
        num_samples = struct.unpack('I', tmp)[0]
        
        offset = params.LAST_CYCLE_START_ADDR_OFFSET
        tmp = param_bytes[offset : offset + params.LAST_CYCLE_START_ADDR_SIZE]
        last_cycle_start_addr = struct.unpack('I', tmp)[0]

        offset = params.LAST_CYCLE_NUM_SAMPLES_OFFSET
        tmp = param_bytes[offset : offset + params.LAST_CYCLE_NUM_SAMPLES_SIZE]
        last_cyle_num_samples = struct.unpack('I', tmp)[0]

        offset = params.NUM_CYCLES_OFFSET
        tmp = param_bytes[offset : offset + params.NUM_CYCLES_SIZE]
        num_cycles = struct.unpack('I', tmp)[0]

        Params = namedtuple("Params", 
            ["start_addr", "num_samples", "last_cycle_start_addr", "last_cyle_num_samples", "num_cycles"])
        return Params(start_addr, num_samples, last_cycle_start_addr, last_cyle_num_samples, num_cycles)
