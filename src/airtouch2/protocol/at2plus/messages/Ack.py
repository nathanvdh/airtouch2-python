from __future__ import annotations

from airtouch2.common.interfaces import Serializable
from airtouch2.protocol.at2plus.control_status_common import (
    CONTROL_STATUS_SUBHEADER_LENGTH,
    ControlStatusSubType,
    ControlStatusSubHeader,
    SubDataLength,
)
from airtouch2.protocol.at2plus.message_common import (
    AddressMsgType,
    Header,
    MessageType,
    add_checksum_message_buffer,
    prime_message_buffer,
)


class Ack(Serializable):
    message_type: ControlStatusSubType

    def __init__(self, message_type: ControlStatusSubType):
        self.message_type = message_type

    def to_bytes(self) -> bytes:
        subheader = ControlStatusSubHeader(self.message_type, SubDataLength(1, 0, 0))
        buffer = prime_message_buffer(
            Header(
                AddressMsgType.NORMAL,
                MessageType.CONTROL_STATUS,
                CONTROL_STATUS_SUBHEADER_LENGTH + subheader.subdata_length.total(),
            )
        )
        buffer.append(subheader)
        buffer.append_bytes(bytes([0]))  # zero payload byte
        add_checksum_message_buffer(buffer)
        return buffer.to_bytes()
