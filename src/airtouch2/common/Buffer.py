from __future__ import annotations
from airtouch2.common.interfaces import Serializable


class Buffer(Serializable):
    """
    Layer of asbtraction on top of bytearray.
    Has a fixed size and enforces it's filled before it's serialized.
    Prohibits reading more than its size and before it's filled.
    """
    _data: bytearray
    _head: int = 0
    _tail: int = 0
    _mutable: bool = True

    def __init__(self, size: int):
        self._data = bytearray(size)

    def __len__(self):
        return len(self._data)

    def append_bytes(self, data: bytes) -> bool:
        """
        Return true and finalise if buffer was filled, raises BufferError if there
        is not sufficient room in the buffer or the buffer is already finalised.
        """
        if not self._mutable:
            raise BufferError("Buffer has been filled and is immutable")
        if (len(data) > len(self._data) - self._head):
            raise BufferError(
                "Buffer does not have enough room to append this data")
        for byte in data:
            self._data[self._head] = byte
            self._head += 1
        if self._head == len(self._data):
            self._mutable = False
            return True
        return False

    def append(self, object: Serializable) -> bool:
        """
        Return true and finalise if buffer was filled, raises BufferError if there
        is not sufficient room in the buffer or the buffer is already finalised.
        """
        return self.append_bytes(object.to_bytes())

    def to_bytes(self) -> bytes:
        if (self._mutable):
            raise BufferError(
                f"Buffer is not filled - {self._head}/{len(self._data)} bytes filled")
        return self._data

    def read_bytes(self, size: int) -> bytes:
        if (self._tail >= len(self._data)):
            raise BufferError("All data from this buffer has been read")
        if (self._tail >= self._head):
            raise BufferError("There is no remaining data to read")
        if (self._mutable):
            raise BufferError("Cannot read from incomplete buffer")
        start = self._tail
        self._tail += size
        return self._data[start:self._tail]

    def read_remaining(self) -> bytes:
        return self.read_bytes(self._head - self._tail)

    @staticmethod
    def from_bytes(data: bytes) -> Buffer:
        buffer = Buffer(len(data))
        buffer.append_bytes(data)
        return buffer
