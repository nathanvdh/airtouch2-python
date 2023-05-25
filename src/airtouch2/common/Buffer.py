from __future__ import annotations
from airtouch2.common.interfaces import Serializable


class Buffer(Serializable):
    """
    Layer of asbtraction on top of bytearray.
    Has a fixed size and enforces it's filled before it's serialized.
    Prohibits reading more than its size and before it's filled.
    """
    data: bytearray
    head: int = 0
    tail: int = 0
    mutable: bool = True

    def __init__(self, size: int):
        self.data = bytearray(size)

    def __len__(self):
        return len(self.data)

    def append_bytes(self, data: bytes) -> bool:
        """Returns true if buffer was filled, raises BufferError if there is not sufficient room in the buffer or the buffer is finalised"""
        if not self.mutable:
            raise BufferError("Buffer has been finalised and is immutable")
        if (len(data) > len(self.data) - self.head):
            raise BufferError(
                "Buffer does not have enough room to append this data")
        for byte in data:
            self.data[self.head] = byte
            self.head += 1
        return self.head == len(self.data)

    def append(self, object: Serializable) -> None:
        self.append_bytes(object.to_bytes())

    def to_bytes(self) -> bytes:
        self.finalise()
        return self.data

    def finalise(self) -> Buffer:
        if (self.head != len(self.data)):
            raise BufferError(
                f"Buffer is not filled - {self.head}/{len(self.data)} bytes filled")
        self.mutable = False
        return self

    def read_bytes(self, size: int) -> bytes:
        if (self.tail >= len(self.data)):
            raise BufferError("All data from this buffer has been read")
        if (self.tail >= self.head):
            raise BufferError("There is not data to read")
        if (self.mutable):
            raise BufferError("Cannot read from incomplete buffer")
        start = self.tail
        self.tail += size
        return self.data[start:self.tail]

    def read_remaining(self) -> bytes:
        return self.read_bytes(self.head - self.tail)

    @staticmethod
    def from_bytes(data: bytes) -> Buffer:
        buffer = Buffer(len(data))
        buffer.append_bytes(data)
        return buffer
