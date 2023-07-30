from __future__ import annotations
from typing import TYPE_CHECKING
from airtouch2.protocol.at2.messages.SystemInfo import GroupInfo
from airtouch2.protocol.at2.messages import ChangeDamper, ToggleGroup
from airtouch2.common.interfaces import Publisher, Callback, add_callback
if TYPE_CHECKING:
    from airtouch2.at2.At2Client import At2Client


class At2Group(Publisher):
    info: GroupInfo

    def __init__(self, client: At2Client, info: GroupInfo):
        self.info = info

        self._client = client
        self._callbacks: list[Callback] = []

    def update(self, status: GroupInfo):
        self.info = status

        for func in self._callbacks:
            func()

    def add_callback(self, callback: Callback) -> Callback:
        return add_callback(callback, self._callbacks)

    async def inc_dec_damp(self, inc: bool):
        await self._client.send(ChangeDamper(self.info.number, inc))

    async def set_damp(self, new_damp: int):
        if new_damp < 0 or new_damp > 10:
            raise ValueError("Dampers can only be set from 0 to 10")
        # Set to 0 is equivalent to turning off
        if new_damp == 0:
            await self.turn_off()
        else:
            await self.turn_on()
            damp_diff = new_damp - self.info.damp
            inc = damp_diff > 0
            for i in range(abs(damp_diff)):
                await self.inc_dec_damp(inc)

    async def _turn_on_off(self, on: bool):
        if self.info.active != on:
            await self._client.send(ToggleGroup(self.info.number))

    async def turn_off(self):
        await self._turn_on_off(False)

    async def turn_on(self):
        await self._turn_on_off(True)

    def __str__(self):
        return str(self.info)
