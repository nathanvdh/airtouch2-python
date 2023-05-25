
import logging
from airtouch2.protocol.at2.constants import OPEN_ISSUE_TEXT
from airtouch2.protocol.at2.enums import ACBrand, ACFanSpeedReference
from airtouch2.protocol.at2.lookups import GATEWAYID_BRAND_LOOKUP

_LOGGER = logging.getLogger(__name__)

# TODO: read through app smali code more and do this more properly
# Currently I'm assuming:
#   4 speed is always LOW, MED, HIGH, POWERFUL (EXCEPT for fujitsus with 4 speeds)
#   3 speed is always LOW, MED, HIGH
#   2 speed is always LOW, HIGH
#   Daikins have no Auto
#   Gateway ID 0x14 has no Auto
#   Gateway IDs 0xFF with 3 speed have no Auto
# This is based on the app decompiled code


def supported_fan_speeds(brand: ACBrand, num_supported_speeds: int, gateway_id: int) -> list[ACFanSpeedReference]:
    all_speeds: list[ACFanSpeedReference] = list(ACFanSpeedReference.__members__.values())
    supported_speeds: list[ACFanSpeedReference] = []

    if brand == ACBrand.FUJITSU and num_supported_speeds == 4:
        supported_speeds = all_speeds[:5]
        return supported_speeds

    # Check cases that don't support Auto mode
    if (brand == ACBrand.DAIKIN or (gateway_id == 0xFF and num_supported_speeds == 3) or gateway_id == 0x14):
        supported_speeds = []
    else:
        supported_speeds = [ACFanSpeedReference.AUTO]

    if num_supported_speeds > 2:
        supported_speeds += all_speeds[2:2+num_supported_speeds]
    elif num_supported_speeds == 2:
        supported_speeds += [ACFanSpeedReference.LOW, ACFanSpeedReference.HIGH]
    elif num_supported_speeds < 2:
        _LOGGER.warning(
            f"AC reports less than 2 supported fan speeds, this is unusual - " + OPEN_ISSUE_TEXT)

    return supported_speeds


def fan_speed_from_val(supported_speeds: list[ACFanSpeedReference], speed_val: int) -> ACFanSpeedReference:
    if speed_val < 5:
        # Units with no Auto speed still start with low == 1
        if ACFanSpeedReference.AUTO not in supported_speeds:
            speed_val -= 1
        return supported_speeds[speed_val]
    else:
        return ACFanSpeedReference.AUTO


def val_from_fan_speed(supported_speeds: list[ACFanSpeedReference], speed: ACFanSpeedReference):
    speed_val = supported_speeds.index(speed)
    # Units with no Auto speed still start with low == 1
    if ACFanSpeedReference.AUTO not in supported_speeds:
        speed_val += 1
    return speed_val


def brand_from_gateway_id(gateway_id: int) -> ACBrand | None:
    if gateway_id > 0:
        if gateway_id in GATEWAYID_BRAND_LOOKUP:
            return GATEWAYID_BRAND_LOOKUP[gateway_id]
        else:
            _LOGGER.warning(
                f"AC has an unfamiliar gateway ID: {hex(gateway_id)} - " + OPEN_ISSUE_TEXT +
                "\nInclude the gateway ID shown above")
    return None
