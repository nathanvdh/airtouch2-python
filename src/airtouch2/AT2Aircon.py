from __future__ import annotations
import logging
from itertools import compress
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from airtouch2.AT2Client import AT2Client
from airtouch2.protocol.enums import ACFanSpeedReference, ACBrand, ACMode
from airtouch2.protocol.messages import ChangeSetTemperature, ResponseMessage, SetFanSpeed, SetMode, ToggleAC
from airtouch2.protocol.lookups import GATEWAYID_BRAND_LOOKUP

OPEN_ISSUE_TEXT = "please open an issue and detail your system to me:\n\thttps://github.com/nathanvdh/airtouch2-python/issues/new"

_LOGGER = logging.getLogger(__name__)
class AT2Aircon:
    def __init__(self, number: int, client: AT2Client, response_message: ResponseMessage):
        self.number: int = number
        self._client: AT2Client = client
        if response_message:
            self.update(response_message)
        else:
            raise ValueError("Null response message provided")

    # TODO: read through app source code more and do this more properly
    # Currently I'm assuming:
    #   4 speed is always LOW, MED, HIGH, POWERFUL (EXCEPT for fujitsus with 4 speeds)
    #   3 speed is always LOW, MED, HIGH
    #   2 speed is always LOW, HIGH
    #   Daikins have no Auto
    #   Gateway ID 0x14 has no Auto
    #   Gateway IDs 0xFF with 3 speed have no Auto
    # These are based on the app decompiled code
    def _set_supported_fan_speeds(self, num_supported_speeds: int, gateway_id: int):
        all_speeds: list[ACFanSpeedReference] = list(ACFanSpeedReference._member_map_.values())

        if self.brand == ACBrand.FUJITSU and num_supported_speeds == 4:
            self.supported_fan_speeds = all_speeds[:5]
            return
        # Check cases that don't support Auto mode
        if (self.brand == ACBrand.DAIKIN or (gateway_id == 0xFF and num_supported_speeds == 3) or gateway_id == 0x14):
            self.supported_fan_speeds = []
        else:
            self.supported_fan_speeds = [ACFanSpeedReference.AUTO]

        if num_supported_speeds > 2:
            self.supported_fan_speeds += all_speeds[2:2+num_supported_speeds]
        elif num_supported_speeds == 2:
            self.supported_fan_speeds += [ACFanSpeedReference.LOW, ACFanSpeedReference.HIGH]
        elif num_supported_speeds < 2:
            _LOGGER.warning(f"AC{self.number} reports less than 2 supported fan speeds, this is unusual - " + OPEN_ISSUE_TEXT)

    def _set_fan_speed_from_val(self, speed_val: int):
        if speed_val < 5:
            # Units with no Auto speed still start with low = 1
            if ACFanSpeedReference.AUTO not in self.supported_fan_speeds:
                speed_val -= 1
            self.fan_speed = self.supported_fan_speeds[speed_val]
        else:
            self.fan_speed = ACFanSpeedReference.AUTO

    def _get_speed_val_from_speed(self, fan_speed: ACFanSpeedReference):
        speed_val = self.supported_fan_speeds.index(fan_speed)
        # Units with no Auto speed still start with low = 1
        if ACFanSpeedReference.AUTO not in self.supported_fan_speeds:
            speed_val += 1
        return speed_val

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
        # Brand based on gateway ID takes priority
        if gateway_id:
            if gateway_id not in GATEWAYID_BRAND_LOOKUP:
                _LOGGER.warning(f"AC{self.number} has an unfamiliar gateway ID: {hex(gateway_id)} - " + OPEN_ISSUE_TEXT + "\nInclude the gateway ID shown above")
                self.brand = brand
            else:
                self.brand = GATEWAYID_BRAND_LOOKUP[gateway_id]
        else:
            self.brand = brand

        # Modes
        self.mode = response_message.ac_mode[self.number]
        num_fan_speeds = response_message.ac_num_fan_speeds[self.number]
        fan_speed_val = response_message.ac_fan_speed[self.number]
        self._set_supported_fan_speeds(num_fan_speeds, gateway_id)
        self._set_fan_speed_from_val(fan_speed_val)

        # TODO: Handle this?
        if brand == ACBrand.NONE and gateway_id == 0:
            _LOGGER.warning(f"AC{self.number} appears disconnected from airtouch")

        self.name = response_message.ac_name[self.number]

    def inc_dec_set_temp(self, inc: bool):
        self._client.send_command(ChangeSetTemperature(self.number, inc))

    def set_set_temp(self, new_temp: int):
        temp_diff = new_temp - self.set_temp
        inc = temp_diff > 0
        for i in range(abs(temp_diff)):
            self.inc_dec_set_temp(inc)

    def _turn_on_off(self, on: bool):
        if self.on != on:
            self._client.send_command(ToggleAC(self.number))

    def turn_off(self):
        self._turn_on_off(False)

    def turn_on(self):
        self._turn_on_off(True)

    def set_fan_speed(self, fan_speed: ACFanSpeedReference):
        if fan_speed in self.supported_fan_speeds:
            self._client.send_command(SetFanSpeed(self.number, self._get_speed_val_from_speed(fan_speed)))
        else:
            _LOGGER.warning(f"Cannot set fan speed to unsupported value {fan_speed}")

    def set_mode(self, mode: ACMode):
        self._client.send_command(SetMode(self.number, mode))

    def get_status_strings(self):
        flags = [self.error, self.safety, self.spill, self.turbo]
        flag_names = ['ERROR', 'SAFETY', 'SPILL', 'TURBO']
        statuses = list(compress(flag_names, flags))
        if not statuses:
            statuses.append('NORMAL')
        return statuses

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
