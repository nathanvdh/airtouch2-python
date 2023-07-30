from enum import IntEnum


class MessageLength(IntEnum):
    UNDETERMINED = 0
    COMMAND = 13
    RESPONSE = 395


class CommandMessageConstants(IntEnum):
    BYTE_0 = 85   # Byte 0 of command always fixed
    BYTE_2 = 12   # Byte 2 of command always fixed
    TOGGLE = 128  # toggle is common to both ACCommands and GroupCommands


class CommandMessageType(IntEnum):
    # Go in byte 1 of command messages
    REQUEST_STATE = 1
    GROUP_CONTROL = 129
    AC_CONTROL = 134


class ACCommands(IntEnum):
    # Go in byte 4 of CommandMessageType.AC_CONTROL messages
    SET_MODE = 129
    SET_FAN_SPEED = 130
    TEMP_DEC = 147
    TEMP_INC = 163


class GroupCommands(IntEnum):
    CHANGE_DAMP = 1  # 1 goes in byte 5 for change damp
    TOGGLE = 0       # 0 goes in byte 5 for toggle
    DAMP_DEC = 1     # Damper decrement (10% down) in byte 4
    DAMP_INC = 2     # Damper increment (10% up) in byte 4


class ResponseMessageConstants(IntEnum):
    LONG_STRING_LENGTH = 16
    SHORT_STRING_LENGTH = 8


class ResponseMessageOffsets(IntEnum):
    # Header is 2 bytes
    HEADER = 0
    # There are 16 zones
    # zone names are 8 bytes (ResponseMessageConstants.SHORT_STRING_LENGTH)
    GROUP_NAMES_START = 100
    # zone statuses are 1 byte each
    ZONE_STATUSES_START = 228
    # In order, each group and the number of zones it consists of
    # Zones must be in consecutive order
    GROUP_ZONES_START = 244
    # Zone strengths are 1 byte each
    ZONE_DAMPS_START = 276
    NUM_GROUPS = 292
    TURBO_GROUP = 297
    # Contains isTurbo, isSafety, isSpill bits of the 2 ACs
    ACs_STATUS = 299
    TOUCHPAD_TEMP = 323  # I think?? Idk what happens when there's 2 touchpads then...
    # System name is 16 bytes (ResponseMessageConstants.LONG_STRING_LENGTH)
    SYSTEM_NAME = 324
    # The following have 2 consecutuve bytes of each type, 1 for each AC.
    # On/Off, isError, 'Auto off' enabled, 'thermistor on AC', program number
    AC_STATUS_START = 354
    AC_BRAND_START = 356
    AC_MODE_START = 358
    AC_FAN_SPEED_START = 360
    AC_SET_TEMP_START = 362
    AC_MEASURED_TEMP_START = 364
    AC_ERROR_CODE_START = 366
    AC_GATEWAY_ID_START = 368
    AC_NAME_START = 370  # AC names are 8 bytes (ResponseMessageConstants.SHORT_STRING_LENGTH)
    HASH = 394


OPEN_ISSUE_TEXT = "please open an issue and detail your system:\n\thttps://github.com/nathanvdh/airtouch2-python/issues/new"
