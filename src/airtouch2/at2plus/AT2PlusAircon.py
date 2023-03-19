
from typing import Callable
from airtouch2.protocol.at2plus.enums import AcFanSpeed, AcSetMode
from airtouch2.protocol.at2plus.messages.AcAbilityMessage import AcAbility
from airtouch2.protocol.at2plus.messages.AcStatus import AcStatus

class At2PlusAircon:
    status: AcStatus
    ability: AcAbility
    _callbacks: list[Callable]

    def __init__(self, ability: AcAbility, status: AcStatus):
        self.ability = ability
        self.status = status

    def toggle(self):
        pass

    def on(self):
        pass

    def off(self):
        pass

    def set_mode(self, mode: AcSetMode):
        pass

    def set_fan_speed(self, speed: AcFanSpeed):
        pass

    def set_setpoint(self, setpoint: float):
        pass

    def update_status(self, status: AcStatus):
        self.status = status
        for callback in self._callbacks:
            callback()
    
    def add_callback(self, callback: Callable):
        self._callbacks.append(callback)

        def remove_callback() -> None:
            if callback in self._callbacks:
                self._callbacks.remove(callback)

        return remove_callback