from __future__ import annotations
from abc import ABC
from airtouch2.protocol.constants import ACControlCommands, CommandMessageConstants, CommandMessageType, MessageLength, ResponseMessageConstants, ResponseMessageOffsets
from airtouch2.protocol.enums import ACFanSpeed, ACManufacturer, ACMode
from sys import maxsize as MAX_INT

class Message(ABC):
    """ Message base class from which all airtouch 2 communications messages are derived"""
    length: MessageLength = MessageLength.UNDETERMINED

    def add_checksum(self, serial_msg: bytearray) -> bytearray:
        serial_msg[self.length-1] = self.checksum(serial_msg)
        return serial_msg
    
    @staticmethod
    def checksum(serial_msg: bytearray) -> int:
        sum: int = 0
        for b in serial_msg:
            sum += b
        sum = (sum % 256)
        return sum

class CommandMessage(Message):
    """ Command message base class from which all airtouch2 command messages are derived"""
    length: MessageLength = MessageLength.COMMAND
    
    # command messages are only sent so only need to be serialized
    def serialize(self, prefilled_msg: bytearray) -> bytearray:
        prefilled_msg[0] = CommandMessageConstants.BYTE_0
        prefilled_msg[2] = CommandMessageConstants.BYTE_2
        return self.add_checksum(prefilled_msg)

class RequestState(CommandMessage):
    """ Command to request the state of the airtouch 2 system"""
    
    def serialize(self) -> bytearray:
        serial_msg: bytearray = bytearray(self.length)
        serial_msg[1] = CommandMessageType.REQUEST_STATE
        return super().serialize(serial_msg)

class ACControlCommand(CommandMessage):
    """Base class from which all AC control messages are derived"""
    def __init__(self, target_ac_number: int):
        super().__init__()
        self.target_ac = target_ac_number

    def serialize(self, prefilled_msg: bytearray) -> bytearray:
        prefilled_msg[1] = CommandMessageType.AC_CONTROL
        prefilled_msg[3] = self.target_ac
        return super().serialize(prefilled_msg)

class ChangeSetTemperature(ACControlCommand):
    """Command to increment or decrement the AC set point by 1 degree"""
    def __init__(self, target_ac_number: int, inc: bool):
        super().__init__(target_ac_number)
        self.inc = inc

    def serialize(self) -> bytearray:
        serial_msg: bytearray = bytearray(self.length)
        serial_msg[4] = ACControlCommands.TEMP_INC if self.inc else ACControlCommands.TEMP_DEC
        return super().serialize(serial_msg)

class ToggleAC(ACControlCommand):
    """Command to toggle an AC on or off"""
    
    def serialize(self) -> bytearray:
        serial_msg: bytearray = bytearray(self.length)
        serial_msg[4] = CommandMessageConstants.TOGGLE
        return super().serialize(serial_msg)

# needs investigation
class SetFanSpeed(ACControlCommand):
    """Command to set the AC fan speed to one of those in ACFanSpeed"""
    def __init__(self, target_ac_number: int, fan_speed: ACFanSpeed):
        super().__init__(target_ac_number)
        self.fan_speed: ACFanSpeed = fan_speed

    def serialize(self) -> bytearray:
        serial_msg: bytearray = bytearray(self.length)
        serial_msg[4] = ACControlCommands.SET_FAN_SPEED
        serial_msg[5] = self.fan_speed
        return super().serialize(serial_msg)

class SetMode(ACControlCommand):
    """Command to set the AC mode to one of those in ACMode"""
    def __init__(self, target_ac_number: int, mode: ACMode):
        super().__init__(target_ac_number)
        self.mode: ACMode = mode
    
    def serialize(self) -> bytearray:
        serial_msg: bytearray = bytearray(self.length)
        serial_msg[4] = ACControlCommands.SET_MODE
        serial_msg[5] = self.mode
        return super().serialize(serial_msg)

class ResponseMessage(Message):
    """ The airtouch 2 response message (there is only one) that contains all the information about the current state of the system"""
    
    length: MessageLength = MessageLength.RESPONSE

    # only getting fundamental things for AC1 for now
    def __init__(self, raw_response: bytes):
        super().__init__()
        # seems to be x000_1111 - x is on/off. This is different to what Luke describes.
        status = raw_response[ResponseMessageOffsets.AC1_STATUS]
        self.ac_active = [(status & 0x80 > 0)]
        self.ac_status = [(status & 0x7F)]
        # simply 0-4, see ACMode enum
        self.ac_mode = [ACMode(raw_response[ResponseMessageOffsets.AC1_MODE])]
        # 0100_0xxx - least significant byte is 0 to 4 - see ACFanSpeed enum
        self.ac_fan_speed = [ACFanSpeed(raw_response[ResponseMessageOffsets.AC1_FAN_SPEED] & 0x0F)]
        self.ac_set_temp = [raw_response[ResponseMessageOffsets.AC1_SET_TEMP]]
        self.ac_ambient_temp = [raw_response[ResponseMessageOffsets.AC1_AMBIENT_TEMP]]
        self.ac_manufacturer = [ACManufacturer(raw_response[ResponseMessageOffsets.AC1_MANUFACTURER])]
        self.ac_name = [raw_response[ResponseMessageOffsets.AC1_NAME_START:ResponseMessageOffsets.AC1_NAME_START+ResponseMessageConstants.SHORT_STRING_LENGTH].decode()]
        #self.zones = {}
        self.system_name = raw_response[ResponseMessageOffsets.SYSTEM_NAME:ResponseMessageOffsets.SYSTEM_NAME+ResponseMessageConstants.LONG_STRING_LENGTH].decode()
