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
        return [item for item in STG]

    @classmethod
    def of(cls, val):
        if not cls.includes(val):
            raise ValueError("connot convert {} to STG".format(val))
        return cls.all()[val]

    @classmethod
    def includes(cls, *vals):
        stgs = cls.all()
        return all([val in stgs for val in vals])


class DigitalOut(IntEnum):
    """Digital Output の ID"""
    U0  = 0 
    U1  = 1 

    @classmethod
    def all(cls):
        """全 Digital Output の ID をリストとして返す"""
        return [item for item in DigitalOut]

    @classmethod
    def of(cls, val):
        if not cls.includes(val):
            raise ValueError("connot convert {} to DigitalOut".format(val))
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
        return [item for item in StgErr]

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
