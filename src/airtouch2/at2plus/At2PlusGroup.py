from __future__ import annotations
from typing import TYPE_CHECKING

from airtouch2.common.interfaces import Callback
from airtouch2.protocol.at2plus.enums import GroupPower, GroupSetDamper, GroupSetPower
from airtouch2.protocol.at2plus.messages.GroupControl import GroupControlMessage, GroupSettings
from airtouch2.protocol.at2plus.messages.GroupStatus import GroupStatus

if TYPE_CHECKING:
    from airtouch2.at2plus.At2PlusClient import At2PlusClient


class At2PlusGroup:
    """
    A class that represents a single airtouch2+ group.

    """

    def __init__(self, status: GroupStatus, client: At2PlusClient):
        self.status = status
        self.name: str | None = None
        self._client = client
        self._callbacks: list[Callback] = []

    async def _set_power(self, power: GroupSetPower, damp: int | None = None):
        settings = GroupSettings(self.status.id, GroupSetDamper.UNCHANGED, power, damp)
        await self._client.send(GroupControlMessage([settings]))

    async def turn_on(self, damp: int | None = None):
        await self._set_power(GroupSetPower.ON, damp)

    async def turn_off(self):
        await self._set_power(GroupSetPower.OFF)

    def is_on(self) -> bool:
        return self.status.power != GroupPower.OFF

    async def set_damp(self, new_damp: int):
        settings = GroupSettings(self.status.id, GroupSetDamper.SET, GroupSetPower.UNCHANGED, new_damp)
        await self._client.send(GroupControlMessage([settings]))

    async def set_turbo(self):
        settings = GroupSettings(self.status.id, GroupSetDamper.UNCHANGED, GroupSetPower.TURBO)
        await self._client.send(GroupControlMessage([settings]))

    def add_callback(self, callback: Callback) -> Callback:
        self._callbacks.append(callback)

        def remove_callback() -> None:
            if callback in self._callbacks:
                self._callbacks.remove(callback)

        return remove_callback

    def _update_status(self, status: GroupStatus):
        self.status = status
        for callback in self._callbacks:
            callback()

    def _update_name(self, name: str):
        self.name = name
        for callback in self._callbacks:
            callback()

    def __repr__(self):
        return str(self.status) + f"""
          name: {self.name if self.name is not None else f"Group {self.status.id}"}
"""