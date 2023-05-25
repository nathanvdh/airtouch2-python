
from __future__ import annotations
from enum import IntEnum
from airtouch2.protocol.at2plus.constants import Limits
from airtouch2.protocol.at2plus.conversions import setpoint_from_value, value_from_setpoint
from airtouch2.protocol.at2plus.control_status_common import CONTROL_STATUS_SUBHEADER_LENGTH, ControlStatusSubType, SubDataLength, ControlStatusSubHeader
from airtouch2.protocol.at2plus.enums import AcFanSpeed, AcSetMode, AcSetPower
from airtouch2.protocol.at2plus.message_common import AddressMsgType, Header, MessageType, add_checksum_message_buffer, prime_message_buffer
from airtouch2.common.interfaces import Serializable

AC_SETTINGS_LENGTH = 4


class SetpointControl(IntEnum):
    KEEP = 0
    CHANGE = 0x40


class AcSettings(Serializable):
    id: int
    power: AcSetPower
    mode: AcSetMode
    speed: AcFanSpeed
    setpoint: float | None

    def __init__(self, ac_id: int, power: AcSetPower, mode: AcSetMode, speed: AcFanSpeed, setpoint: float | None = None):
        if setpoint is not None:
            if not Limits.SETPOINT_MIN <= setpoint <= Limits.SETPOINT_MAX:
                raise ValueError(
                    f'Setpoint must be from {Limits.SETPOINT_MIN} to {Limits.SETPOINT_MAX}')
        if not 0 <= ac_id < Limits.MAX_ACS:
            raise ValueError(f'AC ID must be from 0 to {Limits.MAX_ACS-1}')
        self.id = ac_id
        self.power = power
        self.mode = mode
        self.speed = speed
        self.setpoint = setpoint

    def to_bytes(self) -> bytes:
        data = bytearray(AC_SETTINGS_LENGTH)
        data[0] = (self.power << 4) | self.id
        data[1] = (self.mode << 4) | self.speed
        data[2] = SetpointControl.CHANGE if self.setpoint is not None else SetpointControl.KEEP
        data[3] = value_from_setpoint(self.setpoint)
        return data

    @staticmethod
    def from_bytes(data: bytes) -> AcSettings:
        if (len(data) != AC_SETTINGS_LENGTH):
            raise ValueError(f"Data must be {AC_SETTINGS_LENGTH} bytes")
        id = data[0] & 0x0F
        power = AcSetPower.from_int((data[0] & 0xF0) >> 4)
        mode = AcSetMode.from_int((data[1] & 0xF0) >> 4)
        speed = AcFanSpeed.from_int(data[1] & 0x0F)
        change_setpoint = data[2] == SetpointControl.CHANGE
        setpoint = setpoint_from_value(data[3]) if change_setpoint else None
        return AcSettings(id, power, mode, speed, setpoint)


class AcControlMessage(Serializable):
    """AcControl Message to control all ACs"""
    settings: list[AcSettings]

    def __init__(self, settings: list[AcSettings]):
        self.settings = settings

    def to_bytes(self) -> bytes:
        subheader = ControlStatusSubHeader(ControlStatusSubType.AC_CONTROL, SubDataLength(
            0, len(self.settings), AC_SETTINGS_LENGTH))
        buffer = prime_message_buffer(Header(AddressMsgType.NORMAL, MessageType.CONTROL_STATUS,
                                      CONTROL_STATUS_SUBHEADER_LENGTH + subheader.subdata_length.total()))
        buffer.append(subheader)
        for setting in self.settings:
            buffer.append(setting)
        add_checksum_message_buffer(buffer)
        return buffer.to_bytes()
