from airtouch2.protocol.messages.Message import Message
from airtouch2.protocol.constants import CommandMessageConstants, MessageLength

class CommandMessage(Message):
    """ Command message base class from which all airtouch2 command messages are derived"""
    length: MessageLength = MessageLength.COMMAND

    # command messages are only sent so only need to be serialized
    def serialize(self, prefilled_msg: bytearray) -> bytearray:
        prefilled_msg[0] = CommandMessageConstants.BYTE_0
        prefilled_msg[2] = CommandMessageConstants.BYTE_2
        return self.add_checksum(prefilled_msg)