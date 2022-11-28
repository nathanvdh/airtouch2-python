from __future__ import annotations
from abc import ABC
from airtouch2.protocol.constants import ACControlCommands, CommandMessageConstants, CommandMessageType, MessageLength, ResponseMessageConstants, ResponseMessageOffsets
from airtouch2.protocol.enums import ACFanSpeedReference, ACBrand, ACMode
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
    """Command to set the AC fan speed"""
    def __init__(self, target_ac_number: int, fan_speed: int):
        super().__init__(target_ac_number)
        self.fan_speed: int = fan_speed

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

    # only getting things for AC1 for now
    def __init__(self, raw_response: bytes):
        super().__init__()

        status = raw_response[ResponseMessageOffsets.AC1_STATUS]
        # MS bit is on/off
        self.ac_active = [(status & 0x80 > 0)]
        # Bit 7 is whether AC is errored
        self.ac_error = [(status & 0x40 > 0)]
        self.ac_error_code = [raw_response[ResponseMessageOffsets.AC1_ERROR_CODE]]
        # bit 4 is whether or not 'thermistor on AC' is checked (0 = checked)
        self.ac_thermistor = [(status & 0x04 == 0)]
        # lowest 3 bits are AC program number
        #self.ac_program = [(status & 0x07)]

        status2 = raw_response[ResponseMessageOffsets.ACs_STATUS]
        self.ac_turbo = [(status2 & 0x20 > 0)]
        self.ac_safety = [(status2 & 0x04 > 0)]
        self.ac_spill = [(status2 & 0x02) > 0]

        # simply 0-4, see ACMode enum
        self.ac_mode = [ACMode(raw_response[ResponseMessageOffsets.AC1_MODE])]
        # most signficant byte is # of speeds, least significant byte is speed (the meaning of which depends), see AT2Aircon::_set_true_and_supported_fan_speed()
        self.ac_num_fan_speeds = [(raw_response[ResponseMessageOffsets.AC1_FAN_SPEED] & 0xF0) >> 4]
        self.ac_fan_speed = [raw_response[ResponseMessageOffsets.AC1_FAN_SPEED] & 0x0F]

        self.ac_set_temp = [raw_response[ResponseMessageOffsets.AC1_SET_TEMP]]
        self.ac_measured_temp = [raw_response[ResponseMessageOffsets.AC1_MEASURED_TEMP]]
        self.touchpad_temp = raw_response[ResponseMessageOffsets.TOUCHPAD_TEMP]

        self.ac_brand = [ACBrand(raw_response[ResponseMessageOffsets.AC1_BRAND])]
        self.ac_gateway_id = [raw_response[ResponseMessageOffsets.AC1_GATEWAY_ID]]

        self.ac_name = [raw_response[ResponseMessageOffsets.AC1_NAME_START:ResponseMessageOffsets.AC1_NAME_START+ResponseMessageConstants.SHORT_STRING_LENGTH].decode().split("\0")[0]]
        self.system_name = raw_response[ResponseMessageOffsets.SYSTEM_NAME:ResponseMessageOffsets.SYSTEM_NAME+ResponseMessageConstants.LONG_STRING_LENGTH].decode().split("\0")[0]
