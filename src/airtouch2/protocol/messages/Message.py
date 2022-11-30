from abc import ABC
from airtouch2.protocol.constants import MessageLength

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