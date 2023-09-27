from enum import IntEnum

class StgTrigger(IntEnum):
    START = 0

    @classmethod
    def all(cls):
        return list(StgTrigger)

    @classmethod
    def of(cls, value):
        if value == 0 or value == '0':
            return StgTrigger.START

        raise ValueError("cannot convert {} to StgTrigger".format(value))

    @classmethod
    def includes(cls, *vals):
        types = cls.all()
        return all([val in types for val in vals])


class DigitalOutTrigger(IntEnum):
    START   = 0
    RESTART = 1
    PAUSE   = 2
    RESUME  = 3

    @classmethod
    def all(cls):
        return list(DigitalOutTrigger)

    @classmethod
    def of(cls, value):
        if value == 0 or value == '0':
            return DigitalOutTrigger.START
        elif value == 0 or value == '1':
            return DigitalOutTrigger.RESTART
        elif value == 2 or value == '2':
            return DigitalOutTrigger.PAUSE
        elif value == 3 or value == '3':
            return DigitalOutTrigger.RESUME

        raise ValueError("cannot convert {} to DigitalOutTrigger".format(value))

    @classmethod
    def includes(cls, *vals):
        types = cls.all()
        return all([val in types for val in vals])
