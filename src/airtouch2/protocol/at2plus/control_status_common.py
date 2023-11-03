from __future__ import annotations
from dataclasses import dataclass
from enum import IntEnum
from airtouch2.common.Buffer import Buffer
import logging

from airtouch2.common.interfaces import Serializable


CONTROL_STATUS_SUBHEADER_LENGTH = 8
SUBDATALENGTH_LENGTH = 6

_LOGGER = logging.getLogger(__name__)

class ControlStatusOffsets(IntEnum):
    # Control/Status messages 'data' consists of:
    # * 8 byte header with information as described below, immediately followed by:
    # * a 'normal data', which occurs once, with length described in the header.
    # * a number of 'repeat data', which each have length described by the header
    # 1st byte is one of ControlStatusSubType
    SUBTYPE = 0
    # 2nd byte empty
    # bytes 3-4 are 'normal data' length
    NORMAL_DATA_LENGTH = 2
    # bytes 5-6 are each 'repeat data' length
    REPEAT_DATA_LENGTH = 4
    # bytes 7-8 are number of repeated 'repeat data's
    REPEAT_DATA_COUNT = 6
    SUBDATA = 8


class ControlStatusSubType(IntEnum):
    UNSET = 0
    GROUP_CONTROL = 0x20
    GROUP_STATUS = 0x21
    AC_CONTROL = 0x22
    AC_STATUS = 0x23


@dataclass
class SubDataLength(Serializable):
    normal: int
    repeat_count: int
    repeat_length: int

    def total(self):
        return self.normal + self.repeat_count * self.repeat_length

    @staticmethod
    def from_bytes(length_bytes: bytes) -> SubDataLength:
        if len(length_bytes) != SUBDATALENGTH_LENGTH:
            raise ValueError("Unexpected SubDataLength size")
        normal = int.from_bytes(length_bytes[0:2], 'big')
        repeat_length = int.from_bytes(length_bytes[2:4], 'big')
        repeat_count = int.from_bytes(length_bytes[4:6], 'big')
        return SubDataLength(normal, repeat_count, repeat_length)

    def to_bytes(self) -> bytes:
        return self.normal.to_bytes(2, 'big') + \
            self.repeat_length.to_bytes(2, 'big') + \
            self.repeat_count.to_bytes(2, 'big')


@dataclass
class ControlStatusSubHeader(Serializable):
    sub_type: ControlStatusSubType
    subdata_length: SubDataLength

    @staticmethod
    def from_bytes(subheader_bytes: bytes) -> ControlStatusSubHeader:
        if len(subheader_bytes) != CONTROL_STATUS_SUBHEADER_LENGTH:
            raise ValueError("Unexpected control/status subheader size")
        try:
            subtype = ControlStatusSubType(subheader_bytes[0])
        except ValueError as e:
            _LOGGER.warning(
                f"Unknown message type in header ({hex(subheader_bytes[0])})", exc_info=e)
            subtype = ControlStatusSubType.UNSET

        data_length = SubDataLength.from_bytes(subheader_bytes[2:8])
        return ControlStatusSubHeader(subtype, data_length)

    @staticmethod
    def from_buffer(buffer: Buffer) -> ControlStatusSubHeader:
        return ControlStatusSubHeader.from_bytes(buffer.read_bytes(CONTROL_STATUS_SUBHEADER_LENGTH))

    def to_bytes(self) -> bytes:
        return self.sub_type.to_bytes(1, 'big') + \
            bytes(1) + \
            self.subdata_length.to_bytes()
