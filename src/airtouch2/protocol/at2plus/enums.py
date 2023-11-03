
from __future__ import annotations
from enum import IntEnum


class AcSetPower(IntEnum):
    TOGGLE = 1
    OFF = 2
    ON = 3
    AWAY = 4
    SLEEP = 5
    UNCHANGED = 15

    @staticmethod
    def from_int(val: int) -> AcSetPower:
        try:
            return AcSetPower(val)
        except ValueError:
            return AcSetPower.UNCHANGED


class AcPower(IntEnum):
    OFF = 0
    ON = 1
    AWAY_OFF = 2
    AWAY_ON = 3
    SLEEP = 5
    NOT_AVAILABLE = 15

    @staticmethod
    def from_int(val: int) -> AcPower:
        try:
            return AcPower(val)
        except ValueError:
            return AcPower.NOT_AVAILABLE


class AcSetMode(IntEnum):
    AUTO = 0
    HEAT = 1
    DRY = 2
    FAN = 3
    COOL = 4
    UNCHANGED = 15

    @staticmethod
    def from_int(val: int) -> AcSetMode:
        try:
            return AcSetMode(val)
        except ValueError:
            return AcSetMode.UNCHANGED


class AcMode(IntEnum):
    AUTO = 0
    HEAT = 1
    DRY = 2
    FAN = 3
    COOL = 4
    AUTO_HEAT = 8
    AUTO_COOL = 9
    NOT_AVAILABLE = 15

    @staticmethod
    def from_int(val: int) -> AcMode:
        try:
            return AcMode(val)
        except ValueError:
            return AcMode.NOT_AVAILABLE


class AcFanSpeed(IntEnum):
    AUTO = 0
    QUIET = 1
    LOW = 2
    MEDIUM = 3
    HIGH = 4
    POWERFUL = 5
    TURBO = 6
    UNCHANGED = 15

    @staticmethod
    def from_int(val: int) -> AcFanSpeed:
        try:
            return AcFanSpeed(val)
        except ValueError:
            return AcFanSpeed.UNCHANGED

class GroupPower(IntEnum):
    OFF = 0
    ON = 1
    TURBO = 3

class GroupSetDamper(IntEnum):
    UNCHANGED = 0
    INC = 2
    DEC = 3
    SET = 4

    @staticmethod
    def from_int(val: int) -> GroupSetDamper:
        try:
            return GroupSetDamper(val)
        except ValueError:
            return GroupSetDamper.UNCHANGED

class GroupSetPower(IntEnum):
    UNCHANGED = 0
    NEXT = 1
    OFF = 2
    ON = 3
    TURBO = 5

    @staticmethod
    def from_int(val: int) -> GroupSetPower:
        try:
            return GroupSetPower(val)
        except ValueError:
            return GroupSetPower.UNCHANGED