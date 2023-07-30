from airtouch2.protocol.at2.conversions import val_from_fan_speed
from airtouch2.protocol.at2.message_common import add_checksum_message_buffer
from airtouch2.protocol.at2.constants import ACCommands, CommandMessageConstants, CommandMessageType, MessageLength
from airtouch2.protocol.at2.enums import ACFanSpeed, ACMode
from airtouch2.common.Buffer import Buffer
from airtouch2.common.interfaces import Serializable


def prime_ac_control_message_buffer(target_ac: int) -> Buffer:
    buffer = Buffer(MessageLength.COMMAND)
    buffer.append_bytes(CommandMessageConstants.BYTE_0.to_bytes(1, 'little'))
    buffer.append_bytes(CommandMessageType.AC_CONTROL.to_bytes(1, 'little'))
    buffer.append_bytes(CommandMessageConstants.BYTE_2.to_bytes(1, 'little'))
    buffer.append_bytes(target_ac.to_bytes(1, 'little'))
    return buffer


class ChangeSetTemperature(Serializable):
    def __init__(self, target_ac_number: int, inc: bool):
        self.target_ac = target_ac_number
        self.inc = inc

    def to_bytes(self) -> bytes:
        buffer = prime_ac_control_message_buffer(self.target_ac)
        inc_dec = ACCommands.TEMP_INC if self.inc else ACCommands.TEMP_DEC
        buffer.append_bytes(inc_dec.to_bytes(1, 'little'))
        buffer.append_bytes(bytes([0, 0, 0, 0, 0, 0, 0]))
        add_checksum_message_buffer(buffer)
        return buffer.to_bytes()


class ToggleAc(Serializable):
    def __init__(self, target_ac_number: int):
        self.target_ac = target_ac_number

    def to_bytes(self) -> bytes:
        buffer = prime_ac_control_message_buffer(self.target_ac)
        buffer.append_bytes(CommandMessageConstants.TOGGLE.to_bytes(1, 'little'))
        buffer.append_bytes(bytes([0, 0, 0, 0, 0, 0, 0]))
        add_checksum_message_buffer(buffer)
        return buffer.to_bytes()


class SetFanSpeed(Serializable):
    def __init__(self, target_ac_number: int, supported_fan_speeds: list[ACFanSpeed], fan_speed: ACFanSpeed):
        self.target_ac = target_ac_number
        self.fan_speed_val: int = val_from_fan_speed(supported_fan_speeds, fan_speed)

    def to_bytes(self) -> bytes:
        buffer = prime_ac_control_message_buffer(self.target_ac)
        buffer.append_bytes(ACCommands.SET_FAN_SPEED.to_bytes(1, 'little'))
        buffer.append_bytes(self.fan_speed_val.to_bytes(1, 'little'))
        buffer.append_bytes(bytes([0, 0, 0, 0, 0, 0]))
        add_checksum_message_buffer(buffer)
        return buffer.to_bytes()


class SetMode(Serializable):
    def __init__(self, target_ac_number: int, mode: ACMode):
        self.target_ac = target_ac_number
        self.mode = mode

    def to_bytes(self) -> bytes:
        buffer = prime_ac_control_message_buffer(self.target_ac)
        buffer.append_bytes(ACCommands.SET_MODE.to_bytes(1, 'little'))
        buffer.append_bytes(self.mode.to_bytes(1, 'little'))
        buffer.append_bytes(bytes([0, 0, 0, 0, 0, 0]))
        add_checksum_message_buffer(buffer)
        return buffer.to_bytes()
