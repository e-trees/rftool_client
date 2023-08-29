
class StgMasterCtrlRegs(object):
    ADDR = 0x0

    class Offset(object):
        VERSION             = 0x0
        CTRL_TARGET_SEL     = 0x4
        CTRL                = 0x8
        WAKEUP_STATUS       = 0xC
        BUSY_STATUS         = 0x10
        READY_STATUS        = 0x14
        DONE_STATUS         = 0x18
        READ_ERR            = 0x1C
        SAMPLE_SHORTAGE_ERR = 0x20

    class Bit(object):
        CTRL_RESET     = 0
        CTRL_PREPARE   = 1
        CTRL_START     = 2
        CTRL_TERMINATE = 3
        CTRL_DONE_CLR  = 4
        STG_0  = 0
        STG_1  = 1
        STG_2  = 2
        STG_3  = 3
        STG_4  = 4
        STG_5  = 5
        STG_6  = 6
        STG_7  = 7
        __stgs = [
            STG_0, STG_1, STG_2, STG_3,
            STG_4, STG_5, STG_6, STG_7]

        @classmethod
        def stg(cls, idx):
            return cls.__stgs[idx]


class StgCtrlRegs(object):

    class Addr(object):
        STG_0  = 0x80
        STG_1  = 0x100
        STG_2  = 0x180
        STG_3  = 0x200
        STG_4  = 0x280
        STG_5  = 0x300
        STG_6  = 0x380
        STG_7  = 0x400
        __stgs = [
            STG_0, STG_1, STG_2, STG_3,
            STG_4, STG_5, STG_6, STG_7]
        
        @classmethod
        def stg(cls, idx): 
            return cls.__stgs[idx]

    class Offset(object):
        CTRL   = 0x0
        STATUS = 0x4
        ERR    = 0x8

    class Bit(object):
        CTRL_RESET          = 0
        CTRL_PREPARE        = 1
        CTRL_START          = 2
        CTRL_TERMINATE      = 3
        CTRL_DONE_CLR       = 4
        STATUS_WAKEUP       = 0
        STATUS_BUSY         = 1
        STATUS_READY        = 2
        STATUS_DONE         = 3
        ERR_READ            = 0
        ERR_SAMPLE_SHORTAGE = 1


class WaveParamRegs(object):
    #### wave params ####
    class Addr(object):
        STG_0  = 0x1000
        STG_1  = 0x1400
        STG_2  = 0x1800
        STG_3  = 0x1C00
        STG_4  = 0x2000
        STG_5  = 0x2400
        STG_6  = 0x2800
        STG_7  = 0x2C00
        __stgs = [
            STG_0, STG_1, STG_2, STG_3,
            STG_4, STG_5, STG_6, STG_7]

        @classmethod
        def stg(cls, idx):
            return cls.__stgs[idx]

    class Offset(object):
        CHUNK_0  = 0x40
        CHUNK_1  = 0x50
        CHUNK_2  = 0x60
        CHUNK_3  = 0x70
        CHUNK_4  = 0x80
        CHUNK_5  = 0x90
        CHUNK_6  = 0xA0
        CHUNK_7  = 0xB0
        CHUNK_8  = 0xC0
        CHUNK_9  = 0xD0
        CHUNK_10 = 0xE0
        CHUNK_11 = 0xF0
        CHUNK_12 = 0x100
        CHUNK_13 = 0x110
        CHUNK_14 = 0x120
        CHUNK_15 = 0x130
        __chunks = [
            CHUNK_0,  CHUNK_1,  CHUNK_2,  CHUNK_3,
            CHUNK_4,  CHUNK_5,  CHUNK_6,  CHUNK_7,
            CHUNK_8,  CHUNK_9,  CHUNK_10, CHUNK_11,
            CHUNK_12, CHUNK_13, CHUNK_14, CHUNK_15]
        
        @classmethod
        def chunk(cls, idx):
            return cls.__chunks[idx]

        NUM_WAIT_WORDS                = 0x0
        NUM_REPEATS                   = 0x4
        NUM_CHUNKS                    = 0x8
        WAVE_STARTABLE_BLOCK_INTERVAL = 0xC

        CHUNK_START_ADDR    = 0x0
        NUM_WAVE_PART_WORDS = 0x4
        NUM_BLANK_WORDS     = 0x8
        NUM_CHUNK_REPEATS   = 0xC


