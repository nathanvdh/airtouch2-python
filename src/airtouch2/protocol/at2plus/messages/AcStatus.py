
from __future__ import annotations
from dataclasses import dataclass
from airtouch2.protocol.at2plus.conversions import setpoint_from_value, temperature_from_value, value_from_setpoint, value_from_temperature
from airtouch2.protocol.at2plus.control_status_common import CONTROL_STATUS_SUBHEADER_LENGTH, ControlStatusSubType, SubDataLength, ControlStatusSubHeader
from airtouch2.protocol.at2plus.enums import AcFanSpeed, AcMode, AcPower
from airtouch2.protocol.at2plus.message_common import AddressMsgType, Header, MessageType, add_checksum_message_buffer, prime_message_buffer
from airtouch2.common.Buffer import Buffer
from airtouch2.common.interfaces import Serializable

AC_STATUS_LENGTH = 10


@dataclass
class AcStatus(Serializable):
    id: int
    power: AcPower
    mode: AcMode
    fan_speed: AcFanSpeed
    set_point: float | None
    temperature: float | None
    turbo: bool
    bypass: bool
    spill: bool
    timer: bool
    error: int

    def to_bytes(self) -> bytes:
        buffer = Buffer(AC_STATUS_LENGTH)
        buffer.append_bytes(
            bytes([
                ((self.power << 4) | self.id),
                ((self.mode << 4) | self.fan_speed),
                value_from_setpoint(self.set_point),
                self.turbo << 3 | self.bypass << 2 | self.spill << 1 | self.timer,
            ])
        )
        buffer.append_bytes(value_from_temperature(
            self.temperature).to_bytes(2, 'big'))
        buffer.append_bytes(self.error.to_bytes(2, 'big'))
        buffer.append_bytes(bytes([0, 0]))
        return buffer.to_bytes()

    @staticmethod
    def from_bytes(repeat_data: bytes) -> AcStatus:
        """Construct an AcStatus message from its 10-byte serial data"""
        if (len(repeat_data) != AC_STATUS_LENGTH):
            raise ValueError(f"repeat_data must be {AC_STATUS_LENGTH} bytes")
        number: int = repeat_data[0] & 0x0F
        power = AcPower.from_int((repeat_data[0] & 0xF0) >> 4)
        mode = AcMode.from_int((repeat_data[1] & 0xF0) >> 4)
        fan_speed = AcFanSpeed.from_int(repeat_data[1] & 0x0F)
        set_point: float | None = setpoint_from_value(repeat_data[2])
        turbo: bool = repeat_data[3] & 8 > 0
        bypass: bool = repeat_data[3] & 4 > 0
        spill: bool = repeat_data[3] & 2 > 0
        timer: bool = repeat_data[3] & 1 > 0
        temperature: float | None = temperature_from_value(
            int.from_bytes(repeat_data[4:6], 'big'))
        error: int = int.from_bytes(repeat_data[6:8], 'big')
        return AcStatus(number, power, mode, fan_speed, set_point, temperature, turbo, bypass, spill, timer, error)

    def __repr__(self) -> str:
        return f"""
            id: {self.id}
            power: {self.power}
            mode: {self.mode}
            fan_speed: {self.fan_speed}
            set_point: {self.set_point}
            temperature: {self.temperature}
            turbo: {self.turbo}
            bypass: {self.bypass}
            spill: {self.spill}
            timer: {self.timer}
            error: {self.error}
        """


class AcStatusMessage(Serializable):
    """AcStatus Message (can be response with repeat subdata or request with empty subdata)"""
    statuses: list[AcStatus]

    def __init__(self, statuses: list[AcStatus]):
        self.statuses = statuses

    @staticmethod
    def from_bytes(subdata: bytes) -> AcStatusMessage:
        return AcStatusMessage(
            [AcStatus.from_bytes(subdata[i:i+AC_STATUS_LENGTH])
             for i in range(0, len(subdata), AC_STATUS_LENGTH)]
        )

    def to_bytes(self) -> bytes:
        subheader = ControlStatusSubHeader(ControlStatusSubType.AC_STATUS, SubDataLength(
            0, len(self.statuses), AC_STATUS_LENGTH))
        buffer = prime_message_buffer(
            Header(
                AddressMsgType.NORMAL, MessageType.CONTROL_STATUS,
                CONTROL_STATUS_SUBHEADER_LENGTH + subheader.subdata_length.total()))
        buffer.append(subheader)
        for status in self.statuses:
            buffer.append(status)
        add_checksum_message_buffer(buffer)
        return buffer.to_bytes()
