from airtouch2.protocol.constants import CommandMessageConstants, CommandMessageType, GroupCommands
from airtouch2.protocol.messages.CommandMessage import CommandMessage

class GroupCommand(CommandMessage):
    """Base class from which all group control messages are derived"""
    def __init__(self, target_group_number: int):
        super().__init__()
        self.target_group = target_group_number

    def serialize(self, prefilled_msg: bytearray) -> bytearray:
        prefilled_msg[1] = CommandMessageType.GROUP_CONTROL
        prefilled_msg[3] = self.target_group

        return super().serialize(prefilled_msg)

class ToggleGroup(GroupCommand):
    """Command to toggle a group on or off"""

    def serialize(self) -> bytearray:
        serial_msg: bytearray = bytearray(self.length)
        serial_msg[4] = CommandMessageConstants.TOGGLE
        serial_msg[5] = GroupCommands.TOGGLE
        return super().serialize(serial_msg)

class ChangeDamper(GroupCommand):
    """Command to toggle a group on or off"""
    def __init__(self, target_group_number: int, inc: bool):
        super().__init__(target_group_number)
        self.inc = inc

    def serialize(self) -> bytearray:
        serial_msg: bytearray = bytearray(self.length)
        serial_msg[4] = GroupCommands.DAMP_INC if self.inc else GroupCommands.DAMP_DEC
        serial_msg[5] = GroupCommands.CHANGE_DAMP
        return super().serialize(serial_msg)