class DigitalOutMasterCtrlRegs(object):
    ADDR = 0x8000

    class Offset(object):
        VERSION             = 0x0
        CTRL_TARGET_SEL_0   = 0x4
        CTRL_TARGET_SEL_1   = 0x8
        CTRL                = 0xC
        START_TRIG_MASK_0   = 0x10
        START_TRIG_MASK_1   = 0x14
        RESTART_TRIG_MASK_0 = 0x18
        RESTART_TRIG_MASK_1 = 0x1C

    class Bit(object):
        CTRL_RESET     = 0
        CTRL_START     = 1
        CTRL_TERMINATE = 2
        CTRL_DONE_CLR  = 3
        CTRL_PAUSE     = 4
        CTRL_RESUME    = 5
        CTRL_RESTART   = 6
        DOUT_0  = 0
        DOUT_1  = 1
        DOUT_2  = 2
        DOUT_3  = 3
        DOUT_4  = 4
        DOUT_5  = 5
        DOUT_6  = 6
        DOUT_7  = 7
        DOUT_8  = 8
        DOUT_9  = 9
        DOUT_10 = 10
        DOUT_11 = 11
        DOUT_12 = 12
        DOUT_13 = 13
        DOUT_14 = 14
        DOUT_15 = 15
        DOUT_16 = 16
        DOUT_17 = 17
        DOUT_18 = 18
        DOUT_19 = 19
        DOUT_20 = 20
        DOUT_21 = 21
        DOUT_22 = 22
        DOUT_23 = 23
        DOUT_24 = 24
        DOUT_25 = 25
        DOUT_26 = 26
        DOUT_27 = 27
        DOUT_28 = 28
        DOUT_29 = 29
        DOUT_30 = 30
        DOUT_31 = 31
        DOUT_32 = 0
        DOUT_33 = 1
        __douts = [
            DOUT_0,  DOUT_1,  DOUT_2,  DOUT_3,
            DOUT_4,  DOUT_5,  DOUT_6,  DOUT_7,
            DOUT_8,  DOUT_9,  DOUT_10, DOUT_11,
            DOUT_12, DOUT_13, DOUT_14, DOUT_15,
            DOUT_16, DOUT_17, DOUT_18, DOUT_19,
            DOUT_20, DOUT_21, DOUT_22, DOUT_23,
            DOUT_24, DOUT_25, DOUT_26, DOUT_27,
            DOUT_28, DOUT_29, DOUT_30, DOUT_31,
            DOUT_32, DOUT_33]

        @classmethod
        def dout(cls, idx):
            return cls.__douts[idx]


