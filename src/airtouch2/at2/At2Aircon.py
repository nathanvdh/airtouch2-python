from __future__ import annotations
import asyncio
import logging
from itertools import compress
from typing import TYPE_CHECKING, Callable
from airtouch2.common.interfaces import Callback
from airtouch2.protocol.at2.conversions import brand_from_gateway_id, fan_speed_from_val, supported_fan_speeds, val_from_fan_speed
if TYPE_CHECKING:
    from airtouch2.at2.At2Client import At2Client
from airtouch2.protocol.at2.enums import ACFanSpeedReference, ACBrand, ACMode
from airtouch2.protocol.at2.messages import ChangeSetTemperature, ResponseMessage, SetFanSpeed, SetMode, ToggleAc
from airtouch2.protocol.at2.lookups import GATEWAYID_BRAND_LOOKUP

_LOGGER = logging.getLogger(__name__)


class At2Aircon:
    number: int
    on: bool
    safety: bool
    error: bool
    turbo: bool
    spill: bool
    error_code: int
    measured_temp: int
    set_temp: int
    brand: ACBrand
    gateway_id: int
    mode: ACMode
    supported_fan_speeds: list[ACFanSpeedReference]
    fan_speed: ACFanSpeedReference

    def __init__(self, number: int, client: At2Client, response_message: ResponseMessage):
        self.number: int = number
        self._client: At2Client = client
        self._callbacks: list[Callable] = []
        if response_message:
            self.update(response_message)
        else:
            raise ValueError("Null response message provided")

    def update(self, response_message: ResponseMessage) -> None:
        self.system_name = response_message.system_name

        # Flags
        self.on = response_message.ac_active[self.number]
        self.safety = response_message.ac_safety[self.number]
        self.error = response_message.ac_error[self.number]
        self.turbo = response_message.ac_turbo[self.number]
        self.spill = response_message.ac_spill[self.number]

        # Error code
        self.error_code = response_message.ac_error_code[self.number]

        # Temperatures
        self.measured_temp = response_message.ac_measured_temp[self.number]
        if (self.measured_temp <= 0):
            self.measured_temp = response_message.touchpad_temp
        self.set_temp = response_message.ac_set_temp[self.number]

        # Brand
        brand = response_message.ac_brand[self.number]
        gateway_id = response_message.ac_gateway_id[self.number]
        # Brand based on gateway ID takes priority according to app smali
        gateway_based_brand = brand_from_gateway_id(gateway_id)
        if gateway_based_brand is not None:
            self.brand = gateway_based_brand
        else:
            self.brand = brand

        # Modes
        self.mode = response_message.ac_mode[self.number]
        num_fan_speeds = response_message.ac_num_fan_speeds[self.number]
        fan_speed_val = response_message.ac_fan_speed[self.number]
        self.supported_fan_speeds = supported_fan_speeds(self.brand, num_fan_speeds, gateway_id)
        self.fan_speed = fan_speed_from_val(self.supported_fan_speeds, fan_speed_val)

        # TODO: Handle this?
        if brand == ACBrand.NONE and gateway_id == 0:
            _LOGGER.warning(f"AC{self.number} appears disconnected from airtouch")

        self.name = response_message.ac_name[self.number]

        for callback in self._callbacks:
            callback()

    def add_callback(self, func: Callback) -> Callback:
        self._callbacks.append(func)

        def remove_callback() -> None:
            if func in self._callbacks:
                self._callbacks.remove(func)

        return remove_callback

    async def inc_dec_set_temp(self, inc: bool):
        await self._client.send(ChangeSetTemperature(self.number, inc))

    async def set_set_temp(self, new_temp: int):
        temp_diff = new_temp - self.set_temp
        inc = temp_diff > 0
        for i in range(abs(temp_diff)):
            await self.inc_dec_set_temp(inc)
            await asyncio.sleep(0.1)  # server doesn't like being spammed, 0.1s is faster than waiting for response

    async def turn_off(self):
        await self._turn_on_off(False)

    async def turn_on(self):
        await self._turn_on_off(True)

    async def set_fan_speed(self, fan_speed: ACFanSpeedReference):
        if fan_speed in self.supported_fan_speeds:
            await self._client.send(SetFanSpeed(self.number, val_from_fan_speed(self.supported_fan_speeds, fan_speed)))
        else:
            _LOGGER.warning(f"Cannot set fan speed to unsupported value {fan_speed}")

    async def set_mode(self, mode: ACMode):
        await self._client.send(SetMode(self.number, mode))

    def get_status_strings(self):
        flags = [self.error, self.safety, self.spill, self.turbo]
        flag_names = ['ERROR', 'SAFETY', 'SPILL', 'TURBO']
        statuses = list(compress(flag_names, flags))
        if not statuses:
            statuses.append('NORMAL')
        return statuses

    async def _turn_on_off(self, on: bool):
        if self.on != on:
            await self._client.send(ToggleAc(self.number))

    def __str__(self):
        return f"""
        System Name:\t\t{self.system_name}
        AC Number:\t\t{self.number}
        AC Name:\t\t{self.name}
        On:\t\t\t{self.on}
        Status:\t\t\t{self.get_status_strings()}
        Error Code:\t\t{self.error_code}
        Mode:\t\t\t{self.mode}
        Fan Speed:\t\t{self.fan_speed}
        Supported Speeds:\t{[s.name for s in self.supported_fan_speeds]}
        Measured Temp:\t\t{self.measured_temp}
        Set Temp:\t\t{self.set_temp}
        Brand:\t\t\t{self.brand}
        """
