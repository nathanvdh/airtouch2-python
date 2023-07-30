from __future__ import annotations

import logging
from dataclasses import dataclass
from itertools import compress
from pprint import pprint

from airtouch2.protocol.at2.constants import OPEN_ISSUE_TEXT, MessageLength, ResponseMessageConstants, ResponseMessageOffsets
from airtouch2.protocol.at2.conversions import brand_from_gateway_id, fan_speed_from_val
from airtouch2.protocol.at2.enums import ACBrand, ACFanSpeed, ACMode

_LOGGER = logging.getLogger(__name__)


def _resolve_brand(gateway_id: int, reported_brand: int) -> ACBrand:
    # Brand based on gateway ID takes priority according to app smali
    gateway_based_brand = brand_from_gateway_id(gateway_id)
    return gateway_based_brand if gateway_based_brand is not None else ACBrand(reported_brand)


def _parse_name(name: bytes) -> str:
    # There's probably a better way of doing this.
    return name.decode().split()[0].split("\0")[0]

# TODO: read through app smali code more and do this more properly
# Currently I'm assuming:
#   4 speed is always LOW, MED, HIGH, POWERFUL (EXCEPT for fujitsus with 4 speeds)
#   3 speed is always LOW, MED, HIGH
#   2 speed is always LOW, HIGH
#   Daikins have no Auto
#   Gateway ID 0x14 has no Auto
#   Gateway IDs 0xFF with 3 speed have no Auto
# This is based on the app decompiled code


def _supported_fan_speeds(brand: ACBrand, num_supported_speeds: int, gateway_id: int) -> list[ACFanSpeed]:
    all_speeds: list[ACFanSpeed] = list(ACFanSpeed.__members__.values())
    supported_speeds: list[ACFanSpeed] = []

    if brand == ACBrand.FUJITSU and num_supported_speeds == 4:
        supported_speeds = all_speeds[:5]
        return supported_speeds

    # Check cases that don't support Auto mode
    if (brand == ACBrand.DAIKIN or (gateway_id == 0xFF and num_supported_speeds == 3) or gateway_id == 0x14):
        supported_speeds = []
    else:
        supported_speeds = [ACFanSpeed.AUTO]

    if num_supported_speeds > 2:
        supported_speeds += all_speeds[2:2+num_supported_speeds]
    elif num_supported_speeds == 2:
        supported_speeds += [ACFanSpeed.LOW, ACFanSpeed.HIGH]
    elif num_supported_speeds < 2:
        _LOGGER.warning(
            f"AC reports less than 2 supported fan speeds, this is unusual - " + OPEN_ISSUE_TEXT)

    return supported_speeds


