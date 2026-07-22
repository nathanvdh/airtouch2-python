from __future__ import annotations

from airtouch2.common.interfaces import Serializable
from airtouch2.protocol.at2plus.control_status_common import (
    CONTROL_STATUS_SUBHEADER_LENGTH,
    ControlStatusSubType,
    ControlStatusSubHeader,
    SubDataLength,
)
from airtouch2.protocol.at2plus.message_common import (
    Header,
    MessageType,
    add_checksum_message_buffer,
    prime_message_buffer,
)

# The controller requires the ACK's top-level address byte to carry the
# control/status identifier (0xC0), NOT the usual client value (0x80). Verified
# on a live AirTouch 2+: acking the status broadcasts with 0x80 triggers a
# continuous broadcast spam storm (~1.7/sec, ~100x normal) until the session is
# unusable; 0xC0 is accepted cleanly. It looks redundant with the message-type
# byte, but the controller genuinely validates it.
CONTROL_STATUS_REPLY_ADDRESS = 0xC0


class Ack(Serializable):
    message_type: ControlStatusSubType

    def __init__(self, message_type: ControlStatusSubType):
        self.message_type = message_type

    def to_bytes(self) -> bytes:
        subheader = ControlStatusSubHeader(self.message_type, SubDataLength(1, 0, 0))
        buffer = prime_message_buffer(
            Header(
                CONTROL_STATUS_REPLY_ADDRESS,
                MessageType.CONTROL_STATUS,
                CONTROL_STATUS_SUBHEADER_LENGTH + subheader.subdata_length.total(),
            )
        )
        buffer.append(subheader)
        buffer.append_bytes(bytes([0]))  # zero payload byte
        add_checksum_message_buffer(buffer)
        return buffer.to_bytes()
