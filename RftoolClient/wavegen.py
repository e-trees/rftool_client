#!/usr/bin/env python3
# coding: utf-8

import numpy
import logging


"""
wavegen.py
    - Arbitrary waveform data generation tool
"""


class WaveGen(object):
    def __init__(self, logger=None):
        self._logger = logging.getLogger(__name__)
        self._logger.addHandler(logging.NullHandler())
        self._logger = logger or self._logger

        self.num_sample = 8192  # (samples)
        self.dac_freq = 4096.0  # (MHz)
        self.carrier_freq = 200.0  # (MHz)
        self.sweep_end_freq = 200.0  # (MHz)
        self.amplitude = 32767.0
        self.pulse_dutyratio = 0.5
        self.impulse_delta = 2  # (samples)
        self._set_subparam()

        self._logger.debug("WaveGen __init__")

    def _set_subparam(self):
        self.cycles = self.num_sample * self.carrier_freq / self.dac_freq
        self.r_cycles = numpy.round(self.cycles)
        self.actual_carrier_freq = self.r_cycles * self.dac_freq / self.num_sample

    def _put_paramlog(self):
        nyquist_freq = self.dac_freq / 2.
        if self.actual_carrier_freq > nyquist_freq:
            self._logger.warning(
                "# WARNING: the carrier frequency is greater than nyquist frequency: {0}MHz > {1}MHz".format(
                    self.actual_carrier_freq, nyquist_freq))
        self._logger.info(
            "Num. samples: {0}, DAC Freq.: {1}MHz".format(
                self.num_sample, self.dac_freq))
        self._logger.info(
            "Carrier Freq.: {0}MHz, Amplitude:{1}".format(
                self.carrier_freq, self.amplitude))
        self._logger.info(
            "Cycles: {0}, Rounded cycles: {1}, Actual carrier Freq.: {2}MHz".format(
                self.cycles, self.r_cycles, self.actual_carrier_freq))

    def set_parameter(self, *,
                      num_sample=None, dac_freq=None, carrier_freq=None, sweep_end_freq=None,
                      amplitude=None, pulse_dutyratio=None, impulse_delta=None):

        if num_sample == None:
            pass
        elif not isinstance(num_sample, int):
            raise ValueError("num_sample must be integer")
        elif num_sample < 32:
            raise ValueError("num_sample must be greater than or equal to 32")
        elif num_sample % 32 != 0:
            raise ValueError("num_sample must be multiples of 32")
        self.num_sample = num_sample or self.num_sample

        if dac_freq == None:
            pass
        elif dac_freq <= 0.:
            raise ValueError("dac_freq must be greater than 0.0")
        self.dac_freq = float(dac_freq or self.dac_freq)

        if carrier_freq == None:
            pass
        elif carrier_freq <= 0.:
            raise ValueError("carrier_freq must be greater than 0.0")
        self.carrier_freq = float(carrier_freq or self.carrier_freq)

        if sweep_end_freq == None:
            pass
        elif sweep_end_freq <= 0.:
            raise ValueError("sweep_end_freq must be greater than 0.0")
        self.sweep_end_freq = float(sweep_end_freq or self.sweep_end_freq)

        if pulse_dutyratio == None:
            pass
        elif pulse_dutyratio > 1. or pulse_dutyratio < 0.:
            raise ValueError("pulse_dutyratio must be range of 0.0 - 1.0")
        self.pulse_dutyratio = float(pulse_dutyratio or self.pulse_dutyratio)

        if impulse_delta == None:
            pass
        elif not isinstance(impulse_delta, int):
            raise ValueError("impulse_delta must be integer")
        elif impulse_delta > self.num_sample or impulse_delta < 0:
            raise ValueError("impulse_delta must be range of 0 to num_sample")
        self.impulse_delta = impulse_delta

        self.amplitude = float(amplitude or self.amplitude)

        self._set_subparam()

    def sinwave(self, mode="sin"):
        omega = 2. * numpy.pi * numpy.linspace(
            0., self.r_cycles, self.num_sample, endpoint=False)
        if mode == "iq":
            wave = numpy.array([numpy.sin(omega), numpy.cos(omega)]).T.reshape(-1)
        elif mode == "cos":
            wave = numpy.cos(omega)
        else:
            wave = numpy.sin(omega)
        wave = wave * self.amplitude
        wave = numpy.clip(numpy.round(wave), -32768., 32767.).astype("<i2")
        self._put_paramlog()
        return wave.tobytes()

    def pulsewave(self):
        wave = numpy.linspace(0., self.r_cycles, self.num_sample, endpoint=False)
        wave = numpy.array(
            numpy.modf(wave)[0] < self.pulse_dutyratio).astype("float")
        wave = (2. * wave - 1.0) * self.amplitude
        wave = numpy.clip(numpy.round(wave), -32768., 32767.).astype("<i2")
        self._put_paramlog()
        self._logger.info(
            "Duty Ratio: {0}%".format(self.pulse_dutyratio * 100.))
        return wave.tobytes()

    def sawwave(self):
        wave = numpy.linspace(0.5, self.r_cycles + 0.5, self.num_sample,
            endpoint=False)
        wave = (2. * (wave % 1.) - 1.0) * self.amplitude
        wave = numpy.clip(numpy.round(wave), -32768., 32767.).astype("<i2")
        self._put_paramlog()
        return wave.tobytes()

    def triwave(self):
        wave = numpy.linspace(0.25, self.r_cycles + 0.25, self.num_sample,
            endpoint=False)
        wave = (-2. * numpy.abs(2. * (wave % 1.) - 1.) + 1.) * self.amplitude
        wave = numpy.clip(numpy.round(wave), -32768., 32767.).astype("<i2")
        self._put_paramlog()
        return wave.tobytes()

    def impluse(self):
        wave = numpy.zeros(self.num_sample)
        wave[0:self.impulse_delta] = self.amplitude
        wave = numpy.clip(numpy.round(wave), -32768., 32767.).astype("<i2")
        self._logger.info(
            "Num. samples: {0}, Amplitude: {1}, Impluse Delta: {2}".format(
                self.num_sample, self.amplitude, self.impulse_delta))
        return wave.tobytes()

    def sinsweep(self):
        t = numpy.linspace(0., self.num_sample / (self.dac_freq * 1.e6),
            self.num_sample, endpoint=False)
        f = (self.carrier_freq + ((self.sweep_end_freq - self.carrier_freq
            ) * (self.dac_freq * 1.e6) / self.num_sample * t)) * 1.e6
        wave = self.amplitude * numpy.sin(2. * numpy.pi * f * t)
        wave = numpy.clip(numpy.round(wave), -32768., 32767.).astype("<i2")
        self._logger.info(
            "Num. samples: {0}, DAC Freq.: {1}MHz".format(
                self.num_sample, self.dac_freq))
        self._logger.info(
            "Sweep Start Freq.: {0}MHz, Sweep End Freq.:{1}, Amplitude:{2}".format(
                self.carrier_freq, self.sweep_end_freq, self.amplitude))
        return wave.tobytes()