@dataclass
class AcInfo:
    number: int  # 0 or 1
    name: str
    active: bool
    mode: ACMode
    supported_fan_speeds: list[ACFanSpeed]
    fan_speed: ACFanSpeed
    set_temp: int
    measured_temp: int
    brand: ACBrand
    program: int
    error: bool
    error_code: int
    thermistor: bool
    turbo: bool
    safety: bool
    spill: bool

    def _get_status_strings(self):
        flags = [self.error, self.safety, self.spill, self.turbo]
        flag_names = ['ERROR', 'SAFETY', 'SPILL', 'TURBO']
        statuses = list(compress(flag_names, flags))
        if not statuses:
            statuses.append('NORMAL')
        return statuses

    def __str__(self):
        return f"""
        AC Name:\t\t{self.name}
        AC Number:\t\t{self.number}
        Active:\t\t\t{self.active}
        Status:\t\t\t{self._get_status_strings()}
        Mode:\t\t\t{self.mode}
        Fan Speed:\t\t{self.fan_speed}
        Supported Speeds:\t{[s.name for s in self.supported_fan_speeds]}
        Measured Temp:\t\t{self.measured_temp}
        Set Temp:\t\t{self.set_temp}
        Brand:\t\t\t{self.brand}
        Error Code:\t\t{self.error_code}
        """

    @staticmethod
    def parse(ac_number: int, ac_status1: int, ac_error_code: int, ac_status2: int, ac_mode: int, ac_fan_speed: int,
              ac_set_temp: int, ac_measured_temp: int, ac_brand: int, ac_gateway_id: int, ac_name: bytes) -> AcInfo | None:

        if (ac_fan_speed == 0 and ac_fan_speed == 0 and ac_gateway_id == 0):
            # This AC isn't connected
            return None

        # MS bit is on/off
        active = (ac_status1 & 0x80 > 0)
        # Bit 7 is whether AC is errored
        error = (ac_status1 & 0x40 > 0)
        # bit 4 is whether or not 'thermistor on AC' is checked (0 = checked)
        thermistor = (ac_status1 & 0x04 == 0)
        # lowest 3 bits are AC program number
        program = (ac_status1 & 0x07)

        # 6, 5 is turbo for AC0 and AC1
        turbo = (ac_status2 & (1 << (5 - ac_number))) > 0
        # 4, 3 is safety
        safety = (ac_status2 & (1 << (3 - ac_number))) > 0
        # 2, 1 is safety
        spill = (ac_status2 & (1 << (1 - ac_number))) > 0

        # simply 0-4, see ACMode enum
        mode = ACMode(ac_mode)

        brand = _resolve_brand(ac_gateway_id, ac_brand)

        # most signficant byte is # of speeds, least significant byte is speed (the meaning of which depends), see AT2Aircon::_set_true_and_supported_fan_speed()
        num_fan_speeds = (ac_fan_speed & 0xF0) >> 4
        supported_fan_speeds = _supported_fan_speeds(brand, num_fan_speeds, ac_gateway_id)

        fan_speed = fan_speed_from_val(supported_fan_speeds, ac_fan_speed & 0x0F)

        name = _parse_name(ac_name)

        return AcInfo(
            ac_number, name, active, mode, supported_fan_speeds, fan_speed, ac_set_temp, ac_measured_temp, brand,
            program, error, ac_error_code, thermistor, turbo, safety, spill)


@dataclass
class ZoneInfo:
    active: bool
    spill: bool
    damp: int

    @staticmethod
    def parse(damp: int, zone_status: int) -> ZoneInfo:
        return ZoneInfo(zone_status & 0x80 > 0, zone_status & 0x40 > 0, damp)


@dataclass
class GroupInfo:
    name: str
    number: int
    active: bool
    damp: int
    spill: bool
    turbo: bool

    def _get_status_strings(self):
        flags = [self.spill, self.turbo]
        flag_names = ['SPILL', 'TURBO']
        statuses = list(compress(flag_names, flags))
        if not statuses:
            statuses.append('NORMAL')
        return statuses

    def __str__(self):
        return f"""
        Group Name:\t{self.name}
        Group Number:\t{self.number}
        Active:\t\t{self.active}
        Status:\t\t{self._get_status_strings()}
        Damper:\t\t{f'{self.damp*10}%'}
        """


