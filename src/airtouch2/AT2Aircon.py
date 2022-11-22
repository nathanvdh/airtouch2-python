from __future__ import annotations
import logging
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from airtouch2.AT2Client import AT2Client
from airtouch2.protocol.enums import ACFanSpeedReference, ACBrand, ACMode
from airtouch2.protocol.messages import ChangeSetTemperature, ResponseMessage, SetFanSpeed, SetMode, ToggleAC
from airtouch2.protocol.lookups import GATEWAYID_BRAND_LOOKUP

OPEN_ISSUE_TEXT = "please open an issue and detail your system to me:\n\thttps://github.com/nathanvdh/airtouch2-python/issues/new"

_LOGGER = logging.getLogger(__name__)
class AT2Aircon:
    def __init__(self, number: int, client: AT2Client, response_message: ResponseMessage=None):
        self.number: int = number
        self._client: AT2Client = client
        if response_message:
            self.update(response_message)
        else:
            self.system_name: str = "UNKNOWN"
            self.name: str = "UNKNOWN"
            self.brand: ACBrand = ACBrand.NONE
            self.on: bool = False
            self.safety: bool = False
            self.mode: ACMode = ACMode.AUTO
            self.num_fan_speeds: int = -1
            self.fan_speed: ACFanSpeedReference = ACFanSpeedReference.AUTO
            self.supported_fan_speeds: list[ACFanSpeedReference] = []
            self.ambient_temp: int = -1
            self.set_temp: int = -1

    # TODO: read through app source code more and do this more properly
    # Currently I'm assuming:
    #   4 speed is always LOW, MED, HIGH, POWERFUL (EXCEPT for fujitsus with 4 speeds)
    #   3 speed is always LOW, MED, HIGH
    #   2 speed is always LOW, HIGH
    # These seem reasonable assumptions based on the app decompiled code
    def _set_true_and_supported_fan_speed(self, fan_speed: int, num_supported_speeds: int):
        all_speeds: list[ACFanSpeedReference] = list(ACFanSpeedReference._member_map_.values())
        # Unsure if this is sufficent or if I need to check the second/other type of brand
        if self.brand == ACBrand.FUJITSU and num_supported_speeds == 4:
            self.supported_fan_speeds = all_speeds[:num_supported_speeds+1]
        elif num_supported_speeds > 2:
            self.supported_fan_speeds = [ACFanSpeedReference.AUTO] + all_speeds[2:2+num_supported_speeds]
        elif num_supported_speeds == 2:
            self.supported_fan_speeds = [ACFanSpeedReference.AUTO, ACFanSpeedReference.LOW, ACFanSpeedReference.HIGH]
        elif num_supported_speeds < 2:
            _LOGGER.warning(f"AC{self.number} reports less than 2 supported fan speeds, this is unusual - " + OPEN_ISSUE_TEXT)

        if fan_speed < 5:
            self.fan_speed = self.supported_fan_speeds[fan_speed]
        else:
            self.fan_speed = ACFanSpeedReference.AUTO

    def update(self, response_message: ResponseMessage) -> None:
        self.system_name = response_message.system_name
        self.on = response_message.ac_active[self.number]
        self.safety = response_message.ac_safety[self.number]
        self.mode = response_message.ac_mode[self.number]

        self.ambient_temp = response_message.ac_ambient_temp[self.number]
        self.set_temp = response_message.ac_set_temp[self.number]
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

        num_fan_speeds = response_message.ac_num_fan_speeds[self.number]
        fan_speed = response_message.ac_fan_speed[self.number]
        self._set_true_and_supported_fan_speed(fan_speed, num_fan_speeds)

        # TODO: Handle this?
        if brand == ACBrand.NONE and gateway_id == 0:
            _LOGGER.warning(f"AC{self.number} appears disconnected from airtouch")

        self.name = response_message.ac_name[self.number]

    def inc_dec_set_temp(self, inc: bool):
        self._client.send_command(ChangeSetTemperature(self.number, inc))

    def set_set_temp(self, new_temp: int):
        temp_diff = new_temp - self.set_temp
        #print(f"Temp diff: {temp_diff}")
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
            speed_val = self.supported_fan_speeds.index(fan_speed)
            self._client.send_command(SetFanSpeed(self.number, speed_val))
        else:
            _LOGGER.warning(f"Cannot set fan speed to unsupported value {fan_speed}")

    def set_mode(self, mode: ACMode):
        self._client.send_command(SetMode(self.number, mode))

    def __str__(self):
        status_string = ''
        if self.safety:
            status_string += "SAFETY"
        else:
            status_string += "NORMAL"
        return f"""
        System Name:\t\t{self.system_name}
        AC Number:\t\t{self.number}
        AC Name:\t\t{self.name}
        On:\t\t\t{self.on}
        Status:\t\t\t{status_string}
        Mode:\t\t\t{self.mode}
        Fan Speed:\t\t{self.fan_speed}
        Supported Speeds:\t{[s.name for s in self.supported_fan_speeds]}
        Ambient Temp:\t\t{self.ambient_temp}
        Set Temp:\t\t{self.set_temp}
        Brand:\t\t\t{self.brand}
        """
