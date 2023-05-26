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

    def send_data(self, data, bufsize=2048, show_progress = False):
        total = 0
        size = len(data)
        diff = 0
        try:
            while total < size:
                sent = self.sock.send(data[total:total + bufsize])
                if sent < bufsize:
                    sent += self.sock.send(data[total+sent:total+bufsize])
                if sent == 0:
                    raise ConnectionError("socket connection broken")
                total += sent
                diff += sent
                if show_progress and (diff >= 0x2000000):
                    self._logger.info("  ... sent {} bytes".format(total))
                    diff = 0

        except (ConnectionError, socket.timeout):
            self.err_connection = True
            raise

        finally:
            if show_progress:
                self._logger.info("  total sent {} bytes".format(total))
        return total

    def recv_data(self, size, bufsize=2048, show_progress = False):
        chunks = []
        received = 0
        diff = 0
        try:
            while received < size:
                buf = self.sock.recv(min(size - received, bufsize))
                if buf == b"":
                    raise ConnectionError("socket connection broken")
                chunks.append(buf)
                received += len(buf)
                diff += len(buf)
                if show_progress and (diff >= 0x2000000):
                    self._logger.info("  ... received {} bytes".format(received))
                    diff = 0

        except (ConnectionError, socket.timeout):
            self.err_connection = True
            raise

        recvdata = b"".join(chunks)
        if show_progress:
            self._logger.info("  total received {} bytes".format(len(recvdata)))
        return recvdata



    def PutCmdWithData(self, command, data, bufsize = 2048):
        """Send a command followed by data.

        Parameters
        ----------
        cmd : string
            The command to send.
        data : bytes
            The data to send

        Returns
        -------
        The response of the sent command.
        """

        self.send_command(command)
        self._logger.debug("> " + command)

        try:
            self.send_data(data, bufsize = bufsize)
        except (ConnectionError, socket.timeout):
            self.err_connection = True
            raise

        try:
            res = self.recv_response().replace("\r\n", "")
            if res[:5] == "ERROR":
                raise rfterr.RftoolExecuteCommandError(res)
            self._logger.debug(res)
        except (ConnectionError, socket.timeout):
            self.err_connection = True
            raise

        return res