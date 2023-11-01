from __future__ import annotations
from dataclasses import dataclass

from airtouch2.common.interfaces import Serializable
from airtouch2.protocol.at2plus.control_status_common import CONTROL_STATUS_SUBHEADER_LENGTH, ControlStatusSubHeader, ControlStatusSubType, SubDataLength
from airtouch2.protocol.at2plus.enums import GroupPower
from airtouch2.common.Buffer import Buffer
from airtouch2.protocol.at2plus.message_common import AddressMsgType, Header, MessageType, add_checksum_message_buffer, prime_message_buffer

GROUP_STATUS_LENGTH = 8


@dataclass
class GroupStatus(Serializable):
    id: int
    power: GroupPower
    damp: int
    supports_turbo: bool
    spill_active: bool

    def to_bytes(self) -> bytes:
        buffer = Buffer(GROUP_STATUS_LENGTH)
        buffer.append_bytes(
            bytes([
                (self.power << 6) | self.id,
                self.damp,
                0, 0, 0, 0,
                self.supports_turbo << 7 | self.spill_active << 1,
                0
            ])
        )
        return buffer.to_bytes()

    @staticmethod
    def from_bytes(repeat_data: bytes) -> GroupStatus:
        if (len(repeat_data) != GROUP_STATUS_LENGTH):
            raise ValueError(f"repeat_data must be {GROUP_STATUS_LENGTH} bytes")
        id = repeat_data[0] & 0x3F
        power = GroupPower((repeat_data[0] >> 6) & 3)
        damp = repeat_data[1] & 0x7F
        supports_turbo = ((repeat_data[6] >> 7) & 1) > 0
        spill_active = ((repeat_data[6] >> 1) & 1) > 0

        return GroupStatus(id, power, damp, supports_turbo, spill_active)

    def __repr__(self) -> str:
        return f"""
            id: {self.id}
         power: {self.power}
        damper: {self.damp}%
supports_turbo: {self.supports_turbo}
  spill_active: {self.spill_active}"""


class GroupStatusMessage(Serializable):
    """GroupStatus message (can be response with repeat subdata or request with empty subdata)"""
    statuses: list[GroupStatus]

    def __init__(self, statuses: list[GroupStatus]):
        self.statuses = statuses

    @staticmethod
    def from_bytes(subdata: bytes) -> GroupStatusMessage:
        return GroupStatusMessage(
            [GroupStatus.from_bytes(subdata[i:i+GROUP_STATUS_LENGTH])
             for i in range(0, len(subdata), GROUP_STATUS_LENGTH)]
        )

    def to_bytes(self) -> bytes:
        subheader = ControlStatusSubHeader(ControlStatusSubType.GROUP_STATUS,
                                           SubDataLength(0, len(self.statuses),
                                                         GROUP_STATUS_LENGTH))
        buffer = prime_message_buffer(
            Header(
                AddressMsgType.NORMAL, MessageType.CONTROL_STATUS,
                CONTROL_STATUS_SUBHEADER_LENGTH + subheader.subdata_length.total()))
        buffer.append(subheader)
        for status in self.statuses:
            buffer.append(status)
        add_checksum_message_buffer(buffer)
        return buffer.to_bytes()
