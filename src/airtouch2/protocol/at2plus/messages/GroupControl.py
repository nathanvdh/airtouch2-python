from __future__ import annotations
# from dataclasses import dataclass
from airtouch2.common.Buffer import Buffer

from airtouch2.common.interfaces import Serializable
from airtouch2.protocol.at2plus.constants import Limits
from airtouch2.protocol.at2plus.control_status_common import CONTROL_STATUS_SUBHEADER_LENGTH, ControlStatusSubHeader, ControlStatusSubType, SubDataLength
from airtouch2.protocol.at2plus.enums import GroupSetDamper, GroupSetPower
from airtouch2.protocol.at2plus.message_common import AddressMsgType, Header, MessageType, add_checksum_message_buffer, prime_message_buffer


GROUP_SETTINGS_LENGTH = 4


class GroupSettings(Serializable):
    id: int
    damp_mode: GroupSetDamper
    power: GroupSetPower
    damp: int | None

    def __init__(self, group_id: int, damp_mode: GroupSetDamper, power: GroupSetPower, damp: int | None = None):
        if damp is not None:
            if not 0 <= damp <= 100:
                raise ValueError(f"Damper percentage must be from 0 to 100")
        if not 0 <= group_id < Limits.MAX_GROUPS:
            raise ValueError(f'Group ID must be from 0 to {Limits.MAX_GROUPS-1}')
        self.id = group_id
        self.damp_mode = damp_mode
        self.power = power
        self.damp = damp

    def to_bytes(self) -> bytes:
        buffer = Buffer(GROUP_SETTINGS_LENGTH)
        buffer.append_bytes(
            bytes([
                self.id,
                (self.damp_mode << 5) | (self.power),
                self.damp if self.damp is not None else 255,
                0
            ])
        )
        return buffer.to_bytes()

    @staticmethod
    def from_bytes(repeat_data: bytes) -> GroupSettings:
        if (len(repeat_data) != GROUP_SETTINGS_LENGTH):
            raise ValueError(f"repeat_data must be {GROUP_SETTINGS_LENGTH} bytes")
        id = repeat_data[0] & 0x0F
        damp_mode = GroupSetDamper.from_int((repeat_data[1] >> 5) & 0x07)
        power = GroupSetPower.from_int((repeat_data[1]) & 0x07)
        damp = repeat_data[2] if 0 <= repeat_data[2] <= 100 else None

        return GroupSettings(id, damp_mode, power, damp)


class GroupControlMessage(Serializable):
    settings: list[GroupSettings]

    def __init__(self, settings: list[GroupSettings]):
        self.settings = settings

    def to_bytes(self) -> bytes:
        subheader = ControlStatusSubHeader(ControlStatusSubType.GROUP_CONTROL, SubDataLength(
            0, len(self.settings), GROUP_SETTINGS_LENGTH))
        buffer = prime_message_buffer(Header(AddressMsgType.NORMAL, MessageType.CONTROL_STATUS,
                                             CONTROL_STATUS_SUBHEADER_LENGTH + subheader.subdata_length.total()))
        buffer.append(subheader)
        for setting in self.settings:
            buffer.append(setting)
        add_checksum_message_buffer(buffer)
        return buffer.to_bytes()
