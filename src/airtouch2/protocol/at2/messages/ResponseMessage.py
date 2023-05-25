from __future__ import annotations
from dataclasses import dataclass
from airtouch2.protocol.at2.constants import ResponseMessageConstants, ResponseMessageOffsets
from airtouch2.protocol.at2.enums import ACBrand, ACMode


@dataclass
class ResponseMessage:
    """ The airtouch 2 response message (there is only one) that contains all the information about the current state of the system"""
    # Currently only 1 AC is supported, information in the message about a 2nd AC is unknown.
    # Data structures are lists in the hope to eventually contain a value for each AC.
    ac_active: list[bool]
    ac_error: list[bool]
    ac_error_code: list[int]
    ac_thermistor: list[bool]
    ac_turbo: list[bool]
    ac_safety: list[bool]
    ac_spill: list[bool]
    ac_mode: list[ACMode]
    ac_num_fan_speeds: list[int]
    ac_fan_speed: list[int]
    ac_set_temp: list[int]
    ac_measured_temp: list[int]
    touchpad_temp: int
    ac_brand: list[ACBrand]
    ac_gateway_id: list[int]
    ac_name: list[str]
    system_name: str
    num_groups: int
    group_zones: list[tuple[int, int]]
    zone_damps: list[int]
    group_names: list[str]
    zone_ons: list[bool]
    zone_spills: list[bool]
    turbo_group: int

    # TODO: 'Bufferise' this?
    @staticmethod
    def from_bytes(raw_response: bytes) -> ResponseMessage:
        status = raw_response[ResponseMessageOffsets.AC1_STATUS]
        # MS bit is on/off
        ac_active = [(status & 0x80 > 0)]
        # Bit 7 is whether AC is errored
        ac_error = [(status & 0x40 > 0)]
        ac_error_code = [raw_response[ResponseMessageOffsets.AC1_ERROR_CODE]]
        # bit 4 is whether or not 'thermistor on AC' is checked (0 = checked)
        ac_thermistor = [(status & 0x04 == 0)]
        # lowest 3 bits are AC program number
        # ac_program = [(status & 0x07)]

        status2 = raw_response[ResponseMessageOffsets.ACs_STATUS]
        ac_turbo = [(status2 & 0x20 > 0)]
        ac_safety = [(status2 & 0x04 > 0)]
        ac_spill = [(status2 & 0x02) > 0]

        # simply 0-4, see ACMode enum
        ac_mode = [ACMode(raw_response[ResponseMessageOffsets.AC1_MODE])]
        # most signficant byte is # of speeds, least significant byte is speed (the meaning of which depends), see AT2Aircon::_set_true_and_supported_fan_speed()
        ac_num_fan_speeds = [(raw_response[ResponseMessageOffsets.AC1_FAN_SPEED] & 0xF0) >> 4]
        ac_fan_speed = [raw_response[ResponseMessageOffsets.AC1_FAN_SPEED] & 0x0F]

        ac_set_temp = [raw_response[ResponseMessageOffsets.AC1_SET_TEMP]]
        ac_measured_temp = [raw_response[ResponseMessageOffsets.AC1_MEASURED_TEMP]]
        touchpad_temp = raw_response[ResponseMessageOffsets.TOUCHPAD_TEMP]

        ac_brand = [ACBrand(raw_response[ResponseMessageOffsets.AC1_BRAND])]
        ac_gateway_id = [raw_response[ResponseMessageOffsets.AC1_GATEWAY_ID]]

        ac_name = [
            raw_response
            [ResponseMessageOffsets.AC1_NAME_START: ResponseMessageOffsets.AC1_NAME_START +
             ResponseMessageConstants.SHORT_STRING_LENGTH].decode().split("\0")[0]]
        system_name = raw_response[ResponseMessageOffsets.SYSTEM_NAME: ResponseMessageOffsets.SYSTEM_NAME +
                                   ResponseMessageConstants.LONG_STRING_LENGTH].decode().split("\0")[0]

        # Group stuff
        num_groups = raw_response[ResponseMessageOffsets.NUM_GROUPS]
        # list of tuples: (start_zone, num_zones)
        group_zones = [
            ((raw_response[offset] & 0xF0) >> 4, raw_response[offset] & 0x0F)
            for offset in range(
                ResponseMessageOffsets.GROUP_ZONES_START, ResponseMessageOffsets.GROUP_ZONES_START + 16)]
        zone_damps = [
            raw_response[offset]
            for offset in range(
                ResponseMessageOffsets.ZONE_DAMPS_START, ResponseMessageOffsets.ZONE_DAMPS_START + 16)]
        group_names = [
            raw_response[offset: offset + ResponseMessageConstants.SHORT_STRING_LENGTH].decode().split("\0")[0]
            for offset in range(
                ResponseMessageOffsets.GROUP_NAMES_START, ResponseMessageOffsets.GROUP_NAMES_START + 16 *
                ResponseMessageConstants.SHORT_STRING_LENGTH, ResponseMessageConstants.SHORT_STRING_LENGTH)]
        zone_statuses = [
            raw_response[offset]
            for offset in range(
                ResponseMessageOffsets.ZONE_STATUSES_START, ResponseMessageOffsets.ZONE_STATUSES_START + 16)]
        zone_ons = [(status & 0x80 > 0) for status in zone_statuses]
        zone_spills = [(status & 0x40 > 0) for status in zone_statuses]
        turbo_group = raw_response[ResponseMessageOffsets.TURBO_GROUP]

        return ResponseMessage(
            ac_active, ac_error, ac_error_code, ac_thermistor, ac_turbo, ac_safety, ac_spill, ac_mode,
            ac_num_fan_speeds, ac_fan_speed, ac_set_temp, ac_measured_temp, touchpad_temp, ac_brand, ac_gateway_id,
            ac_name, system_name, num_groups, group_zones, zone_damps, group_names, zone_ons, zone_spills, turbo_group)
