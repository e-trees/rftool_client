#!/usr/bin/env python3
# coding: utf-8

import numpy as np


"""
ndarrayutil.py
    - Conversion functions between np.ndarray and data type
"""

class NdarrayUtil:

    @classmethod
    def real_to_bytes(cls, data):
        if not isinstance(data, np.ndarray):
            raise ValueError(
                "argument must be numpy.ndarray, but {} found".format(type(data)))
        elif not np.issubdtype(data.dtype, np.integer) and not np.issubdtype(data.dtype, np.floating):
            raise ValueError(
                "ndarray.dtype must be integer or float, but {} found".format(data.dtype))

        return np.round(data).astype("<i2").tobytes()

    @classmethod
    def bytes_to_real(cls, data):
        if not isinstance(data, bytes):
            raise ValueError(
                "argument must be bytes, but {} found".format(type(data)))

        return np.frombuffer(data, dtype="<i2")

    @classmethod
    def complex_to_bytes(cls, data):
        if not isinstance(data, np.ndarray):
            raise ValueError(
                "argument must be numpy.ndarray, but {} found".format(type(data)))
        elif not np.issubdtype(data.dtype, np.complexfloating):
            raise ValueError(
                "ndarray.dtype must be complex, but {} found".format(type(data.dtype)))

        data = data.reshape(-1, 8)
        data = np.hstack((data.real, data.imag)).reshape(-1)
        return np.round(data).astype("<i2").tobytes()

    @classmethod
    def bytes_to_complex(cls, data):
        if not isinstance(data, bytes):
            raise ValueError(
                "argument must be bytes, but {} found".format(type(data)))

        data = np.frombuffer(data, dtype="<i2").reshape(-1, 2)
        data = data[:, 0] + (1j * data[:, 1])
        return data.astype("complex64")

    @classmethod
    def real_to_bytes_32(cls, data):
        if not isinstance(data, np.ndarray):
            raise ValueError(
                "argument must be numpy.ndarray, but {} found".format(type(data)))
        elif not np.issubdtype(data.dtype, np.integer) and not np.issubdtype(data.dtype, np.floating):
            raise ValueError(
                "ndarray.dtype must be integer or float, but {} found".format(data.dtype))

        return np.round(data).astype("<i4").tobytes()

    @classmethod
    def bytes_to_real_32(cls, data):
        if not isinstance(data, bytes):
            raise ValueError(
                "argument must be bytes, but {} found".format(type(data)))

        return np.frombuffer(data, dtype="<i4")

    @classmethod
    def complex_to_bytes_32(cls, data):
        if not isinstance(data, np.ndarray):
            raise ValueError(
                "argument must be numpy.ndarray, but {} found".format(type(data)))
        elif not np.issubdtype(data.dtype, np.complexfloating):
            raise ValueError(
                "ndarray.dtype must be complex, but {} found".format(type(data.dtype)))

        data = data.reshape(-1, 8)
        data = np.hstack((data.real, data.imag)).reshape(-1)
        return np.round(data).astype("<i4").tobytes()

    @classmethod
    def bytes_to_complex_32(cls, data):
        if not isinstance(data, bytes):
            raise ValueError(
                "argument must be bytes, but {} found".format(type(data)))

        data = np.frombuffer(data, dtype="<i4").reshape(-1, 2)
        data = data[:, 0] + (1j * data[:, 1])
        return data.astype("complex128")

    @classmethod
    def bytes_to_real_64(cls, data):
        if not isinstance(data, bytes):
            raise ValueError(
                "argument must be bytes, but {} found".format(type(data)))

        return np.frombuffer(data, dtype="<i8")
