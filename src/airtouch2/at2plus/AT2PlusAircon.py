from __future__ import annotations
from typing import TYPE_CHECKING, Callable

from airtouch2.protocol.at2plus.messages.AcControl import AcControlMessage, AcSettings
if TYPE_CHECKING:
    from airtouch2.at2plus.AT2PlusClient import At2PlusClient
from asyncio import Event
from airtouch2.protocol.at2plus.enums import AcFanSpeed, AcSetMode, AcSetPower
from airtouch2.protocol.at2plus.messages.AcAbilityMessage import AcAbility
from airtouch2.protocol.at2plus.messages.AcStatus import AcStatus


class At2PlusAircon:
    """
    A class that represents a single airtouch2+ AC unit.

    An At2PlusAircon is not 'ready' until it's AcAbility has been retrieved.

    While unready, mode and fan speed setter calls cannot be made as the unit's supported modes are unknown.
    """
    status: AcStatus
    ability: AcAbility | None

    _ready: Event
    _client: At2PlusClient
    _callbacks: list[Callable] = []

    def __init__(self, status: AcStatus, client: At2PlusClient):
        self.status = status
        self.ability = None
        self._ready = Event()
        self._client = client

    async def _set_power(self, power: AcSetPower):
        settings = AcSettings(self.status.id, power, AcSetMode.UNCHANGED, AcFanSpeed.UNCHANGED, None)
        await self._client.send(AcControlMessage([settings]))

    async def toggle(self):
        await self._set_power(AcSetPower.TOGGLE)

    async def on(self):
        await self._set_power(AcSetPower.ON)

    async def off(self):
        await self._set_power(AcSetPower.OFF)

    async def set_mode(self, mode: AcSetMode):
        settings = AcSettings(self.status.id, AcSetPower.UNCHANGED, mode, AcFanSpeed.UNCHANGED, None)
        await self._client.send(AcControlMessage([settings]))

    async def set_fan_speed(self, speed: AcFanSpeed):
        settings = AcSettings(self.status.id, AcSetPower.UNCHANGED, AcSetMode.UNCHANGED, speed, None)
        await self._client.send(AcControlMessage([settings]))

    async def set_setpoint(self, setpoint: float):
        settings = AcSettings(self.status.id, AcSetPower.UNCHANGED, AcSetMode.UNCHANGED, AcFanSpeed.UNCHANGED, setpoint)
        await self._client.send(AcControlMessage([settings]))

    async def wait_until_ready(self) -> None:
        await self._ready.wait()

    def add_callback(self, callback: Callable):
        self._callbacks.append(callback)

        def remove_callback() -> None:
            if callback in self._callbacks:
                self._callbacks.remove(callback)

        return remove_callback

    def _update_status(self, status: AcStatus):
        self.status = status
        for callback in self._callbacks:
            callback()

    def _set_ability(self, ability: AcAbility):
        self.ability = ability
        self._ready.set()
