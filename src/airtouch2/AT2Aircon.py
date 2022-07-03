from __future__ import annotations
from typing import TYPE_CHECKING
from airtouch2.protocol.enums import ACFanSpeed, ACManufacturer, ACMode
from airtouch2.protocol.messages import ChangeSetTemperature, ResponseMessage, SetFanSpeed, SetMode, ToggleAC
if TYPE_CHECKING:
    from airtouch2.AT2Client import AT2Client

class AT2Aircon:
    def __init__(self, number: int, client: AT2Client, response_message: ResponseMessage=None):
        self.number = number
        self._client = client
        if response_message:
            self.update(response_message)
        else:
            self.system_name = "UNKNOWN"
            self.name = "UNKNOWN"
            self.manufacturer = ACManufacturer.NONE
            self.on = False
            self.mode = -1
            self.fan_speed = -1
            self.ambient_temp = -1
            self.set_temp = -1
            self.zones = []

    def update(self, response_message: ResponseMessage) -> None:
        self.system_name = response_message.system_name
        self.on = response_message.ac_active[self.number]
        self.status = response_message.ac_status[self.number]
        self.mode = response_message.ac_mode[self.number]
        self.fan_speed = response_message.ac_fan_speed[self.number]
        self.ambient_temp = response_message.ac_ambient_temp[self.number]
        self.set_temp = response_message.ac_set_temp[self.number]
        self.manufacturer = response_message.ac_manufacturer[self.number]
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

    def set_fan_speed(self, fan_speed: ACFanSpeed):
        self._client.send_command(SetFanSpeed(self.number, fan_speed))

    def set_mode(self, mode: ACMode):
        self._client.send_command(SetMode(self.number, mode))

    def __str__(self):
        return f"""
        System Name:\t{self.system_name}
        AC Name:\t{self.name}
        On:\t\t{self.on}
        Status:\t\t{self.status}
        Mode:\t\t{self.mode}
        Fan Speed:\t{self.fan_speed}
        Ambient Temp:\t{self.ambient_temp}
        Set Temp:\t{self.set_temp}
        Manufacturer:\t{self.manufacturer}
        """
        