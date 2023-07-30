from __future__ import annotations
import asyncio
import logging
from typing import TYPE_CHECKING, Callable
from airtouch2.common.interfaces import Publisher, Callback, add_callback
if TYPE_CHECKING:
    from airtouch2.at2.At2Client import At2Client
from airtouch2.protocol.at2.enums import ACFanSpeed, ACBrand, ACMode
from airtouch2.protocol.at2.messages import ChangeSetTemperature, SetFanSpeed, SetMode, ToggleAc
from airtouch2.protocol.at2.messages.SystemInfo import AcInfo

_LOGGER = logging.getLogger(__name__)


class At2Aircon(Publisher):
    info: AcInfo

    def __init__(self, client: At2Client, info: AcInfo):
        self._client: At2Client = client
        self._callbacks: list[Callable] = []
        self.info = info

    def update(self, info: AcInfo) -> None:
        self.info = info

        for callback in self._callbacks:
            callback()

    def add_callback(self, callback: Callback) -> Callback:
        return add_callback(callback, self._callbacks)

    async def inc_dec_set_temp(self, inc: bool):
        await self._client.send(ChangeSetTemperature(self.info.number, inc))

    async def set_set_temp(self, new_temp: int):
        temp_diff = new_temp - self.info.set_temp
        inc = temp_diff > 0
        for i in range(abs(temp_diff)):
            await self.inc_dec_set_temp(inc)
            await asyncio.sleep(0.1)  # server doesn't like being spammed, 0.1s is faster than waiting for response.

    async def turn_off(self):
        await self._turn_on_off(False)

    async def turn_on(self):
        await self._turn_on_off(True)

    async def set_fan_speed(self, fan_speed: ACFanSpeed):
        if fan_speed in self.info.supported_fan_speeds:
            await self._client.send(SetFanSpeed(self.info.number, self.info.supported_fan_speeds, fan_speed))
        else:
            _LOGGER.warning(f"Cannot set fan speed to unsupported value {fan_speed}")

    async def set_mode(self, mode: ACMode):
        await self._client.send(SetMode(self.info.number, mode))

    async def _turn_on_off(self, on: bool):
        if self.info.active != on:
            await self._client.send(ToggleAc(self.info.number))

    def __str__(self):
        return str(self.info)