@dataclass
class SystemInfo:
    """ The state of the airtouch2 system"""
    aircons_by_id: dict[int, AcInfo]
    groups_by_id: dict[int, GroupInfo]
    touchpad_temp: int
    system_name: str

    # TODO: 'Bufferise' this code?
    @staticmethod
    def from_bytes(raw_response: bytes) -> SystemInfo:
        assert len(raw_response) == MessageLength.RESPONSE, f"Response message must be {MessageLength.RESPONSE} bytes"

        # ACs

        aircons_by_id: dict[int, AcInfo] = {}
        for ac_id in range(2):
            name_start = ResponseMessageOffsets.AC_NAME_START + ac_id * ResponseMessageConstants.SHORT_STRING_LENGTH
            name_end = name_start + ResponseMessageConstants.SHORT_STRING_LENGTH

            ac_info = AcInfo.parse(ac_id,
                                   raw_response[ResponseMessageOffsets.AC_STATUS_START + ac_id],
                                   raw_response[ResponseMessageOffsets.AC_ERROR_CODE_START + ac_id],
                                   raw_response[ResponseMessageOffsets.ACs_STATUS + ac_id],
                                   raw_response[ResponseMessageOffsets.AC_MODE_START + ac_id],
                                   raw_response[ResponseMessageOffsets.AC_FAN_SPEED_START + ac_id],
                                   raw_response[ResponseMessageOffsets.AC_SET_TEMP_START + ac_id],
                                   raw_response[ResponseMessageOffsets.AC_MEASURED_TEMP_START + ac_id],
                                   raw_response[ResponseMessageOffsets.AC_BRAND_START + ac_id],
                                   raw_response[ResponseMessageOffsets.AC_GATEWAY_ID_START + ac_id],
                                   raw_response[name_start:name_end])
            if ac_info is not None:
                aircons_by_id[ac_id] = ac_info

        # Groups
        # TODO: Factor out into an analogous 'GroupInfo.parse()'

        num_groups = raw_response[ResponseMessageOffsets.NUM_GROUPS]
        turbo_group = raw_response[ResponseMessageOffsets.TURBO_GROUP]
        groups_by_id: dict[int, GroupInfo] = {}

        for group_id in range(num_groups):
            name_start = ResponseMessageOffsets.GROUP_NAMES_START + group_id * ResponseMessageConstants.SHORT_STRING_LENGTH
            name_end = name_start + ResponseMessageConstants.SHORT_STRING_LENGTH
            name = _parse_name(raw_response[name_start:name_end])

            group_zones = raw_response[ResponseMessageOffsets.GROUP_ZONES_START + group_id]
            start_zone = (group_zones & 0xF0) >> 4
            num_zones = group_zones & 0x0F
            
            zone_info = ZoneInfo.parse(raw_response[ResponseMessageOffsets.ZONE_DAMPS_START + start_zone],
                                       raw_response[ResponseMessageOffsets.ZONE_STATUSES_START + start_zone])
            active = zone_info.active
            spill = zone_info.spill
            damp = zone_info.damp

            mismatches: set[str] = set()
            for zone_number in range(start_zone+1, start_zone + num_zones):
                zone_info = ZoneInfo.parse(raw_response[ResponseMessageOffsets.ZONE_DAMPS_START + zone_number],
                                           raw_response[ResponseMessageOffsets.ZONE_STATUSES_START + zone_number])
                # this group is spilling if any of its zones are
                if not spill:
                    spill = zone_info.spill
                # these should match for all zones that comprise this group
                if (damp != zone_info.damp):
                    mismatches.add("damper percents")
                if (active != zone_info.active):
                    mismatches.add("on/off states")
                if mismatches:
                    _LOGGER.warning(f"Zones of group '{name}' have mismatching {', '.join(mismatches)}")

            turbo = True if turbo_group == group_id else False

            groups_by_id[group_id] = GroupInfo(name, group_id, active, damp, spill, turbo)

        # System-wide

        touchpad_temp = raw_response[ResponseMessageOffsets.TOUCHPAD_TEMP]
        system_name = raw_response[ResponseMessageOffsets.SYSTEM_NAME: ResponseMessageOffsets.SYSTEM_NAME +
                                   ResponseMessageConstants.LONG_STRING_LENGTH].decode().split("\0")[0]

        return SystemInfo(aircons_by_id, groups_by_id, touchpad_temp, system_name)

    def __str__(self):
        return f"""
        System Name:\t{self.system_name}
        ACs:\t\t\t{pprint(self.aircons_by_id)}
        Groups:\t\t{pprint(self.groups_by_id)}
        Touchpad Temp:\t{self.touchpad_temp}
        """
