from airtouch2.protocol.at2plus.constants import Limits


def value_from_setpoint(setpoint: float | None) -> int:
    if setpoint:
        if not Limits.SETPOINT_MIN <= setpoint <= Limits.SETPOINT_MAX:
            raise ValueError(
                f'Setpoint must be between {Limits.SETPOINT_MIN} and {Limits.SETPOINT_MAX}')
        return int(setpoint * 10 - 100)
    return int(Limits.SETPOINT_MAX * 10 - 100 + 1)


def setpoint_from_value(value: int) -> float | None:
    setpoint = (value+100)/10
    if Limits.SETPOINT_MIN <= setpoint <= Limits.SETPOINT_MAX:
        return setpoint
    return None


def value_from_temperature(temp: float | None) -> int:
    if temp:
        if not Limits.TEMP_MIN <= temp <= Limits.SETPOINT_MAX:
            raise ValueError(
                f'Temperature must be between {Limits.TEMP_MIN} abd {Limits.TEMP_MAX}')
        else:
            return int(temp * 10 + 500)
    return int(Limits.TEMP_MAX * 10 + 501)


def temperature_from_value(val: int) -> float | None:
    temp: float = (val - 500)/10
    if Limits.TEMP_MIN <= temp <= Limits.TEMP_MAX:
        return temp
    return None
