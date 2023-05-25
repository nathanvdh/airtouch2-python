from airtouch2.protocol.at2.constants import CommandMessageConstants, CommandMessageType, GroupCommands, MessageLength
from airtouch2.protocol.at2.message_common import add_checksum_message_buffer
from airtouch2.common.Buffer import Buffer
from airtouch2.common.interfaces import Serializable


def prime_group_control_message_buffer(target_group: int) -> Buffer:
    buffer = Buffer(MessageLength.COMMAND)
    buffer.append_bytes(CommandMessageConstants.BYTE_0.to_bytes(1, 'little'))
    buffer.append_bytes(CommandMessageType.GROUP_CONTROL.to_bytes(1, 'little'))
    buffer.append_bytes(CommandMessageConstants.BYTE_2.to_bytes(1, 'little'))
    buffer.append_bytes(target_group.to_bytes(1, 'little'))
    return buffer


class ToggleGroup(Serializable):
    def __init__(self, target_group_number: int):
        self.target_group = target_group_number

    def to_bytes(self) -> bytes:
        buffer = prime_group_control_message_buffer(self.target_group)
        buffer.append_bytes(CommandMessageConstants.TOGGLE.to_bytes(1, 'little'))
        buffer.append_bytes(GroupCommands.TOGGLE.to_bytes(1, 'little'))
        buffer.append_bytes(bytes([0, 0, 0, 0, 0, 0]))
        add_checksum_message_buffer(buffer)
        return buffer.to_bytes()


class ChangeDamper(Serializable):
    def __init__(self, target_group_number: int, inc: bool):
        self.target_group = target_group_number
        self.inc = inc

    def to_bytes(self) -> bytes:
        buffer = prime_group_control_message_buffer(self.target_group)
        inc_dec = GroupCommands.DAMP_INC if self.inc else GroupCommands.DAMP_DEC
        buffer.append_bytes(inc_dec.to_bytes(1, 'little'))
        buffer.append_bytes(GroupCommands.CHANGE_DAMP.to_bytes(1, 'little'))
        buffer.append_bytes(bytes([0, 0, 0, 0, 0, 0]))
        add_checksum_message_buffer(buffer)
        return buffer.to_bytes()
