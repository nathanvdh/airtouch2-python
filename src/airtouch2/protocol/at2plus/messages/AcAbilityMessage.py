
from __future__ import annotations
from dataclasses import dataclass
from enum import IntEnum
from airtouch2.protocol.at2plus.enums import AcFanSpeed, AcSetMode
from airtouch2.protocol.at2plus.extended_common import EXTENDED_SUBHEADER_LENGTH, ExtendedMessageSubType, ExtendedSubHeader
from airtouch2.protocol.at2plus.message_common import AddressMsgType, Header, MessageType, add_checksum_message_buffer, prime_message_buffer
from airtouch2.common.interfaces import Serializable


class AcAbilitySubDataLength(IntEnum):
    V1 = 24
    V1_1 = 26


@dataclass
class SetpointLimits:
    min: int
    max: int

    def __repr__(self) -> str:
        return f"""
        min: {self.min}
        max: {self.min}
        """


@dataclass
class DualSetpointLimits:
    cool: SetpointLimits
    heat: SetpointLimits

    def __repr__(self) -> str:
        return f"""
        cool: {self.cool}
        heat: {self.heat}
        """


@dataclass
class AcAbility(Serializable):
    ac_id: int
    name: str
    start_group: int
    group_count: int
    supported_modes: list[AcSetMode]
    supported_fan_speeds: list[AcFanSpeed]
    setpoint_limits: SetpointLimits | DualSetpointLimits

    @staticmethod
    def from_bytes(data: bytes) -> AcAbility:
        if len(data) != AcAbilitySubDataLength.V1 and len(data) != AcAbilitySubDataLength.V1_1:
            raise ValueError(
                f"Invalid AcAbility length, should be {AcAbilitySubDataLength.V1} or {AcAbilitySubDataLength.V1_1}, got: {len(data)}")
        ac_id = data[0]
        following_data_length = data[1]
        if following_data_length != len(data) - 2:
            raise ValueError(
                f"Data length specified in message does not match received data length: specified {following_data_length}, got {len(data) - 2}")

        name = data[2:18].decode('ascii').split("\x00")[0]
        start_group = data[18]
        group_count = data[19]
        supported_modes = []
        for i in range(5):
            # this loop exploits the fact that the support bits are in the same order as the enum values
            if (data[20] & (1 << i)) > 0:
                supported_modes.append(AcSetMode.from_int(i))
        supported_fan_speeds = []
        for i in range(7):
            # ditto
            if (data[21] & (1 << i)) > 0:
                supported_fan_speeds.append(AcFanSpeed.from_int(i))

        set_point_limits = SetpointLimits(data[22], data[23])
        if len(data) == AcAbilitySubDataLength.V1_1:
            set_point_limits = DualSetpointLimits(set_point_limits, SetpointLimits(data[24], data[25]))

        return AcAbility(
            ac_id, name, start_group, group_count, supported_modes, supported_fan_speeds, set_point_limits)

    def to_bytes(self) -> bytes:
        data = bytes([self.ac_id, (AcAbilitySubDataLength.V1_1 - 2) if isinstance(self.setpoint_limits, DualSetpointLimits) else (
            AcAbilitySubDataLength.V1 - 2)]) + self.name.encode("ascii") + bytes(16-len(self.name)) + bytes([self.start_group, self.group_count])
        supported_modes_val: int = 0
        for mode in self.supported_modes:
            supported_modes_val |= 1 << mode
        supported_speeds_val: int = 0
        for speed in self.supported_fan_speeds:
            supported_speeds_val |= 1 << speed
        data += bytes([supported_modes_val, supported_speeds_val])
        if isinstance(self.setpoint_limits, DualSetpointLimits):
            data += bytes([self.setpoint_limits.cool.min, self.setpoint_limits.cool.max,
                          self.setpoint_limits.heat.min, self.setpoint_limits.heat.max])
        elif isinstance(self.setpoint_limits, SetpointLimits):
            data += bytes([self.setpoint_limits.min, self.setpoint_limits.max])

        return data

    def __repr__(self) -> str:
        return f"""
        id: {self.ac_id}
        name: {self.name}
        start_group: {self.start_group}
        group_count: {self.group_count}
        supported_modes: {self.supported_modes}
        supported_fan_speeds: {self.supported_fan_speeds}
        setpoint_limits: {self.setpoint_limits}
        """


class AcAbilityMessage(Serializable):
    abilities: list[AcAbility]

    def __init__(self, abilities: list[AcAbility]):
        self.abilities = abilities

    @staticmethod
    def from_bytes(subdata: bytes) -> AcAbilityMessage:
        ac_ability_list = []
        # peek the protocol version, assume they all match
        length = AcAbilitySubDataLength(subdata[1] + 2)
        # Iterate over subdata in steps of AC_ABILITY_LENGTH
        for i in range(0, len(subdata), length):
            subdata_slice = subdata[i:i+length]
            ac_ability = AcAbility.from_bytes(subdata_slice)
            ac_ability_list.append(ac_ability)
            break  # ! Ignores the other ACs in the list for now
        ac_ability_message = AcAbilityMessage(ac_ability_list)
        return ac_ability_message

    def to_bytes(self) -> bytes:
        length = AcAbilitySubDataLength.V1 if isinstance(
            self.abilities[0].setpoint_limits, SetpointLimits) else AcAbilitySubDataLength.V1_1
        buffer = prime_message_buffer(
            Header(
                AddressMsgType.EXTENDED, MessageType.EXTENDED, EXTENDED_SUBHEADER_LENGTH +
                length * len(self.abilities)))
        buffer.append(ExtendedSubHeader(ExtendedMessageSubType.ABILITY))
        for ability in self.abilities:
            buffer.append(ability)
        add_checksum_message_buffer(buffer)
        return buffer.to_bytes()


class RequestAcAbilityMessage(Serializable):
    ac_id: int | None

    def __init__(self, ac_id: int | None = None):
        self.ac_id = ac_id

    def to_bytes(self) -> bytes:
        buffer = prime_message_buffer(
            Header(
                AddressMsgType.EXTENDED, MessageType.EXTENDED, EXTENDED_SUBHEADER_LENGTH +
                (1 if self.ac_id is not None else 0)))
        buffer.append(ExtendedSubHeader(ExtendedMessageSubType.ABILITY))
        if self.ac_id is not None:
            buffer.append_bytes(bytes([self.ac_id]))
        add_checksum_message_buffer(buffer)
        return buffer.to_bytes()
