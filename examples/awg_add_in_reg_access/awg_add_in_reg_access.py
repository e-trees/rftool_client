#!/usr/bin/env python3
# coding: utf-8

"""
外部トリガサンプルプログラム
AWG 4 が出力した波形を外部トリガモジュール 4 が受け取り, AWG 0 ～ AWG 3, AWG 5 ～ AWG 7 にトリガをかける.
"""

import os
import sys
import time
import logging
import pathlib
import random

lib_path = str(pathlib.Path(__file__).resolve().parents[2])
sys.path.append(lib_path)
from RftoolClient import client, rfterr, wavegen, ndarrayutil

# Parameters
ZCU111_IP_ADDR = os.environ.get('ZCU111_IP_ADDR', "192.168.1.3")
# Log level
LOG_LEVEL = logging.INFO

# Constants
BITSTREAM = 10 # AWG SA BINARIZATION
BITSTREAM_LOAD_TIMEOUT = 10

def config_bitstream(rftcmd, num_design):
    if rftcmd.GetBitstream() != num_design:
        rftcmd.SetBitstream(num_design)
        for i in range(BITSTREAM_LOAD_TIMEOUT):
            time.sleep(2.)
            if rftcmd.GetBitstreamStatus() == 1:
                break
            if i > BITSTREAM_LOAD_TIMEOUT:
                raise Exception(
                    "Failed to configure bitstream, please reboot ZCU111.")

def main():
    with client.RftoolClient(logger=logger) as rft:
        print("Connect to RFTOOL Server.")
        rft.connect(ZCU111_IP_ADDR)
        rft.command.TermMode(0)
        print("Configure Bitstream.")
        config_bitstream(rft.command, BITSTREAM)
      
        # 初期化
        rft.awg_sa_cmd.initialize_awg_sa()
        # 機能拡張用レジスタにアクセス
        for idx in range(4):
            wr_val = random.randint(0, 0xFFFFFFFF)
            rft.awg_sa_cmd.write_user_ctrl_reg(idx, wr_val)
            rd_val_0 = rft.awg_sa_cmd.read_user_ctrl_reg(idx)
            rd_val_1 = rft.awg_sa_cmd.read_user_status_reg(idx)
            print('[WR]  user ctrl   reg {} : 0x{:08x}'.format(idx, wr_val))
            print('[RD]  user ctrl   reg {} : 0x{:08x}'.format(idx, rd_val_0))
            print('[RD]  user status reg {} : 0x{:08x}\n'.format(idx, rd_val_1))
        
    print("Done.")
    return


if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    handler = logging.StreamHandler()
    handler.setLevel(LOG_LEVEL)
    logger.setLevel(LOG_LEVEL)
    logger.addHandler(handler)
    main()
