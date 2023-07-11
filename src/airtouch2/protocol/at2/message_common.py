
from airtouch2.common.Buffer import Buffer


def checksum(data: bytearray) -> int:
    sum: int = 0
    for b in data:
        sum += b
    sum = (sum % 256)
    return sum


def add_checksum_message_buffer(buffer: Buffer) -> None:
    buffer.append_bytes(checksum(buffer._data[:-1]).to_bytes(1, 'little'))
