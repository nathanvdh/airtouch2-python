from airtouch2.protocol.at2.messages.CommandMessage import CommandMessage
from airtouch2.protocol.at2.constants import CommandMessageType

class RequestState(CommandMessage):
    """ Command to request the state of the airtouch 2 system"""

    def serialize(self) -> bytearray:
        serial_msg: bytearray = bytearray(self.length)
        serial_msg[1] = CommandMessageType.REQUEST_STATE
        return super()._serialize(serial_msg)