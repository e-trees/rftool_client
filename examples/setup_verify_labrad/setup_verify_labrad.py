#!/usr/bin/env python3
# coding: utf-8

"""
rftoolクライアント サンプルプログラム: 疎通確認プログラム (LabRADサーバ接続)

<使用ライブラリ>
    pylabrad
"""

import sys
import time
import socket
import logging
import labrad
import pathlib

lib_path = str(pathlib.Path(__file__).resolve().parents[2])
sys.path.append(lib_path)

# Parameters
LABRAD_HOST = "localhost"

# Log level
LOG_LEVEL = logging.WARN


def main():
    status = 0

    try:
        cxn = labrad.connect(LABRAD_HOST)
        rft = cxn.zcu111_rftool_labrad_server
        rft.version()
    except Exception as e:
        status = 1
        print("exception:", e)

    return status


if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    handler = logging.StreamHandler()
    handler.setLevel(LOG_LEVEL)
    logger.setLevel(LOG_LEVEL)
    logger.addHandler(handler)

    status = main()

    if status == 0:
        print("Connection test succeeded")
    else:
        print("Connection test failed")

    sys.exit(status)
