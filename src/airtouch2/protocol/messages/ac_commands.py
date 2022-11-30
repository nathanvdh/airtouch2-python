from airtouch2.protocol.messages.CommandMessage import CommandMessage
from airtouch2.protocol.constants import ACCommands, CommandMessageConstants, CommandMessageType
from airtouch2.protocol.enums import ACMode

class ACCommand(CommandMessage):
    """Base class from which all AC control messages are derived"""
    def __init__(self, target_ac_number: int):
        super().__init__()
        self.target_ac = target_ac_number

    def serialize(self, prefilled_msg: bytearray) -> bytearray:
        prefilled_msg[1] = CommandMessageType.AC_CONTROL
        prefilled_msg[3] = self.target_ac
        return super().serialize(prefilled_msg)

class ChangeSetTemperature(ACCommand):
    """Command to increment or decrement the AC set point by 1 degree"""
    def __init__(self, target_ac_number: int, inc: bool):
        super().__init__(target_ac_number)
        self.inc = inc

    def serialize(self) -> bytearray:
        serial_msg: bytearray = bytearray(self.length)
        serial_msg[4] = ACCommands.TEMP_INC if self.inc else ACCommands.TEMP_DEC
        return super().serialize(serial_msg)

class ToggleAC(ACCommand):
    """Command to toggle an AC on or off"""

    def serialize(self) -> bytearray:
        serial_msg: bytearray = bytearray(self.length)
        serial_msg[4] = CommandMessageConstants.TOGGLE
        return super().serialize(serial_msg)

# needs investigation
class SetFanSpeed(ACCommand):
    """Command to set the AC fan speed"""
    def __init__(self, target_ac_number: int, fan_speed: int):
        super().__init__(target_ac_number)
        self.fan_speed: int = fan_speed

    def serialize(self) -> bytearray:
        serial_msg: bytearray = bytearray(self.length)
        serial_msg[4] = ACCommands.SET_FAN_SPEED
        serial_msg[5] = self.fan_speed
        return super().serialize(serial_msg)

class SetMode(ACCommand):
    """Command to set the AC mode to one of those in ACMode"""
    def __init__(self, target_ac_number: int, mode: ACMode):
        super().__init__(target_ac_number)
        self.mode: ACMode = mode

    def serialize(self) -> bytearray:
        serial_msg: bytearray = bytearray(self.length)
        serial_msg[4] = ACCommands.SET_MODE
        serial_msg[5] = self.mode
        return super().serialize(serial_msg)