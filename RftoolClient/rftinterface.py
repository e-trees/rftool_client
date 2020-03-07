#!/usr/bin/env python3
# coding: utf-8


from RftoolClient import cmdutil, rfterr
import socket
import logging


"""
rftinterface.py
    - RFTOOLs command / data communication interface
"""


class RftoolInterface(object):
    def __init__(self, logger=None):
        self._logger = logging.getLogger(__name__)
        self._logger.addHandler(logging.NullHandler())
        self._logger = logger or self._logger

        self.sock = None
        self._joinargs = cmdutil.CmdUtil.joinargs
        self.err_connection = False

        self._logger.debug("RftoolInterface __init__")

    def attach_socket(self, sock):
        self.sock = sock

    def send_command(self, cmd):
        cmd = cmd.encode() + b"\r\n"
        try:
            self.sock.sendall(cmd)
        except (ConnectionError, socket.timeout):
            self.err_connection = True
            raise

    def recv_response(self):
        res = b""
        try:
            while res[-1:] != b"\n":
                res += self.sock.recv(1)
        except (ConnectionError, socket.timeout):
            self.err_connection = True
            self._logger.error("received string: {}".format(res))
            raise
        res = res.decode()

        return res

    def put(self, command):
        self._logger.debug("> " + command)
        self.send_command(command)
        res = self.recv_response().replace("\r\n", "")
        self._logger.debug(res)

        if res[:5] == "ERROR":
            self.send_command("GetLog")
            log = self.recv_response().replace("\r\n", "")
            raise rfterr.RftoolExecuteCommandError(
                " ".join([res, log[6:]]))

        return res

    def put_mult(self, commands):
        is_error = False
        responses = []
        logs = []

        self._logger.debug("> " + "\r\n.. ".join(commands))
        self.send_command("\r\n".join(commands))

        for cmd in commands:
            res = self.recv_response().replace("\r\n", "")

            if res[:5] == "ERROR":
                is_error = True
                self.send_command("GetLog")
                log = self.recv_response().replace("\r\n", "")
                res = " ".join([res, log[6:]])
                logs.append(res)
            else:
                self._logger.debug(res)

            responses.append(res)

        if is_error:
            raise rfterr.RftoolExecuteCommandError(
                " ".join(logs))

        return responses

    def send_data(self, data, bufsize=2048):
        total = 0
        size = len(data)
        count = 0
        try:
            while total < size:
                sent = self.sock.send(data[total:total + bufsize])
                if sent < bufsize:
                    sent += self.sock.send(data[total+sent:total+bufsize])
                if sent == 0:
                    raise ConnectionError("socket connection broken")
                total += sent
                if count % 8192 == 8191:
                    self._logger.info("  ... sent {} bytes".format(total))
                count += 1

        except (ConnectionError, socket.timeout):
            self.err_connection = True
            raise

        finally:
            self._logger.info("  total sent {} bytes".format(total))
        return total

    def recv_data(self, size, bufsize=2048):
        chunks = []
        received = 0
        count = 0
        try:
            while received < size:
                buf = self.sock.recv(min(size - received, bufsize))
                if buf == b"":
                    raise ConnectionError("socket connection broken")
                chunks.append(buf)
                received += len(buf)
                if count % 8192 == 8191:
                    self._logger.info(
                        "  ... received {} bytes".format(received))
                count += 1

        except (ConnectionError, socket.timeout):
            self.err_connection = True
            raise

        recvdata = b"".join(chunks)
        self._logger.info("  total received {} bytes".format(len(recvdata)))
        return recvdata

    def WriteDataToMemory(self, type, channel, size, data):
        """Write data to the memory allocated to the ADC/DAC/PMOD/Coefficients/Parameters.

        Parameters
        ----------
        Bitstream : DRAM 8-ADC/8-DAC design (1)
            type : int
                0 -> ADC capture data
                1 -> DAC waveform data
                2 -> PMOD digital out data
            channel : int
                - type : 0(ADC)
                    0 -> ADC Tile 0 Block 0
                    1 -> ADC Tile 0 Block 1
                    2 -> ADC Tile 1 Block 0
                    3 -> ADC Tile 1 Block 1
                    4 -> ADC Tile 2 Block 0
                    5 -> ADC Tile 2 Block 1
                    6 -> ADC Tile 3 Block 0
                    7 -> ADC Tile 3 Block 1
                - type : 1(DAC)
                    0 -> DAC Tile 0 Block 0
                    1 -> DAC Tile 0 Block 1
                    2 -> DAC Tile 0 Block 2
                    3 -> DAC Tile 0 Block 3
                    4 -> DAC Tile 1 Block 0
                    5 -> DAC Tile 1 Block 1
                    6 -> DAC Tile 1 Block 2
                    7 -> DAC Tile 1 Block 3
                - type : 2(PMOD)
                    The parameter is ignored
            size : int
                Data size (unit: byte)
                Usually specify the length of the data (e.g. len(data)).
            data : bytes
                Bytes of transmission data
                - type : 0(ADC), 1(DAC)
                    16-bit Integer, Little-endian, real only or I/Q interleaved data, max. 256MB.
                - type : 2(PMOD digital out data)
                    8-bit logic, max. 4kB.

        Bitstream : DRAM 2-ADC/2-DAC design (2)
            type : int
                0 -> ADC capture data
                1 -> DAC waveform data
                2 -> PMOD digital out data
            channel : int
                - type : 0(ADC)
                    0, 2, 4, 6 -> ADC Tile {0, 1, 2, 3} Block 0 shared memory.
                    1, 3, 5, 7 -> ADC Tile {0, 1, 2, 3} Block 1 shared memory.
                - type : 1(DAC)
                    0, 2, 4, 6 -> DAC Tile {0, 1} Block {0, 2} shared memory.
                    1, 3, 5, 7 -> DAC Tile {0, 1} Block {1, 3} shared memory.
                - type : 2(PMOD)
                    The parameter is ignored
            size : int
                Data size (unit: byte)
                Usually specify the length of the data (e.g. len(data)).
            data : bytes
                Bytes of transmission data
                - type : 0(ADC), 1(DAC)
                    16-bit Integer, Little-endian, real only or I/Q interleaved data, max. 1GB.
                - type : 2(PMOD digital out data)
                    8-bit logic, max. 4kB.

        Bitstream : BRAM accumulation design (3)
            type : int
                0 -> ADC capture/accumulation data
                1 -> DAC waveform data
                2 -> PMOD digital out data
            channel : int
                - type : 0(ADC)
                    0 -> ADC Tile 0 Block 0
                    1 -> ADC Tile 0 Block 1
                    2 -> ADC Tile 1 Block 0
                    3 -> ADC Tile 1 Block 1
                    4 -> ADC Tile 2 Block 0
                    5 -> ADC Tile 2 Block 1
                    6 -> ADC Tile 3 Block 0
                    7 -> ADC Tile 3 Block 1
                - type : 1(DAC)
                    0 -> DAC Tile 0 Block 0
                    1 -> DAC Tile 0 Block 1
                    2 -> DAC Tile 0 Block 2
                    3 -> DAC Tile 0 Block 3
                    4 -> DAC Tile 1 Block 0
                    5 -> DAC Tile 1 Block 1
                    6 -> DAC Tile 1 Block 2
                    7 -> DAC Tile 1 Block 3
                - type : 2(PMOD)
                    The parameter is ignored
            size : int
                Data size (unit: byte)
                Usually specify the length of the data (e.g. len(data)).
            data : bytes
                Bytes of transmission data
                - type : 0(ADC)
                    32-bit Integer, Little-endian, Real only or I/Q interleaved data, max. 128kB.
                - type : 1(DAC)
                    16-bit Integer, Little-endian, Real only or I/Q interleaved data, max. 64kB.
                - type : 2(PMOD digital out data)
                    8-bit logic, max. 4kB.

            Bitstream : BRAM accumulation design (4)
            type : int
                0 -> ADC capture data
                1 -> DAC waveform data
                2 -> PMOD digital out data
                3 -> Coefficients for ADC Multiply-accumulate
                4 -> Coefficients for Multiply-accumulate result comparation
                5 -> DAC Num of word/Start of word parameters
            channel : int
                - type : 0(ADC capture data), 1(DAC waveform data), 3(ADC MAC coefficients),
                         4(ADC MAC result comparation coefficients), 5(DAC parameters)
                    0 -> ADC Tile 0 Block 0 (I) to trigger DAC Tile 1 Block 2
                    1 -> ADC Tile 0 Block 0 (Q) to trigger DAC Tile 1 Block 2
                    2 -> ADC Tile 0 Block 1 (I) to trigger DAC Tile 1 Block 3
                    3 -> ADC Tile 0 Block 1 (Q) to trigger DAC Tile 1 Block 3
                    4 -> ADC Tile 1 Block 0 (I) to trigger DAC Tile 1 Block 0
                    5 -> ADC Tile 1 Block 0 (Q) to trigger DAC Tile 1 Block 0
                    6 -> ADC Tile 1 Block 1 (I) to trigger DAC Tile 1 Block 1
                    7 -> ADC Tile 1 Block 1 (Q) to trigger DAC Tile 1 Block 1
                    8 -> ADC Tile 2 Block 0 (I) to trigger DAC Tile 0 Block 0
                    9 -> ADC Tile 2 Block 0 (Q) to trigger DAC Tile 0 Block 0
                    10 -> ADC Tile 2 Block 1 (I) to trigger DAC Tile 0 Block 1
                    11 -> ADC Tile 2 Block 1 (Q) to trigger DAC Tile 0 Block 1
                    12 -> ADC Tile 3 Block 0 (I) to trigger DAC Tile 0 Block 2
                    13 -> ADC Tile 3 Block 0 (Q) to trigger DAC Tile 0 Block 2
                    14 -> ADC Tile 3 Block 1 (I) to trigger DAC Tile 0 Block 3
                    15 -> ADC Tile 3 Block 1 (Q) to trigger DAC Tile 0 Block 3
                - type : 2(PMOD)
                    The parameter is ignored
            size : int
                Data size (unit: byte)
                Usually specify the length of the data (e.g. len(data)).
            data : bytes
                Bytes of transmission data
                - type : 0(ADC capture data)
                    16-bit signed integer, max. 2kB.
                - type : 1(DAC waveform data)
                    16-bit signed integer, Real only or I/Q interleaved format, max. 64kB.
                - type : 2(PMOD digital out data)
                    8-bit logic, max. 4kB.
                - type : 3(Coefficients for ADC Multiply-accumulate)
                    32-bit signed integer, max. 4kB.
                - type : 4(Coefficients for Multiply-accumulate result comparation)
                    32-bit signed integer, 12bytes.
                - type : 5(DAC Num of word/Start of word parameters)
                    32-bit unsigned integer, 128bytes.
        """
        if size > len(data):
            raise rfterr.RftoolInterfaceError(
                "The specified size is larger than the data size.")
        cmd = self._joinargs("WriteDataToMemory", [type, channel, size])

        self.send_command(cmd)
        self._logger.debug("> " + cmd)

        try:
            self.send_data(data)
        except (ConnectionError, socket.timeout):
            self.err_connection = True
            raise

        try:
            res = self.recv_response()
            self._logger.debug(res)
        except (ConnectionError, socket.timeout):
            self.err_connection = True
            raise

    def ReadDataFromMemory(self, type, channel, size):
        """Read data from the memory allocated to the ADC/DAC/PMOD/Coefficients/Parameters.

        Parameters
        ----------
        Bitstream : DRAM 8-ADC/8-DAC design (1)
            type : int
                0 -> ADC capture data
                1 -> DAC waveform data
                2 -> PMOD digital out data
            channel : int
                - type : 0(ADC)
                    0 -> ADC Tile 0 Block 0
                    1 -> ADC Tile 0 Block 1
                    2 -> ADC Tile 1 Block 0
                    3 -> ADC Tile 1 Block 1
                    4 -> ADC Tile 2 Block 0
                    5 -> ADC Tile 2 Block 1
                    6 -> ADC Tile 3 Block 0
                    7 -> ADC Tile 3 Block 1
                - type : 1(DAC)
                    0 -> DAC Tile 0 Block 0
                    1 -> DAC Tile 0 Block 1
                    2 -> DAC Tile 0 Block 2
                    3 -> DAC Tile 0 Block 3
                    4 -> DAC Tile 1 Block 0
                    5 -> DAC Tile 1 Block 1
                    6 -> DAC Tile 1 Block 2
                    7 -> DAC Tile 1 Block 3
                - type : 2(PMOD)
                    The parameter is ignored
            size : int
                Data size (unit: byte)
                Usually specify the length of the data (e.g. len(data)).

        Bitstream : DRAM 2-ADC/2-DAC design (2)
            type : int
                0 -> ADC capture data
                1 -> DAC waveform data
                2 -> PMOD digital out data
            channel : int
                - type : 0(ADC)
                    0, 2, 4, 6 -> ADC Tile {0, 1, 2, 3} Block 0 shared memory.
                    1, 3, 5, 7 -> ADC Tile {0, 1, 2, 3} Block 1 shared memory.
                - type : 1(DAC)
                    0, 2, 4, 6 -> DAC Tile {0, 1} Block {0, 2} shared memory.
                    1, 3, 5, 7 -> DAC Tile {0, 1} Block {1, 3} shared memory.
                - type : 2(PMOD)
                    The parameter is ignored
            size : int
                Data size (unit: byte)
                Usually specify the length of the data (e.g. len(data)).

        Bitstream : BRAM accumulation design (3)
            type : int
                0 -> ADC capture/accumulation data
                1 -> DAC waveform data
                2 -> PMOD digital out data
            channel : int
                - type : 0(ADC)
                    0 -> ADC Tile 0 Block 0
                    1 -> ADC Tile 0 Block 1
                    2 -> ADC Tile 1 Block 0
                    3 -> ADC Tile 1 Block 1
                    4 -> ADC Tile 2 Block 0
                    5 -> ADC Tile 2 Block 1
                    6 -> ADC Tile 3 Block 0
                    7 -> ADC Tile 3 Block 1
                - type : 1(DAC)
                    0 -> DAC Tile 0 Block 0
                    1 -> DAC Tile 0 Block 1
                    2 -> DAC Tile 0 Block 2
                    3 -> DAC Tile 0 Block 3
                    4 -> DAC Tile 1 Block 0
                    5 -> DAC Tile 1 Block 1
                    6 -> DAC Tile 1 Block 2
                    7 -> DAC Tile 1 Block 3
                - type : 2(PMOD)
                    The parameter is ignored
            size : int
                Data size (unit: byte)
                Usually specify the length of the data (e.g. len(data)).

        Bitstream : BRAM accumulation design (4)
            type : int
                0 -> ADC capture data
                1 -> DAC waveform data
                2 -> PMOD digital out data
                3 -> Coefficients for ADC Multiply-accumulate
                4 -> Coefficients for Multiply-accumulate result comparation
                5 -> DAC Num of word/Start of word parameters
            channel : int
                - type : 0(ADC capture data), 1(DAC waveform data), 3(ADC MAC coefficients),
                         4(ADC MAC result comparation coefficients), 5(DAC parameters)
                    0 -> ADC Tile 0 Block 0 (I) to trigger DAC Tile 1 Block 2
                    1 -> ADC Tile 0 Block 0 (Q) to trigger DAC Tile 1 Block 2
                    2 -> ADC Tile 0 Block 1 (I) to trigger DAC Tile 1 Block 3
                    3 -> ADC Tile 0 Block 1 (Q) to trigger DAC Tile 1 Block 3
                    4 -> ADC Tile 1 Block 0 (I) to trigger DAC Tile 1 Block 0
                    5 -> ADC Tile 1 Block 0 (Q) to trigger DAC Tile 1 Block 0
                    6 -> ADC Tile 1 Block 1 (I) to trigger DAC Tile 1 Block 1
                    7 -> ADC Tile 1 Block 1 (Q) to trigger DAC Tile 1 Block 1
                    8 -> ADC Tile 2 Block 0 (I) to trigger DAC Tile 0 Block 0
                    9 -> ADC Tile 2 Block 0 (Q) to trigger DAC Tile 0 Block 0
                    10 -> ADC Tile 2 Block 1 (I) to trigger DAC Tile 0 Block 1
                    11 -> ADC Tile 2 Block 1 (Q) to trigger DAC Tile 0 Block 1
                    12 -> ADC Tile 3 Block 0 (I) to trigger DAC Tile 0 Block 2
                    13 -> ADC Tile 3 Block 0 (Q) to trigger DAC Tile 0 Block 2
                    14 -> ADC Tile 3 Block 1 (I) to trigger DAC Tile 0 Block 3
                    15 -> ADC Tile 3 Block 1 (Q) to trigger DAC Tile 0 Block 3
                - type : 2(PMOD)
                    The parameter is ignored
            size : int
                Data size (unit: byte)
                Usually specify the length of the data (e.g. len(data)).

        Returns
        -------
        Bitstream : DRAM 8-ADC/8-DAC design (1)
            data : bytes
                Bytes of transmission data
                - type : 0(ADC), 1(DAC)
                    16-bit Integer, Little-endian, real only or I/Q interleaved data, max. 256MB.
                - type : 2(PMOD digital out data)
                    8-bit logic, max. 4kB.

        Bitstream : DRAM 2-ADC/2-DAC design (2)
            data : bytes
                Bytes of transmission data
                - type : 0(ADC), 1(DAC)
                    16-bit Integer, Little-endian, real only or I/Q interleaved data, max. 1GB.
                - type : 2(PMOD digital out data)
                    8-bit logic, max. 4kB.

        Bitstream : BRAM accumulation design (3)
            data : bytes
                Bytes of transmission data
                - type : 0(ADC)
                    32-bit Integer, Little-endian, Real only or I/Q interleaved data, max. 128kB.
                - type : 1(DAC)
                    16-bit Integer, Little-endian, Real only or I/Q interleaved data, max. 64kB.
                - type : 2(PMOD digital out data)
                    8-bit logic, max. 4kB.

        Bitstream : BRAM accumulation design (4)
        data : bytes
            Bytes of transmission data
            - type : 0(ADC capture data)
                16-bit signed integer, max. 2kB.
            - type : 1(DAC waveform data)
                16-bit signed integer, Real only or I/Q interleaved format, max. 64kB.
            - type : 2(PMOD digital out data)
                8-bit logic, max. 4kB.
            - type : 3(Coefficients for ADC Multiply-accumulate)
                32-bit signed integer, max. 4kB.
            - type : 4(Coefficients for Multiply-accumulate result comparation)
                32-bit signed integer, 12bytes.
            - type : 5(DAC Num of word/Start of word parameters)
                32-bit unsigned integer, 128bytes.
        """
        cmd = self._joinargs("ReadDataFromMemory", [type, channel, size])

        self.send_command(cmd)
        self._logger.debug("> " + cmd)

        data = self.recv_data(size)
        self.recv_response()  # passing line feed (\r\n) next to end of data

        res = self.recv_response()
        self._logger.debug(res)

        return data
