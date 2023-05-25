from airtouch2.protocol.at2.message_common import add_checksum_message_buffer
from airtouch2.protocol.at2.constants import CommandMessageConstants, CommandMessageType, MessageLength
from airtouch2.common.Buffer import Buffer
from airtouch2.common.interfaces import Serializable


class RequestState(Serializable):
    """ Command to request the state of the airtouch 2 system"""

    def to_bytes(self) -> bytes:
        buffer = Buffer(MessageLength.COMMAND)
        buffer.append_bytes(CommandMessageConstants.BYTE_0.to_bytes(1, 'little'))
        buffer.append_bytes(CommandMessageType.REQUEST_STATE.to_bytes(1, 'little'))
        buffer.append_bytes(CommandMessageConstants.BYTE_2.to_bytes(1, 'little'))
        buffer.append_bytes(bytes([0, 0, 0, 0, 0, 0, 0, 0, 0]))
        add_checksum_message_buffer(buffer)
        return buffer.to_bytes()
