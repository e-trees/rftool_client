from enum import Enum, IntEnum

ADC = 0
DAC = 1
PL_DDR4_RAM_SIZE = 0x100000000

class FpgaDesign(IntEnum):
    AWG_SA = 7
    MTS_AWG_SA = 8
    AWG_SA_BRAM_CAPTURE = 9
    AWG_BINARIZATION = 10
    AWG_DSP = 11
    MTS_AWG_SA_LOW_SAMPLING_RATE = 12
    STIM_GEN = 13
    STIM_GEN_ALL_SYNC = 14

class RfdcInterrupt(Enum):
    """Rfdc 割り込み一覧"""

    # DAC 補間オーバーフロー
    DAC_INTERPOLATION_OVERFLOW = 0
    # ADC 間引きオーバーフロー
    ADC_DECIMATION_OVERFLOW = 1
    # QMC オーバーフロー
    DAC_QMC_GAIN_PHASE_OVERFLOW  = 2
    DAC_QMC_OFFSET_OVERFLOW      = 3
    ADC_QMC_GAIN_PHASE_OVERFLOW  = 4
    ADC_QMC_OFFSET_OVERFLOW      = 5
    # Inverse Sinc Filter オーバーフロー
    DAC_INV_SINC_OVERFLOW = 6
    # SUB ADC オーバーレンジ
    SUB_ADC_OVER_RANGE = 7
    # ADC オーバーボルテージ
    ADC_OVER_VOLTAGE = 8
    # ADC オーバーレンジ
    ADC_OVER_RANGE = 9
    # DAC FIFO オーバー/アンダーフロー
    DAC_FIFO_OVERFLOW  = 10
    DAC_FIFO_UNDERFLOW = 11
    DAC_FIFO_MARGINAL_OVERFLOW  = 12
    DAC_FIFO_MARGINAL_UNDERFLOW = 13
    # ADC FIFO オーバー/アンダーフロー
    ADC_FIFO_OVERFLOW  = 14
    ADC_FIFO_UNDERFLOW = 15
    ADC_FIFO_MARGINAL_OVERFLOW  = 16
    ADC_FIFO_MARGINAL_UNDERFLOW = 17

    @classmethod
    def to_msg(cls, interrupt):
        if interrupt == cls.DAC_INTERPOLATION_OVERFLOW:
            return 'Overflow detected in DAC Interpolation stage datapath.'
        if interrupt == cls.ADC_DECIMATION_OVERFLOW:
            return 'Overflow detected in ADC decimation stage datapath.'
        if interrupt == cls.DAC_QMC_GAIN_PHASE_OVERFLOW:
            return 'Overflow detected in DAC QMC Gain/Phase.'
        if interrupt == cls.DAC_QMC_OFFSET_OVERFLOW: 
            return 'Overflow detected in DAC QMC offset.'
        if interrupt == cls.ADC_QMC_GAIN_PHASE_OVERFLOW:
            return 'Overflow detected in ADC QMC Gain/Phase.'
        if interrupt == cls.ADC_QMC_OFFSET_OVERFLOW:
            return 'Overflow detected in ADC QMC offset.'
        if interrupt == cls.DAC_INV_SINC_OVERFLOW:
            return 'Overflow detected in DAC Inverse Sinc Filter.'
        if interrupt == cls.SUB_ADC_OVER_RANGE:
            return 'Sub ADC over/under range detected.'
        if interrupt == cls.ADC_OVER_VOLTAGE:
            return 'ADC over voltage detected.'
        if interrupt == cls.ADC_OVER_RANGE:
            return 'ADC over range detected.'
        if interrupt == cls.DAC_FIFO_OVERFLOW:
            return 'DAC FIFO overflow detected.'
        if interrupt == cls.DAC_FIFO_UNDERFLOW:
            return 'DAC FIFO underflow detected.'
        if interrupt == cls.DAC_FIFO_MARGINAL_OVERFLOW:
            return 'DAC FIFO marginal overflow detected.'
        if interrupt == cls.DAC_FIFO_MARGINAL_UNDERFLOW:
            return 'DAC FIFO marginal underflow detected.'
        if interrupt == cls.ADC_FIFO_OVERFLOW:
            return 'ADC FIFO overflow detected.'
        if interrupt == cls.ADC_FIFO_UNDERFLOW:
            return 'ADC FIFO underflow detected.'
        if interrupt == cls.ADC_FIFO_MARGINAL_OVERFLOW:
            return 'ADC FIFO marginal overflow detected.'
        if interrupt == cls.ADC_FIFO_MARGINAL_UNDERFLOW:
            return 'ADC FIFO marginal underflow detected.'
        
        raise ValueError('unknown rfdc interrupt {}'.format(interrupt))


class RfdcIntrpMask(IntEnum):
    """Rfdc 割り込みマスク一覧"""

    # DAC 補間オーバーフロー
    DAC_I_INTP_STG0_OVF = 0x00000010
    DAC_I_INTP_STG1_OVF = 0x00000020
    DAC_I_INTP_STG2_OVF = 0x00000040
    DAC_Q_INTP_STG0_OVF = 0x00000080
    DAC_Q_INTP_STG1_OVF = 0x00000100
    DAC_Q_INTP_STG2_OVF = 0x00000200
    # ADC 間引きオーバーフロー
    ADC_I_DMON_STG0_OVF = 0x00000010
    ADC_I_DMON_STG1_OVF = 0x00000020
    ADC_I_DMON_STG2_OVF = 0x00000040
    ADC_Q_DMON_STG0_OVF = 0x00000080
    ADC_Q_DMON_STG1_OVF = 0x00000100
    ADC_Q_DMON_STG2_OVF = 0x00000200
    # QMC オーバーフロー
    DAC_QMC_GAIN_PHASE_OVF = 0x00000400
    DAC_QMC_OFFSET_OVF     = 0x00000800
    ADC_QMC_GAIN_PHASE_OVF = 0x00000400
    ADC_QMC_OFFSET_OVF     = 0x00000800
    # Inverse Sinc Filter オーバーフロー
    DAC_INV_SINC_OVF = 0x00001000
    # SUB ADC オーバーレンジ
    SUB_ADC0_OVR = 0x00010000
    SUB_ADC0_UDR = 0x00020000
    SUB_ADC1_OVR = 0x00040000
    SUB_ADC1_UDR = 0x00080000
    SUB_ADC2_OVR = 0x00100000
    SUB_ADC2_UDR = 0x00200000
    SUB_ADC3_OVR = 0x00400000
    SUB_ADC3_UDR = 0x00800000
    # ADC オーバーボルテージ
    ADC_OVV = 0x04000000
    # ADC オーバーレンジ
    ADC_OVR = 0x08000000
    # DAC FIFO オーバー/アンダーフロー
    DAC_FIFO_OVF          = 0x00000001
    DAC_FIFO_UDF          = 0x00000002
    DAC_FIFO_MARGIANL_OVF = 0x00000004
    DAC_FIFO_MARGIANL_UDF = 0x00000008
    # ADC FIFO オーバー/アンダーフロー
    ADC_FIFO_OVF          = 0x00000001
    ADC_FIFO_UDF          = 0x00000002
    ADC_FIFO_MARGIANL_OVF = 0x00000004
    ADC_FIFO_MARGIANL_UDF = 0x00000008
