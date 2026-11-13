from __future__ import annotations
from dataclasses import dataclass

from airtouch2.protocol.at2plus.conversions import temperature_from_value

# 0x2B is not in the published protocol document. Its layout was decoded from
# captures: a run of 4-byte records, one per sensor slot.
#   byte 0:    sensor id. 0x90 and 0x91 are consoles 1 and 2. 0x80-0x83 look
#              like zone sensors (not confirmed: no capture yet from a system
#              that has them fitted).
#   byte 1:    not decoded (0xFF on the console records)
#   bytes 2-3: temperature, same encoding as AC status. 0x07FF means no
#              reading, which temperature_from_value maps to None.
SENSOR_STATUS_LENGTH = 4


@dataclass
class SensorStatus:
    id: int
    temperature: float | None

    @staticmethod
    def from_bytes(repeat_data: bytes) -> SensorStatus:
        if len(repeat_data) != SENSOR_STATUS_LENGTH:
            raise ValueError(f"repeat_data must be {SENSOR_STATUS_LENGTH} bytes")
        return SensorStatus(repeat_data[0], temperature_from_value(int.from_bytes(repeat_data[2:4], 'big')))


class SensorStatusMessage:
    """Sensor status message (0x2B), broadcast by the console every 30 s or so"""
    statuses: list[SensorStatus]

    def __init__(self, statuses: list[SensorStatus]):
        self.statuses = statuses

    @staticmethod
    def from_bytes(subdata: bytes) -> SensorStatusMessage:
        return SensorStatusMessage(
            [SensorStatus.from_bytes(subdata[i:i+SENSOR_STATUS_LENGTH])
             for i in range(0, len(subdata), SENSOR_STATUS_LENGTH)]
        )
