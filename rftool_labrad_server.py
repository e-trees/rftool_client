#!/usr/bin/env python3
# coding: utf-8

import time
import logging
from labrad.server import LabradServer, setting
from twisted.internet.defer import inlineCallbacks
from RftoolClient import client, rfterr


ZCU111_IP_ADDR = "192.168.1.3"
LOG_LEVEL = logging.DEBUG
BUF_MEM_SIZE = 1024 * 1024 * 1024


class RftoolClientWrappedServer(LabradServer):
    name = "LABRAD Server wrapped RFTOOL Client"
    instanceName = "ZCU111 RFTOOL LabRAD Server"

    @inlineCallbacks
    def initServer(self):
        logger = logging.getLogger(__name__)
        handler = logging.StreamHandler()
        handler.setLevel(LOG_LEVEL)
        logger.setLevel(LOG_LEVEL)
        logger.addHandler(handler)
        self.rft = client.RftoolClient(logger)
        self.rft.connect(ZCU111_IP_ADDR)
        self.wr_size = 0
        self.wr_pos = 0
        self.rd_size = 0
        self.rd_pos = 0
        self.buf_mem = bytearray(BUF_MEM_SIZE)
        yield None

    @inlineCallbacks
    def stopServer(self):
        self.rft.close()
        yield None

    @setting(11, "SetMixerSettings")
    def SetMixerSettings(self, c, args):
        return self.rft.command.SetMixerSettings(*args)

    @setting(12, "GetMixerSettings")
    def GetMixerSettings(self, c, args):
        return self.rft.command.GetMixerSettings(*args)

    @setting(13, "GetQMCSettings")
    def GetQMCSettings(self, c, args):
        return self.rft.command.GetQMCSettings(*args)

    @setting(14, "SetExtParentclk")
    def SetExtParentclk(self, c, args):
        return self.rft.command.SetExtParentclk(*args)

    @setting(15, "iic_write")
    def iic_write(self, c, args):
        return self.rft.command.iic_write(*args)

    @setting(16, "iic_read")
    def iic_read(self, c, args):
        return self.rft.command.iic_read(*args)

    @setting(17, "SetExtPllClkRate")
    def SetExtPllClkRate(self, c, args):
        return self.rft.command.SetExtPllClkRate(*args)

    @setting(18, "SetDACPowerMode")
    def SetDACPowerMode(self, c, args):
        return self.rft.command.SetDACPowerMode(*args)

    @setting(19, "GetDACPower")
    def GetDACPower(self, c, args):
        return self.rft.command.GetDACPower(*args)

    @setting(20, "StartUp")
    def StartUp(self, c, args):
        return self.rft.command.StartUp(*args)

    @setting(21, "Shutdown")
    def Shutdown(self, c, args):
        return self.rft.command.Shutdown(*args)

    @setting(22, "RfdcVersion")
    def RfdcVersion(self, c):
        return self.rft.command.RfdcVersion()

    @setting(23, "Version")
    def Version(self, c):
        return self.rft.command.Version()

    @setting(24, "JtagIdcode")
    def JtagIdcode(self, c):
        return self.rft.command.JtagIdcode()

    @setting(25, "GetIPStatus")
    def GetIPStatus(self, c):
        return self.rft.command.GetIPStatus()

    @setting(26, "Reset")
    def Reset(self, c):
        return self.rft.command.Reset()

    @setting(27, "GetPLLConfig")
    def GetPLLConfig(self, c, args):
        return self.rft.command.GetPLLConfig(*args)

    @setting(28, "GetLinkCoupling")
    def GetLinkCoupling(self, c, args):
        return self.rft.command.GetLinkCoupling(*args)

    @setting(29, "SetQMCSettings")
    def SetQMCSettings(self, c, args):
        return self.rft.command.SetQMCSettings(*args)

    @setting(30, "GetCoarseDelaySettings")
    def GetCoarseDelaySettings(self, c, args):
        return self.rft.command.GetCoarseDelaySettings(*args)

    @setting(31, "SetCoarseDelaySettings")
    def SetCoarseDelaySettings(self, c, args):
        return self.rft.command.SetCoarseDelaySettings(*args)

    @setting(32, "GetInterpolationFactor")
    def GetInterpolationFactor(self, c, args):
        return self.rft.command.GetInterpolationFactor(*args)

    @setting(33, "SetInterpolationFactor")
    def SetInterpolationFactor(self, c, args):
        return self.rft.command.SetInterpolationFactor(*args)

    @setting(34, "GetDecimationFactor")
    def GetDecimationFactor(self, c, args):
        return self.rft.command.GetDecimationFactor(*args)

    @setting(35, "SetDecimationFactor")
    def SetDecimationFactor(self, c, args):
        return self.rft.command.SetDecimationFactor(*args)

    @setting(36, "GetNyquistZone")
    def GetNyquistZone(self, c, args):
        return self.rft.command.GetNyquistZone(*args)

    @setting(37, "SetNyquistZone")
    def SetNyquistZone(self, c, args):
        return self.rft.command.SetNyquistZone(*args)

    @setting(38, "GetOutputCurr")
    def GetOutputCurr(self, c, args):
        return self.rft.command.GetOutputCurr(*args)

    @setting(39, "GetPLLLockStatus")
    def GetPLLLockStatus(self, c, args):
        return self.rft.command.GetPLLLockStatus(*args)

    @setting(40, "GetClockSource")
    def GetClockSource(self, c, args):
        return self.rft.command.GetClockSource(*args)

    @setting(41, "DynamicPLLConfig")
    def DynamicPLLConfig(self, c, args):
        return self.rft.command.DynamicPLLConfig(*args)

    @setting(42, "SetFabClkOutDiv")
    def SetFabClkOutDiv(self, c, args):
        return self.rft.command.SetFabClkOutDiv(*args)

    @setting(43, "SetupFIFO")
    def SetupFIFO(self, c, args):
        return self.rft.command.SetupFIFO(*args)

    @setting(44, "GetFIFOStatus")
    def GetFIFOStatus(self, c, args):
        return self.rft.command.GetFIFOStatus(*args)

    @setting(45, "SetFabWrVldWords")
    def SetFabWrVldWords(self, c, args):
        return self.rft.command.SetFabWrVldWords(*args)

    @setting(46, "GetFabWrVldWords")
    def GetFabWrVldWords(self, c, args):
        return self.rft.command.GetFabWrVldWords(*args)

    @setting(47, "SetFabRdVldWords")
    def SetFabRdVldWords(self, c, args):
        return self.rft.command.SetFabRdVldWords(*args)

    @setting(48, "GetFabRdVldWords")
    def GetFabRdVldWords(self, c, args):
        return self.rft.command.GetFabRdVldWords(*args)

    @setting(49, "SetDecoderMode")
    def SetDecoderMode(self, c, args):
        return self.rft.command.SetDecoderMode(*args)

    @setting(50, "GetDecoderMode")
    def GetDecoderMode(self, c, args):
        return self.rft.command.GetDecoderMode(*args)

    @setting(51, "ResetNCOPhase")
    def ResetNCOPhase(self, c, args):
        return self.rft.command.ResetNCOPhase(*args)

    @setting(52, "DumpRegs")
    def DumpRegs(self, c, args):
        return self.rft.command.DumpRegs(*args)

    @setting(53, "UpdateEvent")
    def UpdateEvent(self, c, args):
        return self.rft.command.UpdateEvent(*args)

    @setting(54, "GetCalibrationMode")
    def GetCalibrationMode(self, c, args):
        return self.rft.command.GetCalibrationMode(*args)

    @setting(55, "SetCalibrationMode")
    def SetCalibrationMode(self, c, args):
        return self.rft.command.SetCalibrationMode(*args)

    @setting(56, "GetBlockStatus")
    def GetBlockStatus(self, c, args):
        return self.rft.command.GetBlockStatus(*args)

    @setting(57, "GetThresholdSettings")
    def GetThresholdSettings(self, c, args):
        return self.rft.command.GetThresholdSettings(*args)

    @setting(58, "RF_ReadReg32")
    def RF_ReadReg32(self, c, arg):
        return self.rft.command.RF_ReadReg32(arg)

    @setting(59, "RF_WriteReg32")
    def RF_WriteReg32(self, c, args):
        return self.rft.command.RF_WriteReg32(*args)

    @setting(60, "RF_ReadReg16")
    def RF_ReadReg16(self, c, arg):
        return self.rft.command.RF_ReadReg16(arg)

    @setting(61, "RF_WriteReg16")
    def RF_WriteReg16(self, c, args):
        return self.rft.command.RF_WriteReg16(*args)

    @setting(62, "RF_ReadReg8")
    def RF_ReadReg8(self, c, arg):
        return self.rft.command.RF_ReadReg8(arg)

    @setting(63, "RF_WriteReg8")
    def RF_WriteReg8(self, c, args):
        return self.rft.command.RF_WriteReg8(*args)

    @setting(64, "MultiBand")
    def MultiBand(self, c, args):
        return self.rft.command.MultiBand(*args)

    @setting(65, "GetConnectedData")
    def GetConnectedData(self, c, args):
        return self.rft.command.GetConnectedData(*args)

    @setting(66, "GetInvSincFIR")
    def GetInvSincFIR(self, c, args):
        return self.rft.command.GetInvSincFIR(*args)

    @setting(67, "SetInvSincFIR")
    def SetInvSincFIR(self, c, args):
        return self.rft.command.SetInvSincFIR(*args)

    @setting(68, "IntrClr")
    def IntrClr(self, c, args):
        return self.rft.command.IntrClr(*args)

    @setting(69, "GetIntrStatus")
    def GetIntrStatus(self, c, args):
        return self.rft.command.GetIntrStatus(*args)

    @setting(70, "TermMode")
    def TermMode(self, c, arg):
        return self.rft.command.TermMode(arg)

    @setting(71, "GetExtPllFreqList")
    def GetExtPllFreqList(self, c, args):
        return self.rft.command.GetExtPllFreqList(*args)

    @setting(72, "GetExtPllConfig")
    def GetExtPllConfig(self, c, args):
        return self.rft.command.GetExtPllConfig(*args)

    @setting(73, "SetCalFreeze")
    def SetCalFreeze(self, c, args):
        return self.rft.command.SetCalFreeze(*args)

    @setting(74, "GetCalFreeze")
    def GetCalFreeze(self, c, args):
        return self.rft.command.GetCalFreeze(*args)

    @setting(75, "SetBitstream")
    def SetBitstream(self, c, arg):
        return self.rft.command.SetBitstream(arg)

    @setting(76, "GetBitstream")
    def GetBitstream(self, c):
        return self.rft.command.GetBitstream()

    @setting(77, "GetBitstreamStatus")
    def GetBitstreamStatus(self, c):
        return self.rft.command.GetBitstreamStatus()

    @setting(78, "GetDither")
    def GetDither(self, c, args):
        return self.rft.command.GetDither(*args)

    @setting(79, "SetDither")
    def SetDither(self, c, args):
        return self.rft.command.SetDither(*args)

    @setting(80, "GetFabClkOutDiv")
    def GetFabClkOutDiv(self, c, args):
        return self.rft.command.GetFabClkOutDiv(*args)

    @setting(81, "SetTriggerLatency")
    def SetTriggerLatency(self, c, args):
        return self.rft.command.SetTriggerLatency(*args)

    @setting(82, "SetTriggerInfo")
    def SetTriggerInfo(self, c, args):
        return self.rft.command.SetTriggerInfo(*args)

    @setting(83, "SetTriggerCycle")
    def SetTriggerCycle(self, c, args):
        return self.rft.command.SetTriggerCycle(*args)

    @setting(84, "StartTrigger")
    def StartTrigger(self, c):
        return self.rft.command.StartTrigger()

    @setting(85, "GetTriggerStatus")
    def GetTriggerStatus(self, c):
        return self.rft.command.GetTriggerStatus()

    @setting(86, "SetAccumulateMode")
    def SetAccumulateMode(self, c, arg):
        return self.rft.command.SetAccumulateMode(arg)

    @setting(87, "GetAccumulateOverrange")
    def GetAccumulateOverrange(self, c):
        return self.rft.command.GetAccumulateOverrange()

    @setting(88, "SetMACConfig")
    def SetMACConfig(self, c, args):
        return self.rft.command.SetMACConfig(*args)

    @setting(89, "ClearBRAM")
    def ClearBRAM(self, c):
        return self.rft.command.ClearBRAM()

    @setting(100, "WriteDataToMemory_setsize")
    def WriteDataToMemory_setsize(self, c, size):
        self.wr_size = size
        self.wr_pos = 0
        return

    @setting(101, "WriteDataToMemory_setdata")
    def WriteDataToMemory_setdata(self, c, data):
        len_data = len(data)
        self.buf_mem[self.wr_pos:self.wr_pos+len_data] = data
        self.wr_pos += len_data
        return

    @setting(102, "WriteDataToMemory_exec")
    def WriteDataToMemory_exec(self, c, type, ch):
        return self.rft.if_data.WriteDataToMemory(
            type, ch, self.wr_size, bytes(self.buf_mem[0:self.wr_size]))

    @setting(110, "ReadDataFromMemory_setsize")
    def ReadDataFromMemory_setsize(self, c, size):
        self.rd_size = size
        self.rd_pos = 0
        return

    @setting(111, "ReadDataFromMemory_getdata")
    def ReadDataFromMemory_getdata(self, c, len):
        data = bytes(self.buf_mem[self.rd_pos:self.rd_pos+len])
        self.rd_pos += len
        return data

    @setting(112, "ReadDataFromMemory_exec")
    def ReadDataFromMemory_exec(self, c, type, ch):
        self.buf_mem[0:self.rd_size] = self.rft.if_data.ReadDataFromMemory(
            type, ch, self.rd_size)
        return

__server__ = RftoolClientWrappedServer()

if __name__ == "__main__":
    from labrad import util
    util.runServer(__server__)
