from __future__ import annotations
from dataclasses import dataclass
from enum import IntEnum

from airtouch2.protocol.bits_n_bytes.buffer import Buffer
from airtouch2.protocol.bits_n_bytes.crc16_modbus import crc16
from airtouch2.protocol.interfaces import Serializable

# Message ID can be whatever
MESSAGE_ID = 1
HEADER_MAGIC = 0x55
HEADER_LENGTH = 8
ADDRESS_CONSTANT = 0xB0
NON_DATA_LENGTH = 10


class CommonMessageOffsets(IntEnum):
    # Header is 0x55 0x55
    HEADER = 0
    # 0x80 0xb0 when sending, 0x?? 0x80 for receiving
    # Except extended message which is 0x90 0xb0 when sending and 0x?? 0x90 when receiving
    ADDRESS = 2
    # 'Can be any data' - response will match
    MESAGE_ID = 4
    # Usually 0xC0 but 0x1F for extended message
    MESSAGE_TYPE = 5
    # Number of bytes of data
    DATA_LENGTH = 6
    DATA = 8
    # Data length depends on message
    # Followed by 2-byte CRC16 MODBUS of message *without* header (AKA CRC-16-ANSI AKA CRC-16-IBM)


class Address(IntEnum):
    UNSET = 0
    NORMAL = 0x80
    EXTENDED = 0x90


class MessageType(IntEnum):
    UNSET = 0
    CONTROL_STATUS = 0xC0
    EXTENDED = 0x1F


class Header(Serializable):
    address: Address
    type: MessageType
    data_length: int
    _received: bool

    def __init__(self, address: Address, type: MessageType, data_length: int, _received=False):
        self.address = address
        self.type = type
        self.data_length = data_length
        self._received = _received

    @staticmethod
    def from_bytes(header_bytes: bytes) -> Header:
        if len(header_bytes) != HEADER_LENGTH:
            raise ValueError("Unexpected header size")
        for b in header_bytes[CommonMessageOffsets.HEADER:CommonMessageOffsets.ADDRESS]:
            if (b != HEADER_MAGIC):
                raise ValueError("Message header magic is invalid")
        type = MessageType(header_bytes[CommonMessageOffsets.MESSAGE_TYPE])
        # Ignore the first byte of the address, as it's undefined for received messages.
        address = Address(header_bytes[CommonMessageOffsets.ADDRESS+1])
        if type == MessageType.CONTROL_STATUS:
            if (address != Address.NORMAL):
                raise ValueError(f"Message address value is invalid: {header_bytes.hex(':')}")
        elif type == MessageType.EXTENDED:
            if (address != Address.EXTENDED):
                raise ValueError(f"Message address value is invalid: {header_bytes.hex(':')}")
        else:
            raise ValueError("Message type is invalid")
        id = header_bytes[CommonMessageOffsets.MESAGE_ID]
        data_length = int.from_bytes(
            header_bytes[CommonMessageOffsets.DATA_LENGTH:CommonMessageOffsets.DATA], 'big')
        return Header(address, type, data_length, True)

    def to_bytes(self) -> bytes:
        return bytes([HEADER_MAGIC, HEADER_MAGIC]) + \
            (bytes([ADDRESS_CONSTANT, self.address]) if self._received else bytes([self.address, ADDRESS_CONSTANT])) + \
            bytes([MESSAGE_ID, self.type]) + \
            self.data_length.to_bytes(2, 'big')


def prime_message_buffer(header: Header) -> Buffer:
    buffer = Buffer(header.data_length + NON_DATA_LENGTH)
    buffer.append(header)
    return buffer


def add_checksum_message_buffer(buffer: Buffer) -> None:
    buffer.append_bytes(crc16(buffer.data[2:-2]))


def add_checksum_message_bytes(data: bytearray) -> None:
    checksum = crc16(data[2:-2])
    data[-2] = checksum[0]
    data[-1] = checksum[1]


@dataclass
class Message:
    header: Header
    data_buffer: Buffer
