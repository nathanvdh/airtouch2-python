from __future__ import annotations
from typing import TYPE_CHECKING
from airtouch2.protocol.at2plus.messages.AcControl import AcControlMessage, AcSettings
from airtouch2.common.interfaces import Callback
if TYPE_CHECKING:
    from airtouch2.at2plus.At2PlusClient import At2PlusClient
from asyncio import Event
from airtouch2.protocol.at2plus.enums import AcFanSpeed, AcPower, AcSetMode, AcSetPower
from airtouch2.protocol.at2plus.messages.AcAbilityMessage import AcAbility
from airtouch2.protocol.at2plus.messages.AcStatus import AcStatus


class At2PlusAircon:
    """
    A class that represents a single airtouch2+ AC unit.

    An At2PlusAircon is not 'ready' until it's AcAbility has been retrieved.

    While unready, mode and fan speed setter calls cannot be made as the unit's supported modes are unknown.
    """

    def __init__(self, status: AcStatus, client: At2PlusClient):
        self.status: AcStatus = status
        self.ability: AcAbility | None = None
        self._ready: Event = Event()
        self._client: At2PlusClient = client
        self._callbacks: list[Callback] = []

    async def _set_power(self, power: AcSetPower):
        settings = AcSettings(self.status.id, power, AcSetMode.UNCHANGED, AcFanSpeed.UNCHANGED, None)
        await self._client.send(AcControlMessage([settings]))

    async def toggle(self):
        await self._set_power(AcSetPower.TOGGLE)

    async def turn_on(self):
        await self._set_power(AcSetPower.ON)

    async def turn_off(self):
        await self._set_power(AcSetPower.OFF)

    def is_on(self) -> bool:
        return self.status.power == AcPower.ON

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

    def add_callback(self, callback: Callback) -> Callback:
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
