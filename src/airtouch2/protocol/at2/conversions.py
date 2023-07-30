
import logging
from airtouch2.protocol.at2.constants import OPEN_ISSUE_TEXT
from airtouch2.protocol.at2.enums import ACBrand, ACFanSpeed
from airtouch2.protocol.at2.lookups import GATEWAYID_BRAND_LOOKUP

_LOGGER = logging.getLogger(__name__)


def fan_speed_from_val(supported_speeds: list[ACFanSpeed], speed_val: int) -> ACFanSpeed:
    if speed_val < 5:
        # Units with no Auto speed still start with low == 1
        if ACFanSpeed.AUTO not in supported_speeds:
            speed_val -= 1
        return supported_speeds[speed_val]
    else:
        return ACFanSpeed.AUTO


def val_from_fan_speed(supported_speeds: list[ACFanSpeed], speed: ACFanSpeed):
    speed_val = supported_speeds.index(speed)
    # Units with no Auto speed still start with low == 1
    if ACFanSpeed.AUTO not in supported_speeds:
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
