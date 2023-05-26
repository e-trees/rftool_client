
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

        @classmethod
        def stg(cls, idx):
            stgs = [cls.STG_0,  cls.STG_1,  cls.STG_2,  cls.STG_3,
                    cls.STG_4,  cls.STG_5,  cls.STG_6,  cls.STG_7]
            return stgs[idx]


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
    
        @classmethod
        def stg(cls, idx):
            stgs = [cls.STG_0,  cls.STG_1,  cls.STG_2,  cls.STG_3,
                    cls.STG_4,  cls.STG_5,  cls.STG_6,  cls.STG_7]
            return stgs[idx]

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

        @classmethod
        def stg(cls, idx):
            stgs = [cls.STG_0,  cls.STG_1,  cls.STG_2,  cls.STG_3,
                    cls.STG_4,  cls.STG_5,  cls.STG_6,  cls.STG_7]
            return stgs[idx]

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
        
        @classmethod
        def chunk(cls, idx):
            chunks = [cls.CHUNK_0,  cls.CHUNK_1,  cls.CHUNK_2,  cls.CHUNK_3,
                      cls.CHUNK_4,  cls.CHUNK_5,  cls.CHUNK_6,  cls.CHUNK_7,
                      cls.CHUNK_8,  cls.CHUNK_9,  cls.CHUNK_10, cls.CHUNK_11,
                      cls.CHUNK_12, cls.CHUNK_13, cls.CHUNK_14, cls.CHUNK_15]
            return chunks[idx]

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

        @classmethod
        def dout(cls, idx):
            douts = [cls.DOUT_0, cls.DOUT_1]
            return douts[idx]


class DigitalOutCtrlRegs(object):

    class Addr(object):
        DOUT_0  = 0x5080
        DOUT_1  = 0x5100
    
        @classmethod
        def dout(cls, idx):
            douts = [cls.DOUT_0, cls.DOUT_1]
            return douts[idx]

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
        DOUT_0  = 0x6000
        DOUT_1  = 0x7000

        @classmethod
        def dout(cls, idx):
            douts = [cls.DOUT_0, cls.DOUT_1]
            return douts[idx]

    class Offset(object):        
        @classmethod
        def pattern(cls, idx):
            return idx * 8

        BIT_PATTERN = 0x0
        OUTPUT_TIME = 0x4