class DigitalOutCtrlRegs(object):

    class Addr(object):
        DOUT_0  = 0x8080
        DOUT_1  = 0x8100
        DOUT_2  = 0x8180
        DOUT_3  = 0x8200
        DOUT_4  = 0x8280
        DOUT_5  = 0x8300
        DOUT_6  = 0x8380
        DOUT_7  = 0x8400
        DOUT_8  = 0x8480
        DOUT_9  = 0x8500
        DOUT_10 = 0x8580
        DOUT_11 = 0x8600
        DOUT_12 = 0x8680
        DOUT_13 = 0x8700
        DOUT_14 = 0x8780
        DOUT_15 = 0x8800
        DOUT_16 = 0x8880
        DOUT_17 = 0x8900
        DOUT_18 = 0x8980
        DOUT_19 = 0x8A00
        DOUT_20 = 0x8A80
        DOUT_21 = 0x8B00
        DOUT_22 = 0x8B80
        DOUT_23 = 0x8C00
        DOUT_24 = 0x8C80
        DOUT_25 = 0x8D00
        DOUT_26 = 0x8D80
        DOUT_27 = 0x8E00
        DOUT_28 = 0x8E80
        DOUT_29 = 0x8F00
        DOUT_30 = 0x8F80
        DOUT_31 = 0x9000
        DOUT_32 = 0x9080
        DOUT_33 = 0x9100
        __douts = [
            DOUT_0,  DOUT_1,  DOUT_2,  DOUT_3,
            DOUT_4,  DOUT_5,  DOUT_6,  DOUT_7,
            DOUT_8,  DOUT_9,  DOUT_10, DOUT_11,
            DOUT_12, DOUT_13, DOUT_14, DOUT_15,
            DOUT_16, DOUT_17, DOUT_18, DOUT_19,
            DOUT_20, DOUT_21, DOUT_22, DOUT_23,
            DOUT_24, DOUT_25, DOUT_26, DOUT_27,
            DOUT_28, DOUT_29, DOUT_30, DOUT_31,
            DOUT_32, DOUT_33]

        @classmethod
        def dout(cls, idx):
            return cls.__douts[idx]

    class Offset(object):
        CTRL         = 0x0
        STATUS       = 0x4
        NUM_PATTERNS = 0x8
        START_IDX    = 0xC

    class Bit(object):
        CTRL_RESET     = 0
        CTRL_START     = 1
        CTRL_TERMINATE = 2
        CTRL_DONE_CLR  = 3
        CTRL_PAUSE     = 4
        CTRL_RESUME    = 5
        CTRL_RESTART   = 6
        STATUS_WAKEUP  = 0
        STATUS_BUSY    = 1
        STATUS_DONE    = 2
        STATUS_PAUSED  = 3


class DigitalOutputDataListRegs(object):
    #### digital output data params ####
    class Addr(object):
        DOUT_0  = 0x10_0000
        DOUT_1  = 0x14_0000
        DOUT_2  = 0x18_0000
        DOUT_3  = 0x1C_0000
        DOUT_4  = 0x20_0000
        DOUT_5  = 0x24_0000
        DOUT_6  = 0x28_0000
        DOUT_7  = 0x2C_0000
        DOUT_8  = 0x30_0000
        DOUT_9  = 0x34_0000
        DOUT_10 = 0x38_0000
        DOUT_11 = 0x3C_0000
        DOUT_12 = 0x40_0000
        DOUT_13 = 0x44_0000
        DOUT_14 = 0x48_0000
        DOUT_15 = 0x4C_0000
        DOUT_16 = 0x50_0000
        DOUT_17 = 0x54_0000
        DOUT_18 = 0x58_0000
        DOUT_19 = 0x5C_0000
        DOUT_20 = 0x60_0000
        DOUT_21 = 0x64_0000
        DOUT_22 = 0x68_0000
        DOUT_23 = 0x6C_0000
        DOUT_24 = 0x70_0000
        DOUT_25 = 0x74_0000
        DOUT_26 = 0x78_0000
        DOUT_27 = 0x7C_0000
        DOUT_28 = 0x80_0000
        DOUT_29 = 0x84_0000
        DOUT_30 = 0x88_0000
        DOUT_31 = 0x8C_0000
        DOUT_32 = 0x90_0000
        DOUT_33 = 0x94_0000
        __douts = [
            DOUT_0,  DOUT_1,  DOUT_2,  DOUT_3,
            DOUT_4,  DOUT_5,  DOUT_6,  DOUT_7,
            DOUT_8,  DOUT_9,  DOUT_10, DOUT_11,
            DOUT_12, DOUT_13, DOUT_14, DOUT_15,
            DOUT_16, DOUT_17, DOUT_18, DOUT_19,
            DOUT_20, DOUT_21, DOUT_22, DOUT_23,
            DOUT_24, DOUT_25, DOUT_26, DOUT_27,
            DOUT_28, DOUT_29, DOUT_30, DOUT_31,
            DOUT_32, DOUT_33]

        @classmethod
        def dout(cls, idx):    
            return cls.__douts[idx]

    class Offset(object):        
        @classmethod
        def pattern(cls, idx):
            return idx * 8

        BIT_PATTERN = 0x0
        OUTPUT_TIME = 0x4
        DEFAULT_BIT_PATTERN = 0x1000
