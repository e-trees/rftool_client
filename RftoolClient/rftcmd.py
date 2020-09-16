#!/usr/bin/env python3
# coding: utf-8

from RftoolClient import cmdutil
import logging

"""
rftcmd.py
    - RFTOOL commands
"""


class RftoolCommand(object):
    """Class wrapping rftool commands"""

    def __init__(self, interface, logger=None):
        self._logger = logging.getLogger(__name__)
        self._logger.addHandler(logging.NullHandler())
        self._logger = logger or self._logger

        self.rft_if = interface
        self.cmd = ""
        self.res = ""
        self._joinargs = cmdutil.CmdUtil.joinargs
        self._splitargs = cmdutil.CmdUtil.splitargs

        self._logger.debug("RftoolCommand __init__")
        return

    def SetMixerSettings(
        self, type, tile_id, block_id, freq, phase_offset,
        event_source, mixer_type, coarse_mix_freq,
        mixer_mode, fine_mixer_scale
    ):
        """Set mixer settings of ADC/DAC.

        Parameters
        ----------
        type : int
            Type (ADC=0, DAC=1)
        tile_id : int
            ADC/DAC Tile ID number
        block_id : int
            ADC/DAC Block ID number
        freq : float
            NCO frequency of mixer
        phase_offset : float
            NCO phase offset of mixer
        event_source : int
            Event source
            (IMMEDIATE=0, SLICE=1, TILE=2, SYSREF=3, MARKER=4, PL=5)
        mixer_type : int
            Mixer type (COARSE=1, FINE=2, OFF=3)
        coarse_mixer_freq : int
            Coarse mixer frequency
            (OFF=0, SAMPLE_FREQ_BY_TWO=2, SAMPLE_FREQ_BY_FOUR=4,
            MIN_SAMPLE_FREQ_BY_FOUR=8, BYPASS=16)
        mixer_mode : int
            Mixer mode (OFF=0, C2C=1, C2R=2, R2C=3, R2R=4)
        fine_mixer_scale : int
            Fine mixer scale (AUTO=0, 1P0=1, 0P7=2)
        """
        self.cmd = self._joinargs("SetMixerSettings", [
            type, tile_id, block_id, freq, phase_offset,
            event_source, mixer_type, coarse_mix_freq,
            mixer_mode, fine_mixer_scale
        ])
        self.res = self.rft_if.put(self.cmd)
        return

    def GetMixerSettings(self, type, tile_id, block_id):
        """Get mixer settings of ADC/DAC.

        Parameters
        ----------
        type : int
            specify type (ADC=0, DAC=1)
        tile_id : int
            ADC/DAC Tile ID number
        block_id : int
            ADC/DAC Block ID number

        Returns
        -------
        type : int
            Type (ADC=0, DAC=1)
        tile_id : int
            ADC/DAC Tile ID number
        block_id : int
            ADC/DAC Block ID number
        freq : float
            NCO frequency of mixer
        phase_offset : float
            NCO phase offset of mixer
        event_source : int
            Event source
            (IMMEDIATE=0, SLICE=1, TILE=2, SYSREF=3, MARKER=4, PL=5)
        mixer_type : int
            Mixer type (COARSE=1, FINE=2, OFF=3)
        coarse_mixer_freq : int
            Coarse mixer frequency
            (OFF=0, SAMPLE_FREQ_BY_TWO=2, SAMPLE_FREQ_BY_FOUR=4,
            MIN_SAMPLE_FREQ_BY_FOUR=8, BYPASS=16)
        mixer_mode : int
            Mixer mode (OFF=0, C2C=1, C2R=2, R2C=3, R2R=4)
        fine_mixer_scale : int
            Fine mixer scale (AUTO=0, 1P0=1, 0P7=2)
        """
        self.cmd = self._joinargs(
            "GetMixerSettings", [type, tile_id, block_id])
        self.res = self.rft_if.put(self.cmd)

        [type, tile_id, block_id, freq, phase_offset,
            event_source, mixer_type, coarse_mixer_freq,
            mixer_mode, fine_mixer_scale] = self._splitargs(self.res)

        return type, tile_id, block_id, freq, phase_offset, \
            event_source, mixer_type, coarse_mixer_freq, \
            mixer_mode, fine_mixer_scale

    def GetQMCSettings(self, type, tile_id, block_id):
        """Get QMC Gain, Phase, Offset settings of ADC/DAC.
           **has not been used yet.**
        Parameters
        ----------
        type : int
            Type (ADC=0, DAC=1)
        tile_id : int
            ADC/DAC Tile ID number
        block_id : int
            ADC/DAC Block ID number

        Returns
        -------
        type : int
            Type (ADC=0, DAC=1)
        tile_id : int
            ADC/DAC Tile ID number
        block_id : int
            ADC/DAC Block ID number
        gain_correction_factor : float
            Gain correction factor
        phase_correction_factor : float
            Phase correction factor
        enable_phase : int
            Enable phase (enable=1, disable=0)
        enable_gain : int
            Enable gain (enable=1, disable=0)
        offset_correction_factor : int
            Offset correction factor
        event_source : int
            Event source
            (IMMEDIATE=0, SLICE=1, TILE=2, SYSREF=3, MARKER=4, PL=5)
        """
        self.cmd = self._joinargs("GetQMCSettings", [type, tile_id, block_id])
        self.res = self.rft_if.put(self.cmd)

        [type, tile_id, block_id, gain_correction_factor,
            phase_correction_factor, enable_phase, enable_gain,
            offset_correction_factor, event_source] = self._splitargs(self.res)

        return type, tile_id, block_id, gain_correction_factor, \
            phase_correction_factor, enable_phase, enable_gain, \
            offset_correction_factor, event_source

    def SetExtParentclk(self, board_id, freq):
        """Set parent clock (LMK04208) settings.
           **has not been used yet.**

        Parameters
        ----------
        board_id : int
            Board ID (ZCU111=0, ZC1254=1, ZC1275=2)
        freq : int
            LMK04208 frequency
            (12M8_3072M_122M88_REVA=0, 12M8_3072M_122M88_REVAB=1,
            12M8_3072M_122M88_REVB=2)

        Returns
        -------
        board_id : int
            Board ID (ZCU111=0, ZC1254=1, ZC1275=2)
        freq : int
            LMK04208 frequency
            (12M8_3072M_122M88_REVA=0, 12M8_3072M_122M88_REVAB=1,
            12M8_3072M_122M88_REVB=2)
        """
        self.cmd = self._joinargs("SetExtParentclk", [board_id, freq])
        self.res = self.rft_if.put(self.cmd)

        [board_id, freq] = self._splitargs(self.res)

        return board_id, freq

    def iic_write(self, iic_inst, slave_addr, reg_offset, size, data):
        """Write data to I2C slave (LMX2594/LMK04208) for clock settings.
           **has not been used yet.**

        Parameters
        ----------
        iic_inst : int
        slave_addr : int
        reg_offset : int
        size : int
        data : int
        """
        self.cmd = self._joinargs(
            "iic_write", [iic_inst, slave_addr, reg_offset, size, data])
        self.res = self.rft_if.put(self.cmd)
        return

    def iic_read(self, iic_inst, slave_addr, size):
        """Read data from I2C slave (LMX2594/LMK04208) for clock settings.
           **has not been used yet.**

        This command is NOT IMPLEMENTED YET on rftool (2019.1 ZCU111 TRD).
        """
        self.cmd = self._joinargs("iic_read", [iic_inst, slave_addr, size])
        self.res = self.rft_if.put(self.cmd)
        return

    def SetExtPllClkRate(self, board_id, pll_src, freq):
        """Set external PLL clock (LMX2594) frequency.

        Parameters
        ----------
        board_id : int
            Board ID (ZCU111=0, ZC1254=1, ZC1275=2)
        pll_src : int
            PLL Source (PLL_A=0x8, PLL_B=0x4, PLL_C=0x1)
        freq : int
            PLL frequency - this value corresponds to the index of the list
            obtained by GetExtPllFreqList command

        Returns
        -------
        board_id : int
            Board ID (ZCU111=0, ZC1254=1, ZC1275=2)
        pll_src : int
            PLL Source (PLL_A=0x8, PLL_B=0x4, PLL_C=0x1)
        freq : int
            PLL frequency - this value corresponds to the index of the list
            obtained by GetExtPllFreqList command

        """
        self.cmd = self._joinargs(
            "SetExtPllClkRate", [board_id, pll_src, freq])
        self.res = self.rft_if.put(self.cmd)

        [board_id, pll_src, freq] = self._splitargs(self.res)

        return board_id, pll_src, freq

    def SetDACPowerMode(self, board_id, tile_id, block_id, output_current):
        """Set DAC output current.
           **has not been used yet.**

        Parameters
        ----------
        board_id : int
            Board ID (ZCU111=0, ZC1254=1, ZC1275=2)
        tile_id : int
            DAC Tile ID number
        block_id : int
            DAC Block ID number
        output_current :
            DAC Output current (current_20mA=0, curent_32mA=1)

        Returns
        -------
        board_id : int
            Board ID (ZCU111=0, ZC1254=1, ZC1275=2)
        tile_id : int
            DAC Tile ID number
        block_id : int
            DAC Block ID number
        output_current :
            DAC Output current (current_20mA=0, curent_32mA=1)
            - Note: The constants is different from output_curr argument of
              GetOutputCurr command.
        """
        self.cmd = self._joinargs(
            "SetDACPowerMode", [board_id, tile_id, block_id, output_current])
        self.res = self.rft_if.put(self.cmd)

        [board_id, tile_id, block_id,
            output_current] = self._splitargs(self.res)

        return board_id, tile_id, block_id, output_current

    def GetDACPower(self, board_id, tile_id):
        """Get power values from driver.
           **has not been used yet.**

        Parameters
        ----------
        board_id : int
            Board ID (ZCU111=0, ZC1254=1, ZC1275=2)
        tile_id : int
            DAC Tile ID number

        Returns
        -------
        board_id : int
            Board ID (ZCU111=0, ZC1254=1, ZC1275=2)
        tile_id : int
            DAC Tile ID number
        dac_avtt : int
        dac_avcc_aux : int
        dac_avcc : int
        adc_avcc_aux : int
        adc_avcc : int
        """
        self.cmd = self._joinargs("GetDACPower", [board_id, tile_id])
        self.res = self.rft_if.put(self.cmd)

        [board_id, tile_id, dac_avtt, dac_avcc_aux, dac_avcc,
            adc_avcc_aux, adc_avcc] = self._splitargs(self.res)

        return board_id, tile_id, dac_avtt, dac_avcc_aux, dac_avcc, \
            adc_avcc_aux, adc_avcc

    def StartUp(self, type, tile_id):
        """Restart the requested ADC/DAC tile.

        This command does not clear the existing register values.

        Parameters
        ----------
        type : int
            Type (ADC=0, DAC=1)
        tile_id : int
            ADC/DAC Tile ID number
        """
        self.cmd = self._joinargs("StartUp", [type, tile_id])
        self.res = self.rft_if.put(self.cmd)
        return

    def Shutdown(self, type, tile_id):
        """Shutdown the requested ADC/DAC tile.

        This command does not clear the existing register values.

        Parameters
        ----------
        type : int
            Type (ADC=0, DAC=1)
        tile_id : int
            ADC/DAC Tile ID number
        """
        self.cmd = self._joinargs("Shutdown", [type, tile_id])
        self.res = self.rft_if.put(self.cmd)
        return

    def RfdcVersion(self):
        """Get Xilinx RFDC Version

        Returns
        -------
        version : string
            RFDC version
        """
        self.cmd = "RfdcVersion"
        self.res = self.rft_if.put(self.cmd)
        version = self.res.split(" ")[1]
        return version

    def Version(self):
        """Get Rftool Version

        Returns
        -------
        version : string
            Rftool version
        """
        self.cmd = "Version"
        self.res = self.rft_if.put(self.cmd)
        version = self.res.split(" ")[1]
        return version

    def JtagIdcode(self):
        """Get JTAG ID code
           **has not been used yet.**

        Returns
        -------
        idcode : int
            JTAG ID code
        """
        self.cmd = "JtagIdcode"
        self.res = self.rft_if.put(self.cmd)
        [idcode] = self._splitargs(self.res)
        return idcode

    def GetIPStatus(self):
        """Get status of ADC/DAC IP like block status, tile status,
        power up state and PLL state.

        Returns
        -------
        status : dict
            Return the nested dict of ADC/DAC tile status
            - dict:{"adc", "dac"} ... specify the key corresponding ADC/DAC
            - list ... specify the index corresponding Tile ID (0 to 3)
            - dict:{
                "is_enabled",
                "block_status_mask",
                "tile_state",
                "power_up_state",
                "pll_state"
              } ... specify the key corresponding item

        Example
        -------
        ip_status = rft.command.GetIPStatus()
        print(ip_status)  # print all status
        print(ip_status["adc"][0]["pll_state"])  # get ADC Tile 0 PLLState
        """
        self.cmd = "GetIPStatus"
        self.res = self.rft_if.put(self.cmd)
        returns = self._splitargs(self.res)
        index = 0
        status = {}
        items = ["is_enabled", "block_status_mask", "tile_state",
                 "power_up_state", "pll_state"]

        for type in ["dac", "adc"]:
            status[type] = []
            for tile_id in [0, 1, 2, 3]:
                status[type].append({})
                for item in items:
                    status[type][-1][item] = returns[index]
                    index = index + 1

        return status

    def Reset(self, type, tile_id):
        """Reset the requested ADC/DAC tile.

        This command initializes all existing register values.

        Parameters
        ----------
        type : int
            Type (ADC=0, DAC=1)
        tile_id : int
            ADC/DAC Tile ID number
        """
        self.cmd = self._joinargs("Reset", [type, tile_id])
        self.res = self.rft_if.put(self.cmd)
        return

    def GetPLLConfig(self, type, tile_id):
        """Get PLL configuration of ADC/DAC.

        Parameters
        ----------
        type : int
            Type (ADC=0, DAC=1)
        tile_id : int
            ADC/DAC Tile ID number

        Returns
        -------
        type : int
            Type (ADC=0, DAC=1)
        tile_id : int
            ADC/DAC Tile ID number
        enabled : int
            PLL enabled (enabled=1, disabled=0)
        ref_clk_freq : float
            Reference clock frequency [MHz]
        sample_rate : float
            Sample Rate [MHz]
        ref_clk_divider : int
            Refence clock divider
        feedback_divider : int
            Feedback divider
        output_divider : int
            Output divider
        """
        self.cmd = self._joinargs("GetPLLConfig", [type, tile_id])
        self.res = self.rft_if.put(self.cmd)

        [type, tile_id, enabled, ref_clk_freq, sample_rate, ref_clk_divider,
            feedback_divider, output_divider] = self._splitargs(self.res)

        return type, tile_id, enabled, ref_clk_freq, sample_rate, \
            ref_clk_divider, feedback_divider, output_divider

    def GetLinkCoupling(self, tile_id, block_id):
        """Get ADC Link Coupling mode.
           **has not been used yet.**

        Parameters
        ----------
        tile_id : int
            ADC Tile ID number
        block_id : int
            ADC Block ID number

        Returns
        -------
        tile_id : int
            ADC Tile ID number
        block_id : int
            ADC Block ID number
        mode : int
            Link Coupling mode (DC=0, AC=1)
        """
        self.cmd = self._joinargs("GetLinkCoupling", [tile_id, block_id])
        self.res = self.rft_if.put(self.cmd)

        [tile_id, block_id, mode] = self._splitargs(self.res)

        return block_id, mode

    def SetQMCSettings(
        self, type, tile_id, block_id, enable_phase, enable_gain,
        gain_correction_factor, phase_correction_factor,
        offset_correction_factor, event_source
    ):
        """Set QMC Gain, Phase, Offset settings of ADC/DAC.
           **has not been used yet.**

        Parameters
        ----------
        type : int
            Type (ADC=0, DAC=1)
        tile_id : int
            ADC/DAC Tile ID number
        block_id : int
            ADC/DAC Block ID number
        gain_correction_factor : float
            Gain correction factor
        phase_correction_factor : float
            Phase correction factor
        enable_phase : int
            Enable phase (enable=1, disable=0)
        enable_gain : int
            Enable gain (enable=1, disable=0)
        offset_correction_factor : int
            Offset correction factor
        event_source : int
            Event source
            (IMMEDIATE=0, SLICE=1, TILE=2, SYSREF=3, MARKER=4, PL=5)
        """
        self.cmd = self._joinargs("SetQMCSettings", [
            type, tile_id, block_id, enable_phase, enable_gain,
            gain_correction_factor, phase_correction_factor,
            offset_correction_factor, event_source
        ])
        self.res = self.rft_if.put(self.cmd)
        return

    def GetCoarseDelaySettings(self, type, tile_id, block_id):
        """Get coarse delay settings of ADC/DAC.
           **has not been used yet.**

        Parameters
        ----------
        type : int
            Type (ADC=0, DAC=1)
        tile_id : int
            ADC/DAC Tile ID number
        block_id : int
            ADC/DAC Block ID number

        Returns
        -------
        type : int
            Type (ADC=0, DAC=1)
        tile_id : int
            ADC/DAC Tile ID number
        block_id : int
            ADC/DAC Block ID number
        coarse_delay : int
            Coarse delay
        event_source : int
            Event source
            (IMMEDIATE=0, SLICE=1, TILE=2, SYSREF=3, MARKER=4, PL=5)
        """
        self.cmd = self._joinargs("GetCoarseDelaySettings", [
            type, tile_id, block_id])
        self.res = self.rft_if.put(self.cmd)

        [type, tile_id, block_id, coarse_delay,
            event_source] = self._splitargs(self.res)

        return type, tile_id, block_id, coarse_delay, event_source

    def SetCoarseDelaySettings(
        self, type, tile_id, block_id, coarse_delay, event_source
    ):
        """Set coarse delay settings of ADC/DAC.
           **has not been used yet.**

        This command may not work properly due to a bug in rftool (2019.1 ZCU111 TRD).
        Please refer to rftool source code (rfdc_functions_w.c:477) for details.

        Parameters
        ----------
        type : int
            Type (ADC=0, DAC=1)
        tile_id : int
            ADC/DAC Tile ID number
        block_id : int
            ADC/DAC Block ID number
        coarse_delay : int
            Coarse delay
        event_source : int
            Event source
            (IMMEDIATE=0, SLICE=1, TILE=2, SYSREF=3, MARKER=4, PL=5)
        """
        self.cmd = self._joinargs("SetCoarseDelaySettings", [
            type, tile_id, block_id, coarse_delay, event_source])
        self.res = self.rft_if.put(self.cmd)
        return

    def GetInterpolationFactor(self, tile_id, block_id):
        """Get DAC Interpolation factor.

        Parameters
        ----------
        tile_id : int
            DAC Tile ID number
        block_id : int
            DAC Block ID number

        Returns
        -------
        tile_id : int
            DAC Tile ID number
        block_id : int
            DAC Block ID number
        interpolation_factor : int
            DAC Interpolation factor
        """
        self.cmd = self._joinargs(
            "GetInterpolationFactor", [tile_id, block_id])
        self.res = self.rft_if.put(self.cmd)

        [tile_id, block_id, interpolation_factor] = self._splitargs(self.res)

        return tile_id, block_id, interpolation_factor

    def SetInterpolationFactor(self, tile_id, block_id, interpolation_factor):
        """Set DAC Interpolation factor.

        Parameters
        ----------
        tile_id : int
            DAC Tile ID number
        block_id : int
            DAC Block ID number
        interpolation_factor : int
            DAC Interpolation factor
        """
        self.cmd = self._joinargs("SetInterpolationFactor", [
            tile_id, block_id, interpolation_factor])
        self.res = self.rft_if.put(self.cmd)
        return

    def GetDecimationFactor(self, tile_id, block_id):
        """Get ADC Decimation factor.

        Parameters
        ----------
        tile_id : int
            ADC Tile ID number
        block_id : int
            ADC Block ID number

        Returns
        -------
        tile_id : int
            ADC Tile ID number
        block_id : int
            ADC Block ID number
        decimation_factor : int
            ADC Interpolation factor
        """
        self.cmd = self._joinargs("GetDecimationFactor", [tile_id, block_id])
        self.res = self.rft_if.put(self.cmd)

        [tile_id, block_id, decimation_factor] = self._splitargs(self.res)

        return tile_id, block_id, decimation_factor

    def SetDecimationFactor(self, tile_id, block_id, decimation_factor):
        """Set ADC Decimation factor.

        Parameters
        ----------
        tile_id : int
            ADC Tile ID number
        block_id : int
            ADC Block ID number
        decimation_factor : int
            ADC Interpolation factor
        """
        self.cmd = self._joinargs("SetDecimationFactor", [
            tile_id, block_id, decimation_factor])
        self.res = self.rft_if.put(self.cmd)
        return

    def GetNyquistZone(self, type, tile_id, block_id):
        """Get Nyquist factor of ADC/DAC.
           **has not been used yet.**

        Parameters
        ----------
        type : int
            Type (ADC=0, DAC=1)
        tile_id : int
            ADC/DAC Tile ID number
        block_id : int
            ADC/DAC Block ID number

        Returns
        -------
        type : int
            Type (ADC=0, DAC=1)
        tile_id : int
            ADC/DAC Tile ID number
        block_id : int
            ADC/DAC Block ID number
        nyquist_zone : int
            Nyquist factor (Odd=1, Even=2)
        """
        self.cmd = self._joinargs("GetNyquistZone", [type, tile_id, block_id])
        self.res = self.rft_if.put(self.cmd)

        [type, tile_id, block_id, nyquist_zone] = self._splitargs(self.res)

        return type, tile_id, block_id, nyquist_zone

    def SetNyquistZone(self, type, tile_id, block_id, nyquist_zone):
        """Set Nyquist factor of ADC/DAC.
           **has not been used yet.**

        Parameters
        ----------
        type : int
            Type (ADC=0, DAC=1)
        tile_id : int
            ADC/DAC Tile ID number
        block_id : int
            ADC/DAC Block ID number
        nyquist_zone : int
            Nyquist factor (Odd=1, Even=2)
        """
        self.cmd = self._joinargs("SetNyquistZone", [
            type, tile_id, block_id, nyquist_zone])
        self.res = self.rft_if.put(self.cmd)
        return

    def GetOutputCurr(self, tile_id, block_id):
        """Get DAC Output current.
           **has not been used yet.**

        Parameters
        ----------
        tile_id : int
            DAC Tile ID number
        block_id : int
            DAC Block ID number

        Returns
        -------
        tile_id : int
            DAC Tile ID number
        block_id : int
            DAC Block ID number
        output_curr : int
            DAC Output current (current_20mA=20, curent_32mA=32)
            - Note: The constants is different from output_current argument of
              SetDACPowerMode command.
        """
        self.cmd = self._joinargs("GetOutputCurr", [tile_id, block_id])
        self.res = self.rft_if.put(self.cmd)

        [tile_id, block_id, output_curr] = self._splitargs(self.res)

        return tile_id, block_id, output_curr

    def GetPLLLockStatus(self, type, tile_id):
        """Get PLL Lock status of ADC/DAC.

        Parameters
        ----------
        type : int
            Type (ADC=0, DAC=1)
        tile_id : int
            ADC/DAC Tile ID number

        Returns
        -------
        type : int
            Type (ADC=0, DAC=1)
        tile_id : int
            ADC/DAC Tile ID number
        lock_status : int
            PLL Lock status (UNLOCKED=1, LOCKED=2)
        """
        self.cmd = self._joinargs("GetPLLLockStatus", [type, tile_id])
        self.res = self.rft_if.put(self.cmd)

        [type, tile_id, lock_status] = self._splitargs(self.res)

        return type, tile_id, lock_status

    def GetClockSource(self, type, tile_id):
        """Get Clock source of ADC/DAC.
           **has not been used yet.**

        Parameters
        ----------
        type : int
            Type (ADC=0, DAC=1)
        tile_id : int
            ADC/DAC Tile ID number

        Returns
        -------
        type : int
            Type (ADC=0, DAC=1)
        tile_id : int
            ADC/DAC Tile ID number
        clock_source : int
            Clock source
        """
        self.cmd = self._joinargs("GetClockSource", [type, tile_id])
        self.res = self.rft_if.put(self.cmd)

        [type, tile_id, clock_source] = self._splitargs(self.res)

        return type, tile_id, clock_source

    def DynamicPLLConfig(
        self, type, tile_id, source, ref_clk_freq, sampling_rate
    ):
        """Dynamically set the internal PLL from the specified sampling rate
        and the external PLL reference clock frequency.

        Parameters
        ----------
        type : int
            Type (ADC=0, DAC=1)
        tile_id : int
            ADC/DAC Tile ID number
        source : int
            Clock source (EXTERNAL_CLK=0, INTERNAL_PLL_CLK=1)
        ref_clk_freq : float
            PLL Reference clock frequency [MHz]
        sampling_rate : float
            Sampling rate [MHz]

        Returns
        -------
        ref_clk_divider : int
            Refence clock divider
        feedback_divider : int
            Feedback divider
        output_divider : int
            Output divider
        """
        self.cmd = self._joinargs("DynamicPLLConfig", [
            type, tile_id, source, ref_clk_freq, sampling_rate])
        self.res = self.rft_if.put(self.cmd)

        [ref_clk_divider, feedback_divider,
            output_divider] = self._splitargs(self.res)

        return ref_clk_divider, feedback_divider, output_divider

    def SetFabClkOutDiv(self, type, tile_id, fab_clk_div):
        """Set Fablic clock divider of ADC/DAC.

        Parameters
        ----------
        type : int
            Type (ADC=0, DAC=1)
        tile_id : int
            ADC/DAC Tile ID number
        fab_clk_div : int
            Fablic clock divider (1 to 16)
        """
        self.cmd = self._joinargs(
            "SetFabClkOutDiv", [type, tile_id, fab_clk_div])
        self.res = self.rft_if.put(self.cmd)
        return

    def SetupFIFO(self, type, tile_id, enable):
        """Enable and Disable the ADC/DAC FIFO.

        Parameters
        ----------
        type : int
            Type (ADC=0, DAC=1)
        tile_id : int
            ADC/DAC Tile ID number
        enable : int
            FIFO Enable/Disable (enable=1, disable=0)
        """
        self.cmd = self._joinargs("SetupFIFO", [type, tile_id, enable])
        self.res = self.rft_if.put(self.cmd)

    def GetFIFOStatus(self, type, tile_id):
        """Get FIFO status of ADC/DAC.

        Parameters
        ----------
        type : int
            Type (ADC=0, DAC=1)
        tile_id : int
            ADC/DAC Tile ID number

        Returns
        -------
        type : int
            Type (ADC=0, DAC=1)
        tile_id : int
            ADC/DAC Tile ID number
        enable : int
            FIFO Enable/Disable (enable=1, disable=0)
        """
        self.cmd = self._joinargs("GetFIFOStatus", [type, tile_id])
        self.res = self.rft_if.put(self.cmd)

        [type, tile_id, enable] = self._splitargs(self.res)

        return type, tile_id, enable

    def SetFabWrVldWords(self, tile_id, block_id, fabric_data_rate):
        """Set Fabric write valid dWords of DAC.
           Configration parameters in DAC. In case it is not right vlaue, interrupt occurs.
        
        Parameters
        ----------
        tile_id : int
            DAC Tile ID number
        block_id : int
            DAC Block ID number
        fabric_data_rate : int
            Number of valid write words
        """
        self.cmd = self._joinargs("SetFabWrVldWords", [
            tile_id, block_id, fabric_data_rate])
        self.res = self.rft_if.put(self.cmd)
        return

    def GetFabWrVldWords(self, type, tile_id, block_id):
        """Get Fabric write valid dWords of ADC/DAC.

        Parameters
        ----------
        type : int
            Type (ADC=0, DAC=1)
        tile_id : int
            ADC/DAC Tile ID number
        block_id : int
            ADC/DAC Block ID number

        Returns
        -------
        type : int
            Type (ADC=0, DAC=1)
        tile_id : int
            ADC/DAC Tile ID number
        block_id : int
            ADC/DAC Block ID number
        fabric_data_rate : int
            Number of valid write words
        """
        self.cmd = self._joinargs(
            "GetFabWrVldWords", [type, tile_id, block_id])
        self.res = self.rft_if.put(self.cmd)

        [type, tile_id, block_id, fabric_data_rate] = self._splitargs(self.res)

        return type, tile_id, block_id, fabric_data_rate

    def SetFabRdVldWords(self, tile_id, block_id, fabric_data_rate):
        """Set Fabric read valid dWords of ADC.
           Configration parameters in ADC. In case it is not right vlaue, interrupt occurs.

        Parameters
        ----------
        tile_id : int
            ADC Tile ID number
        block_id : int
            ADC Block ID number
        fabric_data_rate : int
            Number of valid read words
        """
        self.cmd = self._joinargs("SetFabRdVldWords", [
            tile_id, block_id, fabric_data_rate])
        self.res = self.rft_if.put(self.cmd)
        return

    def GetFabRdVldWords(self, type, tile_id, block_id):
        """Get Fabric read valid dWords of ADC/DAC.

        Parameters
        ----------
        type : int
            Type (ADC=0, DAC=1)
        tile_id : int
            ADC/DAC Tile ID number
        block_id : int
            ADC/DAC Block ID number

        Returns
        -------
        type : int
            Type (ADC=0, DAC=1)
        tile_id : int
            ADC/DAC Tile ID number
        block_id : int
            ADC/DAC Block ID number
        fabric_data_rate : int
            Number of valid read words
        """
        self.cmd = self._joinargs(
            "GetFabRdVldWords", [type, tile_id, block_id])
        self.res = self.rft_if.put(self.cmd)

        [type, tile_id, block_id, fabric_data_rate] = self._splitargs(self.res)

        return type, tile_id, block_id, fabric_data_rate

    def SetDecoderMode(self, tile_id, block_id, decoder_mode):
        """Set DAC Decode mode.
           **has not been used yet.**

        Parameters
        ----------
        tile_id : int
            DAC Tile ID number
        block_id : int
            DAC Block ID number
        decoder_mode : int
            DAC Decoder mode (MAX_SNR_MODE=1, MAX_LINEARITY_MODE=2)
        """
        self.cmd = self._joinargs("SetDecoderMode", [
            tile_id, block_id, decoder_mode])
        self.res = self.rft_if.put(self.cmd)
        return

    def GetDecoderMode(self, tile_id, block_id):
        """Get DAC Decode mode.
           **has not been used yet.**

        Parameters
        ----------
        tile_id : int
            DAC Tile ID number
        block_id : int
            DAC Block ID number

        Returns
        ----------
        tile_id : int
            DAC Tile ID number
        block_id : int
            DAC Block ID number
        decoder_mode : int
            DAC Decoder mode (MAX_SNR_MODE=1, MAX_LINEARITY_MODE=2)
        """
        self.cmd = self._joinargs("GetDecoderMode", [tile_id, block_id])
        self.res = self.rft_if.put(self.cmd)

        [tile_id, block_id, decoder_mode] = self._splitargs(self.res)

        return tile_id, block_id, decoder_mode

    def ResetNCOPhase(self, type, tile_id, block_id):
        """Reset NCO phase of ADC/DAC.
           Reset before changing from I/Q mode to Real mode
         
        Parameters
        ----------
        type : int
            Type (ADC=0, DAC=1)
        tile_id : int
            ADC/DAC Tile ID number
        block_id : int
            ADC/DAC Block ID number
        """
        self.cmd = self._joinargs("ResetNCOPhase", [type, tile_id, block_id])
        self.res = self.rft_if.put(self.cmd)
        return

    def DumpRegs(self, type, tile_id):
        """Dump ADC/DAC register values.
           **has not been used yet.**

        This command prints the register offsets and values ​​to standard output
        of ZCU111.

        Parameters
        ----------
        type : int
            Type (ADC=0, DAC=1)
        tile_id : int
            ADC/DAC Tile ID number
        """
        self.cmd = self._joinargs("DumpRegs", [type, tile_id])
        self.res = self.rft_if.put(self.cmd)
        return

    def UpdateEvent(self, type, tile_id, block_id, event):
        """Trigger the update event for ADC/DAC.
           This function is always after configuring I/Q mixer parameters.

        Parameters
        ----------
        type : int
            Type (ADC=0, DAC=1)
        tile_id : int
            ADC/DAC Tile ID number
        block_id : int
            ADC/DAC Block ID number
        event : int
            Event to trigger (MIXER=1, CRSE_DLY=2, QMC=4)
        """
        self.cmd = self._joinargs(
            "UpdateEvent", [type, tile_id, block_id, event])
        self.res = self.rft_if.put(self.cmd)
        return

    def GetCalibrationMode(self, tile_id, block_id):
        """Get ADC Calibration mode.
           **has not been used yet.**

        Parameters
        ----------
        tile_id : int
            ADC Tile ID number
        block_id : int
            ADC Block ID number

        Returns
        -------
        tile_id : int
            ADC Tile ID number
        block_id : int
            ADC Block ID number
        calibration_mode : int
            ADC Calibration mode (MODE1=1, MODE2=2)
        """
        self.cmd = self._joinargs("GetCalibrationMode", [tile_id, block_id])
        self.res = self.rft_if.put(self.cmd)

        [tile_id, block_id, calibration_mode] = self._splitargs(self.res)

        return tile_id, block_id, calibration_mode

    def SetCalibrationMode(self, tile_id, block_id, calibration_mode):
        """Set ADC Calibration mode.
           **has not been used yet.**

        Parameters
        ----------
        tile_id : int
            ADC Tile ID number
        block_id : int
            ADC Block ID number
        calibration_mode : int
            ADC Calibration mode (MODE1=1, MODE2=2)
        """
        self.cmd = self._joinargs("SetCalibrationMode", [
            tile_id, block_id, calibration_mode])
        self.res = self.rft_if.put(self.cmd)
        return

    def GetBlockStatus(self, type, tile_id, block_id):
        """Get Data converter block status of ADC/DAC.

        Parameters
        ----------
        type : int
            Type (ADC=0, DAC=1)
        tile_id : int
            ADC/DAC Tile ID number
        block_id : int
            ADC/DAC Block ID number

        Returns
        -------
        type : int
            Type (ADC=0, DAC=1)
        tile_id : int
            ADC/DAC Tile ID number
        block_id : int
            ADC/DAC Block ID number
        sampling_freq : float
            Sampling rate [MHz]
        analog_data_path_status : int
            in ADC
                   0 bit : Block enabled (enable=1, disable=0)
                   Note: may change in next release (see comment xrfdc.c:1034)
            in DAC
                 1-0 bit : Inverse-Sync filter mode
                    (disable=0, 1st nyquist zone=1, 2nd nyquist zone=2)
                 5-4 bit : Decoder mode (MAX_SNR_MODE=1, MAX_LINEARITY_MODE=2)
        digital_data_path_status : int
            in ADC
                   0 bit : FIFO Status (enable=1, disable=0)
                 7-4 bit : Decimation factor
                10-8 bit : Mixer mode (OFF=0, C2C=1, R2C=3)
            in DAC
                   0 bit : FIFO Status (enable=1, disable=0)
                 7-4 bit : Interpolation factor
                   8 bit : Multiband adder enable (enable=1, disable=0)
               14-12 bit : Mixer mode (OFF=0, C2C=1, C2R=2)
        data_path_clocks_status : int
            Data path clocks status (enable=1, disable=0)
        is_fifo_flags_asserted : int
            Interrupt status register (ISR) of FIFO
               0 bit : FIFO overflow flag (data written faster than read)
               1 bit : FIFO underflow flag (data read faster than written)
        is_fifo_flags_enabled : int
            Interrupt mask register (IMR) of FIFO
               0 bit : FIFO overflow flag (data written faster than read)
               1 bit : FIFO underflow flag (data read faster than written)
        """
        self.cmd = self._joinargs("GetBlockStatus", [type, tile_id, block_id])
        self.res = self.rft_if.put(self.cmd)

        [type, tile_id, block_id, sampling_freq,
            analog_data_path_status, digital_data_path_status,
            data_path_clocks_status, is_fifo_flags_asserted,
            is_fifo_flags_enabled] = self._splitargs(self.res)

        return type, tile_id, block_id, sampling_freq, \
            analog_data_path_status, digital_data_path_status, \
            data_path_clocks_status, is_fifo_flags_asserted, \
            is_fifo_flags_enabled

    def GetThresholdSettings(self, tile_id, block_id):
        """Get ADC Threshold settings.
           **has not been used yet.**

        Parameters
        ----------
        tile_id : int
            ADC Tile ID number
        block_id : int
            ADC Block ID number

        Returns
        -------
        tile_id : int
            ADC Tile ID number
        block_id : int
            ADC Block ID number
        update_threshold : int
            The RFDC driver always returns 4 on success
            (see xrfdc.c:3001, xrfdc.h:784)
        threshold_mode_0 : int
            Threshold 0 Mode
        threshold_mode_1 : int
            Threshold 1 Mode
        threshold_avg_val_0 : int
            Threshold 0 Average
        threshold_avg_val_1 : int
            Threshold 1 Average
        threshold_under_val_0 : int
            Threshold 0 Under threshold
        threshold_under_val_1 : int
            Threshold 1 Under threshold
        threshold_over_val_0 : int
            Threshold 0 Over threshold
        threshold_over_val_1 : int
            Threshold 1 Over threshold
        """
        self.cmd = self._joinargs("GetThresholdSettings", [tile_id, block_id])
        self.res = self.rft_if.put(self.cmd)

        [tile_id, block_id, update_threshold, threshold_mode_0,
            threshold_mode_1, threshold_avg_val_0, threshold_avg_val_1,
            threshold_under_val_0, threshold_under_val_1,
            threshold_over_val_0, threshold_over_val_1
         ] = self._splitargs(self.res)

        return tile_id, block_id, update_threshold, threshold_mode_0, \
            threshold_mode_1, threshold_avg_val_0, threshold_avg_val_1, \
            threshold_under_val_0, threshold_under_val_1, \
            threshold_over_val_0, threshold_over_val_1

    def RF_ReadReg32(self, address_offset):
        """Read RFDC register in 32 bits
           **has not been used yet.**

        Parameters
        ----------
        address_offset : int
            Addres offset

        Returns
        value : int
            Register value
        """
        self.cmd = self._joinargs("RF_ReadReg32", [address_offset])
        self.res = self.rft_if.put(self.cmd)

        [value] = self._splitargs(self.res)

        return value

    def RF_WriteReg32(self, address_offset, value):
        """Write RFDC register in 32 bits
           **has not been used yet.**

        Parameters
        ----------
        address_offset : int
            Addres offset
        value : int
            Register value
        """
        self.cmd = self._joinargs("RF_WriteReg32", [address_offset, value])
        self.res = self.rft_if.put(self.cmd)
        return

    def RF_ReadReg16(self, address_offset):
        """Read RFDC register in 16 bits
           **has not been used yet.**

        Parameters
        ----------
        address_offset : int
            Addres offset

        Returns
        value : int
            Register value
        """
        self.cmd = self._joinargs("RF_ReadReg16", [address_offset])
        self.res = self.rft_if.put(self.cmd)

        [value] = self._splitargs(self.res)

        return value

    def RF_WriteReg16(self, address_offset, value):
        """Write RFDC register in 16 bits
           **has not been used yet.**

        Parameters
        ----------
        address_offset : int
            Addres offset
        value : int
            Register value
        """
        self.cmd = self._joinargs("RF_WriteReg16", [address_offset, value])
        self.res = self.rft_if.put(self.cmd)
        return

    def RF_ReadReg8(self, address_offset):
        """Read RFDC register in 8 bits
           **has not been used yet.**

        Parameters
        ----------
        address_offset : int
            Addres offset

        Returns
        value : int
            Register value
        """
        self.cmd = self._joinargs("RF_ReadReg8", [address_offset])
        self.res = self.rft_if.put(self.cmd)

        [value] = self._splitargs(self.res)

        return value

    def RF_WriteReg8(self, address_offset, value):
        """Write RFDC register in 8 bits
           **has not been used yet.**

        Parameters
        ----------
        address_offset : int
            Addres offset
        value : int
            Register value
        """
        self.cmd = self._joinargs("RF_WriteReg8", [address_offset, value])
        self.res = self.rft_if.put(self.cmd)
        return

    def MultiBand(
        self, type, tile_id, digital_data_path_mask,
        data_type, data_converter_mask
    ):
        """Setup Multiband configuration of ADC/DAC
           **has not been used yet.**

        Parameters
        ----------
        type : int
            Type (ADC=0, DAC=1)
        tile_id : int
            ADC/DAC Tile ID number
        block_id : int
            ADC/DAC Block ID number
        digital_data_path_mask : int
            Digital data path mask
            First 4 bits represent 4 data paths (enable=1, disable=0)
            e.g. to enable datapath 0 and datapath 2, specify 0x5(=0b0101).
        data_type : int
            Multiband data type (C2C=1, R2C=2, C2R=4)
        data_converter_mask : int
            Digital converter mask
            First 4 bits represent 4 ADC/DAC blocks (enable=1, disable=0)
            e.g. when masking Block 0 and Block 2, specify 0x5(=0b0101).
        """
        self.cmd = self._joinargs("MultiBand", [
            type, tile_id, digital_data_path_mask,
            data_type, data_converter_mask])
        self.res = self.rft_if.put(self.cmd)
        return

    def GetConnectedData(self, type, tile_id, block_id):
        """Get Data converter connected for digital data path I/Q.
           **has not been used yet.**

        Parameters
        ----------
        type : int
            Type (ADC=0, DAC=1)
        tile_id : int
            ADC/DAC Tile ID number
        block_id : int
            ADC/DAC Block ID number

        Returns
        -------
        type : int
            Type (ADC=0, DAC=1)
        tile_id : int
            ADC/DAC Tile ID number
        block_id : int
            ADC/DAC Block ID number
        connected_I_data : int
            Connected I Data
        connected_Q_data : int
            Connected Q Data
        """
        self.cmd = self._joinargs(
            "GetConnectedData", [type, tile_id, block_id])
        self.res = self.rft_if.put(self.cmd)

        [type, tile_id, block_id,
            connected_I_data, connected_Q_data] = self._splitargs(self.res)

        return type, tile_id, block_id, connected_I_data, connected_Q_data

    def GetInvSincFIR(self, tile_id, block_id):
        """Get DAC Inverse-Sync filter enable/mode.
           **has not been used yet.**

        Parameters
        ----------
        tile_id : int
            DAC Tile ID number
        block_id : int
            DAC Block ID number

        Returns
        -------
        tile_id : int
            DAC Tile ID number
        block_id : int
            DAC Block ID number
        mode : int
            Inverse-Sync filter mode
            (disable=0, 1st nyquist zone=1, 2nd nyquist zone=2)
        """
        self.cmd = self._joinargs("GetInvSincFIR", [tile_id, block_id])
        self.res = self.rft_if.put(self.cmd)

        [tile_id, block_id, mode] = self._splitargs(self.res)

        return tile_id, block_id, mode

    def SetInvSincFIR(self, tile_id, block_id, mode):
        """Set DAC Inverse-Sync filter mode.
           **has not been used yet.**

        Parameters
        ----------
        tile_id : int
            DAC Tile ID number
        block_id : int
            DAC Block ID number
        mode : int
            Inverse-Sync filter mode
            (disable=0, 1st nyquist zone=1, 2nd nyquist zone=2)
        """
        self.cmd = self._joinargs("SetInvSincFIR", [tile_id, block_id, mode])
        self.res = self.rft_if.put(self.cmd)
        return

    def IntrClr(self, type, tile_id, block_id, interrupt_mask):
        """Clear interrupt status of ADC/DAC.

        Parameters
        ----------
        type : int
            Type (ADC=0, DAC=1)
        tile_id : int
            ADC/DAC Tile ID number
        block_id : int
            ADC/DAC Block ID number
        interrupt_mask : int
            Mask to clear interrupt flag (set bit to clear)
            in ADC
             3- 0 bit : IXR_FIFOUSRDAT_MASK
            11- 4 bit : ADC_IXR_DATAPATH_MASK
            23-16 bit : SUBADC_IXR_DCDR_MASK
               26 bit : ADC_OVR_VOLTAGE_MASK
               27 bit : ADC_OVR_RANGE_MASK
               28 bit : ADC_CMODE_OVR_MASK
               29 bit : ADC_CMODE_UNDR_MASK
               30 bit : ADC_DAT_OVR_MASK
               31 bit : ADC_FIFO_OVR_MASK
            in DAC
             3- 0 bit : IXR_FIFOUSRDAT_MASK
            12- 4 bit : DAC_IXR_DATAPATH_MASK
        """
        self.cmd = self._joinargs(
            "IntrClr", [type, tile_id, block_id, interrupt_mask])
        self.res = self.rft_if.put(self.cmd)
        return

    def GetIntrStatus(self, type, tile_id, block_id):
        """Get interrupt status of ADC/DAC.

        Parameters
        ----------
        type : int
            Type (ADC=0, DAC=1)
        tile_id : int
            ADC/DAC Tile ID number
        block_id : int
            ADC/DAC Block ID number

        Returns
        -------
        type : int
            Type (ADC=0, DAC=1)
        tile_id : int
            ADC/DAC Tile ID number
        block_id : int
            ADC/DAC Block ID number
        interrupt_status : int
            Interrupt flags (asserted=1, not asserted=0)
            Details below.

            RF-ADC/RF-DAC datapath interrupt
                0x40000000 : XRFDC_ADC_DAT_OVR_MASK
            Overflow in RF-DAC Interpolation Stage 0/1/2/3 I or Q datapath
                0x00000010 : XRFDC_DAC_IXR_INTP_I_STG0_MASK
                0x00000020 : XRFDC_DAC_IXR_INTP_I_STG1_MASK
                0x00000040 : XRFDC_DAC_IXR_INTP_I_STG2_MASK
                0x00000080 : XRFDC_DAC_IXR_INTP_Q_STG0_MASK
                0x00000100 : XRFDC_DAC_IXR_INTP_Q_STG1_MASK
                0x00000200 : XRFDC_DAC_IXR_INTP_Q_STG2_MASK
            Overflow in RF-ADC Decimation Stage 0/1/2/3 I or Q datapath
                0x00000010 : XRFDC_ADC_IXR_DMON_I_STG0_MASK
                0x00000020 : XRFDC_ADC_IXR_DMON_I_STG1_MASK
                0x00000040 : XRFDC_ADC_IXR_DMON_I_STG2_MASK
                0x00000080 : XRFDC_ADC_IXR_DMON_Q_STG0_MASK
                0x00000100 : XRFDC_ADC_IXR_DMON_Q_STG1_MASK
                0x00000200 : XRFDC_ADC_IXR_DMON_Q_STG2_MASK
            Overflow in RF-DAC/RF-ADC QMC Gain/Phase
                0x00000400 : XRFDC_IXR_QMC_GAIN_PHASE_MASK
            Overflow in RF-DAC/RF-ADC QMC Offset
                0x00000800 : XRFDC_IXR_QMC_OFFST_MASK
            Overflow in RF-DAC Inverse Sinc Filter
                0x00001000 : XRFDC_DAC_IXR_INVSNC_OF_MASK
            Sub RF-ADC0/1/2/3 Over/Under range Interrupt
                0x00010000 : XRFDC_SUBADC0_IXR_DCDR_OF_MASK
                0x00020000 : XRFDC_SUBADC0_IXR_DCDR_UF_MASK
                0x00040000 : XRFDC_SUBADC1_IXR_DCDR_OF_MASK
                0x00080000 : XRFDC_SUBADC1_IXR_DCDR_UF_MASK
                0x00100000 : XRFDC_SUBADC2_IXR_DCDR_OF_MASK
                0x00200000 : XRFDC_SUBADC2_IXR_DCDR_UF_MASK
                0x00400000 : XRFDC_SUBADC3_IXR_DCDR_OF_MASK
                0x00800000 : XRFDC_SUBADC3_IXR_DCDR_UF_MASK
            RF-ADC over range
                0x08000000 : XRFDC_ADC_OVR_RANGE_MASK
            RF-ADC over voltage
                0x04000000 : XRFDC_ADC_OVR_VOLTAGE_MASK
            RF-ADC/RF-DAC FIFO over/underflow
                0x80000000 : XRFDC_ADC_FIFO_OVR_MASK
            RF-ADC/RF-DAC FIFO overflow
                0x00000001 : XRFDC_IXR_FIFOUSRDAT_OF_MASK
            RF-ADC/RF-DAC FIFO underflow
                0x00000002 : XRFDC_IXR_FIFOUSRDAT_UF_MASK
            RF-ADC/RF-DAC FIFO merginal overflow
                0x00000004 : XRFDC_IXR_FIFOMRGNIND_OF_MASK
            RF-ADC/RF-DAC FIFO merginal underflow
                0x00000008 : XRFDC_IXR_FIFOMRGNIND_UF_MASK
        """
        self.cmd = self._joinargs("GetIntrStatus", [type, tile_id, block_id])
        self.res = self.rft_if.put(self.cmd)

        [type, tile_id, block_id, interrupt_status] = self._splitargs(self.res)

        return type, tile_id, block_id, interrupt_status

    def TermMode(self, enable):
        """Enable terminal mode.

        Additional debug print are enabled and sent back to the console.

        Parameters
        ----------
        enable : int
            enable terminal mode (enable=1, disable=0)
        """
        self.cmd = self._joinargs("TermMode", [enable])
        self.res = self.rft_if.put(self.cmd)
        return

    def GetExtPllFreqList(self, board_id, pll_src):
        """Get available frequencies of External PLL clock (LMX2594).

        Parameters
        ----------
        board_id : int
            Board ID (ZCU111=0, ZC1254=1, ZC1275=2)
        pll_src : int
            PLL Source (PLL_A=0x8, PLL_B=0x4, PLL_C=0x1)

        Returns
        -------
        freq_list : list
            Available frequencies of LMX2594
        """
        self.cmd = self._joinargs("GetExtPllFreqList", [board_id, pll_src])
        self.res = self.rft_if.put(self.cmd)

        freq_list = self._splitargs(self.res)

        return freq_list

    def GetExtPllConfig(self, board_id, pll_src):
        """Get currently configured frequency of External PLL clock (LMX2594).
           **has not been used yet.**

        Parameters
        ----------
        board_id : int
            Board ID (ZCU111=0, ZC1254=1, ZC1275=2)
        pll_src : int
            PLL Source (PLL_A=0x8, PLL_B=0x4, PLL_C=0x1)

        Returns
        -------
        freq : int
            PLL frequency - this value corresponds to the index of the list
            obtained by GetExtPllFreqList command
        """
        self.cmd = self._joinargs("GetExtPllConfig", [board_id, pll_src])
        self.res = self.rft_if.put(self.cmd)

        [freq] = self._splitargs(self.res)

        return freq

    def SetCalFreeze(self, tile_id, block_id, enable):
        """Set calibration freeze feature of ADC.
           **has not been used yet.**

        Parameters
        ----------
        tile_id : int
            ADC Tile ID number
        block_id : int
            ADC Block ID number
        enable : int
            Calibration freeze enable (enable=1, disalbe=0)
        """
        self.cmd = self._joinargs("SetCalFreeze", [tile_id, block_id, enable])
        self.res = self.rft_if.put(self.cmd)
        return

    def GetCalFreeze(self, tile_id, block_id):
        """Set calibration freeze feature of ADC.
           **has not been used yet.**

        Parameters
        ----------
        tile_id : int
            ADC Tile ID number
        block_id : int
            ADC Block ID number

        Returns
        -------
        tile_id : int
            ADC Tile ID number
        block_id : int
            ADC Block ID number
        enable : int
            Calibration freeze enable (enable=1, disalbe=0)
        """
        self.cmd = self._joinargs("GetCalFreeze", [tile_id, block_id])
        self.res = self.rft_if.put(self.cmd)

        [tile_id, block_id, enable] = self._splitargs(self.res)

        return tile_id, block_id, enable

    def SetBitstream(self, design):
        """Invoke thread to load the specified Bitstream.

        Parameters
        ----------
        design : int
            Design type (NON_MTS=1, MTS=2, DAC1_ADC1(SSR)=3)
        """
        self.cmd = self._joinargs("SetBitstream", [design])
        self.res = self.rft_if.put(self.cmd)
        return

    def GetBitstream(self):
        """Get the enum value of loaded Bitstream.

        Returns
        -------
        design : int
            Design type (NON_MTS=1, MTS=2, DAC1_ADC1(SSR)=3)
        """
        self.cmd = "GetBitstream"
        self.res = self.rft_if.put(self.cmd)

        [design] = self._splitargs(self.res)

        return design

    def GetBitstreamStatus(self):
        """Get the PL loading status.

        Returns
        -------
        design_ready : int
            PL design ready (not_ready=0, ready=1)
        """
        self.cmd = "GetBitstreamStatus"
        self.res = self.rft_if.put(self.cmd)

        [design_ready] = self._splitargs(self.res)

        return design_ready

    def GetDither(self, tile_id, block_id):
        """Get ADC Dither status.

        Parameters
        ----------
        tile_id : int
            ADC Tile ID number
        block_id : int
            ADC Block ID number

        Returns
        -------
        tile_id : int
            ADC Tile ID number
        block_id : int
            ADC Block ID number
        enable : int
            ADC Dither enable (enable=1, disable=0)
        """
        self.cmd = self._joinargs("GetDither", [tile_id, block_id])
        self.res = self.rft_if.put(self.cmd)

        [tile_id, block_id, enable] = self._splitargs(self.res)

        return tile_id, block_id, enable

    def SetDither(self, tile_id, block_id, enable):
        """Set ADC Dither status.

        Parameters
        ----------
        tile_id : int
            ADC Tile ID number
        block_id : int
            ADC Block ID number
        enable : int
            ADC Dither enable (enable=1, disable=0)
        """
        self.cmd = self._joinargs("SetDither", [tile_id, block_id, enable])
        self.res = self.rft_if.put(self.cmd)
        return

    def GetFabClkOutDiv(self, type, tile_id):
        """Get Fablic clock divider of ADC/DAC.

        Parameters
        ----------
        type : int
            Type (ADC=0, DAC=1)
        tile_id : int
            ADC/DAC Tile ID number

        Returns
        -------
        type : int
            Type (ADC=0, DAC=1)
        tile_id : int
            ADC/DAC Tile ID number
        fab_clk_div : int
            Fablic clock divider (1 to 16)
        """
        self.cmd = self._joinargs("GetFabClkOutDiv", [type, tile_id])
        self.res = self.rft_if.put(self.cmd)
        [type, tile_id, fab_clk_div] = self._splitargs(self.res)

        return type, tile_id, fab_clk_div

    def SetTriggerLatency(self, type, latency):
        """Set latency of Trigger system. (e-trees)

        Parameters
        ----------
        type : int
            Type (ADC=0, DAC=1)
        latency : int
            trigger latency (0-32767)
        """
        self.cmd = self._joinargs("SetTriggerLatency", [type, latency])
        self.res = self.rft_if.put(self.cmd)
        return

    def SetTriggerInfo(self, type, channels, num_of_samples, data_format):
        """Set parameters of Trigger system. (e-trees)

        Parameters
        ----------
        type : int
            Type (ADC=0, DAC=1)
        channels : int
            Mask bit corresponding to the channel to use
            e.g. when masking channnel 0 and channel 2, specify 0x5(=0b0101).
        num_of_samples : int
            Number of samples
        data_format : int
            Real data or I/Q interleaved data (Real=0, I/Q interleaved=1)
        """
        self.cmd = self._joinargs("SetTriggerInfo", [type, channels, num_of_samples, data_format])
        self.res = self.rft_if.put(self.cmd)
        return

    def SetTriggerCycle(self, num_of_cycle, cycle_period):
        """Set Num of trigger / period. (e-trees)

        Parameters
        ----------
        num_of_cycle : int
            Num of trigger cycles
        cycle_period : int
            Trigger cycle period
        """
        self.cmd = self._joinargs("SetTriggerCycle", [num_of_cycle, cycle_period])
        self.res = self.rft_if.put(self.cmd)
        return

    def StartTrigger(self):
        """Start Trigger system. (e-trees)
        """
        self.cmd = "StartTrigger"
        self.res = self.rft_if.put(self.cmd)
        return

    def GetTriggerStatus(self):
        """Get Trigger status. (e-trees)

        Returns
        -------
        busy : int
            Trigger system is standby/busy (standby=0, busy=1)
        """
        self.cmd = "GetTriggerStatus"
        self.res = self.rft_if.put(self.cmd)
        [busy] = self._splitargs(self.res)

        return busy

    def SetAccumulateMode(self, enable):
        """Set Accumulation mode for BRAM Accumulation design. (e-trees)

        Parameters
        ----------
        enable : int
            Accumulation enable (disable=0, enable=1)
        """
        self.cmd = self._joinargs("SetAccumulateMode", [enable])
        self.res = self.rft_if.put(self.cmd)
        return

    def GetAccumulateOverrange(self):
        """Get Accumulator overrange flag. (e-trees)

        Returns
        -------
        accum_ovr : int
            Accumulator overrange flag per ADC channel
        """
        self.cmd = "GetAccumulateOverrange"
        self.res = self.rft_if.put(self.cmd)
        [accum_ovr] = self._splitargs(self.res)

        return accum_ovr

    def SetMACConfig(self, adc_bwidth_mode, ignore_mac_overrange):
        """Set Multiply-Accumulator configuration for BRAM Feedback design. (e-trees)

        Parameters
        ----------
        adc_bwidth_mode : int
            Multiply-Accumulator input bit width select (16bit=0, 12bit=1, per ADC channel)
        ignore_mac_overrange : int
            Ignore Multiply-Accumulator overrange then DAC trigger
            (do not trigger=0, ignore overrange then trigger=1, per ADC channel)
        """
        self.cmd = self._joinargs("SetMACConfig", [adc_bwidth_mode, ignore_mac_overrange])
        self.res = self.rft_if.put(self.cmd)
        return

    def ClearBRAM(self):
        """Clear All BRAM. (e-trees)
        """
        self.cmd = "ClearBRAM"
        self.res = self.rft_if.put(self.cmd)
        return

    def ClearDRAM(self, type):
        """Clear a DRAM block.
        """
        self.cmd = self._joinargs("ClearDRAM", [type])
        self.res = self.rft_if.put(self.cmd)
        return