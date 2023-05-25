from __future__ import annotations
from dataclasses import dataclass
from enum import IntEnum
from airtouch2.common.Buffer import Buffer

from airtouch2.common.interfaces import Serializable

SUBHEADER_MAGIC = 0xFF
EXTENDED_SUBHEADER_LENGTH = 2


class ExtendedMessageSubType(IntEnum):
    ERROR = 0x10
    ABILITY = 0x11
    GROUP_NAME = 0x12


@dataclass
class ExtendedSubHeader(Serializable):
    sub_type: ExtendedMessageSubType

    @staticmethod
    def from_bytes(subheader_bytes: bytes) -> ExtendedSubHeader:
        if len(subheader_bytes) != EXTENDED_SUBHEADER_LENGTH:
            raise ValueError("Unexpected control/status subheader size")
        if subheader_bytes[0] != SUBHEADER_MAGIC:
            raise ValueError("Subheader magic is incorrect")
        subtype = ExtendedMessageSubType(subheader_bytes[1])
        return ExtendedSubHeader(subtype)

    def to_bytes(self):
        return bytes([SUBHEADER_MAGIC, self.sub_type])

    @staticmethod
    def from_buffer(buffer: Buffer) -> ExtendedSubHeader:
        return ExtendedSubHeader.from_bytes(buffer.read_bytes(EXTENDED_SUBHEADER_LENGTH))
