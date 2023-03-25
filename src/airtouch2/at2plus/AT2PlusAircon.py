from __future__ import annotations
from typing import TYPE_CHECKING, Callable
if TYPE_CHECKING:
    from airtouch2.at2plus.AT2PlusClient import At2PlusClient
from asyncio import Event
from airtouch2.protocol.at2plus.enums import AcFanSpeed, AcSetMode
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

    _callbacks: list[Callable] = []

    def __init__(self, status: AcStatus, client: At2PlusClient):
        self.status = status
        self.ability = None
        self._ready = Event()
        self._client = client

    def toggle(self):
        # send msg with client
        pass

    def on(self):
        # send msg with client
        pass

    def off(self):
        # send msg with client
        pass

    def set_mode(self, mode: AcSetMode):
        # send msg with client
        pass

    def set_fan_speed(self, speed: AcFanSpeed):
        # send msg with client
        pass

    def set_setpoint(self, setpoint: float):
        # send msg with client
        pass

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
        if (self.ability is not None):
            raise RuntimeError("AcAbility should only be set once per unit")
        self.ability = ability
        self._ready.set()
