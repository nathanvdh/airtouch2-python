from enum import Enum, IntEnum

# Note the order here is also the priority in which the messages are handled (lower = higher priority)
# class MessageType(IntEnum):
#     UNDETERMINED = 0
#     RESPONSE = 1
#     COMMAND = 2

#     def __str__(self):
#         if self == MessageType.UNDETERMINED:
#             return "Undetermined"
#         if self == MessageType.RESPONSE:
#             return "Response"
#         if self == MessageType.COMMAND:
#             return "Command"

class ACMode(Enum):
    AUTO = 0
    HEAT = 1
    DRY = 2
    FAN = 3
    COOL = 4

    def __str__(self):
        if self == ACMode.AUTO:
            return "Auto"
        if self == ACMode.HEAT:
            return "Heat"
        if self == ACMode.DRY:
            return "Dry"
        if self == ACMode.FAN:
            return "Fan"
        if self == ACMode.COOL:
            return "Cool"
        return "Unknown"

class ACFanSpeed(Enum):
    AUTO = 0
    QUIET = 1
    LOW = 2
    MEDIUM = 3
    HIGH = 4

    def __str__(self):
        if self == ACFanSpeed.AUTO:
            return "Auto"
        if self == ACFanSpeed.QUIET:
            return "Quiet"
        if self == ACFanSpeed.LOW:
            return "Low"
        if self == ACFanSpeed.MEDIUM:
            return "Medium"
        if self == ACFanSpeed.HIGH:
            return "High"
        return "Unknown"
