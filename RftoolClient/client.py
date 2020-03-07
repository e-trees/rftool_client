#!/usr/bin/env python3
# coding: utf-8

"""
client.py
    - A Client for command/data interface of Xilinx ZCU111 TRD 2019.1 RFTOOL
"""

from RftoolClient import rftcmd, rftinterface, rfterr
import socket
import logging


class RftoolClient(object):
    def __init__(self, logger=None, timeout=10.0):

        self._logger = logging.getLogger(__name__)
        self._logger.addHandler(logging.NullHandler())
        self._logger = logger or self._logger

        self.if_ctrl = rftinterface.RftoolInterface(self._logger)
        self.if_data = rftinterface.RftoolInterface(self._logger)
        self.command = rftcmd.RftoolCommand(self.if_ctrl, self._logger)

        self.address = ""
        self.port_ctrl = 0
        self.port_data = 0

        self.sock_data = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock_ctrl = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.err_connection = False

        self.if_ctrl.attach_socket(self.sock_ctrl)
        self.if_data.attach_socket(self.sock_data)

        self.settimeout(timeout)

        self._logger.debug("RftoolClient __init__")

    def __enter__(self):
        self._logger.debug("RftoolClient __enter__")
        return self

    def __exit__(self, excep_type, excep_val, trace):
        self.close()
        self._logger.debug("RftoolClient __exit__")

    def settimeout(self, timeout):
        self.sock_data.settimeout(timeout)
        self.sock_ctrl.settimeout(timeout)

        self._logger.debug("RftoolClient settimeout")

    def connect(self, address, port_ctrl=8081, port_data=8082):
        self.address = address
        self.port_data = port_data
        self.port_ctrl = port_ctrl

        try:
            self.sock_data.connect((self.address, self.port_data))
            self.sock_ctrl.connect((self.address, self.port_ctrl))
        except ConnectionError:
            self.err_connection = True
            raise

        self._logger.debug("RftoolClient connect")

    def close(self):
        err_c = self.err_connection | \
            self.if_ctrl.err_connection | self.if_data.err_connection

        if err_c == False:
            self.if_ctrl.put("disconnect")
            self.sock_data.shutdown(socket.SHUT_RDWR)
            self.sock_ctrl.shutdown(socket.SHUT_RDWR)

        self.sock_data.close()
        self.sock_ctrl.close()

        self._logger.debug("RftoolClient close")
