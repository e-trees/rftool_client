from RftoolClient import cmdutil, rfterr
import logging

class CommonCommand(object):
    
    PL_DDR4_RAM_SIZE = 0x100000000

    def __init__(self, ctrl_interface, data_interface, logger=None):
        self.__logger = logging.getLogger(__name__)
        self.__logger.addHandler(logging.NullHandler())
        self.__logger = logger or self.__logger
        self.__rft_ctrl_if = ctrl_interface
        self.__rft_data_if = data_interface
        self.__joinargs = cmdutil.CmdUtil.joinargs
        self.__stim_reg_access = StimRegAccess(ctrl_interface, data_interface)


    def read_dram(self, offset, size, show_progress = False):
        """
        PL に接続された外部 DRAM の任意のアドレスからデータを読み取る.
        
        Parameters
        ----------
        offset : int
            データを取得する DRAM 内部のアドレス.
        size : int
            読み取るサイズ (Bytes)
        
        Returns
        -------
        data : bytes
            DRAM のデータ
        """
        if (not isinstance(offset, int) or (offset < 0 or 0xFFFFFFFF < offset)):
            raise ValueError("invalid offset " + str(offset))

        if (not isinstance(size, int) or (size <= 0 or self.PL_DDR4_RAM_SIZE < (size + offset))):
            raise ValueError(
                "invalid read addr range  ({} - {})\n".format(offset, size + offset - 1) + 
                "The valid one is 0 to {}.".format(self.PL_DDR4_RAM_SIZE - 1))

        command = self.__joinargs("ReadDram", [offset, size])
        self.__rft_data_if.send_command(command)
        res = self.__rft_data_if.recv_response().rstrip('\r\n') # キャプチャデータの前のコマンド成否レスポンス  AWG_SUCCESS/AWG_FAILURE
        if (res == "AWG_SUCCESS"):
            data = self.__rft_data_if.recv_data(
                size, bufsize = 0x400000, show_progress = show_progress)
            res = self.__rft_data_if.recv_response() # end of capture data

        res = self.__rft_data_if.recv_response() # end of 'ReadDram' command
        if res[:5] == "ERROR":
            raise rfterr.RftoolExecuteCommandError(res)

        return data


    def write_dram(self, offset, data, show_progress = False):
        """
        PL に接続された外部 DRAM の任意のアドレスにデータを書き込む.
        
        Parameters
        ----------
        offset : int
            データを書き込む DRAM 内部のアドレス.
        data : bytes
            書き込みデータ
        """
        if (not isinstance(offset, int) or (offset < 0 or 0xFFFFFFFF < offset)):
            raise ValueError("invalid offset " + str(offset))
        
        if (not isinstance(data, (bytes, bytearray))):
            raise ValueError("invalid write data type {}",format(type(data)))

        size = len(data)
        if (not isinstance(size, int) or (size <= 0 or self.PL_DDR4_RAM_SIZE < (size + offset))):
            raise ValueError(
                "invalid write addr range  ({} - {})\n".format(offset, size + offset - 1) + 
                "The valid one is 0 to {}.".format(self.PL_DDR4_RAM_SIZE - 1))

        command = self.__joinargs("WriteDram", [offset, size])
        self.__rft_data_if.send_command(command)
        res = self.__rft_data_if.recv_response().rstrip('\r\n') # キャプチャデータの前のコマンド成否レスポンス  AWG_SUCCESS/AWG_FAILURE
        if (res == "AWG_SUCCESS"):
            self.__rft_data_if.send_data(
                data, bufsize = 0x400000, show_progress = show_progress)

        res = self.__rft_data_if.recv_response() # end of 'WriteDram' command
        if res[:5] == "ERROR":
            raise rfterr.RftoolExecuteCommandError(res)

        return data


    def sync_dac_tiles(self):
        """
        全ての DAC タイルを同期させる.
        このメソッドを呼ぶ前に, DAC データパスの設定 (I/Q ミキサ, 補間など) の設定を完了させておくこと.
        """
        command = self.__joinargs("SyncMultiTiles", [0, 1])
        self.__rft_ctrl_if.put(command)

    
    def sync_adc_tiles(self):
        """
        全ての ADC タイルを同期させる.
        このメソッドを呼ぶ前に, ADC データパスの設定 (I/Q ミキサ, 間引きなど) の設定を完了させておくこと.
        """
        command = self.__joinargs("SyncMultiTiles", [1, 0])
        self.__rft_ctrl_if.put(command)


    @property
    def stim_reg_access(self):
        return self.__stim_reg_access


class StimRegAccess:
    __REG_SIZE = 4 # bytes

    def __init__(self, ctrl_interface, data_interface):
        self.__rft_ctrl_if = ctrl_interface
        self.__rft_data_if = data_interface
        self.__joinargs = cmdutil.CmdUtil.joinargs

    def write(self, addr, val):
        self.write_multi(addr, *[val])


    def write_multi(self, addr, *vals):
        wr_data = bytearray()
        for val in vals:
            val = val & ((1 << (self.__REG_SIZE * 8)) - 1)
            wr_data += val.to_bytes(self.__REG_SIZE, 'little')

        command = self.__joinargs('WriteStimRegs', [addr, len(wr_data)])
        self.__rft_data_if.PutCmdWithData(command, wr_data, bufsize = 0x4000)


    def write_bits(self, addr, bit_offset, bit_len, val):
        command = self.__joinargs('WriteStimRegBits', [addr, bit_offset, bit_len, val])
        self.__rft_ctrl_if.put(command)


    def read(self, addr):
        return self.read_multi(addr, 1)[0]


    def read_multi(self, addr, num_regs):
        len = num_regs * self.__REG_SIZE
        command = self.__joinargs('ReadStimRegs', [addr, len])
        self.__rft_data_if.send_command(command)
        reg_data = self.__rft_data_if.recv_data(len, bufsize = 0x4000)
        res = self.__rft_data_if.recv_response() # end of 'ReadDram' command
        if res[:5] == "ERROR":
            raise rfterr.RftoolExecuteCommandError(res)

        return [
            int.from_bytes(reg_data[i * self.__REG_SIZE : (i + 1) * self.__REG_SIZE], 'little') 
            for i in range(num_regs)]


    def read_bits(self, addr, bit_offset, bit_len):
        command = self.__joinargs('ReadStimRegBits', [addr, bit_offset, bit_len])
        return int(self.__rft_ctrl_if.put(command))
