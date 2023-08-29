from enum import IntEnum, Enum

class STG(IntEnum):
    """Stimulus Generator の ID"""
    U0  = 0 
    U1  = 1 
    U2  = 2 
    U3  = 3 
    U4  = 4 
    U5  = 5 
    U6  = 6 
    U7  = 7 

    @classmethod
    def all(cls):
        """全 STG の ID をリストとして返す"""
        return list(STG)

    @classmethod
    def of(cls, val):
        if not cls.includes(val):
            raise ValueError("cannot convert {} to STG".format(val))
        return cls.all()[val]

    @classmethod
    def includes(cls, *vals):
        stgs = cls.all()
        return all([val in stgs for val in vals])


class DigitalOut(IntEnum):
    """Digital Output の ID"""
    U0  = 0
    U1  = 1
    U2  = 2
    U3  = 3
    U4  = 4
    U5  = 5
    U6  = 6
    U7  = 7
    U8  = 8
    U9  = 9
    U10 = 10
    U11 = 11
    U12 = 12
    U13 = 13
    U14 = 14
    U15 = 15
    U16 = 16
    U17 = 17
    U18 = 18
    U19 = 19
    U20 = 20
    U21 = 21
    U22 = 22
    U23 = 23
    U24 = 24
    U25 = 25
    U26 = 26
    U27 = 27
    U28 = 28
    U29 = 29
    U30 = 30
    U31 = 31
    U32 = 32
    U33 = 33

    @classmethod
    def all(cls):
        """全 Digital Output の ID をリストとして返す"""
        return list(DigitalOut)

    @classmethod
    def of(cls, val):
        if not cls.includes(val):
            raise ValueError("cannot convert {} to DigitalOut".format(val))
        return cls.all()[val]

    @classmethod
    def includes(cls, *vals):
        douts = cls.all()
        return all([val in douts for val in vals])


class StgErr(Enum):
    """STG エラーの列挙型"""

    MEM_RD = 0
    SAMPLE_SHORTAGE = 1

    @classmethod
    def all(cls):
        """全 STG エラーの列挙子をリストとして返す"""
        return list(StgErr)

    @classmethod
    def includes(cls, *vals):
        errs = cls.all()
        return all([val in errs for val in vals])

    @classmethod
    def to_msg(cls, err):
        if err == cls.MEM_RD:
            return 'Failed to read waveform.'
        if err == cls.SAMPLE_SHORTAGE:
            return 'Wave samples were not sent to a DAC in time.'
        
        raise ValueError('unknown stg error {}'.format(err))
