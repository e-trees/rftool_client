
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
    ADDR = 0x5000

    class Offset(object):
        VERSION         = 0x0
        CTRL_TARGET_SEL = 0x4
        CTRL            = 0x8
        EXT_TRIG_MASK   = 0xC

    class Bit(object):
        CTRL_RESET     = 0
        CTRL_START     = 1
        CTRL_TERMINATE = 2
        CTRL_DONE_CLR  = 3
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
        __douts = [
            DOUT_0,  DOUT_1,  DOUT_2,  DOUT_3,
            DOUT_4,  DOUT_5,  DOUT_6,  DOUT_7,
            DOUT_8,  DOUT_9,  DOUT_10, DOUT_11,
            DOUT_12, DOUT_13, DOUT_14, DOUT_15]

        @classmethod
        def dout(cls, idx):
            return cls.__douts[idx]


class DigitalOutCtrlRegs(object):

    class Addr(object):
        DOUT_0  = 0x5080
        DOUT_1  = 0x5100
        DOUT_2  = 0x5180
        DOUT_3  = 0x5200
        DOUT_4  = 0x5280
        DOUT_5  = 0x5300
        DOUT_6  = 0x5380
        DOUT_7  = 0x5400
        DOUT_8  = 0x5480
        DOUT_9  = 0x5500
        DOUT_10 = 0x5580
        DOUT_11 = 0x5600
        DOUT_12 = 0x5680
        DOUT_13 = 0x5700
        DOUT_14 = 0x5780
        DOUT_15 = 0x5800
        __douts = [
            DOUT_0,  DOUT_1,  DOUT_2,  DOUT_3,
            DOUT_4,  DOUT_5,  DOUT_6,  DOUT_7,
            DOUT_8,  DOUT_9,  DOUT_10, DOUT_11,
            DOUT_12, DOUT_13, DOUT_14, DOUT_15]

        @classmethod
        def dout(cls, idx):
            return cls.__douts[idx]

    class Offset(object):
        CTRL         = 0x0
        STATUS       = 0x4
        NUM_PATTERNS = 0x8
        START_IDX    = 0xC

    class Bit(object):
        CTRL_RESET          = 0
        CTRL_START          = 1
        CTRL_TERMINATE      = 2
        CTRL_DONE_CLR       = 3
        STATUS_WAKEUP       = 0
        STATUS_BUSY         = 1
        STATUS_DONE         = 2


class DigitalOutputDataListRegs(object):
    #### digital output data params ####
    class Addr(object):
        DOUT_0   = 0x10_0000
        DOUT_1   = 0x14_0000
        DOUT_2   = 0x18_0000
        DOUT_3   = 0x1C_0000
        DOUT_4   = 0x20_0000
        DOUT_5   = 0x24_0000
        DOUT_6   = 0x28_0000
        DOUT_7   = 0x2C_0000
        DOUT_8   = 0x30_0000
        DOUT_9   = 0x34_0000
        DOUT_10  = 0x38_0000
        DOUT_11  = 0x3C_0000
        DOUT_12  = 0x40_0000
        DOUT_13  = 0x44_0000
        DOUT_14  = 0x48_0000
        DOUT_15  = 0x4C_0000
        __douts = [
            DOUT_0,  DOUT_1,  DOUT_2,  DOUT_3,
            DOUT_4,  DOUT_5,  DOUT_6,  DOUT_7,
            DOUT_8,  DOUT_9,  DOUT_10, DOUT_11,
            DOUT_12, DOUT_13, DOUT_14, DOUT_15]

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
