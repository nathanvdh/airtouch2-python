
from __future__ import annotations
from asyncio import StreamReader
from dataclasses import dataclass
from airtouch2.protocol.at2plus.enums import AcFanSpeed, AcMode
from airtouch2.protocol.at2plus.extended_common import SUBHEADER_LENGTH, ExtendedMessageSubType, ExtendedSubHeader
from airtouch2.protocol.at2plus.message_common import Address, Header, MessageType, add_checksum_message_buffer, prime_message_buffer
from airtouch2.protocol.interfaces import Serializable

AC_ABILITY_LENGTH = 24


@dataclass
class AcAbility(Serializable):
    number: int
    name: str
    start_group: int
    group_count: int
    supported_modes: list[AcMode]
    supported_fan_speeds: list[AcFanSpeed]
    min_setpoint: int
    max_setpoint: int

    @staticmethod
    def from_bytes(data: bytes) -> AcAbility:
        if len(data) != AC_ABILITY_LENGTH:
            raise ValueError(f"Data must be {AC_ABILITY_LENGTH} bytes")
        number = data[0]
        # length = data[1]
        name = data[2:18].decode('ascii').split("\x00")[0]
        start_group = data[18]
        group_count = data[19]
        supported_modes = []
        for i in range(5):
            # this loop exploits the fact that the support bits are in the same order as the enum values
            if (data[20] & (1 << i)) > 0:
                supported_modes.append(AcMode.from_int(i))
        supported_fan_speeds = []
        for i in range(7):
            # ditto
            if (data[21] & (1 << i)) > 0:
                supported_fan_speeds.append(AcFanSpeed.from_int(i))
        min_setpoint = data[22]
        max_setpoint = data[23]
        return AcAbility(number, name, start_group, group_count, supported_modes, supported_fan_speeds, min_setpoint, max_setpoint)

    def to_bytes(self) -> bytes:
        data = bytes([self.number, 22]) + self.name.encode("ascii") + \
            bytes(16-len(self.name)) + \
            bytes([self.start_group, self.group_count])
        supported_modes_val: int = 0
        for mode in self.supported_modes:
            supported_modes_val |= 1 << mode
        supported_speeds_val: int = 0
        for speed in self.supported_fan_speeds:
            supported_speeds_val |= 1 << speed
        data += bytes([supported_modes_val, supported_speeds_val,
                      self.min_setpoint, self.max_setpoint])
        return data

    def __repr__(self) -> str:
        return f"""
        number: {self.number}
        name: {self.name}
        start_group: {self.start_group}
        group_count: {self.group_count}
        supported_modes: {self.supported_modes}
        supported_fan_speeds: {self.supported_fan_speeds}
        min_setpoint: {self.min_setpoint}
        max_setpoint: {self.max_setpoint}
        """


class AcAbilityMessage(Serializable):
    abilities: list[AcAbility]

    def __init__(self, abilities: list[AcAbility]):
        self.abilities = abilities

    @staticmethod
    def from_bytes(subdata: bytes) -> AcAbilityMessage:
        return AcAbilityMessage([AcAbility.from_bytes(subdata[i:i+AC_ABILITY_LENGTH]) for i in range(0, len(subdata), AC_ABILITY_LENGTH)])

    def to_bytes(self) -> bytes:
        buffer = prime_message_buffer(Header(
            Address.EXTENDED, MessageType.EXTENDED, SUBHEADER_LENGTH + AC_ABILITY_LENGTH * len(self.abilities)))
        buffer.append(ExtendedSubHeader(ExtendedMessageSubType.ABILITY))
        for ability in self.abilities:
            buffer.append(ability)
        add_checksum_message_buffer(buffer)
        return buffer.to_bytes()


class RequestAcAbilityMessage(Serializable):
    ac_number: int | None

    def __init__(self, ac_number: int | None = None):
        self.ac_number = ac_number

    def to_bytes(self) -> bytes:
        buffer = prime_message_buffer(Header(
            Address.EXTENDED, MessageType.EXTENDED, SUBHEADER_LENGTH + (1 if self.ac_number is not None else 0)))
        buffer.append(ExtendedSubHeader(ExtendedMessageSubType.ABILITY))
        if self.ac_number is not None:
            buffer.append_bytes(bytes([self.ac_number]))
        add_checksum_message_buffer(buffer)
        return buffer.to_bytes()
